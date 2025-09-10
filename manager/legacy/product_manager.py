import pandas as pd
import os
from datetime import datetime

class ProductManager:
    def __init__(self):
        self.data_file = 'data/products.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'product_id', 'product_code', 'product_name', 'product_name_english', 'product_name_vietnamese',
                'main_category', 'sub_category_mb', 'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material',
                'supplier_id', 'supplier_name', 'cost_price_usd', 'cost_price_local', 'local_currency', 
                'recommended_price_usd', 'margin_percent', 'hs_code', 'import_tax_percent', 'vat_percent', 
                'description', 'specifications', 'unit', 'minimum_order_qty', 'lead_time_days', 
                'status', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        else:
            # 기존 파일이 있을 때 새로운 구조로 마이그레이션
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8-sig')
                
                # 새로운 컬럼 구조 정의
                new_columns = [
                    'product_id', 'product_code', 'product_name', 'product_name_english', 'product_name_vietnamese',
                    'main_category', 'sub_category_mb', 'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material',
                    'supplier_id', 'supplier_name', 'cost_price_usd', 'cost_price_local', 'local_currency', 
                    'recommended_price_usd', 'margin_percent', 'hs_code', 'import_tax_percent', 'vat_percent', 
                    'description', 'specifications', 'unit', 'minimum_order_qty', 'lead_time_days', 
                    'status', 'input_date', 'updated_date'
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
                print(f"제품 데이터 마이그레이션 중 오류: {e}")
                # 백업 생성 후 새 파일 생성
                backup_file = f"{self.data_file}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if os.path.exists(self.data_file):
                    os.rename(self.data_file, backup_file)
                
                df = pd.DataFrame(columns=[
                    'product_id', 'product_code', 'product_name', 'product_name_english', 'product_name_vietnamese',
                    'main_category', 'sub_category_mb', 'sub_category_hrc', 'sub_category_hr', 'sub_category_mb_material',
                    'supplier_id', 'supplier_name', 'cost_price_usd', 'cost_price_local', 'local_currency', 
                    'recommended_price_usd', 'margin_percent', 'hs_code', 'import_tax_percent', 'vat_percent', 
                    'description', 'specifications', 'unit', 'minimum_order_qty', 'lead_time_days', 
                    'status', 'input_date', 'updated_date'
                ])
                df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_product_id(self):
        """제품 ID를 생성합니다."""
        try:
            df = self.get_all_products()
            if len(df) == 0:
                return 'P001'
            
            # 기존 ID에서 숫자 부분 추출하여 다음 번호 생성
            existing_ids = df['product_id'].tolist()
            numbers = []
            for pid in existing_ids:
                if pid.startswith('P') and pid[1:].isdigit():
                    numbers.append(int(pid[1:]))
            
            next_num = max(numbers) + 1 if numbers else 1
            return f'P{next_num:03d}'
        except Exception as e:
            print(f"제품 ID 생성 중 오류: {e}")
            return f'P{datetime.now().strftime("%m%d%H%M")}'
    
    def _ensure_utf8_encoding(self, text):
        """문자열이 UTF-8로 제대로 인코딩되도록 보장합니다."""
        if text is None:
            return ""
        
        if isinstance(text, str):
            # 이미 문자열인 경우 그대로 반환
            return text
        elif isinstance(text, bytes):
            # 바이트인 경우 UTF-8로 디코딩
            try:
                return text.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return text.decode('cp949')  # 한국어 인코딩 시도
                except UnicodeDecodeError:
                    return text.decode('latin1', errors='ignore')
        else:
            # 다른 타입인 경우 문자열로 변환
            return str(text)
    
    def add_product(self, product_data):
        """새 제품을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 중복 확인 (제품코드로 확인)
            if 'product_code' in product_data and product_data['product_code']:
                if product_data['product_code'] in df['product_code'].values:
                    return False
            
            # 제품 ID가 없으면 생성
            if 'product_id' not in product_data or not product_data['product_id']:
                product_data['product_id'] = self.generate_product_id()
            
            # 문자열 필드에 대한 UTF-8 인코딩 보장
            text_fields = ['product_name', 'product_name_english', 'product_name_vietnamese', 
                          'description', 'specifications', 'supplier_name', 'notes']
            for field in text_fields:
                if field in product_data:
                    product_data[field] = self._ensure_utf8_encoding(product_data[field])
            
            # 기본값 설정
            product_data['status'] = product_data.get('status', '활성')
            product_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            product_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 마진 계산
            if 'cost_price_usd' in product_data and 'recommended_price_usd' in product_data:
                try:
                    cost = float(product_data['cost_price_usd'])
                    recommended = float(product_data['recommended_price_usd'])
                    if cost > 0:
                        margin = ((recommended - cost) / cost) * 100
                        product_data['margin_percent'] = round(margin, 2)
                except (ValueError, ZeroDivisionError):
                    product_data['margin_percent'] = 0
            
            df = pd.concat([df, pd.DataFrame([product_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"제품 추가 중 오류: {e}")
            return False
    
    def get_all_products(self):
        """모든 제품 정보를 가져옵니다."""
        try:
            # 여러 인코딩 시도
            encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(self.data_file, encoding=encoding)
                    
                    # 누락된 컬럼 추가 (마이그레이션)
                    required_columns = [
                        'product_id', 'product_code', 'product_name', 'product_name_english', 'product_name_vietnamese',
                        'category1', 'category2', 'category3', 'category4', 'category5', 'category6', 'supplier_id', 'supplier_name', 
                        'cost_price_usd', 'cost_price_local', 'local_currency', 'recommended_price_usd', 'margin_percent', 
                        'hs_code', 'import_tax_percent', 'vat_percent', 'description', 'specifications', 
                        'unit', 'minimum_order_qty', 'lead_time_days', 'status', 'input_date', 'updated_date'
                    ]
                    
                    # 누락된 컬럼을 빈 값으로 추가
                    for col in required_columns:
                        if col not in df.columns:
                            df[col] = ''
                    
                    # 컬럼 순서 정렬
                    df = df[required_columns]
                    
                    # 변경사항이 있으면 저장
                    if 'category5' not in pd.read_csv(self.data_file, encoding=encoding, nrows=0).columns:
                        df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
                    
                    # 데이터 정리 및 UTF-8 보장
                    for col in ['product_name', 'product_name_english', 'product_name_vietnamese', 
                               'description', 'specifications', 'supplier_name']:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: self._ensure_utf8_encoding(x) if pd.notna(x) else "")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"{encoding} 인코딩으로 읽기 실패: {e}")
                    continue
            
            # 모든 인코딩 실패시 빈 DataFrame 반환
            print("모든 인코딩 실패, 빈 DataFrame을 반환합니다.")
            return pd.DataFrame(columns=self.columns)
            
        except FileNotFoundError:
            return pd.DataFrame(columns=self.columns)
        except Exception as e:
            print(f"제품 데이터 로드 중 오류: {e}")
            return pd.DataFrame(columns=self.columns)
    
    def get_product_by_id(self, product_id):
        """특정 제품 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            product = df[df['product_id'] == product_id]
            if len(product) > 0:
                return product.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"제품 조회 중 오류: {e}")
            return None
    
    def get_product_by_code(self, product_code):
        """제품 코드로 제품 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            product = df[df['product_code'] == product_code]
            if len(product) > 0:
                return product.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"제품 조회 중 오류: {e}")
            return None
    
    def update_product(self, product_id, product_data):
        """제품 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if product_id not in df['product_id'].values:
                return False
            
            product_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 마진 재계산
            if 'cost_price_usd' in product_data and 'recommended_price_usd' in product_data:
                try:
                    cost = float(product_data['cost_price_usd'])
                    recommended = float(product_data['recommended_price_usd'])
                    if cost > 0:
                        margin = ((recommended - cost) / cost) * 100
                        product_data['margin_percent'] = round(margin, 2)
                except (ValueError, ZeroDivisionError):
                    product_data['margin_percent'] = 0
            
            for key, value in product_data.items():
                if key in df.columns:
                    df.loc[df['product_id'] == product_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"제품 업데이트 중 오류: {e}")
            return False
    
    def delete_product(self, product_id):
        """제품을 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            df = df[df['product_id'] != product_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"제품 삭제 중 오류: {e}")
            return False
    
    def get_filtered_products(self, category_filter=None, supplier_filter=None, search_term=None):
        """필터링된 제품 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if category_filter and category_filter != 'All':
                df = df[df['category1'] == category_filter]
            
            if supplier_filter and supplier_filter != 'All':
                df = df[df['supplier_name'] == supplier_filter]
            
            if search_term:
                mask = (
                    df['product_name'].str.contains(search_term, na=False, case=False) |
                    df['product_code'].str.contains(search_term, na=False, case=False) |
                    df['supplier_name'].str.contains(search_term, na=False, case=False)
                )
                df = df[mask]
            
            return df
        except Exception as e:
            print(f"제품 필터링 중 오류: {e}")
            return pd.DataFrame()
    
    def get_categories(self):
        """모든 카테고리1 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            categories = df['category1'].dropna().unique().tolist()
            return sorted(categories)
        except Exception as e:
            print(f"카테고리1 목록 조회 중 오류: {e}")
            return self.get_category1_options()  # 기본값 반환
    
    def get_suppliers(self):
        """모든 공급업체 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            suppliers = df['supplier_name'].dropna().unique().tolist()
            return sorted(suppliers)
        except Exception as e:
            print(f"공급업체 목록 조회 중 오류: {e}")
            return []
    
    def get_product_count_by_category(self):
        """카테고리별 제품 수를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df['category1'].value_counts().to_dict()
        except Exception as e:
            print(f"카테고리별 제품 수 조회 중 오류: {e}")
            return {}
    
    def get_product_count_by_supplier(self):
        """공급업체별 제품 수를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df['supplier_name'].value_counts().to_dict()
        except Exception as e:
            print(f"공급업체별 제품 수 조회 중 오류: {e}")
            return {}
    
    def get_price_summary(self):
        """가격 요약 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 숫자 컬럼들을 float로 변환
            df['cost_price_usd'] = pd.to_numeric(df['cost_price_usd'], errors='coerce').fillna(0)
            df['recommended_price_usd'] = pd.to_numeric(df['recommended_price_usd'], errors='coerce').fillna(0)
            
            summary = {
                'avg_cost_usd': df['cost_price_usd'].mean(),
                'avg_recommended_usd': df['recommended_price_usd'].mean(),
                'min_cost_usd': df['cost_price_usd'].min(),
                'max_cost_usd': df['cost_price_usd'].max(),
                'min_recommended_usd': df['recommended_price_usd'].min(),
                'max_recommended_usd': df['recommended_price_usd'].max()
            }
            
            return summary
        except Exception as e:
            print(f"가격 요약 조회 중 오류: {e}")
            return {}
    
    def bulk_add_products(self, products_data):
        """여러 제품을 한번에 추가합니다."""
        results = {'added': 0, 'updated': 0, 'errors': []}
        
        for product_data in products_data:
            try:
                # 제품 ID가 없으면 생성
                if 'product_id' not in product_data or not product_data['product_id']:
                    product_data['product_id'] = self.generate_product_id()
                
                # 기존 제품 확인
                existing_product = self.get_product_by_id(product_data['product_id'])
                
                if existing_product:
                    # 업데이트
                    if self.update_product(product_data['product_id'], product_data):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"제품 {product_data['product_id']} 업데이트 실패")
                else:
                    # 새로 추가
                    if self.add_product(product_data):
                        results['added'] += 1
                    else:
                        results['errors'].append(f"제품 {product_data.get('product_name', 'Unknown')} 추가 실패")
            
            except Exception as e:
                results['errors'].append(f"제품 처리 중 오류: {str(e)}")
        
        return results
    
    def get_template_dataframe(self):
        """제품 대량 등록용 템플릿 DataFrame을 반환합니다."""
        template_data = {
            'product_code': ['SAMPLE001'],
            'product_name': ['샘플 제품'],
            'product_name_english': ['Sample Product'],
            'product_name_vietnamese': ['Sản phẩm mẫu'],
            'category1': ['MB'],
            'category2': ['Valve'],
            'category3': ['ST'],
            'category4': ['S50C'],
            'category5': ['샘플'],
            'category6': [''],
            'supplier_name': ['샘플 공급업체'],
            'cost_price_usd': [100.0],
            'recommended_price_usd': [150.0],
            'margin_percent': [50.0],
            'hs_code': ['8542.32.0000'],
            'import_tax_percent': [8.0],
            'vat_percent': [10.0],
            'description': ['제품 설명'],
            'specifications': ['상세 사양'],
            'unit': ['개'],
            'minimum_order_qty': [1],
            'lead_time_days': [14],
            'status': ['활성']
        }
        return pd.DataFrame(template_data)
    
    def get_bulk_download_data(self, df):
        """대량 다운로드용 CSV 데이터를 반환합니다."""
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    def get_category1_options(self):
        """Category1 옵션 목록을 반환합니다."""
        return ['MB', 'HRC', 'HR', 'MB+HR', 'MTC', 'ROBOT', 'SPARE-HR', 'SPARE-MB', 'SPARE-ROBOT']
    
    def get_category2_options(self):
        """Category2 옵션 목록을 반환합니다."""
        return ['Valve', 'Block', 'Plate', 'Cylinder', 'Pump', 'Motor', 'Sensor', 'Controller']
    
    def get_category3_options(self):
        """Category3 옵션 목록을 반환합니다."""
        return ['ST', 'SP', 'HT', 'LT', 'Standard', 'Premium', 'Custom']
    
    def get_category4_options(self):
        """Category4 옵션 목록을 반환합니다."""
        return ['S50C', 'SUS304', 'SUS316', 'SKD61', 'P20', 'NAK80', 'HPM38']
    
    def get_category5_options(self):
        """Category5 옵션 목록을 반환합니다."""
        return ['Basic', 'Standard', 'Premium', 'Custom', 'Import', 'Export', 'Domestic', 'International']
    
    def get_category6_options(self):
        """Category6 옵션 목록을 반환합니다."""
        return ['Grade A', 'Grade B', 'Grade C', 'Heavy Duty', 'Light Duty', 'Professional', 'Commercial', 'Industrial']
