"""
SQLite 업무 상태 관리자 - 업무 진행 상태 관리
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

class SQLiteWorkStatusManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업무 상태 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_status (
                        status_id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT,
                        department TEXT,
                        work_date TEXT NOT NULL,
                        work_type TEXT DEFAULT 'office',
                        status TEXT DEFAULT 'working',
                        start_time TEXT,
                        end_time TEXT,
                        break_start_time TEXT,
                        break_end_time TEXT,
                        total_hours REAL DEFAULT 0,
                        break_hours REAL DEFAULT 0,
                        effective_hours REAL DEFAULT 0,
                        location TEXT DEFAULT 'office',
                        description TEXT,
                        notes TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 업무 활동 로그 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_activity_logs (
                        log_id TEXT PRIMARY KEY,
                        status_id TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        activity_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        previous_status TEXT,
                        new_status TEXT,
                        location TEXT,
                        device_info TEXT,
                        ip_address TEXT,
                        notes TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (status_id) REFERENCES work_status (status_id)
                    )
                ''')
                
                # 업무 유형 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_types (
                        type_id TEXT PRIMARY KEY,
                        type_name TEXT NOT NULL,
                        type_name_en TEXT,
                        type_name_vi TEXT,
                        description TEXT,
                        is_remote_allowed INTEGER DEFAULT 0,
                        requires_approval INTEGER DEFAULT 0,
                        color_code TEXT DEFAULT '#0066cc',
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 기본 업무 유형 추가
                default_work_types = [
                    ('office', '사무업무', 'Office Work', 'Công việc văn phòng', '일반적인 사무 업무', 0, 0, '#0066cc', 1),
                    ('remote', '재택근무', 'Remote Work', 'Làm việc từ xa', '원격 근무', 1, 1, '#009900', 1),
                    ('field', '현장업무', 'Field Work', 'Công việc hiện trường', '현장 작업', 0, 1, '#ff6600', 1),
                    ('meeting', '회의', 'Meeting', 'Họp', '회의 참석', 0, 0, '#9900cc', 1),
                    ('training', '교육', 'Training', 'Đào tạo', '교육 및 훈련', 0, 0, '#cc9900', 1),
                    ('business_trip', '출장', 'Business Trip', 'Công tác', '출장 업무', 1, 1, '#cc0000', 1),
                    ('vacation', '휴가', 'Vacation', 'Nghỉ phép', '휴가 중', 0, 1, '#666666', 1),
                    ('sick_leave', '병가', 'Sick Leave', 'Nghỉ ốm', '병가', 0, 1, '#ff9999', 1)
                ]
                
                for work_type in default_work_types:
                    cursor.execute('''
                        INSERT OR IGNORE INTO work_types 
                        (type_id, type_name, type_name_en, type_name_vi, description,
                         is_remote_allowed, requires_approval, color_code, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', work_type)
                
                conn.commit()
                logger.info("업무 상태 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_work_status(self, employee_id=None, work_date=None, status=None, limit=100):
        """업무 상태 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM work_status WHERE 1=1"
                params = []
                
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if work_date:
                    query += " AND work_date = ?"
                    params.append(work_date)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY work_date DESC, start_time DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"업무 상태 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_work_status(self, status_data):
        """업무 상태 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['status_id', 'employee_id', 'work_date']
                for field in required_fields:
                    if field not in status_data or not status_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 근무 시간 계산
                total_hours = 0
                break_hours = 0
                if status_data.get('start_time') and status_data.get('end_time'):
                    start = datetime.fromisoformat(f"{status_data['work_date']}T{status_data['start_time']}")
                    end = datetime.fromisoformat(f"{status_data['work_date']}T{status_data['end_time']}")
                    total_hours = (end - start).total_seconds() / 3600
                
                if status_data.get('break_start_time') and status_data.get('break_end_time'):
                    break_start = datetime.fromisoformat(f"{status_data['work_date']}T{status_data['break_start_time']}")
                    break_end = datetime.fromisoformat(f"{status_data['work_date']}T{status_data['break_end_time']}")
                    break_hours = (break_end - break_start).total_seconds() / 3600
                
                effective_hours = total_hours - break_hours
                
                status_record = {
                    'status_id': status_data['status_id'],
                    'employee_id': status_data['employee_id'],
                    'employee_name': status_data.get('employee_name', ''),
                    'department': status_data.get('department', ''),
                    'work_date': status_data['work_date'],
                    'work_type': status_data.get('work_type', 'office'),
                    'status': status_data.get('status', 'working'),
                    'start_time': status_data.get('start_time', ''),
                    'end_time': status_data.get('end_time', ''),
                    'break_start_time': status_data.get('break_start_time', ''),
                    'break_end_time': status_data.get('break_end_time', ''),
                    'total_hours': total_hours,
                    'break_hours': break_hours,
                    'effective_hours': effective_hours,
                    'location': status_data.get('location', 'office'),
                    'description': status_data.get('description', ''),
                    'notes': status_data.get('notes', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO work_status (
                        status_id, employee_id, employee_name, department, work_date,
                        work_type, status, start_time, end_time, break_start_time,
                        break_end_time, total_hours, break_hours, effective_hours, location,
                        description, notes, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(status_record.values()))
                
                # 활동 로그 추가
                self._add_activity_log(status_data['status_id'], 'STATUS_CREATE', 
                                     '', status_data.get('status', 'working'), 
                                     status_data.get('location', 'office'))
                
                conn.commit()
                logger.info(f"업무 상태 추가 완료: {status_data['status_id']}")
                return True
                
        except Exception as e:
            logger.error(f"업무 상태 추가 실패: {str(e)}")
            return False

    def update_work_status(self, status_id, updates):
        """업무 상태 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 상태 조회
                cursor.execute("SELECT status FROM work_status WHERE status_id = ?", (status_id,))
                result = cursor.fetchone()
                old_status = result[0] if result else ''
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [status_id]
                
                cursor.execute(f'''
                    UPDATE work_status 
                    SET {set_clause}
                    WHERE status_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    # 상태 변경 시 활동 로그 추가
                    if 'status' in updates and updates['status'] != old_status:
                        self._add_activity_log(status_id, 'STATUS_CHANGE', 
                                             old_status, updates['status'],
                                             updates.get('location', 'office'))
                    
                    conn.commit()
                    logger.info(f"업무 상태 수정 완료: {status_id}")
                    return True, "업무 상태가 성공적으로 업데이트되었습니다."
                else:
                    logger.warning(f"수정할 업무 상태 없음: {status_id}")
                    return False, "업데이트할 업무를 찾을 수 없습니다."
                    
        except Exception as e:
            logger.error(f"업무 상태 수정 실패: {str(e)}")
            return False, f"업무 상태 수정 실패: {str(e)}"

    def _add_activity_log(self, status_id, activity_type, previous_status, new_status, location, notes=''):
        """활동 로그 추가 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                log_id = f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{status_id}"
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO work_activity_logs (
                        log_id, status_id, activity_type, activity_time,
                        previous_status, new_status, location, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, status_id, activity_type, current_time,
                      previous_status, new_status, location, notes))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"활동 로그 추가 실패: {str(e)}")

    def get_activity_logs(self, status_id=None, employee_id=None, limit=100):
        """활동 로그 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT al.*, ws.employee_id, ws.employee_name
                    FROM work_activity_logs al
                    LEFT JOIN work_status ws ON al.status_id = ws.status_id
                    WHERE 1=1
                '''
                params = []
                
                if status_id:
                    query += " AND al.status_id = ?"
                    params.append(status_id)
                if employee_id:
                    query += " AND ws.employee_id = ?"
                    params.append(employee_id)
                
                query += " ORDER BY al.activity_time DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"활동 로그 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_work_types(self, is_active=True):
        """업무 유형 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM work_types"
                params = []
                
                if is_active is not None:
                    query += " WHERE is_active = ?"
                    params.append(1 if is_active else 0)
                
                query += " ORDER BY type_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"업무 유형 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_work_statistics(self, employee_id=None, date_from=None, date_to=None):
        """업무 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        employee_id,
                        employee_name,
                        department,
                        work_type,
                        COUNT(*) as work_days,
                        SUM(total_hours) as total_hours,
                        SUM(break_hours) as total_break_hours,
                        SUM(effective_hours) as total_effective_hours,
                        AVG(effective_hours) as avg_daily_hours
                    FROM work_status
                    WHERE 1=1
                '''
                params = []
                
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if date_from:
                    query += " AND work_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND work_date <= ?"
                    params.append(date_to)
                
                query += " GROUP BY employee_id, employee_name, department, work_type"
                query += " ORDER BY employee_name, work_type"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"업무 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, status_csv_path=None, logs_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 업무 상태 데이터 마이그레이션
            if status_csv_path is None:
                status_csv_path = os.path.join("data", "work_status.csv")
            
            if os.path.exists(status_csv_path):
                df = pd.read_csv(status_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        status_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in status_data.items():
                            if pd.isna(value):
                                if key in ['total_hours', 'break_hours', 'effective_hours']:
                                    status_data[key] = 0
                                else:
                                    status_data[key] = ''
                        
                        self.add_work_status(status_data)
                    
                    logger.info(f"업무 상태 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False



    def get_work_status(self, status_id=None, employee_id=None, work_date=None):
        """업무 상태 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM work_status WHERE 1=1"
                params = []
                
                if status_id:
                    query += " AND status_id = ?"
                    params.append(status_id)
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if work_date:
                    query += " AND work_date = ?"
                    params.append(work_date)
                
                query += " ORDER BY work_date DESC, start_time DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"업무 상태 조회 실패: {str(e)}")
            return pd.DataFrame()