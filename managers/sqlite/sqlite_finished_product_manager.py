"""
SQLite 완성품 관리자 - 완성된 제품 코드 전용 관리
견적서, 발주서, 출고 확인서에 사용되는 완성품 정보 관리
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteFinishedProductManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 완성품 마스터 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS finished_products (
                        finished_product_id TEXT PRIMARY KEY,
                        product_code TEXT UNIQUE NOT NULL,
                        product_name_ko TEXT NOT NULL,
                        product_name_en TEXT,
                        product_name_vi TEXT,
                        description TEXT,
                        specifications TEXT,
                        unit TEXT DEFAULT 'EA',
                        category TEXT,
                        subcategory TEXT,
                        brand TEXT,
                        model TEXT,
                        origin_country TEXT,
                        manufacturer TEXT,
                        status TEXT DEFAULT 'active',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 완성품 가격 관리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS finished_product_prices (
                        price_id TEXT PRIMARY KEY,
                        finished_product_id TEXT NOT NULL,
                        supplier_price_vnd REAL DEFAULT 0,
                        supplier_price_usd REAL DEFAULT 0,
                        selling_price_vnd REAL DEFAULT 0,
                        selling_price_usd REAL DEFAULT 0,
                        cost_price_vnd REAL DEFAULT 0,
                        cost_price_usd REAL DEFAULT 0,
                        margin_rate REAL DEFAULT 0,
                        discount_rate REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        valid_from TEXT,
                        valid_to TEXT,
                        is_active INTEGER DEFAULT 1,
                        price_type TEXT DEFAULT 'standard',
                        notes TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (finished_product_id) REFERENCES finished_products (finished_product_id)
                    )
                ''')
                
                # 완성품 문서 연결 테이블 (견적서, 발주서, 출고확인서 등에서 사용)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS finished_product_documents (
                        document_id TEXT PRIMARY KEY,
                        finished_product_id TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        document_number TEXT,
                        quantity INTEGER DEFAULT 1,
                        unit_price REAL DEFAULT 0,
                        total_price REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        document_date TEXT,
                        customer_id TEXT,
                        supplier_id TEXT,
                        notes TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (finished_product_id) REFERENCES finished_products (finished_product_id)
                    )
                ''')
                
                conn.commit()
                logger.info("완성품 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"완성품 테이블 초기화 오류: {str(e)}")
            
    def get_connection(self):
        """DB 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def generate_product_id(self):
        """완성품 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"FP{timestamp}"
    
    def generate_price_id(self):
        """가격 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"FPP{timestamp}"
    
    def add_finished_product(self, product_code, product_name_ko, product_name_en=None, 
                           product_name_vi=None, description=None, specifications=None,
                           unit='EA', category=None, subcategory=None, brand=None, 
                           model=None, origin_country=None, manufacturer=None):
        """완성품 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 중복 코드 확인
                cursor.execute('SELECT product_code FROM finished_products WHERE product_code = ?', (product_code,))
                if cursor.fetchone():
                    return False, f"제품 코드 '{product_code}'가 이미 존재합니다."
                
                finished_product_id = self.generate_product_id()
                
                cursor.execute('''
                    INSERT INTO finished_products 
                    (finished_product_id, product_code, product_name_ko, product_name_en, 
                     product_name_vi, description, specifications, unit, category, 
                     subcategory, brand, model, origin_country, manufacturer, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (finished_product_id, product_code, product_name_ko, product_name_en,
                      product_name_vi, description, specifications, unit, category,
                      subcategory, brand, model, origin_country, manufacturer,
                      datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
                logger.info(f"완성품 추가 성공: {product_code}")
                return True, finished_product_id
                
        except Exception as e:
            logger.error(f"완성품 추가 오류: {str(e)}")
            return False, str(e)
    
    def add_product_price(self, finished_product_id, supplier_price_vnd=0, supplier_price_usd=0,
                         selling_price_vnd=0, selling_price_usd=0, cost_price_vnd=0, 
                         cost_price_usd=0, margin_rate=0, discount_rate=0, currency='VND',
                         valid_from=None, valid_to=None, price_type='standard', notes=None):
        """완성품 가격 정보 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 활성 가격 비활성화
                cursor.execute('''
                    UPDATE finished_product_prices 
                    SET is_active = 0, updated_date = ?
                    WHERE finished_product_id = ? AND is_active = 1
                ''', (datetime.now().isoformat(), finished_product_id))
                
                price_id = self.generate_price_id()
                
                cursor.execute('''
                    INSERT INTO finished_product_prices 
                    (price_id, finished_product_id, supplier_price_vnd, supplier_price_usd,
                     selling_price_vnd, selling_price_usd, cost_price_vnd, cost_price_usd,
                     margin_rate, discount_rate, currency, valid_from, valid_to, 
                     price_type, notes, created_date, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (price_id, finished_product_id, supplier_price_vnd, supplier_price_usd,
                      selling_price_vnd, selling_price_usd, cost_price_vnd, cost_price_usd,
                      margin_rate, discount_rate, currency, valid_from, valid_to,
                      price_type, notes, datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
                logger.info(f"완성품 가격 정보 추가 성공: {price_id}")
                return True, price_id
                
        except Exception as e:
            logger.error(f"완성품 가격 추가 오류: {str(e)}")
            return False, str(e)
    
    def get_all_finished_products(self):
        """모든 완성품 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT fp.*, fpp.supplier_price_vnd, fpp.supplier_price_usd,
                           fpp.selling_price_vnd, fpp.selling_price_usd, fpp.cost_price_vnd,
                           fpp.cost_price_usd, fpp.margin_rate, fpp.currency
                    FROM finished_products fp
                    LEFT JOIN finished_product_prices fpp ON fp.finished_product_id = fpp.finished_product_id 
                                                         AND fpp.is_active = 1
                    WHERE fp.status = 'active'
                    ORDER BY fp.product_code
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"완성품 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_finished_product_by_code(self, product_code):
        """제품 코드로 완성품 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT fp.*, fpp.supplier_price_vnd, fpp.supplier_price_usd,
                           fpp.selling_price_vnd, fpp.selling_price_usd, fpp.cost_price_vnd,
                           fpp.cost_price_usd, fpp.margin_rate, fpp.currency, fpp.notes
                    FROM finished_products fp
                    LEFT JOIN finished_product_prices fpp ON fp.finished_product_id = fpp.finished_product_id 
                                                         AND fpp.is_active = 1
                    WHERE fp.product_code = ? AND fp.status = 'active'
                '''
                
                df = pd.read_sql_query(query, conn, params=(product_code,))
                return df.iloc[0] if not df.empty else None
                
        except Exception as e:
            logger.error(f"완성품 코드 조회 오류: {str(e)}")
            return None
    
    def update_finished_product(self, finished_product_id, **kwargs):
        """완성품 정보 수정"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 수정할 필드들 동적 구성
                update_fields = []
                update_values = []
                
                for field, value in kwargs.items():
                    if field in ['product_name_ko', 'product_name_en', 'product_name_vi', 
                               'description', 'specifications', 'unit', 'category', 
                               'subcategory', 'brand', 'model', 'origin_country', 'manufacturer']:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if update_fields:
                    update_fields.append("updated_date = ?")
                    update_values.append(datetime.now().isoformat())
                    update_values.append(finished_product_id)
                    
                    query = f"UPDATE finished_products SET {', '.join(update_fields)} WHERE finished_product_id = ?"
                    cursor.execute(query, update_values)
                    
                    conn.commit()
                    logger.info(f"완성품 정보 수정 성공: {finished_product_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"완성품 정보 수정 오류: {str(e)}")
            return False
    
    def delete_finished_product(self, finished_product_id):
        """완성품 삭제 (상태만 변경)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE finished_products 
                    SET status = 'deleted', updated_date = ?
                    WHERE finished_product_id = ?
                ''', (datetime.now().isoformat(), finished_product_id))
                
                conn.commit()
                logger.info(f"완성품 삭제 성공: {finished_product_id}")
                return True
                
        except Exception as e:
            logger.error(f"완성품 삭제 오류: {str(e)}")
            return False
    
    def get_products_for_document(self, document_type=None):
        """문서용 완성품 목록 조회 (견적서, 발주서, 출고확인서 등)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT fp.finished_product_id, fp.product_code, fp.product_name_ko,
                           fp.product_name_en, fp.product_name_vi, fp.unit,
                           fpp.selling_price_vnd, fpp.selling_price_usd, fpp.supplier_price_vnd,
                           fpp.supplier_price_usd, fpp.currency
                    FROM finished_products fp
                    LEFT JOIN finished_product_prices fpp ON fp.finished_product_id = fpp.finished_product_id 
                                                         AND fpp.is_active = 1
                    WHERE fp.status = 'active'
                    ORDER BY fp.product_code
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"문서용 완성품 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def add_document_usage(self, finished_product_id, document_type, document_number=None,
                          quantity=1, unit_price=0, total_price=0, currency='VND',
                          document_date=None, customer_id=None, supplier_id=None, notes=None):
        """완성품 문서 사용 기록 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                document_id = f"DOC{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                cursor.execute('''
                    INSERT INTO finished_product_documents 
                    (document_id, finished_product_id, document_type, document_number,
                     quantity, unit_price, total_price, currency, document_date,
                     customer_id, supplier_id, notes, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (document_id, finished_product_id, document_type, document_number,
                      quantity, unit_price, total_price, currency, document_date,
                      customer_id, supplier_id, notes, datetime.now().isoformat()))
                
                conn.commit()
                logger.info(f"완성품 문서 사용 기록 추가: {document_id}")
                return True, document_id
                
        except Exception as e:
            logger.error(f"완성품 문서 사용 기록 오류: {str(e)}")
            return False, str(e)