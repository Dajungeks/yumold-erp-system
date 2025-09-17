"""
시스템 설정 페이지 - 제품 분류 관리 중심
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from managers.legacy.multi_category_manager import MultiCategoryManager
# 기존 import들 아래에 추가
from managers.postgresql.base_postgresql_manager import BasePostgreSQLManager

def show_system_settings_page(config_manager, get_text, hide_header=False, managers=None):
    """시스템 설정 메인 페이지"""
    
    # 메인 컨텐츠 영역만 영향을 주는 레이아웃 설정
    st.markdown("""
    <style>
    /* 사이드바 버튼 간격 유지 */
    .stSidebar .stButton {
        margin-bottom: 0.25rem !important;
    }
    .stSidebar .stButton > button {
        margin-bottom: 0 !important;
    }
    
    /* 메인 컨텐츠 영역만 영향 */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    .main .stTabs [data-baseweb="tab-list"] {
        margin-top: -1rem;
        margin-bottom: 1rem;
    }
    .main .stSubheader {
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }
    .main .element-container {
        margin-bottom: 1rem !important;
    }
    .main .stExpander {
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not hide_header:
        st.header("⚙️ 시스템 설정")
        st.caption("제품 분류, 회사 정보, 시스템 옵션을 관리합니다")
    
    # 메인 시스템 설정 탭 구성
    main_tabs = st.tabs(["🏗️ 제품 카테고리 관리", "🏢 회사 기본 정보", "🏭 공급업체 관리"])
    
    with main_tabs[0]:
        # 제품 카테고리 관리
        # 제품 카테고리 설정 관리자 확인
        if config_manager is None:
            try:
                from product_category_config_manager import ProductCategoryConfigManager
                config_manager = ProductCategoryConfigManager()
            except Exception as e:
                st.error(f"시스템 설정 관리자 초기화 오류: {e}")
                return
        
        show_product_category_management(config_manager)
    
    with main_tabs[1]:
        # 회사 기본 정보 입력/수정
        if managers and 'system_config_manager' in managers:
            from pages.system_config_page import show_system_settings_tab
            from notification_helper import NotificationHelper
            notif = NotificationHelper()
            show_system_settings_tab(managers['system_config_manager'], notif)
        else:
            st.error("시스템 설정 매니저가 로드되지 않았습니다.")
    
    with main_tabs[2]:
        # 공급업체 관리
        if managers and 'supplier_manager' in managers:
            show_supplier_management(managers['supplier_manager'])
        else:
            st.error("공급업체 관리자가 로드되지 않았습니다.")

def show_supplier_management(supplier_manager):
    """공급업체 관리 섹션"""
    st.subheader("🏭 공급업체 관리")
    st.caption("공급업체 등록, 수정, 조회를 관리합니다")
    
    # 공급업체 관리 탭 구성
    supplier_tabs = st.tabs(["📋 공급업체 목록", "➕ 신규 공급업체 등록", "✏️ 공급업체 수정"])
    
    with supplier_tabs[0]:
        show_supplier_list(supplier_manager)
    
    with supplier_tabs[1]:
        show_supplier_registration(supplier_manager)
    
    with supplier_tabs[2]:
        show_supplier_edit(supplier_manager)

def show_supplier_list(supplier_manager):
    """공급업체 목록 표시"""
    st.markdown("### 📋 등록된 공급업체 목록")
    
    try:
        suppliers_df = supplier_manager.get_all_suppliers()
        
        if not suppliers_df.empty:
            # 통계 정보
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 공급업체", len(suppliers_df))
            with col2:
                active_count = len(suppliers_df[suppliers_df['status'] == '활성'])
                st.metric("활성 공급업체", active_count)
            with col3:
                countries = suppliers_df['country'].value_counts()
                st.metric("국가 수", len(countries) if not countries.empty else 0)
            with col4:
                avg_rating = suppliers_df['rating'].mean() if 'rating' in suppliers_df.columns else 0
                st.metric("평균 평점", f"{avg_rating:.1f}")
            
            st.markdown("---")
            
            # 필터 옵션
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                status_filter = st.selectbox("상태 필터", ["전체", "활성", "비활성"])
            with col_filter2:
                country_filter = st.selectbox("국가 필터", ["전체"] + list(suppliers_df['country'].unique()))
            
            # 데이터 필터링
            filtered_df = suppliers_df.copy()
            if status_filter != "전체":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            if country_filter != "전체":
                filtered_df = filtered_df[filtered_df['country'] == country_filter]
            
            # 데이터 표시
            if not filtered_df.empty:
                # 주요 컬럼만 표시
                display_columns = ['supplier_id', 'company_name', 'contact_person', 'country', 'city', 'business_type', 'rating', 'status']
                available_columns = [col for col in display_columns if col in filtered_df.columns]
                
                st.dataframe(
                    filtered_df[available_columns],
                    use_container_width=True,
                    hide_index=True
                )
                
                # 상세 정보 표시
                if st.checkbox("상세 정보 표시"):
                    for idx, row in filtered_df.iterrows():
                        with st.expander(f"🏢 {row['company_name']} ({row['supplier_id']})"):
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.write(f"**담당자:** {row.get('contact_person', 'N/A')}")
                                st.write(f"**연락처:** {row.get('contact_phone', 'N/A')}")
                                st.write(f"**이메일:** {row.get('contact_email', 'N/A')}")
                                st.write(f"**주소:** {row.get('address', 'N/A')}")
                            with col_info2:
                                st.write(f"**업종:** {row.get('business_type', 'N/A')}")
                                st.write(f"**리드타임:** {row.get('lead_time_days', 'N/A')}일")
                                st.write(f"**최소주문금액:** {row.get('minimum_order_amount', 0):,.0f} {row.get('currency', 'VND')}")
                                st.write(f"**평점:** {row.get('rating', 0)}/5.0")
            else:
                st.info("필터 조건에 맞는 공급업체가 없습니다.")
        else:
            st.info("등록된 공급업체가 없습니다.")
    
    except Exception as e:
        st.error(f"공급업체 목록 조회 중 오류 발생: {str(e)}")

def show_supplier_registration(supplier_manager):
    """신규 공급업체 등록"""
    st.markdown("### ➕ 신규 공급업체 등록")
    
    with st.form("supplier_registration_form"):
        st.markdown("#### 📝 기본 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("회사명 *", placeholder="공급업체 회사명")
            contact_person = st.text_input("담당자명", placeholder="담당자 이름")
            contact_phone = st.text_input("연락처", placeholder="02-1234-5678")
            contact_email = st.text_input("이메일", placeholder="supplier@company.com")
        
        with col2:
            country = st.selectbox("국가", ["한국", "중국", "베트남", "일본", "미국", "독일", "기타"])
            city = st.text_input("도시", placeholder="도시명")
            business_type = st.selectbox("업종", ["제조업", "유통업", "서비스업", "IT", "화학", "기계", "전자", "기타"])
            rating = st.slider("평점", 1.0, 5.0, 3.0, 0.5)
        
        st.markdown("#### 🏢 상세 정보")
        col3, col4 = st.columns(2)
        
        with col3:
            address = st.text_area("주소", placeholder="상세 주소")
            tax_id = st.text_input("사업자번호", placeholder="123-45-67890")
            bank_info = st.text_input("계좌정보", placeholder="은행명 계좌번호")
        
        with col4:
            payment_terms = st.selectbox("결제조건", ["즉시결제", "NET 30", "NET 60", "전신송금", "신용장", "기타"])
            lead_time_days = st.number_input("리드타임(일)", min_value=1, max_value=365, value=30)
            minimum_order_amount = st.number_input("최소주문금액", min_value=0.0, value=0.0, step=100000.0)
            currency = st.selectbox("통화", ["VND", "KRW", "CNY", "USD", "EUR"])
        
        st.markdown("#### 📋 추가 정보")
        notes = st.text_area("비고", placeholder="추가 메모나 특이사항")
        status = st.selectbox("상태", ["활성", "비활성"], index=0)
        
        submitted = st.form_submit_button("✅ 공급업체 등록", use_container_width=True, type="primary")
        
        if submitted:
            if not company_name:
                st.error("회사명은 필수 입력 항목입니다.")
                return
            
            supplier_data = {
                'company_name': company_name,
                'contact_person': contact_person,
                'contact_phone': contact_phone,
                'contact_email': contact_email,
                'address': address,
                'country': country,
                'city': city,
                'business_type': business_type,
                'tax_id': tax_id,
                'bank_info': bank_info,
                'payment_terms': payment_terms,
                'lead_time_days': lead_time_days,
                'minimum_order_amount': minimum_order_amount,
                'currency': currency,
                'rating': rating,
                'notes': notes,
                'status': status
            }
            
            try:
                success = supplier_manager.add_supplier(supplier_data)
                if success:
                    st.success(f"✅ 공급업체 '{company_name}'가 성공적으로 등록되었습니다!")
                    st.info("공급업체 목록 탭에서 등록된 공급업체를 확인할 수 있습니다.")
                    st.rerun()
                else:
                    st.error("❌ 공급업체 등록에 실패했습니다. (중복된 회사명일 수 있습니다)")
            except Exception as e:
                st.error(f"❌ 공급업체 등록 중 오류 발생: {str(e)}")

def show_supplier_edit(supplier_manager):
    """공급업체 정보 수정"""
    st.markdown("### ✏️ 공급업체 정보 수정")
    
    try:
        suppliers_df = supplier_manager.get_all_suppliers()
        
        if not suppliers_df.empty:
            # 공급업체 선택
            supplier_options = {f"{row['company_name']} ({row['supplier_id']})": row['supplier_id'] 
                              for _, row in suppliers_df.iterrows()}
            
            selected_option = st.selectbox("수정할 공급업체 선택", ["공급업체 선택"] + list(supplier_options.keys()))
            
            if selected_option and selected_option != "공급업체 선택":
                selected_supplier_id = supplier_options[selected_option]
                supplier_info = supplier_manager.get_supplier_by_id(selected_supplier_id)
                
                if supplier_info:
                    st.success(f"✅ 선택된 공급업체: **{supplier_info['company_name']}**")
                    
                    with st.form("supplier_edit_form"):
                        st.markdown("#### 📝 기본 정보 수정")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            company_name = st.text_input("회사명 *", value=supplier_info.get('company_name', ''))
                            contact_person = st.text_input("담당자명", value=supplier_info.get('contact_person', ''))
                            contact_phone = st.text_input("연락처", value=supplier_info.get('contact_phone', ''))
                            contact_email = st.text_input("이메일", value=supplier_info.get('contact_email', ''))
                        
                        with col2:
                            country = st.selectbox("국가", ["한국", "중국", "베트남", "일본", "미국", "독일", "기타"], 
                                                 index=["한국", "중국", "베트남", "일본", "미국", "독일", "기타"].index(supplier_info.get('country', '기타')) if supplier_info.get('country') in ["한국", "중국", "베트남", "일본", "미국", "독일", "기타"] else 7)
                            city = st.text_input("도시", value=supplier_info.get('city', ''))
                            business_type = st.selectbox("업종", ["제조업", "유통업", "서비스업", "IT", "화학", "기계", "전자", "기타"],
                                                       index=["제조업", "유통업", "서비스업", "IT", "화학", "기계", "전자", "기타"].index(supplier_info.get('business_type', '기타')) if supplier_info.get('business_type') in ["제조업", "유통업", "서비스업", "IT", "화학", "기계", "전자", "기타"] else 7)
                            rating = st.slider("평점", 1.0, 5.0, float(supplier_info.get('rating', 3.0)), 0.5)
                        
                        st.markdown("#### 🏢 상세 정보")
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            address = st.text_area("주소", value=supplier_info.get('address', ''))
                            tax_id = st.text_input("사업자번호", value=supplier_info.get('tax_id', ''))
                            bank_info = st.text_input("계좌정보", value=supplier_info.get('bank_info', ''))
                        
                        with col4:
                            payment_terms = st.selectbox("결제조건", ["즉시결제", "NET 30", "NET 60", "전신송금", "신용장", "기타"],
                                                        index=["즉시결제", "NET 30", "NET 60", "전신송금", "신용장", "기타"].index(supplier_info.get('payment_terms', '기타')) if supplier_info.get('payment_terms') in ["즉시결제", "NET 30", "NET 60", "전신송금", "신용장", "기타"] else 5)
                            lead_time_days = st.number_input("리드타임(일)", min_value=1, max_value=365, value=int(supplier_info.get('lead_time_days', 30)))
                            minimum_order_amount = st.number_input("최소주문금액", min_value=0.0, value=float(supplier_info.get('minimum_order_amount', 0)), step=100000.0)
                            currency = st.selectbox("통화", ["VND", "KRW", "CNY", "USD", "EUR"],
                                                   index=["VND", "KRW", "CNY", "USD", "EUR"].index(supplier_info.get('currency', 'VND')) if supplier_info.get('currency') in ["VND", "KRW", "CNY", "USD", "EUR"] else 0)
                        
                        st.markdown("#### 📋 추가 정보")
                        notes = st.text_area("비고", value=supplier_info.get('notes', ''))
                        status = st.selectbox("상태", ["활성", "비활성"], 
                                            index=["활성", "비활성"].index(supplier_info.get('status', '활성')) if supplier_info.get('status') in ["활성", "비활성"] else 0)
                        
                        submitted = st.form_submit_button("💾 정보 수정", use_container_width=True, type="primary")
                        
                        if submitted:
                            if not company_name:
                                st.error("회사명은 필수 입력 항목입니다.")
                                return
                            
                            updated_data = {
                                'company_name': company_name,
                                'contact_person': contact_person,
                                'contact_phone': contact_phone,
                                'contact_email': contact_email,
                                'address': address,
                                'country': country,
                                'city': city,
                                'business_type': business_type,
                                'tax_id': tax_id,
                                'bank_info': bank_info,
                                'payment_terms': payment_terms,
                                'lead_time_days': lead_time_days,
                                'minimum_order_amount': minimum_order_amount,
                                'currency': currency,
                                'rating': rating,
                                'notes': notes,
                                'status': status
                            }
                            
                            try:
                                success = supplier_manager.update_supplier(selected_supplier_id, updated_data)
                                if success:
                                    st.success(f"✅ 공급업체 '{company_name}' 정보가 성공적으로 수정되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("❌ 공급업체 정보 수정에 실패했습니다.")
                            except Exception as e:
                                st.error(f"❌ 공급업체 정보 수정 중 오류 발생: {str(e)}")
                else:
                    st.error("선택한 공급업체 정보를 찾을 수 없습니다.")
        else:
            st.info("등록된 공급업체가 없습니다. 먼저 공급업체를 등록해주세요.")
    
    except Exception as e:
        st.error(f"공급업체 정보 조회 중 오류 발생: {str(e)}")

def show_product_category_management(config_manager):
    """Total Category 관리"""
    
    # Multi-Category Manager 초기화
    try:
        multi_manager = MultiCategoryManager()
    except Exception as e:
        st.error(f"Multi-Category Manager 초기화 오류: {e}")
        return
    
    # 메인 섹션 구성: Total 카탈로그 vs Category 관리
    main_sections = st.tabs(["📊 Total 카탈로그", "🏗️ Category 관리"])
    
    with main_sections[0]:
        # Total 카탈로그 섹션
        show_total_catalog(config_manager, multi_manager)
    
    with main_sections[1]:
        # Category 관리 섹션
        show_category_management_tabs(config_manager, multi_manager)

def show_total_catalog(config_manager, multi_manager):
    """Total 카탈로그 - 모든 카테고리 조회 및 통계"""
    st.subheader("📊 Total 카탈로그")
    st.caption("등록된 모든 카테고리의 코드와 통계를 조회합니다")
    
    # Total 카탈로그 내부 탭 구성
    catalog_tabs = st.tabs(["📝 등록된 코드 설명", "📋 카테고리별 테이블 조회"])
    
    with catalog_tabs[0]:
        # 등록된 코드 설명 표시
        show_registered_codes(config_manager, multi_manager)
    
    with catalog_tabs[1]:
        # 카테고리별 테이블 조회 (Category A~G)
        show_category_table_query_section(config_manager, multi_manager)

def show_category_table_query_section(config_manager, multi_manager):
    """카테고리별 테이블 조회 섹션"""
    
    # Category 선택 필터
    col1, col2 = st.columns([1, 3])
    
    with col1:
        categories = ["Category A", "Category B", "Category C", "Category D", "Category E", "Category F", "Category G", "Category H", "Category I"]
        selected_category = st.selectbox("📋 카테고리 선택", categories)
    
    with col2:
        st.info(f"선택된 카테고리: **{selected_category}**")
    
    try:
        import pandas as pd
        
        # PostgreSQL 연결 사용
        postgres_manager = BasePostgreSQLManager()
        conn = postgres_manager.get_connection()
        
        # 선택된 카테고리에 따른 테이블 및 쿼리 설정
        category_letter = selected_category.split()[-1]  # "Category A" -> "A"
        
        if category_letter == "A":
            # Category A: 완성된 코드 생성 (6단계 조합) - 활성 코드만
            query = '''
                SELECT DISTINCT
                    (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key || '-' || l6.component_key) as "완성된 코드",
                    (COALESCE(s.description, s.component_name) || ' / ' || 
                     COALESCE(p.description, p.component_name) || ' / ' || 
                     COALESCE(g.description, g.component_name) || ' / ' || 
                     COALESCE(sz.description, sz.component_name) || ' / ' || 
                     COALESCE(l5.description, l5.component_name) || ' / ' || 
                     COALESCE(l6.description, l6.component_name)) as "설명",
                    l6.created_date as "생성일"
                FROM hr_product_components s
                JOIN hr_product_components p ON p.parent_component = s.component_key
                JOIN hr_product_components g ON g.parent_component = (s.component_key || '-' || p.component_key)
                JOIN hr_product_components sz ON sz.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key)
                JOIN hr_product_components l5 ON l5.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key)
                JOIN hr_product_components l6 ON l6.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key)
                WHERE s.component_type = 'system_type'
                  AND p.component_type = 'product_type'
                  AND g.component_type = 'gate_type'
                  AND sz.component_type = 'size'
                  AND l5.component_type = 'level5'
                  AND l6.component_type = 'level6'
                  AND s.is_active = true AND p.is_active = true AND g.is_active = true AND sz.is_active = true AND l5.is_active = true AND l6.is_active = true

            '''
        else:
            # Category B~G: 완성된 코드 생성 (6단계 조합)
            query = f'''
                SELECT DISTINCT
                    (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key || '-' || l5.component_key || '-' || l6.component_key) as "완성된 코드",
                    (COALESCE(l1.description, l1.component_name) || ' / ' || 
                     COALESCE(l2.description, l2.component_name) || ' / ' || 
                     COALESCE(l3.description, l3.component_name) || ' / ' || 
                     COALESCE(l4.description, l4.component_name) || ' / ' || 
                     COALESCE(l5.description, l5.component_name) || ' / ' || 
                     COALESCE(l6.description, l6.component_name)) as "설명",
                    l6.created_date as "생성일"
                FROM multi_category_components l1
                JOIN multi_category_components l2 ON l2.parent_component = l1.component_key AND l2.category_type = '{category_letter}'
                JOIN multi_category_components l3 ON l3.parent_component = (l1.component_key || '-' || l2.component_key) AND l3.category_type = '{category_letter}'
                JOIN multi_category_components l4 ON l4.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key) AND l4.category_type = '{category_letter}'
                JOIN multi_category_components l5 ON l5.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key) AND l5.category_type = '{category_letter}'
                JOIN multi_category_components l6 ON l6.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key || '-' || l5.component_key) AND l6.category_type = '{category_letter}'
                WHERE l1.category_type = '{category_letter}' AND l1.component_level = 'level1'
                  AND l2.component_level = 'level2'
                  AND l3.component_level = 'level3'
                  AND l4.component_level = 'level4'
                  AND l5.component_level = 'level5'
                  AND l6.component_level = 'level6'
                  AND l1.is_active = 1 AND l2.is_active = 1 AND l3.is_active = 1 AND l4.is_active = 1 AND l5.is_active = 1 AND l6.is_active = 1

            '''
        
        postgres_manager = BasePostgreSQLManager()
        postgres_conn = postgres_manager.get_connection()
        
        df = pd.read_sql_query(query, postgres_conn)
        postgres_manager.close_connection(postgres_conn)
        
        if not df.empty:
            st.subheader(f"📋 {selected_category} 완성된 코드 목록")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 통계 정보
            st.info(f"📊 **총 {len(df)}개**의 완성된 코드가 있습니다.")
            
            # CSV 내보내기
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 파일로 내보내기",
                data=csv,
                file_name=f"{selected_category.lower().replace(' ', '_')}_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            if category_letter == "A":
                st.info("완성된 코드가 없습니다. 6단계 구성 요소가 모두 등록되어야 완성된 코드가 생성됩니다.")
            else:
                # Category B~G의 활성화 상태 확인
                config = multi_manager.get_category_config(category_letter)
                if not config or not config['is_enabled']:
                    st.warning(f"{selected_category}는 비활성화 상태입니다. Category 관리에서 활성화해주세요.")
                else:
                    st.info("완성된 코드가 없습니다. 6단계 구성 요소가 모두 등록되어야 완성된 코드가 생성됩니다.")
            
    except Exception as e:
        st.error(f"테이블 조회 중 오류가 발생했습니다: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_category_management_tabs(config_manager, multi_manager):
    """Category 관리 탭들"""
    
    # Category 탭 구성
    tabs = st.tabs([
        "📁 Category A", "📁 Category B", "📁 Category C", 
        "📁 Category D", "📁 Category E", "📁 Category F", 
        "📁 Category G", "📁 Category H", "📁 Category I"
    ])
    
    with tabs[0]:  # Category A
        show_hr_subcategories(config_manager)
    
    with tabs[1]:  # Category B
        manage_general_category(multi_manager, 'B')
    
    with tabs[2]:  # Category C
        manage_general_category(multi_manager, 'C')
    
    with tabs[3]:  # Category D
        manage_general_category(multi_manager, 'D')
    
    with tabs[4]:  # Category E
        manage_general_category(multi_manager, 'E')
    
    with tabs[5]:  # Category F
        manage_general_category(multi_manager, 'F')
    
    with tabs[6]:  # Category G
        manage_general_category(multi_manager, 'G')
    
    with tabs[7]:  # Category H
        manage_general_category(multi_manager, 'H')
    
    with tabs[8]:  # Category I
        manage_general_category(multi_manager, 'I')

def show_registered_codes(config_manager, multi_manager):
    """등록된 코드들을 표시하는 테이블"""
    st.subheader("📝 등록된 코드 설명")
    
    try:
        import sqlite3
        import pandas as pd
        
        # 데이터베이스 연결
        db_path = "erp_system.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 하위 카테고리 컬럼명
        sub_categories = ["Product", "Category 1", "Category 2", "Category 3", "Category 4", "Category 5", "Category 6"]
        
        # 메인 카테고리별 데이터 생성
        main_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        data_rows = []
        
        for main_cat in main_categories:
            if main_cat == 'A':
                row_data = ["Category A"]  # Category A로 표시
                
                # Category A의 경우 실제 데이터 조회
                category_a_components = ["level1", "level2", "level3", "level4", "level5", "level6"]
                
                # Product 컬럼: Category A-1(level1)의 설명 표시
                try:
                    cursor.execute('''
                        SELECT DISTINCT COALESCE(description, component_name, component_key)
                        FROM hr_product_components 
                        WHERE component_type = ? AND is_active = 1

                    ''', ("level1",))
                    descriptions = cursor.fetchall()
                    
                    if descriptions:
                        desc_list = [desc[0] for desc in descriptions]
                        row_data.append(", ".join(desc_list))
                    else:
                        row_data.append("미등록")
                except Exception as e:
                    row_data.append("오류")
                
                # Category 1~6: 각 A-1~A-6의 키를 순차적으로 표시
                for component_type in category_a_components:  # level1부터 level6까지 모든 component
                    try:
                        cursor.execute('''
                            SELECT DISTINCT component_key 
                            FROM hr_product_components 
                            WHERE component_type = ? AND is_active = 1

                        ''', (component_type,))
                        codes = cursor.fetchall()
                        
                        if codes:
                            code_list = [code[0] for code in codes]
                            row_data.append(", ".join(code_list))
                        else:
                            row_data.append("미등록")
                    except Exception as e:
                        row_data.append("오류")
                
            else:
                row_data = [f"Category {main_cat}"]
                # Category B~I는 Multi-Category Manager로 관리 - 실제 데이터 조회
                level_names = ["level1", "level2", "level3", "level4", "level5", "level6"]
                
                # Product 컬럼: Level1의 설명 표시
                try:
                    cursor.execute('''
                        SELECT DISTINCT COALESCE(description, component_name, component_key)
                        FROM multi_category_components 
                        WHERE category_type = ? AND component_level = 'level1' AND is_active = 1

                    ''', (main_cat,))
                    level1_descriptions = cursor.fetchall()
                    
                    if level1_descriptions:
                        desc_list = [desc[0] for desc in level1_descriptions]
                        row_data.append(", ".join(desc_list))
                    else:
                        row_data.append("미등록")
                except Exception as e:
                    row_data.append("오류")
                
                # Category 1~6: 각 레벨의 키를 순차적으로 표시
                for level_name in level_names:
                    try:
                        cursor.execute('''
                            SELECT DISTINCT component_key 
                            FROM multi_category_components 
                            WHERE category_type = ? AND component_level = ? AND is_active = 1

                        ''', (main_cat, level_name))
                        codes = cursor.fetchall()
                        
                        if codes:
                            code_list = [code[0] for code in codes]
                            row_data.append(", ".join(code_list))
                        else:
                            row_data.append("미등록")
                    except Exception as e:
                        row_data.append("오류")
            
            data_rows.append(row_data)
        
        conn.close()
        
        # 데이터프레임 생성 (메인 카테고리가 좌측에 표시됨)
        df = pd.DataFrame(data_rows, columns=[""] + sub_categories)
        df = df.set_index("")  # 첫 번째 컬럼을 인덱스로 설정
        
        st.dataframe(df, use_container_width=True)
        
        # 총 등록 코드 수 (모든 카테고리)
        if data_rows:
            total_codes = 0
            category_totals = {}
            
            for i, row in enumerate(data_rows):
                category_name = row[0]
                category_codes = row[1:8]  # Product부터 Category 6까지
                category_total = 0
                
                for codes_str in category_codes:
                    if codes_str not in ["미등록", "미구현", "오류"]:
                        if isinstance(codes_str, str) and codes_str:
                            category_total += len(codes_str.split(", "))
                
                if category_total > 0:
                    category_totals[category_name] = category_total
                    total_codes += category_total
            
            # 결과 표시
            if category_totals:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.info(f"📊 **전체 {total_codes}개**의 코드가 등록되어 있습니다.")
                with col2:
                    summary_text = " | ".join([f"{cat}: {count}개" for cat, count in category_totals.items()])
                    st.caption(f"카테고리별: {summary_text}")
            else:
                st.info("아직 등록된 코드가 없습니다.")
            
    except Exception as e:
        st.error(f"등록된 코드 조회 중 오류가 발생했습니다: {e}")

def show_code_registration_status(config_manager):
    """계층별 카테고리 등록 코드 수 표시 (메인 카테고리 A~G 좌측, 하위 카테고리 상단)"""
    st.subheader("📊 코드 등록 현황")
    
    try:
        import sqlite3
        import pandas as pd
        
        # 데이터베이스 연결
        db_path = "erp_system.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 하위 카테고리 컬럼명
        sub_categories = ["Product", "Category 1", "Category 2", "Category 3", "Category 4", "Category 5", "Category 6"]
        
        # 메인 카테고리별 데이터 생성
        main_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        data_rows = []
        
        for main_cat in main_categories:
            if main_cat == 'A':
                row_data = ["Category A"]  # Category A로 표시
                
                # Category A의 경우 실제 데이터 조회
                category_a_components = ["system_type", "product_type", "gate_type", "size", "level5", "level6"]
                
                for component_type in category_a_components:
                    try:
                        cursor.execute('''
                            SELECT COUNT(DISTINCT component_key) 
                            FROM hr_product_components 
                            WHERE component_type = ? AND is_active = 1
                        ''', (component_type,))
                        count = cursor.fetchone()[0]
                        row_data.append(count)
                    except Exception as e:
                        row_data.append(0)
                
                # Category 6은 아직 구현되지 않음
                row_data.append(0)
                
            else:
                row_data = [f"Category {main_cat}"]
                # Category B~I는 Multi-Category Manager로 관리 - 실제 개수 조회
                level_names = ["level1", "level2", "level3", "level4", "level5", "level6"]
                
                # Product 컬럼: Level1 개수
                try:
                    cursor.execute('''
                        SELECT COUNT(DISTINCT component_key) 
                        FROM multi_category_components 
                        WHERE category_type = ? AND component_level = 'level1' AND is_active = 1
                    ''', (main_cat,))
                    count = cursor.fetchone()[0]
                    row_data.append(count)
                except Exception as e:
                    row_data.append(0)
                
                # Category 1~6: 각 레벨의 개수
                for level_name in level_names:
                    try:
                        cursor.execute('''
                            SELECT COUNT(DISTINCT component_key) 
                            FROM multi_category_components 
                            WHERE category_type = ? AND component_level = ? AND is_active = 1
                        ''', (main_cat, level_name))
                        count = cursor.fetchone()[0]
                        row_data.append(count)
                    except Exception as e:
                        row_data.append(0)
            
            data_rows.append(row_data)
        
        conn.close()
        
        # 데이터프레임 생성 (메인 카테고리가 좌측에 표시됨)
        df = pd.DataFrame(data_rows, columns=[""] + sub_categories)
        df = df.set_index("")  # 첫 번째 컬럼을 인덱스로 설정
        
        st.dataframe(df, use_container_width=True)
        
        # 총 등록 코드 수는 제거 (불필요한 정보박스)
            
    except Exception as e:
        st.error(f"코드 등록 현황 조회 중 오류가 발생했습니다: {e}")

def show_hr_subcategories(config_manager):
    """Category A 구성 요소 관리 (구성 관리만)"""
    st.subheader("🏗️ Category A ↗")
    
    # 세션 상태 초기화
    if 'hr_component_tab' in st.session_state:
        del st.session_state['hr_component_tab']
    if 'settings_tab' in st.session_state:
        del st.session_state['settings_tab']
    
    # Category A 구성 요소 관리 탭
    hr_tabs = st.tabs([
        "🔧 Category A-1 (Product)", 
        "📋 Category A-2 (Code)", 
        "🚪 Category A-3 (Code)", 
        "📏 Category A-4 (Code)",
        "🔩 Category A-5 (Code)",
        "⚙️ Category A-6 (Code)"
    ])
    
    with hr_tabs[0]:
        manage_hr_system_types(config_manager)
    with hr_tabs[1]:
        manage_hr_product_types(config_manager)
    with hr_tabs[2]:
        manage_hr_gate_types(config_manager)
    with hr_tabs[3]:
        manage_hr_sizes(config_manager)
    with hr_tabs[4]:
        manage_hr_level5_components(config_manager)
    with hr_tabs[5]:
        manage_hr_level6_components(config_manager)


def manage_hr_system_types(config_manager):
    """Category A-1 (Product)"""
    st.subheader("🔧 Category A-1 (Product)")
    
    # 현재 Category A-1 목록 표시 (활성 상태만)
    system_types = config_manager.get_hr_components_for_management('system_type')
    active_types = [st for st in system_types if st['is_active']] if system_types else []
    
    if active_types:
        st.write("**현재 Category A-1 목록:**")
        for st_type in active_types:
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                st.write(f"**{st_type['component_key']}** - {st_type['component_name']}")
                if st_type['description']:
                    st.caption(st_type['description'])
            with col2:
                if st.button("✏️", key=f"edit_st_{st_type['component_id']}", help="수정", use_container_width=True):
                    st.session_state[f"editing_st_{st_type['component_id']}"] = True
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_st_{st_type['component_id']}", help="완전삭제", use_container_width=True):
                    if config_manager.delete_hr_component_permanently(st_type['component_id']):
                        st.success("Category A-1이 완전 삭제되었습니다!")
                        st.rerun()
            
            # 수정 폼 표시
            if st.session_state.get(f"editing_st_{st_type['component_id']}", False):
                with st.expander("✏️ Category A-1 수정", expanded=True):
                    with st.form(f"edit_system_type_{st_type['component_id']}"):
                        new_key = st.text_input("키", value=st_type['component_key'])
                        new_description = st.text_input("제품명", value=st_type['description'] or "")
                        
                        col_submit, col_cancel = st.columns([1, 1])
                        with col_submit:
                            if st.form_submit_button("💾 저장"):
                                if config_manager.update_hr_component(
                                    st_type['component_id'], component_key=new_key, 
                                    component_name=new_key, description=new_description
                                ):
                                    st.success("Category A-1이 수정되었습니다!")
                                    del st.session_state[f"editing_st_{st_type['component_id']}"]
                                    st.rerun()
                                else:
                                    st.error("수정 중 오류가 발생했습니다.")
                        with col_cancel:
                            if st.form_submit_button("❌ 취소"):
                                del st.session_state[f"editing_st_{st_type['component_id']}"]
                                st.rerun()
    
    # 새 Category A-1 추가
    with st.expander("➕ 새 Category A-1 추가"):
        with st.form("add_system_type"):
            new_key = st.text_input("키", placeholder="예: Coil")
            new_description = st.text_input("제품명", placeholder="예: 코일형 핫러너 시스템")
            
            if st.form_submit_button("➕ Category A-1 추가"):
                if new_key:
                    success = config_manager.add_hr_component(
                        'system_type', None, new_key, new_key, None, None, new_description
                    )
                    if success:
                        st.success(f"Category A-1 '{new_key}'가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("Category A-1 추가 중 오류가 발생했습니다. (중복된 키일 수 있습니다)")
                else:
                    st.warning("키는 필수입니다.")

def manage_hr_product_types(config_manager):
    """Category A-2 (Code)"""
    st.subheader("📋 Category A-2 (Code)")
    
    # Category A-1 선택
    system_types = config_manager.get_hr_system_types()
    
    if not system_types:
        st.warning("먼저 Category A-1을 등록해주세요.")
        return
    
    selected_system = st.selectbox("Category A-1 선택", [""] + system_types)
    
    if selected_system:
        # 선택된 Category A-1의 Category A-2 목록
        product_types = config_manager.get_hr_components_for_management('product_type')
        filtered_types = [pt for pt in product_types if pt['parent_component'] == selected_system and pt['is_active']]
        
        if filtered_types:
            st.write(f"**{selected_system}의 Category A-2:**")
            for pt in filtered_types:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"• **{pt['component_key']}** - {pt['component_name']}")
                    if pt['description']:
                        st.caption(pt['description'])
                with col2:
                    if st.button("✏️", key=f"edit_pt_{pt['component_id']}", help="수정", use_container_width=True):
                        st.session_state[f"editing_pt_{pt['component_id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_pt_{pt['component_id']}", help="삭제", use_container_width=True):
                        if config_manager.delete_hr_component_permanently(pt['component_id']):
                            st.success("Category A-2가 완전 삭제되었습니다!")
                            st.rerun()
                
                # 수정 폼 표시
                if st.session_state.get(f"editing_pt_{pt['component_id']}", False):
                    with st.expander("✏️ Category A-2 수정", expanded=True):
                        with st.form(f"edit_product_type_{pt['component_id']}"):
                            new_key = st.text_input("키", value=pt['component_key'])
                            new_description = st.text_input("제품명", value=pt['description'] or "")
                            
                            col_submit, col_cancel = st.columns([1, 1])
                            with col_submit:
                                if st.form_submit_button("💾 저장"):
                                    if config_manager.update_hr_component(
                                        pt['component_id'], component_key=new_key, 
                                        component_name=new_key, description=new_description
                                    ):
                                        st.success("Category A-2가 수정되었습니다!")
                                        del st.session_state[f"editing_pt_{pt['component_id']}"]
                                        st.rerun()
                                    else:
                                        st.error("수정 중 오류가 발생했습니다.")
                            with col_cancel:
                                if st.form_submit_button("❌ 취소"):
                                    del st.session_state[f"editing_pt_{pt['component_id']}"]
                                    st.rerun()
        
        # 새 Product Type 추가
        with st.expander(f"➕ {selected_system}에 새 Category A-2 추가"):
            with st.form(f"add_product_type_{selected_system}"):
                new_key = st.text_input("키", placeholder="예: ST")
                new_description = st.text_input("제품명", placeholder="예: 표준형 제품")
                
                if st.form_submit_button("➕ Category A-2 추가"):
                    if new_key:
                        success = config_manager.add_hr_component(
                            'product_type', selected_system, new_key, new_key, 
                            None, None, new_description
                        )
                        if success:
                            st.success(f"Category A-2 '{new_key}'가 추가되었습니다!")
                            st.rerun()
                        else:
                            st.error("Category A-2 추가 중 오류가 발생했습니다.")
                    else:
                        st.warning("키는 필수입니다.")

def manage_hr_gate_types(config_manager):
    """Category A-3 (Code)"""
    st.subheader("🚪 Category A-3 (Code)")
    
    # Category A-1과 Category A-2 선택
    system_types = config_manager.get_hr_system_types()
    
    if not system_types:
        st.warning("먼저 Category A-1을 등록해주세요.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_system = st.selectbox("Category A-1", [""] + system_types, key="gate_system")
    
    with col2:
        if selected_system:
            product_types = config_manager.get_hr_product_types(selected_system)
            selected_product = st.selectbox("Category A-2", [""] + product_types, key="gate_product")
        else:
            selected_product = None
    
    if selected_system and selected_product:
        parent_key = f"{selected_system}-{selected_product}"
        
        # Gate Type 목록 표시
        gate_types = config_manager.get_hr_components_for_management('gate_type')
        filtered_gates = [gt for gt in gate_types if gt['parent_component'] == parent_key and gt['is_active']]
        
        if filtered_gates:
            st.write(f"**{selected_system}-{selected_product}의 Category A-3:**")
            for gt in filtered_gates:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"• **{gt['component_key']}** - {gt['component_name']}")
                    if gt['description']:
                        st.caption(gt['description'])
                with col2:
                    if st.button("✏️", key=f"edit_gt_{gt['component_id']}", help="수정", use_container_width=True):
                        st.session_state[f"editing_gt_{gt['component_id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_gt_{gt['component_id']}", help="삭제", use_container_width=True):
                        if config_manager.delete_hr_component_permanently(gt['component_id']):
                            st.success("Category A-3이 완전 삭제되었습니다!")
                            st.rerun()
                
                # 수정 폼 표시
                if st.session_state.get(f"editing_gt_{gt['component_id']}", False):
                    with st.expander("✏️ Category A-3 수정", expanded=True):
                        with st.form(f"edit_gate_type_{gt['component_id']}"):
                            new_key = st.text_input("키", value=gt['component_key'])
                            new_description = st.text_input("제품명", value=gt['description'] or "")
                            
                            col_submit, col_cancel = st.columns([1, 1])
                            with col_submit:
                                if st.form_submit_button("💾 저장"):
                                    if config_manager.update_hr_component(
                                        gt['component_id'], component_key=new_key, 
                                        component_name=new_key, description=new_description
                                    ):
                                        st.success("Category A-3이 수정되었습니다!")
                                        del st.session_state[f"editing_gt_{gt['component_id']}"]
                                        st.rerun()
                                    else:
                                        st.error("수정 중 오류가 발생했습니다.")
                            with col_cancel:
                                if st.form_submit_button("❌ 취소"):
                                    del st.session_state[f"editing_gt_{gt['component_id']}"]
                                    st.rerun()
        
        # 새 Gate Type 추가
        with st.expander(f"➕ {parent_key}에 새 Category A-3 추가"):
            # 고유한 폼 키 사용
            form_key = f"add_gate_type_{parent_key.replace('-', '_')}"
            with st.form(form_key):
                new_key = st.text_input("키", placeholder="예: MAE", key=f"gt_key_{parent_key}")
                new_description = st.text_input("제품명", placeholder="예: MAE 타입 게이트", key=f"gt_desc_{parent_key}")
                
                if st.form_submit_button("➕ Category A-3 추가"):
                    if new_key.strip():
                        try:
                            success = config_manager.add_hr_component(
                                'gate_type', parent_key, new_key.strip(), new_key.strip(), 
                                None, None, new_description.strip() if new_description else None
                            )
                            if success:
                                st.success(f"✅ Category A-3 '{new_key}'가 추가되었습니다!")
                                # 세션 상태 초기화로 새로고침 효과
                                if 'gate_type_refresh' in st.session_state:
                                    del st.session_state['gate_type_refresh']
                                st.rerun()
                            else:
                                st.error("❌ Category A-3 추가 중 오류가 발생했습니다. (중복된 키일 수 있습니다)")
                        except Exception as e:
                            st.error(f"❌ 오류: {str(e)}")
                    else:
                        st.warning("⚠️ 키는 필수입니다.")

def manage_hr_sizes(config_manager):
    """Category A-4 (Code)"""
    st.subheader("📏 Category A-4 (Code)")
    
    # Category A-1과 Category A-2 선택
    system_types = config_manager.get_hr_system_types()
    
    if not system_types:
        st.warning("먼저 Category A-1을 등록해주세요.")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_system = st.selectbox("Category A-1", [""] + system_types, key="size_system")
    
    with col2:
        if selected_system:
            product_types = config_manager.get_hr_product_types(selected_system)
            selected_product = st.selectbox("Category A-2", [""] + product_types, key="size_product")
        else:
            selected_product = None
    
    with col3:
        if selected_system and selected_product:
            gate_types = config_manager.get_hr_gate_types(selected_system, selected_product)
            selected_gate = st.selectbox("Category A-3", [""] + gate_types, key="size_gate")
        else:
            selected_gate = None
    
    if selected_system and selected_product and selected_gate:
        parent_key = f"{selected_system}-{selected_product}-{selected_gate}"
        
        # Size 목록 표시
        sizes = config_manager.get_hr_components_for_management('size')
        filtered_sizes = [sz for sz in sizes if sz['parent_component'] == parent_key and sz['is_active']]
        
        if filtered_sizes:
            st.write(f"**{selected_system}-{selected_product}-{selected_gate}의 Category A-4:**")
            for sz in filtered_sizes:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"• **{sz['component_key']}** - {sz['component_name']}")
                    if sz['description']:
                        st.caption(sz['description'])
                with col2:
                    if st.button("✏️", key=f"edit_sz_{sz['component_id']}", help="수정", use_container_width=True):
                        st.session_state[f"editing_sz_{sz['component_id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"delete_sz_{sz['component_id']}", help="삭제", use_container_width=True):
                        if config_manager.delete_hr_component_permanently(sz['component_id']):
                            st.success("Category A-4가 완전 삭제되었습니다!")
                            st.rerun()
                
                # 수정 폼 표시
                if st.session_state.get(f"editing_sz_{sz['component_id']}", False):
                    with st.expander("✏️ Category A-4 수정", expanded=True):
                        with st.form(f"edit_size_{sz['component_id']}"):
                            new_key = st.text_input("키", value=sz['component_key'])
                            new_description = st.text_input("제품명", value=sz['description'] or "")
                            
                            col_submit, col_cancel = st.columns([1, 1])
                            with col_submit:
                                if st.form_submit_button("💾 저장"):
                                    old_size = sz['component_key']
                                    
                                    if config_manager.update_hr_component(
                                        sz['component_id'], component_key=new_key, 
                                        component_name=new_key, description=new_description
                                    ):
                                        st.success("Category A-4가 수정되었습니다!")
                                        
                                        # Category A-4 변경 시 관련 제품들 자동 업데이트
                                        if old_size != new_key:
                                            st.info(f"🔄 Category A-4 변경 감지: {old_size} → {new_key}")
                                            try:
                                                from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
                                                master_manager = SQLiteMasterProductManager()
                                                
                                                # parent_key에서 System Type, Product Type, Gate Type 추출
                                                parts = parent_key.split('-')
                                                st.info(f"📋 Parent Key 분석: {parent_key} → {parts}")
                                                
                                                if len(parts) == 3:
                                                    system_type, product_type, gate_type = parts
                                                    
                                                    # System Type 코드 변환
                                                    system_type_code = ""
                                                    if system_type == "Valve":
                                                        system_type_code = "VV"
                                                    elif system_type == "Open":
                                                        system_type_code = "OP"
                                                    else:
                                                        system_type_code = system_type[:2].upper()
                                                    
                                                    # 기존 및 새로운 제품 코드
                                                    old_product_code = f"HR-{system_type_code}-{product_type}-{gate_type}-{old_size}"
                                                    new_product_code = f"HR-{system_type_code}-{product_type}-{gate_type}-{new_key}"
                                                    
                                                    st.info(f"🎯 제품 코드 변환: {old_product_code} → {new_product_code}")
                                                    
                                                    # 기존 제품 조회
                                                    import sqlite3
                                                    conn = sqlite3.connect(master_manager.db_path)
                                                    cursor = conn.cursor()
                                                    
                                                    cursor.execute("SELECT * FROM master_products WHERE product_code = ?", (old_product_code,))
                                                    existing_product = cursor.fetchone()
                                                    
                                                    if existing_product:
                                                        st.info(f"✅ 기존 제품 발견: {old_product_code}")
                                                        
                                                        # 새로운 제품명 생성
                                                        korean_base = "핫러너 밸브" if system_type == "Valve" else f"핫러너 {system_type}"
                                                        new_korean_name = f"{korean_base} {product_type} {gate_type} {new_key}mm"
                                                        new_english_name = f"Hot Runner {system_type} {product_type} {gate_type} {new_key}mm"
                                                        
                                                        # 제품 정보 업데이트
                                                        cursor.execute('''
                                                            UPDATE master_products 
                                                            SET product_code = ?, product_name = ?, product_name_en = ?, product_name_vi = ?, updated_date = datetime('now')
                                                            WHERE product_code = ?
                                                        ''', (new_product_code, new_korean_name, new_english_name, new_english_name, old_product_code))
                                                        
                                                        updated_count = cursor.rowcount
                                                        conn.commit()
                                                        conn.close()
                                                        
                                                        if updated_count > 0:
                                                            st.success(f"🎯 **제품 자동 업데이트 완료!** `{old_product_code}` → `{new_product_code}`")
                                                        else:
                                                            st.warning(f"⚠️ 제품 업데이트 실패: {old_product_code}")
                                                    else:
                                                        st.warning(f"⚠️ 기존 제품을 찾을 수 없음: {old_product_code}")
                                                        conn.close()
                                                else:
                                                    st.error(f"❌ Parent Key 형식 오류: {parent_key}")
                                                        
                                            except Exception as e:
                                                st.error(f"❌ 제품 자동 업데이트 오류: {str(e)}")
                                                import traceback
                                                st.code(traceback.format_exc())
                                        
                                        del st.session_state[f"editing_sz_{sz['component_id']}"]
                                        st.rerun()
                                    else:
                                        st.error("수정 중 오류가 발생했습니다.")
                            with col_cancel:
                                if st.form_submit_button("❌ 취소"):
                                    del st.session_state[f"editing_sz_{sz['component_id']}"]
                                    st.rerun()
        
        
        # 새 Category A-4 추가
        with st.expander(f"➕ {selected_system}-{selected_product}-{selected_gate}에 새 Category A-4 추가"):
            # 폼 리셋을 위한 동적 키 생성
            form_key = f"add_size_{parent_key.replace('-', '_')}_{len(filtered_sizes)}"
            with st.form(form_key):
                new_key = st.text_input("키", placeholder="예: 20")
                new_description = st.text_input("제품명", placeholder="예: 20mm Category A-4")
                
                if st.form_submit_button("➕ Category A-4 추가"):
                    if new_key:
                        try:
                            st.info(f"🔄 추가 시도: '{new_key}' (parent: {parent_key})")
                            success = config_manager.add_hr_component(
                                'size', parent_key, new_key, new_key, 
                                None, None, new_description
                            )
                            if success:
                                st.success(f"✅ Category A-4 '{new_key}'가 추가되었습니다!")
                                
                                # 제품 코드 자동 생성 및 등록
                                try:
                                    # parent_key에서 System Type, Product Type, Gate Type 추출
                                    parts = parent_key.split('-')
                                    if len(parts) == 3:
                                        system_type, product_type, gate_type = parts
                                        
                                        # System Type 코드 변환
                                        system_type_code = ""
                                        if system_type == "Valve":
                                            system_type_code = "VV"
                                        elif system_type == "Open":
                                            system_type_code = "OP"
                                        else:
                                            system_type_code = system_type[:2].upper()
                                        
                                        # 제품 코드 생성
                                        generated_code = f"HR-{system_type_code}-{product_type}-{gate_type}-{new_key}"
                                        
                                        # master_products에 자동 등록
                                        from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
                                        master_manager = SQLiteMasterProductManager()
                                        
                                        # 중복 체크
                                        existing_product = master_manager.get_product_by_code(generated_code)
                                        if not existing_product:
                                            import uuid
                                            import time
                                            timestamp = str(int(time.time()))[-6:]
                                            product_count = str(len(master_manager.get_all_products()) + 1).zfill(3)
                                            master_product_id = f"MP-HR-{timestamp}-{product_count}"
                                        
                                            # 기본 제품명 생성
                                            korean_base = "핫러너 밸브" if system_type == "Valve" else f"핫러너 {system_type}"
                                            default_korean = f"{korean_base} {product_type} {gate_type} {new_key}mm"
                                            default_english = f"Hot Runner {system_type} {product_type} {gate_type} {new_key}mm"
                                        
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
                                        
                                        result = master_manager.add_master_product(product_data)
                                        if result:
                                            st.success(f"🎯 **제품 코드 자동 생성:** `{generated_code}`")
                                            st.info("📋 HR 카테고리 목록에서 확인할 수 있습니다.")
                                        else:
                                            st.warning(f"⚠️ Category A-4는 추가되었지만 제품 코드 생성 실패: `{generated_code}`")
                                    else:
                                        st.info(f"ℹ️ 제품 코드 `{generated_code}`는 이미 존재합니다.")
                                        
                                except Exception as e:
                                    st.warning(f"⚠️ Category A-4는 추가되었지만 제품 코드 자동 생성 중 오류: {e}")
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Category A-4 '{new_key}' 추가 실패")
                        except Exception as e:
                            st.error(f"❌ 오류 발생: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                    else:
                        st.warning("키는 필수입니다.")




def manage_hr_level5_components(config_manager):
    """Category A-5 (Code)"""
    st.subheader("🔩 Category A-5 (Code)")
    
    # A-1~A-4 가로 배치 선택
    system_types = config_manager.get_hr_system_types()
    if not system_types:
        st.warning("먼저 Category A-1을 등록해주세요.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_system = st.selectbox("Category A-1", [""] + system_types, key="a5_system")
    
    with col2:
        if selected_system:
            product_types = config_manager.get_hr_product_types(selected_system)
            selected_product = st.selectbox("Category A-2", [""] + product_types, key="a5_product")
        else:
            selected_product = None
    
    with col3:
        if selected_system and selected_product:
            gate_types = config_manager.get_hr_gate_types(selected_system, selected_product)
            selected_gate = st.selectbox("Category A-3", [""] + gate_types, key="a5_gate")
        else:
            selected_gate = None
            
    with col4:
        if selected_system and selected_product and selected_gate:
            sizes = config_manager.get_hr_sizes(selected_system, selected_product, selected_gate)
            selected_size = st.selectbox("Category A-4", [""] + sizes, key="a5_size")
        else:
            selected_size = None
    
    if not (selected_system and selected_product and selected_gate and selected_size):
        return
    
    # 현재 선택된 조합의 A-5 목록
    parent_key = f"{selected_system}-{selected_product}-{selected_gate}-{selected_size}"
    level5_components = config_manager.get_hr_components_for_management('level5')
    filtered_level5 = [l5 for l5 in level5_components if l5.get('parent_component') == parent_key]
    
    if filtered_level5:
        st.write(f"**{parent_key}의 Category A-5:**")
        for l5 in filtered_level5:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                component_key = l5['component_key']
                description = l5.get('description', l5['component_name'])
                st.write(f"🔩 **{component_key}** - {description}")
            with col2:
                component_id = l5['component_id']
                if st.button("✏️", key=f"edit_l5_{component_id}", help="수정"):
                    st.session_state[f"editing_l5_{component_id}"] = True
            with col3:
                component_id = l5['component_id']
                if st.button("🗑️", key=f"delete_l5_{component_id}", help="완전삭제"):
                    if config_manager.delete_hr_component_permanently(l5['component_id']):
                        st.success("Category A-5가 완전 삭제되었습니다!")
                        st.rerun()
            
            # 수정 폼 표시
            if st.session_state.get(f"editing_l5_{component_id}", False):
                with st.expander("✏️ Category A-5 수정", expanded=True):
                    with st.form(f"edit_level5_{component_id}"):
                        new_key = st.text_input("키", value=l5['component_key'])
                        new_description = st.text_input("제품명", value=l5.get('description', ''))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 저장"):
                                if config_manager.update_hr_component(
                                    l5['component_id'], new_key, new_key, 
                                    None, None, new_description
                                ):
                                    st.success("Category A-5가 수정되었습니다!")
                                    del st.session_state[f"editing_l5_{component_id}"]
                                    st.rerun()
                                else:
                                    st.error("수정 중 오류가 발생했습니다.")
                        with col_cancel:
                            if st.form_submit_button("❌ 취소"):
                                del st.session_state[f"editing_l5_{component_id}"]
                                st.rerun()
    
    # 새 A-5 추가
    with st.expander(f"➕ {parent_key}에 새 Category A-5 추가"):
        # 폼 리셋을 위한 동적 키 생성
        form_key = f"add_level5_{parent_key.replace('-', '_')}_{len(filtered_level5)}"
        with st.form(form_key):
            new_key = st.text_input("키", placeholder="예: TYPE1")
            new_description = st.text_input("제품명", placeholder="예: 타입1 Category A-5")
            
            if st.form_submit_button("➕ Category A-5 추가"):
                if new_key:
                    success = config_manager.add_hr_component(
                        'level5', parent_key, new_key, new_key, 
                        None, None, new_description
                    )
                    if success:
                        st.success(f"✅ Category A-5 '{new_key}'가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"❌ Category A-5 '{new_key}' 추가 실패")
                else:
                    st.warning("키는 필수입니다.")

def manage_hr_level6_components(config_manager):
    """Category A-6 (Code)"""
    st.subheader("⚙️ Category A-6 (Code)")
    
    # A-1~A-5 가로 배치 선택
    system_types = config_manager.get_hr_system_types()
    if not system_types:
        st.warning("먼저 Category A-1을 등록해주세요.")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        selected_system = st.selectbox("Category A-1", [""] + system_types, key="a6_system")
    
    with col2:
        if selected_system:
            product_types = config_manager.get_hr_product_types(selected_system)
            selected_product = st.selectbox("Category A-2", [""] + product_types, key="a6_product")
        else:
            selected_product = None
    
    with col3:
        if selected_system and selected_product:
            gate_types = config_manager.get_hr_gate_types(selected_system, selected_product)
            selected_gate = st.selectbox("Category A-3", [""] + gate_types, key="a6_gate")
        else:
            selected_gate = None
            
    with col4:
        if selected_system and selected_product and selected_gate:
            sizes = config_manager.get_hr_sizes(selected_system, selected_product, selected_gate)
            selected_size = st.selectbox("Category A-4", [""] + sizes, key="a6_size")
        else:
            selected_size = None
    
    with col5:
        if selected_system and selected_product and selected_gate and selected_size:
            level5_components = config_manager.get_hr_components_for_management('level5')
            level5_parent_key = f"{selected_system}-{selected_product}-{selected_gate}-{selected_size}"
            filtered_level5 = [l5 for l5 in level5_components if l5.get('parent_component') == level5_parent_key]
            level5_keys = [l5['component_key'] for l5 in filtered_level5]
            selected_level5 = st.selectbox("Category A-5", [""] + level5_keys, key="a6_level5") if level5_keys else None
        else:
            selected_level5 = None
    
    if not (selected_system and selected_product and selected_gate and selected_size and selected_level5):
        return
    
    # 현재 선택된 조합의 A-6 목록
    parent_key = f"{selected_system}-{selected_product}-{selected_gate}-{selected_size}-{selected_level5}"
    level6_components = config_manager.get_hr_components_for_management('level6')
    filtered_level6 = [l6 for l6 in level6_components if l6.get('parent_component') == parent_key]
    
    if filtered_level6:
        st.write(f"**{parent_key}의 Category A-6:**")
        for l6 in filtered_level6:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                component_key = l6['component_key']
                description = l6.get('description', l6['component_name'])
                st.write(f"⚙️ **{component_key}** - {description}")
            with col2:
                component_id = l6['component_id']
                if st.button("✏️", key=f"edit_l6_{component_id}", help="수정"):
                    st.session_state[f"editing_l6_{component_id}"] = True
            with col3:
                component_id = l6['component_id']
                if st.button("🗑️", key=f"delete_l6_{component_id}", help="완전삭제"):
                    if config_manager.delete_hr_component_permanently(l6['component_id']):
                        st.success("Category A-6이 완전 삭제되었습니다!")
                        st.rerun()
            
            # 수정 폼 표시
            if st.session_state.get(f"editing_l6_{component_id}", False):
                with st.expander("✏️ Category A-6 수정", expanded=True):
                    with st.form(f"edit_level6_{component_id}"):
                        new_key = st.text_input("키", value=l6['component_key'])
                        new_description = st.text_input("제품명", value=l6.get('description', ''))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 저장"):
                                if config_manager.update_hr_component(
                                    l6['component_id'], new_key, new_key, 
                                    None, None, new_description
                                ):
                                    st.success("Category A-6이 수정되었습니다!")
                                    del st.session_state[f"editing_l6_{component_id}"]
                                    st.rerun()
                                else:
                                    st.error("수정 중 오류가 발생했습니다.")
                        with col_cancel:
                            if st.form_submit_button("❌ 취소"):
                                del st.session_state[f"editing_l6_{component_id}"]
                                st.rerun()
    
    # 새 A-6 추가
    with st.expander(f"➕ {parent_key}에 새 Category A-6 추가"):
        # 폼 리셋을 위한 동적 키 생성
        form_key = f"add_level6_{parent_key.replace('-', '_')}_{len(filtered_level6)}"
        with st.form(form_key):
            new_key = st.text_input("키", placeholder="예: SUB1")
            new_description = st.text_input("제품명", placeholder="예: 서브타입1 Category A-6")
            
            if st.form_submit_button("➕ Category A-6 추가"):
                if new_key:
                    success = config_manager.add_hr_component(
                        'level6', parent_key, new_key, new_key, 
                        None, None, new_description
                    )
                    if success:
                        st.success(f"✅ Category A-6 '{new_key}'가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"❌ Category A-6 '{new_key}' 추가 실패")
                else:
                    st.warning("키는 필수입니다.")

def manage_general_category(multi_manager, category_type):
    """Category B~G 구성 요소 관리 (Category A와 완전히 동일한 구조)"""
    st.subheader(f"🏗️ Category {category_type}")
    
    # 세션 상태 초기화 (Category A와 동일)
    if f'{category_type.lower()}_component_tab' in st.session_state:
        del st.session_state[f'{category_type.lower()}_component_tab']
    if f'{category_type.lower()}_settings_tab' in st.session_state:
        del st.session_state[f'{category_type.lower()}_settings_tab']
    
    # Category 구성 요소 관리 탭 (Category A와 완전히 동일한 6단계)
    hr_tabs = st.tabs([
        f"🔧 Category {category_type}-1 (Product)", 
        f"📋 Category {category_type}-2 (Code)", 
        f"🚪 Category {category_type}-3 (Code)", 
        f"📏 Category {category_type}-4 (Code)",
        f"🔩 Category {category_type}-5 (Code)",
        f"⚙️ Category {category_type}-6 (Code)"
    ])
    
    with hr_tabs[0]:
        manage_multi_category_level(multi_manager, category_type, 'level1', f"Category {category_type}-1 (Product)", "🔧")
    with hr_tabs[1]:
        manage_multi_category_level(multi_manager, category_type, 'level2', f"Category {category_type}-2 (Code)", "📋")
    with hr_tabs[2]:
        manage_multi_category_level(multi_manager, category_type, 'level3', f"Category {category_type}-3 (Code)", "🚪")
    with hr_tabs[3]:
        manage_multi_category_level(multi_manager, category_type, 'level4', f"Category {category_type}-4 (Code)", "📏")
    with hr_tabs[4]:
        manage_multi_category_level(multi_manager, category_type, 'level5', f"Category {category_type}-5 (Code)", "🔩")
    with hr_tabs[5]:
        manage_multi_category_level(multi_manager, category_type, 'level6', f"Category {category_type}-6 (Code)", "⚙️")

def manage_multi_category_level(multi_manager, category_type, level, title, icon):
    """Multi-Category Level 관리 (Category A와 동일한 패턴)"""
    st.subheader(f"{icon} {title}")
    
    # Level에 따른 부모 선택 로직
    if level == 'level1':
        # Level 1은 부모가 없음
        parent_component = None
        manage_level_components(multi_manager, category_type, level, parent_component, title, icon)
    else:
        # Level 2~6은 상위 레벨 선택 필요
        parent_level = get_parent_level(level)
        # Level 2의 경우 parent_component 없이 조회, Level 3이상은 계층적 확인 필요
        if level == 'level2':
            parent_components = multi_manager.get_components_by_level(category_type, parent_level)
        else:
            # Level 3이상은 최소한 level1이 있는지만 확인
            level1_components = multi_manager.get_components_by_level(category_type, 'level1')
            if not level1_components:
                st.warning(f"먼저 {category_type}-1을 등록해주세요.")
                return
            parent_components = level1_components  # 일단 level1이 있으면 진행
        
        if not parent_components:
            st.warning(f"먼저 {category_type}-{get_level_number(parent_level)}을 등록해주세요.")
            return
        
        # 상위 레벨들의 계층적 선택
        selected_parents = select_parent_hierarchy(multi_manager, category_type, level)
        if not selected_parents:
            return
            
        parent_key = '-'.join(selected_parents)
        manage_level_components(multi_manager, category_type, level, parent_key, title, icon)

def select_parent_hierarchy(multi_manager, category_type, target_level):
    """계층적 부모 선택"""
    levels = ['level1', 'level2', 'level3', 'level4', 'level5', 'level6']
    target_index = levels.index(target_level)
    selected_parents = []
    
    for i in range(target_index):
        current_level = levels[i]
        level_num = i + 1
        
        if i == 0:
            # Level 1
            components = multi_manager.get_components_by_level(category_type, current_level)
        else:
            # Level 2~5
            parent_key = '-'.join(selected_parents) if selected_parents else None
            components = multi_manager.get_components_by_level(category_type, current_level, parent_key)
        
        if not components:
            st.warning(f"먼저 {category_type}-{level_num}을 등록해주세요.")
            return None
        
        component_keys = [comp['component_key'] for comp in components]
        selected = st.selectbox(
            f"{category_type}-{level_num}", 
            [""] + component_keys, 
            key=f"{category_type}_{target_level}_select_{level_num}"
        )
        
        if not selected:
            return None
            
        selected_parents.append(selected)
    
    return selected_parents

def manage_level_components(multi_manager, category_type, level, parent_component, title, icon):
    """레벨 구성 요소 관리"""
    # 기존 구성 요소들 표시
    components = multi_manager.get_components_by_level(category_type, level, parent_component)
    
    if components:
        parent_display = f" ({parent_component})" if parent_component else ""
        st.write(f"**등록된 {title}{parent_display}:**")
        
        for comp in components:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{icon} **{comp['component_key']}** - {comp.get('description', comp['component_name'])}")
            with col2:
                component_id = comp.get('component_id', f"{comp['component_key']}_{parent_component or 'root'}")
                if st.button("✏️", key=f"edit_{category_type}_{level}_{component_id}_{comp['component_key']}", help="수정"):
                    st.session_state[f"editing_{category_type}_{level}_{component_id}"] = True
            with col3:
                if st.button("🗑️", key=f"delete_{category_type}_{level}_{component_id}_{comp['component_key']}", help="완전삭제"):
                    if multi_manager.delete_component_permanently(comp['component_id']):
                        st.success(f"{title}이 완전 삭제되었습니다!")
                        st.rerun()
            
            # 수정 폼 표시
            if st.session_state.get(f"editing_{category_type}_{level}_{component_id}", False):
                with st.expander(f"✏️ {title} 수정", expanded=True):
                    with st.form(f"edit_{category_type}_{level}_{component_id}_{comp['component_key']}"):
                        new_key = st.text_input("키", value=comp['component_key'])
                        new_description = st.text_input("제품명", value=comp.get('description', ''))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 저장"):
                                if multi_manager.update_component(comp['component_id'], new_key, new_key, new_description):
                                    st.success(f"{title}이 수정되었습니다!")
                                    del st.session_state[f"editing_{category_type}_{level}_{component_id}"]
                                    st.rerun()
                                else:
                                    st.error("수정 중 오류가 발생했습니다.")
                        with col_cancel:
                            if st.form_submit_button("❌ 취소"):
                                del st.session_state[f"editing_{category_type}_{level}_{component_id}"]
                                st.rerun()
    
    # 새 구성 요소 추가
    parent_display = f" {parent_component}에" if parent_component else ""
    with st.expander(f"➕{parent_display} 새 {title} 추가"):
        form_key = f"add_{category_type}_{level}_{parent_component or 'root'}"
        with st.form(form_key):
            new_key = st.text_input("키", placeholder="예: CODE1")
            new_description = st.text_input("제품명", placeholder=f"예: {title} 제품명")
            
            if st.form_submit_button(f"➕ {title} 추가"):
                if new_key:
                    if multi_manager.add_component(category_type, level, parent_component, new_key, new_key, new_description):
                        st.success(f"✅ {title} '{new_key}'가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"❌ {title} '{new_key}' 추가 실패")
                else:
                    st.warning("키는 필수입니다.")

def get_parent_level(level):
    """상위 레벨 반환"""
    level_map = {
        'level2': 'level1',
        'level3': 'level2',
        'level4': 'level3',
        'level5': 'level4',
        'level6': 'level5'
    }
    return level_map.get(level)

def get_level_number(level):
    """레벨 번호 반환"""
    level_map = {
        'level1': '1',
        'level2': '2',
        'level3': '3',
        'level4': '4',
        'level5': '5',
        'level6': '6'
    }
    return level_map.get(level)


