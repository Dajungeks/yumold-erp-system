"""
현금 흐름 관리 페이지 - 완전한 현금 흐름 추적 및 관리 시스템
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from notification_helper import NotificationHelper
import os

def show_cash_flow_management_page(managers, selected_submenu, get_text, hide_header=False):
    """현금 흐름 관리 메인 페이지"""
    
    if not hide_header:
        st.header(f"💰 {get_text('cash_flow_management')}")
        st.caption(get_text('cash_flow_management_desc'))
    
    # 매니저들 가져오기
    if managers is None:
        managers = {}
    cash_flow_manager = managers.get('cash_flow_manager')
    quotation_manager = managers.get('quotation_manager')
    invoice_manager = managers.get('invoice_manager')
    purchase_order_manager = managers.get('purchase_order_manager')
    
    if not cash_flow_manager:
        st.error(get_text('cash_flow_manager_load_error'))
        return
    
    # 알림 헬퍼 초기화
    notification = NotificationHelper()
    
    # 7개 탭 구성
    tabs = st.tabs([
        f"🏠 {get_text('cash_flow_status')}", 
        f"💰 {get_text('transaction_history')}", 
        f"📊 {get_text('chart_analysis')}", 
        f"📈 {get_text('statistics_analysis')}", 
        f"⚙️ {get_text('transaction_registration')}", 
        f"💳 {get_text('account_management')}",
        f"🧹 {get_text('data_management')}"
    ])
    
    with tabs[0]:  # 현금 흐름 현황
        show_cash_flow_overview(cash_flow_manager, notification, get_text)
    
    with tabs[1]:  # 거래 내역
        show_transaction_history(cash_flow_manager, notification, get_text)
    
    with tabs[2]:  # 차트 분석
        show_cash_flow_charts(cash_flow_manager, get_text)
    
    with tabs[3]:  # 통계 분석
        show_cash_flow_statistics(cash_flow_manager, get_text)
    
    with tabs[4]:  # 거래 등록
        show_transaction_registration(cash_flow_manager, quotation_manager, purchase_order_manager, notification, get_text)
    
    with tabs[5]:  # 계좌 관리
        show_account_management(cash_flow_manager, notification, get_text)
    
    with tabs[6]:  # 데이터 관리
        show_data_management(cash_flow_manager, quotation_manager, purchase_order_manager, notification, get_text)

def show_cash_flow_overview(cash_flow_manager, notification, get_text=None):
    """현금 흐름 현황 탭"""
    if get_text is None:
        get_text = lambda key: key
    st.subheader(f"💳 {get_text('cash_flow_status')}")
    
    # 실제 데이터 동기화 버튼
    col_sync1, col_sync2 = st.columns(2)
    
    with col_sync1:
        if st.button(f"🔄 {get_text('real_data_sync')}", type="primary"):
            # 견적서, 구매주문 등 실제 데이터와 동기화
            try:
                from quotation_manager import QuotationManager
                from purchase_order_manager import PurchaseOrderManager
                
                quotation_manager = QuotationManager()
                purchase_order_manager = PurchaseOrderManager()
                
                sync_results = cash_flow_manager.auto_sync_all_data(
                    quotation_manager=quotation_manager,
                    purchase_order_manager=purchase_order_manager
                )
                
                success_count = sum(1 for _, result in sync_results if result)
                st.success(f"✅ 데이터 동기화 완료! ({success_count}/{len(sync_results)} 성공)")
                st.rerun()
            except Exception as e:
                st.error(f"동기화 중 오류: {str(e)}")
    
    with col_sync2:
        st.caption("승인된 견적서를 수입으로, 구매주문을 지출로 자동 기록합니다")
    
    st.divider()
    
    # 현금 흐름 요약 정보 가져오기
    try:
        summary = cash_flow_manager.get_cash_flow_summary()
        
        # 메트릭 카드 (4개 컬럼)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_income = summary.get('total_income', 0)
            st.success("**💰 수입**")
            st.metric("총 수입", f"${total_income:,.2f}")
        
        with col2:
            total_expense = summary.get('total_expense', 0)
            st.error("**💸 지출**")
            st.metric("총 지출", f"${total_expense:,.2f}")
        
        with col3:
            net_income = total_income - total_expense
            st.info("**📊 순익**")
            if net_income >= 0:
                st.metric("순익", f"${net_income:,.2f}", delta=f"{net_income:,.2f}")
            else:
                st.metric("순손실", f"${abs(net_income):,.2f}", delta=f"-{abs(net_income):,.2f}")
        
        with col4:
            current_balance = summary.get('current_balance', 0)
            st.warning("**🏦 잔고**")
            st.metric("현재 잔고", f"${current_balance:,.2f}")
        
        st.markdown("---")
        
        # 월별 현금 흐름
        st.subheader("📅 월별 현금 흐름")
        monthly_data = cash_flow_manager.get_monthly_cash_flow()
        
        if len(monthly_data) > 0:
            # 이미 딕셔너리 리스트이므로 그대로 DataFrame으로 변환
            monthly_df = pd.DataFrame(monthly_data)
            
            # 월별 차트
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='수입',
                x=monthly_df['month'],
                y=monthly_df['income'],
                marker_color='green',
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                name='지출',
                x=monthly_df['month'],
                y=monthly_df['expense'],
                marker_color='red',
                opacity=0.7
            ))
            
            fig.update_layout(
                title='월별 수입/지출 비교',
                xaxis_title='월',
                yaxis_title='금액 (USD)',
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("표시할 월별 데이터가 없습니다.")
            
        # 최근 거래 내역 (5건)
        st.subheader("📋 최근 거래 내역")
        recent_transactions = cash_flow_manager.get_all_transactions()
        
        if len(recent_transactions) > 0:
            # 최근 5건만 표시
            # 딕셔너리 리스트 처리
            if isinstance(recent_transactions, list) and len(recent_transactions) > 0:
                recent_5 = recent_transactions[:5]  # 최신 5개만 선택
            else:
                recent_5 = []
            
            for transaction in recent_5:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    transaction_type = transaction.get('transaction_type', 'N/A')
                    description = transaction.get('description', 'N/A')
                    st.markdown(f"**{description}**")
                    st.caption(f"유형: {transaction_type}")
                
                with col2:
                    amount = float(transaction.get('amount', 0))
                    if transaction_type == 'income':
                        st.success(f"+${amount:,.2f}")
                    else:
                        st.error(f"-${amount:,.2f}")
                
                with col3:
                    transaction_date = transaction.get('transaction_date', 'N/A')
                    st.caption(f"날짜: {transaction_date[:10]}")
                
                with col4:
                    status = transaction.get('status', 'N/A')
                    if status == 'completed':
                        st.success("✅ 완료")
                    elif status == 'pending':
                        st.warning("🕐 대기")
                    else:
                        st.info(f"📋 {status}")
                
                st.divider()
        else:
            st.info("등록된 거래 내역이 없습니다.")
            
    except Exception as e:
        st.error(f"현금 흐름 현황 로드 중 오류: {str(e)}")

def show_transaction_history(cash_flow_manager, notification, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """거래 내역 탭"""
    st.subheader("📊 거래 내역")
    
    # 필터링 옵션
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        transaction_type_filter = st.selectbox(
            "거래 유형",
            ["전체", "income", "expense"],
            format_func=lambda x: {"전체": "전체", "income": "수입", "expense": "지출"}.get(x, x)
        )
    
    with col2:
        status_filter = st.selectbox(
            "상태",
            ["전체", "completed", "pending", "cancelled"],
            format_func=lambda x: {"전체": "전체", "completed": "완료", "pending": "대기", "cancelled": "취소"}.get(x, x)
        )
    
    with col3:
        start_date = st.date_input(
            "시작일",
            value=datetime.now().date() - timedelta(days=30)
        )
    
    with col4:
        end_date = st.date_input(
            "종료일",
            value=datetime.now().date()
        )
    
    # 거래 내역 가져오기
    try:
        all_transactions = cash_flow_manager.get_all_transactions()
        
        if len(all_transactions) > 0:
            # 딕셔너리 리스트 필터링
            filtered_transactions = []
            
            for transaction in all_transactions:
                # 거래 유형 필터
                if transaction_type_filter != "전체" and transaction.get('transaction_type') != transaction_type_filter:
                    continue
                
                # 상태 필터  
                if status_filter != "전체" and transaction.get('status') != status_filter:
                    continue
                
                # 날짜 필터
                try:
                    transaction_date_str = transaction.get('transaction_date', '')
                    if transaction_date_str:
                        # 날짜 형식에 맞게 파싱
                        transaction_date = datetime.strptime(transaction_date_str[:10], '%Y-%m-%d').date()
                        if not (start_date <= transaction_date <= end_date):
                            continue
                    else:
                        continue
                except:
                    continue
                
                filtered_transactions.append(transaction)
            
            if len(filtered_transactions) > 0:
                st.success(f"총 {len(filtered_transactions)}건의 거래가 조회되었습니다.")
                
                # 거래 목록 표시
                for idx, transaction in enumerate(filtered_transactions):
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{transaction.get('description', 'N/A')}**")
                            st.caption(f"ID: {transaction.get('transaction_id', 'N/A')}")
                            ref_type = transaction.get('reference_type', 'N/A')
                            ref_id = transaction.get('reference_id', 'N/A')
                            if ref_type != 'N/A' and ref_id != 'N/A':
                                st.caption(f"참조: {ref_type} - {ref_id}")
                        
                        with col2:
                            transaction_type = transaction.get('transaction_type', 'N/A')
                            amount = float(transaction.get('amount', 0))
                            currency = transaction.get('currency', 'USD')
                            
                            if transaction_type == 'income':
                                st.success(f"+{amount:,.2f} {currency}")
                            else:
                                st.error(f"-{amount:,.2f} {currency}")
                        
                        with col3:
                            transaction_date = transaction.get('transaction_date', 'N/A')
                            st.caption(f"날짜: {transaction_date[:10]}")
                        
                        with col4:
                            status = transaction.get('status', 'N/A')
                            if status == 'completed':
                                st.success("✅ 완료")
                            elif status == 'pending':
                                st.warning("🕐 대기")
                            elif status == 'cancelled':
                                st.error("❌ 취소")
                            else:
                                st.info(f"📋 {status}")
                        
                        with col5:
                            account = transaction.get('account', 'N/A')
                            st.caption(f"계좌: {account}")
                            created_by = transaction.get('created_by', 'N/A')
                            st.caption(f"등록자: {created_by}")
                        
                        with col6:
                            # 수정/삭제 버튼
                            col_edit, col_delete = st.columns(2)
                            
                            with col_edit:
                                if st.button(f"✏️", key=f"edit_transaction_{idx}", help="수정"):
                                    st.session_state.edit_transaction_data = transaction
                                    st.rerun()
                            
                            with col_delete:
                                if st.button(f"🗑️", key=f"delete_transaction_{idx}", help="삭제"):
                                    if cash_flow_manager.delete_transaction(transaction.get('transaction_id')):
                                        st.success("거래가 삭제되었습니다!")
                                        st.rerun()
                                    else:
                                        st.error("거래 삭제에 실패했습니다.")
                        
                        st.divider()
                
                # 다운로드 버튼
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    # 리스트를 DataFrame으로 변환한 후 CSV 생성
                    if filtered_transactions:
                        df_for_csv = pd.DataFrame(filtered_transactions)
                        csv_data = df_for_csv.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 CSV 다운로드",
                            data=csv_data,
                            file_name=f"cash_flow_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    # 요약 통계 - 딕셔너리 리스트로 계산
                    total_income = sum(float(t.get('amount', 0)) for t in filtered_transactions if t.get('transaction_type') == 'income')
                    total_expense = sum(float(t.get('amount', 0)) for t in filtered_transactions if t.get('transaction_type') == 'expense')
                    net_amount = total_income - total_expense
                    
                    st.info(f"수입: ${total_income:,.2f} | 지출: ${total_expense:,.2f} | 순액: ${net_amount:,.2f}")
            
            else:
                st.warning("필터 조건에 맞는 거래가 없습니다.")
        
        else:
            st.info("등록된 거래 내역이 없습니다.")
            
    except Exception as e:
        st.error(f"거래 내역 로드 중 오류: {str(e)}")
    
    # 거래 수정 모달
    if st.session_state.get('edit_transaction_data'):
        show_edit_transaction_modal(cash_flow_manager, notification)

def show_cash_flow_charts(cash_flow_manager, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """차트 분석 탭"""
    st.subheader("📈 현금 흐름 차트 분석")
    
    try:
        all_transactions = cash_flow_manager.get_all_transactions()
        
        if len(all_transactions) > 0:
            # 딕셔너리 리스트를 DataFrame으로 변환
            if isinstance(all_transactions, list):
                all_transactions = pd.DataFrame(all_transactions)
            # 이미 DataFrame인 경우 그대로 사용
            
            # 1. 거래 유형별 파이 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 거래 유형별 분포")
                type_counts = all_transactions['transaction_type'].value_counts()
                
                fig_pie = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="거래 유형별 건수",
                    color_discrete_map={'income': 'green', 'expense': 'red'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("#### 거래 상태별 분포")
                status_counts = all_transactions['status'].value_counts()
                
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="거래 상태별 건수"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            # 2. 일별 현금 흐름 트렌드
            st.markdown("#### 📅 일별 현금 흐름 트렌드")
            
            # 날짜별 그룹화 - 날짜 형식 수정
            all_transactions['transaction_date'] = pd.to_datetime(all_transactions['transaction_date'], format='%Y-%m-%d', errors='coerce')
            all_transactions = all_transactions.dropna(subset=['transaction_date'])
            all_transactions['date'] = all_transactions['transaction_date'].dt.date
            
            daily_summary = all_transactions.groupby(['date', 'transaction_type']).agg({
                'amount': 'sum'
            }).reset_index()
            
            # 피벗 테이블 생성
            daily_pivot = daily_summary.pivot(index='date', columns='transaction_type', values='amount').fillna(0)
            daily_pivot = daily_pivot.reset_index()
            
            # 순 현금 흐름 계산
            if 'income' in daily_pivot.columns and 'expense' in daily_pivot.columns:
                daily_pivot['net_flow'] = daily_pivot['income'] - daily_pivot['expense']
            elif 'income' in daily_pivot.columns:
                daily_pivot['net_flow'] = daily_pivot['income']
                daily_pivot['expense'] = 0
            elif 'expense' in daily_pivot.columns:
                daily_pivot['net_flow'] = -daily_pivot['expense']
                daily_pivot['income'] = 0
            else:
                daily_pivot['net_flow'] = 0
                daily_pivot['income'] = 0
                daily_pivot['expense'] = 0
            
            # 트렌드 차트
            fig_trend = go.Figure()
            
            if 'income' in daily_pivot.columns:
                fig_trend.add_trace(go.Scatter(
                    x=daily_pivot['date'],
                    y=daily_pivot['income'],
                    mode='lines+markers',
                    name='수입',
                    line=dict(color='green'),
                    fill='tonexty'
                ))
            
            if 'expense' in daily_pivot.columns:
                fig_trend.add_trace(go.Scatter(
                    x=daily_pivot['date'],
                    y=daily_pivot['expense'],
                    mode='lines+markers',
                    name='지출',
                    line=dict(color='red'),
                    fill='tonexty'
                ))
            
            fig_trend.add_trace(go.Scatter(
                x=daily_pivot['date'],
                y=daily_pivot['net_flow'],
                mode='lines+markers',
                name='순 현금 흐름',
                line=dict(color='blue', width=3)
            ))
            
            fig_trend.update_layout(
                title='일별 현금 흐름 트렌드',
                xaxis_title='날짜',
                yaxis_title='금액 (USD)',
                height=500
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # 3. 계좌별 분포
            st.markdown("#### 🏦 계좌별 거래 분포")
            
            account_summary = all_transactions.groupby('account').agg({
                'amount': 'sum',
                'transaction_id': 'count'
            }).reset_index()
            account_summary.columns = ['계좌', '총 금액', '거래 건수']
            
            fig_account = px.bar(
                account_summary,
                x='계좌',
                y='총 금액',
                title='계좌별 총 거래 금액',
                text='거래 건수'
            )
            fig_account.update_traces(texttemplate='%{text}건', textposition='outside')
            
            st.plotly_chart(fig_account, use_container_width=True)
            
        else:
            st.info("차트를 생성할 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"차트 생성 중 오류: {str(e)}")

def show_cash_flow_statistics(cash_flow_manager, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """통계 분석 탭"""
    st.subheader("📊 현금 흐름 통계 분석")
    
    try:
        all_transactions = cash_flow_manager.get_all_transactions()
        
        if len(all_transactions) > 0:
            # 딕셔너리 리스트를 DataFrame으로 변환
            df = pd.DataFrame(all_transactions)
            
            # 기본 통계
            st.markdown("### 📈 기본 통계")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_transactions = len(df)
                st.metric("총 거래 건수", f"{total_transactions:,}건")
            
            with col2:
                income_transactions = len(df[df['transaction_type'] == 'income'])
                st.metric("수입 거래", f"{income_transactions:,}건")
            
            with col3:
                expense_transactions = len(df[df['transaction_type'] == 'expense'])
                st.metric("지출 거래", f"{expense_transactions:,}건")
            
            with col4:
                avg_amount = df['amount'].astype(float).mean()
                st.metric("평균 거래액", f"${avg_amount:,.2f}")
            
            st.markdown("---")
            
            # 상세 통계 표
            st.markdown("### 📋 상세 통계")
            
            # 거래 유형별 통계
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💰 수입 통계")
                income_data = df[df['transaction_type'] == 'income']
                
                if len(income_data) > 0:
                    income_stats = {
                        "총 수입": f"${income_data['amount'].astype(float).sum():,.2f}",
                        "평균 수입": f"${income_data['amount'].astype(float).mean():,.2f}",
                        "최대 수입": f"${income_data['amount'].astype(float).max():,.2f}",
                        "최소 수입": f"${income_data['amount'].astype(float).min():,.2f}",
                        "수입 건수": f"{len(income_data):,}건"
                    }
                    
                    for key, value in income_stats.items():
                        st.success(f"**{key}**: {value}")
                else:
                    st.info("수입 데이터가 없습니다.")
            
            with col2:
                st.markdown("#### 💸 지출 통계")
                expense_data = df[df['transaction_type'] == 'expense']
                
                if len(expense_data) > 0:
                    expense_stats = {
                        "총 지출": f"${expense_data['amount'].astype(float).sum():,.2f}",
                        "평균 지출": f"${expense_data['amount'].astype(float).mean():,.2f}",
                        "최대 지출": f"${expense_data['amount'].astype(float).max():,.2f}",
                        "최소 지출": f"${expense_data['amount'].astype(float).min():,.2f}",
                        "지출 건수": f"{len(expense_data):,}건"
                    }
                    
                    for key, value in expense_stats.items():
                        st.error(f"**{key}**: {value}")
                else:
                    st.info("지출 데이터가 없습니다.")
            
            # 월별 트렌드 분석
            st.markdown("### 📅 월별 트렌드 분석")
            
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%Y-%m-%d', errors='coerce')
            df = df.dropna(subset=['transaction_date'])
            df['year_month'] = df['transaction_date'].dt.to_period('M')
            
            monthly_trends = df.groupby(['year_month', 'transaction_type']).agg({
                'amount': ['sum', 'count', 'mean']
            }).reset_index()
            
            monthly_trends.columns = ['월', '거래유형', '총액', '건수', '평균']
            
            if len(monthly_trends) > 0:
                st.dataframe(
                    monthly_trends,
                    use_container_width=True,
                    column_config={
                        "총액": st.column_config.NumberColumn("총액 (USD)", format="$%.2f"),
                        "평균": st.column_config.NumberColumn("평균 (USD)", format="$%.2f")
                    }
                )
            
            # 계좌별 통계
            st.markdown("### 🏦 계좌별 통계")
            
            # DataFrame으로 변환된 데이터로 계좌별 통계 계산
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                account_stats = df.groupby('account').agg({
                    'amount': ['sum', 'count', 'mean']
                }).reset_index()
                
                account_stats.columns = ['계좌', '총액', '건수', '평균']
            
                if len(account_stats) > 0:
                    for _, account in account_stats.iterrows():
                        with st.container():
                            st.markdown(f"#### 🏦 {account['계좌']} 계좌")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.info(f"**총 거래액**: ${account['총액']:,.2f}")
                            
                            with col2:
                                st.info(f"**거래 건수**: {account['건수']}건")
                            
                            with col3:
                                st.info(f"**평균 거래액**: ${account['평균']:,.2f}")
                            
                            st.divider()
                else:
                    st.info("계좌별 통계를 생성할 데이터가 없습니다.")
            else:
                st.info("통계를 생성할 데이터가 없습니다.")
        
        else:
            st.info("통계를 생성할 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"통계 분석 중 오류: {str(e)}")

def show_transaction_registration(cash_flow_manager, quotation_manager, purchase_order_manager, notification, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """거래 등록 탭"""
    st.subheader("⚙️ 거래 등록")
    
    # 실제 데이터 기반 거래 등록 섹션
    st.subheader("📋 실제 데이터 기반 등록")
    
    tab1, tab2, tab3 = st.tabs(["견적서 → 수입", "구매주문 → 지출", "수동 등록"])
    
    with tab1:
        st.caption("승인된 견적서를 수입으로 등록")
        try:
            if quotation_manager:
                all_quotations = quotation_manager.get_all_quotations()
                approved_quotations = []
                
                # 데이터 형식 확인 및 처리
                if isinstance(all_quotations, list) and len(all_quotations) > 0:
                    for q in all_quotations:
                        if q.get('status') == 'approved':
                            # 이미 현금흐름에 등록되었는지 확인
                            existing = cash_flow_manager.cash_flow_df[
                                (cash_flow_manager.cash_flow_df['reference_id'] == q.get('quotation_id', '')) & 
                                (cash_flow_manager.cash_flow_df['reference_type'] == 'quotation')
                            ]
                            if len(existing) == 0:
                                approved_quotations.append(q)
                
                if approved_quotations:
                    for quotation in approved_quotations:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**{quotation.get('quotation_title', '제목 없음')}**")
                            st.caption(f"고객: {quotation.get('customer_name', 'N/A')}")
                            st.caption(f"ID: {quotation.get('quotation_id', 'N/A')}")
                        
                        with col2:
                            amount = quotation.get('grand_total', 0)
                            st.metric("금액", f"${amount:,.2f}")
                        
                        with col3:
                            if st.button(f"💰 수입 등록", key=f"income_{quotation.get('quotation_id')}"):
                                transaction_id = cash_flow_manager.record_cash_flow_transaction(
                                    reference_id=quotation.get('quotation_id'),
                                    reference_type='quotation',
                                    transaction_type='income',
                                    amount=amount,
                                    description=f"Quotation income: {quotation.get('quotation_title', '')}"
                                )
                                if transaction_id:
                                    st.success("수입이 등록되었습니다!")
                                    st.rerun()
                        
                        st.divider()
                else:
                    st.info("등록 가능한 승인된 견적서가 없습니다.")
            else:
                st.warning("견적서 관리자를 로드할 수 없습니다.")
        except Exception as e:
            st.error(f"견적서 로드 오류: {str(e)}")
    
    with tab2:
        st.caption("승인된 구매주문을 지출로 등록")
        try:
            if purchase_order_manager:
                all_pos = purchase_order_manager.get_all_purchase_orders()
                approved_pos = []
                
                if len(all_pos) > 0:
                    for _, po in all_pos.iterrows():
                        if po.get('status') in ['approved', 'completed']:
                            # 이미 현금흐름에 등록되었는지 확인
                            existing = cash_flow_manager.cash_flow_df[
                                (cash_flow_manager.cash_flow_df['reference_id'] == po.get('po_id', '')) & 
                                (cash_flow_manager.cash_flow_df['reference_type'] == 'purchase_order')
                            ]
                            if len(existing) == 0:
                                approved_pos.append(po)
                
                if approved_pos:
                    for po in approved_pos:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**PO: {po.get('po_id', 'ID 없음')}**")
                            st.caption(f"공급업체: {po.get('supplier_name', 'N/A')}")
                        
                        with col2:
                            amount = po.get('total_amount', 0)
                            st.metric("금액", f"${amount:,.2f}")
                        
                        with col3:
                            if st.button(f"💸 지출 등록", key=f"expense_{po.get('po_id')}"):
                                transaction_id = cash_flow_manager.record_cash_flow_transaction(
                                    reference_id=po.get('po_id'),
                                    reference_type='purchase_order',
                                    transaction_type='expense',
                                    amount=amount,
                                    description=f"Purchase order: {po.get('supplier_name', '')} - {po.get('po_id')}"
                                )
                                if transaction_id:
                                    st.success("지출이 등록되었습니다!")
                                    st.rerun()
                        
                        st.divider()
                else:
                    st.info("등록 가능한 승인된 구매주문이 없습니다.")
            else:
                st.warning("구매주문 관리자를 로드할 수 없습니다.")
        except Exception as e:
            st.error(f"구매주문 로드 오류: {str(e)}")
    
    with tab3:
        st.caption("직접 거래를 수동으로 등록합니다")
        
        # 계좌 정보 로드 (자동 채우기용)
        account_options = get_available_accounts()
        
        with st.form("manual_transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_type = st.selectbox(
                    "거래 유형 *",
                    ["income", "expense"],
                    format_func=lambda x: "💰 수입" if x == "income" else "💸 지출"
                )
                
                amount = st.number_input(
                    "금액 *",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    help="거래 금액을 입력하세요"
                )
                
                currency = st.selectbox("통화", ["USD", "VND", "KRW", "EUR", "CNY", "JPY"])
            
            with col2:
                # 등록된 계좌 자동 채우기
                if account_options:
                    account = st.selectbox(
                        "계좌 *",
                        account_options,
                        help="등록된 계좌에서 선택하세요"
                    )
                else:
                    account = st.text_input(
                        "계좌 *",
                        placeholder="계좌명을 입력하세요",
                        help="계좌 관리 탭에서 계좌를 등록하면 자동 선택됩니다"
                    )
                
                transaction_date = st.date_input(
                    "거래일 *",
                    value=datetime.now().date()
                )
                
                reference_type = st.selectbox(
                    "참조 유형",
                    ["manual", "quotation", "purchase_order", "invoice", "other"],
                    format_func=lambda x: {
                        "manual": "수동 등록",
                        "quotation": "견적서",
                        "purchase_order": "구매주문",
                        "invoice": "송장",
                        "other": "기타"
                    }.get(x, x)
                )
            
            description = st.text_area(
                "거래 내용 *",
                placeholder="거래에 대한 설명을 입력하세요"
            )
            
            reference_id = st.text_input(
                "참조 ID",
                placeholder="관련 문서 ID가 있다면 입력하세요 (선택사항)"
            )
            
            submitted = st.form_submit_button("💾 거래 등록", type="primary")
            
            if submitted:
                if transaction_type and amount > 0 and account and description:
                    try:
                        transaction_id = cash_flow_manager.record_cash_flow_transaction(
                            reference_id=reference_id if reference_id else None,
                            reference_type=reference_type,
                            transaction_type=transaction_type,
                            amount=amount,
                            currency=currency,
                            description=description,
                            account=account,
                            transaction_date=transaction_date.strftime('%Y-%m-%d')
                        )
                        
                        if transaction_id:
                            transaction_type_text = "수입" if transaction_type == "income" else "지출"
                            st.success(f"✅ {transaction_type_text} 거래가 성공적으로 등록되었습니다!")
                            notification.show_success(f"{transaction_type_text} ${amount:,.2f} 등록 완료")
                            st.rerun()
                        else:
                            st.error("거래 등록 중 오류가 발생했습니다.")
                    except Exception as e:
                        st.error(f"거래 등록 오류: {str(e)}")
                else:
                    st.error("필수 항목을 모두 입력해주세요.")

def get_available_accounts():
    """등록된 계좌 목록을 가져오는 함수"""
    try:
        account_info_file = "data/account_info.csv"
        if os.path.exists(account_info_file):
            account_info_df = pd.read_csv(account_info_file)
            if len(account_info_df) > 0:
                # 활성 계좌만 반환
                active_accounts = account_info_df[account_info_df['status'] == 'active']
                return [f"{row['account_name']} ({row['bank_name']})" for _, row in active_accounts.iterrows()]
    except Exception as e:
        print(f"계좌 정보 로드 오류: {e}")
    return []
    


def show_account_management(cash_flow_manager, notification, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """계좌 관리 탭"""
    st.subheader("🏦 계좌 관리")
    
    # 탭으로 계좌 관리 기능 분리
    tab1, tab2, tab3 = st.tabs(["💳 계좌 정보 관리", "📊 계좌별 현황", "➕ 새 계좌 등록"])
    
    with tab1:
        show_account_info_management(cash_flow_manager, notification)
    
    with tab2:
        show_account_balance_overview(cash_flow_manager, notification)
    
    with tab3:
        show_new_account_registration(cash_flow_manager, notification)

def show_account_info_management(cash_flow_manager, notification):
    """계좌 정보 관리"""
    st.subheader("💳 계좌 정보 관리")
    
    # 계좌 정보 파일 관리
    account_info_file = "data/account_info.csv"
    
    # 계좌 정보 로드
    try:
        if os.path.exists(account_info_file):
            account_info_df = pd.read_csv(account_info_file)
        else:
            account_info_df = pd.DataFrame(columns=[
                'account_id', 'account_name', 'account_number', 'bank_name', 
                'bank_code', 'account_type', 'currency', 'notes', 'status', 'created_date'
            ])
            account_info_df.to_csv(account_info_file, index=False)
    except Exception as e:
        st.error(f"계좌 정보 로드 오류: {str(e)}")
        account_info_df = pd.DataFrame()
    
    if len(account_info_df) > 0:
        st.markdown("### 📋 등록된 계좌 목록")
        
        for idx, account in account_info_df.iterrows():
            with st.expander(f"🏦 {account['account_name']} ({account['bank_name']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**계좌명:** {account['account_name']}")
                    st.write(f"**계좌번호:** {account['account_number']}")
                    st.write(f"**은행:** {account['bank_name']}")
                
                with col2:
                    st.write(f"**은행코드:** {account.get('bank_code', 'N/A')}")
                    st.write(f"**계좌종류:** {account.get('account_type', 'N/A')}")
                    st.write(f"**통화:** {account.get('currency', 'VND')}")
                
                with col3:
                    st.write(f"**상태:** {account.get('status', 'active')}")
                    st.write(f"**생성일:** {account.get('created_date', 'N/A')}")
                    if account.get('notes'):
                        st.write(f"**메모:** {account['notes']}")
                
                # 수정/삭제 버튼
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    if st.button(f"✏️ 수정", key=f"edit_account_{idx}"):
                        st.session_state.edit_account_idx = idx
                        st.rerun()
                
                with col_delete:
                    if st.button(f"🗑️ 삭제", key=f"delete_account_{idx}"):
                        account_info_df = account_info_df.drop(idx).reset_index(drop=True)
                        account_info_df.to_csv(account_info_file, index=False)
                        st.success("계좌가 삭제되었습니다!")
                        st.rerun()
    else:
        st.info("등록된 계좌 정보가 없습니다. '새 계좌 등록' 탭에서 계좌를 추가하세요.")
    
    # 계좌 수정 모달
    if st.session_state.get('edit_account_idx') is not None:
        show_edit_account_modal(account_info_df, account_info_file, notification)

def show_new_account_registration(cash_flow_manager, notification):
    """새 계좌 등록"""
    st.subheader("➕ 새 계좌 등록")
    
    # 베트남 주요 은행 목록
    vietnam_banks = [
        "Vietcombank (VCB)", "BIDV", "VietinBank", "Agribank", "Techcombank (TCB)",
        "MB Bank (MBB)", "ACB", "VPBank", "SHB", "Eximbank",
        "HDBank", "LienVietPostBank", "VIB", "OCB", "TPBank",
        "SeABank", "Nam A Bank", "KienLongBank", "BacABank", "PVcomBank",
        "SaigonBank", "VietABank", "NCB", "Dong A Bank", "GPBank",
        "ABBank", "MSB", "HSBC Vietnam", "Standard Chartered Vietnam", "ANZ Vietnam",
        "Citibank Vietnam", "Shinhan Bank Vietnam", "Woori Bank Vietnam", "기타"
    ]
    
    with st.form("new_account_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_name = st.text_input("계좌명 *", placeholder="예: 운영계좌, 급여계좌")
            account_number = st.text_input("계좌번호 *", placeholder="계좌번호를 입력하세요")
            bank_name = st.selectbox("은행명 *", vietnam_banks)
            bank_code = st.text_input("은행코드", placeholder="예: VCB, BIDV")
        
        with col2:
            account_type = st.selectbox(
                "계좌종류", 
                ["checking", "savings", "business", "foreign_currency", "other"],
                format_func=lambda x: {
                    "checking": "당좌계좌",
                    "savings": "저축계좌", 
                    "business": "기업계좌",
                    "foreign_currency": "외화계좌",
                    "other": "기타"
                }.get(x, x)
            )
            
            currency = st.selectbox("통화", ["VND", "USD", "EUR", "KRW", "CNY", "JPY"])
            
            status = st.selectbox(
                "상태",
                ["active", "inactive", "closed"],
                format_func=lambda x: {
                    "active": "활성",
                    "inactive": "비활성", 
                    "closed": "폐쇄"
                }.get(x, x)
            )
        
        notes = st.text_area("메모", placeholder="계좌에 대한 추가 정보나 메모")
        
        submitted = st.form_submit_button("💾 계좌 등록", type="primary")
        
        if submitted:
            if account_name and account_number and bank_name:
                try:
                    # 계좌 정보 파일 로드/생성
                    account_info_file = "data/account_info.csv"
                    
                    if os.path.exists(account_info_file):
                        account_info_df = pd.read_csv(account_info_file)
                    else:
                        account_info_df = pd.DataFrame(columns=[
                            'account_id', 'account_name', 'account_number', 'bank_name', 
                            'bank_code', 'account_type', 'currency', 'notes', 'status', 'created_date'
                        ])
                    
                    # 중복 계좌 확인
                    existing_account = account_info_df[
                        (account_info_df['account_name'] == account_name) & 
                        (account_info_df['account_number'] == account_number) &
                        (account_info_df['bank_name'] == bank_name)
                    ]
                    
                    if len(existing_account) > 0:
                        st.error("이미 등록된 계좌입니다. 계좌명, 계좌번호, 은행이 모두 동일한 계좌가 존재합니다.")
                        st.stop()
                    
                    # 새 계좌 정보 추가
                    new_account = {
                        'account_id': f"ACC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'account_name': account_name,
                        'account_number': account_number,
                        'bank_name': bank_name,
                        'bank_code': bank_code,
                        'account_type': account_type,
                        'currency': currency,
                        'notes': notes,
                        'status': status,
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    new_account_df = pd.DataFrame([new_account])
                    if len(account_info_df) == 0:
                        account_info_df = new_account_df
                    else:
                        account_info_df = pd.concat([account_info_df, new_account_df], ignore_index=True)
                    
                    account_info_df.to_csv(account_info_file, index=False)
                    
                    st.success("계좌가 성공적으로 등록되었습니다!")
                    notification.show_success("계좌 등록", f"{account_name} 계좌가 등록되었습니다.")
                    # 폼 리셋을 위한 새로고침
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"계좌 등록 중 오류: {str(e)}")
            else:
                st.error("필수 항목을 모두 입력해주세요.")

def show_edit_account_modal(account_info_df, account_info_file, notification):
    """계좌 수정 모달"""
    edit_idx = st.session_state.get('edit_account_idx')
    if edit_idx is not None and edit_idx < len(account_info_df):
        account = account_info_df.iloc[edit_idx]
        
        st.subheader(f"✏️ {account['account_name']} 계좌 수정")
        
        # 베트남 주요 은행 목록
        vietnam_banks = [
            "Vietcombank (VCB)", "BIDV", "VietinBank", "Agribank", "Techcombank (TCB)",
            "MB Bank (MBB)", "ACB", "VPBank", "SHB", "Eximbank",
            "HDBank", "LienVietPostBank", "VIB", "OCB", "TPBank",
            "SeABank", "Nam A Bank", "KienLongBank", "BacABank", "PVcomBank",
            "SaigonBank", "VietABank", "NCB", "Dong A Bank", "GPBank",
            "ABBank", "MSB", "HSBC Vietnam", "Standard Chartered Vietnam", "ANZ Vietnam",
            "Citibank Vietnam", "Shinhan Bank Vietnam", "Woori Bank Vietnam", "기타"
        ]
        
        with st.form("edit_account_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_account_name = st.text_input("계좌명 *", value=account['account_name'])
                new_account_number = st.text_input("계좌번호 *", value=account['account_number'])
                
                current_bank_idx = vietnam_banks.index(account['bank_name']) if account['bank_name'] in vietnam_banks else 0
                new_bank_name = st.selectbox("은행명 *", vietnam_banks, index=current_bank_idx)
                new_bank_code = st.text_input("은행코드", value=account.get('bank_code', ''))
            
            with col2:
                account_types = ["checking", "savings", "business", "foreign_currency", "other"]
                current_type_idx = account_types.index(account.get('account_type', 'checking')) if account.get('account_type') in account_types else 0
                new_account_type = st.selectbox(
                    "계좌종류", 
                    account_types,
                    index=current_type_idx,
                    format_func=lambda x: {
                        "checking": "당좌계좌",
                        "savings": "저축계좌", 
                        "business": "기업계좌",
                        "foreign_currency": "외화계좌",
                        "other": "기타"
                    }.get(x, x)
                )
                
                currencies = ["VND", "USD", "EUR", "KRW", "CNY", "JPY"]
                current_currency_idx = currencies.index(account.get('currency', 'VND')) if account.get('currency') in currencies else 0
                new_currency = st.selectbox("통화", currencies, index=current_currency_idx)
                
                statuses = ["active", "inactive", "closed"]
                current_status_idx = statuses.index(account.get('status', 'active')) if account.get('status') in statuses else 0
                new_status = st.selectbox(
                    "상태",
                    statuses,
                    index=current_status_idx,
                    format_func=lambda x: {
                        "active": "활성",
                        "inactive": "비활성", 
                        "closed": "폐쇄"
                    }.get(x, x)
                )
            
            new_notes = st.text_area("메모", value=account.get('notes', ''))
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                save_submitted = st.form_submit_button("💾 저장", type="primary")
            
            with col_cancel:
                cancel_submitted = st.form_submit_button("❌ 취소")
            
            if save_submitted:
                if new_account_name and new_account_number and new_bank_name:
                    try:
                        # 계좌 정보 업데이트
                        account_info_df.at[edit_idx, 'account_name'] = new_account_name
                        account_info_df.at[edit_idx, 'account_number'] = new_account_number
                        account_info_df.at[edit_idx, 'bank_name'] = new_bank_name
                        account_info_df.at[edit_idx, 'bank_code'] = new_bank_code
                        account_info_df.at[edit_idx, 'account_type'] = new_account_type
                        account_info_df.at[edit_idx, 'currency'] = new_currency
                        account_info_df.at[edit_idx, 'notes'] = new_notes
                        account_info_df.at[edit_idx, 'status'] = new_status
                        
                        account_info_df.to_csv(account_info_file, index=False)
                        
                        st.success("계좌 정보가 성공적으로 업데이트되었습니다!")
                        del st.session_state.edit_account_idx
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"계좌 수정 중 오류: {str(e)}")
                else:
                    st.error("필수 항목을 모두 입력해주세요.")
            
            if cancel_submitted:
                del st.session_state.edit_account_idx
                st.rerun()

def show_account_balance_overview(cash_flow_manager, notification):
    """계좌별 잔고 현황"""
    st.subheader("📊 계좌별 현황")
    
    # 계좌 정보와 잔고 정보 매핑
    account_info_file = "data/account_info.csv"
    
    try:
        if os.path.exists(account_info_file):
            account_info_df = pd.read_csv(account_info_file)
        else:
            account_info_df = pd.DataFrame()
    except:
        account_info_df = pd.DataFrame()
    
    try:
        all_transactions = cash_flow_manager.get_all_transactions()
        
        if len(all_transactions) > 0:
            # 딕셔너리 리스트를 DataFrame으로 변환
            if isinstance(all_transactions, list):
                all_transactions_df = pd.DataFrame(all_transactions)
            else:
                all_transactions_df = all_transactions
            
            # 계좌별 잔고 계산
            account_balances = {}
            
            for account in all_transactions_df['account'].unique() if len(all_transactions_df) > 0 else []:
                account_transactions = all_transactions_df[all_transactions_df['account'] == account]
                
                income_total = account_transactions[
                    account_transactions['transaction_type'] == 'income'
                ]['amount'].astype(float).sum()
                
                expense_total = account_transactions[
                    account_transactions['transaction_type'] == 'expense'
                ]['amount'].astype(float).sum()
                
                balance = income_total - expense_total
                transaction_count = len(account_transactions)
                
                account_balances[account] = {
                    'balance': balance,
                    'income': income_total,
                    'expense': expense_total,
                    'transactions': transaction_count
                }
            
            # 계좌별 카드 표시
            for account, data in account_balances.items():
                with st.container():
                    # 계좌 정보 조회
                    account_info = None
                    if len(account_info_df) > 0:
                        matching_accounts = account_info_df[account_info_df['account_name'] == account]
                        if len(matching_accounts) > 0:
                            account_info = matching_accounts.iloc[0]
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        if account_info is not None:
                            st.markdown(f"**🏦 {account_info['account_name']}**")
                            st.caption(f"{account_info['bank_name']}")
                            st.caption(f"계좌: {account_info['account_number']}")
                        else:
                            st.markdown(f"**📋 {account}**")
                        st.caption(f"거래 {data['transactions']}건")
                    
                    with col2:
                        currency = account_info['currency'] if account_info is not None else 'USD'
                        if data['balance'] >= 0:
                            st.success(f"잔고: {data['balance']:,.2f} {currency}")
                        else:
                            st.error(f"잔고: {data['balance']:,.2f} {currency}")
                    
                    with col3:
                        currency = account_info['currency'] if account_info is not None else 'USD'
                        st.info(f"수입: {data['income']:,.2f} {currency}")
                    
                    with col4:
                        currency = account_info['currency'] if account_info is not None else 'USD'
                        st.warning(f"지출: {data['expense']:,.2f} {currency}")
                    
                    with col5:
                        # 계좌 상세 버튼
                        if st.button(f"상세", key=f"detail_{account}"):
                            st.session_state[f'show_account_detail_{account}'] = True
                            st.rerun()
                        
                        # 계좌 정보가 등록되지 않은 경우 등록 버튼
                        if account_info is None:
                            if st.button(f"정보등록", key=f"register_{account}"):
                                st.session_state.register_account_name = account
                                st.rerun()
                    
                    st.divider()
            
            # 계좌별 상세 정보 표시
            for account in account_balances.keys():
                if st.session_state.get(f'show_account_detail_{account}', False):
                    with st.expander(f"🏦 {account} 계좌 상세 정보", expanded=True):
                        # 딕셔너리 리스트를 DataFrame으로 변환
                        if isinstance(all_transactions, list):
                            all_transactions_df = pd.DataFrame(all_transactions)
                            account_transactions = all_transactions_df[all_transactions_df['account'] == account] if len(all_transactions_df) > 0 else pd.DataFrame()
                        else:
                            account_transactions = all_transactions[all_transactions['account'] == account]
                        
                        # 최근 거래 내역
                        st.markdown("#### 최근 거래 내역")
                        recent_transactions = account_transactions.head(10) if len(account_transactions) > 0 else pd.DataFrame()
                        
                        for _, transaction in recent_transactions.iterrows():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{transaction.get('description', 'N/A')}**")
                                st.caption(f"ID: {transaction.get('transaction_id', 'N/A')}")
                            
                            with col2:
                                amount = float(transaction.get('amount', 0))
                                if transaction.get('transaction_type') == 'income':
                                    st.success(f"+${amount:,.2f}")
                                else:
                                    st.error(f"-${amount:,.2f}")
                            
                            with col3:
                                transaction_date = transaction.get('transaction_date', 'N/A')
                                st.caption(f"{transaction_date[:10]}")
                        
                        # 닫기 버튼
                        if st.button(f"닫기", key=f"close_{account}"):
                            st.session_state[f'show_account_detail_{account}'] = False
                            st.rerun()
            
            # 전체 계좌 요약
            st.markdown("---")
            st.markdown("### 📊 전체 계좌 요약")
            
            total_balance = sum(data['balance'] for data in account_balances.values())
            total_income = sum(data['income'] for data in account_balances.values())
            total_expense = sum(data['expense'] for data in account_balances.values())
            total_transactions = sum(data['transactions'] for data in account_balances.values())
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if total_balance >= 0:
                    st.success(f"**총 잔고**\n${total_balance:,.2f}")
                else:
                    st.error(f"**총 잔고**\n${total_balance:,.2f}")
            
            with col2:
                st.info(f"**총 수입**\n${total_income:,.2f}")
            
            with col3:
                st.warning(f"**총 지출**\n${total_expense:,.2f}")
            
            with col4:
                st.metric("총 거래", f"{total_transactions}건")
        
        else:
            st.info("등록된 거래가 없습니다.")
            
    except Exception as e:
        st.error(f"계좌 관리 로드 중 오류: {str(e)}")
    
    # 계좌 정보 미등록 계좌 자동 등록 모달
    if st.session_state.get('register_account_name'):
        show_quick_account_registration_modal(cash_flow_manager, notification)

def show_quick_account_registration_modal(cash_flow_manager, notification):
    """미등록 계좌 빠른 등록 모달"""
    account_name = st.session_state.get('register_account_name')
    
    st.subheader(f"🏦 '{account_name}' 계좌 정보 등록")
    st.caption("현금 흐름에 사용되고 있는 계좌의 상세 정보를 등록하세요.")
    
    # 베트남 주요 은행 목록
    vietnam_banks = [
        "Vietcombank (VCB)", "BIDV", "VietinBank", "Agribank", "Techcombank (TCB)",
        "MB Bank (MBB)", "ACB", "VPBank", "SHB", "Eximbank",
        "HDBank", "LienVietPostBank", "VIB", "OCB", "TPBank",
        "SeABank", "Nam A Bank", "KienLongBank", "BacABank", "PVcomBank",
        "SaigonBank", "VietABank", "NCB", "Dong A Bank", "GPBank",
        "ABBank", "MSB", "HSBC Vietnam", "Standard Chartered Vietnam", "ANZ Vietnam",
        "Citibank Vietnam", "Shinhan Bank Vietnam", "Woori Bank Vietnam", "기타"
    ]
    
    with st.form("quick_account_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_number = st.text_input("계좌번호 *", placeholder="계좌번호를 입력하세요")
            bank_name = st.selectbox("은행명 *", vietnam_banks)
            bank_code = st.text_input("은행코드", placeholder="예: VCB, BIDV")
        
        with col2:
            account_type = st.selectbox(
                "계좌종류", 
                ["checking", "savings", "business", "foreign_currency", "other"],
                format_func=lambda x: {
                    "checking": "당좌계좌",
                    "savings": "저축계좌", 
                    "business": "기업계좌",
                    "foreign_currency": "외화계좌",
                    "other": "기타"
                }.get(x, x)
            )
            
            currency = st.selectbox("통화", ["VND", "USD", "EUR", "KRW", "CNY", "JPY"])
        
        notes = st.text_area("메모", placeholder="계좌에 대한 추가 정보나 메모")
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            save_submitted = st.form_submit_button("💾 등록", type="primary")
        
        with col_cancel:
            cancel_submitted = st.form_submit_button("❌ 취소")
        
        if save_submitted:
            if account_number and bank_name:
                try:
                    # 계좌 정보 파일 로드/생성
                    account_info_file = "data/account_info.csv"
                    
                    if os.path.exists(account_info_file):
                        account_info_df = pd.read_csv(account_info_file)
                    else:
                        account_info_df = pd.DataFrame(columns=[
                            'account_id', 'account_name', 'account_number', 'bank_name', 
                            'bank_code', 'account_type', 'currency', 'notes', 'status', 'created_date'
                        ])
                    
                    # 새 계좌 정보 추가
                    new_account = {
                        'account_id': f"ACC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'account_name': account_name,
                        'account_number': account_number,
                        'bank_name': bank_name,
                        'bank_code': bank_code,
                        'account_type': account_type,
                        'currency': currency,
                        'notes': notes,
                        'status': 'active',
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    new_account_df = pd.DataFrame([new_account])
                    if len(account_info_df) == 0:
                        account_info_df = new_account_df
                    else:
                        account_info_df = pd.concat([account_info_df, new_account_df], ignore_index=True)
                    
                    account_info_df.to_csv(account_info_file, index=False)
                    
                    st.success(f"'{account_name}' 계좌 정보가 성공적으로 등록되었습니다!")
                    del st.session_state.register_account_name
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"계좌 등록 중 오류: {str(e)}")
            else:
                st.error("계좌번호와 은행명은 필수 항목입니다.")
        
        if cancel_submitted:
            del st.session_state.register_account_name
            st.rerun()

def show_edit_transaction_modal(cash_flow_manager, notification):
    """거래 수정 모달"""
    transaction_data = st.session_state.get('edit_transaction_data')
    
    st.subheader(f"✏️ 거래 수정: {transaction_data.get('description', 'N/A')}")
    
    with st.form("edit_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_description = st.text_area(
                "거래 설명 *",
                value=transaction_data.get('description', ''),
                height=100
            )
            
            new_amount = st.number_input(
                "금액 *",
                min_value=0.01,
                value=float(transaction_data.get('amount', 0)),
                step=0.01,
                format="%.2f"
            )
            
            new_transaction_type = st.selectbox(
                "거래 유형 *",
                ["income", "expense"],
                index=0 if transaction_data.get('transaction_type') == 'income' else 1,
                format_func=lambda x: "수입" if x == "income" else "지출"
            )
        
        with col2:
            new_currency = st.selectbox(
                "통화",
                ["USD", "VND", "EUR", "KRW", "CNY", "JPY"],
                index=["USD", "VND", "EUR", "KRW", "CNY", "JPY"].index(transaction_data.get('currency', 'USD'))
            )
            
            new_status = st.selectbox(
                "상태",
                ["completed", "pending", "cancelled"],
                index=["completed", "pending", "cancelled"].index(transaction_data.get('status', 'completed')),
                format_func=lambda x: {
                    "completed": "완료",
                    "pending": "대기",
                    "cancelled": "취소"
                }.get(x, x)
            )
            
            new_account = st.text_input(
                "계좌",
                value=transaction_data.get('account', '')
            )
        
        new_transaction_date = st.date_input(
            "거래 날짜",
            value=datetime.strptime(transaction_data.get('transaction_date', '')[:10], '%Y-%m-%d').date()
        )
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            save_submitted = st.form_submit_button("💾 저장", type="primary")
        
        with col_cancel:
            cancel_submitted = st.form_submit_button("❌ 취소")
        
        if save_submitted:
            if new_description and new_amount:
                try:
                    # 거래 수정
                    updated_data = {
                        'transaction_id': transaction_data.get('transaction_id'),
                        'description': new_description,
                        'amount': new_amount,
                        'transaction_type': new_transaction_type,
                        'currency': new_currency,
                        'status': new_status,
                        'account': new_account,
                        'transaction_date': new_transaction_date.strftime('%Y-%m-%d'),
                        'updated_by': st.session_state.get('user_id', 'system'),
                        'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if cash_flow_manager.update_transaction(updated_data):
                        st.success("거래가 성공적으로 수정되었습니다!")
                        del st.session_state.edit_transaction_data
                        st.rerun()
                    else:
                        st.error("거래 수정에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"거래 수정 중 오류: {str(e)}")
            else:
                st.error("필수 항목을 모두 입력해주세요.")
        
        if cancel_submitted:
            del st.session_state.edit_transaction_data
            st.rerun()

def show_data_management(cash_flow_manager, quotation_manager, purchase_order_manager, notification, get_text=None):
    if get_text is None:
        get_text = lambda key: key
    """데이터 관리 탭"""
    st.subheader("🧹 데이터 관리")
    st.caption("더미 데이터 정리 및 실제 데이터 동기화")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 현재 데이터 현황")
        
        all_transactions = cash_flow_manager.get_all_transactions()
        total_transactions = len(all_transactions)
        
        # 실제 데이터와 더미 데이터 분류
        real_data_count = 0
        dummy_data_count = 0
        
        for transaction in all_transactions:
            ref_type = transaction.get('reference_type', '')
            if ref_type in ['quotation', 'purchase_order', 'invoice']:
                real_data_count += 1
            else:
                dummy_data_count += 1
        
        st.info(f"**총 거래 수**: {total_transactions}건")
        st.success(f"**실제 데이터**: {real_data_count}건")
        st.warning(f"**더미/테스트 데이터**: {dummy_data_count}건")
        
        if dummy_data_count > 0:
            if st.button("🗑️ 더미 데이터 삭제", type="primary"):
                success, message = cash_flow_manager.clear_all_dummy_data()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.markdown("### 🔄 실제 데이터 동기화")
        
        if st.button("📋 견적서 데이터 동기화"):
            if quotation_manager:
                if cash_flow_manager.sync_with_quotations(quotation_manager):
                    st.success("견적서 데이터가 동기화되었습니다!")
                    st.rerun()
                else:
                    st.error("견적서 데이터 동기화에 실패했습니다.")
            else:
                st.error("견적서 관리자를 사용할 수 없습니다.")
        
        if st.button("🛒 구매주문 데이터 동기화"):
            if purchase_order_manager:
                if cash_flow_manager.sync_with_purchase_orders(purchase_order_manager):
                    st.success("구매주문 데이터가 동기화되었습니다!")
                    st.rerun()
                else:
                    st.error("구매주문 데이터 동기화에 실패했습니다.")
            else:
                st.error("구매주문 관리자를 사용할 수 없습니다.")
        
        if st.button("🔄 전체 데이터 동기화"):
            sync_results = cash_flow_manager.auto_sync_all_data(
                quotation_manager=quotation_manager,
                purchase_order_manager=purchase_order_manager
            )
            
            if sync_results:
                st.success("전체 데이터 동기화가 완료되었습니다!")
                for source, result in sync_results:
                    if result:
                        st.success(f"✅ {source} 동기화 성공")
                    else:
                        st.error(f"❌ {source} 동기화 실패")
                st.rerun()
            else:
                st.error("데이터 동기화에 실패했습니다.")
    
    # 데이터 검증 섹션
    st.markdown("---")
    st.markdown("### 🔍 데이터 검증")
    
    if st.button("데이터 무결성 검사"):
        verification_results = []
        
        # 1. 중복 거래 검사
        all_transactions = cash_flow_manager.get_all_transactions()
        transaction_ids = [t.get('transaction_id') for t in all_transactions]
        duplicates = len(transaction_ids) - len(set(transaction_ids))
        
        if duplicates > 0:
            verification_results.append(f"⚠️ 중복된 거래 ID {duplicates}개 발견")
        else:
            verification_results.append("✅ 거래 ID 중복 없음")
        
        # 2. 금액 유효성 검사
        invalid_amounts = 0
        for transaction in all_transactions:
            try:
                amount = float(transaction.get('amount', 0))
                if amount <= 0:
                    invalid_amounts += 1
            except:
                invalid_amounts += 1
        
        if invalid_amounts > 0:
            verification_results.append(f"⚠️ 유효하지 않은 금액 {invalid_amounts}개 발견")
        else:
            verification_results.append("✅ 모든 금액이 유효함")
        
        # 3. 날짜 형식 검사
        invalid_dates = 0
        for transaction in all_transactions:
            try:
                date_str = transaction.get('transaction_date', '')
                datetime.strptime(date_str[:10], '%Y-%m-%d')
            except:
                invalid_dates += 1
        
        if invalid_dates > 0:
            verification_results.append(f"⚠️ 유효하지 않은 날짜 {invalid_dates}개 발견")
        else:
            verification_results.append("✅ 모든 날짜가 유효함")
        
        # 결과 표시
        for result in verification_results:
            if "⚠️" in result:
                st.warning(result)
            else:
                st.success(result)
    
    # 백업 및 복원 섹션
    st.markdown("---")
    st.markdown("### 💾 백업 및 복원")
    
    backup_col1, backup_col2 = st.columns(2)
    
    with backup_col1:
        if st.button("📥 현재 데이터 백업"):
            try:
                backup_filename = f"cash_flow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                backup_path = f"data/backups/{backup_filename}"
                
                os.makedirs("data/backups", exist_ok=True)
                
                if len(cash_flow_manager.cash_flow_df) > 0:
                    cash_flow_manager.cash_flow_df.to_csv(backup_path, index=False)
                    st.success(f"백업이 완료되었습니다: {backup_filename}")
                else:
                    st.warning("백업할 데이터가 없습니다.")
                    
            except Exception as e:
                st.error(f"백업 중 오류 발생: {str(e)}")
    
    with backup_col2:
        st.caption("⚠️ 백업 기능은 중요한 데이터 손실을 방지합니다")
        st.caption("정기적으로 백업을 생성하는 것을 권장합니다")