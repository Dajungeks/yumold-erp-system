import pandas as pd
import os
from datetime import datetime
import uuid

class CashFlowManager:
    def __init__(self):
        self.cash_flow_file = "data/cash_flow.csv"
        self.payments_file = "data/payments.csv"
        self.ensure_data_directory()
        self.load_cash_flow()
    
    def ensure_data_directory(self):
        """Ensure data directory and files exist"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.cash_flow_file):
            cash_flow_df = pd.DataFrame(columns=[
                'transaction_id', 'reference_id', 'reference_type', 'transaction_type',
                'amount', 'currency', 'transaction_date', 'description',
                'status', 'account', 'created_by', 'created_date'
            ])
            cash_flow_df.to_csv(self.cash_flow_file, index=False)
        
        if not os.path.exists(self.payments_file):
            payments_df = pd.DataFrame(columns=[
                'payment_id', 'invoice_id', 'payment_date', 'amount',
                'payment_method', 'reference_number', 'status', 'notes'
            ])
            payments_df.to_csv(self.payments_file, index=False)
    
    def load_cash_flow(self):
        """Load cash flow from CSV files"""
        try:
            self.cash_flow_df = pd.read_csv(self.cash_flow_file)
            self.payments_df = pd.read_csv(self.payments_file)
        except Exception as e:
            print(f"Error loading cash flow: {e}")
            self.cash_flow_df = pd.DataFrame()
            self.payments_df = pd.DataFrame()
    
    def record_payment_received(self, invoice_id, amount, payment_method='bank_transfer', reference_number=None):
        """Record payment received from customer"""
        try:
            payment_id = str(uuid.uuid4())
            
            # Record payment
            payment_data = {
                'payment_id': payment_id,
                'invoice_id': invoice_id,
                'payment_date': datetime.now().strftime('%Y-%m-%d'),
                'amount': amount,
                'payment_method': payment_method,
                'reference_number': reference_number,
                'status': 'received',
                'notes': None
            }
            
            new_payment_df = pd.DataFrame([payment_data])
            if len(self.payments_df) == 0:
                self.payments_df = new_payment_df
            else:
                self.payments_df = pd.concat([self.payments_df, new_payment_df], ignore_index=True)
            
            # Record cash flow transaction
            self.record_cash_flow_transaction(
                reference_id=invoice_id,
                reference_type='invoice',
                transaction_type='income',
                amount=amount,
                description=f'Payment received for invoice {invoice_id}'
            )
            
            self.save_cash_flow()
            return payment_id
        except Exception as e:
            print(f"Error recording payment: {e}")
            return None
    
    def record_payment_made(self, po_id, amount, payment_method='bank_transfer', reference_number=None):
        """Record payment made to supplier"""
        try:
            # Record cash flow transaction
            transaction_id = self.record_cash_flow_transaction(
                reference_id=po_id,
                reference_type='purchase_order',
                transaction_type='expense',
                amount=amount,
                description=f'Payment made for purchase order {po_id}'
            )
            
            self.save_cash_flow()
            return transaction_id
        except Exception as e:
            print(f"Error recording payment made: {e}")
            return None
    
    def record_cash_flow_transaction(self, reference_id, reference_type, transaction_type, amount, description, account='main', currency='USD', transaction_date=None):
        """Record cash flow transaction"""
        try:
            transaction_id = str(uuid.uuid4())
            
            transaction_data = {
                'transaction_id': transaction_id,
                'reference_id': reference_id,
                'reference_type': reference_type,
                'transaction_type': transaction_type,
                'amount': amount,
                'currency': currency,
                'transaction_date': transaction_date if transaction_date else datetime.now().strftime('%Y-%m-%d'),
                'description': description,
                'status': 'completed',
                'account': account,
                'created_by': 'system',
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            new_transaction_df = pd.DataFrame([transaction_data])
            if len(self.cash_flow_df) == 0:
                self.cash_flow_df = new_transaction_df
            else:
                self.cash_flow_df = pd.concat([self.cash_flow_df, new_transaction_df], ignore_index=True)
            
            return transaction_id
        except Exception as e:
            print(f"Error recording cash flow transaction: {e}")
            return None
    
    def get_cash_flow_summary(self, start_date=None, end_date=None):
        """Get cash flow summary with real data from quotations and purchase orders"""
        summary = {'total_income': 0, 'total_expense': 0, 'current_balance': 0}
        
        if len(self.cash_flow_df) == 0:
            return summary
        
        df = self.cash_flow_df.copy()
        
        # Filter by date range if provided
        if start_date or end_date:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            if start_date:
                df = df[df['transaction_date'] >= start_date]
            if end_date:
                df = df[df['transaction_date'] <= end_date]
        
        # Calculate summary
        total_income = df[df['transaction_type'] == 'income']['amount'].sum()
        total_expense = df[df['transaction_type'] == 'expense']['amount'].sum()
        
        summary.update({
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'current_balance': float(total_income - total_expense)
        })
        
        return summary
    
    def get_monthly_cash_flow(self):
        """Get monthly cash flow summary"""
        if len(self.cash_flow_df) == 0:
            return []
        
        try:
            df = self.cash_flow_df.copy()
            # 날짜 형식을 먼저 정리
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%Y-%m-%d', errors='coerce')
            df = df.dropna(subset=['transaction_date'])
            
            if len(df) == 0:
                return []
            
            df['month'] = df['transaction_date'].dt.to_period('M')
            
            monthly_summary = df.groupby(['month', 'transaction_type'])['amount'].sum().unstack(fill_value=0)
            monthly_summary = monthly_summary.reset_index()
            monthly_summary['month'] = monthly_summary['month'].astype(str)
            
            # 컬럼명 통일 (income/expense)
            if 'income' not in monthly_summary.columns:
                monthly_summary['income'] = 0
            if 'expense' not in monthly_summary.columns:
                monthly_summary['expense'] = 0
            
            monthly_summary['net_flow'] = monthly_summary['income'] - monthly_summary['expense']
            
            # 딕셔너리 리스트로 반환
            return monthly_summary.to_dict('records')
        except Exception as e:
            print(f"Error generating monthly cash flow: {e}")
            return []
    
    def get_all_transactions(self):
        """Get all cash flow transactions"""
        if len(self.cash_flow_df) > 0:
            return self.cash_flow_df.to_dict('records')
        else:
            return []
    
    def get_all_payments(self):
        """Get all payments"""
        return self.payments_df.to_dict('records') if len(self.payments_df) > 0 else []
    
    def get_outstanding_invoices(self, invoice_manager):
        """Get outstanding invoices (not fully paid)"""
        try:
            if not hasattr(invoice_manager, 'get_all_invoices'):
                return pd.DataFrame()
            
            all_invoices = invoice_manager.get_all_invoices()
            if len(all_invoices) == 0:
                return pd.DataFrame()
            
            outstanding = []
            for _, invoice in all_invoices.iterrows():
                invoice_id = invoice['invoice_id']
                total_amount = invoice['grand_total']
                
                # Calculate paid amount
                paid_amount = 0
                if len(self.payments_df) > 0:
                    invoice_payments = self.payments_df[
                        (self.payments_df['invoice_id'] == invoice_id) & 
                        (self.payments_df['status'] == 'received')
                    ]
                    paid_amount = invoice_payments['amount'].sum()
                
                # Check if outstanding
                if paid_amount < total_amount:
                    outstanding_amount = total_amount - paid_amount
                    outstanding.append({
                        'invoice_id': invoice_id,
                        'invoice_number': invoice.get('invoice_number', ''),
                        'customer_name': invoice.get('customer_name', ''),
                        'total_amount': total_amount,
                        'paid_amount': paid_amount,
                        'outstanding_amount': outstanding_amount,
                        'invoice_date': invoice.get('invoice_date', ''),
                        'due_date': invoice.get('due_date', '')
                    })
            
            return pd.DataFrame(outstanding)
        except Exception as e:
            print(f"Error getting outstanding invoices: {e}")
            return pd.DataFrame()
    
    def sync_with_quotations(self, quotation_manager):
        """Sync cash flow with approved quotations (potential income)"""
        try:
            if not hasattr(quotation_manager, 'get_all_quotations'):
                return False
            
            all_quotations = quotation_manager.get_all_quotations()
            
            # 데이터 타입 확인 및 처리
            if isinstance(all_quotations, list):
                # 리스트인 경우 직접 처리
                quotations_list = all_quotations
            elif hasattr(all_quotations, 'to_dict'):
                # DataFrame인 경우 records 형태로 변환
                quotations_list = all_quotations.to_dict('records')
            else:
                print("Unsupported quotations data format")
                return False
            
            if len(quotations_list) == 0:
                return True
            
            # 승인된 견적서들을 수입으로 기록
            for quotation in quotations_list:
                if quotation.get('status') == 'approved':
                    quotation_id = quotation.get('quotation_id', '')
                    total_amount = quotation.get('grand_total', 0)
                    
                    # 이미 기록된 거래인지 확인
                    existing = self.cash_flow_df[
                        (self.cash_flow_df['reference_id'] == quotation_id) & 
                        (self.cash_flow_df['reference_type'] == 'quotation')
                    ]
                    
                    if len(existing) == 0 and total_amount > 0:
                        # 새로운 수입 거래 기록
                        self.record_cash_flow_transaction(
                            reference_id=quotation_id,
                            reference_type='quotation',
                            transaction_type='income',
                            amount=total_amount,
                            description=f'Approved quotation income: {quotation.get("quotation_title", quotation_id)}'
                        )
            
            self.save_cash_flow()
            return True
        except Exception as e:
            print(f"Error syncing with quotations: {e}")
            return False
    
    def clear_all_dummy_data(self):
        """더미 데이터를 완전히 제거하고 실제 데이터만 유지"""
        try:
            # 현재 데이터에서 실제 데이터(견적서, 구매주문, 인보이스 기반)만 유지
            real_reference_types = ['quotation', 'purchase_order', 'invoice']
            
            # 실제 데이터만 필터링
            if len(self.cash_flow_df) > 0:
                # reference_type이 실제 데이터 타입이거나 reference_id가 명확한 실제 데이터만 유지
                real_data_mask = (
                    (self.cash_flow_df['reference_type'].isin(real_reference_types)) |
                    (self.cash_flow_df['reference_id'].str.contains('QUO-|PO-|INV-', na=False, regex=True))
                )
                self.cash_flow_df = self.cash_flow_df[real_data_mask]
            
            # 결제 데이터에서도 더미 데이터 제거
            if len(self.payments_df) > 0:
                # 인보이스 ID가 실제 형식인 것만 유지
                real_payment_mask = self.payments_df['invoice_id'].str.contains('INV-|QUO-', na=False, regex=True)
                self.payments_df = self.payments_df[real_payment_mask]
            
            # 변경사항 저장
            self.save_cash_flow()
            
            # 월별 매출 데이터도 정리
            try:
                monthly_sales_file = "data/monthly_sales.csv"
                if os.path.exists(monthly_sales_file):
                    sales_df = pd.read_csv(monthly_sales_file, encoding='utf-8')
                    if len(sales_df) > 0:
                        # 실제 견적서나 주문 ID가 있는 것만 유지
                        real_sales_mask = (
                            (sales_df['quotation_id'].notna() & (sales_df['quotation_id'] != '')) |
                            (sales_df['order_id'].notna() & (sales_df['order_id'] != ''))
                        )
                        sales_df = sales_df[real_sales_mask]
                        sales_df.to_csv(monthly_sales_file, index=False, encoding='utf-8')
            except Exception as sales_error:
                print(f"월별 매출 더미 데이터 정리 중 오류: {sales_error}")
            
            return True, "모든 더미 데이터가 제거되었습니다. 실제 데이터만 유지됩니다."
            
        except Exception as e:
            return False, f"더미 데이터 제거 중 오류 발생: {str(e)}"
    
    def sync_with_purchase_orders(self, purchase_order_manager):
        """Sync cash flow with purchase orders (expenses)"""
        try:
            if not hasattr(purchase_order_manager, 'get_all_purchase_orders'):
                return False
            
            all_pos = purchase_order_manager.get_all_purchase_orders()
            if len(all_pos) == 0:
                return True
            
            # 승인된 구매주문들을 지출로 기록
            for _, po in all_pos.iterrows():
                if po.get('status') in ['approved', 'completed']:
                    po_id = po.get('po_id', '')
                    total_amount = po.get('total_amount', 0)
                    
                    # 이미 기록된 거래인지 확인
                    existing = self.cash_flow_df[
                        (self.cash_flow_df['reference_id'] == po_id) & 
                        (self.cash_flow_df['reference_type'] == 'purchase_order')
                    ]
                    
                    if len(existing) == 0 and total_amount > 0:
                        # 새로운 지출 거래 기록
                        self.record_cash_flow_transaction(
                            reference_id=po_id,
                            reference_type='purchase_order',
                            transaction_type='expense',
                            amount=total_amount,
                            description=f'Purchase order expense: {po.get("supplier_name", "")} - {po_id}'
                        )
            
            self.save_cash_flow()
            return True
        except Exception as e:
            print(f"Error syncing with purchase orders: {e}")
            return False
    
    def auto_sync_all_data(self, quotation_manager=None, purchase_order_manager=None, invoice_manager=None):
        """Automatically sync all real data sources"""
        try:
            sync_results = []
            
            if quotation_manager:
                result = self.sync_with_quotations(quotation_manager)
                sync_results.append(('quotations', result))
            
            if purchase_order_manager:
                result = self.sync_with_purchase_orders(purchase_order_manager)
                sync_results.append(('purchase_orders', result))
            
            # 인보이스 동기화도 추가 가능
            if invoice_manager:
                # 인보이스 기반 수입 기록 로직
                pass
            
            return sync_results
        except Exception as e:
            print(f"Error in auto sync: {e}")
            return []
    
    def save_cash_flow(self):
        """Save cash flow to CSV files"""
        try:
            self.cash_flow_df.to_csv(self.cash_flow_file, index=False)
            self.payments_df.to_csv(self.payments_file, index=False)
            return True
        except Exception as e:
            print(f"Error saving cash flow: {e}")
            return False
    
    def update_transaction(self, updated_data):
        """Update an existing transaction"""
        try:
            transaction_id = updated_data.get('transaction_id')
            if not transaction_id:
                return False
            
            # Find transaction index
            transaction_index = self.cash_flow_df[
                self.cash_flow_df['transaction_id'] == transaction_id
            ].index
            
            if len(transaction_index) == 0:
                return False
            
            # Update transaction data
            for key, value in updated_data.items():
                if key in self.cash_flow_df.columns:
                    self.cash_flow_df.loc[transaction_index[0], key] = value
            
            return self.save_cash_flow()
            
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False
    
    def delete_transaction(self, transaction_id):
        """Delete a transaction"""
        try:
            if not transaction_id:
                return False
            
            # Find and remove transaction
            initial_count = len(self.cash_flow_df)
            self.cash_flow_df = self.cash_flow_df[
                self.cash_flow_df['transaction_id'] != transaction_id
            ]
            
            # Check if transaction was actually deleted
            if len(self.cash_flow_df) < initial_count:
                return self.save_cash_flow()
            else:
                return False
                
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
    
    def remove_test_data(self):
        """Remove all test/dummy data and keep only real data from quotations/purchase orders"""
        try:
            # Keep only transactions with reference_type that are real (quotation, purchase_order, invoice)
            real_reference_types = ['quotation', 'purchase_order', 'invoice']
            
            if len(self.cash_flow_df) > 0:
                # Filter to keep only real transactions
                self.cash_flow_df = self.cash_flow_df[
                    self.cash_flow_df['reference_type'].isin(real_reference_types)
                ]
            
            return self.save_cash_flow()
            
        except Exception as e:
            print(f"Error removing test data: {e}")
            return False
