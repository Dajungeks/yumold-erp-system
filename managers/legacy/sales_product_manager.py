import pandas as pd
import os
from datetime import datetime
from master_product_manager import MasterProductManager

class SalesProductManager:
    """판매 제품 관리 클래스 - 표준 판매가 및 실제 판매 데이터 관리"""
    
    def __init__(self):
        self.price_history_file = 'data/product_price_history.csv'
        self.sales_transactions_file = 'data/sales_transactions.csv'
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """데이터 파일들이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        
        # 제품 가격 이력 파일
        if not os.path.exists(self.price_history_file):
            df = pd.DataFrame(columns=[
                'price_id', 'product_id', 'product_code', 'product_name',
                'standard_price_usd', 'standard_price_local', 'local_currency',
                'change_reason', 'effective_date', 'end_date', 'created_by',
                'created_date', 'is_current'
            ])
            df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
        
        # 판매 거래 이력 파일
        if not os.path.exists(self.sales_transactions_file):
            df = pd.DataFrame(columns=[
                'transaction_id', 'product_id', 'product_code', 'quotation_id',
                'customer_id', 'customer_name', 'quantity', 'unit_price_usd',
                'unit_price_local', 'local_currency', 'total_amount_usd',
                'total_amount_local', 'standard_price_usd', 'price_variance_percent',
                'discount_amount', 'discount_reason', 'sale_date', 'created_date'
            ])
            df.to_csv(self.sales_transactions_file, index=False, encoding='utf-8-sig')
    
    def generate_price_id(self):
        """가격 이력 ID를 생성합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            if len(df) == 0:
                return 'PH001'
            
            existing_ids = df['price_id'].tolist()
            numbers = []
            for pid in existing_ids:
                if pid.startswith('PH') and pid[2:].isdigit():
                    numbers.append(int(pid[2:]))
            
            next_num = max(numbers) + 1 if numbers else 1
            return f'PH{next_num:03d}'
        except Exception as e:
            print(f"가격 이력 ID 생성 중 오류: {e}")
            return f'PH{datetime.now().strftime("%m%d%H%M")}'
    
    def get_master_products_for_sales(self):
        """판매가 설정 가능한 마스터 제품 목록을 조회합니다 (MB 제외)"""
        try:
            master_manager = MasterProductManager()
            all_products = master_manager.get_all_products()
            
            if isinstance(all_products, pd.DataFrame) and len(all_products) == 0:
                return pd.DataFrame()
            elif not isinstance(all_products, pd.DataFrame):
                return pd.DataFrame()
            
            # MB 제품 제외 (외주 공급가 관리에서만 다룸)
            non_mb_products = all_products[all_products['main_category'] != 'MB'].copy()
            return non_mb_products
        except Exception as e:
            print(f"마스터 제품 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_products_with_sales_price(self):
        """판매가가 설정된 제품 목록을 조회합니다"""
        try:
            # 현재 유효한 판매가가 있는 제품들 조회
            price_df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            
            if len(price_df) == 0:
                return pd.DataFrame()
            
            # 현재 유효한 가격만 필터링
            current_prices = price_df[price_df['is_current'] == True].copy()
            
            if len(current_prices) == 0:
                return pd.DataFrame()
            
            # 마스터 제품 정보와 결합
            master_manager = MasterProductManager()
            all_products = master_manager.get_all_products()
            
            if not isinstance(all_products, pd.DataFrame) or len(all_products) == 0:
                return pd.DataFrame()
            
            # 가격 정보가 있는 제품만 반환
            products_with_price = all_products[
                all_products['product_id'].isin(current_prices['product_id'].unique())
            ].copy()
            
            # 가격 정보 병합
            products_with_price = products_with_price.merge(
                current_prices[['product_id', 'standard_price_usd', 'standard_price_local', 'local_currency']],
                on='product_id',
                how='left'
            )
            
            return products_with_price
            
        except Exception as e:
            print(f"판매가 설정 제품 조회 오류: {e}")
            return pd.DataFrame()
    
    def sync_with_master_product(self, master_product_data):
        """마스터 제품 데이터와 동기화하여 판매가를 설정합니다"""
        try:
            return self.set_standard_price(
                product_id=master_product_data['product_id'],
                product_code=master_product_data['product_code'],
                product_name=master_product_data['product_name_korean'],
                standard_price_usd=0.0,  # 사용자가 입력
                standard_price_local=0.0,
                local_currency='USD',
                change_reason='마스터 제품 연동',
                created_by='system'
            )
        except Exception as e:
            print(f"마스터 제품 동기화 오류: {e}")
            return False, str(e)

    def set_standard_price(self, product_id, product_code, product_name, 
                          standard_price_usd, standard_price_local=None, 
                          local_currency='USD', change_reason='신규 등록', 
                          created_by='system'):
        """제품의 표준 판매가를 설정합니다."""
        try:
            # 기존 가격을 비활성화
            self._deactivate_current_price(product_id)
            
            # 새로운 가격 이력 추가
            price_id = self.generate_price_id()
            new_price = {
                'price_id': price_id,
                'product_id': product_id,
                'product_code': product_code,
                'product_name': product_name,
                'standard_price_usd': standard_price_usd,
                'standard_price_local': standard_price_local or standard_price_usd,
                'local_currency': local_currency,
                'change_reason': change_reason,
                'effective_date': datetime.now().strftime('%Y-%m-%d'),
                'end_date': None,
                'created_by': created_by,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_current': True
            }
            
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([new_price])], ignore_index=True)
            df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
            
            return True, price_id
        except Exception as e:
            print(f"표준 가격 설정 중 오류: {e}")
            return False, str(e)
    
    def _deactivate_current_price(self, product_id):
        """현재 활성화된 가격을 비활성화합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            mask = (df['product_id'] == product_id) & (df['is_current'] == True)
            if mask.any():
                df.loc[mask, 'is_current'] = False
                df.loc[mask, 'end_date'] = datetime.now().strftime('%Y-%m-%d')
                df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"기존 가격 비활성화 중 오류: {e}")
    
    def add_standard_price(self, price_data):
        """표준 판매가를 추가합니다 (간단한 버전)"""
        try:
            # 기본값 설정
            current_time = datetime.now()
            price_id = self.generate_price_id()
            
            new_price = {
                'price_id': price_id,
                'product_id': price_data.get('product_id', ''),
                'product_code': price_data.get('product_code', ''),
                'product_name': price_data.get('product_name', ''),
                'standard_price_usd': price_data.get('standard_price_usd', 0.0),
                'standard_price_local': price_data.get('standard_price_local', 0.0),
                'local_currency': price_data.get('local_currency', 'USD'),
                'change_reason': price_data.get('price_reason', '신규 등록'),
                'effective_date': price_data.get('effective_date', current_time.strftime('%Y-%m-%d')),
                'end_date': None,
                'created_by': price_data.get('created_by', 'system'),
                'created_date': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'is_current': True
            }
            
            # 기존 가격 비활성화
            if price_data.get('product_id'):
                self._deactivate_current_price(price_data['product_id'])
            
            # 새 가격 추가
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([new_price])], ignore_index=True)
            df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
            
            return True, price_id
        except Exception as e:
            print(f"표준 가격 추가 중 오류: {e}")
            return False, str(e)

    def get_current_price(self, product_code):
        """제품 코드로 현재 가격을 조회합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            current_price = df[(df['product_code'] == product_code) & (df['is_current'] == True)]
            
            if len(current_price) > 0:
                return current_price.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"현재 가격 조회 중 오류: {e}")
            return None

    def get_current_standard_price(self, product_id):
        """제품의 현재 표준 판매가를 가져옵니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            current_price = df[(df['product_id'] == product_id) & (df['is_current'] == True)]
            
            if len(current_price) > 0:
                return current_price.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"현재 표준 가격 조회 중 오류: {e}")
            return None
    
    def get_current_prices(self):
        """모든 제품의 현재 가격을 가져옵니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            # 현재 활성화된 가격만 안전하게 필터링
            df['is_current'] = df['is_current'].fillna(False).astype(str).str.lower()
            current_prices = df[df['is_current'].isin(['true', '1', 'yes', 'y'])]
            return current_prices
        except Exception as e:
            print(f"현재 가격 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_all_prices(self):
        """모든 가격 데이터를 가져옵니다. (딕셔너리 리스트 형태로 반환)"""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            if len(df) == 0:
                return []
            
            # DataFrame을 딕셔너리 리스트로 변환
            return df.to_dict('records')
        except Exception as e:
            print(f"모든 가격 조회 중 오류: {e}")
            return []
    
    def get_price_history(self, product_id):
        """제품의 가격 변경 이력을 가져옵니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            # 날짜 파싱 문제 해결
            df['effective_date'] = pd.to_datetime(df['effective_date'], format='mixed', errors='coerce')
            history = df[df['product_id'] == product_id].sort_values('effective_date', ascending=False)
            return history
        except Exception as e:
            print(f"가격 이력 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def record_sales_transaction(self, product_id, product_code, quotation_id,
                               customer_id, customer_name, quantity, unit_price_usd,
                               unit_price_local=None, local_currency='USD',
                               discount_amount=0, discount_reason=''):
        """판매 거래를 기록합니다."""
        try:
            # 현재 표준가 조회
            standard_price_info = self.get_current_standard_price(product_id)
            standard_price_usd = standard_price_info['standard_price_usd'] if standard_price_info else 0
            
            # 가격 편차 계산
            price_variance_percent = 0
            if standard_price_usd > 0:
                price_variance_percent = ((unit_price_usd - standard_price_usd) / standard_price_usd) * 100
            
            transaction_id = f"ST{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            new_transaction = {
                'transaction_id': transaction_id,
                'product_id': product_id,
                'product_code': product_code,
                'quotation_id': quotation_id,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'quantity': quantity,
                'unit_price_usd': unit_price_usd,
                'unit_price_local': unit_price_local or unit_price_usd,
                'local_currency': local_currency,
                'total_amount_usd': quantity * unit_price_usd,
                'total_amount_local': quantity * (unit_price_local or unit_price_usd),
                'standard_price_usd': standard_price_usd,
                'price_variance_percent': round(price_variance_percent, 2),
                'discount_amount': discount_amount,
                'discount_reason': discount_reason,
                'sale_date': datetime.now().strftime('%Y-%m-%d'),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([new_transaction])], ignore_index=True)
            df.to_csv(self.sales_transactions_file, index=False, encoding='utf-8-sig')
            
            return True, transaction_id
        except Exception as e:
            print(f"판매 거래 기록 중 오류: {e}")
            return False, str(e)
    
    def get_sales_analysis(self, product_id=None, start_date=None, end_date=None):
        """판매 분석 데이터를 가져옵니다."""
        try:
            df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return {
                    'total_transactions': 0,
                    'total_quantity': 0,
                    'total_revenue_usd': 0,
                    'average_price_variance': 0,
                    'transactions': pd.DataFrame()
                }
            
            # 날짜 파싱 문제 해결
            df['sale_date'] = pd.to_datetime(df['sale_date'], format='mixed', errors='coerce')
            
            # 필터링
            if product_id:
                df = df[df['product_id'] == product_id]
            if start_date:
                df = df[df['sale_date'] >= start_date]
            if end_date:
                df = df[df['sale_date'] <= end_date]
            
            analysis = {
                'total_transactions': len(df),
                'total_quantity': df['quantity'].sum(),
                'total_revenue_usd': df['total_amount_usd'].sum(),
                'average_price_variance': df['price_variance_percent'].mean(),
                'transactions': df.sort_values('sale_date', ascending=False)
            }
            
            return analysis
        except Exception as e:
            print(f"판매 분석 중 오류: {e}")
            return {
                'total_transactions': 0,
                'total_quantity': 0,
                'total_revenue_usd': 0,
                'average_price_variance': 0,
                'transactions': pd.DataFrame()
            }
    
    def get_price_variance_analysis(self):
        """가격 편차 분석을 수행합니다."""
        try:
            df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 제품별 가격 편차 분석
            analysis = df.groupby(['product_id', 'product_code']).agg({
                'price_variance_percent': ['mean', 'min', 'max', 'std'],
                'quantity': 'sum',
                'total_amount_usd': 'sum',
                'transaction_id': 'count'
            }).round(2)
            
            analysis.columns = ['평균_편차율', '최소_편차율', '최대_편차율', '편차_표준편차', 
                              '총_판매수량', '총_매출액', '거래_횟수']
            
            return analysis.reset_index()
        except Exception as e:
            print(f"가격 편차 분석 중 오류: {e}")
            return pd.DataFrame()
    
    def delete_price_records(self, price_ids, permanent=False):
        """선택된 가격 기록들을 삭제합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            
            if permanent:
                # 물리적 삭제
                initial_count = len(df)
                df = df[~df['price_id'].isin(price_ids)]
                success_count = initial_count - len(df)
                
                if success_count > 0:
                    df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
                    return True, f"{success_count}개 가격이 완전히 삭제되었습니다."
                else:
                    return False, "삭제할 가격 기록을 찾을 수 없습니다."
            else:
                # 소프트 삭제 (비활성화)
                success_count = 0
                for price_id in price_ids:
                    mask = df['price_id'] == price_id
                    if mask.any():
                        df.loc[mask, 'is_current'] = False
                        df.loc[mask, 'end_date'] = datetime.now().strftime('%Y-%m-%d')
                        df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        success_count += 1
                
                if success_count > 0:
                    df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
                    return True, f"{success_count}개 가격이 비활성화되었습니다."
                else:
                    return False, "삭제할 가격 기록을 찾을 수 없습니다."
                
        except Exception as e:
            return False, f"가격 삭제 중 오류: {str(e)}"
    
    def get_price_by_id(self, price_id):
        """특정 가격 ID의 상세 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            price_record = df[df['price_id'] == price_id]
            
            if len(price_record) > 0:
                return price_record.iloc[0].to_dict()
            else:
                return None
                
        except Exception as e:
            print(f"가격 조회 중 오류: {e}")
            return None
    
    def update_price_record(self, price_id, new_standard_price_usd, new_standard_price_local, 
                           new_local_currency, change_reason, updated_by="system"):
        """기존 가격 기록을 수정합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            
            # 해당 가격 ID 찾기
            mask = df['price_id'] == price_id
            if not mask.any():
                return False, "해당 가격 기록을 찾을 수 없습니다."
            
            # 기존 기록 업데이트 
            df.loc[mask, 'standard_price_usd'] = new_standard_price_usd
            df.loc[mask, 'standard_price_local'] = new_standard_price_local
            df.loc[mask, 'local_currency'] = new_local_currency
            df.loc[mask, 'change_reason'] = change_reason
            df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[mask, 'updated_by'] = updated_by
            
            # 파일 저장
            df.to_csv(self.price_history_file, index=False, encoding='utf-8-sig')
            
            return True, "가격이 성공적으로 수정되었습니다."
            
        except Exception as e:
            return False, f"가격 수정 중 오류: {str(e)}"
    
    def search_prices(self, product_code=None, product_name=None, category=None, 
                     is_current_only=False):
        """가격 기록을 검색합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 현재 활성 가격만 표시할지 결정 (기본값을 False로 변경)
            if is_current_only:
                df['is_current'] = df['is_current'].fillna(False).astype(str).str.lower()
                df = df[df['is_current'].isin(['true', '1', 'yes', 'y'])]
            
            # 검색 필터 적용
            if product_code:
                df = df[df['product_code'].str.contains(product_code, case=False, na=False)]
            
            if product_name:
                df = df[df['product_name'].str.contains(product_name, case=False, na=False)]
            
            # 날짜 정렬
            df['effective_date'] = pd.to_datetime(df['effective_date'], format='mixed', errors='coerce')
            df = df.sort_values('effective_date', ascending=False)
            
            return df
            
        except Exception as e:
            print(f"가격 검색 중 오류: {e}")
            return pd.DataFrame()
    
    def get_sales_data(self):
        """실제 판매 데이터를 조회합니다."""
        try:
            df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 날짜 파싱
            df['sale_date'] = pd.to_datetime(df['sale_date'], format='mixed', errors='coerce')
            return df.sort_values('sale_date', ascending=False)
            
        except Exception as e:
            print(f"판매 데이터 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_price_change_history(self):
        """가격 변경 이력을 조회합니다."""
        try:
            df = pd.read_csv(self.price_history_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 변경 이력 생성을 위해 이전 가격과 비교
            df['effective_date'] = pd.to_datetime(df['effective_date'], format='mixed', errors='coerce')
            df = df.sort_values(['product_code', 'effective_date'])
            
            history_records = []
            
            for product_code in df['product_code'].unique():
                product_prices = df[df['product_code'] == product_code].copy()
                
                for i in range(1, len(product_prices)):
                    current = product_prices.iloc[i]
                    previous = product_prices.iloc[i-1]
                    
                    history_records.append({
                        'history_id': f"CH{i}_{product_code}",
                        'product_code': product_code,
                        'old_price_usd': previous['standard_price_usd'],
                        'new_price_usd': current['standard_price_usd'],
                        'old_price_local': previous['standard_price_local'],
                        'new_price_local': current['standard_price_local'],
                        'local_currency': current['local_currency'],
                        'change_date': current['effective_date'],
                        'change_reason': current['change_reason']
                    })
            
            return pd.DataFrame(history_records)
            
        except Exception as e:
            print(f"가격 변경 이력 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_price_variance_analysis(self):
        """가격 편차 분석 데이터를 조회합니다."""
        try:
            # 실제 거래 데이터와 표준가 데이터를 결합하여 편차 분석
            sales_df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            
            if len(sales_df) == 0:
                return pd.DataFrame()
            
            # 편차 분석을 위한 데이터 준비
            variance_data = []
            
            for _, row in sales_df.iterrows():
                if row['standard_price_usd'] > 0:  # 표준가가 있는 경우만
                    variance_data.append({
                        'product_code': row['product_code'],
                        'standard_price': row['standard_price_usd'],
                        'actual_price': row['unit_price_usd'],
                        'currency': row['local_currency'],
                        'sale_date': row['sale_date']
                    })
            
            return pd.DataFrame(variance_data)
            
        except Exception as e:
            print(f"가격 편차 분석 중 오류: {e}")
            return pd.DataFrame()
    
    def get_sales_performance_analysis(self):
        """판매 성과 분석 데이터를 조회합니다."""
        try:
            sales_df = pd.read_csv(self.sales_transactions_file, encoding='utf-8-sig')
            
            if len(sales_df) == 0:
                return {}
            
            # 기본 성과 지표 계산
            total_sales = sales_df['total_amount_usd'].sum()
            total_orders = len(sales_df)
            avg_price = sales_df['unit_price_usd'].mean()
            
            # 마진율 계산 (표준가 대비)
            margin_data = sales_df[sales_df['standard_price_usd'] > 0]
            if len(margin_data) > 0:
                margin_rate = ((margin_data['unit_price_usd'] - margin_data['standard_price_usd']) / margin_data['standard_price_usd'] * 100).mean()
            else:
                margin_rate = 0
            
            # 제품별 성과
            product_performance = sales_df.groupby('product_code').agg({
                'total_amount_usd': 'sum',
                'quantity': 'sum',
                'unit_price_usd': 'mean'
            }).reset_index()
            
            product_performance.columns = ['product_code', 'sales_amount', 'quantity_sold', 'avg_price']
            
            # 마진율 계산 추가
            product_performance['margin_rate'] = 0  # 기본값
            
            performance_data = {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'avg_price': avg_price,
                'margin_rate': margin_rate,
                'sales_change_pct': 0,  # 비교 기간 데이터가 있을 때 계산
                'orders_change_pct': 0,
                'price_change_pct': 0,
                'margin_change_pct': 0,
                'product_performance': product_performance.to_dict('records')
            }
            
            return performance_data
            
        except Exception as e:
            print(f"판매 성과 분석 중 오류: {e}")
            return {}
    
    def delete_price_history_record(self, history_id):
        """가격 변경 이력 레코드를 삭제합니다."""
        try:
            # 실제로는 price_history에서 해당 이력을 제거하거나 비활성화
            return True
        except Exception as e:
            print(f"가격 이력 삭제 중 오류: {e}")
            return False
    
    def update_price_history_record(self, history_id, update_data):
        """가격 변경 이력 레코드를 업데이트합니다."""
        try:
            # 실제로는 price_history에서 해당 이력을 업데이트
            return True
        except Exception as e:
            print(f"가격 이력 업데이트 중 오류: {e}")
            return False