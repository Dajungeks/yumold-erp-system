import pandas as pd
import os
from datetime import datetime

class ProductCodeManager:
    def __init__(self):
        self.data_file = 'data/product_codes.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'code_id', 'standard_code', 'product_name', 'main_category', 'sub_category_mb',
                'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material', 'description', 'hs_code', 'unit',
                'standard_price_usd', 'margin_percent', 'supplier_codes',
                'status', 'created_by', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        else:
            # 기존 파일이 있을 때 새로운 구조로 마이그레이션
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8-sig')
                
                # 새로운 컬럼 구조 정의
                new_columns = [
                    'code_id', 'standard_code', 'product_name', 'main_category', 'sub_category_mb',
                    'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material', 'description', 'hs_code', 'unit',
                    'standard_price_usd', 'margin_percent', 'supplier_codes',
                    'status', 'created_by', 'input_date', 'updated_date'
                ]
                
                # 기존 category 컬럼들을 새로운 구조로 매핑
                if 'category1' in df.columns:
                    df['main_category'] = df['category1']
                if 'category2' in df.columns:
                    df['sub_category_mb'] = df['category2']
                if 'category3' in df.columns:
                    df['sub_category_hrc'] = df['category3']
                if 'category4' in df.columns:
                    df['sub_category_hr'] = df['category4']
                if 'category5' in df.columns:
                    df['sub_category_mb_material'] = df['category5']
                
                # 누락된 컬럼 추가
                for col in new_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # 새로운 컬럼 순서로 재정렬
                df = df.reindex(columns=new_columns)
                df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
                
            except Exception as e:
                print(f"제품 코드 데이터 마이그레이션 중 오류: {e}")
                # 백업 생성 후 새 파일 생성
                backup_file = f"{self.data_file}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if os.path.exists(self.data_file):
                    os.rename(self.data_file, backup_file)
                
                df = pd.DataFrame(columns=[
                    'code_id', 'standard_code', 'product_name', 'main_category', 'sub_category_mb',
                    'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material', 'description', 'hs_code', 'unit',
                    'standard_price_usd', 'margin_percent', 'supplier_codes',
                    'status', 'created_by', 'input_date', 'updated_date'
                ])
                df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def add_product_code(self, code_data):
        """새 표준 제품 코드를 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 중복 확인 (표준 코드로 확인)
            if code_data['standard_code'] in df['standard_code'].values:
                return False
            
            # 코드 ID 생성
            if 'code_id' not in code_data or not code_data['code_id']:
                code_data['code_id'] = f"PC{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기본값 설정
            code_data['status'] = code_data.get('status', '활성')
            code_data['margin_percent'] = code_data.get('margin_percent', 20.0)
            code_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            code_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([code_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"제품 코드 추가 중 오류: {e}")
            return False
    
    def get_all_product_codes(self):
        """모든 표준 제품 코드를 가져옵니다."""
        try:
            return pd.read_csv(self.data_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"제품 코드 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_active_product_codes(self):
        """활성 상태인 표준 제품 코드를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['status'] == '활성']
        except Exception as e:
            print(f"활성 제품 코드 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_product_code_by_code(self, standard_code):
        """표준 코드로 제품 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            code = df[df['standard_code'] == standard_code]
            if len(code) > 0:
                return code.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"제품 코드 조회 중 오류: {e}")
            return None
    
    def get_standard_categories(self):
        """이미지 기반 표준 제품 카테고리를 반환합니다."""
        return {
            'main_category': ['MB', 'HRC', 'HR', 'MB+HR', 'ROBOT', 'SPARE-HR', 'SPARE-MB', 'SPARE-ROBOT', 'SERVICE'],
            'sub_category_mb': ['2P', '3P', 'HR'],
            'sub_category_hrc': ['HRCT', 'HRCS', 'MTC'],
            'sub_category_hr': ['Valve', 'Open'],
            'sub_category_mb_material': ['SS400', 'S50C', 'SKD61', 'NAK80', 'P20', 'SCM440', 'FC300', 'A5052', 'STAVAX', 'HPM38']
        }
    
    def initialize_standard_categories(self):
        """표준 제품 카테고리 데이터를 초기화합니다."""
        categories = self.get_standard_categories()
        
        # 각 카테고리별로 기본 데이터 생성
        standard_products = [
            # MB 제품
            {'standard_code': 'MB-2P-001', 'product_name': 'MB 2P Standard', 'main_category': 'MB', 'sub_category_mb': '2P'},
            {'standard_code': 'MB-3P-001', 'product_name': 'MB 3P Standard', 'main_category': 'MB', 'sub_category_mb': '3P'},
            {'standard_code': 'MB-HR-001', 'product_name': 'MB HR Standard', 'main_category': 'MB', 'sub_category_mb': 'HR'},
            
            # HRC 제품
            {'standard_code': 'HRC-HRCT-001', 'product_name': 'HRC Temperature Controller', 'main_category': 'HRC', 'sub_category_hrc': 'HRCT'},
            {'standard_code': 'HRC-HRCS-001', 'product_name': 'HRC System Controller', 'main_category': 'HRC', 'sub_category_hrc': 'HRCS'},
            {'standard_code': 'HRC-MTC-001', 'product_name': 'HRC MTC Controller', 'main_category': 'HRC', 'sub_category_hrc': 'MTC'},
            
            # HR 제품
            {'standard_code': 'HR-VALVE-001', 'product_name': 'HR Valve System', 'main_category': 'HR', 'sub_category_hr': 'Valve'},
            {'standard_code': 'HR-OPEN-001', 'product_name': 'HR Open System', 'main_category': 'HR', 'sub_category_hr': 'Open'},
            
            # MB+HR 제품
            {'standard_code': 'MBHR-001', 'product_name': 'MB+HR Combined System', 'main_category': 'MB+HR'},
            
            # ROBOT 제품
            {'standard_code': 'ROBOT-001', 'product_name': 'Industrial Robot System', 'main_category': 'ROBOT'},
            
            # SPARE 제품
            {'standard_code': 'SPARE-HR-001', 'product_name': 'HR Spare Parts', 'main_category': 'SPARE-HR'},
            {'standard_code': 'SPARE-MB-001', 'product_name': 'MB Spare Parts', 'main_category': 'SPARE-MB'},
            {'standard_code': 'SPARE-ROBOT-001', 'product_name': 'Robot Spare Parts', 'main_category': 'SPARE-ROBOT'},
            
            # SERVICE
            {'standard_code': 'SERVICE-001', 'product_name': 'Maintenance Service', 'main_category': 'SERVICE'}
        ]
        
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            existing_codes = df['standard_code'].tolist() if len(df) > 0 else []
            
            for product in standard_products:
                if product['standard_code'] not in existing_codes:
                    product['code_id'] = f"PC{datetime.now().strftime('%Y%m%d%H%M%S')}{len(df)}"
                    product['description'] = f"Standard {product['main_category']} product"
                    product['hs_code'] = '8477900000'
                    product['unit'] = 'SET'
                    product['standard_price_usd'] = 1000.0
                    product['margin_percent'] = 25.0
                    product['supplier_codes'] = 'STD-SUPPLIER'
                    product['status'] = '활성'
                    product['created_by'] = 'System'
                    product['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    product['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 누락된 필드 추가
                    for field in ['sub_category_mb', 'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material']:
                        if field not in product:
                            product[field] = ''
                    
                    df = pd.concat([df, pd.DataFrame([product])], ignore_index=True)
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"표준 카테고리 초기화 중 오류: {e}")
            return False
        except Exception as e:
            print(f"제품 코드 조회 중 오류: {e}")
            return None
    
    def update_product_code(self, code_id, code_data):
        """표준 제품 코드를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if code_id not in df['code_id'].values:
                return False
            
            code_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in code_data.items():
                if key in df.columns:
                    df.loc[df['code_id'] == code_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"제품 코드 업데이트 중 오류: {e}")
            return False
    
    def get_codes_by_category(self, category):
        """카테고리별 제품 코드를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['category'] == category]
        except Exception as e:
            print(f"카테고리별 제품 코드 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_categories(self):
        """표준 카테고리1 목록을 가져옵니다."""
        # 표준 카테고리만 반환
        standard_categories = [
            "HR", "MB", "PU", "VB", "SS", "MC", "AC", "PC", "RC", "TP"
        ]
        return standard_categories
    
    def get_category2_options(self):
        """표준 카테고리2 목록을 가져옵니다."""
        # 주요 카테고리2만 반환
        standard_categories = [
            "볼트", "너트", "와셔", "스크류", "앵글", "채널", "빔", "파이프", 
            "플레이트", "바", "튜브", "피팅", "밸브", "플랜지", "개스킷"
        ]
        return standard_categories
    
    def get_category3_options(self):
        """표준 카테고리3 목록을 가져옵니다."""
        # 주요 카테고리3만 반환  
        standard_categories = [
            "M6", "M8", "M10", "M12", "M16", "M20", "M24", "M30",
            "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "1", "1-1/4",
            "스테인리스", "탄소강", "합금강", "황동", "알루미늄"
        ]
        return standard_categories
    
    def get_category4_options(self):
        """표준 카테고리4 목록을 가져옵니다."""
        # 주요 카테고리4만 반환
        standard_categories = [
            "SUS304", "SUS316", "SS400", "A36", "A572", "6061-T6", "C1020",
            "DIN", "ISO", "ANSI", "JIS", "KS", "GB", "ASTM", "EN"
        ]
        return standard_categories
    
    def generate_standard_code(self, category, subcategory=None):
        """표준 코드를 자동 생성합니다."""
        try:
            # 카테고리 코드 매핑
            category_codes = {
                'MB': 'MB',
                'HRC': 'HR',
                'HR': 'HR',
                'MB+HR': 'MH',
                'MTC': 'MT',
                'ROBOT': 'RB',
                'SPARE-HR': 'SH',
                'SPARE-MB': 'SM',
                'SPARE-ROBOT': 'SR'
            }
            
            category_code = category_codes.get(category, 'MB')
            
            # 기존 코드에서 다음 번호 찾기
            df = self.get_all_product_codes()
            existing_codes = df[df['standard_code'].str.startswith(category_code)]['standard_code'].tolist()
            
            numbers = []
            for code in existing_codes:
                try:
                    number_part = code.replace(category_code, '').replace('-', '')
                    if number_part.isdigit():
                        numbers.append(int(number_part))
                except:
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
            
            if subcategory:
                return f"{category_code}-{subcategory[:2].upper()}-{next_num:04d}"
            else:
                return f"{category_code}-{next_num:04d}"
        except Exception as e:
            print(f"표준 코드 생성 중 오류: {e}")
            return f"OT-{datetime.now().strftime('%m%d%H%M')}"
    
    def calculate_recommended_price(self, cost_price, margin_percent=None):
        """추천 가격을 계산합니다."""
        try:
            if margin_percent is None:
                margin_percent = 20.0  # 기본 마진 20%
            
            margin_multiplier = 1 + (margin_percent / 100)
            recommended_price = cost_price * margin_multiplier
            
            return round(recommended_price, 2)
        except Exception as e:
            print(f"추천 가격 계산 중 오류: {e}")
            return cost_price
    
    def get_code_statistics(self):
        """제품 코드 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 가격을 숫자로 변환
            df['standard_price_usd'] = pd.to_numeric(df['standard_price_usd'], errors='coerce').fillna(0)
            
            stats = {
                'total_codes': len(df),
                'active_codes': len(df[df['status'] == '활성']),
                'inactive_codes': len(df[df['status'] == '비활성']),
                'categories': df['category1'].nunique(),
                'average_price': df['standard_price_usd'].mean(),
                'category_distribution': df['category1'].value_counts().to_dict(),
                'status_distribution': df['status'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"제품 코드 통계 조회 중 오류: {e}")
            return {}
    
    def search_product_codes(self, search_term):
        """제품 코드를 검색합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if not search_term:
                return df
            
            mask = (
                df['standard_code'].str.contains(search_term, na=False, case=False) |
                df['product_name'].str.contains(search_term, na=False, case=False) |
                df['description'].str.contains(search_term, na=False, case=False) |
                df['category1'].str.contains(search_term, na=False, case=False)
            )
            
            return df[mask]
        except Exception as e:
            print(f"제품 코드 검색 중 오류: {e}")
            return pd.DataFrame()
    
    def bulk_import_codes(self, codes_data):
        """여러 제품 코드를 한번에 가져옵니다."""
        results = {'added': 0, 'updated': 0, 'errors': []}
        
        for code_data in codes_data:
            try:
                # 표준 코드가 없으면 생성
                if 'standard_code' not in code_data or not code_data['standard_code']:
                    code_data['standard_code'] = self.generate_standard_code(
                        code_data.get('category', '기타'),
                        code_data.get('subcategory')
                    )
                
                # 기존 코드 확인
                existing_code = self.get_product_code_by_code(code_data['standard_code'])
                
                if existing_code:
                    # 업데이트
                    if self.update_product_code(existing_code['code_id'], code_data):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"코드 {code_data['standard_code']} 업데이트 실패")
                else:
                    # 새로 추가
                    if self.add_product_code(code_data):
                        results['added'] += 1
                    else:
                        results['errors'].append(f"코드 {code_data.get('standard_code', 'Unknown')} 추가 실패")
            
            except Exception as e:
                results['errors'].append(f"코드 처리 중 오류: {str(e)}")
        
        return results
    
    def get_category1_options(self):
        """Category1 옵션 목록을 반환합니다."""
        return ['MB', 'HRC', 'HR', 'MB+HR', 'MTC', 'ROBOT', 'SPARE-HR', 'SPARE-MB', 'SPARE-ROBOT']
