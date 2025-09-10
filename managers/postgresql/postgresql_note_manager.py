# -*- coding: utf-8 -*-
"""
PostgreSQL Note 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLNoteManager(BasePostgreSQLManager):
    """PostgreSQL Note 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """Note 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 사용자 노트 테이블 (SQLite 매니저와 호환)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_notes (
                        note_id VARCHAR(100) PRIMARY KEY,
                        user_id VARCHAR(50) NOT NULL,
                        page_name VARCHAR(100) NOT NULL,
                        note_content TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, page_name)
                    )
                """)
                
                self.log_info("Note 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"Note 테이블 초기화 실패: {e}")
    
    def get_user_note(self, user_id, page_name):
        """특정 사용자의 특정 페이지 노트 조회"""
        try:
            query = """
                SELECT note_content, updated_date 
                FROM user_notes 
                WHERE user_id = %s AND page_name = %s
            """
            result = self.execute_query(query, (user_id, page_name), fetch_one=True)
            
            if result:
                return {
                    'content': result['note_content'],
                    'updated_date': result['updated_date']
                }
            else:
                return None
                
        except Exception as e:
            self.log_error(f"사용자 노트 조회 실패: {e}")
            return None

    def save_user_note(self, user_id, page_name, note_content):
        """사용자 노트 저장 (신규 생성 또는 업데이트)"""
        try:
            # 200자 제한 확인
            if len(note_content) > 200:
                note_content = note_content[:200]
            
            from datetime import datetime
            current_time = datetime.now()
            note_id = f"NOTE_{user_id}_{page_name}_{current_time.strftime('%Y%m%d%H%M%S')}"
            
            # UPSERT (PostgreSQL 방식)
            query = """
                INSERT INTO user_notes 
                (note_id, user_id, page_name, note_content, created_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, page_name) 
                DO UPDATE SET 
                    note_content = EXCLUDED.note_content,
                    updated_date = EXCLUDED.updated_date
            """
            
            self.execute_query(query, (
                note_id, user_id, page_name, note_content,
                current_time, current_time
            ))
            
            self.log_info(f"사용자 노트 저장 완료: {user_id} - {page_name}")
            return True
            
        except Exception as e:
            self.log_error(f"사용자 노트 저장 실패: {e}")
            return False

    def delete_user_note(self, user_id, page_name):
        """사용자 노트 삭제"""
        try:
            query = """
                DELETE FROM user_notes 
                WHERE user_id = %s AND page_name = %s
            """
            
            result = self.execute_query(query, (user_id, page_name))
            
            self.log_info(f"사용자 노트 삭제 완료: {user_id} - {page_name}")
            return True
            
        except Exception as e:
            self.log_error(f"사용자 노트 삭제 실패: {e}")
            return False
    
    def get_all_user_notes(self, user_id):
        """특정 사용자의 모든 노트 조회"""
        try:
            query = """
                SELECT * FROM user_notes 
                WHERE user_id = %s 
                ORDER BY updated_date DESC
            """
            
            result = self.execute_query(query, (user_id,), fetch_all=True)
            return result if result else []
            
        except Exception as e:
            self.log_error(f"사용자 노트 목록 조회 실패: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            query = "SELECT COUNT(*) as total_count FROM user_notes"
            result = self.execute_query(query, fetch_one=True)
            
            return {'total_count': result['total_count'] if result else 0}
            
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
