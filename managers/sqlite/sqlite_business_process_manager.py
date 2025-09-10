"""
SQLite 업무 프로세스 관리자 - 업무 워크플로우, 프로세스 관리
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

class SQLiteBusinessProcessManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업무 프로세스 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS business_processes (
                        process_id TEXT PRIMARY KEY,
                        process_name TEXT NOT NULL,
                        process_type TEXT DEFAULT 'general',
                        description TEXT,
                        owner TEXT,
                        department TEXT,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'active',
                        start_date TEXT,
                        end_date TEXT,
                        estimated_hours REAL DEFAULT 0,
                        actual_hours REAL DEFAULT 0,
                        completion_rate REAL DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 프로세스 단계 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS process_steps (
                        step_id TEXT PRIMARY KEY,
                        process_id TEXT NOT NULL,
                        step_name TEXT NOT NULL,
                        step_order INTEGER DEFAULT 1,
                        description TEXT,
                        assignee TEXT,
                        status TEXT DEFAULT 'pending',
                        estimated_hours REAL DEFAULT 0,
                        actual_hours REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        dependencies TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (process_id) REFERENCES business_processes (process_id)
                    )
                ''')
                
                # 프로세스 로그 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS process_logs (
                        log_id TEXT PRIMARY KEY,
                        process_id TEXT NOT NULL,
                        step_id TEXT,
                        action TEXT NOT NULL,
                        user_id TEXT,
                        message TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (process_id) REFERENCES business_processes (process_id),
                        FOREIGN KEY (step_id) REFERENCES process_steps (step_id)
                    )
                ''')
                
                conn.commit()
                logger.info("업무 프로세스 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_processes(self, status=None, owner=None, department=None):
        """업무 프로세스 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM business_processes WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if owner:
                    query += " AND owner = ?"
                    params.append(owner)
                if department:
                    query += " AND department = ?"
                    params.append(department)
                
                query += " ORDER BY created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"프로세스 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_process(self, process_data):
        """업무 프로세스 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                if 'process_id' not in process_data or not process_data['process_id']:
                    raise ValueError("프로세스 ID는 필수입니다")
                if 'process_name' not in process_data or not process_data['process_name']:
                    raise ValueError("프로세스 이름은 필수입니다")
                
                current_time = datetime.now().isoformat()
                
                process_record = {
                    'process_id': process_data['process_id'],
                    'process_name': process_data['process_name'],
                    'process_type': process_data.get('process_type', 'general'),
                    'description': process_data.get('description', ''),
                    'owner': process_data.get('owner', ''),
                    'department': process_data.get('department', ''),
                    'priority': process_data.get('priority', 'medium'),
                    'status': process_data.get('status', 'active'),
                    'start_date': process_data.get('start_date', ''),
                    'end_date': process_data.get('end_date', ''),
                    'estimated_hours': process_data.get('estimated_hours', 0),
                    'actual_hours': process_data.get('actual_hours', 0),
                    'completion_rate': process_data.get('completion_rate', 0),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO business_processes (
                        process_id, process_name, process_type, description, owner,
                        department, priority, status, start_date, end_date,
                        estimated_hours, actual_hours, completion_rate,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(process_record.values()))
                
                conn.commit()
                
                # 로그 추가
                self._add_log(process_data['process_id'], None, 'CREATE', 
                             process_data.get('creator', ''), '프로세스 생성')
                
                logger.info(f"프로세스 추가 완료: {process_data['process_id']}")
                return True
                
        except Exception as e:
            logger.error(f"프로세스 추가 실패: {str(e)}")
            return False

    def update_process(self, process_id, updates):
        """업무 프로세스 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [process_id]
                
                cursor.execute(f'''
                    UPDATE business_processes 
                    SET {set_clause}
                    WHERE process_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    
                    # 로그 추가
                    self._add_log(process_id, None, 'UPDATE', 
                                 updates.get('updater', ''), '프로세스 수정')
                    
                    logger.info(f"프로세스 수정 완료: {process_id}")
                    return True
                else:
                    logger.warning(f"수정할 프로세스 없음: {process_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"프로세스 수정 실패: {str(e)}")
            return False

    def get_process_steps(self, process_id):
        """프로세스 단계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM process_steps 
                    WHERE process_id = ? 
                    ORDER BY step_order, created_date
                '''
                df = pd.read_sql_query(query, conn, params=[process_id])
                return df
                
        except Exception as e:
            logger.error(f"프로세스 단계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_process_step(self, step_data):
        """프로세스 단계 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['step_id', 'process_id', 'step_name']
                for field in required_fields:
                    if field not in step_data or not step_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                step_record = {
                    'step_id': step_data['step_id'],
                    'process_id': step_data['process_id'],
                    'step_name': step_data['step_name'],
                    'step_order': step_data.get('step_order', 1),
                    'description': step_data.get('description', ''),
                    'assignee': step_data.get('assignee', ''),
                    'status': step_data.get('status', 'pending'),
                    'estimated_hours': step_data.get('estimated_hours', 0),
                    'actual_hours': step_data.get('actual_hours', 0),
                    'start_date': step_data.get('start_date', ''),
                    'end_date': step_data.get('end_date', ''),
                    'dependencies': step_data.get('dependencies', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO process_steps (
                        step_id, process_id, step_name, step_order, description,
                        assignee, status, estimated_hours, actual_hours,
                        start_date, end_date, dependencies, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(step_record.values()))
                
                conn.commit()
                
                # 로그 추가
                self._add_log(step_data['process_id'], step_data['step_id'], 'CREATE_STEP', 
                             step_data.get('creator', ''), f"단계 생성: {step_data['step_name']}")
                
                logger.info(f"프로세스 단계 추가 완료: {step_data['step_id']}")
                return True
                
        except Exception as e:
            logger.error(f"프로세스 단계 추가 실패: {str(e)}")
            return False

    def update_process_step(self, step_id, updates):
        """프로세스 단계 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [step_id]
                
                cursor.execute(f'''
                    UPDATE process_steps 
                    SET {set_clause}
                    WHERE step_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    
                    # 프로세스 ID 조회
                    cursor.execute("SELECT process_id FROM process_steps WHERE step_id = ?", (step_id,))
                    result = cursor.fetchone()
                    process_id = result[0] if result else ''
                    
                    # 로그 추가
                    self._add_log(process_id, step_id, 'UPDATE_STEP', 
                                 updates.get('updater', ''), '단계 수정')
                    
                    logger.info(f"프로세스 단계 수정 완료: {step_id}")
                    return True
                else:
                    logger.warning(f"수정할 단계 없음: {step_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"프로세스 단계 수정 실패: {str(e)}")
            return False

    def get_process_logs(self, process_id, limit=100):
        """프로세스 로그 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM process_logs 
                    WHERE process_id = ? 
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=[process_id, limit])
                return df
                
        except Exception as e:
            logger.error(f"프로세스 로그 조회 실패: {str(e)}")
            return pd.DataFrame()

    def _add_log(self, process_id, step_id, action, user_id, message, old_value=None, new_value=None):
        """프로세스 로그 추가 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                log_id = f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{process_id}"
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO process_logs (
                        log_id, process_id, step_id, action, user_id,
                        message, old_value, new_value, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, process_id, step_id, action, user_id, message, old_value, new_value, current_time))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"로그 추가 실패: {str(e)}")

    def get_process_statistics(self, department=None, date_from=None, date_to=None):
        """프로세스 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        department,
                        status,
                        COUNT(*) as count,
                        AVG(completion_rate) as avg_completion,
                        AVG(actual_hours) as avg_hours,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count
                    FROM business_processes
                    WHERE 1=1
                '''
                params = []
                
                if department:
                    query += " AND department = ?"
                    params.append(department)
                if date_from:
                    query += " AND created_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND created_date <= ?"
                    params.append(date_to)
                
                query += " GROUP BY department, status ORDER BY department, status"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"프로세스 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, processes_csv_path=None, steps_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 프로세스 데이터 마이그레이션
            if processes_csv_path is None:
                processes_csv_path = os.path.join("data", "business_processes.csv")
            
            if os.path.exists(processes_csv_path):
                df = pd.read_csv(processes_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        process_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in process_data.items():
                            if pd.isna(value):
                                if key in ['estimated_hours', 'actual_hours', 'completion_rate']:
                                    process_data[key] = 0
                                else:
                                    process_data[key] = ''
                        
                        self.add_process(process_data)
                    
                    logger.info(f"프로세스 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 프로세스 단계 데이터 마이그레이션
            if steps_csv_path is None:
                steps_csv_path = os.path.join("data", "process_steps.csv")
            
            if os.path.exists(steps_csv_path):
                df = pd.read_csv(steps_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        step_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in step_data.items():
                            if pd.isna(value):
                                if key in ['step_order', 'estimated_hours', 'actual_hours']:
                                    step_data[key] = 0
                                else:
                                    step_data[key] = ''
                        
                        self.add_process_step(step_data)
                    
                    logger.info(f"프로세스 단계 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False