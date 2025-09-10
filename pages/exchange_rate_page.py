import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go

def show_exchange_rate_page(exchange_rate_manager, user_permissions, get_text):
    """환율 관리 페이지를 표시합니다."""
    
    st.header("💱 환율 관리")
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💱 현재 환율",
        "📅 분기별 기준환율",
        "📈 환율 차트",
        "📊 환율 통계",
        "🔍 환율 검색",
        "📝 환율 입력",
        "📥 환율 다운로드"
    ])
    
    with tab1:
        st.header("💱 현재 환율 (USD 기준)")
        
        # 환율 업데이트 버튼
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 환율 업데이트"):
                with st.spinner("환율을 업데이트하는 중..."):
                    try:
                        exchange_rate_manager.update_exchange_rates()
                        st.success("환율이 성공적으로 업데이트되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"환율 업데이트 중 오류가 발생했습니다: {e}")
        
        with col2:
            if st.button("⚡ 강제 업데이트"):
                with st.spinner("강제 환율 업데이트 중..."):
                    try:
                        exchange_rate_manager.force_update_exchange_rates()
                        st.success("환율이 강제로 업데이트되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"강제 업데이트 중 오류가 발생했습니다: {e}")
        
        try:
            # 최신 환율 가져오기
            latest_rates = exchange_rate_manager.get_latest_rates()
            
            if len(latest_rates) > 0:
                # 환율 업데이트 시간 표시
                latest_update = latest_rates['rate_date'].max()
                st.info(f"마지막 업데이트: {latest_update}")
                
                # 주요 통화 환율 표시
                major_currencies = ['KRW', 'CNY', 'VND', 'THB', 'IDR', 'MYR']
                
                st.subheader("주요 통화 환율")
                cols = st.columns(len(major_currencies))
                
                for i, currency in enumerate(major_currencies):
                    with cols[i]:
                        rate_data = latest_rates[latest_rates['currency_code'] == currency]
                        if len(rate_data) > 0:
                            rate = rate_data.iloc[0]['rate']
                            currency_name = rate_data.iloc[0]['currency_name']
                            
                            # 환율 변화 계산 (전일 대비)
                            yesterday = datetime.now() - timedelta(days=1)
                            yesterday_rate = exchange_rate_manager.get_rate_by_currency(
                                currency, yesterday.strftime('%Y-%m-%d')
                            )
                            
                            if yesterday_rate:
                                change = rate - yesterday_rate
                                change_pct = (change / yesterday_rate) * 100
                                delta = f"{change_pct:+.2f}%"
                            else:
                                delta = None
                            
                            st.metric(
                                label=f"{currency_name} ({currency})",
                                value=f"{rate:,.4f}",
                                delta=delta
                            )
                        else:
                            st.warning(f"{currency} 환율 정보 없음")
                
                # 전체 환율 테이블
                st.subheader("전체 환율 정보")
                display_columns = ['currency_name', 'currency_code', 'rate', 'rate_date']
                column_mapping = {
                    'currency_name': '통화명',
                    'currency_code': '통화코드',
                    'rate': '환율',
                    'rate_date': '업데이트 시간'
                }
                
                latest_rates_display = latest_rates[display_columns].copy()
                # 환율 데이터를 안전하게 float로 변환하고 포맷팅
                latest_rates_display['rate'] = latest_rates_display['rate'].apply(
                    lambda x: f"{float(x):,.4f}" if isinstance(x, (int, float)) else f"{float(x['rate']) if isinstance(x, dict) and 'rate' in x else 0.0:,.4f}"
                )
                
                st.dataframe(
                    latest_rates_display.rename(columns=column_mapping),
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.warning("환율 데이터가 없습니다. 환율 업데이트를 실행해주세요.")
                
        except Exception as e:
            st.error(f"환율 정보를 불러오는 중 오류가 발생했습니다: {e}")
    
    with tab2:
        st.header("📅 분기별 기준환율 (한국은행 기준)")
        
        # 분기별 환율 입력 섹션
        st.subheader("🔧 분기별 환율 입력")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 연도 선택 (2025년부터)
            current_year = datetime.now().year
            year_options = list(range(2025, current_year + 3))
            selected_year = st.selectbox("연도", year_options, index=0 if current_year < 2025 else year_options.index(current_year))
        
        with col2:
            # 분기 선택
            quarter_options = [1, 2, 3, 4]
            current_quarter = (datetime.now().month - 1) // 3 + 1
            selected_quarter = st.selectbox("분기", quarter_options, 
                                          index=current_quarter-1 if selected_year == current_year else 0)
        
        with col3:
            # 통화 선택
            currency_options = ["USD", "CNY", "VND", "EUR", "JPY"]
            selected_currency = st.selectbox("통화", currency_options)
        
        with col4:
            # 환율 입력
            exchange_rate = st.number_input("환율 (KRW 기준)", min_value=0.0, step=0.01, format="%.2f")
        
        # 환율 저장 버튼
        if st.button("💾 분기별 환율 저장", key="save_quarterly_rate"):
            if exchange_rate > 0:
                success, message = exchange_rate_manager.add_quarterly_rate(
                    selected_year, selected_quarter, selected_currency, exchange_rate, 
                    created_by="admin"
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("환율을 올바르게 입력해주세요.")
        
        st.divider()
        
        # 분기별 환율 조회 섹션
        st.subheader("📊 등록된 분기별 환율")
        
        # 조회 필터
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_year = st.selectbox("조회 연도", ["전체"] + year_options, key="filter_year")
        with col2:
            filter_quarter = st.selectbox("조회 분기", ["전체"] + quarter_options, key="filter_quarter")
        with col3:
            if st.button("🔍 조회", key="search_quarterly"):
                st.rerun()
        
        try:
            # 분기별 환율 데이터 조회
            search_year = None if filter_year == "전체" else filter_year
            search_quarter = None if filter_quarter == "전체" else filter_quarter
            
            quarterly_data = exchange_rate_manager.get_quarterly_rates(search_year, search_quarter)
            
            if len(quarterly_data) > 0:
                # 분기명 추가
                quarterly_data['분기'] = quarterly_data['year'].astype(str) + "년 " + quarterly_data['quarter'].astype(str) + "분기"
                
                # 표시용 데이터 준비
                display_data = quarterly_data[['분기', 'target_currency', 'currency_name', 'rate', 'created_by', 'updated_date']].copy()
                display_data.columns = ['분기', '통화코드', '통화명', '환율(KRW)', '등록자', '수정일시']
                
                # 환율 포맷팅
                display_data['환율(KRW)'] = display_data['환율(KRW)'].apply(lambda x: f"{x:,.2f}")
                
                st.dataframe(display_data, use_container_width=True, hide_index=True)
                
                # 통계 정보
                st.subheader("📈 분기별 환율 통계")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("등록된 분기 수", len(quarterly_data['분기'].unique()))
                with col2:
                    st.metric("등록된 통화 수", len(quarterly_data['target_currency'].unique()))
                with col3:
                    if selected_year == current_year and selected_quarter == current_quarter:
                        current_rate = exchange_rate_manager.get_current_quarter_rate(selected_currency)
                        if current_rate:
                            st.metric(f"현재분기 {selected_currency}", f"{current_rate:,.2f}")
                        else:
                            st.metric(f"현재분기 {selected_currency}", "미등록")
                    else:
                        st.metric("현재분기", f"{current_year}년 {current_quarter}분기")
                with col4:
                    avg_rate = quarterly_data['rate'].mean()
                    st.metric("평균 환율", f"{avg_rate:,.2f}")
                
            else:
                st.info("등록된 분기별 환율이 없습니다. 위에서 환율을 입력해주세요.")
                
        except Exception as e:
            st.error(f"분기별 환율 조회 중 오류가 발생했습니다: {e}")
    
    with tab3:
        st.header("📈 환율 차트")
        
        # 통화 선택
        supported_currencies = exchange_rate_manager.get_supported_currencies()
        if len(supported_currencies) > 0:
            currency_options = [f"{row['currency_name']} ({row['currency_code']})" 
                              for row in supported_currencies]
            selected_currency = st.selectbox("통화 선택", currency_options, key="chart_currency")
            
            if selected_currency:
                currency_code = selected_currency.split('(')[-1].rstrip(')')
                
                # 기간 선택
                col1, col2 = st.columns(2)
                with col1:
                    period_options = [7, 14, 30, 60, 90]
                    selected_period = st.selectbox("조회 기간 (일)", period_options, index=2, key="chart_period")
                
                with col2:
                    chart_type = st.selectbox("차트 유형", ["선 그래프", "캔들스틱", "영역 차트"], key="chart_type")
                
                try:
                    # 히스토리 데이터 가져오기
                    historical_data = exchange_rate_manager.get_historical_rates(
                        currency_code, days=selected_period
                    )
                    
                    if len(historical_data) > 0:
                        historical_data['rate_date'] = pd.to_datetime(historical_data['rate_date'])
                        historical_data = historical_data.sort_values('rate_date')
                        
                        if chart_type == "선 그래프":
                            fig = px.line(
                                historical_data, 
                                x='rate_date', 
                                y='rate',
                                title=f"{selected_currency} 환율 추이 ({selected_period}일)",
                                labels={'rate_date': '날짜', 'rate': '환율'}
                            )
                            
                        elif chart_type == "영역 차트":
                            fig = px.area(
                                historical_data,
                                x='rate_date',
                                y='rate',
                                title=f"{selected_currency} 환율 추이 ({selected_period}일)",
                                labels={'rate_date': '날짜', 'rate': '환율'}
                            )
                        
                        else:  # 캔들스틱
                            # 일일 집계 데이터 생성
                            daily_data = historical_data.groupby(historical_data['rate_date'].dt.date).agg({
                                'rate': ['min', 'max', 'first', 'last']
                            }).round(4)
                            daily_data.columns = ['low', 'high', 'open', 'close']
                            daily_data = daily_data.reset_index()
                            
                            fig = go.Figure(data=go.Candlestick(
                                x=daily_data['rate_date'],
                                open=daily_data['open'],
                                high=daily_data['high'],
                                low=daily_data['low'],
                                close=daily_data['close']
                            ))
                            fig.update_layout(
                                title=f"{selected_currency} 환율 캔들스틱 차트 ({selected_period}일)",
                                xaxis_title="날짜",
                                yaxis_title="환율"
                            )
                        
                        fig.update_layout(
                            xaxis_title="날짜",
                            yaxis_title="환율",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 통계 정보
                        st.subheader("기간 통계")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("최고값", f"{historical_data['rate'].max():,.4f}")
                        with col2:
                            st.metric("최저값", f"{historical_data['rate'].min():,.4f}")
                        with col3:
                            st.metric("평균값", f"{historical_data['rate'].mean():,.4f}")
                        with col4:
                            rate_change = historical_data['rate'].iloc[-1] - historical_data['rate'].iloc[0]
                            change_pct = (rate_change / historical_data['rate'].iloc[0]) * 100
                            st.metric("기간 변화율", f"{change_pct:+.2f}%")
                        
                    else:
                        st.warning(f"{currency_code}의 히스토리 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"차트 생성 중 오류가 발생했습니다: {e}")
        
        else:
            st.warning("지원되는 통화가 없습니다.")
    
    with tab3:
        st.header("📊 환율 통계")
        
        # 통화 선택
        supported_currencies = exchange_rate_manager.get_supported_currencies()
        if len(supported_currencies) > 0:
            currency_options = [f"{row['currency_name']} ({row['currency_code']})" 
                              for row in supported_currencies]
            selected_currency = st.selectbox("통계 조회 통화", currency_options)
            
            if selected_currency:
                currency_code = selected_currency.split('(')[-1].rstrip(')')
                
                # 통계 기간 선택
                period_options = [7, 14, 30, 60, 90]
                selected_period = st.selectbox("통계 기간 (일)", period_options, index=2)
                
                try:
                    stats = exchange_rate_manager.get_rate_statistics(currency_code, days=selected_period)
                    
                    if stats:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("기본 통계")
                            max_rate = float(stats.get('max_rate', 0)) if isinstance(stats.get('max_rate'), (int, float)) else 0.0
                            min_rate = float(stats.get('min_rate', 0)) if isinstance(stats.get('min_rate'), (int, float)) else 0.0
                            avg_rate = float(stats.get('avg_rate', 0)) if isinstance(stats.get('avg_rate'), (int, float)) else 0.0
                            std_rate = float(stats.get('std_rate', 0)) if isinstance(stats.get('std_rate'), (int, float)) else 0.0
                            
                            st.metric("최고 환율", f"{max_rate:,.4f}")
                            st.metric("최저 환율", f"{min_rate:,.4f}")
                            st.metric("평균 환율", f"{avg_rate:,.4f}")
                            st.metric("표준편차", f"{std_rate:,.4f}")
                        
                        with col2:
                            st.subheader("변동성 지표")
                            volatility = (std_rate / avg_rate) * 100 if avg_rate > 0 else 0.0
                            st.metric("변동성 (%)", f"{volatility:.2f}%")
                            
                            price_range = max_rate - min_rate
                            range_pct = (price_range / avg_rate) * 100 if avg_rate > 0 else 0.0
                            st.metric("가격 범위 (%)", f"{range_pct:.2f}%")
                            
                            st.metric("데이터 포인트", stats['data_points'])
                        
                        # 분기별/월별 평균
                        st.subheader("기간별 평균 환율")
                        
                        tab_quarter, tab_month = st.tabs(["분기별", "월별"])
                        
                        with tab_quarter:
                            current_year = datetime.now().year
                            quarters = [1, 2, 3, 4]
                            
                            quarter_data = []
                            for quarter in quarters:
                                try:
                                    avg_rate = exchange_rate_manager.get_quarterly_average_rate(
                                        currency_code, current_year, quarter
                                    )
                                    # avg_rate가 None이 아니고 유효한 숫자인지 확인
                                    if avg_rate is not None and isinstance(avg_rate, (int, float)):
                                        quarter_data.append({
                                            'quarter': f"{current_year}Q{quarter}",
                                            'average_rate': float(avg_rate)
                                        })
                                except Exception as e:
                                    print(f"분기별 환율 조회 오류: {e}")
                                    continue
                            
                            if quarter_data:
                                quarter_df = pd.DataFrame(quarter_data)
                                st.dataframe(quarter_df, use_container_width=True)
                        
                        with tab_month:
                            current_year = datetime.now().year
                            months = range(1, 13)
                            
                            month_data = []
                            for month in months:
                                try:
                                    avg_rate = exchange_rate_manager.get_monthly_average_rate(
                                        currency_code, current_year, month
                                    )
                                    # avg_rate가 None이 아니고 유효한 숫자인지 확인
                                    if avg_rate is not None and isinstance(avg_rate, (int, float)):
                                        month_name = datetime(current_year, month, 1).strftime('%Y-%m')
                                        month_data.append({
                                            'month': month_name,
                                            'average_rate': float(avg_rate)
                                        })
                                except Exception as e:
                                    print(f"월별 환율 조회 오류: {e}")
                                    continue
                            
                            if month_data:
                                month_df = pd.DataFrame(month_data)
                                st.dataframe(month_df, use_container_width=True)
                                
                                # 월별 추이 차트
                                fig = px.line(
                                    month_df, 
                                    x='month', 
                                    y='average_rate',
                                    title=f"{selected_currency} 월별 평균 환율 추이 ({current_year})",
                                    labels={'month': '월', 'average_rate': '평균 환율'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.warning(f"{currency_code}의 통계 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"통계 조회 중 오류가 발생했습니다: {e}")
        
        else:
            st.warning("지원되는 통화가 없습니다.")
    
    with tab4:
        st.header("🔍 환율 검색")
        
        # 검색 옵션
        with st.expander("검색 조건", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # 통화 선택
                supported_currencies = exchange_rate_manager.get_supported_currencies()
                if len(supported_currencies) > 0:
                    currency_options = ["전체"] + [f"{row['currency_name']} ({row['currency_code']})" 
                                                  for row in supported_currencies]
                    selected_currency = st.selectbox("통화", currency_options)
                
                # 날짜 범위
                # 시작 날짜 - 월별 입력
                col_start_1, col_start_2 = st.columns(2) 
                with col_start_1:
                    start_year = st.selectbox(
                        "시작 연도",
                        options=list(range(2020, 2030)),
                        index=list(range(2020, 2030)).index(datetime.now().year),
                        key="search_start_year"
                    )
                with col_start_2:
                    start_month = st.selectbox(
                        "시작 월",
                        options=list(range(1, 13)),
                        index=0,
                        format_func=lambda x: f"{x}월",
                        key="search_start_month"
                    )
                start_date = datetime(start_year, start_month, 1).date()
                
                # 종료 날짜 - 월별 입력
                col_end_1, col_end_2 = st.columns(2)
                with col_end_1:
                    end_year = st.selectbox(
                        "종료 연도",
                        options=list(range(2020, 2030)),
                        index=list(range(2020, 2030)).index(datetime.now().year),
                        key="search_end_year"
                    )
                with col_end_2:
                    end_month = st.selectbox(
                        "종료 월",
                        options=list(range(1, 13)),
                        index=datetime.now().month - 1,
                        format_func=lambda x: f"{x}월",
                        key="search_end_month"
                    )
                # 해당 월의 마지막 날로 설정
                import calendar
                last_day = calendar.monthrange(end_year, end_month)[1]
                end_date = datetime(end_year, end_month, last_day).date()
            
            with col2:
                # 환율 범위
                min_rate = st.number_input("최소 환율", min_value=0.0, value=0.0)
                max_rate = st.number_input("최대 환율", min_value=0.0, value=10000.0)
                
                # 정렬 옵션
                sort_options = ["날짜 (최신순)", "날짜 (오래된순)", "환율 (높은순)", "환율 (낮은순)"]
                sort_option = st.selectbox("정렬", sort_options)
            
            if st.button("검색 실행"):
                try:
                    # 모든 환율 데이터 가져오기
                    all_rates = exchange_rate_manager.get_all_rates()
                    
                    # 필터 적용
                    filtered_rates = all_rates.copy()
                    
                    # 통화 필터
                    if selected_currency != "전체":
                        currency_code = selected_currency.split('(')[-1].rstrip(')')
                        filtered_rates = filtered_rates[filtered_rates['currency_code'] == currency_code]
                    
                    # 날짜 필터
                    filtered_rates['rate_date'] = pd.to_datetime(filtered_rates['rate_date'])
                    filtered_rates = filtered_rates[
                        (filtered_rates['rate_date'].dt.date >= start_date) &
                        (filtered_rates['rate_date'].dt.date <= end_date)
                    ]
                    
                    # 환율 범위 필터
                    filtered_rates = filtered_rates[
                        (filtered_rates['rate'] >= min_rate) &
                        (filtered_rates['rate'] <= max_rate)
                    ]
                    
                    # 정렬
                    if sort_option == "날짜 (최신순)":
                        filtered_rates = filtered_rates.sort_values('rate_date', ascending=False)
                    elif sort_option == "날짜 (오래된순)":
                        filtered_rates = filtered_rates.sort_values('rate_date', ascending=True)
                    elif sort_option == "환율 (높은순)":
                        filtered_rates = filtered_rates.sort_values('rate', ascending=False)
                    else:  # 환율 (낮은순)
                        filtered_rates = filtered_rates.sort_values('rate', ascending=True)
                    
                    if len(filtered_rates) > 0:
                        st.success(f"검색 결과: {len(filtered_rates)}건")
                        
                        # 페이지네이션
                        items_per_page = 20
                        total_items = len(filtered_rates)
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
                            page_data = filtered_rates.iloc[start_idx:end_idx]
                        else:
                            page_data = filtered_rates
                        
                        # 결과 표시
                        display_columns = ['currency_name', 'currency_code', 'rate', 'rate_date']
                        column_mapping = {
                            'currency_name': '통화명',
                            'currency_code': '통화코드',
                            'rate': '환율',
                            'rate_date': '날짜'
                        }
                        
                        st.dataframe(
                            page_data[display_columns].rename(columns=column_mapping),
                            use_container_width=True
                        )
                        
                        # 다운로드 버튼
                        csv_data = filtered_rates.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 검색 결과 다운로드 (CSV)",
                            data=csv_data,
                            file_name=f"exchange_rates_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        st.warning("검색 조건에 맞는 환율 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"검색 중 오류가 발생했습니다: {e}")
    
    with tab5:
        st.header("📝 환율 입력 (한국은행 기준)")
        
        if user_permissions.get('can_edit_data', False):
            with st.form("manual_rate_form"):
                st.subheader("🔧 지원 통화 및 평균 환율 참고")
                
                # 통화 선택 섹션
                st.write("통화 선택")
                currency_code = st.selectbox(
                    "통화 선택", 
                    ["대한민국 원 (KRW)", "중국 위안 (CNY)", "미국 달러 (USD)", "베트남 동 (VND)", "유로 (EUR)", "일본 엔 (JPY)"]
                )
                
                # 통화 코드 추출
                currency_map = {
                    "대한민국 원 (KRW)": ("KRW", "대한민국 원"),
                    "중국 위안 (CNY)": ("CNY", "중국 위안"), 
                    "미국 달러 (USD)": ("USD", "미국 달러"),
                    "베트남 동 (VND)": ("VND", "베트남 동"),
                    "유로 (EUR)": ("EUR", "유로"),
                    "일본 엔 (JPY)": ("JPY", "일본 엔")
                }
                actual_currency_code, currency_name = currency_map[currency_code]
                
                # 환율 및 날짜 입력 섹션
                col1, col2 = st.columns(2)
                with col1:
                    rate = st.number_input("환율 (USD 기준)", min_value=0.01, value=0.01, step=0.01, format="%.2f")
                    
                with col2:
                    st.write("환율 적용일")
                    # 월별 입력으로 변경
                    current_date = datetime.now()
                    col2_1, col2_2 = st.columns(2)
                    with col2_1:
                        year = st.selectbox(
                            "연도", 
                            options=list(range(2020, 2030)), 
                            index=list(range(2020, 2030)).index(current_date.year),
                            key="rate_input_year"
                        )
                    with col2_2:
                        month = st.selectbox(
                            "월", 
                            options=list(range(1, 13)), 
                            index=current_date.month - 1,
                            format_func=lambda x: f"{x}월",
                            key="rate_input_month"
                        )
                
                # 입력자와 관리자 정보
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("입력자", value="관리자", disabled=True)
                with col2:
                    st.text_input("관리자", value="관리자", disabled=True)
                
                submitted = st.form_submit_button("환율 저장", type="primary")
                
                if submitted:
                    if actual_currency_code and currency_name and rate > 0:
                        try:
                            # 월별로 해당 월의 첫째 날로 저장
                            rate_date = f"{year}-{month:02d}-01"
                            
                            success = exchange_rate_manager.add_manual_rate(
                                actual_currency_code, 
                                currency_name, 
                                rate, 
                                rate_date
                            )
                            
                            if success:
                                st.success(f"{actual_currency_code} 환율이 성공적으로 추가되었습니다!")
                                st.rerun()
                            else:
                                st.error("환율 추가에 실패했습니다.")
                                
                        except Exception as e:
                            st.error(f"환율 추가 중 오류가 발생했습니다: {e}")
                    else:
                        st.error("모든 필수 정보를 입력해주세요.")
        
        else:
            st.warning("환율 입력 권한이 없습니다.")
    
    with tab6:
        st.header("📥 환율 다운로드")
        
        # 다운로드 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            download_type = st.selectbox(
                "다운로드 유형",
                ["전체 환율 데이터", "최신 환율만", "특정 통화", "날짜 범위"]
            )
        
        with col2:
            file_format = st.selectbox("파일 형식", ["CSV", "Excel"])
        
        # 옵션별 설정
        if download_type == "특정 통화":
            supported_currencies = exchange_rate_manager.get_supported_currencies()
            if len(supported_currencies) > 0:
                currency_options = [f"{row['currency_name']} ({row['currency_code']})" 
                                  for row in supported_currencies]
                selected_currency = st.selectbox("통화 선택", currency_options)
        
        elif download_type == "날짜 범위":
            col1, col2 = st.columns(2)
            with col1:
                st.write("시작 월")
                col1_1, col1_2 = st.columns(2)
                with col1_1:
                    dl_start_year = st.selectbox(
                        "연도",
                        options=list(range(2020, 2030)),
                        index=list(range(2020, 2030)).index(datetime.now().year),
                        key="dl_start_year"
                    )
                with col1_2:
                    dl_start_month = st.selectbox(
                        "월",
                        options=list(range(1, 13)),
                        index=0,
                        format_func=lambda x: f"{x}월",
                        key="dl_start_month"
                    )
                start_date = datetime(dl_start_year, dl_start_month, 1).date()
                
            with col2:
                st.write("종료 월")
                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    dl_end_year = st.selectbox(
                        "연도",
                        options=list(range(2020, 2030)),
                        index=list(range(2020, 2030)).index(datetime.now().year),
                        key="dl_end_year"
                    )
                with col2_2:
                    dl_end_month = st.selectbox(
                        "월",
                        options=list(range(1, 13)),
                        index=datetime.now().month - 1,
                        format_func=lambda x: f"{x}월",
                        key="dl_end_month"
                    )
                # 해당 월의 마지막 날로 설정
                last_day = calendar.monthrange(dl_end_year, dl_end_month)[1]
                end_date = datetime(dl_end_year, dl_end_month, last_day).date()
        
        if st.button("다운로드 실행"):
            try:
                # 데이터 가져오기
                if download_type == "전체 환율 데이터":
                    data = exchange_rate_manager.get_all_rates()
                    filename = f"all_exchange_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                elif download_type == "최신 환율만":
                    data = exchange_rate_manager.get_latest_rates()
                    filename = f"latest_exchange_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                elif download_type == "특정 통화":
                    currency_code = selected_currency.split('(')[-1].rstrip(')')
                    data = exchange_rate_manager.get_all_rates()
                    data = data[data['currency_code'] == currency_code]
                    filename = f"{currency_code}_exchange_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                else:  # 날짜 범위
                    data = exchange_rate_manager.get_all_rates()
                    data['rate_date'] = pd.to_datetime(data['rate_date'])
                    data = data[
                        (data['rate_date'].dt.date >= start_date) &
                        (data['rate_date'].dt.date <= end_date)
                    ]
                    filename = f"exchange_rates_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
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
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            data.to_excel(writer, sheet_name='환율데이터', index=False)
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label="📥 Excel 다운로드",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    st.success(f"총 {len(data)}건의 환율 데이터를 다운로드할 수 있습니다.")
                    
                else:
                    st.warning("선택한 조건에 맞는 환율 데이터가 없습니다.")
                    
            except Exception as e:
                st.error(f"다운로드 중 오류가 발생했습니다: {e}")