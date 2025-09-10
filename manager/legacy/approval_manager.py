import pandas as pd
import os
from datetime import datetime

class ApprovalManager:
    def __init__(self):
        self.data_file = 'data/approvals.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            columns = [
                'approval_id', 'request_type', 'request_id', 'requester_id',
                'requester_name', 'approver_id', 'approver_name', 'request_date',
                'approval_date', 'status', 'priority', 'description', 'reason',
                'rejection_reason', 'supporting_documents', 'input_date', 'updated_date'
            ]
            df = pd.DataFrame(columns=columns)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def create_approval_request(self, request_data):
        """새 승인 요청을 생성합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 승인 ID 생성
            if 'approval_id' not in request_data or not request_data['approval_id']:
                request_data['approval_id'] = f"APR{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 기본값 설정
            request_data['status'] = request_data.get('status', '대기')
            request_data['priority'] = request_data.get('priority', '보통')
            request_data['request_date'] = request_data.get('request_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            request_data['input_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request_data['updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.concat([df, pd.DataFrame([request_data])], ignore_index=True)
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"승인 요청 생성 중 오류: {e}")
            return False
    
    def get_all_requests(self):
        """모든 승인 요청을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            if not df.empty:
                df = df.sort_values('request_date', ascending=False)
            return df.to_dict('records')
        except Exception as e:
            print(f"승인 요청 조회 중 오류: {e}")
            return []
    
    def get_pending_requests(self):
        """대기 중인 승인 요청을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['status'] == 'pending']
        except Exception as e:
            print(f"대기 중인 승인 요청 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_requests_by_approver(self, approver_id):
        """특정 승인자의 요청들을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['approver_id'] == approver_id]
        except Exception as e:
            print(f"승인자별 요청 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_requests_by_requester(self, requester_id):
        """특정 요청자의 요청들을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            return df[df['requester_id'] == requester_id]
        except Exception as e:
            print(f"요청자별 요청 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def approve_request(self, approval_id, approver_id, approver_name=None, notes=None):
        """승인 요청을 승인합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if approval_id not in df['approval_id'].values:
                return False
            
            # 승인할 요청 정보 가져오기
            request_row = df[df['approval_id'] == approval_id].iloc[0]
            request_type = request_row.get('request_type', '')
            
            # 승인 처리
            df.loc[df['approval_id'] == approval_id, 'status'] = 'approved'
            df.loc[df['approval_id'] == approval_id, 'approver_id'] = approver_id
            if approver_name:
                df.loc[df['approval_id'] == approval_id, 'approver_name'] = approver_name
            df.loc[df['approval_id'] == approval_id, 'approval_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[df['approval_id'] == approval_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if notes:
                df.loc[df['approval_id'] == approval_id, 'reason'] = notes
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            # 휴가 승인인 경우 휴가 데이터도 업데이트
            if request_type == '휴가신청':
                self._update_vacation_status(request_row)
            
            return True
        except Exception as e:
            print(f"승인 처리 중 오류: {e}")
            return False
    
    def _update_vacation_status(self, request_row):
        """승인된 휴가 요청을 휴가 데이터에 반영합니다."""
        try:
            import json
            import sys
            import os
            
            # vacation_manager 모듈 import 
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from vacation_manager import VacationManager
            
            vacation_manager = VacationManager()
            
            # 요청 세부정보에서 휴가 정보 추출
            description = request_row.get('description', '')
            request_type = request_row.get('request_type', '')
            
            if description and '휴가' in request_type:
                try:
                    # JSON 형태로 저장된 휴가 정보 파싱
                    if description.startswith('{') and description.endswith('}'):
                        vacation_data = json.loads(description)
                    else:
                        # 문자열 형태로 저장된 경우 파싱
                        vacation_data = self._parse_vacation_description(description)
                    
                    # 요청자 정보 추가
                    vacation_data['employee_id'] = request_row.get('requester_id', '')
                    vacation_data['employee_name'] = request_row.get('requester_name', '')
                    
                    # 휴가 데이터 업데이트
                    if vacation_data.get('employee_id'):
                        vacation_data['status'] = '승인'
                        vacation_data['approval_date'] = datetime.now().strftime('%Y-%m-%d')
                        vacation_data['approved_by'] = request_row.get('approver_id', 'system')
                        
                        # 휴가 매니저를 통해 상태 업데이트
                        success = vacation_manager.approve_vacation_request(vacation_data)
                        print(f"휴가 승인 처리 결과: {success}")
                        
                except Exception as e:
                    print(f"휴가 데이터 파싱 중 오류: {e}")
                    import traceback
                    print(f"상세 오류: {traceback.format_exc()}")
                    
        except Exception as e:
            print(f"휴가 상태 업데이트 중 오류: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
    
    def _parse_vacation_description(self, description):
        """문자열 형태의 휴가 설명을 파싱합니다."""
        vacation_data = {}
        
        # 기본 패턴 매칭으로 정보 추출
        lines = description.split('\n')
        for line in lines:
            if 'Employee ID:' in line or '직원 ID:' in line:
                vacation_data['employee_id'] = line.split(':')[1].strip()
            elif 'Vacation Type:' in line or '휴가 유형:' in line:
                vacation_data['vacation_type'] = line.split(':')[1].strip()
            elif 'Start Date:' in line or '시작일:' in line:
                vacation_data['start_date'] = line.split(':')[1].strip()
            elif 'End Date:' in line or '종료일:' in line:
                vacation_data['end_date'] = line.split(':')[1].strip()
            elif 'Days:' in line or '일수:' in line:
                try:
                    vacation_data['days'] = int(line.split(':')[1].strip().replace('일', '').replace('days', ''))
                except:
                    vacation_data['days'] = 1
            elif '사유:' in line:
                vacation_data['reason'] = line.split('사유:')[1].strip()
        
        return vacation_data
    
    def reject_request(self, approval_id, approver_id, rejection_reason, approver_name=None):
        """승인 요청을 거부합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if approval_id not in df['approval_id'].values:
                return False
            
            # 거부 처리
            df.loc[df['approval_id'] == approval_id, 'status'] = 'rejected'
            df.loc[df['approval_id'] == approval_id, 'approver_id'] = approver_id
            if approver_name:
                df.loc[df['approval_id'] == approval_id, 'approver_name'] = approver_name
            df.loc[df['approval_id'] == approval_id, 'approval_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[df['approval_id'] == approval_id, 'rejection_reason'] = rejection_reason
            df.loc[df['approval_id'] == approval_id, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"거부 처리 중 오류: {e}")
            return False
    
    def get_approval_statistics(self):
        """승인 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 상태값 매핑 (기존 한글 데이터와 새 영어 데이터 모두 지원)
            def map_status(status):
                mapping = {'대기': 'pending', '승인': 'approved', '거부': 'rejected'}
                return mapping.get(status, status)
            
            df['mapped_status'] = df['status'].apply(map_status)
            
            stats = {
                'total_requests': len(df),
                'pending_requests': len(df[df['mapped_status'] == 'pending']),
                'approved_requests': len(df[df['mapped_status'] == 'approved']),
                'rejected_requests': len(df[df['mapped_status'] == 'rejected']),
                'approval_rate': (len(df[df['mapped_status'] == 'approved']) / len(df) * 100) if len(df) > 0 else 0,
                'status_distribution': df['mapped_status'].value_counts().to_dict(),
                'type_distribution': df['request_type'].value_counts().to_dict(),
                'priority_distribution': df['priority'].value_counts().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"승인 통계 조회 중 오류: {e}")
            return {}
    
    def create_quotation_approval_request(self, quotation_id, quotation_data, requester_id, requester_name):
        """견적서 승인 요청을 생성합니다."""
        try:
            request_data = {
                'request_type': '견적서 승인',
                'request_id': quotation_id,
                'requester_id': requester_id,
                'requester_name': requester_name,
                'description': f"견적서 {quotation_data.get('quotation_number')} 승인 요청",
                'priority': '높음' if float(quotation_data.get('total_amount_usd', 0)) > 10000 else '보통'
            }
            
            return self.create_approval_request(request_data)
        except Exception as e:
            print(f"견적서 승인 요청 생성 중 오류: {e}")
            return False
    
    def create_purchase_order_approval_request(self, po_id, po_data, requester_id, requester_name):
        """발주서 승인 요청을 생성합니다."""
        try:
            request_data = {
                'request_type': '발주서 승인',
                'request_id': po_id,
                'requester_id': requester_id,
                'requester_name': requester_name,
                'description': f"발주서 {po_data.get('po_number')} 승인 요청",
                'priority': '높음' if float(po_data.get('total_amount', 0)) > 5000 else '보통'
            }
            
            return self.create_approval_request(request_data)
        except Exception as e:
            print(f"발주서 승인 요청 생성 중 오류: {e}")
            return False
    
    def create_vacation_approval_request(self, vacation_data, requester_id, requester_name):
        """휴가 승인 요청을 생성합니다."""
        try:
            request_data = {
                'request_type': '휴가 승인',
                'request_id': vacation_data.get('vacation_id'),
                'requester_id': requester_id,
                'requester_name': requester_name,
                'description': f"휴가 신청 ({vacation_data.get('start_date')} ~ {vacation_data.get('end_date')})",
                'priority': '보통'
            }
            
            return self.create_approval_request(request_data)
        except Exception as e:
            print(f"휴가 승인 요청 생성 중 오류: {e}")
            return False
    
    def get_approval_by_id(self, approval_id):
        """특정 승인 요청 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            approval = df[df['approval_id'] == approval_id]
            if len(approval) > 0:
                return approval.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"승인 요청 조회 중 오류: {e}")
            return None
    
    def get_recent_requests(self, days=7):
        """최근 요청들을 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 날짜 필터링
            cutoff_date = (datetime.now() - pd.Timedelta(days=days))
            df['request_date'] = pd.to_datetime(df['request_date'])
            
            recent_requests = df[df['request_date'] >= cutoff_date]
            return recent_requests.sort_values('request_date', ascending=False)
        except Exception as e:
            print(f"최근 승인 요청 조회 중 오류: {e}")
            return pd.DataFrame()
