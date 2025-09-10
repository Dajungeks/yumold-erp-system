"""
SQLite 지출 요청 관리자 - 지출 요청, 승인 프로세스 관리
CSV 기반에서 SQLite 기반으로 전환
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteExpenseRequestManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 지출요청서 테이블 생성 (헤더 정보)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expense_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id TEXT NOT NULL,
                requester_name TEXT NOT NULL,
                expense_title TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'VND',
                expected_date DATE,
                expense_description TEXT,
                notes TEXT,
                first_approver_id TEXT,
                first_approver_name TEXT,
                second_approver_id TEXT,
                second_approver_name TEXT,
                status TEXT DEFAULT 'pending',
                request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                approval_date DATETIME,
                approver_comments TEXT,
                attachment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 지출항목 테이블 생성 (상세 항목들)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expense_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                item_description TEXT NOT NULL,
                item_category TEXT,
                item_amount REAL NOT NULL,
                item_currency TEXT DEFAULT 'VND',
                vendor TEXT,
                item_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES expense_requests (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("지출 요청 관련 테이블 초기화 완료")

    def get_pending_approvals(self, approver_id):
        """특정 승인자의 승인 대기 지출 요청 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 승인 대기 중인 지출 요청 조회
            cursor.execute('''
                SELECT er.*, ea.approval_id, ea.approval_step
                FROM expense_requests er
                JOIN expense_approvals ea ON CAST(er.id AS TEXT) = ea.request_id
                WHERE ea.approver_id = ? AND ea.result = '대기'
                ORDER BY er.request_date ASC
            ''', (approver_id,))
            
            requests = cursor.fetchall()
            conn.close()
            
            # Row 객체를 dict로 변환
            return [dict(row) for row in requests] if requests else []
            
        except Exception as e:
            logger.error(f"승인 대기 요청 조회 오류: {str(e)}")
            return []

    def process_approval(self, approval_id, approver_id, decision, comments=""):
        """승인 처리 (승인/반려)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 승인 정보 업데이트
            cursor.execute('''
                UPDATE expense_approvals 
                SET result = ?, comments = ?, approval_date = CURRENT_TIMESTAMP
                WHERE approval_id = ? AND approver_id = ?
            ''', (decision, comments, approval_id, approver_id))
            
            # 지출 요청 상태 업데이트
            if decision == "승인":
                # 다음 승인 단계가 있는지 확인
                cursor.execute('''
                    SELECT COUNT(*) FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = CAST(er.id AS TEXT)
                    WHERE ea.approval_id = ? AND ea.result = '대기'
                ''', (approval_id,))
                
                remaining = cursor.fetchone()[0]
                
                if remaining == 0:
                    # 모든 승인 완료
                    cursor.execute('''
                        UPDATE expense_requests 
                        SET status = '승인완료', approval_date = CURRENT_TIMESTAMP
                        WHERE id IN (
                            SELECT CAST(ea.request_id AS INTEGER)
                            FROM expense_approvals ea 
                            WHERE ea.approval_id = ?
                        )
                    ''', (approval_id,))
            else:
                # 반려 처리
                cursor.execute('''
                    UPDATE expense_requests 
                    SET status = '반려', approval_date = CURRENT_TIMESTAMP
                    WHERE id IN (
                        SELECT CAST(ea.request_id AS INTEGER)
                        FROM expense_approvals ea 
                        WHERE ea.approval_id = ?
                    )
                ''', (approval_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"승인 처리 완료: {approval_id} - {decision}")
            return True, f"승인이 {decision}되었습니다."
            
        except Exception as e:
            logger.error(f"승인 처리 오류: {str(e)}")
            return False, f"승인 처리 중 오류가 발생했습니다: {str(e)}"

    def create_expense_request(self, request_data):
        """지출요청서 생성 - 메인 에러 원인 해결"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 첫 번째 승인자 정보 추출
            first_approver = request_data.get('first_approver', {})
            second_approver = request_data.get('second_approver', {})
            
            cursor.execute('''
                INSERT INTO expense_requests (
                    requester_id, requester_name, expense_title, category, 
                    amount, currency, expected_date, expense_description, 
                    notes, first_approver_id, first_approver_name,
                    second_approver_id, second_approver_name, status, attachment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_data['requester_id'],
                request_data['requester_name'],
                request_data['expense_title'],
                request_data['category'],
                request_data['amount'],
                request_data.get('currency', 'USD'),
                request_data['expected_date'],
                request_data['expense_description'],
                request_data.get('notes', ''),
                first_approver.get('approver_id', ''),  # 수정: employee_id → approver_id
                first_approver.get('approver_name', ''),  # 수정: employee_name → approver_name
                second_approver.get('approver_id', '') if second_approver else '',
                second_approver.get('approver_name', '') if second_approver else '',
                request_data.get('status', 'pending'),
                request_data.get('attachment', '')
            ))
            
            request_id = cursor.lastrowid
            
            # 승인 레코드 생성 (1차 승인자)
            if first_approver.get('approver_id'):
                cursor.execute('''
                    INSERT INTO expense_approvals (
                        approval_id, request_id, approval_step, approver_id, approver_name,
                        approval_order, result, status, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"APP-{request_id}-1",  # approval_id
                    str(request_id),  # request_id를 문자열로 변환
                    1,  # approval_step
                    first_approver.get('approver_id', ''),  # approver_id
                    first_approver.get('approver_name', ''),  # approver_name
                    1,  # approval_order
                    '대기',  # result
                    'pending',  # status
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # created_date
                ))
            
            # 승인 레코드 생성 (2차 승인자, 필요시)
            if second_approver and second_approver.get('approver_id'):
                cursor.execute('''
                    INSERT INTO expense_approvals (
                        approval_id, request_id, approval_step, approver_id, approver_name,
                        approval_order, result, status, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"APP-{request_id}-2",  # approval_id
                    str(request_id),  # request_id를 문자열로 변환
                    2,  # approval_step
                    second_approver.get('approver_id', ''),  # approver_id
                    second_approver.get('approver_name', ''),  # approver_name
                    2,  # approval_order
                    '대기',  # result
                    'pending',  # status
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # created_date
                ))
            
            conn.commit()
            conn.close()
            
            return True, f"지출요청서가 성공적으로 제출되었습니다. (요청번호: {request_id})"
            
        except Exception as e:
            return False, f"지출요청서 제출 중 오류가 발생했습니다: {str(e)}"
    
    def get_expense_categories(self):
        """지출 카테고리 목록 반환"""
        return [
            "교통비", "숙박비", "식비", "회의비", "사무용품", 
            "통신비", "마케팅비", "교육비", "의료비", "기타"
        ]
    
    def get_my_expense_requests(self, user_id):
        """사용자별 지출요청서 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT * FROM expense_requests 
                WHERE requester_id = ? 
                ORDER BY request_date DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=[user_id])
            conn.close()
            
            return df if len(df) > 0 else None
            
        except Exception as e:
            print(f"내 요청서 조회 중 오류: {str(e)}")
            return None
    
    def get_expense_request_statistics(self, user_id):
        """사용자별 지출요청서 통계"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 전체 통계
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END) as total_approved_amount
                FROM expense_requests 
                WHERE requester_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'total': result[0],
                    'pending': result[1],
                    'approved': result[2],
                    'rejected': result[3],
                    'total_approved_amount': result[4] or 0
                }
            else:
                return {
                    'total': 0,
                    'pending': 0,
                    'approved': 0,
                    'rejected': 0,
                    'total_approved_amount': 0
                }
                
        except Exception as e:
            print(f"통계 조회 중 오류: {str(e)}")
            return None
    
    def get_all_expense_requests(self):
        """모든 지출요청서 조회 (관리자용)"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM expense_requests 
                ORDER BY request_date DESC
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            print(f"전체 요청서 조회 중 오류: {str(e)}")
            return None
    
    def update_expense_request_status(self, request_id, status, approver_comments=""):
        """지출요청서 상태 업데이트 (승인/거부)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE expense_requests 
                SET status = ?, approval_date = ?, approver_comments = ?, updated_at = ?
                WHERE id = ?
            ''', (status, datetime.now(), approver_comments, datetime.now(), request_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            if affected_rows > 0:
                return True, "요청서 상태가 업데이트되었습니다."
            else:
                return False, "요청서를 찾을 수 없습니다."
                
        except Exception as e:
            return False, f"상태 업데이트 중 오류: {str(e)}"
    
    def delete_expense_request(self, request_id, user_id):
        """지출요청서 삭제 (본인만 가능, pending 상태만)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 먼저 요청서가 존재하고 본인 것인지, pending 상태인지 확인
            cursor.execute('''
                SELECT status FROM expense_requests 
                WHERE id = ? AND requester_id = ?
            ''', (request_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                return False, "요청서를 찾을 수 없거나 삭제 권한이 없습니다."
            
            if result[0] != 'pending':
                return False, "승인 처리된 요청서는 삭제할 수 없습니다."
            
            # 삭제 실행
            cursor.execute('DELETE FROM expense_requests WHERE id = ? AND requester_id = ?', 
                         (request_id, user_id))
            
            conn.commit()
            conn.close()
            
            return True, "요청서가 삭제되었습니다."
            
        except Exception as e:
            return False, f"삭제 중 오류: {str(e)}"
    
    def add_expense_request_with_items(self, request_data, items):
        """다중 항목을 포함한 지출요청서 추가"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 총 금액 계산
            total_amount = sum(float(item.get('item_amount', 0)) for item in items)
            
            # 메인 지출요청서 추가
            cursor.execute('''
                INSERT INTO expense_requests (
                    requester_id, requester_name, expense_title, category,
                    amount, currency, expected_date, expense_description,
                    notes, status, request_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_data['requester_id'],
                request_data['requester_name'],
                request_data['expense_title'],
                request_data['category'],
                total_amount,  # amount 컬럼에 총 금액 저장
                request_data['currency'],
                request_data['expected_date'],
                request_data['expense_description'],
                request_data.get('notes', ''),
                'pending',
                request_data['request_date'],
                datetime.now(),
                datetime.now()
            ))
            
            # 생성된 요청서 ID 가져오기
            request_id = cursor.lastrowid
            
            # 각 지출 항목 추가
            for item in items:
                cursor.execute('''
                    INSERT INTO expense_items (
                        request_id, item_description, item_category, item_amount,
                        item_currency, vendor, item_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id,
                    item['item_description'],
                    item['item_category'],
                    float(item['item_amount']),
                    item.get('item_currency', request_data['currency']),
                    item.get('vendor', ''),
                    item.get('item_notes', ''),
                    datetime.now(),
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            return request_id
            
        except Exception as e:
            print(f"다중 항목 지출요청서 추가 중 오류: {str(e)}")
            return None
    
    def get_expense_items(self, request_id):
        """특정 지출요청서의 항목들 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM expense_items 
                WHERE request_id = ?
                ORDER BY created_at ASC
            ''', (request_id,))
            
            columns = [description[0] for description in cursor.description]
            items = []
            
            for row in cursor.fetchall():
                item_dict = {}
                for i, value in enumerate(row):
                    item_dict[columns[i]] = value
                items.append(item_dict)
            
            conn.close()
            return items
            
        except Exception as e:
            print(f"지출 항목 조회 중 오류: {str(e)}")
            return []
    
    def cancel_expense_request(self, request_id):
        """지출요청서 취소 (상태를 'cancelled'로 변경)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 먼저 요청서가 존재하고 pending 상태인지 확인
            cursor.execute('''
                SELECT status FROM expense_requests 
                WHERE id = ?
            ''', (request_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "요청서를 찾을 수 없습니다."
            
            if result[0] not in ['pending', '대기', 'PENDING']:
                return False, "승인 처리된 요청서는 취소할 수 없습니다."
            
            # 상태를 'cancelled'로 업데이트
            cursor.execute('''
                UPDATE expense_requests 
                SET status = 'cancelled', updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), request_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            if affected_rows > 0:
                return True, "요청서가 취소되었습니다."
            else:
                return False, "요청서 취소에 실패했습니다."
            
        except Exception as e:
            return False, f"취소 중 오류: {str(e)}"
    
    def get_my_requests(self, user_id):
        """내 지출요청서 목록 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id as request_id,
                    expense_title as expense_type,
                    amount,
                    currency,
                    expected_date as expense_date,
                    expense_description as purpose,
                    notes as additional_notes,
                    status,
                    request_date,
                    requester_name,
                    category,
                    first_approver_name,
                    attachment
                FROM expense_requests 
                WHERE requester_id = ?
                ORDER BY request_date DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Row 객체를 dict로 변환
            requests = []
            for row in rows:
                request_dict = dict(row)
                # 필드 매핑 추가
                request_dict['vendor'] = ''  # 업체 정보는 별도 테이블에 없으면 빈 값
                request_dict['priority'] = 'normal'  # 우선순위 기본값
                requests.append(request_dict)
                
            return requests
            
        except Exception as e:
            logger.error(f"내 요청서 조회 중 오류: {str(e)}")
            return []

    def add_expense_request_with_items(self, request_data, items_data):
        """여러 항목을 포함한 지출요청서 추가"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 총 금액 계산
            total_amount = sum(float(item.get('item_amount', 0)) for item in items_data)
            
            # 지출요청서 헤더 추가
            cursor.execute('''
                INSERT INTO expense_requests (
                    requester_id, requester_name, expense_title, category,
                    amount, currency, expected_date, expense_description, notes, request_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_data.get('requester_id'),
                request_data.get('requester_name'),
                request_data.get('expense_title'),
                request_data.get('category'),
                total_amount,
                request_data.get('currency', 'VND'),
                request_data.get('expected_date'),
                request_data.get('expense_description'),
                request_data.get('notes'),
                request_data.get('request_date')
            ))
            
            request_id = cursor.lastrowid
            
            # 지출 항목들 추가
            for item in items_data:
                cursor.execute('''
                    INSERT INTO expense_items (
                        request_id, item_description, item_category,
                        item_amount, item_currency, vendor, item_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id,
                    item.get('item_description'),
                    item.get('item_category'),
                    float(item.get('item_amount', 0)),
                    item.get('item_currency', 'VND'),
                    item.get('vendor'),
                    item.get('item_notes')
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"지출요청서 {request_id} 및 {len(items_data)}개 항목 추가 완료")
            return request_id
            
        except Exception as e:
            logger.error(f"지출요청서 및 항목 추가 오류: {str(e)}")
            return None

    def get_expense_items(self, request_id):
        """특정 지출요청서의 항목들 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM expense_items 
                WHERE request_id = ? 
                ORDER BY id ASC
            ''', (request_id,))
            
            items = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in items] if items else []
            
        except Exception as e:
            logger.error(f"지출 항목 조회 오류: {str(e)}")
            return []

    def get_expense_request_with_items(self, request_id):
        """지출요청서와 항목들을 함께 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 헤더 정보 조회
            cursor.execute('SELECT * FROM expense_requests WHERE id = ?', (request_id,))
            request = cursor.fetchone()
            
            if not request:
                conn.close()
                return None
                
            request_dict = dict(request)
            
            # 항목들 조회
            cursor.execute('''
                SELECT * FROM expense_items 
                WHERE request_id = ? 
                ORDER BY id ASC
            ''', (request_id,))
            
            items = cursor.fetchall()
            request_dict['items'] = [dict(row) for row in items] if items else []
            
            conn.close()
            return request_dict
            
        except Exception as e:
            logger.error(f"지출요청서 및 항목 조회 오류: {str(e)}")
            return None

