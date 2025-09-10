# -*- coding: utf-8 -*-
"""
SQLite 기반 제품 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SQLiteProductManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 제품 매니저 초기화"""
        self.db_path = db_path
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_all_products(self):
        """모든 제품 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COALESCE(product_id, product_code) as product_id,
                        product_code, 
                        product_name,
                        product_name as english_name,
                        category,
                        subcategory,
                        description as model,
                        description as specifications,
                        unit_price as price,
                        currency as price_currency,
                        '' as supplier,
                        status,
                        created_date, 
                        updated_date
                    FROM products
                    ORDER BY product_name
                ''')
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"제품 목록 조회 오류: {e}")
            return []
    
    def get_products_dataframe(self):
        """제품 정보를 DataFrame으로 가져옵니다."""
        try:
            products_list = self.get_all_products()
            return pd.DataFrame(products_list)
        except Exception as e:
            logger.error(f"제품 DataFrame 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_product_by_id(self, product_id):
        """특정 제품 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COALESCE(product_id, product_code) as product_id,
                        product_code, 
                        product_name,
                        product_name as english_name,
                        category,
                        subcategory,
                        description as model,
                        specifications,
                        unit_price as price,
                        currency as price_currency,
                        '' as supplier,
                        status,
                        created_date, 
                        updated_date
                    FROM products 
                    WHERE COALESCE(product_id, product_code) = ?
                ''', (str(product_id),))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"제품 조회 오류: {e}")
            return None
    
    def get_product_by_code(self, product_code):
        """제품 코드로 제품을 조회합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COALESCE(product_id, product_code) as product_id,
                        product_code, 
                        product_name,
                        product_name as english_name,
                        category,
                        subcategory,
                        description as model,
                        specifications,
                        unit_price as price,
                        currency as price_currency,
                        '' as supplier,
                        status,
                        created_date, 
                        updated_date
                    FROM products 
                    WHERE product_code = ?
                ''', (str(product_code),))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"제품 코드 조회 오류: {e}")
            return None
    
    def add_product(self, product_data):
        """새 제품을 추가합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('''
                    INSERT INTO products (
                        product_id, product_code, product_name, english_name,
                        category, subcategory, model, specifications,
                        price, price_currency, supplier, status,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_data.get('product_id', ''),
                    product_data.get('product_code', ''),
                    product_data.get('product_name', ''),
                    product_data.get('english_name', ''),
                    product_data.get('category', ''),
                    product_data.get('subcategory', ''),
                    product_data.get('model', ''),
                    product_data.get('specifications', ''),
                    float(product_data.get('price', 0)),
                    product_data.get('price_currency', 'VND'),
                    product_data.get('supplier', ''),
                    product_data.get('status', 'active'),
                    current_time,
                    current_time
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"제품 추가 오류: {e}")
            return False
    
    def update_product(self, product_id, product_data):
        """제품 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                # 기존 제품 확인
                cursor = conn.execute('SELECT * FROM products WHERE product_id = ?', (str(product_id),))
                if not cursor.fetchone():
                    return False
                
                # 업데이트 실행
                conn.execute('''
                    UPDATE products SET
                        product_code = ?, product_name = ?, english_name = ?,
                        category = ?, subcategory = ?, model = ?, specifications = ?,
                        price = ?, price_currency = ?, supplier = ?, status = ?,
                        updated_date = ?
                    WHERE product_id = ?
                ''', (
                    product_data.get('product_code', ''),
                    product_data.get('product_name', ''),
                    product_data.get('english_name', ''),
                    product_data.get('category', ''),
                    product_data.get('subcategory', ''),
                    product_data.get('model', ''),
                    product_data.get('specifications', ''),
                    float(product_data.get('price', 0)),
                    product_data.get('price_currency', 'VND'),
                    product_data.get('supplier', ''),
                    product_data.get('status', 'active'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    str(product_id)
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"제품 업데이트 오류: {e}")
            return False
    
    def delete_product(self, product_id):
        """제품을 삭제합니다."""
        try:
            with self.get_connection() as conn:
                conn.execute('DELETE FROM products WHERE product_id = ?', (str(product_id),))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"제품 삭제 오류: {e}")
            return False
    
    def get_categories(self):
        """모든 제품 카테고리 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT category FROM products 
                    WHERE category IS NOT NULL AND category != ''
                    ORDER BY category
                ''')
                results = cursor.fetchall()
                categories = [row['category'] for row in results]
                
                # 기본 카테고리 추가 (데이터가 없을 경우)
                default_categories = ["HRC", "MB", "PLC", "HMI", "SENSOR", "MOTOR", "VALVE", "ACTUATOR"]
                for category in default_categories:
                    if category not in categories:
                        categories.append(category)
                
                return sorted(categories)
        except Exception as e:
            logger.error(f"카테고리 목록 조회 오류: {e}")
            return ["HRC", "MB", "PLC", "HMI", "SENSOR", "MOTOR", "VALVE", "ACTUATOR"]
    
    def get_products_by_category(self, category):
        """특정 카테고리의 제품 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COALESCE(product_id, product_code) as product_id,
                        product_code, 
                        product_name,
                        product_name as english_name,
                        category,
                        subcategory,
                        description as model,
                        description as specifications,
                        unit_price as price,
                        currency as price_currency,
                        status
                    FROM products
                    WHERE category = ?
                    ORDER BY product_name
                ''', (category,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"카테고리별 제품 조회 오류: {e}")
            return []
    
    def get_filtered_products(self, category_filter=None, subcategory_filter=None, search_term=None, status_filter=None):
        """필터링된 제품 목록을 DataFrame으로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        COALESCE(product_id, product_code) as product_id,
                        product_code, 
                        product_name,
                        product_name as english_name,
                        category,
                        subcategory,
                        description as model,
                        description as specifications,
                        unit_price as price,
                        currency as price_currency,
                        status,
                        created_date,
                        updated_date
                    FROM products
                    WHERE 1=1
                '''
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
                    query += " AND (product_name LIKE ? OR product_code LIKE ? OR product_name_english LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY product_name"
                
                cursor = conn.execute(query, params)
                results = cursor.fetchall()
                products_list = [dict(row) for row in results]
                
                if products_list:
                    return pd.DataFrame(products_list)
                else:
                    return pd.DataFrame({
                        'product_id': [],
                        'product_code': [],
                        'product_name': [],
                        'english_name': [],
                        'category': [],
                        'subcategory': [],
                        'model': [],
                        'specifications': [],
                        'price': [],
                        'price_currency': [],
                        'status': [],
                        'created_date': [],
                        'updated_date': []
                    })
        except Exception as e:
            logger.error(f"필터링된 제품 목록 조회 오류: {e}")
            return pd.DataFrame({
                'product_id': [],
                'product_code': [],
                'product_name': [],
                'english_name': [],
                'category': [],
                'subcategory': [],
                'model': [],
                'specifications': [],
                'price': [],
                'price_currency': [],
                'status': [],
                'created_date': [],
                'updated_date': []
            })
    
    def get_subcategories(self, category=None):
        """특정 카테고리의 하위 카테고리 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                if category:
                    cursor = conn.execute('''
                        SELECT DISTINCT subcategory FROM products 
                        WHERE category = ? AND subcategory IS NOT NULL AND subcategory != ''
                        ORDER BY subcategory
                    ''', (category,))
                else:
                    cursor = conn.execute('''
                        SELECT DISTINCT subcategory FROM products 
                        WHERE subcategory IS NOT NULL AND subcategory != ''
                        ORDER BY subcategory
                    ''')
                results = cursor.fetchall()
                return [row['subcategory'] for row in results]
        except Exception as e:
            logger.error(f"하위 카테고리 목록 조회 오류: {e}")
            return []