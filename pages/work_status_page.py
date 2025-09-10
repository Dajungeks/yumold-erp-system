import streamlit as st
from datetime import datetime, date
import json
import pandas as pd

def show_work_status_page(get_text):
    """업무 진행 상태 관리 페이지"""
    st.title(f"📋 {get_text('work_status_management')}")
    
    # 관리자들 초기화
    if 'work_status_manager' not in st.session_state:
        from managers.legacy.work_status_manager import WorkStatusManager
        st.session_state.work_status_manager = WorkStatusManager()
    
    if 'bp_manager_v2' not in st.session_state:
        from scripts.business_process_manager_v2 import BusinessProcessManagerV2
        st.session_state.bp_manager_v2 = BusinessProcessManagerV2()
    
    # 현재 사용자 정보
    current_user_id = st.session_state.get('user_id', '')
    current_user_name = '알 수 없음'
    is_master = st.session_state.get('user_type') == 'master'
    
    # 사용자 이름 가져오기
    if current_user_id:
        try:
            employee_data = st.session_state.employee_manager.get_employee_by_id(current_user_id)
            if employee_data:
                current_user_name = employee_data.get('name', '알 수 없음')
        except:
            current_user_name = current_user_id
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📊 {get_text('work_status_dashboard')}", 
        f"➕ {get_text('new_work')}", 
        f"📝 {get_text('work_management')}", 
        f"👥 {get_text('assignee_status')}"
    ])
    
    with tab1:
        show_work_status_dashboard(get_text)
    
    with tab2:
        show_create_work_status(current_user_id, current_user_name, get_text)
    
    with tab3:
        show_manage_work_status(current_user_id, is_master, get_text)
    
    with tab4:
        show_assignee_dashboard(get_text)

def show_work_status_dashboard(get_text):
    """업무 상태 대시보드"""
    st.header(f"📊 {get_text('work_status_dashboard')}")
    
    # 모든 업무 상태 조회
    work_status_list = []
    if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
        work_status_list = st.session_state.work_status_manager.get_all_work_status()
    else:
        st.error(get_text("work_manager_not_initialized"))
    
    if len(work_status_list) == 0:
        st.info(get_text("no_registered_work"))
        return
    
    # 상태별 통계
    col1, col2, col3, col4 = st.columns(4)
    
    status_counts = {}
    priority_counts = {}
    for work in work_status_list:
        status = work.get('status', '알 수 없음')
        priority = work.get('priority', '알 수 없음')
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    with col1:
        st.metric(get_text("total_work_count"), len(work_status_list))
    with col2:
        st.metric(get_text("in_progress"), status_counts.get('진행중', 0))
    with col3:
        st.metric(get_text("completed"), status_counts.get('완료', 0))
    with col4:
        st.metric(get_text("waiting"), status_counts.get('대기', 0))
    
    st.divider()
    
    # 우선순위별 현황
    st.subheader(get_text("priority_status"))
    priority_col1, priority_col2, priority_col3 = st.columns(3)
    
    with priority_col1:
        st.metric(f"🔴 {get_text('high_priority')}", priority_counts.get('높음', 0))
    with priority_col2:
        st.metric(f"🟡 {get_text('normal_priority')}", priority_counts.get('보통', 0))
    with priority_col3:
        st.metric(f"🟢 {get_text('low_priority')}", priority_counts.get('낮음', 0))
    
    st.divider()
    
    # 최근 업무 목록
    st.subheader(f"📋 {get_text('recent_work_list')}")
    
    # 테이블 헤더 (진행률 업데이트 기능 추가)
    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.2, 0.8, 0.8, 1, 1.2, 1])
    
    with col1:
        st.markdown(f"**제목**")
    with col2:
        st.markdown(f"**담당자**")
    with col3:
        st.markdown(f"**상태**")
    with col4:
        st.markdown(f"**우선순위**")
    with col5:
        st.markdown(f"**진행률**")
    with col6:
        st.markdown(f"**마감일**")
    with col7:
        st.markdown(f"**업데이트**")
    
    st.divider()
    
    # 최근 생성된 순으로 정렬
    sorted_works = sorted(work_status_list, key=lambda x: x.get('created_date', ''), reverse=True)
    
    for work in sorted_works[:10]:  # 최근 10개만 표시
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.2, 0.8, 0.8, 1, 1.2, 1])
        
        status_id = work.get('status_id', '')
        
        # 현재 사용자가 담당자인지 확인
        assigned_to = work.get('assigned_to', '')
        is_assignee = False
        current_user_id = st.session_state.get('user_id', '')
        is_master = st.session_state.get('user_type') == 'master'
        
        if assigned_to and '(' in assigned_to:
            assignee_id = assigned_to.split('(')[1].replace(')', '').strip()
            is_assignee = assignee_id == current_user_id
        elif assigned_to:
            is_assignee = assigned_to.strip() == current_user_id
        
        with col1:
            st.text(work.get('title', '')[:25] + "..." if len(work.get('title', '')) > 25 else work.get('title', ''))
        with col2:
            if '(' in assigned_to:
                english_name = assigned_to.split('(')[0].strip()
                st.text(english_name)
            else:
                st.text(assigned_to)
        with col3:
            status = work.get('status', '대기')
            if status == '완료':
                st.success(status)
            elif status == '진행중':
                st.warning(status)
            else:
                st.info(status)
        with col4:
            priority = work.get('priority', '보통')
            if priority == '높음':
                st.error(priority)
            elif priority == '보통':
                st.warning(priority)
            else:
                st.success(priority)
        with col5:
            progress = float(work.get('progress', 0))
            st.progress(progress / 100)
            st.text(f"{progress}%")
        with col6:
            due_date = work.get('due_date', '')
            st.text(due_date[:10] if due_date else get_text('due_date_undefined'))
        with col7:
            # 담당자나 마스터만 업데이트 버튼 표시
            if is_assignee or is_master:
                if st.button("📈", key=f"quick_update_{status_id}", help="진행률 업데이트"):
                    st.session_state.quick_update_work = status_id
                    st.rerun()
            else:
                st.text("")

def show_create_work_status(current_user_id, current_user_name, get_text):
    """새 업무 생성"""
    st.header(f"➕ {get_text('new_work_registration')}")
    
    # 폼을 사용하여 등록 후 자동 리셋 지원
    with st.form("create_work_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(get_text("work_title_input"), placeholder=get_text("work_title_placeholder"))
            status = st.selectbox(get_text("work_status_select"), [get_text("status_waiting"), get_text("status_in_progress"), get_text("status_completed"), get_text("status_hold"), get_text("status_cancelled")])
            category = st.selectbox(get_text("work_category"), [get_text("category_general"), get_text("category_sales"), get_text("category_service"), get_text("category_tech_support"), get_text("category_management"), get_text("category_others")])
        
        with col2:
            # 등록된 직원 목록 가져오기
            assigned_to_options = [get_text("assignee_unassigned")]
            try:
                if hasattr(st.session_state, 'employee_manager') and st.session_state.employee_manager:
                    employees_data = st.session_state.employee_manager.get_all_employees()
                    if isinstance(employees_data, list):
                        for emp in employees_data:
                            if emp.get('name') and emp.get('employee_id'):
                                assigned_to_options.append(f"{emp['name']} ({emp['employee_id']})")
                    elif hasattr(employees_data, 'iterrows'):
                        for _, emp in employees_data.iterrows():
                            if pd.notna(emp.get('name')) and pd.notna(emp.get('employee_id')):
                                assigned_to_options.append(f"{emp['name']} ({emp['employee_id']})")
            except Exception as e:
                st.warning(f"{get_text('employee_data_load_error')}: {e}")
            
            assigned_to = st.selectbox(get_text("work_assignee_select"), assigned_to_options)
            
            priority = st.selectbox(get_text("work_priority_select"), [get_text("priority_low"), get_text("priority_normal"), get_text("priority_high"), get_text("priority_urgent")])
            
            due_date = st.date_input(get_text("work_due_date_select"), value=None)
            
            progress = st.slider(get_text("work_progress_slider"), 0, 100, 0, key="create_work_progress")
        
        description = st.text_area(get_text("work_description"), placeholder=get_text("work_description_placeholder"), height=100)
        
        tags = st.text_input(get_text("work_tags"), placeholder=get_text("work_tags_placeholder"))
        
        submitted = st.form_submit_button(f"📝 {get_text('btn_register_work')}", type="primary", use_container_width=True)
        
        if submitted:
            if not title:
                st.error(get_text("enter_work_title"))
            elif not description:
                st.error(get_text("enter_work_description"))
            else:
                # 마감일 처리
                due_date_str = due_date.strftime('%Y-%m-%d') if due_date else ''
                
                if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
                    success, message = st.session_state.work_status_manager.create_work_status(
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    assigned_to=assigned_to,
                    created_by=current_user_id,
                    due_date=due_date_str,
                    category=category,
                    tags=tags,
                    progress=progress
                    )
                    
                    if success:
                        st.success(get_text('work_registered_successfully'))
                        
                        # 폼이 자동으로 리셋되므로 추가 처리 불필요
                        st.rerun()
                    else:
                        st.error(get_text('work_registration_failed'))
                else:
                    st.error("업무 상태 관리자가 초기화되지 않았습니다.")

def show_manage_work_status(current_user_id, is_master, get_text):
    """업무 관리"""
    st.header(f"📝 {get_text('work_management')}")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(get_text("status_filter"), [get_text("status_filter_all"), get_text("status_waiting"), get_text("status_in_progress"), get_text("status_completed"), get_text("status_hold"), get_text("status_cancelled")])
    with col2:
        filter_priority = st.selectbox(get_text("priority_filter"), [get_text("priority_filter_all"), get_text("priority_low"), get_text("priority_normal"), get_text("priority_high"), get_text("priority_urgent")])
    with col3:
        filter_assignee = st.text_input(get_text("assignee_filter"), placeholder=get_text("assignee_filter_placeholder"))
    
    # 업무 목록 조회
    work_status_list = []
    if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
        work_status_list = st.session_state.work_status_manager.get_all_work_status()
    else:
        st.error(get_text("work_manager_not_initialized"))
        return
    
    # 필터 적용
    if filter_status != get_text("status_filter_all"):
        work_status_list = [w for w in work_status_list if w.get('status') == filter_status]
    if filter_priority != get_text("priority_filter_all"):
        work_status_list = [w for w in work_status_list if w.get('priority') == filter_priority]
    if filter_assignee:
        work_status_list = [w for w in work_status_list if filter_assignee in w.get('assigned_to', '')]
    
    if len(work_status_list) == 0:
        st.info(get_text("no_registered_work"))
        return
    
    # 안내 메시지 추가
    st.info("💡 **업무 수정/삭제 방법**: 각 업무를 클릭하면 나타나는 버튼들을 사용하세요. 마스터이거나 업무 작성자만 수정/삭제가 가능합니다.")
    
    # 업무 목록 표시
    for work in work_status_list:
        with st.expander(f"📋 {work.get('title', '')} - {work.get('status', '')}"):
            # 기본 정보 표시
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**{get_text('work_assignee')}:** {work.get('assigned_to', get_text('assignee_unassigned'))}")
                st.write(f"**{get_text('work_status')}:** {work.get('status', get_text('status_waiting'))}")
                st.write(f"**{get_text('work_priority')}:** {work.get('priority', get_text('priority_normal'))}")
            
            with col2:
                st.write(f"**{get_text('work_category')}:** {work.get('category', get_text('category_general'))}")
                st.write(f"**{get_text('created_date')}:** {work.get('created_date', '')[:10]}")
                st.write(f"**{get_text('work_due_date')}:** {work.get('due_date', get_text('due_date_undefined'))}")
            
            with col3:
                progress = float(work.get('progress', 0))
                st.write(f"**{get_text('work_progress')}:** {progress}%")
                st.progress(progress / 100)
                tags = work.get('tags', '')
                if tags:
                    st.write(f"**{get_text('work_tags')}:** {tags}")
            
            st.write(f"**{get_text('description')}:** {work.get('description', '')}")
            
            # 댓글 표시
            comments = work.get('comments', '[]')
            try:
                comments_list = json.loads(comments) if comments else []
            except:
                comments_list = []
            
            if comments_list:
                st.write(f"**{get_text('work_comments')}:**")
                for comment in comments_list:
                    st.write(f"👤 {comment.get('author', '')}: {comment.get('comment', '')} ({comment.get('timestamp', '')[:16]})")
            
            # 액션 버튼
            col1, col2, col3, col4, col5 = st.columns(5)
            
            status_id = work.get('status_id', '')
            # 마스터는 모든 업무를 수정/삭제 가능, 일반 사용자는 본인 작성 업무만
            can_edit = is_master or work.get('created_by') == current_user_id
            # 담당자도 상태 변경 가능 (담당자 매칭 개선)
            assigned_to = work.get('assigned_to', '')
            is_assignee = False
            if assigned_to and '(' in assigned_to:
                # "LUU THI HANG (2508002)" 형식에서 ID 추출
                assignee_id = assigned_to.split('(')[1].replace(')', '').strip()
                is_assignee = assignee_id == current_user_id
            elif assigned_to:
                # 직접 이름으로 비교
                is_assignee = assigned_to.strip() == current_user_id
                
            can_change_status = is_master or work.get('created_by') == current_user_id or is_assignee
            
            with col1:
                if st.button("💬 댓글", key=f"comment_{status_id}"):
                    st.session_state.comment_work_status = status_id
                    st.rerun()
            
            with col2:
                if can_change_status:
                    if st.button("🔄 상태변경", key=f"status_{status_id}"):
                        st.session_state.change_status = status_id
                        st.rerun()
                else:
                    st.write("") # 빈 공간
            
            with col3:
                # 담당자인 경우 빠른 진행률 업데이트 버튼 표시 (마스터 제외)
                if is_assignee and not is_master:
                    if st.button("📈 진행률", key=f"progress_{status_id}"):
                        st.session_state.quick_update_work = status_id
                        st.rerun()
                else:
                    st.write("") # 빈 공간
            
            with col4:
                if can_edit:
                    if st.button("✏️ **업무 수정**", key=f"edit_{status_id}", type="secondary"):
                        st.session_state.edit_work_status = status_id
                        st.rerun()
                else:
                    st.caption("🔒 수정 권한 없음") 
            
            with col5:
                if can_edit:
                    # 삭제 확인을 위한 2단계 버튼
                    delete_confirm_key = f"delete_confirm_{status_id}"
                    
                    if st.session_state.get(delete_confirm_key, False):
                        st.error("⚠️ 정말 삭제하시겠습니까?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅", key=f"delete_yes_{status_id}", help="삭제 확인"):
                                if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
                                    success, message = st.session_state.work_status_manager.delete_work_status(status_id)
                                    if success:
                                        st.success(message)
                                        st.session_state[delete_confirm_key] = False
                                        st.rerun()
                                    else:
                                        st.error(message)
                                        st.session_state[delete_confirm_key] = False
                                else:
                                    st.error("업무 상태 관리자가 초기화되지 않았습니다.")
                                    st.session_state[delete_confirm_key] = False
                        with col_no:
                            if st.button("❌", key=f"delete_no_{status_id}", help="삭제 취소"):
                                st.session_state[delete_confirm_key] = False
                                st.rerun()
                    else:
                        if st.button("🗑️ **업무 삭제**", key=f"delete_{status_id}", type="secondary"):
                            st.session_state[delete_confirm_key] = True
                            st.rerun()
                else:
                    st.caption("🔒 삭제 권한 없음")
    
    # 상태 변경 모달
    if st.session_state.get('change_status'):
        show_status_change_modal()
    
    # 댓글 추가 모달
    if st.session_state.get('comment_work_status'):
        show_comment_modal(current_user_id)
    
    # 업무 수정 모달
    if st.session_state.get('edit_work_status'):
        show_edit_work_status_modal(current_user_id, is_master)
    
    # 빠른 진행률 업데이트 모달 (대시보드용)
    if st.session_state.get('quick_update_work'):
        show_quick_update_modal()

def show_status_change_modal():
    """상태 변경 모달"""
    status_id = st.session_state.get('change_status')
    
    st.subheader("🔄 상태 변경")
    
    new_status = st.selectbox("새 상태", ["대기", "진행중", "완료", "보류", "취소"], key=f"status_change_{status_id}")
    new_progress = st.slider("진행률 (%)", 0, 100, 0, key=f"progress_change_{status_id}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 변경"):
            updates = {
                'status_id': status_id,
                'status': new_status,
                'progress': new_progress
            }
            if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
                success, message = st.session_state.work_status_manager.update_work_status(updates)
                if success:
                    st.success(message)
                    st.session_state.change_status = None
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("업무 상태 관리자가 초기화되지 않았습니다.")
    
    with col2:
        if st.button("❌ 취소"):
            st.session_state.change_status = None
            st.rerun()

def show_comment_modal(current_user_id):
    """댓글 추가 모달"""
    status_id = st.session_state.get('comment_work_status')
    
    st.subheader("💬 댓글 추가")
    
    comment = st.text_area("댓글 내용", placeholder="댓글을 입력하세요")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 추가"):
            if comment:
                if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
                    success, message = st.session_state.work_status_manager.add_comment(status_id, comment, current_user_id)
                    if success:
                        st.success(message)
                        st.session_state.comment_work_status = None
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("업무 상태 관리자가 초기화되지 않았습니다.")
            else:
                st.error("댓글 내용을 입력해주세요.")
    
    with col2:
        if st.button("❌ 취소"):
            st.session_state.comment_work_status = None
            st.rerun()

def show_assignee_dashboard(get_text):
    """담당자별 현황"""
    st.header(f"👥 {get_text('assignee_dashboard')}")
    
    work_status_list = []
    if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
        work_status_list = st.session_state.work_status_manager.get_all_work_status()
    else:
        st.error(get_text("work_manager_not_initialized"))
        return
    
    if len(work_status_list) == 0:
        st.info(get_text("no_registered_work"))
        return
    
    # 담당자별 그룹화
    assignee_stats = {}
    for work in work_status_list:
        assignee = work.get('assigned_to', get_text('assignee_unassigned'))
        if assignee not in assignee_stats:
            assignee_stats[assignee] = {'total': 0, '완료': 0, '진행중': 0, '대기': 0}
        
        assignee_stats[assignee]['total'] += 1
        status = work.get('status', '대기')
        if status in assignee_stats[assignee]:
            assignee_stats[assignee][status] += 1
    
    # 담당자별 현황 표시
    for assignee, stats in assignee_stats.items():
        with st.expander(f"👤 {assignee} ({get_text('total_count')} {stats['total']}건)"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(get_text("total_work_count"), stats['total'])
            with col2:
                st.metric(get_text("completed"), stats['완료'])
            with col3:
                st.metric(get_text("in_progress"), stats['진행중'])
            with col4:
                st.metric(get_text("waiting"), stats['대기'])
            
            # 완료율 계산
            completion_rate = (stats['완료'] / stats['total']) * 100 if stats['total'] > 0 else 0
            st.write(f"**{get_text('completion_rate')}:** {completion_rate:.1f}%")
            st.progress(completion_rate / 100)

def show_edit_work_status_modal(current_user_id, is_master):
    """업무 수정 모달"""
    status_id = st.session_state.get('edit_work_status')
    
    if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
        work_data = st.session_state.work_status_manager.get_work_status_by_id(status_id)
    else:
        st.error("업무 상태 관리자가 초기화되지 않았습니다.")
        return
    
    if not work_data or len(work_data) == 0:
        st.error("업무 데이터를 찾을 수 없습니다.")
        return
    
    # 권한 확인 - 마스터는 모든 업무 수정 가능
    can_edit = is_master or work_data.get('created_by') == current_user_id
    
    if not can_edit:
        st.error("이 업무를 수정할 권한이 없습니다.")
        return
    
    st.subheader("✏️ 업무 수정")
    
    # 현재 데이터로 폼 초기화
    title = st.text_input("업무 제목", value=work_data.get('title', ''))
    description = st.text_area("업무 설명", value=work_data.get('description', ''))
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox("카테고리", 
                               ["일반", "긴급", "개발", "영업", "고객지원", "기타"],
                               index=0 if work_data.get('category') not in ["일반", "긴급", "개발", "영업", "고객지원", "기타"] 
                               else ["일반", "긴급", "개발", "영업", "고객지원", "기타"].index(work_data.get('category', '일반')))
        
        priority = st.selectbox("우선순위", 
                               ["낮음", "보통", "높음", "긴급"],
                               index=0 if work_data.get('priority') not in ["낮음", "보통", "높음", "긴급"]
                               else ["낮음", "보통", "높음", "긴급"].index(work_data.get('priority', '보통')))
    
    with col2:
        status = st.selectbox("상태", 
                             ["대기", "진행중", "완료", "보류", "취소"],
                             index=0 if work_data.get('status') not in ["대기", "진행중", "완료", "보류", "취소"]
                             else ["대기", "진행중", "완료", "보류", "취소"].index(work_data.get('status', '대기')))
        
        progress = st.slider("진행률 (%)", 0, 100, int(work_data.get('progress', 0)), key=f"edit_progress_{work_data.get('work_id', 'unknown')}")
    
    # 담당자 선택
    assigned_to_options = ["미지정"]
    try:
        if hasattr(st.session_state, 'employee_manager') and st.session_state.employee_manager:
            employees_data = st.session_state.employee_manager.get_all_employees()
            if isinstance(employees_data, list):
                for emp in employees_data:
                    if emp.get('name') and emp.get('employee_id'):
                        assigned_to_options.append(f"{emp['name']} ({emp['employee_id']})")
            elif hasattr(employees_data, 'iterrows'):
                for _, emp in employees_data.iterrows():
                    if pd.notna(emp.get('name')) and pd.notna(emp.get('employee_id')):
                        assigned_to_options.append(f"{emp['name']} ({emp['employee_id']})")
    except Exception as e:
        st.warning(f"직원 데이터 로드 오류: {e}")
    
    current_assigned = work_data.get('assigned_to', '미지정')
    assigned_index = 0
    if current_assigned in assigned_to_options:
        assigned_index = assigned_to_options.index(current_assigned)
    
    assigned_to = st.selectbox("담당자", assigned_to_options, index=assigned_index, key="edit_assigned_to")
    
    # 마감일
    try:
        current_due_date = datetime.strptime(work_data.get('due_date', ''), '%Y-%m-%d').date()
    except:
        current_due_date = date.today()
    
    due_date = st.date_input("마감일", value=current_due_date)
    
    # 태그
    tags = st.text_input("태그 (쉼표로 구분)", value=work_data.get('tags', ''))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 수정 완료"):
            if title and description:
                update_data = {
                    'status_id': status_id,
                    'title': title,
                    'description': description,
                    'category': category,
                    'priority': priority,
                    'status': status,
                    'progress': progress,
                    'assigned_to': assigned_to,
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'tags': tags,
                    'updated_by': current_user_id,
                    'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                success, message = st.session_state.work_status_manager.update_work_status(update_data)
                if success:
                    st.success(message)
                    st.session_state.edit_work_status = None
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("제목과 설명을 입력해주세요.")
    
    with col2:
        if st.button("❌ 취소"):
            st.session_state.edit_work_status = None
            st.rerun()

def show_quick_update_modal():
    """빠른 진행률 업데이트 모달 (대시보드용)"""
    status_id = st.session_state.get('quick_update_work')
    
    if not status_id:
        return
    
    # 현재 업무 정보 가져오기
    work_data = None
    if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
        work_list = st.session_state.work_status_manager.get_all_work_status()
        work_data = next((work for work in work_list if work.get('status_id') == status_id), None)
    
    if not work_data:
        st.error("업무 정보를 찾을 수 없습니다.")
        st.session_state.quick_update_work = None
        return
    
    st.subheader(f"📈 진행률 업데이트: {work_data.get('title', '')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_progress = float(work_data.get('progress', 0))
        st.write(f"현재 진행률: **{current_progress}%**")
        
        new_progress = st.slider("새 진행률 (%)", 0, 100, int(current_progress), key=f"quick_progress_{status_id}")
        
        # 상태 자동 조정 제안
        suggested_status = work_data.get('status', '대기')
        if new_progress == 0:
            suggested_status = '대기'
        elif 0 < new_progress < 100:
            suggested_status = '진행중'
        elif new_progress == 100:
            suggested_status = '완료'
        
        new_status = st.selectbox("상태", ["대기", "진행중", "완료", "보류", "취소"], 
                                 index=["대기", "진행중", "완료", "보류", "취소"].index(suggested_status))
    
    with col2:
        st.write(f"담당자: **{work_data.get('assigned_to', '미지정')}**")
        st.write(f"우선순위: **{work_data.get('priority', '보통')}**")
        st.write(f"마감일: **{work_data.get('due_date', '미정')[:10]}**")
        
        # 간단한 코멘트 추가
        comment = st.text_area("업데이트 코멘트 (선택사항)", 
                              placeholder="진행 상황에 대한 간단한 설명을 입력하세요",
                              height=80)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 업데이트"):
            # 진행률과 상태 업데이트
            updates = {
                'progress': new_progress,
                'status': new_status
            }
            
            if hasattr(st.session_state, 'work_status_manager') and st.session_state.work_status_manager:
                updates['status_id'] = status_id
                success, message = st.session_state.work_status_manager.update_work_status(updates)
                
                # 코멘트가 있으면 추가
                if success and comment.strip():
                    current_user_id = st.session_state.get('user_id', 'unknown')
                    comment_text = f"진행률 업데이트: {current_progress}% → {new_progress}%. {comment.strip()}"
                    st.session_state.work_status_manager.add_comment(status_id, comment_text, current_user_id)
                
                if success:
                    st.success("진행률이 업데이트되었습니다!")
                    st.session_state.quick_update_work = None
                    st.rerun()
                else:
                    st.error(f"업데이트 실패: {message}")
            else:
                st.error("업무 상태 관리자가 초기화되지 않았습니다.")
    
    with col2:
        if st.button("❌ 취소"):
            st.session_state.quick_update_work = None
            st.rerun()