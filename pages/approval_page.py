import streamlit as st
st.write("🔴 approval_page.py 파일 실행됨!")



import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_approval_page(approval_manager, employee_manager, user_permissions, get_text):
    """승인 관리 페이지를 표시합니다."""
    
    st.header("✅ 승인 관리")
    
    # 현재 사용자 정보
    current_user = st.session_state.get('user_id', 'system')
    user_name = st.session_state.get('user_name', 'System User')
    
    # 디버깅용 - 현재 사용자 정보 표시
    st.info(f"현재 로그인 사용자: {user_name} (ID: {current_user})")
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 승인 대기",
        "✅ 승인 처리", 
        "📊 승인 통계",
        "🔍 승인 내역",
        "📝 내 요청"
    ])
    
    with tab1:
        show_pending_approvals_tab(approval_manager, employee_manager, current_user, user_name)
    
    with tab2:
        show_approval_processing_tab(approval_manager, current_user, user_name)
    
    with tab3:
        show_approval_statistics_tab(approval_manager)
    
    with tab4:
        show_approval_history_tab(approval_manager, current_user)
    
    with tab5:
        show_my_requests_tab(approval_manager, current_user, user_name)

def show_pending_approvals_tab(approval_manager, employee_manager, current_user, user_name):
    """승인 대기 목록 탭을 표시합니다."""
    st.header("📋 승인 대기 목록")
    
    try:
        show_pending_expense_requests(current_user, user_name)
        show_pending_other_requests(approval_manager, current_user, user_name)
        
    except Exception as e:
        st.error(f"승인 대기 목록 조회 중 오류: {e}")

def show_pending_expense_requests(current_user, user_name):
    """지출요청서 승인 대기를 표시합니다."""
    try:
        import psycopg2
        import streamlit as st
        
        # PostgreSQL에서 직접 조회
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"]
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ea.approval_id,
                er.request_id,
                er.expense_title,
                er.total_amount as amount,
                er.currency,
                er.expected_date,
                er.expense_description,
                er.request_date,
                er.employee_name as requester_name,
                er.category,
                er.first_approver_name,
                ea.approval_step,
                ea.status as approval_status
            FROM expense_approvals ea
            JOIN expense_requests er ON ea.request_id = er.id
            WHERE ea.approver_id = %s 
            AND ea.status = 'pending'
            ORDER BY ea.created_date ASC
        """, (current_user,))
        
        columns = [desc[0] for desc in cursor.description]
        pending_expense_requests = []
        
        for row in cursor.fetchall():
            request_dict = dict(zip(columns, row))
            pending_expense_requests.append(request_dict)
        
        cursor.close()
        conn.close()
        
        # 간단한 상태 표시
        st.info(f"현재 사용자: {user_name} (ID: {current_user}) - 승인 대기 건수: {len(pending_expense_requests) if pending_expense_requests else 0}건")
        
        st.subheader("💰 지출요청서 승인 대기")
        
        if pending_expense_requests and len(pending_expense_requests) > 0:
            st.success(f"총 {len(pending_expense_requests)}건의 지출요청서 승인 대기")
            
            for request in pending_expense_requests:
                with st.expander(f"🎫 {request['expense_title']} - {request['amount']:,.0f} {request['currency']} ({request['request_date'][:10]})"):
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
                    
                    st.write(f"**지출내용:** {request['expense_description']}")
                    
                    # 승인 처리 폼
                    st.markdown("---")
                    
                    with st.form(f"expense_approval_{request['approval_id']}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            comments = st.text_area(
                                "승인/반려 사유",
                                placeholder="승인 또는 반려 사유를 입력하세요 (선택사항)",
                                key=f"exp_comments_{request['approval_id']}"
                            )
                        
                        with col2:
                            if st.form_submit_button("✅ 승인", type="primary"):
                                # PostgreSQL 직접 처리
                                conn = psycopg2.connect(
                                    host=st.secrets["postgres"]["host"],
                                    port=st.secrets["postgres"]["port"],
                                    database=st.secrets["postgres"]["database"],
                                    user=st.secrets["postgres"]["user"],
                                    password=st.secrets["postgres"]["password"]
                                )
                                cursor = conn.cursor()

                                # 승인 처리
                                cursor.execute("""
                                    UPDATE expense_approvals 
                                    SET status = %s, 
                                        approver_comments = %s, 
                                        approved_date = CURRENT_TIMESTAMP
                                    WHERE approval_id = %s 
                                    AND approver_id = %s
                                """, ('approved', comments, request['approval_id'], current_user))

                                if cursor.rowcount > 0:
                                    # expense_requests 테이블도 업데이트
                                    cursor.execute("""
                                        UPDATE expense_requests 
                                        SET status = 'approved',
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE id = (
                                            SELECT request_id FROM expense_approvals 
                                            WHERE approval_id = %s
                                        )
                                    """, (request['approval_id'],))
                                    
                                    conn.commit()
                                    success = True
                                    message = "승인이 완료되었습니다."
                                else:
                                    success = False
                                    message = "승인 처리에 실패했습니다."

                                cursor.close()
                                conn.close()
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        
                        with col3:
                            if st.form_submit_button("❌ 반려"):
                                if comments.strip():
                                    # PostgreSQL 직접 처리
                                    conn = psycopg2.connect(
                                        host=st.secrets["postgres"]["host"],
                                        port=st.secrets["postgres"]["port"],
                                        database=st.secrets["postgres"]["database"],
                                        user=st.secrets["postgres"]["user"],
                                        password=st.secrets["postgres"]["password"]
                                    )
                                    cursor = conn.cursor()

                                    # 반려 처리
                                    cursor.execute("""
                                        UPDATE expense_approvals 
                                        SET status = %s, 
                                            approver_comments = %s, 
                                            approved_date = CURRENT_TIMESTAMP
                                        WHERE approval_id = %s 
                                        AND approver_id = %s
                                    """, ('rejected', comments, request['approval_id'], current_user))

                                    if cursor.rowcount > 0:
                                        # expense_requests 테이블도 업데이트
                                        cursor.execute("""
                                            UPDATE expense_requests 
                                            SET status = 'rejected',
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE id = (
                                                SELECT request_id FROM expense_approvals 
                                                WHERE approval_id = %s
                                            )
                                        """, (request['approval_id'],))
                                        
                                        conn.commit()
                                        success = True
                                        message = "반려 처리가 완료되었습니다."
                                    else:
                                        success = False
                                        message = "반려 처리에 실패했습니다."

                                    cursor.close()
                                    conn.close()
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("반려 시 사유를 반드시 입력해주세요.")
        else:
            st.info("💰 지출요청서 승인 대기 건이 없습니다.")
    
    except Exception as e:
        st.error(f"지출요청서 승인 대기 조회 중 오류: {e}")

def show_pending_other_requests(approval_manager, current_user, user_name):
    """기타 승인 대기 항목들을 표시합니다."""
    st.markdown("---")
    st.subheader("📋 기타 승인 대기")
    
    try:
        pending_requests = approval_manager.get_pending_requests()
        
        if len(pending_requests) > 0:
            st.success(f"기타 승인 대기: {len(pending_requests)}건")
            
            for _, request in pending_requests.iterrows():
                with st.expander(f"📄 {request['request_type']} - {request['requester_name']} ({request['request_date'][:10]})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**승인 ID:** {request['approval_id']}")
                        st.write(f"**요청 유형:** {request['request_type']}")
                        st.write(f"**요청자:** {request['requester_name']}")
                        st.write(f"**우선순위:** {request['priority']}")
                    
                    with col2:
                        st.write(f"**요청일:** {request['request_date'][:10]}")
                        st.write(f"**상태:** {request['status']}")
                    
                    st.write(f"**내용:** {request['description']}")
                    
                    # 승인 처리 폼
                    with st.form(f"other_approval_{request['approval_id']}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            reason = st.text_area(
                                "처리 사유",
                                placeholder="승인/거부 사유를 입력하세요",
                                key=f"other_reason_{request['approval_id']}"
                            )
                        
                        with col2:
                            if st.form_submit_button("✅ 승인", type="primary"):
                                success, message = approval_manager.process_approval(
                                    request['approval_id'], 
                                    current_user, 
                                    "승인",
                                    reason
                                )
                                if success:
                                    st.success("승인 완료!")
                                    st.rerun()
                                else:
                                    st.error("승인 처리 중 오류가 발생했습니다.")
                        
                        with col3:
                            if st.form_submit_button("❌ 거부"):
                                if reason.strip():
                                    success, message = approval_manager.process_approval(
                                        request['approval_id'], 
                                        current_user, 
                                        "반려", 
                                        reason
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
        st.error(f"기타 승인 대기 조회 중 오류: {e}")

def show_approval_processing_tab(approval_manager, current_user, user_name):
    """승인 처리 탭을 표시합니다."""
    st.header("✅ 승인 처리")
    
    try:
        from managers.sqlite.sqlite_expense_request_manager import SQLiteExpenseRequestManager
        expense_manager = SQLiteExpenseRequestManager()
        
        # 현재 사용자의 승인 대기 목록 가져오기
        pending_requests = expense_manager.get_pending_approvals(current_user)
        
        if not pending_requests:
            st.info("🎉 처리할 승인 건이 없습니다.")
            return
        
        st.success(f"📋 총 {len(pending_requests)}건의 승인 대기 건이 있습니다.")
        
        # 각 승인 건을 처리
        for i, request in enumerate(pending_requests):
            with st.expander(f"📄 {request.get('expense_title', '제목 없음')} - {request.get('amount', 0):,} {request.get('currency', 'VND')}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**요청자:** {request.get('requester_name', 'N/A')}")
                    st.write(f"**요청일:** {request.get('request_date', 'N/A')}")
                    st.write(f"**지출 목적:** {request.get('expense_description', 'N/A')}")
                    st.write(f"**예상 지출일:** {request.get('expected_date', 'N/A')}")
                    if request.get('notes'):
                        st.write(f"**메모:** {request.get('notes')}")
                
                with col2:
                    st.write(f"**금액:** {request.get('amount', 0):,} {request.get('currency', 'VND')}")
                    st.write(f"**카테고리:** {request.get('category', 'N/A')}")
                    st.write(f"**승인 단계:** {request.get('approval_step', 1)}")
                
                # 승인 처리 버튼
                col_approve, col_reject, col_comment = st.columns([1, 1, 2])
                
                with col_comment:
                    comment_key = f"comment_{request.get('approval_id', i)}"
                    approval_comment = st.text_input(
                        "승인 의견", 
                        key=comment_key,
                        placeholder="승인 또는 반려 사유를 입력하세요"
                    )
                
                with col_approve:
                    approve_key = f"approve_{request.get('approval_id', i)}"
                    if st.button("✅ 승인", key=approve_key, type="primary"):
                        # 승인 처리
                        approval_id = request.get('approval_id')
                        if approval_id:
                            success, message = expense_manager.process_approval(
                                approval_id, current_user, "승인", approval_comment
                            )
                            if success:
                                st.success(f"✅ 승인 완료: {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ 승인 실패: {message}")
                
                with col_reject:
                    reject_key = f"reject_{request.get('approval_id', i)}"
                    if st.button("❌ 반려", key=reject_key):
                        # 반려 처리
                        approval_id = request.get('approval_id')
                        if approval_id:
                            if not approval_comment:
                                st.error("반려 시 사유를 반드시 입력해주세요.")
                            else:
                                success, message = expense_manager.process_approval(
                                    approval_id, current_user, "반려", approval_comment
                                )
                                if success:
                                    st.success(f"✅ 반려 완료: {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ 반려 실패: {message}")
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"승인 처리 중 오류가 발생했습니다: {str(e)}")
        import traceback
        st.write(f"상세 오류: {traceback.format_exc()}")

def show_approval_statistics_tab(approval_manager):
    """승인 통계 탭을 표시합니다."""
    st.header("📊 승인 통계")
    
    try:
        # 임시 통계 (메서드가 없으므로 기본값 제공)
        stats = {'total_requests': 0, 'pending': 0, 'approved': 0, 'rejected': 0}
        
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
        else:
            st.info("승인 통계를 표시할 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"승인 통계 조회 중 오류: {e}")

def show_approval_history_tab(approval_manager, current_user):
    """승인 내역 탭을 표시합니다."""
    st.header("🔍 승인 내역")
    
    try:
        all_requests = approval_manager.get_all_approvals()
        
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
            
            if len(filtered_df) > 0:
                st.success(f"검색 결과: {len(filtered_df)}건")
                
                for _, request in filtered_df.head(20).iterrows():
                    status_color = {
                        'pending': '🟡', 'approved': '✅', 'rejected': '❌',
                        '대기': '🟡', '승인': '✅', '거부': '❌'
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
                            if pd.notna(request.get('approver_name')):
                                st.write(f"**승인자:** {request['approver_name']}")
                            if pd.notna(request.get('approval_date')):
                                st.write(f"**처리일:** {request['approval_date']}")
                        
                        st.write(f"**내용:** {request['description']}")
                        
                        if pd.notna(request.get('reason')):
                            st.write(f"**승인 사유:** {request['reason']}")
                        
                        if pd.notna(request.get('rejection_reason')):
                            st.write(f"**거부 사유:** {request['rejection_reason']}")
            else:
                st.info("검색 조건에 맞는 승인 내역이 없습니다.")
        else:
            st.info("승인 내역이 없습니다.")
    
    except Exception as e:
        st.error(f"승인 내역 조회 중 오류: {e}")

def show_my_requests_tab(approval_manager, current_user, user_name):
    """내 요청 탭을 표시합니다."""
    st.header("📝 내 요청 현황")
    
    try:
        my_requests = approval_manager.get_approvals_by_requester(current_user)
        
        if len(my_requests) > 0:
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
            
            my_requests['request_date'] = pd.to_datetime(my_requests['request_date'])
            my_requests_sorted = my_requests.sort_values('request_date', ascending=False)
            
            for _, request in my_requests_sorted.head(10).iterrows():
                status_color = {
                    'pending': '🟡', 'approved': '✅', 'rejected': '❌',
                    '대기': '🟡', '승인': '✅', '거부': '❌'
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
                        if pd.notna(request.get('approver_name')):
                            st.write(f"**승인자:** {request['approver_name']}")
                        if pd.notna(request.get('approval_date')):
                            st.write(f"**처리일:** {request['approval_date']}")
                    
                    st.write(f"**내용:** {request['description']}")
                    
                    if pd.notna(request.get('reason')):
                        st.write(f"**승인 사유:** {request['reason']}")
                    
                    if pd.notna(request.get('rejection_reason')):
                        st.write(f"**거부 사유:** {request['rejection_reason']}")
        else:
            st.info("요청한 승인이 없습니다.")
    
    except Exception as e:
        st.error(f"내 요청 조회 중 오류: {e}")
