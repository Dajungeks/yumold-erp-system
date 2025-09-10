# -*- coding: utf-8 -*-
"""
지출요청서 관리 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from sqlite_expense_request_manager import SQLiteExpenseRequestManager
from sqlite_approval_manager import SQLiteApprovalManager
from simple_expense_pdf_generator import SimpleExpensePDFGenerator
import os

def generate_expense_pdf(request_data, approval_settings, get_text, language='ko'):
    """지출요청서 PDF를 생성합니다."""
    try:
        # PDF 생성기 초기화
        pdf_generator = SimpleExpensePDFGenerator()
        
        # 승인자 데이터 준비
        approval_data = {
            'approvers': approval_settings
        }
        
        # 요청서 ID 생성
        request_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        request_data['request_id'] = request_id
        
        # 파일명 생성
        filename = f"expense_request_{request_id}_{language}.pdf"
        
        # PDF 생성
        success, message = pdf_generator.generate_pdf(request_data, approval_data, filename, language)
        
        if success:
            # 파일이 존재하는지 확인
            if os.path.exists(filename):
                # 파일 다운로드 버튼
                with open(filename, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                st.download_button(
                    label=f"📥 {get_text('expense_request.download_pdf')} ({language.upper()})",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf"
                )
                st.success(f"✅ PDF 생성 완료: {filename}")
            else:
                st.error(f"❌ PDF 파일을 찾을 수 없습니다: {filename}")
        else:
            st.error(f"❌ PDF 생성 실패: {message}")
            
    except Exception as e:
        st.error(f"❌ PDF 생성 중 오류 발생: {str(e)}")

def process_approval_action(expense_manager, approval_id, approver_id, result, comments=""):
    """승인/반려 처리 액션"""
    try:
        success, message = expense_manager.process_approval(approval_id, approver_id, result, comments)
        
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
            
    except Exception as e:
        st.error(f"❌ 승인 처리 중 오류가 발생했습니다: {str(e)}")

def show_expense_request_page(get_text):
    """지출요청서 관리 페이지를 표시합니다."""
    st.title(f"💰 {get_text('expense_request.title')}")
    st.markdown("---")
    
    # 지출요청서 매니저 초기화 (SQLite 버전)
    if 'sqlite_expense_request_manager' not in st.session_state:
        st.session_state.sqlite_expense_request_manager = SQLiteExpenseRequestManager()
    if 'sqlite_approval_manager' not in st.session_state:
        st.session_state.sqlite_approval_manager = SQLiteApprovalManager()
    
    expense_manager = st.session_state.sqlite_expense_request_manager
    approval_manager = st.session_state.sqlite_approval_manager
    
    # 현재 사용자 정보 - 올바른 세션 키 사용
    current_user_id = st.session_state.get('user_id', 'USER001')
    current_user_name = st.session_state.get('username', '관리자')
    
    # 디버그 정보 출력 (개발용)
    if st.checkbox("🔧 디버그 모드", help="세션 상태 정보를 확인합니다"):
        st.write(f"세션 user_id: {st.session_state.get('user_id', '없음')}")
        st.write(f"세션 username: {st.session_state.get('username', '없음')}")
        st.write(f"로그인 상태: {st.session_state.get('logged_in', False)}")
        st.write(f"사용자 타입: {st.session_state.get('user_type', '없음')}")
        st.write(f"접근 레벨: {st.session_state.get('access_level', '없음')}")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        f"📝 {get_text('expense_request.create_title')}",
        f"📋 {get_text('expense_request.my_requests')}", 
        f"✅ {get_text('expense_request.approval_management')}",
        f"✏️ {get_text('expense_request.edit_title')}",
        f"🗑️ {get_text('expense_request.delete_title')}",
        f"📄 {get_text('expense_request.pdf_title')}",
        f"📊 {get_text('expense_request.statistics')}"
    ])
    
    with tab1:
        show_expense_request_form(expense_manager, current_user_id, current_user_name, get_text)
    
    with tab2:
        show_my_requests(expense_manager, current_user_id, get_text)
    
    with tab3:
        show_pending_approvals(expense_manager, current_user_id, get_text)
    
    with tab4:
        show_expense_request_edit(expense_manager, current_user_id, get_text)
    
    with tab5:
        show_expense_request_delete(expense_manager, current_user_id, get_text)
    
    with tab6:
        show_expense_request_pdf(expense_manager, current_user_id, get_text)
    
    with tab7:
        show_expense_statistics(expense_manager, get_text)

def show_expense_request_edit(expense_manager, current_user_id, get_text):
    """지출요청서 수정 페이지"""
    st.header("✏️ 지출요청서 수정")
    
    # 수정 가능한 요청서 목록 (대기 상태만)
    try:
        df = expense_manager.get_expense_requests(status='pending', requester_id=current_user_id)
        
        if len(df) == 0:
            st.info("수정 가능한 요청서가 없습니다. (대기 상태의 본인 요청서만 수정 가능)")
            return
        
        # 요청서 선택
        request_options = []
        for _, req in df.iterrows():
            option = f"{req['request_id']} - {req['expense_title']} ({req['amount']:,.0f} {req['currency']})"
            request_options.append(option)
        
        selected_request_option = st.selectbox("수정할 요청서 선택", request_options)
        
        if selected_request_option:
            # 선택된 요청서 ID 추출
            selected_request_id = selected_request_option.split(' - ')[0]
            current_request = df[df['request_id'] == selected_request_id].iloc[0]
            
            st.markdown("---")
            st.subheader(f"📝 요청서 수정: {selected_request_id}")
            
            # 수정 폼
            with st.form("edit_expense_request_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_title = st.text_input("지출 제목", value=current_request.get('expense_title', ''))
                    new_category = st.selectbox("카테고리", 
                                              expense_manager.get_expense_categories(),
                                              index=expense_manager.get_expense_categories().index(current_request.get('category', '업무용품')))
                    new_amount = st.number_input("금액", value=float(current_request.get('amount', 0)), min_value=0.0)
                
                with col2:
                    new_currency = st.selectbox("통화", ['USD', 'VND'], 
                                              index=['USD', 'VND'].index(current_request.get('currency', 'USD')))
                    new_expected_date = st.date_input("예상 지출일", 
                                                    value=datetime.strptime(current_request.get('expected_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date())
                
                new_description = st.text_area("지출 설명", value=current_request.get('expense_description', ''))
                new_notes = st.text_area("비고", value=current_request.get('notes', ''))
                
                submit_edit = st.form_submit_button("수정 완료", type="primary")
                
                if submit_edit:
                    updated_data = {
                        'expense_title': new_title,
                        'expense_description': new_description,
                        'category': new_category,
                        'amount': new_amount,
                        'currency': new_currency,
                        'expected_date': new_expected_date.strftime('%Y-%m-%d'),
                        'notes': new_notes
                    }
                    
                    success, message = expense_manager.update_expense_request(selected_request_id, updated_data)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    except Exception as e:
        st.error(f"요청서 목록 로드 중 오류: {str(e)}")

def show_expense_request_delete(expense_manager, current_user_id, get_text):
    """지출요청서 삭제 페이지"""
    st.header("🗑️ 지출요청서 삭제")
    
    # 삭제 가능한 요청서 목록 (대기 또는 반려 상태)
    try:
        # 삭제 가능한 상태의 요청서 조회
        pending_df = expense_manager.get_expense_requests(status='pending', requester_id=current_user_id)
        rejected_df = expense_manager.get_expense_requests(status='rejected', requester_id=current_user_id)
        
        # 두 DataFrame 결합
        if len(pending_df) > 0 and len(rejected_df) > 0:
            deletable_requests = pd.concat([pending_df, rejected_df], ignore_index=True)
        elif len(pending_df) > 0:
            deletable_requests = pending_df
        elif len(rejected_df) > 0:
            deletable_requests = rejected_df
        else:
            deletable_requests = pd.DataFrame()
        
        if len(deletable_requests) == 0:
            st.info("삭제 가능한 요청서가 없습니다. (대기 또는 반려 상태의 본인 요청서만 삭제 가능)")
            return
        
        # 요청서 선택
        request_options = []
        for _, req in deletable_requests.iterrows():
            status_color = "🔴" if req['status'] == '반려' else "🟡"
            option = f"{req['request_id']} - {req['expense_title']} ({req['amount']:,.0f} {req['currency']}) {status_color}{req['status']}"
            request_options.append(option)
        
        selected_request_option = st.selectbox("삭제할 요청서 선택", request_options)
        
        if selected_request_option:
            selected_request_id = selected_request_option.split(' - ')[0]
            current_request = deletable_requests[deletable_requests['request_id'] == selected_request_id].iloc[0]
            
            st.markdown("---")
            st.subheader(f"⚠️ 요청서 삭제 확인: {selected_request_id}")
            
            # 요청서 상세 정보 표시
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**제목:** {current_request.get('expense_title', '')}")
                st.write(f"**카테고리:** {current_request.get('category', '')}")
                st.write(f"**금액:** {current_request.get('amount', 0):,.0f} {current_request.get('currency', '')}")
            
            with col2:
                st.write(f"**요청일:** {current_request.get('request_date', '')}")
                st.write(f"**상태:** {current_request.get('status', '')}")
                st.write(f"**예상 지출일:** {current_request.get('expected_date', '')}")
            
            st.write(f"**설명:** {current_request.get('expense_description', '')}")
            
            st.error("⚠️ 삭제된 요청서는 복구할 수 없습니다!")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🗑️ 삭제 확인", type="secondary", use_container_width=True):
                    success, message = expense_manager.delete_expense_request(selected_request_id)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    except Exception as e:
        st.error(f"요청서 목록 로드 중 오류: {str(e)}")

def show_expense_request_pdf(expense_manager, current_user_id, get_text):
    """지출요청서 PDF 출력 페이지"""
    st.header("📄 지출요청서 PDF 출력")
    
    try:
        df = expense_manager.get_expense_requests()
        
        if len(df) == 0:
            st.info("출력할 요청서가 없습니다.")
            return
        
        # 요청서 목록 (모든 상태)
        request_options = []
        for _, req in df.iterrows():
            status_emoji = {'대기': '🟡', '진행중': '🔵', '승인': '🟢', '반려': '🔴', '완료': '✅'}.get(req['status'], '⚪')
            option = f"{req['request_id']} - {req['expense_title']} ({req['amount']:,.0f} {req['currency']}) {status_emoji}{req['status']}"
            request_options.append(option)
        
        selected_request_option = st.selectbox("PDF로 출력할 요청서 선택", request_options)
        
        if selected_request_option:
            selected_request_id = selected_request_option.split(' - ')[0]
            current_request = df[df['request_id'] == selected_request_id].iloc[0]
            
            st.markdown("---")
            st.subheader(f"📄 PDF 출력: {selected_request_id}")
            
            # 요청서 정보 미리보기
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**제목:** {current_request.get('expense_title', '')}")
                st.write(f"**요청자:** {current_request.get('requester_name', '')}")
                st.write(f"**카테고리:** {current_request.get('category', '')}")
                st.write(f"**금액:** {current_request.get('amount', 0):,.0f} {current_request.get('currency', '')}")
            
            with col2:
                st.write(f"**요청일:** {current_request.get('request_date', '')}")
                st.write(f"**상태:** {current_request.get('status', '')}")
                st.write(f"**예상 지출일:** {current_request.get('expected_date', '')}")
            
            st.write(f"**설명:** {current_request.get('expense_description', '')}")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📄 PDF 생성 및 다운로드", type="primary", use_container_width=True):
                    with st.spinner("PDF 생성 중..."):
                        pdf_filename, message = expense_manager.generate_expense_request_pdf(selected_request_id)
                        
                        if pdf_filename:
                            st.success(message)
                            
                            # PDF 파일 다운로드 제공
                            try:
                                with open(pdf_filename, "rb") as pdf_file:
                                    pdf_data = pdf_file.read()
                                    st.download_button(
                                        label="📥 PDF 파일 다운로드",
                                        data=pdf_data,
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                
                                # 임시 파일 정리
                                import os
                                try:
                                    os.remove(pdf_filename)
                                except:
                                    pass
                                    
                            except Exception as e:
                                st.error(f"PDF 파일 읽기 오류: {str(e)}")
                        else:
                            st.error(message)
    
    except Exception as e:
        st.error(f"요청서 목록 로드 중 오류: {str(e)}")

def show_expense_request_form(expense_manager, user_id, user_name, get_text):
    """지출요청서 작성 폼을 표시합니다."""
    st.header("📝 지출요청서 작성")
    
    # 직원 관리에서 등록된 직원들 정보 미리 로드
    from employee_manager import EmployeeManager
    employee_manager = EmployeeManager()
    
    approver_options = {}
    employee_info = {}
    
    try:
        employees_df = employee_manager.get_all_employees()
        
        if employees_df is not None and isinstance(employees_df, pd.DataFrame) and len(employees_df) > 0:
            # 재직 중인 직원만 필터링 (status가 'active'이거나 work_status가 '재직'인 직원)
            active_employees = employees_df[
                (employees_df['status'] == 'active') | 
                (employees_df['work_status'] == '재직') |
                (employees_df['status'] == '재직')
            ]
            if len(active_employees) > 0:
                for _, employee in active_employees.iterrows():
                    name = employee.get('name', '')
                    position = employee.get('position', '')
                    department = employee.get('department', '')
                    employee_id = employee.get('employee_id', '')
                    
                    display_name = f"{name} ({position}, {department})" if position and department else name
                    approver_options[display_name] = {
                        'employee_id': employee_id,
                        'employee_name': name,
                        'position': position,
                        'department': department,
                        'approval_level': employee.get('approval_level', 1),
                        'max_approval_amount': employee.get('max_approval_amount', 0)
                    }
                    # 직원 정보를 별도로 저장
                    employee_info[name] = {
                        'employee_id': employee_id,
                        'position': position,
                        'department': department
                    }
        
        if not approver_options:
            st.warning("등록된 직원이 없습니다. 수동 입력 옵션을 사용하세요.")
            approver_options = {"수동 입력": {
                'employee_id': 'manual',
                'employee_name': "수동 입력",
                'position': '',
                'department': '',
                'approval_level': 1
            }}
    except Exception as e:
        st.warning(f"직원 정보 로드 중 오류 발생: {str(e)}")
        approver_options = {"수동 입력": {
            'employee_id': 'manual',
            'employee_name': "수동 입력",
            'position': '',
            'department': '',
            'approval_level': 1
        }}

    # 승인자 선택 - form 밖에서 먼저 표시
    st.subheader("👥 승인자 선택")
    st.info("💡 지출 요청서의 승인을 받을 담당자를 선택하세요. 승인전에는 수정 및 삭제가 가능합니다.")
    
    # 디버그 정보 표시
    with st.expander("🔧 승인자 정보 확인", expanded=True):
        st.write(f"로드된 승인자 수: {len(approver_options)}")
        if approver_options:
            st.write("승인자 목록:")
            for name, info in approver_options.items():
                st.write(f"- {name}")
        else:
            st.error("승인자 정보가 로드되지 않았습니다!")
            st.write("직원 데이터 확인 중...")
            
            # 직접 직원 매니저에서 데이터 확인
            try:
                debug_employees = employee_manager.get_all_employees()
                if debug_employees is not None and len(debug_employees) > 0:
                    st.write(f"전체 직원 수: {len(debug_employees)}")
                    st.dataframe(debug_employees[['name', 'position', 'department', 'status']].head())
                else:
                    st.write("직원 데이터가 없습니다.")
            except Exception as e:
                st.write(f"직원 데이터 로드 오류: {str(e)}")

    # 1차 승인자 선택
    st.markdown("### 🔹 1차 승인자 *")
    first_approver_name = st.selectbox(
        "1차 승인자 선택 *", 
        list(approver_options.keys()) if approver_options else ["수동 입력"],
        help="지출 승인을 담당할 1차 승인자를 선택하세요"
    )
    
    first_approver = None
    if first_approver_name and approver_options:
        first_approver = approver_options[first_approver_name].copy()
        
        # 선택된 승인자 정보 표시
        st.success(f"✅ 선택된 1차 승인자: {first_approver['employee_name']} ({first_approver['position']}, {first_approver['department']})")
    
    # 2차 승인자 선택
    st.markdown("### 🔸 2차 승인자 (선택사항)")
    use_second_approver = st.checkbox("2차 승인자 추가")
    second_approver = None
    
    if use_second_approver and approver_options:
        second_approver_options = {k: v for k, v in approver_options.items() if k != first_approver_name}
        if second_approver_options:
            second_approver_name = st.selectbox("2차 승인자 선택", list(second_approver_options.keys()))
            if second_approver_name:
                second_approver = second_approver_options[second_approver_name].copy()
                st.success(f"✅ 선택된 2차 승인자: {second_approver['employee_name']} ({second_approver['position']}, {second_approver['department']})")

    with st.form("expense_request_form"):
        # 요청자 정보 표시 (자동으로 현재 로그인 사용자 정보 설정)
        st.subheader(f"👤 {get_text('expense_request.requester_info')}")
        
        # 현재 로그인한 사용자의 정보를 자동으로 가져오기
        current_user_info = None
        
        try:
            employees_df = employee_manager.get_all_employees()
            
            if employees_df is not None and isinstance(employees_df, pd.DataFrame) and len(employees_df) > 0:
                # 현재 로그인한 사용자 정보 찾기 (user_id 기준 - 정수/문자열 모두 처리)
                try:
                    # user_id를 정수로 변환하여 비교
                    user_id_int = int(user_id)
                    user_info = employees_df[employees_df['employee_id'] == user_id_int]
                except (ValueError, TypeError):
                    # 문자열로 직접 비교
                    user_info = employees_df[employees_df['employee_id'] == user_id]
                
                if len(user_info) > 0:
                    current_user_info = {
                        'employee_id': user_info.iloc[0].get('employee_id', user_id),
                        'employee_name': user_info.iloc[0].get('name', user_name),
                        'position': user_info.iloc[0].get('position', ''),
                        'department': user_info.iloc[0].get('department', ''),
                        'contact': user_info.iloc[0].get('contact', ''),
                        'email': user_info.iloc[0].get('email', '')
                    }
                else:
                    # 로그인 정보로 기본값 설정
                    current_user_info = {
                        'employee_id': user_id,
                        'employee_name': user_name,
                        'position': '',
                        'department': '',
                        'contact': '',
                        'email': ''
                    }
            else:
                # 직원 정보가 없을 경우 로그인 정보 사용
                current_user_info = {
                    'employee_id': user_id,
                    'employee_name': user_name,
                    'position': '',
                    'department': '',
                    'contact': '',
                    'email': ''
                }
        
        except Exception as e:
            # 오류 발생시 로그인 정보로 기본값 설정
            current_user_info = {
                'employee_id': user_id,
                'employee_name': user_name,
                'position': '',
                'department': '',
                'contact': '',
                'email': ''
            }
        
        # 현재 로그인 사용자 정보 자동 표시 (수정 불가)
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(get_text("expense_request.requester_name"), value=current_user_info['employee_name'], disabled=True, key="req_name")
            st.text_input(get_text("expense_request.department"), value=current_user_info['department'], disabled=True, key="req_dept")
        with col2:
            st.text_input(get_text("expense_request.position"), value=current_user_info['position'], disabled=True, key="req_pos")
            st.text_input(get_text("expense_request.contact"), value=current_user_info['contact'], disabled=True, key="req_contact")
        

        
        # 기본 정보
        st.subheader(f"📋 {get_text('expense_request.basic_info')}")
        col1, col2 = st.columns(2)
        
        with col1:
            expense_title = st.text_input(f"{get_text('expense_request.expense_title')}*", placeholder=get_text("expense_request.expense_title_placeholder"))
            category = st.selectbox(f"{get_text('expense_request.expense_category')}*", expense_manager.get_expense_categories())
            amount = st.number_input(f"{get_text('expense_request.expense_amount')}*", min_value=0.0, step=1000.0)
        
        with col2:
            currency = st.selectbox(get_text("expense_request.currency"), ["USD", "VND", "KRW"], index=0)
            expected_date = st.date_input(get_text("expense_request.expected_date"), value=datetime.now().date())
            attachment = st.file_uploader(get_text("expense_request.attachment"), type=['pdf', 'jpg', 'png', 'doc', 'docx'])
        
        expense_description = st.text_area(f"{get_text('expense_request.expense_description')}*", placeholder=get_text("expense_request.expense_description_placeholder"))
        notes = st.text_area(get_text("expense_request.notes"), placeholder=get_text("expense_request.notes_placeholder"))
        
        # 승인자 선택 - 개선된 UI
        st.subheader("👥 승인자 선택")
        st.info("💡 지출 요청서의 승인을 받을 담당자를 선택하세요. 승인전에는 수정 및 삭제가 가능합니다.")
        
        # 디버그 정보 표시
        with st.expander("🔧 승인자 정보 확인", expanded=False):
            st.write(f"로드된 승인자 수: {len(approver_options)}")
            if approver_options:
                st.write("승인자 목록:")
                for name, info in approver_options.items():
                    st.write(f"- {name}: {info}")
            else:
                st.error("승인자 정보가 로드되지 않았습니다!")
                st.write("직원 데이터 확인 중...")
                
                # 직접 직원 매니저에서 데이터 확인
                try:
                    debug_employees = employee_manager.get_all_employees()
                    if debug_employees is not None and len(debug_employees) > 0:
                        st.write(f"전체 직원 수: {len(debug_employees)}")
                        st.dataframe(debug_employees[['name', 'position', 'department', 'status']].head())
                    else:
                        st.write("직원 데이터가 없습니다.")
                except Exception as e:
                    st.write(f"직원 데이터 로드 오류: {str(e)}")
        
        # 승인 권한에 따른 필터링 함수
        def filter_approvers_by_amount(amount, min_level=1):
            """금액과 최소 승인 레벨에 따라 승인자를 필터링합니다."""
            filtered_options = {}
            for name, approver in approver_options.items():
                try:
                    approval_level_raw = approver.get('approval_level', 1)
                    if pd.isna(approval_level_raw):
                        approver_level = 1
                    else:
                        approver_level = int(float(approval_level_raw))
                    
                    max_approval_amount_raw = approver.get('max_approval_amount', 0)
                    if pd.isna(max_approval_amount_raw):
                        max_amount = 0
                    else:
                        max_amount = float(max_approval_amount_raw)
                    
                    if approver_level >= min_level and (max_amount == 0 or amount <= max_amount):
                        filtered_options[name] = approver
                except (ValueError, TypeError):
                    if min_level <= 1:
                        filtered_options[name] = approver
            return filtered_options

        # 1차 승인자 (필수)
        st.markdown("### 🔹 1차 승인자 *")
        first_approver_filtered = approver_options
        first_approver = None
        
        first_approver_name = st.selectbox(
            "1차 승인자 선택 *", 
            list(first_approver_filtered.keys()),
            help="지출 승인을 담당할 1차 승인자를 선택하세요"
        )
        
        if first_approver_name:
            first_approver = first_approver_filtered[first_approver_name].copy()
            
            # 선택된 승인자 정보 카드 표시
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 5px solid #1f77b4; margin: 10px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #1f77b4;">🔹 선택된 1차 승인자</h4>
                    <p style="margin: 5px 0;"><strong>이름:</strong> {first_approver['employee_name']}</p>
                    <p style="margin: 5px 0;"><strong>직책:</strong> {first_approver['position']}</p>
                    <p style="margin: 5px 0;"><strong>부서:</strong> {first_approver['department']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 직접 입력 옵션인 경우 추가 입력 필드
            if first_approver.get('employee_name') == "수동 입력":
                first_approver['employee_name'] = st.text_input(
                    "1차 승인자 이름", 
                    placeholder="승인자 이름을 입력하세요"
                )
                first_approver['position'] = st.text_input(
                    "1차 승인자 직책", 
                    placeholder="직책을 입력하세요"
                )
                first_approver['department'] = st.text_input(
                    "1차 승인자 부서", 
                    placeholder="부서를 입력하세요"
                )
        
        # 2차 승인자 (선택사항)
        st.markdown("### 🔸 2차 승인자 (선택사항)")
        use_second_approver = st.checkbox("2차 승인자 추가", help="고액 지출이나 특별한 승인이 필요한 경우 2차 승인자를 추가하세요")
        second_approver = None
        
        if use_second_approver and first_approver_name and first_approver:
            # 1차 승인자와 다른 직원만 선택 가능
            second_approver_filtered = {k: v for k, v in approver_options.items() 
                                       if v['employee_id'] != first_approver['employee_id']}
            
            if second_approver_filtered:
                second_approver_name = st.selectbox(
                    "2차 승인자 선택", 
                    list(second_approver_filtered.keys()),
                    help="1차 승인 후 추가 승인을 담당할 2차 승인자를 선택하세요"
                )
                
                if second_approver_name:
                    second_approver = second_approver_filtered[second_approver_name].copy()
                    
                    # 선택된 2차 승인자 정보 카드 표시
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: #f0fff0; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; margin: 10px 0;">
                            <h4 style="margin: 0 0 10px 0; color: #28a745;">🔸 선택된 2차 승인자</h4>
                            <p style="margin: 5px 0;"><strong>이름:</strong> {second_approver['employee_name']}</p>
                            <p style="margin: 5px 0;"><strong>직책:</strong> {second_approver['position']}</p>
                            <p style="margin: 5px 0;"><strong>부서:</strong> {second_approver['department']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 직접 입력 옵션인 경우
                    if second_approver.get('employee_name') == '수동 입력':
                        second_approver['employee_name'] = st.text_input("2차 승인자 이름", placeholder="승인자 이름을 입력하세요")
                        second_approver['position'] = st.text_input("2차 승인자 직책", placeholder="직책을 입력하세요")
                        second_approver['department'] = st.text_input("2차 승인자 부서", placeholder="부서를 입력하세요")
            else:
                st.warning("2차 승인자로 선택할 수 있는 직원이 없습니다.")
            
            with col2:
                # 선택된 승인자의 부서 표시
                if second_approver['employee_name'] != '직접 입력':
                    st.text_input("부서", value=second_approver.get('department', ''), disabled=True, key="second_dept")
                else:
                    second_approver['department'] = st.text_input("부서", placeholder="부서명 입력", key="second_dept_input")
            
            with col3:
                # 선택된 승인자의 직급 표시
                if second_approver['employee_name'] != '직접 입력':
                    st.text_input("직급", value=second_approver.get('position', ''), disabled=True, key="second_pos")
                else:
                    second_approver['position'] = st.text_input("직급", placeholder="직급 입력", key="second_pos_input")
        
        # 최종 승인자 (고액 시 필수)
        st.write(f"**{get_text('expense_request.final_approver_optional')}**")
        use_final_approver = st.checkbox(get_text("expense_request.use_final_approver"))
        final_approver = None
        
        # 금액별 자동 승인 경로 설정
        if amount >= 5000000:  # 500만원 이상
            use_final_approver = True
            use_second_approver = True
            st.info("💡 500만원 이상 지출은 1차→2차→최종 승인이 필요합니다.")
        elif amount >= 1000000:  # 100만원 이상
            use_second_approver = True
            st.info("💡 100만원 이상 지출은 1차→2차 승인이 필요합니다.")
        else:
            st.info("💡 100만원 미만 지출은 1차 승인만 필요합니다.")
        
        if use_final_approver:
            # 최종 승인자 필터링 (모든 승인자 선택 가능)
            final_approver_filtered = approver_options  # 모든 승인자 선택 가능
                
            col1, col2, col3 = st.columns(3)
            
            with col1:
                final_approver_name = st.selectbox(
                    "최종 승인자 선택", 
                    list(final_approver_filtered.keys()),
                    help=f"금액: {amount:,.0f}원 승인 가능한 경영진"
                )
                final_approver = final_approver_filtered[final_approver_name].copy()
                
                # 직접 입력 옵션인 경우
                if final_approver['employee_name'] == '직접 입력':
                    final_approver['employee_name'] = st.text_input("최종 승인자 이름", placeholder="승인자 이름을 입력하세요")
            
            with col2:
                # 선택된 승인자의 부서 표시
                if final_approver['employee_name'] != '직접 입력':
                    st.text_input("부서", value=final_approver.get('department', ''), disabled=True, key="final_dept")
                else:
                    final_approver['department'] = st.text_input("부서", placeholder="부서명 입력", key="final_dept_input")
            
            with col3:
                # 선택된 승인자의 직급 표시
                if final_approver['employee_name'] != '직접 입력':
                    st.text_input("직급", value=final_approver.get('position', ''), disabled=True, key="final_pos")
                else:
                    final_approver['position'] = st.text_input("직급", placeholder="직급 입력", key="final_pos_input")
        
        # 제출 버튼
        submitted = st.form_submit_button(f"🚀 {get_text('expense_request.submit_button')}", type="primary")
        
        if submitted:
            # 필수 필드 검증
            if not expense_title or not expense_description or amount <= 0:
                st.error(get_text("expense_request.required_field"))
                return
            
            # 현재 로그인 사용자 정보 사용
            request_data = {
                'requester_id': current_user_info['employee_id'],
                'requester_name': current_user_info['employee_name'],
                'expense_title': expense_title,
                'expense_description': expense_description,
                'category': category,
                'amount': amount,
                'currency': currency,
                'expected_date': expected_date.strftime('%Y-%m-%d'),
                'attachment_path': attachment.name if attachment else '',
                'notes': notes
            }
            
            # 승인자 설정
            approval_settings = []
            
            # 1차 승인자 추가
            if first_approver:
                approval_settings.append({
                    'approver_id': first_approver['employee_id'],
                    'approver_name': first_approver['employee_name'],
                    'is_required': True
                })
            
            # 2차 승인자 추가
            if second_approver:
                approval_settings.append({
                    'approver_id': second_approver['employee_id'],
                    'approver_name': second_approver['employee_name'],
                    'is_required': True
                })
            
            # 최종 승인자 추가
            if final_approver:
                approval_settings.append({
                    'approver_id': final_approver['employee_id'],
                    'approver_name': final_approver['employee_name'],
                    'is_required': True
                })
            
            # 요청서 생성
            success, message = expense_manager.create_expense_request(request_data, approval_settings)
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def show_my_requests(expense_manager, user_id, get_text):
    """내 요청서 현황을 표시합니다."""
    st.header("📋 내 요청서 현황")
    
    # 내 요청서 목록 가져오기 (SQLite 기반)
    my_requests_df = expense_manager.get_expense_requests(requester_id=user_id)
    
    if len(my_requests_df) == 0:
        st.info("등록된 지출요청서가 없습니다.")
        return
    
    # 상태별 필터링
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("상태 필터", ["전체", "pending", "approved", "rejected", "completed"])
    with col2:
        period_filter = st.selectbox("기간 필터", ["전체", "최근 1주일", "최근 1개월", "최근 3개월"])
    
    # 필터링 적용
    filtered_requests = my_requests_df.copy()
    
    if status_filter != "전체":
        filtered_requests = filtered_requests[filtered_requests['status'] == status_filter]
    
    if period_filter != "전체":
        days_map = {"최근 1주일": 7, "최근 1개월": 30, "최근 3개월": 90}
        if period_filter in days_map:
            cutoff_date = (datetime.now() - timedelta(days=days_map[period_filter])).strftime('%Y-%m-%d')
            filtered_requests = filtered_requests[filtered_requests['request_date'] >= cutoff_date]
    
    # 요청서 목록 표시
    if len(filtered_requests) > 0:
        for _, request in filtered_requests.iterrows():
            with st.expander(f"🎫 {request['expense_title']} - {request['status']} ({request['request_date']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**요청번호:** {request['request_id']}")
                    st.write(f"**카테고리:** {request['category']}")
                    st.write(f"**금액:** {request['amount']:,.0f} {request['currency']}")
                
                with col2:
                    st.write(f"**상태:** {request.get('status', 'N/A')}")
                    st.write(f"**예상지출일:** {request.get('expected_date', 'N/A')}")
                
                with col3:
                    st.write(f"**요청일:** {request.get('request_date', 'N/A')}")
                    st.write(f"**수정일:** {request.get('updated_date', 'N/A')}")
                
                st.write(f"**지출내용:** {request.get('expense_description', 'N/A')}")
                
                if request.get('notes'):
                    st.write(f"**비고:** {request.get('notes')}")
                
                # 상세보기 버튼
                if st.button(f"📋 상세보기", key=f"detail_{request['request_id']}"):
                    show_request_detail_modal(expense_manager, request['request_id'])
    else:
        st.info("조건에 맞는 요청서가 없습니다.")

def show_pending_approvals(expense_manager, user_id, get_text):
    """승인 대기 목록을 표시합니다."""
    st.header("✅ 승인 대기 목록")
    
    try:
        # 승인 대기 목록 가져오기 (SQLite 기반)
        pending_approvals_df = expense_manager.get_expense_requests(status='pending')
        
        if len(pending_approvals_df) == 0:
            st.info("승인 대기 중인 요청이 없습니다.")
            return
        
        # 승인 대기 목록을 리스트로 변환
        pending_approvals = []
        for _, row in pending_approvals_df.iterrows():
            pending_approvals.append(row.to_dict())
    
        # 승인 대기 목록 표시
        for approval in pending_approvals:
            with st.expander(f"🎫 {approval['expense_title']} - {approval['amount']:,.0f} {approval['currency']} ({approval['request_date']})"):
                col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**요청번호:** {approval['request_id']}")
                st.write(f"**요청자:** {approval['requester_name']}")
                st.write(f"**카테고리:** {approval['category']}")
                st.write(f"**금액:** {approval['amount']:,.0f} {approval['currency']}")
                st.write(f"**예상지출일:** {approval['expected_date']}")
            
            with col2:
                st.write(f"**승인단계:** {approval['approval_step']}")
                st.write(f"**요청일:** {approval['request_date']}")
                st.write(f"**지출내용:** {approval['expense_description']}")
                if approval.get('notes'):
                    st.write(f"**비고:** {approval['notes']}")
            
            # 승인/반려 처리
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                comments = st.text_area(
                    "승인/반려 사유", 
                    placeholder="승인/반려 사유를 입력하세요 (선택사항)",
                    key=f"comments_{approval['approval_id']}"
                )
            
            with col2:
                if st.button(f"✅ 승인", key=f"approve_{approval['approval_id']}", type="primary"):
                    process_approval_action(expense_manager, approval['approval_id'], user_id, '승인', comments)
                    st.rerun()
            
            with col3:
                if st.button(f"❌ 반려", key=f"reject_{approval['approval_id']}", type="secondary"):
                    process_approval_action(expense_manager, approval['approval_id'], user_id, '반려', comments)
                    st.rerun()
    
        st.write(f"**승인 대기 건수:** {len(pending_approvals)}건")
        
    except Exception as e:
        st.error(f"승인 대기 목록 조회 중 오류: {str(e)}")

def show_expense_statistics(expense_manager, get_text):
    """지출 현황 분석을 표시합니다."""
    st.header("📊 지출 현황 분석")
    
    # 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("종료일", value=datetime.now().date())
    
    # 통계 조회
    try:
        stats = expense_manager.get_expense_statistics(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
    except Exception as e:
        st.error(f"승인 통계를 불러오는 중 오류가 발생했습니다: {str(e)}")
        stats = None
    
    if stats and isinstance(stats, dict) and stats.get('total_count', 0) > 0:
        # 주요 지표
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 지출금액", f"{stats['total_amount']:,.0f}")
        with col2:
            st.metric("총 건수", f"{stats['total_count']:,}")
        with col3:
            st.metric("평균 지출금액", f"{stats['average_amount']:,.0f}")
        with col4:
            by_status = stats.get('by_status', {})
            if isinstance(by_status, dict):
                approved_count = by_status.get('승인', 0) + by_status.get('완료', 0)
                approval_rate = (approved_count / stats['total_count'] * 100) if stats['total_count'] > 0 else 0
                st.metric("승인율", f"{approval_rate:.1f}%")
            else:
                st.metric("승인율", "0.0%")
        
        # 카테고리별 지출 차트
        by_category = stats.get('by_category', {})
        if by_category and isinstance(by_category, dict):
            st.subheader("📈 카테고리별 지출 현황")
            
            categories = list(by_category.keys())
            amounts = list(by_category.values())
            
            fig = px.pie(values=amounts, names=categories, title="카테고리별 지출 비율")
            st.plotly_chart(fig, use_container_width=True)
        
        # 상태별 현황
        by_status = stats.get('by_status', {})
        if by_status and isinstance(by_status, dict):
            st.subheader("📋 상태별 현황")
            
            status_df = pd.DataFrame(list(by_status.items()), columns=['상태', '건수'])
            fig = px.bar(status_df, x='상태', y='건수', title="상태별 요청서 건수")
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("선택한 기간에 지출 데이터가 없습니다.")

def show_approver_management(expense_manager, get_text):
    """승인자 관리를 표시합니다."""
    st.header("👥 승인자 관리")
    
    # 승인자 풀 조회
    approver_pool = expense_manager.get_approver_pool()
    
    if approver_pool:
        st.subheader("현재 승인자 목록")
        
        # 데이터프레임으로 표시
        df = pd.DataFrame(approver_pool)
        df['max_approval_amount'] = df['max_approval_amount'].apply(lambda x: f"{x:,.0f}")
        df.columns = ['직원ID', '이름', '부서', '직급', '승인레벨', '최대승인금액', '활성여부']
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 승인자 추가 (관리자만)
        st.subheader("승인자 추가")
        with st.form("add_approver_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_employee_id = st.text_input("직원 ID")
                new_employee_name = st.text_input("이름")
                new_department = st.text_input("부서")
            
            with col2:
                new_position = st.text_input("직급")
                new_approval_level = st.number_input("승인 레벨", min_value=1, max_value=5, value=1)
                new_max_amount = st.number_input("최대 승인 금액", min_value=0, value=1000000)
            
            submitted = st.form_submit_button("승인자 추가", use_container_width=True)
            
            if submitted:
                if new_employee_id and new_employee_name and new_department and new_position:
                    # 승인자 추가 로직 구현
                    success = expense_manager.add_approver({
                        'employee_id': new_employee_id,
                        'employee_name': new_employee_name,
                        'department': new_department,
                        'position': new_position,
                        'approval_level': new_approval_level,
                        'max_approval_amount': new_max_amount,
                        'is_active': True
                    })
                    
                    if success:
                        st.success("승인자가 성공적으로 추가되었습니다.")
                        st.rerun()
                    else:
                        st.error("승인자 추가 중 오류가 발생했습니다.")
                else:
                    st.error("모든 필드를 입력해주세요.")
    
    else:
        st.warning("등록된 승인자가 없습니다.")

def show_request_detail_modal(expense_manager, request_id):
    """요청서 상세 정보를 모달로 표시합니다."""
    request_data, approval_history = expense_manager.get_request_details(request_id)
    
    if request_data:
        st.subheader(f"📋 요청서 상세 정보 - {request_data['expense_title']}")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**요청번호:** {request_data['request_id']}")
            st.write(f"**요청자:** {request_data['requester_name']}")
            st.write(f"**카테고리:** {request_data['category']}")
            st.write(f"**금액:** {request_data['amount']:,.0f} {request_data['currency']}")
        
        with col2:
            st.write(f"**상태:** {request_data['status']}")
            st.write(f"**요청일:** {request_data['request_date']}")
            st.write(f"**예상지출일:** {request_data['expected_date']}")
            st.write(f"**진행단계:** {request_data['current_step']}/{request_data['total_steps']}")
        
        st.write(f"**지출내용:** {request_data['expense_description']}")
        
        if request_data['notes']:
            st.write(f"**비고:** {request_data['notes']}")
        
        # 승인 이력
        if approval_history:
            st.subheader("승인 이력")
            for approval in approval_history:
                status_icon = "✅" if approval['result'] == '승인' else "❌" if approval['result'] == '반려' else "⏳"
                st.write(f"{status_icon} **{approval['approval_step']}단계** - {approval['approver_name']} ({approval['result']})")
                if approval['comments']:
                    st.write(f"   💬 {approval['comments']}")
                if approval['approval_date']:
                    st.write(f"   📅 {approval['approval_date']}")
    else:
        st.error("요청서 정보를 찾을 수 없습니다.")