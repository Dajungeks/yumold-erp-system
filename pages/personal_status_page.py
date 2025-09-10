import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

def show_personal_status_page(employee_manager, vacation_manager, approval_manager, user_permissions, get_text):
    """개인 상태 관리 페이지를 표시합니다."""
    
    # 메인 제목 - HTML 제거하고 순수 Streamlit으로
    st.header(f"👤 {get_text('personal_status_management')}")
    
    # 현재 로그인한 사용자 정보
    current_user_id = st.session_state.get('user_id', '')
    current_user_type = st.session_state.get('user_type', '')
    
    if current_user_type not in ["employee", "master"]:
        st.warning("직원만 접근 가능한 페이지입니다.")
        return
    
    # 탭 기반 메뉴로 변경
    tabs = st.tabs([
        f"👤 {get_text('personal_info')}",
        f"🏖️ {get_text('leave_request')}", 
        f"📝 {get_text('personal_request_history')}",
        f"📊 {get_text('personal_statistics')}",
        f"🔧 {get_text('info_edit_request')}"
    ])
    
    with tabs[0]:  # 개인 정보
        show_personal_status_view(employee_manager, vacation_manager, approval_manager, current_user_id, current_user_type, get_text)
    
    with tabs[1]:  # 휴가 신청
        show_vacation_request_page(vacation_manager, approval_manager, current_user_id, current_user_type, get_text)
    
    with tabs[2]:  # 개인 요청 내역
        show_my_requests_page(approval_manager, current_user_id, current_user_type, get_text)
    
    with tabs[3]:  # 개인 통계
        show_personal_statistics_page(vacation_manager, approval_manager, current_user_id, current_user_type, get_text)
    
    with tabs[4]:  # 정보 수정 요청
        show_personal_info_update_page(employee_manager, approval_manager, current_user_id, current_user_type, get_text)

def show_personal_status_view(employee_manager, vacation_manager, approval_manager, current_user_id, current_user_type, get_text):
    """개인 상태 조회 페이지"""
    st.header(f"👤 {get_text('my_personal_status')}")
    
    # 직원은 자신의 정보만 조회 가능, 법인장/총무/마스터는 모든 직원 조회 가능
    current_access_level = st.session_state.get('access_level', 'user')
    if current_user_type == "master" or current_access_level in ['ceo', 'admin']:
        if current_access_level == 'ceo':
            st.info("👑 법인장 계정: 모든 직원의 개인 상태를 조회할 수 있습니다.")
        elif current_access_level == 'admin':
            st.info("👔 총무 계정: 모든 직원의 개인 상태를 조회할 수 있습니다.")
        else:
            st.info(f"🔐 {get_text('master_account_info')}")
        
        employees = employee_manager.get_all_employees()
        if len(employees) > 0:
            # employees가 DataFrame인지 리스트인지 확인
            if hasattr(employees, 'iterrows'):
                # DataFrame인 경우
                employee_options = [row['employee_id'] for _, row in employees.iterrows()]
                employee_labels = [f"{row['name']} ({row['employee_id']})" for _, row in employees.iterrows()]
            else:
                # 리스트인 경우 - 각 항목이 딕셔너리인지 확인
                if employees and isinstance(employees[0], dict):
                    employee_options = [emp['employee_id'] for emp in employees]
                    employee_labels = [f"{emp['name']} ({emp['employee_id']})" for emp in employees]
                else:
                    st.error("직원 데이터 형식이 올바르지 않습니다.")
                    return
            
            selected_idx = st.selectbox(
                get_text('select_employee_to_view'),
                range(len(employee_options)),
                format_func=lambda x: employee_labels[x] if x < len(employee_labels) else "선택하세요"
            )
            
            if selected_idx < len(employee_options):
                selected_employee_id = employee_options[selected_idx]
            else:
                selected_employee_id = current_user_id
        else:
            st.warning(get_text('no_registered_employees'))
            return
    else:
        # 일반 직원은 자신의 정보만 조회
        selected_employee_id = current_user_id
        st.info(f"🙋‍♂️ {get_text('my_personal_info_desc')}")
    
    # 선택된 직원 정보 가져오기
    employee_info = None
    try:
        employee_info = employee_manager.get_employee_by_id(selected_employee_id)
        if employee_info is None:
            st.error(f"{get_text('employee_info_not_found')} (ID: {selected_employee_id})")
            return
    except Exception as e:
        st.error(f"{get_text('employee_info_query_error')}: {str(e)}")
        return
    
    # 직원 기본 정보 표시
    st.subheader(f"📋 {employee_info.get('name', 'N/A')} ({selected_employee_id})")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**{get_text('department')}:** {employee_info.get('department', 'N/A')}")
        st.info(f"**{get_text('label_position')}:** {employee_info.get('position', 'N/A')}")
    
    with col2:
        st.info(f"**{get_text('hire_date')}:** {employee_info.get('hire_date', 'N/A')}")
        st.info(f"**{get_text('work_status')}:** {employee_info.get('work_status', '재직')}")
    
    with col3:
        st.info(f"**{get_text('work_location')}:** {employee_info.get('city', 'N/A')}")
        st.info(f"**{get_text('contact')}:** {employee_info.get('contact', 'N/A')}")
    
    # 자신의 정보인 경우에만 비밀번호 변경 기능 제공
    if selected_employee_id == current_user_id:
        st.markdown("---")
        st.subheader(f"🔒 {get_text('password_change')}")
        
        with st.expander("비밀번호 변경", expanded=False):
            show_password_change_section(current_user_id, current_user_type)
    
    st.markdown("---")
    
    # 휴가 요약 정보
    st.subheader(f"🏖️ {get_text('leave_usage_status')}")
    try:
        vacation_summary = vacation_manager.get_vacation_summary(selected_employee_id)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(get_text('annual_leave'), f"{vacation_summary.get('annual_vacation_days', 15)}{get_text('days')}")
        
        with col2:
            st.metric(get_text('used_leave'), f"{vacation_summary.get('used_vacation_days', 0)}{get_text('days')}")
        
        with col3:
            st.metric(get_text('remaining_leave'), f"{vacation_summary.get('remaining_vacation_days', 15)}{get_text('days')}")
        
        with col4:
            st.metric(get_text('pending_applications'), f"{vacation_summary.get('pending_requests', 0)}{get_text('cases')}")
    
    except Exception as e:
        st.warning(f"휴가 정보 조회 중 오류: {str(e)}")
    
    # 나의 휴가 신청 내역
    st.subheader(f"📋 {get_text('my_leave_request_history')}")
    try:
        my_vacations = vacation_manager.get_vacations_by_employee(selected_employee_id)
        
        if len(my_vacations) > 0:
            # 최근 5건만 표시
            recent_vacations = my_vacations.sort_values('request_date', ascending=False).head(5)
            
            for _, vacation in recent_vacations.iterrows():
                status = vacation.get('status', 'pending')
                
                # 상태값 매핑 (영어 -> 한국어)
                status_map = {
                    'pending': '대기중',
                    'approved': '승인됨',
                    'rejected': '거부됨',
                    '대기': '대기중',  # 기존 한글 데이터 호환
                    '승인': '승인됨',
                    '거부': '거부됨'
                }
                
                status_text = status_map.get(status, status)
                
                status_color = {
                    'approved': '🟢',
                    'pending': '🟡',
                    'rejected': '🔴',
                    '승인': '🟢',  # 기존 한글 호환
                    '대기': '🟡',
                    '거부': '🔴'
                }.get(status, '⚪')
                
                # 휴가 유형 매핑 (영어 -> 한국어)
                vacation_type_map = {
                    'annual_leave': '연차',
                    'sick_leave': '병가',
                    'family_event': '경조사',
                    'special_leave': '특별휴가',
                    'unpaid_leave': '무급휴가'
                }
                vacation_type_display = vacation_type_map.get(vacation.get('vacation_type', ''), vacation.get('vacation_type', 'N/A'))
                
                with st.expander(f"{status_color} {vacation_type_display} - {vacation.get('start_date', 'N/A')} ~ {vacation.get('end_date', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**휴가 유형:** {vacation_type_display}")
                        st.write(f"**기간:** {vacation.get('start_date', 'N/A')} ~ {vacation.get('end_date', 'N/A')}")
                        st.write(f"**일수:** {vacation.get('days_count', 'N/A')}{get_text('days')}")
                    
                    with col2:
                        st.write(f"**{get_text('work_status')}:** {status_text}")
                        st.write(f"**신청일:** {vacation.get('request_date', 'N/A')}")
                        if vacation.get('approved_date'):
                            st.write(f"**승인일:** {vacation.get('approved_date', 'N/A')}")
                    
                    if vacation.get('reason'):
                        st.write(f"**사유:** {vacation.get('reason', 'N/A')}")
                    
                    if vacation.get('rejection_reason'):
                        st.error(f"**거부 사유:** {vacation.get('rejection_reason', 'N/A')}")
                    
                    # 관리자만 삭제 버튼 표시
                    if current_user_type == "master":
                        st.markdown("---")
                        vacation_id = vacation.get('vacation_id', '')
                        if vacation_id and st.button(f"🗑️ 휴가 내역 삭제", key=f"delete_vacation_{vacation_id}", type="secondary"):
                            if vacation_manager.delete_vacation(vacation_id):
                                st.success("✅ 휴가 내역이 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 휴가 내역 삭제에 실패했습니다.")
        else:
            st.info(get_text('no_leave_request_history'))
            
    except Exception as e:
        st.error(f"휴가 내역 조회 중 오류: {str(e)}")

def show_vacation_request_page(vacation_manager, approval_manager, current_user_id, current_user_type, get_text):
    """휴가 신청 페이지"""
    st.header(f"🏖️ {get_text('vacation_application')}")
    
    with st.form("vacation_request_form"):
        st.subheader(get_text('vacation_application_info'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            vacation_type = st.selectbox(
                get_text('vacation_type'),
                ["annual", "sick", "family_event", "special", "unpaid"]
            )
            
            # 반차 옵션 추가
            is_half_day = st.checkbox(get_text('half_day_option'))
            
            start_date = st.date_input(
                get_text('start_date'),
                value=datetime.now().date(),
                min_value=datetime.now().date(),
                max_value=datetime(2035, 7, 3).date()
            )
        
        with col2:
            # 반차인 경우 종료일을 시작일과 동일하게 설정
            if is_half_day:
                end_date = start_date
                st.info(get_text('half_day_info'))
                st.date_input(
                    get_text('end_date_half_day'),
                    value=start_date,
                    disabled=True
                )
            else:
                end_date = st.date_input(
                    get_text('end_date'),
                    value=datetime.now().date(),
                    min_value=datetime.now().date(),
                    max_value=datetime(2035, 7, 3).date()
                )
            
            reason = st.text_area(get_text('reason'), height=100)
        
        submitted = st.form_submit_button(get_text('submit_vacation'))
        
        if submitted:
            if start_date and end_date and reason:
                # 휴가 일수 계산 (반차 고려)
                if is_half_day:
                    days_count = 0.5
                else:
                    days_count = (end_date - start_date).days + 1
                
                # 직원 정보 가져오기
                from employee_manager import EmployeeManager
                emp_manager = EmployeeManager()
                employee_info = emp_manager.get_employee_by_id(current_user_id)
                employee_name = employee_info.get('name', f"직원 {current_user_id}") if employee_info else f"직원 {current_user_id}"
                
                vacation_data = {
                    'employee_id': current_user_id,
                    'employee_name': employee_name,
                    'vacation_type': vacation_type,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days_count': days_count,
                    'reason': reason,
                    'status': 'pending'
                }
                
                try:
                    # VacationManager를 통해 직접 휴가 신청 추가
                    success = vacation_manager.add_vacation_request(vacation_data)
                    if success:
                        # 승인 관리에 휴가 승인 요청 생성
                        from approval_manager import ApprovalManager
                        approval_manager = ApprovalManager()
                        
                        approval_result = approval_manager.create_vacation_approval_request(
                            vacation_data, current_user_id, employee_name
                        )
                        
                        if approval_result:
                            st.success(f"✅ 휴가 신청이 완료되었습니다. ({days_count}일간)")
                            st.info("📋 승인 관리에 요청이 전달되었습니다. 관리자 승인 후 휴가가 확정됩니다.")
                            
                        else:
                            st.warning("⚠️ 휴가 신청은 완료되었으나, 승인 요청 생성에 실패했습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 휴가 신청에 실패했습니다.")
                except Exception as e:
                    st.error(f"❌ 휴가 신청 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("모든 필수 정보를 입력해주세요.")

def show_personal_info_update_page_old(employee_manager, approval_manager, current_user_id, current_user_type):
    """개인정보 수정 요청 페이지 (구버전)"""
    st.header("📄 개인정보 수정 요청")
    
    # 현재 직원 정보 가져오기
    try:
        current_info = employee_manager.get_employee_by_id(current_user_id)
        if current_info is None:
            st.error("직원 정보를 찾을 수 없습니다.")
            return
    except Exception as e:
        st.error(f"직원 정보 조회 중 오류가 발생했습니다: {str(e)}")
        return
    
    st.info("개인정보 수정은 승인이 필요합니다. 변경하고자 하는 정보만 입력해주세요.")
    
    with st.form("personal_info_update_form"):
        st.subheader("수정할 개인정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_phone = st.text_input("연락처", placeholder=current_info.get('phone', ''))
            new_email = st.text_input("이메일", placeholder=current_info.get('email', ''))
            new_address = st.text_input("주소", placeholder=current_info.get('address', ''))
        
        with col2:
            new_emergency_contact = st.text_input("비상연락처", placeholder=current_info.get('emergency_contact', ''))
            new_emergency_relationship = st.text_input("비상연락처 관계", placeholder=current_info.get('emergency_relationship', ''))
            
        reason = st.text_area("수정 사유", height=100)
        
        submitted = st.form_submit_button("개인정보 수정 요청")
        
        if submitted:
            if reason:
                # 변경된 정보만 수집
                changes = {}
                if new_phone and new_phone != current_info.get('phone', ''):
                    changes['phone'] = new_phone
                if new_email and new_email != current_info.get('email', ''):
                    changes['email'] = new_email
                if new_address and new_address != current_info.get('address', ''):
                    changes['address'] = new_address
                if new_emergency_contact and new_emergency_contact != current_info.get('emergency_contact', ''):
                    changes['emergency_contact'] = new_emergency_contact
                if new_emergency_relationship and new_emergency_relationship != current_info.get('emergency_relationship', ''):
                    changes['emergency_relationship'] = new_emergency_relationship
                
                if changes:
                    try:
                        request_data = {
                            'employee_id': current_user_id,
                            'changes': changes,
                            'reason': reason,
                            'status': 'pending'
                        }
                        
                        approval_manager.create_approval_request({
                            'type': 'personal_info_update',
                            'data': request_data,
                            'requester_id': current_user_id,
                            'requester_name': f"직원 {current_user_id}",
                            'status': 'pending',
                            'description': f"개인정보 수정 요청 - {reason}"
                        })
                        
                        st.success("개인정보 수정 요청이 완료되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"개인정보 수정 요청 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.warning("변경할 정보가 없습니다.")
            else:
                st.error("수정 사유를 입력해주세요.")

def show_password_change_section(current_user_id, current_user_type):
    """비밀번호 변경 섹션 (개인 정보 탭용)"""
    from auth_manager import AuthManager
    auth_manager = AuthManager()
    
    st.info("🔒 보안을 위해 현재 비밀번호를 확인한 후 새 비밀번호로 변경할 수 있습니다.")
    
    with st.form("password_change_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            current_password = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호")
            new_password = st.text_input("새 비밀번호", type="password", placeholder="새로운 비밀번호 (최소 4자)")
        
        with col2:
            confirm_password = st.text_input("새 비밀번호 확인", type="password", placeholder="새 비밀번호 재입력")
        
        # 비밀번호 조건 안내
        st.info("🔐 비밀번호는 최소 4자 이상이어야 합니다.")
        
        submitted = st.form_submit_button("🔒 비밀번호 변경", type="primary", use_container_width=True)
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("❌ 모든 필드를 입력해주세요.")
            elif new_password != confirm_password:
                st.error("❌ 새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
            elif len(new_password) < 4:
                st.error("❌ 새 비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                try:
                    # 개선된 비밀번호 변경 함수 사용
                    success, message = auth_manager.change_password(current_user_id, current_password, new_password)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("🔄 다음 로그인부터 새 비밀번호를 사용하세요.")
                    else:
                        st.error(f"❌ {message}")
                        
                except Exception as e:
                    st.error(f"❌ 비밀번호 변경 중 오류가 발생했습니다: {str(e)}")

def show_password_change_page(current_user_id, current_user_type):
    """비밀번호 변경 페이지"""
    st.header("🔒 비밀번호 변경")
    
    # AuthManager 인스턴스 필요
    from auth_manager import AuthManager
    auth_manager = AuthManager()
    
    with st.form("password_change_form"):
        st.subheader("비밀번호 변경")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_password = st.text_input("현재 비밀번호", type="password")
            new_password = st.text_input("새 비밀번호", type="password")
        
        with col2:
            confirm_password = st.text_input("새 비밀번호 확인", type="password")
            
            # 비밀번호 강도 가이드
            st.info("""
            **비밀번호 조건:**
            - 최소 4자 이상
            - 영문, 숫자 조합 권장
            """)
        
        submitted = st.form_submit_button("비밀번호 변경", type="primary")
        
        if submitted:
            if current_password and new_password and confirm_password:
                if new_password == confirm_password:
                    if len(new_password) >= 4:
                        try:
                            # 현재 비밀번호 확인
                            if current_user_type == "employee":
                                auth_result = auth_manager.authenticate_employee(current_user_id, current_password)
                            else:
                                auth_result = auth_manager.authenticate_master(current_password)
                            
                            if auth_result:
                                # 비밀번호 변경
                                success, message = auth_manager.change_password(current_user_id, current_password, new_password)
                                if success:
                                    st.success(f"✅ {message}")
                                    st.info("다음 로그인부터 새 비밀번호를 사용하세요.")
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.error("❌ 현재 비밀번호가 올바르지 않습니다.")
                        except Exception as e:
                            st.error(f"❌ 비밀번호 변경 중 오류가 발생했습니다: {str(e)}")
                    else:
                        st.error("❌ 새 비밀번호는 최소 4자 이상이어야 합니다.")
                else:
                    st.error("❌ 새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
            else:
                st.error("❌ 모든 필드를 입력해주세요.")

def show_my_requests_page(approval_manager, current_user_id, current_user_type, get_text):
    """내 요청 내역 페이지"""
    st.header(f"📋 {get_text('my_request_history')}")
    
    try:
        my_requests_df = approval_manager.get_requests_by_requester(current_user_id)
        
        if len(my_requests_df) > 0:
            # 페이지네이션 설정
            items_per_page = 10
            total_items = len(my_requests_df)
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                page = st.selectbox("페이지", range(1, total_pages + 1), index=0)
            else:
                page = 1
            
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_requests_df = my_requests_df.iloc[start_idx:end_idx]
            
            for _, request in page_requests_df.iterrows():
                request_type = request.get('request_type', 'N/A')
                status = request.get('status', 'N/A')
                request_date = request.get('request_date', 'N/A')
                
                # 상태값 매핑 (영어 -> 한국어)
                status_map = {
                    'pending': '대기중',
                    'approved': '승인됨',
                    'rejected': '거부됨',
                    '대기': '대기중',  # 기존 한글 데이터 호환
                    '승인': '승인됨',
                    '거부': '거부됨'
                }
                
                status_text = status_map.get(status, status)
                
                with st.expander(f"[{status_text}] {request_type} - {request_date}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**요청 ID:** {request.get('approval_id', 'N/A')}")
                        st.write(f"**요청 유형:** {request_type}")
                        st.write(f"**상태:** {status_text}")
                        st.write(f"**요청일:** {request_date}")
                    
                    with col2:
                        if status in ['approved', '승인']:
                            st.success("✅ 승인됨")
                            if request.get('approval_date') and request.get('approval_date') != '':
                                st.write(f"**승인일:** {request.get('approval_date')}")
                            if request.get('approver_name') and request.get('approver_name') != '':
                                st.write(f"**승인자:** {request.get('approver_name')}")
                        elif status in ['rejected', '거부']:
                            st.error("❌ 거부됨")
                            if request.get('rejection_reason') and request.get('rejection_reason') != '':
                                st.write(f"**거부 사유:** {request.get('rejection_reason')}")
                        else:
                            st.warning("⏳ 승인 대기 중")
                    
                    if request.get('description') and request.get('description') != '':
                        st.write(f"**상세 내용:** {request.get('description')}")
                    
                    # 관리자만 휴가 관련 요청 삭제 가능
                    if current_user_type == "master" and "휴가" in request_type:
                        st.markdown("---")
                        approval_id = request.get('approval_id', '')
                        if approval_id and st.button(f"🗑️ 요청 삭제", key=f"delete_request_{approval_id}", type="secondary"):
                            # 승인 요청 삭제
                            from approval_manager import ApprovalManager
                            approval_mgr = ApprovalManager()
                            
                            # 승인 데이터에서 삭제
                            try:
                                import pandas as pd
                                df = pd.read_csv(approval_mgr.data_file, encoding='utf-8-sig')
                                if approval_id in df['approval_id'].values:
                                    df = df[df['approval_id'] != approval_id]
                                    df.to_csv(approval_mgr.data_file, index=False, encoding='utf-8-sig')
                                    st.success("✅ 승인 요청이 삭제되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("❌ 요청을 찾을 수 없습니다.")
                            except Exception as e:
                                st.error(f"❌ 요청 삭제 중 오류: {str(e)}")
            
            if total_pages > 1:
                st.info(f"전체 {total_items}개 요청 중 {start_idx + 1}-{min(end_idx, total_items)}개 표시 (페이지 {page}/{total_pages})")
        else:
            st.info("요청 내역이 없습니다.")
            
    except Exception as e:
        st.error(f"요청 내역 조회 중 오류가 발생했습니다: {str(e)}")
        # 디버깅을 위한 상세 오류 정보
        import traceback
        st.text(f"상세 오류: {traceback.format_exc()}")

def show_personal_statistics_page(vacation_manager, approval_manager, current_user_id, current_user_type, get_text):
    """개인 통계 페이지"""
    st.header(f"📊 {get_text('personal_statistics')}")
    
    try:
        # 휴가 통계
        st.subheader(f"🏖️ {get_text('vacation_usage_statistics')}")
        
        # 실제 휴가 통계 계산
        vacation_summary = vacation_manager.get_vacation_summary(current_user_id)
        my_vacations = vacation_manager.get_vacations_by_employee(current_user_id)
        
        # 휴가 신청 건수 계산
        total_requests = len(my_vacations) if len(my_vacations) > 0 else 0
        approved_requests = len(my_vacations[my_vacations['status'].isin(['approved', '승인'])]) if len(my_vacations) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(get_text('total_vacation_requests'), f"{total_requests}{get_text('cases')}")
        
        with col2:
            st.metric(get_text('approved_vacations'), f"{approved_requests}{get_text('cases')}")
        
        with col3:
            remaining_days = vacation_summary.get('remaining_vacation_days', 15)
            st.metric(get_text('available_annual_leave'), f"{remaining_days}{get_text('days')}")
        
        # 요청 승인 통계
        st.subheader(f"📋 {get_text('request_approval_statistics')}")
        
        my_requests_df = approval_manager.get_requests_by_requester(current_user_id)
        
        if len(my_requests_df) > 0:
            # 상태값 매핑 (영어 -> 한국어)
            status_map = {
                'pending': '대기중',
                'approved': '승인됨',
                'rejected': '거부됨',
                '대기': '대기중',  # 기존 한글 데이터 호환
                '승인': '승인됨',
                '거부': '거부됨'
            }
            
            status_counts = {}
            for _, request in my_requests_df.iterrows():
                status = request.get('status', 'N/A')
                status_text = status_map.get(status, status)
                status_counts[status_text] = status_counts.get(status_text, 0) + 1
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(get_text('total_requests'), len(my_requests_df))
            
            with col2:
                st.metric(get_text('approved_requests'), status_counts.get('승인됨', 0))
            
            with col3:
                approval_rate = (status_counts.get('승인됨', 0) / len(my_requests_df) * 100) if len(my_requests_df) > 0 else 0
                st.metric(get_text('approval_rate'), f"{approval_rate:.1f}%")
        else:
            st.info(get_text('no_request_statistics'))
            
    except Exception as e:
        st.error(f"통계 조회 중 오류가 발생했습니다: {str(e)}")

def show_password_change_section(current_user_id, current_user_type):
    """비밀번호 변경 섹션을 표시합니다."""
    from managers.legacy.auth_manager import AuthManager
    
    auth_manager = AuthManager()
    
    st.info("보안을 위해 현재 비밀번호를 먼저 확인합니다.")
    
    with st.form("password_change_form"):
        current_password = st.text_input("현재 비밀번호", type="password", placeholder="현재 사용 중인 비밀번호를 입력하세요")
        new_password = st.text_input("새 비밀번호", type="password", placeholder="새로운 비밀번호를 입력하세요")
        confirm_password = st.text_input("새 비밀번호 확인", type="password", placeholder="새 비밀번호를 다시 입력하세요")
        
        submit_password_change = st.form_submit_button("🔒 비밀번호 변경", use_container_width=True, type="primary")
        
        if submit_password_change:
            if not current_password or not new_password or not confirm_password:
                st.error("모든 필드를 입력해주세요.")
            elif new_password != confirm_password:
                st.error("새 비밀번호가 일치하지 않습니다.")
            elif len(new_password) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                # 비밀번호 변경 시도
                success, message = auth_manager.change_password(current_user_id, current_password, new_password)
                if success:
                    st.success(f"✅ {message}")
                    
                    st.info("다음 로그인부터 새 비밀번호를 사용하세요.")
                else:
                    st.error(f"❌ {message}")

def show_personal_info_update_page(employee_manager, approval_manager, current_user_id, current_user_type, get_text):
    """개인정보 수정 요청 페이지"""
    st.header("🔧 정보 수정 요청")
    
    st.info("📝 개인정보 변경을 원하시면 아래 양식을 작성해주세요. 승인 후 변경사항이 적용됩니다.")
    
    # 현재 정보 표시
    try:
        employee_info = employee_manager.get_employee_by_id(current_user_id)
        if employee_info is not None and len(employee_info) > 0:
            st.subheader("📋 현재 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**이름:** {employee_info.get('name', 'N/A')}")
                st.write(f"**부서:** {employee_info.get('department', 'N/A')}")
                st.write(f"**직급:** {employee_info.get('position', 'N/A')}")
            
            with col2:
                st.write(f"**연락처:** {employee_info.get('contact', 'N/A')}")
                st.write(f"**이메일:** {employee_info.get('email', 'N/A')}")
                st.write(f"**거주지:** {employee_info.get('city', 'N/A')}")
            
            st.markdown("---")
    except Exception as e:
        st.warning(f"현재 정보 조회 중 오류: {str(e)}")
    
    # 수정 요청 폼
    st.subheader("✏️ 수정 요청")
    
    with st.form("info_update_request_form"):
        update_type = st.selectbox("수정할 항목", [
            "연락처 변경",
            "이메일 변경", 
            "거주지 변경",
            "기타 개인정보 변경"
        ])
        
        current_value = st.text_input("현재 값", placeholder="현재 저장된 값을 입력하세요")
        new_value = st.text_input("변경할 값", placeholder="새로운 값을 입력하세요")
        reason = st.text_area("변경 사유", placeholder="변경이 필요한 이유를 설명해주세요")
        
        submit_update_request = st.form_submit_button("📝 수정 요청 제출", use_container_width=True, type="primary")
        
        if submit_update_request:
            if not update_type or not current_value or not new_value or not reason:
                st.error("모든 필드를 입력해주세요.")
            else:
                # 승인 요청 생성
                request_data = {
                    'request_type': f'개인정보 수정 - {update_type}',
                    'requester_id': current_user_id,
                    'requester_name': employee_info.get('name', current_user_id) if 'employee_info' in locals() else current_user_id,
                    'description': f"수정 항목: {update_type}\n현재 값: {current_value}\n변경 값: {new_value}\n변경 사유: {reason}",
                    'status': 'pending',
                    'priority': 'normal'
                }
                
                try:
                    approval_id = approval_manager.create_approval_request(request_data)
                    if approval_id:
                        st.success("✅ 개인정보 수정 요청이 제출되었습니다!")
                        st.info(f"요청 ID: {approval_id}")
                        
                    else:
                        st.error("요청 제출 중 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"요청 제출 중 오류: {str(e)}")