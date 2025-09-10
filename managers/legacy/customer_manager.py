import pandas as pd
import os
from datetime import datetime
from geographic_database import GeographicDatabase

class CustomerManager:
    def __init__(self):
        self.data_file = 'data/customers.csv'
        self.geo_db = GeographicDatabase()
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'customer_id', 'company_name', 'contact_person', 'position', 
                'contact_phone', 'contact_email', 'address', 'country', 'city', 
                'business_type', 'company_size', 'tax_id', 'annual_revenue',
                'customer_grade', 'payment_terms', 'website', 'fax', 
                'secondary_contact', 'main_products', 'notes', 'status', 
                'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        else:
            # 기존 파일이 있을 때 새로운 데이터 구조 확인 및 업데이트
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8-sig')
                
                # 실제 고객 데이터 구조에 맞는 모든 컬럼 정의
                all_columns = [
                    'customer_id', 'company_name', 'contact_person', 'contact_phone', 
                    'contact_email', 'address', 'detail_address', 'country', 'city', 'business_type',
                    'tax_id', 'notes', 'status', 'input_date', 'updated_date', 'position',
                    'company_size', 'annual_revenue', 'customer_grade', 'payment_terms',
                    'website', 'fax', 'secondary_contact', 'main_products', 
                    'special_requirements', 'kam_manager', 'relationship_level',
                    'communication_frequency', 'last_meeting_date', 'potential_value',
                    'decision_maker', 'decision_process', 'competitive_status',
                    'sales_strategy', 'cross_sell_opportunity', 'growth_potential', 'risk_factors'
                ]
                
                # 누락된 컬럼 추가
                for col in all_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # 표준 컬럼 순서로 재정렬
                df = df.reindex(columns=all_columns)
                df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
                
            except Exception as e:
                print(f"고객 데이터 마이그레이션 중 오류: {e}")
                # 실제 고객 데이터 파일이 이미 올바른 구조를 가지고 있으므로 그대로 사용
    
    def generate_customer_id(self):
        """고객 ID를 생성합니다."""
        try:
            df = self.get_all_customers()
            if len(df) == 0:
                return 'C001'
            
            # 기존 ID에서 숫자 부분 추출하여 다음 번호 생성
            existing_ids = df['customer_id'].tolist()
            numbers = []
            for cid in existing_ids:
                if cid.startswith('C') and cid[1:].isdigit():
                    numbers.append(int(cid[1:]))
            
            next_num = max(numbers) + 1 if numbers else 1
            return f'C{next_num:03d}'
        except Exception as e:
            print(f"고객 ID 생성 중 오류: {e}")
            return f'C{datetime.now().strftime("%m%d%H%M")}'
    
    def add_customer(self, customer_data):
        """새 고객을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 중복 확인 (회사명으로 확인)
            if customer_data['company_name'] in df['company_name'].values:
                return False
            
            # 고객 ID가 없으면 생성
            if 'customer_id' not in customer_data or not customer_data['customer_id']:
                customer_data['customer_id'] = self.generate_customer_id()
            
            # 기본값 설정 (영어로 표준화)
            status = customer_data.get('status', 'active')
            # 한국어 status를 영어로 변환
            status_mapping = {
                '활성': 'active',
                '비활성': 'inactive',
                '보류': 'pending',
                '삭제': 'deleted'
            }
            customer_data['status'] = status_mapping.get(status, status)
            customer_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            customer_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([customer_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"고객 추가 중 오류: {e}")
            return False
    
    def get_all_customers(self):
        """모든 고객 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df  # DataFrame으로 반환
        except Exception as e:
            print(f"고객 조회 중 오류: {e}")
            return pd.DataFrame()  # 빈 DataFrame 반환
    
    def get_customer_by_id(self, customer_id):
        """특정 고객 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            customer = df[df['customer_id'] == customer_id]
            if len(customer) > 0:
                return customer.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"고객 조회 중 오류: {e}")
            return None
    
    def update_customer(self, customer_id, customer_data):
        """고객 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if customer_id not in df['customer_id'].values:
                return False
            
            customer_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for key, value in customer_data.items():
                if key in df.columns:
                    df.loc[df['customer_id'] == customer_id, key] = value
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"고객 업데이트 중 오류: {e}")
            return False
    
    def delete_customer(self, customer_id):
        """고객을 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            df = df[df['customer_id'] != customer_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"고객 삭제 중 오류: {e}")
            return False
    
    def get_filtered_customers(self, country_filter=None, business_type_filter=None, search_term=None):
        """필터링된 고객 목록을 가져옵니다."""
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
                    df['customer_id'].str.contains(search_term, na=False, case=False)
                )
                df = df[mask]
            
            return df
        except Exception as e:
            print(f"고객 필터링 중 오류: {e}")
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
    
    def get_cities_by_country(self, country):
        """국가별 도시 목록을 가져옵니다."""
        cities_data = {
            '한국': ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '수원', '화성', '창원', '안산', '고양', '용인', '성남', '부천', '남양주', '안양', '평택', '시흥', '파주', '의정부', '김포', '광명', '구리', '오산', '이천', '양주', '동두천', '과천', '춘천', '원주', '강릉', '동해', '태백', '속초', '삼척', '청주', '충주', '제천', '천안', '공주', '보령', '아산', '서산', '논산', '계룡', '당진', '전주', '군산', '익산', '정읍', '남원', '김제', '목포', '여수', '순천', '나주', '광양', '포항', '경주', '김천', '안동', '구미', '영주', '영천', '상주', '문경', '경산', '진주', '통영', '사천', '김해', '밀양', '거제', '양산', '제주', '서귀포'],
            '중국': ['베이징', '상하이', '광저우', '선전', '청두', '항저우', '난징', '우한', '시안', '충칭', '톈진', '다롄', '칭다오', '하얼빈', '장춘', '심양', '석가장', '타이위안', '후허하오터', '란저우', '시닝', '인촨', '우루무치', '쿤밍', '구이양', '난닝', '하이커우', '싼야', '라싸', '닝보', '원저우', '자싱', '후저우', '소흥', '진화', '취저우', '리수이', '타이저우', '창저우', '난퉁', '리엔윈강', '화이안', '양저우', '전장', '쑤저우', '무시', '쉬저우', '푸양', '먼청'],
            '태국': ['방콕', '치앙마이', '파타야', '푸켓', '아유타야', '촌부리', '라용', '사뭇프라칸', '사뭇사콘', '나콘랏차시마', '우돈타니', '콘켄', '우본랏차타니', '나콘사완', '핏사눌록', '캄팽펫', '수코타이', '탁', '람팡', '치앙라이', '매홍손', '난', '파야오', '프레', '수린', '시사켓', '야소톤', '로이엣', '마하사라캄', '칼라신', '논칼라이', '논타부리', '파툼타니', '민부리', '나콘나욕', '프라친부리', '사라부리', '싱부리', '앙통', '수팡부리', '차이낫', '로부리', '펫차부리', '프라추압키리칸', '트랏', '짠타부리', '랏차부리', '나콘시탐마랏'],
            '베트남': ['하노이', '호치민', '다낭', '나트랑', '후에', '비엔호아', '칸토', '부온마투옷', '롱쑤옌', '하이퐁', '박닌', '박장', '꽝닌', '하롱', '빈롱', '랑손', '꽝응아이', '꽝빈', '타인호아', '하띤', '응에안', '깐호아', '빈투언', '응아이', '빈딘', '푸옌', '다클락', '라이쩌우', '손라', '디엔비엔', '호아빈', '퐁토', '투엔꽝', '꽝트리', '꽝남', '꼰뚬', '안장', '키엔장', '빈푹', '동탑', '롱안', '띠엔장', '벤째', '쩌빈', '남딘', '타이빈', '닌빈', '하남', '예바이', '까마우', '박리에우', '소이짱', '허우장', '지엔호아', '밤럽', '몽깨', '까오방', '방주', '홍야', '흠름', '롱꽝', '리엔', '바리아', '붕따우', '냐짱', '호이안', '하몽', '띠엔하', '룽비엔', '하이즈엉', '홍옌', '흥옌', '타이응웬', '투득'],
            '인도네시아': ['자카르타', '수라바야', '반둥', '메단', '스마랑', '마카사르', '팔렘방', '뎅파사르', '요그야카르타', '바탐', '탕그랑', '보고르', '데포크', '베카시', '솔로', '말랑', '사마린다', '반자르마신', '폰티아낙', '쿠팡', '암본', '자야푸라', '매나도', '팔루', '켄다리', '고론탈로', '테르나테', '소롱', '마타람', '신가라자', '프로볼링고', '마디운', '케디리', '블리타르', '파수루안', '모조케르토', '방일', '루마장', '본도워소', '투반', '시두아르조', '그레식', '라몬간', '파메카산', '삼팍', '방카란', '응아위', '보조네고로'],
            '말레이시아': ['쿠알라룸푸르', '조호르바루', '페낭', '이포', '쿠칭', '코타키나발루', '샤알람', '페트로나스', '클랑', '세렘반', '쿠안탄', '쿠알라테렝가누', '알로르스타', '카논', '말라카', '미리', '산다칸', '타와우', '라하드다투', '세파', '크루아크', '스리아만', '사리케이', '시부', '비투', '무크', '타이핑', '텔룩인탄', '쿠알라칸사르', '라율', '바투가자', '포트딕슨', '님핀', '마당', '베르하랑', '롬핀', '젬폴', '베라', '펠리스', '술탄압둘할림', '시티아완', '카장', '암팡', '세팡', '발라카르', '치라스', '페듈리', '렌투', '세펜틴']
        }
        return cities_data.get(country, [])
    
    def get_customer_statistics(self):
        """고객 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            stats = {
                'total_customers': len(df),
                'active_customers': len(df[df['status'] == '활성']),
                'countries': df['country'].nunique(),
                'business_types': df['business_type'].nunique(),
                'country_distribution': df['country'].value_counts().to_dict(),
                'business_type_distribution': df['business_type'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"고객 통계 조회 중 오류: {e}")
            return {}
    
    def bulk_add_customers(self, customers_data):
        """여러 고객을 한번에 추가합니다."""
        results = {'added': 0, 'updated': 0, 'errors': []}
        
        for customer_data in customers_data:
            try:
                # 고객 ID가 없으면 생성
                if 'customer_id' not in customer_data or not customer_data['customer_id']:
                    customer_data['customer_id'] = self.generate_customer_id()
                
                # 기존 고객 확인
                existing_customer = self.get_customer_by_id(customer_data['customer_id'])
                
                if existing_customer:
                    # 업데이트
                    if self.update_customer(customer_data['customer_id'], customer_data):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"고객 {customer_data['customer_id']} 업데이트 실패")
                else:
                    # 새로 추가
                    if self.add_customer(customer_data):
                        results['added'] += 1
                    else:
                        results['errors'].append(f"고객 {customer_data.get('company_name', 'Unknown')} 추가 실패")
            
            except Exception as e:
                results['errors'].append(f"고객 처리 중 오류: {str(e)}")
        
        return results
