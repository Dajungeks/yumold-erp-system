# -*- coding: utf-8 -*-
"""
PostgreSQL 승인 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLApprovalManager(BasePostgreSQLManager):
    """PostgreSQL 승인 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """승인 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 승인 요청 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS approval_requests (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(50) UNIQUE NOT NULL,
                        request_type VARCHAR(50) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        requester_id VARCHAR(50) NOT NULL,
                        requester_name VARCHAR(100),
                        approver_id VARCHAR(50),
                        approver_name VARCHAR(100),
                        amount DECIMAL(15,2),
                        currency VARCHAR(10) DEFAULT 'USD',
                        status VARCHAR(20) DEFAULT 'pending',
                        priority VARCHAR(20) DEFAULT 'normal',
                        requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        approved_date TIMESTAMP,
                        rejected_date TIMESTAMP,
                        approval_notes TEXT,
                        related_document_id VARCHAR(50),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 승인 히스토리 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS approval_history (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(50) NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        action_by VARCHAR(50) NOT NULL,
                        action_by_name VARCHAR(100),
                        action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        FOREIGN KEY (request_id) REFERENCES approval_requests(request_id) ON DELETE CASCADE
                    )
                """)
                
                self.log_info("승인 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"승인 테이블 초기화 실패: {e}")
    
    def create_approval_request(self, request_data):
        """승인 요청 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 요청 ID 생성
                request_id = self._generate_request_id()
                
                cursor.execute("""
                    INSERT INTO approval_requests (
                        request_id, request_type, title, description, requester_id,
                        requester_name, amount, currency, priority, related_document_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    request_id,
                    request_data.get('request_type'),
                    request_data.get('title'),
                    request_data.get('description'),
                    request_data.get('requester_id'),
                    request_data.get('requester_name'),
                    request_data.get('amount'),
                    request_data.get('currency', 'USD'),
                    request_data.get('priority', 'normal'),
                    request_data.get('related_document_id')
                ))
                
                result = cursor.fetchone()
                
                # 히스토리 추가
                cursor.execute("""
                    INSERT INTO approval_history (request_id, action, action_by, action_by_name, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    request_id,
                    'submitted',
                    request_data.get('requester_id'),
                    request_data.get('requester_name'),
                    '승인 요청 제출'
                ))
                
                conn.commit()
                
                return {
                    'success': True,
                    'request_id': request_id,
                    'id': result[0] if result else None
                }
                
        except Exception as e:
            self.log_error(f"승인 요청 생성 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def approve_request(self, request_id, approver_id, approver_name, notes=''):
        """승인 요청 승인"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE approval_requests SET
                        status = 'approved',
                        approver_id = %s,
                        approver_name = %s,
                        approved_date = CURRENT_TIMESTAMP,
                        approval_notes = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE request_id = %s
                """, (approver_id, approver_name, notes, request_id))
                
                # 히스토리 추가
                cursor.execute("""
                    INSERT INTO approval_history (request_id, action, action_by, action_by_name, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request_id, 'approved', approver_id, approver_name, notes))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            self.log_error(f"승인 처리 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def reject_request(self, request_id, approver_id, approver_name, notes=''):
        """승인 요청 거부"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE approval_requests SET
                        status = 'rejected',
                        approver_id = %s,
                        approver_name = %s,
                        rejected_date = CURRENT_TIMESTAMP,
                        approval_notes = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE request_id = %s
                """, (approver_id, approver_name, notes, request_id))
                
                # 히스토리 추가
                cursor.execute("""
                    INSERT INTO approval_history (request_id, action, action_by, action_by_name, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request_id, 'rejected', approver_id, approver_name, notes))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            self.log_error(f"거부 처리 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_pending_requests(self):
        """대기 중인 승인 요청 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM approval_requests 
                    WHERE status = 'pending'
                    ORDER BY requested_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                requests = []
                
                for row in cursor.fetchall():
                    request = dict(zip(columns, row))
                    requests.append(request)
                
                return requests
                
        except Exception as e:
            self.log_error(f"대기 중인 요청 조회 실패: {e}")
            return []
    
    def get_approval_statistics(self):
        """승인 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 총 요청 수
                cursor.execute("SELECT COUNT(*) FROM approval_requests")
                total_requests = cursor.fetchone()[0]
                
                # 상태별 요청 수
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM approval_requests 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                return {
                    'total_requests': total_requests,
                    'pending': status_counts.get('pending', 0),
                    'approved': status_counts.get('approved', 0),
                    'rejected': status_counts.get('rejected', 0)
                }
                
        except Exception as e:
            self.log_error(f"승인 통계 조회 실패: {e}")
            return {
                'total_requests': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0
            }
    
    def _generate_request_id(self):
        """요청 ID 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT request_id FROM approval_requests 
                    WHERE request_id LIKE 'APR%' 
                    ORDER BY request_id DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    last_id = result[0]
                    number = int(last_id[3:]) + 1
                    return f"APR{number:06d}"
                else:
                    return "APR000001"
                    
        except Exception as e:
            self.log_error(f"요청 ID 생성 오류: {e}")
            return f"APR{str(uuid.uuid4())[:6].upper()}"