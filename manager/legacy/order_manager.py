"""
주문 관리 시스템
견적서가 승인된 후 주문으로 전환하여 관리하는 시스템
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import json

class OrderManager:
    def __init__(self):
        self.data_dir = "data"
        self.orders_file = os.path.join(self.data_dir, "orders.csv")
        self.order_items_file = os.path.join(self.data_dir, "order_items.csv")
        self.order_status_history_file = os.path.join(self.data_dir, "order_status_history.csv")
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 주문 기본 정보 파일
        if not os.path.exists(self.orders_file):
            df = pd.DataFrame(columns=[
                'order_id', 'quotation_id', 'customer_id', 'customer_name',
                'order_date', 'requested_delivery_date', 'confirmed_delivery_date',
                'total_amount', 'currency', 'order_status', 'payment_status',
                'payment_terms', 'special_instructions', 'created_by',
                'created_date', 'last_updated', 'notes'
            ])
            df.to_csv(self.orders_file, index=False, encoding='utf-8-sig')
        
        # 주문 상품 상세 정보 파일
        if not os.path.exists(self.order_items_file):
            df = pd.DataFrame(columns=[
                'item_id', 'order_id', 'product_code', 'product_name',
                'quantity', 'unit_price', 'total_price', 'currency',
                'specifications', 'delivery_notes', 'production_status'
            ])
            df.to_csv(self.order_items_file, index=False, encoding='utf-8-sig')
        
        # 주문 상태 변경 이력 파일
        if not os.path.exists(self.order_status_history_file):
            df = pd.DataFrame(columns=[
                'history_id', 'order_id', 'previous_status', 'new_status',
                'changed_by', 'changed_date', 'notes', 'reason'
            ])
            df.to_csv(self.order_status_history_file, index=False, encoding='utf-8-sig')
    
    def generate_order_id(self):
        """주문 ID를 생성합니다. (ORD + YYYYMMDD + 순서번호)"""
        today = datetime.now().strftime("%Y%m%d")
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            today_orders = [oid for oid in df['order_id'].astype(str) if oid.startswith(f"ORD{today}")]
            sequence = len(today_orders) + 1
        except:
            sequence = 1
        
        return f"ORD{today}{sequence:03d}"
    
    def create_order_from_quotation(self, quotation_data, created_by, order_details=None):
        """견적서에서 주문을 생성합니다."""
        try:
            order_id = self.generate_order_id()
            
            # 기본 주문 정보
            order_data = {
                'order_id': order_id,
                'quotation_id': quotation_data.get('quotation_id'),
                'customer_id': quotation_data.get('customer_id'),
                'customer_name': quotation_data.get('customer_name'),
                'order_date': datetime.now().strftime('%Y-%m-%d'),
                'requested_delivery_date': order_details.get('requested_delivery_date') if order_details else None,
                'confirmed_delivery_date': None,
                'total_amount': quotation_data.get('total_amount'),
                'currency': quotation_data.get('currency', 'VND'),
                'order_status': 'pending',  # pending, confirmed, in_production, shipped, delivered, cancelled
                'payment_status': 'pending',  # pending, partial, paid, overdue
                'payment_terms': order_details.get('payment_terms', '30일 선불') if order_details else '30일 선불',
                'special_instructions': order_details.get('special_instructions', '') if order_details else '',
                'created_by': created_by,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'notes': ''
            }
            
            # 주문 정보 저장
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            new_df = pd.concat([df, pd.DataFrame([order_data])], ignore_index=True)
            new_df.to_csv(self.orders_file, index=False, encoding='utf-8-sig')
            
            # 견적서 상품들을 주문 상품으로 복사
            quotation_products = quotation_data.get('products', [])
            if isinstance(quotation_products, str):
                quotation_products = json.loads(quotation_products)
            
            order_items = []
            for i, product in enumerate(quotation_products):
                item_data = {
                    'item_id': f"{order_id}_ITEM_{i+1:03d}",
                    'order_id': order_id,
                    'product_code': product.get('product_code'),
                    'product_name': product.get('product_name'),
                    'quantity': product.get('quantity'),
                    'unit_price': product.get('unit_price'),
                    'total_price': product.get('total_price'),
                    'currency': product.get('currency', 'VND'),
                    'specifications': product.get('specifications', ''),
                    'delivery_notes': '',
                    'production_status': 'not_started'
                }
                order_items.append(item_data)
            
            if order_items:
                items_df = pd.read_csv(self.order_items_file, encoding='utf-8-sig')
                new_items_df = pd.concat([items_df, pd.DataFrame(order_items)], ignore_index=True)
                new_items_df.to_csv(self.order_items_file, index=False, encoding='utf-8-sig')
            
            # 상태 변경 이력 생성
            self.add_status_history(order_id, None, 'pending', created_by, f"주문 생성 (견적서: {quotation_data.get('quotation_id')})")
            
            return order_id
            
        except Exception as e:
            print(f"주문 생성 중 오류: {e}")
            return None
    
    def get_all_orders(self):
        """모든 주문을 가져옵니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            return df.to_dict('records')
        except Exception as e:
            print(f"주문 조회 중 오류: {e}")
            return []
    
    def get_order_by_id(self, order_id):
        """특정 주문 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            order_data = df[df['order_id'] == order_id]
            if len(order_data) > 0:
                return order_data.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"주문 조회 중 오류: {e}")
            return None
    
    def get_order_items(self, order_id):
        """주문의 상품 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.order_items_file, encoding='utf-8-sig')
            items = df[df['order_id'] == order_id]
            return items.to_dict('records')
        except Exception as e:
            print(f"주문 상품 조회 중 오류: {e}")
            return []
    
    def update_order_status(self, order_id, new_status, updated_by, notes=None):
        """주문 상태를 업데이트합니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            order_index = df[df['order_id'] == order_id].index
            
            if len(order_index) > 0:
                previous_status = df.loc[order_index[0], 'order_status']
                df.loc[order_index[0], 'order_status'] = new_status
                df.loc[order_index[0], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if notes:
                    df.loc[order_index[0], 'notes'] = notes
                
                df.to_csv(self.orders_file, index=False, encoding='utf-8-sig')
                
                # 상태 변경 이력 추가
                self.add_status_history(order_id, previous_status, new_status, updated_by, notes)
                return True
            
            return False
        except Exception as e:
            print(f"주문 상태 업데이트 중 오류: {e}")
            return False
    
    def update_payment_status(self, order_id, payment_status, updated_by, notes=None):
        """결제 상태를 업데이트합니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            order_index = df[df['order_id'] == order_id].index
            
            if len(order_index) > 0:
                df.loc[order_index[0], 'payment_status'] = payment_status
                df.loc[order_index[0], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if notes:
                    current_notes = df.loc[order_index[0], 'notes'] or ''
                    df.loc[order_index[0], 'notes'] = f"{current_notes}\n[결제] {notes}".strip()
                
                df.to_csv(self.orders_file, index=False, encoding='utf-8-sig')
                return True
            
            return False
        except Exception as e:
            print(f"결제 상태 업데이트 중 오류: {e}")
            return False
    
    def add_status_history(self, order_id, previous_status, new_status, changed_by, notes=None):
        """상태 변경 이력을 추가합니다."""
        try:
            history_data = {
                'history_id': f"{order_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'order_id': order_id,
                'previous_status': previous_status,
                'new_status': new_status,
                'changed_by': changed_by,
                'changed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'notes': notes or '',
                'reason': ''
            }
            
            df = pd.read_csv(self.order_status_history_file, encoding='utf-8-sig')
            new_df = pd.concat([df, pd.DataFrame([history_data])], ignore_index=True)
            new_df.to_csv(self.order_status_history_file, index=False, encoding='utf-8-sig')
            
            return True
        except Exception as e:
            print(f"상태 이력 추가 중 오류: {e}")
            return False
    
    def get_order_history(self, order_id):
        """주문의 상태 변경 이력을 가져옵니다."""
        try:
            df = pd.read_csv(self.order_status_history_file, encoding='utf-8-sig')
            history = df[df['order_id'] == order_id].sort_values('changed_date')
            return history.to_dict('records')
        except Exception as e:
            print(f"주문 이력 조회 중 오류: {e}")
            return []
    
    def get_filtered_orders(self, status_filter=None, customer_filter=None, date_from=None, date_to=None):
        """필터링된 주문 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            
            if status_filter and status_filter != "전체":
                df = df[df['order_status'] == status_filter]
            
            if customer_filter:
                df = df[df['customer_name'].str.contains(customer_filter, case=False, na=False)]
            
            if date_from:
                df['order_date'] = pd.to_datetime(df['order_date'])
                df = df[df['order_date'] >= pd.to_datetime(date_from)]
            
            if date_to:
                df['order_date'] = pd.to_datetime(df['order_date'])
                df = df[df['order_date'] <= pd.to_datetime(date_to)]
            
            return df.to_dict('records')
        except Exception as e:
            print(f"주문 필터링 중 오류: {e}")
            return []
    
    def get_order_statistics(self):
        """주문 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return {
                    'total_orders': 0,
                    'pending_orders': 0,
                    'completed_orders': 0,
                    'total_value': 0,
                    'avg_order_value': 0,
                    'status_distribution': {},
                    'monthly_orders': {}
                }
            
            stats = {
                'total_orders': len(df),
                'pending_orders': len(df[df['order_status'].isin(['pending', 'confirmed', 'in_production'])]),
                'completed_orders': len(df[df['order_status'] == 'delivered']),
                'total_value': df['total_amount'].astype(float).sum(),
                'avg_order_value': df['total_amount'].astype(float).mean(),
                'status_distribution': df['order_status'].value_counts().to_dict(),
                'payment_distribution': df['payment_status'].value_counts().to_dict()
            }
            
            # 월별 주문 통계
            df['order_date'] = pd.to_datetime(df['order_date'])
            df['month'] = df['order_date'].dt.to_period('M')
            monthly_stats = df.groupby('month').agg({
                'order_id': 'count',
                'total_amount': 'sum'
            }).to_dict()
            
            stats['monthly_orders'] = monthly_stats
            
            return stats
        except Exception as e:
            print(f"주문 통계 조회 중 오류: {e}")
            return {}
    
    def get_delivery_schedule(self):
        """배송 일정을 가져옵니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            
            # 배송 예정 주문들 (confirmed, in_production 상태)
            delivery_orders = df[df['order_status'].isin(['confirmed', 'in_production'])].copy()
            
            if len(delivery_orders) > 0:
                delivery_orders.loc[:, 'requested_delivery_date'] = pd.to_datetime(delivery_orders['requested_delivery_date'], errors='coerce')
                delivery_orders = delivery_orders.dropna(subset=['requested_delivery_date'])
                delivery_orders = delivery_orders.sort_values('requested_delivery_date')
                
                return delivery_orders.to_dict('records')
            
            return []
        except Exception as e:
            print(f"배송 일정 조회 중 오류: {e}")
            return []
    
    def update_delivery_date(self, order_id, confirmed_delivery_date, updated_by):
        """확정 배송일을 업데이트합니다."""
        try:
            df = pd.read_csv(self.orders_file, encoding='utf-8-sig')
            order_index = df[df['order_id'] == order_id].index
            
            if len(order_index) > 0:
                df.loc[order_index[0], 'confirmed_delivery_date'] = confirmed_delivery_date
                df.loc[order_index[0], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                df.to_csv(self.orders_file, index=False, encoding='utf-8-sig')
                
                # 상태 이력 추가
                self.add_status_history(order_id, None, None, updated_by, f"배송일 확정: {confirmed_delivery_date}")
                return True
            
            return False
        except Exception as e:
            print(f"배송일 업데이트 중 오류: {e}")
            return False