# -*- coding: utf-8 -*-
"""
PostgreSQL ExpenseRequest 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid
import pandas as pd

class PostgreSQLExpenseRequestManager(BasePostgreSQLManager):
    """PostgreSQL ExpenseRequest 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """ExpenseRequest 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 완전한 expense_requests 테이블 생성 (SQLite 매니저 참조)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS expense_requests (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(50) UNIQUE NOT NULL,
                        requester_id VARCHAR(50) NOT NULL,
                        requester_name VARCHAR(100) NOT NULL,
                        request_date DATE NOT NULL,
                        expense_title VARCHAR(200) NOT NULL,
                        expense_description TEXT,
                        category VARCHAR(100),
                        amount DECIMAL(15, 2) NOT NULL,
                        currency VARCHAR(10) DEFAULT 'VND',
                        expected_date DATE,
                        status VARCHAR(20) DEFAULT 'pending',
                        current_step INTEGER DEFAULT 1,
                        total_steps INTEGER DEFAULT 1,
                        attachment_path TEXT,
                        notes TEXT,
                        first_approver_id VARCHAR(50),
                        first_approver_name VARCHAR(100),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 지출항목 테이블 생성 (상세 항목들)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS expense_items (
                        id SERIAL PRIMARY KEY,
                        request_id INTEGER NOT NULL,
                        item_description TEXT NOT NULL,
                        item_category VARCHAR(100),
                        item_amount DECIMAL(15, 2) NOT NULL,
                        item_currency VARCHAR(10) DEFAULT 'VND',
                        vendor VARCHAR(200),
                        item_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (request_id) REFERENCES expense_requests (id) ON DELETE CASCADE
                    )
                """)
                
                self.log_info("ExpenseRequest 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"ExpenseRequest 테이블 초기화 실패: {e}")
    
    def get_all_items(self) -> 'pd.DataFrame':
        """모든 항목을 DataFrame으로 조회"""
        try:
            import pandas as pd
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM expense_requests ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                if items:
                    return pd.DataFrame(items)
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"항목 조회 실패 (SQL 오류): {e}")
            return pd.DataFrame()
    
    def get_my_requests(self, user_id):
        """내 지출요청서 목록 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        request_id,
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
                        attachment_path as attachment
                    FROM expense_requests 
                    WHERE requester_id = %s
                    ORDER BY request_date DESC
                """
                
                cursor.execute(query, (user_id,))
                columns = [desc[0] for desc in cursor.description]
                requests = []
                
                for row in cursor.fetchall():
                    request_dict = dict(zip(columns, row))
                    # 추가 필드 매핑
                    request_dict['vendor'] = ''  # 업체 정보는 별도 처리
                    request_dict['priority'] = 'normal'  # 우선순위 기본값
                    requests.append(request_dict)
                
                return requests
                
        except Exception as e:
            self.log_error(f"내 요청서 조회 중 오류: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM expense_requests")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
    
    def add_expense_request_with_items(self, request_data, items):
        """다중 항목을 포함한 지출요청서 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 총 금액 계산
                total_amount = sum(float(item.get('item_amount', 0)) for item in items)
                
                # request_id 생성 (UUID 기반)
                request_id = str(uuid.uuid4())[:8]
                
                # 메인 지출요청서 추가
                cursor.execute("""
                    INSERT INTO expense_requests (
                        request_id, requester_id, requester_name, expense_title, category,
                        amount, currency, expected_date, expense_description,
                        notes, status, request_date, created_date, updated_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    request_id,
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
                expense_request_id = cursor.fetchone()[0]
                
                # 각 지출 항목 추가
                for item in items:
                    cursor.execute("""
                        INSERT INTO expense_items (
                            request_id, item_description, item_category, item_amount,
                            item_currency, vendor, item_notes, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        expense_request_id,
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
                self.log_info(f"다중 항목 지출요청서 추가 완료: {request_id}")
                return expense_request_id
                
        except Exception as e:
            self.log_error(f"다중 항목 지출요청서 추가 중 오류: {e}")
            return None
    
    def get_expense_items(self, request_id):
        """특정 지출요청서의 항목들 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM expense_items 
                    WHERE request_id = %s
                    ORDER BY created_at ASC
                """, (request_id,))
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item_dict = dict(zip(columns, row))
                    items.append(item_dict)
                
                return items
                
        except Exception as e:
            self.log_error(f"지출 항목 조회 중 오류: {e}")
            return []
    
    def get_expense_categories(self):
        """지출 카테고리 목록 반환"""
        return [
            "교통비", "숙박비", "식비", "회의비", "사무용품", 
            "통신비", "마케팅비", "교육비", "의료비", "기타"
        ]
    
    def get_pending_approvals(self, current_user):
        """현재 사용자에 대한 승인 대기 지출요청서 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 승인 관련 테이블이 있는지 확인하고 없으면 기본 로직으로 처리
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'expense_approvals'
                """)
                
                approval_table_exists = cursor.fetchone() is not None
                
                if approval_table_exists:
                    # 승인 테이블이 있는 경우 - 실제 승인 로직
                    query = """
                        SELECT 
                            ea.approval_id,
                            er.request_id,
                            er.expense_title,
                            er.amount,
                            er.currency,
                            er.expected_date,
                            er.expense_description,
                            er.request_date,
                            er.requester_name,
                            er.category,
                            er.first_approver_name,
                            ea.approval_step,
                            ea.status as approval_status
                        FROM expense_approvals ea
                        JOIN expense_requests er ON ea.request_id = er.request_id
                        WHERE ea.approver_id = %s 
                        AND ea.status = 'pending'
                        ORDER BY ea.created_date ASC
                    """
                    
                    cursor.execute(query, (current_user,))
                    columns = [desc[0] for desc in cursor.description]
                    
                else:
                    # 승인 테이블이 없는 경우 - 기본 로직 (first_approver_id 기반)
                    query = """
                        SELECT 
                            CONCAT('APPR_', er.id) as approval_id,
                            er.request_id,
                            er.expense_title,
                            er.amount,
                            er.currency,
                            er.expected_date,
                            er.expense_description,
                            er.request_date,
                            er.requester_name,
                            er.category,
                            er.first_approver_name,
                            1 as approval_step,
                            'pending' as approval_status
                        FROM expense_requests er
                        WHERE er.first_approver_id = %s 
                        AND er.status = 'pending'
                        ORDER BY er.created_date ASC
                    """
                    
                    cursor.execute(query, (current_user,))
                    columns = [desc[0] for desc in cursor.description]
                
                requests = []
                for row in cursor.fetchall():
                    request_dict = dict(zip(columns, row))
                    requests.append(request_dict)
                
                self.log_info(f"승인 대기 지출요청서 조회 완료: {current_user} - {len(requests)}건")
                return requests
                
        except Exception as e:
            self.log_error(f"승인 대기 지출요청서 조회 중 오류: {e}")
            return []
    
    def process_approval(self, approval_id, approver_id, action, comments=''):
        """승인 처리"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 승인 테이블 존재 확인
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'expense_approvals'
                """)
                
                approval_table_exists = cursor.fetchone() is not None
                
                if approval_table_exists:
                    # 실제 승인 테이블 처리
                    cursor.execute("""
                        UPDATE expense_approvals 
                        SET status = %s, approver_comments = %s, approved_date = CURRENT_TIMESTAMP
                        WHERE approval_id = %s AND approver_id = %s
                    """, (action, comments, approval_id, approver_id))
                    
                    if cursor.rowcount > 0:
                        # 지출요청서 상태도 업데이트
                        cursor.execute("""
                            UPDATE expense_requests 
                            SET status = %s, updated_date = CURRENT_TIMESTAMP
                            WHERE request_id = (
                                SELECT request_id FROM expense_approvals 
                                WHERE approval_id = %s
                            )
                        """, ('approved' if action == '승인' else 'rejected', approval_id))
                        
                        conn.commit()
                        return True, f"지출요청서가 {action}되었습니다."
                    else:
                        return False, "승인 권한이 없거나 이미 처리된 요청입니다."
                        
                else:
                    # 기본 로직 - request_id에서 추출
                    if approval_id.startswith('APPR_'):
                        request_internal_id = approval_id[5:]  # 'APPR_' 제거
                        
                        cursor.execute("""
                            UPDATE expense_requests 
                            SET status = %s, updated_date = CURRENT_TIMESTAMP
                            WHERE id = %s AND first_approver_id = %s
                        """, ('approved' if action == '승인' else 'rejected', request_internal_id, approver_id))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            return True, f"지출요청서가 {action}되었습니다."
                        else:
                            return False, "승인 권한이 없거나 이미 처리된 요청입니다."
                    else:
                        return False, "올바르지 않은 승인 ID입니다."
                
        except Exception as e:
            self.log_error(f"승인 처리 중 오류: {e}")
            return False, f"승인 처리 중 오류가 발생했습니다: {e}"
