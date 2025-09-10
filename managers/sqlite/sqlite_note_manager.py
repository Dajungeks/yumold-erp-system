"""
SQLite 노트 관리자 - 페이지별 사용자 노트 관리
각 메인 메뉴에서 200자 내외의 메모를 작성할 수 있는 기능 제공
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteNoteManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 사용자 노트 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_notes (
                        note_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        page_name TEXT NOT NULL,
                        note_content TEXT NOT NULL,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, page_name)
                    )
                ''')
                
                conn.commit()
                logger.info("사용자 노트 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"노트 테이블 초기화 실패: {str(e)}")
            raise

    def get_user_note(self, user_id, page_name):
        """특정 사용자의 특정 페이지 노트 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT note_content, updated_date 
                    FROM user_notes 
                    WHERE user_id = ? AND page_name = ?
                """, (user_id, page_name))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'content': result[0],
                        'updated_date': result[1]
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"사용자 노트 조회 실패: {e}")
            return None

    def save_user_note(self, user_id, page_name, note_content):
        """사용자 노트 저장 (신규 생성 또는 업데이트)"""
        try:
            # 200자 제한 확인
            if len(note_content) > 200:
                note_content = note_content[:200]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                current_time = datetime.now().isoformat()
                note_id = f"NOTE_{user_id}_{page_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # UPSERT (INSERT OR REPLACE)
                cursor.execute("""
                    INSERT OR REPLACE INTO user_notes 
                    (note_id, user_id, page_name, note_content, created_date, updated_date)
                    VALUES (?, ?, ?, ?, 
                        COALESCE((SELECT created_date FROM user_notes WHERE user_id = ? AND page_name = ?), ?),
                        ?)
                """, (
                    note_id, user_id, page_name, note_content,
                    user_id, page_name, current_time,  # COALESCE를 위한 파라미터
                    current_time
                ))
                
                conn.commit()
                logger.info(f"사용자 노트 저장 완료: {user_id} - {page_name}")
                return True
                
        except Exception as e:
            logger.error(f"사용자 노트 저장 실패: {e}")
            return False

    def delete_user_note(self, user_id, page_name):
        """사용자 노트 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM user_notes 
                    WHERE user_id = ? AND page_name = ?
                """, (user_id, page_name))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"사용자 노트 삭제 완료: {user_id} - {page_name}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"사용자 노트 삭제 실패: {e}")
            return False

    def get_all_user_notes(self, user_id):
        """특정 사용자의 모든 노트 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT page_name, note_content, updated_date 
                    FROM user_notes 
                    WHERE user_id = ?
                    ORDER BY updated_date DESC
                """
                
                df = pd.read_sql_query(query, conn, params=(user_id,))
                return df
                
        except Exception as e:
            logger.error(f"사용자 노트 목록 조회 실패: {e}")
            return pd.DataFrame()

    def get_note_statistics(self):
        """노트 통계 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전체 노트 수
                cursor.execute("SELECT COUNT(*) FROM user_notes")
                total_notes = cursor.fetchone()[0]
                
                # 활성 사용자 수 (노트를 작성한 사용자)
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_notes")
                active_users = cursor.fetchone()[0]
                
                # 페이지별 노트 수
                cursor.execute("""
                    SELECT page_name, COUNT(*) as note_count 
                    FROM user_notes 
                    GROUP BY page_name 
                    ORDER BY note_count DESC
                """)
                page_stats = cursor.fetchall()
                
                return {
                    'total_notes': total_notes,
                    'active_users': active_users,
                    'page_stats': page_stats
                }
                
        except Exception as e:
            logger.error(f"노트 통계 조회 실패: {e}")
            return {
                'total_notes': 0,
                'active_users': 0,
                'page_stats': []
            }