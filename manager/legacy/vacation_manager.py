import pandas as pd
import os
from datetime import datetime, date

class VacationManager:
    def __init__(self):
        self.data_file = 'data/vacations.csv'
        self.personal_status_file = 'data/personal_status.csv'
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        
        # 휴가 데이터 파일
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'vacation_id', 'employee_id', 'employee_name', 'vacation_type',
                'start_date', 'end_date', 'days_count', 'reason', 'status',
                'request_date', 'approved_by', 'approved_date', 'rejection_reason',
                'input_date', 'updated_date'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        
        # 개인 상태 데이터 파일
        if not os.path.exists(self.personal_status_file):
            df = pd.DataFrame(columns=[
                'status_id', 'employee_id', 'employee_name', 'status_type',
                'start_date', 'end_date', 'reason', 'current_status',
                'request_date', 'approved_by', 'approved_date',
                'input_date', 'updated_date'
            ])
            df.to_csv(self.personal_status_file, index=False, encoding='utf-8-sig')
    
    def add_vacation_request(self, vacation_data):
        """휴가 신청을 추가합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 휴가 ID 생성
            if 'vacation_id' not in vacation_data or not vacation_data['vacation_id']:
                vacation_data['vacation_id'] = f"VAC{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기본값 설정
            vacation_data['status'] = vacation_data.get('status', 'pending')
            vacation_data['request_date'] = vacation_data.get('request_date', datetime.now().strftime('%Y-%m-%d'))
            vacation_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            vacation_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 휴가 일수 계산
            if 'start_date' in vacation_data and 'end_date' in vacation_data:
                start = datetime.strptime(vacation_data['start_date'], '%Y-%m-%d').date()
                end = datetime.strptime(vacation_data['end_date'], '%Y-%m-%d').date()
                vacation_data['days_count'] = (end - start).days + 1
            
            df = pd.concat([df, pd.DataFrame([vacation_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"휴가 신청 추가 중 오류: {e}")
            return False
    
    def get_all_vacations(self):
        """모든 휴가 데이터를 가져옵니다."""
        try:
            return pd.read_csv(self.data_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"휴가 데이터 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_vacations_by_employee(self, employee_id):
        """특정 직원의 휴가 데이터를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['employee_id'] == employee_id]
        except Exception as e:
            print(f"직원별 휴가 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_vacation_summary(self, employee_id, year=None):
        """직원의 휴가 요약을 가져옵니다."""
        try:
            if year is None:
                year = datetime.now().year
            
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 해당 연도의 승인된 휴가만 필터링
            # 상태값 매핑 (기존 한글 데이터와 새 영어 데이터 모두 지원)
            def map_status(status):
                mapping = {'대기': 'pending', '승인': 'approved', '거부': 'rejected'}
                return mapping.get(status, status)
            
            df['mapped_status'] = df['status'].apply(map_status)
            
            employee_vacations = df[
                (df['employee_id'] == employee_id) & 
                (df['mapped_status'] == 'approved') &
                (pd.to_datetime(df['start_date']).dt.year == year)
            ]
            
            # days_count를 숫자형으로 변환하여 합계 계산
            if len(employee_vacations) > 0:
                used_days = pd.to_numeric(employee_vacations['days_count'], errors='coerce').fillna(0).sum()
            else:
                used_days = 0
            
            # 직원별 연차 일수 가져오기
            from employee_manager import EmployeeManager
            emp_manager = EmployeeManager()
            annual_days = emp_manager.get_employee_annual_leave_days(employee_id)
            
            remaining_days = max(0, annual_days - used_days)
            
            return {
                'annual_vacation_days': annual_days,
                'used_vacation_days': used_days,
                'remaining_vacation_days': remaining_days,
                'total_requests': len(df[df['employee_id'] == employee_id]),
                'approved_requests': len(df[(df['employee_id'] == employee_id) & (df['mapped_status'] == 'approved')]),
                'pending_requests': len(df[(df['employee_id'] == employee_id) & (df['mapped_status'] == 'pending')])
            }
        except Exception as e:
            print(f"휴가 요약 조회 중 오류: {e}")
            return {}
    
    def approve_vacation(self, vacation_id, approved_by):
        """휴가를 승인합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if vacation_id not in df['vacation_id'].values:
                return False
            
            df.loc[df['vacation_id'] == vacation_id, 'status'] = '승인'
            df.loc[df['vacation_id'] == vacation_id, 'approved_by'] = approved_by
            df.loc[df['vacation_id'] == vacation_id, 'approved_date'] = datetime.now().strftime('%Y-%m-%d')
            df.loc[df['vacation_id'] == vacation_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"휴가 승인 중 오류: {e}")
            return False
    
    def reject_vacation(self, vacation_id, rejection_reason):
        """휴가를 거부합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if vacation_id not in df['vacation_id'].values:
                return False
            
            df.loc[df['vacation_id'] == vacation_id, 'status'] = '거부'
            df.loc[df['vacation_id'] == vacation_id, 'rejection_reason'] = rejection_reason
            df.loc[df['vacation_id'] == vacation_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"휴가 거부 중 오류: {e}")
            return False
    
    def approve_vacation_request(self, vacation_data):
        """휴가 승인 시 휴가 데이터를 업데이트합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 승인 데이터를 휴가 테이블에 추가 또는 업데이트
            vacation_id = vacation_data.get('vacation_id')
            employee_id = vacation_data.get('employee_id')
            
            if vacation_id:
                # 기존 휴가 요청 업데이트
                if vacation_id in df['vacation_id'].values:
                    df.loc[df['vacation_id'] == vacation_id, 'status'] = '승인'
                    df.loc[df['vacation_id'] == vacation_id, 'approved_date'] = vacation_data.get('approval_date', datetime.now().strftime('%Y-%m-%d'))
                    df.loc[df['vacation_id'] == vacation_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 새로운 휴가 데이터 추가
                    vacation_data['status'] = '승인'
                    vacation_data['approved_date'] = vacation_data.get('approval_date', datetime.now().strftime('%Y-%m-%d'))
                    vacation_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    vacation_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    df = pd.concat([df, pd.DataFrame([vacation_data])], ignore_index=True)
            else:
                # 새 휴가 ID 생성하여 추가
                vacation_data['vacation_id'] = f"VAC{datetime.now().strftime('%Y%m%d%H%M%S')}"
                vacation_data['status'] = '승인'
                vacation_data['approved_date'] = vacation_data.get('approval_date', datetime.now().strftime('%Y-%m-%d'))
                vacation_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                vacation_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                df = pd.concat([df, pd.DataFrame([vacation_data])], ignore_index=True)
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
            
        except Exception as e:
            print(f"휴가 승인 처리 중 오류: {e}")
            return False
    
    def add_personal_status(self, status_data):
        """개인 상태 변경을 추가합니다."""
        try:
            df = pd.read_csv(self.personal_status_file, encoding='utf-8-sig')
            
            # 상태 ID 생성
            if 'status_id' not in status_data or not status_data['status_id']:
                status_data['status_id'] = f"STS{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기본값 설정
            status_data['current_status'] = status_data.get('current_status', '활성')
            status_data['request_date'] = status_data.get('request_date', datetime.now().strftime('%Y-%m-%d'))
            status_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([status_data])], ignore_index=True)
            df.to_csv(self.personal_status_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"개인 상태 추가 중 오류: {e}")
            return False
    
    def get_personal_status_by_employee(self, employee_id):
        """특정 직원의 개인 상태를 가져옵니다."""
        try:
            df = pd.read_csv(self.personal_status_file, encoding='utf-8-sig')
            return df[df['employee_id'] == employee_id].sort_values('input_date', ascending=False)
        except Exception as e:
            print(f"개인 상태 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_current_status(self, employee_id):
        """직원의 현재 상태를 가져옵니다."""
        try:
            df = pd.read_csv(self.personal_status_file, encoding='utf-8-sig')
            employee_status = df[df['employee_id'] == employee_id].sort_values('input_date', ascending=False)
            
            if len(employee_status) > 0:
                today = datetime.now().date()
                
                # 현재 유효한 상태 찾기
                for _, status in employee_status.iterrows():
                    start_date = datetime.strptime(status['start_date'], '%Y-%m-%d').date()
                    end_date = datetime.strptime(status['end_date'], '%Y-%m-%d').date() if status['end_date'] else today
                    
                    if start_date <= today <= end_date:
                        return status.to_dict()
                
                # 유효한 상태가 없으면 최근 상태 반환
                return employee_status.iloc[0].to_dict()
            
            return {'status_type': '재직', 'reason': '정상 근무'}
        except Exception as e:
            print(f"현재 상태 조회 중 오류: {e}")
            return {'status_type': '재직', 'reason': '정상 근무'}
    
    def get_all_vacation_requests(self):
        """모든 휴가 요청을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"휴가 요청 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_vacation_statistics(self):
        """휴가 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return {}
            
            current_year = datetime.now().year
            current_year_vacations = df[pd.to_datetime(df['start_date']).dt.year == current_year]
            
            # 상태값 매핑 (기존 한글 데이터와 새 영어 데이터 모두 지원)
            def map_status(status):
                mapping = {'대기': 'pending', '승인': 'approved', '거부': 'rejected'}
                return mapping.get(status, status)
            
            df['mapped_status'] = df['status'].apply(map_status)
            current_year_vacations['mapped_status'] = current_year_vacations['status'].apply(map_status)
            
            stats = {
                'total_requests': len(df),
                'pending_requests': len(df[df['mapped_status'] == 'pending']),
                'approved_requests': len(df[df['mapped_status'] == 'approved']),
                'rejected_requests': len(df[df['mapped_status'] == 'rejected']),
                'current_year_requests': len(current_year_vacations),
                'current_year_approved': len(current_year_vacations[current_year_vacations['mapped_status'] == 'approved']),
                'vacation_type_distribution': df['vacation_type'].value_counts().to_dict(),
                'status_distribution': df['mapped_status'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"휴가 통계 조회 중 오류: {e}")
            return {}
    
    def approve_vacation_request(self, vacation_data):
        """승인된 휴가 요청을 휴가 데이터에 추가하고 상태를 업데이트합니다."""
        try:
            # 기존 휴가 데이터 로드
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 동일한 휴가 요청이 이미 있는지 확인
            employee_id = vacation_data.get('employee_id')
            start_date = vacation_data.get('start_date')
            end_date = vacation_data.get('end_date')
            
            existing_vacation = df[
                (df['employee_id'] == employee_id) & 
                (df['start_date'] == start_date) & 
                (df['end_date'] == end_date)
            ]
            
            if len(existing_vacation) > 0:
                # 기존 휴가 요청의 상태를 승인으로 업데이트
                df.loc[
                    (df['employee_id'] == employee_id) & 
                    (df['start_date'] == start_date) & 
                    (df['end_date'] == end_date), 
                    'status'
                ] = 'approved'
                
                df.loc[
                    (df['employee_id'] == employee_id) & 
                    (df['start_date'] == start_date) & 
                    (df['end_date'] == end_date), 
                    'approved_date'
                ] = vacation_data.get('approval_date', datetime.now().strftime('%Y-%m-%d'))
            else:
                # 새로운 휴가 요청을 추가 (승인된 상태로)
                new_vacation = {
                    'vacation_id': f"VAC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'employee_id': employee_id,
                    'employee_name': vacation_data.get('employee_name', ''),
                    'vacation_type': vacation_data.get('vacation_type', 'annual'),
                    'start_date': start_date,
                    'end_date': end_date,
                    'days_count': vacation_data.get('days_count', vacation_data.get('days', 1)),
                    'reason': vacation_data.get('reason', ''),
                    'status': 'approved',
                    'request_date': datetime.now().strftime('%Y-%m-%d'),
                    'approved_date': vacation_data.get('approval_date', datetime.now().strftime('%Y-%m-%d')),
                    'input_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # DataFrame에 새 행 추가
                df = pd.concat([df, pd.DataFrame([new_vacation])], ignore_index=True)
            
            # 파일에 저장
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
            
        except Exception as e:
            print(f"휴가 승인 처리 중 오류: {e}")
            return False

    def delete_vacation(self, vacation_id):
        """휴가 내역을 삭제합니다 (관리자 전용)."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if vacation_id not in df['vacation_id'].values:
                return False
            
            # 해당 휴가 내역 삭제
            df = df[df['vacation_id'] != vacation_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
            
        except Exception as e:
            print(f"휴가 삭제 중 오류: {e}")
            return False

    def get_vacation_by_id(self, vacation_id):
        """특정 휴가 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if vacation_id in df['vacation_id'].values:
                return df[df['vacation_id'] == vacation_id].iloc[0].to_dict()
            else:
                return None
                
        except Exception as e:
            print(f"휴가 정보 조회 중 오류: {e}")
            return None
