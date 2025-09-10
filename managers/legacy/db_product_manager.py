"""
SQLite 기반 제품 관리자
기존 product_manager.py의 SQLite 버전
"""
import sqlite3
import pandas as pd
from datetime import datetime
from .database_manager import DatabaseManager

class DBProductManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 제품 관리자 초기화"""
        self.db_manager = DatabaseManager(db_path)
    
    def get_all_products(self):
        """모든 제품 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM products ORDER BY product_name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_code(self, product_code):
        """특정 제품 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM products WHERE product_code = ?", (product_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_product(self, product_data):
        """새 제품 추가"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO products 
                    (product_code, product_name, category, subcategory, description, 
                     unit_price, currency, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_data.get('product_code'),
                    product_data.get('product_name'),
                    product_data.get('category', ''),
                    product_data.get('subcategory', ''),
                    product_data.get('description', ''),
                    product_data.get('unit_price', 0),
                    product_data.get('currency', 'VND'),
                    product_data.get('status', 'active')
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 중복 코드
        except Exception as e:
            print(f"제품 추가 오류: {e}")
            return False
    
    def update_product(self, product_code, product_data):
        """제품 정보 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE products 
                    SET product_name=?, category=?, subcategory=?, description=?,
                        unit_price=?, currency=?, status=?, updated_date=CURRENT_TIMESTAMP
                    WHERE product_code=?
                ''', (
                    product_data.get('product_name'),
                    product_data.get('category', ''),
                    product_data.get('subcategory', ''),
                    product_data.get('description', ''),
                    product_data.get('unit_price', 0),
                    product_data.get('currency', 'VND'),
                    product_data.get('status', 'active'),
                    product_code
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"제품 업데이트 오류: {e}")
            return False
    
    def delete_product(self, product_code):
        """제품 삭제 (비활성화)"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE products 
                    SET status='inactive', updated_date=CURRENT_TIMESTAMP
                    WHERE product_code=?
                ''', (product_code,))
                conn.commit()
            return True
        except Exception as e:
            print(f"제품 삭제 오류: {e}")
            return False
    
    def get_categories(self):
        """모든 카테고리 목록 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
            return [row[0] for row in cursor.fetchall()]
    
    def get_subcategories(self, category=None):
        """하위 카테고리 목록 반환 (카테고리별 필터링 가능)"""
        query = "SELECT DISTINCT subcategory FROM products WHERE subcategory IS NOT NULL AND subcategory != ''"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
    
    def get_filtered_products(self, category_filter=None, subcategory_filter=None, 
                             status_filter=None, search_term=None):
        """필터링된 제품 목록 반환"""
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
        
        if subcategory_filter:
            query += " AND subcategory = ?"
            params.append(subcategory_filter)
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if search_term:
            query += " AND (product_name LIKE ? OR product_code LIKE ? OR description LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY product_name"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product_count(self):
        """총 제품 수 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
            return cursor.fetchone()[0]
    
    def get_product_statistics(self):
        """제품 통계 반환"""
        with self.db_manager.get_connection() as conn:
            stats = {}
            
            # 총 제품 수
            cursor = conn.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
            stats['total_products'] = cursor.fetchone()[0]
            
            # 카테고리별 통계
            cursor = conn.execute('''
                SELECT category, COUNT(*) 
                FROM products 
                WHERE status = 'active' AND category IS NOT NULL AND category != ''
                GROUP BY category
            ''')
            stats['category_distribution'] = dict(cursor.fetchall())
            
            # 평균 가격
            cursor = conn.execute('''
                SELECT AVG(unit_price) 
                FROM products 
                WHERE status = 'active' AND unit_price > 0
            ''')
            avg_price = cursor.fetchone()[0]
            stats['avg_price'] = avg_price if avg_price else 0
            
            # 가격 범위별 분포
            cursor = conn.execute('''
                SELECT 
                    CASE 
                        WHEN unit_price = 0 THEN '가격 미설정'
                        WHEN unit_price < 100 THEN '100 이하'
                        WHEN unit_price < 500 THEN '100-500'
                        WHEN unit_price < 1000 THEN '500-1000'
                        ELSE '1000 이상'
                    END as price_range,
                    COUNT(*)
                FROM products 
                WHERE status = 'active'
                GROUP BY price_range
            ''')
            stats['price_distribution'] = dict(cursor.fetchall())
            
            return stats
    
    def search_products(self, search_term):
        """제품 검색"""
        return self.get_filtered_products(search_term=search_term)
    
    def get_products_by_category(self, category):
        """특정 카테고리의 제품 목록"""
        return self.get_filtered_products(category_filter=category)
    
    def export_to_dataframe(self):
        """제품 데이터를 DataFrame으로 반환"""
        products = self.get_all_products()
        return pd.DataFrame(products)
    
    def generate_product_code(self, category=None):
        """새 제품 코드 생성"""
        with self.db_manager.get_connection() as conn:
            if category:
                # 카테고리별 코드 생성
                prefix = category[:2].upper()
                cursor = conn.execute(
                    "SELECT MAX(CAST(SUBSTR(product_code, 3) AS INTEGER)) FROM products WHERE product_code LIKE ?", 
                    (f"{prefix}%",)
                )
            else:
                cursor = conn.execute("SELECT MAX(CAST(SUBSTR(product_code, 2) AS INTEGER)) FROM products WHERE product_code LIKE 'P%'")
            
            max_id = cursor.fetchone()[0]
            if max_id:
                if category:
                    return f"{prefix}{max_id + 1:04d}"
                else:
                    return f"P{max_id + 1:04d}"
            else:
                if category:
                    return f"{prefix}0001"
                else:
                    return "P0001"