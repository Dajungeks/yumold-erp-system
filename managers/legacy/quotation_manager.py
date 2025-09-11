import pandas as pd
import os
import json
from datetime import datetime
from database_manager import DatabaseManager

class QuotationManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self._migrate_from_csv()
    
    def _migrate_from_csv(self):
        """CSV 데이터를 SQLite로 마이그레이션"""
        csv_file = 'data/quotations.csv'
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                if len(df) > 0:
                    with self.db_manager.get_connection() as conn:
                        # 기존 데이터 확인
                        existing = conn.execute("SELECT COUNT(*) FROM quotations").fetchone()[0]
                        if existing == 0:
                            print(f"CSV에서 {len(df)}개 견적서를 SQLite로 마이그레이션 중...")
                            for _, row in df.iterrows():
                                self._insert_quotation(row.to_dict())
                            print("마이그레이션 완료")
            except Exception as e:
                print(f"CSV 마이그레이션 실패: {e}")

    def generate_quotation_number(self):
        """견적서 번호 생성 (QYYYYMMDD#### 형식)"""
        try:
            today = datetime.now()
            prefix = f"Q{today.strftime('%Y%m%d')}"
            
            # SQLite에서 오늘 날짜 견적서 번호 조회
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT quotation_number FROM quotations WHERE quotation_number LIKE ?",
                    (f"{prefix}%",)
                )
                existing_numbers = [row[0] for row in cursor.fetchall() if row[0]]
            
            # 순번 추출 및 다음 번호 계산
            numbers = []
            for qnum in existing_numbers:
                try:
                    if len(str(qnum)) == len(prefix) + 4:
                        suffix = str(qnum)[len(prefix):]
                        if suffix.isdigit():
                            numbers.append(int(suffix))
                except:
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
            return f"{prefix}{next_num:04d}"
            
        except Exception as e:
            print(f"견적서 번호 생성 오류: {e}")
            return f"Q{datetime.now().strftime('%Y%m%d')}0001"

    def _insert_quotation(self, quotation_data):
        """견적서 SQLite에 삽입"""
        try:
            with self.db_manager.get_connection() as conn:
                # 필수 필드 준비
                fields = [
                    'quotation_id', 'quotation_number', 'customer_id', 'customer_name',
                    'quotation_date', 'quote_date', 'valid_until', 'total_amount', 
                    'total_amount_usd', 'total_amount_vnd', 'currency', 'exchange_rates_json',
                    'products_json', 'payment_terms', 'delivery_terms', 'project_name',
                    'contact_person', 'contact_detail', 'quotation_title', 'remark',
                    'sales_representative', 'sales_rep_contact', 'sales_rep_email', 
                    'status', 'created_by', 'notes'
                ]
                
                # 데이터 준비 (None/NaN 값 처리)
                values = []
                for field in fields:
                    value = quotation_data.get(field, '')
                    if pd.isna(value) or value is None:
                        value = ''
                    values.append(str(value) if value else '')
                
                placeholders = ', '.join(['?' for _ in fields])
                sql = f"INSERT OR REPLACE INTO quotations ({', '.join(fields)}) VALUES ({placeholders})"
                conn.execute(sql, values)
                return True
        except Exception as e:
            print(f"견적서 DB 삽입 실패: {e}")
            return False

    def add_quotation(self, quotation_data):
        """새 견적서 추가"""
        try:
            # ID 및 번호 생성
            if not quotation_data.get('quotation_id'):
                quotation_data['quotation_id'] = f"QID{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if not quotation_data.get('quotation_number'):
                quotation_data['quotation_number'] = self.generate_quotation_number()
            
            # 생성/수정 시간 설정
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            quotation_data['created_date'] = current_time
            quotation_data['updated_date'] = current_time
            quotation_data['status'] = quotation_data.get('status', '진행중')
            
            # JSON 직렬화
            if 'products' in quotation_data:
                quotation_data['products_json'] = json.dumps(quotation_data['products'], ensure_ascii=False)
                del quotation_data['products']
            
            if 'exchange_rates' in quotation_data:
                quotation_data['exchange_rates_json'] = json.dumps(quotation_data['exchange_rates'], ensure_ascii=False)
                del quotation_data['exchange_rates']
            
            # SQLite에 저장
            if self._insert_quotation(quotation_data):
                print(f"견적서 추가 성공: {quotation_data['quotation_id']}")
                return True, quotation_data['quotation_number']
            else:
                return False, "DB 저장 실패"
                
        except Exception as e:
            print(f"견적서 추가 실패: {e}")
            return False, str(e)

    def get_all_quotations(self):
        """모든 견적서 조회"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM quotations ORDER BY created_date DESC")
                quotations = []
                for row in cursor.fetchall():
                    quotation = dict(row)
                    # JSON 필드 파싱
                    if quotation.get('products_json'):
                        try:
                            quotation['products'] = json.loads(quotation['products_json'])
                        except:
                            quotation['products'] = []
                    
                    if quotation.get('exchange_rates_json'):
                        try:
                            quotation['exchange_rates'] = json.loads(quotation['exchange_rates_json'])
                        except:
                            quotation['exchange_rates'] = {}
                    
                    quotations.append(quotation)
                return quotations
        except Exception as e:
            print(f"견적서 조회 실패: {e}")
            return []

    def get_quotation_by_id(self, quotation_id):
        """특정 견적서 조회"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM quotations WHERE quotation_id = ?", (quotation_id,))
                row = cursor.fetchone()
                if row:
                    quotation = dict(row)
                    # JSON 필드 파싱
                    if quotation.get('products_json'):
                        try:
                            quotation['products'] = json.loads(quotation['products_json'])
                        except:
                            quotation['products'] = []
                    
                    if quotation.get('exchange_rates_json'):
                        try:
                            quotation['exchange_rates'] = json.loads(quotation['exchange_rates_json'])
                        except:
                            quotation['exchange_rates'] = {}
                    
                    return quotation
                return None
        except Exception as e:
            print(f"견적서 조회 실패: {e}")
            return None

    def update_quotation_status(self, quotation_id, status):
        """견적서 상태 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE quotations SET status = ?, updated_date = ? WHERE quotation_id = ?",
                    (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), quotation_id)
                )
                return True
        except Exception as e:
            print(f"견적서 상태 업데이트 실패: {e}")
            return False

    def update_quotation(self, quotation_id, updated_data):
        """견적서 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                # 업데이트할 필드들
                set_clauses = []
                values = []
                
                for field, value in updated_data.items():
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
                
                values.append(quotation_id)
                
                sql = f"UPDATE quotations SET {', '.join(set_clauses)} WHERE quotation_id = ?"
                conn.execute(sql, values)
                return True
        except Exception as e:
            print(f"견적서 업데이트 실패: {e}")
            return False

    def delete_quotation(self, quotation_id):
        """견적서 삭제"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM quotations WHERE quotation_id = ?", (quotation_id,))
                return True
        except Exception as e:
            print(f"견적서 삭제 실패: {e}")
            return False

    # 호환성을 위한 별칭 메서드들
    def create_quotation(self, quotation_data):
        return self.add_quotation(quotation_data)
    
    def generate_quotation_id(self):
        return self.generate_quotation_number()
