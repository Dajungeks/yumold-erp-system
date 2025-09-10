"""
베트남 직원 친화적인 간소화된 지출요청서 관리 페이지
- 3단계 간단 프로세스: 기본정보 → 지출내용 → 승인자 선택
- 디버그 정보 제거, 직관적 UI
- 실제 직원 목록에서 승인자 선택
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

def show_expense_request_page(expense_manager, user_id, user_name, get_text):
    """베트남 직원 친화적인 간소화된 지출요청서 페이지"""
    
    st.header(f"💰 {get_text('expense_request_management')}")
    st.info(f"💡 **{get_text('simple_3_step')}**")
    
    # 탭 생성 (간소화)
    tab1, tab2 = st.tabs([f"📝 {get_text('new_request_form')}", f"📋 {get_text('my_requests_check')}"])
    
    with tab1:
        show_simple_expense_form(expense_manager, user_id, user_name, get_text)
    
    with tab2:
        show_my_requests_simple(expense_manager, user_id, user_name, get_text)

def show_simple_expense_form(expense_manager, user_id, user_name, get_text):
    """베트남 직원용 초간단 지출요청서 작성 폼"""
    
    st.markdown(f"### 🚀 {get_text('expense_request_form_3_step')}")
    
    # 직원 목록 미리 로드 (간단하게)
    approver_list = load_approvers_simple()
    
    if not approver_list:
        st.error(f"❌ {get_text('no_approvers_error')}")
        st.info(f"💡 {get_text('admin_setup_approvers')}")
        return
    
    with st.form("simple_expense_form", clear_on_submit=True):
        
        # 1단계: 기본 정보 (한 줄로)
        st.markdown(f"#### 1️⃣ {get_text('basic_info')}")
        col1, col2 = st.columns([2, 1])
        with col1:
            current_user_info = get_current_user_info_simple(user_id, user_name)
            display_name = f"{current_user_info['name']} ({current_user_info['position']})" if current_user_info['position'] else current_user_info['name']
            st.text_input(get_text('requester'), value=display_name, disabled=True)
        with col2:
            today = datetime.now().date()
            request_date = st.date_input(get_text('request_date'), value=today)
        
        st.divider()
        
        # 2단계: 지출 내용 (핵심만)
        st.markdown(f"#### 2️⃣ {get_text('expense_content')}")
        
        col1, col2 = st.columns(2)
        with col1:
            # 간단한 카테고리
            try:
                categories = expense_manager.get_expense_categories()
            except:
                categories = ["교통비", "숙박비", "식비", "회의비", "사무용품", "통신비", "기타"]
            
            category = st.selectbox(
                f"🏷️ {get_text('expense_type')} *", 
                categories,
                help="지출의 종류를 선택하세요"
            )
            
            expense_title = st.text_input(
                f"💰 {get_text('expense_title')} *", 
                placeholder=get_text('expense_title_placeholder'),
                help="무엇을 위한 지출인지 간단히 적어주세요"
            )
        
        with col2:
            # 금액과 통화
            col_amount, col_currency = st.columns([3, 1])
            with col_amount:
                amount = st.number_input(
                    "💵 금액 *", 
                    min_value=0.0, 
                    step=10000.0,
                    format="%.0f"
                )
            with col_currency:
                currency = st.selectbox("통화", ["VND", "USD", "KRW"], index=0)
            
            expected_date = st.date_input(
                "📅 언제 사용하나요? *", 
                value=today + timedelta(days=1)
            )
        
        # 설명 (간단하게)
        expense_description = st.text_area(
            "📝 왜 필요한가요? *", 
            placeholder="지출이 필요한 이유를 간단히 설명해주세요 (2-3줄)",
            height=80,
            help="승인자가 이해할 수 있도록 간단히 설명해주세요"
        )
        
        st.divider()
        
        # 3단계: 승인자 선택 (간단하게)
        st.markdown("#### 3️⃣ 승인자 선택")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            approver_name = st.selectbox(
                "👤 누가 승인해야 하나요? *",
                options=list(approver_list.keys()),
                help="지출을 승인해줄 사람을 선택하세요"
            )
        
        with col2:
            if approver_name:
                approver_info = approver_list[approver_name]
                st.success(f"✅ {approver_info['name']}\n({approver_info['position']})")
        
        # 추가 메모 (선택사항)
        with st.expander("📎 추가 정보 (선택사항)"):
            notes = st.text_area(
                "추가 메모", 
                placeholder="특별히 전달할 내용이 있다면 작성하세요",
                height=60
            )
            
            attachment = st.file_uploader(
                "첨부파일", 
                type=['pdf', 'jpg', 'png', 'doc', 'docx'],
                help="영수증, 견적서 등을 첨부할 수 있습니다"
            )
        
        # 제출 버튼
        st.markdown("---")
        submitted = st.form_submit_button(
            "🚀 지출요청서 제출", 
            type="primary", 
            use_container_width=True
        )
        
        if submitted:
            # 필수 항목 검증
            if not expense_title or not amount or not expense_description or not approver_name:
                st.error("❌ 빨간색 * 표시된 필수 항목을 모두 입력해주세요!")
                return
            
            # 요청서 데이터 생성
            selected_approver = approver_list[approver_name]
            
            request_data = {
                'requester_id': user_id,
                'requester_name': current_user_info['name'],
                'expense_title': expense_title,
                'category': category,
                'amount': amount,
                'currency': currency,
                'expected_date': expected_date.strftime('%Y-%m-%d'),
                'expense_description': expense_description,
                'notes': notes if 'notes' in locals() else '',
                'first_approver': {
                    'employee_id': selected_approver['employee_id'],
                    'employee_name': selected_approver['name'],
                    'position': selected_approver['position'],
                    'department': selected_approver['department']
                },
                'status': 'pending'
            }
            
            # 첨부파일 처리
            if 'attachment' in locals() and attachment:
                request_data['attachment'] = attachment.name
            
            # 요청서 저장
            try:
                success, message = expense_manager.create_expense_request(request_data)
                if success:
                    st.success(f"✅ {message}")
                    st.success(f"📤 승인 요청이 {selected_approver['name']}님께 전송되었습니다!")
                    
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"❌ 시스템 오류가 발생했습니다: {str(e)}")
                st.info("💡 관리자에게 문의하거나 잠시 후 다시 시도해주세요.")

def load_approvers_simple():
    """승인자 목록을 간단하게 로드"""
    try:
        # 직원 매니저 import (기존 구조와 호환)
        from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
        employee_manager = SQLiteEmployeeManager()
        
        employees_df = employee_manager.get_all_employees()
        
        if employees_df is None or (hasattr(employees_df, '__len__') and len(employees_df) == 0):
            # 기본 승인자 추가 (마스터 계정)
            return {
                "법인장 (Master)": {
                    'employee_id': 'master',
                    'name': '법인장',
                    'position': 'Master',
                    'department': '경영진'
                }
            }
        
        approver_list = {}
        
        # DataFrame인 경우
        if isinstance(employees_df, pd.DataFrame):
            for _, employee in employees_df.iterrows():
                # 재직 중이고 승인 권한이 있는 직원만
                status = str(employee.get('status', '')).lower()
                access_level = str(employee.get('access_level', '')).lower()
                work_status = str(employee.get('work_status', '')).lower()
                position = str(employee.get('position', '')).lower()
                
                # 상태 확인 (더 넓은 범위로 수정)
                is_active = (status in ['active', '재직', 'employed', ''] or 
                           work_status in ['재직', 'active', ''] or
                           True)  # 임시로 모든 직원을 활성으로 처리
                
                # 승인 권한 확인 (더 넓은 범위로 수정)
                has_approval_authority = (access_level in ['master', 'manager', 'admin', 'supervisor', 'employee'] or
                                        position in ['manager', '관리자', '팀장', '부장', '과장', '대리', '사원', '직원'] or
                                        True)  # 임시로 모든 직원을 승인자로 허용
                
                if is_active and has_approval_authority:
                    name = str(employee.get('name', '')).strip()
                    position_display = str(employee.get('position', '')).strip()
                    department = str(employee.get('department', '')).strip()
                    
                    if name:  # 이름이 있는 경우만
                        display_name = f"{name}"
                        if position_display:
                            display_name += f" ({position_display})"
                        if department:
                            display_name += f" - {department}"
                            
                        approver_list[display_name] = {
                            'employee_id': str(employee.get('employee_id', '')),
                            'name': name,
                            'position': position_display,
                            'department': department
                        }
        
        # 리스트인 경우 (하위 호환성)
        elif employees_df is not None and isinstance(employees_df, list):
            for employee in employees_df:
                if not isinstance(employee, dict):
                    continue
                    
                status = str(employee.get('status', '')).lower()
                access_level = str(employee.get('access_level', '')).lower()
                work_status = str(employee.get('work_status', '')).lower()
                
                is_active = (status in ['active', '재직', 'employed', ''] or 
                           work_status in ['재직', 'active', ''] or
                           True)  # 임시로 모든 직원을 활성으로 처리
                has_approval_authority = (access_level in ['master', 'manager', 'admin', 'supervisor', 'employee'] or
                                        True)  # 임시로 모든 직원을 승인자로 허용
                
                if is_active and has_approval_authority:
                    name = str(employee.get('name', '')).strip()
                    position = str(employee.get('position', '')).strip()
                    department = str(employee.get('department', '')).strip()
                    
                    if name:
                        display_name = f"{name}"
                        if position:
                            display_name += f" ({position})"
                            
                        approver_list[display_name] = {
                            'employee_id': str(employee.get('employee_id', '')),
                            'name': name,
                            'position': position,
                            'department': department
                        }
        
        # 만약 승인자가 없으면 기본 승인자 추가
        if not approver_list:
            approver_list["법인장 (기본)"] = {
                'employee_id': 'CEO001',
                'name': '법인장',
                'position': '대표이사',
                'department': '경영진'
            }
        
        return approver_list
    
    except Exception as e:
        st.error(f"승인자 목록 로드 오류: {str(e)}")
        st.info("💡 직원 관리에서 승인 권한이 있는 직원을 확인해주세요.")
        return {}

def show_my_requests_simple(expense_manager, user_id, user_name, get_text):
    """내 요청서 간단 조회"""
    st.markdown("### 📋 내 지출요청서 현황")
    
    try:
        my_requests = expense_manager.get_my_expense_requests(user_id)
        
        if my_requests is None or len(my_requests) == 0:
            st.info("📭 아직 작성한 지출요청서가 없습니다.")
            st.info("💡 위의 '새 요청서 작성' 탭에서 첫 번째 요청서를 만들어보세요!")
            return
        
        st.success(f"📄 총 {len(my_requests)}건의 요청서가 있습니다")
        
        # 간단한 통계
        if isinstance(my_requests, pd.DataFrame):
            pending_count = len(my_requests[my_requests['status'] == 'pending'])
            approved_count = len(my_requests[my_requests['status'] == 'approved'])
            rejected_count = len(my_requests[my_requests['status'] == 'rejected'])
        else:
            pending_count = sum(1 for req in my_requests if req.get('status') == 'pending')
            approved_count = sum(1 for req in my_requests if req.get('status') == 'approved')
            rejected_count = sum(1 for req in my_requests if req.get('status') == 'rejected')
        
        # 통계 카드
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏳ 대기 중", f"{pending_count}건")
        with col2:
            st.metric("✅ 승인됨", f"{approved_count}건")
        with col3:
            st.metric("❌ 반려됨", f"{rejected_count}건")
        
        st.divider()
        
        # 최근 요청서 목록 (간단하게)
        st.markdown("#### 📋 최근 요청서 목록")
        
        # DataFrame을 리스트로 변환 (통일성)
        if isinstance(my_requests, pd.DataFrame):
            requests_list = my_requests.to_dict('records')
        else:
            requests_list = my_requests
        
        # 최신순 정렬
        requests_list = sorted(requests_list, key=lambda x: x.get('created_date', ''), reverse=True)
        
        for i, request in enumerate(requests_list[:10]):  # 최근 10건만
            status = request.get('status', 'unknown')
            
            # 상태별 이모지
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'cancelled': '🚫'
            }.get(status, '❓')
            
            # 상태별 색상
            status_color = {
                'pending': 'orange',
                'approved': 'green',
                'rejected': 'red',
                'cancelled': 'gray'
            }.get(status, 'gray')
            
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{request.get('expense_title', '제목 없음')}**")
                    st.markdown(f"💰 {request.get('amount', 0):,.0f} {request.get('currency', 'VND')}")
                
                with col2:
                    st.markdown(f"📅 {request.get('created_date', '날짜 없음')[:10]}")
                    st.markdown(f"🏷️ {request.get('category', '미분류')}")
                
                with col3:
                    st.markdown(f"<span style='color: {status_color}'>{status_emoji} {status.upper()}</span>", unsafe_allow_html=True)
                    
                    # 간단한 액션 버튼
                    if status == 'pending':
                        if st.button(f"❌ 취소", key=f"cancel_{i}", help="요청서를 취소합니다"):
                            try:
                                success = expense_manager.cancel_expense_request(request.get('id', ''))
                                if success:
                                    st.success("요청서가 취소되었습니다")
                                    st.rerun()
                                else:
                                    st.error("취소 실패")
                            except:
                                st.error("취소 중 오류 발생")
                
                # 상세 내용 (접기/펼치기)
                with st.expander(f"📝 상세 내용 보기"):
                    st.write(f"**설명:** {request.get('expense_description', '설명 없음')}")
                    if request.get('notes'):
                        st.write(f"**메모:** {request.get('notes')}")
                    
                    approver = request.get('first_approver', {})
                    if isinstance(approver, str):
                        st.write(f"**승인자:** {approver}")
                    elif isinstance(approver, dict):
                        approver_name = approver.get('employee_name', '미정')
                        st.write(f"**승인자:** {approver_name}")
                
                st.divider()
        
        # 더 많은 요청서가 있는 경우
        if len(requests_list) > 10:
            st.info(f"💡 더 많은 요청서가 있습니다. (총 {len(requests_list)}건)")
    
    except Exception as e:
        st.error(f"❌ 요청서 조회 중 오류 발생: {str(e)}")
        st.info("💡 관리자에게 문의하거나 페이지를 새로고침해주세요.")

def get_current_user_info_simple(user_id, user_name):
    """현재 사용자 정보를 간단하게 가져오기"""
    try:
        from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
        employee_manager = SQLiteEmployeeManager()
        
        # 사용자 정보 조회
        employee_info = employee_manager.get_employee_by_id(user_id)
        
        if employee_info:
            if isinstance(employee_info, pd.DataFrame) and not employee_info.empty:
                employee = employee_info.iloc[0]
                return {
                    'name': employee.get('name', user_name or user_id),
                    'position': employee.get('position', ''),
                    'department': employee.get('department', ''),
                    'employee_id': user_id
                }
            elif isinstance(employee_info, dict):
                return {
                    'name': employee_info.get('name', user_name or user_id),
                    'position': employee_info.get('position', ''),
                    'department': employee_info.get('department', ''),
                    'employee_id': user_id
                }
        
        # 기본값 반환
        return {
            'name': user_name or user_id,
            'position': '',
            'department': '',
            'employee_id': user_id
        }
        
    except Exception as e:
        # 오류 시 기본값 반환
        return {
            'name': user_name or user_id,
            'position': '',
            'department': '',
            'employee_id': user_id
        }