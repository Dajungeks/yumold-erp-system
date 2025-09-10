import pandas as pd
import os
from datetime import datetime

class MasterProductManager:
    """
    마스터 제품 관리자 - 기준 제품 데이터베이스
    견적서, 판매제품관리, 외주공급가관리와 연동되는 기준 데이터
    """
    
    def __init__(self):
        self.data_file = 'data/master_products.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            # 영어 기반 필드명으로 마스터 제품 데이터베이스 구조 정의
            df = pd.DataFrame(columns=[
                # 기본 식별 정보
                'product_id',           # 고유 제품 ID (자동생성)
                'product_code',         # 제품 코드 (YMV-ST-MAE-20-xx 등)
                'product_name_korean',  # 한국어 제품명
                'product_name_english', # 영어 제품명
                'product_name_vietnamese', # 베트남어 제품명
                
                # 카테고리 정보 (영어 기반)
                'main_category',        # MB, HR, HRC, MB+HR, ROBOT, SPARE-HR, SPARE-MB, SPARE-ROBOT, SERVICE
                'sub_category',         # 2P, 3P, HR (MB용) / Valve, Open (HR용) / HRCT, HRCS, MTC (HRC용)
                'product_type',         # ST, CP 등
                'product_variant',      # MAE, MCC, MAA, SC, VL 등
                'size_primary',         # 주요 사이즈 (20, 25, 35, 45 등)
                'size_secondary',       # 보조 사이즈 (xx, 1.2, 1.5, 2.0 등)
                'material_type',        # SS400, S50C, SKD61, NAK80, P20, SCM440, FC300, A5052, STAVAX, HPM38
                
                # 기술 사양
                'specifications',       # 기술 사양 (H30,34,1.0 등)
                'unit_of_measure',      # 단위 (EA, SET, PC 등)
                'weight_kg',           # 중량 (kg)
                'dimensions',          # 치수 정보
                
                # 세관/세무 정보
                'hs_code',             # HS 코드
                'import_tax_rate',     # 수입세율 (%)
                'vat_rate',            # VAT 세율 (%)
                'description_vietnamese', # 베트남어 설명
                
                # 공급업체 정보
                'primary_supplier_id',  # 주 공급업체 ID
                'primary_supplier_name', # 주 공급업체명
                'secondary_supplier_id', # 보조 공급업체 ID
                'secondary_supplier_name', # 보조 공급업체명
                
                # 가격 정보 (기준가)
                'standard_cost_usd',    # 표준 원가 (USD)
                'standard_cost_local',  # 현지 통화 원가
                'local_currency',       # 현지 통화 코드
                'recommended_price_usd', # 권장 판매가 (USD)
                'margin_percentage',    # 마진율 (%)
                
                # 재고/주문 정보
                'minimum_order_qty',    # 최소 주문 수량
                'lead_time_days',      # 리드타임 (일)
                'stock_level',         # 재고 수준
                'reorder_point',       # 재주문 시점
                
                # 상태 및 관리 정보
                'status',              # active, inactive, discontinued
                'is_standard_product', # 표준품 여부 (True/False)
                'is_custom_available', # 커스텀 제작 가능 여부
                'quality_grade',       # 품질 등급 (A, B, C)
                
                # 시스템 정보
                'created_date',        # 생성일
                'updated_date',        # 수정일
                'created_by',          # 생성자
                'updated_by',          # 수정자
                'data_source',         # 데이터 출처 (HR_CODE, MB_CODE, MANUAL)
                'source_row_number',   # 원본 데이터 행 번호
                
                # 연동 정보
                'quotation_available', # 견적서 사용 가능 여부
                'sales_price_set',     # 판매가 설정 여부
                'supply_price_set',    # 공급가 설정 여부
                'last_quoted_date',    # 마지막 견적일
                'last_sold_date',      # 마지막 판매일
                'gate_type'            # 게이트 타입 (HR 제품용)
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def get_all_products(self):
        """모든 마스터 제품 데이터 조회"""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df  # DataFrame으로 반환
        except Exception as e:
            print(f"제품 데이터 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_products_by_category(self, main_category):
        """카테고리별 제품 조회"""
        df = self.get_all_products()
        if len(df) > 0:
            return df[df['main_category'] == main_category]
        return pd.DataFrame()
    
    def get_product_by_code(self, product_code):
        """제품 코드로 제품 조회"""
        df = self.get_all_products()
        if len(df) > 0:
            result = df[df['product_code'] == product_code]
            if len(result) > 0:
                return result.iloc[0].to_dict()
        return None
    
    def is_product_code_exists(self, product_code):
        """제품 코드 중복 체크"""
        df = self.get_all_products()
        if len(df) > 0:
            return product_code in df['product_code'].values
        return False
    
    def add_product(self, product_data):
        """새로운 제품을 마스터 데이터베이스에 추가"""
        try:
            # 중복 코드 체크
            if self.is_product_code_exists(product_data['product_code']):
                return False, f"제품 코드 '{product_data['product_code']}'가 이미 존재합니다."
            
            # 현재 시간
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 제품 ID 생성 (MANUAL_접두사 + 타임스탬프)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            product_data['product_id'] = f"MANUAL_{timestamp}"
            
            # 시스템 필드 설정
            product_data.update({
                'created_date': current_time,
                'updated_date': current_time,
                'created_by': 'USER',
                'updated_by': 'USER',
                'data_source': 'MANUAL',
                'source_row_number': 0,
                'status': 'active',
                'is_standard_product': True,
                'is_custom_available': True,
                'quality_grade': 'A',
                'quotation_available': True,
                'sales_price_set': False,
                'supply_price_set': False,
                'last_quoted_date': '',
                'last_sold_date': ''
            })
            
            # 기존 데이터 로드
            df = self.get_all_products()
            
            # 새 제품 데이터를 DataFrame으로 변환
            new_product_df = pd.DataFrame([product_data])
            
            # 데이터 결합
            if len(df) > 0:
                df_combined = pd.concat([df, new_product_df], ignore_index=True)
            else:
                df_combined = new_product_df
            
            # 파일 저장
            df_combined.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"제품 코드 '{product_data['product_code']}'가 성공적으로 등록되었습니다."
            
        except Exception as e:
            return False, f"제품 등록 중 오류가 발생했습니다: {str(e)}"
    
    def get_statistics(self):
        """제품 통계 정보 반환"""
        df = self.get_all_products()
        if len(df) == 0:
            return {}
        
        stats = {
            'total_products': len(df),
            'active_products': len(df[df['status'] == 'active']),
            'categories': df['main_category'].value_counts().to_dict(),
            'with_sales_price': len(df[df['sales_price_set'] == 'True']),
            'with_supply_price': len(df[df['supply_price_set'] == 'True']),
            'quotation_available': len(df[df['quotation_available'] == 'True'])
        }
        return stats
    
    def get_quotation_available_products(self):
        """견적서에서 사용 가능한 제품들 조회"""
        df = self.get_all_products()
        if len(df) > 0:
            return df[(df['quotation_available'] == True) & (df['status'] == 'active')]
        return pd.DataFrame()
    
    def get_categories(self):
        """모든 메인 카테고리 목록 반환"""
        df = self.get_all_products()
        if len(df) > 0:
            return sorted(df['main_category'].unique().tolist())
        return []
    
    def get_sub_categories(self, main_category):
        """메인 카테고리의 서브 카테고리 목록 반환"""
        df = self.get_products_by_category(main_category)
        if len(df) > 0:
            return sorted(df['sub_category'].unique().tolist())
        return []
    
    def get_product_by_code(self, product_code):
        """제품 코드로 제품 정보 조회"""
        try:
            df = self.get_all_products()
            if len(df) > 0:
                product = df[df['product_code'] == product_code]
                if len(product) > 0:
                    return product.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"제품 조회 오류: {str(e)}")
            return None
    
    def update_product(self, product_code, updated_data):
        """제품 정보 업데이트"""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return False, "제품 데이터가 없습니다."
            
            # 제품 코드로 해당 제품 찾기
            product_index = df[df['product_code'] == product_code].index
            if len(product_index) == 0:
                return False, f"제품 코드 '{product_code}'를 찾을 수 없습니다."
            
            # 업데이트 시간 설정
            updated_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_data['updated_by'] = 'USER'
            
            # 데이터 업데이트
            for key, value in updated_data.items():
                if key in df.columns:
                    df.loc[product_index, key] = value
            
            # 파일 저장
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"제품 코드 '{product_code}'가 성공적으로 수정되었습니다."
            
        except Exception as e:
            return False, f"제품 수정 중 오류가 발생했습니다: {str(e)}"
    
    def delete_product(self, product_code):
        """제품 삭제 (상태를 inactive로 변경)"""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return False, "제품 데이터가 없습니다."
            
            # 제품 코드로 해당 제품 찾기
            product_index = df[df['product_code'] == product_code].index
            if len(product_index) == 0:
                return False, f"제품 코드 '{product_code}'를 찾을 수 없습니다."
            
            # 상태를 inactive로 변경 (소프트 삭제)
            df.loc[product_index, 'status'] = 'inactive'
            df.loc[product_index, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[product_index, 'updated_by'] = 'USER'
            
            # 파일 저장
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"제품 코드 '{product_code}'가 성공적으로 삭제되었습니다."
            
        except Exception as e:
            return False, f"제품 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def restore_product(self, product_code):
        """삭제된 제품 복원 (상태를 active로 변경)"""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return False, "제품 데이터가 없습니다."
            
            # 제품 코드로 해당 제품 찾기
            product_index = df[df['product_code'] == product_code].index
            if len(product_index) == 0:
                return False, f"제품 코드 '{product_code}'를 찾을 수 없습니다."
            
            # 상태를 active로 변경 (복원)
            df.loc[product_index, 'status'] = 'active'
            df.loc[product_index, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[product_index, 'updated_by'] = 'USER'
            
            # 파일 저장
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"제품 코드 '{product_code}'가 성공적으로 복원되었습니다."
            
        except Exception as e:
            return False, f"제품 복원 중 오류가 발생했습니다: {str(e)}"
    
    def permanently_delete_product(self, product_code):
        """제품 완전 삭제 (데이터베이스에서 물리적 제거)"""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return False, "제품 데이터가 없습니다."
            
            # 제품 코드로 해당 제품 찾기
            product_index = df[df['product_code'] == product_code].index
            if len(product_index) == 0:
                return False, f"제품 코드 '{product_code}'를 찾을 수 없습니다."
            
            # 백업 생성
            backup_filename = f"master_products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            backup_path = os.path.join(os.path.dirname(self.data_file), backup_filename)
            df.to_csv(backup_path, index=False, encoding='utf-8-sig')
            
            # 해당 제품 행 완전 삭제
            df_cleaned = df.drop(product_index).reset_index(drop=True)
            
            # 파일 저장
            df_cleaned.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"제품 코드 '{product_code}'가 완전히 삭제되었습니다. 백업: {backup_filename}"
            
        except Exception as e:
            return False, f"제품 완전 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def search_products(self, search_term="", category="", status="active"):
        """제품 검색"""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return []
            
            # 상태 필터
            if status and status != "all":
                df = df[df['status'] == status]
            
            # 카테고리 필터
            if category:
                df = df[df['main_category'] == category]
            
            # 검색어 필터
            if search_term:
                search_mask = (
                    df['product_code'].str.contains(search_term, case=False, na=False) |
                    df['product_name_korean'].str.contains(search_term, case=False, na=False) |
                    df['product_name_english'].str.contains(search_term, case=False, na=False)
                )
                df = df[search_mask]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"제품 검색 오류: {str(e)}")
            return []