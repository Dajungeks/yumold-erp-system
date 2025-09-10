"""
판매 제품 관리 페이지 - 간단한 버전
"""

import streamlit as st
import pandas as pd
from datetime import date


def show_sales_product_page(sales_product_manager, product_manager, exchange_rate_manager, user_permissions, get_text, quotation_manager=None, customer_manager=None, supply_product_manager=None, pdf_design_manager=None, master_product_manager=None):
    """판매 제품 관리 페이지를 표시합니다."""
    
    st.header("💰 판매 제품 관리")
    st.markdown("**HR=핫런너 시스템, HRC=핫런너 제어기 제품군**을 관리합니다.")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["🏷️ 표준 판매가 관리", "📋 가격 목록"])
    
    with tab1:
        show_standard_price_management(sales_product_manager, master_product_manager, exchange_rate_manager)
    
    with tab2:
        show_price_list(sales_product_manager)


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
            
            # HR, HRC 제품만 필터링 (MB 제품 제외)
            filtered_products = master_products[
                (master_products['main_category'].isin(['HR', 'HRC'])) &
                (~master_products['product_code'].str.startswith('MB-', na=False))
            ]
            
            if len(filtered_products) == 0:
                st.warning("HR/HRC 제품이 없습니다.")
                return
            
            # 제품 선택 드롭다운
            product_options = ["선택하세요..."] + [
                f"{row['product_code']} - {row.get('product_name_korean', row.get('product_name_english', '이름없음'))} [{row['main_category']}]"
                for _, row in filtered_products.iterrows()
            ]
            
            selected_option = st.selectbox("제품 선택 *", product_options)
            
            if selected_option != "선택하세요...":
                # 선택된 제품 정보
                selected_idx = product_options.index(selected_option) - 1
                selected_product = filtered_products.iloc[selected_idx]
                
                st.success(f"✅ 선택된 제품: **{selected_product['product_code']}**")
                
                # 현재 설정된 가격 표시
                try:
                    current_price = sales_product_manager.get_current_price(selected_product['product_code'])
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
                    
                    # 기본값 설정
                    base_usd_price = float(selected_product.get('recommended_price_usd', 100))
                    
                    if local_currency == "VND":
                        default_local_price = base_usd_price * 24000
                        currency_label = "표준 판매가 (VND) *"
                    elif local_currency == "THB":
                        default_local_price = base_usd_price * 36
                        currency_label = "표준 판매가 (THB) *"
                    elif local_currency == "IDR":
                        default_local_price = base_usd_price * 15000
                        currency_label = "표준 판매가 (IDR) *"
                    else:
                        default_local_price = base_usd_price
                        currency_label = f"표준 판매가 ({local_currency}) *"
                    
                    new_price_local = st.number_input(currency_label, min_value=0.0, value=default_local_price)
                
                with col2:
                    # 환율 설정
                    st.subheader("🔄 환율 설정")
                    
                    # 기본 환율 사용
                    default_rates = {"VND": 24000, "THB": 36, "IDR": 15000, "KRW": 1300, "MYR": 4.5}
                    exchange_rate = default_rates.get(local_currency, 1.0)
                    
                    # 수동 환율 입력 옵션
                    use_manual_rate = st.checkbox("수동 환율 입력")
                    if use_manual_rate:
                        exchange_rate = st.number_input(f"환율 (1 USD = ? {local_currency})", 
                                                      min_value=0.0, value=exchange_rate)
                    else:
                        st.info(f"기본 환율 사용: 1 USD = {exchange_rate:,.2f} {local_currency}")
                
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
                                notification.show_success("표준 판매가", "등록")
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
                
        except Exception as e:
            st.error(f"제품 데이터 로드 실패: {str(e)}")
    else:
        st.error("마스터 제품 매니저가 없습니다.")


def show_price_list(sales_product_manager):
    """가격 목록 표시"""
    st.subheader("📋 현재 표준 가격 목록")
    
    try:
        # 현재 활성 가격들 조회
        price_df = pd.read_csv('data/product_price_history.csv', encoding='utf-8-sig')
        
        # 활성 가격에서 MB 제품 제외
        current_prices = price_df[
            (price_df['is_current'] == True) & 
            (~price_df['product_code'].str.startswith('MB-', na=False))
        ]
        
        if len(current_prices) > 0:
            st.dataframe(
                current_prices[['product_code', 'product_name', 'standard_price_usd', 
                              'standard_price_local', 'local_currency', 'effective_date']],
                column_config={
                    "product_code": "제품코드",
                    "product_name": "제품명",
                    "standard_price_usd": st.column_config.NumberColumn("표준가(USD)", format="$%.2f"),
                    "standard_price_local": st.column_config.NumberColumn("표준가(현지)", format="%.0f"),
                    "local_currency": "통화",
                    "effective_date": "적용일"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("📝 설정된 표준 가격이 없습니다. 위에서 새로운 가격을 설정해주세요.")
    
    except FileNotFoundError:
        st.info("📝 가격 데이터가 없습니다. 새로운 가격을 설정해주세요.")
    except Exception as e:
        st.error(f"가격 목록 로드 실패: {str(e)}")