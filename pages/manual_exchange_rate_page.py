# -*- coding: utf-8 -*-
"""
수동 환율 관리 페이지
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from managers.legacy.manual_exchange_rate_manager import ManualExchangeRateManager

def show_manual_exchange_rate_page(get_text):
    """수동 환율 관리 페이지를 표시합니다."""
    st.title("💱 환율 관리 (공식 기준)")
    st.markdown("---")
    
    # 환율 매니저 초기화
    if 'manual_exchange_rate_manager' not in st.session_state:
        st.session_state.manual_exchange_rate_manager = ManualExchangeRateManager()
    
    rate_manager = st.session_state.manual_exchange_rate_manager
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 현재 환율",
        "✏️ 환율 입력", 
        "📈 환율 차트",
        "📋 환율 관리"
    ])
    
    with tab1:
        show_current_rates(rate_manager, get_text)
    
    with tab2:
        show_rate_input(rate_manager, get_text)
    
    with tab3:
        show_rate_charts(rate_manager, get_text)
    
    with tab4:
        show_rate_management(rate_manager, get_text)

def show_current_rates(rate_manager, get_text):
    """현재 환율 현황을 표시합니다."""
    st.header("📊 현재 환율 현황")
    
    # 최신 환율 데이터 가져오기
    latest_rates = rate_manager.get_latest_rates()
    
    if len(latest_rates) > 0:
        st.info("💡 모든 환율은 USD 기준이며, KRW/THB/IDR은 한국은행(ECOS), CNY는 CFETS 3M, VND는 SBV 공식 환율 기준입니다.")
        
        # 환율 카드 표시
        cols = st.columns(len(latest_rates))
        
        for idx, (_, row) in enumerate(latest_rates.iterrows()):
            with cols[idx]:
                currency_code = row['currency_code']
                currency_name = row['currency_name']
                rate = float(row['rate'])
                rate_date = row['rate_date']
                input_by = row.get('input_by', '시스템')
                
                # 환율 변화 계산 (전날 대비)
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                history = rate_manager.get_rate_history(currency_code, 2)
                
                delta = None
                if len(history) > 1:
                    prev_rate = float(history.iloc[-2]['rate'])
                    change = rate - prev_rate
                    change_pct = (change / prev_rate) * 100
                    delta = f"{change_pct:+.2f}%"
                
                st.metric(
                    label=f"{currency_name} ({currency_code})",
                    value=f"{rate:,.2f}",
                    delta=delta
                )
                
                st.caption(f"📅 {rate_date}")
                st.caption(f"👤 입력자: {input_by}")
        
        st.markdown("---")
        
        # 전체 환율 테이블
        st.subheader("📋 전체 환율 정보")
        
        display_df = latest_rates[['currency_name', 'currency_code', 'rate', 'rate_date', 'input_by']].copy()
        display_df['rate'] = display_df['rate'].apply(lambda x: f"{float(x):,.2f}")
        display_df.columns = ['통화명', '통화코드', '환율 (USD 기준)', '입력일', '입력자']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    else:
        st.warning("⚠️ 등록된 환율 데이터가 없습니다. 환율을 입력해주세요.")

def show_rate_input(rate_manager, get_text):
    """환율 입력 폼을 표시합니다."""
    st.header("✏️ 환율 입력 (공식 기준)")
    
    st.info("💡 각 통화별 공식 기준에 따른 정확한 환율을 입력해주세요. 평균 환율 대비 5% 이상 차이나는 경우 경고가 표시됩니다.")
    
    # 지원 통화 및 기준 정보 표시
    with st.expander("📖 지원 통화 및 기준 출처"):
        st.markdown("### 🏛️ **환율 기준 출처**")
        
        # 한국은행 기준 통화들
        st.markdown("#### 📊 **한국은행(ECOS) 기준** - [바로가기](https://ecos.bok.or.kr/)")
        st.markdown("- **🇰🇷 대한민국 원 (KRW)**: USD 기준 환율")
        st.markdown("- **🇹🇭 태국 바트 (THB)**: USD 기준 환율") 
        st.markdown("- **🇮🇩 인도네시아 루피아 (IDR)**: USD 기준 환율")
        
        # CFETS 기준
        st.markdown("#### 📊 **CFETS 3M 기준** - [바로가기](https://www.chinamoney.org.cn/english/bmkierertrat6mm/?term=6)")
        st.markdown("- **🇨🇳 중국 위안 (CNY)**: USD 기준 환율")
        
        # SBV 기준
        st.markdown("#### 📊 **SBV 공식 환율 기준** - [바로가기](https://dttktt.sbv.gov.vn/TyGia/faces/TyGia.jspx)")
        st.markdown("- **🇻🇳 베트남 동 (VND)**: USD 기준 환율")
        
        st.markdown("---")
        st.markdown("### 💰 **평균 환율 참고**")
        supported_currencies = rate_manager.get_supported_currencies()
        for currency in supported_currencies:
            flag_map = {
                'KRW': '🇰🇷',
                'THB': '🇹🇭', 
                'IDR': '🇮🇩',
                'CNY': '🇨🇳',
                'VND': '🇻🇳'
            }
            flag = flag_map.get(currency['currency_code'], '💱')
            st.write(f"**{flag} {currency['currency_name']} ({currency['currency_code']})**: {currency['average_rate']:,.2f}")
    
    # 환율 입력 폼
    with st.form("rate_input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            currency_options = [(c['currency_code'], f"{c['currency_name']} ({c['currency_code']})") 
                               for c in rate_manager.get_supported_currencies()]
            currency_code = st.selectbox(
                "통화 선택", 
                options=[code for code, _ in currency_options],
                format_func=lambda x: next(label for code, label in currency_options if code == x)
            )
            
            rate = st.number_input(
                "환율 (USD 기준)", 
                min_value=0.01,
                step=0.01,
                help="한국은행 고시 환율을 정확히 입력해주세요"
            )
        
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
                    key="manual_rate_year"
                )
            with col2_2:
                month = st.selectbox(
                    "월", 
                    options=list(range(1, 13)), 
                    index=current_date.month - 1,
                    format_func=lambda x: f"{x}월",
                    key="manual_rate_month"
                )
            
            input_by = st.text_input(
                "입력자", 
                value=st.session_state.get('current_user', '관리자'),
                help="환율을 입력하는 담당자명을 입력해주세요"
            )
        
        submitted = st.form_submit_button("환율 저장", type="primary")
        
        if submitted:
            if currency_code and rate > 0 and input_by:
                # 월별로 해당 월의 첫째 날로 저장
                rate_date = f"{year}-{month:02d}-01"
                
                # 환율 저장 시도
                success, message, is_valid = rate_manager.add_manual_rate(
                    currency_code, 
                    rate, 
                    input_by, 
                    rate_date
                )
                
                if success:
                    if is_valid:
                        st.success(f"✅ 환율이 성공적으로 저장되었습니다! {message}")
                    else:
                        st.warning(f"⚠️ 환율이 저장되었지만 주의가 필요합니다:\n{message}")
                    st.rerun()
                else:
                    st.error(f"❌ 환율 저장 실패: {message}")
            else:
                st.error("모든 필드를 올바르게 입력해주세요.")

def show_rate_charts(rate_manager, get_text):
    """환율 차트를 표시합니다."""
    st.header("📈 환율 차트")
    
    # 통화 선택
    supported_currencies = rate_manager.get_supported_currencies()
    if len(supported_currencies) > 0:
        currency_options = [(c['currency_code'], f"{c['currency_name']} ({c['currency_code']})") 
                           for c in supported_currencies]
        
        selected_currency = st.selectbox(
            "통화 선택", 
            options=[code for code, _ in currency_options],
            format_func=lambda x: next(label for code, label in currency_options if code == x)
        )
        
        # 기간 선택
        col1, col2 = st.columns(2)
        with col1:
            period_options = {
                "전체 기간": None,
                "최근 365일": 365,
                "최근 180일": 180,
                "최근 90일": 90,
                "최근 60일": 60,
                "최근 30일": 30,
                "최근 14일": 14,
                "최근 7일": 7
            }
            period_label = st.selectbox("조회 기간", list(period_options.keys()), index=0)
            period_days = period_options[period_label]
        with col2:
            chart_type = st.selectbox("차트 유형", ["선 그래프", "영역 차트"])
        
        # 히스토리 데이터 가져오기
        history_data = rate_manager.get_rate_history(selected_currency, period_days)
        
        if len(history_data) > 0:
            # 차트 생성
            fig = None
            if chart_type == "선 그래프":
                fig = px.line(
                    history_data, 
                    x='rate_date', 
                    y='rate',
                    title=f"{selected_currency} 환율 추이 ({period_label})",
                    labels={'rate_date': '날짜', 'rate': '환율 (USD 기준)'}
                )
            else:  # 영역 차트
                fig = px.area(
                    history_data, 
                    x='rate_date', 
                    y='rate',
                    title=f"{selected_currency} 환율 추이 ({period_label})",
                    labels={'rate_date': '날짜', 'rate': '환율 (USD 기준)'}
                )
            
            fig.update_layout(
                xaxis_title="날짜",
                yaxis_title="환율 (USD 기준)",
                hovermode='x'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 통계 정보
            stats = rate_manager.get_rate_statistics(selected_currency)
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("현재 환율", f"{stats['current_rate']:,.2f}")
                with col2:
                    st.metric("평균 환율", f"{stats['avg_rate']:,.2f}")
                with col3:
                    st.metric("최저 환율", f"{stats['min_rate']:,.2f}")
                with col4:
                    st.metric("최고 환율", f"{stats['max_rate']:,.2f}")
        else:
            st.info(f"{selected_currency} 통화의 환율 데이터가 없습니다.")
    
    else:
        st.warning("지원하는 통화가 없습니다.")

def show_rate_management(rate_manager, get_text):
    """환율 데이터 관리 기능을 표시합니다."""
    st.header("📋 환율 데이터 관리")
    
    # 전체 환율 데이터 가져오기
    if os.path.exists(rate_manager.data_file):
        all_rates = pd.read_csv(rate_manager.data_file, encoding='utf-8-sig')
        
        if len(all_rates) > 0:
            # 필터링 옵션
            col1, col2 = st.columns(2)
            with col1:
                currency_filter = st.selectbox(
                    "통화 필터", 
                    ["전체"] + list(all_rates['currency_code'].unique())
                )
            with col2:
                filter_options = {
                    "전체 기간": None,
                    "최근 365일": 365,
                    "최근 180일": 180,
                    "최근 90일": 90,
                    "최근 60일": 60,
                    "최근 30일": 30,
                    "최근 14일": 14,
                    "최근 7일": 7
                }
                filter_label = st.selectbox("기간 필터", list(filter_options.keys()), index=0)
                days_filter = filter_options[filter_label]
            
            # 필터링 적용
            filtered_data = all_rates.copy()
            
            if currency_filter != "전체":
                filtered_data = filtered_data[filtered_data['currency_code'] == currency_filter]
            
            # 날짜 필터링 (전체 기간이 아닐 경우만)
            if days_filter is not None:
                cutoff_date = (datetime.now() - timedelta(days=days_filter)).strftime('%Y-%m-%d')
                filtered_data = filtered_data[filtered_data['rate_date'] >= cutoff_date]
            
            # 데이터 표시
            st.subheader(f"📊 환율 데이터 ({len(filtered_data)}건)")
            
            if len(filtered_data) > 0:
                if currency_filter == "전체":
                    # 전체 통화를 선택했을 때 날짜별로 통합 테이블 생성
                    
                    # 피벗 테이블 생성 (날짜별로 각 통화 환율을 열로 배치)
                    pivot_data = filtered_data.pivot_table(
                        values='rate', 
                        index='rate_date', 
                        columns='currency_code', 
                        aggfunc='first'
                    ).reset_index()
                    
                    # 날짜순 정렬
                    pivot_data = pivot_data.sort_values('rate_date')
                    
                    # 컬럼명 설정
                    flag_map = {
                        'KRW': '🇰🇷 KRW',
                        'THB': '🇹🇭 THB', 
                        'IDR': '🇮🇩 IDR',
                        'CNY': '🇨🇳 CNY',
                        'VND': '🇻🇳 VND'
                    }
                    
                    # 컬럼명 변경
                    renamed_columns = {'rate_date': '📅 입력일'}
                    for col in pivot_data.columns:
                        if col != 'rate_date':
                            renamed_columns[col] = flag_map.get(col, col)
                    
                    pivot_data = pivot_data.rename(columns=renamed_columns)
                    
                    # 환율 값을 포맷팅
                    for col in pivot_data.columns:
                        if col != '📅 입력일':
                            pivot_data[col] = pivot_data[col].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else "-")
                    
                    # 날짜 포맷팅
                    pivot_data['📅 입력일'] = pd.to_datetime(pivot_data['📅 입력일']).dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(pivot_data, use_container_width=True, hide_index=True)
                    
                else:
                    # 특정 통화만 선택했을 때
                    display_columns = ['currency_name', 'currency_code', 'rate', 'rate_date', 'input_by', 'rate_id']
                    display_data = filtered_data[display_columns].copy().sort_values('rate_date')
                    display_data['rate'] = display_data['rate'].apply(lambda x: f"{float(x):,.2f}")
                    display_data.columns = ['통화명', '통화코드', '환율', '입력일', '입력자', 'ID']
                    
                    # 데이터 테이블로 표시
                    st.dataframe(display_data.drop(columns=['ID']), use_container_width=True, hide_index=True)
                
                # 삭제 기능
                st.subheader("🗑️ 데이터 삭제")
                col1, col2 = st.columns(2)
                with col1:
                    rate_options = list(filtered_data['rate_id'])
                    rate_labels = {}
                    for rate_id in rate_options:
                        row = filtered_data[filtered_data['rate_id'] == rate_id].iloc[0]
                        rate_labels[rate_id] = f"{row['currency_name']} ({row['currency_code']}) - {row['rate_date']}"
                    
                    rate_to_delete = st.selectbox(
                        "삭제할 데이터 선택",
                        options=[""] + rate_options,
                        format_func=lambda x: rate_labels.get(x, "선택하세요") if x else "선택하세요"
                    )
                with col2:
                    if rate_to_delete and st.button("🗑️ 삭제 확인"):
                        success, message = rate_manager.delete_rate(rate_to_delete)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.info("선택한 조건에 맞는 데이터가 없습니다.")
        else:
            st.info("등록된 환율 데이터가 없습니다.")
    else:
        st.info("환율 데이터 파일이 없습니다.")