# -*- coding: utf-8 -*-
"""
지출요청서 관리 시스템
승인자 선택형 지출요청 및 승인 프로세스 관리
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

class ExpenseRequestManager:
    def __init__(self):
        self.requests_file = 'data/expense_requests.csv'
        self.approvals_file = 'data/expense_approvals.csv'
        self.approver_pool_file = 'data/approver_pool.csv'
        self.budgets_file = 'data/department_budgets.csv'
        
        self.ensure_data_files()
        self.init_approver_pool()
        
        # 지출 카테고리 정의
        self.expense_categories = [
            '업무용품', '출장비', '교육비', '회식비', 
            '시설비', '마케팅비', '기타'
        ]
        
        # 승인 상태 정의
        self.approval_statuses = [
            '대기', '진행중', '승인', '반려', '완료'
        ]
    
    def ensure_data_files(self):
        """데이터 파일들이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        
        # 지출요청서 파일
        if not os.path.exists(self.requests_file):
            requests_df = pd.DataFrame(columns=[
                'request_id', 'requester_id', 'requester_name', 'request_date',
                'expense_title', 'expense_description', 'category', 'amount',
                'currency', 'expected_date', 'status', 'current_step',
                'total_steps', 'attachment_path', 'notes', 'created_date',
                'updated_date'
            ])
            requests_df.to_csv(self.requests_file, index=False, encoding='utf-8-sig')
        
        # 승인이력 파일
        if not os.path.exists(self.approvals_file):
            approvals_df = pd.DataFrame(columns=[
                'approval_id', 'request_id', 'approval_step', 'approver_id',
                'approver_name', 'approval_order', 'approval_date', 'result',
                'comments', 'is_required'
            ])
            approvals_df.to_csv(self.approvals_file, index=False, encoding='utf-8-sig')
        
        # 승인자 풀 파일
        if not os.path.exists(self.approver_pool_file):
            approver_df = pd.DataFrame(columns=[
                'employee_id', 'employee_name', 'department', 'position',
                'approval_level', 'max_approval_amount', 'is_active'
            ])
            approver_df.to_csv(self.approver_pool_file, index=False, encoding='utf-8-sig')
        
        # 부서예산 파일
        if not os.path.exists(self.budgets_file):
            budgets_df = pd.DataFrame(columns=[
                'budget_id', 'department', 'year', 'month', 'category',
                'budget_amount', 'spent_amount', 'remaining_amount'
            ])
            budgets_df.to_csv(self.budgets_file, index=False, encoding='utf-8-sig')
    
    def init_approver_pool(self):
        """승인자 풀 초기 데이터를 설정합니다."""
        try:
            df = pd.read_csv(self.approver_pool_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                # 기본 승인자 데이터 추가
                initial_approvers = [
                    {'employee_id': 'MGR001', 'employee_name': '김팀장', 'department': '영업부', 'position': '팀장', 'approval_level': 1, 'max_approval_amount': 1000000, 'is_active': True},
                    {'employee_id': 'MGR002', 'employee_name': '이부장', 'department': '영업부', 'position': '부장', 'approval_level': 2, 'max_approval_amount': 5000000, 'is_active': True},
                    {'employee_id': 'MGR003', 'employee_name': '박팀장', 'department': '기술부', 'position': '팀장', 'approval_level': 1, 'max_approval_amount': 1000000, 'is_active': True},
                    {'employee_id': 'MGR004', 'employee_name': '최부장', 'department': '기술부', 'position': '부장', 'approval_level': 2, 'max_approval_amount': 5000000, 'is_active': True},
                    {'employee_id': 'FIN001', 'employee_name': '재무담당자', 'department': '재무부', 'position': '차장', 'approval_level': 3, 'max_approval_amount': 10000000, 'is_active': True},
                    {'employee_id': 'CEO001', 'employee_name': '대표이사', 'department': '경영진', 'position': '대표', 'approval_level': 4, 'max_approval_amount': 50000000, 'is_active': True}
                ]
                
                df = pd.concat([df, pd.DataFrame(initial_approvers)], ignore_index=True)
                df.to_csv(self.approver_pool_file, index=False, encoding='utf-8-sig')
                
        except Exception as e:
            print(f"승인자 풀 초기화 중 오류: {e}")
    
    def create_expense_request(self, request_data, approval_settings):
        """지출요청서를 생성합니다."""
        try:
            # 요청서 ID 생성
            request_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 기본 요청서 데이터
            new_request = {
                'request_id': request_id,
                'requester_id': request_data.get('requester_id', ''),
                'requester_name': request_data.get('requester_name', ''),
                'request_date': datetime.now().strftime('%Y-%m-%d'),
                'expense_title': request_data.get('expense_title', ''),
                'expense_description': request_data.get('expense_description', ''),
                'category': request_data.get('category', ''),
                'amount': float(request_data.get('amount', 0)),
                'currency': request_data.get('currency', 'USD'),
                'expected_date': request_data.get('expected_date', ''),
                'status': '대기',
                'current_step': 1,
                'total_steps': len(approval_settings),
                'attachment_path': request_data.get('attachment_path', ''),
                'notes': request_data.get('notes', ''),
                'created_date': current_time,
                'updated_date': current_time
            }
            
            # 요청서 저장
            requests_df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            requests_df = pd.concat([requests_df, pd.DataFrame([new_request])], ignore_index=True)
            requests_df.to_csv(self.requests_file, index=False, encoding='utf-8-sig')
            
            # 승인 설정 저장
            approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
            
            for step, approver_info in enumerate(approval_settings, 1):
                approval_record = {
                    'approval_id': f"APP{datetime.now().strftime('%Y%m%d%H%M%S')}{step}",
                    'request_id': request_id,
                    'approval_step': step,
                    'approver_id': approver_info.get('approver_id', ''),
                    'approver_name': approver_info.get('approver_name', ''),
                    'approval_order': step,
                    'approval_date': '',
                    'result': '대기',
                    'comments': '',
                    'is_required': approver_info.get('is_required', True)
                }
                approvals_df = pd.concat([approvals_df, pd.DataFrame([approval_record])], ignore_index=True)
            
            approvals_df.to_csv(self.approvals_file, index=False, encoding='utf-8-sig')
            
            return True, f"지출요청서가 성공적으로 등록되었습니다. (요청번호: {request_id})"
            
        except Exception as e:
            return False, f"지출요청서 등록 중 오류: {e}"
    
    def get_approver_pool(self, department=None, min_approval_level=None):
        """승인자 풀을 조회합니다. (실제 직원 데이터베이스에서)"""
        try:
            # 먼저 직원 데이터에서 승인자 목록을 가져옵니다
            import streamlit as st
            employee_manager = getattr(st.session_state, 'employee_manager', None)
            
            if employee_manager:
                # 실제 직원 데이터 가져오기
                try:
                    employees_df = employee_manager.get_all_employees()
                    
                    # DataFrame 타입 확인 및 변환
                    if not isinstance(employees_df, pd.DataFrame):
                        if hasattr(employees_df, 'to_frame'):
                            employees_df = employees_df.to_frame()
                        elif isinstance(employees_df, list):
                            employees_df = pd.DataFrame(employees_df)
                        else:
                            print(f"직원 데이터 타입 확인 필요: {type(employees_df)}")
                            return []
                    
                    if len(employees_df) > 0:
                        # 재직 중인 직원만 필터링
                        if 'work_status' in employees_df.columns:
                            active_employees = employees_df[employees_df['work_status'] == '재직'].copy()
                        else:
                            active_employees = employees_df.copy()  # work_status 컬럼이 없으면 모든 직원
                        
                        if len(active_employees) == 0:
                            print("재직 중인 직원이 없습니다.")
                            return []
                        
                        # 승인자 정보를 위한 컬럼 추가 (모든 직급이 승인 가능)
                        position_level_map = {
                            '사원': 1, '주임': 1, '대리': 2, '과장': 2, 
                            '차장': 3, '부장': 3, '팀장': 3, '부차장': 3,
                            '이사': 4, '상무': 4, '전무': 5, '부사장': 5, 
                            '사장': 6, '회장': 6, '대표이사': 6
                        }
                        
                        # position 컬럼이 있는지 확인
                        if 'position' in active_employees.columns:
                            active_employees['approval_level'] = active_employees['position'].map(position_level_map).fillna(1)
                        else:
                            active_employees['approval_level'] = 1  # 기본값
                        
                        # 최대 승인 금액 설정 (무제한으로 설정)
                        active_employees['max_approval_amount'] = 999999999999  # 모든 금액 승인 가능
                        
                        # 필요한 컬럼 확인 및 선택
                        required_cols = ['employee_id', 'name', 'department', 'position']
                        available_cols = [col for col in required_cols if col in active_employees.columns]
                        
                        if not available_cols:
                            print("필요한 컬럼이 없습니다.")
                            return []
                        
                        # 기본 컬럼들 추가
                        available_cols.extend(['approval_level', 'max_approval_amount'])
                        approver_data = active_employees[available_cols].copy()
                        
                        # name 컬럼을 employee_name으로 변경
                        if 'name' in approver_data.columns:
                            approver_data = approver_data.rename(columns={'name': 'employee_name'})
                        
                        approver_data['is_active'] = True
                        
                        # 부서 필터링
                        if department and 'department' in approver_data.columns:
                            approver_data = approver_data[approver_data['department'] == department]
                        
                        # 승인 레벨 필터링
                        if min_approval_level:
                            approver_data = approver_data[approver_data['approval_level'] >= min_approval_level]
                        
                        return approver_data.to_dict('records')
                        
                except Exception as e:
                    print(f"직원 데이터 처리 중 오류: {e}")
                    # fallback으로 계속 진행
            
            # fallback: 기존 승인자 풀 파일에서 읽기
            df = pd.read_csv(self.approver_pool_file, encoding='utf-8-sig')
            
            # 활성 승인자만 필터링
            df = df[df['is_active'] == True]
            
            # 부서 필터링
            if department:
                df = df[df['department'] == department]
            
            # 승인 레벨 필터링
            if min_approval_level:
                df = df[df['approval_level'] >= min_approval_level]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"승인자 풀 조회 중 오류: {e}")
            return []
    
    def get_my_requests(self, requester_id):
        """내 요청서 목록을 조회합니다."""
        try:
            df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            my_requests = df[df['requester_id'] == requester_id].copy()
            
            # 날짜순으로 정렬 (최신순)
            my_requests = my_requests.sort_values('created_date', ascending=False)
            
            return my_requests.to_dict('records')
            
        except Exception as e:
            print(f"내 요청서 조회 중 오류: {e}")
            return []
    
    def get_pending_approvals(self, approver_id):
        """승인 대기 목록을 조회합니다."""
        try:
            # 승인 대기 중인 건들 조회
            approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
            requests_df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            # 데이터 타입 통일 (모두 문자열로 변환)
            approvals_df['approver_id'] = approvals_df['approver_id'].astype(str)
            approver_id = str(approver_id)
            
            # 해당 승인자의 대기 건들
            pending_approvals = approvals_df[
                (approvals_df['approver_id'] == approver_id) & 
                (approvals_df['result'] == '대기')
            ]
            
            # 요청서 정보와 조인
            pending_requests = []
            for _, approval in pending_approvals.iterrows():
                request_info = requests_df[requests_df['request_id'] == approval['request_id']]
                if len(request_info) > 0:
                    request_data = request_info.iloc[0].to_dict()
                    request_data['approval_step'] = approval['approval_step']
                    request_data['approval_id'] = approval['approval_id']
                    pending_requests.append(request_data)
            return pending_requests
            
        except Exception as e:
            print(f"승인 대기 목록 조회 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_approval(self, approval_id, approver_id, result, comments=""):
        """승인 처리를 합니다."""
        try:
            # 승인 이력 업데이트
            approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
            requests_df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            # 해당 승인 건 찾기
            approval_idx = approvals_df[approvals_df['approval_id'] == approval_id].index
            if len(approval_idx) == 0:
                return False, "승인 건을 찾을 수 없습니다."
            
            approval_idx = approval_idx[0]
            request_id = approvals_df.loc[approval_idx, 'request_id']
            
            # 승인 이력 업데이트
            approvals_df.loc[approval_idx, 'result'] = result
            approvals_df.loc[approval_idx, 'comments'] = comments
            approvals_df.loc[approval_idx, 'approval_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 요청서 상태 업데이트
            request_idx = requests_df[requests_df['request_id'] == request_id].index[0]
            
            if result == '승인':
                # 다음 승인 단계 확인
                current_step = requests_df.loc[request_idx, 'current_step']
                total_steps = requests_df.loc[request_idx, 'total_steps']
                
                if current_step < total_steps:
                    # 다음 승인 단계로 진행
                    requests_df.loc[request_idx, 'current_step'] = current_step + 1
                    requests_df.loc[request_idx, 'status'] = '진행중'
                else:
                    # 모든 승인 완료
                    requests_df.loc[request_idx, 'status'] = '승인'
            else:
                # 반려
                requests_df.loc[request_idx, 'status'] = '반려'
            
            requests_df.loc[request_idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 저장
            approvals_df.to_csv(self.approvals_file, index=False, encoding='utf-8-sig')
            requests_df.to_csv(self.requests_file, index=False, encoding='utf-8-sig')
            
            return True, f"승인 처리가 완료되었습니다. (결과: {result})"
            
        except Exception as e:
            return False, f"승인 처리 중 오류: {e}"
    
    def get_request_details(self, request_id):
        """요청서 상세 정보를 조회합니다."""
        try:
            requests_df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
            
            # 요청서 정보
            request_info = requests_df[requests_df['request_id'] == request_id]
            if len(request_info) == 0:
                return None, None
            
            request_data = request_info.iloc[0].to_dict()
            
            # 승인 이력
            approval_history = approvals_df[approvals_df['request_id'] == request_id].copy()
            approval_history = approval_history.sort_values('approval_step')
            
            return request_data, approval_history.to_dict('records')
            
        except Exception as e:
            print(f"요청서 상세 조회 중 오류: {e}")
            return None, None
    
    def get_expense_statistics(self, department=None, start_date=None, end_date=None):
        """지출 통계를 조회합니다."""
        try:
            df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            # 날짜 필터링
            if start_date and end_date:
                df['request_date'] = pd.to_datetime(df['request_date'])
                df = df[
                    (df['request_date'] >= start_date) & 
                    (df['request_date'] <= end_date)
                ]
            
            # 승인된 건만 필터링
            approved_requests = df[df['status'].isin(['승인', '완료'])]
            
            if len(approved_requests) == 0:
                return {
                    'total_amount': 0,
                    'total_count': 0,
                    'by_category': {},
                    'by_status': {},
                    'average_amount': 0
                }
            
            # 통계 계산
            stats = {
                'total_amount': float(approved_requests['amount'].sum()),
                'total_count': len(approved_requests),
                'by_category': approved_requests.groupby('category')['amount'].sum().to_dict(),
                'by_status': df['status'].value_counts().to_dict(),
                'average_amount': float(approved_requests['amount'].mean())
            }
            
            return stats
            
        except Exception as e:
            print(f"지출 통계 조회 중 오류: {e}")
            return {}
    
    def get_expense_categories(self):
        """지출 카테고리 목록을 반환합니다."""
        return self.expense_categories
    
    def get_approval_statuses(self):
        """승인 상태 목록을 반환합니다."""
        return self.approval_statuses
    
    def add_approver(self, approver_data):
        """새로운 승인자를 추가합니다."""
        try:
            # 기존 승인자 풀 로드
            try:
                df = pd.read_csv(self.approver_pool_file, encoding='utf-8-sig')
            except FileNotFoundError:
                # 파일이 없으면 빈 데이터프레임 생성
                df = pd.DataFrame(columns=['employee_id', 'employee_name', 'department', 'position', 'approval_level', 'max_approval_amount', 'is_active'])
            
            # 중복 체크
            if len(df) > 0 and approver_data['employee_id'] in df['employee_id'].values:
                print(f"이미 등록된 직원입니다: {approver_data['employee_id']}")
                return False
            
            # 새 승인자 추가
            new_row = pd.DataFrame([approver_data])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # 파일 저장
            df.to_csv(self.approver_pool_file, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            print(f"승인자 추가 중 오류: {e}")
            return False
    
    def update_expense_request(self, request_id, updated_data):
        """지출요청서를 수정합니다."""
        try:
            df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            # 해당 요청서 찾기
            request_index = df[df['request_id'] == request_id].index
            
            if len(request_index) == 0:
                return False, "요청서를 찾을 수 없습니다."
            
            # 수정 가능한 상태 확인 (대기 상태만 수정 가능)
            current_status = df.loc[request_index[0], 'status']
            if current_status != '대기':
                return False, f"승인 진행 중인 요청서는 수정할 수 없습니다. (현재 상태: {current_status})"
            
            # 데이터 업데이트
            for key, value in updated_data.items():
                if key in df.columns:
                    df.loc[request_index[0], key] = value
            
            # 수정 시간 업데이트
            df.loc[request_index[0], 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 파일 저장
            df.to_csv(self.requests_file, index=False, encoding='utf-8-sig')
            
            return True, "요청서가 성공적으로 수정되었습니다."
            
        except Exception as e:
            return False, f"요청서 수정 중 오류: {str(e)}"
    
    def delete_expense_request(self, request_id):
        """지출요청서를 삭제합니다."""
        try:
            df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            # 해당 요청서 찾기
            request_row = df[df['request_id'] == request_id]
            
            if len(request_row) == 0:
                return False, "요청서를 찾을 수 없습니다."
            
            # 삭제 가능한 상태 확인 (대기 또는 반려 상태만 삭제 가능)
            current_status = request_row.iloc[0]['status']
            if current_status not in ['대기', '반려']:
                return False, f"승인 진행 중이거나 완료된 요청서는 삭제할 수 없습니다. (현재 상태: {current_status})"
            
            # 요청서 삭제
            df = df[df['request_id'] != request_id]
            df.to_csv(self.requests_file, index=False, encoding='utf-8-sig')
            
            # 관련 승인 이력도 삭제
            try:
                approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
                approvals_df = approvals_df[approvals_df['request_id'] != request_id]
                approvals_df.to_csv(self.approvals_file, index=False, encoding='utf-8-sig')
            except:
                pass  # 승인 이력 파일이 없어도 요청서 삭제는 진행
            
            return True, "요청서가 성공적으로 삭제되었습니다."
            
        except Exception as e:
            return False, f"요청서 삭제 중 오류: {str(e)}"
    
    def get_expense_request_by_id(self, request_id):
        """특정 지출요청서 정보를 가져옵니다."""
        try:
            df = pd.read_csv(self.requests_file, encoding='utf-8-sig')
            
            request_row = df[df['request_id'] == request_id]
            
            if len(request_row) == 0:
                return None
            
            return request_row.iloc[0].to_dict()
            
        except Exception as e:
            print(f"요청서 조회 중 오류: {e}")
            return None
    
    def generate_expense_request_pdf(self, request_id):
        """지출요청서 PDF를 생성합니다."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from reportlab.pdfbase import pdfutils
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics
            import os
            
            # 한글 폰트 등록
            try:
                font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Korean', font_path))
                    font_name = 'Korean'
                else:
                    font_name = 'Helvetica'
            except:
                font_name = 'Helvetica'
            
            # 요청서 데이터 가져오기
            request_data = self.get_expense_request_by_id(request_id)
            if not request_data:
                return None, "요청서를 찾을 수 없습니다."
            
            # PDF 파일명 생성
            pdf_filename = f"expense_request_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(pdf_filename, pagesize=A4,
                                  rightMargin=inch, leftMargin=inch,
                                  topMargin=inch, bottomMargin=inch)
            
            # 스타일 설정
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT
            )
            
            # PDF 내용 구성
            story = []
            
            # 제목
            title = Paragraph("지출요청서", title_style)
            story.append(title)
            story.append(Spacer(1, 12))
            
            # 요청서 정보 테이블
            request_info_data = [
                ['요청서 번호', request_data.get('request_id', '')],
                ['요청자', request_data.get('requester_name', '')],
                ['요청일자', request_data.get('request_date', '')],
                ['상태', request_data.get('status', '')],
                ['카테고리', request_data.get('category', '')],
                ['금액', f"{float(request_data.get('amount', 0)):,.0f} {request_data.get('currency', 'USD')}"],
                ['예상 지출일', request_data.get('expected_date', '')]
            ]
            
            request_info_table = Table(request_info_data, colWidths=[2*inch, 4*inch])
            request_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(request_info_table)
            story.append(Spacer(1, 20))
            
            # 지출 내역
            story.append(Paragraph("지출 내역", heading_style))
            
            expense_details = [
                ['항목', '내용'],
                ['지출 제목', request_data.get('expense_title', '')],
                ['지출 설명', request_data.get('expense_description', '')],
                ['비고', request_data.get('notes', '')]
            ]
            
            expense_table = Table(expense_details, colWidths=[1.5*inch, 4.5*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(expense_table)
            story.append(Spacer(1, 30))
            
            # 승인 정보 (있는 경우)
            try:
                approvals_df = pd.read_csv(self.approvals_file, encoding='utf-8-sig')
                request_approvals = approvals_df[approvals_df['request_id'] == request_id]
                
                if len(request_approvals) > 0:
                    story.append(Paragraph("승인 이력", heading_style))
                    
                    approval_data = [['승인 단계', '승인자', '승인일', '결과', '의견']]
                    
                    for _, approval in request_approvals.iterrows():
                        approval_data.append([
                            str(approval.get('approval_step', '')),
                            approval.get('approver_name', ''),
                            approval.get('approval_date', ''),
                            approval.get('result', ''),
                            approval.get('comments', '')
                        ])
                    
                    approval_table = Table(approval_data, colWidths=[0.8*inch, 1.5*inch, 1.2*inch, 1*inch, 1.5*inch])
                    approval_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(approval_table)
            except:
                pass
            
            # PDF 생성
            doc.build(story)
            
            return pdf_filename, "PDF가 성공적으로 생성되었습니다."
            
        except Exception as e:
            return None, f"PDF 생성 중 오류: {str(e)}"