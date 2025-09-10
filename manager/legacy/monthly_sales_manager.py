"""
월별 매출 관리자 - 월별 매출 분석, 트렌드, 목표 관리
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
from currency_helper import CurrencyHelper

class MonthlySalesManager:
    def __init__(self):
        self.data_dir = "data"
        self.monthly_sales_file = os.path.join(self.data_dir, "monthly_sales.csv")
        self.sales_targets_file = os.path.join(self.data_dir, "sales_targets.csv")
        self.currency_helper = CurrencyHelper()
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """데이터 파일들이 존재하는지 확인하고 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 월별 매출 파일 초기화
        if not os.path.exists(self.monthly_sales_file):
            monthly_sales_data = {
                'sales_id': [],
                'year_month': [],
                'customer_id': [],
                'customer_name': [],
                'product_code': [],
                'product_name': [],
                'category': [],
                'quantity': [],
                'unit_price': [],
                'total_amount': [],
                'currency': [],
                'amount_vnd': [],
                'amount_usd': [],
                'sales_date': [],
                'quotation_id': [],
                'order_id': [],
                'payment_status': [],
                'sales_rep': [],
                'profit_margin': [],
                'cost_amount': [],
                'created_date': [],
                'updated_date': []
            }
            monthly_sales_df = pd.DataFrame(monthly_sales_data)
            monthly_sales_df.to_csv(self.monthly_sales_file, index=False, encoding='utf-8')
        
        # 매출 목표 파일 초기화
        if not os.path.exists(self.sales_targets_file):
            sales_targets_data = {
                'target_id': [],
                'year_month': [],
                'target_type': [],
                'target_category': [],
                'target_amount_vnd': [],
                'target_amount_usd': [],
                'currency': [],
                'target_quantity': [],
                'responsible_person': [],
                'description': [],
                'created_date': [],
                'updated_date': []
            }
            sales_targets_df = pd.DataFrame(sales_targets_data)
            sales_targets_df.to_csv(self.sales_targets_file, index=False, encoding='utf-8')
            
        # 실제 데이터 연동 (더미 데이터 생성 제거)
        self._sync_with_real_data()
    
    def _sync_with_real_data(self):
        """실제 ERP 데이터(견적서, 주문, 현금흐름)와 동기화"""
        try:
            # 실제 데이터 연동
            self._import_from_quotations()
            self._import_from_orders() 
            self._import_from_cash_flow()
            
        except Exception as e:
            print(f"실제 데이터 동기화 오류: {str(e)}")
    
    def _import_from_quotations(self):
        """견적서 데이터에서 매출 예상 데이터 생성"""
        try:
            from quotation_manager import QuotationManager
            quotation_manager = QuotationManager()
            quotations = quotation_manager.get_all_quotations()
            
            # 승인된 견적서만 매출 예상으로 포함
            approved_quotations = [q for q in quotations if isinstance(q, dict) and q.get('status') == '승인']
            
            for quotation in approved_quotations:
                # 견적서 데이터를 매출 예상으로 변환
                quotation_date = quotation.get('quotation_date', datetime.now().strftime('%Y-%m-%d'))
                if isinstance(quotation_date, str):
                    try:
                        quote_date = datetime.strptime(quotation_date, '%Y-%m-%d')
                        year_month = quote_date.strftime('%Y-%m')
                        
                        # 견적서 제품 정보 파싱
                        products_info = quotation.get('products_info', '[]')
                        if isinstance(products_info, str):
                            try:
                                import json
                                products = json.loads(products_info)
                            except:
                                products = []
                        else:
                            products = products_info if isinstance(products_info, list) else []
                        
                        for product in products:
                            if isinstance(product, dict):
                                self._add_sales_from_source(
                                    source_type='quotation',
                                    source_id=quotation.get('quotation_id', ''),
                                    year_month=year_month,
                                    customer_id=quotation.get('customer_id', ''),
                                    customer_name=quotation.get('customer_name', ''),
                                    product_code=product.get('product_code', ''),
                                    product_name=product.get('product_name', ''),
                                    category=product.get('category', 'UNKNOWN'),
                                    quantity=float(product.get('quantity', 1)),
                                    unit_price=float(product.get('unit_price', 0)),
                                    currency=quotation.get('currency', 'USD'),
                                    sales_date=quotation_date,
                                    payment_status='pending',
                                    sales_rep=quotation.get('created_by', 'Unknown')
                                )
                    except Exception as date_error:
                        continue
                        
        except Exception as e:
            print(f"견적서 데이터 연동 오류: {str(e)}")
    
    def _import_from_orders(self):
        """주문 데이터에서 실제 매출 데이터 생성"""
        try:
            import os
            order_file = os.path.join(self.data_dir, "orders.csv")
            
            if os.path.exists(order_file):
                orders_df = pd.read_csv(order_file, encoding='utf-8')
                
                for _, order in orders_df.iterrows():
                    if order.get('status') in ['confirmed', 'delivered']:
                        try:
                            order_date = order.get('order_date', datetime.now().strftime('%Y-%m-%d'))
                            if isinstance(order_date, str):
                                order_date_obj = datetime.strptime(order_date, '%Y-%m-%d')
                                year_month = order_date_obj.strftime('%Y-%m')
                                
                                # 주문 제품 정보 파싱
                                products_info = order.get('products_info', '[]')
                                if isinstance(products_info, str):
                                    try:
                                        import json
                                        products = json.loads(products_info)
                                    except:
                                        products = []
                                else:
                                    products = products_info if isinstance(products_info, list) else []
                                
                                for product in products:
                                    if isinstance(product, dict):
                                        payment_status = 'paid' if order.get('payment_status') == 'paid' else 'pending'
                                        
                                        self._add_sales_from_source(
                                            source_type='order',
                                            source_id=order.get('order_id', ''),
                                            year_month=year_month,
                                            customer_id=order.get('customer_id', ''),
                                            customer_name=order.get('customer_name', ''),
                                            product_code=product.get('product_code', ''),
                                            product_name=product.get('product_name', ''),
                                            category=product.get('category', 'UNKNOWN'),
                                            quantity=float(product.get('quantity', 1)),
                                            unit_price=float(product.get('unit_price', 0)),
                                            currency=order.get('currency', 'USD'),
                                            sales_date=order_date,
                                            payment_status=payment_status,
                                            sales_rep=order.get('sales_rep', 'Unknown')
                                        )
                        except Exception as order_error:
                            continue
                            
        except Exception as e:
            print(f"주문 데이터 연동 오류: {str(e)}")
    
    def _import_from_cash_flow(self):
        """현금흐름 데이터에서 실제 수입 매출 데이터 생성"""
        try:
            import os
            cash_flow_file = os.path.join(self.data_dir, "cash_transactions.csv")
            
            if os.path.exists(cash_flow_file):
                cash_df = pd.read_csv(cash_flow_file, encoding='utf-8')
                
                # 수입(income) 거래만 매출로 인식 - 컬럼명 확인 후 처리
                if 'transaction_type' in cash_df.columns:
                    income_transactions = cash_df[cash_df['transaction_type'] == 'income']
                elif 'type' in cash_df.columns:
                    income_transactions = cash_df[cash_df['type'] == 'income']
                else:
                    # amount가 양수인 거래를 수입으로 간주
                    income_transactions = cash_df[cash_df['amount'] > 0]
                
                for _, transaction in income_transactions.iterrows():
                    try:
                        trans_date = transaction.get('date', datetime.now().strftime('%Y-%m-%d'))
                        if isinstance(trans_date, str):
                            trans_date_obj = datetime.strptime(trans_date, '%Y-%m-%d')
                            year_month = trans_date_obj.strftime('%Y-%m')
                            
                            # 매출로 인식되는 수입 거래
                            if 'sales' in str(transaction.get('description', '')).lower() or \
                               'revenue' in str(transaction.get('description', '')).lower():
                                
                                amount_value = transaction.get('amount', 0)
                                amount = float(amount_value) if amount_value not in [None, '', 'None'] else 0.0
                                currency = transaction.get('currency', 'VND')
                                
                                self._add_sales_from_source(
                                    source_type='cash_flow',
                                    source_id=transaction.get('transaction_id', ''),
                                    year_month=year_month,
                                    customer_id=transaction.get('reference_id', 'CASH_CUSTOMER'),
                                    customer_name=transaction.get('description', 'Cash Customer'),
                                    product_code='CASH_SALE',
                                    product_name=transaction.get('description', 'Cash Sale'),
                                    category='SERVICE',
                                    quantity=1,
                                    unit_price=amount,
                                    currency=currency,
                                    sales_date=trans_date,
                                    payment_status='paid',
                                    sales_rep='Cash Team'
                                )
                    except Exception as cash_error:
                        continue
                        
        except Exception as e:
            print(f"현금흐름 데이터 연동 오류: {str(e)}")
    
    def _add_sales_from_source(self, source_type, source_id, year_month, customer_id, 
                              customer_name, product_code, product_name, category, 
                              quantity, unit_price, currency, sales_date, payment_status, sales_rep):
        """다양한 소스에서 매출 데이터 추가 (중복 방지)"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            # 중복 체크: 같은 소스 ID와 제품 코드 조합이 이미 있는지 확인
            duplicate_check = df[
                (df['quotation_id'] == source_id) & 
                (df['product_code'] == product_code)
            ]
            
            if len(duplicate_check) > 0:
                return  # 이미 존재하는 데이터
            
            # 환율 변환
            if currency == 'USD':
                amount_usd = quantity * unit_price
                amount_vnd = amount_usd * 24500
            elif currency == 'VND':
                amount_vnd = quantity * unit_price
                amount_usd = amount_vnd / 24500
            else:
                amount_usd = quantity * unit_price
                amount_vnd = amount_usd * 24500
            
            # 기본 이익률 설정
            profit_margins = {
                'SERVICE': 0.7, 'HR': 0.3, 'HRC': 0.35, 'MB': 0.2, 'SPARE': 0.25
            }
            profit_margin = profit_margins.get(category, 0.25)
            cost_amount = amount_usd * (1 - profit_margin)
            
            sales_id = f"S{source_type[:2].upper()}{year_month.replace('-', '')}{len(df)+1:03d}"
            
            new_record = {
                'sales_id': sales_id,
                'year_month': year_month,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'product_code': product_code,
                'product_name': product_name,
                'category': category,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_amount': amount_usd,
                'currency': currency,
                'amount_vnd': amount_vnd,
                'amount_usd': amount_usd,
                'sales_date': sales_date,
                'quotation_id': source_id if source_type == 'quotation' else '',
                'order_id': source_id if source_type == 'order' else '',
                'payment_status': payment_status,
                'sales_rep': sales_rep,
                'profit_margin': profit_margin,
                'cost_amount': cost_amount,
                'created_date': datetime.now().strftime("%Y-%m-%d"),
                'updated_date': datetime.now().strftime("%Y-%m-%d")
            }
            
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            df.to_csv(self.monthly_sales_file, index=False, encoding='utf-8')
            
        except Exception as e:
            print(f"매출 데이터 추가 오류: {str(e)}")
    
    def _create_sample_data(self):
        """더미 데이터 생성 비활성화 - 실제 데이터만 사용"""
        # 더미 데이터 생성을 완전히 비활성화
        # 실제 ERP 데이터(견적서, 주문, 현금흐름)만 사용
        pass
    
    def get_monthly_sales_summary(self, year_month=None):
        """월별 매출 요약 조회"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            if len(df) == 0:
                return []
            
            if year_month:
                df = df[df['year_month'] == year_month]
            
            # 월별 그룹화
            summary = df.groupby('year_month').agg({
                'total_amount': 'sum',
                'amount_vnd': 'sum',
                'amount_usd': 'sum',
                'quantity': 'sum',
                'sales_id': 'count',
                'profit_margin': 'mean',
                'cost_amount': 'sum'
            }).reset_index()
            
            # 컬럼명 변경
            summary = summary.rename(columns={
                'total_amount': 'total_sales_usd',
                'sales_id': 'transaction_count',
                'profit_margin': 'avg_profit_margin',
                'cost_amount': 'total_cost_usd'
            })
            
            return summary.to_dict('records')
            
        except Exception as e:
            print(f"월별 매출 요약 조회 오류: {str(e)}")
            return []
    
    def get_customer_sales_analysis(self, year_month=None):
        """고객별 매출 분석"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            if len(df) == 0:
                return []
            
            if year_month:
                df = df[df['year_month'] == year_month]
            
            # 고객별 그룹화
            customer_analysis = df.groupby(['customer_id', 'customer_name']).agg({
                'amount_usd': 'sum',
                'amount_vnd': 'sum',
                'quantity': 'sum',
                'sales_id': 'count',
                'profit_margin': 'mean'
            }).reset_index()
            
            # 매출 비중 계산
            total_sales = customer_analysis['amount_usd'].sum()
            customer_analysis['sales_percentage'] = (customer_analysis['amount_usd'] / total_sales * 100).round(2)
            
            # 매출 순으로 정렬
            customer_analysis = customer_analysis.sort_values('amount_usd', ascending=False)
            
            return customer_analysis.to_dict('records')
            
        except Exception as e:
            print(f"고객별 매출 분석 오류: {str(e)}")
            return []
    
    def get_product_sales_analysis(self, year_month=None):
        """제품별 매출 분석"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            if len(df) == 0:
                return []
            
            if year_month:
                df = df[df['year_month'] == year_month]
            
            # 제품별 그룹화
            product_analysis = df.groupby(['category', 'product_code', 'product_name']).agg({
                'amount_usd': 'sum',
                'amount_vnd': 'sum',
                'quantity': 'sum',
                'sales_id': 'count',
                'profit_margin': 'mean',
                'unit_price': 'mean'
            }).reset_index()
            
            # 매출 비중 계산
            total_sales = product_analysis['amount_usd'].sum()
            product_analysis['sales_percentage'] = (product_analysis['amount_usd'] / total_sales * 100).round(2)
            
            # 매출 순으로 정렬
            product_analysis = product_analysis.sort_values('amount_usd', ascending=False)
            
            return product_analysis.to_dict('records')
            
        except Exception as e:
            print(f"제품별 매출 분석 오류: {str(e)}")
            return []
    
    def get_sales_targets(self, year_month=None):
        """매출 목표 조회"""
        try:
            df = pd.read_csv(self.sales_targets_file, encoding='utf-8')
            
            if len(df) == 0:
                return []
            
            if year_month:
                df = df[df['year_month'] == year_month]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"매출 목표 조회 오류: {str(e)}")
            return []
    
    def add_sales_target(self, year_month, target_type, target_category, target_amount_vnd, 
                        target_amount_usd, currency, target_quantity, responsible_person, description):
        """매출 목표 추가"""
        try:
            df = pd.read_csv(self.sales_targets_file, encoding='utf-8')
            
            target_id = f"T{year_month.replace('-', '')}{len(df)+1:03d}"
            
            new_target = {
                'target_id': target_id,
                'year_month': year_month,
                'target_type': target_type,
                'target_category': target_category,
                'target_amount_vnd': target_amount_vnd,
                'target_amount_usd': target_amount_usd,
                'currency': currency,
                'target_quantity': target_quantity,
                'responsible_person': responsible_person,
                'description': description,
                'created_date': datetime.now().strftime("%Y-%m-%d"),
                'updated_date': datetime.now().strftime("%Y-%m-%d")
            }
            
            df = pd.concat([df, pd.DataFrame([new_target])], ignore_index=True)
            df.to_csv(self.sales_targets_file, index=False, encoding='utf-8')
            
            return target_id
            
        except Exception as e:
            print(f"매출 목표 추가 오류: {str(e)}")
            return None
    
    def get_target_vs_actual(self, year_month=None):
        """목표 대비 실적 분석"""
        try:
            # 매출 목표 조회
            targets = self.get_sales_targets(year_month)
            
            # 실제 매출 조회
            actual_sales = self.get_monthly_sales_summary(year_month)
            
            # 목표 vs 실적 매칭
            results = []
            
            for target in targets:
                target_month = target['year_month']
                
                # 해당 월 실제 매출 찾기
                actual = next((s for s in actual_sales if s['year_month'] == target_month), None)
                
                if actual:
                    achievement_rate = (actual['total_sales_usd'] / target['target_amount_usd'] * 100) if target['target_amount_usd'] > 0 else 0
                    variance_usd = actual['total_sales_usd'] - target['target_amount_usd']
                    variance_vnd = actual['amount_vnd'] - target['target_amount_vnd']
                else:
                    achievement_rate = 0
                    variance_usd = -target['target_amount_usd']
                    variance_vnd = -target['target_amount_vnd']
                    actual = {
                        'total_sales_usd': 0,
                        'amount_vnd': 0,
                        'transaction_count': 0,
                        'quantity': 0
                    }
                
                results.append({
                    'year_month': target_month,
                    'target_amount_usd': target['target_amount_usd'],
                    'target_amount_vnd': target['target_amount_vnd'],
                    'actual_amount_usd': actual['total_sales_usd'],
                    'actual_amount_vnd': actual['amount_vnd'],
                    'achievement_rate': round(achievement_rate, 2),
                    'variance_usd': variance_usd,
                    'variance_vnd': variance_vnd,
                    'target_quantity': target.get('target_quantity', 0),
                    'actual_quantity': actual.get('quantity', 0),
                    'responsible_person': target['responsible_person']
                })
            
            return results
            
        except Exception as e:
            print(f"목표 대비 실적 분석 오류: {str(e)}")
            return []
    
    def get_sales_trend(self, months=6):
        """매출 트렌드 분석"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            if len(df) == 0:
                return []
            
            # 최근 N개월 데이터
            df['year_month'] = pd.to_datetime(df['year_month'], format='%Y-%m', errors='coerce')
            df = df.sort_values('year_month').tail(months * 30)  # 대략적 필터링
            
            # 월별 트렌드 계산
            trend = df.groupby(df['year_month'].dt.strftime('%Y-%m')).agg({
                'amount_usd': 'sum',
                'amount_vnd': 'sum',
                'quantity': 'sum',
                'sales_id': 'count',
                'profit_margin': 'mean'
            }).reset_index()
            
            return trend.to_dict(orient='records')
            
        except Exception as e:
            print(f"매출 트렌드 분석 오류: {str(e)}")
            return []
    
    def add_sales_record(self, customer_id, customer_name, product_code, product_name, 
                        category, quantity, unit_price, currency, quotation_id, order_id, 
                        sales_rep, payment_status="pending"):
        """매출 기록 추가"""
        try:
            df = pd.read_csv(self.monthly_sales_file, encoding='utf-8')
            
            # 환율 변환
            if currency == 'USD':
                amount_usd = quantity * unit_price
                amount_vnd = amount_usd * 24500
            elif currency == 'VND':
                amount_vnd = quantity * unit_price
                amount_usd = amount_vnd / 24500
            else:
                # 기타 통화는 USD로 변환 후 처리
                amount_usd = quantity * unit_price
                amount_vnd = amount_usd * 24500
            
            # 기본 이익률 설정 (카테고리별)
            profit_margins = {
                'SERVICE': 0.7,
                'HR': 0.3,
                'HRC': 0.35,
                'MB': 0.2,
                'SPARE': 0.25
            }
            profit_margin = profit_margins.get(category, 0.25)
            cost_amount = amount_usd * (1 - profit_margin)
            
            sales_date = datetime.now()
            year_month = sales_date.strftime("%Y-%m")
            sales_id = f"S{year_month.replace('-', '')}{len(df)+1:03d}"
            
            new_record = {
                'sales_id': sales_id,
                'year_month': year_month,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'product_code': product_code,
                'product_name': product_name,
                'category': category,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_amount': amount_usd,
                'currency': currency,
                'amount_vnd': amount_vnd,
                'amount_usd': amount_usd,
                'sales_date': sales_date.strftime("%Y-%m-%d"),
                'quotation_id': quotation_id,
                'order_id': order_id,
                'payment_status': payment_status,
                'sales_rep': sales_rep,
                'profit_margin': profit_margin,
                'cost_amount': cost_amount,
                'created_date': sales_date.strftime("%Y-%m-%d"),
                'updated_date': sales_date.strftime("%Y-%m-%d")
            }
            
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            df.to_csv(self.monthly_sales_file, index=False, encoding='utf-8')
            
            return sales_id
            
        except Exception as e:
            print(f"매출 기록 추가 오류: {str(e)}")
            return None