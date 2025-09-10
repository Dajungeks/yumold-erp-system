import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
from cash_transaction_manager import CashTransactionManager
from notification_helper import NotificationHelper


def show_cash_transaction_page(selected_submenu):
    """현금 거래 관리 메인 페이지"""
    manager = CashTransactionManager()
    notifier = NotificationHelper()
    
    if selected_submenu == "거래 내역":
        show_transaction_history(manager, notifier)
    elif selected_submenu == "거래 등록":
        show_transaction_registration(manager, notifier)
    elif selected_submenu == "거래 편집":
        show_transaction_edit(manager, notifier)
    elif selected_submenu == "주가 관리":
        show_stock_price_management(manager, notifier)
    elif selected_submenu == "거래 통계":
        show_transaction_statistics(manager)
    else:
        show_transaction_dashboard(manager)


def show_transaction_dashboard(manager):
    """현금 거래 대시보드"""
    st.header("💰 현금 거래 대시보드")
    
    # 요약 정보
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    
    # 이번 달 요약
    monthly_summary = manager.get_transaction_summary(this_month_start, today)
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "이번 달 총 수입",
            f"₩{monthly_summary['total_income']:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "이번 달 총 지출",
            f"₩{monthly_summary['total_expense']:,.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "순 현금 흐름",
            f"₩{monthly_summary['net_amount']:,.0f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "총 거래 건수",
            f"{monthly_summary['transaction_count']}건",
            delta=None
        )
    
    # 차트 표시
    col1, col2 = st.columns(2)
    
    with col1:
        # 최근 7일 거래 추이
        week_start = today - timedelta(days=7)
        week_transactions = manager.get_transactions_by_date_range(week_start, today)
        
        if len(week_transactions) > 0:
            daily_summary = week_transactions.groupby(['date', 'type'])['amount'].sum().reset_index()
            
            fig = px.bar(
                daily_summary,
                x='date',
                y='amount',
                color='type',
                title="최근 7일 거래 추이",
                color_discrete_map={'입금': '#2E86AB', '출금': '#F24236'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("최근 7일간 거래 내역이 없습니다.")
    
    with col2:
        # 카테고리별 지출 분석
        expense_transactions = manager.get_all_transactions()
        expense_transactions = expense_transactions[expense_transactions['type'] == '출금']
        
        if len(expense_transactions) > 0:
            category_summary = expense_transactions.groupby('category')['amount'].sum().reset_index()
            
            fig = px.pie(
                category_summary,
                values='amount',
                names='category',
                title="카테고리별 지출 분석"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("지출 내역이 없습니다.")


def show_transaction_history(manager, notifier):
    """거래 내역 페이지"""
    st.header("📋 현금 거래 내역")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("시작일", value=date.today() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("종료일", value=date.today())
    
    with col3:
        transaction_type = st.selectbox("거래 유형", ["전체", "입금", "출금"])
    
    # 거래 내역 조회
    if start_date and end_date:
        transactions = manager.get_transactions_by_date_range(start_date, end_date)
        
        # 거래 유형 필터링
        if transaction_type != "전체":
            transactions = transactions[transactions['type'] == transaction_type]
        
        if len(transactions) > 0:
            st.info(f"총 {len(transactions)}건의 거래가 조회되었습니다.")
            
            # 표시할 컬럼 설정
            display_columns = ['date', 'type', 'category', 'amount', 'currency', 'description', 'account', 'status']
            available_columns = [col for col in display_columns if col in transactions.columns]
            
            if available_columns:
                display_df = transactions[available_columns].copy()
                
                # 컬럼명 한국어로 변경
                column_mapping = {
                    'date': '날짜',
                    'type': '유형',
                    'category': '카테고리',
                    'amount': '금액',
                    'currency': '통화',
                    'description': '설명',
                    'account': '계좌',
                    'status': '상태'
                }
                
                rename_dict = {k: v for k, v in column_mapping.items() if k in display_df.columns}
                display_df = display_df.rename(columns=rename_dict)
                
                # 거래 내역 테이블 표시
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 다운로드 버튼
                csv_buffer = io.StringIO()
                transactions.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 거래 내역 다운로드",
                    data=csv_buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"transactions_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("조건에 맞는 거래 내역이 없습니다.")


def show_transaction_registration(manager, notifier):
    """거래 등록 페이지"""
    st.header("➕ 새 거래 등록")
    
    with st.form("transaction_registration_form"):
        # 거래 기본 정보
        st.subheader("거래 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_date = st.date_input("거래일", value=date.today())
            transaction_type = st.selectbox("거래 유형", ["입금", "출금"])
            category = st.selectbox("카테고리", [
                "매출", "급여", "임대료", "유틸리티", "사무용품", "마케팅",
                "여행비", "식비", "교육비", "보험료", "세금", "기타"
            ])
        
        with col2:
            amount = st.number_input("금액", min_value=0.0, value=0.0, step=1000.0)
            currency = st.selectbox("통화", ["KRW", "USD", "VND", "THB", "CNY", "JPY"])
            account = st.selectbox("계좌", ["주계좌", "예비계좌", "현금", "신용카드"])
        
        # 추가 정보
        st.subheader("추가 정보")
        description = st.text_input("거래 설명", placeholder="거래에 대한 설명을 입력하세요")
        reference_id = st.text_input("참조 번호", placeholder="관련 문서나 거래 번호")
        notes = st.text_area("비고", placeholder="추가 메모사항")
        
        # 등록 버튼
        submitted = st.form_submit_button("💾 거래 등록", use_container_width=True, type="primary")
        
        if submitted:
            if amount <= 0:
                notifier.show_error("금액은 0보다 커야 합니다.")
            else:
                # 거래 데이터 준비
                transaction_data = {
                    'date': transaction_date.strftime('%Y-%m-%d'),
                    'type': transaction_type,
                    'category': category,
                    'amount': amount,
                    'currency': currency,
                    'description': description,
                    'reference_id': reference_id,
                    'account': account,
                    'status': '완료',
                    'created_by': st.session_state.get('user_name', ''),
                    'notes': notes
                }
                
                # 거래 등록
                transaction_id = manager.add_transaction(transaction_data)
                if transaction_id:
                    notifier.show_success(f"거래가 성공적으로 등록되었습니다! (ID: {transaction_id})")
                    st.rerun()
                else:
                    notifier.show_error("거래 등록에 실패했습니다.")


def show_transaction_edit(manager, notifier):
    """거래 편집 페이지"""
    st.header("✏️ 거래 편집")
    
    # 편집할 거래 선택
    transactions = manager.get_all_transactions()
    if len(transactions) > 0:
        # 최근 거래 목록 표시
        recent_transactions = transactions.head(20)
        transaction_options = [
            f"{row['date']} - {row['type']} - ₩{row['amount']:,.0f} - {row['description'][:30]}"
            for _, row in recent_transactions.iterrows()
        ]
        
        selected_transaction = st.selectbox("편집할 거래 선택", transaction_options)
        
        if selected_transaction:
            # 선택된 거래 정보 가져오기
            selected_index = transaction_options.index(selected_transaction)
            transaction_data = recent_transactions.iloc[selected_index]
            transaction_id = transaction_data['transaction_id']
            
            # 편집 폼
            with st.form("transaction_edit_form"):
                st.subheader("거래 정보 수정")
                col1, col2 = st.columns(2)
                
                with col1:
                    transaction_date = st.date_input("거래일", value=pd.to_datetime(transaction_data['date']).date())
                    transaction_type = st.selectbox("거래 유형", ["입금", "출금"], 
                                                  index=0 if transaction_data['type'] == '입금' else 1)
                    category = st.selectbox("카테고리", [
                        "매출", "급여", "임대료", "유틸리티", "사무용품", "마케팅",
                        "여행비", "식비", "교육비", "보험료", "세금", "기타"
                    ], index=[
                        "매출", "급여", "임대료", "유틸리티", "사무용품", "마케팅",
                        "여행비", "식비", "교육비", "보험료", "세금", "기타"
                    ].index(transaction_data['category']) if transaction_data['category'] in [
                        "매출", "급여", "임대료", "유틸리티", "사무용품", "마케팅",
                        "여행비", "식비", "교육비", "보험료", "세금", "기타"
                    ] else 11)
                
                with col2:
                    amount = st.number_input("금액", min_value=0.0, value=float(transaction_data['amount']), step=1000.0)
                    currency = st.selectbox("통화", ["KRW", "USD", "VND", "THB", "CNY", "JPY"],
                                          index=["KRW", "USD", "VND", "THB", "CNY", "JPY"].index(transaction_data['currency']) if transaction_data['currency'] in ["KRW", "USD", "VND", "THB", "CNY", "JPY"] else 0)
                    account = st.selectbox("계좌", ["주계좌", "예비계좌", "현금", "신용카드"],
                                         index=["주계좌", "예비계좌", "현금", "신용카드"].index(transaction_data['account']) if transaction_data['account'] in ["주계좌", "예비계좌", "현금", "신용카드"] else 0)
                
                # 추가 정보
                description = st.text_input("거래 설명", value=transaction_data.get('description', ''))
                reference_id = st.text_input("참조 번호", value=transaction_data.get('reference_id', ''))
                notes = st.text_area("비고", value=transaction_data.get('notes', ''))
                
                # 버튼
                col_update, col_delete = st.columns(2)
                
                with col_update:
                    update_submitted = st.form_submit_button("💾 수정", use_container_width=True, type="primary")
                
                with col_delete:
                    delete_submitted = st.form_submit_button("🗑️ 삭제", use_container_width=True, type="secondary")
                
                if update_submitted:
                    if amount <= 0:
                        notifier.show_error("금액은 0보다 커야 합니다.")
                    else:
                        # 수정된 데이터 준비
                        updated_data = {
                            'date': transaction_date.strftime('%Y-%m-%d'),
                            'type': transaction_type,
                            'category': category,
                            'amount': amount,
                            'currency': currency,
                            'description': description,
                            'reference_id': reference_id,
                            'account': account,
                            'notes': notes
                        }
                        
                        # 거래 수정
                        if manager.update_transaction(transaction_id, updated_data):
                            notifier.show_success("거래 정보가 성공적으로 수정되었습니다!")
                            st.rerun()
                        else:
                            notifier.show_error("거래 수정에 실패했습니다.")
                
                if delete_submitted:
                    # 삭제 확인
                    if st.session_state.get('confirm_delete') != transaction_id:
                        st.session_state['confirm_delete'] = transaction_id
                        notifier.show_warning("삭제를 확인하려면 다시 삭제 버튼을 클릭하세요.")
                    else:
                        if manager.delete_transaction(transaction_id):
                            notifier.show_success("거래가 성공적으로 삭제되었습니다!")
                            del st.session_state['confirm_delete']
                            st.rerun()
                        else:
                            notifier.show_error("거래 삭제에 실패했습니다.")
    else:
        st.warning("등록된 거래가 없습니다.")


def show_stock_price_management(manager, notifier):
    """주가 관리 페이지"""
    st.header("📈 주가 관리")
    
    tab1, tab2, tab3 = st.tabs(["주가 등록", "주가 목록", "주가 차트"])
    
    with tab1:
        # 주가 등록
        st.subheader("새 주가 정보 등록")
        
        with st.form("stock_price_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stock_symbol = st.text_input("종목 코드", placeholder="예: 005930")
                stock_name = st.text_input("종목명", placeholder="예: 삼성전자")
                price_date = st.date_input("날짜", value=date.today())
                market = st.selectbox("시장", ["KOSPI", "KOSDAQ", "NYSE", "NASDAQ", "기타"])
            
            with col2:
                price = st.number_input("주가", min_value=0.0, value=0.0, step=100.0)
                currency = st.selectbox("통화", ["KRW", "USD", "VND", "THB", "CNY"])
                change_amount = st.number_input("전일대비 변동액", value=0.0, step=100.0)
                change_percent = st.number_input("전일대비 변동률(%)", value=0.0, step=0.1)
            
            volume = st.number_input("거래량", min_value=0, value=0, step=1000)
            
            submitted = st.form_submit_button("📈 주가 등록", use_container_width=True, type="primary")
            
            if submitted:
                if not stock_symbol or not stock_name or price <= 0:
                    notifier.show_error("종목 코드, 종목명, 주가는 필수 입력 항목입니다.")
                else:
                    # 주가 데이터 준비
                    price_data = {
                        'date': price_date.strftime('%Y-%m-%d'),
                        'stock_symbol': stock_symbol,
                        'stock_name': stock_name,
                        'price': price,
                        'currency': currency,
                        'change_amount': change_amount,
                        'change_percent': change_percent,
                        'volume': volume,
                        'market': market,
                        'source': '수동입력'
                    }
                    
                    # 주가 등록
                    price_id = manager.add_stock_price(price_data)
                    if price_id:
                        notifier.show_success(f"주가 정보가 성공적으로 등록되었습니다! (ID: {price_id})")
                        st.rerun()
                    else:
                        notifier.show_error("주가 등록에 실패했습니다.")
    
    with tab2:
        # 주가 목록
        st.subheader("등록된 주가 정보")
        
        stock_prices = manager.get_all_stock_prices()
        if len(stock_prices) > 0:
            # 표시할 컬럼 설정
            display_columns = ['date', 'stock_symbol', 'stock_name', 'price', 'currency', 'change_percent', 'volume', 'market']
            available_columns = [col for col in display_columns if col in stock_prices.columns]
            
            if available_columns:
                display_df = stock_prices[available_columns].copy()
                
                # 컬럼명 한국어로 변경
                column_mapping = {
                    'date': '날짜',
                    'stock_symbol': '종목코드',
                    'stock_name': '종목명',
                    'price': '주가',
                    'currency': '통화',
                    'change_percent': '변동률(%)',
                    'volume': '거래량',
                    'market': '시장'
                }
                
                rename_dict = {k: v for k, v in column_mapping.items() if k in display_df.columns}
                display_df = display_df.rename(columns=rename_dict)
                
                # 주가 목록 테이블 표시
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 다운로드 버튼
                csv_buffer = io.StringIO()
                stock_prices.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 주가 정보 다운로드",
                    data=csv_buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"stock_prices_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("등록된 주가 정보가 없습니다.")
    
    with tab3:
        # 주가 차트
        st.subheader("주가 차트")
        
        stock_prices = manager.get_all_stock_prices()
        if len(stock_prices) > 0:
            # 종목 선택
            unique_stocks = stock_prices['stock_symbol'].unique()
            selected_stock = st.selectbox("종목 선택", unique_stocks)
            
            if selected_stock:
                # 선택된 종목의 주가 데이터
                stock_data = stock_prices[stock_prices['stock_symbol'] == selected_stock].copy()
                stock_data['date'] = pd.to_datetime(stock_data['date'])
                stock_data = stock_data.sort_values('date')
                
                if len(stock_data) > 0:
                    # 주가 차트
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=stock_data['date'],
                        y=stock_data['price'],
                        mode='lines+markers',
                        name='주가',
                        line=dict(color='#2E86AB', width=2),
                        marker=dict(size=6)
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_stock} 주가 추이",
                        xaxis_title="날짜",
                        yaxis_title="주가",
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 주가 통계
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("현재가", f"₩{stock_data['price'].iloc[-1]:,.0f}")
                    
                    with col2:
                        st.metric("최고가", f"₩{stock_data['price'].max():,.0f}")
                    
                    with col3:
                        st.metric("최저가", f"₩{stock_data['price'].min():,.0f}")
                    
                    with col4:
                        avg_price = stock_data['price'].mean()
                        st.metric("평균가", f"₩{avg_price:,.0f}")
                else:
                    st.info("선택된 종목의 주가 데이터가 없습니다.")
        else:
            st.info("주가 데이터가 없습니다.")


def show_transaction_statistics(manager):
    """거래 통계 페이지"""
    st.header("📊 거래 통계")
    
    transactions = manager.get_all_transactions()
    
    if len(transactions) > 0:
        # 전체 통계
        total_summary = manager.get_transaction_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 수입", f"₩{total_summary['total_income']:,.0f}")
        
        with col2:
            st.metric("총 지출", f"₩{total_summary['total_expense']:,.0f}")
        
        with col3:
            st.metric("순 현금 흐름", f"₩{total_summary['net_amount']:,.0f}")
        
        # 월별 추이 차트
        st.subheader("월별 현금 흐름 추이")
        
        transactions['date'] = pd.to_datetime(transactions['date'])
        transactions['month'] = transactions['date'].dt.to_period('M')
        
        monthly_summary = transactions.groupby(['month', 'type'])['amount'].sum().reset_index()
        monthly_summary['month_str'] = monthly_summary['month'].astype(str)
        
        fig = px.bar(
            monthly_summary,
            x='month_str',
            y='amount',
            color='type',
            title="월별 수입/지출 추이",
            color_discrete_map={'입금': '#2E86AB', '출금': '#F24236'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 카테고리별 분석
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("카테고리별 수입")
            income_data = transactions[transactions['type'] == '입금']
            if len(income_data) > 0:
                income_by_category = income_data.groupby('category')['amount'].sum().reset_index()
                income_by_category = income_by_category.sort_values('amount', ascending=False)
                
                fig = px.bar(
                    income_by_category,
                    x='amount',
                    y='category',
                    orientation='h',
                    title="카테고리별 수입"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("수입 데이터가 없습니다.")
        
        with col2:
            st.subheader("카테고리별 지출")
            expense_data = transactions[transactions['type'] == '출금']
            if len(expense_data) > 0:
                expense_by_category = expense_data.groupby('category')['amount'].sum().reset_index()
                expense_by_category = expense_by_category.sort_values('amount', ascending=False)
                
                fig = px.bar(
                    expense_by_category,
                    x='amount',
                    y='category',
                    orientation='h',
                    title="카테고리별 지출",
                    color_discrete_sequence=['#F24236']
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("지출 데이터가 없습니다.")
    else:
        st.info("거래 데이터가 없습니다.")