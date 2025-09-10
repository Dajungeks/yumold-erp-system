import pandas as pd
import os
from datetime import datetime
from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager as MasterProductManager

class SupplyProductManager:
    """공급 제품 관리 클래스 - 협정 공급가 및 환율 변동 관리"""
    
    def __init__(self):
        self.supplier_agreements_file = 'data/supplier_agreements.csv'
        self.supply_price_history_file = 'data/supply_price_history.csv'
        self.exchange_rate_impact_file = 'data/exchange_rate_impact.csv'
        self.moq_pricing_file = 'data/moq_pricing.csv'
        self.actual_purchases_file = 'data/actual_purchases.csv'
        self.ensure_data_files()
    
    def get_master_mb_products(self):
        """MB 제품만 마스터 제품 DB에서 조회합니다"""
        try:
            master_manager = MasterProductManager()
            all_products = master_manager.get_all_products()
            
            if len(all_products) == 0:
                return pd.DataFrame()
            
            # MB 제품만 필터링
            mb_products = all_products[all_products['main_category'] == 'MB']
            return mb_products
        except Exception as e:
            print(f"마스터 MB 제품 조회 오류: {e}")
            return pd.DataFrame()
    
    def sync_with_master_mb_product(self, master_product_data, supplier_data):
        """마스터 MB 제품과 동기화하여 공급 협정을 생성합니다"""
        try:
            return self.create_supplier_agreement(
                product_id=master_product_data['product_id'],
                product_code=master_product_data['product_code'],
                product_name=master_product_data['product_name_korean'],
                supplier_id=supplier_data['supplier_id'],
                supplier_name=supplier_data['supplier_name'],
                agreement_price_usd=0.0,  # 사용자가 입력
                agreement_price_local=0.0,
                local_currency='CNY',  # MB 제품은 기본적으로 CNY
                minimum_quantity=1,
                payment_terms='30일',
                created_by='system'
            )
        except Exception as e:
            print(f"마스터 MB 제품 동기화 오류: {e}")
            return False, str(e)

    def ensure_data_files(self):
        """데이터 파일들이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        
        # 공급업체 협정 파일
        if not os.path.exists(self.supplier_agreements_file):
            df = pd.DataFrame(columns=[
                'agreement_id', 'product_id', 'product_code', 'product_name',
                'supplier_id', 'supplier_name', 'agreement_price_usd', 
                'agreement_price_local', 'local_currency', 'base_exchange_rate',
                'agreement_start_date', 'agreement_end_date', 'minimum_quantity',
                'payment_terms', 'agreement_conditions', 'created_by',
                'created_date', 'is_active'
            ])
            df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
        
        # 공급가 변동 이력 파일
        if not os.path.exists(self.supply_price_history_file):
            df = pd.DataFrame(columns=[
                'price_history_id', 'agreement_id', 'product_id', 'supplier_id',
                'old_price_usd', 'new_price_usd', 'old_price_local', 'new_price_local',
                'exchange_rate_at_change', 'change_reason', 'change_date',
                'effective_date', 'created_by', 'notes'
            ])
            df.to_csv(self.supply_price_history_file, index=False, encoding='utf-8-sig')
        
        # 환율 영향 분석 파일
        if not os.path.exists(self.exchange_rate_impact_file):
            df = pd.DataFrame(columns=[
                'impact_id', 'product_id', 'supplier_id', 'agreement_id',
                'base_exchange_rate', 'current_exchange_rate', 'rate_change_percent',
                'agreement_price_usd', 'current_equivalent_usd', 'price_impact_usd',
                'price_impact_percent', 'analysis_date', 'alert_level'
            ])
            df.to_csv(self.exchange_rate_impact_file, index=False, encoding='utf-8-sig')
        
        # MOQ별 가격 설정 파일
        if not os.path.exists(self.moq_pricing_file):
            df = pd.DataFrame(columns=[
                'moq_id', 'agreement_id', 'product_id', 'supplier_id',
                'min_quantity', 'max_quantity', 'tier_name', 'price_usd',
                'price_local', 'discount_percent', 'effective_date',
                'created_by', 'is_active'
            ])
            df.to_csv(self.moq_pricing_file, index=False, encoding='utf-8-sig')
        
        # 실제 구매 데이터 파일
        if not os.path.exists(self.actual_purchases_file):
            df = pd.DataFrame(columns=[
                'purchase_id', 'product_id', 'supplier_id', 'agreement_id',
                'purchase_order_id', 'quantity', 'actual_price_usd', 'actual_price_local',
                'exchange_rate_at_purchase', 'purchase_date', 'delivery_date',
                'agreement_variance_percent', 'total_amount_usd', 'total_amount_local',
                'payment_terms_actual', 'quality_rating', 'delivery_rating',
                'notes', 'created_by', 'created_date'
            ])
            df.to_csv(self.actual_purchases_file, index=False, encoding='utf-8-sig')
    
    def generate_agreement_id(self):
        """협정 ID를 생성합니다."""
        try:
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            if len(df) > 0:
                return 'AG001'
            
            existing_ids = df['agreement_id'].tolist()
            numbers = []
            for aid in existing_ids:
                if aid.startswith('AG') and aid[2:].isdigit():
                    numbers.append(int(aid[2:]))
            
            next_num = max(numbers) + 1 if numbers else 1
            return f'AG{next_num:03d}'
        except Exception as e:
            print(f"협정 ID 생성 중 오류: {e}")
            return f'AG{datetime.now().strftime("%m%d%H%M")}'
    
    def create_supplier_agreement(self, product_id, product_code, product_name,
                                supplier_id, supplier_name, agreement_price_usd,
                                agreement_price_local, local_currency, base_exchange_rate,
                                agreement_start_date, agreement_end_date,
                                minimum_quantity=1, payment_terms='NET 30',
                                agreement_conditions='', created_by='system'):
        """공급업체와의 협정을 생성합니다."""
        try:
            # 동일한 제품 코드로 여러 협정 등록 허용 (중복 체크 제거)
            agreement_id = self.generate_agreement_id()
            new_agreement = {
                'agreement_id': agreement_id,
                'product_id': product_id,
                'product_code': product_code,
                'product_name': product_name,
                'supplier_id': supplier_id,
                'supplier_name': supplier_name,
                'agreement_price_usd': agreement_price_usd,
                'agreement_price_local': agreement_price_local,
                'local_currency': local_currency,
                'base_exchange_rate': base_exchange_rate,
                'agreement_start_date': agreement_start_date,
                'agreement_end_date': agreement_end_date,
                'minimum_quantity': minimum_quantity,
                'payment_terms': payment_terms,
                'agreement_conditions': agreement_conditions,
                'created_by': created_by,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': True
            }
            
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([new_agreement])], ignore_index=True)
            df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
            
            return True, agreement_id
        except Exception as e:
            print(f"공급업체 협정 생성 중 오류: {e}")
            return False, str(e)
    
    def _deactivate_existing_agreements(self, product_id, supplier_id):
        """기존 활성 협정을 비활성화합니다."""
        try:
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            mask = ((df['product_id'] == product_id) & 
                   (df['supplier_id'] == supplier_id) & 
                   (df['is_active'] == True))
            
            if mask.any():
                df.loc[mask, 'is_active'] = False
                df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"기존 협정 비활성화 중 오류: {e}")
    
    def get_all_agreements(self):
        """모든 협정 데이터를 가져옵니다. (견적서에서 사용)"""
        return self.get_active_agreements()
    
    def get_active_agreements(self, product_id=None, supplier_id=None):
        """활성 협정을 조회합니다."""
        try:
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            # is_active 컬럼의 값을 안전하게 boolean으로 변환
            df['is_active'] = df['is_active'].astype(str).str.strip().str.lower()
            active_agreements = df[df['is_active'].isin(['true', '1', 'yes', 'y'])]
            
            if product_id:
                active_agreements = active_agreements[active_agreements['product_id'] == product_id]
            if supplier_id:
                active_agreements = active_agreements[active_agreements['supplier_id'] == supplier_id]
            
            return active_agreements
        except Exception as e:
            print(f"활성 협정 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def analyze_exchange_rate_impact(self, exchange_rate_manager):
        """환율 변동이 협정가에 미치는 영향을 분석합니다."""
        try:
            agreements_df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            # is_active 컬럼의 값을 안전하게 boolean으로 변환
            agreements_df['is_active'] = agreements_df['is_active'].astype(str).str.strip().str.lower()
            active_agreements = agreements_df[agreements_df['is_active'].isin(['true', '1', 'yes', 'y'])]
            
            if len(active_agreements) == 0:
                return pd.DataFrame()
            
            impact_data = []
            
            for _, agreement in active_agreements.iterrows():
                local_currency = agreement['local_currency']
                base_rate = agreement['base_exchange_rate']
                
                # 현재 환율 조회
                current_rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                current_rate = current_rate_info['rate'] if current_rate_info else base_rate
                
                # 환율 변동률 계산
                rate_change_percent = ((current_rate - base_rate) / base_rate) * 100 if base_rate > 0 else 0
                
                # 현재 환율 기준 USD 환산가
                current_equivalent_usd = agreement['agreement_price_local'] / current_rate if current_rate > 0 else 0
                
                # 가격 영향 계산
                price_impact_usd = current_equivalent_usd - agreement['agreement_price_usd']
                price_impact_percent = (price_impact_usd / agreement['agreement_price_usd']) * 100 if agreement['agreement_price_usd'] > 0 else 0
                
                # 알림 레벨 결정
                alert_level = 'LOW'
                if abs(price_impact_percent) > 10:
                    alert_level = 'HIGH'
                elif abs(price_impact_percent) > 5:
                    alert_level = 'MEDIUM'
                
                impact_record = {
                    'impact_id': f"IM{datetime.now().strftime('%Y%m%d%H%M%S')}{len(impact_data):03d}",
                    'product_id': agreement['product_id'],
                    'supplier_id': agreement['supplier_id'],
                    'agreement_id': agreement['agreement_id'],
                    'base_exchange_rate': base_rate,
                    'current_exchange_rate': current_rate,
                    'rate_change_percent': round(rate_change_percent, 2),
                    'agreement_price_usd': agreement['agreement_price_usd'],
                    'current_equivalent_usd': round(current_equivalent_usd, 2),
                    'price_impact_usd': round(price_impact_usd, 2),
                    'price_impact_percent': round(price_impact_percent, 2),
                    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                    'alert_level': alert_level
                }
                
                impact_data.append(impact_record)
            
            # 분석 결과 저장
            if impact_data:
                impact_df = pd.DataFrame(impact_data)
                impact_df.to_csv(self.exchange_rate_impact_file, index=False, encoding='utf-8-sig')
                return impact_df
            
            return pd.DataFrame()
        except Exception as e:
            print(f"환율 영향 분석 중 오류: {e}")
            return pd.DataFrame()
    
    def get_price_variance_alerts(self, threshold_percent=5):
        """가격 변동 알림을 가져옵니다."""
        try:
            df = pd.read_csv(self.exchange_rate_impact_file, encoding='utf-8-sig')
            
            if len(df) > 0:
                return pd.DataFrame()
            
            # 임계값을 초과하는 변동만 필터링
            alerts = df[df['price_impact_percent'].abs() > threshold_percent]
            
            return alerts.sort_values('price_impact_percent', ascending=False)
        except Exception as e:
            print(f"가격 변동 알림 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def update_agreement_price(self, agreement_id, new_price_usd, new_price_local,
                             change_reason, created_by='system'):
        """협정 가격을 업데이트합니다."""
        try:
            # 기존 협정 정보 조회
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            agreement = df[df['agreement_id'] == agreement_id]
            
            if len(agreement) > 0:
                return False, "협정을 찾을 수 없습니다."
            
            old_price_usd = agreement.iloc[0]['agreement_price_usd']
            old_price_local = agreement.iloc[0]['agreement_price_local']
            
            # 가격 변동 이력 기록
            history_id = f"PH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            price_history = {
                'price_history_id': history_id,
                'agreement_id': agreement_id,
                'product_id': agreement.iloc[0]['product_id'],
                'supplier_id': agreement.iloc[0]['supplier_id'],
                'old_price_usd': old_price_usd,
                'new_price_usd': new_price_usd,
                'old_price_local': old_price_local,
                'new_price_local': new_price_local,
                'exchange_rate_at_change': new_price_local / new_price_usd if new_price_usd > 0 else 0,
                'change_reason': change_reason,
                'change_date': datetime.now().strftime('%Y-%m-%d'),
                'effective_date': datetime.now().strftime('%Y-%m-%d'),
                'created_by': created_by,
                'notes': f'가격 변경: {old_price_usd} -> {new_price_usd} USD'
            }
            
            # 이력 저장
            history_df = pd.read_csv(self.supply_price_history_file, encoding='utf-8-sig')
            history_df = pd.concat([history_df, pd.DataFrame([price_history])], ignore_index=True)
            history_df.to_csv(self.supply_price_history_file, index=False, encoding='utf-8-sig')
            
            # 협정 가격 업데이트
            df.loc[df['agreement_id'] == agreement_id, 'agreement_price_usd'] = new_price_usd
            df.loc[df['agreement_id'] == agreement_id, 'agreement_price_local'] = new_price_local
            df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
            
            return True, history_id
        except Exception as e:
            print(f"협정 가격 업데이트 중 오류: {e}")
            return False, str(e)
    
    def get_supplier_performance_analysis(self, supplier_id=None):
        """공급업체 성과 분석을 수행합니다."""
        try:
            agreements_df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            history_df = pd.read_csv(self.supply_price_history_file, encoding='utf-8-sig')
            
            if supplier_id:
                agreements_df = agreements_df[agreements_df['supplier_id'] == supplier_id]
                history_df = history_df[history_df['supplier_id'] == supplier_id]
            
            if len(agreements_df) == 0:
                return {
                    'total_agreements': 0,
                    'active_agreements': 0,
                    'price_changes': 0,
                    'average_price_stability': 0,
                    'supplier_summary': pd.DataFrame()
                }
            
            # 공급업체별 성과 분석
            performance = agreements_df.groupby('supplier_id').agg({
                'agreement_id': 'count',
                'agreement_price_usd': 'mean',
                'is_active': 'sum'
            }).round(2)
            
            performance.columns = ['총_협정수', '평균_협정가', '활성_협정수']
            
            # 가격 변동 횟수 추가
            price_changes = history_df.groupby('supplier_id')['price_history_id'].count()
            performance['가격_변동횟수'] = price_changes.fillna(0)
            
            analysis = {
                'total_agreements': len(agreements_df),
                'active_agreements': len(agreements_df[agreements_df['is_active'] == True]),
                'price_changes': len(history_df),
                'average_price_stability': (len(agreements_df) - len(history_df)) / len(agreements_df) * 100 if len(agreements_df) > 0 else 0,
                'supplier_summary': performance.reset_index()
            }
            
            return analysis
        except Exception as e:
            print(f"공급업체 성과 분석 중 오류: {e}")
            return {
                'total_agreements': 0,
                'active_agreements': 0,
                'price_changes': 0,
                'average_price_stability': 0,
                'supplier_summary': pd.DataFrame()
            }
    
    def create_moq_pricing(self, agreement_id, product_id, supplier_id, 
                          pricing_tiers, created_by='system'):
        """MOQ별 가격 체계를 생성합니다."""
        try:
            moq_records = []
            
            for tier in pricing_tiers:
                moq_id = f"MOQ{datetime.now().strftime('%Y%m%d%H%M%S')}{len(moq_records):03d}"
                moq_record = {
                    'moq_id': moq_id,
                    'agreement_id': agreement_id,
                    'product_id': product_id,
                    'supplier_id': supplier_id,
                    'min_quantity': tier['min_quantity'],
                    'max_quantity': tier.get('max_quantity', 999999),
                    'tier_name': tier['tier_name'],
                    'price_usd': tier['price_usd'],
                    'price_local': tier.get('price_local', tier['price_usd']),
                    'discount_percent': tier.get('discount_percent', 0),
                    'effective_date': datetime.now().strftime('%Y-%m-%d'),
                    'created_by': created_by,
                    'is_active': True
                }
                moq_records.append(moq_record)
            
            # MOQ 가격 저장
            if moq_records:
                df = pd.read_csv(self.moq_pricing_file, encoding='utf-8-sig')
                new_df = pd.concat([df, pd.DataFrame(moq_records)], ignore_index=True)
                new_df.to_csv(self.moq_pricing_file, index=False, encoding='utf-8-sig')
                return True, f"MOQ 가격 {len(moq_records)}개 등록 완료"
            
            return False, "등록할 MOQ 가격이 없습니다."
        except Exception as e:
            print(f"MOQ 가격 생성 중 오류: {e}")
            return False, str(e)
    
    def get_moq_pricing(self, agreement_id=None, product_id=None):
        """MOQ별 가격을 조회합니다."""
        try:
            df = pd.read_csv(self.moq_pricing_file, encoding='utf-8-sig')
            
            if agreement_id:
                df = df[df['agreement_id'] == agreement_id]
            if product_id:
                df = df[df['product_id'] == product_id]
            
            return df[df['is_active'] == True].sort_values('min_quantity')
        except Exception as e:
            print(f"MOQ 가격 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def record_actual_purchase(self, product_id, supplier_id, agreement_id,
                             purchase_order_id, quantity, actual_price_usd,
                             actual_price_local, exchange_rate_at_purchase,
                             purchase_date, delivery_date=None,
                             payment_terms_actual='', quality_rating=5,
                             delivery_rating=5, notes='', created_by='system'):
        """실제 구매 데이터를 기록합니다."""
        try:
            # 협정가 조회
            agreements_df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            agreement = agreements_df[agreements_df['agreement_id'] == agreement_id]
            
            if len(agreement) > 0:
                return False, "협정 정보를 찾을 수 없습니다."
            
            agreement_price_usd = agreement.iloc[0]['agreement_price_usd']
            
            # 협정가 대비 편차 계산
            variance_percent = 0
            if agreement_price_usd > 0:
                variance_percent = ((actual_price_usd - agreement_price_usd) / agreement_price_usd) * 100
            
            purchase_id = f"PUR{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            purchase_record = {
                'purchase_id': purchase_id,
                'product_id': product_id,
                'supplier_id': supplier_id,
                'agreement_id': agreement_id,
                'purchase_order_id': purchase_order_id,
                'quantity': quantity,
                'actual_price_usd': actual_price_usd,
                'actual_price_local': actual_price_local,
                'exchange_rate_at_purchase': exchange_rate_at_purchase,
                'purchase_date': purchase_date,
                'delivery_date': delivery_date or purchase_date,
                'agreement_variance_percent': round(variance_percent, 2),
                'total_amount_usd': quantity * actual_price_usd,
                'total_amount_local': quantity * actual_price_local,
                'payment_terms_actual': payment_terms_actual,
                'quality_rating': quality_rating,
                'delivery_rating': delivery_rating,
                'notes': notes,
                'created_by': created_by,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 구매 데이터 저장
            df = pd.read_csv(self.actual_purchases_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([purchase_record])], ignore_index=True)
            df.to_csv(self.actual_purchases_file, index=False, encoding='utf-8-sig')
            
            return True, purchase_id
        except Exception as e:
            print(f"실제 구매 기록 중 오류: {e}")
            return False, str(e)
    
    def get_purchase_vs_agreement_analysis(self, supplier_id=None, product_id=None):
        """협정가 vs 실제 구매가 분석을 수행합니다."""
        try:
            purchases_df = pd.read_csv(self.actual_purchases_file, encoding='utf-8-sig')
            
            if len(purchases_df) == 0:
                return {
                    'total_purchases': 0,
                    'average_variance': 0,
                    'cost_savings': 0,
                    'analysis_data': pd.DataFrame()
                }
            
            # 필터 적용
            if supplier_id:
                purchases_df = purchases_df[purchases_df['supplier_id'] == supplier_id]
            if product_id:
                purchases_df = purchases_df[purchases_df['product_id'] == product_id]
            
            if len(purchases_df) == 0:
                return {
                    'total_purchases': 0,
                    'average_variance': 0,
                    'cost_savings': 0,
                    'analysis_data': pd.DataFrame()
                }
            
            # 분석 계산
            total_purchases = len(purchases_df)
            average_variance = purchases_df['agreement_variance_percent'].mean()
            
            # 비용 절약/손실 계산
            cost_impact = purchases_df['agreement_variance_percent'] * purchases_df['total_amount_usd'] / 100
            cost_savings = -cost_impact.sum()  # 음수면 절약, 양수면 손실
            
            # 제품별/공급업체별 분석
            analysis_data = purchases_df.groupby(['product_id', 'supplier_id']).agg({
                'agreement_variance_percent': ['mean', 'min', 'max', 'std'],
                'total_amount_usd': 'sum',
                'quantity': 'sum',
                'quality_rating': 'mean',
                'delivery_rating': 'mean',
                'purchase_id': 'count'
            }).round(2)
            
            analysis_data.columns = ['평균_편차율', '최소_편차율', '최대_편차율', '편차_표준편차',
                                   '총_구매액', '총_구매수량', '평균_품질점수', '평균_배송점수', '구매_횟수']
            
            return {
                'total_purchases': total_purchases,
                'average_variance': round(average_variance, 2),
                'cost_savings': round(cost_savings, 2),
                'analysis_data': analysis_data.reset_index()
            }
        except Exception as e:
            print(f"구매 vs 협정가 분석 중 오류: {e}")
            return {
                'total_purchases': 0,
                'average_variance': 0,
                'cost_savings': 0,
                'analysis_data': pd.DataFrame()
            }
    
    def get_supplier_comprehensive_performance(self, supplier_id=None):
        """공급업체 종합 성과 평가를 수행합니다."""
        try:
            # 협정 정보
            agreements_df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            # 실제 구매 정보
            purchases_df = pd.read_csv(self.actual_purchases_file, encoding='utf-8-sig')
            # 가격 변동 이력
            history_df = pd.read_csv(self.supply_price_history_file, encoding='utf-8-sig')
            
            if supplier_id:
                agreements_df = agreements_df[agreements_df['supplier_id'] == supplier_id]
                purchases_df = purchases_df[purchases_df['supplier_id'] == supplier_id]
                history_df = history_df[history_df['supplier_id'] == supplier_id]
            
            performance_data = []
            
            for supplier in agreements_df['supplier_id'].unique():
                supplier_agreements = agreements_df[agreements_df['supplier_id'] == supplier]
                supplier_purchases = purchases_df[purchases_df['supplier_id'] == supplier]
                supplier_history = history_df[history_df['supplier_id'] == supplier]
                
                # 기본 지표
                total_agreements = len(supplier_agreements)
                active_agreements = len(supplier_agreements[supplier_agreements['is_active'] == True])
                total_purchases = len(supplier_purchases)
                price_changes = len(supplier_history)
                
                # 성과 지표
                avg_quality = supplier_purchases['quality_rating'].mean() if not len(supplier_purchases) > 0 else 0
                avg_delivery = supplier_purchases['delivery_rating'].mean() if not len(supplier_purchases) > 0 else 0
                avg_variance = supplier_purchases['agreement_variance_percent'].mean() if not len(supplier_purchases) > 0 else 0
                total_purchase_amount = supplier_purchases['total_amount_usd'].sum() if not len(supplier_purchases) > 0 else 0
                
                # 가격 안정성 (변동 횟수가 적을수록 안정적)
                price_stability = (total_agreements - price_changes) / total_agreements * 100 if total_agreements > 0 else 0
                
                # 종합 점수 계산 (가중 평균)
                performance_score = (
                    avg_quality * 0.3 +      # 품질 30%
                    avg_delivery * 0.3 +     # 배송 30%
                    (100 - abs(avg_variance)) * 0.2 +  # 가격 준수 20%
                    price_stability * 0.2    # 가격 안정성 20%
                ) / 100 * 5  # 5점 만점으로 조정
                
                performance_data.append({
                    'supplier_id': supplier,
                    'total_agreements': total_agreements,
                    'active_agreements': active_agreements,
                    'total_purchases': total_purchases,
                    'price_changes': price_changes,
                    'avg_quality_rating': round(avg_quality, 1),
                    'avg_delivery_rating': round(avg_delivery, 1),
                    'avg_price_variance': round(avg_variance, 2),
                    'total_purchase_amount': round(total_purchase_amount, 2),
                    'price_stability': round(price_stability, 1),
                    'performance_score': round(performance_score, 1)
                })
            
            return pd.DataFrame(performance_data)
        except Exception as e:
            print(f"공급업체 종합 성과 평가 중 오류: {e}")
            return pd.DataFrame()
    
    def get_all_prices(self):
        """모든 공급 가격 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            return df.to_dict('records')
        except Exception as e:
            print(f"공급 가격 조회 중 오류: {e}")
            return []
    
    def update_agreements_batch(self, edited_data, original_data):
        """협정 정보를 일괄 업데이트합니다."""
        try:
            # 전체 협정 데이터 로드
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            
            # 수정된 데이터와 원본 데이터 비교하여 변경사항 적용
            for idx, edited_row in edited_data.iterrows():
                agreement_id = edited_row['agreement_id']
                
                # 전체 데이터에서 해당 협정 찾기
                df_idx = df[df['agreement_id'] == agreement_id].index
                if len(df_idx) > 0:
                    # 편집 가능한 컬럼들만 업데이트
                    df.loc[df_idx[0], 'supplier_name'] = edited_row['supplier_name']
                    df.loc[df_idx[0], 'agreement_price_usd'] = edited_row['agreement_price_usd']
                    df.loc[df_idx[0], 'agreement_price_local'] = edited_row['agreement_price_local']
                    df.loc[df_idx[0], 'agreement_start_date'] = edited_row['agreement_start_date']
                    df.loc[df_idx[0], 'agreement_end_date'] = edited_row['agreement_end_date']
                    df.loc[df_idx[0], 'minimum_quantity'] = edited_row['minimum_quantity']
                    df.loc[df_idx[0], 'payment_terms'] = edited_row['payment_terms']
                    df.loc[df_idx[0], 'agreement_conditions'] = edited_row['agreement_conditions']
                    df.loc[df_idx[0], 'is_active'] = edited_row['is_active']
                    df.loc[df_idx[0], 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 파일 저장
            df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"협정 일괄 업데이트 중 오류: {e}")
            return False
    
    def delete_agreements(self, agreement_ids):
        """협정을 삭제합니다."""
        try:
            # 전체 협정 데이터 로드
            df = pd.read_csv(self.supplier_agreements_file, encoding='utf-8-sig')
            
            # 선택된 협정들 삭제
            df = df[~df['agreement_id'].isin(agreement_ids)]
            
            # 파일 저장
            df.to_csv(self.supplier_agreements_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"협정 삭제 중 오류: {e}")
            return False