"""
SQLite 통합 제품 관리자 - 전체 제품 통합 관리
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

class SQLiteMasterProductManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 통합 제품 마스터 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS master_products (
                        master_product_id TEXT PRIMARY KEY,
                        product_code TEXT UNIQUE NOT NULL,
                        product_name TEXT NOT NULL,
                        product_name_en TEXT,
                        product_name_vi TEXT,
                        category_id TEXT,
                        category_name TEXT,
                        subcategory_id TEXT,
                        subcategory_name TEXT,
                        brand TEXT,
                        model TEXT,
                        description TEXT,
                        specifications TEXT,
                        unit TEXT DEFAULT 'EA',
                        weight REAL DEFAULT 0,
                        dimensions TEXT,
                        color TEXT,
                        material TEXT,
                        origin_country TEXT,
                        manufacturer TEXT,
                        supplier_id TEXT,
                        supplier_name TEXT,
                        status TEXT DEFAULT 'active',
                        is_sellable INTEGER DEFAULT 1,
                        is_purchasable INTEGER DEFAULT 1,
                        is_trackable INTEGER DEFAULT 1,
                        min_stock_level INTEGER DEFAULT 0,
                        max_stock_level INTEGER DEFAULT 1000,
                        reorder_point INTEGER DEFAULT 10,
                        lead_time_days INTEGER DEFAULT 7,
                        shelf_life_days INTEGER DEFAULT 0,
                        barcode TEXT,
                        sku TEXT,
                        internal_code TEXT,
                        tags TEXT,
                        attachments TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 제품 가격 통합 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS master_product_prices (
                        price_id TEXT PRIMARY KEY,
                        master_product_id TEXT NOT NULL,
                        price_type TEXT DEFAULT 'purchase',
                        customer_type TEXT DEFAULT 'general',
                        supplier_id TEXT,
                        currency TEXT DEFAULT 'VND',
                        price REAL DEFAULT 0,
                        cost_price REAL DEFAULT 0,
                        markup_percentage REAL DEFAULT 0,
                        discount_percentage REAL DEFAULT 0,
                        min_quantity INTEGER DEFAULT 1,
                        max_quantity INTEGER,
                        valid_from TEXT,
                        valid_to TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (master_product_id) REFERENCES master_products (master_product_id)
                    )
                ''')
                
                # 제품 재고 통합 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS master_product_inventory (
                        inventory_id TEXT PRIMARY KEY,
                        master_product_id TEXT NOT NULL,
                        location_id TEXT DEFAULT 'MAIN',
                        location_name TEXT DEFAULT '메인창고',
                        current_stock INTEGER DEFAULT 0,
                        reserved_stock INTEGER DEFAULT 0,
                        available_stock INTEGER DEFAULT 0,
                        in_transit_stock INTEGER DEFAULT 0,
                        damaged_stock INTEGER DEFAULT 0,
                        last_count_date TEXT,
                        last_count_by TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (master_product_id) REFERENCES master_products (master_product_id)
                    )
                ''')
                
                conn.commit()
                logger.info("통합 제품 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_master_products(self, category=None, status='active', search_term=None, is_sellable=None):
        """통합 제품 조회 (DataFrame 반환)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM master_products WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND (category_name = ? OR category_id = ?)"
                    params.extend([category, category])
                if is_sellable is not None:
                    query += " AND is_sellable = ?"
                    params.append(1 if is_sellable else 0)
                if search_term:
                    query += " AND (product_name LIKE ? OR product_code LIKE ? OR description LIKE ? OR brand LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param, search_param])
                
                query += " ORDER BY created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"통합 제품 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_all_products(self):
        """모든 제품 조회 (DataFrame 반환 - 호환성 향상)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        master_product_id,
                        product_code,
                        product_name,
                        product_name as product_name_korean,
                        product_name_en,
                        product_name_vi,
                        category_name,
                        category_name as main_category,
                        subcategory_name,
                        brand,
                        model,
                        description,
                        specifications,
                        unit,
                        weight,
                        dimensions,
                        color,
                        material,
                        origin_country,
                        manufacturer,
                        supplier_id,
                        supplier_name,
                        supply_currency,
                        supply_price,
                        exchange_rate,
                        sales_price_vnd,
                        status,
                        is_sellable,
                        is_purchasable,
                        is_trackable,
                        min_stock_level,
                        max_stock_level,
                        reorder_point,
                        lead_time_days,
                        shelf_life_days,
                        barcode,
                        sku,
                        internal_code,
                        tags,
                        attachments,
                        'sqlite' as data_source,
                        created_date,
                        updated_date
                    FROM master_products 
                    WHERE status = 'active'
                    ORDER BY created_date DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"모든 제품 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_master_product(self, product_data):
        """통합 제품 추가 (기존 삭제된 제품이 있으면 업데이트)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['master_product_id', 'product_code', 'product_name']
                for field in required_fields:
                    if field not in product_data or not product_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                # 같은 제품 코드로 기존 제품이 있는지 확인
                cursor.execute('''
                    SELECT master_product_id, status FROM master_products 
                    WHERE product_code = ?
                ''', (product_data['product_code'],))
                existing_product = cursor.fetchone()
                
                current_time = datetime.now().isoformat()
                
                if existing_product:
                    # 기존 제품이 있으면 업데이트
                    existing_id, existing_status = existing_product
                    logger.info(f"기존 제품 발견 (상태: {existing_status}): {existing_id}, 업데이트 진행")
                    
                    update_data = {
                        'master_product_id': product_data['master_product_id'],
                        'product_name': product_data['product_name'],
                        'product_name_en': product_data.get('product_name_en', ''),
                        'product_name_vi': product_data.get('product_name_vi', ''),
                        'category_id': product_data.get('category_id', ''),
                        'category_name': product_data.get('category_name', ''),
                        'subcategory_id': product_data.get('subcategory_id', ''),
                        'subcategory_name': product_data.get('subcategory_name', ''),
                        'brand': product_data.get('brand', ''),
                        'model': product_data.get('model', ''),
                        'description': product_data.get('description', ''),
                        'specifications': product_data.get('specifications', ''),
                        'unit': product_data.get('unit', 'EA'),
                        'weight': product_data.get('weight', 0),
                        'dimensions': product_data.get('dimensions', ''),
                        'color': product_data.get('color', ''),
                        'material': product_data.get('material', ''),
                        'origin_country': product_data.get('origin_country', ''),
                        'manufacturer': product_data.get('manufacturer', ''),
                        'supplier_id': product_data.get('supplier_id', ''),
                        'supplier_name': product_data.get('supplier_name', ''),
                        'supply_currency': product_data.get('supply_currency', 'CNY'),
                        'supply_price': product_data.get('supply_price', 0),
                        'exchange_rate': product_data.get('exchange_rate', 24000),
                        'sales_price_vnd': product_data.get('sales_price_vnd', 0),
                        'status': 'active',  # 항상 활성 상태로 복원
                        'is_sellable': product_data.get('is_sellable', 1),
                        'is_purchasable': product_data.get('is_purchasable', 1),
                        'is_trackable': product_data.get('is_trackable', 1),
                        'min_stock_level': product_data.get('min_stock_level', 0),
                        'max_stock_level': product_data.get('max_stock_level', 1000),
                        'reorder_point': product_data.get('reorder_point', 10),
                        'lead_time_days': product_data.get('lead_time_days', 7),
                        'shelf_life_days': product_data.get('shelf_life_days', 0),
                        'barcode': product_data.get('barcode', ''),
                        'sku': product_data.get('sku', ''),
                        'internal_code': product_data.get('internal_code', ''),
                        'tags': product_data.get('tags', ''),
                        'attachments': json.dumps(product_data.get('attachments', [])),
                        'updated_date': current_time
                    }
                    
                    # 기존 제품 업데이트
                    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
                    values = list(update_data.values()) + [product_data['product_code']]
                    
                    cursor.execute(f'''
                        UPDATE master_products 
                        SET {set_clause}
                        WHERE product_code = ?
                    ''', values)
                    
                    logger.info(f"기존 제품 업데이트 완료: {product_data['product_code']}")
                    
                else:
                    # 새 제품 등록
                    product_record = {
                        'master_product_id': product_data['master_product_id'],
                        'product_code': product_data['product_code'],
                        'product_name': product_data['product_name'],
                        'product_name_en': product_data.get('product_name_en', ''),
                        'product_name_vi': product_data.get('product_name_vi', ''),
                        'category_id': product_data.get('category_id', ''),
                        'category_name': product_data.get('category_name', ''),
                        'subcategory_id': product_data.get('subcategory_id', ''),
                        'subcategory_name': product_data.get('subcategory_name', ''),
                        'brand': product_data.get('brand', ''),
                        'model': product_data.get('model', ''),
                        'description': product_data.get('description', ''),
                        'specifications': product_data.get('specifications', ''),
                        'unit': product_data.get('unit', 'EA'),
                        'weight': product_data.get('weight', 0),
                        'dimensions': product_data.get('dimensions', ''),
                        'color': product_data.get('color', ''),
                        'material': product_data.get('material', ''),
                        'origin_country': product_data.get('origin_country', ''),
                        'manufacturer': product_data.get('manufacturer', ''),
                        'supplier_id': product_data.get('supplier_id', ''),
                        'supplier_name': product_data.get('supplier_name', ''),
                        'supply_currency': product_data.get('supply_currency', 'CNY'),
                        'supply_price': product_data.get('supply_price', 0),
                        'exchange_rate': product_data.get('exchange_rate', 24000),
                        'sales_price_vnd': product_data.get('sales_price_vnd', 0),
                        'status': product_data.get('status', 'active'),
                        'is_sellable': product_data.get('is_sellable', 1),
                        'is_purchasable': product_data.get('is_purchasable', 1),
                        'is_trackable': product_data.get('is_trackable', 1),
                        'min_stock_level': product_data.get('min_stock_level', 0),
                        'max_stock_level': product_data.get('max_stock_level', 1000),
                        'reorder_point': product_data.get('reorder_point', 10),
                        'lead_time_days': product_data.get('lead_time_days', 7),
                        'shelf_life_days': product_data.get('shelf_life_days', 0),
                        'barcode': product_data.get('barcode', ''),
                        'sku': product_data.get('sku', ''),
                        'internal_code': product_data.get('internal_code', ''),
                        'tags': product_data.get('tags', ''),
                        'attachments': json.dumps(product_data.get('attachments', [])),
                        'created_date': current_time,
                        'updated_date': current_time
                    }
                    
                    cursor.execute('''
                        INSERT INTO master_products (
                            master_product_id, product_code, product_name, product_name_en, product_name_vi,
                            category_id, category_name, subcategory_id, subcategory_name, brand,
                            model, description, specifications, unit, weight,
                            dimensions, color, material, origin_country, manufacturer,
                            supplier_id, supplier_name, supply_currency, supply_price, exchange_rate, sales_price_vnd,
                            status, is_sellable, is_purchasable,
                            is_trackable, min_stock_level, max_stock_level, reorder_point, lead_time_days,
                            shelf_life_days, barcode, sku, internal_code, tags,
                            attachments, created_date, updated_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', tuple(product_record.values()))
                    
                    # 기본 재고 레코드 생성 (새 제품인 경우만)
                    inventory_id = f"INV_{product_data['master_product_id']}_MAIN"
                    cursor.execute('''
                        INSERT INTO master_product_inventory (
                            inventory_id, master_product_id, location_id, location_name,
                            current_stock, available_stock
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (inventory_id, product_data['master_product_id'], 'MAIN', '메인창고', 0, 0))
                    
                    logger.info(f"신규 제품 추가 완료: {product_data['master_product_id']}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"통합 제품 추가 실패: {str(e)}")
            return False


    def get_product_with_inventory(self, master_product_id=None, location_id=None):
        """제품과 재고 정보 함께 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        mp.*,
                        mpi.inventory_id,
                        mpi.location_id,
                        mpi.location_name,
                        mpi.current_stock,
                        mpi.reserved_stock,
                        mpi.available_stock,
                        mpi.in_transit_stock,
                        mpi.damaged_stock,
                        mpi.last_count_date
                    FROM master_products mp
                    LEFT JOIN master_product_inventory mpi ON mp.master_product_id = mpi.master_product_id
                    WHERE mp.status = 'active'
                '''
                params = []
                
                if master_product_id:
                    query += " AND mp.master_product_id = ?"
                    params.append(master_product_id)
                if location_id:
                    query += " AND (mpi.location_id = ? OR mpi.location_id IS NULL)"
                    params.append(location_id)
                
                query += " ORDER BY mp.created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"제품 재고 정보 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_product_prices(self, master_product_id=None, price_type=None):
        """제품 가격 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM master_product_prices WHERE is_active = 1"
                params = []
                
                if master_product_id:
                    query += " AND master_product_id = ?"
                    params.append(master_product_id)
                if price_type:
                    query += " AND price_type = ?"
                    params.append(price_type)
                
                query += " ORDER BY price_type, customer_type, valid_from DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"제품 가격 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_product_price(self, price_data):
        """제품 가격 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['price_id', 'master_product_id', 'price']
                for field in required_fields:
                    if field not in price_data or price_data[field] is None:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                price_record = {
                    'price_id': price_data['price_id'],
                    'master_product_id': price_data['master_product_id'],
                    'price_type': price_data.get('price_type', 'purchase'),
                    'customer_type': price_data.get('customer_type', 'general'),
                    'supplier_id': price_data.get('supplier_id', ''),
                    'currency': price_data.get('currency', 'VND'),
                    'price': price_data['price'],
                    'cost_price': price_data.get('cost_price', 0),
                    'markup_percentage': price_data.get('markup_percentage', 0),
                    'discount_percentage': price_data.get('discount_percentage', 0),
                    'min_quantity': price_data.get('min_quantity', 1),
                    'max_quantity': price_data.get('max_quantity', None),
                    'valid_from': price_data.get('valid_from', ''),
                    'valid_to': price_data.get('valid_to', ''),
                    'is_active': price_data.get('is_active', 1),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO master_product_prices (
                        price_id, master_product_id, price_type, customer_type, supplier_id,
                        currency, price, cost_price, markup_percentage, discount_percentage,
                        min_quantity, max_quantity, valid_from, valid_to, is_active,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(price_record.values()))
                
                conn.commit()
                logger.info(f"제품 가격 추가 완료: {price_data['price_id']}")
                return True
                
        except Exception as e:
            logger.error(f"제품 가격 추가 실패: {str(e)}")
            return False

    def update_inventory(self, master_product_id, location_id, stock_changes):
        """재고 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 재고 조회
                cursor.execute('''
                    SELECT current_stock, reserved_stock 
                    FROM master_product_inventory 
                    WHERE master_product_id = ? AND location_id = ?
                ''', (master_product_id, location_id))
                
                result = cursor.fetchone()
                if not result:
                    # 재고 레코드가 없으면 생성
                    inventory_id = f"INV_{master_product_id}_{location_id}"
                    cursor.execute('''
                        INSERT INTO master_product_inventory 
                        (inventory_id, master_product_id, location_id, current_stock, available_stock)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (inventory_id, master_product_id, location_id, 0, 0))
                    current_stock, reserved_stock = 0, 0
                else:
                    current_stock, reserved_stock = result
                
                # 재고 업데이트
                new_current = current_stock + stock_changes.get('current_stock', 0)
                new_reserved = reserved_stock + stock_changes.get('reserved_stock', 0)
                new_available = new_current - new_reserved
                
                cursor.execute('''
                    UPDATE master_product_inventory 
                    SET current_stock = ?, 
                        reserved_stock = ?, 
                        available_stock = ?,
                        updated_date = ?
                    WHERE master_product_id = ? AND location_id = ?
                ''', (new_current, new_reserved, new_available, 
                      datetime.now().isoformat(), master_product_id, location_id))
                
                conn.commit()
                logger.info(f"재고 업데이트 완료: {master_product_id} at {location_id}")
                return True
                
        except Exception as e:
            logger.error(f"재고 업데이트 실패: {str(e)}")
            return False

    def get_low_stock_products(self, location_id=None):
        """재고 부족 제품 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        mp.master_product_id,
                        mp.product_code,
                        mp.product_name,
                        mp.reorder_point,
                        mpi.location_id,
                        mpi.current_stock,
                        mpi.available_stock,
                        (mp.reorder_point - mpi.available_stock) as shortage
                    FROM master_products mp
                    JOIN master_product_inventory mpi ON mp.master_product_id = mpi.master_product_id
                    WHERE mp.status = 'active' 
                        AND mp.is_trackable = 1
                        AND mpi.available_stock <= mp.reorder_point
                '''
                params = []
                
                if location_id:
                    query += " AND mpi.location_id = ?"
                    params.append(location_id)
                
                query += " ORDER BY shortage DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"재고 부족 제품 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, products_csv_path=None, prices_csv_path=None, inventory_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 제품 데이터 마이그레이션
            if products_csv_path is None:
                products_csv_path = os.path.join("data", "master_products.csv")
            
            if os.path.exists(products_csv_path):
                # CSV 파일이 헤더만 있는지 확인 (데이터 없음)
                with open(products_csv_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    if len(lines) <= 1:  # 헤더만 있거나 빈 파일
                        logger.info("CSV 파일이 비어있음 - 마이그레이션 스킵")
                        return True
                
                df = pd.read_csv(products_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        product_data = row.to_dict()
                        
                        # CSV 구조에 맞게 필드 매핑
                        if 'product_id' in product_data and 'master_product_id' not in product_data:
                            product_data['master_product_id'] = product_data['product_id']
                        elif 'master_product_id' not in product_data:
                            # master_product_id가 없으면 새로 생성
                            product_data['master_product_id'] = f"MP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(df)}"
                        
                        # product_name 필드 매핑
                        if 'product_name_korean' in product_data and 'product_name' not in product_data:
                            product_data['product_name'] = product_data['product_name_korean']
                        elif 'product_name' not in product_data:
                            product_data['product_name'] = product_data.get('product_code', '제품명 없음')
                        
                        # NaN 값 처리
                        for key, value in product_data.items():
                            if pd.isna(value):
                                if key in ['weight', 'min_stock_level', 'max_stock_level', 'reorder_point', 'lead_time_days', 'shelf_life_days', 'is_sellable', 'is_purchasable', 'is_trackable']:
                                    if key in ['is_sellable', 'is_purchasable', 'is_trackable']:
                                        product_data[key] = 1
                                    else:
                                        product_data[key] = 0
                                else:
                                    product_data[key] = ''
                        
                        # 필수 필드 확인
                        if ('master_product_id' in product_data and product_data['master_product_id'] and
                            'product_name' in product_data and product_data['product_name']):
                            self.add_master_product(product_data)
                        else:
                            logger.warning(f"필수 필드 누락으로 제품 데이터 스킵: {product_data.get('product_code', 'N/A')}")
                    
                    logger.info(f"통합 제품 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False

    def get_statistics(self):
        """통합 제품 통계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기본 통계
                stats_query = '''
                    SELECT 
                        COUNT(*) as total_products,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_products,
                        COUNT(CASE WHEN is_sellable = 1 THEN 1 END) as sellable_products,
                        COUNT(CASE WHEN is_purchasable = 1 THEN 1 END) as purchasable_products,
                        COUNT(DISTINCT category_name) as total_categories,
                        COUNT(DISTINCT supplier_name) as total_suppliers
                    FROM master_products
                '''
                
                cursor = conn.execute(stats_query)
                stats = cursor.fetchone()
                
                # 카테고리별 통계
                category_query = '''
                    SELECT category_name, COUNT(*) as count
                    FROM master_products 
                    WHERE status = 'active'
                    GROUP BY category_name
                    ORDER BY count DESC
                '''
                
                category_df = pd.read_sql_query(category_query, conn)
                
                return {
                    'total_products': stats[0] if stats else 0,
                    'active_products': stats[1] if stats else 0,
                    'sellable_products': stats[2] if stats else 0,
                    'purchasable_products': stats[3] if stats else 0,
                    'total_categories': stats[4] if stats else 0,
                    'total_suppliers': stats[5] if stats else 0,
                    'category_breakdown': category_df
                }
                
        except Exception as e:
            logger.error(f"통합 제품 통계 조회 실패: {str(e)}")
            return {
                'total_products': 0,
                'active_products': 0,
                'sellable_products': 0,
                'purchasable_products': 0,
                'total_categories': 0,
                'total_suppliers': 0,
                'category_breakdown': pd.DataFrame()
            }

    def get_product_by_code(self, product_code):
        """제품 코드로 제품 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        master_product_id,
                        product_code,
                        product_name,
                        product_name_en,
                        product_name_vi,
                        category_name,
                        main_category,
                        sub_category,
                        brand,
                        model,
                        description,
                        specifications,
                        unit,
                        weight,
                        dimensions,
                        color,
                        material,
                        origin_country,
                        manufacturer,
                        supplier_id,
                        supplier_name,
                        supplier_product_code,
                        cost_price,
                        recommended_price_usd,
                        recommended_price_vnd,
                        min_stock_level,
                        max_stock_level,
                        reorder_point,
                        lead_time_days,
                        shelf_life_days,
                        storage_conditions,
                        hs_code,
                        certifications,
                        is_sellable,
                        is_purchasable,
                        is_trackable,
                        status,
                        tags,
                        notes,
                        created_date,
                        updated_date
                    FROM master_products 
                    WHERE product_code = ? AND status = 'active'
                '''
                
                cursor = conn.execute(query, (product_code,))
                row = cursor.fetchone()
                
                if row:
                    # 컬럼명과 값을 매핑하여 딕셔너리로 반환
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"제품 코드 조회 실패: {str(e)}")
            return None


    def get_categories(self):
        """모든 제품 카테고리 목록을 가져옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT category_name FROM master_products WHERE category_name IS NOT NULL AND category_name != \"\" ORDER BY category_name")
                results = cursor.fetchall()
                categories = [row[0] for row in results]
                
                # 기본 카테고리 추가
                default_categories = ["HRC", "MB", "PLC", "HMI", "SENSOR", "MOTOR", "VALVE", "ACTUATOR"]
                for category in default_categories:
                    if category not in categories:
                        categories.append(category)
                
                return sorted(categories)
        except Exception as e:
            logger.error(f"카테고리 목록 조회 오류: {e}")
            return ["HRC", "MB", "PLC", "HMI", "SENSOR", "MOTOR", "VALVE", "ACTUATOR"]

    def update_master_product(self, master_product_id, update_data):
        """통합 제품 정보 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업데이트 데이터 가공
                update_data['updated_date'] = datetime.now().isoformat()
                
                # SQL 문 생성
                set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
                values = list(update_data.values()) + [master_product_id]
                
                cursor.execute(f'''
                    UPDATE master_products 
                    SET {set_clause}
                    WHERE master_product_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    logger.info(f"통합 제품 수정 완료: {master_product_id}")
                    return True
                else:
                    logger.warning(f"수정할 제품을 찾을 수 없음: {master_product_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"통합 제품 수정 실패: {str(e)}")
            return False

    def delete_master_product(self, master_product_id, hard_delete=True):
        """통합 제품 완전 삭제 또는 비활성화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if hard_delete:
                    # 완전 삭제 - 관련 데이터도 모두 삭제
                    
                    # 1. 제품 재고 데이터 삭제
                    cursor.execute('''
                        DELETE FROM master_product_inventory 
                        WHERE master_product_id = ?
                    ''', (master_product_id,))
                    
                    # 2. 제품 가격 데이터 삭제
                    cursor.execute('''
                        DELETE FROM master_product_prices 
                        WHERE master_product_id = ?
                    ''', (master_product_id,))
                    
                    # 3. 메인 제품 데이터 삭제
                    cursor.execute('''
                        DELETE FROM master_products 
                        WHERE master_product_id = ?
                    ''', (master_product_id,))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"통합 제품 완전 삭제 완료: {master_product_id}")
                        return True
                    else:
                        logger.warning(f"삭제할 제품을 찾을 수 없음: {master_product_id}")
                        return False
                else:
                    # 비활성화 (소프트 삭제)
                    update_data = {
                        'status': 'deleted',
                        'updated_date': datetime.now().isoformat()
                    }
                    return self.update_master_product(master_product_id, update_data)
                    
        except Exception as e:
            logger.error(f"통합 제품 삭제 실패: {str(e)}")
            return False

