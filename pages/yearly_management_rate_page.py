"""
환율 관리 페이지
- 연도별 관리 환율 조회
- 관리 환율 입력/수정
- 환율 데이터 관리
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def show_yearly_management_rate_page(get_text):
    """환율 관리 메인 페이지"""
    st.title("📊 연도별 관리 환율 관리")
    
    # 환율 매니저 초기화
    from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager
    rate_manager = SQLiteExchangeRateManager()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "📈 관리 환율 조회",
        "✏️ 관리 환율 입력", 
        "⚙️ 환율 관리"
    ])
    
    with tab1:
        show_management_rates_view(rate_manager, get_text)
    
    with tab2:
        show_management_rate_input(rate_manager, get_text)
        
    with tab3:
        show_management_rate_management(rate_manager, get_text)

def show_management_rates_view(rate_manager, get_text):
    """관리 환율 조회 화면"""
    
    # 데이터 조회
    try:
        # 전체 데이터를 가져와서 피벗 테이블 형태로 표시
        all_management_data = rate_manager.get_yearly_management_rates()
        
        if all_management_data.empty:
            # 데이터가 없는 경우 - 빈 테이블 구조만 표시
            empty_data = pd.DataFrame({
                '연도': [],
                'CNY (CN)': [],
                'VND (VN)': [],
                'THB (TH)': [],
                'KRW (KR)': [],
                'IDR (ID)': []
            })
            st.dataframe(empty_data, use_container_width=True, hide_index=True)
            return
        
        # 피벗 테이블 생성
        pivot_data = all_management_data.pivot_table(
            values='rate',
            index='year',
            columns='target_currency',
            aggfunc='first'
        ).reset_index()
        
        # 연도순 정렬 (최신년도 상단)
        pivot_data = pivot_data.sort_values('year', ascending=False)
        
        # 통화 컬럼 순서 정렬
        currency_columns = [col for col in pivot_data.columns if col != 'year']
        # 이미지 순서대로 정렬: CNY, VND, THB, KRW, IDR
        preferred_order = ['CNY', 'VND', 'THB', 'KRW', 'IDR']
        sorted_columns = []
        for currency in preferred_order:
            if currency in currency_columns:
                sorted_columns.append(currency)
        # 나머지 통화 추가
        for currency in currency_columns:
            if currency not in sorted_columns:
                sorted_columns.append(currency)
        
        # 컬럼 순서 재배치
        ordered_columns = ['year'] + sorted_columns
        pivot_data = pivot_data[ordered_columns]
        
        # 컬럼명 변경
        column_names = {'year': '연도'}
        country_code_map = {
            'CNY': 'CNY (CN)',
            'VND': 'VND (VN)', 
            'THB': 'THB (TH)',
            'KRW': 'KRW (KR)',
            'IDR': 'IDR (ID)'
        }
        
        for col in sorted_columns:
            column_names[col] = country_code_map.get(col, col)
        
        # 컬럼명 변경
        pivot_data.rename(columns=column_names, inplace=True)
        
        # NaN 값을 '0.00'으로 처리하고 숫자 포맷 적용
        for col in pivot_data.columns:
            if col != '연도':
                pivot_data[col] = pivot_data[col].apply(
                    lambda x: f"{float(x):.2f}" if pd.notna(x) else '0.00'
                )
        
        # 테이블 표시
        st.dataframe(pivot_data, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {str(e)}")

def show_management_rate_input(rate_manager, get_text):
    """관리 환율 입력 폼"""
    st.header("✏️ 연도별 관리 환율 입력")
    
    # 입력 방식 선택
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("연도별 USD 기준 관리 환율을 입력하세요")
    with col2:
        input_method = st.selectbox("입력 방식", ["📝 수동 입력", "📊 일괄 입력"], key="input_method")
    
    if input_method == "📊 일괄 입력":
        show_bulk_rate_input(rate_manager)
    else:
        show_manual_rate_input(rate_manager)

def show_bulk_rate_input(rate_manager):
    """일괄 환율 입력 (여러 연도 동시 입력)"""
    st.markdown("### 📊 일괄 환율 입력")
    st.info("💡 **안내**: 여러 연도의 환율을 한 번에 입력할 수 있습니다. 아래 가로 테이블에 직접 값을 입력하세요.")
    
    # 연도 범위 선택
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("시작 연도", min_value=2020, max_value=2040, value=2022, step=1)
    with col2:
        end_year = st.number_input("종료 연도", min_value=2020, max_value=2040, value=2024, step=1)
    
    if start_year > end_year:
        st.error("시작 연도는 종료 연도보다 작거나 같아야 합니다.")
        return
    
    # 통화 목록
    currencies = ['CNY', 'IDR', 'KRW', 'THB', 'VND']
    
    # 입력 테이블 생성
    years = list(range(start_year, end_year + 1))
    
    st.markdown("### 📋 환율 입력 테이블")
    
    # 기존 데이터 조회하여 기본값 설정
    existing_data = rate_manager.get_yearly_management_rates()
    
    # 입력 폼 생성
    input_data = {}
    for year in years:
        st.markdown(f"#### {year}년")
        cols = st.columns(len(currencies))
        input_data[year] = {}
        
        for i, currency in enumerate(currencies):
            with cols[i]:
                # 기존 데이터가 있으면 기본값으로 설정
                default_value = 0.0
                if not existing_data.empty:
                    existing_rate = existing_data[
                        (existing_data['year'] == year) & 
                        (existing_data['target_currency'] == currency)
                    ]
                    if not existing_rate.empty:
                        default_value = float(existing_rate.iloc[0]['rate'])
                
                value = st.number_input(
                    f"{currency}",
                    min_value=0.0,
                    value=default_value,
                    step=0.01,
                    format="%.2f",
                    key=f"bulk_{year}_{currency}"
                )
                input_data[year][currency] = value
    
    # 저장 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 일괄 저장", type="primary", use_container_width=True):
            try:
                success_count = 0
                for year, currencies_data in input_data.items():
                    for currency, rate in currencies_data.items():
                        if rate > 0:  # 0보다 큰 값만 저장
                            result = rate_manager.add_yearly_management_rate(
                                year=year,
                                target_currency=currency,
                                rate=rate,
                                created_by='master'
                            )
                            if result:
                                success_count += 1
                
                if success_count > 0:
                    st.success(f"✅ {success_count}개의 환율 데이터가 성공적으로 저장되었습니다!")
                    st.rerun()
                else:
                    st.warning("저장할 유효한 데이터가 없습니다. (0보다 큰 값을 입력하세요)")
                    
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {str(e)}")

def show_manual_rate_input(rate_manager):
    """수동 환율 입력 (단일 입력)"""
    st.markdown("### 📝 수동 환율 입력")
    
    # 세션 상태 초기화
    if 'prev_year' not in st.session_state:
        st.session_state.prev_year = datetime.now().year
    if 'prev_currency' not in st.session_state:
        st.session_state.prev_currency = 'USD'
    
    # 입력 폼
    col1, col2 = st.columns(2)
    
    with col1:
        year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2040,
            value=datetime.now().year,
            step=1,
            key="manual_year_input"
        )
        
        currency = st.selectbox(
            "통화",
            ['USD', 'CNY', 'IDR', 'KRW', 'THB', 'VND'],
            format_func=lambda x: f"{x} ({'US' if x=='USD' else 'CN' if x=='CNY' else 'ID' if x=='IDR' else 'KR' if x=='KRW' else 'TH' if x=='THB' else 'VN'})",
            key="manual_currency_input"
        )
    
    # 년도나 통화가 변경되었는지 확인
    changed = (st.session_state.prev_year != year) or (st.session_state.prev_currency != currency)
    
    with col2:
        # 선택된 년도와 통화에 따라 기존 환율 데이터 자동 로드
        default_rate = 0.0
        info_message = ""
        
        try:
            existing_data = rate_manager.get_yearly_management_rates()
            if not existing_data.empty:
                matching_data = existing_data[
                    (existing_data['year'] == year) & 
                    (existing_data['target_currency'] == currency)
                ]
                if not matching_data.empty:
                    default_rate = float(matching_data.iloc[0]['rate'])
                    if default_rate > 0:
                        info_message = f"💡 기존 {year}년 {currency} 환율: {default_rate:,.2f}"
        except Exception as e:
            st.warning(f"기존 데이터 조회 중 오류: {str(e)}")
        
        # 정보 메시지 표시
        if info_message:
            st.info(info_message)
        elif currency != 'USD':
            st.info(f"💡 {year}년 {currency} 환율이 없습니다. 새로 입력하세요.")
        
        # 환율 입력 - 값이 변경되었을 때 기본값 업데이트
        rate_key = "manual_rate_input"
        if changed:
            # 년도/통화가 변경되면 환율 필드를 새 기본값으로 재설정
            if rate_key in st.session_state:
                del st.session_state[rate_key]
        
        rate = st.number_input(
            "환율 (USD 기준)",
            min_value=0.0,
            value=default_rate,
            step=0.01,
            format="%.2f",
            help="1 USD = ? 해당통화",
            key=rate_key
        )
        
        st.markdown(f"**환율 미리보기**: 1 USD = {rate:,.2f} {currency}")
    
    # 이전 값 업데이트
    st.session_state.prev_year = year
    st.session_state.prev_currency = currency
    
    # 저장 버튼
    if st.button("💾 저장", type="primary"):
        if rate <= 0:
            st.error("환율은 0보다 큰 값이어야 합니다.")
            return
            
        try:
            result = rate_manager.add_yearly_management_rate(
                year=year,
                target_currency=currency,
                rate=rate,
                created_by='master'
            )
            
            if result:
                st.success(f"✅ {year}년 {currency} 환율이 성공적으로 저장되었습니다!")
                st.rerun()
            else:
                st.error("환율 저장에 실패했습니다.")
                
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {str(e)}")

def show_management_rate_management(rate_manager, get_text):
    """환율 관리 화면"""
    st.header("⚙️ 환율 데이터 관리")