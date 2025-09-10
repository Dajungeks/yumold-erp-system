# -*- coding: utf-8 -*-
"""
PostgreSQL MonthlySales 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLMonthlySalesManager(BasePostgreSQLManager):
    """PostgreSQL MonthlySales 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """MonthlySales 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기본 테이블 생성 (SQLite 매니저 참조하여 수정 필요)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS monthly_saless (
                        id SERIAL PRIMARY KEY,
                        item_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(200),
                        status VARCHAR(20) DEFAULT 'active',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("MonthlySales 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"MonthlySales 테이블 초기화 실패: {e}")
    
    def get_all_items(self):
        """모든 항목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM monthly_saless ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM monthly_saless")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
