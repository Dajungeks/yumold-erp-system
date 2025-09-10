# -*- coding: utf-8 -*-
"""
SQLite 기반 지출요청서 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class SQLiteExpenseManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 지출요청서 매니저 초기화"""
        self.db_path = db_path
        
        # 지출 카테고리 정의
        self.expense_categories = [
            '업무용품', '출장비', '교육비', '회식비', 
            '시설비', '마케팅비', '기타'
        ]
        
        # 승인 상태 정의
        self.approval_statuses = [
            '대기', '진행중', '승인', '반려', '완료'
        ]
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def create_expense_request(self, request_data, approval_settings):
        """새로운 지출요청서를 생성합니다."""
        try:
            with self.get_connection() as conn:
                # 요청서 ID 생성
                request_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 요청서 데이터 삽입
                conn.execute('''
                    INSERT INTO expense_requests (
                        request_id, requester_id, requester_name, request_date,
                        expense_title, expense_description, category, amount,
                        currency, expected_date, status, current_step, total_steps,
                        attachment_path, notes, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id,
                    request_data.get('requester_id', ''),
                    request_data.get('requester_name', ''),
                    datetime.now().strftime('%Y-%m-%d'),
                    request_data.get('expense_title', ''),
                    request_data.get('expense_description', ''),
                    request_data.get('category', ''),
                    float(request_data.get('amount', 0)),
                    request_data.get('currency', 'VND'),
                    request_data.get('expected_date', ''),
                    '대기',
                    1,
                    len(approval_settings),
                    request_data.get('attachment_path', ''),
                    request_data.get('notes', ''),
                    current_time,
                    current_time
                ))
                
                # 승인 설정 저장
                for step, approver_info in enumerate(approval_settings, 1):
                    approval_id = f"APP{datetime.now().strftime('%Y%m%d%H%M%S')}{step}"
                    conn.execute('''
                        INSERT INTO expense_approvals (
                            approval_id, request_id, approval_step, approver_id,
                            approver_name, approval_order, result, comments, is_required
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        approval_id,
                        request_id,
                        step,
                        approver_info.get('approver_id', ''),
                        approver_info.get('approver_name', ''),
                        step,
                        '대기',
                        '',
                        approver_info.get('is_required', True)
                    ))
                
                conn.commit()
                return True, f"지출요청서가 성공적으로 등록되었습니다. (요청번호: {request_id})"
                
        except Exception as e:
            logger.error(f"지출요청서 생성 오류: {e}")
            return False, f"지출요청서 등록 중 오류: {e}"
    
    def get_my_requests(self, user_id):
        """특정 사용자의 지출요청서 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        request_id, requester_id, requester_name, request_date,
                        expense_title, expense_description, category, amount, currency,
                        expected_date, status, current_step, total_steps, 
                        attachment_path, notes, created_date, updated_date
                    FROM expense_requests 
                    WHERE requester_id = ?
                    ORDER BY created_date DESC
                ''', (str(user_id),))
                
                results = cursor.fetchall()
                requests_list = []
                
                for row in results:
                    request_dict = dict(row)
                    # expense_type 필드 추가 (페이지에서 사용)
                    request_dict['expense_type'] = request_dict.get('expense_title', 'N/A')
                    requests_list.append(request_dict)
                
                return requests_list
                
        except Exception as e:
            logger.error(f"내 요청서 조회 오류: {e}")
            return []
    
    def get_pending_approvals(self, approver_id):
        """특정 승인자의 승인 대기 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        a.approval_id,
                        a.request_id,
                        a.approval_step,
                        r.expense_title,
                        r.expense_description,
                        r.requester_name,
                        r.request_date,
                        r.amount,
                        r.currency,
                        r.expected_date,
                        r.category,
                        r.notes
                    FROM expense_approvals a
                    JOIN expense_requests r ON a.request_id = r.request_id
                    WHERE a.approver_id = ? AND a.result = '대기'
                    ORDER BY r.created_date DESC
                ''', (str(approver_id),))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"승인 대기 목록 조회 오류: {e}")
            return []
    
    def process_approval(self, approval_id, approver_id, result, comments=""):
        """승인을 처리합니다."""
        try:
            with self.get_connection() as conn:
                # 승인 정보 업데이트
                conn.execute('''
                    UPDATE expense_approvals 
                    SET result = ?, comments = ?, approval_date = ?
                    WHERE approval_id = ? AND approver_id = ?
                ''', (
                    result,
                    comments,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    approval_id,
                    str(approver_id)
                ))
                
                # 요청서 상태 업데이트
                cursor = conn.execute('''
                    SELECT request_id FROM expense_approvals 
                    WHERE approval_id = ?
                ''', (approval_id,))
                
                request_row = cursor.fetchone()
                if request_row:
                    request_id = request_row['request_id']
                    
                    # 요청서 상태를 승인/반려에 따라 업데이트
                    new_status = result  # '승인' 또는 '반려'
                    conn.execute('''
                        UPDATE expense_requests 
                        SET status = ?, updated_date = ?
                        WHERE request_id = ?
                    ''', (
                        new_status,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        request_id
                    ))
                
                conn.commit()
                return True, f"승인 처리가 완료되었습니다: {result}"
                
        except Exception as e:
            logger.error(f"승인 처리 오류: {e}")
            return False, f"승인 처리 중 오류: {e}"
    
    def get_request_by_id(self, request_id):
        """특정 요청서 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM expense_requests WHERE request_id = ?
                ''', (request_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"요청서 조회 오류: {e}")
            return None
    
    def get_requests_by_requester(self, requester_id):
        """특정 요청자의 요청서 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM expense_requests 
                    WHERE requester_id = ?
                    ORDER BY created_date DESC
                ''', (str(requester_id),))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"요청자별 요청서 조회 오류: {e}")
            return []
    
    def get_all_requests(self):
        """모든 요청서를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM expense_requests 
                    ORDER BY created_date DESC
                ''')
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"전체 요청서 조회 오류: {e}")
            return []