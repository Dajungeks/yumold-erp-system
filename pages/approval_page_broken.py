import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

def show_approval_page(approval_manager, employee_manager, user_permissions, get_text):
    """승인 관리 페이지를 표시합니다."""
    
    st.header("✅ 승인 관리")
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 승인 대기",
        "✅ 승인 처리",
        "📊 승인 통계",
        "🔍 승인 검색",
        "📝 내 요청",
        "📥 승인 내역"
    ])
    
    with tab1:
        st.header("📋 승인 대기 목록")
        
        try:
            # 현재 사용자 정보
            current_user = st.session_state.get('user_id', 'system')
            
            # 지출요청서 승인 대기 목록 추가
            from expense_request_manager import ExpenseRequestManager
            expense_manager = ExpenseRequestManager()
            
            # 현재 사용자의 승인 대기 목록
            pending_expense_requests = expense_manager.get_pending_approvals(current_user)
            
            st.subheader("💰 지출요청서 승인 대기")
            
            if pending_expense_requests:
                st.success(f"총 {len(pending_expense_requests)}건의 지출요청서 승인 대기")
                
                for request in pending_expense_requests:
                    with st.expander(f"🎫 {request['expense_title']} - {request['amount']:,.0f} {request['currency']} ({request['request_date']})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**요청번호:** {request['request_id']}")
                            st.write(f"**요청자:** {request['requester_name']}")
                            st.write(f"**카테고리:** {request['category']}")
                            st.write(f"**금액:** {request['amount']:,.0f} {request['currency']}")
                        
                        with col2:
                            st.write(f"**승인단계:** {request['approval_step']}")
                            st.write(f"**요청일:** {request['request_date']}")
                            st.write(f"**예상지출일:** {request['expected_date']}")
                        
                        st.write(f"**지출내용:** {request['expense_description']}")
                        
                        # 승인 처리
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            comments = st.text_area(
                                "승인/반려 사유",
                                placeholder="승인/반려 사유를 입력하세요 (선택사항)",
                                key=f"ceo_comments_{request['approval_id']}"
                            )
                        
                        with col2:
                            if st.button(f"✅ 승인", key=f"ceo_approve_{request['approval_id']}", type="primary"):
                                success, message = expense_manager.process_approval(
                                    request['approval_id'], 
                                    current_user, 
                                    '승인', 
                                    comments
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        with col3:
                            if st.button(f"❌ 반려", key=f"ceo_reject_{request['approval_id']}", type="secondary"):
                                success, message = expense_manager.process_approval(
                                    request['approval_id'], 
                                    current_user, 
                                    '반려', 
                                    comments
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
            else:
                st.info("지출요청서 승인 대기 건이 없습니다.")
            
            st.markdown("---")
            st.subheader("📋 기타 승인 대기")
            
            # 기존 승인 대기 목록 (다른 유형들)
            try:
                pending_requests = approval_manager.get_pending_requests()
                
                if len(pending_requests) > 0:
                    # 필터링 옵션
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        request_types = ["전체"] + list(pending_requests['request_type'].unique())
                        type_filter = st.selectbox("요청 유형", request_types)
                    
                    with col2:
                        search_term = st.text_input("검색 (요청자, 제목)")
                    
                    with col3:
                        date_range = st.selectbox("기간", ["전체", "오늘", "최근 7일", "최근 30일"])
                    
                    # 필터 적용
                    filtered_requests = pending_requests.copy()
                    
                    if type_filter != "전체":
                        filtered_requests = filtered_requests[filtered_requests['request_type'] == type_filter]
                    
                    if search_term:
                        filtered_requests = filtered_requests[
                            filtered_requests['requester_name'].str.contains(search_term, na=False) |
                            filtered_requests['description'].str.contains(search_term, na=False)
                        ]
                    
                    if date_range != "전체":
                        if date_range == "오늘":
                            today = datetime.now().date()
                            filtered_requests = filtered_requests[
                                pd.to_datetime(filtered_requests['created_date']).dt.date == today
                            ]
                        elif date_range == "최근 7일":
                            week_ago = datetime.now() - timedelta(days=7)
                            filtered_requests = filtered_requests[
                                pd.to_datetime(filtered_requests['created_date']) >= week_ago
                            ]
                        elif date_range == "최근 30일":
                            month_ago = datetime.now() - timedelta(days=30)
                            filtered_requests = filtered_requests[
                                pd.to_datetime(filtered_requests['created_date']) >= month_ago
                            ]
                
                    if len(filtered_requests) > 0:
                        st.success(f"총 {len(filtered_requests)}건의 대기 중인 승인 요청이 있습니다.")
                    else:
                        st.info("조건에 맞는 승인 요청이 없습니다.")
                else:
                    st.info("기타 승인 대기 건이 없습니다.")
                    
            except Exception as e:
                st.error(f"승인 대기 목록 조회 중 오류: {e}")
        
        except Exception as e:
            st.error(f"승인 관리 페이지 로딩 중 오류: {e}")
            
    with tab2:
        st.header("✅ 승인 처리")
        st.info("승인 처리 기능을 구현해주세요.")
    
    with tab3:
        st.header("📊 승인 통계")
        st.info("승인 통계 기능을 구현해주세요.")
    
    with tab4:
        st.header("🔍 승인 검색")
        st.info("승인 검색 기능을 구현해주세요.")
        
    with tab5:
        st.header("📝 내 요청")
        st.info("내 요청 기능을 구현해주세요.")
        
    with tab6:
        st.header("📥 승인 내역")
        st.info("승인 내역 기능을 구현해주세요.")
                    total_items = len(filtered_requests)
                    total_pages = (total_items - 1) // items_per_page + 1
                    
                    if total_pages > 1:
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            page = st.selectbox(
                                "페이지 선택",
                                range(1, total_pages + 1),
                                format_func=lambda x: f"페이지 {x} / {total_pages}"
                            )
                        
                        start_idx = (page - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, total_items)
                        page_requests = filtered_requests.iloc[start_idx:end_idx]
                    else:
                        page_requests = filtered_requests
                    
                    # 승인 요청 카드 표시
                    for _, request in page_requests.iterrows():
                        with st.expander(f"🔔 {request['description']} - {request['requester_name']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**요청 유형:**", request['request_type'])
                                st.write("**요청자:**", request['requester_name'])
                                st.write("**생성일:**", request['created_date'])
                                st.write("**우선순위:**", request.get('priority', '보통'))
                            
                            with col2:
                                st.write("**승인자:**", request.get('approver_name', '미지정'))
                                st.write("**상태:**", request['status'])
                                if request.get('deadline'):
                                    st.write("**마감일:**", request['deadline'])
                            
                            if request.get('description'):
                                st.write("**설명:**", request['description'])
                            
                            # 승인/거부 버튼
                            if user_permissions.get('can_approve_requests', False):
                                col1, col2, col3 = st.columns(3)
                                
                                approval_key = f"approve_{request['approval_id']}"
                                rejection_key = f"reject_{request['approval_id']}"
                                
                                with col1:
                                    if st.button("✅ 승인", key=approval_key):
                                        try:
                                            success = approval_manager.approve_request(
                                                request['approval_id'],
                                                current_user,
                                                employee_manager.get_employee_name(current_user)
                                            )
                                            if success:
                                                st.success("승인이 완료되었습니다!")
                                                st.rerun()
                                            else:
                                                st.error("승인 처리에 실패했습니다.")
                                        except Exception as e:
                                            st.error(f"승인 처리 중 오류가 발생했습니다: {e}")
                                
                                with col2:
                                    if st.button("❌ 거부", key=rejection_key):
                                        st.session_state[f'rejecting_{request["approval_id"]}'] = True
                                
                                # 거부 사유 입력
                                if st.session_state.get(f'rejecting_{request["approval_id"]}', False):
                                    rejection_reason = st.text_area(
                                        "거부 사유를 입력해주세요:", 
                                        key=f"reason_{request['approval_id']}"
                                    )
                                    
                                    col_confirm, col_cancel = st.columns(2)
                                    with col_confirm:
                                        if st.button("거부 확인", key=f"confirm_reject_{request['approval_id']}"):
                                            if rejection_reason.strip():
                                                try:
                                                    success = approval_manager.reject_request(
                                                        request['approval_id'],
                                                        current_user,
                                                        rejection_reason,
                                                        employee_manager.get_employee_name(current_user)
                                                    )
                                                    if success:
                                                        st.success("거부가 완료되었습니다!")
                                                        st.rerun()
                                                    else:
                                                        st.error("거부 처리에 실패했습니다.")
                                                except Exception as e:
                                                    st.error(f"거부 처리 중 오류가 발생했습니다: {e}")
                                            else:
                                                st.error("거부 사유를 입력해주세요.")
                                    
                                    with col_cancel:
                                        if st.button("취소", key=f"cancel_reject_{request['approval_id']}"):
                                            st.session_state[f'rejecting_{request["approval_id"]}'] = False
                                            st.rerun()
                            else:
                                st.info("승인 권한이 없습니다.")
                
                else:
                    st.warning("필터 조건에 맞는 승인 요청이 없습니다.")
            
            else:
                st.info("현재 대기 중인 승인 요청이 없습니다.")
                
        except Exception as e:
            st.error(f"승인 대기 목록을 불러오는 중 오류가 발생했습니다: {e}")
    
    with tab2:
        st.header("✅ 승인 처리")
        
        # 빠른 승인 처리
        try:
            recent_requests = approval_manager.get_recent_requests(days=7)
            
            if len(recent_requests) > 0:
                st.subheader("최근 7일 승인 요청")
                
                # 상태별 분류
                pending = recent_requests[recent_requests['status'] == 'pending']
                approved = recent_requests[recent_requests['status'] == 'approved']
                rejected = recent_requests[recent_requests['status'] == 'rejected']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("대기 중", len(pending))
                    if len(pending) > 0:
                        st.dataframe(
                            pending[['description', 'requester_name', 'request_date']].head(5),
                            use_container_width=True
                        )
                
                with col2:
                    st.metric("승인됨", len(approved))
                    if len(approved) > 0:
                        st.dataframe(
                            approved[['description', 'requester_name', 'approval_date']].head(5),
                            use_container_width=True
                        )
                
                with col3:
                    st.metric("거부됨", len(rejected))
                    if len(rejected) > 0:
                        st.dataframe(
                            rejected[['description', 'requester_name', 'approval_date']].head(5),
                            use_container_width=True
                        )
                
                # 일괄 처리 옵션
                if user_permissions.get('can_approve_requests', False) and len(pending) > 0:
                    st.subheader("일괄 처리")
                    
                    # 선택 가능한 대기 요청들
                    selected_requests = st.multiselect(
                        "일괄 처리할 요청 선택",
                        options=pending['approval_id'].tolist(),
                        format_func=lambda x: f"{pending[pending['approval_id'] == x]['request_title'].iloc[0]} - {pending[pending['approval_id'] == x]['requester_name'].iloc[0]}"
                    )
                    
                    if selected_requests:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("선택한 요청 일괄 승인"):
                                try:
                                    current_user = st.session_state.get('user_id', 'system')
                                    approver_name = employee_manager.get_employee_name(current_user)
                                    
                                    success_count = 0
                                    for approval_id in selected_requests:
                                        if approval_manager.approve_request(approval_id, current_user, approver_name):
                                            success_count += 1
                                    
                                    st.success(f"{success_count}/{len(selected_requests)}건의 요청이 승인되었습니다!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"일괄 승인 중 오류가 발생했습니다: {e}")
                        
                        with col2:
                            if st.button("선택한 요청 일괄 거부"):
                                rejection_reason = st.text_input("일괄 거부 사유")
                                if rejection_reason:
                                    try:
                                        current_user = st.session_state.get('user_id', 'system')
                                        approver_name = employee_manager.get_employee_name(current_user)
                                        
                                        success_count = 0
                                        for approval_id in selected_requests:
                                            if approval_manager.reject_request(approval_id, current_user, rejection_reason, approver_name):
                                                success_count += 1
                                        
                                        st.success(f"{success_count}/{len(selected_requests)}건의 요청이 거부되었습니다!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"일괄 거부 중 오류가 발생했습니다: {e}")
                                else:
                                    st.warning("거부 사유를 입력해주세요.")
                
            else:
                st.info("최근 7일간 승인 요청이 없습니다.")
                
        except Exception as e:
            st.error(f"승인 처리 정보를 불러오는 중 오류가 발생했습니다: {e}")
    
    with tab3:
        st.header("📊 승인 통계")
        
        try:
            stats = approval_manager.get_approval_statistics()
            
            if stats:
                # 기본 통계
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("총 요청 수", stats['total_requests'])
                
                with col2:
                    approval_rate = (stats['approved_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
                    st.metric("승인율", f"{approval_rate:.1f}%")
                
                with col3:
                    st.metric("대기 중", stats['pending_requests'])
                
                with col4:
                    rejection_rate = (stats['rejected_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
                    st.metric("거부율", f"{rejection_rate:.1f}%")
                
                # 상태별 분포 차트
                st.subheader("승인 상태별 분포")
                
                status_data = {
                    '대기 중': stats['pending_requests'],
                    '승인됨': stats['approved_requests'],
                    '거부됨': stats['rejected_requests']
                }
                
                if sum(status_data.values()) > 0:
                    fig_pie = px.pie(
                        values=list(status_data.values()),
                        names=list(status_data.keys()),
                        title="승인 상태별 분포"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # 월별 승인 추이
                st.subheader("월별 승인 처리 추이")
                
                all_requests = approval_manager.get_all_requests()
                if len(all_requests) > 0:
                    all_requests['created_date'] = pd.to_datetime(all_requests['created_date'])
                    monthly_stats = all_requests.groupby([
                        all_requests['created_date'].dt.to_period('M'),
                        'status'
                    ]).size().reset_index(name='count')
                    
                    if len(monthly_stats) > 0:
                        monthly_stats['period'] = monthly_stats['created_date'].astype(str)
                        
                        fig_bar = px.bar(
                            monthly_stats,
                            x='period',
                            y='count',
                            color='status',
                            title="월별 승인 처리 현황",
                            labels={'period': '월', 'count': '건수', 'status': '상태'}
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                
                # 요청 유형별 통계
                st.subheader("요청 유형별 통계")
                
                if len(all_requests) > 0:
                    type_stats = all_requests.groupby('request_type')['status'].value_counts().reset_index(name='count')
                    
                    if len(type_stats) > 0:
                        fig_type = px.bar(
                            type_stats,
                            x='request_type',
                            y='count',
                            color='status',
                            title="요청 유형별 처리 현황",
                            labels={'request_type': '요청 유형', 'count': '건수', 'status': '상태'}
                        )
                        st.plotly_chart(fig_type, use_container_width=True)
                
            else:
                st.warning("승인 통계 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"승인 통계를 불러오는 중 오류가 발생했습니다: {e}")
    
    with tab4:
        st.header("🔍 승인 검색")
        
        # 고급 검색 옵션
        with st.expander("검색 조건", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # 기본 검색 조건
                approval_id_search = st.text_input("승인 ID")
                requester_search = st.text_input("요청자명")
                title_search = st.text_input("요청 제목")
            
            with col2:
                # 고급 검색 조건
                status_search = st.multiselect("상태", ["pending", "approved", "rejected"])
                type_search = st.multiselect("요청 유형", ["vacation", "quotation", "purchase_order", "personal_info"])
                
                # 날짜 범위
                date_from = st.date_input("시작 날짜", value=datetime.now() - timedelta(days=30))
                date_to = st.date_input("종료 날짜", value=datetime.now())
            
            if st.button("검색 실행"):
                try:
                    all_requests = approval_manager.get_all_requests()
                    
                    # 필터 적용
                    filtered_requests = all_requests.copy()
                    
                    if approval_id_search:
                        filtered_requests = filtered_requests[
                            filtered_requests['approval_id'].str.contains(approval_id_search, na=False)
                        ]
                    
                    if requester_search:
                        filtered_requests = filtered_requests[
                            filtered_requests['requester_name'].str.contains(requester_search, na=False)
                        ]
                    
                    if title_search:
                        filtered_requests = filtered_requests[
                            filtered_requests['description'].str.contains(title_search, na=False)
                        ]
                    
                    if status_search:
                        filtered_requests = filtered_requests[filtered_requests['status'].isin(status_search)]
                    
                    if type_search:
                        filtered_requests = filtered_requests[filtered_requests['request_type'].isin(type_search)]
                    
                    # 날짜 필터
                    filtered_requests['created_date'] = pd.to_datetime(filtered_requests['created_date'])
                    filtered_requests = filtered_requests[
                        (filtered_requests['created_date'].dt.date >= date_from) &
                        (filtered_requests['created_date'].dt.date <= date_to)
                    ]
                    
                    if len(filtered_requests) > 0:
                        st.success(f"검색 결과: {len(filtered_requests)}건")
                        
                        # 검색 결과 표시
                        display_columns = [
                            'approval_id', 'request_title', 'requester_name', 'request_type', 
                            'status', 'created_date'
                        ]
                        
                        column_mapping = {
                            'approval_id': '승인ID',
                            'request_title': '요청제목',
                            'requester_name': '요청자',
                            'request_type': '요청유형',
                            'status': '상태',
                            'created_date': '생성일'
                        }
                        
                        # 페이지네이션
                        items_per_page = 20
                        total_items = len(filtered_requests)
                        total_pages = (total_items - 1) // items_per_page + 1
                        
                        if total_pages > 1:
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                page = st.selectbox(
                                    "페이지 선택",
                                    range(1, total_pages + 1),
                                    format_func=lambda x: f"페이지 {x} / {total_pages}"
                                )
                            
                            start_idx = (page - 1) * items_per_page
                            end_idx = min(start_idx + items_per_page, total_items)
                            page_data = filtered_requests.iloc[start_idx:end_idx]
                        else:
                            page_data = filtered_requests
                        
                        st.dataframe(
                            page_data[display_columns].rename(columns=column_mapping),
                            use_container_width=True
                        )
                        
                        # 다운로드 버튼
                        csv_data = filtered_requests.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 검색 결과 다운로드 (CSV)",
                            data=csv_data,
                            file_name=f"approval_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.warning("검색 조건에 맞는 승인 요청이 없습니다.")
                        
                except Exception as e:
                    st.error(f"검색 중 오류가 발생했습니다: {e}")
    
    with tab5:
        st.header("📝 내 요청")
        
        try:
            current_user = st.session_state.get('user_id', 'system')
            my_requests = approval_manager.get_requests_by_requester(current_user)
            
            if len(my_requests) > 0:
                # 상태별 필터
                status_filter = st.selectbox("상태 필터", ["전체", "pending", "approved", "rejected"])
                
                if status_filter != "전체":
                    filtered_requests = my_requests[my_requests['status'] == status_filter]
                else:
                    filtered_requests = my_requests
                
                if len(filtered_requests) > 0:
                    # 내 요청 통계
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_requests = len(my_requests)
                        st.metric("총 요청", total_requests)
                    
                    with col2:
                        pending_count = len(my_requests[my_requests['status'] == 'pending'])
                        st.metric("대기 중", pending_count)
                    
                    with col3:
                        approved_count = len(my_requests[my_requests['status'] == 'approved'])
                        approval_rate = (approved_count / total_requests * 100) if total_requests > 0 else 0
                        st.metric("승인률", f"{approval_rate:.1f}%")
                    
                    with col4:
                        rejected_count = len(my_requests[my_requests['status'] == 'rejected'])
                        st.metric("거부됨", rejected_count)
                    
                    # 요청 목록
                    st.subheader("내 요청 목록")
                    
                    for _, request in filtered_requests.iterrows():
                        status_emoji = {
                            'pending': '⏳',
                            'approved': '✅',
                            'rejected': '❌'
                        }.get(request['status'], '❓')
                        
                        with st.expander(f"{status_emoji} {request['request_title']} - {request['status']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**요청 유형:**", request['request_type'])
                                st.write("**생성일:**", request['created_date'])
                                st.write("**상태:**", request['status'])
                            
                            with col2:
                                if request.get('approver_name'):
                                    st.write("**승인자:**", request['approver_name'])
                                if request.get('approved_date'):
                                    st.write("**승인일:**", request['approved_date'])
                                if request.get('rejected_date'):
                                    st.write("**거부일:**", request['rejected_date'])
                            
                            if request.get('description'):
                                st.write("**설명:**", request['description'])
                            
                            if request.get('rejection_reason'):
                                st.error(f"**거부 사유:** {request['rejection_reason']}")
                            
                            if request.get('approval_notes'):
                                st.info(f"**승인자 메모:** {request['approval_notes']}")
                
                else:
                    st.warning("선택한 상태의 요청이 없습니다.")
            
            else:
                st.info("아직 등록한 승인 요청이 없습니다.")
                
        except Exception as e:
            st.error(f"내 요청을 불러오는 중 오류가 발생했습니다: {e}")
    
    with tab6:
        st.header("📥 승인 내역")
        
        # 다운로드 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            download_type = st.selectbox(
                "다운로드 유형",
                ["전체 승인 내역", "승인된 요청만", "거부된 요청만", "내 요청만", "날짜 범위"]
            )
        
        with col2:
            file_format = st.selectbox("파일 형식", ["CSV", "Excel"])
        
        # 날짜 범위 설정 (날짜 범위 선택 시)
        if download_type == "날짜 범위":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("시작 날짜", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("종료 날짜", value=datetime.now())
        
        if st.button("다운로드 실행"):
            try:
                # 데이터 가져오기
                if download_type == "전체 승인 내역":
                    data = approval_manager.get_all_requests()
                    filename = f"all_approvals_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                elif download_type == "승인된 요청만":
                    data = approval_manager.get_all_requests()
                    data = data[data['status'] == 'approved']
                    filename = f"approved_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                elif download_type == "거부된 요청만":
                    data = approval_manager.get_all_requests()
                    data = data[data['status'] == 'rejected']
                    filename = f"rejected_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                elif download_type == "내 요청만":
                    current_user = st.session_state.get('user_id', 'system')
                    data = approval_manager.get_requests_by_requester(current_user)
                    filename = f"my_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                else:  # 날짜 범위
                    data = approval_manager.get_all_requests()
                    data['created_date'] = pd.to_datetime(data['created_date'])
                    data = data[
                        (data['created_date'].dt.date >= start_date) &
                        (data['created_date'].dt.date <= end_date)
                    ]
                    filename = f"approvals_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                if len(data) > 0:
                    if file_format == "CSV":
                        csv_data = data.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 CSV 다운로드",
                            data=csv_data,
                            file_name=f"{filename}.csv",
                            mime="text/csv"
                        )
                    
                    else:  # Excel
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            data.to_excel(writer, sheet_name='승인내역', index=False)
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label="📥 Excel 다운로드",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    st.success(f"총 {len(data)}건의 승인 내역을 다운로드할 수 있습니다.")
                    
                    # 미리보기
                    st.subheader("데이터 미리보기")
                    st.dataframe(data.head(10), use_container_width=True)
                    
                else:
                    st.warning("선택한 조건에 맞는 승인 내역이 없습니다.")
                    
            except Exception as e:
                st.error(f"다운로드 중 오류가 발생했습니다: {e}")