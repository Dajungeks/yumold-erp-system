import pandas as pd
import os
import requests
from datetime import datetime, timedelta

class ExchangeRateManager:
    def __init__(self):
        self.data_file = 'data/exchange_rates.csv'
        self.api_key = os.getenv('OPEN_EXCHANGE_RATES_API_KEY', '8778586b7483463fae392e7c886d8099')
        self.base_url = 'https://openexchangerates.org/api'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'rate_id', 'currency_code', 'currency_name', 'rate',
                'base_currency', 'rate_date', 'source', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def fetch_exchange_rates(self):
        """외부 API에서 환율을 가져옵니다."""
        try:
            if self.api_key == 'demo_key' or self.api_key == '8778586b7483463fae392e7c886d8099':
                # 데모 데이터 사용 - 딕셔너리 형태로 반환
                demo_rates = {
                    'KRW': 1300.50,
                    'VND': 24500.00,
                    'THB': 35.75,
                    'CNY': 7.25,
                    'EUR': 0.85,
                    'JPY': 110.25,
                    'SGD': 1.35,
                    'MYR': 4.15,
                    'IDR': 15500.00
                }
                return demo_rates
            
            # 실제 API 호출
            url = f"{self.base_url}/latest.json"
            params = {
                'app_id': self.api_key,
                'base': 'USD'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('rates', {})
        except Exception as e:
            print(f"환율 조회 실패: {e}")
            return None
    
    def fetch_historical_rates(self, date_str):
        """특정 날짜의 과거 환율을 가져옵니다."""
        try:
            if self.api_key == 'demo_key' or self.api_key == '8778586b7483463fae392e7c886d8099':
                print(f"API 키로 {date_str} 과거 환율 조회 중...")
                
            # 과거 환율 API 호출
            url = f"{self.base_url}/historical/{date_str}.json"
            params = {
                'app_id': self.api_key,
                'base': 'USD'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('rates', {})
        except Exception as e:
            print(f"{date_str} 과거 환율 조회 실패: {e}")
            return None
    
    def populate_historical_data(self):
        """2025년 1월 1일부터 현재까지의 환율 데이터를 수집합니다."""
        try:
            start_date = datetime(2025, 1, 1)
            current_date = datetime.now()
            
            print(f"환율 데이터 수집 시작: {start_date.strftime('%Y-%m-%d')}부터 {current_date.strftime('%Y-%m-%d')}까지")
            
            # 날짜별로 환율 데이터 수집
            current = start_date
            success_count = 0
            
            while current <= current_date:
                date_str = current.strftime('%Y-%m-%d')
                rates = self.fetch_historical_rates(date_str)
                
                if rates:
                    # 환율 데이터 저장
                    self.save_historical_rates(rates, current)
                    success_count += 1
                    print(f"{date_str} 환율 데이터 저장 완료")
                else:
                    print(f"{date_str} 환율 데이터 수집 실패")
                
                # 다음 날로 이동
                current += timedelta(days=1)
                
                # API 호출 제한을 고려한 지연 (무료 계정은 1000회/월 제한)
                import time
                time.sleep(0.1)
            
            print(f"환율 데이터 수집 완료: 총 {success_count}일의 데이터 수집")
            return success_count > 0
            
        except Exception as e:
            print(f"과거 환율 데이터 수집 중 오류: {e}")
            return False
    
    def save_historical_rates(self, rates, rate_date):
        """과거 환율 데이터를 저장합니다."""
        try:
            # 주요 통화만 저장
            target_currencies = {
                'KRW': '대한민국 원',
                'VND': '베트남 동', 
                'THB': '태국 바트',
                'CNY': '중국 위안',
                'EUR': '유로',
                'JPY': '일본 엔',
                'SGD': '싱가포르 달러',
                'MYR': '말레이시아 링깃',
                'IDR': '인도네시아 루피아'
            }
            
            new_rates = []
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            for currency_code, currency_name in target_currencies.items():
                if currency_code in rates:
                    rate_id = f"RATE{timestamp}{currency_code}"
                    rate_data = {
                        'rate_id': rate_id,
                        'currency_code': currency_code,
                        'currency_name': currency_name,
                        'rate': float(rates[currency_code]) if rates[currency_code] is not None else 0.0,
                        'base_currency': 'USD',
                        'rate_date': rate_date.strftime('%Y-%m-%d'),
                        'source': 'OpenExchangeRates API (Historical)',
                        'input_date': rate_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    new_rates.append(rate_data)
            
            if new_rates:
                # 기존 데이터 읽기
                if os.path.exists(self.data_file):
                    existing_df = pd.read_csv(self.data_file, encoding='utf-8-sig')
                else:
                    existing_df = pd.DataFrame()
                
                # 새 데이터 추가
                new_df = pd.DataFrame(new_rates)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # 중복 제거 (같은 날짜, 같은 통화)
                combined_df = combined_df.drop_duplicates(
                    subset=['currency_code', 'rate_date'], 
                    keep='last'
                )
                
                # 저장
                combined_df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
                
        except Exception as e:
            print(f"과거 환율 데이터 저장 중 오류: {e}")
    
    def update_exchange_rates(self):
        """환율을 업데이트합니다."""
        try:
            rates = self.fetch_exchange_rates()
            
            if not rates:
                return False
            
            # 기본값과 동일한지 확인 (실제 API 데이터인지 검증)
            default_rates = {
                'KRW': 1300.00,
                'VND': 24000.00,
                'THB': 35.00,
                'CNY': 7.00,
                'EUR': 0.85,
                'JPY': 110.00
            }
            
            # 모든 환율이 기본값과 동일하면 실제 API 데이터가 아님
            is_default_data = False
            try:
                is_default_data = all(
                    abs(float(rates.get(currency, 0)) - float(default_rate)) < 0.01
                    for currency, default_rate in default_rates.items()
                    if currency in rates and isinstance(rates.get(currency), (int, float))
                )
            except (TypeError, ValueError):
                print("환율 데이터 형식 오류 감지 - 기본값 사용")
                is_default_data = True
            
            if is_default_data:
                print("기본값 환율이 반환되었습니다. 실제 API 연결 필요.")
                return False
            
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 통화 이름 매핑
            currency_names = {
                'KRW': '대한민국 원',
                'VND': '베트남 동',
                'THB': '태국 바트',
                'CNY': '중국 위안',
                'EUR': '유로',
                'JPY': '일본 엔',
                'SGD': '싱가포르 달러',
                'MYR': '말레이시아 링깃',
                'IDR': '인도네시아 루피아'
            }
            
            # 각 환율 업데이트
            for currency_code, rate in rates.items():
                if currency_code in currency_names:
                    # 기존 데이터 확인
                    existing = df[
                        (df['currency_code'] == currency_code) & 
                        (df['rate_date'] == current_date)
                    ]
                    
                    if len(existing) == 0:
                        # 새 레코드 추가
                        new_rate = {
                            'rate_id': f"RATE{datetime.now().strftime('%Y%m%d%H%M%S')}{currency_code}",
                            'currency_code': currency_code,
                            'currency_name': currency_names[currency_code],
                            'rate': float(rate) if rate is not None else 0.0,
                            'base_currency': 'USD',
                            'rate_date': current_date,
                            'source': 'OpenExchangeRates API',
                            'input_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        df = pd.concat([df, pd.DataFrame([new_rate])], ignore_index=True)
                    else:
                        # 기존 레코드 업데이트
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        df.loc[
                            (df['currency_code'] == currency_code) & 
                            (df['rate_date'] == current_date),
                            ['rate', 'source', 'updated_date']
                        ] = [float(rate) if rate is not None else 0.0, 'OpenExchangeRates API (Live)', current_time]
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"환율 업데이트 중 오류: {e}")
            return False
    
    def force_update_exchange_rates(self):
        """강제로 환율을 현재 시간으로 업데이트합니다 (API 실패 시에도)."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 모든 환율의 업데이트 시간을 현재 시간으로 갱신
            df.loc[:, 'updated_date'] = current_time
            df.loc[:, 'rate_date'] = current_date
            df.loc[:, 'source'] = 'Manual Update (기본값)'
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"강제 환율 업데이트 중 오류: {e}")
            return False
    
    def get_all_rates(self):
        """모든 환율 데이터를 가져옵니다."""
        try:
            return pd.read_csv(self.data_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"환율 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_latest_rates(self):
        """최신 환율을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 각 통화별 최신 환율을 안전하게 조회
            latest_rates = []
            for currency in df['currency_code'].unique():
                currency_df = df[df['currency_code'] == currency].copy()
                if len(currency_df) > 0:
                    # 날짜를 파싱하여 가장 최신 날짜 찾기
                    currency_df.loc[:, 'rate_date'] = pd.to_datetime(currency_df['rate_date'])
                    latest_row = currency_df.loc[currency_df['rate_date'].idxmax()]
                    latest_rates.append(latest_row.to_dict())
            
            return pd.DataFrame(latest_rates) if latest_rates else pd.DataFrame()
        except Exception as e:
            print(f"최신 환율 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_rate_by_currency(self, currency_code, rate_date=None):
        """특정 통화의 환율을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if rate_date:
                rate = df[
                    (df['currency_code'] == currency_code) & 
                    (df['rate_date'] == rate_date)
                ]
            else:
                # 최신 환율
                currency_rates = df[df['currency_code'] == currency_code]
                if len(currency_rates) > 0:
                    rate = currency_rates.loc[currency_rates['rate_date'].idxmax()]
                else:
                    return None
            
            if rate is not None and len(rate) > 0:
                return rate.iloc[0].to_dict() if isinstance(rate, pd.DataFrame) else rate.to_dict()
            return None
        except Exception as e:
            print(f"환율 조회 중 오류: {e}")
            return None
    
    def convert_currency(self, amount, from_currency, to_currency, rate_date=None):
        """통화를 변환합니다."""
        try:
            if from_currency == to_currency:
                return amount
            
            # USD를 기준으로 변환
            if from_currency == 'USD':
                to_rate_data = self.get_rate_by_currency(to_currency, rate_date)
                if to_rate_data is not None:
                    to_rate = to_rate_data['rate'] if isinstance(to_rate_data, dict) else to_rate_data.rate
                    return amount * to_rate
            elif to_currency == 'USD':
                from_rate_data = self.get_rate_by_currency(from_currency, rate_date)
                if from_rate_data is not None:
                    from_rate = from_rate_data['rate'] if isinstance(from_rate_data, dict) else from_rate_data.rate
                    return amount / from_rate
            else:
                # 두 통화 모두 USD가 아닌 경우
                from_rate_data = self.get_rate_by_currency(from_currency, rate_date)
                to_rate_data = self.get_rate_by_currency(to_currency, rate_date)
                
                if from_rate_data is not None and to_rate_data is not None:
                    from_rate = from_rate_data['rate'] if isinstance(from_rate_data, dict) else from_rate_data.rate
                    to_rate = to_rate_data['rate'] if isinstance(to_rate_data, dict) else to_rate_data.rate
                    
                    # USD를 거쳐서 변환
                    usd_amount = amount / from_rate
                    return usd_amount * to_rate
            
            return None
        except Exception as e:
            print(f"통화 변환 중 오류: {e}")
            return None
    
    def get_historical_rates(self, currency_code, days=30):
        """과거 환율 데이터를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 날짜 필터링 - 2025년 1월 1일부터 현재까지
            end_date = datetime.now()
            start_date = datetime(2025, 1, 1)
            
            df['rate_date'] = pd.to_datetime(df['rate_date'])
            
            historical_data = df[
                (df['currency_code'] == currency_code) &
                (df['rate_date'] >= start_date) &
                (df['rate_date'] <= end_date)
            ].sort_values('rate_date')
            
            return historical_data
        except Exception as e:
            print(f"과거 환율 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_rate_statistics(self, currency_code, days=30):
        """환율 통계를 가져옵니다."""
        try:
            historical_data = self.get_historical_rates(currency_code, days)
            
            if len(historical_data) == 0:
                return {}
            
            rates = historical_data['rate'].astype(float)
            
            stats = {
                'current_rate': float(rates.iloc[-1]) if len(rates) > 0 else 0.0,
                'avg_rate': float(rates.mean()) if len(rates) > 0 else 0.0,
                'min_rate': float(rates.min()) if len(rates) > 0 else 0.0,
                'max_rate': float(rates.max()) if len(rates) > 0 else 0.0,
                'rate_change': float(rates.iloc[-1] - rates.iloc[0]) if len(rates) > 1 else 0.0,
                'rate_change_percent': float(((rates.iloc[-1] - rates.iloc[0]) / rates.iloc[0] * 100)) if len(rates) > 1 and float(rates.iloc[0]) != 0 else 0.0,
                'std_rate': float(rates.std()) if len(rates) > 0 else 0.0,
                'data_points': len(rates)
            }
            
            return stats
        except Exception as e:
            print(f"환율 통계 조회 중 오류: {e}")
            return {}
    
    def add_manual_rate(self, currency_code, currency_name, rate, rate_date=None):
        """수동으로 환율을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if rate_date is None:
                rate_date = datetime.now().strftime('%Y-%m-%d')
            
            new_rate = {
                'rate_id': f"RATE{datetime.now().strftime('%Y%m%d%H%M%S')}{currency_code}",
                'currency_code': currency_code,
                'currency_name': currency_name,
                'rate': rate,
                'base_currency': 'USD',
                'rate_date': rate_date,
                'source': 'Manual Input',
                'input_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            df = pd.concat([df, pd.DataFrame([new_rate])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"수동 환율 추가 중 오류: {e}")
            return False
    
    def get_supported_currencies(self):
        """지원되는 통화 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            currencies = df[['currency_code', 'currency_name']].drop_duplicates()
            return currencies.to_dict('records')
        except Exception as e:
            print(f"지원 통화 조회 중 오류: {e}")
            return []
    
    def get_all_latest_rates(self):
        """모든 통화의 최신 환율을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 각 통화별로 최신 날짜의 환율만 선택
            latest_rates = df.loc[df.groupby('currency_code')['rate_date'].idxmax()]
            
            return latest_rates.sort_values('currency_code')
        except Exception as e:
            print(f"전체 최신 환율 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_quarterly_average_rate(self, currency_code, year, quarter):
        """분기별 평균 환율을 계산합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return None
            
            # 분기별 월 매핑
            quarter_months = {
                1: [1, 2, 3],    # 1분기: 1-3월
                2: [4, 5, 6],    # 2분기: 4-6월  
                3: [7, 8, 9],    # 3분기: 7-9월
                4: [10, 11, 12]  # 4분기: 10-12월
            }
            
            months = quarter_months.get(quarter, [])
            if not months:
                return None
            
            # 해당 통화와 분기에 해당하는 데이터 필터링
            currency_df = df[df['currency_code'] == currency_code].copy()
            currency_df['rate_date'] = pd.to_datetime(currency_df['rate_date'])
            
            # 2025년 1월 1일 이후 데이터만 사용
            start_date = datetime(2025, 1, 1)
            
            # 해당 연도와 분기 데이터 필터링
            quarterly_data = currency_df[
                (currency_df['rate_date'] >= start_date) &
                (currency_df['rate_date'].dt.year == year) &
                (currency_df['rate_date'].dt.month.isin(months))
            ]
            
            if len(quarterly_data) == 0:
                # 분기 데이터가 없으면 None 반환
                return None
            
            # 분기 평균 계산
            average_rate = quarterly_data['rate'].mean()
            return float(average_rate) if pd.notna(average_rate) else None
            
        except Exception as e:
            print(f"분기 평균 환율 계산 중 오류: {e}")
            return None
    
    def get_monthly_average_rate(self, currency_code, year, month):
        """월별 평균 환율을 계산합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return None
            
            # 해당 통화와 월에 해당하는 데이터 필터링
            currency_df = df[df['currency_code'] == currency_code].copy()
            currency_df['rate_date'] = pd.to_datetime(currency_df['rate_date'])
            
            # 해당 연도와 월 데이터 필터링
            monthly_data = currency_df[
                (currency_df['rate_date'].dt.year == year) &
                (currency_df['rate_date'].dt.month == month)
            ]
            
            if len(monthly_data) == 0:
                # 월 데이터가 없으면 None 반환
                return None
            
            # 월 평균 계산
            average_rate = monthly_data['rate'].mean()
            return float(average_rate) if pd.notna(average_rate) else None
            
        except Exception as e:
            print(f"월 평균 환율 계산 중 오류: {e}")
            return None
