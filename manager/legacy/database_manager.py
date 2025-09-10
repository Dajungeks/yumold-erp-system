"""
SQLite 데이터베이스 관리자
CSV 파일에서 SQLite로 마이그레이션 및 관리
"""
import sqlite3
import pandas as pd
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 데이터베이스 매니저 초기화"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def init_database(self):
        """데이터베이스 및 테이블 초기화"""
        with self.get_connection() as conn:
            # 직원 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    english_name TEXT,
                    email TEXT,
                    phone TEXT,
                    position TEXT,
                    department TEXT,
                    hire_date TEXT,
                    status TEXT DEFAULT 'active',
                    region TEXT,
                    password TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 고객 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    contact_person TEXT,
                    email TEXT,
                    phone TEXT,
                    country TEXT,
                    city TEXT,
                    address TEXT,
                    business_type TEXT,
                    status TEXT DEFAULT 'active',
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 제품 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT UNIQUE NOT NULL,
                    product_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    description TEXT,
                    unit_price REAL,
                    currency TEXT DEFAULT 'VND',
                    status TEXT DEFAULT 'active',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 기존 quotations 테이블에 누락된 컬럼들 추가
            try:
                # 먼저 기본 테이블 생성
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS quotations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quotation_id TEXT UNIQUE NOT NULL,
                        customer_id TEXT NOT NULL,
                        customer_name TEXT,
                        quotation_date TEXT,
                        valid_until TEXT,
                        total_amount REAL,
                        currency TEXT DEFAULT 'VND',
                        status TEXT DEFAULT 'draft',
                        created_by TEXT,
                        notes TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                ''')
                
                # 누락된 컬럼들을 하나씩 추가 (이미지 기반 완전한 필드 목록)
                new_columns = [
                    ('quotation_number', 'TEXT'),
                    ('quote_date', 'TEXT'),
                    ('total_amount_usd', 'REAL'),
                    ('total_amount_vnd', 'REAL'),
                    ('exchange_rates_json', 'TEXT'),
                    ('products_json', 'TEXT'),
                    ('payment_terms', 'TEXT'),
                    ('delivery_terms', 'TEXT'),
                    ('shipping_terms', 'TEXT'),
                    ('terms_conditions', 'TEXT'),
                    ('project_name', 'TEXT'),
                    ('delivery_date', 'TEXT'),
                    # 고객 상세 정보
                    ('customer_contact', 'TEXT'),
                    ('customer_email', 'TEXT'),
                    ('customer_address', 'TEXT'),
                    # 프로젝트 상세 필드 (이미지 기반)
                    ('mold_no', 'TEXT'),
                    ('hrs_info', 'TEXT'),
                    ('part_name', 'TEXT'),
                    ('part_weight', 'TEXT'),
                    ('resin_type', 'TEXT'),
                    ('account', 'TEXT'),
                    ('remark', 'TEXT'),
                    ('contact_person', 'TEXT'),
                    ('contact_detail', 'TEXT'),
                    ('product_name_detail', 'TEXT'),
                    ('quotation_title', 'TEXT'),
                    ('special_notes', 'TEXT'),
                    ('delivery_unknown', 'BOOLEAN'),
                    ('sales_representative', 'TEXT'),
                    ('sales_rep_contact', 'TEXT'),
                    ('sales_rep_email', 'TEXT'),
                    ('approved_by', 'TEXT'),
                    ('approved_date', 'TEXT')
                ]
                
                for column_name, column_type in new_columns:
                    try:
                        conn.execute(f'ALTER TABLE quotations ADD COLUMN {column_name} {column_type}')
                        logger.info(f"컬럼 추가됨: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            pass  # 이미 존재하는 컬럼은 무시
                        else:
                            logger.warning(f"컬럼 {column_name} 추가 실패: {e}")
                            
            except Exception as e:
                logger.error(f"quotations 테이블 업데이트 실패: {e}")
            
            # 주문 테이블 (notes 컬럼 추가)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    quotation_id TEXT,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT,
                    order_date TEXT,
                    requested_delivery_date TEXT,
                    confirmed_delivery_date TEXT,
                    total_amount REAL,
                    currency TEXT DEFAULT 'VND',
                    order_status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'pending',
                    payment_terms TEXT,
                    special_instructions TEXT,
                    created_by TEXT,
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (quotation_id) REFERENCES quotations(quotation_id)
                )
            ''')
            
            # notes 컬럼이 없는 기존 테이블에 추가
            try:
                conn.execute('ALTER TABLE orders ADD COLUMN notes TEXT')
                logger.info("orders 테이블에 notes 컬럼 추가")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    pass  # 이미 존재하는 컬럼은 무시
                else:
                    logger.warning(f"notes 컬럼 추가 실패: {e}")
            
            # 공급업체 테이블 (확장된 버전)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    contact_person TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    address TEXT,
                    country TEXT,
                    city TEXT,
                    business_type TEXT,
                    tax_id TEXT,
                    bank_info TEXT,
                    payment_terms TEXT,
                    lead_time_days INTEGER,
                    minimum_order_amount REAL,
                    currency TEXT DEFAULT 'VND',
                    rating REAL DEFAULT 3.0,
                    notes TEXT,
                    status TEXT DEFAULT '활성',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 주문 아이템 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    order_id TEXT NOT NULL,
                    product_code TEXT,
                    product_name TEXT,
                    quantity REAL,
                    unit_price REAL,
                    total_price REAL,
                    currency TEXT,
                    specifications TEXT,
                    delivery_notes TEXT,
                    production_status TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            ''')
            
            # 주문 상태 변경 이력 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id TEXT UNIQUE NOT NULL,
                    order_id TEXT NOT NULL,
                    previous_status TEXT,
                    new_status TEXT,
                    changed_by TEXT,
                    changed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    reason TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            ''')
            
            # 지출요청서 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS expense_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    requester_id TEXT NOT NULL,
                    requester_name TEXT NOT NULL,
                    request_date TEXT NOT NULL,
                    expense_title TEXT,
                    expense_description TEXT,
                    category TEXT,
                    amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'VND',
                    expected_date TEXT,
                    status TEXT DEFAULT '대기',
                    current_step INTEGER DEFAULT 1,
                    total_steps INTEGER DEFAULT 1,
                    attachment_path TEXT,
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 지출요청서 승인 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS expense_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT UNIQUE NOT NULL,
                    request_id TEXT NOT NULL,
                    approval_step INTEGER NOT NULL,
                    approver_id TEXT NOT NULL,
                    approver_name TEXT NOT NULL,
                    approval_order INTEGER NOT NULL,
                    approval_date TEXT,
                    result TEXT DEFAULT '대기',
                    comments TEXT,
                    is_required BOOLEAN DEFAULT 1,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES expense_requests(request_id)
                )
            ''')
            
            conn.commit()
            logger.info("데이터베이스 테이블 초기화 완료")
    
    def migrate_csv_to_db(self, csv_folder="data"):
        """CSV 파일들을 SQLite 데이터베이스로 마이그레이션"""
        try:
            # 직원 데이터 마이그레이션
            self._migrate_employees(csv_folder)
            # 고객 데이터 마이그레이션
            self._migrate_customers(csv_folder)
            # 제품 데이터 마이그레이션
            self._migrate_products(csv_folder)
            # 견적 데이터 마이그레이션
            self._migrate_quotations(csv_folder)
            # 주문 데이터 마이그레이션
            self._migrate_orders(csv_folder)
            # 공급업체 데이터 마이그레이션
            self._migrate_suppliers(csv_folder)
            
            logger.info("모든 CSV 데이터 마이그레이션 완료")
            return True
            
        except Exception as e:
            logger.error(f"마이그레이션 오류: {str(e)}")
            return False
    
    def _migrate_employees(self, csv_folder):
        """직원 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "employees.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            with self.get_connection() as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO employees 
                        (employee_id, name, english_name, email, phone, position, department, 
                         hire_date, status, region, password)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('employee_id', ''),
                        row.get('name', ''),
                        row.get('english_name', ''),
                        row.get('email', ''),
                        row.get('phone', ''),
                        row.get('position', ''),
                        row.get('department', ''),
                        row.get('hire_date', ''),
                        row.get('status', 'active'),
                        row.get('region', ''),
                        row.get('password', '')
                    ))
                conn.commit()
            logger.info(f"직원 데이터 마이그레이션 완료: {len(df)}건")
        except Exception as e:
            logger.error(f"직원 데이터 마이그레이션 오류: {str(e)}")
    
    def _migrate_customers(self, csv_folder):
        """고객 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "customers.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # BOM 제거
            df.columns = df.columns.str.replace('\ufeff', '')
            
            with self.get_connection() as conn:
                migrated_count = 0
                for idx, row in df.iterrows():
                    # 필수 필드 검증 및 기본값 설정
                    customer_id = str(row.get('customer_id', '')).strip()
                    company_name = str(row.get('company_name', '')).strip()
                    
                    # 빈 값 처리
                    if not customer_id or customer_id == 'nan':
                        customer_id = f"C{idx+1:04d}"
                    if not company_name or company_name == 'nan':
                        company_name = '미설정 고객'
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO customers 
                        (customer_id, company_name, contact_person, email, phone, 
                         country, city, address, business_type, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        customer_id,
                        company_name,
                        str(row.get('contact_person', '')).strip() or '',
                        str(row.get('contact_email', '')).strip() or '',
                        str(row.get('contact_phone', '')).strip() or '',
                        str(row.get('country', '')).strip() or '',
                        str(row.get('city', '')).strip() or '',
                        str(row.get('address', '')).strip() or '',
                        str(row.get('business_type', '')).strip() or '',
                        'active',
                        str(row.get('notes', '')).strip() or ''
                    ))
                    migrated_count += 1
                conn.commit()
            logger.info(f"고객 데이터 마이그레이션 완료: {migrated_count}건")
        except Exception as e:
            logger.error(f"고객 데이터 마이그레이션 오류: {str(e)}")
    
    def _migrate_products(self, csv_folder):
        """제품 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "products.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # BOM 제거
            df.columns = df.columns.str.replace('\ufeff', '')
            
            with self.get_connection() as conn:
                migrated_count = 0
                for idx, row in df.iterrows():
                    # 필수 필드 검증 및 기본값 설정
                    product_code = str(row.get('product_code', '')).strip()
                    product_name = str(row.get('product_name', '')).strip()
                    
                    # 빈 값 처리
                    if not product_code or product_code == 'nan':
                        product_code = f"P{idx+1:04d}"
                    if not product_name or product_name == 'nan':
                        product_name = '제품명 미설정'
                    
                    # 가격 데이터 처리
                    try:
                        unit_price = float(row.get('cost_price_usd', 0) or 0)
                    except (ValueError, TypeError):
                        unit_price = 0
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO products 
                        (product_code, product_name, category, subcategory, description, 
                         unit_price, currency, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_code,
                        product_name,
                        str(row.get('category1', '')).strip() or '',
                        str(row.get('category2', '')).strip() or '',
                        str(row.get('description', '')).strip() or '',
                        unit_price,
                        'USD',
                        'active'
                    ))
                    migrated_count += 1
                conn.commit()
            logger.info(f"제품 데이터 마이그레이션 완료: {migrated_count}건")
        except Exception as e:
            logger.error(f"제품 데이터 마이그레이션 오류: {str(e)}")
    
    def _migrate_quotations(self, csv_folder):
        """견적 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "quotations.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            with self.get_connection() as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO quotations 
                        (quotation_id, customer_id, customer_name, quotation_date, 
                         valid_until, total_amount, currency, status, created_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('quotation_id', ''),
                        row.get('customer_id', ''),
                        row.get('customer_name', ''),
                        row.get('quotation_date', ''),
                        row.get('valid_until', ''),
                        row.get('total_amount', 0),
                        row.get('currency', 'VND'),
                        row.get('status', 'draft'),
                        row.get('created_by', ''),
                        row.get('notes', '')
                    ))
                conn.commit()
            logger.info(f"견적 데이터 마이그레이션 완료: {len(df)}건")
        except Exception as e:
            logger.error(f"견적 데이터 마이그레이션 오류: {str(e)}")
    
    def _migrate_orders(self, csv_folder):
        """주문 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "orders.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            with self.get_connection() as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO orders 
                        (order_id, quotation_id, customer_id, customer_name, order_date,
                         requested_delivery_date, confirmed_delivery_date, total_amount, 
                         currency, order_status, payment_status, payment_terms, 
                         special_instructions, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('order_id', ''),
                        row.get('quotation_id', ''),
                        row.get('customer_id', ''),
                        row.get('customer_name', ''),
                        row.get('order_date', ''),
                        row.get('requested_delivery_date', ''),
                        row.get('confirmed_delivery_date', ''),
                        row.get('total_amount', 0),
                        row.get('currency', 'VND'),
                        row.get('order_status', 'pending'),
                        row.get('payment_status', 'pending'),
                        row.get('payment_terms', ''),
                        row.get('special_instructions', ''),
                        row.get('created_by', '')
                    ))
                conn.commit()
            logger.info(f"주문 데이터 마이그레이션 완료: {len(df)}건")
        except Exception as e:
            logger.error(f"주문 데이터 마이그레이션 오류: {str(e)}")
    
    def _migrate_suppliers(self, csv_folder):
        """공급업체 데이터 마이그레이션"""
        csv_file = os.path.join(csv_folder, "suppliers.csv")
        if not os.path.exists(csv_file):
            logger.warning(f"파일을 찾을 수 없음: {csv_file}")
            return
        
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            with self.get_connection() as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO suppliers 
                        (supplier_id, company_name, contact_person, email, phone,
                         country, city, address, business_type, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('supplier_id', ''),
                        row.get('company_name', ''),
                        row.get('contact_person', ''),
                        row.get('email', ''),
                        row.get('phone', ''),
                        row.get('country', ''),
                        row.get('city', ''),
                        row.get('address', ''),
                        row.get('business_type', ''),
                        row.get('status', 'active'),
                        row.get('notes', '')
                    ))
                conn.commit()
            logger.info(f"공급업체 데이터 마이그레이션 완료: {len(df)}건")
        except Exception as e:
            logger.error(f"공급업체 데이터 마이그레이션 오류: {str(e)}")
    
    def backup_database(self, backup_path=None):
        """데이터베이스 백업"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_erp_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"백업 오류: {str(e)}")
            return None
    
    def get_table_info(self):
        """테이블 정보 및 레코드 수 반환"""
        info = {}
        with self.get_connection() as conn:
            tables = ['employees', 'customers', 'products', 'quotations', 'orders', 'suppliers']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                info[table] = count
        return info

if __name__ == "__main__":
    # 테스트 실행
    db_manager = DatabaseManager()
    
    # CSV 데이터 마이그레이션
    success = db_manager.migrate_csv_to_db()
    
    if success:
        # 테이블 정보 출력
        info = db_manager.get_table_info()
        print("=== 마이그레이션 결과 ===")
        for table, count in info.items():
            print(f"{table}: {count}건")
        
        # 백업 생성
        backup_file = db_manager.backup_database()
        if backup_file:
            print(f"백업 파일 생성: {backup_file}")