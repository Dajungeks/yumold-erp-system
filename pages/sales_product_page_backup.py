import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from notification_helper import notify

def show_sales_product_page(sales_product_manager, product_manager, exchange_rate_manager, user_permissions, get_text, quotation_manager=None, customer_manager=None, supply_product_manager=None, pdf_design_manager=None, master_product_manager=None):
    """판매 제품 관리 페이지를 표시합니다."""
    
    st.header("💰 판매 제품 관리")
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 표준 판매가 관리",
        "🎯 HR 대량 가격 설정",
        "📊 가격 변경 이력",
        "💳 실제 판매 데이터",
        "📈 가격 편차 분석",
        "🏆 판매 성과 분석",
        "📝 견적 관리"
    ])
    
    with tab1:
        show_standard_price_management(sales_product_manager, product_manager, exchange_rate_manager)
    
    with tab2:
        show_hr_bulk_price_setting(sales_product_manager, product_manager, exchange_rate_manager)
    
    with tab3:
        show_price_history(sales_product_manager, product_manager)
    
    with tab4:
        show_sales_transactions(sales_product_manager)
    
    with tab5:
        show_price_variance_analysis(sales_product_manager)
    
    with tab6:
        show_sales_performance_analysis(sales_product_manager)
    
    with tab7:
        if quotation_manager and customer_manager and supply_product_manager and pdf_design_manager and master_product_manager:
            from pages.quotation_page import show_quotation_page
            show_quotation_page(
                quotation_manager,
                customer_manager,
                product_manager,
                sales_product_manager,
                supply_product_manager,
                pdf_design_manager,
                user_permissions,
                get_text,
                master_product_manager
            )
        else:
            st.warning("⚠️ 견적 관리 기능을 사용하려면 모든 필수 매니저가 필요합니다.")

def show_standard_price_management(sales_product_manager, product_manager, exchange_rate_manager):
    """표준 판매가 관리 페이지"""
    st.header("💰 표준 판매가 관리")
    
    # 관리 대상 제품 안내 문구 추가
    st.info("🎯 **표준 판매가 관리 대상 제품**\n"
           "- **HR** (Hot Runner) 제품: 핫런너 시스템 제품군\n"
           "- **HRC** (Controller) 제품: 컨트롤러 제품군\n"
           "- **Service** 제품: 서비스 및 가공 제품군\n"
           "- **Spare** 제품: 부품 및 교체재 제품군\n"
           "- **기타**: MB 제품을 제외한 모든 표준 제품\n\n"
           "💡 **MB 제품은 외주 공급가 관리에서 별도 관리됩니다**")
    
    tab1, tab2 = st.tabs(["📝 가격 설정", "📋 현재 가격 목록"])
    
    with tab1:
        st.subheader("표준 판매가 설정")
        
        # 마스터 제품 데이터베이스에서 제품 가져오기
        try:
            from master_product_manager import MasterProductManager
            master_manager = MasterProductManager()
            all_products = master_manager.get_all_products()
            
            if len(all_products) == 0:
                st.warning("등록된 제품이 없습니다. 먼저 제품을 등록해주세요.")
                return
            
            # MB 제품 필터링 (MB로 시작하는 제품코드 제외)
            non_mb_products = []
            for _, row in all_products.iterrows():
                product_code = str(row.get('product_code', '')).strip()
                if not product_code.startswith('MB-'):
                    non_mb_products.append(row)
            
            if len(non_mb_products) == 0:
                st.warning("표준 판매가 관리 대상 제품이 없습니다. MB 제품은 공급 제품 관리에서 가격을 설정해주세요.")
                return
            
            products = pd.DataFrame(non_mb_products)
            
        except Exception as e:
            st.error(f"제품 데이터 로드 중 오류가 발생했습니다: {str(e)}")
            return
        
        # 제품 선택 섹션
        st.subheader("🔍 제품 검색 및 선택")
        
        # 간단한 제품 드롭다운 방식
        product_options = []
        product_data = []
        
        # 제품 옵션 생성
        for _, row in products.iterrows():
            try:
                product_code = str(row.get('product_code', '')).strip()
                product_name_korean = str(row.get('product_name_korean', '')).strip()
                product_name_english = str(row.get('product_name_english', '')).strip()
                
                # 제품명이 있는 것 우선 사용
                product_name = product_name_korean if product_name_korean else product_name_english
                
                if product_code:
                    if product_name:
                        display_text = f"{product_code} - {product_name}"
                    else:
                        display_text = product_code
                    
                    # 카테고리 정보 추가
                    main_cat = str(row.get('main_category', '')).strip()
                    if main_cat and main_cat != 'nan' and main_cat != '':
                        display_text += f" [{main_cat}]"
                    
                    sub_cat = str(row.get('sub_category', '')).strip() 
                    if sub_cat and sub_cat != 'nan' and sub_cat != '':
                        display_text += f" ({sub_cat})"
                    
                    product_options.append(display_text)
                    product_data.append(row)
            except Exception as e:
                continue
        
        if len(product_options) == 0:
            st.error("선택할 수 있는 제품이 없습니다.")
            return
        
        # 제품 선택 드롭다운
        selected_product_display = st.selectbox(
            "판매가 설정할 제품 선택 *", 
            ["선택하세요..."] + product_options,
            help="판매가를 설정할 제품을 선택해주세요"
        )
        
        if not (selected_product_display and selected_product_display != "선택하세요..."):
            st.info("제품을 선택하면 판매가 설정 폼이 나타납니다.")
            return
        
        # 선택된 제품 정보
        selected_idx = product_options.index(selected_product_display)
        selected_product = product_data[selected_idx]
        
        # 현재 표준가 표시
        try:
            current_price = sales_product_manager.get_current_standard_price(selected_product.get('product_id', ''))
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
            
            # 기본값 설정 (USD에서 현지 통화로 환산)
            base_usd_price = float(selected_product.get('recommended_price_usd', 0))
            
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
                    from notification_helper import NotificationHelper
                    notification = NotificationHelper()
                    notification.show_success("표준 판매가", "등록")
                    
                    # 페이지 새로고침
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 저장 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("❌ 가격을 올바르게 입력해주세요.")
    
    else:
        st.info("⬆️ 위에서 제품을 선택하여 표준 판매가를 설정하세요.")
                        
                elif rate_period == "분기별 평균":
                    # 연도와 분기 선택
                    col_year, col_quarter = st.columns(2)
                    
                    with col_year:
                        from datetime import datetime as dt
                        current_year = dt.now().year
                        selected_year = st.selectbox("연도 선택", range(current_year-2, current_year+2), 
                                                   index=2, format_func=lambda x: f"{x}년", key="quarter_year")
                    
                    with col_quarter:
                        quarter_options = ["1분기 (1-3월)", "2분기 (4-6월)", "3분기 (7-9월)", "4분기 (10-12월)"]
                        current_month = dt.now().month
                        current_quarter = (current_month - 1) // 3
                        
                        # 진행 중인 분기는 데이터가 부족할 수 있으므로 이전 완료된 분기를 기본값으로 설정
                        if current_month <= 3:  # 1분기 진행 중
                            default_quarter = 3  # 작년 4분기
                        elif current_month <= 6:  # 2분기 진행 중
                            default_quarter = 0  # 1분기
                        elif current_month <= 9:  # 3분기 진행 중
                            default_quarter = 1  # 2분기
                        else:  # 4분기 진행 중
                            default_quarter = 2  # 3분기
                        
                        selected_quarter = st.selectbox("분기 선택", quarter_options, index=default_quarter)
                    
                    # 분기별 평균 환율 계산
                    quarter_num = int(selected_quarter.split('분기')[0])
                    
                    # 현재 진행 중인 분기인지 확인
                    current_date = dt.now()
                    is_current_quarter = (selected_year == current_date.year and 
                                        quarter_num == ((current_date.month - 1) // 3) + 1)
                    
                    try:
                        quarterly_rate = exchange_rate_manager.get_quarterly_average_rate(
                            local_currency, selected_year, quarter_num
                        )
                        
                        if quarterly_rate and quarterly_rate > 0:
                            exchange_rate = quarterly_rate
                            status_text = "(진행중)" if is_current_quarter else "(완료)"
                            st.info(f"{selected_year}년 {selected_quarter} 평균 환율 {status_text}: 1 USD = {exchange_rate:,.2f} {local_currency}")
                        else:
                            # 분기 데이터가 없으면 최신 환율 사용
                            rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                            if rate_info and rate_info.get('rate', 0) > 0:
                                exchange_rate = rate_info['rate']
                                if is_current_quarter:
                                    st.warning(f"진행 중인 분기입니다. 최신 환율 사용: 1 USD = {exchange_rate:,.2f} {local_currency}")
                                else:
                                    st.warning(f"분기 데이터 없음. 최신 환율 사용: 1 USD = {exchange_rate:,.2f} {local_currency}")
                            else:
                                raise ValueError("환율 조회 실패")
                    except Exception as e:
                        # 오류 발생 시 안전한 대체 환율 사용
                        try:
                            rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                            if rate_info and rate_info.get('rate', 0) > 0:
                                exchange_rate = rate_info['rate']
                                st.warning(f"분기 평균 계산 실패. 최신 환율 사용: 1 USD = {exchange_rate:,.2f} {local_currency}")
                            else:
                                # 통화별 기본 환율 설정
                                default_rates = {'VND': 24500, 'THB': 36.5, 'IDR': 15800, 'KRW': 1300, 'CNY': 7.2}
                                exchange_rate = default_rates.get(local_currency, 1.0)
                                st.error(f"환율 조회 실패. 임시 환율 사용: 1 USD = {exchange_rate:,.0f} {local_currency}")
                        except:
                            # 최종 대체 환율
                            default_rates = {'VND': 24500, 'THB': 36.5, 'IDR': 15800, 'KRW': 1300, 'CNY': 7.2}
                            exchange_rate = default_rates.get(local_currency, 1.0)
                            st.error(f"환율 시스템 오류. 임시 환율 사용: 1 USD = {exchange_rate:,.0f} {local_currency}")
                        
                else:  # 수동 입력
                    # 실제 환율을 기본값으로 사용
                    try:
                        rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                        default_rate = rate_info['rate'] if rate_info else 1.0
                    except:
                        default_rate = 1.0
                    
                    exchange_rate = st.number_input(f"환율 입력 (1 USD = ? {local_currency})", 
                                                   min_value=0.1, value=float(default_rate), step=0.1)
                
                # USD 환산가 계산 및 표시
                if new_price_local > 0:
                    new_price_usd = new_price_local / exchange_rate
                    st.metric("USD 환산가", f"${new_price_usd:.2f}", 
                             help=f"환율: 1 USD = {exchange_rate:,.2f} {local_currency}")
                else:
                    new_price_usd = 0.0
            
            # 가격 변경 사유 입력
            change_reason = st.text_input("가격 변경 사유 *", placeholder="예: 원자재 가격 상승, 시장 상황 변화 등")
            
            if st.button("💾 표준 가격 설정", type="primary", use_container_width=True):
                if new_price_local > 0 and new_price_usd > 0 and change_reason.strip():
                    success, result = sales_product_manager.set_standard_price(
                        product_id=selected_product['product_id'],
                        product_code=selected_product['product_code'],
                        product_name=selected_product['product_name'],
                        standard_price_usd=new_price_usd,
                        standard_price_local=new_price_local,
                        local_currency=local_currency,
                        change_reason=change_reason,
                        created_by=st.session_state.get('user_id', 'system')
                    )
                    
                    if success:
                        notify.show_operation_success("등록", f"표준 가격 (ID: {result})")
                        st.rerun()
                    else:
                        notify.show_operation_error("등록", result, "표준 가격")
                else:
                    notify.show_validation_error("필수 항목")
    
    with tab2:
        st.subheader("현재 표준 가격 목록")
        
        # 현재 활성 가격들 조회 (MB 제품 제외)
        try:
            price_df = pd.read_csv('data/product_price_history.csv', encoding='utf-8-sig')
            # 활성 가격에서 MB 제품 제외
            current_prices = price_df[
                (price_df['is_current'] == True) & 
                (~price_df['product_code'].str.startswith('MB-', na=False))
            ]
            
            if len(current_prices) > 0:
                # 페이지네이션 설정
                items_per_page = 10
                total_items = len(current_prices)
                total_pages = (total_items - 1) // items_per_page + 1
                
                # 페이지 번호 선택
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    current_page = st.selectbox(
                        f"페이지 선택 (총 {total_pages}페이지, {total_items}개 항목)",
                        range(1, total_pages + 1),
                        index=0,
                        key="price_page_selector"
                    )
                
                # 현재 페이지 데이터 계산
                start_idx = (current_page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, total_items)
                current_page_data = current_prices.iloc[start_idx:end_idx]
                
                # 페이지 정보 표시
                st.info(f"📄 {current_page}/{total_pages} 페이지 ({start_idx + 1}-{end_idx}/{total_items})")
                
                # 선택 삭제 기능 추가
                st.write("🗑️ **가격 삭제 관리**")
                
                # 삭제할 항목 선택
                selected_indices = []
                for idx, (_, row) in enumerate(current_page_data.iterrows()):
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
                    
                    with col1:
                        # 체크박스로 선택
                        is_selected = st.checkbox("선택", key=f"select_{row['price_id']}", label_visibility="collapsed")
                        if is_selected:
                            selected_indices.append(row['price_id'])
                    
                    with col2:
                        st.write(f"**{row['product_code']}**")
                        st.caption(row['product_name'] if pd.notna(row['product_name']) else "이름 없음")
                    
                    with col3:
                        st.write(f"${row['standard_price_usd']:,.2f}")
                    
                    with col4:
                        local_price = row['standard_price_local'] if pd.notna(row['standard_price_local']) else 0
                        currency = row['local_currency'] if pd.notna(row['local_currency']) else 'USD'
                        st.write(f"{local_price:,.0f} {currency}")
                    
                    with col5:
                        st.caption(str(row['effective_date']))
                
                # 삭제 버튼과 확인
                if selected_indices:
                    st.write(f"📋 선택된 항목: **{len(selected_indices)}개**")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                            # SalesProductManager를 통한 삭제 처리
                            success, message = sales_product_manager.delete_price_records(selected_indices)
                            
                            if success:
                                notify.show_operation_success("삭제", "", len(selected_indices))
                                st.rerun()
                            else:
                                notify.show_operation_error("삭제", message)
                    
                    with col2:
                        if st.button("❌ 선택 취소", use_container_width=True):
                            st.rerun()
                
                st.markdown("---")
                
                # 전체 가격 목록 표시 (읽기 전용)
                st.write("📋 **전체 가격 목록**")
                
                # 편집 가능한 데이터 표시
                display_df = current_page_data[['product_code', 'product_name', 'standard_price_usd', 
                                             'standard_price_local', 'local_currency', 'effective_date', 'change_reason']].copy()
                
                st.dataframe(
                    display_df,
                    column_config={
                        "product_code": st.column_config.TextColumn("제품코드"),
                        "product_name": st.column_config.TextColumn("제품명"),
                        "standard_price_usd": st.column_config.NumberColumn("표준가(USD)", format="$%.2f"),
                        "standard_price_local": st.column_config.NumberColumn("표준가(현지)", format="%.0f"),
                        "local_currency": st.column_config.TextColumn("통화"),
                        "effective_date": st.column_config.DateColumn("적용일"),
                        "change_reason": st.column_config.TextColumn("변경사유")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("📝 설정된 표준 가격이 없습니다. 위에서 새로운 가격을 설정해주세요.")
        
        except FileNotFoundError:
            st.info("📝 가격 데이터가 없습니다. 새로운 가격을 설정해주세요.")

def show_price_history(sales_product_manager, product_manager):
    """가격 변경 이력 페이지"""
    st.header("📊 가격 변경 이력")
    
    # 제품 선택 필터
    products = product_manager.get_all_products()
    if len(products) == 0:
        st.warning("등록된 제품이 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_options = ["전체"] + [f"{row['product_code']} - {row['product_name']}" for _, row in products.iterrows()]
        selected_filter = st.selectbox("제품 필터", product_options)
    
    with col2:
        date_range = st.date_input("기간 선택", value=[date.today().replace(month=1, day=1), date.today()], 
                                  help="시작일과 종료일을 선택하세요")
    
    # 이력 데이터 조회 및 표시
    try:
        history_df = pd.read_csv('data/product_price_history.csv', encoding='utf-8-sig')
        
        if len(history_df) > 0:
            # 필터 적용
            if selected_filter != "전체":
                selected_idx = product_options.index(selected_filter) - 1
                selected_product = products.iloc[selected_idx]
                history_df = history_df[history_df['product_id'] == selected_product['product_id']]
            
            if len(date_range) == 2:
                history_df['effective_date'] = pd.to_datetime(history_df['effective_date'], format='mixed', errors='coerce')
                start_date, end_date = date_range
                history_df = history_df[
                    (history_df['effective_date'] >= pd.Timestamp(start_date)) &
                    (history_df['effective_date'] <= pd.Timestamp(end_date))
                ]
            
            if len(history_df) > 0:
                # 삭제 기능 추가
                st.subheader("🗑️ 선택 삭제")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.info("💡 삭제할 가격 이력을 체크박스로 선택하고 삭제 버튼을 클릭하세요.")
                
                with col2:
                    delete_mode = st.checkbox("삭제 모드", help="체크하면 삭제 체크박스가 표시됩니다")
                
                # 편집 가능한 이력 테이블
                display_columns = ['product_code', 'product_name', 'standard_price_usd', 
                                 'standard_price_local', 'local_currency', 'effective_date', 
                                 'change_reason', 'created_by', 'is_current']
                
                # 삭제 모드인 경우 선택 컬럼 추가
                if delete_mode:
                    display_columns = ['_delete_'] + display_columns
                
                # 날짜 정렬을 위해 다시 파싱
                display_df = history_df[display_columns if not delete_mode else display_columns[1:]].copy()
                display_df['effective_date'] = pd.to_datetime(display_df['effective_date'], format='mixed', errors='coerce')
                
                # 삭제 선택 컬럼 추가
                if delete_mode:
                    display_df.insert(0, '_delete_', False)
                
                column_config = {
                    "product_code": st.column_config.TextColumn("제품코드", disabled=True),
                    "product_name": st.column_config.TextColumn("제품명", disabled=True),
                    "standard_price_usd": st.column_config.NumberColumn("표준가(USD)", format="$%.2f", disabled=True),
                    "standard_price_local": st.column_config.NumberColumn("표준가(현지)", disabled=True),
                    "local_currency": st.column_config.TextColumn("통화", disabled=True),
                    "effective_date": st.column_config.DatetimeColumn("적용일", disabled=True),
                    "change_reason": st.column_config.TextColumn("변경사유"),
                    "created_by": st.column_config.TextColumn("등록자", disabled=True),
                    "is_current": st.column_config.CheckboxColumn("현재가격")
                }
                
                if delete_mode:
                    column_config["_delete_"] = st.column_config.CheckboxColumn("선택")
                
                edited_history = st.data_editor(
                    display_df.sort_values('effective_date', ascending=False),
                    column_config=column_config,
                    hide_index=True,
                    use_container_width=True,
                    key="price_history_editor"
                )
                
                # 삭제 실행
                if delete_mode:
                    selected_for_deletion = edited_history[edited_history['_delete_'] == True]
                    
                    if len(selected_for_deletion) > 0:
                        st.warning(f"⚠️ 선택된 {len(selected_for_deletion)}개 이력이 삭제됩니다.")
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            if st.button("🗑️ 선택된 이력 삭제", type="primary", use_container_width=True):
                                try:
                                    # 삭제할 이력들의 인덱스 확인
                                    sorted_df = display_df.sort_values('effective_date', ascending=False).reset_index()
                                    selected_indices = selected_for_deletion.index.tolist()
                                    
                                    # 원본 데이터에서 해당 행들 제거
                                    original_indices = sorted_df.loc[selected_indices, 'index'].tolist()
                                    history_df_updated = history_df.drop(original_indices)
                                    
                                    # CSV 파일 업데이트
                                    history_df_updated.to_csv('data/product_price_history.csv', 
                                                            index=False, encoding='utf-8-sig')
                                    
                                    from notification_helper import NotificationHelper
                                    notification = NotificationHelper()
                                    notification.success("삭제", f"{len(selected_for_deletion)}개 가격 이력")
                                    
                                    st.rerun()
                                    
                                except Exception as e:
                                    from notification_helper import NotificationHelper
                                    notification = NotificationHelper()
                                    notification.error("삭제", f"오류: {str(e)}")
                        
                        with col2:
                            if st.button("❌ 취소", use_container_width=True):
                                st.rerun()
                
                # 수정사항 저장 버튼 (삭제 모드가 아닐 때만)
                if not delete_mode:
                    if st.button("💾 변경사항 저장", type="primary"):
                        try:
                            # 편집된 데이터로 업데이트
                            updated_df = edited_history.sort_values('effective_date', ascending=False)
                            
                            # 원본 데이터프레임 업데이트 (인덱스 매칭)
                            for idx, row in updated_df.iterrows():
                                # 해당 행을 원본에서 찾아 업데이트
                                mask = (
                                    (history_df['product_code'] == row['product_code']) &
                                    (pd.to_datetime(history_df['effective_date'], format='mixed') == row['effective_date'])
                                )
                                if mask.any():
                                    history_df.loc[mask, 'change_reason'] = row['change_reason']
                                    history_df.loc[mask, 'is_current'] = row['is_current']
                            
                            # CSV 파일 저장
                            history_df.to_csv('data/product_price_history.csv', 
                                            index=False, encoding='utf-8-sig')
                            
                            from notification_helper import NotificationHelper
                            notification = NotificationHelper()
                            notification.success("수정", "가격 이력 변경사항")
                            
                        except Exception as e:
                            from notification_helper import NotificationHelper
                            notification = NotificationHelper()
                            notification.error("수정", f"오류: {str(e)}")
                
                # 가격 변동 차트
                if selected_filter != "전체":
                    st.subheader("📈 가격 변동 추이")
                    chart_data = history_df[['effective_date', 'standard_price_usd']].sort_values('effective_date')
                    
                    fig = px.line(chart_data, x='effective_date', y='standard_price_usd',
                                title=f"가격 변동 추이: {selected_filter}",
                                labels={'effective_date': '날짜', 'standard_price_usd': '가격 (USD)'})
                    
                    fig.update_traces(mode='lines+markers')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("선택된 조건에 해당하는 이력이 없습니다.")
        else:
            st.info("가격 변경 이력이 없습니다.")
    
    except FileNotFoundError:
        st.info("가격 이력 데이터가 없습니다.")

def show_sales_transactions(sales_product_manager):
    """실제 판매 데이터 페이지"""
    st.header("💼 실제 판매 데이터")
    
    tab1, tab2 = st.tabs(["📝 판매 기록 입력", "📋 판매 이력"])
    
    with tab1:
        st.subheader("판매 거래 기록")
        
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_id = st.text_input("거래 ID", placeholder="자동 생성됩니다", disabled=True)
            product_code = st.text_input("제품 코드 *")
            quotation_id = st.text_input("견적서 ID")
            customer_name = st.text_input("고객명 *")
        
        with col2:
            quantity = st.number_input("판매 수량 *", min_value=1, value=1)
            unit_price_usd = st.number_input("단가 (USD) *", min_value=0.0)
            discount_amount = st.number_input("할인 금액 (USD)", min_value=0.0, value=0.0)
            discount_reason = st.text_input("할인 사유", placeholder="예: 대량 주문, 신규 고객 등")
        
        if st.button("💾 판매 기록 저장", type="primary", use_container_width=True):
            if product_code.strip() and customer_name.strip() and unit_price_usd > 0:
                # 실제 구현에서는 product_id와 customer_id를 조회해야 함
                success, result = sales_product_manager.record_sales_transaction(
                    product_id=f"P{product_code}",  # 임시
                    product_code=product_code,
                    quotation_id=quotation_id or "DIRECT",
                    customer_id=f"C{customer_name[:3].upper()}",  # 임시
                    customer_name=customer_name,
                    quantity=quantity,
                    unit_price_usd=unit_price_usd,
                    discount_amount=discount_amount,
                    discount_reason=discount_reason
                )
                
                if success:
                    st.success(f"✅ 판매 기록이 저장되었습니다. (ID: {result})")
                    st.rerun()
                else:
                    st.error(f"❌ 오류가 발생했습니다: {result}")
            else:
                st.warning("⚠️ 모든 필수 항목을 입력해주세요.")
    
    with tab2:
        st.subheader("판매 이력 조회")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.date_input("판매일 필터", value=date.today().replace(month=1, day=1))
        
        with col2:
            product_filter = st.text_input("제품 코드 필터")
        
        with col3:
            customer_filter = st.text_input("고객명 필터")
        
        # 판매 이력 표시
        try:
            sales_df = pd.read_csv('data/sales_transactions.csv', encoding='utf-8-sig')
            
            if len(sales_df) > 0:
                # 필터 적용
                if product_filter:
                    sales_df = sales_df[sales_df['product_code'].str.contains(product_filter, case=False, na=False)]
                if customer_filter:
                    sales_df = sales_df[sales_df['customer_name'].str.contains(customer_filter, case=False, na=False)]
                
                # 편집 가능한 판매 데이터 테이블
                display_columns = ['transaction_id', 'product_code', 'customer_name', 'quantity', 
                                 'unit_price_usd', 'total_amount_usd', 'price_variance_percent', 
                                 'discount_amount', 'sale_date']
                
                edited_sales = st.data_editor(
                    sales_df[display_columns].sort_values('sale_date', ascending=False),
                    column_config={
                        "transaction_id": st.column_config.TextColumn("거래ID", disabled=True),
                        "product_code": st.column_config.TextColumn("제품코드"),
                        "customer_name": st.column_config.TextColumn("고객명"),
                        "quantity": st.column_config.NumberColumn("수량"),
                        "unit_price_usd": st.column_config.NumberColumn("단가", format="$%.2f"),
                        "total_amount_usd": st.column_config.NumberColumn("총액", format="$%.2f", disabled=True),
                        "price_variance_percent": st.column_config.NumberColumn("편차율", format="%.1f%%", disabled=True),
                        "discount_amount": st.column_config.NumberColumn("할인액", format="$%.2f"),
                        "sale_date": st.column_config.DateColumn("판매일")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 삭제 버튼
                if st.button("🗑️ 선택된 거래 삭제", help="체크박스로 선택된 거래를 삭제합니다"):
                    st.warning("삭제 기능을 실행하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
            else:
                st.info("판매 이력이 없습니다.")
        
        except FileNotFoundError:
            st.info("판매 데이터가 없습니다.")

def show_price_variance_analysis(sales_product_manager):
    """가격 편차 분석 페이지"""
    st.header("📊 가격 편차 분석")
    
    # 분석 결과 표시
    variance_analysis = sales_product_manager.get_price_variance_analysis()
    
    if len(variance_analysis) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("제품별 가격 편차 현황")
            st.dataframe(variance_analysis, use_container_width=True)
        
        with col2:
            st.subheader("편차율 분포")
            fig = px.histogram(variance_analysis, x='평균_편차율', 
                             title="가격 편차율 분포",
                             labels={'평균_편차율': '평균 편차율 (%)', 'count': '제품 수'})
            st.plotly_chart(fig, use_container_width=True)
        
        # 상세 분석
        st.subheader("📈 상세 편차 분석")
        
        # 편차가 큰 제품들 경고
        high_variance = variance_analysis[abs(variance_analysis['평균_편차율']) > 10]
        if len(high_variance) > 0:
            st.warning("⚠️ 편차율이 10%를 초과하는 제품들:")
            st.dataframe(high_variance[['product_code', '평균_편차율', '총_매출액']], 
                        use_container_width=True)
    else:
        st.info("분석할 판매 데이터가 없습니다.")

def show_sales_performance_analysis(sales_product_manager):
    """판매 성과 분석 페이지"""
    st.header("🎯 판매 성과 분석")
    
    # 기간 선택
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("시작일", value=date.today().replace(month=1, day=1))
    
    with col2:
        end_date = st.date_input("종료일", value=date.today())
    
    # 성과 분석 데이터 조회
    analysis = sales_product_manager.get_sales_analysis(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if analysis['total_transactions'] > 0:
        # KPI 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 거래건수", f"{analysis['total_transactions']:,}")
        
        with col2:
            st.metric("총 판매수량", f"{analysis['total_quantity']:,}")
        
        with col3:
            st.metric("총 매출액", f"${analysis['total_revenue_usd']:,.2f}")
        
        with col4:
            st.metric("평균 편차율", f"{analysis['average_price_variance']:.1f}%")
        
        # 상세 거래 내역
        st.subheader("📋 거래 내역")
        transactions = analysis['transactions']
        
        if len(transactions) > 0:
            display_columns = ['product_code', 'customer_name', 'quantity', 
                             'unit_price_usd', 'total_amount_usd', 'price_variance_percent', 'sale_date']
            
            st.dataframe(
                transactions[display_columns],
                column_config={
                    "product_code": "제품코드",
                    "customer_name": "고객명",
                    "quantity": "수량",
                    "unit_price_usd": st.column_config.NumberColumn("단가", format="$%.2f"),
                    "total_amount_usd": st.column_config.NumberColumn("총액", format="$%.2f"),
                    "price_variance_percent": st.column_config.NumberColumn("편차율", format="%.1f%%"),
                    "sale_date": "판매일"
                },
                use_container_width=True
            )
    else:
        st.info("선택된 기간에 판매 데이터가 없습니다.")

def show_hr_bulk_price_setting(sales_product_manager, product_manager, exchange_rate_manager):
    """HR 제품 대량 가격 설정 페이지"""
    st.header("🎯 HR 핫런너 대량 가격 설정")
    
    st.info("🚀 **핫런너 시스템 Valve와 Open 제품의 가격을 일률적으로 설정할 수 있습니다**\n"
           "- **Valve 제품**: 밸브 타입 핫런너 시스템\n"
           "- **Open 제품**: 오픈 타입 핫런너 시스템\n"
           "- 설정된 가격은 표준 판매가 관리에 자동 등록됩니다")
    
    # 마스터 제품 매니저 가져오기
    if 'master_product_manager' not in st.session_state:
        st.error("마스터 제품 매니저가 초기화되지 않았습니다.")
        return
    
    master_product_manager = st.session_state.master_product_manager
    
    # HR 제품 목록 가져오기
    try:
        all_products = master_product_manager.get_all_products()
        
        if len(all_products) == 0:
            st.warning("마스터 제품 데이터가 없습니다.")
            return
        
        # HR 제품 필터링 (main_category가 'HR'인 제품들)
        hr_products = all_products[all_products['main_category'] == 'HR'].copy()
        
        if len(hr_products) == 0:
            st.warning("HR 카테고리 제품이 없습니다.")
            return
        
        # Valve와 Open 제품 분리
        valve_products = hr_products[hr_products['sub_category'] == 'Valve'].copy()
        open_products = hr_products[hr_products['sub_category'] == 'Open'].copy()
        
        st.markdown("---")
        
        # 현재 제품 현황 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 HR 제품", len(hr_products))
        with col2:
            st.metric("Valve 제품", len(valve_products))
        with col3:
            st.metric("Open 제품", len(open_products))
        
        st.markdown("---")
        
        # 대량 가격 설정 폼
        st.subheader("💰 대량 가격 설정")
        
        tab1, tab2 = st.tabs(["🔧 Valve 제품 가격 설정", "🌊 Open 제품 가격 설정"])
        
        with tab1:
            if len(valve_products) > 0:
                show_product_type_price_setting(valve_products, "Valve", sales_product_manager, exchange_rate_manager)
            else:
                st.info("Valve 타입 HR 제품이 없습니다.")
        
        with tab2:
            if len(open_products) > 0:
                show_product_type_price_setting(open_products, "Open", sales_product_manager, exchange_rate_manager)
            else:
                st.info("Open 타입 HR 제품이 없습니다.")
                
    except Exception as e:
        st.error(f"HR 제품 데이터 로딩 중 오류: {str(e)}")

def show_product_type_price_setting(products_df, product_type, sales_product_manager, exchange_rate_manager):
    """특정 타입(Valve/Open) 제품의 가격 설정"""
    
    st.write(f"**{product_type} 타입 제품: {len(products_df)}개**")
    
    # 제품 목록 미리보기
    with st.expander(f"📋 {product_type} 제품 목록 보기"):
        display_columns = ['product_code', 'product_name_korean', 'product_name_english']
        available_columns = [col for col in display_columns if col in products_df.columns]
        if available_columns:
            st.dataframe(products_df[available_columns], use_container_width=True)
        else:
            st.dataframe(products_df[['product_code']], use_container_width=True)
    
    st.markdown("---")
    
    # 가격 설정 폼
    with st.form(f"bulk_price_form_{product_type.lower()}"):
        st.subheader(f"💵 {product_type} 제품 일률 가격 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 원가 설정
            cost_price_usd = st.number_input(
                "원가 (USD)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                help=f"모든 {product_type} 제품에 적용할 원가"
            )
            
            # 표준 판매가 설정
            sale_price_usd = st.number_input(
                "표준 판매가 (USD)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                help=f"모든 {product_type} 제품에 적용할 판매가"
            )
        
        with col2:
            # 환율 정보 표시
            try:
                latest_rates = exchange_rate_manager.get_latest_rates()
                vnd_rate = latest_rates[latest_rates['currency_code'] == 'VND']['rate'].iloc[0] if len(latest_rates[latest_rates['currency_code'] == 'VND']) > 0 else 24500
                
                if cost_price_usd > 0:
                    st.info(f"**원가 환산**\n"
                           f"VND: {cost_price_usd * vnd_rate:,.0f} VND")
                
                if sale_price_usd > 0:
                    st.info(f"**판매가 환산**\n"
                           f"VND: {sale_price_usd * vnd_rate:,.0f} VND")
                    
                    if cost_price_usd > 0:
                        margin_percent = ((sale_price_usd - cost_price_usd) / cost_price_usd) * 100
                        st.success(f"**마진율**: {margin_percent:.1f}%")
                        
            except Exception as e:
                st.warning("환율 정보를 가져올 수 없습니다.")
        
        # 적용 설정
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            apply_cost = st.checkbox(f"{product_type} 제품 원가 일률 적용", value=True)
            apply_sale = st.checkbox(f"{product_type} 제품 판매가 일률 적용", value=True)
        
        with col2:
            effective_date = st.date_input(
                "적용 시작일",
                value=datetime.now().date(),
                help="가격 적용 시작일"
            )
        
        # 적용 버튼
        submitted = st.form_submit_button(
            f"🚀 {product_type} 제품 가격 일률 적용 ({len(products_df)}개)",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not apply_cost and not apply_sale:
                st.error("원가 또는 판매가 중 최소 하나는 선택해야 합니다.")
                return
            
            if apply_cost and cost_price_usd <= 0:
                st.error("원가를 0보다 큰 값으로 입력해주세요.")
                return
                
            if apply_sale and sale_price_usd <= 0:
                st.error("판매가를 0보다 큰 값으로 입력해주세요.")
                return
            
            # 대량 가격 적용 실행
            apply_bulk_pricing(products_df, product_type, cost_price_usd, sale_price_usd, 
                             apply_cost, apply_sale, effective_date, sales_product_manager)

def apply_bulk_pricing(products_df, product_type, cost_price_usd, sale_price_usd, 
                      apply_cost, apply_sale, effective_date, sales_product_manager):
    """대량 가격 적용 실행"""
    
    success_count = 0
    error_count = 0
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = len(st) == 0()
    
    total_products = len(products_df)
    
    for index, (_, product) in enumerate(products_df.iterrows()):
        try:
            product_code = product['product_code']
            
            # 진행 상황 업데이트
            progress = (index + 1) / total_products
            progress_bar.progress(progress)
            status_text.text(f"처리 중: {product_code} ({index + 1}/{total_products})")
            
            # 가격 데이터 준비
            price_data = {
                'product_code': product_code,
                'effective_date': effective_date,
                'created_by': st.session_state.get('user_id', 'system'),
                'notes': f"{product_type} 제품 대량 가격 설정"
            }
            
            # 원가 적용
            if apply_cost:
                price_data['cost_price_usd'] = cost_price_usd
            
            # 판매가 적용
            if apply_sale:
                price_data['sale_price_usd'] = sale_price_usd
            
            # 판매 제품 매니저에 가격 추가
            result = sales_product_manager.add_price_record(price_data)
            
            if result:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            st.error(f"{product_code} 처리 중 오류: {str(e)}")
    
    # 완료 메시지
    progress_bar.progress(1.0)
    status_text.text("완료!")
    
    if success_count > 0:
        notify("success", f"{product_type} 제품 가격 설정", 
               f"{success_count}개 제품의 가격이 성공적으로 설정되었습니다.")
        
        st.success(f"✅ **완료!**\n"
                  f"- 성공: {success_count}개\n"
                  f"- 실패: {error_count}개")
    
    if error_count > 0:
        st.warning(f"⚠️ {error_count}개 제품 처리 중 오류가 발생했습니다.")