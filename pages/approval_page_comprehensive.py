import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_approval_page(approval_manager, employee_manager, user_permissions, get_text):
    """종합 승인 관리 페이지를 표시합니다."""
    
    st.header("✅ 승인 관리")
    
    # 현재 사용자 정보
    current_user = st.session_state.get('user_id', 'system')
    user_name = st.session_state.get('user_name', 'System User')
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 승인 대기",
        "✅ 승인 처리", 
        "📊 승인 통계",
        "🔍 승인 내역",
        "📝 내 요청"
    ])
    
    with tab1:
        show_pending_approvals(approval_manager, employee_manager, current_user, user_name)
    
    with tab2:
        show_approval_processing(approval_manager, current_user, user_name)
    
    with tab3:
        show_approval_statistics(approval_manager)
    
    with tab4:
        show_approval_history(approval_manager, current_user)
    
    with tab5:
        show_my_requests(approval_manager, current_user, user_name)

def show_pending_approvals(approval_manager, employee_manager, current_user, user_name):
    """승인 대기 목록을 표시합니다."""
    st.header("📋 승인 대기 목록")
    
    try:
        # 지출요청서 승인 대기 목록
        from expense_request_manager import ExpenseRequestManager
        expense_manager = ExpenseRequestManager()
        
        # 현재 사용자의 승인 대기 목록
        pending_expense_requests = expense_manager.get_pending_approvals(current_user)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("지출요청서 승인 대기", len(pending_expense_requests) if pending_expense_requests else 0)
        
        with col2:
            # 기타 승인 대기
            try:
                pending_requests = approval_manager.get_pending_requests()
                other_count = len(pending_requests) if not len(pending_requests) == 0 else 0
                st.metric("기타 승인 대기", other_count)
            except:
                st.metric("기타 승인 대기", 0)
        
        # 지출요청서 승인 처리
        if pending_expense_requests:
            st.subheader("💰 지출요청서 승인 대기")
            
            for request in pending_expense_requests:
                with st.expander(f"🎫 {request['expense_title']} - {request['amount']:,.0f} {request['currency']} ({request['request_date'][:10]})"):
                    
                    # 요청 정보 표시
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**요청번호:** {request['request_id']}")
                        st.write(f"**요청자:** {request['requester_name']}")
                        st.write(f"**카테고리:** {request['category']}")
                        st.write(f"**금액:** {request['amount']:,.0f} {request['currency']}")
                    
                    with col2:
                        st.write(f"**승인단계:** {request['approval_step']}")
                        st.write(f"**요청일:** {request['request_date'][:10]}")
                        st.write(f"**예상지출일:** {request['expected_date']}")
                        st.write(f"**상태:** {request['status']}")
                    
                    st.write(f"**지출내용:**")
                    st.write(request['expense_description'])
                    
                    # 승인 처리 폼
                    st.markdown("---")
                    
                    with st.form(f"approval_form_{request['approval_id']}"):
                        st.subheader("승인 처리")
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            comments = st.text_area(
                                "승인/반려 사유",
                                placeholder="승인 또는 반려 사유를 입력하세요 (선택사항)",
                                key=f"comments_{request['approval_id']}"
                            )
                        
                        with col2:
                            if st.form_submit_button("✅ 승인", type="primary"):
                                success, message = expense_manager.process_approval(
                                    request['approval_id'], 
                                    current_user, 
                                    '승인', 
                                    comments
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        
                        with col3:
                            if st.form_submit_button("❌ 반려"):
                                if comments.strip():
                                    success, message = expense_manager.process_approval(
                                        request['approval_id'], 
                                        current_user, 
                                        '반려', 
                                        comments
                                    )
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("반려 시 사유를 반드시 입력해주세요.")
        else:
            st.info("💰 지출요청서 승인 대기 건이 없습니다.")
        
        # 기타 승인 대기 항목들
        st.markdown("---")
        st.subheader("📋 기타 승인 대기")
        
        try:
            pending_requests = approval_manager.get_pending_requests()
            
            if len(pending_requests) > 0:
                for _, request in pending_requests.iterrows():
                    with st.expander(f"📄 {request['request_type']} - {request['requester_name']} ({request['request_date'][:10]})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**요청 유형:** {request['request_type']}")
                            st.write(f"**요청자:** {request['requester_name']}")
                            st.write(f"**우선순위:** {request['priority']}")
                        
                        with col2:
                            st.write(f"**요청일:** {request['request_date'][:10]}")
                            st.write(f"**상태:** {request['status']}")
                        
                        st.write(f"**내용:** {request['description']}")
                        
                        # 승인 처리
                        with st.form(f"other_approval_{request['approval_id']}"):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                reason = st.text_area(
                                    "처리 사유",
                                    placeholder="승인/거부 사유를 입력하세요",
                                    key=f"reason_{request['approval_id']}"
                                )
                            
                            with col2:
                                if st.form_submit_button("✅ 승인", type="primary"):
                                    success = approval_manager.approve_request(
                                        request['approval_id'], 
                                        current_user, 
                                        reason, 
                                        user_name
                                    )
                                    if success:
                                        st.success("승인 완료!")
                                        st.rerun()
                                    else:
                                        st.error("승인 처리 중 오류가 발생했습니다.")
                            
                            with col3:
                                if st.form_submit_button("❌ 거부"):
                                    if reason.strip():
                                        success = approval_manager.reject_request(
                                            request['approval_id'], 
                                            current_user, 
                                            reason, 
                                            user_name
                                        )
                                        if success:
                                            st.success("거부 처리 완료!")
                                            st.rerun()
                                        else:
                                            st.error("거부 처리 중 오류가 발생했습니다.")
                                    else:
                                        st.error("거부 시 사유를 반드시 입력해주세요.")
            else:
                st.info("기타 승인 대기 건이 없습니다.")
                
        except Exception as e:
            st.error(f"기타 승인 대기 목록 조회 중 오류: {e}")
    
    except Exception as e:
        st.error(f"승인 대기 목록 조회 중 오류: {e}")

def show_approval_processing(approval_manager, current_user, user_name):
    """승인 처리 현황을 표시합니다."""
    st.header("✅ 승인 처리 현황")
    
    try:
        # 최근 7일간의 승인 요청
        recent_requests = approval_manager.get_recent_requests(7)
        
        if len(not len(recent_requests) == 0.replace(".empty", "")) > 0:
            st.subheader("📈 최근 7일간 승인 요청")
            
            # 일별 요청 수 차트
            recent_requests['date'] = pd.to_datetime(recent_requests['request_date']).dt.date
            daily_counts = recent_requests.groupby('date').size()
            
            fig = px.line(
                x=daily_counts.index, 
                y=daily_counts.values,
                title="일별 승인 요청 수",
                labels={'x': '날짜', 'y': '요청 수'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # 상태별 분포
            status_counts = recent_requests['status'].value_counts()
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    values=status_counts.values, 
                    names=status_counts.index,
                    title="최근 7일 승인 요청 상태 분포"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # 요청 유형별 분포
                type_counts = recent_requests['request_type'].value_counts()
                fig_bar = px.bar(
                    x=type_counts.index, 
                    y=type_counts.values,
                    title="요청 유형별 분포",
                    labels={'x': '요청 유형', 'y': '건수'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # 상세 목록
            st.subheader("🔍 최근 승인 요청 상세")
            
            # 필터링 옵션
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox(
                    "상태 필터",
                    options=['전체'] + list(recent_requests['status'].unique())
                )
            
            with col2:
                type_filter = st.selectbox(
                    "유형 필터",
                    options=['전체'] + list(recent_requests['request_type'].unique())
                )
            
            # 필터 적용
            filtered_requests = recent_requests.copy()
            if status_filter != '전체':
                filtered_requests = filtered_requests[filtered_requests['status'] == status_filter]
            if type_filter != '전체':
                filtered_requests = filtered_requests[filtered_requests['request_type'] == type_filter]
            
            # 테이블 표시
            if len(not len(filtered_requests) == 0.replace(".empty", "")) > 0:
                display_columns = ['approval_id', 'request_type', 'requester_name', 'status', 'priority', 'request_date']
                st.dataframe(
                    filtered_requests[display_columns],
                    column_config={
                        'approval_id': '승인ID',
                        'request_type': '요청유형',
                        'requester_name': '요청자',
                        'status': '상태',
                        'priority': '우선순위',
                        'request_date': '요청일시'
                    },
                    use_container_width=True
                )
            else:
                st.info("필터 조건에 맞는 요청이 없습니다.")
        else:
            st.info("최근 7일간 승인 요청이 없습니다.")
    
    except Exception as e:
        st.error(f"승인 처리 현황 조회 중 오류: {e}")

def show_approval_statistics(approval_manager):
    """승인 통계를 표시합니다."""
    st.header("📊 승인 통계")
    
    try:
        stats = approval_manager.get_approval_statistics()
        
        if stats and stats.get('total_requests', 0) > 0:
            # 주요 지표
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 요청", f"{stats['total_requests']}건")
            
            with col2:
                st.metric("승인률", f"{stats['approval_rate']:.1f}%")
            
            with col3:
                st.metric("승인 완료", f"{stats['approved_requests']}건")
            
            with col4:
                st.metric("대기 중", f"{stats['pending_requests']}건")
            
            # 차트들
            col1, col2 = st.columns(2)
            
            with col1:
                # 상태별 분포
                status_data = stats.get('status_distribution', {})
                if status_data:
                    fig_status = px.pie(
                        values=list(status_data.values()), 
                        names=list(status_data.keys()),
                        title="승인 요청 상태별 분포"
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # 요청 유형별 분포
                type_data = stats.get('type_distribution', {})
                if type_data:
                    fig_type = px.bar(
                        x=list(type_data.keys()), 
                        y=list(type_data.values()),
                        title="요청 유형별 분포",
                        labels={'x': '요청 유형', 'y': '건수'}
                    )
                    st.plotly_chart(fig_type, use_container_width=True)
            
            # 우선순위별 분포
            priority_data = stats.get('priority_distribution', {})
            if priority_data:
                st.subheader("우선순위별 분포")
                fig_priority = px.bar(
                    x=list(priority_data.keys()), 
                    y=list(priority_data.values()),
                    title="우선순위별 승인 요청 분포",
                    labels={'x': '우선순위', 'y': '건수'},
                    color=list(priority_data.keys()),
                    color_discrete_map={
                        '긴급': 'red',
                        '높음': 'orange', 
                        '보통': 'yellow',
                        '낮음': 'green'
                    }
                )
                st.plotly_chart(fig_priority, use_container_width=True)
        else:
            st.info("승인 통계를 표시할 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"승인 통계 조회 중 오류: {e}")

def show_approval_history(approval_manager, current_user):
    """승인 내역을 표시합니다."""
    st.header("🔍 승인 내역")
    
    try:
        # 모든 승인 요청 가져오기
        all_requests = approval_manager.get_all_requests()
        
        if all_requests:
            df = pd.DataFrame(all_requests)
            
            # 날짜 필터
            col1, col2, col3 = st.columns(3)
            
            with col1:
                start_date = st.date_input(
                    "시작일",
                    value=datetime.now().date() - timedelta(days=30)
                )
            
            with col2:
                end_date = st.date_input(
                    "종료일",
                    value=datetime.now().date()
                )
            
            with col3:
                status_filter = st.selectbox(
                    "상태",
                    options=['전체'] + list(df['status'].unique())
                )
            
            # 필터 적용
            df['request_date'] = pd.to_datetime(df['request_date'])
            filtered_df = df[
                (df['request_date'].dt.date >= start_date) &
                (df['request_date'].dt.date <= end_date)
            ]
            
            if status_filter != '전체':
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            # 결과 표시
            if len(not len(filtered_df) == 0.replace(".empty", "")) > 0:
                st.success(f"검색 결과: {len(filtered_df)}건")
                
                # 상세 내역
                for _, request in filtered_df.iterrows():
                    status_color = {
                        'pending': '🟡',
                        'approved': '✅', 
                        'rejected': '❌',
                        '대기': '🟡',
                        '승인': '✅',
                        '거부': '❌'
                    }.get(request['status'], '⚪')
                    
                    with st.expander(f"{status_color} {request['request_type']} - {request['requester_name']} ({request['request_date'].strftime('%Y-%m-%d')})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**승인 ID:** {request['approval_id']}")
                            st.write(f"**요청 유형:** {request['request_type']}")
                            st.write(f"**요청자:** {request['requester_name']}")
                            st.write(f"**상태:** {request['status']}")
                        
                        with col2:
                            st.write(f"**요청일:** {request['request_date'].strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**우선순위:** {request['priority']}")
                            if pd.notna(request['approver_name']):
                                st.write(f"**승인자:** {request['approver_name']}")
                            if pd.notna(request['approval_date']):
                                st.write(f"**처리일:** {request['approval_date']}")
                        
                        st.write(f"**내용:** {request['description']}")
                        
                        if pd.notna(request['reason']):
                            st.write(f"**승인 사유:** {request['reason']}")
                        
                        if pd.notna(request['rejection_reason']):
                            st.write(f"**거부 사유:** {request['rejection_reason']}")
            else:
                st.info("검색 조건에 맞는 승인 내역이 없습니다.")
        else:
            st.info("승인 내역이 없습니다.")
    
    except Exception as e:
        st.error(f"승인 내역 조회 중 오류: {e}")

def show_my_requests(approval_manager, current_user, user_name):
    """내 요청 현황을 표시합니다."""
    st.header("📝 내 요청 현황")
    
    try:
        # 내가 요청한 승인들
        my_requests = approval_manager.get_requests_by_requester(current_user)
        
        if len(not len(my_requests) == 0.replace(".empty", "")) > 0:
            # 상태별 개수
            status_counts = my_requests['status'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 요청", len(my_requests))
            
            with col2:
                st.metric("대기 중", status_counts.get('pending', status_counts.get('대기', 0)))
            
            with col3:
                st.metric("승인됨", status_counts.get('approved', status_counts.get('승인', 0)))
            
            with col4:
                st.metric("거부됨", status_counts.get('rejected', status_counts.get('거부', 0)))
            
            # 최근 요청들
            st.subheader("최근 요청 내역")
            
            # 날짜순 정렬
            my_requests['request_date'] = pd.to_datetime(my_requests['request_date'])
            my_requests_sorted = my_requests.sort_values('request_date', ascending=False)
            
            for _, request in my_requests_sorted.head(10).iterrows():
                status_color = {
                    'pending': '🟡',
                    'approved': '✅', 
                    'rejected': '❌',
                    '대기': '🟡',
                    '승인': '✅',
                    '거부': '❌'
                }.get(request['status'], '⚪')
                
                with st.expander(f"{status_color} {request['request_type']} ({request['request_date'].strftime('%Y-%m-%d')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**승인 ID:** {request['approval_id']}")
                        st.write(f"**요청 유형:** {request['request_type']}")
                        st.write(f"**상태:** {request['status']}")
                        st.write(f"**우선순위:** {request['priority']}")
                    
                    with col2:
                        st.write(f"**요청일:** {request['request_date'].strftime('%Y-%m-%d %H:%M')}")
                        if pd.notna(request['approver_name']):
                            st.write(f"**승인자:** {request['approver_name']}")
                        if pd.notna(request['approval_date']):
                            st.write(f"**처리일:** {request['approval_date']}")
                    
                    st.write(f"**내용:** {request['description']}")
                    
                    if pd.notna(request['reason']):
                        st.write(f"**승인 사유:** {request['reason']}")
                    
                    if pd.notna(request['rejection_reason']):
                        st.write(f"**거부 사유:** {request['rejection_reason']}")
        else:
            st.info("요청한 승인이 없습니다.")
    
    except Exception as e:
        st.error(f"내 요청 조회 중 오류: {e}")