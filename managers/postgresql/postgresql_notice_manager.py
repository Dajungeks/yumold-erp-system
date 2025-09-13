# -*- coding: utf-8 -*-
"""
PostgreSQL Notice 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLNoticeManager(BasePostgreSQLManager):
    """PostgreSQL Notice 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """Notice 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 먼저 기존 테이블 구조 확인
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'notices'
                """)
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                if not existing_columns:
                    # 새로 테이블 생성
                    cursor.execute("""
                        CREATE TABLE notices (
                            id SERIAL PRIMARY KEY,
                            notice_id VARCHAR(50) UNIQUE NOT NULL,
                            title VARCHAR(500) NOT NULL,
                            title_en VARCHAR(500),
                            title_vi VARCHAR(500),
                            content TEXT NOT NULL,
                            content_en TEXT,
                            content_vi TEXT,
                            category VARCHAR(50) DEFAULT 'general',
                            priority VARCHAR(20) DEFAULT 'normal',
                            status VARCHAR(20) DEFAULT 'active',
                            target_audience VARCHAR(50) DEFAULT 'all',
                            department VARCHAR(100),
                            author_id VARCHAR(50),
                            author_name VARCHAR(100),
                            publish_date TIMESTAMP,
                            expire_date TIMESTAMP,
                            is_pinned INTEGER DEFAULT 0,
                            view_count INTEGER DEFAULT 0,
                            attachments TEXT,
                            tags TEXT,
                            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    # 기존 테이블에 누락된 컬럼들 추가
                    required_columns = {
                        'notice_id': 'VARCHAR(50) UNIQUE',
                        'title': 'VARCHAR(500) NOT NULL',
                        'content': 'TEXT NOT NULL',
                        'category': 'VARCHAR(50) DEFAULT \'general\'',
                        'priority': 'VARCHAR(20) DEFAULT \'normal\'',
                        'target_audience': 'VARCHAR(50) DEFAULT \'all\'',
                        'department': 'VARCHAR(100)',
                        'author_id': 'VARCHAR(50)',
                        'author_name': 'VARCHAR(100)',
                        'publish_date': 'TIMESTAMP',
                        'expire_date': 'TIMESTAMP',
                        'is_pinned': 'INTEGER DEFAULT 0',
                        'view_count': 'INTEGER DEFAULT 0',
                        'attachments': 'TEXT',
                        'tags': 'TEXT',
                        'title_en': 'VARCHAR(500)',
                        'title_vi': 'VARCHAR(500)',
                        'content_en': 'TEXT',
                        'content_vi': 'TEXT'
                    }
                    
                    for col_name, col_definition in required_columns.items():
                        if col_name not in existing_columns:
                            try:
                                cursor.execute(f"ALTER TABLE notices ADD COLUMN {col_name} {col_definition}")
                            except Exception as col_error:
                                self.log_error(f"컬럼 {col_name} 추가 실패: {col_error}")
                
                # 공지사항 읽음 표시 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notice_reads (
                        id SERIAL PRIMARY KEY,
                        read_id VARCHAR(50) UNIQUE NOT NULL,
                        notice_id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        user_name VARCHAR(100),
                        read_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(notice_id, user_id)
                    )
                """)
                
                self.log_info("Notice 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"Notice 테이블 초기화 실패: {e}")
    
    def get_all_notices(self, status=None, category=None, limit=None) -> 'pd.DataFrame':
        """모든 공지사항을 DataFrame으로 조회"""
        try:
            import pandas as pd
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM notices WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                query += " ORDER BY COALESCE(is_pinned, 0) DESC, CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END DESC, COALESCE(publish_date, created_date) DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                notices = []
                
                for row in cursor.fetchall():
                    notice = dict(zip(columns, row))
                    notices.append(notice)
                
                if notices:
                    return pd.DataFrame(notices)
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"공지사항 조회 실패: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_all_items(self) -> 'pd.DataFrame':
        """모든 항목을 DataFrame으로 조회 (get_all_notices 호출)"""
        return self.get_all_notices()
    
    def get_notice_by_id(self, notice_id):
        """특정 공지사항 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM notices WHERE notice_id = %s", [notice_id])
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            self.log_error(f"공지사항 조회 실패: {e}")
            return None
    
    def get_notices(self, category=None, status='active', target_audience=None, limit=50):
        """조건에 따른 공지사항 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM notices WHERE status = %s"
                params = [status]
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                if target_audience:
                    query += " AND (target_audience = %s OR target_audience = 'all')"
                    params.append(target_audience)
                
                query += " ORDER BY is_pinned DESC, publish_date DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                notices = []
                
                for row in cursor.fetchall():
                    notice = dict(zip(columns, row))
                    notices.append(notice)
                
                return notices
                
        except Exception as e:
            self.log_error(f"공지사항 조회 실패: {e}")
            return []
    
    def get_all_employee_posts(self, status=None, category=None, limit=None) -> 'pd.DataFrame':
        """모든 직원 게시글을 DataFrame으로 조회 (공지사항과 동일하게 처리)"""
        return self.get_all_notices(status=status, category=category, limit=limit)
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM notices")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
