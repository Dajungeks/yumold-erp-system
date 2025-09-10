"""
완성품 관리 페이지 - 완성된 제품 코드 전용 관리
견적서, 발주서, 출고 확인서에 사용되는 완성품 정보 관리
"""

import streamlit as st
import pandas as pd
from datetime import datetime

def show_finished_product_page(finished_product_manager, user_permissions, get_text):
    """완성품 관리 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'finished_product_management', get_text)
    
    st.title("✅ 완성품 관리")
    st.markdown("견적서, 발주서, 출고 확인서에 사용되는 완성품 정보를 관리합니다.")
    st.markdown("---")
    
    # 완성품 매니저가 없는 경우 처리
    if not finished_product_manager:
        st.error("완성품 매니저가 초기화되지 않았습니다.")
        return
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 완성품 현황", 
        "➕ 완성품 등록", 
        "💰 가격 관리",
        "🔍 완성품 조회"
    ])
    
    with tab1:
        show_finished_product_overview(finished_product_manager, get_text)
    
    with tab2:
        show_finished_product_registration(finished_product_manager, get_text)
    
    with tab3:
        show_finished_product_price_management(finished_product_manager, get_text)
    
    with tab4:
        show_finished_product_search(finished_product_manager, get_text)

def show_finished_product_overview(finished_product_manager, get_text):
    """완성품 현황 개요를 표시합니다."""
    st.header("📊 완성품 현황")
    
    # 완성품 목록 조회
    products_df = finished_product_manager.get_all_finished_products()
    
    if products_df.empty:
        st.info("📢 등록된 완성품이 없습니다. '완성품 등록' 탭에서 제품을 추가해주세요.")
        return
    
    # 통계 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 완성품", len(products_df))
    
    with col2:
        active_count = len(products_df[products_df['status'] == 'active'])
        st.metric("활성 제품", active_count)
    
    with col3:
        price_set_count = len(products_df.dropna(subset=['selling_price_vnd']))
        st.metric("가격 설정 완료", price_set_count)
    
    with col4:
        categories = products_df['category'].dropna().nunique()
        st.metric("카테고리 수", categories)
    
    st.markdown("---")
    
    # 완성품 목록 표시
    st.subheader("📋 완성품 목록")
    
    # 필요한 컬럼만 선택
    display_columns = ['product_code', 'product_name_ko', 'product_name_en', 
                      'category', 'selling_price_vnd', 'supplier_price_vnd', 'status']
    
    display_df = products_df[display_columns].copy()
    display_df.columns = ['제품코드', '제품명(한국어)', '제품명(영어)', 
                         '카테고리', '판매가(VND)', '공급가(VND)', '상태']
    
    # 가격 포맷팅
    for col in ['판매가(VND)', '공급가(VND)']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "-")
    
    st.dataframe(display_df, use_container_width=True)

def show_finished_product_registration(finished_product_manager, get_text):
    """완성품 등록 폼을 표시합니다."""
    st.header("➕ 완성품 등록")
    
    with st.form("finished_product_form"):
        st.subheader("📝 기본 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_code = st.text_input("제품 코드 *", placeholder="HR-OP-CP-CC-10-00")
            product_name_ko = st.text_input("제품명 (한국어) *", placeholder="제품명을 입력하세요")
            product_name_en = st.text_input("제품명 (영어)", placeholder="Product Name")
            category = st.selectbox("카테고리", [
                "", "Controller", "Sensor", "Heater", "Valve", "Pump", "Motor", "기타"
            ])
            
        with col2:
            product_name_vi = st.text_input("제품명 (베트남어)", placeholder="Tên sản phẩm")
            unit = st.selectbox("단위", ["EA", "SET", "KG", "M", "L", "기타"], index=0)
            brand = st.text_input("브랜드", placeholder="제조사 브랜드")
            model = st.text_input("모델", placeholder="제품 모델")
        
        st.subheader("💰 가격 정보")
        
        col3, col4 = st.columns(2)
        
        with col3:
            supplier_price_vnd = st.number_input("공급가 (VND)", min_value=0.0, value=0.0, step=1000.0)
            selling_price_vnd = st.number_input("판매가 (VND)", min_value=0.0, value=0.0, step=1000.0)
            
        with col4:
            supplier_price_usd = st.number_input("공급가 (USD)", min_value=0.0, value=0.0, step=1.0)
            selling_price_usd = st.number_input("판매가 (USD)", min_value=0.0, value=0.0, step=1.0)
        
        st.subheader("📋 추가 정보")
        
        col5, col6 = st.columns(2)
        
        with col5:
            description = st.text_area("제품 설명", placeholder="제품에 대한 상세 설명")
            origin_country = st.text_input("원산지", placeholder="Korea, China, Japan 등")
            
        with col6:
            specifications = st.text_area("제품 사양", placeholder="기술적 사양 및 특징")
            manufacturer = st.text_input("제조사", placeholder="제조회사명")
        
        submitted = st.form_submit_button("✅ 완성품 등록", use_container_width=True)
        
        if submitted:
            # 필수 필드 검증
            if not product_code or not product_name_ko:
                st.error("제품 코드와 제품명(한국어)은 필수 입력 항목입니다.")
                return
            
            # 완성품 등록
            success, result = finished_product_manager.add_finished_product(
                product_code=product_code,
                product_name_ko=product_name_ko,
                product_name_en=product_name_en,
                product_name_vi=product_name_vi,
                description=description,
                specifications=specifications,
                unit=unit,
                category=category,
                brand=brand,
                model=model,
                origin_country=origin_country,
                manufacturer=manufacturer
            )
            
            if success:
                finished_product_id = result
                st.success(f"✅ 완성품이 성공적으로 등록되었습니다! (ID: {finished_product_id})")
                
                # 가격 정보가 입력된 경우 가격도 등록
                if any([supplier_price_vnd, selling_price_vnd, supplier_price_usd, selling_price_usd]):
                    price_success, price_result = finished_product_manager.add_product_price(
                        finished_product_id=finished_product_id,
                        supplier_price_vnd=supplier_price_vnd,
                        supplier_price_usd=supplier_price_usd,
                        selling_price_vnd=selling_price_vnd,
                        selling_price_usd=selling_price_usd,
                        currency='VND' if supplier_price_vnd > 0 else 'USD'
                    )
                    
                    if price_success:
                        st.success("💰 가격 정보도 성공적으로 등록되었습니다!")
                    else:
                        st.warning(f"⚠️ 가격 정보 등록 실패: {price_result}")
                
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ 완성품 등록 실패: {result}")

def show_finished_product_price_management(finished_product_manager, get_text):
    """완성품 가격 관리를 표시합니다."""
    st.header("💰 가격 관리")
    
    # 완성품 목록 조회
    products_df = finished_product_manager.get_all_finished_products()
    
    if products_df.empty:
        st.info("등록된 완성품이 없습니다.")
        return
    
    # 제품 선택
    product_options = {row['product_code']: row['finished_product_id'] 
                      for _, row in products_df.iterrows()}
    
    selected_code = st.selectbox("가격을 관리할 제품을 선택하세요", 
                                list(product_options.keys()))
    
    if selected_code:
        selected_id = product_options[selected_code]
        product_info = products_df[products_df['product_code'] == selected_code].iloc[0]
        
        st.subheader(f"📦 {selected_code} - {product_info['product_name_ko']}")
        
        # 현재 가격 정보 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("현재 공급가 (VND)", 
                     f"{product_info.get('supplier_price_vnd', 0):,.0f}" if pd.notna(product_info.get('supplier_price_vnd')) else "미설정")
            st.metric("현재 판매가 (VND)", 
                     f"{product_info.get('selling_price_vnd', 0):,.0f}" if pd.notna(product_info.get('selling_price_vnd')) else "미설정")
        
        with col2:
            st.metric("현재 공급가 (USD)", 
                     f"{product_info.get('supplier_price_usd', 0):,.2f}" if pd.notna(product_info.get('supplier_price_usd')) else "미설정")
            st.metric("현재 판매가 (USD)", 
                     f"{product_info.get('selling_price_usd', 0):,.2f}" if pd.notna(product_info.get('selling_price_usd')) else "미설정")
        
        st.markdown("---")
        
        # 새 가격 설정
        with st.form("price_update_form"):
            st.subheader("💰 새 가격 설정")
            
            col3, col4 = st.columns(2)
            
            with col3:
                new_supplier_vnd = st.number_input("새 공급가 (VND)", 
                                                  min_value=0.0, 
                                                  value=float(product_info.get('supplier_price_vnd', 0)) if pd.notna(product_info.get('supplier_price_vnd')) else 0.0,
                                                  step=1000.0)
                new_selling_vnd = st.number_input("새 판매가 (VND)", 
                                                 min_value=0.0, 
                                                 value=float(product_info.get('selling_price_vnd', 0)) if pd.notna(product_info.get('selling_price_vnd')) else 0.0,
                                                 step=1000.0)
            
            with col4:
                new_supplier_usd = st.number_input("새 공급가 (USD)", 
                                                  min_value=0.0, 
                                                  value=float(product_info.get('supplier_price_usd', 0)) if pd.notna(product_info.get('supplier_price_usd')) else 0.0,
                                                  step=1.0)
                new_selling_usd = st.number_input("새 판매가 (USD)", 
                                                 min_value=0.0, 
                                                 value=float(product_info.get('selling_price_usd', 0)) if pd.notna(product_info.get('selling_price_usd')) else 0.0,
                                                 step=1.0)
            
            margin_rate = st.number_input("마진율 (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
            price_notes = st.text_area("가격 설정 메모", placeholder="가격 변경 사유나 특이사항을 입력하세요")
            
            price_submitted = st.form_submit_button("💰 가격 업데이트", use_container_width=True)
            
            if price_submitted:
                success, result = finished_product_manager.add_product_price(
                    finished_product_id=selected_id,
                    supplier_price_vnd=new_supplier_vnd,
                    supplier_price_usd=new_supplier_usd,
                    selling_price_vnd=new_selling_vnd,
                    selling_price_usd=new_selling_usd,
                    margin_rate=margin_rate,
                    currency='VND',
                    notes=price_notes
                )
                
                if success:
                    st.success("✅ 가격이 성공적으로 업데이트되었습니다!")
                    st.rerun()
                else:
                    st.error(f"❌ 가격 업데이트 실패: {result}")

def show_finished_product_search(finished_product_manager, get_text):
    """완성품 검색 및 조회를 표시합니다."""
    st.header("🔍 완성품 조회")
    
    # 검색 필터
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_code = st.text_input("제품 코드 검색", placeholder="HR-OP-CP")
    
    with col2:
        search_name = st.text_input("제품명 검색", placeholder="제품명")
    
    with col3:
        search_category = st.selectbox("카테고리 필터", 
                                     ["전체", "Controller", "Sensor", "Heater", "Valve", "Pump", "Motor", "기타"])
    
    # 완성품 목록 조회 및 필터링
    products_df = finished_product_manager.get_all_finished_products()
    
    if not products_df.empty:
        # 필터 적용
        filtered_df = products_df.copy()
        
        if search_code:
            filtered_df = filtered_df[filtered_df['product_code'].str.contains(search_code, case=False, na=False)]
        
        if search_name:
            name_mask = (
                filtered_df['product_name_ko'].str.contains(search_name, case=False, na=False) |
                filtered_df['product_name_en'].str.contains(search_name, case=False, na=False) |
                filtered_df['product_name_vi'].str.contains(search_name, case=False, na=False)
            )
            filtered_df = filtered_df[name_mask]
        
        if search_category != "전체":
            filtered_df = filtered_df[filtered_df['category'] == search_category]
        
        st.markdown("---")
        
        if not filtered_df.empty:
            st.subheader(f"📋 검색 결과 ({len(filtered_df)}개)")
            
            # 상세 정보 표시
            for _, product in filtered_df.iterrows():
                with st.expander(f"📦 {product['product_code']} - {product['product_name_ko']}", expanded=False):
                    
                    info_col1, info_col2 = st.columns(2)
                    
                    with info_col1:
                        st.markdown(f"**제품 코드:** {product['product_code']}")
                        st.markdown(f"**제품명 (한국어):** {product['product_name_ko']}")
                        st.markdown(f"**제품명 (영어):** {product.get('product_name_en', '-')}")
                        st.markdown(f"**제품명 (베트남어):** {product.get('product_name_vi', '-')}")
                        st.markdown(f"**카테고리:** {product.get('category', '-')}")
                        st.markdown(f"**브랜드:** {product.get('brand', '-')}")
                    
                    with info_col2:
                        selling_vnd = product.get('selling_price_vnd', 0)
                        supplier_vnd = product.get('supplier_price_vnd', 0)
                        selling_usd = product.get('selling_price_usd', 0)
                        supplier_usd = product.get('supplier_price_usd', 0)
                        
                        st.markdown(f"**판매가 (VND):** {selling_vnd:,.0f}" if pd.notna(selling_vnd) and selling_vnd > 0 else "**판매가 (VND):** 미설정")
                        st.markdown(f"**공급가 (VND):** {supplier_vnd:,.0f}" if pd.notna(supplier_vnd) and supplier_vnd > 0 else "**공급가 (VND):** 미설정")
                        st.markdown(f"**판매가 (USD):** {selling_usd:,.2f}" if pd.notna(selling_usd) and selling_usd > 0 else "**판매가 (USD):** 미설정")
                        st.markdown(f"**공급가 (USD):** {supplier_usd:,.2f}" if pd.notna(supplier_usd) and supplier_usd > 0 else "**공급가 (USD):** 미설정")
                        st.markdown(f"**단위:** {product.get('unit', 'EA')}")
                        st.markdown(f"**상태:** {product.get('status', 'active')}")
                    
                    if product.get('description'):
                        st.markdown(f"**설명:** {product['description']}")
                    
                    if product.get('specifications'):
                        st.markdown(f"**사양:** {product['specifications']}")
        else:
            st.info("🔍 검색 조건에 맞는 완성품이 없습니다.")
    else:
        st.info("📢 등록된 완성품이 없습니다.")