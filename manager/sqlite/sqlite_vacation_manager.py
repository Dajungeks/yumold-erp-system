"""
SQLite 휴가 관리자 - 휴가 신청, 승인, 관리
CSV 기반에서 SQLite 기반으로 전환
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteVacationManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 휴가 신청 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vacation_requests (
                        request_id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT,
                        department TEXT,
                        position TEXT,
                        vacation_type TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        total_days INTEGER DEFAULT 0,
                        business_days INTEGER DEFAULT 0,
                        reason TEXT,
                        emergency_contact TEXT,
                        emergency_phone TEXT,
                        handover_person TEXT,
                        handover_details TEXT,
                        status TEXT DEFAULT 'pending',
                        approver_id TEXT,
                        approver_name TEXT,
                        approval_date TEXT,
                        approval_comments TEXT,
                        rejection_reason TEXT,
                        submitted_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 휴가 잔여일수 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vacation_balances (
                        balance_id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        vacation_type TEXT NOT NULL,
                        allocated_days REAL DEFAULT 0,
                        used_days REAL DEFAULT 0,
                        remaining_days REAL DEFAULT 0,
                        carried_over REAL DEFAULT 0,
                        expires_date TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(employee_id, year, vacation_type)
                    )
                ''')
                
                # 휴가 유형 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vacation_types (
                        type_id TEXT PRIMARY KEY,
                        type_name TEXT NOT NULL,
                        type_name_en TEXT,
                        type_name_vi TEXT,
                        description TEXT,
                        max_days_per_year REAL DEFAULT 0,
                        max_consecutive_days INTEGER DEFAULT 0,
                        requires_approval INTEGER DEFAULT 1,
                        advance_notice_days INTEGER DEFAULT 1,
                        can_carry_over INTEGER DEFAULT 0,
                        is_paid INTEGER DEFAULT 1,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 기본 휴가 유형 추가
                default_types = [
                    ('ANNUAL', '연차', 'Annual Leave', 'Nghỉ phép năm', '연간 유급휴가', 15, 10, 1, 3, 1, 1, 1),
                    ('SICK', '병가', 'Sick Leave', 'Nghỉ ốm', '질병으로 인한 휴가', 30, 30, 1, 0, 0, 1, 1),
                    ('PERSONAL', '개인사유', 'Personal Leave', 'Nghỉ cá nhân', '개인적 사유로 인한 휴가', 5, 3, 1, 1, 0, 0, 1),
                    ('MATERNITY', '출산휴가', 'Maternity Leave', 'Nghỉ sinh', '출산 및 육아휴가', 90, 90, 1, 30, 0, 1, 1),
                    ('EMERGENCY', '긴급사유', 'Emergency Leave', 'Nghỉ khẩn cấp', '응급상황으로 인한 휴가', 3, 3, 1, 0, 0, 1, 1)
                ]
                
                cursor.executemany('''
                    INSERT OR IGNORE INTO vacation_types 
                    (type_id, type_name, type_name_en, type_name_vi, description, max_days_per_year, 
                     max_consecutive_days, requires_approval, advance_notice_days, can_carry_over, is_paid, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_types)
                
                conn.commit()
                logger.info("휴가 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_vacation_requests(self, employee_id=None, status=None, start_date=None, end_date=None):
        """휴가 신청 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM vacation_requests WHERE 1=1"
                params = []
                
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if start_date:
                    query += " AND start_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND end_date <= ?"
                    params.append(end_date)
                
                query += " ORDER BY submitted_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"휴가 신청 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_vacation_request(self, request_data):
        """휴가 신청 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['request_id', 'employee_id', 'vacation_type', 'start_date', 'end_date']
                for field in required_fields:
                    if field not in request_data or not request_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 휴가 일수 계산
                start_date = datetime.strptime(request_data['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(request_data['end_date'], '%Y-%m-%d')
                total_days = (end_date - start_date).days + 1
                
                # 평일 계산 (간단한 계산, 실제로는 공휴일도 고려해야 함)
                business_days = 0
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # 월-금
                        business_days += 1
                    current_date += timedelta(days=1)
                
                request_record = {
                    'request_id': request_data['request_id'],
                    'employee_id': request_data['employee_id'],
                    'employee_name': request_data.get('employee_name', ''),
                    'department': request_data.get('department', ''),
                    'position': request_data.get('position', ''),
                    'vacation_type': request_data['vacation_type'],
                    'start_date': request_data['start_date'],
                    'end_date': request_data['end_date'],
                    'total_days': total_days,
                    'business_days': business_days,
                    'reason': request_data.get('reason', ''),
                    'emergency_contact': request_data.get('emergency_contact', ''),
                    'emergency_phone': request_data.get('emergency_phone', ''),
                    'handover_person': request_data.get('handover_person', ''),
                    'handover_details': request_data.get('handover_details', ''),
                    'status': request_data.get('status', 'pending'),
                    'approver_id': request_data.get('approver_id', ''),
                    'approver_name': request_data.get('approver_name', ''),
                    'approval_date': request_data.get('approval_date', ''),
                    'approval_comments': request_data.get('approval_comments', ''),
                    'rejection_reason': request_data.get('rejection_reason', ''),
                    'submitted_date': current_time,
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO vacation_requests (
                        request_id, employee_id, employee_name, department, position,
                        vacation_type, start_date, end_date, total_days, business_days,
                        reason, emergency_contact, emergency_phone, handover_person, handover_details,
                        status, approver_id, approver_name, approval_date, approval_comments,
                        rejection_reason, submitted_date, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(request_record.values()))
                
                conn.commit()
                logger.info(f"휴가 신청 추가 완료: {request_data['request_id']}")
                return True
                
        except Exception as e:
            logger.error(f"휴가 신청 추가 실패: {str(e)}")
            return False

    def approve_vacation_request(self, request_id, approver_id, approver_name, comments=''):
        """휴가 신청 승인"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 휴가 신청 정보 조회
                cursor.execute('''
                    SELECT employee_id, vacation_type, business_days, start_date 
                    FROM vacation_requests 
                    WHERE request_id = ?
                ''', (request_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"휴가 신청을 찾을 수 없음: {request_id}")
                    return False
                
                employee_id, vacation_type, business_days, start_date = result
                year = datetime.strptime(start_date, '%Y-%m-%d').year
                
                # 휴가 신청 승인 처리
                cursor.execute('''
                    UPDATE vacation_requests 
                    SET status = 'approved', 
                        approver_id = ?, 
                        approver_name = ?, 
                        approval_date = ?, 
                        approval_comments = ?,
                        updated_date = ?
                    WHERE request_id = ?
                ''', (approver_id, approver_name, datetime.now().isoformat(), 
                      comments, datetime.now().isoformat(), request_id))
                
                # 휴가 잔여일수 업데이트
                self._update_vacation_balance(employee_id, year, vacation_type, business_days)
                
                conn.commit()
                logger.info(f"휴가 신청 승인 완료: {request_id}")
                return True
                
        except Exception as e:
            logger.error(f"휴가 신청 승인 실패: {str(e)}")
            return False

    def reject_vacation_request(self, request_id, approver_id, approver_name, reason=''):
        """휴가 신청 거부"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE vacation_requests 
                    SET status = 'rejected', 
                        approver_id = ?, 
                        approver_name = ?, 
                        approval_date = ?, 
                        rejection_reason = ?,
                        updated_date = ?
                    WHERE request_id = ?
                ''', (approver_id, approver_name, datetime.now().isoformat(), 
                      reason, datetime.now().isoformat(), request_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"휴가 신청 거부 완료: {request_id}")
                    return True
                else:
                    logger.warning(f"거부할 휴가 신청 없음: {request_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"휴가 신청 거부 실패: {str(e)}")
            return False

    def get_vacation_balances(self, employee_id=None, year=None):
        """휴가 잔여일수 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM vacation_balances WHERE 1=1"
                params = []
                
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if year:
                    query += " AND year = ?"
                    params.append(year)
                
                query += " ORDER BY year DESC, vacation_type"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"휴가 잔여일수 조회 실패: {str(e)}")
            return pd.DataFrame()

    def _update_vacation_balance(self, employee_id, year, vacation_type, used_days):
        """휴가 잔여일수 업데이트 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 잔여일수 조회
                cursor.execute('''
                    SELECT allocated_days, used_days, remaining_days 
                    FROM vacation_balances 
                    WHERE employee_id = ? AND year = ? AND vacation_type = ?
                ''', (employee_id, year, vacation_type))
                
                result = cursor.fetchone()
                
                if result:
                    # 기존 레코드 업데이트
                    allocated_days, current_used, current_remaining = result
                    new_used = current_used + used_days
                    new_remaining = allocated_days - new_used
                    
                    cursor.execute('''
                        UPDATE vacation_balances 
                        SET used_days = ?, remaining_days = ?, updated_date = ?
                        WHERE employee_id = ? AND year = ? AND vacation_type = ?
                    ''', (new_used, new_remaining, datetime.now().isoformat(), 
                          employee_id, year, vacation_type))
                else:
                    # 새 레코드 생성 (기본 할당일수는 휴가 유형에 따라)
                    cursor.execute('''
                        SELECT max_days_per_year FROM vacation_types WHERE type_id = ?
                    ''', (vacation_type,))
                    
                    type_result = cursor.fetchone()
                    allocated_days = type_result[0] if type_result else 15  # 기본값
                    
                    balance_id = f"{employee_id}_{year}_{vacation_type}"
                    remaining_days = allocated_days - used_days
                    
                    cursor.execute('''
                        INSERT INTO vacation_balances 
                        (balance_id, employee_id, year, vacation_type, allocated_days, 
                         used_days, remaining_days, created_date, updated_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (balance_id, employee_id, year, vacation_type, allocated_days,
                          used_days, remaining_days, datetime.now().isoformat(), 
                          datetime.now().isoformat()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"휴가 잔여일수 업데이트 실패: {str(e)}")

    def get_vacation_types(self, is_active=True):
        """휴가 유형 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM vacation_types"
                params = []
                
                if is_active is not None:
                    query += " WHERE is_active = ?"
                    params.append(1 if is_active else 0)
                
                query += " ORDER BY type_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"휴가 유형 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_vacation_statistics(self, year=None, department=None):
        """휴가 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        department,
                        vacation_type,
                        status,
                        COUNT(*) as count,
                        SUM(business_days) as total_days,
                        AVG(business_days) as avg_days
                    FROM vacation_requests
                    WHERE 1=1
                '''
                params = []
                
                if year:
                    query += " AND strftime('%Y', start_date) = ?"
                    params.append(str(year))
                if department:
                    query += " AND department = ?"
                    params.append(department)
                
                query += " GROUP BY department, vacation_type, status ORDER BY department, vacation_type"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"휴가 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_vacations_by_employee(self, employee_id, year=None, status=None):
        """직원별 휴가 내역 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM vacation_requests WHERE employee_id = ?"
                params = [employee_id]
                
                if year:
                    query += " AND strftime('%Y', start_date) = ?"
                    params.append(str(year))
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY submitted_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"직원별 휴가 내역 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_vacation_summary(self, employee_id=None, year=None):
        """휴가 요약 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if employee_id:
                    # 특정 직원의 휴가 요약
                    query = '''
                        SELECT 
                            employee_id,
                            employee_name,
                            COUNT(*) as total_requests,
                            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_requests,
                            SUM(CASE WHEN status = 'approved' THEN total_days ELSE 0 END) as total_used_days,
                            SUM(CASE WHEN status = 'pending' THEN total_days ELSE 0 END) as pending_days
                        FROM vacation_requests 
                        WHERE employee_id = ?
                    '''
                    params = [employee_id]
                    
                    if year:
                        query += " AND strftime('%Y', start_date) = ?"
                        params.append(str(year))
                    
                    query += " GROUP BY employee_id, employee_name"
                    
                else:
                    # 전체 직원 휴가 요약
                    query = '''
                        SELECT 
                            employee_id,
                            employee_name,
                            COUNT(*) as total_requests,
                            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_requests,
                            SUM(CASE WHEN status = 'approved' THEN total_days ELSE 0 END) as total_used_days,
                            SUM(CASE WHEN status = 'pending' THEN total_days ELSE 0 END) as pending_days
                        FROM vacation_requests
                    '''
                    params = []
                    
                    if year:
                        query += " WHERE strftime('%Y', start_date) = ?"
                        params.append(str(year))
                    
                    query += " GROUP BY employee_id, employee_name ORDER BY employee_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                # 휴가 잔여일수 계산 (기본 연차 15일 가정)
                if not df.empty:
                    df['remaining_days'] = 15 - df['total_used_days'].fillna(0)
                
                return df
                
        except Exception as e:
            logger.error(f"휴가 요약 정보 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, requests_csv_path=None, balances_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 휴가 신청 데이터 마이그레이션
            if requests_csv_path is None:
                requests_csv_path = os.path.join("data", "vacation_requests.csv")
            
            if os.path.exists(requests_csv_path):
                df = pd.read_csv(requests_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        request_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in request_data.items():
                            if pd.isna(value):
                                if key in ['total_days', 'business_days']:
                                    request_data[key] = 0
                                else:
                                    request_data[key] = ''
                        
                        self.add_vacation_request(request_data)
                    
                    logger.info(f"휴가 신청 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 휴가 잔여일수 데이터 마이그레이션
            if balances_csv_path is None:
                balances_csv_path = os.path.join("data", "vacation_balances.csv")
            
            if os.path.exists(balances_csv_path):
                df = pd.read_csv(balances_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        for _, row in df.iterrows():
                            balance_data = row.to_dict()
                            # NaN 값 처리
                            for key, value in balance_data.items():
                                if pd.isna(value):
                                    if key in ['year', 'allocated_days', 'used_days', 'remaining_days', 'carried_over']:
                                        balance_data[key] = 0
                                    else:
                                        balance_data[key] = ''
                            
                            try:
                                cursor.execute('''
                                    INSERT OR REPLACE INTO vacation_balances
                                    (balance_id, employee_id, year, vacation_type, allocated_days,
                                     used_days, remaining_days, carried_over, expires_date)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    balance_data.get('balance_id', f"{balance_data.get('employee_id', '')}_{balance_data.get('year', 0)}_{balance_data.get('vacation_type', '')}"),
                                    balance_data.get('employee_id', ''),
                                    balance_data.get('year', 0),
                                    balance_data.get('vacation_type', ''),
                                    balance_data.get('allocated_days', 0),
                                    balance_data.get('used_days', 0),
                                    balance_data.get('remaining_days', 0),
                                    balance_data.get('carried_over', 0),
                                    balance_data.get('expires_date', '')
                                ))
                            except sqlite3.IntegrityError:
                                # 중복 데이터 스킵
                                pass
                        
                        conn.commit()
                    
                    logger.info(f"휴가 잔여일수 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False