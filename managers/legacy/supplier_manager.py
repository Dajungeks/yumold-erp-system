import pandas as pd
import os
from datetime import datetime

class SupplierManager:
    def __init__(self):
        self.data_file = 'data/suppliers.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'supplier_id', 'company_name', 'contact_person', 'contact_phone',
                'contact_email', 'address', 'country', 'city', 'business_type',
                'tax_id', 'bank_info', 'payment_terms', 'lead_time_days',
                'minimum_order_amount', 'currency', 'rating', 'notes',
                'status', 'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_supplier_id(self):
        """공급업체 ID를 생성합니다."""
        try:
            df = self.get_all_suppliers()
            if len(df) == 0:
                return 'SUP001'
            
            # 기존 ID에서 숫자 부분 추출하여 다음 번호 생성
            existing_ids = df['supplier_id'].tolist()
            numbers = []
            for sid in existing_ids:
                if sid.startswith('SUP') and sid[3:].isdigit():
                    numbers.append(int(sid[3:]))
            
            next_num = max(numbers) + 1 if numbers else 1
            return f'SUP{next_num:03d}'
        except Exception as e:
            print(f"공급업체 ID 생성 중 오류: {e}")
            return f'S{datetime.now().strftime("%m%d%H%M")}'
    
    def add_supplier(self, supplier_data):
        """새 공급업체를 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 중복 확인 (회사명으로 확인)
            if supplier_data['company_name'] in df['company_name'].values:
                return False
            
            # 공급업체 ID가 없으면 생성
            if 'supplier_id' not in supplier_data or not supplier_data['supplier_id']:
                supplier_data['supplier_id'] = self.generate_supplier_id()
            
            # 기본값 설정
            supplier_data['status'] = supplier_data.get('status', '활성')
            supplier_data['rating'] = supplier_data.get('rating', 3.0)
            supplier_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            supplier_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([supplier_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"공급업체 추가 중 오류: {e}")
            return False
    
    def get_all_suppliers(self):
        """모든 공급업체 정보를 가져옵니다."""
        try:
            return pd.read_csv(self.data_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"공급업체 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_supplier_by_id(self, supplier_id):
        """특정 공급업체 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            supplier = df[df['supplier_id'] == supplier_id]
            if len(supplier) > 0:
                return supplier.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"공급업체 조회 중 오류: {e}")
            return None
    
    def update_supplier(self, supplier_id, supplier_data):
        """공급업체 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if supplier_id not in df['supplier_id'].values:
                return False
            
            supplier_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in supplier_data.items():
                if key in df.columns:
                    df.loc[df['supplier_id'] == supplier_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"공급업체 업데이트 중 오류: {e}")
            return False
    
    def delete_supplier(self, supplier_id):
        """공급업체를 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            df = df[df['supplier_id'] != supplier_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"공급업체 삭제 중 오류: {e}")
            return False
    
    def get_filtered_suppliers(self, country_filter=None, business_type_filter=None, search_term=None):
        """필터링된 공급업체 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if country_filter and country_filter != 'All':
                df = df[df['country'] == country_filter]
            
            if business_type_filter and business_type_filter != 'All':
                df = df[df['business_type'] == business_type_filter]
            
            if search_term:
                mask = (
                    df['company_name'].str.contains(search_term, na=False, case=False) |
                    df['contact_person'].str.contains(search_term, na=False, case=False) |
                    df['supplier_id'].str.contains(search_term, na=False, case=False)
                )
                df = df[mask]
            
            return df
        except Exception as e:
            print(f"공급업체 필터링 중 오류: {e}")
            return pd.DataFrame()
    
    def get_countries(self):
        """모든 국가 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            countries = df['country'].dropna().unique().tolist()
            return sorted(countries)
        except Exception as e:
            print(f"국가 목록 조회 중 오류: {e}")
            return []
    
    def get_business_types(self):
        """모든 사업 유형 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            business_types = df['business_type'].dropna().unique().tolist()
            return sorted(business_types)
        except Exception as e:
            print(f"사업 유형 목록 조회 중 오류: {e}")
            return []
    
    def get_supplier_statistics(self):
        """공급업체 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # rating 컬럼이 없으면 추가
            if 'rating' not in df.columns:
                df['rating'] = 5.0
                df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            # 평점을 숫자로 변환
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(5.0)
            
            stats = {
                'total_suppliers': len(df),
                'active_suppliers': len(df[df['status'] == '활성']),
                'countries': df['country'].nunique(),
                'business_types': df['business_type'].nunique(),
                'average_rating': df['rating'].mean(),
                'country_distribution': df['country'].value_counts().to_dict(),
                'business_type_distribution': df['business_type'].value_counts().to_dict(),
                'rating_distribution': df['rating'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"공급업체 통계 조회 중 오류: {e}")
            return {
                'total_suppliers': 0,
                'active_suppliers': 0,
                'countries': 0,
                'business_types': 0,
                'average_rating': 0,
                'country_distribution': {},
                'business_type_distribution': {},
                'rating_distribution': {}
            }
    
    def get_cities_by_country(self, country):
        """국가별 도시 목록을 가져옵니다."""
        try:
            from geographic_database import GeographicDatabase
            geo_db = GeographicDatabase()
            return geo_db.get_cities_by_country(country)
        except ImportError:
            # 기본 도시 목록 반환
            cities_map = {
                "한국": ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "수원", "창원", "고양", "용인", "성남", "청주", "전주", "안산", "천안", "남양주", "화성", "평택", "의정부"],
                "중국": ["베이징", "상하이", "광저우", "선전", "충칭", "톈진", "시안", "칭다오", "다롄", "난징", "항저우", "우한", "청두", "선양", "하얼빈", "지난", "창춘", "닝보", "푸저우", "샤먼"],
                "태국": ["방콕", "치앙마이", "파타야", "푸켓", "핫야이", "나콘라차시마", "우본라차타니", "우돈타니", "콘켄", "수랏타니", "촌부리", "사뭇프라칸", "라용", "논타부리", "나콘시탐마랏", "사무트사콘", "로펴부리", "프라친부리", "싱부리", "펫차부리"],
                "베트남": ["호치민시", "하노이", "다낭", "하이퐁", "껀터", "박닌", "빈즈엉", "동나이", "롱안", "빈롱", "띠엔장", "안장", "카마우", "빈푸옥", "하띤", "응에안", "투아티엔후에", "꽝남", "빈딘", "푸옌"],
                "인도네시아": ["자카르타", "수라바야", "반둥", "메단", "스마랑", "탄게랑", "데포크", "팔렘방", "마카사르", "보고르", "바탐", "페칸바루", "반다르람푸응", "파당", "말랑", "사마린다", "타시크말라야", "반자르마신", "자야푸라", "수라카르타"],
                "말레이시아": ["쿠알라룸푸르", "조호르바루", "페낭", "이포", "샤알람", "쿠칭", "코타키나발루", "클랑", "말라카", "페탈링자야", "쿠안탄", "수방자야", "세렘반", "산다칸", "테렝가누", "앨러스타", "시부", "쿠알라테렝가누", "카지아", "바투파핫"]
            }
            return cities_map.get(country, [])
    
    def bulk_add_suppliers(self, suppliers_data):
        """여러 공급업체를 한번에 추가합니다."""
        results = {'added': 0, 'updated': 0, 'errors': []}
        
        for supplier_data in suppliers_data:
            try:
                # 공급업체 ID가 없으면 생성
                if 'supplier_id' not in supplier_data or not supplier_data['supplier_id']:
                    supplier_data['supplier_id'] = self.generate_supplier_id()
                
                # 기존 공급업체 확인
                existing_supplier = self.get_supplier_by_id(supplier_data['supplier_id'])
                
                if existing_supplier:
                    # 업데이트
                    if self.update_supplier(supplier_data['supplier_id'], supplier_data):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"공급업체 {supplier_data['supplier_id']} 업데이트 실패")
                else:
                    # 새로 추가
                    if self.add_supplier(supplier_data):
                        results['added'] += 1
                    else:
                        results['errors'].append(f"공급업체 {supplier_data.get('company_name', 'Unknown')} 추가 실패")
            
            except Exception as e:
                results['errors'].append(f"공급업체 처리 중 오류: {str(e)}")
        
        return results
