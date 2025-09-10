import pandas as pd
import os
from datetime import datetime
import json
import uuid

class BusinessProcessManagerV2:
    """새로운 비즈니스 프로세스 관리자 - 판매/서비스 프로세스 분리"""
    
    def __init__(self):
        self.workflow_file = 'data/business_workflows_v2.csv'
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.workflow_file):
            # 빈 데이터프레임 생성
            data = {
                'workflow_id': [],
                'workflow_type': [],
                'quotation_id': [],
                'quotation_number': [],
                'customer_name': [],
                'product_types': [],
                'has_sales_items': [],
                'has_service_items': [],
                'sales_current_stage': [],
                'sales_stages_json': [],
                'sales_progress': [],
                'sales_completed_date': [],
                'service_current_stage': [],
                'service_stages_json': [],
                'service_progress': [],
                'service_completed_date': [],
                'overall_status': [],
                'overall_progress': [],
                'total_amount_usd': [],
                'currency': [],
                'created_date': [],
                'created_by': [],
                'last_updated': [],
                'completed_date': [],
                'assigned_sales_team': [],
                'assigned_service_team': [],
                'notes': []
            }
            df = pd.DataFrame(data)
            df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
    
    def get_sales_stages_template(self):
        """판매 프로세스 기본 단계 템플릿"""
        return [
            {
                'stage_name': '견적서 승인',
                'stage_order': 1,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '주문 확정',
                'stage_order': 2,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '발주서 생성',
                'stage_order': 3,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '재고 입고',
                'stage_order': 4,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '배송 준비',
                'stage_order': 5,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '납품 완료',
                'stage_order': 6,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '정산 완료',
                'stage_order': 7,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            }
        ]
    
    def get_service_stages_template(self):
        """서비스 프로세스 기본 단계 템플릿 (9단계)"""
        return [
            {
                'stage_name': '서비스 요청 접수',
                'stage_order': 1,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '일정 조율',
                'stage_order': 2,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '고객 방문',
                'stage_order': 3,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '서비스 진행중',
                'stage_order': 4,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '서비스 완료',
                'stage_order': 5,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '비용 정산 진행중',
                'stage_order': 6,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '비용 정산 거부',
                'stage_order': 7,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '비용 정산 승인',
                'stage_order': 8,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            },
            {
                'stage_name': '비용 정산 완료',
                'stage_order': 9,
                'status': '대기',
                'assigned_to': None,
                'started_date': None,
                'completed_date': None,
                'notes': ''
            }
        ]
    
    def analyze_quotation_products(self, quotation_data):
        """견적서의 제품을 분석하여 판매/서비스 여부 판단"""
        try:
            # 견적서에서 제품 정보 추출
            products_json = quotation_data.get('products', '[]')
            if isinstance(products_json, str):
                products = json.loads(products_json)
            else:
                products = products_json
            
            product_types = set()
            has_sales_items = False
            has_service_items = False
            
            for product in products:
                product_code = product.get('product_code', '')
                product_name = product.get('product_name', '')
                
                # 제품 코드나 이름에서 제품 타입 추출
                if any(keyword in product_code.upper() or keyword in product_name.upper() 
                       for keyword in ['HR-', 'HOT RUNNER SYSTEM']):
                    product_types.add('HR')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
                        
                elif any(keyword in product_code.upper() or keyword in product_name.upper() 
                         for keyword in ['HRC-', 'HOT RUNNER CONTROLLER']):
                    product_types.add('HRC')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
                        
                elif any(keyword in product_code.upper() or keyword in product_name.upper() 
                         for keyword in ['MB-', 'MOLD BASE']):
                    product_types.add('MB')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
                        
                elif any(keyword in product_code.upper() or keyword in product_name.upper() 
                         for keyword in ['MTC-', 'MOLD TEMP CONTROLLER']):
                    product_types.add('MTC')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
                        
                elif any(keyword in product_code.upper() or keyword in product_name.upper() 
                         for keyword in ['ROBOT', 'RBT-']):
                    product_types.add('ROBOT')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
                        
                else:
                    product_types.add('기타')
                    if 'SERVICE' in product_code.upper() or 'SERVICE' in product_name.upper():
                        has_service_items = True
                    else:
                        has_sales_items = True
            
            return list(product_types), has_sales_items, has_service_items
            
        except Exception as e:
            print(f"제품 분석 중 오류: {e}")
            return ['기타'], True, False
    
    def determine_workflow_type(self, has_sales_items, has_service_items):
        """워크플로우 타입 결정"""
        if has_sales_items and has_service_items:
            return 'mixed'
        elif has_service_items:
            return 'service'
        else:
            return 'sales'
    
    def create_workflow_from_quotation(self, quotation_data, created_by):
        """견적서에서 새로운 워크플로우 생성"""
        try:
            # 이미 해당 견적서에 대한 워크플로우가 있는지 확인
            existing_workflows = self.get_all_workflows()
            if len(existing_workflows) > 0:
                existing_quotation_numbers = set(existing_workflows['quotation_number'].tolist())
                if quotation_data.get('quotation_number') in existing_quotation_numbers:
                    return None, f"견적서 {quotation_data.get('quotation_number')}에 대한 워크플로우가 이미 존재합니다."
            
            # 제품 분석
            product_types, has_sales_items, has_service_items = self.analyze_quotation_products(quotation_data)
            workflow_type = self.determine_workflow_type(has_sales_items, has_service_items)
            
            # 새 워크플로우 ID 생성
            workflow_id = str(uuid.uuid4())[:8].upper()
            
            # 단계 템플릿 생성
            sales_stages = self.get_sales_stages_template() if has_sales_items else []
            service_stages = self.get_service_stages_template() if has_service_items else []
            
            # 첫 번째 단계 활성화
            if sales_stages:
                sales_stages[0]['status'] = '진행중'
                sales_stages[0]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if service_stages:
                service_stages[0]['status'] = '진행중'
                service_stages[0]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 워크플로우 데이터 생성
            new_workflow = {
                'workflow_id': workflow_id,
                'workflow_type': workflow_type,
                'quotation_id': quotation_data.get('quotation_id', ''),
                'quotation_number': quotation_data.get('quotation_number', ''),
                'customer_name': quotation_data.get('customer_name', ''),
                
                'product_types': json.dumps(product_types),
                'has_sales_items': has_sales_items,
                'has_service_items': has_service_items,
                
                'sales_current_stage': sales_stages[0]['stage_name'] if sales_stages else '',
                'sales_stages_json': json.dumps(sales_stages),
                'sales_progress': 0.0,
                'sales_completed_date': '',
                
                'service_current_stage': service_stages[0]['stage_name'] if service_stages else '',
                'service_stages_json': json.dumps(service_stages),
                'service_progress': 0.0,
                'service_completed_date': '',
                
                'overall_status': 'active',
                'overall_progress': 0.0,
                'total_amount_usd': quotation_data.get('total_amount_usd', 0),
                'currency': quotation_data.get('currency', 'USD'),
                
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': created_by,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'completed_date': '',
                'assigned_sales_team': quotation_data.get('assigned_sales_team', ''),
                'assigned_service_team': quotation_data.get('assigned_service_team', ''),
                'notes': quotation_data.get('notes', '')
            }
            
            # 데이터 저장
            workflows_df = pd.read_csv(self.workflow_file, encoding='utf-8-sig')
            workflows_df = pd.concat([workflows_df, pd.DataFrame([new_workflow])], ignore_index=True)
            workflows_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return workflow_id, f"{workflow_type.upper()} 워크플로우가 생성되었습니다."
            
        except Exception as e:
            print(f"워크플로우 생성 중 오류: {e}")
            return None, f"워크플로우 생성 중 오류가 발생했습니다: {str(e)}"
    
    def create_workflow_from_data(self, workflow_data):
        """기존 워크플로우 데이터로부터 새로운 워크플로우 생성 (복제용)"""
        try:
            # 기존 워크플로우 확인
            existing_workflows = self.get_all_workflows()
            if len(existing_workflows) > 0:
                existing_quotation_numbers = set(existing_workflows['quotation_number'].tolist())
                if workflow_data.get('quotation_number') in existing_quotation_numbers:
                    return False, f"견적서 {workflow_data.get('quotation_number')}에 대한 워크플로우가 이미 존재합니다."
            
            # 새 데이터프레임에 추가
            new_workflow_df = pd.DataFrame([workflow_data])
            
            # 기존 데이터와 병합
            if len(existing_workflows) > 0:
                updated_df = pd.concat([existing_workflows, new_workflow_df], ignore_index=True)
            else:
                updated_df = new_workflow_df
            
            # 파일 저장
            updated_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return True, "워크플로우가 성공적으로 복제되었습니다."
            
        except Exception as e:
            print(f"워크플로우 복제 중 오류: {e}")
            return False, f"워크플로우 복제 중 오류가 발생했습니다: {str(e)}"
    
    def get_all_workflows(self):
        """모든 워크플로우 조회"""
        try:
            return pd.read_csv(self.workflow_file, encoding='utf-8-sig')
        except Exception as e:
            print(f"워크플로우 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_workflow_by_id(self, workflow_id):
        """특정 워크플로우 조회"""
        try:
            workflows_df = self.get_all_workflows()
            workflow_data = workflows_df[workflows_df['workflow_id'] == workflow_id]
            if len(workflow_data) > 0:
                return workflow_data.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"워크플로우 조회 중 오류: {e}")
            return None
    
    def advance_sales_stage(self, workflow_id, completed_by, notes=""):
        """판매 프로세스 다음 단계로 진행"""
        return self._advance_stage(workflow_id, 'sales', completed_by, notes)
    
    def advance_service_stage(self, workflow_id, completed_by, notes=""):
        """서비스 프로세스 다음 단계로 진행"""
        return self._advance_stage(workflow_id, 'service', completed_by, notes)
    
    def _advance_stage(self, workflow_id, process_type, completed_by, notes=""):
        """프로세스 단계 진행 (공통) - 서비스 프로세스 분기 로직 포함"""
        try:
            workflows_df = self.get_all_workflows()
            workflow_idx = workflows_df[workflows_df['workflow_id'] == workflow_id].index
            
            if len(workflow_idx) == 0:
                return False, "워크플로우를 찾을 수 없습니다."
            
            workflow_idx = workflow_idx[0]
            
            # 현재 단계 정보 가져오기
            stages_json_col = f'{process_type}_stages_json'
            current_stage_col = f'{process_type}_current_stage'
            
            stages_json = workflows_df.at[workflow_idx, stages_json_col]
            if isinstance(stages_json, str):
                stages = json.loads(stages_json)
            else:
                stages = []
            
            # 현재 진행중인 단계 찾기
            current_stage_idx = None
            for i, stage in enumerate(stages):
                if stage['status'] == '진행중':
                    current_stage_idx = i
                    break
            
            if current_stage_idx is None:
                return False, "진행중인 단계를 찾을 수 없습니다."
            
            # 현재 단계 완료 처리
            stages[current_stage_idx]['status'] = '완료'
            stages[current_stage_idx]['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if notes:
                stages[current_stage_idx]['notes'] = notes
            
            # 서비스 프로세스 특별 로직: 6단계(비용 정산 진행중) 후 분기 처리
            if process_type == 'service' and current_stage_idx == 5:  # 6단계 (인덱스 5)
                # 사용자가 승인/거부를 선택할 수 있도록 두 단계 모두 대기 상태로 설정
                stages[6]['status'] = '대기'  # 비용 정산 거부
                stages[7]['status'] = '대기'  # 비용 정산 승인
                next_stage_name = '비용 정산 대기중'
            elif process_type == 'service' and current_stage_idx == 6:  # 7단계 거부 완료 후
                # 거부 후 다시 승인 단계로 진행 가능
                stages[7]['status'] = '진행중'
                stages[7]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                next_stage_name = stages[7]['stage_name']
            else:
                # 일반적인 단계 진행
                next_stage_idx = current_stage_idx + 1
                if next_stage_idx < len(stages):
                    stages[next_stage_idx]['status'] = '진행중'
                    stages[next_stage_idx]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    next_stage_name = stages[next_stage_idx]['stage_name']
                else:
                    # 모든 단계 완료
                    next_stage_name = '완료'
                    workflows_df.at[workflow_idx, f'{process_type}_completed_date'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 진행률 계산
            completed_stages = sum(1 for stage in stages if stage['status'] == '완료')
            progress = (completed_stages / len(stages)) * 100
            
            # 데이터 업데이트
            workflows_df.at[workflow_idx, stages_json_col] = json.dumps(stages)
            workflows_df.at[workflow_idx, current_stage_col] = next_stage_name
            workflows_df.at[workflow_idx, f'{process_type}_progress'] = progress
            workflows_df.at[workflow_idx, 'last_updated'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 전체 진행률 계산
            sales_progress = workflows_df.at[workflow_idx, 'sales_progress'] if workflows_df.at[workflow_idx, 'has_sales_items'] else 100.0
            service_progress = workflows_df.at[workflow_idx, 'service_progress'] if workflows_df.at[workflow_idx, 'has_service_items'] else 100.0
            
            if workflows_df.at[workflow_idx, 'has_sales_items'] and workflows_df.at[workflow_idx, 'has_service_items']:
                overall_progress = (sales_progress + service_progress) / 2
            else:
                overall_progress = max(sales_progress, service_progress)
            
            workflows_df.at[workflow_idx, 'overall_progress'] = overall_progress
            
            # 전체 완료 확인
            if overall_progress == 100.0:
                workflows_df.at[workflow_idx, 'overall_status'] = 'completed'
                workflows_df.at[workflow_idx, 'completed_date'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 파일 저장
            workflows_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return True, f"{process_type.upper()} 프로세스가 다음 단계({next_stage_name})로 진행되었습니다."
            
        except Exception as e:
            print(f"단계 진행 중 오류: {e}")
            return False, f"단계 진행 중 오류가 발생했습니다: {str(e)}"
    
    def update_workflow(self, workflow_id, updates):
        """워크플로우 정보 업데이트"""
        try:
            workflows_df = self.get_all_workflows()
            workflow_idx = workflows_df[workflows_df['workflow_id'] == workflow_id].index
            
            if len(workflow_idx) == 0:
                return False, "워크플로우를 찾을 수 없습니다."
            
            workflow_idx = workflow_idx[0]
            
            # 업데이트 적용
            for key, value in updates.items():
                if key in workflows_df.columns:
                    workflows_df.at[workflow_idx, key] = value
            
            workflows_df.at[workflow_idx, 'last_updated'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 파일 저장
            workflows_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return True, "워크플로우가 업데이트되었습니다."
            
        except Exception as e:
            print(f"워크플로우 업데이트 중 오류: {e}")
            return False, f"업데이트 중 오류가 발생했습니다: {str(e)}"
    
    def delete_workflow(self, workflow_id):
        """워크플로우 삭제"""
        try:
            workflows_df = self.get_all_workflows()
            
            if workflow_id not in workflows_df['workflow_id'].values:
                return False, "워크플로우를 찾을 수 없습니다."
            
            # 워크플로우 삭제
            workflows_df = workflows_df[workflows_df['workflow_id'] != workflow_id]
            workflows_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return True, "워크플로우가 삭제되었습니다."
            
        except Exception as e:
            print(f"워크플로우 삭제 중 오류: {e}")
            return False, f"삭제 중 오류가 발생했습니다: {str(e)}"
    
    def advance_service_stage_with_decision(self, workflow_id, decision, completed_by, notes=""):
        """서비스 프로세스 단계 진행 - 승인/거부 결정 포함"""
        try:
            workflows_df = self.get_all_workflows()
            workflow_idx = workflows_df[workflows_df['workflow_id'] == workflow_id].index
            
            if len(workflow_idx) == 0:
                return False, "워크플로우를 찾을 수 없습니다."
            
            workflow_idx = workflow_idx[0]
            
            stages_json = workflows_df.at[workflow_idx, 'service_stages_json']
            stages = json.loads(stages_json)
            
            if decision == 'approve':
                # 승인: 8단계(비용 정산 승인)로 진행
                stages[7]['status'] = '진행중'
                stages[7]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if notes:
                    stages[7]['notes'] = notes
                next_stage_name = stages[7]['stage_name']
            elif decision == 'reject':
                # 거부: 7단계(비용 정산 거부)로 진행
                stages[6]['status'] = '진행중'
                stages[6]['started_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if notes:
                    stages[6]['notes'] = notes
                next_stage_name = stages[6]['stage_name']
            else:
                return False, "올바른 결정을 선택해주세요 (approve/reject)."
            
            # 진행률 계산
            completed_stages = sum(1 for stage in stages if stage['status'] == '완료')
            progress = (completed_stages / len(stages)) * 100
            
            # 데이터 업데이트
            workflows_df.at[workflow_idx, 'service_stages_json'] = json.dumps(stages)
            workflows_df.at[workflow_idx, 'service_current_stage'] = next_stage_name
            workflows_df.at[workflow_idx, 'service_progress'] = progress
            workflows_df.at[workflow_idx, 'last_updated'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 전체 진행률 재계산
            sales_progress = workflows_df.at[workflow_idx, 'sales_progress'] if workflows_df.at[workflow_idx, 'has_sales_items'] else 100.0
            
            if workflows_df.at[workflow_idx, 'has_sales_items']:
                overall_progress = (sales_progress + progress) / 2
            else:
                overall_progress = progress
            
            workflows_df.at[workflow_idx, 'overall_progress'] = overall_progress
            
            # 파일 저장
            workflows_df.to_csv(self.workflow_file, index=False, encoding='utf-8-sig')
            
            return True, f"서비스 프로세스가 {next_stage_name} 단계로 진행되었습니다."
            
        except Exception as e:
            print(f"서비스 단계 진행 중 오류: {e}")
            return False, f"단계 진행 중 오류가 발생했습니다: {str(e)}"
    
    def get_workflow_statistics(self):
        """워크플로우 통계 정보"""
        try:
            workflows_df = self.get_all_workflows()
            
            if len(workflows_df) == 0:
                return {}
            
            stats = {
                'total_workflows': len(workflows_df),
                'sales_workflows': len(workflows_df[workflows_df['workflow_type'].isin(['sales', 'mixed'])]),
                'service_workflows': len(workflows_df[workflows_df['workflow_type'].isin(['service', 'mixed'])]),
                'mixed_workflows': len(workflows_df[workflows_df['workflow_type'] == 'mixed']),
                'active_workflows': len(workflows_df[workflows_df['overall_status'] == 'active']),
                'completed_workflows': len(workflows_df[workflows_df['overall_status'] == 'completed']),
                'average_progress': workflows_df['overall_progress'].mean()
            }
            
            # 제품 타입별 분포
            product_type_counts = {}
            for _, workflow in workflows_df.iterrows():
                try:
                    product_types = json.loads(workflow['product_types'])
                    for ptype in product_types:
                        product_type_counts[ptype] = product_type_counts.get(ptype, 0) + 1
                except:
                    pass
            
            stats['product_type_distribution'] = product_type_counts
            
            return stats
            
        except Exception as e:
            print(f"통계 계산 중 오류: {e}")
            return {}