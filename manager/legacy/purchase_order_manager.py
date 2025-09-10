import pandas as pd
import os
from datetime import datetime
import json

class PurchaseOrderManager:
    def __init__(self):
        self.data_file = 'data/purchase_orders.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'po_id', 'po_number', 'quotation_id', 'supplier_id', 'supplier_name',
                'po_date', 'delivery_date', 'total_amount', 'currency',
                'products_json', 'terms_conditions', 'status', 'created_by',
                'approved_by', 'approved_date', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_po_number(self):
        """발주서 번호를 생성합니다."""
        try:
            today = datetime.now()
            prefix = f"PO{today.strftime('%Y%m')}"
            
            df = self.get_all_purchase_orders()
            existing_numbers = df[df['po_number'].str.startswith(prefix)]['po_number'].tolist()
            
            numbers = []
            for po_num in existing_numbers:
                try:
                    suffix = po_num.replace(prefix, '')
                    if suffix.isdigit():
                        numbers.append(int(suffix))
                except:
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
            return f"{prefix}{next_num:03d}"
        except Exception as e:
            print(f"발주서 번호 생성 중 오류: {e}")
            return f"PO{datetime.now().strftime('%Y%m')}001"
    
    def create_purchase_order(self, po_data):
        """새 발주서를 생성합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 발주서 번호가 없으면 생성
            if 'po_number' not in po_data or not po_data['po_number']:
                po_data['po_number'] = self.generate_po_number()
            
            # 발주서 ID 생성
            if 'po_id' not in po_data or not po_data['po_id']:
                po_data['po_id'] = f"POID{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in po_data:
                po_data['products_json'] = json.dumps(po_data['products'], ensure_ascii=False)
                del po_data['products']
            
            # 기본값 설정
            po_data['status'] = po_data.get('status', '대기')
            po_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            po_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([po_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"발주서 생성 중 오류: {e}")
            return False
    
    def get_all_purchase_orders(self):
        """모든 발주서 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # products_json을 products로 변환
            if 'products_json' in df.columns:
                df['products'] = df['products_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            return df
        except Exception as e:
            print(f"발주서 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_order_by_id(self, po_id):
        """특정 발주서 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            po = df[df['po_id'] == po_id]
            if not po.empty:
                result = po.iloc[0].to_dict()
                
                # products_json을 products로 변환
                if 'products_json' in result and result['products_json']:
                    try:
                        result['products'] = json.loads(result['products_json'])
                    except:
                        result['products'] = []
                
                return result
            return None
        except Exception as e:
            print(f"발주서 조회 중 오류: {e}")
            return None
    
    def update_purchase_order(self, po_id, po_data):
        """발주서 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if po_id not in df['po_id'].values:
                return False
            
            # 제품 목록을 JSON 문자열로 변환
            if 'products' in po_data:
                po_data['products_json'] = json.dumps(po_data['products'], ensure_ascii=False)
                del po_data['products']
            
            po_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in po_data.items():
                if key in df.columns:
                    df.loc[df['po_id'] == po_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"발주서 업데이트 중 오류: {e}")
            return False
    
    def approve_purchase_order(self, po_id, approved_by):
        """발주서를 승인합니다."""
        try:
            return self.update_purchase_order(po_id, {
                'status': '승인됨',
                'approved_by': approved_by,
                'approved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            print(f"발주서 승인 중 오류: {e}")
            return False
    
    def get_purchase_orders_by_status(self, status):
        """상태별 발주서를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['status'] == status]
        except Exception as e:
            print(f"상태별 발주서 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_order_statistics(self):
        """발주서 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 금액을 숫자로 변환
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
            
            stats = {
                'total_pos': len(df),
                'pending_pos': len(df[df['status'] == '대기']),
                'approved_pos': len(df[df['status'] == '승인됨']),
                'completed_pos': len(df[df['status'] == '완료']),
                'total_amount': df['total_amount'].sum(),
                'average_amount': df['total_amount'].mean(),
                'status_distribution': df['status'].value_counts().to_dict(),
                'supplier_distribution': df['supplier_name'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"발주서 통계 조회 중 오류: {e}")
            return {}
