# -*- coding: utf-8 -*-
"""
PostgreSQL 제품 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLProductManager(BasePostgreSQLManager):
    """PostgreSQL 제품 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """제품 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 제품 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        product_id VARCHAR(50) UNIQUE NOT NULL,
                        product_code VARCHAR(100) UNIQUE NOT NULL,
                        product_name VARCHAR(200) NOT NULL,
                        category VARCHAR(100),
                        subcategory VARCHAR(100),
                        description TEXT,
                        unit_price DECIMAL(15,2),
                        currency VARCHAR(10) DEFAULT 'VND',
                        status VARCHAR(20) DEFAULT 'active',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                print("제품 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            print(f"제품 테이블 초기화 실패: {e}")
    
    def add_product(self, product_data):
        """제품 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 제품 ID 생성
                product_id = self._generate_product_id()
                
                cursor.execute("""
                    INSERT INTO products (
                        product_id, product_code, product_name, category, subcategory,
                        description, unit_price, currency, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    product_id,
                    product_data.get('product_code'),
                    product_data.get('product_name'),
                    product_data.get('category'),
                    product_data.get('subcategory'),
                    product_data.get('description', ''),
                    product_data.get('unit_price', 0),
                    product_data.get('currency', 'VND'),
                    product_data.get('status', 'active')
                ))
                
                result = cursor.fetchone()
                conn.commit()
                
                return {
                    'success': True,
                    'product_id': product_id,
                    'id': result[0] if result else None
                }
                
        except Exception as e:
            print(f"제품 추가 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_products(self):
        """모든 제품 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM products 
                    ORDER BY created_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                products = []
                
                for row in cursor.fetchall():
                    product = dict(zip(columns, row))
                    products.append(product)
                
                return products
                
        except Exception as e:
            print(f"제품 조회 실패: {e}")
            return []
    
    def get_product_by_id(self, product_id):
        """제품 ID로 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM products WHERE product_id = %s
                """, (product_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
                return None
                
        except Exception as e:
            print(f"제품 조회 실패: {e}")
            return None
    
    def update_product(self, product_id, product_data):
        """제품 정보 수정"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE products SET
                        product_code = %s,
                        product_name = %s,
                        category = %s,
                        subcategory = %s,
                        description = %s,
                        unit_price = %s,
                        currency = %s,
                        status = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE product_id = %s
                """, (
                    product_data.get('product_code'),
                    product_data.get('product_name'),
                    product_data.get('category'),
                    product_data.get('subcategory'),
                    product_data.get('description'),
                    product_data.get('unit_price'),
                    product_data.get('currency'),
                    product_data.get('status'),
                    product_id
                ))
                
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            print(f"제품 수정 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_product(self, product_id):
        """제품 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
                conn.commit()
                return {'success': True}
                
        except Exception as e:
            print(f"제품 삭제 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_product_statistics(self):
        """제품 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 총 제품 수
                cursor.execute("SELECT COUNT(*) FROM products")
                total_products = cursor.fetchone()[0]
                
                # 활성 제품 수
                cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
                active_products = cursor.fetchone()[0]
                
                # 카테고리별 제품 수
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM products 
                    WHERE category IS NOT NULL 
                    GROUP BY category
                """)
                categories = cursor.fetchall()
                
                return {
                    'total_products': total_products,
                    'active_products': active_products,
                    'categories': dict(categories) if categories else {}
                }
                
        except Exception as e:
            print(f"제품 통계 조회 실패: {e}")
            return {
                'total_products': 0,
                'active_products': 0,
                'categories': {}
            }
    
    def _generate_product_id(self):
        """제품 ID 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT product_id FROM products 
                    WHERE product_id LIKE 'PRD%' 
                    ORDER BY product_id DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    last_id = result[0]
                    number = int(last_id[3:]) + 1
                    return f"PRD{number:06d}"
                else:
                    return "PRD000001"
                    
        except Exception as e:
            print(f"제품 ID 생성 오류: {e}")
            return f"PRD{str(uuid.uuid4())[:6].upper()}"
    
    def search_products(self, search_term):
        """제품 검색"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE product_name ILIKE %s 
                       OR product_code ILIKE %s 
                       OR category ILIKE %s
                    ORDER BY product_name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                
                columns = [desc[0] for desc in cursor.description]
                products = []
                
                for row in cursor.fetchall():
                    product = dict(zip(columns, row))
                    products.append(product)
                
                return products
                
        except Exception as e:
            print(f"제품 검색 실패: {e}")
            return []