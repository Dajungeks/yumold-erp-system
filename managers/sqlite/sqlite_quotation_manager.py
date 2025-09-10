"""
SQLite 기반 견적서 관리 매니저
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json


class SQLiteQuotationManager:
    def __init__(self, db_path='erp_system.db'):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """견적서 관련 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # quotations 테이블 - YUMOLD 양식 기준으로 재설계 (DROP 후 재생성은 제거)
        # 기존 데이터 보존을 위해 DROP 제거
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotations (
                quotation_id TEXT PRIMARY KEY,
                quotation_number TEXT UNIQUE,
                quote_date TEXT,
                revision_number TEXT DEFAULT '00',
                currency TEXT DEFAULT 'VND',
                customer_company TEXT,
                customer_address TEXT,
                customer_contact_person TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                vat_percentage REAL DEFAULT 10.0,
                subtotal_excl_vat REAL DEFAULT 0.0,
                vat_amount REAL DEFAULT 0.0,
                total_incl_vat REAL DEFAULT 0.0,
                project_name TEXT,
                part_name TEXT,
                part_weight TEXT,
                mold_number TEXT,
                hrs_info TEXT,
                resin_type TEXT,
                resin_additive TEXT,
                sol_material TEXT,
                remark TEXT,
                valid_date TEXT,
                contact_info TEXT,
                payment_terms TEXT,
                delivery_date TEXT,
                sales_representative TEXT,
                sales_rep_contact TEXT,
                sales_rep_email TEXT,
                quotation_status TEXT DEFAULT 'draft',
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 기존 테이블에 컬럼 추가 (ALTER TABLE)
        try:
            cursor.execute('ALTER TABLE quotations ADD COLUMN sales_representative TEXT')
        except sqlite3.OperationalError:
            pass  # 컬럼이 이미 존재하면 무시
            
        try:
            cursor.execute('ALTER TABLE quotations ADD COLUMN sales_rep_contact TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE quotations ADD COLUMN sales_rep_email TEXT')
        except sqlite3.OperationalError:
            pass
        
        # quotation_items 테이블 - YUMOLD 양식 기준으로 재설계
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotation_items (
                item_id TEXT PRIMARY KEY,
                quotation_id TEXT,
                line_number INTEGER,
                source_product_code TEXT,
                item_code TEXT,
                item_name_en TEXT,
                item_name_vn TEXT,
                quantity INTEGER DEFAULT 1,
                standard_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                discount_rate REAL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                amount REAL DEFAULT 0,
                remark TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (quotation_id) REFERENCES quotations (quotation_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_quotation_number(self):
        """견적서 번호 자동 생성 (YMV-Q250903-001 형식)"""
        today = datetime.now()
        date_part = today.strftime("%y%m%d")
        today_prefix = f"YMV-Q{date_part}-"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 오늘 날짜의 견적서 번호들을 모두 조회하여 최대값 찾기
        cursor.execute('''
            SELECT quotation_number FROM quotations 
            WHERE quotation_number LIKE ? 
            ORDER BY quotation_number DESC
        ''', (f"{today_prefix}%",))
        
        results = cursor.fetchall()
        
        # 기존 번호들에서 순번 추출
        numbers = []
        for result in results:
            quotation_num = result[0]
            if quotation_num.startswith(today_prefix):
                try:
                    # YMV-Q250903-001에서 001 부분 추출
                    suffix = quotation_num.replace(today_prefix, "")
                    if suffix.isdigit():
                        numbers.append(int(suffix))
                except:
                    continue
        
        # 다음 번호 생성
        next_number = max(numbers) + 1 if numbers else 1
        
        conn.close()
        return f"{today_prefix}{next_number:03d}"
    
    def create_quotation(self, quotation_data):
        """새 견적서 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        quotation_id = f"QT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        quotation_number = self.generate_quotation_number()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO quotations (
                quotation_id, quotation_number, quotation_date, validity_date,
                quotation_status, employee_id, customer_id, customer_contact_person,
                customer_phone, customer_email, delivery_period, payment_terms,
                warranty_years, resin_1, resin_2, solenoid_voltage, mold_no,
                project_name, tax_rate, subtotal, tax_amount, total_amount,
                currency, exchange_rate, usd_reference, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quotation_id, quotation_number, quotation_data.get('quotation_date'),
            quotation_data.get('validity_date'), quotation_data.get('quotation_status', 'draft'),
            quotation_data.get('employee_id'), quotation_data.get('customer_id'),
            quotation_data.get('customer_contact_person', ''), quotation_data.get('customer_phone', ''),
            quotation_data.get('customer_email', ''), quotation_data.get('delivery_period', '주문 후 2-3주'),
            quotation_data.get('payment_terms', '현금'), quotation_data.get('warranty_years', 1),
            quotation_data.get('resin_1', ''), quotation_data.get('resin_2', ''),
            quotation_data.get('solenoid_voltage', 'DC24V'), quotation_data.get('mold_no', ''),
            quotation_data.get('project_name', ''), quotation_data.get('tax_rate', 10.0),
            quotation_data.get('subtotal', 0), quotation_data.get('tax_amount', 0),
            quotation_data.get('total_amount', 0), quotation_data.get('currency', 'VND'),
            quotation_data.get('exchange_rate', 1.0), quotation_data.get('usd_reference', 0),
            quotation_data.get('notes', ''), now, now
        ))
        
        conn.commit()
        conn.close()
        return quotation_id, quotation_number
    
    def add_quotation_item(self, quotation_id, item_data):
        """견적서에 제품 라인 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        item_id = f"QI_{datetime.now().strftime('%Y%m%d%H%M%S')}_{item_data.get('line_number', 1)}"
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO quotation_items (
                item_id, quotation_id, line_number, product_code,
                product_name_en, product_name_vi, quantity, unit,
                unit_price, discount_rate, line_total, remark,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, quotation_id, item_data.get('line_number', 1),
            item_data.get('product_code', ''), item_data.get('product_name_en', ''),
            item_data.get('product_name_vi', ''), item_data.get('quantity', 1),
            item_data.get('unit', 'EA'), item_data.get('unit_price', 0),
            item_data.get('discount_rate', 0), item_data.get('line_total', 0),
            item_data.get('remark', ''), now, now
        ))
        
        conn.commit()
        conn.close()
        return item_id
    
    def generate_unique_quotation_number(self, base_number=None):
        """중복되지 않는 견적번호 생성 - YMV-Q{YYMMDD}-{001} 형식"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today_str = datetime.now().strftime('%y%m%d')
        
        if base_number and not base_number.endswith('NEW'):
            # 기존 번호가 있고 NEW가 아니면 해당 번호 사용 시도
            cursor.execute('SELECT COUNT(*) FROM quotations WHERE quotation_number = ?', (base_number,))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return base_number
        
        # 오늘 날짜로 시작하는 견적번호 중 가장 큰 번호 찾기
        cursor.execute('''
            SELECT quotation_number FROM quotations 
            WHERE quotation_number LIKE ? 
            AND LENGTH(quotation_number) = 15
            ORDER BY quotation_number DESC LIMIT 1
        ''', (f"YMV-Q{today_str}-%",))
        
        result = cursor.fetchone()
        if result:
            try:
                last_number = result[0]
                # YMV-Q250828-002 형식에서 마지막 숫자 부분 추출
                parts = last_number.split('-')
                if len(parts) == 3 and parts[2].isdigit():
                    next_count = int(parts[2]) + 1
                else:
                    next_count = 1
            except:
                next_count = 1
        else:
            next_count = 1
        
        conn.close()
        return f"YMV-Q{today_str}-{next_count:03d}"

    def save_quotation(self, quotation_data):
        """견적서 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            # 견적번호가 제공되었는지 확인하고, 없으면 생성
            if quotation_data.get('quotation_number'):
                quotation_number = quotation_data.get('quotation_number')
                
                # 중복 체크
                cursor.execute('SELECT COUNT(*) FROM quotations WHERE quotation_number = ?', (quotation_number,))
                if cursor.fetchone()[0] > 0:
                    # 중복 발견 시 새 번호 생성
                    quotation_number = self.generate_quotation_number()
            else:
                quotation_number = self.generate_quotation_number()
            
            # 견적서 데이터 삽입
            cursor.execute('''
                INSERT INTO quotations (
                    quotation_id, quotation_number, quote_date, revision_number,
                    currency, customer_company, customer_address, customer_contact_person,
                    customer_phone, customer_email, vat_percentage, subtotal_excl_vat,
                    vat_amount, total_incl_vat, project_name, part_name, part_weight,
                    mold_number, hrs_info, resin_type, resin_additive, sol_material,
                    remark, valid_date, contact_info, payment_terms, delivery_date,
                    sales_representative, sales_rep_contact, sales_rep_email,
                    quotation_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quotation_data.get('quotation_id'),
                quotation_number,  # 중복 검사 완료된 번호 사용
                quotation_data.get('quote_date'),
                quotation_data.get('revision_number', '00'),
                quotation_data.get('currency', 'VND'),
                quotation_data.get('customer_company'),
                quotation_data.get('customer_address'),
                quotation_data.get('customer_contact_person'),
                quotation_data.get('customer_phone'),
                quotation_data.get('customer_email'),
                quotation_data.get('vat_percentage', 10.0),
                quotation_data.get('subtotal_excl_vat', 0.0),
                quotation_data.get('vat_amount', 0.0),
                quotation_data.get('total_incl_vat', 0.0),
                quotation_data.get('project_name'),
                quotation_data.get('part_name'),
                quotation_data.get('part_weight'),
                quotation_data.get('mold_number'),
                quotation_data.get('hrs_info'),
                quotation_data.get('resin_type'),
                quotation_data.get('resin_additive'),
                quotation_data.get('sol_material'),
                quotation_data.get('remark'),
                quotation_data.get('valid_date'),
                quotation_data.get('contact_info'),
                quotation_data.get('payment_terms'),
                quotation_data.get('delivery_date'),
                quotation_data.get('sales_representative'),
                quotation_data.get('sales_rep_contact'),
                quotation_data.get('sales_rep_email'),
                quotation_data.get('quotation_status', 'draft'),
                quotation_data.get('created_at', current_time),
                quotation_data.get('updated_at', current_time)
            ))
            
            conn.commit()
            conn.close()
            print(f"✓ Quotation saved successfully: {quotation_data.get('quotation_number')}")
            return True
        except Exception as e:
            print(f"Error saving quotation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_quotation_item(self, item_data):
        """견적서 아이템 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quotation_items (
                    item_id, quotation_id, line_number, source_product_code,
                    item_code, item_name_en, item_name_vn, quantity, 
                    standard_price, selling_price, discount_rate, unit_price, amount,
                    remark, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_data.get('item_id'),
                item_data.get('quotation_id'),
                item_data.get('line_number'),
                item_data.get('source_product_code'),
                item_data.get('item_code'),
                item_data.get('item_name_en'),
                item_data.get('item_name_vn'),
                item_data.get('quantity'),
                item_data.get('standard_price'),
                item_data.get('selling_price'),
                item_data.get('discount_rate'),
                item_data.get('unit_price'),
                item_data.get('amount'),
                item_data.get('remark'),
                item_data.get('created_at'),
                item_data.get('updated_at')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving quotation item: {e}")
            return False
    
    def get_all_quotations(self):
        """모든 견적서 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 먼저 테이블과 데이터 존재 확인
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotations';")
            if not cursor.fetchone():
                print("Quotations table does not exist")
                conn.close()
                return pd.DataFrame()
            
            cursor.execute("SELECT COUNT(*) FROM quotations;")
            count = cursor.fetchone()[0]
            # 성능 최적화: 디버그 로그 제거
            # print(f"Found {count} quotations in database")
            
            # 데이터 조회 (모든 필드 포함)
            df = pd.read_sql_query('''
                SELECT quotation_id, quotation_number, quote_date, 
                       customer_company, total_incl_vat, currency, quotation_status,
                       valid_date, project_name, delivery_date, payment_terms,
                       created_at, updated_at
                FROM quotations 
                ORDER BY customer_company ASC, created_at DESC
            ''', conn)
            conn.close()
            
            # 성능 최적화: 디버그 로그 제거
            # print(f"Retrieved {len(df)} quotations from database")
            return df
        except Exception as e:
            print(f"Error getting quotations: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_quotation_items(self, quotation_id):
        """견적서의 제품 라인들 조회"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM quotation_items 
            WHERE quotation_id = ? 
            ORDER BY line_number
        ''', conn, params=[quotation_id])
        conn.close()
        return df
    
    def delete_quotation(self, quotation_id):
        """견적서 삭제 (승인 전만 가능)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 견적서 상태 확인
            cursor.execute('SELECT quotation_status FROM quotations WHERE quotation_id = ?', (quotation_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "Quotation not found."
            
            status = result[0]
            if status == 'approved':
                conn.close()
                return False, "Approved quotations cannot be deleted."
            
            # 견적서 아이템들 먼저 삭제
            cursor.execute('DELETE FROM quotation_items WHERE quotation_id = ?', (quotation_id,))
            
            # 견적서 삭제
            cursor.execute('DELETE FROM quotations WHERE quotation_id = ?', (quotation_id,))
            
            conn.commit()
            conn.close()
            return True, "Quotation deleted successfully."
            
        except Exception as e:
            print(f"Error deleting quotation: {e}")
            return False, f"Error occurred during deletion: {str(e)}"

    def can_edit_quotation(self, quotation_id):
        """견적서 수정 가능 여부 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT quotation_status FROM quotations WHERE quotation_id = ?', (quotation_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, "Quotation not found."
            
            status = result[0]
            if status == 'approved':
                return False, "Approved quotations cannot be edited."
            
            return True, "Editable."
            
        except Exception as e:
            print(f"Error checking edit permission: {e}")
            return False, f"Error occurred while checking status: {str(e)}"

    def update_quotation_totals(self, quotation_id):
        """견적서 총액 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 제품 라인들의 총합 계산
        cursor.execute('''
            SELECT SUM(line_total) FROM quotation_items WHERE quotation_id = ?
        ''', (quotation_id,))
        
        result = cursor.fetchone()
        subtotal = result[0] if result[0] else 0
        
        # 부가세율 조회
        cursor.execute('''
            SELECT tax_rate FROM quotations WHERE quotation_id = ?
        ''', (quotation_id,))
        
        tax_result = cursor.fetchone()
        tax_rate = tax_result[0] if tax_result and tax_result[0] else 10.0
        
        # 세금 및 총액 계산
        tax_amount = subtotal * (tax_rate / 100)
        total_amount = subtotal + tax_amount
        
        # 견적서 업데이트
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE quotations 
            SET subtotal = ?, tax_amount = ?, total_amount = ?, updated_at = ?
            WHERE quotation_id = ?
        ''', (subtotal, tax_amount, total_amount, now, quotation_id))
        
        conn.commit()
        conn.close()
        return subtotal, tax_amount, total_amount
    
    def get_quotation_by_id(self, quotation_id):
        """견적서 상세 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quotations WHERE quotation_id = ?
        ''', (quotation_id,))
        
        result = cursor.fetchone()
        if result:
            columns = [description[0] for description in cursor.description]
            quotation_data = dict(zip(columns, result))
        else:
            quotation_data = None
        
        conn.close()
        return quotation_data
    
    def update_quotation_status(self, quotation_id, status):
        """견적서 상태 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 진행률 계산
        progress_map = {
            'draft': 25,
            'sent': 50,
            'pending': 70,
            'approved': 100,
            'rejected': 0,
            'expired': 0,
            'converted': 100
        }
        progress = progress_map.get(status, 25)
        
        cursor.execute('''
            UPDATE quotations 
            SET quotation_status = ?, progress_status = ?, updated_at = ?
            WHERE quotation_id = ?
        ''', (status, progress, datetime.now().isoformat(), quotation_id))
        
        conn.commit()
        conn.close()
    
    def update_quotation_status(self, quotation_number, new_status):
        """견적서 번호로 상태 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE quotations 
                SET quotation_status = ?, updated_at = ?
                WHERE quotation_number = ?
            ''', (new_status, datetime.now().isoformat(), quotation_number))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating quotation status: {e}")
            return False
    
    def update_quotation(self, quotation_data):
        """견적서 정보 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE quotations SET
                    quote_date = ?, currency = ?, customer_company = ?, 
                    customer_address = ?, customer_contact_person = ?, 
                    customer_phone = ?, customer_email = ?, vat_percentage = ?,
                    subtotal_excl_vat = ?, vat_amount = ?, total_incl_vat = ?,
                    quotation_status = ?, updated_at = ?
                WHERE quotation_id = ?
            ''', (
                quotation_data.get('quote_date'),
                quotation_data.get('currency'),
                quotation_data.get('customer_company'),
                quotation_data.get('customer_address'),
                quotation_data.get('customer_contact_person'),
                quotation_data.get('customer_phone'),
                quotation_data.get('customer_email'),
                quotation_data.get('vat_percentage'),
                quotation_data.get('subtotal_excl_vat'),
                quotation_data.get('vat_amount'),
                quotation_data.get('total_incl_vat'),
                quotation_data.get('quotation_status'),
                quotation_data.get('updated_at'),
                quotation_data.get('quotation_id')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating quotation: {e}")
            return False
    
    def delete_quotation_items(self, quotation_id):
        """견적서의 모든 아이템 삭제"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM quotation_items WHERE quotation_id = ?', (quotation_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting quotation items: {e}")
            return False
    
    def get_quotation_by_number(self, quotation_number):
        """견적서 번호로 특정 견적서 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM quotations 
                WHERE quotation_number = ?
            ''', conn, params=[quotation_number])
            conn.close()
            
            if len(df) > 0:
                return df.iloc[0]
            return None
        except Exception as e:
            print(f"Error getting quotation by number: {e}")
            return None

    def get_quotation_dashboard_data(self):
        """견적서 대시보드용 데이터 조회"""
        conn = sqlite3.connect(self.db_path)
        
        # 월별 통계
        monthly_stats = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_quotations,
                SUM(total_amount) as total_amount,
                quotation_status,
                strftime('%Y-%m', quotation_date) as month
            FROM quotations 
            WHERE quotation_date >= date('now', '-3 months')
            GROUP BY quotation_status, month
        ''', conn)
        
        # 긴급 처리 필요 견적서
        urgent_quotations = pd.read_sql_query('''
            SELECT quotation_number, customer_id, validity_date, quotation_status
            FROM quotations 
            WHERE quotation_status IN ('sent', 'pending') 
                AND date(validity_date) <= date('now', '+7 days')
            ORDER BY validity_date ASC
        ''', conn)
        
        # 상태별 현황
        status_summary = pd.read_sql_query('''
            SELECT quotation_status, COUNT(*) as count, SUM(total_amount) as total
            FROM quotations 
            WHERE quotation_date >= date('now', '-1 month')
            GROUP BY quotation_status
        ''', conn)
        
        conn.close()
        
        return {
            'monthly_stats': monthly_stats,
            'urgent_quotations': urgent_quotations,
            'status_summary': status_summary
        }
    
