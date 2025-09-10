"""
SQLite 공지사항 관리자 - 공지사항 작성, 관리
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

class SQLiteNoticeManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 공지사항 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notices (
                        notice_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        title_en TEXT,
                        title_vi TEXT,
                        content TEXT NOT NULL,
                        content_en TEXT,
                        content_vi TEXT,
                        category TEXT DEFAULT 'general',
                        priority TEXT DEFAULT 'normal',
                        status TEXT DEFAULT 'active',
                        target_audience TEXT DEFAULT 'all',
                        department TEXT,
                        author_id TEXT,
                        author_name TEXT,
                        publish_date TEXT,
                        expire_date TEXT,
                        is_pinned INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        attachments TEXT,
                        tags TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 공지사항 읽음 표시 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notice_reads (
                        read_id TEXT PRIMARY KEY,
                        notice_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        read_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(notice_id, user_id),
                        FOREIGN KEY (notice_id) REFERENCES notices (notice_id)
                    )
                ''')
                
                # 공지사항 카테고리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notice_categories (
                        category_id TEXT PRIMARY KEY,
                        category_name TEXT NOT NULL,
                        category_name_en TEXT,
                        category_name_vi TEXT,
                        description TEXT,
                        color_code TEXT DEFAULT '#0066cc',
                        is_active INTEGER DEFAULT 1,
                        display_order INTEGER DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 직원 게시글 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS employee_posts (
                        post_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        title_en TEXT,
                        title_vi TEXT,
                        content TEXT NOT NULL,
                        content_en TEXT,
                        content_vi TEXT,
                        category TEXT DEFAULT 'general',
                        author_id TEXT NOT NULL,
                        author_name TEXT NOT NULL,
                        department TEXT,
                        position TEXT,
                        status TEXT DEFAULT 'active',
                        visible_to TEXT DEFAULT 'all',
                        is_pinned INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        reply_count INTEGER DEFAULT 0,
                        tags TEXT DEFAULT '',
                        attachments TEXT DEFAULT '[]',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 기본 카테고리 추가
                default_categories = [
                    ('general', '일반공지', 'General Notice', 'Thông báo chung', '일반적인 공지사항', '#0066cc', 1, 1),
                    ('urgent', '긴급공지', 'Urgent Notice', 'Thông báo khẩn cấp', '긴급한 공지사항', '#ff6600', 1, 2),
                    ('system', '시스템공지', 'System Notice', 'Thông báo hệ thống', '시스템 관련 공지', '#009900', 1, 3),
                    ('hr', '인사공지', 'HR Notice', 'Thông báo nhân sự', '인사 관련 공지', '#9900cc', 1, 4),
                    ('meeting', '회의공지', 'Meeting Notice', 'Thông báo họp', '회의 관련 공지', '#cc9900', 1, 5)
                ]
                
                cursor.executemany('''
                    INSERT OR IGNORE INTO notice_categories 
                    (category_id, category_name, category_name_en, category_name_vi, 
                     description, color_code, is_active, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_categories)
                
                conn.commit()
                logger.info("공지사항 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_notices(self, category=None, status='active', target_audience=None, limit=50):
        """공지사항 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM notices WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                if target_audience:
                    query += " AND (target_audience = 'all' OR target_audience = ?)"
                    params.append(target_audience)
                
                query += " ORDER BY is_pinned DESC, publish_date DESC, created_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"공지사항 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_notice(self, notice_data):
        """공지사항 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['notice_id', 'title', 'content']
                for field in required_fields:
                    if field not in notice_data or not notice_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                notice_record = {
                    'notice_id': notice_data['notice_id'],
                    'title': notice_data['title'],
                    'title_en': notice_data.get('title_en', ''),
                    'title_vi': notice_data.get('title_vi', ''),
                    'content': notice_data['content'],
                    'content_en': notice_data.get('content_en', ''),
                    'content_vi': notice_data.get('content_vi', ''),
                    'category': notice_data.get('category', 'general'),
                    'priority': notice_data.get('priority', 'normal'),
                    'status': notice_data.get('status', 'active'),
                    'target_audience': notice_data.get('target_audience', 'all'),
                    'department': notice_data.get('department', ''),
                    'author_id': notice_data.get('author_id', ''),
                    'author_name': notice_data.get('author_name', ''),
                    'publish_date': notice_data.get('publish_date', current_time),
                    'expire_date': notice_data.get('expire_date', ''),
                    'is_pinned': notice_data.get('is_pinned', 0),
                    'view_count': 0,
                    'attachments': json.dumps(notice_data.get('attachments', [])),
                    'tags': notice_data.get('tags', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO notices (
                        notice_id, title, title_en, title_vi, content, content_en, content_vi,
                        category, priority, status, target_audience, department, author_id, author_name,
                        publish_date, expire_date, is_pinned, view_count, attachments, tags,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(notice_record.values()))
                
                conn.commit()
                logger.info(f"공지사항 추가 완료: {notice_data['notice_id']}")
                return True
                
        except Exception as e:
            logger.error(f"공지사항 추가 실패: {str(e)}")
            return False

    def update_notice(self, notice_id, updates):
        """공지사항 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [notice_id]
                
                cursor.execute(f'''
                    UPDATE notices 
                    SET {set_clause}
                    WHERE notice_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"공지사항 수정 완료: {notice_id}")
                    return True
                else:
                    logger.warning(f"수정할 공지사항 없음: {notice_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"공지사항 수정 실패: {str(e)}")
            return False

    def mark_as_read(self, notice_id, user_id, user_name=''):
        """공지사항 읽음 표시"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                read_id = f"{notice_id}_{user_id}"
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO notice_reads 
                    (read_id, notice_id, user_id, user_name, read_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (read_id, notice_id, user_id, user_name, current_time))
                
                # 조회수 증가
                cursor.execute('''
                    UPDATE notices 
                    SET view_count = view_count + 1 
                    WHERE notice_id = ?
                ''', (notice_id,))
                
                conn.commit()
                logger.info(f"공지사항 읽음 표시 완료: {notice_id} by {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"공지사항 읽음 표시 실패: {str(e)}")
            return False

    def get_notice_readers(self, notice_id):
        """공지사항 읽은 사용자 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM notice_reads 
                    WHERE notice_id = ? 
                    ORDER BY read_date DESC
                '''
                df = pd.read_sql_query(query, conn, params=[notice_id])
                return df
                
        except Exception as e:
            logger.error(f"공지사항 읽은 사용자 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_unread_notices(self, user_id, limit=10):
        """읽지 않은 공지사항 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT n.* FROM notices n
                    LEFT JOIN notice_reads nr ON n.notice_id = nr.notice_id AND nr.user_id = ?
                    WHERE n.status = 'active' 
                        AND (n.expire_date = '' OR n.expire_date > date('now'))
                        AND nr.notice_id IS NULL
                    ORDER BY n.is_pinned DESC, n.priority = 'urgent' DESC, n.publish_date DESC
                '''
                params = [user_id]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"읽지 않은 공지사항 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_notice_categories_df(self, is_active=True):
        """공지사항 카테고리 조회 (DataFrame 형태)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM notice_categories"
                params = []
                
                if is_active is not None:
                    query += " WHERE is_active = ?"
                    params.append(1 if is_active else 0)
                
                query += " ORDER BY display_order, category_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"공지사항 카테고리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_notice_statistics(self, date_from=None, date_to=None):
        """공지사항 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        category,
                        priority,
                        status,
                        COUNT(*) as count,
                        AVG(view_count) as avg_views,
                        MAX(view_count) as max_views,
                        SUM(is_pinned) as pinned_count
                    FROM notices
                    WHERE 1=1
                '''
                params = []
                
                if date_from:
                    query += " AND publish_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND publish_date <= ?"
                    params.append(date_to)
                
                query += " GROUP BY category, priority, status ORDER BY category, priority"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"공지사항 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_all_notices(self, status=None, category=None, limit=None):
        """모든 공지사항 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM notices WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY is_pinned DESC, priority = 'urgent' DESC, publish_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"공지사항 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_all_employee_posts(self, status=None, category=None, limit=None):
        """모든 직원 게시글 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM employee_posts WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY is_pinned DESC, created_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"직원 게시글 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_employee_post_categories(self):
        """직원 게시글 카테고리 목록 조회"""
        try:
            categories = ['일반', '공지', '질문', '제안', '기타']
            return categories
        except Exception as e:
            logger.error(f"직원 게시글 카테고리 조회 실패: {str(e)}")
            return []

    def get_target_audiences(self):
        """공지사항 대상 그룹 목록 조회"""
        try:
            audiences = [
                'all',  # 전체
                'management',  # 경영진
                'general_affairs',  # 총무
                'sales',  # 영업
                'engineering',  # 기술
                'production',  # 생산
                'quality',  # 품질
                'accounting'  # 회계
            ]
            return audiences
        except Exception as e:
            logger.error(f"대상 그룹 조회 실패: {str(e)}")
            return ['all']

    def get_notice_categories(self):
        """공지사항 카테고리 목록 조회 (단순 리스트)"""
        try:
            categories = ['일반공지', '긴급공지', '시스템공지', '인사공지', '회의공지']
            return categories
        except Exception as e:
            logger.error(f"공지사항 카테고리 조회 실패: {str(e)}")
            return ['일반공지']

    def create_notice(self, notice_data):
        """공지사항 생성"""
        try:
            if 'notice_id' not in notice_data:
                notice_data['notice_id'] = f"NOTICE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            success = self.add_notice(notice_data)
            if success:
                return True, notice_data['notice_id']
            else:
                return False, None
        except Exception as e:
            logger.error(f"공지사항 생성 실패: {str(e)}")
            return False, None

    def create_employee_post(self, post_data):
        """직원 게시글 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if 'post_id' not in post_data:
                    post_data['post_id'] = f"POST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO employee_posts
                    (post_id, title, content, category, author_id, author_name, 
                     department, position, status, visible_to, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_data['post_id'],
                    post_data.get('title', ''),
                    post_data.get('content', ''),
                    post_data.get('category', 'general'),
                    post_data.get('author_id', ''),
                    post_data.get('author_name', ''),
                    post_data.get('department', ''),
                    post_data.get('position', ''),
                    post_data.get('status', 'active'),
                    post_data.get('visible_to', 'all'),
                    current_time,
                    current_time
                ))
                
                conn.commit()
                logger.info(f"직원 게시글 생성 완료: {post_data['post_id']}")
                return True, post_data['post_id']
                
        except Exception as e:
            logger.error(f"직원 게시글 생성 실패: {str(e)}")
            return False, None

    def delete_notice(self, notice_id):
        """공지사항 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notices WHERE notice_id = ?", (notice_id,))
                conn.commit()
                logger.info(f"공지사항 삭제 완료: {notice_id}")
                return True
        except Exception as e:
            logger.error(f"공지사항 삭제 실패: {str(e)}")
            return False

    def delete_employee_post(self, post_id):
        """직원 게시글 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM employee_posts WHERE post_id = ?", (post_id,))
                conn.commit()
                logger.info(f"직원 게시글 삭제 완료: {post_id}")
                return True
        except Exception as e:
            logger.error(f"직원 게시글 삭제 실패: {str(e)}")
            return False

    def migrate_from_csv(self, notices_csv_path=None, reads_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 공지사항 데이터 마이그레이션
            if notices_csv_path is None:
                notices_csv_path = os.path.join("data", "notices.csv")
            
            if os.path.exists(notices_csv_path):
                df = pd.read_csv(notices_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        notice_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in notice_data.items():
                            if pd.isna(value):
                                if key in ['is_pinned', 'view_count']:
                                    notice_data[key] = 0
                                else:
                                    notice_data[key] = ''
                        
                        self.add_notice(notice_data)
                    
                    logger.info(f"공지사항 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 읽음 표시 데이터 마이그레이션
            if reads_csv_path is None:
                reads_csv_path = os.path.join("data", "notice_reads.csv")
            
            if os.path.exists(reads_csv_path):
                df = pd.read_csv(reads_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        for _, row in df.iterrows():
                            read_data = row.to_dict()
                            # NaN 값 처리
                            for key, value in read_data.items():
                                if pd.isna(value):
                                    read_data[key] = ''
                            
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO notice_reads
                                    (read_id, notice_id, user_id, user_name, read_date)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    read_data.get('read_id', f"{read_data.get('notice_id', '')}_{read_data.get('user_id', '')}"),
                                    read_data.get('notice_id', ''),
                                    read_data.get('user_id', ''),
                                    read_data.get('user_name', ''),
                                    read_data.get('read_date', datetime.now().isoformat())
                                ))
                            except sqlite3.IntegrityError:
                                # 중복 데이터 스킵
                                pass
                        
                        conn.commit()
                    
                    logger.info(f"읽음 표시 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False