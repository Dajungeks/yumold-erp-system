import streamlit as st
from notification_helper import NotificationHelper

def show_product_edit(master_product_manager):
    """제품 편집 기능"""
    st.subheader("✏️ 제품 편집")
    
    # 제품 검색 및 선택
    st.markdown("### 1️⃣ 편집할 제품 선택")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("제품 검색", placeholder="제품 코드 또는 제품명 입력")
    
    with col2:
        category_filter = st.selectbox("카테고리 필터", ["전체", "HR", "HRC", "MB", "SERVICE", "SPARE"])
        category = None if category_filter == "전체" else category_filter
    
    # 제품 검색
    if search_term or category:
        products = master_product_manager.search_products(search_term, category)
        
        if products:
            # 제품 선택
            product_options = [f"{p['product_code']} - {p['product_name_korean']}" for p in products]
            selected_option = st.selectbox("편집할 제품 선택", product_options)
            
            if selected_option and st.button("편집 시작", type="primary"):
                # 선택된 제품 코드 추출
                selected_code = selected_option.split(" - ")[0]
                product = master_product_manager.get_product_by_code(selected_code)
                
                if product:
                    st.session_state.editing_product = product
                    st.rerun()
        else:
            st.info("검색 조건에 맞는 제품이 없습니다.")
    
    # 제품 편집 폼
    if 'editing_product' in st.session_state:
        product = st.session_state.editing_product
        st.markdown("---")
        st.markdown("### 2️⃣ 제품 정보 편집")
        
        with st.form("product_edit_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📋 기본 정보")
                product_code = st.text_input("제품 코드", value=product.get('product_code', ''), disabled=True)
                product_name_korean = st.text_input("한국어 제품명", value=product.get('product_name_korean', ''))
                product_name_english = st.text_input("영어 제품명", value=product.get('product_name_english', ''))
                product_name_vietnamese = st.text_input("베트남어 제품명", value=product.get('product_name_vietnamese', ''))
                
            with col2:
                st.markdown("#### 🏷️ 분류 정보")
                main_category = st.selectbox("메인 카테고리", ["HR", "HRC", "MB", "SERVICE", "SPARE"], 
                                           index=["HR", "HRC", "MB", "SERVICE", "SPARE"].index(product.get('main_category', 'HR')))
                sub_category = st.text_input("서브 카테고리", value=product.get('sub_category', ''))
                specifications = st.text_input("기술 사양", value=product.get('specifications', ''))
                unit_of_measure = st.selectbox("단위", ["EA", "SET", "PC", "KG", "M"], 
                                             index=["EA", "SET", "PC", "KG", "M"].index(product.get('unit_of_measure', 'EA')) if product.get('unit_of_measure') in ["EA", "SET", "PC", "KG", "M"] else 0)
            
            # 제출 버튼
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                submit_edit = st.form_submit_button("💾 수정 저장", type="primary")
            with col2:
                cancel_edit = st.form_submit_button("❌ 취소", type="secondary")
            
            if submit_edit:
                # 수정 데이터 구성
                updated_data = {
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'product_name_vietnamese': product_name_vietnamese,
                    'main_category': main_category,
                    'sub_category': sub_category,
                    'specifications': specifications,
                    'unit_of_measure': unit_of_measure
                }
                
                # 제품 수정
                result, message = master_product_manager.update_product(product_code, updated_data)
                if result:
                    NotificationHelper.show_operation_success("수정", product_code or "제품")
                    del st.session_state.editing_product
                    st.rerun()
                else:
                    NotificationHelper.show_error(message)
            
            if cancel_edit:
                del st.session_state.editing_product
                st.rerun()


def show_product_delete(master_product_manager):
    """제품 삭제 기능"""
    st.subheader("🗑️ 제품 삭제")
    
    # 삭제 방식 선택
    delete_type = st.radio(
        "삭제 방식 선택",
        options=["소프트 삭제 (비활성화)", "완전 삭제 (데이터 제거)"],
        key="delete_type_option",
        help="소프트 삭제는 제품을 비활성화하여 목록에서 숨기고, 완전 삭제는 데이터베이스에서 영구 제거합니다."
    )
    
    if delete_type == "완전 삭제 (데이터 제거)":
        st.error("⚠️ 완전 삭제 시 데이터가 영구적으로 제거됩니다. 백업이 자동으로 생성됩니다.")
    else:
        st.info("ℹ️ 소프트 삭제 시 제품은 비활성화되어 목록에서 숨겨집니다.")
    
    # 제품 검색 및 선택
    st.markdown("### 1️⃣ 삭제할 제품 선택")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("제품 검색", placeholder="제품 코드 또는 제품명 입력", key="delete_search")
    
    with col2:
        category_filter = st.selectbox("카테고리 필터", ["전체", "HR", "HRC", "MB", "SERVICE", "SPARE"], key="delete_category")
        category = None if category_filter == "전체" else category_filter
    
    # 제품 검색
    if search_term or category:
        # 삭제 방식에 따라 검색 상태 결정
        search_status = "active" if delete_type == "소프트 삭제 (비활성화)" else "all"
        products = master_product_manager.search_products(search_term, category, search_status)
        
        if products:
            # 제품 목록 표시
            st.markdown("### 2️⃣ 검색 결과")
            
            for i, product in enumerate(products):
                with st.expander(f"🔍 {product['product_code']} - {product['product_name_korean']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**제품 코드**: {product['product_code']}")
                        st.write(f"**한국어명**: {product['product_name_korean']}")
                        st.write(f"**영어명**: {product['product_name_english']}")
                    
                    with col2:
                        st.write(f"**카테고리**: {product['main_category']}")
                        st.write(f"**서브카테고리**: {product.get('sub_category', 'N/A')}")
                        
                        # 상태 표시
                        status = product.get('status', 'N/A')
                        if status == 'active':
                            st.success(f"✅ 상태: 활성")
                        elif status == 'inactive':
                            st.error(f"🗑️ 상태: 삭제됨")
                        else:
                            st.info(f"ℹ️ 상태: {status}")
                    
                    with col3:
                        # 버튼 표시
                        if delete_type == "완전 삭제 (데이터 제거)":
                            button_label = "💥 완전삭제"
                            button_type = "primary"
                        else:
                            button_label = "🗑️ 삭제"
                            button_type = "secondary"
                        
                        if st.button(button_label, key=f"delete_{i}", type=button_type):
                            # 삭제 확인 대화상자
                            st.session_state[f'confirm_delete_{product["product_code"]}_{delete_type}'] = True
                        
                        # 삭제 확인이 활성화된 경우
                        confirm_key = f'confirm_delete_{product["product_code"]}_{delete_type}'
                        if st.session_state.get(confirm_key, False):
                            if delete_type == "완전 삭제 (데이터 제거)":
                                st.error(f"⚠️ 정말로 '{product['product_code']}'를 완전 삭제하시겠습니까?")
                                st.caption("이 작업은 되돌릴 수 없습니다!")
                            else:
                                st.warning(f"⚠️ 정말로 '{product['product_code']}'를 삭제하시겠습니까?")
                            
                            col_yes, col_no = st.columns(2)
                            
                            with col_yes:
                                if st.button("✅ 예", key=f"yes_{i}", type="primary"):
                                    if delete_type == "완전 삭제 (데이터 제거)":
                                        result, message = master_product_manager.permanently_delete_product(product['product_code'])
                                        action_text = "완전삭제"
                                    else:
                                        result, message = master_product_manager.delete_product(product['product_code'])
                                        action_text = "삭제"
                                    
                                    if result:
                                        NotificationHelper.show_operation_success(action_text, product.get('product_code', '제품'))
                                        # 확인 상태 초기화
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        st.rerun()
                                    else:
                                        NotificationHelper.show_error(message)
                            
                            with col_no:
                                if st.button("❌ 아니오", key=f"no_{i}", type="secondary"):
                                    # 확인 상태 초기화
                                    if confirm_key in st.session_state:
                                        del st.session_state[confirm_key]
                                    st.rerun()
        else:
            st.info("검색 조건에 맞는 제품이 없습니다.")