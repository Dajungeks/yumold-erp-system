import pandas as pd
import os
from datetime import datetime, date
import uuid


class CashTransactionManager:
    def __init__(self):
        self.data_dir = "data"
        self.transactions_file = os.path.join(self.data_dir, "cash_transactions.csv")
        self.stock_prices_file = os.path.join(self.data_dir, "stock_prices.csv")
        self.ensure_data_files()
        
    def ensure_data_files(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # 현금 거래 내역 파일 생성
        if not os.path.exists(self.transactions_file):
            df = pd.DataFrame(columns=[
                'transaction_id', 'date', 'type', 'category', 'amount', 'currency',
                'description', 'reference_id', 'account', 'status', 'created_by',
                'created_date', 'updated_date', 'notes'
            ])
            df.to_csv(self.transactions_file, index=False, encoding='utf-8-sig')
        
        # 주가 정보 파일 생성
        if not os.path.exists(self.stock_prices_file):
            df = pd.DataFrame(columns=[
                'price_id', 'date', 'stock_symbol', 'stock_name', 'price', 'currency',
                'change_amount', 'change_percent', 'volume', 'market', 'source',
                'created_date', 'updated_date'
            ])
            df.to_csv(self.stock_prices_file, index=False, encoding='utf-8-sig')
    
    def generate_transaction_id(self):
        """거래 ID를 생성합니다."""
        return f"TX-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def generate_price_id(self):
        """주가 ID를 생성합니다."""
        return f"SP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def add_transaction(self, transaction_data):
        """새 현금 거래를 추가합니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            
            # 거래 ID 생성
            transaction_id = self.generate_transaction_id()
            
            # 거래 데이터 준비
            new_transaction = {
                'transaction_id': transaction_id,
                'date': transaction_data.get('date', date.today().strftime('%Y-%m-%d')),
                'type': transaction_data.get('type', '입금'),
                'category': transaction_data.get('category', '기타'),
                'amount': transaction_data.get('amount', 0),
                'currency': transaction_data.get('currency', 'KRW'),
                'description': transaction_data.get('description', ''),
                'reference_id': transaction_data.get('reference_id', ''),
                'account': transaction_data.get('account', '주계좌'),
                'status': transaction_data.get('status', '완료'),
                'created_by': transaction_data.get('created_by', ''),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'notes': transaction_data.get('notes', '')
            }
            
            # 데이터 추가
            df = pd.concat([df, pd.DataFrame([new_transaction])], ignore_index=True)
            df.to_csv(self.transactions_file, index=False, encoding='utf-8-sig')
            
            return transaction_id
            
        except Exception as e:
            print(f"거래 추가 중 오류: {e}")
            return None
    
    def get_all_transactions(self):
        """모든 현금 거래를 가져옵니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"거래 목록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_transaction_by_id(self, transaction_id):
        """특정 거래 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            transaction = df[df['transaction_id'] == transaction_id]
            if len(transaction) > 0:
                return transaction.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"거래 조회 중 오류: {e}")
            return None
    
    def update_transaction(self, transaction_id, transaction_data):
        """거래 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            
            # 거래 찾기
            mask = df['transaction_id'] == transaction_id
            if not mask.any():
                return False
            
            # 데이터 업데이트
            for key, value in transaction_data.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.to_csv(self.transactions_file, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            print(f"거래 수정 중 오류: {e}")
            return False
    
    def delete_transaction(self, transaction_id):
        """거래를 삭제합니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            
            # 거래 삭제
            df = df[df['transaction_id'] != transaction_id]
            df.to_csv(self.transactions_file, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            print(f"거래 삭제 중 오류: {e}")
            return False
    
    def get_transactions_by_date_range(self, start_date, end_date):
        """날짜 범위로 거래를 조회합니다."""
        try:
            df = pd.read_csv(self.transactions_file, encoding='utf-8-sig')
            
            # 날짜 필터링
            df['date'] = pd.to_datetime(df['date'])
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            return filtered_df
            
        except Exception as e:
            print(f"날짜별 거래 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_transaction_summary(self, start_date=None, end_date=None):
        """거래 요약 정보를 가져옵니다."""
        try:
            if start_date and end_date:
                df = self.get_transactions_by_date_range(start_date, end_date)
            else:
                df = self.get_all_transactions()
            
            if len(df) == 0:
                return {
                    'total_income': 0,
                    'total_expense': 0,
                    'net_amount': 0,
                    'transaction_count': 0
                }
            
            # 수입과 지출 분리
            income_df = df[df['type'] == '입금']
            expense_df = df[df['type'] == '출금']
            
            total_income = income_df['amount'].sum() if len(income_df) > 0 else 0
            total_expense = expense_df['amount'].sum() if len(expense_df) > 0 else 0
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_amount': total_income - total_expense,
                'transaction_count': len(df)
            }
            
        except Exception as e:
            print(f"거래 요약 조회 중 오류: {e}")
            return {
                'total_income': 0,
                'total_expense': 0,
                'net_amount': 0,
                'transaction_count': 0
            }
    
    # 주가 관련 메서드
    def add_stock_price(self, price_data):
        """주가 정보를 추가합니다."""
        try:
            df = pd.read_csv(self.stock_prices_file, encoding='utf-8-sig')
            
            # 주가 ID 생성
            price_id = self.generate_price_id()
            
            # 주가 데이터 준비
            new_price = {
                'price_id': price_id,
                'date': price_data.get('date', date.today().strftime('%Y-%m-%d')),
                'stock_symbol': price_data.get('stock_symbol', ''),
                'stock_name': price_data.get('stock_name', ''),
                'price': price_data.get('price', 0),
                'currency': price_data.get('currency', 'KRW'),
                'change_amount': price_data.get('change_amount', 0),
                'change_percent': price_data.get('change_percent', 0),
                'volume': price_data.get('volume', 0),
                'market': price_data.get('market', 'KOSPI'),
                'source': price_data.get('source', '수동입력'),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 데이터 추가
            df = pd.concat([df, pd.DataFrame([new_price])], ignore_index=True)
            df.to_csv(self.stock_prices_file, index=False, encoding='utf-8-sig')
            
            return price_id
            
        except Exception as e:
            print(f"주가 추가 중 오류: {e}")
            return None
    
    def get_all_stock_prices(self):
        """모든 주가 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.stock_prices_file, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"주가 목록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_latest_stock_prices(self):
        """최신 주가 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.stock_prices_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 종목별 최신 주가만 가져오기
            df['date'] = pd.to_datetime(df['date'])
            latest_prices = df.groupby('stock_symbol').apply(
                lambda x: x.loc[x['date'].idxmax()]
            ).reset_index(drop=True)
            
            return latest_prices
            
        except Exception as e:
            print(f"최신 주가 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def update_stock_price(self, price_id, price_data):
        """주가 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.stock_prices_file, encoding='utf-8-sig')
            
            # 주가 찾기
            mask = df['price_id'] == price_id
            if not mask.any():
                return False
            
            # 데이터 업데이트
            for key, value in price_data.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.to_csv(self.stock_prices_file, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            print(f"주가 수정 중 오류: {e}")
            return False
    
    def delete_stock_price(self, price_id):
        """주가 정보를 삭제합니다."""
        try:
            df = pd.read_csv(self.stock_prices_file, encoding='utf-8-sig')
            
            # 주가 삭제
            df = df[df['price_id'] != price_id]
            df.to_csv(self.stock_prices_file, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            print(f"주가 삭제 중 오류: {e}")
            return False