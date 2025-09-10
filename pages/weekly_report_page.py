"""
주간 보고 게시판 페이지
- 등록된 사용자만 열람 가능한 주간 보고서 시스템
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

def show_weekly_report_page(current_user_id, get_text):
    """주간 보고 게시판 메인 페이지"""
    st.title("📊 주간 보고 게시판")
    
    # 매니저 초기화 (세션 스테이트에서 가져오기)
    report_manager = st.session_state.get('weekly_report_manager')
    employee_manager = st.session_state.get('employee_manager')
    
    if not report_manager:
        st.error("주간 보고서 매니저가 초기화되지 않았습니다.")
        return
    
    if not employee_manager:
        st.error("직원 매니저가 초기화되지 않았습니다.")
        return
    
    # 현재 사용자 정보
    current_user_info = employee_manager.get_employee_by_id(current_user_id)
    current_user_name = current_user_info.get('name', current_user_id) if current_user_info else current_user_id
    current_user_dept = current_user_info.get('department', '') if current_user_info else ''
    
    # 탭 메뉴
    tab1, tab2, tab3, tab4 = st.tabs(["📝 보고서 작성", "📋 보고서 목록", "👥 권한 관리", "🔍 검색"])
    
    with tab1:
        show_report_creation(report_manager, current_user_id, current_user_name, current_user_dept)
    
    with tab2:
        show_report_list(report_manager, current_user_id)
    
    with tab3:
        show_permission_management(report_manager, employee_manager, current_user_id)
    
    with tab4:
        show_report_search(report_manager, current_user_id)

def show_report_creation(report_manager, current_user_id, current_user_name, current_user_dept):
    """주간 보고서 작성"""
    st.header("📝 주간 보고서 작성")
    
    # 현재 주 정보 표시
    week_start, week_end = report_manager.get_current_week_dates()
    st.info(f"📅 작성 기간: {week_start.strftime('%Y년 %m월 %d일')} ~ {week_end.strftime('%Y년 %m월 %d일')}")
    
    # 성공 메시지 처리
    if 'report_success_message' in st.session_state:
        st.success(f"✅ 주간 보고서가 성공적으로 저장되었습니다! (ID: {st.session_state.report_success_message})")
        del st.session_state.report_success_message
    
    # 보고서 작성 폼
    with st.form("weekly_report_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            title = st.text_input("제목*", placeholder="예: 2025년 1주차 주간보고")
        
        with col2:
            st.write(f"**작성자:** {current_user_name}")
            st.write(f"**부서:** {current_user_dept}")
        
        # 보고서 내용 템플릿
        st.subheader("📋 주간 보고 내용")
        
        content_template = f"""
## 📊 이번 주 주요 업무 (주요 성과)

### 1. 완료된 업무
- 

### 2. 진행 중인 업무
- 

### 3. 주요 성과 및 결과
- 

## 📈 다음 주 계획

### 1. 예정된 업무
- 

### 2. 목표 및 우선순위
- 

## ⚠️ 이슈 및 건의사항

### 1. 발생한 문제점
- 

### 2. 지원 요청 사항
- 

### 3. 개선 제안
- 

## 📝 기타 사항
- 
        """.strip()
        
        content = st.text_area(
            "보고서 내용*", 
            value=content_template,
            height=400,
            placeholder="위 템플릿을 참고하여 주간 보고서를 작성해주세요."
        )
        
        # 제출 버튼
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📝 임시 저장", type="secondary")
        with col2:
            final_submit = st.form_submit_button("✅ 최종 제출", type="primary")
        
        if submitted or final_submit:
            # 필수 필드 검증
            errors = []
            if not title or not title.strip():
                errors.append("제목을 입력해주세요.")
            if not content or not content.strip():
                errors.append("보고서 내용을 입력해주세요.")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # 보고서 생성
                success, report_id = report_manager.create_report(
                    author_id=current_user_id,
                    author_name=current_user_name,
                    department=current_user_dept,
                    title=title.strip(),
                    content=content.strip()
                )
                
                if success:
                    # 최종 제출인 경우 상태 변경
                    if final_submit:
                        report_manager.update_report_status(report_id, '제출완료')
                        st.session_state.report_success_message = f"{report_id} (최종 제출 완료)"
                    else:
                        st.session_state.report_success_message = f"{report_id} (임시 저장)"
                    
                    st.rerun()
                else:
                    st.error("보고서 저장에 실패했습니다.")

def show_report_list(report_manager, current_user_id):
    """보고서 목록 표시"""
    st.header("📋 내가 볼 수 있는 보고서")
    
    # 접근 가능한 보고서 가져오기
    accessible_reports = report_manager.get_accessible_reports(current_user_id)
    
    if len(accessible_reports) == 0:
        st.info("📄 열람 가능한 보고서가 없습니다.")
        st.write("- 본인이 작성한 보고서")
        st.write("- 열람 권한이 부여된 보고서만 표시됩니다.")
        return
    
    st.write(f"**총 {len(accessible_reports)}건의 보고서를 볼 수 있습니다.**")
    
    # 상태별 필터
    status_filter = st.selectbox("상태 필터", ["전체"] + report_manager.get_report_statuses())
    
    # 필터링 적용
    if status_filter != "전체":
        accessible_reports = accessible_reports[accessible_reports['status'] == status_filter]
    
    # 보고서 목록 표시
    for idx, row in accessible_reports.iterrows():
        with st.expander(f"📄 {row['title']} ({row['report_id']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # 상태 아이콘
                status_icons = {
                    '작성중': '📝',
                    '제출완료': '📤',
                    '승인됨': '✅',
                    '반려': '❌'
                }
                status_icon = status_icons.get(row['status'], '📄')
                
                st.write(f"**작성자:** {row['author_name']} ({row['department']})")
                st.write(f"**기간:** {row['week_start_date']} ~ {row['week_end_date']}")
                st.write(f"**상태:** {status_icon} {row['status']}")
                st.write(f"**작성일:** {row['created_date']}")
                
                if row['submitted_date']:
                    st.write(f"**제출일:** {row['submitted_date']}")
                if row['approved_date']:
                    st.write(f"**승인일:** {row['approved_date']} (승인자: {row['approved_by']})")
                if row['rejection_reason']:
                    st.write(f"**반려 사유:** {row['rejection_reason']}")
            
            with col2:
                if st.button("📖 내용 보기", key=f"view_{row['report_id']}"):
                    st.session_state.view_report_id = row['report_id']
                    st.rerun()
            
            with col3:
                # 본인 보고서인 경우만 상태 변경 가능
                if row['author_id'] == current_user_id and row['status'] == '작성중':
                    if st.button("📤 제출", key=f"submit_{row['report_id']}"):
                        success, message = report_manager.update_report_status(row['report_id'], '제출완료')
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    # 보고서 내용 보기 모달
    if 'view_report_id' in st.session_state:
        show_report_detail_modal(report_manager, st.session_state.view_report_id)

def show_report_detail_modal(report_manager, report_id):
    """보고서 상세 내용 모달"""
    try:
        # SQLite 매니저 메소드 사용
        report = report_manager.get_report_by_id(report_id)
        if not report:
            st.error("보고서를 찾을 수 없습니다.")
            return
        
        st.subheader(f"📄 {report.get('title', 'N/A')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**작성자:** {report.get('author_name', 'N/A')}")
            st.write(f"**부서:** {report.get('department', 'N/A')}")
        with col2:
            st.write(f"**기간:** {report.get('week_start_date', 'N/A')} ~ {report.get('week_end_date', 'N/A')}")
            st.write(f"**상태:** {report.get('status', 'N/A')}")
        
        st.markdown("---")
        st.write("**보고서 내용:**")
        st.markdown(report.get('content', 'N/A'))
        
        if st.button("❌ 닫기"):
            del st.session_state.view_report_id
            st.rerun()
            
    except Exception as e:
        st.error(f"보고서를 불러올 수 없습니다: {e}")
        if st.button("❌ 닫기"):
            del st.session_state.view_report_id
            st.rerun()

def show_permission_management(report_manager, employee_manager, current_user_id):
    """권한 관리"""
    st.header("👥 보고서 열람 권한 관리")
    
    # 본인이 작성한 보고서 가져오기
    try:
        my_reports = report_manager.get_reports_by_author(current_user_id)
        
        if not my_reports:
            st.info("📝 권한을 관리할 보고서가 없습니다. 먼저 보고서를 작성해주세요.")
            return
        
        # 보고서 선택
        report_options = {f"{report.get('title', 'N/A')} ({report.get('report_id', 'N/A')})": report.get('report_id') 
                         for report in my_reports}
        selected_report_display = st.selectbox("보고서 선택", list(report_options.keys()))
        selected_report_id = report_options[selected_report_display]
        
        st.subheader("📋 현재 권한 목록")
        
        # 현재 권한 목록 표시
        permissions = report_manager.get_report_permissions(selected_report_id)
        
        if permissions:
            for perm in permissions:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"👤 {perm.get('authorized_user_name', 'N/A')} ({perm.get('authorized_user_id', 'N/A')})")
                with col2:
                    st.write(f"권한: {perm.get('access_level', 'N/A')}")
                with col3:
                    if st.button("🗑️ 제거", key=f"remove_{perm.get('permission_id')}"):
                        success, message = report_manager.remove_user_permission(
                            selected_report_id, perm.get('authorized_user_id')
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("현재 추가된 권한이 없습니다.")
        
        st.subheader("➕ 새 권한 추가")
        
        # 직원 목록 가져오기
        all_employees = employee_manager.get_all_employees()
        
        # DataFrame이나 리스트인지 확인 후 처리
        if hasattr(all_employees, 'iterrows'):  # DataFrame인 경우
            active_employees = all_employees[
                (all_employees['status'] == '재직') & 
                (all_employees['employee_id'] != current_user_id)
            ]
            employees_data = [(row['name'], row['employee_id']) for _, row in active_employees.iterrows()]
        else:  # 리스트인 경우 (SQLite)
            active_employees = [emp for emp in all_employees 
                             if emp.get('status') == '재직' and emp.get('employee_id') != current_user_id]
            employees_data = [(emp.get('name', 'N/A'), emp.get('employee_id')) for emp in active_employees]
        
        if employees_data:
            with st.form("add_permission_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    employee_options = {f"{name} ({emp_id})": emp_id 
                                      for name, emp_id in employees_data}
                    selected_employee_display = st.selectbox("직원 선택", list(employee_options.keys()))
                    selected_employee_id = employee_options[selected_employee_display]
                    selected_employee_name = selected_employee_display.split(' (')[0]
                
                with col2:
                    access_level = st.selectbox("접근 권한", report_manager.get_access_levels())
                
                if st.form_submit_button("➕ 권한 추가"):
                    success, message = report_manager.add_authorized_user(
                        report_id=selected_report_id,
                        authorized_user_id=selected_employee_id,
                        authorized_user_name=selected_employee_name,
                        access_level=access_level,
                        granted_by=current_user_id
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("권한을 부여할 직원이 없습니다.")
            
    except Exception as e:
        st.error(f"권한 관리 중 오류가 발생했습니다: {e}")

def show_report_search(report_manager, current_user_id):
    """보고서 검색"""
    st.header("🔍 보고서 검색")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("검색어", placeholder="제목, 내용, 작성자로 검색")
    
    with col2:
        status_filter = st.selectbox("상태", ["전체"] + report_manager.get_report_statuses())
    
    if st.button("🔍 검색") or search_term:
        results = report_manager.search_reports(
            user_id=current_user_id,
            search_term=search_term,
            status_filter=status_filter
        )
        
        if results:
            st.write(f"**검색 결과: {len(results)}건**")
            
            # DataFrame이나 리스트인지 확인 후 처리
            if hasattr(results, 'iterrows'):  # DataFrame인 경우
                results_data = results
            else:  # 리스트인 경우 (SQLite)
                results_data = results
            
            for result in (results_data.iterrows() if hasattr(results_data, 'iterrows') else [(None, result) for result in results_data]):
                if hasattr(results_data, 'iterrows'):
                    _, row = result
                    row_data = row
                else:
                    _, row_data = result
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{row_data.get('title', 'N/A') if isinstance(row_data, dict) else row_data['title']}**")
                        author = row_data.get('author_name', 'N/A') if isinstance(row_data, dict) else row_data['author_name']
                        start_date = row_data.get('week_start_date', 'N/A') if isinstance(row_data, dict) else row_data['week_start_date']
                        end_date = row_data.get('week_end_date', 'N/A') if isinstance(row_data, dict) else row_data['week_end_date']
                        st.write(f"작성자: {author} | 기간: {start_date} ~ {end_date}")
                    
                    with col2:
                        status_icons = {
                            '작성중': '📝',
                            '제출완료': '📤',
                            '승인됨': '✅',
                            '반려': '❌'
                        }
                        status = row_data.get('status', 'N/A') if isinstance(row_data, dict) else row_data['status']
                        st.write(f"{status_icons.get(status, '📄')} {status}")
                    
                    with col3:
                        report_id = row_data.get('report_id') if isinstance(row_data, dict) else row_data['report_id']
                        if st.button("📖 보기", key=f"search_view_{report_id}"):
                            st.session_state.view_report_id = report_id
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("검색 결과가 없습니다.")