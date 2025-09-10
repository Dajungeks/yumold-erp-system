import pandas as pd
import os
from datetime import datetime
import json

class BusinessProcessManager:
    def __init__(self):
        self.workflow_file = 'data/business_workflows.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.workflow_file):
            df = pd.DataFrame(columns=[
                'workflow_id', 'quotation_id', 'quotation_number', 'customer_name',
                'current_stage', 'stages_json', 'total_amount_usd', 'currency',
                'created_date', 'last_updated', 'completed_date', 'status',
                'created_by', 'notes'
            ])
            df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
    
    def create_workflow_from_quotation(self, quotation_data, created_by):
        """견적서에서 비즈니스 워크플로우를 생성합니다."""
        try:
            # 이미 해당 견적서에 대한 워크플로우가 있는지 확인
            existing_workflows = self.get_all_workflows()
            if len(existing_workflows) > 0:
                existing_quotation_numbers = set()
                if isinstance(existing_workflows, pd.DataFrame):
                    # DataFrame 컬럼 확인
                    if 'quotation_number' in existing_workflows.columns:
                        existing_quotation_numbers = set(existing_workflows['quotation_number'].dropna().tolist())
                    elif 'quotation_id' in existing_workflows.columns:
                        existing_quotation_numbers = set(existing_workflows['quotation_id'].dropna().tolist())
                else:
                    existing_quotation_numbers = set([w.get('quotation_number') or w.get('quotation_id') for w in existing_workflows if w.get('quotation_number') or w.get('quotation_id')])
                
                quotation_id = quotation_data.get('quotation_number') or quotation_data.get('quotation_id')
                if quotation_id and quotation_id in existing_quotation_numbers:
                    print(f"이미 견적서 {quotation_id}에 대한 워크플로우가 존재합니다.")
                    return None
            # 승인 없이 바로 진행되는 워크플로우 단계 정의
            stages = [
                {
                    'stage_name': '발주서 생성',
                    'stage_order': 1,
                    'status': '진행중',  # 첫 번째 단계를 바로 진행중으로 시작
                    'assigned_to': created_by,
                    'started_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'completed_date': None,
                    'notes': '견적서 기반 자동 워크플로우 시작'
                },
                {
                    'stage_name': '재고 입고',
                    'stage_order': 2,
                    'status': '대기',
                    'assigned_to': None,
                    'started_date': None,
                    'completed_date': None,
                    'notes': ''
                },
                {
                    'stage_name': '배송 준비',
                    'stage_order': 3,
                    'status': '대기',
                    'assigned_to': None,
                    'started_date': None,
                    'completed_date': None,
                    'notes': ''
                },
                {
                    'stage_name': '인보이스 발행',
                    'stage_order': 4,
                    'status': '대기',
                    'assigned_to': None,
                    'started_date': None,
                    'completed_date': None,
                    'notes': ''
                },
                {
                    'stage_name': '결제 완료',
                    'stage_order': 5,
                    'status': '대기',
                    'assigned_to': None,
                    'started_date': None,
                    'completed_date': None,
                    'notes': ''
                }
            ]
            
            # 워크플로우 데이터 생성 (승인 없이 바로 발주서 생성 단계부터 시작)
            workflow_id = f"WF{datetime.now().strftime('%Y%m%d%H%M%S')}"
            workflow_data = {
                'workflow_id': workflow_id,
                'quotation_id': quotation_data.get('quotation_id'),
                'quotation_number': quotation_data.get('quotation_number'),
                'customer_name': quotation_data.get('customer_name'),
                'current_stage': '발주서 생성',  # 승인 단계 건너뛰고 바로 발주서 생성
                'stages_json': json.dumps(stages, ensure_ascii=False),
                'total_amount_usd': quotation_data.get('total_amount_usd', quotation_data.get('total_amount', 0)),
                'currency': quotation_data.get('currency', 'USD'),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'completed_date': None,
                'status': '진행중',
                'created_by': created_by,
                'notes': '견적서 기반 자동 워크플로우'
            }
            
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            df = pd.concat([df, pd.DataFrame([workflow_data])], ignore_index=True)
            df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return workflow_id
        except Exception as e:
            print(f"워크플로우 생성 중 오류: {e}")
            return None
    
    def get_all_workflows(self):
        """모든 비즈니스 워크플로우를 가져옵니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            
            # stages_json을 stages로 변환
            if 'stages_json' in df.columns:
                df['stages'] = df['stages_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            return df
        except Exception as e:
            print(f"워크플로우 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_workflow_by_id(self, workflow_id):
        """특정 워크플로우 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            workflow = df[df['workflow_id'] == workflow_id]
            if len(workflow) > 0:
                result = workflow.iloc[0].to_dict()
                
                # stages_json을 stages로 변환
                if 'stages_json' in result and result['stages_json']:
                    try:
                        result['stages'] = json.loads(result['stages_json'])
                    except:
                        result['stages'] = []
                
                return result
            return None
        except Exception as e:
            print(f"워크플로우 조회 중 오류: {e}")
            return None
    
    def advance_workflow_stage(self, workflow_id, completed_by, notes=None):
        """워크플로우를 다음 단계로 진행합니다."""
        try:
            workflow = self.get_workflow_by_id(workflow_id)
            if not workflow:
                return False
            
            stages = workflow.get('stages', [])
            if not stages:
                return False
            
            # 현재 진행중인 단계 찾기
            current_stage_index = None
            for i, stage in enumerate(stages):
                if stage['status'] == '진행중':
                    current_stage_index = i
                    break
            
            if current_stage_index is None:
                return False
            
            # 현재 단계 완료 처리
            stages[current_stage_index]['status'] = '완료'
            stages[current_stage_index]['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if notes:
                stages[current_stage_index]['notes'] = notes
            
            # 다음 단계 활성화
            next_stage_index = current_stage_index + 1
            if next_stage_index < len(stages):
                stages[next_stage_index]['status'] = '진행중'
                stages[next_stage_index]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                stages[next_stage_index]['assigned_to'] = completed_by
                
                current_stage = stages[next_stage_index]['stage_name']
                workflow_status = '진행중'
            else:
                # 모든 단계 완료
                current_stage = '완료'
                workflow_status = '완료'
            
            # 워크플로우 업데이트
            update_data = {
                'current_stage': current_stage,
                'stages_json': json.dumps(stages, ensure_ascii=False),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': workflow_status
            }
            
            if workflow_status == '완료':
                update_data['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return self.update_workflow(workflow_id, update_data)
        except Exception as e:
            print(f"워크플로우 단계 진행 중 오류: {e}")
            return False
    
    def update_workflow(self, workflow_id, workflow_data):
        """워크플로우 정보를 업데이트합니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            
            if workflow_id not in df['workflow_id'].values:
                return False
            
            # stages를 JSON 문자열로 변환
            if 'stages' in workflow_data:
                workflow_data['stages_json'] = json.dumps(workflow_data['stages'], ensure_ascii=False)
                del workflow_data['stages']
            
            workflow_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            mask = df['workflow_id'] == workflow_id
            for key, value in workflow_data.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"워크플로우 업데이트 중 오류: {e}")
            return False
    
    def get_workflows_by_stage(self, stage_name):
        """특정 단계의 워크플로우들을 가져옵니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            filtered_df = df[df['current_stage'] == stage_name]
            
            # stages_json을 stages로 변환
            if 'stages_json' in filtered_df.columns:
                filtered_df = filtered_df.copy()
                filtered_df.loc[:, 'stages'] = filtered_df['stages_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            # 딕셔너리 리스트로 반환
            return filtered_df.to_dict('records')
        except Exception as e:
            print(f"단계별 워크플로우 조회 중 오류: {e}")
            return []
    
    def get_workflow_statistics(self):
        """워크플로우 통계를 가져옵니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            
            stats = {
                'total_workflows': len(df),
                'active_workflows': len(df[df['status'] == '진행중']),
                'completed_workflows': len(df[df['status'] == '완료']),
                'stage_distribution': df['current_stage'].value_counts().to_dict(),
                'total_amount': pd.to_numeric(df['total_amount_usd'], errors='coerce').sum(),
                'monthly_completion': df[df['status'] == '완료'].groupby(
                    pd.to_datetime(df['completed_date'], errors='coerce').dt.to_period('M')
                ).size().to_dict()
            }
            
            return stats
        except Exception as e:
            print(f"워크플로우 통계 조회 중 오류: {e}")
            return {}
    
    def get_pending_workflows(self, assigned_to=None):
        """대기 중인 워크플로우를 가져옵니다."""
        try:
            df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            
            # 진행중인 워크플로우만 필터링
            pending_workflows = df[df['status'] == '진행중'].copy()
            
            if assigned_to:
                # 특정 사용자에게 할당된 워크플로우 필터링
                # 이를 위해서는 stages_json을 파싱해야 함
                def is_assigned_to_user(stages_json):
                    try:
                        stages = json.loads(stages_json) if stages_json else []
                        for stage in stages:
                            if stage.get('status') == '진행중' and stage.get('assigned_to') == assigned_to:
                                return True
                        return False
                    except:
                        return False
                
                pending_workflows = pending_workflows[
                    pending_workflows['stages_json'].apply(is_assigned_to_user)
                ]
            
            # stages_json을 stages로 변환
            if 'stages_json' in pending_workflows.columns:
                pending_workflows['stages'] = pending_workflows['stages_json'].apply(
                    lambda x: json.loads(x) if pd.notna(x) and x else []
                )
            
            # 딕셔너리 리스트로 반환
            return pending_workflows.to_dict('records')
        except Exception as e:
            print(f"대기 중인 워크플로우 조회 중 오류: {e}")
            return []
