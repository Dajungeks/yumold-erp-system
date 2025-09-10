"""
업무 보고 게시판 페이지 - 직원별 업무 보고서 관리
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

def show_work_report_page(get_text):
    """업무 보고 게시판 페이지 표시"""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'work_reports', get_text)
    
    st.title(f"📝 {get_text('work_reports')}")
    
    # 게시판 관리자 초기화 (기존 notice_manager 재사용)
    if 'notice_manager' not in st.session_state:
        from managers.sqlite.sqlite_notice_manager import SQLiteNoticeManager
        st.session_state.notice_manager = SQLiteNoticeManager()
    
    # 현재 사용자 정보
    user_role = st.session_state.get('user_role', 'employee')
    user_id = st.session_state.get('user_id', '')
    user_type = st.session_state.get('user_type', 'employee')
    access_level = st.session_state.get('access_level', 'user')
    is_admin = user_role == 'master' or user_type == 'master' or access_level in ['ceo', 'admin', 'master']
    
    # 직원 정보 가져오기
    try:
        if user_id != 'master':
            employees_data = st.session_state.employee_manager.get_all_employees()
            user_name = "Unknown"
            user_department = "Unknown"
            user_position = "Unknown"
            
            if isinstance(employees_data, pd.DataFrame):
                user_info = employees_data[employees_data['employee_id'] == user_id]
                if len(user_info) > 0:
                    user_name = user_info.iloc[0]['name']
                    user_department = user_info.iloc[0].get('department', 'Unknown')
                    user_position = user_info.iloc[0].get('position', 'Unknown')
        else:
            user_name = "법인장"
            user_department = "경영진"
            user_position = "CEO"
    except Exception as e:
        user_name = "Unknown"
        user_department = "Unknown"
        user_position = "Unknown"
    
    # 탭 생성
    if is_admin:
        tab1, tab2, tab3 = st.tabs([
            f"📋 {get_text('my_reports')}", 
            f"✏️ {get_text('write_report')}",
            f"👥 {get_text('report_management')}"
        ])
    else:
        tab1, tab2 = st.tabs([
            f"📋 {get_text('my_reports')}", 
            f"✏️ {get_text('write_report')}"
        ])
        tab3 = None
    
    # 탭 1: 내 보고서 (작성자만 본인 글 조회 가능)
    with tab1:
        st.header(f"📋 {get_text('my_reports')}")
        
        # 내가 작성한 보고서만 조회
        try:
            all_reports = st.session_state.notice_manager.get_all_notices()
            if isinstance(all_reports, pd.DataFrame) and len(all_reports) > 0:
                # work_report 카테고리이면서 본인이 작성한 것만 필터링
                my_reports = all_reports[
                    (all_reports['category'] == 'work_report') & 
                    (all_reports['author_id'] == user_id)
                ]
                
                if len(my_reports) > 0:
                    # 최신순으로 정렬
                    my_reports = my_reports.sort_values('created_date', ascending=False)
                    
                    st.write(f"**{get_text('total_reports')}: {len(my_reports)}개**")
                    
                    for idx, report in my_reports.iterrows():
                        with st.expander(f"📄 {report['title']} ({report['created_date'][:10]})"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**작성일:** {report['created_date'][:10]}")
                                st.write(f"**부서:** {user_department}")
                                st.write(f"**직급:** {user_position}")
                                
                            with col2:
                                st.write(f"**조회수:** {report.get('view_count', 0)}")
                                st.write(f"**상태:** {'활성' if report['status'] == 'active' else '비활성'}")
                            
                            st.write("**보고 내용:**")
                            st.write(report['content'])
                            
                            # 태그가 있으면 표시
                            if report.get('tags') and report['tags'].strip():
                                st.write(f"**태그:** {report['tags']}")
                            
                            # 수정 모드 확인
                            if st.session_state.get(f'edit_report_{report["notice_id"]}', False):
                                st.write("---")
                                st.subheader(f"✏️ {get_text('edit_report')}")
                                
                                # 수정 폼
                                with st.form(f"edit_report_form_{report['notice_id']}"):
                                    # 보고서 제목
                                    edit_title = st.text_input(
                                        get_text('report_title_input'),
                                        value=report['title'],
                                        placeholder=get_text('report_title_placeholder')
                                    )
                                    
                                    # 보고서 내용
                                    edit_content = st.text_area(
                                        get_text('report_content_input'),
                                        value=report['content'],
                                        height=300
                                    )
                                    
                                    # 태그
                                    edit_tags = st.text_input(
                                        get_text('tags_optional'),
                                        value=report.get('tags', ''),
                                        placeholder=get_text('tags_placeholder')
                                    )
                                    
                                    # 우선순위
                                    priority_options = {
                                        'normal': get_text('priority_normal'), 
                                        'high': get_text('priority_high'), 
                                        'urgent': get_text('priority_urgent')
                                    }
                                    current_priority = report.get('priority', 'normal')
                                    current_priority_index = ['normal', 'high', 'urgent'].index(current_priority) if current_priority in ['normal', 'high', 'urgent'] else 0
                                    
                                    edit_priority = st.selectbox(
                                        get_text('priority_label'),
                                        options=['normal', 'high', 'urgent'],
                                        index=current_priority_index,
                                        format_func=lambda x: priority_options[x]
                                    )
                                    
                                    # 수정/취소 버튼
                                    col_update, col_cancel = st.columns(2)
                                    with col_update:
                                        update_submitted = st.form_submit_button(get_text('update_button'), use_container_width=True)
                                    with col_cancel:
                                        cancel_submitted = st.form_submit_button(get_text('cancel_button'), use_container_width=True)
                                    
                                    if update_submitted:
                                        if edit_title.strip() and edit_content.strip():
                                            try:
                                                # 수정된 데이터 준비
                                                updated_data = {
                                                    'id': report['notice_id'],
                                                    'title': edit_title.strip(),
                                                    'content': edit_content.strip(),
                                                    'tags': edit_tags.strip() if edit_tags.strip() else None,
                                                    'priority': edit_priority
                                                }
                                                
                                                # 보고서 업데이트
                                                success = st.session_state.notice_manager.update_notice(report['notice_id'], updated_data)
                                                
                                                if success:
                                                    st.success(get_text('edit_success'))
                                                    st.session_state[f'edit_report_{report["notice_id"]}'] = False
                                                    st.rerun()
                                                else:
                                                    st.error(get_text('edit_error'))
                                            except Exception as e:
                                                st.error(f"{get_text('edit_error')}: {str(e)}")
                                        else:
                                            st.error(get_text('report_error_missing_fields'))
                                    
                                    if cancel_submitted:
                                        st.session_state[f'edit_report_{report["notice_id"]}'] = False
                                        st.rerun()
                            
                            # 수정/삭제 버튼 (본인 보고서이므로 항상 표시)
                            st.write("---")
                            col_edit, col_delete = st.columns(2)
                            
                            with col_edit:
                                if st.button(get_text('edit_button'), key=f"edit_my_{report['notice_id']}", use_container_width=True):
                                    st.session_state[f'edit_report_{report["notice_id"]}'] = True
                                    st.rerun()
                            
                            with col_delete:
                                if st.button(get_text('delete_button'), key=f"delete_my_{report['notice_id']}", use_container_width=True):
                                    # 삭제 확인
                                    if st.session_state.get(f'confirm_delete_{report["notice_id"]}', False):
                                        try:
                                            success = st.session_state.notice_manager.delete_notice(report['notice_id'])
                                            if success:
                                                st.success(get_text('delete_success'))
                                                st.session_state[f'confirm_delete_{report["notice_id"]}'] = False
                                                st.rerun()
                                            else:
                                                st.error(get_text('delete_error'))
                                        except Exception as e:
                                            st.error(f"{get_text('delete_error')}: {str(e)}")
                                    else:
                                        st.session_state[f'confirm_delete_{report["notice_id"]}'] = True
                                        st.rerun()
                            
                            # 삭제 확인 상태일 때 확인 메시지 표시
                            if st.session_state.get(f'confirm_delete_{report["notice_id"]}', False):
                                st.warning(get_text('confirm_delete'))
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ 예", key=f"yes_{report['notice_id']}", use_container_width=True):
                                        try:
                                            success = st.session_state.notice_manager.delete_notice(report['notice_id'])
                                            if success:
                                                st.success(get_text('delete_success'))
                                                st.session_state[f'confirm_delete_{report["notice_id"]}'] = False
                                                st.rerun()
                                            else:
                                                st.error(get_text('delete_error'))
                                        except Exception as e:
                                            st.error(f"{get_text('delete_error')}: {str(e)}")
                                
                                with col_no:
                                    if st.button("❌ 아니오", key=f"no_{report['notice_id']}", use_container_width=True):
                                        st.session_state[f'confirm_delete_{report["notice_id"]}'] = False
                                        st.rerun()
                else:
                    st.info("📝 작성된 보고서가 없습니다. '보고서 작성' 탭에서 새로운 보고서를 작성해주세요.")
            else:
                st.info("📝 작성된 보고서가 없습니다. '보고서 작성' 탭에서 새로운 보고서를 작성해주세요.")
                
        except Exception as e:
            st.error(f"보고서 조회 중 오류가 발생했습니다: {str(e)}")
    
    # 탭 2: 보고서 작성
    with tab2:
        st.header(f"✏️ {get_text('write_report')}")
        
        with st.form("work_report_form"):
            st.subheader(get_text('work_report_title'))
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**{get_text('author_label')}:** {user_name}")
                st.write(f"**{get_text('department_label')}:** {user_department}")
            with col2:
                st.write(f"**{get_text('position_label')}:** {user_position}")
                report_date = st.date_input(get_text('report_date_label'), value=date.today())
            
            # 보고서 제목
            title = st.text_input(get_text('report_title_input'), placeholder=get_text('report_title_placeholder'))
            
            # 보고서 내용
            content = st.text_area(
                get_text('report_content_input'), 
                height=300,
                placeholder="""예시:
1. 금일 수행 업무
   - 고객 A사 견적서 작성 및 발송
   - 프로젝트 B 진행 상황 점검

2. 주요 성과
   - 신규 견적 3건 완료
   - 고객 미팅 2회 진행

3. 이슈 및 건의사항
   - 자재 납기 지연 문제
   - 추가 인력 필요

4. 향후 계획
   - 내일 고객사 방문 예정
   - 주간 보고서 준비"""
            )
            
            # 태그 (선택사항)
            tags = st.text_input(get_text('tags_optional'), placeholder=get_text('tags_placeholder'))
            
            # 우선순위
            priority_options = {
                'normal': get_text('priority_normal'), 
                'high': get_text('priority_high'), 
                'urgent': get_text('priority_urgent')
            }
            priority = st.selectbox(
                get_text('priority_label'),
                options=['normal', 'high', 'urgent'],
                format_func=lambda x: priority_options[x]
            )
            
            submitted = st.form_submit_button(get_text('save_report_button'))
            
            if submitted:
                if title.strip() and content.strip():
                    try:
                        # 보고서 ID 생성 (날짜 + 순번)
                        today_str = datetime.now().strftime("%Y%m%d")
                        existing_reports = st.session_state.notice_manager.get_all_notices()
                        
                        if isinstance(existing_reports, pd.DataFrame) and len(existing_reports) > 0:
                            today_reports = existing_reports[
                                existing_reports['notice_id'].str.startswith(f"WR-{today_str}")
                            ]
                            next_num = len(today_reports) + 1
                        else:
                            next_num = 1
                        
                        report_id = f"WR-{today_str}-{next_num:03d}"
                        
                        # 보고서 데이터 준비
                        report_data = {
                            'notice_id': report_id,
                            'title': title.strip(),
                            'content': content.strip(),
                            'category': 'work_report',
                            'priority': priority,
                            'status': 'active',
                            'target_audience': 'admin',  # 관리자만 조회 가능
                            'department': user_department,
                            'author_id': user_id,
                            'author_name': user_name,
                            'publish_date': report_date.strftime("%Y-%m-%d"),
                            'tags': tags.strip() if tags.strip() else '',
                            'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'updated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # 보고서 저장
                        success = st.session_state.notice_manager.add_notice(report_data)
                        
                        if success:
                            st.success(f"✅ {get_text('report_saved_success')} (ID: {report_id})")
                            st.rerun()
                        else:
                            st.error(get_text('report_save_error'))
                            
                    except Exception as e:
                        st.error(f"{get_text('report_save_error')}: {str(e)}")
                else:
                    st.error(get_text('report_error_missing_fields'))
    
    # 탭 3: 전체 보고서 관리 (관리자만)
    if tab3 is not None and is_admin:
        with tab3:
            st.header(f"👥 {get_text('report_management')}")
            
            try:
                all_reports = st.session_state.notice_manager.get_all_notices()
                if isinstance(all_reports, pd.DataFrame) and len(all_reports) > 0:
                    # work_report 카테고리만 필터링
                    work_reports = all_reports[all_reports['category'] == 'work_report']
                    
                    if len(work_reports) > 0:
                        st.write(f"**{get_text('total_reports_count')}: {len(work_reports)}개**")
                        
                        # 필터링 옵션
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            filter_department = st.selectbox(
                                get_text('department_filter'),
                                options=[get_text('all_option')] + list(work_reports['department'].dropna().unique())
                            )
                        
                        with col2:
                            filter_author = st.selectbox(
                                get_text('author_filter'), 
                                options=[get_text('all_option')] + list(work_reports['author_name'].dropna().unique())
                            )
                        
                        with col3:
                            filter_date = st.date_input(
                                get_text('date_filter'),
                                value=None
                            )
                        
                        # 필터 적용
                        filtered_reports = work_reports.copy()
                        
                        if filter_department != get_text('all_option'):
                            filtered_reports = filtered_reports[
                                filtered_reports['department'] == filter_department
                            ]
                        
                        if filter_author != get_text('all_option'):
                            filtered_reports = filtered_reports[
                                filtered_reports['author_name'] == filter_author
                            ]
                        
                        if filter_date:
                            date_str = filter_date.strftime("%Y-%m-%d")
                            filtered_reports = filtered_reports[
                                filtered_reports['publish_date'] == date_str
                            ]
                        
                        # 보고서 목록 표시
                        if len(filtered_reports) > 0:
                            filtered_reports = filtered_reports.sort_values('created_date', ascending=False)
                            
                            st.write(f"**{get_text('filter_results')}: {len(filtered_reports)}개**")
                            
                            for idx, report in filtered_reports.iterrows():
                                priority_emoji = {'normal': '📄', 'high': '🔥', 'urgent': '🚨'}
                                emoji = priority_emoji.get(report.get('priority', 'normal'), '📄')
                                
                                with st.expander(f"{emoji} {report['title']} - {report['author_name']} ({report['publish_date']})"):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.write(f"**작성자:** {report['author_name']}")
                                        st.write(f"**부서:** {report.get('department', 'N/A')}")
                                        st.write(f"**작성일:** {report['created_date'][:10]}")
                                        
                                    with col2:
                                        priority_map = {'normal': '일반', 'high': '높음', 'urgent': '긴급'}
                                        priority_text = priority_map.get(report.get('priority', 'normal'), '일반')
                                        st.write(f"**우선순위:** {priority_text}")
                                        st.write(f"**조회수:** {report.get('view_count', 0)}")
                                    
                                    st.write("**보고 내용:**")
                                    st.write(report['content'])
                                    
                                    if report.get('tags') and report['tags'].strip():
                                        st.write(f"**태그:** {report['tags']}")
                                    
                                    # 수정 모드 확인 (관리자 탭)
                                    if st.session_state.get(f'edit_report_{report["notice_id"]}', False):
                                        st.write("---")
                                        st.subheader(f"✏️ {get_text('edit_report')}")
                                        
                                        # 수정 폼 (관리자 탭)
                                        with st.form(f"edit_admin_report_form_{report['notice_id']}"):
                                            # 보고서 제목
                                            edit_title_admin = st.text_input(
                                                get_text('report_title_input'),
                                                value=report['title'],
                                                placeholder=get_text('report_title_placeholder')
                                            )
                                            
                                            # 보고서 내용
                                            edit_content_admin = st.text_area(
                                                get_text('report_content_input'),
                                                value=report['content'],
                                                height=300
                                            )
                                            
                                            # 태그
                                            edit_tags_admin = st.text_input(
                                                get_text('tags_optional'),
                                                value=report.get('tags', ''),
                                                placeholder=get_text('tags_placeholder')
                                            )
                                            
                                            # 우선순위
                                            priority_options_admin = {
                                                'normal': get_text('priority_normal'), 
                                                'high': get_text('priority_high'), 
                                                'urgent': get_text('priority_urgent')
                                            }
                                            current_priority_admin = report.get('priority', 'normal')
                                            current_priority_index_admin = ['normal', 'high', 'urgent'].index(current_priority_admin) if current_priority_admin in ['normal', 'high', 'urgent'] else 0
                                            
                                            edit_priority_admin = st.selectbox(
                                                get_text('priority_label'),
                                                options=['normal', 'high', 'urgent'],
                                                index=current_priority_index_admin,
                                                format_func=lambda x: priority_options_admin[x]
                                            )
                                            
                                            # 수정/취소 버튼
                                            col_update_admin, col_cancel_admin = st.columns(2)
                                            with col_update_admin:
                                                update_submitted_admin = st.form_submit_button(get_text('update_button'), use_container_width=True)
                                            with col_cancel_admin:
                                                cancel_submitted_admin = st.form_submit_button(get_text('cancel_button'), use_container_width=True)
                                            
                                            if update_submitted_admin:
                                                if edit_title_admin.strip() and edit_content_admin.strip():
                                                    try:
                                                        # 수정된 데이터 준비
                                                        updated_data_admin = {
                                                            'id': report['notice_id'],
                                                            'title': edit_title_admin.strip(),
                                                            'content': edit_content_admin.strip(),
                                                            'tags': edit_tags_admin.strip() if edit_tags_admin.strip() else None,
                                                            'priority': edit_priority_admin
                                                        }
                                                        
                                                        # 보고서 업데이트
                                                        success = st.session_state.notice_manager.update_notice(report['notice_id'], updated_data_admin)
                                                        
                                                        if success:
                                                            st.success(get_text('edit_success'))
                                                            st.session_state[f'edit_report_{report["notice_id"]}'] = False
                                                            st.rerun()
                                                        else:
                                                            st.error(get_text('edit_error'))
                                                    except Exception as e:
                                                        st.error(f"{get_text('edit_error')}: {str(e)}")
                                                else:
                                                    st.error(get_text('report_error_missing_fields'))
                                            
                                            if cancel_submitted_admin:
                                                st.session_state[f'edit_report_{report["notice_id"]}'] = False
                                                st.rerun()
                                    
                                    # 수정/삭제 버튼 (관리자는 모든 보고서, 일반 사용자는 본인 것만)
                                    can_edit = is_admin or (report['author_id'] == user_id)
                                    
                                    if can_edit:
                                        st.write("---")
                                        col_edit_admin, col_delete_admin = st.columns(2)
                                        
                                        with col_edit_admin:
                                            if st.button(get_text('edit_button'), key=f"edit_admin_{report['notice_id']}", use_container_width=True):
                                                st.session_state[f'edit_report_{report["notice_id"]}'] = True
                                                st.rerun()
                                        
                                        with col_delete_admin:
                                            if st.button(get_text('delete_button'), key=f"delete_admin_{report['notice_id']}", use_container_width=True):
                                                st.session_state[f'confirm_delete_admin_{report["notice_id"]}'] = True
                                                st.rerun()
                                        
                                        # 삭제 확인 상태일 때 확인 메시지 표시
                                        if st.session_state.get(f'confirm_delete_admin_{report["notice_id"]}', False):
                                            st.warning(get_text('confirm_delete'))
                                            col_yes_admin, col_no_admin = st.columns(2)
                                            with col_yes_admin:
                                                if st.button("✅ 예", key=f"yes_admin_{report['notice_id']}", use_container_width=True):
                                                    try:
                                                        success = st.session_state.notice_manager.delete_notice(report['notice_id'])
                                                        if success:
                                                            st.success(get_text('delete_success'))
                                                            st.session_state[f'confirm_delete_admin_{report["notice_id"]}'] = False
                                                            st.rerun()
                                                        else:
                                                            st.error(get_text('delete_error'))
                                                    except Exception as e:
                                                        st.error(f"{get_text('delete_error')}: {str(e)}")
                                            
                                            with col_no_admin:
                                                if st.button("❌ 아니오", key=f"no_admin_{report['notice_id']}", use_container_width=True):
                                                    st.session_state[f'confirm_delete_admin_{report["notice_id"]}'] = False
                                                    st.rerun()
                        else:
                            st.info("필터 조건에 맞는 보고서가 없습니다.")
                    else:
                        st.info("작성된 업무 보고서가 없습니다.")
                else:
                    st.info("작성된 업무 보고서가 없습니다.")
                    
            except Exception as e:
                st.error(f"보고서 목록 조회 중 오류가 발생했습니다: {str(e)}")
