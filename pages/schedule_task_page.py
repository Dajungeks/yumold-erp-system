"""
총무 일정 관리 페이지
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta
from schedule_task_manager import ScheduleTaskManager
from employee_manager import EmployeeManager

def show_schedule_task_page(get_text):
    """총무 일정 관리 메인 페이지"""
    st.title(f"📅 {get_text('schedule_task_management')}")
    st.markdown(get_text('schedule_task_main_page'))
    
    # 관리자 객체 생성
    task_manager = ScheduleTaskManager()
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        f"📊 {get_text('dashboard')}",
        f"📝 {get_text('registration')}", 
        f"📋 {get_text('management')}",
        f"🔔 {get_text('notifications')}",
        f"📈 {get_text('statistics')}",
        f"⚙️ {get_text('categories')}"
    ])
    
    with tab1:
        show_dashboard(task_manager, get_text)
    
    with tab2:
        show_task_registration(task_manager, get_text)
    
    with tab3:
        show_task_management(task_manager, get_text)
    
    with tab4:
        show_notifications(task_manager, get_text)
    
    with tab5:
        show_statistics(task_manager, get_text)
    
    with tab6:
        show_category_management(task_manager, get_text)

def show_dashboard(task_manager, get_text):
    """대시보드 표시"""
    st.header(f"📊 {get_text('dashboard')}")
    
    # 통계 가져오기
    stats = task_manager.get_task_statistics()
    
    if not stats:
        st.info(get_text('no_tasks_message'))
        return
    
    # 주요 지표
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(get_text('total_tasks'), f"{stats.get('total_tasks', 0)}건")
    
    with col2:
        overdue_count = stats.get('overdue_tasks', 0)
        st.metric(get_text('overdue_tasks'), f"{overdue_count}건", delta=f"-{overdue_count}" if overdue_count > 0 else None)
    
    with col3:
        upcoming_count = stats.get('upcoming_tasks', 0)
        st.metric(get_text('upcoming_tasks'), f"{upcoming_count}건")
    
    with col4:
        completion_rate = 0
        if stats.get('total_tasks', 0) > 0:
            completion_rate = (stats.get('completed_tasks', 0) / stats.get('total_tasks', 0)) * 100
        st.metric(get_text('schedule_task.dashboard.completion_rate'), f"{completion_rate:.1f}%")
    
    st.markdown("---")
    
    # 연체된 작업 알림
    overdue_tasks = task_manager.get_overdue_tasks()
    if len(overdue_tasks) > 0:
        st.error(f"🚨 **{get_text('schedule_task.dashboard.overdue_alert')}**: {len(overdue_tasks)}건")
        
        with st.expander(get_text('schedule_task.dashboard.view_overdue')):
            for _, task in overdue_tasks.head(5).iterrows():
                days_overdue = (datetime.now().date() - pd.to_datetime(task['due_date']).date()).days
                overdue_text = get_text('schedule_task.notifications.overdue_days').format(days=days_overdue)
                st.write(f"- **{task['task_title']}** ({overdue_text}) - {get_text('schedule_task.management.assignee')}: {task['assigned_person']}")
    
    # 임박한 작업
    upcoming_tasks = task_manager.get_upcoming_tasks(7)  # 7일 내
    if len(upcoming_tasks) > 0:
        st.warning(f"⚠️ **{get_text('schedule_task.dashboard.upcoming_alert')}**: {len(upcoming_tasks)}건")
        
        with st.expander(get_text('schedule_task.dashboard.view_upcoming')):
            for _, task in upcoming_tasks.iterrows():
                due_date = pd.to_datetime(task['due_date']).date()
                days_left = (due_date - datetime.now().date()).days
                days_left_text = get_text('schedule_task.notifications.days_left').format(days=days_left)
                st.write(f"- **{task['task_title']}** ({days_left_text}) - {get_text('schedule_task.management.assignee')}: {task['assigned_person']}")
    
    # 카테고리별 현황 차트
    if stats.get('by_category'):
        st.subheader(f"📊 {get_text('schedule_task.dashboard.category_status')}")
        
        categories_df = task_manager.get_categories()
        category_dict = dict(zip(categories_df['category_id'], categories_df['category_name']))
        
        chart_data = []
        for cat_id, count in stats['by_category'].items():
            chart_data.append({
                'category': category_dict.get(cat_id, cat_id),
                'count': count
            })
        
        chart_df = pd.DataFrame(chart_data)
        fig = px.bar(chart_df, x='category', y='count', title=get_text('schedule_task.dashboard.category_chart_title'))
        st.plotly_chart(fig, use_container_width=True)

def show_task_registration(task_manager, get_text):
    """일정 등록 폼"""
    st.header(f"📝 {get_text('schedule_task.registration.title')}")
    
    # 카테고리 목록 가져오기
    categories_df = task_manager.get_categories()
    category_options = dict(zip(categories_df['category_id'], categories_df['category_name']))
    
    # 직원 목록 가져오기
    employee_manager = EmployeeManager()
    try:
        employees_df = employee_manager.get_all_employees()
        employee_names = [get_text('schedule_task.registration.direct_input')]  # 기본 옵션
        
        if employees_df is not None:
            # DataFrame인지 확인하고 처리
            import pandas as pd
            if isinstance(employees_df, pd.DataFrame) and len(employees_df) > 0:
                # 재직 중인 직원만 필터링
                active_employees = employees_df[employees_df['status'] == '재직']
                if len(active_employees) > 0:
                    employee_names.extend(active_employees['name'].tolist())
    except Exception as e:
        employee_names = [get_text('schedule_task.registration.direct_input')]  # 오류 발생 시 기본값만 사용
    
    with st.form("task_registration_form"):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            task_title = st.text_input(f"{get_text('schedule_task.registration.task_title')}*", 
                                      placeholder=get_text('schedule_task.registration.task_title_placeholder'))
            category_id = st.selectbox(f"{get_text('schedule_task.registration.category')}*", 
                                     options=list(category_options.keys()), 
                                     format_func=lambda x: category_options[x])
            
            # 담당자 선택 개선
            assigned_option = st.selectbox(f"{get_text('schedule_task.registration.assignee_method')}*", employee_names)
            
            if assigned_option == get_text('schedule_task.registration.direct_input'):
                assigned_person = st.text_input(f"{get_text('schedule_task.registration.assignee_input')}*", 
                                              placeholder=get_text('schedule_task.registration.assignee_placeholder'))
            else:
                assigned_person = assigned_option
                st.write(f"{get_text('schedule_task.registration.selected_assignee')}: **{assigned_person}**")
            
            priority = st.selectbox(get_text('schedule_task.registration.priority'), task_manager.get_priority_levels())
        
        with col2:
            responsible_department = st.text_input(get_text('schedule_task.registration.department'), 
                                                 placeholder=get_text('schedule_task.registration.department_placeholder'))
            due_date = st.date_input(f"{get_text('schedule_task.registration.due_date')}*", 
                                   value=datetime.now().date() + timedelta(days=30))
            is_recurring = st.checkbox(get_text('schedule_task.registration.recurring'))
            
            if is_recurring:
                interval_days = st.number_input(get_text('schedule_task.registration.interval_days'), min_value=1, value=365)
            else:
                interval_days = 0
        
        # 상세 정보
        description = st.text_area(get_text('schedule_task.registration.description'), 
                                  placeholder=get_text('schedule_task.registration.description_placeholder'))
        notes = st.text_area(get_text('schedule_task.registration.notes'), 
                            placeholder=get_text('schedule_task.registration.notes_placeholder'))
        documents = st.text_input(get_text('schedule_task.registration.documents'), 
                                placeholder=get_text('schedule_task.registration.documents_placeholder'))
        
        # 제출 버튼
        submitted = st.form_submit_button(get_text('schedule_task.registration.submit'), type="primary")
        
        if submitted:
            # 필수 필드 검증
            errors = []
            if not task_title or not task_title.strip():
                errors.append(get_text('schedule_task.registration.title_required'))
            if assigned_option == get_text('schedule_task.registration.direct_input') and (not assigned_person or not assigned_person.strip()):
                errors.append(get_text('schedule_task.registration.assignee_required'))
            elif assigned_option != get_text('schedule_task.registration.direct_input'):
                assigned_person = assigned_option
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # 일정 데이터 준비
                task_data = {
                    'task_title': task_title,
                    'category_id': category_id,
                    'description': description,
                    'assigned_person': assigned_person,
                    'responsible_department': responsible_department,
                    'priority': priority,
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'is_recurring': is_recurring,
                    'interval_days': interval_days,
                    'notes': notes,
                    'documents': documents,
                    'created_by': st.session_state.get('current_user_name', 'System')
                }
                
                # 일정 등록
                success, task_id = task_manager.add_task(task_data)
                
                if success:
                    st.success(f"✅ {get_text('schedule_task.registration.success')} (ID: {task_id})")
                    st.rerun()
                else:
                    st.error(get_text('schedule_task.registration.failed'))

def show_task_management(task_manager, get_text):
    """일정 관리"""
    st.header(f"📋 {get_text('schedule_task.management.title')}")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(get_text('schedule_task.management.status_filter'), ["전체"] + task_manager.get_task_statuses())
    
    with col2:
        categories_df = task_manager.get_categories()
        category_options = ["전체"] + list(categories_df['category_name'])
        category_filter = st.selectbox(get_text('schedule_task.management.category_filter'), category_options)
    
    with col3:
        priority_filter = st.selectbox(get_text('schedule_task.management.priority_filter'), ["전체"] + task_manager.get_priorities())
    
    # 검색
    search_term = st.text_input(get_text('schedule_task.management.search'), 
                               placeholder=get_text('schedule_task.management.search_placeholder'))
    
    # 일정 목록 가져오기
    tasks = task_manager.get_tasks()
    tasks_df = pd.DataFrame(tasks) if tasks else pd.DataFrame()
    
    if len(tasks_df) == 0:
        st.info(get_text('schedule_task.management.no_tasks'))
        return
    
    # 카테고리 이름 매핑 (category_id가 있는 경우만)
    if 'category_id' in tasks_df.columns:
        categories_df = task_manager.get_categories()
        category_dict = dict(zip(categories_df['category_id'], categories_df['category_name']))
        tasks_df['category_name'] = tasks_df['category_id'].map(category_dict)
    elif 'category' in tasks_df.columns:
        # category 필드가 이미 이름으로 되어 있는 경우
        tasks_df['category_name'] = tasks_df['category']
    
    # 필터링 적용
    filtered_df = tasks_df.copy()
    
    if status_filter != "전체":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if category_filter != "전체":
        filtered_df = filtered_df[filtered_df['category_name'] == category_filter]
    
    if priority_filter != "전체":
        filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
    
    if search_term:
        # 검색 가능한 필드들을 확인하고 존재하는 필드만 사용
        search_fields = []
        if 'task_title' in filtered_df.columns:
            search_fields.append(filtered_df['task_title'].astype(str).str.contains(search_term, case=False, na=False))
        elif 'title' in filtered_df.columns:
            search_fields.append(filtered_df['title'].astype(str).str.contains(search_term, case=False, na=False))
        
        if 'assigned_person' in filtered_df.columns:
            search_fields.append(filtered_df['assigned_person'].astype(str).str.contains(search_term, case=False, na=False))
        elif 'assignee' in filtered_df.columns:
            search_fields.append(filtered_df['assignee'].astype(str).str.contains(search_term, case=False, na=False))
            
        if 'description' in filtered_df.columns:
            search_fields.append(filtered_df['description'].astype(str).str.contains(search_term, case=False, na=False))
        
        if search_fields:
            mask = search_fields[0]
            for field in search_fields[1:]:
                mask = mask | field
            filtered_df = filtered_df[mask]
    
    # 일정 목록 표시
    st.write(f"**{get_text('schedule_task.management.total_count').format(count=len(filtered_df))}**")
    
    for _, task in filtered_df.iterrows():
        # 상태에 따른 아이콘
        status_icons = {
            '예정': '📅',
            '진행중': '🔄',
            '완료': '✅',
            '연기': '⏰',
            '취소': '❌'
        }
        
        # 우선순위에 따른 색상
        priority_colors = {
            '긴급': '🔴',
            '높음': '🟡',
            '보통': '🔵',
            '낮음': '⚪'
        }
        
        status_icon = status_icons.get(task['status'], '📅')
        priority_icon = priority_colors.get(task['priority'], '🔵')
        
        # 마감일까지 남은 일수 계산
        due_date = pd.to_datetime(task['due_date']).date()
        days_left = (due_date - datetime.now().date()).days
        
        if days_left < 0:
            date_info = get_text('schedule_task.management.overdue_days').format(days=abs(days_left))
            date_color = "🔴"
        elif days_left <= 7:
            date_info = get_text('schedule_task.management.d_minus').format(days=days_left)
            date_color = "🟡"
        else:
            date_info = get_text('schedule_task.management.d_minus').format(days=days_left)
            date_color = "🔵"
        
        with st.expander(f"{status_icon} {priority_icon} {task['task_title']} - {task['assigned_person']} ({date_color} {date_info})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{get_text('schedule_task.management.category')}:** {task['category_name']}")
                st.write(f"**{get_text('schedule_task.management.assignee')}:** {task['assigned_person']}")
                st.write(f"**{get_text('schedule_task.management.department')}:** {task['responsible_department']}")
                st.write(f"**{get_text('schedule_task.management.priority')}:** {task['priority']}")
            
            with col2:
                st.write(f"**{get_text('schedule_task.management.status')}:** {task['status']}")
                st.write(f"**{get_text('schedule_task.management.due_date')}:** {task['due_date']}")
                st.write(f"**생성일:** {task['created_date'][:10]}")
                if task['is_recurring']:
                    st.write(f"**반복 주기:** {task['interval_days']}일")
            
            if task['description']:
                st.write(f"**설명:** {task['description']}")
            
            if task['notes']:
                st.write(f"**비고:** {task['notes']}")
            
            # 상태 업데이트
            if task['status'] != '완료':
                st.subheader("상태 업데이트")
                
                with st.form(f"update_form_{task['task_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_status = st.selectbox("새 상태", task_manager.get_task_statuses(), 
                                                index=task_manager.get_task_statuses().index(task['status']))
                    
                    with col2:
                        update_notes = st.text_input("업데이트 메모")
                    
                    if new_status == '완료':
                        completion_date = st.date_input("완료일", value=datetime.now().date())
                    else:
                        completion_date = None
                    
                    if st.form_submit_button("상태 업데이트"):
                        success, message = task_manager.update_task_status(
                            task['task_id'], 
                            new_status, 
                            update_notes if update_notes else task['notes'],
                            completion_date.strftime('%Y-%m-%d') if completion_date else None
                        )
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

def show_notifications(task_manager, get_text):
    """알림 및 임박한 일정"""
    st.header(f"🔔 {get_text('schedule_task.notifications.title')}")
    
    # 연체된 작업
    st.subheader(f"🚨 {get_text('schedule_task.notifications.overdue_title')}")
    overdue_tasks = task_manager.get_overdue_tasks()
    
    if len(overdue_tasks) > 0:
        st.error(f"총 {len(overdue_tasks)}건의 연체된 작업이 있습니다.")
        
        for _, task in overdue_tasks.iterrows():
            days_overdue = (datetime.now().date() - pd.to_datetime(task['due_date']).date()).days
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{task['task_title']}**")
                    st.write(f"{get_text('schedule_task.notifications.assignee')}: {task['assigned_person']}")
                
                with col2:
                    st.write(f"{get_text('schedule_task.management.due_date')}: {task['due_date']}")
                    overdue_text = get_text('schedule_task.notifications.overdue_days').format(days=days_overdue)
                    st.write(overdue_text)
                
                with col3:
                    if st.button(f"처리", key=f"overdue_{task['task_id']}"):
                        st.session_state[f"process_{task['task_id']}"] = True
        
        st.markdown("---")
    else:
        st.success(get_text('schedule_task.notifications.no_overdue'))
    
    # 임박한 작업 (30일 내)
    st.subheader(f"⚠️ {get_text('schedule_task.notifications.upcoming_title')}")
    upcoming_tasks = task_manager.get_upcoming_tasks(30)
    
    if len(upcoming_tasks) > 0:
        # 기간별 그룹화
        today = datetime.now().date()
        
        for days_ahead in [7, 14, 30]:
            period_tasks = upcoming_tasks[
                pd.to_datetime(upcoming_tasks['due_date']).dt.date <= today + timedelta(days=days_ahead)
            ]
            
            if len(period_tasks) > 0:
                if days_ahead == 7:
                    st.write(f"**🔴 7일 내 ({len(period_tasks)}건)**")
                elif days_ahead == 14:
                    st.write(f"**🟡 14일 내 ({len(period_tasks)}건)**")
                else:
                    st.write(f"**🔵 30일 내 ({len(period_tasks)}건)**")
                
                for _, task in period_tasks.head(5).iterrows():
                    due_date = pd.to_datetime(task['due_date']).date()
                    days_left = (due_date - today).days
                    st.write(f"- {task['task_title']} (D-{days_left}) - {task['assigned_person']}")
                
                st.markdown("---")
    else:
        st.info(get_text('schedule_task.notifications.no_upcoming'))

def show_statistics(task_manager, get_text):
    """통계 분석"""
    st.header(f"📈 {get_text('schedule_task.statistics.title')}")
    
    stats = task_manager.get_task_statistics()
    
    if not stats:
        st.info(get_text('schedule_task.statistics.no_data'))
        return
    
    # 상태별 분포
    if stats.get('by_status'):
        st.subheader("상태별 일정 분포")
        
        status_data = []
        for status, count in stats['by_status'].items():
            status_data.append({'status': status, 'count': count})
        
        status_df = pd.DataFrame(status_data)
        fig = px.pie(status_df, values='count', names='status', title="상태별 일정 분포")
        st.plotly_chart(fig, use_container_width=True)
    
    # 우선순위별 분포
    if stats.get('by_priority'):
        st.subheader("우선순위별 일정 분포")
        
        priority_data = []
        for priority, count in stats['by_priority'].items():
            priority_data.append({'priority': priority, 'count': count})
        
        priority_df = pd.DataFrame(priority_data)
        fig = px.bar(priority_df, x='priority', y='count', title="우선순위별 일정 수")
        st.plotly_chart(fig, use_container_width=True)
    
    # 월별 마감일 분포
    tasks_df = task_manager.get_all_tasks()
    if len(tasks_df) > 0:
        st.subheader("월별 마감일 분포")
        
        tasks_df['due_month'] = pd.to_datetime(tasks_df['due_date']).dt.strftime('%Y-%m')
        monthly_counts = tasks_df['due_month'].value_counts().sort_index()
        
        monthly_df = pd.DataFrame({
            'month': monthly_counts.index,
            'count': monthly_counts.values
        })
        
        fig = px.line(monthly_df, x='month', y='count', title="월별 마감일 분포")
        st.plotly_chart(fig, use_container_width=True)

def show_category_management(task_manager, get_text):
    """카테고리 관리"""
    st.header(f"⚙️ {get_text('schedule_task.categories.title')}")
    
    # 탭 구성
    category_tab1, category_tab2 = st.tabs([f"📋 {get_text('schedule_task.categories.existing')}", f"➕ {get_text('schedule_task.categories.add_new')}"])
    
    with category_tab1:
        show_current_categories(task_manager, get_text)
    
    with category_tab2:
        show_category_form(task_manager, get_text)

def show_current_categories(task_manager, get_text):
    """현재 카테고리 목록 표시"""
    st.subheader(get_text('schedule_task.categories.existing'))
    
    categories_df = task_manager.get_categories()
    
    if len(categories_df) > 0:
        for _, category in categories_df.iterrows():
            with st.expander(f"📁 {category['category_name']} ({category['category_id']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{get_text('schedule_task.categories.category_id')}**: {category['category_id']}")
                    st.write(f"**{get_text('schedule_task.categories.category_name')}**: {category['category_name']}")
                    st.write(f"**{get_text('schedule_task.categories.description')}**: {category['description']}")
                    st.write(f"**{get_text('schedule_task.categories.default_interval_label')}**: {category['default_interval_days']}일")
                    
                    # 알림 일정 표시
                    if 'notification_days' in category and category['notification_days']:
                        # 문자열로 저장된 리스트를 파싱
                        try:
                            import ast
                            notification_days = ast.literal_eval(str(category['notification_days']))
                            st.write(f"**{get_text('schedule_task.categories.notification_schedule_label')}**: {', '.join(map(str, notification_days))}일 전")
                        except:
                            st.write(f"**{get_text('schedule_task.categories.notification_schedule_label')}**: {category['notification_days']}")
                
                with col2:
                    if st.button(f"✏️ {get_text('schedule_task.categories.edit')}", key=f"edit_cat_{category['category_id']}"):
                        st.session_state.edit_category_id = category['category_id']
                        st.rerun()
                    
                    if st.button(f"🗑️ {get_text('schedule_task.categories.delete')}", key=f"delete_cat_{category['category_id']}"):
                        # 삭제 확인
                        if st.session_state.get('confirm_delete_cat') == category['category_id']:
                            success, message = task_manager.delete_category(category['category_id'])
                            if success:
                                st.success(get_text('schedule_task.categories.success_delete'))
                                del st.session_state.confirm_delete_cat
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.session_state.confirm_delete_cat = category['category_id']
                            st.warning("정말 삭제하시겠습니까? 삭제 버튼을 다시 클릭하세요.")
    else:
        st.info(get_text('schedule_task.categories.no_categories'))

def show_category_form(task_manager, get_text):
    """카테고리 추가/수정 폼"""
    st.subheader(get_text('schedule_task.categories.form_title'))
    
    # 수정 모드인지 확인
    is_edit_mode = 'edit_category_id' in st.session_state
    category_data = {}
    
    if is_edit_mode:
        categories_df = task_manager.get_categories()
        category_data = categories_df[categories_df['category_id'] == st.session_state.edit_category_id].iloc[0].to_dict()
        st.info(f"'{category_data['category_name']}' {get_text('schedule_task.categories.editing_category')}")
    
    # 폼 키 설정
    form_key = f"category_form_{int(time.time())}" if not is_edit_mode else f"edit_category_form_{st.session_state.edit_category_id}"
    
    with st.form(form_key):
        col1, col2 = st.columns(2)
        
        with col1:
            # 카테고리 ID는 수정 시 비활성화
            if is_edit_mode:
                category_id = st.text_input(f"{get_text('schedule_task.categories.category_id')}*", 
                                          value=category_data.get('category_id', ''),
                                          disabled=True)
            else:
                category_id = st.text_input(f"{get_text('schedule_task.categories.category_id')}*", 
                                          placeholder=get_text('schedule_task.categories.id_placeholder'),
                                          help="영문 대문자와 숫자만 사용")
            
            category_name = st.text_input(f"{get_text('schedule_task.categories.category_name')}*", 
                                        value=category_data.get('category_name', ''),
                                        placeholder=get_text('schedule_task.categories.name_placeholder'))
        
        with col2:
            default_interval_days = st.number_input(f"{get_text('schedule_task.categories.default_interval')}*", 
                                                  min_value=1, 
                                                  max_value=365,
                                                  value=int(category_data.get('default_interval_days', 30)))
        
        description = st.text_area(f"{get_text('schedule_task.categories.description')}*", 
                                 value=category_data.get('description', ''),
                                 placeholder=get_text('schedule_task.categories.desc_placeholder'))
        
        # 알림 일정 설정
        st.subheader(get_text('schedule_task.categories.notification_setup'))
        st.write(get_text('schedule_task.categories.notification_help'))
        
        # 기존 알림 일정 파싱
        default_notifications = "30, 14, 7, 1"
        if is_edit_mode and 'notification_days' in category_data:
            try:
                import ast
                existing_notifications = ast.literal_eval(str(category_data['notification_days']))
                default_notifications = ", ".join(map(str, existing_notifications))
            except:
                pass
        
        notification_input = st.text_input(f"{get_text('schedule_task.categories.notification_days')}*", 
                                         value=default_notifications,
                                         placeholder=get_text('schedule_task.categories.notification_placeholder'))
        
        # 제출 버튼
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit_text = get_text('schedule_task.categories.modify') if is_edit_mode else get_text('schedule_task.categories.add')
            submitted = st.form_submit_button(submit_text, type="primary")
        
        with col_cancel:
            cancelled = st.form_submit_button(get_text('schedule_task.categories.cancel'))
        
        if submitted:
            # 입력 검증
            errors = []
            
            if not category_id or not category_id.strip():
                errors.append(get_text('schedule_task.categories.id_required'))
            elif not is_edit_mode and not category_id.replace('_', '').replace('-', '').isalnum():
                errors.append(get_text('schedule_task.categories.id_format_error'))
            
            if not category_name or not category_name.strip():
                errors.append(get_text('schedule_task.categories.name_required'))
            
            if not description or not description.strip():
                errors.append(get_text('schedule_task.categories.desc_required'))
            
            # 알림 일정 파싱 및 검증
            notification_days = []
            if notification_input.strip():
                try:
                    notification_days = [int(x.strip()) for x in notification_input.split(',') if x.strip()]
                    if not notification_days:
                        errors.append(get_text('schedule_task.categories.notification_required'))
                    elif any(day <= 0 or day > 365 for day in notification_days):
                        errors.append(get_text('schedule_task.categories.notification_range_error'))
                except ValueError:
                    errors.append(get_text('schedule_task.categories.notification_format_error'))
            else:
                errors.append(get_text('schedule_task.categories.notification_required'))
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # 카테고리 데이터 준비
                new_category_data = {
                    'category_id': category_id.strip().upper() if category_id else '',
                    'category_name': category_name.strip() if category_name else '',
                    'description': description.strip() if description else '',
                    'default_interval_days': default_interval_days,
                    'notification_days': notification_days
                }
                
                # 추가 또는 수정
                if is_edit_mode:
                    success, message = task_manager.update_category(st.session_state.edit_category_id, new_category_data)
                    if success:
                        st.success(f"✅ {message}")
                        del st.session_state.edit_category_id
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    success, message = task_manager.add_category(new_category_data)
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        if cancelled:
            if is_edit_mode and 'edit_category_id' in st.session_state:
                del st.session_state.edit_category_id
            st.rerun()