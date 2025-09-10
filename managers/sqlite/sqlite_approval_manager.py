# -*- coding: utf-8 -*-
"""
SQLite 기반 승인 관리 시스템
지출요청서 승인 처리를 위한 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class SQLiteApprovalManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 승인 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """승인 관련 테이블 초기화"""
        with self.get_connection() as conn:
            # 승인 워크플로우 테이블 (이미 database_manager.py에 정의됨)
            
            # 승인자 정의 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS approval_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    user_name TEXT NOT NULL,
                    position TEXT,
                    department TEXT,
                    approval_level INTEGER DEFAULT 1,
                    max_approval_amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'VND',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 승인 규칙 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS approval_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    category TEXT,
                    min_amount REAL DEFAULT 0,
                    max_amount REAL DEFAULT 999999999,
                    currency TEXT DEFAULT 'VND',
                    required_approval_level INTEGER DEFAULT 1,
                    auto_approve BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("승인 관련 테이블 초기화 완료")
    
    def get_pending_approvals(self, approver_id=None):
        """대기 중인 승인 목록 조회"""
        try:
            with self.get_connection() as conn:
                if approver_id:
                    # 특정 승인자의 대기 승인만
                    query = '''
                        SELECT er.id as request_id, er.requester_id, er.requester_name, 
                               er.expense_title, er.category, er.amount, er.currency, 
                               er.expected_date, er.expense_description, er.notes, er.priority,
                               er.status as request_status, er.request_date,
                               ea.approval_id, ea.approval_step, ea.approver_id, ea.approver_name,
                               ea.approval_date, ea.result, ea.comments, ea.status as approval_status,
                               er.expense_description as description
                        FROM expense_requests er
                        JOIN expense_approvals ea ON CAST(er.id AS TEXT) = ea.request_id
                        WHERE ea.approver_id = ? AND ea.status = '대기'
                        ORDER BY er.request_date ASC
                    '''
                    df = pd.read_sql_query(query, conn, params=[approver_id,])
                else:
                    # 모든 대기 승인
                    query = '''
                        SELECT er.id as request_id, er.requester_id, er.requester_name, 
                               er.expense_title, er.category, er.amount, er.currency, 
                               er.expected_date, er.expense_description, er.notes, er.priority,
                               er.status as request_status, er.request_date,
                               ea.approval_id, ea.approval_step, ea.approver_id, ea.approver_name,
                               ea.approval_date, ea.result, ea.comments, ea.status as approval_status,
                               er.expense_description as description
                        FROM expense_requests er
                        JOIN expense_approvals ea ON CAST(er.id AS TEXT) = ea.request_id
                        WHERE ea.status = '대기'
                        ORDER BY er.request_date ASC
                    '''
                    df = pd.read_sql_query(query, conn)
                
                return df
                
        except Exception as e:
            logger.error(f"대기 승인 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def approve_request(self, request_id, approver_id, approval_step, comments="", decision="승인"):
        """지출요청서 승인 처리"""
        try:
            with self.get_connection() as conn:
                # 현재 승인 정보 조회
                cursor = conn.execute('''
                    SELECT * FROM expense_approvals 
                    WHERE request_id = ? AND approval_step = ? AND approver_id = ?
                ''', (request_id, approval_step, approver_id))
                
                approval = cursor.fetchone()
                if not approval:
                    return False, "승인 정보를 찾을 수 없습니다."
                
                if approval['status'] != '대기':
                    return False, "이미 처리된 승인입니다."
                
                # 승인 상태 업데이트
                conn.execute('''
                    UPDATE expense_approvals 
                    SET status = ?, approval_date = CURRENT_TIMESTAMP, comments = ?
                    WHERE request_id = ? AND approval_step = ? AND approver_id = ?
                ''', (decision, comments, request_id, approval_step, approver_id))
                
                # 지출요청서 상태 업데이트
                if decision == "승인":
                    # 다음 승인 단계가 있는지 확인
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM expense_approvals 
                        WHERE request_id = ? AND approval_step > ? AND status = '대기'
                    ''', (request_id, approval_step))
                    
                    next_count = cursor.fetchone()[0]
                    
                    if next_count == 0:
                        # 모든 승인 완료
                        new_status = "승인완료"
                        conn.execute('''
                            UPDATE expense_requests 
                            SET status = ?, current_step = total_steps
                            WHERE request_id = ?
                        ''', (new_status, request_id))
                    else:
                        # 다음 단계로 진행
                        conn.execute('''
                            UPDATE expense_requests 
                            SET current_step = current_step + 1
                            WHERE request_id = ?
                        ''', (request_id,))
                        
                elif decision == "반려":
                    # 반려 처리
                    conn.execute('''
                        UPDATE expense_requests 
                        SET status = '반려'
                        WHERE request_id = ?
                    ''', (request_id,))
                    
                    # 나머지 승인 단계도 반려로 처리
                    conn.execute('''
                        UPDATE expense_approvals 
                        SET status = '반려', approval_date = CURRENT_TIMESTAMP
                        WHERE request_id = ? AND status = '대기'
                    ''', (request_id,))
                
                conn.commit()
                logger.info(f"승인 처리 완료: {request_id} - {decision}")
                return True, f"승인이 {decision}되었습니다."
                
        except Exception as e:
            logger.error(f"승인 처리 오류: {str(e)}")
            return False, f"승인 처리 중 오류가 발생했습니다: {str(e)}"
    
    def get_approval_history(self, request_id=None, approver_id=None):
        """승인 히스토리 조회"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT ea.*, er.expense_title, er.amount, er.requester_name
                    FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = er.id
                '''
                
                conditions = []
                params = []
                
                if request_id:
                    conditions.append("ea.request_id = ?")
                    params.append(request_id)
                
                if approver_id:
                    conditions.append("ea.approver_id = ?")
                    params.append(approver_id)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY ea.approval_date DESC"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                return df
                
        except Exception as e:
            logger.error(f"승인 히스토리 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def add_approval_user(self, user_data):
        """승인자 등록"""
        try:
            with self.get_connection() as conn:
                # 중복 확인
                cursor = conn.execute('SELECT COUNT(*) FROM approval_users WHERE user_id = ?', 
                                    (user_data['user_id'],))
                
                if cursor.fetchone()[0] > 0:
                    return False, "이미 등록된 승인자입니다."
                
                # 승인자 등록
                conn.execute('''
                    INSERT INTO approval_users (
                        user_id, user_name, position, department, approval_level, 
                        max_approval_amount, currency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data['user_name'],
                    user_data.get('position', ''),
                    user_data.get('department', ''),
                    int(user_data.get('approval_level', 1)),
                    float(user_data.get('max_approval_amount', 0)),
                    user_data.get('currency', 'VND')
                ))
                
                conn.commit()
                logger.info(f"승인자 등록 성공: {user_data['user_id']}")
                return True, "승인자가 성공적으로 등록되었습니다."
                
        except Exception as e:
            logger.error(f"승인자 등록 오류: {str(e)}")
            return False, f"승인자 등록 중 오류가 발생했습니다: {str(e)}"
    
    def get_approvers(self, approval_level=None, active_only=True):
        """승인자 목록 조회"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT * FROM approval_users
                '''
                
                conditions = []
                params = []
                
                if approval_level:
                    conditions.append("approval_level >= ?")
                    params.append(approval_level)
                
                if active_only:
                    conditions.append("is_active = TRUE")
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY approval_level DESC, user_name"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                return df
                
        except Exception as e:
            logger.error(f"승인자 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_all_approvals(self):
        """모든 승인 내역 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT er.id as request_id, er.requester_id, er.requester_name, 
                           er.expense_title, er.category, er.amount, er.currency, 
                           er.expected_date, er.expense_description, er.notes, er.priority,
                           er.status as request_status, er.request_date,
                           ea.approval_id, ea.approval_step, ea.approver_id, ea.approver_name,
                           ea.approval_date, ea.result, ea.comments, 
                           ea.created_date as approval_created_date, ea.status as approval_status,
                           'expense' as request_type, er.expense_description as description,
                           CASE 
                               WHEN ea.result = '승인' THEN 'approved'
                               WHEN ea.result = '반려' THEN 'rejected' 
                               ELSE 'pending'
                           END as status
                    FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = CAST(er.id AS TEXT)
                    ORDER BY ea.created_date DESC
                '''
                df = pd.read_sql_query(query, conn)
                return df.to_dict('records') if not df.empty else []
                
        except Exception as e:
            logger.error(f"전체 승인 조회 오류: {str(e)}")
            return []
    
    def get_approvals_by_requester(self, requester_id):
        """요청자별 승인 내역 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT er.id as request_id, er.requester_id, er.requester_name, 
                           er.expense_title, er.category, er.amount, er.currency, 
                           er.expected_date, er.expense_description, er.notes, er.priority,
                           er.status as request_status, er.request_date,
                           ea.approval_id, ea.approval_step, ea.approver_id, ea.approver_name,
                           ea.approval_date, ea.result, ea.comments, 
                           ea.created_date as approval_created_date, ea.status as approval_status,
                           'expense' as request_type, er.expense_description as description,
                           CASE 
                               WHEN ea.result = '승인' THEN 'approved'
                               WHEN ea.result = '반려' THEN 'rejected' 
                               ELSE 'pending'
                           END as status
                    FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = CAST(er.id AS TEXT)
                    WHERE er.requester_id = ?
                    ORDER BY ea.created_date DESC
                '''
                df = pd.read_sql_query(query, conn, params=[requester_id])
                return df
                
        except Exception as e:
            logger.error(f"요청자별 승인 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_suitable_approvers(self, amount, currency='VND', category=""):
        """금액과 카테고리에 적합한 승인자 찾기"""
        try:
            with self.get_connection() as conn:
                # 금액에 따른 승인자 조회
                query = '''
                    SELECT * FROM approval_users 
                    WHERE is_active = TRUE 
                    AND (max_approval_amount >= ? OR max_approval_amount = 0)
                    AND currency = ?
                    ORDER BY approval_level DESC, max_approval_amount ASC
                '''
                
                df = pd.read_sql_query(query, conn, params=[amount, currency])
                return df
                
        except Exception as e:
            logger.error(f"적합한 승인자 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def add_approval_rule(self, rule_data):
        """승인 규칙 추가"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO approval_rules (
                        rule_name, category, min_amount, max_amount, currency,
                        required_approval_level, auto_approve
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule_data['rule_name'],
                    rule_data.get('category', ''),
                    float(rule_data.get('min_amount', 0)),
                    float(rule_data.get('max_amount', 999999999)),
                    rule_data.get('currency', 'VND'),
                    int(rule_data.get('required_approval_level', 1)),
                    bool(rule_data.get('auto_approve', False))
                ))
                
                conn.commit()
                logger.info(f"승인 규칙 추가 성공: {rule_data['rule_name']}")
                return True, "승인 규칙이 성공적으로 추가되었습니다."
                
        except Exception as e:
            logger.error(f"승인 규칙 추가 오류: {str(e)}")
            return False, f"승인 규칙 추가 중 오류가 발생했습니다: {str(e)}"
    
    def get_approval_rules(self, category="", active_only=True):
        """승인 규칙 조회"""
        try:
            with self.get_connection() as conn:
                base_query = "SELECT * FROM approval_rules"
                
                conditions = []
                params = []
                
                if category:
                    conditions.append("category = ?")
                    params.append(category)
                
                if active_only:
                    conditions.append("is_active = TRUE")
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY min_amount"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                return df
                
        except Exception as e:
            logger.error(f"승인 규칙 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_approval_statistics(self, start_date=None, end_date=None):
        """승인 통계 정보"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT 
                        COUNT(*) as total_approvals,
                        SUM(CASE WHEN status = '승인' THEN 1 ELSE 0 END) as approved_count,
                        SUM(CASE WHEN status = '반려' THEN 1 ELSE 0 END) as rejected_count,
                        SUM(CASE WHEN status = '대기' THEN 1 ELSE 0 END) as pending_count,
                        AVG(CASE WHEN status = '승인' THEN julianday(approval_date) - julianday(created_date) END) as avg_approval_days
                    FROM expense_approvals
                '''
                
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("DATE(created_date) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(created_date) <= ?")
                    params.append(end_date)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"승인 통계 조회 오류: {str(e)}")
            return {}
    
    def update_approver(self, user_id, user_data):
        """승인자 정보 업데이트"""
        try:
            with self.get_connection() as conn:
                # 업데이트할 필드들 동적 생성
                fields = []
                values = []
                
                for key, value in user_data.items():
                    if key != 'user_id':  # ID는 업데이트하지 않음
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False, "업데이트할 정보가 없습니다."
                
                # 업데이트 쿼리 실행
                values.append(user_id)  # WHERE 절용
                query = f"UPDATE approval_users SET {', '.join(fields)}, updated_date = CURRENT_TIMESTAMP WHERE user_id = ?"
                
                cursor = conn.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"승인자 업데이트 성공: {user_id}")
                    return True, "승인자 정보가 성공적으로 업데이트되었습니다."
                else:
                    return False, "해당 승인자를 찾을 수 없습니다."
                    
        except Exception as e:
            logger.error(f"승인자 업데이트 오류: {str(e)}")
            return False, f"승인자 업데이트 중 오류가 발생했습니다: {str(e)}"

    def get_requests_by_requester(self, requester_id, status=None):
        """요청자별 요청 내역 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT ea.*, er.expense_title, er.amount, er.requester_name, er.expense_description
                    FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = CAST(er.id AS TEXT)
                    WHERE er.requester_id = ?
                '''
                params = [requester_id]
                
                if status:
                    query += " AND ea.status = ?"
                    params.append(status)
                
                query += " ORDER BY ea.created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                return df
                
        except Exception as e:
            logger.error(f"요청자별 요청 내역 조회 실패: {str(e)}")
            return pd.DataFrame()

    def find_approvers_for_expense(self, amount, currency='VND'):
        """지출 요청에 대한 승인자 찾기"""
        try:
            with self.get_connection() as conn:
                # 법인장 레벨 승인자 찾기 (일반적으로 가장 높은 승인 권한)
                query = '''
                    SELECT * FROM approval_users 
                    WHERE is_active = TRUE 
                    AND approval_level >= 3
                    AND (max_approval_amount >= ? OR max_approval_amount = 0)
                    ORDER BY approval_level DESC
                    LIMIT 5
                '''
                
                df = pd.read_sql_query(query, conn, params=[amount,])
                
                if df.empty:
                    # 승인자가 없는 경우 기본 승인자 데이터 생성
                    default_approvers = [{
                        'user_id': 'CEO001',
                        'user_name': '법인장',
                        'position': '대표이사',
                        'department': '경영진',
                        'approval_level': 5,
                        'max_approval_amount': 0,  # 무제한
                        'currency': currency
                    }]
                    
                    # 기본 승인자 등록
                    for approver in default_approvers:
                        self.add_approval_user(approver)
                    
                    # 다시 조회
                    df = pd.read_sql_query(query, conn, params=[amount,])
                
                return df
                
        except Exception as e:
            logger.error(f"지출 승인자 찾기 실패: {str(e)}")
            return pd.DataFrame()

    def get_pending_requests(self, approver_id=None, request_type=None):
        """승인 대기 요청 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                query = '''
                    SELECT er.id as request_id, er.requester_id, er.requester_name, 
                           er.expense_title, er.category, er.amount, er.currency, 
                           er.expected_date, er.expense_description, er.notes, er.priority,
                           er.status as request_status, er.request_date,
                           ea.approval_id, ea.approval_step, ea.approver_id, ea.approver_name,
                           ea.approval_date, ea.result, ea.comments, ea.status as approval_status,
                           'expense' as request_type, er.expense_description as description,
                           ea.status as status
                    FROM expense_approvals ea
                    JOIN expense_requests er ON ea.request_id = CAST(er.id AS TEXT)
                    WHERE ea.status = 'pending'
                '''
                params = []
                
                if approver_id:
                    query += " AND ea.approver_id = ?"
                    params.append(approver_id)
                if request_type:
                    # request_type이 'expense'인 경우는 모든 지출요청서를 의미하므로 조건 추가하지 않음
                    if request_type != 'expense':
                        query += " AND er.category = ?"
                        params.append(request_type)
                
                query += " ORDER BY ea.created_date ASC"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                return df
                
        except Exception as e:
            logger.error(f"승인 대기 요청 조회 실패: {str(e)}")
            return pd.DataFrame()