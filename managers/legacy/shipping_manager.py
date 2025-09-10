import pandas as pd
import os
from datetime import datetime
import json

class ShippingManager:
    def __init__(self):
        self.data_file = 'data/shipping.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'shipping_id', 'shipping_number', 'quotation_id', 'customer_id',
                'customer_name', 'shipping_address', 'shipping_method',
                'tracking_number', 'estimated_delivery', 'actual_delivery',
                'shipping_cost', 'currency', 'products_json', 'status',
                'created_by', 'shipped_date', 'delivered_date',
                'notes', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_shipping_number(self):
        """배송 번호를 생성합니다."""
        try:
            today = datetime.now()
            prefix = f"SH{today.strftime('%Y%m')}"
            
            df = self.get_all_shipments()
            existing_numbers = df[df['shipping_number'].str.startswith(prefix)]['shipping_number'].tolist()
            
            numbers = []
            for sh_num in existing_numbers:
                try:
                    suffix = sh_num.replace(prefix, '')
                    if suffix.isdigit():
                        numbers.append(int(suffix))
                except:
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
            return f"{prefix}{next_num:03d}"
        except Exception as e:
            print(f"배송 번호 생성 중 오류: {e}")
            return f"SH{datetime.now().strftime('%Y%m')}001"
    
    def create_shipment(self, shipping_data):
        """새 배송을 생성합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 배송 번호가 없으면 생성
            if 'shipping_number' not in shipping_data or not shipping_data['shipping_number']:
                shipping_data['shipping_number'] = self.generate_shipping_number()
            
            # 배송 ID 생성
            if 'shipping_id' not in shipping_data or not shipping_data['shipping_id']:
                shipping_data['shipping_id'] = f"SHID{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in shipping_data:
                shipping_data['products_json'] = json.dumps(shipping_data['products'], ensure_ascii=False)
                del shipping_data['products']
            
            # 기본값 설정
            shipping_data['status'] = shipping_data.get('status', '준비중')
            shipping_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            shipping_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([shipping_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"배송 생성 중 오류: {e}")
            return False
    
    def get_all_shipments(self):
        """모든 배송 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # products_json을 products로 변환
            if 'products_json' in df.columns:
                df['products'] = df['products_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            return df
        except Exception as e:
            print(f"배송 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_shipment_by_id(self, shipping_id):
        """특정 배송 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            shipment = df[df['shipping_id'] == shipping_id]
            if not shipment.empty:
                result = shipment.iloc[0].to_dict()
                
                # products_json을 products로 변환
                if 'products_json' in result and result['products_json']:
                    try:
                        result['products'] = json.loads(result['products_json'])
                    except:
                        result['products'] = []
                
                return result
            return None
        except Exception as e:
            print(f"배송 조회 중 오류: {e}")
            return None
    
    def update_shipment(self, shipping_id, shipping_data):
        """배송 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if shipping_id not in df['shipping_id'].values:
                return False
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in shipping_data:
                shipping_data['products_json'] = json.dumps(shipping_data['products'], ensure_ascii=False)
                del shipping_data['products']
            
            shipping_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in shipping_data.items():
                if key in df.columns:
                    df.loc[df['shipping_id'] == shipping_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"배송 업데이트 중 오류: {e}")
            return False
    
    def mark_as_shipped(self, shipping_id, tracking_number=None, shipped_by=None):
        """배송 출발로 표시합니다."""
        try:
            update_data = {
                'status': '배송중',
                'shipped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if tracking_number:
                update_data['tracking_number'] = tracking_number
            
            return self.update_shipment(shipping_id, update_data)
        except Exception as e:
            print(f"배송 출발 처리 중 오류: {e}")
            return False
    
    def mark_as_delivered(self, shipping_id, delivered_by=None, notes=None):
        """배송 완료로 표시합니다."""
        try:
            update_data = {
                'status': '배송완료',
                'delivered_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'actual_delivery': datetime.now().strftime('%Y-%m-%d')
            }
            
            if notes:
                update_data['notes'] = notes
            
            return self.update_shipment(shipping_id, update_data)
        except Exception as e:
            print(f"배송 완료 처리 중 오류: {e}")
            return False
    
    def get_shipments_by_status(self, status):
        """상태별 배송을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['status'] == status]
        except Exception as e:
            print(f"상태별 배송 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_pending_shipments(self):
        """대기 중인 배송을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['status'].isin(['준비중', '포장중'])]
        except Exception as e:
            print(f"대기 배송 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_shipping_statistics(self):
        """배송 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 비용을 숫자로 변환
            df['shipping_cost'] = pd.to_numeric(df['shipping_cost'], errors='coerce').fillna(0)
            
            stats = {
                'total_shipments': len(df),
                'pending_shipments': len(df[df['status'] == '준비중']),
                'shipped_shipments': len(df[df['status'] == '배송중']),
                'delivered_shipments': len(df[df['status'] == '배송완료']),
                'total_shipping_cost': df['shipping_cost'].sum(),
                'average_shipping_cost': df['shipping_cost'].mean(),
                'status_distribution': df['status'].value_counts().to_dict(),
                'method_distribution': df['shipping_method'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"배송 통계 조회 중 오류: {e}")
            return {}
    
    def create_shipment_from_quotation(self, quotation_data, shipping_address, shipping_method):
        """견적서에서 배송을 생성합니다."""
        try:
            shipping_data = {
                'quotation_id': quotation_data.get('quotation_id'),
                'customer_id': quotation_data.get('customer_id'),
                'customer_name': quotation_data.get('customer_name'),
                'shipping_address': shipping_address,
                'shipping_method': shipping_method,
                'products': quotation_data.get('products', []),
                'currency': quotation_data.get('currency', 'USD'),
                'status': '준비중'
            }
            
            if self.create_shipment(shipping_data):
                return self.get_all_shipments().iloc[-1]['shipping_id']
            
            return None
        except Exception as e:
            print(f"견적서에서 배송 생성 중 오류: {e}")
            return None
    
    def get_delivery_performance(self):
        """배송 성과 분석을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 날짜 컬럼을 datetime으로 변환
            df['estimated_delivery'] = pd.to_datetime(df['estimated_delivery'], errors='coerce')
            df['actual_delivery'] = pd.to_datetime(df['actual_delivery'], errors='coerce')
            
            # 배송완료된 건만 필터
            completed_df = df[df['status'] == '배송완료'].copy()
            
            if completed_df.empty:
                return {
                    'on_time_deliveries': 0,
                    'late_deliveries': 0,
                    'on_time_rate': 0,
                    'average_delay_days': 0
                }
            
            # 지연 계산
            completed_df['delay_days'] = (completed_df['actual_delivery'] - completed_df['estimated_delivery']).dt.days
            
            on_time = len(completed_df[completed_df['delay_days'] <= 0])
            late = len(completed_df[completed_df['delay_days'] > 0])
            
            performance = {
                'on_time_deliveries': on_time,
                'late_deliveries': late,
                'on_time_rate': (on_time / len(completed_df)) * 100 if len(completed_df) > 0 else 0,
                'average_delay_days': completed_df[completed_df['delay_days'] > 0]['delay_days'].mean() if late > 0 else 0
            }
            
            return performance
        except Exception as e:
            print(f"배송 성과 분석 중 오류: {e}")
            return {}
