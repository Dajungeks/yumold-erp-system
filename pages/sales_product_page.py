"""
판매 제품 관리 페이지 - 간단한 버전
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from notification_helper import NotificationHelper
import plotly.express as px


def show_sales_product_page(sales_product_manager, product_manager, exchange_rate_manager, user_permissions, get_text, quotation_manager=None, customer_manager=None, supply_product_manager=None, pdf_design_manager=None, master_product_manager=None):
    """판매 제품 관리 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'sales_product_management', get_text)
    
    st.header("💰 판매 제품 관리")
    st.markdown("**MB 제품을 제외한 모든 제품**(HR=핫런너 시스템, HRC=핫런너 제어기, SERVICE=서비스, SPARE=부품 등)의 표준 판매가를 관리합니다.")
    
    # 탭 메뉴로 구성 - 제품 등록 기능 추가
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "➕ 비MB 제품 등록",
        "📋 표준 판매가 관리",
        "🎯 대량 가격 설정",
        "✏️ 가격 수정",
        "🗑️ 가격 삭제",
        "📝 제품 정보 수정",
        "🗑️ 제품 삭제",
        "📊 가격 변경 이력",
        "💳 실제 판매 데이터",
        "📈 가격 편차 분석",
        "🏆 판매 성과 분석"
    ])
    
    with tab1:
        show_non_mb_product_registration(master_product_manager, sales_product_manager)
    
    with tab2:
        show_standard_price_management(sales_product_manager, master_product_manager, exchange_rate_manager)
    
    with tab3:
        show_bulk_price_setting(sales_product_manager, master_product_manager, exchange_rate_manager)
    
    with tab4:
        show_price_edit_management(sales_product_manager, master_product_manager, exchange_rate_manager)
    
    with tab5:
        show_simple_price_deletion(sales_product_manager)
    
    with tab6:
        show_product_edit_management(sales_product_manager)
    
    with tab7:
        show_product_delete_management(sales_product_manager)
    
    with tab8:
        show_price_change_history(sales_product_manager)
    
    with tab9:
        show_actual_sales_data(sales_product_manager)
    
    with tab10:
        show_price_variance_analysis(sales_product_manager)
    
    with tab11:
        show_sales_performance_analysis(sales_product_manager)

def show_price_edit_management(sales_product_manager, master_product_manager, exchange_rate_manager):
    """가격 수정 관리 페이지"""
    st.subheader("✏️ 가격 수정")
    
    # 검색 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        search_code = st.text_input("제품 코드 검색", placeholder="예: HR-001")
    with col2:
        search_name = st.text_input("제품명 검색", placeholder="제품명 입력")
    with col3:
        show_only_active = st.checkbox("활성 가격만 표시", value=False, help="체크하면 현재 활성화된 가격만 표시합니다")
    
    # 가격 데이터 검색 (기본적으로 모든 데이터 표시)
    try:
        price_data = sales_product_manager.search_prices(
            product_code=search_code if search_code else None,
            product_name=search_name if search_name else None,
            is_current_only=show_only_active
        )
        
        if len(price_data) == 0:
            st.warning("검색 조건에 맞는 가격 데이터가 없습니다.")
            return
        
        st.info(f"🔍 {len(price_data)}개의 가격 기록을 찾았습니다.")
        
        # 가격 목록 표시 및 선택
        price_options = []
        price_mapping = {}
        
        for _, row in price_data.iterrows():
            status = "✅ 활성" if str(row.get('is_current', '')).lower() in ['true', '1', 'yes', 'y'] else "❌ 비활성"
            option_text = f"{row['product_code']} - {row['product_name']} ({status}) - ${row.get('standard_price_usd', 0):.2f}"
            price_options.append(option_text)
            price_mapping[option_text] = row['price_id']
        
        selected_price = st.selectbox("수정할 가격 선택", ["선택하세요..."] + price_options)
        
        if selected_price != "선택하세요...":
            price_id = price_mapping[selected_price]
            price_info = sales_product_manager.get_price_by_id(price_id)
            
            if price_info:
                st.markdown("---")
                st.markdown("**🔧 가격 수정**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**현재 정보**")
                    st.write(f"제품 코드: {price_info.get('product_code', 'N/A')}")
                    st.write(f"제품명: {price_info.get('product_name', 'N/A')}")
                    st.write(f"현재 USD 가격: ${price_info.get('standard_price_usd', 0):.2f}")
                    st.write(f"현재 현지 가격: {price_info.get('standard_price_local', 0):.2f}")
                    st.write(f"현지 통화: {price_info.get('local_currency', 'USD')}")
                
                with col2:
                    st.markdown("**새로운 가격 설정**")
                    new_usd_price = st.number_input("새 USD 가격", 
                                                   min_value=0.0, 
                                                   value=float(price_info.get('standard_price_usd', 0)),
                                                   step=0.01,
                                                   format="%.2f")
                    
                    # 통화 선택
                    currency_options = ["USD", "VND", "THB", "CNY", "KRW", "JPY"]
                    current_currency = price_info.get('local_currency', 'USD')
                    if current_currency not in currency_options:
                        currency_options.append(current_currency)
                    
                    currency_index = currency_options.index(current_currency) if current_currency in currency_options else 0
                    new_currency = st.selectbox("현지 통화", currency_options, index=currency_index)
                    
                    # 환율 적용
                    if new_currency != "USD" and exchange_rate_manager:
                        try:
                            rates = exchange_rate_manager.get_current_rates()
                            if len(rates) > 0:
                                rate_info = rates[rates['currency'] == new_currency]
                                if len(rate_info) > 0:
                                    exchange_rate = rate_info.iloc[0]['rate']
                                    new_local_price = new_usd_price * exchange_rate
                                    st.info(f"환율: 1 USD = {exchange_rate:,.2f} {new_currency}")
                                else:
                                    new_local_price = new_usd_price
                                    st.warning(f"{new_currency} 환율 정보를 찾을 수 없습니다.")
                            else:
                                new_local_price = new_usd_price
                        except:
                            new_local_price = new_usd_price
                    else:
                        new_local_price = new_usd_price
                    
                    new_local_price = st.number_input(f"새 {new_currency} 가격", 
                                                     min_value=0.0, 
                                                     value=float(new_local_price),
                                                     step=0.01,
                                                     format="%.2f")
                    
                    change_reason = st.text_area("변경 사유", 
                                               placeholder="가격 변경 이유를 입력하세요...",
                                               help="가격 변경에 대한 설명을 입력해주세요.")
                
                # 수정 버튼
                if st.button("💾 가격 수정", type="primary", key="update_price"):
                    if not change_reason.strip():
                        NotificationHelper.show_error("변경 사유를 입력해주세요.")
                    else:
                        success, message = sales_product_manager.update_price_record(
                            price_id=price_id,
                            new_standard_price_usd=new_usd_price,
                            new_standard_price_local=new_local_price,
                            new_local_currency=new_currency,
                            change_reason=change_reason.strip(),
                            updated_by="system"
                        )
                        
                        if success:
                            NotificationHelper.show_success("가격이 성공적으로 수정되었습니다.")
                            st.rerun()
                        else:
                            NotificationHelper.show_error(f"가격 수정 실패: {message}")
    
    except Exception as e:
        st.error(f"가격 수정 관리 중 오류: {str(e)}")

def show_simple_price_deletion(sales_product_manager):
    """간단한 가격 완전 삭제 페이지"""
    st.subheader("🗑️ 가격 완전 삭제")
    st.warning("⚠️ **주의**: 선택한 가격 데이터가 영구적으로 삭제됩니다.")
    
    # 현재 가격 데이터 조회
    try:
        all_prices = sales_product_manager.get_all_prices()
        if not all_prices:
            st.info("등록된 가격 정보가 없습니다.")
            return
        
        price_data = pd.DataFrame(all_prices)
        
        st.markdown("**🔍 삭제할 제품 선택:**")
        
        # 바둑판식 레이아웃 (3열로 구성)
        # 3열씩 나누어 표시
        num_cols = 3
        num_items = len(price_data)
        
        for i in range(0, num_items, num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < num_items:
                    row = price_data.iloc[idx]
                    with cols[j]:
                        # 제품 코드와 가격 표시
                        st.markdown(f"**`{row['product_code']}`**")
                        st.caption(f"${row.get('standard_price_usd', 0):.2f}")
                        
                        # 삭제 버튼
                        delete_key = f"delete_{idx}_{row['price_id']}"
                        
                        if st.button("🗑️ 삭제", key=delete_key, type="secondary"):
                            # 확인 단계
                            confirm_key = f"confirm_{row['price_id']}"
                            if st.session_state.get(confirm_key, False):
                                # 실제 삭제 실행
                                try:
                                    success, message = sales_product_manager.delete_price_records(
                                        [row['price_id']], 
                                        permanent=True
                                    )
                                    
                                    if success:
                                        NotificationHelper.show_success("가격 삭제 완료", f"{row['product_code']} 가격이 삭제되었습니다.")
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                                    else:
                                        NotificationHelper.show_error(f"삭제 실패: {message}")
                                        st.session_state[confirm_key] = False
                                except Exception as e:
                                    NotificationHelper.show_error(f"삭제 중 오류: {str(e)}")
                                    st.session_state[confirm_key] = False
                            else:
                                # 확인 요청
                                st.session_state[confirm_key] = True
                                st.error(f"⚠️ {row['product_code']} 삭제 확인 - 다시 클릭하면 영구 삭제됩니다!")
                                st.rerun()
        
        # 전체 통계
        st.markdown("---")
        st.info(f"총 {len(price_data)}개의 가격이 등록되어 있습니다.")
    
    except Exception as e:
        st.error(f"가격 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")
        st.info("가격 삭제는 가격 데이터가 등록된 후 이용 가능합니다.")

def show_standard_price_management(sales_product_manager, master_product_manager, exchange_rate_manager):
    """표준 판매가 관리 페이지"""
    st.subheader("🏷️ 표준 판매가 설정")
    
    # 마스터 제품 데이터 가져오기
    if master_product_manager:
        try:
            master_products = master_product_manager.get_all_products()
            
            if len(master_products) == 0:
                st.warning("등록된 제품이 없습니다.")
                return
            
            # MB 제품만 제외한 모든 제품 필터링 (HR, HRC, SERVICE, SPARE 등 포함)
            # MB- 접두사 또는 main_category가 정확히 MB인 제품만 제외
            if len(master_products) > 0:
                filtered_products = master_products[
                    (~master_products['product_code'].str.startswith('MB-', na=False)) &
                    (master_products['main_category'] != 'MB')
                ]
            else:
                filtered_products = master_products
            
            st.info(f"🔍 총 {len(master_products)}개 제품 중 {len(filtered_products)}개 제품이 표준 판매가 관리 대상입니다.")
            
            if len(filtered_products) == 0:
                st.warning("MB 제품을 제외한 판매 대상 제품이 없습니다.")
                return
            
            # 제품 선택 드롭다운
            product_options = ["선택하세요..."]
            product_mapping = {}
            
            for idx, product in filtered_products.iterrows():
                product_code = product.get('product_code', '')
                main_category = product.get('main_category', '')
                display_name = f"{product_code}"
                product_options.append(display_name)
                product_mapping[display_name] = product.to_dict()
            
            st.success(f"✅ {len(product_options)-1}개의 제품을 선택할 수 있습니다.")
            
            # 세션 상태에서 자동 선택된 제품 확인
            auto_selected_code = st.session_state.get('product_for_price_setting', None)
            default_index = 0
            
            if auto_selected_code:
                # 자동 선택된 제품이 있으면 해당 제품을 기본값으로 설정
                for i, option in enumerate(product_options):
                    if option != "선택하세요..." and auto_selected_code in option:
                        default_index = i
                        break
                # 세션 상태 정리
                if 'product_for_price_setting' in st.session_state:
                    del st.session_state['product_for_price_setting']
            
            selected_option = st.selectbox("제품 선택 *", product_options, index=default_index)
            
            if selected_option != "선택하세요...":
                # 선택된 제품 정보
                selected_product = product_mapping.get(selected_option, {})
                
                if selected_product:
                    st.success(f"✅ 선택된 제품: **{selected_product.get('product_code', '알 수 없음')}**")
                    
                    # 현재 설정된 가격 표시
                    try:
                        current_price = sales_product_manager.get_current_price(selected_product.get('product_code', ''))
                        if current_price:
                            st.info(f"현재 표준가: ${current_price['standard_price_usd']:.2f} USD")
                    except:
                        st.info("현재 설정된 표준가가 없습니다.")
                    
                    # 간단한 가격 설정 폼
                    st.subheader("💰 가격 설정")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 현지 통화 기준 판매가 설정
                        local_currency_options = ["VND", "THB", "IDR", "USD", "KRW", "MYR"]
                        local_currency = st.selectbox("판매 통화", local_currency_options, index=0)
                        
                        # 기본값 설정 (환율 조회 후 계산)
                        base_usd_price = float(selected_product.get('recommended_price_usd', 100))
                        
                        # 환율 미리 조회
                        try:
                            latest_rates = exchange_rate_manager.get_latest_rates()
                            preview_rate = None
                            
                            for _, rate_row in latest_rates.iterrows():
                                if rate_row['currency_code'] == local_currency:
                                    preview_rate = float(rate_row['rate'])
                                    break
                            
                            if preview_rate is None:
                                default_rates = {"VND": 24500, "THB": 36.5, "IDR": 15700, "KRW": 1380, "MYR": 4.7, "CNY": 7.3}
                                preview_rate = default_rates.get(local_currency, 1.0)
                        except:
                            default_rates = {"VND": 24500, "THB": 36.5, "IDR": 15700, "KRW": 1380, "MYR": 4.7, "CNY": 7.3}
                            preview_rate = default_rates.get(local_currency, 1.0)
                        
                        # 실제 환율 기반 기본값 계산
                        default_local_price = base_usd_price * preview_rate
                        currency_label = f"표준 판매가 ({local_currency}) *"
                        
                        # 환율 정보 미리 표시
                        st.caption(f"💡 기본값은 ${base_usd_price} × {preview_rate:,.1f} 환율로 계산됨")
                        
                        new_price_local = st.number_input(currency_label, min_value=0.0, value=default_local_price)
                else:
                    st.error("제품 정보를 불러올 수 없습니다.")
                    return
                
                with col2:
                    # 환율 설정
                    st.subheader("🔄 환율 설정")
                    
                    # 실제 환율 데이터 조회
                    try:
                        latest_rates = exchange_rate_manager.get_latest_rates()
                        current_rate = None
                        
                        # 해당 통화의 최신 환율 찾기
                        for _, rate_row in latest_rates.iterrows():
                            if rate_row['currency_code'] == local_currency:
                                current_rate = float(rate_row['rate'])
                                break
                        
                        # 환율이 없으면 기본값 사용
                        if current_rate is None:
                            default_rates = {"VND": 24500, "THB": 36.5, "IDR": 15700, "KRW": 1380, "MYR": 4.7, "CNY": 7.3}
                            current_rate = default_rates.get(local_currency, 1.0)
                            st.warning(f"⚠️ {local_currency} 환율 데이터 없음 - 기본값 사용")
                        else:
                            st.success(f"✅ 최신 환율 데이터 사용")
                    
                    except Exception as e:
                        # 환율 매니저 오류 시 기본값 사용
                        default_rates = {"VND": 24500, "THB": 36.5, "IDR": 15700, "KRW": 1380, "MYR": 4.7, "CNY": 7.3}
                        current_rate = default_rates.get(local_currency, 1.0)
                        st.warning(f"⚠️ 환율 조회 실패 - 기본값 사용: {e}")
                    
                    # 수동 환율 입력 옵션
                    use_manual_rate = st.checkbox("🔧 수동 환율 입력")
                    if use_manual_rate:
                        exchange_rate = st.number_input(f"환율 (1 USD = ? {local_currency})", 
                                                      min_value=0.1, 
                                                      value=float(current_rate),
                                                      step=0.1,
                                                      help="사용자 정의 환율을 입력하세요")
                        st.info(f"💡 수동 입력: 1 USD = {exchange_rate:,.2f} {local_currency}")
                    else:
                        exchange_rate = current_rate
                        st.info(f"📊 현재 환율: 1 USD = {exchange_rate:,.2f} {local_currency}")
                        
                        # 환율 업데이트 시간 표시
                        try:
                            update_rates = exchange_rate_manager.get_latest_rates()
                            if len(update_rates) > 0:
                                last_update = update_rates.iloc[0].get('rate_date', 'Unknown')
                                st.caption(f"📅 마지막 업데이트: {last_update}")
                        except:
                            pass
                
                # USD 환산가 계산
                if exchange_rate > 0:
                    new_price_usd = new_price_local / exchange_rate
                    st.info(f"USD 환산가: ${new_price_usd:.2f}")
                else:
                    new_price_usd = 0.0
                
                # 추가 정보
                st.subheader("📝 추가 정보")
                col3, col4 = st.columns(2)
                
                with col3:
                    effective_date = st.date_input("적용일 *")
                
                with col4:
                    price_reason = st.text_input("가격 변경 사유", placeholder="예: 신규 등록, 환율 변동, 원가 상승")
                
                # 저장 버튼
                st.divider()
                if st.button("💾 표준 판매가 저장", type="primary", use_container_width=True):
                    if new_price_local > 0 and new_price_usd > 0:
                        # 가격 데이터 생성
                        price_data = {
                            'product_id': selected_product.get('product_id', ''),
                            'product_code': selected_product.get('product_code', ''),
                            'standard_price_usd': new_price_usd,
                            'standard_price_local': new_price_local,
                            'local_currency': local_currency,
                            'exchange_rate': exchange_rate,
                            'effective_date': str(effective_date),
                            'price_reason': price_reason or "표준가 설정"
                        }
                        
                        try:
                            sales_product_manager.add_standard_price(price_data)
                            st.success(f"✅ 표준 판매가가 성공적으로 저장되었습니다!")
                            st.info(f"제품: {selected_product.get('product_code', '')}\n"
                                   f"가격: {new_price_local:,.2f} {local_currency} (${new_price_usd:.2f} USD)")
                            
                            # 알림 표시
                            try:
                                from notification_helper import NotificationHelper
                                notification = NotificationHelper()
                                notification.show_operation_success("등록", "표준 판매가")
                            except:
                                pass
                            
                            # 페이지 새로고침
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ 저장 중 오류가 발생했습니다: {str(e)}")
                    else:
                        st.error("❌ 가격을 올바르게 입력해주세요.")
            
            else:
                st.info("⬆️ 위에서 제품을 선택하여 표준 판매가를 설정하세요.")
            
            # 현재 설정된 가격 목록 표시
            st.markdown("---")
            st.subheader("📋 현재 설정된 판매가 목록")
            
            try:
                # 모든 가격 데이터 조회 (is_current_only=False로 모든 데이터 표시)
                all_prices = sales_product_manager.get_all_prices()
                
                if len(all_prices) > 0:
                    # DataFrame으로 변환하여 표시
                    price_df = pd.DataFrame(all_prices)
                    
                    # 필요한 컬럼만 선택하여 표시 (제품명과 가격 정보 포함)
                    display_columns = ['product_code', 'product_name', 'price_usd', 'price_vnd', 'currency', 'valid_from', 'is_active']
                    available_columns = [col for col in display_columns if col in price_df.columns]
                    
                    if available_columns:
                        display_df = price_df[available_columns].copy()
                        
                        # 컬럼명을 한국어로 변경
                        column_mapping = {
                            'product_code': '제품코드',
                            'product_name': '제품명',
                            'price_usd': 'USD 가격',
                            'price_vnd': 'VND 가격',
                            'currency': '통화',
                            'valid_from': '적용일',
                            'is_active': '활성상태'
                        }
                        
                        display_df = display_df.rename(columns=column_mapping)
                        
                        # 가격 표시 개선 (소수점 2자리, 천단위 구분자)
                        if 'USD 가격' in display_df.columns:
                            display_df['USD 가격'] = display_df['USD 가격'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) and x > 0 else "-")
                        if 'VND 가격' in display_df.columns:
                            display_df['VND 가격'] = display_df['VND 가격'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) and x > 0 else "-")
                        
                        # 활성 상태 표시 개선
                        if '활성상태' in display_df.columns:
                            display_df['활성상태'] = display_df['활성상태'].apply(lambda x: "✅ 활성" if x == 1 else "❌ 비활성")
                        
                        # 최신 순으로 정렬
                        if '적용일' in display_df.columns:
                            display_df['적용일'] = pd.to_datetime(display_df['적용일'], errors='coerce')
                            display_df = display_df.sort_values('적용일', ascending=False)
                        
                        st.dataframe(display_df, use_container_width=True)
                        st.info(f"총 {len(display_df)}개의 가격이 설정되어 있습니다.")
                    else:
                        st.warning("가격 데이터의 형식이 올바르지 않습니다.")
                else:
                    st.info("아직 설정된 가격이 없습니다. 위에서 제품을 선택하여 가격을 설정해보세요.")
                    
            except Exception as e:
                st.warning(f"가격 목록을 불러오는 중 오류: {str(e)}")
                st.info("가격이 설정된 후 목록이 표시됩니다.")
                
        except Exception as e:
            st.error(f"제품 데이터 로드 실패: {str(e)}")
    else:
        st.error("마스터 제품 매니저가 없습니다.")


def show_bulk_price_setting(sales_product_manager, master_product_manager, exchange_rate_manager):
    """전체 제품 대량 가격 설정 (MB 제외)"""
    st.subheader("🎯 제품 대량 가격 설정")
    st.info("MB 제품을 제외한 모든 제품에 대해 일괄적으로 가격을 설정할 수 있습니다.")
    
    if master_product_manager:
        try:
            # MB 제품만 제외한 모든 제품 필터링 (HR, HRC, SERVICE, SPARE 등 포함)
            all_products = master_product_manager.get_all_products()
            filtered_products = all_products[
                (~all_products['product_code'].str.startswith('MB-', na=False)) &
                (all_products['main_category'] != 'MB')
            ]
            
            if len(filtered_products) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 메인 카테고리 선택
                    if 'main_category' in filtered_products.columns:
                        main_categories = filtered_products['main_category'].dropna().unique()
                    else:
                        main_categories = []
                    selected_category = st.selectbox("제품 카테고리 선택", 
                                                   ["전체"] + list(main_categories))
                
                with col2:
                    # 통화 선택
                    currency = st.selectbox("가격 통화", ["VND", "THB", "IDR", "USD"])
                
                # 기본 가격 설정
                base_price = st.number_input(f"기본 가격 ({currency})", min_value=0.0, value=1000000.0 if currency == "VND" else 1000.0)
                
                # 적용할 제품 목록 표시
                display_products = filtered_products
                if selected_category != "전체" and 'main_category' in filtered_products.columns:
                    display_products = display_products[display_products['main_category'] == selected_category]
                
                st.write(f"적용 대상: **{len(display_products)}개 제품**")
                
                if st.button("💾 대량 가격 적용", type="primary"):
                    success_count = 0
                    for _, product in display_products.iterrows():
                        try:
                            price_data = {
                                'product_id': product.get('product_id', ''),
                                'product_code': product.get('product_code', ''),
                                'standard_price_local': base_price,
                                'local_currency': currency,
                                'price_reason': f"{selected_category} 제품 대량 설정"
                            }
                            sales_product_manager.add_standard_price(price_data)
                            success_count += 1
                        except:
                            continue
                    
                    st.success(f"✅ {success_count}개 제품에 가격이 설정되었습니다!")
            else:
                st.warning("MB 제품을 제외한 판매 대상 제품이 없습니다.")
        except Exception as e:
            st.error(f"제품 로드 실패: {str(e)}")
    else:
        st.error("마스터 제품 매니저가 없습니다.")


def show_price_change_history(sales_product_manager):
    """가격 변경 이력"""
    st.subheader("📊 가격 변경 이력")
    
    # 실제 가격 변경 이력 조회
    try:
        history_data = sales_product_manager.get_price_change_history()
        
        if len(history_data) > 0:
            # 날짜 필터
            col1, col2, col3 = st.columns(3)
            
            with col1:
                start_date = st.date_input("시작일", value=date.today().replace(month=1, day=1), key="history_start")
            
            with col2:
                end_date = st.date_input("종료일", value=date.today(), key="history_end")
            
            with col3:
                # 삭제 모드 토글
                delete_mode = st.toggle("🗑️ 삭제 모드", value=False, help="이력 삭제 기능을 활성화합니다")
            
            # 날짜 필터링
            history_data['change_date'] = pd.to_datetime(history_data['change_date'], errors='coerce')
            filtered_data = history_data[
                (history_data['change_date'] >= pd.Timestamp(start_date)) &
                (history_data['change_date'] <= pd.Timestamp(end_date))
            ]
            
            if len(filtered_data) > 0:
                if delete_mode:
                    # 삭제 모드 - 체크박스로 선택
                    st.warning("⚠️ 삭제 모드가 활성화되었습니다. 삭제할 항목을 선택하세요.")
                    
                    # 체크박스로 선택 가능한 데이터 에디터
                    edited_data = st.data_editor(
                        filtered_data,
                        column_config={
                            "선택": st.column_config.CheckboxColumn("선택", default=False),
                            "product_code": "제품코드",
                            "old_price_usd": st.column_config.NumberColumn("이전USD가격", format="$%.2f"),
                            "new_price_usd": st.column_config.NumberColumn("신규USD가격", format="$%.2f"),
                            "old_price_local": st.column_config.NumberColumn("이전현지가격", format="%.0f"),
                            "new_price_local": st.column_config.NumberColumn("신규현지가격", format="%.0f"),
                            "local_currency": "통화",
                            "change_date": "변경일",
                            "change_reason": "변경사유"
                        },
                        hide_index=True,
                        use_container_width=True,
                        disabled=['product_code', 'old_price_usd', 'old_price_local', 'change_date']
                    )
                    
                    # 선택된 항목 삭제 버튼
                    selected_count = len(edited_data[edited_data.get('선택', False) == True]) if '선택' in edited_data.columns else 0
                    
                    if selected_count > 0:
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button(f"🗑️ 선택된 {selected_count}개 삭제", type="secondary"):
                                selected_items = edited_data[edited_data.get('선택', False) == True]
                                try:
                                    for _, item in selected_items.iterrows():
                                        sales_product_manager.delete_price_history_record(item.get('history_id'))
                                    
                                    NotificationHelper.show_operation_success("삭제", f"{selected_count}개 가격 이력")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 실패: {str(e)}")
                    
                    # 변경사항 저장 버튼
                    if st.button("💾 변경사항 저장", type="primary"):
                        try:
                            for _, row in edited_data.iterrows():
                                if row.get('선택', False) != True:  # 선택되지 않은 항목만 업데이트
                                    sales_product_manager.update_price_history_record(
                                        row.get('history_id'),
                                        {
                                            'new_price_usd': row.get('new_price_usd'),
                                            'new_price_local': row.get('new_price_local'),
                                            'change_reason': row.get('change_reason')
                                        }
                                    )
                            
                            NotificationHelper.show_operation_success("수정", "가격 이력")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 실패: {str(e)}")
                
                else:
                    # 일반 보기 모드
                    st.dataframe(
                        filtered_data[['product_code', 'old_price_usd', 'new_price_usd', 'old_price_local', 
                                     'new_price_local', 'local_currency', 'change_date', 'change_reason']],
                        column_config={
                            "product_code": "제품코드",
                            "old_price_usd": st.column_config.NumberColumn("이전USD가격", format="$%.2f"),
                            "new_price_usd": st.column_config.NumberColumn("신규USD가격", format="$%.2f"),
                            "old_price_local": st.column_config.NumberColumn("이전현지가격", format="%.0f"),
                            "new_price_local": st.column_config.NumberColumn("신규현지가격", format="%.0f"),
                            "local_currency": "통화",
                            "change_date": "변경일",
                            "change_reason": "변경사유"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # 요약 통계
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_changes = len(filtered_data)
                        st.metric("총 변경 건수", f"{total_changes}건")
                    with col2:
                        unique_products = filtered_data['product_code'].nunique()
                        st.metric("변경된 제품 수", f"{unique_products}개")
                    with col3:
                        avg_change = ((filtered_data['new_price_usd'] - filtered_data['old_price_usd']) / filtered_data['old_price_usd'] * 100).mean()
                        st.metric("평균 변경률", f"{avg_change:.1f}%")
            else:
                st.info("선택한 기간에 가격 변경 이력이 없습니다.")
        else:
            st.info("가격 변경 이력이 없습니다.")
    
    except Exception as e:
        st.warning(f"가격 이력 로드 실패: {str(e)}")
        st.info("가격 변경 이력은 가격 수정 시 자동으로 기록됩니다.")


def show_actual_sales_data(sales_product_manager):
    """실제 판매 데이터"""
    st.subheader("💳 실제 판매 데이터")
    
    # 실제 판매 데이터 조회
    try:
        sales_data = sales_product_manager.get_sales_data()
        
        if len(sales_data) > 0:
            # 날짜 필터
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("시작일", value=date.today().replace(month=1, day=1), key="sales_start")
            with col2:
                end_date = st.date_input("종료일", value=date.today(), key="sales_end")
            
            # 날짜 필터링
            sales_data['sale_date'] = pd.to_datetime(sales_data['sale_date'], errors='coerce')
            filtered_data = sales_data[
                (sales_data['sale_date'] >= pd.Timestamp(start_date)) &
                (sales_data['sale_date'] <= pd.Timestamp(end_date))
            ]
            
            if len(filtered_data) > 0:
                st.dataframe(
                    filtered_data[['product_code', 'customer_name', 'sale_price', 'currency', 'sale_date', 'quantity']],
                    column_config={
                        "product_code": "제품코드",
                        "customer_name": "고객명",
                        "sale_price": st.column_config.NumberColumn("판매가", format="%.0f"),
                        "currency": "통화",
                        "sale_date": "판매일",
                        "quantity": st.column_config.NumberColumn("수량", format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 요약 통계
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_sales = filtered_data['sale_price'].sum()
                    st.metric("총 판매액", f"{total_sales:,.0f}")
                with col2:
                    total_orders = len(filtered_data)
                    st.metric("총 주문 건수", f"{total_orders}건")
                with col3:
                    avg_price = filtered_data['sale_price'].mean()
                    st.metric("평균 단가", f"{avg_price:,.0f}")
            else:
                st.info("선택한 기간에 판매 데이터가 없습니다.")
        else:
            st.info("실제 판매 데이터가 없습니다.")
    
    except Exception as e:
        st.warning(f"판매 데이터 로드 실패: {str(e)}")
        st.info("실제 판매 데이터는 주문 관리 시스템과 연동되어 표시됩니다.")


def show_price_variance_analysis(sales_product_manager):
    """가격 편차 분석"""
    st.subheader("📈 가격 편차 분석")
    
    try:
        # 실제 표준가와 판매가 데이터 조회
        variance_data = sales_product_manager.get_price_variance_analysis()
        
        if len(variance_data) > 0:
            # 필터 옵션
            col1, col2 = st.columns(2)
            with col1:
                analysis_period = st.selectbox(
                    "분석 기간",
                    ["최근 30일", "최근 3개월", "최근 6개월", "올해"],
                    key="variance_period"
                )
            with col2:
                currency_filter = st.selectbox(
                    "통화 필터",
                    ["전체"] + list(variance_data['currency'].unique()),
                    key="variance_currency"
                )
            
            # 필터 적용
            filtered_data = variance_data.copy()
            if currency_filter != "전체":
                filtered_data = filtered_data[filtered_data['currency'] == currency_filter]
            
            if len(filtered_data) > 0:
                # 편차율 계산
                filtered_data['variance_pct'] = ((filtered_data['actual_price'] - filtered_data['standard_price']) / filtered_data['standard_price'] * 100)
                
                # 차트 표시
                import plotly.express as px
                import plotly.graph_objects as go
                
                # 표준가 vs 실제가 비교 차트
                fig = px.bar(
                    filtered_data.head(10), 
                    x='product_code', 
                    y=['standard_price', 'actual_price'],
                    title="표준가 vs 실제 판매가 비교 (상위 10개 제품)",
                    labels={'value': '가격', 'variable': '구분'},
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 편차율 분포
                fig2 = px.histogram(
                    filtered_data, 
                    x='variance_pct', 
                    title="가격 편차율 분포",
                    labels={'variance_pct': '편차율 (%)', 'count': '제품 수'}
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # 요약 통계
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_variance = filtered_data['variance_pct'].mean()
                    st.metric("평균 편차율", f"{avg_variance:.1f}%")
                with col2:
                    max_variance = filtered_data['variance_pct'].max()
                    st.metric("최대 편차율", f"{max_variance:.1f}%")
                with col3:
                    min_variance = filtered_data['variance_pct'].min()
                    st.metric("최소 편차율", f"{min_variance:.1f}%")
                with col4:
                    std_variance = filtered_data['variance_pct'].std()
                    st.metric("편차율 표준편차", f"{std_variance:.1f}%")
                
                # 상세 데이터 테이블
                st.subheader("📋 상세 편차 분석")
                st.dataframe(
                    filtered_data[['product_code', 'standard_price', 'actual_price', 'variance_pct', 'currency']],
                    column_config={
                        'product_code': '제품코드',
                        'standard_price': st.column_config.NumberColumn('표준가', format="%.0f"),
                        'actual_price': st.column_config.NumberColumn('실제가', format="%.0f"),
                        'variance_pct': st.column_config.NumberColumn('편차율(%)', format="%.1f"),
                        'currency': '통화'
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("선택한 조건에 맞는 데이터가 없습니다.")
        else:
            st.info("가격 편차 분석을 위한 데이터가 없습니다.")
    
    except Exception as e:
        st.warning(f"편차 분석 데이터 로드 실패: {str(e)}")
        st.info("가격 편차 분석은 표준가와 실제 판매 데이터가 축적되면 표시됩니다.")


def show_sales_performance_analysis(sales_product_manager):
    """판매 성과 분석"""
    st.subheader("🏆 판매 성과 분석")
    
    try:
        # 실제 판매 성과 데이터 조회
        performance_data = sales_product_manager.get_sales_performance_analysis()
        
        if performance_data and len(performance_data) > 0:
            # 분석 기간 선택
            col1, col2 = st.columns(2)
            with col1:
                analysis_period = st.selectbox(
                    "분석 기간",
                    ["최근 30일", "최근 3개월", "최근 6개월", "올해", "전체"],
                    key="performance_period"
                )
            with col2:
                comparison_period = st.selectbox(
                    "비교 기간",
                    ["이전 30일", "이전 3개월", "이전 6개월", "작년 동기", "없음"],
                    key="performance_comparison"
                )
            
            # 필터링된 데이터 기반 KPI 계산
            current_data = performance_data  # 실제로는 기간별 필터링 적용
            
            # 주요 성과 지표
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_sales = current_data.get('total_sales', 0)
                sales_change = current_data.get('sales_change_pct', 0)
                change_indicator = "↑" if sales_change > 0 else "↓" if sales_change < 0 else "→"
                st.metric("총 판매액", f"${total_sales:,.0f}", f"{change_indicator}{abs(sales_change):.1f}%")
            
            with col2:
                total_orders = current_data.get('total_orders', 0)
                orders_change = current_data.get('orders_change_pct', 0)
                change_indicator = "↑" if orders_change > 0 else "↓" if orders_change < 0 else "→"
                st.metric("판매 건수", f"{total_orders}건", f"{change_indicator}{abs(orders_change):.1f}%")
            
            with col3:
                avg_price = current_data.get('avg_price', 0)
                price_change = current_data.get('price_change_pct', 0)
                change_indicator = "↑" if price_change > 0 else "↓" if price_change < 0 else "→"
                st.metric("평균 단가", f"${avg_price:,.0f}", f"{change_indicator}{abs(price_change):.1f}%")
            
            with col4:
                margin_rate = current_data.get('margin_rate', 0)
                margin_change = current_data.get('margin_change_pct', 0)
                change_indicator = "↑" if margin_change > 0 else "↓" if margin_change < 0 else "→"
                st.metric("마진율", f"{margin_rate:.1f}%", f"{change_indicator}{abs(margin_change):.1f}%")
            
            # 제품별 성과 차트
            if 'product_performance' in current_data:
                import plotly.express as px
                
                product_perf = pd.DataFrame(current_data['product_performance'])
                
                try:
                    # 매출 상위 제품
                    import plotly.express as px
                    fig1 = px.bar(
                        product_perf.head(10),
                        x='product_code',
                        y='sales_amount',
                        title="매출 상위 10개 제품",
                        labels={'sales_amount': '매출액 ($)', 'product_code': '제품코드'}
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    # 판매량 vs 마진율 분포
                    fig2 = px.scatter(
                        product_perf,
                        x='quantity_sold',
                        y='margin_rate',
                        size='sales_amount',
                        hover_data=['product_code'],
                        title="제품별 판매량 vs 마진율 분포",
                        labels={'quantity_sold': '판매량', 'margin_rate': '마진율 (%)'}
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                except ImportError:
                    st.info("차트 표시를 위해 plotly 라이브러리가 필요합니다.")
            
            # 월별 트렌드
            if 'monthly_trend' in current_data:
                trend_data = pd.DataFrame(current_data['monthly_trend'])
                
                try:
                    import plotly.express as px
                    fig3 = px.line(
                        trend_data,
                        x='month',
                        y=['sales_amount', 'orders_count'],
                        title="월별 판매 트렌드",
                        labels={'value': '값', 'month': '월'}
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                except ImportError:
                    st.info("차트 표시를 위해 plotly 라이브러리가 필요합니다.")
            
            # 상세 성과 테이블
            if 'detailed_performance' in current_data:
                st.subheader("📋 상세 성과 분석")
                detailed_df = pd.DataFrame(current_data['detailed_performance'])
                
                st.dataframe(
                    detailed_df,
                    column_config={
                        'product_code': '제품코드',
                        'sales_amount': st.column_config.NumberColumn('매출액($)', format="%.0f"),
                        'quantity_sold': st.column_config.NumberColumn('판매량', format="%d"),
                        'avg_price': st.column_config.NumberColumn('평균단가($)', format="%.0f"),
                        'margin_rate': st.column_config.NumberColumn('마진율(%)', format="%.1f"),
                        'customer_count': st.column_config.NumberColumn('고객수', format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("판매 성과 분석을 위한 데이터가 없습니다.")
    
    except Exception as e:
        st.warning(f"성과 분석 데이터 로드 실패: {str(e)}")
        st.info("판매 성과 분석은 실제 판매 데이터가 축적되면 표시됩니다.")

def show_non_mb_product_registration(master_product_manager, sales_product_manager):
    """비MB 제품 등록 페이지 - 기존 통합 제품 관리 방식"""
    st.subheader("➕ 신규 제품 등록")
    st.info("🎯 **HR, HRC, SERVICE, SPARE 등 MB를 제외한 모든 제품을 등록합니다**")
    
    # 코드 생성기 초기화
    from product_code_generator import ProductCodeGenerator
    code_generator = ProductCodeGenerator()
    
    # 제품 카테고리 선택 - 시스템 설정에서 가져오기
    st.markdown("### 1️⃣ 제품 카테고리 선택")
    
    # 시스템 설정에서 카테고리 로드
    try:
        from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
        system_config = SQLiteSystemConfigManager()
        available_categories = system_config.get_product_categories()
        if not available_categories:
            st.warning("⚠️ 시스템 설정에서 제품 카테고리를 먼저 설정해주세요. (법인장 → 시스템 설정)")
            available_categories = ['HR', 'HRC', 'SERVICE', 'SPARE', 'ROBOT']  # 기본값
        else:
            # MB 제품은 제외 (외주 공급가 관리에서 등록)
            available_categories = [cat for cat in available_categories if cat != 'MB']
    except Exception as e:
        st.error(f"시스템 설정 로드 오류: {e}")
        available_categories = ['HR', 'HRC', 'SERVICE', 'SPARE', 'ROBOT']  # 기본값
    
    category = st.selectbox(
        "제품 카테고리 *",
        available_categories,
        help="등록할 제품의 주요 카테고리를 선택하세요 (MB 제품은 외주 공급가 관리에서 등록)"
    )
    
    # 카테고리별 제품 등록 폼
    if category == "HR":
        register_hr_product_form(master_product_manager, sales_product_manager)
    elif category == "HRC":
        register_hrc_product_form(master_product_manager, sales_product_manager)
    elif category == "SERVICE":
        register_service_product_form(master_product_manager, sales_product_manager)
    elif category == "SPARE":
        register_spare_product_form(master_product_manager, sales_product_manager)
    elif category == "ROBOT":
        register_robot_product_form(master_product_manager, sales_product_manager)

def register_hr_product_form(master_product_manager, sales_product_manager):
    """HR 제품 등록 폼"""
    st.markdown("### 🔥 Hot Runner 제품 등록")
    st.info("Hot Runner 시스템 제품을 등록합니다. (YMV-ST-MAE-20-xx 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # System Type 선택 - 시스템 설정에서 동적 로딩
        try:
            from managers.legacy.product_category_config_manager import ProductCategoryConfigManager
            config_manager = ProductCategoryConfigManager()
            system_types = config_manager.get_hr_system_types()
            if not system_types:
                system_types = ['Valve', 'Open', 'Nozzle', 'Tip', 'Insert']  # 기본값
        except Exception as e:
            st.warning(f"시스템 설정 연동 오류: {e}")
            system_types = ['Valve', 'Open', 'Nozzle', 'Tip', 'Insert']  # 기본값
        
        system_type = st.selectbox("System Type", [""] + system_types, index=0, help="시스템 설정에서 관리되는 System Type", key="hr_system_type")
        
        # System Type에 따른 제품 타입 선택
        if system_type:
            # 시스템 설정에서 제품 타입 로딩
            try:
                product_types = config_manager.get_hr_product_types(system_type)
                if not product_types:
                    # 기본값 제공
                    if system_type == "Valve":
                        product_types = ['ST', 'MAE', 'CT', 'SG', 'SE']  # SE 추가
                    elif system_type == "Open":
                        product_types = ['OP', 'DP', 'SP']
                    elif system_type == "Nozzle":
                        product_types = ['TN', 'RN', 'HN']
                    elif system_type == "Tip":
                        product_types = ['HT', 'RT', 'ST']
                    elif system_type == "Insert":
                        product_types = ['TI', 'RI', 'SI']
                    else:
                        product_types = ['ST', 'CT', 'OP']
                product_type_help = f"{system_type} 시스템의 제품 타입을 선택하세요"
            except Exception as e:
                st.warning(f"제품 타입 로딩 오류: {e}")
                product_types = ['ST', 'CT', 'OP']  # 기본값
                product_type_help = f"{system_type} 시스템의 제품 타입"
        else:
            product_types = []
            product_type_help = "먼저 System Type을 선택하세요"
        
        product_type = st.selectbox("제품 타입", [""] + product_types, index=0, help=product_type_help, key="hr_product_type")
        
        # 게이트 타입 선택
        if system_type and product_type:
            # 시스템 설정에서 게이트 타입 로딩
            try:
                gate_types = config_manager.get_hr_gate_types(system_type, product_type)
                if not gate_types:
                    # 기본값 제공
                    if product_type in ['ST', 'MAE', 'SE']:
                        gate_types = ['MAE', 'CT', 'SG', 'MVA Type']  # MVA Type 추가
                    elif product_type in ['OP', 'DP']:
                        gate_types = ['OPEN', 'DIRECT', 'SIDE']
                    elif product_type in ['TN', 'RN']:
                        gate_types = ['TIP', 'RING', 'HEAD']
                    else:
                        gate_types = ['STD', 'ADV', 'PRO']
                gate_type_help = f"{system_type}-{product_type} 조합에 사용 가능한 게이트 타입"
            except Exception as e:
                st.warning(f"게이트 타입 로딩 오류: {e}")
                gate_types = ['STD', 'ADV', 'PRO']  # 기본값
                gate_type_help = f"{system_type}-{product_type}에 사용 가능한 게이트 타입"
        else:
            gate_types = []
            gate_type_help = "먼저 System Type과 제품 타입을 선택하세요"
        
        gate_type = st.selectbox("게이트 타입", [""] + gate_types, index=0, help=gate_type_help, key="hr_gate_type")
        
        # 사이즈 선택
        if system_type and product_type and gate_type:
            # 시스템 설정에서 사이즈 로딩
            try:
                sizes = config_manager.get_hr_sizes(system_type, product_type, gate_type)
                if not sizes:
                    # 기본값 제공
                    if gate_type in ['MAE', 'TIP', 'MVA Type']:
                        sizes = ['10', '15', '20', '25', '30']
                    elif gate_type in ['CT', 'RING']:
                        sizes = ['8', '12', '16', '20', '24']
                    elif gate_type in ['SG', 'HEAD']:
                        sizes = ['12', '18', '24', '30', '36']
                    else:
                        sizes = ['10', '15', '20', '25', '30']  # 기본값
                size_help = f"{system_type}-{product_type}-{gate_type} 조합에 사용 가능한 사이즈"
            except Exception as e:
                st.warning(f"사이즈 로딩 오류: {e}")
                sizes = ['10', '15', '20', '25', '30']  # 기본값
                size_help = f"{system_type}-{product_type}-{gate_type}에 사용 가능한 사이즈"
        else:
            sizes = []
            size_help = "먼저 System Type, 제품 타입, 게이트 타입을 모두 선택하세요"
        
        # 사이즈 입력 (직접 입력 + 기존 등록된 사이즈 참고)
        if sizes:
            st.info(f"등록된 사이즈: {', '.join(sizes)}")
        size_primary = st.text_input("사이즈 입력", placeholder="예: 18, 20, 25", help=f"직접 입력하세요. {size_help}", key="hr_size")
        
        # 자동 코드 생성 및 등록
        if system_type and product_type and gate_type and size_primary:
            # System Type 코드 변환
            system_type_code = ""
            if system_type == "Valve":
                system_type_code = "VV"
            elif system_type == "Open":
                system_type_code = "OP"
            else:
                system_type_code = system_type[:2].upper()  # 기본값
            
            # 생성될 코드
            generated_code = f"HR-{system_type_code}-{product_type}-{gate_type}-{size_primary}"
            
            # 자동 등록 (세션 상태 확인으로 중복 방지)
            auto_register_key = f"auto_registered_{generated_code}"
            if auto_register_key not in st.session_state:
                try:
                    # 기본 제품명 생성
                    korean_base = "핫러너 밸브" if system_type == "Valve" else f"핫러너 {system_type}"
                    default_korean = f"{korean_base} {product_type} {gate_type} {size_primary}mm"
                    default_english = f"Hot Runner {system_type} {product_type} {gate_type} {size_primary}mm"
                    
                    # 중복 체크 (더 안전한 방식)
                    existing_master = None
                    try:
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                    except Exception as check_error:
                        st.warning(f"중복 체크 오류: {check_error}")
                        existing_master = None
                    
                    if not existing_master:
                        # master_product_id 생성
                        import uuid
                        import time
                        timestamp = str(int(time.time()))[-6:]  # 마지막 6자리
                        master_product_id = f"MP-HR-{timestamp}"
                        
                        product_data = {
                            'master_product_id': master_product_id,
                            'product_code': generated_code,
                            'product_name': default_korean,
                            'product_name_en': default_english,
                            'product_name_vi': default_english,
                            'category_name': 'HR',
                            'subcategory_name': product_type,
                            'supplier_name': '',
                            'specifications': 'H30,34,1.0',
                            'unit': 'EA',
                            'status': 'active'
                        }
                        
                        try:
                            result = master_product_manager.add_master_product(product_data)
                            if result:
                                st.session_state[auto_register_key] = True
                                st.success(f"✅ **자동 등록 완료:** `{generated_code}`")
                                st.info("🔄 페이지를 새로고침하면 HR 카테고리 목록에서 확인할 수 있습니다.")
                            else:
                                st.error(f"❌ 자동 등록 실패: `{generated_code}`")
                                st.info("수동 등록을 이용하거나 페이지를 새로고침 후 다시 시도해주세요.")
                        except Exception as reg_error:
                            st.error(f"❌ 등록 중 오류: {reg_error}")
                            st.info(f"코드: `{generated_code}` - 수동 등록을 이용해주세요.")
                    else:
                        st.session_state[auto_register_key] = True
                        st.info(f"ℹ️ **이미 등록된 코드:** `{generated_code}`")
                except Exception as e:
                    st.error(f"❌ 자동 등록 오류: {e}")
                    st.info(f"코드: `{generated_code}` - 수동 등록을 이용해주세요.")
            else:
                st.success(f"✅ **등록된 제품 코드:** `{generated_code}`")
        else:
            st.info("System Type, 제품 타입, 게이트 타입, 사이즈를 모두 입력하면 제품이 자동 등록됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성 제안
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        if system_type and product_type and gate_type and size_primary:
            # System Type에 따른 한국어 이름
            if system_type == "Valve":
                korean_base = "핫러너 밸브"
                english_base = "Hot Runner Valve"
                vietnamese_base = "Van Hot Runner"
            elif system_type == "Open":
                korean_base = "핫러너 오픈"
                english_base = "Hot Runner Open"
                vietnamese_base = "Hệ thống Hot Runner Mở"
            elif system_type == "Nozzle":
                korean_base = "핫러너 노즐"
                english_base = "Hot Runner Nozzle"
                vietnamese_base = "Vòi phun Hot Runner"
            elif system_type == "Tip":
                korean_base = "핫러너 팁"
                english_base = "Hot Runner Tip"
                vietnamese_base = "Đầu Hot Runner"
            elif system_type == "Insert":
                korean_base = "핫러너 인서트"
                english_base = "Hot Runner Insert"
                vietnamese_base = "Chèn Hot Runner"
            else:
                korean_base = "핫러너 시스템"
                english_base = "Hot Runner System"
                vietnamese_base = "Hệ thống Hot Runner"
            
            # 제품 타입 설명
            if product_type == "ST":
                type_korean = "표준형"
                type_english = "Standard"
                type_vietnamese = "Chuẩn"
            elif product_type == "MAE":
                type_korean = "다기능"
                type_english = "Multi-Air-Ejector"
                type_vietnamese = "Đa chức năng"
            elif product_type == "CT":
                type_korean = "냉각형"
                type_english = "Cooling Tower"
                type_vietnamese = "Làm mát"
            else:
                type_korean = product_type
                type_english = product_type
                type_vietnamese = product_type
            
            suggested_korean = f"{korean_base} {type_korean} {gate_type} {size_primary}mm"
            suggested_english = f"{english_base} {type_english} {gate_type} {size_primary}mm"
            suggested_vietnamese = f"{vietnamese_base} {type_vietnamese} {gate_type} {size_primary}mm"
        
        korean_name = st.text_input("한국어 제품명 *", value=suggested_korean, key="hr_korean", placeholder="예: 핫러너 밸브 표준 MAE 20")
        english_name = st.text_input("영어 제품명 *", value=suggested_english, key="hr_english", placeholder="예: Hot Runner Valve Standard MAE 20")
        vietnamese_name = st.text_input("베트남어 제품명", value=suggested_vietnamese, key="hr_vietnamese", placeholder="예: Van Hot Runner Chuẩn MAE 20")
        
        # 공급처 정보 및 기술 사양
        supplier = st.text_input("공급처", placeholder="예: ABC Trading Co.", key="hr_supplier")
        tech_spec = st.text_input("기술 사양", value="H30,34,1.0", help="예: H30,34,1.0", key="hr_tech_spec")
        unit = st.selectbox("단위", ["EA", "SET", "PCS"], index=0, key="hr_unit")
    
    # 수동 등록 버튼 (선택적)
    with st.expander("🔧 상세 정보 수정 및 수동 등록"):
        st.info("위에서 자동 등록된 제품의 상세 정보를 수정하거나 새로운 제품을 수동으로 등록할 수 있습니다.")
        
        if st.button("🚀 HR 제품 수동 등록", key="manual_register_hr_btn"):
            # 4단계 모두 입력되었는지 검증: System Type → 제품 타입 → 게이트 타입 → 사이즈
            if system_type and product_type and gate_type and size_primary and korean_name and english_name:
                try:
                    # 제품 코드 생성 - 사용자 요청 형태: HR-VV-SE-MAV-18
                    # System Type 코드 변환
                    system_type_code = ""
                    if system_type == "Valve":
                        system_type_code = "VV"
                    elif system_type == "Open":
                        system_type_code = "OP"
                    else:
                        system_type_code = system_type[:2].upper()  # 기본값
                    
                    generated_code = f"HR-{system_type_code}-{product_type}-{gate_type}-{size_primary}"
                    
                    # 중복 제품 코드 체크
                    try:
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                        existing_sales = sales_product_manager.get_product_by_code(generated_code)
                        
                        # 중복이 있으면 번호 추가
                        counter = 1
                        original_code = generated_code
                        while existing_master or existing_sales:
                            generated_code = f"{original_code}-{counter}"
                            existing_master = master_product_manager.get_product_by_code(generated_code)
                            existing_sales = sales_product_manager.get_product_by_code(generated_code)
                            counter += 1
                    except:
                        # 중복 체크 실패 시 기본 코드 사용
                        pass
                    
                    # master_product_id 생성
                    import uuid
                    master_product_id = f"MP-{str(uuid.uuid4())[:8].upper()}"
                    
                    product_data = {
                        'master_product_id': master_product_id,
                        'product_code': generated_code,
                        'product_name': korean_name,
                        'product_name_en': english_name,
                        'product_name_vi': vietnamese_name or english_name,
                        'category_name': 'HR',
                        'subcategory_name': product_type,
                        'supplier_name': supplier,
                        'specifications': tech_spec,
                        'unit': unit,
                        'status': 'active'
                    }
                    
                    result = master_product_manager.add_master_product(product_data)
                    
                    # 결과 처리 (반환값이 bool만 있을 수 있음)
                    if isinstance(result, tuple):
                        success, message = result
                    else:
                        success = result
                        message = "등록 완료" if success else "등록 실패"
                    
                    if success:
                        st.success(f"✅ HR 제품이 수동 등록되었습니다: {generated_code}")
                        st.rerun()
                    else:
                        st.error(f"❌ 등록 실패: {message}")
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")
            else:
                # 누락된 단계 표시
                missing_steps = []
                if not system_type: missing_steps.append("System Type")
                if not product_type: missing_steps.append("제품 타입") 
                if not gate_type: missing_steps.append("게이트 타입")
                if not size_primary: missing_steps.append("사이즈")
                if not korean_name: missing_steps.append("한국어 제품명")
                if not english_name: missing_steps.append("영어 제품명")
                
                st.error(f"❌ 다음 필수 단계를 완료해주세요: {', '.join(missing_steps)}")
                st.warning("⚠️ HR 수동 등록을 위해 모든 정보를 입력해야 합니다.")
            
    
    # HR 제품 등록 관련 도움말 추가
    st.markdown("---")
    with st.expander("💡 HR 제품 등록 도움말"):
        st.markdown("""
        ### 🔥 HR 제품 등록 4단계 워크플로우
        
        **1단계: System Type 선택**
        - 시스템 설정에서 등록한 System Type (Valve, Open 등)
        
        **2단계: 제품 타입 선택**  
        - 선택한 System Type에 따른 제품 타입 (ST, SE, CP 등)
        
        **3단계: 게이트 타입 선택**
        - System Type과 제품 타입 조합에 따른 게이트 타입 (MVA, Test 등)
        
        **4단계: 사이즈 직접 입력**
        - 숫자만 입력 (예: 18, 20, 25)
        
        ⚠️ **4단계가 모두 완료되어야 HR 코드가 생성됩니다!**
        
        📝 **생성되는 코드 형식:** HR-VV-SE-MVA-18
        - HR: 카테고리
        - VV: System Type (Valve)  
        - SE: 제품 타입
        - MVA: 게이트 타입
        - 18: 사이즈
        """)

def register_service_product_form(master_product_manager, sales_product_manager):
    """SERVICE 제품 등록 폼 - 시스템 설정 연동"""
    st.markdown("### 🔧 서비스 제품 등록")
    st.info("서비스 제품을 등록합니다. (SV-DESIGN-HR 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # SERVICE 타입 선택 - 시스템 설정에서 동적 로딩
        try:
            from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
            system_config = SQLiteSystemConfigManager()
            service_types = system_config.get_service_types()
            if not service_types or not isinstance(service_types, list):
                service_types = ['DESIGN', 'INSTALLATION', 'MAINTENANCE', 'REPAIR', 'TRAINING']
        except:
            service_types = ['DESIGN', 'INSTALLATION', 'MAINTENANCE', 'REPAIR', 'TRAINING']
        
        service_type = st.selectbox("서비스 타입", [""] + service_types, index=0, help="시스템 설정에서 관리되는 서비스 타입", key="svc_type")
        
        # 적용 분야 선택 - 기본값 사용
        usage_fields = ['HR', 'HRC', 'MB', 'General']
        usage_field = st.selectbox("적용 분야", [""] + usage_fields, index=0, help="서비스 적용 분야", key="svc_field")
        
        # 자동 코드 생성 안내
        if service_type and usage_field:
            st.success("🔗 서비스 타입과 적용 분야를 선택하면 제품 코드가 자동 생성됩니다.")
        else:
            st.info("서비스 타입과 적용 분야를 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        
        if service_type and usage_field:
            service_names = {
                "INSTALLATION": ("설치 서비스", "Installation Service"),
                "MAINTENANCE": ("유지보수 서비스", "Maintenance Service"),
                "REPAIR": ("수리 서비스", "Repair Service"),
                "TRAINING": ("교육 서비스", "Training Service"),
                "DESIGN": ("설계 서비스", "Design Service")
            }
            
            if service_type in service_names:
                suggested_korean = f"{service_names[service_type][0]} ({usage_field})"
                suggested_english = f"{service_names[service_type][1]} ({usage_field})"
        
        korean_name = st.text_input("한국어 제품명 *", value=suggested_korean, key="svc_korean", placeholder="예: 설계 서비스 (HR)")
        english_name = st.text_input("영어 제품명 *", value=suggested_english, key="svc_english", placeholder="예: Design Service (HR)")
        vietnamese_name = st.text_input("베트남어 제품명", key="svc_vietnamese", placeholder="예: Dịch vụ thiết kế (HR)")
        
        # 원산지 및 제조사 정보
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            countries = [
                'Korea', 'China', 'Japan', 'Germany', 'USA', 'Taiwan', 'Singapore', 
                'Italy', 'Switzerland', 'Austria', 'France', 'UK', 'Sweden', 'Denmark',
                'Netherlands', 'Belgium', 'Spain', 'Czech Republic', 'Poland', 'Turkey',
                'Thailand', 'Vietnam', 'Malaysia', 'Indonesia', 'Philippines', 'India',
                'Canada', 'Mexico', 'Brazil', 'Australia'
            ]
            svc_origin_country = st.selectbox("원산지", [""] + sorted(countries), index=0, key="svc_origin")
            
        with col_info2:
            svc_manufacturer = st.text_input("제조사", placeholder="예: YUMOLD Co., Ltd.", key="svc_manufacturer")
        
        # 공급처 정보 추가
        svc_supplier = st.text_input("공급처", placeholder="예: ABC Trading Co.", key="svc_supplier")
        
        # 기술 사양
        svc_tech_spec = st.text_input("기술 사양", placeholder="예: CAD, CAM, 3D 설계", key="svc_tech_spec")
        svc_unit = st.selectbox("단위", ["EA", "SET", "PCS", "HR"], index=0, key="svc_unit")
    
    # 등록 버튼
    if st.button("🚀 SERVICE 제품 등록", type="primary", key="register_service_btn"):
        if service_type and usage_field and korean_name and english_name:
            try:
                # 제품 코드 생성 - SERVICE 형태: SV-DESIGN-HR
                generated_code = f"SV-{service_type}-{usage_field}"
                
                # 중복 제품 코드 체크
                try:
                    existing_master = master_product_manager.get_product_by_code(generated_code)
                    existing_sales = sales_product_manager.get_product_by_code(generated_code)
                    
                    # 중복이 있으면 번호 추가
                    counter = 1
                    original_code = generated_code
                    while existing_master or existing_sales:
                        generated_code = f"{original_code}-{counter}"
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                        existing_sales = sales_product_manager.get_product_by_code(generated_code)
                        counter += 1
                except:
                    # 중복 체크 실패 시 기본 코드 사용
                    pass
                
                # master_product_id 생성
                import uuid
                master_product_id = f"MP-{str(uuid.uuid4())[:8].upper()}"
                
                product_data = {
                    'master_product_id': master_product_id,
                    'product_code': generated_code,
                    'product_name': korean_name,
                    'product_name_en': english_name,
                    'product_name_vi': vietnamese_name or english_name,
                    'category_name': 'SERVICE',
                    'subcategory_name': service_type,
                    'origin_country': svc_origin_country,
                    'manufacturer': svc_manufacturer,
                    'supplier_name': svc_supplier,
                    'specifications': svc_tech_spec,
                    'unit': svc_unit,
                    'status': 'active'
                }
                
                result = master_product_manager.add_master_product(product_data)
                
                # 결과 처리
                if isinstance(result, tuple):
                    success, message = result
                else:
                    success = result
                    message = "등록 완료" if success else "등록 실패"
                
                if success:
                    st.success(f"✅ SERVICE 제품이 등록되었습니다: {generated_code}")
                    
                    # 자동 동기화 제거 - 시스템 설정에서 관리
                    st.info("📋 제품이 통합 제품 관리에 등록되었습니다. 판매 제품 등록은 시스템 설정에서 관리할 수 있습니다.")
                    
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {message}")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        else:
            st.error("필수 필드를 모두 입력해주세요.")

def register_spare_product_form(master_product_manager, sales_product_manager):
    """SPARE 제품 등록 폼"""
    st.markdown("### 🔩 SPARE 부품 등록")
    st.info("다양한 SPARE 부품을 등록합니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # SPARE 부품 타입 선택 - 시스템 설정에서 동적 로딩
        try:
            from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
            system_config = SQLiteSystemConfigManager()
            spare_types = system_config.get_spare_types()
            if not spare_types or not isinstance(spare_types, list):
                spare_types = ['Heater', 'Sensor', 'Thermocouple', 'Cable', 'Connector']
        except:
            spare_types = ['Heater', 'Sensor', 'Thermocouple', 'Cable', 'Connector']
        
        spare_part_type = st.selectbox("SPARE 부품 타입 *", [""] + spare_types, index=0, help="시스템 설정에서 관리되는 SPARE 부품 타입", key="spare_type")
        
        # 호환성 정보
        compatibility = st.text_input("호환 제품", placeholder="호환되는 제품 코드나 모델", key="spare_compatibility")
        
        if spare_part_type:
            st.success("🔗 부품 타입을 선택하면 제품 코드가 자동 생성됩니다.")
        else:
            st.info("부품 타입을 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        korean_name = st.text_input("한국어 제품명 *", key="spare_korean", placeholder="예: 히터")
        english_name = st.text_input("영어 제품명 *", key="spare_english", placeholder="예: Heater")
        vietnamese_name = st.text_input("베트남어 제품명", key="spare_vietnamese", placeholder="예: Máy sưởi")
        
        # 원산지 및 제조사 정보
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            countries = [
                'Korea', 'China', 'Japan', 'Germany', 'USA', 'Taiwan', 'Singapore', 
                'Italy', 'Switzerland', 'Austria', 'France', 'UK', 'Sweden', 'Denmark',
                'Netherlands', 'Belgium', 'Spain', 'Czech Republic', 'Poland', 'Turkey',
                'Thailand', 'Vietnam', 'Malaysia', 'Indonesia', 'Philippines', 'India',
                'Canada', 'Mexico', 'Brazil', 'Australia'
            ]
            spare_origin_country = st.selectbox("원산지", [""] + sorted(countries), index=0, key="spare_origin")
            
        with col_info2:
            spare_manufacturer = st.text_input("제조사", placeholder="예: YUMOLD Co., Ltd.", key="spare_manufacturer")
        
        # 공급처 정보 추가
        spare_supplier = st.text_input("공급처", placeholder="예: ABC Trading Co.", key="spare_supplier")
        
        # 기술 사양
        spare_tech_spec = st.text_input("기술 사양", placeholder="예: 220V, 1000W", key="spare_tech_spec")
        spare_unit = st.selectbox("단위", ["EA", "SET", "PCS"], index=0, key="spare_unit")
    
    # 등록 버튼  
    if st.button("🚀 SPARE 제품 등록", type="primary", key="register_spare_btn"):
        if spare_part_type and korean_name and english_name:
            try:
                # 제품 코드 생성 - SPARE 형태: SP-GASKET
                spare_type_clean = spare_part_type.replace(' ', '').replace('-', '')
                generated_code = f"SP-{spare_type_clean}"
                
                # 중복 제품 코드 체크
                try:
                    existing_master = master_product_manager.get_product_by_code(generated_code)
                    existing_sales = sales_product_manager.get_product_by_code(generated_code)
                    
                    # 중복이 있으면 번호 추가
                    counter = 1
                    original_code = generated_code
                    while existing_master or existing_sales:
                        generated_code = f"{original_code}-{counter}"
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                        existing_sales = sales_product_manager.get_product_by_code(generated_code)
                        counter += 1
                except:
                    # 중복 체크 실패 시 기본 코드 사용
                    pass
                
                # master_product_id 생성
                import uuid
                master_product_id = f"MP-{str(uuid.uuid4())[:8].upper()}"
                
                product_data = {
                    'master_product_id': master_product_id,
                    'product_code': generated_code,
                    'product_name': korean_name,
                    'product_name_en': english_name,
                    'product_name_vi': vietnamese_name or english_name,
                    'category_name': 'SPARE',
                    'subcategory_name': spare_part_type,
                    'origin_country': spare_origin_country,
                    'manufacturer': spare_manufacturer,
                    'supplier_name': spare_supplier,
                    'specifications': spare_tech_spec,
                    'unit': spare_unit,
                    'status': 'active'
                }
                
                result = master_product_manager.add_master_product(product_data)
                
                # 결과 처리
                if isinstance(result, tuple):
                    success, message = result
                else:
                    success = result
                    message = "등록 완료" if success else "등록 실패"
                
                if success:
                    st.success(f"✅ SPARE 제품이 등록되었습니다: {generated_code}")
                    
                    # 자동 동기화 제거 - 시스템 설정에서 관리
                    st.info("📋 제품이 통합 제품 관리에 등록되었습니다. 판매 제품 등록은 시스템 설정에서 관리할 수 있습니다.")
                    
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {message}")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        else:
            st.error("필수 필드를 모두 입력해주세요.")

def register_hrc_product_form(master_product_manager, sales_product_manager):
    """HRC 제품 등록 폼 - HRCT/HRCS 구조"""
    st.markdown("### 🎛️ Controller 제품 등록")
    st.info("Controller 제품을 등록합니다. (HRC-HRCT-TEMP-YC60-Zone01 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # HRC Type 카테고리 선택 - 시스템 설정에서 동적 로딩
        try:
            from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
            system_config = SQLiteSystemConfigManager()
            hrc_types = system_config.get_hrc_system_types()
            if not hrc_types or not isinstance(hrc_types, list):
                hrc_types = ['HRCT', 'HRCS', 'TEMP', 'PRESS']
        except:
            hrc_types = ['HRCT', 'HRCS', 'TEMP', 'PRESS']
            system_config = None
        
        hrc_type = st.selectbox("Controller Type 카테고리", [""] + hrc_types, index=0, help="시스템 설정에서 관리되는 Controller Type", key="hrc_type")
        
        # HRC Type에 따른 제품 타입 선택 - 시스템 설정에서 동적 로딩
        if hrc_type:
            try:
                if system_config:
                    product_types = system_config.get_hrc_product_types()
                    if not product_types or not isinstance(product_types, list):
                        product_types = ['YC60', 'YC120', 'YC240']
                else:
                    product_types = ['YC60', 'YC120', 'YC240']
            except:
                product_types = ['YC60', 'YC120', 'YC240']
            product_type_help = f"{hrc_type}의 제품 타입"
        else:
            product_types = []
            product_type_help = "먼저 HRC Type을 선택하세요"
        
        product_type = st.selectbox("제품 타입", [""] + product_types, index=0, help=product_type_help, key="hrc_product_type")
        
        # 모델 타입 선택 - 기본값 사용
        if hrc_type and product_type:
            if product_type == 'YC60':
                model_types = ['4', '7', '12', '16']
            elif product_type == 'YC120':
                model_types = ['8', '12', '16', '24']
            else:
                model_types = ['Zone4', 'Zone8', 'Zone12']
            model_type_help = f"{hrc_type}-{product_type}에 사용 가능한 모델 타입"
        else:
            model_types = []
            model_type_help = "먼저 HRC Type과 제품 타입을 선택하세요"
        
        model_type = st.selectbox("모델 타입", [""] + model_types, index=0, help=model_type_help, key="hrc_model_type")
        
        # 4단계: 존 번호 선택 (기본값 사용)
        zones = ['1', '2', '4', '6', '8', '12', '16', '20', '24']
        zone_number = st.selectbox(
            "존 번호", 
            [""] + zones, 
            index=0, 
            key="hrc_zone",
            help="HRC 존 번호"
        )
        
        # 존 번호 직접 입력 (Special 선택 시)
        custom_zone = ""
        if zone_number == "Special":
            custom_zone = st.text_input(
                "존 번호 직접 입력", 
                placeholder="예: 50, SP01, CUSTOM 등",
                key="hrc_custom_zone",
                help="특별한 존 번호를 직접 입력하세요"
            )
        
        # Cable 포함 여부
        cable_included = ""
        if hrc_type and product_type and model_type and (zone_number and zone_number != "Special" or custom_zone):
            cable_included = st.selectbox(
                "Cable 포함 여부",
                ["", "포함", "미포함"],
                index=0,
                key="hrc_cable"
            )
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        final_zone = custom_zone if zone_number == "Special" else zone_number
        
        if hrc_type and product_type and model_type and final_zone:
            zone_str = f"Zone{final_zone.zfill(2)}" if final_zone.isdigit() else f"Zone{final_zone}"
            
            # 제품명 자동 생성
            suggested_korean = f"HRC {product_type} {model_type} {zone_str}"
            suggested_english = f"HRC {product_type} {model_type} {zone_str}"
            suggested_vietnamese = f"HRC {product_type} {model_type} {zone_str}"
        
        korean_name = st.text_input(
            "한국어 제품명 *", 
            value=suggested_korean, 
            key="hrc_korean", 
            placeholder="예: 온도 제어기 YC60 Zone01"
        )
        english_name = st.text_input(
            "영어 제품명 *", 
            value=suggested_english, 
            key="hrc_english", 
            placeholder="예: Temperature Controller YC60 Zone01"
        )
        vietnamese_name = st.text_input(
            "베트남어 제품명", 
            value=suggested_vietnamese, 
            key="hrc_vietnamese", 
            placeholder="예: Bộ điều khiển nhiệt độ YC60 Zone01"
        )
        
        # 원산지 및 제조사 정보
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            # 원산지 선택
            countries = [
                'Korea', 'China', 'Japan', 'Germany', 'USA', 'Taiwan', 'Singapore', 
                'Italy', 'Switzerland', 'Austria', 'France', 'UK', 'Sweden', 'Denmark',
                'Netherlands', 'Belgium', 'Spain', 'Czech Republic', 'Poland', 'Turkey',
                'Thailand', 'Vietnam', 'Malaysia', 'Indonesia', 'Philippines', 'India',
                'Canada', 'Mexico', 'Brazil', 'Australia'
            ]
            hrc_origin_country = st.selectbox("원산지", [""] + sorted(countries), index=0, key="hrc_origin")
            
        with col_info2:
            hrc_manufacturer = st.text_input("제조사", placeholder="예: YUMOLD Co., Ltd.", key="hrc_manufacturer")
        
        # 공급처 정보 추가
        hrc_supplier = st.text_input("공급처", placeholder="예: ABC Trading Co.", key="hrc_supplier")
        
        # 기술 사양
        hrc_tech_spec = st.text_input("기술 사양", placeholder="예: YC60, 8Zone, BOX Type", key="hrc_tech_spec")
        hrc_unit = st.selectbox("단위", ["EA", "SET", "PCS"], index=0, key="hrc_unit")
    
    # 등록 버튼
    if st.button("🚀 HRC 제품 등록", type="primary", key="register_hrc_btn"):
        final_zone = custom_zone if zone_number == "Special" else zone_number
        
        if hrc_type and product_type and model_type and final_zone and korean_name and english_name:
            try:
                # 제품 코드 생성 - HRC 형태: HRC-HRCT-COLD-STANDARD-Zone01
                zone_formatted = final_zone.zfill(2) if final_zone.isdigit() else final_zone
                cable_suffix = f"-{cable_included}" if cable_included else ""
                generated_code = f"HRC-{hrc_type}-{product_type}-{model_type}-Zone{zone_formatted}{cable_suffix}"
                
                # 중복 제품 코드 체크
                try:
                    existing_master = master_product_manager.get_product_by_code(generated_code)
                    existing_sales = sales_product_manager.get_product_by_code(generated_code)
                    
                    # 중복이 있으면 번호 추가
                    counter = 1
                    original_code = generated_code
                    while existing_master or existing_sales:
                        generated_code = f"{original_code}-{counter}"
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                        existing_sales = sales_product_manager.get_product_by_code(generated_code)
                        counter += 1
                except:
                    # 중복 체크 실패 시 기본 코드 사용
                    pass
                
                # master_product_id 생성
                import uuid
                master_product_id = f"MP-{str(uuid.uuid4())[:8].upper()}"
                
                product_data = {
                    'master_product_id': master_product_id,
                    'product_code': generated_code,
                    'product_name': korean_name,
                    'product_name_en': english_name,
                    'product_name_vi': vietnamese_name or english_name,
                    'category_name': 'HRC',
                    'subcategory_name': hrc_type,
                    'origin_country': hrc_origin_country,
                    'manufacturer': hrc_manufacturer,
                    'supplier_name': hrc_supplier,
                    'specifications': hrc_tech_spec,
                    'unit': hrc_unit,
                    'status': 'active'
                }
                
                result = master_product_manager.add_master_product(product_data)
                
                # 결과 처리
                if isinstance(result, tuple):
                    success, message = result
                else:
                    success = result
                    message = "등록 완료" if success else "등록 실패"
                
                if success:
                    st.success(f"✅ HRC 제품이 등록되었습니다: {generated_code}")
                    
                    # 자동 동기화 제거 - 시스템 설정에서 관리
                    st.info("📋 제품이 통합 제품 관리에 등록되었습니다. 판매 제품 등록은 시스템 설정에서 관리할 수 있습니다.")
                    
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {message}")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        else:
            st.error("필수 필드를 모두 입력해주세요.")

def register_robot_product_form(master_product_manager, sales_product_manager):
    """ROBOT 제품 등록 폼 - 시스템 설정 연동"""
    st.markdown("### 🤖 산업용 로봇 제품 등록")
    st.info("산업용 로봇 제품을 등록합니다. (RBT-INDUSTRIAL-INJECTION-10KG-900MM-6AXIS 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # ROBOT 타입 선택 - 기본값 사용
        robot_types = ['Industrial', 'Collaborative', 'Mobile', 'Service']
        robot_type = st.selectbox("로봇 타입", [""] + robot_types, index=0, help="로봇 타입", key="robot_type")
        
        # 애플리케이션 선택 - 기본값 사용
        applications = ['Assembly', 'Welding', 'Painting', 'Handling', 'Inspection']
        application = st.selectbox("애플리케이션", [""] + applications, index=0, help="로봇 애플리케이션", key="robot_application")
        
        # 페이로드 선택 - 기본값 사용
        payloads = ['5kg', '10kg', '20kg', '50kg', '100kg']
        payload = st.selectbox("페이로드 (KG)", [""] + payloads, index=0, help="페이로드 용량", key="robot_payload")
        
        # 도달거리 선택 - 기본값 사용
        reaches = ['500mm', '800mm', '1200mm', '1500mm', '2000mm']
        reach = st.selectbox("도달거리 (MM)", [""] + reaches, index=0, help="로봇 도달거리", key="robot_reach")
        
        # 축 수 선택 - 기본값 사용
        axes = ['4', '5', '6', '7']
        axis = st.selectbox("축 수", [""] + axes, index=0, help="로봇 축 수", key="robot_axis")
        
        # 자동 코드 생성 안내
        if robot_type and application and payload and reach and axis:
            st.success("🔗 모든 옵션을 선택하면 제품 코드가 자동 생성됩니다.")
        else:
            st.info("모든 옵션을 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        if robot_type and application and payload and reach and axis:
            # 로봇 타입 변환
            type_names = {
                "INDUSTRIAL": ("산업용", "Industrial"),
                "COLLABORATIVE": ("협동", "Collaborative")
            }
            
            # 애플리케이션 변환
            app_names = {
                "INJECTION": ("사출성형", "Injection Molding"),
                "ASSEMBLY": ("조립", "Assembly"),
                "WELDING": ("용접", "Welding"),
                "PAINTING": ("도장", "Painting"),
                "MATERIAL_HANDLING": ("물류", "Material Handling")
            }
            
            if robot_type in type_names and application in app_names:
                suggested_korean = f"{type_names[robot_type][0]} {app_names[application][0]} 로봇 {payload}KG {reach}MM {axis}축"
                suggested_english = f"{type_names[robot_type][1]} {app_names[application][1]} Robot {payload}KG {reach}MM {axis}Axis"
                suggested_vietnamese = f"Robot {type_names[robot_type][1]} {app_names[application][1]} {payload}KG {reach}MM {axis} trục"
        
        korean_name = st.text_input("한국어 제품명 *", value=suggested_korean, key="robot_korean", placeholder="예: 산업용 사출성형 로봇 10KG 900MM 6축")
        english_name = st.text_input("영어 제품명 *", value=suggested_english, key="robot_english", placeholder="예: Industrial Injection Molding Robot 10KG 900MM 6Axis")
        vietnamese_name = st.text_input("베트남어 제품명", value=suggested_vietnamese, key="robot_vietnamese", placeholder="예: Robot công nghiệp ép phun 10KG 900MM 6 trục")
        
        # 원산지 및 제조사 정보
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            countries = [
                'Korea', 'China', 'Japan', 'Germany', 'USA', 'Taiwan', 'Singapore', 
                'Italy', 'Switzerland', 'Austria', 'France', 'UK', 'Sweden', 'Denmark',
                'Netherlands', 'Belgium', 'Spain', 'Czech Republic', 'Poland', 'Turkey',
                'Thailand', 'Vietnam', 'Malaysia', 'Indonesia', 'Philippines', 'India',
                'Canada', 'Mexico', 'Brazil', 'Australia'
            ]
            robot_origin_country = st.selectbox("원산지", [""] + sorted(countries), index=0, key="robot_origin")
            
        with col_info2:
            robot_manufacturer = st.text_input("제조사", placeholder="예: YUMOLD Co., Ltd.", key="robot_manufacturer")
        
        # 공급처 정보 추가
        robot_supplier = st.text_input("공급처", placeholder="예: ABC Trading Co.", key="robot_supplier")
        
        # 기술 사양
        robot_tech_spec = st.text_area("기술 사양", placeholder="로봇의 상세한 기술 사양을 입력하세요", key="robot_tech_spec")
        robot_unit = st.selectbox("단위", ["EA", "SET", "PCS"], index=0, key="robot_unit")
    
    # 등록 버튼
    if st.button("🚀 ROBOT 제품 등록", type="primary", key="register_robot_btn"):
        if robot_type and application and payload and reach and axis and korean_name and english_name:
            try:
                # 제품 코드 생성 - ROBOT 형태: RBT-6AXIS-INJECTION-10KG-900MM-6AXIS
                generated_code = f"RBT-{robot_type}-{application}-{payload}KG-{reach}MM-{axis}AXIS"
                
                # 중복 제품 코드 체크
                try:
                    existing_master = master_product_manager.get_product_by_code(generated_code)
                    existing_sales = sales_product_manager.get_product_by_code(generated_code)
                    
                    # 중복이 있으면 번호 추가
                    counter = 1
                    original_code = generated_code
                    while existing_master or existing_sales:
                        generated_code = f"{original_code}-{counter}"
                        existing_master = master_product_manager.get_product_by_code(generated_code)
                        existing_sales = sales_product_manager.get_product_by_code(generated_code)
                        counter += 1
                except:
                    # 중복 체크 실패 시 기본 코드 사용
                    pass
                
                # master_product_id 생성
                import uuid
                master_product_id = f"MP-{str(uuid.uuid4())[:8].upper()}"
                
                product_data = {
                    'master_product_id': master_product_id,
                    'product_code': generated_code,
                    'product_name': korean_name,
                    'product_name_en': english_name,
                    'product_name_vi': vietnamese_name or english_name,
                    'category_name': 'ROBOT',
                    'subcategory_name': robot_type,
                    'origin_country': robot_origin_country,
                    'manufacturer': robot_manufacturer,
                    'supplier_name': robot_supplier,
                    'specifications': robot_tech_spec,
                    'unit': robot_unit,
                    'status': 'active'
                }
                
                result = master_product_manager.add_master_product(product_data)
                
                # 결과 처리
                if isinstance(result, tuple):
                    success, message = result
                else:
                    success = result
                    message = "등록 완료" if success else "등록 실패"
                
                if success:
                    st.success(f"✅ ROBOT 제품이 등록되었습니다: {generated_code}")
                    
                    # 자동 동기화 제거 - 시스템 설정에서 관리
                    st.info("📋 제품이 통합 제품 관리에 등록되었습니다. 판매 제품 등록은 시스템 설정에서 관리할 수 있습니다.")
                    
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {message}")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        else:
            st.error("필수 필드를 모두 입력해주세요.")


# Utility functions for data processing
def format_currency(amount, currency_code="USD"):
    """화폐 형식으로 표시"""
    try:
        return f"{amount:,.0f} {currency_code}"
    except:
        return f"0 {currency_code}"

def calculate_percentage_change(old_value, new_value):
    """변화율 계산"""
    try:
        if old_value == 0:
            return 100.0 if new_value != 0 else 0.0
        return ((new_value - old_value) / old_value) * 100
    except:
        return 0.0

def show_product_edit_management(sales_product_manager):
    """제품 정보 수정 관리"""
    st.subheader("📝 제품 정보 수정")
    
    try:
        # 수정할 제품 선택
        all_products = sales_product_manager.get_all_prices()
        
        if len(all_products) > 0:
            product_options = ["선택하세요..."]
            product_mapping = {}
            
            for _, product in all_products.iterrows():
                product_code = product.get('product_code', 'N/A')
                product_name = product.get('product_name', 'N/A')
                option_text = f"{product_code} - {product_name}"
                product_options.append(option_text)
                product_mapping[option_text] = product.to_dict()
            
            selected_option = st.selectbox("수정할 제품 선택", product_options)
            
            if selected_option != "선택하세요..." and selected_option in product_mapping:
                selected_product = product_mapping[selected_option]
                
                st.success(f"✅ 선택된 제품: **{selected_product.get('product_code', 'N/A')}**")
                
                # 제품 정보 수정 폼
                with st.form("product_edit_form"):
                    st.subheader("제품 정보 수정")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_product_name = st.text_input(
                            "제품명", 
                            value=selected_product.get('product_name', ''),
                            placeholder="제품명을 입력하세요"
                        )
                        new_category = st.selectbox(
                            "카테고리",
                            ['HR', 'HRC', 'SERVICE', 'SPARE', 'GENERAL'],
                            index=['HR', 'HRC', 'SERVICE', 'SPARE', 'GENERAL'].index(selected_product.get('category', 'GENERAL'))
                        )
                        new_brand = st.text_input(
                            "브랜드",
                            value=selected_product.get('brand', ''),
                            placeholder="브랜드명 입력"
                        )
                    
                    with col2:
                        new_model = st.text_input(
                            "모델",
                            value=selected_product.get('model', ''),
                            placeholder="모델명 입력"
                        )
                        new_status = st.selectbox(
                            "상태",
                            ['active', 'inactive'],
                            index=['active', 'inactive'].index(selected_product.get('status', 'active'))
                        )
                    
                    new_description = st.text_area(
                        "제품 설명",
                        value=selected_product.get('description', ''),
                        placeholder="제품에 대한 상세 설명을 입력하세요"
                    )
                    
                    new_specifications = st.text_area(
                        "제품 사양",
                        value=selected_product.get('specifications', ''),
                        placeholder="제품 사양을 입력하세요"
                    )
                    
                    submitted = st.form_submit_button("💾 제품 정보 업데이트", type="primary")
                    
                    if submitted:
                        # 업데이트 데이터 준비
                        update_data = {
                            'product_name': new_product_name,
                            'category': new_category,
                            'brand': new_brand,
                            'model': new_model,
                            'status': new_status,
                            'description': new_description,
                            'specifications': new_specifications
                        }
                        
                        # 제품 정보 업데이트
                        success = sales_product_manager.update_sales_product(
                            selected_product.get('sales_product_id'), 
                            update_data
                        )
                        
                        if success:
                            st.success("✅ 제품 정보가 성공적으로 업데이트되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 제품 정보 업데이트에 실패했습니다.")
        else:
            st.info("등록된 판매 제품이 없습니다.")
            
    except Exception as e:
        st.error(f"제품 수정 중 오류: {str(e)}")

def show_product_delete_management(sales_product_manager):
    """제품 삭제 관리"""
    st.subheader("🗑️ 제품 삭제")
    st.warning("⚠️ 제품을 삭제하면 관련된 모든 가격 정보도 함께 삭제됩니다. 신중하게 선택하세요.")
    
    try:
        # 삭제할 제품 선택
        all_products = sales_product_manager.get_all_prices()
        
        if len(all_products) > 0:
            product_options = ["선택하세요..."]
            product_mapping = {}
            
            for _, product in all_products.iterrows():
                product_code = product.get('product_code', 'N/A')
                product_name = product.get('product_name', 'N/A')
                option_text = f"{product_code} - {product_name}"
                product_options.append(option_text)
                product_mapping[option_text] = product.to_dict()
            
            selected_option = st.selectbox("삭제할 제품 선택", product_options)
            
            if selected_option != "선택하세요..." and selected_option in product_mapping:
                selected_product = product_mapping[selected_option]
                
                st.error(f"⚠️ 삭제 예정 제품: **{selected_product.get('product_code', 'N/A')} - {selected_product.get('product_name', 'N/A')}**")
                
                # 삭제 확인
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**제품 정보:**")
                    st.write(f"- 제품 코드: {selected_product.get('product_code', 'N/A')}")
                    st.write(f"- 제품명: {selected_product.get('product_name', 'N/A')}")
                    st.write(f"- 카테고리: {selected_product.get('category', 'N/A')}")
                    st.write(f"- 상태: {selected_product.get('status', 'N/A')}")
                
                with col2:
                    confirm_text = st.text_input(
                        "삭제를 확인하려면 '삭제' 를 입력하세요:",
                        placeholder="삭제"
                    )
                    
                    if confirm_text == "삭제":
                        if st.button("🗑️ 제품 완전 삭제", type="primary"):
                            success = sales_product_manager.delete_sales_product(
                                selected_product.get('sales_product_id')
                            )
                            
                            if success:
                                st.success("✅ 제품이 성공적으로 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 제품 삭제에 실패했습니다.")
                    else:
                        st.info("삭제를 확인하려면 위에 '삭제'를 정확히 입력하세요.")
        else:
            st.info("등록된 판매 제품이 없습니다.")
            
    except Exception as e:
        st.error(f"제품 삭제 중 오류: {str(e)}")