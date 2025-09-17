import streamlit as st
import pandas as pd
from datetime import datetime
import io
from utils.notification_helper import NotificationHelper

def show_supplier_page(supplier_manager, user_permissions, get_text):
    """공급업체 관리 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'supplier_management', get_text)
    
    # 알림 헬퍼 초기화
    notification = NotificationHelper()
    
    st.header(f"🏭 {get_text('supplier_management')}")
    
    # 탭 메뉴로 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        f"📋 {get_text('supplier_list')}",
        f"➕ {get_text('supplier_registration')}",
        f"✏️ {get_text('supplier_edit')}",
        f"📊 {get_text('supplier_statistics')}",
        f"📦 {get_text('bulk_operations')}",
        f"🔍 {get_text('supplier_search')}"
    ])
    
    with tab1:
        st.header(f"🏭 {get_text('supplier_list')}")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # customer_manager에서 국가 목록 가져오기
            try:
                customer_manager = st.session_state.get('customer_manager')
                if customer_manager:
                    all_locations = customer_manager.get_all_locations()
                    if len(all_locations) > 0 and 'country' in all_locations.columns:
                        countries = all_locations['country'].dropna().unique().tolist()
                        countries = [get_text("all_status")] + sorted(countries)
                    else:
                        countries = [get_text("all_status")]
                else:
                    countries = [get_text("all_status")]
            except Exception:
                countries = [get_text("all_status")]
                
            country_filter = st.selectbox(get_text("country_filter"), countries)
        
        with col2:
            # 공급업체 데이터에서 사업 유형 가져오기
            try:
                all_suppliers = supplier_manager.get_all_suppliers()
                if len(all_suppliers) > 0 and 'business_type' in all_suppliers.columns:
                    business_types = all_suppliers['business_type'].dropna().unique().tolist()
                    business_types = [get_text("all_status")] + sorted(business_types)
                else:
                    business_types = [get_text("all_status")]
            except Exception:
                business_types = [get_text("all_status")]
                
            business_type_filter = st.selectbox(get_text("business_type_filter"), business_types)
        with col3:
            search_term = st.text_input(get_text("search_company_contact"))
        
        # 필터 적용
        country_filter = None if country_filter == get_text("all_status") else country_filter
        business_type_filter = None if business_type_filter == get_text("all_status") else business_type_filter
        
        filtered_suppliers = supplier_manager.get_filtered_suppliers(
            country_filter=country_filter,
            business_type_filter=business_type_filter,
            search_term=search_term
        )
        
        if len(filtered_suppliers) > 0:
            # 실제 존재하는 컬럼만 표시
            available_columns = filtered_suppliers.columns.tolist()
            
            # 기본 표시 컬럼 (존재하는 경우에만)
            preferred_columns = [
                'supplier_id', 'company_name', 'contact_person', 'contact_phone',
                'contact_email', 'country', 'city', 'business_type', 'rating', 'status'
            ]
            
            # 실제 존재하는 컬럼만 필터링
            display_columns = [col for col in preferred_columns if col in available_columns]
            
            if not display_columns:
                # 기본 컬럼이 없으면 처음 10개 컬럼 표시
                display_columns = available_columns[:10]
            
            st.dataframe(
                filtered_suppliers[display_columns],
                use_container_width=True,
                hide_index=True
            )
            
            st.info(get_text("total_suppliers_found").format(count=len(filtered_suppliers)))
            
            # 데이터 다운로드
            if st.button("📥 검색 결과 다운로드"):
                csv_buffer = io.StringIO()
                filtered_suppliers.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="CSV 파일 다운로드",
                    data=csv_buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"suppliers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("조건에 맞는 공급업체가 없습니다.")
    
    
    with tab2:
        st.header("➕ 공급업체 등록")
        
        # 국가-도시 선택을 폼 밖에서 처리
        st.subheader("🌍 위치 정보")
        col_location1, col_location2 = st.columns(2)
        
        with col_location1:
            countries = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
            selected_country = st.selectbox("국가 *", countries, key="supplier_country_registration")
            
        with col_location2:
            # 국가 변경 시 도시 목록 업데이트
            if 'prev_supplier_country' not in st.session_state:
                st.session_state.prev_supplier_country = selected_country
            
            if st.session_state.prev_supplier_country != selected_country:
                st.session_state.prev_supplier_country = selected_country
                st.rerun()
            
            # 국가별 도시 목록 가져오기 (customer_manager 사용)
            try:
                customer_manager = st.session_state.customer_manager
                cities = customer_manager.get_cities_by_country(selected_country)
            except:
                cities = []
            city_options = ["직접 입력"] + cities if cities else ["직접 입력"]
            
            selected_city_option = st.selectbox("도시", city_options, key="supplier_city_registration")
            
            # 직접 입력인 경우
            if selected_city_option == "직접 입력":
                selected_city = st.text_input("도시명 직접 입력", placeholder="도시명을 입력하세요", key="supplier_city_manual")
            else:
                selected_city = selected_city_option
                st.info(f"선택된 도시: {selected_city}")
        
        # 공급업체 등록 폼
        with st.form("supplier_registration_form"):
            st.subheader("🏢 기본 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("회사명 *", help="정확한 회사명을 입력하세요")
                contact_person = st.text_input("담당자명", help="주요 연락 담당자")
                contact_phone = st.text_input("연락처", placeholder="010-1234-5678")
                contact_email = st.text_input("이메일", placeholder="contact@company.com")
            
            with col2:
                business_types = ["제조업", "무역업", "유통업", "서비스업", "IT", "기타"]
                business_type = st.selectbox("사업 유형", business_types)
                tax_id = st.text_input("사업자번호", placeholder="예: 123-45-67890")
                rating_options = ["★★★★★ (최우수)", "★★★★☆ (우수)", "★★★☆☆ (보통)", "★★☆☆☆ (개선필요)", "★☆☆☆☆ (부적합)"]
                rating = st.selectbox("공급업체 평가", rating_options, index=1)
            
            st.subheader("💰 거래 조건")
            col3, col4 = st.columns(2)
            
            with col3:
                payment_terms = st.text_input("결제 조건", value="NET 30", placeholder="예: NET 30, 현금, 60일")
                lead_time_days = st.number_input("리드타임 (일)", min_value=0, value=14)
                currencies = ["USD", "KRW", "VND", "THB", "CNY"]
                currency = st.selectbox("거래 통화", currencies)
            
            with col4:
                minimum_order_amount = st.number_input("최소 주문 금액", min_value=0.0, step=100.0)
                address = st.text_input("주소", placeholder="상세 주소를 입력하세요")
                
            st.subheader("📋 추가 정보")
            col5, col6 = st.columns(2)
            
            with col5:
                bank_info = st.text_area("은행 정보", placeholder="은행명 및 계좌번호")
                
            with col6:
                notes = st.text_area("비고", placeholder="추가 정보나 특이사항")
            
            submit_button = st.form_submit_button("🏭 공급업체 등록")
            
            if submit_button:
                if company_name and selected_country:
                    supplier_data = {
                        'company_name': company_name,
                        'contact_person': contact_person,
                        'contact_phone': contact_phone,
                        'contact_email': contact_email,
                        'address': address,
                        'country': selected_country,
                        'city': selected_city,
                        'business_type': business_type,
                        'tax_id': tax_id,
                        'bank_info': bank_info,
                        'payment_terms': payment_terms,
                        'lead_time_days': lead_time_days,
                        'minimum_order_amount': minimum_order_amount,
                        'currency': currency,
                        'rating': rating,
                        'notes': notes
                    }
                    
                    if supplier_manager.add_supplier(supplier_data):
                        st.success(f"공급업체 '{company_name}'이 성공적으로 등록되었습니다!")
                        st.rerun()
                    else:
                        st.error("공급업체 등록에 실패했습니다. 이미 등록된 회사명인지 확인해주세요.")
                else:
                    st.error("필수 항목(회사명, 국가)을 모두 입력해주세요.")
    
    
    with tab3:
        st.header("✏️ 공급업체 수정")
        
        can_delete = user_permissions.get('can_delete_data', False)
        
        all_suppliers = supplier_manager.get_all_suppliers()
        
        if len(all_suppliers) > 0:
            # 공급업체 선택
            supplier_options = all_suppliers['supplier_id'].tolist()
            supplier_labels = [f"{row['company_name']} ({row['supplier_id']})" 
                             for _, row in all_suppliers.iterrows()]
            
            selected_supplier_id = st.selectbox(
                "수정할 공급업체 선택",
                options=supplier_options,
                format_func=lambda x: next(label for i, label in enumerate(supplier_labels) 
                                         if supplier_options[i] == x)
            )
            
            if selected_supplier_id:
                supplier_data = supplier_manager.get_supplier_by_id(selected_supplier_id)
                
                if supplier_data:
                    # 국가-도시 선택을 폼 밖에서 처리
                    st.subheader("🌍 위치 정보 수정")
                    col_location1, col_location2 = st.columns(2)
                    
                    with col_location1:
                        countries = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
                        current_country = supplier_data.get('country', '한국')
                        country_index = countries.index(current_country) if current_country in countries else 0
                        selected_country_edit = st.selectbox("국가 *", countries, index=country_index, key=f"supplier_country_edit_{selected_supplier_id}")
                        
                    with col_location2:
                        # 국가 변경 시 도시 목록 업데이트
                        if f'prev_supplier_country_edit_{selected_supplier_id}' not in st.session_state:
                            st.session_state[f'prev_supplier_country_edit_{selected_supplier_id}'] = selected_country_edit
                        
                        if st.session_state[f'prev_supplier_country_edit_{selected_supplier_id}'] != selected_country_edit:
                            st.session_state[f'prev_supplier_country_edit_{selected_supplier_id}'] = selected_country_edit
                            st.rerun()
                        
                        # 국가별 도시 목록 가져오기 (customer_manager 사용)
                        try:
                            customer_manager = st.session_state.customer_manager
                            cities = customer_manager.get_cities_by_country(selected_country_edit)
                        except:
                            cities = []
                        city_options = ["직접 입력"] + cities if cities else ["직접 입력"]
                        
                        current_city = supplier_data.get('city', '')
                        
                        # 현재 도시가 목록에 있는지 확인
                        if current_city in cities:
                            city_index = city_options.index(current_city)
                        else:
                            city_index = 0  # "직접 입력" 선택
                        
                        selected_city_option_edit = st.selectbox("도시", city_options, index=city_index, key=f"supplier_city_edit_{selected_supplier_id}")
                        
                        # 직접 입력인 경우
                        if selected_city_option_edit == "직접 입력":
                            selected_city_edit = st.text_input("도시명 직접 입력", value=current_city, placeholder="도시명을 입력하세요", key=f"supplier_city_manual_edit_{selected_supplier_id}")
                        else:
                            selected_city_edit = selected_city_option_edit
                            st.info(f"선택된 도시: {selected_city_edit}")
                    
                    # 공급업체 수정 폼
                    with st.form("supplier_update_form"):
                        st.subheader("🏢 기본 정보")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            company_name = st.text_input("회사명 *", value=supplier_data.get('company_name', ''))
                            contact_person = st.text_input("담당자명", value=supplier_data.get('contact_person', ''))
                            contact_phone = st.text_input("연락처", value=supplier_data.get('contact_phone', ''))
                            contact_email = st.text_input("이메일", value=supplier_data.get('contact_email', ''))
                        
                        with col2:
                            
                            business_types = ["제조업", "무역업", "유통업", "서비스업", "IT", "기타"]
                            business_type_index = business_types.index(supplier_data.get('business_type', '제조업')) if supplier_data.get('business_type') in business_types else 0
                            business_type = st.selectbox("사업 유형", business_types, index=business_type_index)
                            
                            tax_id = st.text_input("사업자번호", value=supplier_data.get('tax_id', ''))
                        
                        st.subheader("거래 조건")
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            payment_terms = st.text_input("결제 조건", value=supplier_data.get('payment_terms', 'NET 30'))
                            # NaN 값 안전 처리
                            lead_time_value = supplier_data.get('lead_time_days', 14)
                            try:
                                lead_time_default = int(float(lead_time_value)) if pd.notna(lead_time_value) else 14
                            except (ValueError, TypeError):
                                lead_time_default = 14
                            lead_time_days = st.number_input("리드타임 (일)", min_value=0, value=lead_time_default)
                            currencies = ["USD", "KRW", "VND", "THB", "CNY"]
                            currency_index = currencies.index(supplier_data.get('currency', 'USD')) if supplier_data.get('currency') in currencies else 0
                            currency = st.selectbox("거래 통화", currencies, index=currency_index)
                        
                        with col4:
                            minimum_order_amount = st.number_input("최소 주문 금액", min_value=0.0, step=100.0,
                                                                value=float(supplier_data.get('minimum_order_amount', 0)))
                            rating_options = [1.0, 2.0, 3.0, 4.0, 5.0]
                            rating_index = rating_options.index(float(supplier_data.get('rating', 3.0))) if float(supplier_data.get('rating', 3.0)) in rating_options else 2
                            rating = st.selectbox("평점", rating_options, index=rating_index)
                        
                        st.subheader("추가 정보")
                        address = st.text_area("주소", value=supplier_data.get('address', ''))
                        bank_info = st.text_area("은행 정보", value=supplier_data.get('bank_info', ''))
                        notes = st.text_area("비고", value=supplier_data.get('notes', ''))
                        
                        status_options = ["활성", "비활성"]
                        status_index = status_options.index(supplier_data.get('status', '활성')) if supplier_data.get('status') in status_options else 0
                        status = st.selectbox("상태", status_options, index=status_index)
                        
                        # 버튼들
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            update_clicked = st.form_submit_button("공급업체 정보 수정", use_container_width=True)
                        
                        with col_btn2:
                            delete_clicked = st.form_submit_button(
                                "공급업체 삭제", 
                                disabled=not can_delete,
                                use_container_width=True
                            )
                        
                        if update_clicked:
                            if company_name and selected_country_edit:
                                updated_supplier = {
                                    'company_name': company_name,
                                    'contact_person': contact_person,
                                    'contact_phone': contact_phone,
                                    'contact_email': contact_email,
                                    'address': address,
                                    'country': selected_country_edit,
                                    'city': selected_city_edit,
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
                                
                                if supplier_manager.update_supplier(selected_supplier_id, updated_supplier):
                                    st.success(f"공급업체 '{company_name}' 정보가 성공적으로 수정되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("공급업체 정보 수정에 실패했습니다.")
                            else:
                                st.error("필수 항목(회사명, 국가)을 모두 입력해주세요.")
                        
                        if delete_clicked:
                            if supplier_manager.delete_supplier(selected_supplier_id):
                                st.success(f"공급업체 '{supplier_data.get('company_name')}'이 성공적으로 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("공급업체 삭제에 실패했습니다.")
                else:
                    st.error("선택된 공급업체의 데이터를 찾을 수 없습니다.")
        else:
            st.warning("등록된 공급업체가 없습니다.")
    
    
    with tab4:
        st.header("📊 공급업체 통계")
        
        try:
            stats = supplier_manager.get_supplier_statistics()
            
            if stats:
                # 기본 통계
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("총 공급업체 수", stats['total_suppliers'])
                
                with col2:
                    st.metric("활성 공급업체", stats['active_suppliers'])
                
                with col3:
                    st.metric("국가 수", stats['countries'])
                
                with col4:
                    st.metric("평균 평점", f"{stats['average_rating']:.1f}")
                
                # 차트
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("국가별 분포")
                    if stats['country_distribution']:
                        country_df = pd.DataFrame.from_dict(
                            stats['country_distribution'],
                            orient='index'
                        )
                        country_df.columns = ['공급업체 수']
                        country_df.index.name = '국가'
                        st.bar_chart(country_df)
                    else:
                        st.info("국가별 데이터가 없습니다.")
                
                with col_right:
                    st.subheader("사업 유형별 분포")
                    if stats['business_type_distribution']:
                        business_df = pd.DataFrame.from_dict(
                            stats['business_type_distribution'],
                            orient='index'
                        )
                        business_df.columns = ['공급업체 수']
                        business_df.index.name = '사업 유형'
                        st.bar_chart(business_df)
                    else:
                        st.info("사업 유형별 데이터가 없습니다.")
                
                # 평점 분포
                if stats['rating_distribution']:
                    st.subheader("평점 분포")
                    rating_df = pd.DataFrame.from_dict(
                        stats['rating_distribution'],
                        orient='index'
                    )
                    rating_df.columns = ['공급업체 수']
                    rating_df.index.name = '평점'
                    st.bar_chart(rating_df)
            else:
                st.warning("통계 데이터를 불러올 수 없습니다.")
                
        except Exception as e:
            st.error(f"통계 조회 중 오류가 발생했습니다: {e}")
    
    
    with tab5:
        st.header("📤 대량 작업")
        
        tab1, tab2 = st.tabs(["대량 등록", "대량 다운로드"])
        
        with tab1:
            st.subheader("CSV 파일로 공급업체 대량 등록")
            
            st.info("CSV 파일을 사용하여 여러 공급업체를 한 번에 등록할 수 있습니다.")
            
            # 템플릿 다운로드
            if st.button("📥 공급업체 등록 템플릿 다운로드"):
                template_data = pd.DataFrame({
                    'company_name': ['샘플 공급업체'],
                    'contact_person': ['홍길동'],
                    'contact_phone': ['010-1234-5678'],
                    'contact_email': ['contact@supplier.com'],
                    'address': ['서울시 강남구'],
                    'country': ['한국'],
                    'city': ['서울'],
                    'business_type': ['제조업'],
                    'tax_id': ['123-45-67890'],
                    'bank_info': ['국민은행 123-456-789'],
                    'payment_terms': ['NET 30'],
                    'lead_time_days': [14],
                    'minimum_order_amount': [1000.0],
                    'currency': ['USD'],
                    'rating': [3.0],
                    'notes': ['비고사항']
                })
                
                csv_buffer = io.StringIO()
                template_data.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="템플릿 파일 다운로드",
                    data=csv_buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"supplier_template_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            # 파일 업로드
            uploaded_file = st.file_uploader("CSV 파일 선택", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                    st.success("파일이 성공적으로 업로드되었습니다!")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("대량 등록 처리"):
                        suppliers_data = df.to_dict('records')
                        results = supplier_manager.bulk_add_suppliers(suppliers_data)
                        
                        st.subheader("처리 결과")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("추가됨", results['added'])
                        
                        with col2:
                            st.metric("업데이트됨", results['updated'])
                        
                        with col3:
                            st.metric("오류", len(results['errors']))
                        
                        if results['errors']:
                            with st.expander("오류 상세"):
                                for error in results['errors']:
                                    st.error(error)
                        
                        st.success("대량 처리가 완료되었습니다!")
                
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        
        with tab2:
            st.subheader("공급업체 데이터 대량 다운로드")
            
            all_suppliers = supplier_manager.get_all_suppliers()
            
            if len(all_suppliers) > 0:
                st.info(f"총 {len(all_suppliers)}개의 공급업체 데이터를 다운로드할 수 있습니다.")
                
                if st.button("📥 전체 공급업체 데이터 다운로드"):
                    csv_buffer = io.StringIO()
                    all_suppliers.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="CSV 파일 다운로드",
                        data=csv_buffer.getvalue().encode('utf-8-sig'),
                        file_name=f"all_suppliers_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("다운로드할 공급업체 데이터가 없습니다.")
    
    with tab6:
        st.header("🔍 공급업체 검색")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("회사명/담당자 검색", placeholder="검색어를 입력하세요")
        
        with col2:
            # customer_manager에서 국가 목록 가져오기 (tab1과 동일한 방식)
            try:
                customer_manager = st.session_state.get('customer_manager')
                if customer_manager:
                    all_locations = customer_manager.get_all_locations()
                    if len(all_locations) > 0 and 'country' in all_locations.columns:
                        countries = all_locations['country'].dropna().unique().tolist()
                        countries = sorted(countries)
                    else:
                        countries = []
                else:
                    countries = []
            except Exception:
                countries = []
                
            country_filter = st.selectbox("국가별 필터", ["전체"] + countries, key="search_country_filter")
        
        with col3:
            # 공급업체 데이터에서 사업 유형 가져오기 (tab1과 동일한 방식)
            try:
                all_suppliers = supplier_manager.get_all_suppliers()
                if len(all_suppliers) > 0 and 'business_type' in all_suppliers.columns:
                    business_types = all_suppliers['business_type'].dropna().unique().tolist()
                    business_types = sorted(business_types)
                else:
                    business_types = []
            except Exception:
                business_types = []
                
            business_type
    
    # 하단 네비게이션 버튼  
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🏢 영업 관리로 이동", use_container_width=True, type="secondary"):
            st.session_state['selected_system'] = 'sales_management'
            st.rerun()
