"""
SQLite 주간 보고서 관리자 - 주간 업무 보고서 관리
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

class SQLiteWeeklyReportManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 주간 보고서 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_reports (
                        report_id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT,
                        department TEXT,
                        position TEXT,
                        report_week TEXT NOT NULL,
                        week_start_date TEXT NOT NULL,
                        week_end_date TEXT NOT NULL,
                        report_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'draft',
                        this_week_accomplishments TEXT,
                        this_week_challenges TEXT,
                        next_week_plans TEXT,
                        support_needed TEXT,
                        additional_comments TEXT,
                        work_hours REAL DEFAULT 0,
                        overtime_hours REAL DEFAULT 0,
                        projects_worked TEXT,
                        meetings_attended TEXT,
                        training_completed TEXT,
                        supervisor_id TEXT,
                        supervisor_name TEXT,
                        review_status TEXT DEFAULT 'pending',
                        review_date TEXT,
                        review_comments TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 주간 보고서 항목 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_report_items (
                        item_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        item_type TEXT DEFAULT 'task',
                        item_title TEXT NOT NULL,
                        item_description TEXT,
                        priority TEXT DEFAULT 'normal',
                        status TEXT DEFAULT 'in_progress',
                        completion_percentage INTEGER DEFAULT 0,
                        time_spent REAL DEFAULT 0,
                        start_date TEXT,
                        due_date TEXT,
                        completion_date TEXT,
                        notes TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (report_id) REFERENCES weekly_reports (report_id)
                    )
                ''')
                
                # 보고서 승인 히스토리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_approval_history (
                        history_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        reviewer_id TEXT,
                        reviewer_name TEXT,
                        previous_status TEXT,
                        new_status TEXT,
                        comments TEXT,
                        action_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (report_id) REFERENCES weekly_reports (report_id)
                    )
                ''')
                
                conn.commit()
                logger.info("주간 보고서 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_weekly_reports(self, employee_id=None, department=None, report_week=None, status=None, limit=50):
        """주간 보고서 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM weekly_reports WHERE 1=1"
                params = []
                
                if employee_id:
                    query += " AND employee_id = ?"
                    params.append(employee_id)
                if department:
                    query += " AND department = ?"
                    params.append(department)
                if report_week:
                    query += " AND report_week = ?"
                    params.append(report_week)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY report_week DESC, report_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"주간 보고서 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_weekly_report(self, report_data, items_data=None):
        """주간 보고서 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['report_id', 'employee_id', 'report_week']
                for field in required_fields:
                    if field not in report_data or not report_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 주 시작/종료 날짜 계산
                if 'week_start_date' not in report_data or not report_data['week_start_date']:
                    # report_week 형식: 2024-W01
                    year, week = report_data['report_week'].split('-W')
                    first_day = datetime.strptime(f"{year}-W{week.zfill(2)}-1", "%Y-W%U-%w")
                    report_data['week_start_date'] = first_day.strftime('%Y-%m-%d')
                    report_data['week_end_date'] = (first_day + timedelta(days=6)).strftime('%Y-%m-%d')
                
                report_record = {
                    'report_id': report_data['report_id'],
                    'employee_id': report_data['employee_id'],
                    'employee_name': report_data.get('employee_name', ''),
                    'department': report_data.get('department', ''),
                    'position': report_data.get('position', ''),
                    'report_week': report_data['report_week'],
                    'week_start_date': report_data['week_start_date'],
                    'week_end_date': report_data['week_end_date'],
                    'report_date': report_data.get('report_date', current_time),
                    'status': report_data.get('status', 'draft'),
                    'this_week_accomplishments': report_data.get('this_week_accomplishments', ''),
                    'this_week_challenges': report_data.get('this_week_challenges', ''),
                    'next_week_plans': report_data.get('next_week_plans', ''),
                    'support_needed': report_data.get('support_needed', ''),
                    'additional_comments': report_data.get('additional_comments', ''),
                    'work_hours': report_data.get('work_hours', 0),
                    'overtime_hours': report_data.get('overtime_hours', 0),
                    'projects_worked': report_data.get('projects_worked', ''),
                    'meetings_attended': report_data.get('meetings_attended', ''),
                    'training_completed': report_data.get('training_completed', ''),
                    'supervisor_id': report_data.get('supervisor_id', ''),
                    'supervisor_name': report_data.get('supervisor_name', ''),
                    'review_status': report_data.get('review_status', 'pending'),
                    'review_date': report_data.get('review_date', ''),
                    'review_comments': report_data.get('review_comments', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO weekly_reports (
                        report_id, employee_id, employee_name, department, position,
                        report_week, week_start_date, week_end_date, report_date, status,
                        this_week_accomplishments, this_week_challenges, next_week_plans,
                        support_needed, additional_comments, work_hours, overtime_hours,
                        projects_worked, meetings_attended, training_completed,
                        supervisor_id, supervisor_name, review_status, review_date,
                        review_comments, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(report_record.values()))
                
                # 보고서 항목 추가
                if items_data:
                    for item in items_data:
                        item_record = {
                            'item_id': item.get('item_id', f"{report_data['report_id']}_ITEM_{len(items_data)}"),
                            'report_id': report_data['report_id'],
                            'item_type': item.get('item_type', 'task'),
                            'item_title': item.get('item_title', ''),
                            'item_description': item.get('item_description', ''),
                            'priority': item.get('priority', 'normal'),
                            'status': item.get('status', 'in_progress'),
                            'completion_percentage': item.get('completion_percentage', 0),
                            'time_spent': item.get('time_spent', 0),
                            'start_date': item.get('start_date', ''),
                            'due_date': item.get('due_date', ''),
                            'completion_date': item.get('completion_date', ''),
                            'notes': item.get('notes', ''),
                            'created_date': current_time
                        }
                        
                        cursor.execute('''
                            INSERT INTO weekly_report_items (
                                item_id, report_id, item_type, item_title, item_description,
                                priority, status, completion_percentage, time_spent,
                                start_date, due_date, completion_date, notes, created_date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', tuple(item_record.values()))
                
                # 승인 히스토리 추가
                self._add_approval_history(report_data['report_id'], 'CREATE', 
                                         report_data['employee_id'], report_data.get('employee_name', ''),
                                         '', 'draft', '보고서 생성')
                
                conn.commit()
                logger.info(f"주간 보고서 추가 완료: {report_data['report_id']}")
                return True
                
        except Exception as e:
            logger.error(f"주간 보고서 추가 실패: {str(e)}")
            return False

    def update_weekly_report(self, report_id, updates, updated_by=''):
        """주간 보고서 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 상태 조회
                cursor.execute("SELECT status FROM weekly_reports WHERE report_id = ?", (report_id,))
                result = cursor.fetchone()
                old_status = result[0] if result else ''
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [report_id]
                
                cursor.execute(f'''
                    UPDATE weekly_reports 
                    SET {set_clause}
                    WHERE report_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    # 상태 변경 시 승인 히스토리 추가
                    if 'status' in updates and updates['status'] != old_status:
                        self._add_approval_history(report_id, 'UPDATE', updated_by, '',
                                                 old_status, updates['status'], '보고서 상태 변경')
                    
                    conn.commit()
                    logger.info(f"주간 보고서 수정 완료: {report_id}")
                    return True
                else:
                    logger.warning(f"수정할 주간 보고서 없음: {report_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"주간 보고서 수정 실패: {str(e)}")
            return False

    def approve_weekly_report(self, report_id, reviewer_id, reviewer_name, comments=''):
        """주간 보고서 승인"""
        try:
            approval_data = {
                'review_status': 'approved',
                'review_date': datetime.now().isoformat(),
                'review_comments': comments
            }
            
            success = self.update_weekly_report(report_id, approval_data, reviewer_id)
            
            if success:
                # 승인 히스토리 추가
                self._add_approval_history(report_id, 'APPROVE', reviewer_id, reviewer_name,
                                         'pending', 'approved', f"보고서 승인: {comments}")
                
                logger.info(f"주간 보고서 승인 완료: {report_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"주간 보고서 승인 실패: {str(e)}")
            return False

    def reject_weekly_report(self, report_id, reviewer_id, reviewer_name, comments=''):
        """주간 보고서 거부"""
        try:
            rejection_data = {
                'review_status': 'rejected',
                'review_date': datetime.now().isoformat(),
                'review_comments': comments
            }
            
            success = self.update_weekly_report(report_id, rejection_data, reviewer_id)
            
            if success:
                # 승인 히스토리 추가
                self._add_approval_history(report_id, 'REJECT', reviewer_id, reviewer_name,
                                         'pending', 'rejected', f"보고서 거부: {comments}")
                
                logger.info(f"주간 보고서 거부 완료: {report_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"주간 보고서 거부 실패: {str(e)}")
            return False

    def get_report_items(self, report_id):
        """보고서 항목 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM weekly_report_items WHERE report_id = ? ORDER BY created_date"
                df = pd.read_sql_query(query, conn, params=[report_id])
                return df
                
        except Exception as e:
            logger.error(f"보고서 항목 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_approval_history(self, report_id):
        """승인 히스토리 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM report_approval_history 
                    WHERE report_id = ? 
                    ORDER BY action_date DESC
                '''
                df = pd.read_sql_query(query, conn, params=[report_id])
                return df
                
        except Exception as e:
            logger.error(f"승인 히스토리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def _add_approval_history(self, report_id, action, reviewer_id, reviewer_name, 
                            previous_status, new_status, comments):
        """승인 히스토리 추가 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                history_id = f"HIST_{datetime.now().strftime('%Y%m%d%H%M%S')}_{report_id}"
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO report_approval_history (
                        history_id, report_id, action, reviewer_id, reviewer_name,
                        previous_status, new_status, comments, action_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (history_id, report_id, action, reviewer_id, reviewer_name,
                      previous_status, new_status, comments, current_time))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"승인 히스토리 추가 실패: {str(e)}")

    def get_report_statistics(self, department=None, date_from=None, date_to=None):
        """보고서 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        department,
                        status,
                        review_status,
                        COUNT(*) as count,
                        AVG(work_hours) as avg_work_hours,
                        AVG(overtime_hours) as avg_overtime_hours,
                        SUM(work_hours) as total_work_hours,
                        SUM(overtime_hours) as total_overtime_hours
                    FROM weekly_reports
                    WHERE 1=1
                '''
                params = []
                
                if department:
                    query += " AND department = ?"
                    params.append(department)
                if date_from:
                    query += " AND week_start_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND week_end_date <= ?"
                    params.append(date_to)
                
                query += " GROUP BY department, status, review_status ORDER BY department"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"보고서 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, reports_csv_path=None, items_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 주간 보고서 데이터 마이그레이션
            if reports_csv_path is None:
                reports_csv_path = os.path.join("data", "weekly_reports.csv")
            
            if os.path.exists(reports_csv_path):
                df = pd.read_csv(reports_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        report_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in report_data.items():
                            if pd.isna(value):
                                if key in ['work_hours', 'overtime_hours']:
                                    report_data[key] = 0
                                else:
                                    report_data[key] = ''
                        
                        self.add_weekly_report(report_data)
                    
                    logger.info(f"주간 보고서 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False