import pandas as pd
import os
from datetime import datetime, timedelta
import json

class InvoiceManager:
    def __init__(self):
        self.data_file = 'data/invoices.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'invoice_id', 'invoice_number', 'quotation_id', 'customer_id',
                'customer_name', 'invoice_date', 'due_date', 'payment_terms',
                'subtotal', 'tax_amount', 'total_amount', 'currency',
                'products_json', 'billing_address', 'payment_method',
                'payment_status', 'payment_date', 'notes', 'created_by',
                'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_invoice_number(self):
        """인보이스 번호를 생성합니다."""
        try:
            today = datetime.now()
            prefix = f"INV{today.strftime('%Y%m')}"
            
            df = self.get_all_invoices()
            existing_numbers = df[df['invoice_number'].str.startswith(prefix)]['invoice_number'].tolist()
            
            numbers = []
            for inv_num in existing_numbers:
                try:
                    suffix = inv_num.replace(prefix, '')
                    if suffix.isdigit():
                        numbers.append(int(suffix))
                except:
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
            return f"{prefix}{next_num:03d}"
        except Exception as e:
            print(f"인보이스 번호 생성 중 오류: {e}")
            return f"INV{datetime.now().strftime('%Y%m')}001"
    
    def create_invoice(self, invoice_data):
        """새 인보이스를 생성합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 인보이스 번호가 없으면 생성
            if 'invoice_number' not in invoice_data or not invoice_data['invoice_number']:
                invoice_data['invoice_number'] = self.generate_invoice_number()
            
            # 인보이스 ID 생성
            if 'invoice_id' not in invoice_data or not invoice_data['invoice_id']:
                invoice_data['invoice_id'] = f"INVID{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in invoice_data:
                invoice_data['products_json'] = json.dumps(invoice_data['products'], ensure_ascii=False)
                del invoice_data['products']
            
            # 기본값 설정
            invoice_data['payment_status'] = invoice_data.get('payment_status', '미결제')
            invoice_data['invoice_date'] = invoice_data.get('invoice_date', datetime.now().strftime('%Y-%m-%d'))
            
            # 결제 기한 설정 (기본 30일)
            if 'due_date' not in invoice_data or not invoice_data['due_date']:
                due_date = datetime.now() + timedelta(days=30)
                invoice_data['due_date'] = due_date.strftime('%Y-%m-%d')
            
            invoice_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            invoice_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([invoice_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"인보이스 생성 중 오류: {e}")
            return False
    
    def get_all_invoices(self):
        """모든 인보이스 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # products_json을 products로 변환
            if 'products_json' in df.columns:
                df['products'] = df['products_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            return df
        except Exception as e:
            print(f"인보이스 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_invoice_by_id(self, invoice_id):
        """특정 인보이스 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            invoice = df[df['invoice_id'] == invoice_id]
            if len(invoice) > 0:
                result = invoice.iloc[0].to_dict()
                
                # products_json을 products로 변환
                if 'products_json' in result and result['products_json']:
                    try:
                        result['products'] = json.loads(result['products_json'])
                    except:
                        result['products'] = []
                
                return result
            return None
        except Exception as e:
            print(f"인보이스 조회 중 오류: {e}")
            return None
    
    def update_invoice(self, invoice_id, invoice_data):
        """인보이스 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if invoice_id not in df['invoice_id'].values:
                return False
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in invoice_data:
                invoice_data['products_json'] = json.dumps(invoice_data['products'], ensure_ascii=False)
                del invoice_data['products']
            
            invoice_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in invoice_data.items():
                if key in df.columns:
                    df.loc[df['invoice_id'] == invoice_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"인보이스 업데이트 중 오류: {e}")
            return False
    
    def mark_as_paid(self, invoice_id, payment_date=None, payment_method=None, notes=None):
        """인보이스를 결제 완료로 표시합니다."""
        try:
            update_data = {
                'payment_status': '결제완료',
                'payment_date': payment_date or datetime.now().strftime('%Y-%m-%d')
            }
            
            if payment_method:
                update_data['payment_method'] = payment_method
            
            if notes:
                update_data['notes'] = notes
            
            return self.update_invoice(invoice_id, update_data)
        except Exception as e:
            print(f"결제 완료 처리 중 오류: {e}")
            return False
    
    def get_overdue_invoices(self):
        """연체된 인보이스를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 날짜 컬럼을 datetime으로 변환
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
            today = pd.to_datetime(datetime.now().date())
            
            # 미결제이고 기한이 지난 인보이스들
            overdue = df[
                (df['payment_status'] == '미결제') & 
                (df['due_date'] < today)
            ]
            
            return overdue
        except Exception as e:
            print(f"연체 인보이스 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_invoices_by_status(self, status):
        """상태별 인보이스를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['payment_status'] == status]
        except Exception as e:
            print(f"상태별 인보이스 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_invoice_statistics(self):
        """인보이스 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 금액을 숫자로 변환
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
            
            # 연체 인보이스
            overdue_invoices = self.get_overdue_invoices()
            
            stats = {
                'total_invoices': len(df),
                'paid_invoices': len(df[df['payment_status'] == '결제완료']),
                'unpaid_invoices': len(df[df['payment_status'] == '미결제']),
                'overdue_invoices': len(overdue_invoices),
                'total_amount': df['total_amount'].sum(),
                'paid_amount': df[df['payment_status'] == '결제완료']['total_amount'].sum(),
                'unpaid_amount': df[df['payment_status'] == '미결제']['total_amount'].sum(),
                'overdue_amount': overdue_invoices['total_amount'].sum() if len(overdue_invoices) > 0 else 0,
                'payment_rate': (len(df[df['payment_status'] == '결제완료']) / len(df) * 100) if len(df) > 0 else 0,
                'status_distribution': df['payment_status'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"인보이스 통계 조회 중 오류: {e}")
            return {}
    
    def create_invoice_from_quotation(self, quotation_data, billing_address, payment_terms='NET 30'):
        """견적서에서 인보이스를 생성합니다."""
        try:
            # 세금 계산 (기본 10% VAT)
            subtotal = float(quotation_data.get('total_amount_usd', 0))
            tax_rate = 0.1  # 10% VAT
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            invoice_data = {
                'quotation_id': quotation_data.get('quotation_id'),
                'customer_id': quotation_data.get('customer_id'),
                'customer_name': quotation_data.get('customer_name'),
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'currency': quotation_data.get('currency', 'USD'),
                'products': quotation_data.get('products', []),
                'billing_address': billing_address,
                'payment_terms': payment_terms,
                'payment_status': '미결제'
            }
            
            if self.create_invoice(invoice_data):
                return self.get_all_invoices().iloc[-1]['invoice_id']
            
            return None
        except Exception as e:
            print(f"견적서에서 인보이스 생성 중 오류: {e}")
            return None
    
    def get_payment_analytics(self):
        """결제 분석 데이터를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 날짜 컬럼을 datetime으로 변환
            df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
            
            # 결제 완료된 인보이스만 필터
            paid_df = df[df['payment_status'] == '결제완료'].copy()
            
            if len(paid_df) == 0:
                return {
                    'average_payment_days': 0,
                    'monthly_revenue': {},
                    'payment_method_distribution': {},
                    'early_payments': 0,
                    'late_payments': 0,
                    'on_time_payments': 0
                }
            
            # 결제 기간 계산
            paid_df['payment_days'] = (paid_df['payment_date'] - pd.to_datetime(paid_df['invoice_date'])).dt.days
            paid_df['days_from_due'] = (paid_df['payment_date'] - paid_df['due_date']).dt.days
            
            # 월별 매출
            paid_df['payment_month'] = paid_df['payment_date'].dt.to_period('M')
            monthly_revenue = paid_df.groupby('payment_month')['total_amount'].sum().to_dict()
            
            # 결제 방식 분포
            payment_method_dist = paid_df['payment_method'].value_counts().to_dict()
            
            # 결제 타이밍 분석
            early_payments = len(paid_df[paid_df['days_from_due'] < 0])
            on_time_payments = len(paid_df[paid_df['days_from_due'] == 0])
            late_payments = len(paid_df[paid_df['days_from_due'] > 0])
            
            analytics = {
                'average_payment_days': paid_df['payment_days'].mean(),
                'monthly_revenue': {str(k): v for k, v in monthly_revenue.items()},
                'payment_method_distribution': payment_method_dist,
                'early_payments': early_payments,
                'late_payments': late_payments,
                'on_time_payments': on_time_payments
            }
            
            return analytics
        except Exception as e:
            print(f"결제 분석 중 오류: {e}")
            return {}
