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
    catalog_tabs = st.tabs(["📝 등록된 코드 설명", "📋 카테고리별 테이블 조회", "📊 데이터 관리"])
    
    with catalog_tabs[0]:
        # 등록된 코드 설명 표시
        show_registered_codes(config_manager, multi_manager)
    
    with catalog_tabs[1]:
        # 카테고리별 테이블 조회 (Category A~I)
        show_category_table_query_section(config_manager, multi_manager)
    
    with catalog_tabs[2]:
        # 데이터 관리 섹션
        show_data_management_section(config_manager, multi_manager)

def show_data_management_section(config_manager, multi_manager):
    """데이터 관리 섹션 - CSV 다운로드/업로드"""
    st.subheader("📊 데이터 관리")
    st.caption("카테고리별 CSV 다운로드 및 업로드를 통한 데이터 백업/복원")
    
    # 데이터 관리 탭 구성
    data_tabs = st.tabs(["📥 데이터 다운로드", "📤 데이터 업로드"])
    
    with data_tabs[0]:
        show_csv_download_section()
    
    with data_tabs[1]:
        show_csv_upload_section()

def show_csv_download_section():
    """CSV 다운로드 섹션"""
    st.markdown("### 📥 카테고리별 데이터 다운로드")
    
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    
    # 전체 다운로드
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 모든 카테고리 다운로드", use_container_width=True, type="primary"):
            download_all_categories()
    
    with col2:
        st.info("모든 카테고리 데이터를 ZIP 파일로 다운로드합니다.")
    
    st.markdown("---")
    
    # 개별 카테고리 다운로드
    st.markdown("#### 개별 카테고리 다운로드")
    
    # 3열로 카테고리 버튼 배치
    cols = st.columns(3)
    
    for i, category in enumerate(categories):
        with cols[i % 3]:
            if st.button(f"📋 Category {category}", key=f"download_{category}", use_container_width=True):
                download_category_csv(category)

def show_csv_upload_section():
    """CSV 업로드 섹션"""
    st.markdown("### 📤 카테고리별 데이터 업로드")
    
    st.warning("⚠️ 업로드 시 해당 카테고리의 기존 데이터가 모두 삭제됩니다.")
    
    # 카테고리 선택
    selected_category = st.selectbox(
        "업로드할 카테고리 선택",
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
        help="업로드할 데이터의 카테고리를 선택하세요"
    )
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        f"Category {selected_category} CSV 파일 선택",
        type=['csv'],
        help="CSV 파일을 선택해주세요. 기존 데이터 구조와 동일해야 합니다."
    )
    
    if uploaded_file is not None:
        # CSV 미리보기
        try:
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            
            st.markdown(f"#### 📋 {uploaded_file.name} 미리보기")
            st.dataframe(df.head(10), use_container_width=True)
            st.info(f"총 {len(df)}개의 레코드가 포함되어 있습니다.")
            
            # 데이터 검증
            if validate_csv_structure(df, selected_category):
                st.success("✅ CSV 파일 구조가 올바릅니다.")
                
                # 업로드 확인
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button(
                        f"🔄 Category {selected_category} 데이터 교체", 
                        type="primary", 
                        use_container_width=True
                    ):
                        if upload_category_csv(df, selected_category):
                            st.success(f"Category {selected_category} 데이터가 성공적으로 업데이트되었습니다!")
                            st.rerun()
                        else:
                            st.error("데이터 업로드 중 오류가 발생했습니다.")
            else:
                st.error("❌ CSV 파일 구조가 올바르지 않습니다. 올바른 형식의 파일을 업로드해주세요.")
                
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")

def download_category_csv(category):
    """특정 카테고리 CSV 다운로드"""
    postgres_manager = BasePostgreSQLManager()
    conn = None
    try:
        import pandas as pd
        from datetime import datetime
        import io
        
        conn = postgres_manager.get_connection()
        
        # 모든 카테고리가 multi_category_components 테이블 사용 (통일됨)
        query = """
            SELECT * FROM multi_category_components 
            WHERE category_type = %s
            ORDER BY component_level, component_key
        """
        
        df = pd.read_sql_query(query, conn, params=(category,))
        
        if df.empty:
            st.warning(f"Category {category}에 다운로드할 데이터가 없습니다.")
            return
        
        # CSV 파일 생성
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_data = csv_buffer.getvalue()
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Category_{category}_{timestamp}.csv"
        
        st.download_button(
            label=f"💾 {filename} 다운로드",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
        st.success(f"Category {category} 데이터 ({len(df)}개 레코드)가 준비되었습니다.")
        
    except Exception as e:
        st.error(f"다운로드 오류: {str(e)}")
    finally:
        if conn and postgres_manager:
            postgres_manager.close_connection(conn)

def download_all_categories():
    """모든 카테고리 ZIP 파일로 다운로드"""
    postgres_manager = BasePostgreSQLManager()
    conn = None
    try:
        import pandas as pd
        import zipfile
        import io
        from datetime import datetime
        
        conn = postgres_manager.get_connection()
        
        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Category A~I 모두 multi_category_components에서
            for category in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                query = """
                    SELECT * FROM multi_category_components 
                    WHERE category_type = %s
                    ORDER BY component_level, component_key
                """
                df = pd.read_sql_query(query, conn, params=(category,))
                if not df.empty:
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f'Category_{category}.csv', csv_data)
        
        # ZIP 파일 다운로드
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"All_Categories_{timestamp}.zip"
        
        zip_buffer.seek(0)
        st.download_button(
            label=f"📦 {filename} 다운로드",
            data=zip_buffer.getvalue(),
            file_name=filename,
            mime="application/zip",
            use_container_width=True
        )
        
        st.success("모든 카테고리 데이터가 ZIP 파일로 준비되었습니다.")
        
    except Exception as e:
        st.error(f"전체 다운로드 오류: {str(e)}")
    finally:
        if conn and postgres_manager:
            postgres_manager.close_connection(conn)

def validate_csv_structure(df, category):
    """CSV 파일 구조 검증"""
    try:
        # multi_category_components 구조 검증 (모든 카테고리 통일)
        required_columns = [
            'component_id', 'category_type', 'component_level', 
            'parent_component', 'component_key', 'component_name', 'is_active'
        ]
        
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"필수 컬럼 누락: {', '.join(missing_columns)}")
            return False
        
        # 데이터 타입 기본 검증
        if df.empty:
            st.error("CSV 파일이 비어있습니다.")
            return False
        
        return True
        
    except Exception as e:
        st.error(f"구조 검증 오류: {str(e)}")
        return False

def upload_category_csv(df, category):
    """카테고리 CSV 데이터 업로드"""
    postgres_manager = BasePostgreSQLManager()
    conn = None
    try:
        conn = postgres_manager.get_connection()
        cursor = conn.cursor()
        
        # 기존 데이터 삭제 (모든 카테고리가 multi_category_components 사용)
        cursor.execute("DELETE FROM multi_category_components WHERE category_type = %s", (category,))
        
        # 새 데이터 삽입
        table_name = 'multi_category_components'
        
        # DataFrame to 데이터베이스 삽입
        for _, row in df.iterrows():
            columns = list(row.index)
            values = list(row.values)
            
            # NULL 값 처리
            processed_values = []
            for val in values:
                if pd.isna(val) or val == '' or val == 'NULL':
                    processed_values.append(None)
                else:
                    processed_values.append(val)
            
            placeholders = ', '.join(['%s'] * len(processed_values))
            column_names = ', '.join(columns)
            
            insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            cursor.execute(insert_query, processed_values)
        
        conn.commit()
        return True
        
    except Exception as e:
        st.error(f"업로드 오류: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn and postgres_manager:
            postgres_manager.close_connection(conn)
            
def show_category_table_query_section(config_manager, multi_manager):
    """카테고리별 테이블 조회 섹션"""
    
    # Category 선택 필터
    col1, col2 = st.columns([1, 3])
    
    with col1:
        categories = ["Category A", "Category B", "Category C", "Category D", "Category E", "Category F", "Category G", "Category H", "Category I"]
        selected_category = st.selectbox("📋 카테고리 선택", categories)
    
    with col2:
        st.info(f"선택된 카테고리: **{selected_category}**")
    
    postgres_manager = BasePostgreSQLManager()
    conn = None
    try:
        import pandas as pd
        
        conn = postgres_manager.get_connection()
        
        # 선택된 카테고리에 따른 테이블 및 쿼리 설정
        category_letter = selected_category.split()[-1]  # "Category A" -> "A"
        
        # 모든 카테고리가 multi_category_components 테이블 사용 (통일됨)
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
              AND l1.is_active IS TRUE AND l2.is_active IS TRUE AND l3.is_active IS TRUE AND l4.is_active IS TRUE AND l5.is_active IS TRUE AND l6.is_active IS TRUE
        '''
        
        df = pd.read_sql_query(query, conn)
        
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
            # Category의 활성화 상태 확인
            config = multi_manager.get_category_config(category_letter)
            if not config or not config['is_enabled']:
                st.warning(f"{selected_category}는 비활성화 상태입니다. Category 관리에서 활성화해주세요.")
            else:
                st.info("완성된 코드가 없습니다. 6단계 구성 요소가 모두 등록되어야 완성된 코드가 생성됩니다.")
            
    except Exception as e:
        st.error(f"테이블 조회 중 오류가 발생했습니다: {e}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        if conn and postgres_manager:
            postgres_manager.close_connection(conn)

def show_category_management_tabs(config_manager, multi_manager):
    """Category 관리 탭들"""
    
    # Category 탭 구성
    tabs = st.tabs([
        "📁 Category A", "📁 Category B", "📁 Category C", 
        "📁 Category D", "📁 Category E", "📁 Category F", 
        "📁 Category G", "📁 Category H", "📁 Category I"
    ])
    
    with tabs[0]:  # Category A
        manage_general_category(multi_manager, 'A')
    
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
    
    postgres_manager = BasePostgreSQLManager()
    conn = None
    try:
        import pandas as pd
        
        conn = postgres_manager.get_connection()
        cursor = conn.cursor()
        
        # 하위 카테고리 컬럼명
        sub_categories = ["Product", "Category 1", "Category 2", "Category 3", "Category 4", "Category 5", "Category 6"]
        
        # 메인 카테고리별 데이터 생성
        main_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        data_rows = []
        
        for main_cat in main_categories:
            row_data = [f"Category {main_cat}"]
            
            # 모든 카테고리가 multi_category_components 테이블 사용 (통일됨)
            level_names = ["level1", "level2", "level3", "level4", "level5", "level6"]
            
            # Product 컬럼: Level1의 설명 표시
            try:
                cursor.execute('''
                    SELECT DISTINCT COALESCE(description, component_name, component_key)
                    FROM multi_category_components 
                    WHERE category_type = %s AND component_level = 'level1' AND is_active IS TRUE
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
                        WHERE category_type = %s AND component_level = %s AND is_active IS TRUE
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
    finally:
        if conn and postgres_manager:
            postgres_manager.close_connection(conn)

def manage_general_category(multi_manager, category_type):
    """Category A~I 구성 요소 관리 (모든 카테고리 동일한 구조)"""
    st.subheader(f"🏗️ Category {category_type}")
    
    # 세션 상태 초기화
    if f'{category_type.lower()}_component_tab' in st.session_state:
        del st.session_state[f'{category_type.lower()}_component_tab']
    if f'{category_type.lower()}_settings_tab' in st.session_state:
        del st.session_state[f'{category_type.lower()}_settings_tab']
    
    # Category 구성 요소 관리 탭 (모든 카테고리 동일한 6단계)
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
    """Multi-Category Level 관리 (모든 카테고리 동일한 패턴)"""
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
        'level1': 1,
        'level2': 2,
        'level3': 3,
        'level4': 4,
        'level5': 5,
        'level6': 6
    }
    return level_map.get(level, 1)
