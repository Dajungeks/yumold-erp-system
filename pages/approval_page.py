import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import psycopg2

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
        st.info(f"현재 사용자: {user_name} (ID: {current_user}) - 승인 대기 건수: {len(pending_expense_requests)}건")
        
        st.subheader("💰 지출요청서 승인 대기")
        
        if pending_expense_requests and len(pending_expense_requests) > 0:
            st.success(f"총 {len(pending_expense_requests)}건의 지출요청서 승인 대기")
            
            for request in pending_expense_requests:
                # 날짜 안전 처리
                request_date_str = str(request.get('request_date', 'N/A'))[:10] if request.get('request_date') else 'N/A'
                expected_date_str = str(request.get('expected_date', 'N/A'))[:10] if request.get('expected_date') else 'N/A'
                
                with st.expander(f"🎫 {request['expense_title']} - {request['amount']:,.0f} {request['currency']} ({request_date_str})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**요청번호:** {request['request_id']}")
                        st.write(f"**요청자:** {request['requester_name']}")
                        st.write(f"**카테고리:** {request.get('category', 'N/A')}")
                        st.write(f"**금액:** {request['amount']:,.0f} {request['currency']}")
                    
                    with col2:
                        st.write(f"**승인단계:** {request['approval_step']}")
                        st.write(f"**요청일:** {request_date_str}")
                        st.write(f"**예상지출일:** {expected_date_str}")
                    
                    st.write(f"**지출내용:** {request.get('expense_description', 'N/A')}")
                    
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
                # 날짜 안전 처리
                request_date_str = str(request.get('request_date', 'N/A'))[:10] if request.get('request_date') else 'N/A'
                
                with st.expander(f"📄 {request['request_type']} - {request['requester_name']} ({request_date_str})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**승인 ID:** {request['approval_id']}")
                        st.write(f"**요청 유형:** {request['request_type']}")
                        st.write(f"**요청자:** {request['requester_name']}")
                        st.write(f"**우선순위:** {request['priority']}")
                    
                    with col2:
                        st.write(f"**요청일:** {request_date_str}")
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
                er.expense_title,
                er.total_amount as amount,
                er.currency,
                er.expected_date,
                er.expense_description,
                er.request_date,
                er.employee_name as requester_name,
                er.category,
                er.notes,
                ea.approval_step
            FROM expense_approvals ea
            JOIN expense_requests er ON ea.request_id = er.id
            WHERE ea.approver_id = %s 
            AND ea.status = 'pending'
            ORDER BY ea.created_date ASC
        """, (current_user,))
        
        columns = [desc[0] for desc in cursor.description]
        pending_requests = []
        
        for row in cursor.fetchall():
            request = dict(zip(columns, row))
            pending_requests.append(request)
        
        cursor.close()
        conn.close()
        
        if not pending_requests:
            st.info("🎉 처리할 승인 건이 없습니다.")
            return
        
        st.success(f"📋 총 {len(pending_requests)}건의 승인 대기 건이 있습니다.")
        
        # 각 승인 건을 처리
        for i, request in enumerate(pending_requests):
            with st.expander(f"📄 {request.get('expense_title', '제목 없음')} - {request.get('amount', 0):,.0f} {request.get('currency', 'VND')}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**요청자:** {request.get('requester_name', 'N/A')}")
                    request_date_str = str(request.get('request_date', 'N/A'))[:10] if request.get('request_date') else 'N/A'
                    st.write(f"**요청일:** {request_date_str}")
                    st.write(f"**지출 목적:** {request.get('expense_description', 'N/A')}")
                    expected_date_str = str(request.get('expected_date', 'N/A'))[:10] if request.get('expected_date') else 'N/A'
                    st.write(f"**예상 지출일:** {expected_date_str}")
                    if request.get('notes'):
                        st.write(f"**메모:** {request.get('notes')}")
                
                with col2:
                    st.write(f"**금액:** {request.get('amount', 0):,.0f} {request.get('currency', 'VND')}")
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
                        # PostgreSQL 직접 승인 처리
                        conn = psycopg2.connect(
                            host=st.secrets["postgres"]["host"],
                            port=st.secrets["postgres"]["port"],
                            database=st.secrets["postgres"]["database"],
                            user=st.secrets["postgres"]["user"],
                            password=st.secrets["postgres"]["password"]
                        )
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            UPDATE expense_approvals 
                            SET status = 'approved',
                                approver_comments = %s,
                                approved_date = CURRENT_TIMESTAMP
                            WHERE approval_id = %s
                        """, (approval_comment, request['approval_id']))
                        
                        if cursor.rowcount > 0:
                            cursor.execute("""
                                UPDATE expense_requests 
                                SET status = 'approved'
                                WHERE id = (SELECT request_id FROM expense_approvals WHERE approval_id = %s)
                            """, (request['approval_id'],))
                            conn.commit()
                            st.success("✅ 승인 완료!")
                            st.rerun()
                        else:
                            st.error("❌ 승인 실패!")
                        
                        cursor.close()
                        conn.close()
                
                with col_reject:
                    reject_key = f"reject_{request.get('approval_id', i)}"
                    if st.button("❌ 반려", key=reject_key):
                        if not approval_comment:
                            st.error("반려 시 사유를 반드시 입력해주세요.")
                        else:
                            # PostgreSQL 직접 반려 처리
                            conn = psycopg2.connect(
                                host=st.secrets["postgres"]["host"],
                                port=st.secrets["postgres"]["port"],
                                database=st.secrets["postgres"]["database"],
                                user=st.secrets["postgres"]["user"],
                                password=st.secrets["postgres"]["password"]
                            )
                            cursor = conn.cursor()
                            
                            cursor.execute("""
                                UPDATE expense_approvals 
                                SET status = 'rejected',
                                    approver_comments = %s,
                                    approved_date = CURRENT_TIMESTAMP
                                WHERE approval_id = %s
                            """, (approval_comment, request['approval_id']))
                            
                            if cursor.rowcount > 0:
                                cursor.execute("""
                                    UPDATE expense_requests 
                                    SET status = 'rejected'
                                    WHERE id = (SELECT request_id FROM expense_approvals WHERE approval_id = %s)
                                """, (request['approval_id'],))
                                conn.commit()
                                st.success("✅ 반려 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 반려 실패!")
                            
                            cursor.close()
                            conn.close()
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"승인 처리 중 오류가 발생했습니다: {str(e)}")

def show_approval_statistics_tab(approval_manager):
    """승인 통계 탭을 표시합니다."""
    st.header("📊 승인 통계")
    
    try:
        # PostgreSQL에서 통계 조회
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"]
        )
        cursor = conn.cursor()
        
        # 전체 통계
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
            FROM expense_approvals
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if stats and stats[0] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 요청", f"{stats[0]}건")
            
            with col2:
                approval_rate = (stats[2] / stats[0] * 100) if stats[0] > 0 else 0
                st.metric("승인률", f"{approval_rate:.1f}%")
            
            with col3:
                st.metric("승인 완료", f"{stats[2]}건")
            
            with col4:
                st.metric("대기 중", f"{stats[1]}건")
        else:
            st.info("승인 통계를 표시할 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"승인 통계 조회 중 오류: {e}")

def show_approval_history_tab(approval_manager, current_user):
    """승인 내역 탭을 표시합니다."""
    st.header("🔍 승인 내역")
    
    try:
        # PostgreSQL에서 승인 내역 조회
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
                er.expense_title as request_type,
                er.employee_name as requester_name,
                er.request_date,
                ea.status,
                ea.approver_comments as reason,
                ea.approved_date as approval_date,
                'normal' as priority,
                er.expense_description as description
            FROM expense_approvals ea
            JOIN expense_requests er ON ea.request_id = er.id
            ORDER BY ea.created_date DESC
            LIMIT 100
        """)
        
        columns = [desc[0] for desc in cursor.description]
        all_requests = []
        
        for row in cursor.fetchall():
            request = dict(zip(columns, row))
            all_requests.append(request)
        
        cursor.close()
        conn.close()
        
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
                unique_statuses = df['status'].unique().tolist()
                status_filter = st.selectbox(
                    "상태",
                    options=['전체'] + unique_statuses
                )
            
            # 필터 적용
            if 'request_date' in df.columns:
                df['request_date'] = pd.to_datetime(df['request_date'])
                filtered_df = df[
                    (df['request_date'].dt.date >= start_date) &
                    (df['request_date'].dt.date <= end_date)
                ]
            else:
                filtered_df = df
            
            if status_filter != '전체':
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            if len(filtered_df) > 0:
                st.success(f"검색 결과: {len(filtered_df)}건")
                
                for _, request in filtered_df.head(20).iterrows():
                    status_color = {
                        'pending': '🟡', 'approved': '✅', 'rejected': '❌'
                    }.get(request['status'], '⚪')
                    
                    request_date_str = str(request['request_date'])[:10] if pd.notna(request['request_date']) else 'N/A'
                    
                    with st.expander(f"{status_color} {request['request_type']} - {request['requester_name']} ({request_date_str})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**승인 ID:** {request['approval_id']}")
                            st.write(f"**요청 유형:** {request['request_type']}")
                            st.write(f"**요청자:** {request['requester_name']}")
                            st.write(f"**상태:** {request['status']}")
                        
                        with col2:
                            st.write(f"**요청일:** {request_date_str}")
                            st.write(f"**우선순위:** {request['priority']}")
                            if pd.notna(request.get('approval_date')):
                                approval_date_str = str(request['approval_date'])[:19]
                                st.write(f"**처리일:** {approval_date_str}")
                        
                        st.write(f"**내용:** {request['description']}")
                        
                        if pd.notna(request.get('reason')):
                            st.write(f"**처리 사유:** {request['reason']}")
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
        # PostgreSQL에서 내 요청 조회
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
                er.request_id as approval_id,
                er.expense_title as request_type,
                er.status,
                er.request_date,
                er.expense_description as description,
                'normal' as priority
            FROM expense_requests er
            WHERE er.employee_id = %s
            ORDER BY er.created_at DESC
        """, (current_user,))
        
        columns = [desc[0] for desc in cursor.description]
        my_requests = []
        
        for row in cursor.fetchall():
            request = dict(zip(columns, row))
            my_requests.append(request)
        
        cursor.close()
        conn.close()
        
        if my_requests:
            df = pd.DataFrame(my_requests)
            
            # 상태별 개수
            status_counts = df['status'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 요청", len(my_requests))
            
            with col2:
                st.metric("대기 중", status_counts.get('pending', 0))
            
            with col3:
                st.metric("승인됨", status_counts.get('approved', 0))
            
            with col4:
                st.metric("거부됨", status_counts.get('rejected', 0))
            
            # 최근 요청들
            st.subheader("최근 요청 내역")
            
            for request in my_requests[:10]:
                status_color = {
                    'pending': '🟡', 'approved': '✅', 'rejected': '❌'
                }.get(request['status'], '⚪')
                
                request_date_str = str(request['request_date'])[:10] if request['request_date'] else 'N/A'
                
                with st.expander(f"{status_color} {request['request_type']} ({request_date_str})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**요청 ID:** {request['approval_id']}")
                        st.write(f"**요청 유형:** {request['request_type']}")
                        st.write(f"**상태:** {request['status']}")
                        st.write(f"**우선순위:** {request['priority']}")
                    
                    with col2:
                        st.write(f"**요청일:** {request_date_str}")
                    
                    st.write(f"**내용:** {request['description']}")
        else:
            st.info("요청한 승인이 없습니다.")
    
    except Exception as e:
        st.error(f"내 요청 조회 중 오류: {e}")
