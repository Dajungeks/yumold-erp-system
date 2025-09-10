import pandas as pd
import os
from datetime import datetime
import json

class InventoryManager:
    def __init__(self):
        self.data_file = 'data/inventory.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'inventory_id', 'product_id', 'product_code', 'product_name',
                'current_stock', 'minimum_stock', 'maximum_stock', 'unit',
                'warehouse_location', 'supplier_id', 'supplier_name',
                'last_purchase_date', 'last_purchase_price', 'average_cost',
                'total_value', 'status', 'notes', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def add_inventory_item(self, inventory_data):
        """새 재고 아이템을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 중복 확인 (제품 ID로 확인)
            if inventory_data['product_id'] in df['product_id'].values:
                return False
            
            # 재고 ID 생성
            if 'inventory_id' not in inventory_data or not inventory_data['inventory_id']:
                inventory_data['inventory_id'] = f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기본값 설정
            inventory_data['status'] = inventory_data.get('status', '활성')
            inventory_data['current_stock'] = inventory_data.get('current_stock', 0)
            inventory_data['minimum_stock'] = inventory_data.get('minimum_stock', 0)
            inventory_data['maximum_stock'] = inventory_data.get('maximum_stock', 1000)
            inventory_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            inventory_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 총 가치 계산
            if 'average_cost' in inventory_data and 'current_stock' in inventory_data:
                try:
                    cost = float(inventory_data['average_cost'])
                    stock = float(inventory_data['current_stock'])
                    inventory_data['total_value'] = cost * stock
                except (ValueError, TypeError):
                    inventory_data['total_value'] = 0
            
            df = pd.concat([df, pd.DataFrame([inventory_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"재고 아이템 추가 중 오류: {e}")
            return False
    
    def get_all_inventory(self):
        """모든 재고 정보를 가져옵니다."""
        try:
            return pd.read_csv(self.data_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"재고 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_inventory_by_product_id(self, product_id):
        """특정 제품의 재고 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            inventory = df[df['product_id'] == product_id]
            if len(inventory) > 0:
                return inventory.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"재고 조회 중 오류: {e}")
            return None
    
    def update_stock(self, product_id, quantity_change, transaction_type='adjustment', notes=None):
        """재고 수량을 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if product_id not in df['product_id'].values:
                return False
            
            # 현재 재고 가져오기
            current_stock = df.loc[df['product_id'] == product_id, 'current_stock'].iloc[0]
            new_stock = max(0, current_stock + quantity_change)
            
            # 재고 업데이트
            df.loc[df['product_id'] == product_id, 'current_stock'] = new_stock
            df.loc[df['product_id'] == product_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 총 가치 재계산
            average_cost = df.loc[df['product_id'] == product_id, 'average_cost'].iloc[0]
            if pd.notna(average_cost):
                df.loc[df['product_id'] == product_id, 'total_value'] = new_stock * float(average_cost)
            
            # 노트 업데이트
            if notes:
                df.loc[df['product_id'] == product_id, 'notes'] = notes
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            # 재고 이력 기록
            self.record_stock_transaction(product_id, quantity_change, new_stock, transaction_type, notes)
            
            return True
        except Exception as e:
            print(f"재고 업데이트 중 오류: {e}")
            return False
    
    def record_stock_transaction(self, product_id, quantity_change, new_stock, transaction_type, notes=None):
        """재고 거래 이력을 기록합니다."""
        try:
            # 재고 거래 이력 파일
            history_file = 'data/inventory_history.csv'
            
            # 파일이 없으면 생성
            if not os.path.exists(history_file):
                history_df = pd.DataFrame(columns=[
                    'transaction_id', 'product_id', 'transaction_type', 'quantity_change',
                    'stock_before', 'stock_after', 'transaction_date', 'notes'
                ])
                history_df.to_csv(history_file, index=False, encoding='utf-8-sig')
            
            # 새 거래 기록 추가
            history_df = pd.read_csv(history_file, encoding='utf-8-sig')
            
            transaction_data = {
                'transaction_id': f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'product_id': product_id,
                'transaction_type': transaction_type,
                'quantity_change': quantity_change,
                'stock_before': new_stock - quantity_change,
                'stock_after': new_stock,
                'transaction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'notes': notes or ''
            }
            
            history_df = pd.concat([history_df, pd.DataFrame([transaction_data])], ignore_index=True)
            history_df.to_csv(history_file, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"재고 이력 기록 중 오류: {e}")
    
    def get_low_stock_items(self):
        """재고 부족 아이템을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 숫자 컬럼을 float로 변환
            df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce').fillna(0)
            df['minimum_stock'] = pd.to_numeric(df['minimum_stock'], errors='coerce').fillna(0)
            
            # 현재 재고가 최소 재고보다 적은 아이템들
            low_stock = df[df['current_stock'] <= df['minimum_stock']]
            
            return low_stock
        except Exception as e:
            print(f"재고 부족 아이템 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_inventory_value_summary(self):
        """재고 가치 요약을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 숫자 컬럼들을 float로 변환
            df['total_value'] = pd.to_numeric(df['total_value'], errors='coerce').fillna(0)
            df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce').fillna(0)
            
            summary = {
                'total_items': len(df),
                'total_value': df['total_value'].sum(),
                'total_quantity': df['current_stock'].sum(),
                'low_stock_items': len(self.get_low_stock_items()),
                'out_of_stock_items': len(df[df['current_stock'] == 0]),
                'active_items': len(df[df['status'] == '활성'])
            }
            
            return summary
        except Exception as e:
            print(f"재고 가치 요약 조회 중 오류: {e}")
            return {}
    
    def receive_purchase_order(self, po_data, received_by):
        """발주서 입고 처리를 합니다."""
        try:
            results = {'success': [], 'errors': []}
            
            products = po_data.get('products', [])
            
            for product in products:
                product_id = product.get('product_id')
                quantity = product.get('quantity', 0)
                unit_cost = product.get('unit_price', 0)
                
                if not product_id:
                    results['errors'].append(f"제품 ID가 없습니다: {product}")
                    continue
                
                # 재고 업데이트
                if self.update_stock(
                    product_id, 
                    quantity, 
                    'purchase_order',
                    f"발주서 {po_data.get('po_number')} 입고"
                ):
                    # 평균 단가 업데이트
                    self.update_average_cost(product_id, unit_cost, quantity)
                    results['success'].append(f"제품 {product_id} 입고 완료")
                else:
                    results['errors'].append(f"제품 {product_id} 입고 실패")
            
            return results
        except Exception as e:
            print(f"발주서 입고 처리 중 오류: {e}")
            return {'success': [], 'errors': [str(e)]}
    
    def update_average_cost(self, product_id, new_cost, new_quantity):
        """평균 단가를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if product_id not in df['product_id'].values:
                return False
            
            # 현재 정보 가져오기
            current_stock = df.loc[df['product_id'] == product_id, 'current_stock'].iloc[0]
            current_avg_cost = df.loc[df['product_id'] == product_id, 'average_cost'].iloc[0]
            
            # 기존 재고량 (새로 들어온 것 제외)
            old_stock = current_stock - new_quantity
            
            if pd.isna(current_avg_cost):
                current_avg_cost = 0
            
            # 가중 평균 계산
            if old_stock > 0:
                total_cost = (old_stock * current_avg_cost) + (new_quantity * new_cost)
                new_avg_cost = total_cost / current_stock
            else:
                new_avg_cost = new_cost
            
            # 업데이트
            df.loc[df['product_id'] == product_id, 'average_cost'] = new_avg_cost
            df.loc[df['product_id'] == product_id, 'total_value'] = current_stock * new_avg_cost
            df.loc[df['product_id'] == product_id, 'last_purchase_price'] = new_cost
            df.loc[df['product_id'] == product_id, 'last_purchase_date'] = datetime.now().strftime('%Y-%m-%d')
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"평균 단가 업데이트 중 오류: {e}")
            return False
    
    def ship_inventory(self, shipping_data):
        """재고 출고 처리를 합니다."""
        try:
            results = {'success': [], 'errors': []}
            
            products = shipping_data.get('products', [])
            shipping_id = shipping_data.get('shipping_id', 'UNKNOWN')
            
            for product in products:
                product_id = product.get('product_id')
                quantity = product.get('quantity', 0)
                
                if not product_id:
                    results['errors'].append(f"제품 ID가 없습니다: {product}")
                    continue
                
                # 재고 확인
                current_inventory = self.get_inventory_by_product_id(product_id)
                if not current_inventory:
                    results['errors'].append(f"제품 {product_id}의 재고 정보가 없습니다")
                    continue
                
                if current_inventory['current_stock'] < quantity:
                    results['errors'].append(f"제품 {product_id}의 재고가 부족합니다 (현재: {current_inventory['current_stock']}, 요청: {quantity})")
                    continue
                
                # 재고 차감
                if self.update_stock(
                    product_id, 
                    -quantity, 
                    'shipment',
                    f"배송 {shipping_id} 출고"
                ):
                    results['success'].append(f"제품 {product_id} 출고 완료")
                else:
                    results['errors'].append(f"제품 {product_id} 출고 실패")
            
            return results
        except Exception as e:
            print(f"재고 출고 처리 중 오류: {e}")
            return {'success': [], 'errors': [str(e)]}
