# -*- coding: utf-8 -*-
"""
분기별 기준 환율 관리 페이지
SQLite 기반 분기별 기준 환율 시스템
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager

def show_quarterly_exchange_rate_page(get_text):
    """분기별 기준 환율 관리 페이지를 표시합니다."""
    st.title("📊 분기별 기준 환율 관리")
    st.markdown("---")
    
    # 환율 매니저 초기화
    if 'sqlite_exchange_rate_manager' not in st.session_state:
        st.session_state.sqlite_exchange_rate_manager = SQLiteExchangeRateManager()
    
    rate_manager = st.session_state.sqlite_exchange_rate_manager
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "📋 현재 분기 환율",
        "✏️ 분기별 환율 입력", 
        "📈 분기별 환율 관리"
    ])
    
    with tab1:
        show_current_quarterly_rates(rate_manager, get_text)
    
    with tab2:
        show_quarterly_rate_input(rate_manager, get_text)
        
    with tab3:
        show_quarterly_rate_management(rate_manager, get_text)

def show_current_quarterly_rates(rate_manager, get_text):
    """현재 분기 환율 정보를 표시합니다."""
    st.header("📊 현재 분기 환율")
    
    # 현재 분기 정보
    current_date = datetime.now()
    current_year = current_date.year
    current_quarter = (current_date.month - 1) // 3 + 1
    
    st.info(f"📅 현재: {current_year}년 {current_quarter}분기")
    
    # 지원 통화 정의
    supported_currencies = {
        'KRW': {'name': '대한민국 원', 'flag': '🇰🇷'},
        'CNY': {'name': '중국 위안', 'flag': '🇨🇳'},
        'VND': {'name': '베트남 동', 'flag': '🇻🇳'},
        'THB': {'name': '태국 바트', 'flag': '🇹🇭'},
        'IDR': {'name': '인도네시아 루피아', 'flag': '🇮🇩'},
        'USD': {'name': '미국 달러', 'flag': '🇺🇸'}
    }
    
    # 현재 분기 환율 카드 표시
    cols = st.columns(3)
    col_index = 0
    
    for currency_code, currency_info in supported_currencies.items():
        if currency_code == 'VND':  # 기준 통화는 제외
            continue
            
        with cols[col_index % 3]:
            rate = rate_manager.get_current_quarter_rate(currency_code)
            
            if rate:
                st.metric(
                    label=f"{currency_info['flag']} {currency_code}",
                    value=f"{rate:,.2f} VND",
                    help=f"{currency_info['name']} (USD 기준)"
                )
            else:
                st.metric(
                    label=f"{currency_info['flag']} {currency_code}",
                    value="미설정",
                    help=f"{currency_info['name']} - 환율을 입력해주세요"
                )
        
        col_index += 1
    
    # 분기별 환율 기준 안내
    with st.expander("📖 분기별 기준 환율 안내"):
        st.markdown("### 🏛️ **환율 기준 출처**")
        st.markdown("- **🇰🇷 KRW, 🇹🇭 THB, 🇮🇩 IDR**: 한국은행(ECOS) 기준")
        st.markdown("- **🇨🇳 CNY**: CFETS 3M 기준")
        st.markdown("- **🇻🇳 VND**: SBV 공식 환율 기준")
        st.markdown("- **🇺🇸 USD**: 국제 환율 기준")
        
        st.markdown("---")
        st.markdown("### 📊 **분기별 관리 방식**")
        st.markdown("- 분기마다 기준 환율을 설정하여 일관성 있는 가격 관리")
        st.markdown("- 제품 등록 시 해당 분기 기준 환율 자동 적용")
        st.markdown("- 분기별 환율 변화 추이 분석 가능")

def show_quarterly_rate_input(rate_manager, get_text):
    """분기별 환율 입력 폼을 표시합니다."""
    st.header("✏️ 분기별 환율 입력")
    
    with st.form("quarterly_rate_form"):
        # 연도 및 분기 선택
        col1, col2 = st.columns(2)
        
        with col1:
            current_year = datetime.now().year
            year = st.selectbox(
                "연도", 
                range(current_year - 2, current_year + 3),
                index=2  # 현재 연도가 중간에 오도록
            )
        
        with col2:
            current_quarter = (datetime.now().month - 1) // 3 + 1
            quarter = st.selectbox(
                "분기",
                [1, 2, 3, 4],
                index=current_quarter - 1  # 현재 분기가 선택되도록
            )
        
        st.markdown("---")
        st.markdown("### 💱 통화별 환율 입력 (USD → VND 기준)")
        
        # 지원 통화 및 기본 환율
        currencies = {
            'KRW': {'name': '대한민국 원', 'default': 1300.0, 'flag': '🇰🇷'},
            'CNY': {'name': '중국 위안', 'default': 7.2, 'flag': '🇨🇳'},
            'THB': {'name': '태국 바트', 'default': 35.0, 'flag': '🇹🇭'},
            'IDR': {'name': '인도네시아 루피아', 'default': 15500.0, 'flag': '🇮🇩'},
            'USD': {'name': '미국 달러', 'default': 24000.0, 'flag': '🇺🇸'}
        }
        
        rates = {}
        
        for currency_code, currency_info in currencies.items():
            # 기존 환율 조회
            existing_rate = None
            try:
                quarterly_rates = rate_manager.get_quarterly_rates(year, quarter)
                if not quarterly_rates.empty:
                    existing_data = quarterly_rates[quarterly_rates['target_currency'] == currency_code]
                    if not existing_data.empty:
                        existing_rate = float(existing_data.iloc[0]['rate'])
            except:
                pass
            
            default_value = existing_rate if existing_rate else currency_info['default']
            
            rates[currency_code] = st.number_input(
                f"{currency_info['flag']} {currency_code} ({currency_info['name']})",
                min_value=0.0,
                value=default_value,
                step=100.0 if currency_code in ['KRW', 'IDR', 'USD'] else 0.1,
                format="%.2f",
                help=f"1 USD = ? {currency_code} (VND 기준 환율)"
            )
        
        # 입력자 정보
        created_by = st.text_input("입력자", value=st.session_state.get('user_name', 'admin'))
        
        submitted = st.form_submit_button("분기별 환율 저장", use_container_width=True, type="primary")
        
        if submitted:
            success_count = 0
            error_messages = []
            
            for currency_code, rate in rates.items():
                if rate > 0:
                    try:
                        success, message = rate_manager.add_quarterly_rate(
                            year=year,
                            quarter=quarter,
                            target_currency=currency_code,
                            rate=rate,
                            created_by=created_by
                        )
                        
                        if success:
                            success_count += 1
                        else:
                            error_messages.append(f"{currency_code}: {message}")
                    except Exception as e:
                        error_messages.append(f"{currency_code}: {str(e)}")
            
            if success_count > 0:
                st.success(f"✅ {success_count}개 통화의 {year}년 {quarter}분기 환율이 저장되었습니다!")
            
            if error_messages:
                for error in error_messages:
                    st.error(f"❌ {error}")
                    
            st.rerun()

def show_quarterly_rate_management(rate_manager, get_text):
    """분기별 환율 데이터 관리 기능을 표시합니다."""
    st.header("📈 분기별 환율 관리")
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        current_year = datetime.now().year
        year_filter = st.selectbox(
            "연도 필터",
            ["전체"] + list(range(current_year - 3, current_year + 2)),
            index=1  # 작년이 선택되도록
        )
    
    with col2:
        quarter_filter = st.selectbox(
            "분기 필터",
            ["전체", 1, 2, 3, 4]
        )
    
    # 데이터 조회
    try:
        if year_filter == "전체":
            year_param = None
        else:
            year_param = year_filter
            
        if quarter_filter == "전체":
            quarter_param = None
        else:
            quarter_param = quarter_filter
        
        quarterly_data = rate_manager.get_quarterly_rates(year_param, quarter_param)
        
        if quarterly_data.empty:
            st.info("분기별 환율 데이터가 없습니다.")
            return
        
        # 데이터 표시
        st.subheader(f"📊 분기별 환율 데이터 ({len(quarterly_data)}건)")
        
        # 피벗 테이블 생성 (연도-분기별로 각 통화 환율을 열로 배치)
        quarterly_data['period'] = quarterly_data['year'].astype(str) + 'Q' + quarterly_data['quarter'].astype(str)
        
        pivot_data = quarterly_data.pivot_table(
            values='rate',
            index='period',
            columns='target_currency',
            aggfunc='first'
        ).reset_index()
        
        # 기간순 정렬
        pivot_data = pivot_data.sort_values('period')
        
        # 컬럼명 변경
        flag_map = {
            'KRW': '🇰🇷 KRW',
            'CNY': '🇨🇳 CNY',
            'VND': '🇻🇳 VND',
            'THB': '🇹🇭 THB',
            'IDR': '🇮🇩 IDR',
            'USD': '🇺🇸 USD'
        }
        
        renamed_columns = {'period': '📅 분기'}
        for col in pivot_data.columns:
            if col != 'period':
                renamed_columns[col] = flag_map.get(col, col)
        
        pivot_data = pivot_data.rename(columns=renamed_columns)
        
        # 환율 값을 포맷팅
        for col in pivot_data.columns:
            if col != '📅 분기':
                pivot_data[col] = pivot_data[col].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else "-")
        
        st.dataframe(pivot_data, use_container_width=True, hide_index=True)
        
        # 삭제 기능
        st.markdown("---")
        st.subheader("🗑️ 데이터 관리")
        
        # 원본 데이터 표시 (삭제용)
        with st.expander("📋 상세 데이터 및 삭제"):
            st.markdown("**⚠️ 주의**: 삭제된 데이터는 복구할 수 없습니다.")
            
            # 삭제할 데이터 선택
            selected_data = st.selectbox(
                "삭제할 데이터 선택",
                quarterly_data.apply(lambda x: f"{x['year']}년 {x['quarter']}분기 - {x['target_currency']} ({x['rate']:.2f})", axis=1).tolist(),
                key="delete_quarterly_rate"
            )
            
            if st.button("선택한 데이터 삭제", type="secondary"):
                # 선택된 데이터 파싱
                try:
                    parts = selected_data.split(" - ")
                    year_quarter = parts[0].replace("년 ", "Q").replace("분기", "")
                    year = int(year_quarter.split("Q")[0])
                    quarter = int(year_quarter.split("Q")[1])
                    currency = parts[1].split(" (")[0]
                    
                    # 삭제 로직 (실제 구현 필요)
                    st.warning("삭제 기능은 개발 중입니다.")
                except:
                    st.error("데이터 파싱 오류가 발생했습니다.")
                    
    except Exception as e:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {str(e)}")