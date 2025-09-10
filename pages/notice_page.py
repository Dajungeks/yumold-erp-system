"""
게시판 페이지 - 마스터/직원 게시판 관리
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def show_notice_page(get_text):
    """게시판 메뉴 페이지 표시"""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'notice_management', get_text)
    
    st.title(f"📋 {get_text('notice_management')}")
    
    # 게시판 관리자 초기화
    if 'notice_manager' not in st.session_state:
        from notice_manager import NoticeManager
        st.session_state.notice_manager = NoticeManager()
    
    # 현재 사용자 정보
    user_role = st.session_state.get('user_role', 'employee')
    user_id = st.session_state.get('user_id', '')
    user_type = st.session_state.get('user_type', 'employee')
    is_master = user_role == 'master' or user_type == 'master'
    
    # 직원 정보 가져오기 (작성자명 표시용)
    try:
        if user_id != 'master':
            employees_data = st.session_state.employee_manager.get_all_employees()
            user_name = "Unknown"
            if isinstance(employees_data, pd.DataFrame):
                user_info = employees_data[employees_data['employee_id'] == user_id]
                if len(user_info) > 0:
                    user_name = user_info.iloc[0]['name']
            elif isinstance(employees_data, list):
                for emp in employees_data:
                    if emp.get('employee_id') == user_id:
                        user_name = emp.get('name', 'Unknown')
                        break
        else:
            user_name = get_text("master")
    except:
        user_name = "Unknown"
    
    # 탭 생성
    if is_master:
        tab1, tab2, tab3, tab4 = st.tabs([
            f"📢 {get_text('master_notices')}", 
            f"💬 {get_text('employee_board')}", 
            f"✏️ {get_text('write_post')}",
            f"🗑️ {get_text('board_management')}"
        ])
    else:
        tab1, tab2, tab3 = st.tabs([
            f"📢 {get_text('notices')}", 
            f"💬 {get_text('employee_board')}", 
            f"✏️ {get_text('write_post')}"
        ])
        tab4 = None  # 일반 사용자는 관리 탭 없음
    
    with tab1:
        st.header(f"📢 {get_text('notice_board')}")
        
        # 공지사항 목록 가져오기
        notices_df = st.session_state.notice_manager.get_all_notices()
        
        # DataFrame을 딕셔너리 리스트로 변환
        if isinstance(notices_df, pd.DataFrame) and len(notices_df) > 0:
            notices = notices_df.to_dict('records')
        else:
            notices = []
        
        if len(notices) == 0:
            st.info(get_text('no_notices'))
        else:
            # 중요 공지사항 먼저 표시
            important_notices = [n for n in notices if n.get('is_important', False)]
            regular_notices = [n for n in notices if not n.get('is_important', False)]
            
            if len(important_notices) > 0:
                st.subheader(f"🚨 {get_text('important_notices')}")
                for notice in important_notices:
                    with st.expander(f"🚨 {notice['title']} - {notice['author_name']} ({notice['created_date'][:10]})"):
                        st.write(f"**{get_text('category')}:** {notice.get('category', get_text('general'))}")
                        st.write(f"**{get_text('target')}:** {notice.get('target_audience', get_text('all'))}")
                        st.write("---")
                        st.write(notice['content'])
                        if notice.get('updated_date') != notice.get('created_date'):
                            st.caption(f"{get_text('updated_date')}: {notice.get('updated_date', '')}")
            
            if len(regular_notices) > 0:
                st.subheader(f"📋 {get_text('general_notices')}")
                for notice in regular_notices:
                    with st.expander(f"{notice['title']} - {notice['author_name']} ({notice['created_date'][:10]})"):
                        st.write(f"**{get_text('category')}:** {notice.get('category', get_text('general'))}")
                        st.write(f"**{get_text('target')}:** {notice.get('target_audience', get_text('all'))}")
                        st.write("---")
                        st.write(notice['content'])
                        if notice.get('updated_date') != notice.get('created_date'):
                            st.caption(f"{get_text('updated_date')}: {notice.get('updated_date', '')}")
    
    with tab2:
        st.header(f"💬 {get_text('employee_posts')}")
        
        # 직원 게시글 목록 가져오기
        employee_posts_df = st.session_state.notice_manager.get_all_employee_posts()
        
        # DataFrame을 딕셔너리 리스트로 변환
        if isinstance(employee_posts_df, pd.DataFrame) and len(employee_posts_df) > 0:
            employee_posts = employee_posts_df.to_dict('records')
        else:
            employee_posts = []
        
        if len(employee_posts) == 0:
            st.info(get_text('no_posts'))
        else:
            # 카테고리별 필터
            categories = [get_text('all')] + st.session_state.notice_manager.get_employee_post_categories()
            selected_category = st.selectbox(get_text('category_filter'), categories)
            
            # 필터링된 게시글
            if selected_category == get_text('all'):
                filtered_posts = employee_posts
            else:
                filtered_posts = [p for p in employee_posts if p.get('category') == selected_category]
            
            # 접근 권한 확인 및 필터링
            visible_posts = []
            for post in filtered_posts:
                visible_to = post.get('visible_to', get_text('all'))
                if visible_to == get_text('all') or visible_to == '전체' or is_master or visible_to == user_id:
                    visible_posts.append(post)
            
            if len(visible_posts) == 0:
                st.info(get_text('no_visible_posts'))
            else:
                for post in visible_posts:
                    with st.expander(f"{post['title']} - {post['author_name']} ({post['created_date'][:10]})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{get_text('category')}:** {post.get('category', '자유게시판')}")
                            if post.get('visible_to', get_text('all')) != get_text('all') and post.get('visible_to', '전체') != '전체':
                                st.write(f"**{get_text('visibility_permission')}:** {post.get('visible_to')}")
                        with col2:
                            st.write(f"👍 {post.get('likes', 0)}")
                        
                        st.write("---")
                        st.write(post['content'])
                        
                        if post.get('updated_date') != post.get('created_date'):
                            st.caption(f"{get_text('updated_date')}: {post.get('updated_date', '')}")
                        
                        # 삭제 버튼 (작성자 또는 마스터만)
                        if post['author_id'] == user_id or is_master:
                            if st.button(f"🗑️ {get_text('delete')}", key=f"delete_post_{post['post_id']}"):
                                success = st.session_state.notice_manager.delete_employee_post(post['post_id'])
                                if success:
                                    st.success(get_text('post_deleted'))
                                    st.rerun()
                                else:
                                    st.error(get_text('post_delete_failed'))
    
    with tab3:
        st.header(f"✏️ {get_text('write_post')}")
        
        # 작성 타입 선택
        if is_master:
            post_type = st.radio(get_text('post_type'), [get_text('notice_board'), get_text('employee_posts')])
        else:
            post_type = get_text('employee_posts')
            st.info(get_text('employee_board_only'))
        
        if post_type == get_text('notice_board'):
            st.subheader(f"📢 {get_text('write_notice')}")
            
            col1, col2 = st.columns(2)
            with col1:
                notice_title = st.text_input(get_text('title'), placeholder=get_text('notice_title_placeholder'))
                notice_category = st.selectbox(get_text('category'), st.session_state.notice_manager.get_notice_categories())
                is_important = st.checkbox(get_text('important_notice'))
            
            with col2:
                target_audience = st.selectbox(get_text('target_audience'), st.session_state.notice_manager.get_target_audiences())
            
            notice_content = st.text_area(get_text('content'), placeholder=get_text('notice_content_placeholder'), height=200)
            
            if st.button(f"📢 {get_text('register_notice')}", type="primary"):
                if notice_title and notice_content:
                    success, notice_id = st.session_state.notice_manager.create_notice(
                        notice_title, notice_content, user_id, user_name,
                        is_important, notice_category, target_audience
                    )
                    if success:
                        st.success(f"{get_text('notice_registered')} (ID: {notice_id})")
                        st.rerun()
                    else:
                        st.error(get_text('notice_register_failed'))
                else:
                    st.warning(get_text('fill_required_fields'))
        
        else:  # 직원 게시판
            st.subheader(f"💬 {get_text('write_employee_post')}")
            
            col1, col2 = st.columns(2)
            with col1:
                post_title = st.text_input(get_text('title'), placeholder=get_text('post_title_placeholder'))
                post_category = st.selectbox(get_text('category'), st.session_state.notice_manager.get_employee_post_categories())
            
            with col2:
                # 특정 사용자만 볼 수 있는 게시글 옵션
                visibility_options = [get_text('all')]
                try:
                    employees_data = st.session_state.employee_manager.get_all_employees()
                    if isinstance(employees_data, pd.DataFrame):
                        for _, emp in employees_data.iterrows():
                            visibility_options.append(f"{emp['name']} ({emp['employee_id']})")
                    elif isinstance(employees_data, list):
                        for emp in employees_data:
                            visibility_options.append(f"{emp.get('name', 'N/A')} ({emp.get('employee_id', 'N/A')})")
                except:
                    pass
                
                visible_to = st.selectbox(get_text('visibility_permission'), visibility_options)
                if visible_to != get_text('all') and visible_to and "(" in visible_to:
                    visible_to = visible_to.split("(")[1].rstrip(")")  # employee_id 추출
            
            post_content = st.text_area(get_text('content'), placeholder=get_text('post_content_placeholder'), height=200)
            
            if st.button(f"💬 {get_text('register_post')}", type="primary"):
                if post_title and post_content:
                    post_data = {
                        'title': post_title,
                        'content': post_content,
                        'author_id': user_id,
                        'author_name': user_name,
                        'category': post_category,
                        'visible_to': visible_to or "all"
                    }
                    success, post_id = st.session_state.notice_manager.create_employee_post(post_data)
                    if success:
                        st.success(f"{get_text('post_registered')} (ID: {post_id})")
                        st.rerun()
                    else:
                        st.error(get_text('post_register_failed'))
                else:
                    st.warning(get_text('fill_required_fields'))
    
    # 마스터 전용 관리 탭
    if is_master and tab4:
        with tab4:
            st.header(f"🗑️ {get_text('board_admin')}")
            st.warning(f"⚠️ {get_text('master_only_feature')}")
            
            # 공지사항 관리
            st.subheader(f"📢 {get_text('notice_admin')}")
            notices = st.session_state.notice_manager.get_all_notices()
            
            if len(notices) > 0:
                for notice in notices:
                    with st.expander(f"공지: {notice['title']} ({notice['created_date'][:10]})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{get_text('author')}:** {notice['author_name']}")
                            st.write(f"**{get_text('category')}:** {notice.get('category', get_text('general'))}")
                            st.write(f"**{get_text('importance')}:** {'🚨 ' + get_text('important') if notice.get('is_important') else get_text('general')}")
                            st.write(f"**{get_text('target')}:** {notice.get('target_audience', get_text('all'))}")
                        
                        with col2:
                            if st.button(f"🗑️ {get_text('delete')}", key=f"delete_notice_{notice['notice_id']}"):
                                success = st.session_state.notice_manager.delete_notice(notice['notice_id'])
                                if success:
                                    st.success(get_text('notice_deleted'))
                                    st.rerun()
                                else:
                                    st.error(get_text('notice_delete_failed'))
            
            st.divider()
            
            # 직원 게시글 관리
            st.subheader(f"💬 {get_text('employee_post_admin')}")
            employee_posts = st.session_state.notice_manager.get_all_employee_posts()
            
            # DataFrame을 딕셔너리 리스트로 변환
            if isinstance(employee_posts, pd.DataFrame) and len(employee_posts) > 0:
                employee_posts_list = employee_posts.to_dict('records')
                for post in employee_posts_list:
                    with st.expander(f"게시글: {post['title']} ({post['created_date'][:10]})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{get_text('author')}:** {post['author_name']}")
                            st.write(f"**{get_text('category')}:** {post.get('category', '자유게시판')}")
                            st.write(f"**{get_text('visibility_permission')}:** {post.get('visible_to', get_text('all'))}")
                            st.write(f"**{get_text('likes')}:** {post.get('likes', 0)}")
                        
                        with col2:
                            if st.button(f"🗑️ {get_text('delete')}", key=f"delete_emp_post_{post['post_id']}"):
                                success = st.session_state.notice_manager.delete_employee_post(post['post_id'])
                                if success:
                                    st.success(get_text('post_deleted'))
                                    st.rerun()
                                else:
                                    st.error(get_text('post_delete_failed'))
            elif isinstance(employee_posts, list) and len(employee_posts) > 0:
                for post in employee_posts:
                    if isinstance(post, dict):
                        with st.expander(f"게시글: {post['title']} ({post['created_date'][:10]})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{get_text('author')}:** {post['author_name']}")
                                st.write(f"**{get_text('category')}:** {post.get('category', '자유게시판')}")
                                st.write(f"**{get_text('visibility_permission')}:** {post.get('visible_to', get_text('all'))}")
                                st.write(f"**{get_text('likes')}:** {post.get('likes', 0)}")
                            
                            with col2:
                                if st.button(f"🗑️ {get_text('delete')}", key=f"delete_emp_post_{post['post_id']}"):
                                    success = st.session_state.notice_manager.delete_employee_post(post['post_id'])
                                    if success:
                                        st.success(get_text('post_deleted'))
                                        st.rerun()
                                    else:
                                        st.error(get_text('post_delete_failed'))
            else:
                st.info(f"{get_text('no_posts')}")
            
            st.divider()
            
            # 일괄 정리 기능
            st.subheader(f"🧹 {get_text('batch_cleanup')}")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"🗑️ {get_text('delete_all_notices')}", type="secondary"):
                    if st.button(get_text('confirm_delete'), key="confirm_delete_notices"):
                        # 모든 공지사항 삭제 (구현 필요)
                        st.warning(get_text('feature_pending'))
            
            with col2:
                if st.button(f"🗑️ {get_text('delete_all_posts')}", type="secondary"):
                    if st.button(get_text('confirm_delete'), key="confirm_delete_posts"):
                        # 모든 직원 게시글 삭제 (구현 필요)
                        st.warning(get_text('feature_pending'))

def show_work_status_in_notice(current_user_id, current_user_name, is_master, get_text):
    """게시판 내 업무 진행 상태 표시"""
    st.header(f"📋 {get_text('work_progress_status')}")
    
    # 업무 상태 관리자 초기화
    if 'work_status_manager' not in st.session_state:
        from work_status_manager import WorkStatusManager
        st.session_state.work_status_manager = WorkStatusManager()
    
    # 탭 생성
    work_tab1, work_tab2 = st.tabs([f"📊 {get_text('work_status')}", f"➕ {get_text('new_work_registration')}"])
    
    with work_tab1:
        st.subheader(f"📊 {get_text('current_ongoing_work')}")
        
        # 업무 목록 조회
        try:
            work_status_list = st.session_state.work_status_manager.get_all_work_status()
        except Exception as e:
            st.error(f"{get_text('work_status_inquiry_error')}: {e}")
            work_status_list = []
        
        if len(work_status_list) == 0:
            st.info(get_text('no_registered_work'))
        else:
            # 상태별 필터
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.selectbox(get_text('status_filter'), [
                    get_text('work_status_all'), 
                    get_text('work_status_planning'), 
                    get_text('work_status_inprogress'), 
                    get_text('work_status_waiting'), 
                    get_text('work_status_completed'), 
                    get_text('work_status_onhold')
                ])
            with col2:
                filter_priority = st.selectbox(get_text('priority_filter'), [
                    get_text('priority_all'), 
                    get_text('priority_low'), 
                    get_text('priority_normal'), 
                    get_text('priority_high'), 
                    get_text('priority_urgent')
                ])
            with col3:
                search_keyword = st.text_input(get_text('title_search'), placeholder=get_text('work_title_search_placeholder'))
            
            # 필터링
            filtered_works = work_status_list
            if filter_status != get_text('work_status_all'):
                # 번역된 상태값을 원본 상태값으로 매핑
                status_mapping = {
                    get_text('work_status_planning'): '계획중',
                    get_text('work_status_inprogress'): '진행중',
                    get_text('work_status_waiting'): '대기',
                    get_text('work_status_completed'): '완료',
                    get_text('work_status_onhold'): '보류'
                }
                original_status = status_mapping.get(filter_status, filter_status)
                filtered_works = [w for w in filtered_works if w.get('status') == original_status]
                
            if filter_priority != get_text('priority_all'):
                # 번역된 우선순위값을 원본 우선순위값으로 매핑
                priority_mapping = {
                    get_text('priority_low'): '낮음',
                    get_text('priority_normal'): '보통',
                    get_text('priority_high'): '높음',
                    get_text('priority_urgent'): '긴급'
                }
                original_priority = priority_mapping.get(filter_priority, filter_priority)
                filtered_works = [w for w in filtered_works if w.get('priority') == original_priority]
                
            if search_keyword:
                filtered_works = [w for w in filtered_works if search_keyword.lower() in w.get('title', '').lower()]
            
            # 업무 목록 표시
            for work in filtered_works:
                with st.expander(f"{work.get('title', get_text('no_title'))} - {work.get('status', get_text('no_status'))}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{get_text('description')}:** {work.get('description', get_text('no_description'))}")
                        st.write(f"**{get_text('assignee')}:** {work.get('assigned_to', get_text('unassigned'))}")
                        st.write(f"**{get_text('priority')}:** {work.get('priority', get_text('priority_normal'))}")
                        st.write(f"**{get_text('progress_rate')}:** {work.get('progress', 0)}%")
                        
                        # 진행률 바
                        progress = work.get('progress', 0)
                        st.progress(progress / 100)
                        
                        if work.get('due_date'):
                            st.write(f"**{get_text('due_date')}:** {work.get('due_date')}")
                        
                        # 댓글 표시
                        comments = work.get('comments', [])
                        if comments:
                            st.write(f"**{get_text('comments')}:**")
                            for comment in comments:
                                if isinstance(comment, dict):
                                    st.caption(f"• {comment.get('content', '')} - {comment.get('author', '')} ({comment.get('created_date', '')})")
                                else:
                                    st.caption(f"• {str(comment)}")
                    
                    with col2:
                        # 상태 변경 (작성자 또는 마스터만)
                        if is_master or work.get('created_by') == current_user_id:
                            if st.button(f"✏️ {get_text('change_status')}", key=f"edit_work_notice_{work.get('status_id')}"):
                                st.session_state.edit_work_status_notice = work.get('status_id')
                                st.rerun()
                        
                        # 댓글 추가
                        if st.button("💬 댓글", key=f"comment_work_notice_{work.get('status_id')}"):
                            st.session_state.comment_work_status_notice = work.get('status_id')
                            st.rerun()
                        
                        # 삭제 (작성자 또는 마스터만)
                        if is_master or work.get('created_by') == current_user_id:
                            if st.button("🗑️ 삭제", key=f"delete_work_notice_{work.get('status_id')}"):
                                try:
                                    success, message = st.session_state.work_status_manager.delete_work_status(work.get('status_id'))
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"삭제 오류: {e}")
    
    with work_tab2:
        st.subheader("➕ 새 업무 등록")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("업무 제목", placeholder="업무 제목을 입력하세요", key="notice_work_title")
            category = st.selectbox("카테고리", ["프로젝트", "일반 업무", "문서 작업", "고객 응대", "기타"], key="notice_work_category")
            priority = st.selectbox("우선순위", ["낮음", "보통", "높음", "긴급"], key="notice_work_priority")
        
        with col2:
            assigned_to = st.text_input("담당자", placeholder="담당자명을 입력하세요", key="notice_work_assigned")
            status = st.selectbox("상태", ["계획중", "진행중", "대기", "완료", "보류"], key="notice_work_status")
            due_date = st.date_input("마감일", value=None, key="notice_work_due")
        
        description = st.text_area("업무 설명", placeholder="업무 내용을 자세히 설명해주세요", height=100, key="notice_work_desc")
        tags = st.text_input("태그", placeholder="태그를 쉼표로 구분해서 입력 (예: 중요,긴급,프로젝트A)", key="notice_work_tags")
        
        if st.button("📋 업무 등록", type="primary", key="notice_work_submit"):
            if title and description:
                try:
                    # 마감일 처리
                    due_date_str = due_date.strftime('%Y-%m-%d') if due_date else ''
                    
                    success, message = st.session_state.work_status_manager.create_work_status(
                        title=title,
                        description=description,
                        status=status,
                        priority=priority,
                        assigned_to=assigned_to,
                        created_by=current_user_id,
                        due_date=due_date_str,
                        category=category,
                        tags=tags
                    )
                    
                    if success:
                        st.success(message)
                        
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"업무 등록 오류: {e}")
            else:
                st.warning("제목과 설명을 모두 입력해주세요.")
    
    # 상태 변경 폼 (게시판 내)
    if st.session_state.get('edit_work_status_notice'):
        status_id = st.session_state.edit_work_status_notice
        st.subheader("📝 업무 상태 변경")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_status = st.selectbox("새 상태", ["계획중", "진행중", "대기", "완료", "보류"], key="new_status_edit_notice")
            new_progress = st.slider("진행률 (%)", 0, 100, 0, key="new_progress_edit_notice")
        
        with col2:
            if st.button("✅ 저장", key="save_work_status_notice"):
                try:
                    updates = {
                        'status': new_status,
                        'progress': new_progress
                    }
                    success, message = st.session_state.work_status_manager.update_work_status(status_id, **updates)
                    if success:
                        st.success(message)
                        st.session_state.edit_work_status_notice = None
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"상태 변경 오류: {e}")
            
            if st.button("❌ 취소", key="cancel_work_status_notice"):
                st.session_state.edit_work_status_notice = None
                st.rerun()
    
    # 댓글 추가 폼 (게시판 내)
    if st.session_state.get('comment_work_status_notice'):
        status_id = st.session_state.comment_work_status_notice
        st.subheader("💬 댓글 추가")
        
        comment = st.text_area("댓글 내용", placeholder="댓글을 입력하세요", key="new_comment_notice")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 추가", key="add_comment_notice"):
                if comment:
                    try:
                        success, message = st.session_state.work_status_manager.add_comment(status_id, comment, current_user_id)
                        if success:
                            st.success(message)
                            st.session_state.comment_work_status_notice = None
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"댓글 추가 오류: {e}")
                else:
                    st.error("댓글 내용을 입력해주세요.")
        
        with col2:
            if st.button("❌ 취소", key="cancel_comment_notice"):
                st.session_state.comment_work_status_notice = None
                st.rerun()