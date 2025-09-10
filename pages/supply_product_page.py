import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

def show_supply_product_page(supply_product_manager, master_product_manager, supplier_manager, exchange_rate_manager, user_permissions, get_text):
    """공급 제품 관리 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'supply_product_management', get_text)
    
    st.header("🏭 공급 제품 관리")
    
    # 탭 메뉴로 구성 - MB 제품 등록 기능 추가
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "➕ MB 제품 등록",
        "📋 외주 공급가 관리",
        "🎯 MB 대량 가격 설정",
        "📝 제품 정보 수정",
        "🗑️ 제품 삭제",
        "📊 환율 변동 모니터링",
        "📈 공급가 변동 이력",
        "🏆 공급업체 성과 분석",
        "🚨 가격 변동 알림"
    ])
    
    with tab1:
        show_mb_product_registration(master_product_manager, supply_product_manager, supplier_manager)
    
    with tab2:
        show_supplier_agreements(supply_product_manager, master_product_manager, supplier_manager, exchange_rate_manager)
    
    with tab3:
        show_mb_bulk_price_setting(supply_product_manager, master_product_manager, supplier_manager, exchange_rate_manager)
    
    with tab4:
        show_supply_product_edit_management(supply_product_manager)
    
    with tab5:
        show_supply_product_delete_management(supply_product_manager)
    
    with tab6:
        show_exchange_rate_monitoring(supply_product_manager, exchange_rate_manager)
    
    with tab7:
        show_price_change_history(supply_product_manager, supplier_manager)
    
    with tab8:
        show_supplier_performance(supply_product_manager)
    
    with tab9:
        show_price_alerts(supply_product_manager)

def show_supplier_agreements(supply_product_manager, master_product_manager, supplier_manager, exchange_rate_manager):
    """외주 공급가 관리 페이지"""
    st.header("🏭 외주 공급가 관리")
    
    # MB 제품 전용 안내 문구 추가
    st.info("🎯 **외주 공급가 관리는 MB 제품 전용입니다**\n"
           "- MB- 접두사로 시작하는 제품만 가격 등록이 가능합니다\n"
           "- 외주 가공 및 특수 제조 제품의 공급가격을 관리합니다\n"
           "- 기본 통화는 CNY(위안)이며 USD 환산가도 제공됩니다")
    
    tab1, tab2 = st.tabs(["📝 새 협정 등록", "📋 기존 협정 관리"])
    
    with tab1:
        st.subheader("공급업체 협정 등록")
        
        # 제품 선택 및 검색 - 마스터 제품 데이터베이스에서 MB 제품만 로드
        all_products_df = master_product_manager.get_all_products()
        if len(all_products_df) == 0:
            st.warning("등록된 제품이 없습니다. 먼저 제품을 등록해주세요.")
            return
            
        # MB 제품만 필터링 (마스터 제품 DB에서)
        mb_mask = all_products_df['product_code'].str.startswith('MB-', na=False)
        products = all_products_df[mb_mask].copy()
        
        if len(products) == 0:
            st.warning("⚠️ MB 제품이 없습니다. 외주 공급가 관리는 MB- 접두사로 시작하는 제품만 지원합니다.")
            return
        
        st.subheader("🔍 제품 검색 및 선택")
        
        # 검색 필터
        col_search1, col_search2, col_search3 = st.columns(3)
        
        with col_search1:
            search_term = st.text_input("🔍 제품 검색", 
                                      placeholder="MB로 시작하는 제품만 검색 가능",
                                      help="MB- 접두사로 시작하는 제품만 검색 가능합니다",
                                      key="supplier_agreements_search")
        
        with col_search2:
            # MB 제품의 카테고리만 표시
            if len(products) > 0:
                # 카테고리 컬럼이 있는지 확인하고 사용
                category_col = None
                for col in ['category1', 'main_category', 'category']:
                    if col in products.columns:
                        category_col = col
                        break
                
                if category_col:
                    mb_categories = ["전체"] + list(products[category_col].dropna().unique())
                else:
                    mb_categories = ["전체"]
            else:
                mb_categories = ["전체"]
            category_filter = st.selectbox("카테고리 필터", mb_categories)
        
        with col_search3:
            # 등록된 공급업체 목록 가져오기
            suppliers = supplier_manager.get_all_suppliers()
            if len(suppliers) > 0:
                supplier_options = ["전체"] + [f"{row['supplier_id']} - {row['company_name']}" for _, row in suppliers.iterrows()]
                supplier_filter = st.selectbox("공급업체 필터", supplier_options)
            else:
                supplier_filter = st.selectbox("공급업체 필터", ["전체"])
        
        # 검색 및 필터링 적용 (이미 MB 제품만 로드됨)
        filtered_products = products.copy()
        
        if search_term:
            # 제품 코드에서 검색어가 포함된 것만 필터링
            search_mask = filtered_products['product_code'].str.contains(search_term, case=False, na=False)
            
            # 마스터 제품 DB의 제품명 필드들에서도 검색
            if 'product_name_korean' in filtered_products.columns:
                search_mask = search_mask | filtered_products['product_name_korean'].str.contains(search_term, case=False, na=False)
            if 'product_name_english' in filtered_products.columns:
                search_mask = search_mask | filtered_products['product_name_english'].str.contains(search_term, case=False, na=False)
            if 'product_name_vietnamese' in filtered_products.columns:
                search_mask = search_mask | filtered_products['product_name_vietnamese'].str.contains(search_term, case=False, na=False)
                
            filtered_products = filtered_products[search_mask]
        
        category_col = 'main_category' if 'main_category' in filtered_products.columns else 'category'
        if category_filter != "전체" and category_col:
            filtered_products = filtered_products[filtered_products[category_col] == category_filter]
            
        if supplier_filter != "전체":
            # 공급업체 필터에서 선택된 공급업체 ID 추출
            selected_supplier_id = supplier_filter.split(" - ")[0]
            filtered_products = filtered_products[filtered_products['supplier_id'] == selected_supplier_id]
        
        # 검색 결과 표시
        if len(filtered_products) == 0:
            st.warning("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
            return
        
        st.info(f"검색 결과: {len(filtered_products)}개 제품 발견")
        
        # 변수 초기화
        supplier_id = ""
        supplier_name = ""
        selected_product = None
        selected_product_display = ""
        local_currency = "USD"
        agreement_price = 0.0
        agreement_price_display = 0.0
        base_rate = 1.0
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 검색된 제품만 선택 옵션으로 표시
            product_options = []
            for _, row in filtered_products.iterrows():
                product_name = str(row.get('product_name_korean', row.get('product_name_english', row.get('product_code', ''))))
                display_text = f"{row['product_code']} - {product_name[:50]}"
                if len(product_name) > 50:
                    display_text += "..."
                product_options.append(display_text)
            
            if len(product_options) > 10:
                st.warning(f"검색 결과가 많습니다 ({len(product_options)}개). 더 구체적인 검색어를 사용해보세요.")
            
            # 세션 상태에서 자동 선택된 제품 확인
            auto_selected_code = st.session_state.get('product_for_supply_setting', None)
            default_index = 0
            
            if auto_selected_code:
                # 자동 선택된 제품이 있으면 해당 제품을 기본값으로 설정
                for i, option in enumerate(product_options):
                    if auto_selected_code in option:
                        default_index = i + 1  # "선택하세요..." 옵션 때문에 +1
                        break
                # 세션 상태 정리
                if 'product_for_supply_setting' in st.session_state:
                    del st.session_state['product_for_supply_setting']
            
            selected_product_display = st.selectbox("제품 선택 *", 
                                                   ["선택하세요..."] + product_options,
                                                   index=default_index,
                                                   help="위의 검색 필터를 사용해 제품을 찾아보세요")
            
            if selected_product_display and selected_product_display != "선택하세요...":
                try:
                    selected_idx = product_options.index(selected_product_display)
                    selected_product = filtered_products.iloc[selected_idx]
                    
                    # 선택된 제품 정보 표시
                    st.success(f"✅ 선택된 제품: {selected_product['product_code']}")
                    with st.expander("제품 상세 정보"):
                        st.write(f"**제품명 (한국어):** {selected_product.get('product_name_korean', 'N/A')}")
                        st.write(f"**제품명 (영어):** {selected_product.get('product_name_english', 'N/A')}")
                        st.write(f"**제품명 (베트남어):** {selected_product.get('product_name_vietnamese', 'N/A')}")
                        st.write(f"**카테고리:** {selected_product.get('main_category', 'N/A')}")
                        st.write(f"**재고:** {selected_product.get('stock_quantity', 'N/A')}")
                except (ValueError, IndexError):
                    selected_product = None
                    st.error("제품 선택 중 오류가 발생했습니다.")
            else:
                selected_product = None
        
        with col2:
            # 등록된 공급업체 목록 가져오기
            suppliers = supplier_manager.get_all_suppliers()
            if len(suppliers) > 0:
                supplier_options = [f"{row['supplier_id']} - {row['company_name']}" for _, row in suppliers.iterrows()]
                selected_supplier_display = st.selectbox("공급업체 선택 *", 
                                                        ["선택하세요..."] + supplier_options)
                
                if selected_supplier_display and selected_supplier_display != "선택하세요...":
                    supplier_idx = supplier_options.index(selected_supplier_display)
                    selected_supplier = suppliers.iloc[supplier_idx]
                    supplier_id = selected_supplier['supplier_id']
                    supplier_name = selected_supplier['company_name']
                    
                    st.success(f"✅ 선택된 공급업체: {supplier_id} - {supplier_name}")
                else:
                    supplier_id = ""
                    supplier_name = ""
            else:
                st.warning("등록된 공급업체가 없습니다. 먼저 공급업체를 등록해주세요.")
                supplier_id = st.text_input("공급업체 ID *")
                supplier_name = st.text_input("공급업체명 *")
        
        # 제품과 공급업체가 모두 선택된 경우에만 가격 설정 진행
        if selected_product is not None and supplier_id and supplier_name:
            st.subheader("💰 가격 및 통화 설정")
            
            # 제품 코드에 따른 기본 통화 설정
            product_code = selected_product.get('product_code', '')
            if product_code.startswith('MB-'):
                default_currency = "CNY"
                currency_options = ["CNY", "USD", "KRW", "VND", "THB", "IDR", "MYR"]
                price_label = "협정가 (CNY) *"
                default_price = float(selected_product.get('cost_price_usd', 0)) * 7.2  # CNY 환산
            else:
                default_currency = "USD"
                currency_options = ["USD", "CNY", "KRW", "VND", "THB", "IDR", "MYR"]
                price_label = "협정가 (USD) *"
                default_price = float(selected_product.get('cost_price_usd', 0))
            
            col_price1, col_price2 = st.columns(2)
            
            with col_price1:
                agreement_price = st.number_input(price_label, min_value=0.0, value=default_price)
            
            with col_price2:
                local_currency = st.selectbox("공급 통화 *", currency_options, 
                                        index=currency_options.index(default_currency))
            
            # 기본 변수 초기화
            agreement_price_display = agreement_price
            base_rate = 1.0
            
            # 현재 가격이 기본 통화가 아닌 경우 환율 조회
            if local_currency != default_currency:
                try:
                    rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                    if rate_info and isinstance(rate_info, dict) and 'rate' in rate_info:
                        if default_currency == "CNY":
                            # CNY 기준에서 다른 통화로 변환
                            if local_currency == "USD":
                                auto_local_price = agreement_price / 7.2  # CNY to USD 대략
                            else:
                                # CNY -> USD -> 현지통화
                                usd_price = agreement_price / 7.2
                                auto_local_price = usd_price * rate_info['rate']
                        else:
                            # USD 기준에서 다른 통화로 변환
                            auto_local_price = agreement_price * rate_info['rate']
                        
                        base_rate = rate_info['rate']
                        st.info(f"현재 환율: 1 USD = {base_rate:.2f} {local_currency}")
                        agreement_price_display = st.number_input(f"협정가 ({local_currency})", 
                                                              min_value=0.0, value=auto_local_price)
                    else:
                        base_rate = st.number_input("기준 환율", min_value=0.0, help="1 USD = ? 현지통화")
                        agreement_price_display = st.number_input(f"협정가 ({local_currency})", min_value=0.0)
                except:
                    base_rate = st.number_input("기준 환율", min_value=0.0)
                    agreement_price_display = st.number_input(f"협정가 ({local_currency})", min_value=0.0)
            else:
                # 기본 통화인 경우
                agreement_price_display = agreement_price
                base_rate = 1.0
        
        # 협정 조건
        st.subheader("📋 협정 조건")
        col3, col4 = st.columns(2)
        
        with col3:
            start_date = st.date_input("협정 시작일 *", value=date.today())
            minimum_quantity = st.number_input("최소 주문 수량", min_value=1, value=1)
            
        with col4:
            end_date = st.date_input("협정 종료일 *", value=date.today().replace(year=date.today().year + 1))
            payment_terms = st.selectbox("결제 조건", ["NET 30", "NET 15", "NET 60", "COD", "선불", "기타"])
        
        agreement_conditions = st.text_area("기타 협정 조건", 
                                          placeholder="품질 기준, 납기 조건, 특별 할인 등을 입력하세요")
        
        # 협정 등록 버튼
        submitted = st.button("💾 협정 등록", type="primary", use_container_width=True)
        
        if submitted:
            # 유효성 검사
            if selected_product is None:
                st.warning("제품을 선택해주세요.")
                return
            
            if not supplier_id or not supplier_name:
                st.warning("공급업체를 선택해주세요.")
                return
                
            # USD 가격과 현지 가격 계산
            if local_currency == "USD":
                agreement_price_usd = agreement_price_display
                agreement_price_local = agreement_price_display
            else:
                # 현지 통화를 USD로 변환
                if base_rate > 0:
                    agreement_price_usd = agreement_price_display / base_rate
                    agreement_price_local = agreement_price_display
                else:
                    agreement_price_usd = agreement_price
                    agreement_price_local = agreement_price
            
            try:
                success, result = supply_product_manager.create_supplier_agreement(
                    product_id=selected_product['product_id'],
                    product_code=selected_product['product_code'],
                    product_name=selected_product.get('product_name_korean', selected_product.get('product_name_english', selected_product.get('product_code', ''))),
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    agreement_price_usd=agreement_price_usd,
                    agreement_price_local=agreement_price_local,
                    local_currency=local_currency,
                    base_exchange_rate=base_rate,
                    agreement_start_date=start_date.strftime('%Y-%m-%d'),
                    agreement_end_date=end_date.strftime('%Y-%m-%d'),
                    minimum_quantity=minimum_quantity,
                    payment_terms=payment_terms,
                    agreement_conditions=agreement_conditions,
                    created_by=st.session_state.get('user_id', 'system')
                )
                
                if success:
                    st.success(f"협정이 등록되었습니다. (ID: {result})")
                    st.rerun()
                else:
                    st.error(f"오류가 발생했습니다: {result}")
            except Exception as e:
                st.error(f"협정 등록 중 오류가 발생했습니다: {str(e)}")
    
    with tab2:
        st.subheader("기존 협정 관리")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("상태 필터", ["전체", "활성", "비활성"])
        
        with col2:
            supplier_filter = st.text_input("공급업체 필터", key="exchange_rate_supplier_filter")
        
        with col3:
            product_filter = st.text_input("제품 필터", key="exchange_rate_product_filter")
        
        # 협정 목록 조회
        active_agreements = supply_product_manager.get_active_agreements()
        
        if len(active_agreements) > 0:
            # 필터 적용
            filtered_agreements = active_agreements.copy()
            
            if status_filter == "활성":
                filtered_agreements = filtered_agreements[filtered_agreements['is_active'] == True]
            elif status_filter == "비활성":
                filtered_agreements = filtered_agreements[filtered_agreements['is_active'] == False]
            
            if supplier_filter:
                filtered_agreements = filtered_agreements[
                    filtered_agreements['supplier_name'].str.contains(supplier_filter, case=False, na=False)
                ]
            
            if product_filter:
                filtered_agreements = filtered_agreements[
                    filtered_agreements['product_code'].str.contains(product_filter, case=False, na=False)
                ]
            
            if len(filtered_agreements) > 0:
                # 페이지네이션 설정
                items_per_page = 10
                total_items = len(filtered_agreements)
                total_pages = (total_items - 1) // items_per_page + 1
                
                # 페이지 번호 선택
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    current_page = st.selectbox(
                        f"페이지 선택 (총 {total_pages}페이지, {total_items}개 협정)",
                        range(1, total_pages + 1),
                        index=0,
                        key="supply_agreement_page_selector"
                    )
                
                # 현재 페이지 데이터 계산
                start_idx = (current_page - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, total_items)
                current_page_data = filtered_agreements.iloc[start_idx:end_idx]
                
                # 페이지 정보 표시
                st.info(f"📄 {current_page}/{total_pages} 페이지 ({start_idx + 1}-{end_idx}/{total_items})")
                
                # 편집 가능한 협정 테이블
                display_columns = ['agreement_id', 'product_code', 'supplier_name', 
                                 'agreement_price_usd', 'agreement_price_local', 'local_currency',
                                 'agreement_start_date', 'agreement_end_date', 'minimum_quantity', 
                                 'payment_terms', 'agreement_conditions', 'is_active']
                
                # 날짜 컬럼을 문자열로 처리하여 호환성 문제 해결
                display_data = current_page_data[display_columns].copy()
                
                edited_agreements = st.data_editor(
                    display_data,
                    column_config={
                        "agreement_id": st.column_config.TextColumn("협정ID", disabled=True),
                        "product_code": st.column_config.TextColumn("제품코드", disabled=True),
                        "supplier_name": st.column_config.TextColumn("공급업체"),
                        "agreement_price_usd": st.column_config.NumberColumn("협정가(USD)", format="$%.2f"),
                        "agreement_price_local": st.column_config.NumberColumn("협정가(현지)"),
                        "local_currency": st.column_config.TextColumn("통화", disabled=True),
                        "agreement_start_date": st.column_config.TextColumn("시작일"),
                        "agreement_end_date": st.column_config.TextColumn("종료일"),
                        "minimum_quantity": st.column_config.NumberColumn("최소수량"),
                        "payment_terms": st.column_config.TextColumn("결제조건"),
                        "agreement_conditions": st.column_config.TextColumn("협정조건"),
                        "is_active": st.column_config.CheckboxColumn("활성상태")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 액션 버튼들
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
                        if supply_product_manager.update_agreements_batch(edited_agreements, current_page_data):
                            st.success("협정 정보가 성공적으로 업데이트되었습니다!")
                            st.rerun()
                        else:
                            st.error("협정 정보 업데이트 중 오류가 발생했습니다.")
                
                with col_btn2:
                    # 삭제할 협정 선택
                    selected_agreements = st.multiselect(
                        "삭제할 협정 선택",
                        options=current_page_data['agreement_id'].tolist(),
                        format_func=lambda x: f"{x} - {current_page_data[current_page_data['agreement_id']==x]['product_code'].iloc[0]}"
                    )
                    
                with col_btn3:
                    if st.button("🗑️ 선택 항목 삭제", use_container_width=True):
                        if selected_agreements:
                            if supply_product_manager.delete_agreements(selected_agreements):
                                st.success(f"{len(selected_agreements)}개 협정이 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("협정 삭제 중 오류가 발생했습니다.")
                        else:
                            st.warning("삭제할 협정을 선택해주세요.")
            else:
                st.info("필터 조건에 맞는 협정이 없습니다.")
        else:
            st.info("등록된 협정이 없습니다. 새 협정을 등록해주세요.")

def show_exchange_rate_monitoring(supply_product_manager, exchange_rate_manager):
    """환율 변동 모니터링 페이지"""
    st.header("📈 환율 변동 모니터링")
    
    # 환율 영향 분석 실행
    if st.button("🔄 환율 영향 분석 실행", type="primary"):
        with st.spinner("환율 영향을 분석 중입니다..."):
            impact_analysis = supply_product_manager.analyze_exchange_rate_impact(exchange_rate_manager)
        
        if len(impact_analysis) > 0:
            st.success("환율 영향 분석이 완료되었습니다.")
            
            # 경고 레벨별 요약
            col1, col2, col3 = st.columns(3)
            
            with col1:
                high_alerts = len(impact_analysis[impact_analysis['alert_level'] == 'HIGH'])
                st.metric("높은 위험", high_alerts, help="10% 이상 변동")
            
            with col2:
                medium_alerts = len(impact_analysis[impact_analysis['alert_level'] == 'MEDIUM'])
                st.metric("중간 위험", medium_alerts, help="5-10% 변동")
            
            with col3:
                low_alerts = len(impact_analysis[impact_analysis['alert_level'] == 'LOW'])
                st.metric("낮은 위험", low_alerts, help="5% 미만 변동")
            
            # 상세 분석 결과
            st.subheader("📊 상세 환율 영향 분석")
            
            display_columns = ['product_id', 'supplier_id', 'base_exchange_rate', 
                             'current_exchange_rate', 'rate_change_percent',
                             'agreement_price_usd', 'current_equivalent_usd', 
                             'price_impact_usd', 'price_impact_percent', 'alert_level']
            
            edited_impact = st.data_editor(
                impact_analysis[display_columns].sort_values('price_impact_percent', ascending=False),
                column_config={
                    "product_id": st.column_config.TextColumn("제품ID"),
                    "supplier_id": st.column_config.TextColumn("공급업체ID"),
                    "base_exchange_rate": st.column_config.NumberColumn("기준환율", format="%.2f"),
                    "current_exchange_rate": st.column_config.NumberColumn("현재환율", format="%.2f"),
                    "rate_change_percent": st.column_config.NumberColumn("환율변동", format="%.1f%%"),
                    "agreement_price_usd": st.column_config.NumberColumn("협정가", format="$%.2f"),
                    "current_equivalent_usd": st.column_config.NumberColumn("현재환산가", format="$%.2f"),
                    "price_impact_usd": st.column_config.NumberColumn("가격영향", format="$%.2f"),
                    "price_impact_percent": st.column_config.NumberColumn("영향률", format="%.1f%%"),
                    "alert_level": st.column_config.TextColumn("위험도")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 환율 변동 차트
            if len(impact_analysis) > 0:
                st.subheader("📈 환율 변동 시각화")
                
                # 가격 영향도 차트
                fig_impact = px.bar(
                    impact_analysis, 
                    x='product_id', 
                    y='price_impact_percent',
                    color='alert_level',
                    title="제품별 가격 영향도",
                    labels={'price_impact_percent': '가격 영향률 (%)', 'product_id': '제품 ID'},
                    color_discrete_map={'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'green'}
                )
                st.plotly_chart(fig_impact, use_container_width=True)
                
                # 환율 변동 차트
                fig_rate = px.scatter(
                    impact_analysis,
                    x='rate_change_percent',
                    y='price_impact_percent',
                    size='agreement_price_usd',
                    color='alert_level',
                    title="환율 변동 vs 가격 영향",
                    labels={'rate_change_percent': '환율 변동률 (%)', 'price_impact_percent': '가격 영향률 (%)'},
                    hover_data=['product_id', 'supplier_id']
                )
                st.plotly_chart(fig_rate, use_container_width=True)
        else:
            st.info("분석할 협정 데이터가 없습니다.")

def show_price_change_history(supply_product_manager, supplier_manager):
    """공급가 변동 이력 페이지"""
    st.header("📋 공급가 변동 이력")
    
    # 필터링 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input("변경일 범위", 
                                  value=[date.today().replace(month=1, day=1), date.today()])
    
    with col2:
        # 공급업체 목록 가져오기
        suppliers = supplier_manager.get_all_suppliers()
        supplier_options = ["전체"] + [f"{row['company_name']} ({row['supplier_id']})" for _, row in suppliers.iterrows()]
        selected_supplier_filter = st.selectbox(
            "공급업체 필터",
            supplier_options,
            key="price_history_supplier_filter"
        )
    
    # 이력 데이터 조회
    try:
        history_df = pd.read_csv('data/supply_price_history.csv', encoding='utf-8-sig')
        
        if len(history_df) > 0:
            # 필터 적용
            if selected_supplier_filter and selected_supplier_filter != "전체":
                # 선택된 공급업체 ID 추출
                supplier_id = selected_supplier_filter.split("(")[-1].split(")")[0]
                history_df = history_df[history_df['supplier_id'] == supplier_id]
            
            if len(date_range) == 2:
                history_df['change_date'] = pd.to_datetime(history_df['change_date'])
                start_date, end_date = date_range
                history_df = history_df[
                    (history_df['change_date'] >= pd.Timestamp(start_date)) &
                    (history_df['change_date'] <= pd.Timestamp(end_date))
                ]
            
            if len(history_df) > 0:
                # 편집 가능한 이력 테이블
                display_columns = ['price_history_id', 'product_id', 'supplier_id',
                                 'old_price_usd', 'new_price_usd', 'old_price_local', 'new_price_local',
                                 'exchange_rate_at_change', 'change_reason', 'change_date', 'created_by']
                
                history_df_sorted = history_df[display_columns].copy()
                history_df_sorted = history_df_sorted.sort_values('change_date', ascending=False)
                edited_history = st.data_editor(
                    history_df_sorted,
                    column_config={
                        "price_history_id": st.column_config.TextColumn("이력ID", disabled=True),
                        "product_id": st.column_config.TextColumn("제품ID", disabled=True),
                        "supplier_id": st.column_config.TextColumn("공급업체ID", disabled=True),
                        "old_price_usd": st.column_config.NumberColumn("이전가(USD)", format="$%.2f", disabled=True),
                        "new_price_usd": st.column_config.NumberColumn("신규가(USD)", format="$%.2f"),
                        "old_price_local": st.column_config.NumberColumn("이전가(현지)", disabled=True),
                        "new_price_local": st.column_config.NumberColumn("신규가(현지)"),
                        "exchange_rate_at_change": st.column_config.NumberColumn("당시환율", format="%.2f", disabled=True),
                        "change_reason": st.column_config.TextColumn("변경사유"),
                        "change_date": st.column_config.DateColumn("변경일", disabled=True),
                        "created_by": st.column_config.TextColumn("등록자", disabled=True)
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # 가격 변동 통계
                st.subheader("📊 가격 변동 통계")
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    avg_change = ((history_df['new_price_usd'] - history_df['old_price_usd']) / history_df['old_price_usd'] * 100).mean()
                    st.metric("평균 변동률", f"{avg_change:.1f}%")
                
                with col_stat2:
                    total_changes = len(history_df)
                    st.metric("총 변경 건수", total_changes)
                
                with col_stat3:
                    recent_changes = len(history_df[history_df['change_date'] >= pd.Timestamp(date.today()) - pd.Timedelta(days=30)])
                    st.metric("최근 30일 변경", recent_changes)
            else:
                st.info("선택된 조건에 해당하는 이력이 없습니다.")
        else:
            st.info("가격 변동 이력이 없습니다.")
    
    except FileNotFoundError:
        st.info("가격 변동 이력 데이터가 없습니다.")

def show_supplier_performance(supply_product_manager):
    """공급업체 성과 분석 페이지"""
    st.header("🎯 공급업체 성과 분석")
    
    # 성과 분석 실행
    performance = supply_product_manager.get_supplier_performance_analysis()
    
    # 전체 성과 KPI
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 협정 수", performance['total_agreements'])
    
    with col2:
        st.metric("활성 협정 수", performance['active_agreements'])
    
    with col3:
        st.metric("가격 변경 횟수", performance['price_changes'])
    
    with col4:
        st.metric("가격 안정성", f"{performance['average_price_stability']:.1f}%")
    
    # 공급업체별 상세 성과
    if len(performance['supplier_summary']) > 0:
        st.subheader("📊 공급업체별 성과")
        
        summary_df = performance['supplier_summary']
        
        # 편집 가능한 성과 테이블
        edited_performance = st.data_editor(
            summary_df,
            column_config={
                "supplier_id": st.column_config.TextColumn("공급업체ID"),
                "총_협정수": st.column_config.NumberColumn("총 협정수"),
                "평균_협정가": st.column_config.NumberColumn("평균 협정가", format="$%.2f"),
                "활성_협정수": st.column_config.NumberColumn("활성 협정수"),
                "가격_변동횟수": st.column_config.NumberColumn("가격 변동횟수")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 성과 시각화
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # 협정 수 차트
            fig_agreements = px.bar(
                summary_df, 
                x='supplier_id', 
                y='총_협정수',
                title="공급업체별 협정 수",
                labels={'총_협정수': '협정 수', 'supplier_id': '공급업체 ID'}
            )
            st.plotly_chart(fig_agreements, use_container_width=True)
        
        with col_chart2:
            # 가격 안정성 차트
            summary_df['가격_안정성'] = (summary_df['총_협정수'] - summary_df['가격_변동횟수']) / summary_df['총_협정수'] * 100
            summary_df['가격_안정성'] = summary_df['가격_안정성'].fillna(0)
            
            fig_stability = px.bar(
                summary_df,
                x='supplier_id',
                y='가격_안정성',
                title="공급업체별 가격 안정성",
                labels={'가격_안정성': '안정성 (%)', 'supplier_id': '공급업체 ID'}
            )
            st.plotly_chart(fig_stability, use_container_width=True)
    else:
        st.info("분석할 공급업체 데이터가 없습니다.")

def show_price_alerts(supply_product_manager):
    """가격 변동 알림 페이지"""
    st.header("🚨 가격 변동 알림")
    
    # 임계값 설정
    col1, col2 = st.columns(2)
    
    with col1:
        threshold = st.slider("알림 임계값 (%)", min_value=1, max_value=20, value=5)
    
    with col2:
        if st.button("🔄 알림 업데이트", type="primary"):
            st.rerun()
    
    # 알림 조회
    alerts = supply_product_manager.get_price_variance_alerts(threshold)
    
    if len(alerts) > 0:
        # 긴급도별 분류
        high_alerts = alerts[alerts['alert_level'] == 'HIGH']
        medium_alerts = alerts[alerts['alert_level'] == 'MEDIUM']
        low_alerts = alerts[alerts['alert_level'] == 'LOW']
        
        # 긴급 알림
        if len(high_alerts) > 0:
            st.error("🔴 긴급 알림 (10% 이상 변동)")
            st.dataframe(
                high_alerts[['product_id', 'supplier_id', 'price_impact_percent', 'analysis_date']],
                column_config={
                    "product_id": "제품ID",
                    "supplier_id": "공급업체ID",
                    "price_impact_percent": st.column_config.NumberColumn("영향률", format="%.1f%%"),
                    "analysis_date": "분석일"
                },
                hide_index=True,
                use_container_width=True
            )
        
        # 주의 알림
        if len(medium_alerts) > 0:
            st.warning("🟡 주의 알림 (5-10% 변동)")
            st.dataframe(
                medium_alerts[['product_id', 'supplier_id', 'price_impact_percent', 'analysis_date']],
                column_config={
                    "product_id": "제품ID",
                    "supplier_id": "공급업체ID", 
                    "price_impact_percent": st.column_config.NumberColumn("영향률", format="%.1f%%"),
                    "analysis_date": "분석일"
                },
                hide_index=True,
                use_container_width=True
            )
        
        # 일반 알림
        if len(low_alerts) > 0:
            st.info("🟢 일반 알림 (5% 미만 변동)")
            with st.expander("일반 알림 보기"):
                st.dataframe(
                    low_alerts[['product_id', 'supplier_id', 'price_impact_percent', 'analysis_date']],
                    column_config={
                        "product_id": "제품ID",
                        "supplier_id": "공급업체ID",
                        "price_impact_percent": st.column_config.NumberColumn("영향률", format="%.1f%%"),
                        "analysis_date": "분석일"
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        # 알림 요약 차트
        st.subheader("📊 알림 현황")
        alert_summary = alerts['alert_level'].value_counts()
        
        fig_alerts = px.pie(
            values=alert_summary.values,
            names=alert_summary.index,
            title="알림 레벨별 분포",
            color_discrete_map={'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'green'}
        )
        st.plotly_chart(fig_alerts, use_container_width=True)
    else:
        st.success("현재 설정된 임계값을 초과하는 변동이 없습니다.")
        st.info(f"임계값: {threshold}% 이상의 가격 변동이 감지되면 알림이 표시됩니다.")

def show_mb_bulk_price_setting(supply_product_manager, master_product_manager, supplier_manager, exchange_rate_manager):
    """MB 제품 대량 가격 설정 페이지"""
    st.header("🏭 MB 제품 대량 가격 설정")
    
    st.info("🚀 **MB 제품의 공급가격을 일률적으로 설정할 수 있습니다**\n"
           "- **MB- 접두사** 제품만 대상으로 합니다\n"
           "- 외주 가공 및 특수 제조 제품의 공급가격을 관리합니다\n"
           "- 설정된 가격은 외주 공급가 관리에 자동 등록됩니다\n"
           "- 기본 통화는 CNY(위안)이며 USD 환산가도 제공됩니다")
    
    # MB 제품 목록 가져오기
    try:
        all_products = master_product_manager.get_all_products()
        
        if len(all_products) == 0:
            st.warning("마스터 제품 데이터가 없습니다.")
            return
        
        # MB 제품 필터링 (제품코드가 'MB-'로 시작하는 제품들)
        mb_mask = all_products['product_code'].str.startswith('MB-', na=False)
        mb_products_df = all_products[mb_mask].copy()
        
        if len(mb_products_df) == 0:
            st.warning("MB 제품이 없습니다. 외주 공급가 관리는 MB- 접두사 제품만 대상으로 합니다.")
            return
        
        # MB 서브카테고리별 분류 (제품코드 패턴 기반)
        mb_2p_mask = mb_products_df['product_code'].str.contains('2P', na=False)
        mb_3p_mask = mb_products_df['product_code'].str.contains('3P', na=False)
        mb_hr_mask = mb_products_df['product_code'].str.contains('HR', na=False)
        
        mb_2p_products = mb_products_df[mb_2p_mask]
        mb_3p_products = mb_products_df[mb_3p_mask]
        mb_hr_products = mb_products_df[mb_hr_mask]
        
        st.markdown("---")
        
        # 현재 제품 현황 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 MB 제품", len(mb_products_df))
        with col2:
            st.metric("2P 제품", len(mb_2p_products))
        with col3:
            st.metric("3P 제품", len(mb_3p_products))
        with col4:
            st.metric("HR 제품", len(mb_hr_products))
        
        st.markdown("---")
        
        # 대량 가격 설정 폼
        st.subheader("💰 대량 공급가 설정")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔧 2P 제품", "⚙️ 3P 제품", "🌊 HR 제품", "📋 전체 MB 제품"])
        
        with tab1:
            if len(mb_2p_products) > 0:
                show_mb_type_price_setting(mb_2p_products, "2P", supply_product_manager, supplier_manager, exchange_rate_manager)
            else:
                st.info("2P 타입 MB 제품이 없습니다.")
        
        with tab2:
            if len(mb_3p_products) > 0:
                show_mb_type_price_setting(mb_3p_products, "3P", supply_product_manager, supplier_manager, exchange_rate_manager)
            else:
                st.info("3P 타입 MB 제품이 없습니다.")
        
        with tab3:
            if len(mb_hr_products) > 0:
                show_mb_type_price_setting(mb_hr_products, "HR", supply_product_manager, supplier_manager, exchange_rate_manager)
            else:
                st.info("HR 타입 MB 제품이 없습니다.")
        
        with tab4:
            if len(mb_products_df) > 0:
                show_mb_type_price_setting(mb_products_df, "전체", supply_product_manager, supplier_manager, exchange_rate_manager)
                
    except Exception as e:
        st.error(f"MB 제품 데이터 로딩 중 오류: {str(e)}")

def show_mb_type_price_setting(products_df, product_type, supply_product_manager, supplier_manager, exchange_rate_manager):
    """특정 타입 MB 제품의 가격 설정"""
    
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
    
    # 공급업체 목록 가져오기
    suppliers = supplier_manager.get_all_suppliers()
    if len(suppliers) == 0:
        st.warning("등록된 공급업체가 없습니다. 먼저 공급업체를 등록해주세요.")
        return
    
    # 가격 설정 폼
    with st.form(f"mb_bulk_price_form_{product_type.lower()}"):
        st.subheader(f"💵 {product_type} 제품 일률 공급가 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 공급업체 선택
            supplier_options = [f"{row['company_name']} ({row['supplier_id']})" for _, row in suppliers.iterrows()]
            selected_supplier = st.selectbox(
                "공급업체 선택",
                supplier_options,
                help="공급가를 제공할 공급업체를 선택하세요"
            )
            
            # 변수 초기화
            supplier_id = ""
            supplier_name = ""
            
            if selected_supplier:
                supplier_id = selected_supplier.split("(")[-1].split(")")[0]
                supplier_name = selected_supplier.split(" (")[0]
            
            # 공급가 설정 (CNY 기준)
            supply_price_cny = st.number_input(
                "공급가 (CNY)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                help=f"모든 {product_type} 제품에 적용할 공급가 (위안)"
            )
        
        with col2:
            # 변수 초기화
            supply_price_usd = 0.0
            
            # 환율 정보 표시
            try:
                latest_rates = exchange_rate_manager.get_latest_rates()
                cny_rate = latest_rates[latest_rates['currency_code'] == 'CNY']['rate'].iloc[0] if len(latest_rates[latest_rates['currency_code'] == 'CNY']) > 0 else 0.14
                usd_rate = 1.0  # USD는 기준통화
                
                if supply_price_cny > 0:
                    supply_price_usd = supply_price_cny * cny_rate
                    st.info(f"**공급가 환산**\n"
                           f"USD: ${supply_price_usd:.2f}\n"
                           f"CNY: ¥{supply_price_cny:.2f}")
                    
                    st.info(f"**환율 정보**\n"
                           f"CNY/USD: {cny_rate:.4f}")
                        
            except Exception as e:
                st.warning("환율 정보를 가져올 수 없습니다.")
                supply_price_usd = supply_price_cny * 0.14  # 기본 환율 사용
        
        # 적용 설정
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            effective_date = st.date_input(
                "적용 시작일",
                value=datetime.now().date(),
                help="공급가 적용 시작일"
            )
        
        with col2:
            notes = st.text_input(
                "비고",
                value=f"{product_type} 제품 대량 공급가 설정",
                help="가격 설정에 대한 추가 설명"
            )
        
        # 적용 버튼
        submitted = st.form_submit_button(
            f"🚀 {product_type} 제품 공급가 일률 적용 ({len(products_df)}개)",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if supply_price_cny <= 0:
                st.error("공급가를 0보다 큰 값으로 입력해주세요.")
                return
            
            if not selected_supplier:
                st.error("공급업체를 선택해주세요.")
                return
            
            # 대량 공급가 적용 실행
            apply_mb_bulk_pricing(products_df, product_type, supplier_id, supplier_name, 
                                supply_price_cny, supply_price_usd, effective_date, notes, 
                                supply_product_manager)

def apply_mb_bulk_pricing(products_df, product_type, supplier_id, supplier_name, 
                         supply_price_cny, supply_price_usd, effective_date, notes, 
                         supply_product_manager):
    """MB 제품 대량 공급가 적용 실행"""
    
    success_count = 0
    error_count = 0
    
    # 진행 상황 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_products = len(products_df)
    
    for index, (_, product) in enumerate(products_df.iterrows()):
        try:
            product_code = product['product_code']
            
            # 진행 상황 업데이트
            progress = (index + 1) / total_products
            progress_bar.progress(progress)
            status_text.text(f"처리 중: {product_code} ({index + 1}/{total_products})")
            
            # 공급가 데이터 준비
            supply_data = {
                'product_code': product_code,
                'supplier_id': supplier_id,
                'supplier_name': supplier_name,
                'supply_price_cny': supply_price_cny,
                'supply_price_usd': supply_price_usd,
                'effective_date': effective_date,
                'created_by': st.session_state.get('user_id', 'system'),
                'notes': notes,
                'is_current': 'yes'
            }
            
            # 공급 제품 매니저에 공급가 추가
            result = supply_product_manager.add_supplier_agreement(supply_data)
            
            if result:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            product_code = product.get('product_code', '알 수 없음')
            st.error(f"{product_code} 처리 중 오류: {str(e)}")
    
    # 완료 메시지
    progress_bar.progress(1.0)
    status_text.text("완료!")
    
    if success_count > 0:
        from notification_helper import NotificationHelper
        NotificationHelper.show_success(f"{product_type} MB 제품 공급가 설정: {success_count}개 제품의 공급가가 성공적으로 설정되었습니다.")
        
        st.success(f"✅ **완료!**\n"
                  f"- 성공: {success_count}개\n"
                  f"- 실패: {error_count}개\n"
                  f"- 공급업체: {supplier_name}\n"
                  f"- 공급가: ¥{supply_price_cny:.2f} CNY (${supply_price_usd:.2f} USD)")
    
        if error_count > 0:
            st.warning(f"⚠️ {error_count}개 제품 처리 중 오류가 발생했습니다.")

def show_mb_product_registration(master_product_manager, supply_product_manager, supplier_manager):
    """MB 제품 등록 페이지 - 이미지에 맞게 수정"""
    st.subheader("🔧 Mold Base 제품 등록")
    st.info("Mold Base 제품을 등록합니다. (MB-2P-SS400-20 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # MB 타입 선택 - HRC와 동일한 계층형 구조
        from product_category_config_manager import ProductCategoryConfigManager
        config_manager = ProductCategoryConfigManager()
        
        # MB Type 선택
        mb_types = config_manager.get_mb_types()
        selected_mb_type = st.selectbox(
            "MB Type",
            [""] + mb_types,
            index=0,
            help="시스템 설정에서 관리되는 MB 타입 (HRC와 동일한 방식)",
            key="mb_type"
        )
        
        # Sub Category 선택 (MB Type에 따라 동적 로딩)
        if selected_mb_type:
            mb_subcategories = config_manager.get_mb_subcategories(selected_mb_type)
            selected_subcategory = st.selectbox(
                "Sub Category",
                [""] + mb_subcategories,
                index=0,
                key="mb_subcategory",
                help="선택된 MB Type의 서브 카테고리"
            )
        else:
            selected_subcategory = st.selectbox(
                "Sub Category", 
                [""], 
                disabled=True, 
                key="mb_subcategory_disabled",
                help="먼저 MB Type을 선택해주세요"
            )
        
        # 재질 선택 - 제품 분류관리에서 관리되는 재질 사용
        mb_materials = config_manager.get_hr_components_list('mb_material')
        selected_material = st.selectbox(
            "재질",
            [""] + mb_materials,
            index=0,
            key="mb_material",
            help="법인장 메뉴 → 제품 분류관리 → MB 재질 관리에서 등록된 재질"
        )
        
        # MB 전체 크기 (X, Y, Z를 50 단위로)
        st.markdown("**MB 전체 크기 (50 단위)**")
        col_x, col_y, col_z = st.columns(3)
        
        with col_x:
            size_x = st.number_input("X (mm)", min_value=50, max_value=2000, value=400, step=50, key="mb_size_x")
        with col_y:
            size_y = st.number_input("Y (mm)", min_value=50, max_value=2000, value=300, step=50, key="mb_size_y")
        with col_z:
            size_z = st.number_input("Z (mm)", min_value=50, max_value=500, value=200, step=50, key="mb_size_z")
        
        # 크기 정보 및 예상 코드 표시
        size_code = f"{size_x}x{size_y}x{size_z}"
        
        # 계층 구조 요소들로 제품 코드 생성 (HRC와 동일한 방식)
        mb_components = []
        if selected_mb_type:
            mb_components.append(selected_mb_type)
        if selected_subcategory:
            mb_components.append(selected_subcategory)
        if selected_material:
            mb_components.append(selected_material)
        if size_x and size_y and size_z:
            mb_components.append(f"{size_x}x{size_y}x{size_z}")
        
        if len(mb_components) >= 3:  # MB Type, Sub Category, Material은 필수
            preview_code = f"MB-{'-'.join(mb_components)}"
            st.success(f"📦 **예상 제품 코드**: `{preview_code}`")
            st.info(f"📏 **전체 크기**: {size_code}mm")
        else:
            st.info("MB Type, Sub Category, 재질, 크기를 모두 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        if selected_mb_type and selected_subcategory and selected_material and size_x and size_y and size_z:
            suggested_korean = f"몰드베이스 {selected_mb_type} {selected_subcategory} {selected_material} {size_x}x{size_y}x{size_z}"
            suggested_english = f"Mold Base {selected_mb_type} {selected_subcategory} {selected_material} {size_x}x{size_y}x{size_z}"
            suggested_vietnamese = f"Mold Base {selected_mb_type} {selected_subcategory} {selected_material} {size_x}x{size_y}x{size_z}"
        
        korean_name = st.text_input(
            "한국어 제품명 *",
            value=suggested_korean,
            key="mb_korean",
            placeholder="예: 몰드베이스 2P SS400 20"
        )
        english_name = st.text_input(
            "영어 제품명 *",
            value=suggested_english,
            key="mb_english",
            placeholder="예: Mold Base 2P SS400 20"
        )
        vietnamese_name = st.text_input(
            "베트남어 제품명",
            value=suggested_vietnamese,
            key="mb_vietnamese",
            placeholder="예: Mold Base 2P SS400 20"
        )
    
    # 공급업체 정보
    st.markdown("### 🏭 공급업체 정보")
    col3, col4 = st.columns(2)
    
    with col3:
        # 공급업체 관리에서 등록된 업체 리스트 가져오기
        try:
            suppliers = supplier_manager.get_all_suppliers()
            if isinstance(suppliers, pd.DataFrame) and len(suppliers) > 0:
                supplier_options = [""]
                supplier_names = {}
                for _, row in suppliers.iterrows():
                    supplier_id = row['supplier_id']
                    company_name = row['company_name']
                    status = row.get('status', '활성')
                    
                    # 활성 상태인 공급업체만 표시
                    if status == '활성':
                        option_text = f"{supplier_id} - {company_name}"
                        supplier_options.append(option_text)
                        supplier_names[option_text] = supplier_id
                
                if len(supplier_options) > 1:  # 빈 옵션 제외하고 1개 이상
                    selected_supplier_option = st.selectbox(
                        "공급업체 *",
                        supplier_options,
                        help="공급업체 관리에서 등록된 업체 목록 (활성 업체만 표시)"
                    )
                    
                    selected_supplier_id = supplier_names.get(selected_supplier_option, "")
                else:
                    st.warning("활성 상태인 공급업체가 없습니다. 공급업체 관리에서 먼저 업체를 등록하고 활성화해주세요.")
                    selected_supplier_option = ""
                    selected_supplier_id = ""
            else:
                st.warning("등록된 공급업체가 없습니다. 공급업체 관리에서 먼저 업체를 등록해주세요.")
                selected_supplier_option = ""
                selected_supplier_id = ""
        except Exception as e:
            st.error(f"공급업체 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
            st.info("공급업체 관리 메뉴에서 공급업체를 먼저 등록해주세요.")
            selected_supplier_option = ""
            selected_supplier_id = ""
        
        # 예상 리드타임을 영업일 기준으로 변경
        lead_time_days = st.number_input(
            "예상 리드타임 (영업일)",
            min_value=1,
            max_value=365,
            value=8,
            step=1,
            help="영업일 기준으로 입력하세요"
        )
    
    with col4:
        # 활성 상태만 남기고 보증기간 제거
        is_active = st.checkbox("활성 상태", value=True, help="체크 해제 시 비활성 제품으로 등록됩니다")
    
    # 공급가 정보 입력
    st.markdown("### 💰 공급가 정보")
    col5, col6, col7 = st.columns(3)
    
    with col5:
        supply_price_cny = st.number_input(
            "공급가 (CNY) *",
            min_value=0.0,
            value=0.0,
            step=0.01,
            help="중국 위안화 기준 공급가"
        )
    
    with col6:
        usd_rate = st.number_input(
            "USD 환율 (CNY/USD) *",
            min_value=0.0,
            value=7.2,
            step=0.01,
            help="수동 입력: 1 USD = ? CNY"
        )
    
    with col7:
        vnd_rate = st.number_input(
            "VND 환율 (USD/VND)",
            min_value=0.0,
            value=24000.0,
            step=1.0,
            help="수동 입력: 1 USD = ? VND"
        )
    
    # 환율 계산 표시
    if supply_price_cny > 0 and usd_rate > 0:
        supply_price_usd = supply_price_cny / usd_rate
        supply_price_vnd = supply_price_usd * vnd_rate if vnd_rate > 0 else 0
        
        st.markdown("#### 💱 환율 계산 결과")
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        with col_calc1:
            st.info(f"**CNY**: ¥{supply_price_cny:,.2f}")
        with col_calc2:
            st.info(f"**USD**: ${supply_price_usd:,.2f}")
        with col_calc3:
            st.info(f"**VND**: ₫{supply_price_vnd:,.0f}")
    
    # 등록 버튼
    if st.button("🚀 MB 제품 등록", type="primary", key="register_mb_btn"):
        # 변수 초기화
        mb_type = st.session_state.get('mb_type', '')
        material = st.session_state.get('material', '')
        korean_name = st.session_state.get('korean_name', '')
        english_name = st.session_state.get('english_name', '')
        selected_supplier_id = st.session_state.get('selected_supplier_id', '')
        
        if mb_type and material and korean_name and english_name and selected_supplier_id and supply_price_cny > 0 and usd_rate > 0:
            try:
                # 기본값 설정
                size_x = st.session_state.get('size_x', 0)
                size_y = st.session_state.get('size_y', 0) 
                size_z = st.session_state.get('size_z', 0)
                size_code = f"{size_x}x{size_y}x{size_z}"
                vietnamese_name = st.session_state.get('vietnamese_name', '')
                selected_supplier_option = st.session_state.get('selected_supplier_option', '')
                lead_time_days = st.session_state.get('lead_time_days', 7)
                is_active = st.session_state.get('is_active', True)
                
                # 제품 코드 생성 (새 형식: MB-HR-S50C-400-300-200-공급업체ID)
                generated_code = f"MB-{mb_type}-{material}-{size_x}-{size_y}-{size_z}-{selected_supplier_id}"
                
                # 환율 계산
                supply_price_usd = supply_price_cny / usd_rate
                supply_price_vnd = supply_price_usd * vnd_rate if vnd_rate > 0 else 0
                
                product_data = {
                    'product_code': generated_code,
                    'main_category': 'MB',
                    'sub_category': mb_type,
                    'material': material,
                    'size_x': size_x,
                    'size_y': size_y,
                    'size_z': size_z,
                    'size_code': size_code,
                    'product_name_korean': korean_name,
                    'product_name_english': english_name,
                    'product_name_vietnamese': vietnamese_name or english_name,
                    'supplier_id': selected_supplier_id,
                    'supplier_info': selected_supplier_option,
                    'supply_price_cny': supply_price_cny,
                    'supply_price_usd': supply_price_usd,
                    'supply_price_vnd': supply_price_vnd,
                    'usd_rate': usd_rate,
                    'vnd_rate': vnd_rate,
                    'lead_time_days': lead_time_days,
                    'is_active': is_active,
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                success, message = master_product_manager.add_product(product_data)
                
                if success:
                    st.success(f"✅ MB 제품이 등록되었습니다: {generated_code}")
                    st.info(f"📦 제품 정보: {korean_name}")
                    st.info(f"🏭 공급업체: {selected_supplier_option}")
                    st.info(f"💰 공급가: ¥{supply_price_cny:,.2f} / ${supply_price_usd:,.2f} / ₫{supply_price_vnd:,.0f}")
                    st.info(f"📅 예상 리드타임: {lead_time_days}영업일")
                    
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {message}")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
        else:
            missing_fields = []
            if not mb_type: missing_fields.append("MB 타입")
            if not material: missing_fields.append("재질")
            if not korean_name: missing_fields.append("제품명(한국어)")
            if not english_name: missing_fields.append("제품명(영어)")
            if not selected_supplier_id: missing_fields.append("공급업체")
            if supply_price_cny <= 0: missing_fields.append("공급가(CNY)")
            if usd_rate <= 0: missing_fields.append("USD 환율")
            
            st.error(f"필수 필드를 입력해주세요: {', '.join(missing_fields)}")
    
    # 하단 네비게이션 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📦 제품 관리로 이동", use_container_width=True, type="secondary"):
            st.session_state['selected_system'] = 'product_management'
            st.rerun()

def show_supply_product_edit_management(supply_product_manager):
    """공급 제품 정보 수정 관리"""
    st.subheader("📝 공급 제품 정보 수정")
    
    try:
        # 수정할 제품 선택
        all_products = supply_product_manager.get_all_products()
        
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
                with st.form("supply_product_edit_form"):
                    st.subheader("공급 제품 정보 수정")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_product_name = st.text_input(
                            "제품명", 
                            value=selected_product.get('product_name', ''),
                            placeholder="제품명을 입력하세요"
                        )
                        new_category = st.selectbox(
                            "카테고리",
                            ['MB', 'SP', 'GENERAL'],
                            index=['MB', 'SP', 'GENERAL'].index(selected_product.get('category', 'MB'))
                        )
                        new_supplier = st.text_input(
                            "공급업체",
                            value=selected_product.get('supplier', ''),
                            placeholder="공급업체명 입력"
                        )
                    
                    with col2:
                        new_price = st.number_input(
                            "공급가격 (CNY)",
                            value=float(selected_product.get('price', 0)),
                            min_value=0.0,
                            step=0.01
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
                    
                    submitted = st.form_submit_button("💾 공급 제품 정보 업데이트", type="primary")
                    
                    if submitted:
                        # 업데이트 데이터 준비
                        update_data = {
                            'product_name': new_product_name,
                            'category': new_category,
                            'supplier': new_supplier,
                            'price': new_price,
                            'status': new_status,
                            'description': new_description
                        }
                        
                        # 제품 정보 업데이트
                        success = supply_product_manager.update_product(
                            selected_product.get('product_id', selected_product.get('product_code')), 
                            update_data
                        )
                        
                        if success:
                            st.success("✅ 공급 제품 정보가 성공적으로 업데이트되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 공급 제품 정보 업데이트에 실패했습니다.")
        else:
            st.info("등록된 공급 제품이 없습니다.")
            
    except Exception as e:
        st.error(f"공급 제품 수정 중 오류: {str(e)}")

def show_supply_product_delete_management(supply_product_manager):
    """공급 제품 삭제 관리"""
    st.subheader("🗑️ 공급 제품 삭제")
    st.warning("⚠️ 제품을 삭제하면 관련된 모든 공급업체 정보와 가격 정보도 함께 삭제됩니다. 신중하게 선택하세요.")
    
    try:
        # 삭제할 제품 선택
        all_products = supply_product_manager.get_all_products()
        
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
                    st.write(f"- 공급업체: {selected_product.get('supplier', 'N/A')}")
                    st.write(f"- 상태: {selected_product.get('status', 'N/A')}")
                
                with col2:
                    confirm_text = st.text_input(
                        "삭제를 확인하려면 '삭제' 를 입력하세요:",
                        placeholder="삭제"
                    )
                    
                    if confirm_text == "삭제":
                        if st.button("🗑️ 공급 제품 완전 삭제", type="primary"):
                            success = supply_product_manager.delete_product(
                                selected_product.get('product_id', selected_product.get('product_code'))
                            )
                            
                            if success:
                                st.success("✅ 공급 제품이 성공적으로 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 공급 제품 삭제에 실패했습니다.")
                    else:
                        st.info("삭제를 확인하려면 위에 '삭제'를 정확히 입력하세요.")
        else:
            st.info("등록된 공급 제품이 없습니다.")
            
    except Exception as e:
        st.error(f"공급 제품 삭제 중 오류: {str(e)}")

