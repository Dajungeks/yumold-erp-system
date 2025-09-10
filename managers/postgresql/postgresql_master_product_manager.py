# -*- coding: utf-8 -*-
"""
PostgreSQL MasterProduct 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLMasterProductManager(BasePostgreSQLManager):
    """PostgreSQL MasterProduct 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """MasterProduct 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기본 테이블 생성 (SQLite 매니저 참조하여 수정 필요)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS master_products (
                        id SERIAL PRIMARY KEY,
                        item_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(200),
                        status VARCHAR(20) DEFAULT 'active',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("MasterProduct 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"MasterProduct 테이블 초기화 실패: {e}")
    
    def get_all_items(self):
        """모든 항목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM master_products ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            return []
    
    def get_master_products(self):
        """마스터 제품 목록 조회 (SQLite 호환)"""
        try:
            import pandas as pd
            
            query = """
                SELECT * FROM master_products 
                ORDER BY created_date DESC
            """
            
            result = self.execute_query(query, fetch_all=True)
            
            if result:
                # PostgreSQL 결과를 DataFrame으로 변환
                df = pd.DataFrame(result)
                return df
            else:
                # 빈 DataFrame 반환
                return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"마스터 제품 조회 실패: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_statistics(self):
        """통계 조회"""
        try:
            query = "SELECT COUNT(*) as total_count FROM master_products"
            result = self.execute_query(query, fetch_one=True)
            
            return {'total_count': result['total_count'] if result else 0}
            
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
