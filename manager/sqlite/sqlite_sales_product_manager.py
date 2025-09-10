"""
SQLite 판매 제품 관리자 - 판매 제품 관리, 가격 책정
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

class SQLiteSalesProductManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 판매 제품 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sales_products (
                        sales_product_id TEXT PRIMARY KEY,
                        product_code TEXT NOT NULL,
                        product_name TEXT NOT NULL,
                        product_name_en TEXT,
                        product_name_vi TEXT,
                        category TEXT,
                        subcategory TEXT,
                        brand TEXT,
                        model TEXT,
                        specifications TEXT,
                        description TEXT,
                        base_product_id TEXT,
                        status TEXT DEFAULT 'active',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 판매 가격 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sales_prices (
                        price_id TEXT PRIMARY KEY,
                        sales_product_id TEXT NOT NULL,
                        customer_type TEXT DEFAULT 'general',
                        customer_id TEXT,
                        price_type TEXT DEFAULT 'list',
                        price_vnd REAL DEFAULT 0,
                        price_usd REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        min_quantity INTEGER DEFAULT 1,
                        max_quantity INTEGER,
                        discount_rate REAL DEFAULT 0,
                        margin_rate REAL DEFAULT 0,
                        cost_price REAL DEFAULT 0,
                        valid_from TEXT,
                        valid_to TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sales_product_id) REFERENCES sales_products (sales_product_id)
                    )
                ''')
                
                # 판매 제품 이미지/문서 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sales_product_attachments (
                        attachment_id TEXT PRIMARY KEY,
                        sales_product_id TEXT NOT NULL,
                        attachment_type TEXT DEFAULT 'image',
                        file_name TEXT,
                        file_path TEXT,
                        file_size INTEGER DEFAULT 0,
                        description TEXT,
                        display_order INTEGER DEFAULT 0,
                        is_primary INTEGER DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sales_product_id) REFERENCES sales_products (sales_product_id)
                    )
                ''')
                
                conn.commit()
                logger.info("판매 제품 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_product_standard_price(self, product_code):
        """제품의 표준 판매가격 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.product_code,
                        sp.product_name,
                        spr.price_vnd,
                        spr.price_usd,
                        spr.currency
                    FROM sales_products sp
                    JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                    WHERE sp.product_code = ? 
                    AND sp.status = "active" 
                    AND spr.is_active = 1
                    AND spr.price_type = 'list'
                    ORDER BY spr.created_date DESC
                    LIMIT 1
                """
                
                df = pd.read_sql_query(query, conn, params=[product_code])
                if not df.empty:
                    return df.iloc[0].to_dict()
                return None
        except Exception as e:
            logger.error(f"표준 가격 조회 오류: {e}")
            return None

    def get_sales_products(self, category=None, status='active', search_term=None):
        """판매 제품 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM sales_products WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                if search_term:
                    query += " AND (product_name LIKE ? OR product_code LIKE ? OR description LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"판매 제품 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_sales_product(self, product_data):
        """판매 제품 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['sales_product_id', 'product_code', 'product_name']
                for field in required_fields:
                    if field not in product_data or not product_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                product_record = {
                    'sales_product_id': product_data['sales_product_id'],
                    'product_code': product_data['product_code'],
                    'product_name': product_data['product_name'],
                    'product_name_en': product_data.get('product_name_en', ''),
                    'product_name_vi': product_data.get('product_name_vi', ''),
                    'category': product_data.get('category', ''),
                    'subcategory': product_data.get('subcategory', ''),
                    'brand': product_data.get('brand', ''),
                    'model': product_data.get('model', ''),
                    'specifications': product_data.get('specifications', ''),
                    'description': product_data.get('description', ''),
                    'base_product_id': product_data.get('base_product_id', ''),
                    'status': product_data.get('status', 'active'),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO sales_products (
                        sales_product_id, product_code, product_name, product_name_en, product_name_vi,
                        category, subcategory, brand, model, specifications,
                        description, base_product_id, status, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(product_record.values()))
                
                conn.commit()
                logger.info(f"판매 제품 추가 완료: {product_data['sales_product_id']}")
                return True
                
        except Exception as e:
            logger.error(f"판매 제품 추가 실패: {str(e)}")
            return False

    def update_sales_product(self, sales_product_id, updates):
        """판매 제품 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [sales_product_id]
                
                cursor.execute(f'''
                    UPDATE sales_products 
                    SET {set_clause}
                    WHERE sales_product_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"판매 제품 수정 완료: {sales_product_id}")
                    return True
                else:
                    logger.warning(f"수정할 판매 제품 없음: {sales_product_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"판매 제품 수정 실패: {str(e)}")
            return False

    def get_sales_prices(self, sales_product_id=None, customer_type=None, customer_id=None):
        """판매 가격 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM sales_prices WHERE is_active = 1"
                params = []
                
                if sales_product_id:
                    query += " AND sales_product_id = ?"
                    params.append(sales_product_id)
                if customer_type:
                    query += " AND customer_type = ?"
                    params.append(customer_type)
                if customer_id:
                    query += " AND (customer_id = ? OR customer_id IS NULL OR customer_id = '')"
                    params.append(customer_id)
                
                query += " ORDER BY customer_id IS NOT NULL DESC, valid_from DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"판매 가격 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_sales_price(self, price_data):
        """판매 가격 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['price_id', 'sales_product_id']
                for field in required_fields:
                    if field not in price_data or not price_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                price_record = {
                    'price_id': price_data['price_id'],
                    'sales_product_id': price_data['sales_product_id'],
                    'customer_type': price_data.get('customer_type', 'general'),
                    'customer_id': price_data.get('customer_id', ''),
                    'price_type': price_data.get('price_type', 'list'),
                    'price_vnd': price_data.get('price_vnd', 0),
                    'price_usd': price_data.get('price_usd', 0),
                    'currency': price_data.get('currency', 'VND'),
                    'min_quantity': price_data.get('min_quantity', 1),
                    'max_quantity': price_data.get('max_quantity', None),
                    'discount_rate': price_data.get('discount_rate', 0),
                    'margin_rate': price_data.get('margin_rate', 0),
                    'cost_price': price_data.get('cost_price', 0),
                    'valid_from': price_data.get('valid_from', ''),
                    'valid_to': price_data.get('valid_to', ''),
                    'is_active': price_data.get('is_active', 1),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO sales_prices (
                        price_id, sales_product_id, customer_type, customer_id, price_type,
                        price_vnd, price_usd, currency, min_quantity, max_quantity,
                        discount_rate, margin_rate, cost_price, valid_from, valid_to,
                        is_active, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(price_record.values()))
                
                conn.commit()
                logger.info(f"판매 가격 추가 완료: {price_data['price_id']}")
                return True
                
        except Exception as e:
            logger.error(f"판매 가격 추가 실패: {str(e)}")
            return False

    def update_sales_price(self, price_id, updates):
        """판매 가격 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [price_id]
                
                cursor.execute(f'''
                    UPDATE sales_prices 
                    SET {set_clause}
                    WHERE price_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"판매 가격 수정 완료: {price_id}")
                    return True
                else:
                    logger.warning(f"수정할 판매 가격 없음: {price_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"판매 가격 수정 실패: {str(e)}")
            return False

    def get_product_with_prices(self, sales_product_id=None, category=None):
        """제품과 가격 정보 함께 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        sp.*,
                        sr.price_id,
                        sr.price_vnd,
                        sr.price_usd,
                        sr.currency,
                        sr.customer_type,
                        sr.discount_rate,
                        sr.margin_rate,
                        sr.valid_from,
                        sr.valid_to
                    FROM sales_products sp
                    LEFT JOIN sales_prices sr ON sp.sales_product_id = sr.sales_product_id
                    WHERE sp.status = 'active' AND (sr.is_active = 1 OR sr.is_active IS NULL)
                '''
                params = []
                
                if sales_product_id:
                    query += " AND sp.sales_product_id = ?"
                    params.append(sales_product_id)
                if category:
                    query += " AND sp.category = ?"
                    params.append(category)
                
                query += " ORDER BY sp.created_date DESC, sr.customer_id IS NOT NULL DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"제품 및 가격 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_best_price(self, sales_product_id, customer_id=None, quantity=1):
        """최적 가격 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM sales_prices 
                    WHERE sales_product_id = ? 
                        AND is_active = 1
                        AND (min_quantity <= ? OR min_quantity IS NULL)
                        AND (max_quantity >= ? OR max_quantity IS NULL)
                        AND (customer_id = ? OR customer_id IS NULL OR customer_id = '')
                        AND (valid_from <= date('now') OR valid_from IS NULL OR valid_from = '')
                        AND (valid_to >= date('now') OR valid_to IS NULL OR valid_to = '')
                    ORDER BY 
                        customer_id IS NOT NULL DESC,
                        discount_rate DESC,
                        price_vnd ASC
                    LIMIT 1
                '''
                params = [sales_product_id, quantity, quantity, customer_id or '']
                
                df = pd.read_sql_query(query, conn, params=params)
                return df.iloc[0] if not df.empty else None
                
        except Exception as e:
            logger.error(f"최적 가격 조회 실패: {str(e)}")
            return None

    def migrate_from_csv(self, products_csv_path=None, prices_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 판매 제품 데이터 마이그레이션
            if products_csv_path is None:
                products_csv_path = os.path.join("data", "sales_products.csv")
            
            if os.path.exists(products_csv_path):
                df = pd.read_csv(products_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        product_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in product_data.items():
                            if pd.isna(value):
                                product_data[key] = ''
                        
                        self.add_sales_product(product_data)
                    
                    logger.info(f"판매 제품 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 판매 가격 데이터 마이그레이션
            if prices_csv_path is None:
                prices_csv_path = os.path.join("data", "sales_prices.csv")
            
            if os.path.exists(prices_csv_path):
                df = pd.read_csv(prices_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        price_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in price_data.items():
                            if pd.isna(value):
                                if key in ['price_vnd', 'price_usd', 'min_quantity', 'max_quantity', 'discount_rate', 'margin_rate', 'cost_price']:
                                    price_data[key] = 0
                                elif key == 'is_active':
                                    price_data[key] = 1
                                else:
                                    price_data[key] = ''
                        
                        self.add_sales_price(price_data)
                    
                    logger.info(f"판매 가격 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False
    def get_all_prices(self):
        """모든 판매 가격 정보를 가져옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.sales_product_id,
                        sp.product_code,
                        sp.product_name,
                        sp.category,
                        spr.price_id,
                        spr.price_vnd,
                        spr.price_usd,
                        spr.currency,
                        spr.customer_type,
                        spr.valid_from,
                        spr.valid_to,
                        spr.is_active
                    FROM sales_products sp
                    LEFT JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                    WHERE sp.status = "active" AND (spr.is_active = 1 OR spr.is_active IS NULL)
                    ORDER BY sp.product_name
                """
                
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"판매 가격 조회 오류: {e}")
            return pd.DataFrame()

    def search_prices(self, product_code=None, product_name=None, category=None, 
                     is_current_only=False, search_term=None):
        """가격 검색 - 레거시 매니저와 호환성 유지"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.product_code,
                        sp.product_name,
                        sp.category,
                        spr.price_vnd,
                        spr.price_usd,
                        spr.currency,
                        spr.is_active,
                        spr.valid_from,
                        spr.valid_to
                    FROM sales_products sp
                    LEFT JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                    WHERE sp.status = "active"
                """
                params = []
                
                if is_current_only:
                    query += " AND spr.is_active = 1"
                
                if product_code:
                    query += " AND sp.product_code LIKE ?"
                    params.append(f"%{product_code}%")
                
                if product_name:
                    query += " AND sp.product_name LIKE ?"
                    params.append(f"%{product_name}%")
                
                if search_term:
                    query += " AND (sp.product_name LIKE ? OR sp.product_code LIKE ?)"
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                
                if category:
                    query += " AND sp.category = ?"
                    params.append(category)
                
                query += " ORDER BY sp.product_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"가격 검색 오류: {e}")
            return pd.DataFrame()

    def get_price_change_history(self, product_code=None):
        """가격 변경 이력"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.product_code,
                        sp.product_name,
                        spr.price_vnd,
                        spr.price_usd,
                        spr.valid_from,
                        spr.valid_to,
                        spr.created_date
                    FROM sales_products sp
                    JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                """
                params = []
                
                if product_code:
                    query += " WHERE sp.product_code = ?"
                    params.append(product_code)
                
                query += " ORDER BY sp.product_code, spr.created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"가격 변경 이력 조회 오류: {e}")
            return pd.DataFrame()

    def get_sales_data(self):
        """판매 데이터 조회"""
        return self.get_all_prices()

    def get_master_products_for_sales(self):
        """판매가 설정 가능한 마스터 제품 목록을 조회합니다 (MB 제외)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            
            master_manager = SQLiteMasterProductManager()
            all_products = master_manager.get_all_products()
            
            # None 체크
            if all_products is None:
                return pd.DataFrame()
            
            # DataFrame 빈 값 체크
            if isinstance(all_products, pd.DataFrame) and len(all_products) == 0:
                return pd.DataFrame()
            
            # 리스트 빈 값 체크
            if isinstance(all_products, list) and len(all_products) == 0:
                return pd.DataFrame()
            
            # DataFrame이 아닌 경우 (list) DataFrame으로 변환
            if isinstance(all_products, list):
                all_products = pd.DataFrame(all_products)
            
            # MB 제품 제외 (외주 공급가 관리에서만 다룸)
            if 'main_category' in all_products.columns:
                non_mb_products = all_products[all_products['main_category'] != 'MB'].copy()
            elif 'category_name' in all_products.columns:
                non_mb_products = all_products[all_products['category_name'] != 'MB'].copy()
            else:
                # 카테고리 컬럼이 없으면 모든 제품 반환
                non_mb_products = all_products.copy()
            
            return non_mb_products
            
        except Exception as e:
            logger.error(f"마스터 제품 조회 오류: {e}")
            return pd.DataFrame()

    def get_price_variance_analysis(self):
        """가격 편차 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.category,
                        AVG(spr.price_usd) as avg_price,
                        MIN(spr.price_usd) as min_price,
                        MAX(spr.price_usd) as max_price,
                        COUNT(*) as product_count
                    FROM sales_products sp
                    JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                    WHERE spr.is_active = 1 AND spr.price_usd > 0
                    GROUP BY sp.category
                    ORDER BY avg_price DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"가격 편차 분석 오류: {e}")
            return pd.DataFrame()

    def add_standard_price(self, price_data):
        """표준 가격 추가 (판매 제품 페이지에서 사용)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 데이터 검사
                product_code = price_data.get('product_code')
                if not product_code:
                    raise ValueError("제품 코드가 필요합니다")
                
                # 판매 제품이 이미 등록되어 있는지 확인
                cursor.execute("""
                    SELECT sales_product_id FROM sales_products 
                    WHERE product_code = ? AND status = 'active'
                """, (product_code,))
                
                existing_product = cursor.fetchone()
                
                if existing_product:
                    sales_product_id = existing_product[0]
                else:
                    # 새로운 판매 제품 등록
                    sales_product_id = f"SALES_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product_code}"
                    
                    cursor.execute("""
                        INSERT INTO sales_products (
                            sales_product_id, product_code, product_name, category,
                            status, created_date
                        ) VALUES (?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                    """, (
                        sales_product_id,
                        product_code,
                        price_data.get('product_name', ''),
                        price_data.get('category', 'GENERAL')
                    ))
                
                # 기존 가격 비활성화
                cursor.execute("""
                    UPDATE sales_prices 
                    SET is_active = 0, valid_to = CURRENT_TIMESTAMP
                    WHERE sales_product_id = ? AND is_active = 1
                """, (sales_product_id,))
                
                # 새로운 가격 추가
                price_id = f"PRICE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sales_product_id}"
                
                # 가격 데이터 준비
                price_usd = float(price_data.get('standard_price_usd', 0))
                price_local = float(price_data.get('standard_price_local', 0))
                local_currency = price_data.get('local_currency', 'VND')
                
                # VND로 통일하여 저장
                if local_currency == 'USD':
                    price_vnd = 0
                    price_usd = price_local
                else:
                    price_vnd = price_local
                
                cursor.execute("""
                    INSERT INTO sales_prices (
                        price_id, sales_product_id, price_vnd, price_usd, currency,
                        price_type, is_active, valid_from, created_date
                    ) VALUES (?, ?, ?, ?, ?, 'list', 1, ?, CURRENT_TIMESTAMP)
                """, (
                    price_id,
                    sales_product_id,
                    price_vnd,
                    price_usd,
                    local_currency,
                    price_data.get('effective_date', datetime.now().strftime('%Y-%m-%d'))
                ))
                
                conn.commit()
                logger.info(f"표준 가격 추가 완료: {product_code}")
                return True
                
        except Exception as e:
            logger.error(f"표준 가격 추가 실패: {e}")
            raise

    def get_sales_performance_analysis(self):
        """판매 성과 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        sp.category,
                        COUNT(DISTINCT sp.sales_product_id) as total_products,
                        COUNT(spr.price_id) as priced_products,
                        AVG(spr.price_usd) as avg_price
                    FROM sales_products sp
                    LEFT JOIN sales_prices spr ON sp.sales_product_id = spr.sales_product_id
                    WHERE sp.status = "active"
                    GROUP BY sp.category
                    ORDER BY total_products DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"판매 성과 분석 오류: {e}")
            return pd.DataFrame()

    def update_sales_product(self, sales_product_id, update_data):
        """판매 제품 정보 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업데이트할 필드 동적 생성
                set_clauses = []
                params = []
                
                updatable_fields = [
                    'product_name', 'product_name_en', 'product_name_vi',
                    'category', 'subcategory', 'brand', 'model',
                    'specifications', 'description', 'status'
                ]
                
                for field in updatable_fields:
                    if field in update_data:
                        set_clauses.append(f"{field} = ?")
                        params.append(update_data[field])
                
                if not set_clauses:
                    return False
                
                # updated_date 추가
                set_clauses.append("updated_date = CURRENT_TIMESTAMP")
                params.append(sales_product_id)
                
                query = f"""
                    UPDATE sales_products 
                    SET {', '.join(set_clauses)}
                    WHERE sales_product_id = ?
                """
                
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"판매 제품 업데이트 완료: {sales_product_id}")
                    return True
                else:
                    logger.warning(f"업데이트할 판매 제품을 찾을 수 없음: {sales_product_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"판매 제품 업데이트 실패: {e}")
            return False

    def delete_sales_product(self, sales_product_id):
        """판매 제품 삭제 (관련 가격 정보도 함께 삭제)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 먼저 관련 가격 정보 삭제
                cursor.execute("DELETE FROM sales_prices WHERE sales_product_id = ?", (sales_product_id,))
                price_deleted = cursor.rowcount
                
                # 판매 제품 삭제
                cursor.execute("DELETE FROM sales_products WHERE sales_product_id = ?", (sales_product_id,))
                product_deleted = cursor.rowcount
                
                conn.commit()
                
                if product_deleted > 0:
                    logger.info(f"판매 제품 삭제 완료: {sales_product_id} (관련 가격 {price_deleted}개 함께 삭제)")
                    return True
                else:
                    logger.warning(f"삭제할 판매 제품을 찾을 수 없음: {sales_product_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"판매 제품 삭제 실패: {e}")
            return False

    def get_sales_product_by_id(self, sales_product_id):
        """판매 제품 ID로 제품 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM sales_products 
                    WHERE sales_product_id = ? AND status = 'active'
                """
                
                cursor = conn.execute(query, (sales_product_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"판매 제품 조회 실패: {e}")
            return None

