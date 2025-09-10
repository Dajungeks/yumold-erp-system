import pandas as pd
import os
from datetime import datetime, date
import re

class EmployeeManager:
    def __init__(self):
        self.data_file = 'data/employees.csv'
        self.ensure_data_file()
    
    def format_phone_number(self, phone):
        """연락처를 010-XXXX-XXXX 형식으로 포맷팅합니다."""
        if not phone:
            return ""
        
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', phone)
        
        # 11자리 숫자인 경우 포맷팅
        if len(digits) == 11 and digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) == 10 and digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) >= 3:
            # 길이에 따라 포맷팅
            if len(digits) <= 3:
                return digits
            elif len(digits) <= 7:
                return f"{digits[:3]}-{digits[3:]}"
            elif len(digits) <= 11:
                if digits.startswith('010'):
                    if len(digits) <= 7:
                        return f"{digits[:3]}-{digits[3:]}"
                    else:
                        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
                else:
                    return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return phone
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'employee_id', 'name', 'english_name', 'gender', 'birth_date',
                'nationality', 'residence_country', 'city', 'hire_date',
                'salary', 'salary_currency', 'contact', 'email', 'position', 'department',
                'driver_license', 'status', 'work_status', 'resignation_date', 'notes',
                'annual_leave_days', 'access_level', 'created_date', 'updated_date', 'input_date',
                'approval_level', 'max_approval_amount'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def generate_employee_id(self, hire_date):
        """입사일 기반으로 고유한 사번을 생성합니다. (YYMM + 순서번호 3자리)"""
        try:
            if isinstance(hire_date, str):
                hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
            elif isinstance(hire_date, datetime):
                hire_date = hire_date.date()
            
            # 기존 직원들의 사번 확인
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            except:
                df = pd.DataFrame()
            year_month = hire_date.strftime('%y%m')
            
            if len(df) > 0:
                # employee_id를 문자열로 변환하여 처리
                df['employee_id'] = df['employee_id'].astype(str)
                # 해당 년월의 기존 사번들 확인
                existing_ids = df[df['employee_id'].str.startswith(year_month)]['employee_id'].tolist()
                
                # 기존 번호들에서 마지막 3자리 숫자 추출하여 최대값 찾기
                max_num = 0
                for emp_id in existing_ids:
                    if len(emp_id) >= 7:  # YYMM + 3자리 숫자
                        try:
                            num = int(emp_id[-3:])
                            max_num = max(max_num, num)
                        except ValueError:
                            continue
                
                # 다음 번호는 최대값 + 1
                next_num = max_num + 1
            else:
                # 첫 번째 직원인 경우
                next_num = 1
            
            # 새로운 사번 생성 (YYMM + 3자리 순서번호)
            new_id = f"{year_month}{next_num:03d}"
            return new_id
            
        except Exception as e:
            print(f"사번 생성 중 오류: {e}")
            # 오류 발생 시 현재 시간 기준으로 생성
            return f"{datetime.now().strftime('%y%m')}001"
    
    def add_employee(self, employee_data):
        """새 직원을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # date 객체들을 문자열로 변환
            date_fields = ['birth_date', 'hire_date']
            for field in date_fields:
                if field in employee_data and employee_data[field] is not None:
                    if hasattr(employee_data[field], 'strftime'):
                        employee_data[field] = employee_data[field].strftime('%Y-%m-%d')
                    elif employee_data[field] == "":
                        employee_data[field] = '1990-01-01'  # 기본값 설정
                elif field == 'birth_date' and field not in employee_data:
                    employee_data[field] = '1990-01-01'  # birth_date가 없으면 기본값 설정
            
            # 사번 생성 (employee_id가 없는 경우에만)
            if 'employee_id' not in employee_data or not employee_data['employee_id']:
                hire_date_for_id = employee_data.get('hire_date')
                if isinstance(hire_date_for_id, str):
                    hire_date_for_id = datetime.strptime(hire_date_for_id, '%Y-%m-%d').date()
                elif hasattr(hire_date_for_id, 'date'):
                    hire_date_for_id = hire_date_for_id.date()
                employee_data['employee_id'] = self.generate_employee_id(hire_date_for_id)
            
            # 중복 확인 (같은 이름, 생년월일)
            if 'birth_date' in employee_data and 'birth_date' in df.columns:
                existing = df[
                    (df['name'] == employee_data['name']) & 
                    (df['birth_date'] == str(employee_data['birth_date']))
                ]
                if len(existing) > 0:
                    return False
            else:
                # birth_date가 없으면 이름으로만 중복 확인
                existing = df[df['name'] == employee_data['name']]
                if len(existing) > 0:
                    return False
            
            # 입력 날짜 추가
            employee_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            employee_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 연락처 자동 포맷팅
            if 'contact' in employee_data:
                employee_data['contact'] = self.format_phone_number(employee_data['contact'])
            
            # 기본값 설정
            if 'department' not in employee_data or not employee_data['department']:
                employee_data['department'] = '영업'
            if 'position' not in employee_data or not employee_data['position']:
                employee_data['position'] = '사원'
            if 'annual_leave_days' not in employee_data or not employee_data['annual_leave_days']:
                employee_data['annual_leave_days'] = 15  # 기본 연차 15일
            if 'access_level' not in employee_data or not employee_data['access_level']:
                employee_data['access_level'] = 'employee'  # 기본 권한은 employee
            
            df = pd.concat([df, pd.DataFrame([employee_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"직원 추가 중 오류: {e}")
            return False
    
    def get_all_employees(self):
        """모든 직원 정보를 DataFrame으로 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"직원 조회 중 오류: {e}")
            return pd.DataFrame()  # 빈 DataFrame 반환
    
    def get_all_employees_list(self):
        """모든 직원 정보를 리스트로 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            # 빈 DataFrame인 경우 빈 리스트 반환
            if df.empty:
                return []
            # DataFrame을 딕셔너리 리스트로 변환하여 반환
            return df.to_dict('records')
        except Exception as e:
            print(f"직원 조회 중 오류: {e}")
            return []  # 빈 리스트 반환
    
    def get_employee_by_id(self, employee_id):
        """특정 직원 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # employee_id를 문자열로 변환하여 비교
            df['employee_id'] = df['employee_id'].astype(str)
            employee_id = str(employee_id)
            
            employee = df[df['employee_id'] == employee_id]
            if len(employee) > 0:
                return employee.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"직원 조회 중 오류: {e}")
            return None
    
    def get_employee_name(self, employee_id):
        """직원 이름을 가져옵니다."""
        employee = self.get_employee_by_id(employee_id)
        return employee['name'] if employee else None
    
    def update_employee(self, employee_id, employee_data):
        """직원 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # employee_id를 문자열로 변환하여 비교
            df['employee_id'] = df['employee_id'].astype(str)
            employee_id = str(employee_id)
            
            # 직원 존재 확인
            if employee_id not in df['employee_id'].values:
                return False
            
            # 연락처 자동 포맷팅
            if 'contact' in employee_data:
                employee_data['contact'] = self.format_phone_number(employee_data['contact'])
            
            # 업데이트 날짜 추가
            employee_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 데이터 업데이트 (dtype 경고 해결)
            for key, value in employee_data.items():
                if key in df.columns:
                    # 숫자 컬럼의 경우 적절한 타입으로 변환
                    if key in ['salary'] and value is not None:
                        df.loc[df['employee_id'] == employee_id, key] = float(value)
                    else:
                        df.loc[df['employee_id'] == employee_id, key] = str(value) if value is not None else ""
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"직원 업데이트 중 오류: {e}")
            return False
    
    def delete_employee(self, employee_id):
        """직원을 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            df = df[df['employee_id'] != employee_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"직원 삭제 중 오류: {e}")
            return False
    
    def get_filtered_employees(self, status_filter=None, region_filter=None, search_term=None):
        """필터링된 직원 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 상태 필터
            if status_filter:
                df = df[df['status'] == status_filter]
            
            # 지역 필터
            if region_filter:
                if 'residence_country' in df.columns:
                    df = df[df['residence_country'] == region_filter]
                elif 'region' in df.columns:
                    df = df[df['region'] == region_filter]
            
            # 검색 필터
            if search_term:
                mask = (
                    df['name'].str.contains(search_term, na=False, case=False) |
                    df['english_name'].str.contains(search_term, na=False, case=False) |
                    df['employee_id'].str.contains(search_term, na=False, case=False)
                )
                df = df[mask]
            
            return df
        except Exception as e:
            print(f"직원 필터링 중 오류: {e}")
            return pd.DataFrame()
    
    def get_active_employee_count(self):
        """재직 중인 직원 수를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return len(df[df['status'] == 'active'])
        except Exception as e:
            print(f"재직 직원 수 조회 중 오류: {e}")
            return 0
    
    def get_employee_count_by_position(self):
        """직급별 직원 수를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            active_df = df[df['status'] == 'active']
            return active_df['position'].value_counts().to_dict()
        except Exception as e:
            print(f"직급별 직원 수 조회 중 오류: {e}")
            return {}
    
    def get_regions(self):
        """모든 거주국가 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            if 'residence_country' in df.columns:
                regions = df['residence_country'].dropna().unique().tolist()
                return sorted(regions)
            elif 'region' in df.columns:
                regions = df['region'].dropna().unique().tolist()
                return sorted(regions)
            else:
                return ['한국', '중국', '태국', '베트남', '인도네시아', '말레이시아']
        except Exception as e:
            print(f"지역 목록 조회 중 오류: {e}")
            return ['한국', '중국', '태국', '베트남', '인도네시아', '말레이시아']
    
    def get_cities_by_country(self, country):
        """국가별 도시 목록을 가져옵니다."""
        cities_data = {
            '한국': ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '수원', '화성', '창원', '안산', '고양', '용인', '성남', '부천', '남양주', '안양', '평택', '시흥', '파주', '의정부', '김포', '광명', '구리', '오산', '이천', '양주', '동두천', '과천', '춘천', '원주', '강릉', '동해', '태백', '속초', '삼척', '청주', '충주', '제천', '천안', '공주', '보령', '아산', '서산', '논산', '계룡', '당진', '전주', '군산', '익산', '정읍', '남원', '김제', '목포', '여수', '순천', '나주', '광양', '포항', '경주', '김천', '안동', '구미', '영주', '영천', '상주', '문경', '경산', '진주', '통영', '사천', '김해', '밀양', '거제', '양산', '제주', '서귀포'],
            '중국': ['베이징', '상하이', '광저우', '선전', '청두', '항저우', '난징', '우한', '시안', '충칭', '톈진', '다롄', '칭다오', '하얼빈', '장춘', '심양', '석가장', '타이위안', '후허하오터', '란저우', '시닝', '인촨', '우루무치', '쿤밍', '구이양', '난닝', '하이커우', '싼야', '라싸', '닝보', '원저우', '자싱', '후저우', '소흥', '진화', '취저우', '리수이', '타이저우', '창저우', '난퉁', '리엔윈강', '화이안', '양저우', '전장', '쑤저우', '무시', '쉬저우', '푸양', '먼청', '옌청', '당산', '바오딩', '창더', '이양', '헝양', '주저우', '샹탄', '웨이양', '창사', '베이하이', '류저우', '구이린', '우저우', '푸천', '취안저우', '장저우', '샤먼', '룽옌', '산밍', '난핑', '닝더', '푸저우'],
            '태국': ['방콕', '치앙마이', '파타야', '푸켓', '아유타야', '촌부리', '라용', '사뭇프라칸', '사뭇사콘', '나콘랏차시마', '우돈타니', '콘켄', '우본랏차타니', '나콘사완', '핏사눌록', '캄팽펫', '수코타이', '탁', '람팡', '치앙라이', '매홍손', '난', '파야오', '프레', '수린', '시사켓', '야소톤', '로이엣', '마하사라캄', '칼라신', '논칼라이', '논타부리', '파툼타니', '민부리', '나콘나욕', '프라친부리', '사라부리', '싱부리', '앙통', '수팡부리', '차이낫', '로부리', '펫차부리', '프라추압키리칸', '트랏', '짠타부리', '랏차부리', '나콘시탐마랏', '크라비', '퐁가', '수랏타니', '촘폰', '라농', '송클라', '사툰', '팟탈룽', '나라티왓', '얄라', '파타니'],
            '베트남': ['하노이', '호치민', '다낭', '나트랑', '후에', '비엔호아', '칸토', '부온마투옷', '롱쑤옌', '하이퐁', '박닌', '박장', '꽝닌', '하롱', '빈롱', '랑손', '꽝응아이', '꽝빈', '타인호아', '하띤', '응에안', '깐호아', '빈투언', '응아이', '빈딘', '푸옌', '다클락', '라이쩌우', '손라', '디엔비엔', '호아빈', '퐁토', '투엔꽝', '꽝트리', '꽝남', '꼰뚬', '안장', '키엔장', '빈푹', '동탑', '롱안', '띠엔장', '벤째', '쩌빈', '남딘', '타이빈', '닌빈', '하남', '예바이', '까마우', '박리에우', '소이짱', '허우장', '지엔호아', '밤럽', '몽깨', '까오방', '방주', '홍야', '흠름', '롱꽝', '리엔', '바리아', '붕따우', '냐짱', '호이안', '하몽', '띠엔하', '룽비엔', '하이즈엉', '홍옌', '흥옌', '타이응웬', '투득'],
            '인도네시아': ['자카르타', '수라바야', '반둑', '메단', '스마랑', '마카사르', '팔렘방', '뎅파사르', '요그야카르타', '바탐', '탕그랑', '보고르', '데포크', '베카시', '솔로', '말랑', '사마린다', '반자르마신', '폰티아낙', '쿠팡', '암본', '자야푸라', '매나도', '팔루', '켄다리', '고론탈로', '테르나테', '소롱', '마타람', '신가라자', '프로볼링고', '마디운', '케디리', '블리타르', '파수루안', '모조케르토', '방일', '루마장', '본도워소', '투반', '시두아르조', '그레식', '라몬간', '파메카산', '삼팍', '방카란', '응아위', '보조네고로', '마게탄', '응안주크', '풀로워조', '트렝갈렉', '툴룽아궁'],
            '말레이시아': ['쿠알라룸푸르', '조호르바루', '페낭', '이포', '쿠칭', '코타키나발루', '샤알람', '페트로나스', '클랑', '세렘반', '쿠안탄', '쿠알라테렝가누', '알로르스타', '카논', '말라카', '미리', '산다칸', '타와우', '라하드다투', '세파', '크루아크', '스리아만', '사리케이', '시부', '비투', '무크', '타이핑', '텔룩인탄', '쿠알라칸사르', '라율', '바투가자', '포트딕슨', '님핀', '마당', '베르하랑', '롬핀', '젬폴', '베라', '펠리스', '술탄압둘할림', '시티아완', '카장', '암팡', '세팡', '발라카르', '치라스', '페듈리', '렌투', '세펜틴', '갤런', '부킷잘릴']
        }
        return cities_data.get(country, [])
    
    def get_position_options(self):
        """직급 옵션을 가져옵니다."""
        return ['사원', '주임', '대리', '과장', '차장', '부장', '이사', '상무', '전무', '대표']
    
    def bulk_add_employees(self, employees_data):
        """여러 직원을 한번에 추가합니다."""
        results = {'added': 0, 'updated': 0, 'errors': []}
        
        for employee_data in employees_data:
            try:
                # 사번이 없으면 생성
                if 'employee_id' not in employee_data or not employee_data['employee_id']:
                    employee_data['employee_id'] = self.generate_employee_id(employee_data.get('hire_date', date.today()))
                
                # 기존 직원 확인
                existing_employee = self.get_employee_by_id(employee_data['employee_id'])
                
                if existing_employee:
                    # 업데이트
                    if self.update_employee(employee_data['employee_id'], employee_data):
                        results['updated'] += 1
                    else:
                        results['errors'].append(f"직원 {employee_data['employee_id']} 업데이트 실패")
                else:
                    # 새로 추가
                    if self.add_employee(employee_data):
                        results['added'] += 1
                    else:
                        results['errors'].append(f"직원 {employee_data.get('name', 'Unknown')} 추가 실패")
            
            except Exception as e:
                results['errors'].append(f"직원 처리 중 오류: {str(e)}")
        
        return results
    
    def update_annual_leave_days(self, employee_id, annual_days):
        """직원의 연차 일수를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            employee_id = str(employee_id)
            
            # 직원 확인
            if employee_id not in df['employee_id'].astype(str).values:
                return False
            
            # 연차 일수 업데이트
            df.loc[df['employee_id'].astype(str) == employee_id, 'annual_leave_days'] = int(annual_days)
            df.loc[df['employee_id'].astype(str) == employee_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"연차 일수 업데이트 중 오류: {e}")
            return False
    
    def get_employee_annual_leave_days(self, employee_id):
        """직원의 연차 일수를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            employee_id = str(employee_id)
            
            employee = df[df['employee_id'].astype(str) == employee_id]
            if len(employee) > 0:
                annual_days = employee.iloc[0].get('annual_leave_days', 15)
                return int(annual_days) if pd.notna(annual_days) else 15
            return 15
        except Exception as e:
            print(f"연차 일수 조회 중 오류: {e}")
            return 15
    
    def delete_employee(self, employee_id):
        """직원을 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            employee_id = str(employee_id)
            
            # 삭제할 직원이 존재하는지 확인
            employee_exists = len(df[df['employee_id'].astype(str) == employee_id]) > 0
            if not employee_exists:
                return False, "해당 사번의 직원을 찾을 수 없습니다."
            
            # 삭제할 직원 정보 저장 (로깅용)
            employee_info = df[df['employee_id'].astype(str) == employee_id].iloc[0]
            employee_name = employee_info.get('name', '알 수 없음')
            
            # 직원 삭제
            df_filtered = df[df['employee_id'].astype(str) != employee_id]
            
            # 파일에 저장
            df_filtered.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, f"직원 '{employee_name}' (사번: {employee_id})이 성공적으로 삭제되었습니다."
            
        except Exception as e:
            return False, f"직원 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def get_employee_by_id(self, employee_id):
        """사번으로 직원 정보를 조회합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            employee_id = str(employee_id)
            
            employee = df[df['employee_id'].astype(str) == employee_id]
            if len(employee) > 0:
                return employee.iloc[0].to_dict()
            else:
                return None
        except Exception as e:
            print(f"직원 조회 중 오류: {e}")
            return None
