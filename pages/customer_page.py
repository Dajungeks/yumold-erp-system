import streamlit as st
import pandas as pd
from datetime import datetime
import io
from notification_helper import NotificationHelper
from utils.display_helper import display_customer_table

# 알림 헬퍼 인스턴스 생성
notify = NotificationHelper()

def show_customer_page(customer_manager, user_permissions, get_text):
    """고객 관리 페이지 - 탭 기반 UI"""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'customer_management', get_text)
    
    # 탭 생성
    tab_names = [
        f"📋 {get_text('customer_list')}", 
        f"➕ {get_text('customer_registration')}", 
        f"✏️ {get_text('customer_edit')}", 
        f"📊 {get_text('customer_statistics')}", 
        f"🔄 {get_text('bulk_operations')}"
    ]
    
    # 탭 컨테이너 생성
    tabs = st.tabs(tab_names)
    
    # 각 탭의 내용 구현
    with tabs[0]:  # 고객 목록
        show_customer_list(customer_manager, get_text)
    
    with tabs[1]:  # 고객 등록
        show_customer_registration(customer_manager, get_text)
    
    with tabs[2]:  # 고객 편집
        show_customer_edit(customer_manager, get_text)
    
    with tabs[3]:  # 고객 통계
        show_customer_statistics(customer_manager, get_text)
    
    with tabs[4]:  # 대량 등록
        show_customer_bulk_registration(customer_manager, get_text)

def show_customer_list(customer_manager, get_text=lambda x: x):
    """고객 목록 표시"""
    st.header(f"📋 {get_text('customer_list')}")
    
    # 필터링 옵션
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        countries = customer_manager.get_countries()
        country_filter = st.selectbox(get_text("country_filter"), [get_text("all_status")] + countries)
    
    with col2:
        business_types = [get_text("all_status")] + [get_text("business_types_mold"), get_text("business_types_injection"), 
                                                      get_text("business_types_mold_injection"), get_text("business_types_t1"), 
                                                      get_text("business_types_brand"), get_text("business_types_trade"), get_text("business_types_other")]
        business_type_filter = st.selectbox(get_text("business_type_filter"), business_types)
    
    with col3:
        # 도시 필터 추가
        all_customers_data = customer_manager.get_all_customers()
        if len(all_customers_data) > 0:
            all_customers_df = pd.DataFrame(all_customers_data)
            if country_filter != get_text("all_status"):
                cities_in_country = all_customers_df[all_customers_df['country'] == country_filter]['city'].dropna().unique().tolist()
                cities = [get_text("all_status")] + sorted(cities_in_country)
            else:
                cities = [get_text("all_status")] + sorted(all_customers_df['city'].dropna().unique().tolist())
        else:
            cities = [get_text("all_status")]
        city_filter = st.selectbox(get_text("city_filter"), cities)
    
    with col4:
        search_term = st.text_input(get_text("search_company_contact"), placeholder=get_text("enter_search_term"))
    
    # 필터 적용
    if len(all_customers_data) > 0:
        filtered_df = pd.DataFrame(all_customers_data).copy()
    else:
        filtered_df = pd.DataFrame()
    
    # 국가 필터
    if country_filter != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['country'] == country_filter]
    
    # 사업 유형 필터
    if business_type_filter != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['business_type'] == business_type_filter]
    
    # 도시 필터
    if city_filter != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['city'] == city_filter]
    
    # 검색어 필터
    if search_term and search_term.strip():
        search_mask = (
            filtered_df['company_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['contact_person'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # 필터링 결과 및 다운로드 버튼
    col_info, col_download = st.columns([3, 1])
    with col_info:
        st.info(f"{get_text('filtering_results')}: {len(filtered_df)}{get_text('customers_total')} {len(all_customers_data)}{get_text('among')}")
    
    with col_download:
        if len(filtered_df) > 0:
            csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"customers_list_{timestamp}.csv"
            
            st.download_button(
                label=f"📥 {get_text('export')}",
                data=csv_data,
                file_name=filename,
                mime='text/csv'
            )
    
    if len(filtered_df) > 0:
        # 통합 테이블 표시 함수 사용
        display_customer_table(filtered_df, get_text)
    else:
        st.warning(get_text("no_matching_customers"))

def show_customer_registration(customer_manager, get_text=lambda x: x):
    """고객 등록 폼 표시"""
    st.header(f"➕ {get_text('customer_registration')}")
    
    # 국가-도시 선택을 폼 밖에서 처리
    st.subheader(f"🌍 {get_text('location_info')}")
    col_location1, col_location2 = st.columns(2)
    
    with col_location1:
        countries = [get_text("countries_korea"), get_text("countries_china"), get_text("countries_thailand"), 
                     get_text("countries_vietnam"), get_text("countries_indonesia"), get_text("countries_malaysia")]
        selected_country = st.selectbox(f"{get_text('country')} *", countries, key="customer_country_registration")
        
    with col_location2:
        # 국가 변경 시 도시 목록 업데이트
        if 'prev_customer_country' not in st.session_state:
            st.session_state.prev_customer_country = selected_country
        
        if st.session_state.prev_customer_country != selected_country:
            st.session_state.prev_customer_country = selected_country
            st.rerun()
        
        # 국가별 도시 목록 가져오기
        cities = customer_manager.get_cities_by_country(selected_country)
        city_options = [get_text('direct_input')] + cities if cities else [get_text('direct_input')]
        
        selected_city_option = st.selectbox(get_text('city'), city_options, key="customer_city_registration")
        
        # 직접 입력인 경우
        if selected_city_option == get_text('direct_input'):
            selected_city = st.text_input(get_text('direct_input'), placeholder=get_text('enter_city_name'), key="customer_city_manual")
        else:
            selected_city = selected_city_option
            st.info(f"{get_text('selected_city')}: {selected_city}")
    
    # 고객 등록 폼
    # 폼 리셋을 위한 키 생성
    form_key = f"customer_registration_form_{st.session_state.get('customer_form_reset', 0)}"
    
    with st.form(form_key):
        st.subheader(f"🏢 {get_text('basic_info')}")
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input(f"{get_text('company_name')} *", help="정확한 회사명을 입력하세요")
            contact_person = st.text_input(f"{get_text('contact_person')} *", help="주요 연락 담당자")
            contact_phone = st.text_input(f"{get_text('phone')} *", placeholder="010-1234-5678")
            contact_email = st.text_input(get_text('email'), placeholder="contact@company.com")
            position = st.text_input(get_text('position'), placeholder="예: 구매담당자, 부장")
            
        with col2:
            # 사업 유형 업데이트
            business_types = [get_text("business_types_mold"), get_text("business_types_injection"), 
                             get_text("business_types_mold_injection"), get_text("business_types_t1"), 
                             get_text("business_types_brand"), get_text("business_types_trade"), get_text("business_types_other")]
            business_type = st.selectbox(f"{get_text('business_type')} *", business_types)
            customer_grade = st.selectbox(get_text('customer_grade'), [get_text("customer_grades_a"), get_text("customer_grades_b"), 
                                                                      get_text("customer_grades_c"), get_text("customer_grades_potential")])
        
        # 주소 정보
        st.subheader(f"📍 {get_text('address_info')}")
        col3, col4 = st.columns(2)
        
        with col3:
            address = st.text_input(get_text('basic_address'), placeholder="예: 서울시 강남구 테헤란로 123")
            
        with col4:
            detail_address = st.text_input(get_text('detail_address'), placeholder="예: 456동 789호")
        
        # KAM 정보 확장
        st.subheader(f"🎯 {get_text('kam_info')}")
        col5, col6 = st.columns(2)
        
        with col5:
            kam_manager = st.text_input(get_text('kam_manager'), placeholder="담당 영업사원 이름")
            relationship_level = st.selectbox(get_text('relationship_level'), ["1단계 (초기접촉)", "2단계 (관심표명)", "3단계 (협력검토)", "4단계 (파트너십)", "5단계 (전략적파트너)"])
            communication_frequency = st.selectbox(get_text('communication_frequency'), ["주 1회", "월 2회", "월 1회", "분기 1회", "필요시"])
            last_meeting_date = st.date_input(get_text('last_meeting_date'))
            
        with col6:
            potential_value = st.number_input(get_text('potential_value'), min_value=0, step=1000, help="예상 연간 거래 규모")
            decision_maker = st.text_input(get_text('decision_maker'), placeholder="최종 결정권자 이름/직책")
            decision_process = st.text_area(get_text('decision_process'), placeholder="고객의 의사결정 프로세스 설명")
            competitive_status = st.selectbox(get_text('competitive_status'), ["독점", "우위", "경쟁", "열세", "미확인"])
        
        # 영업 전략 정보
        st.subheader(f"📈 {get_text('sales_strategy')}")
        col7, col8 = st.columns(2)
        
        with col7:
            sales_strategy = st.text_area("영업 전략", placeholder="고객별 맞춤 영업 전략")
            cross_sell_opportunity = st.text_area("교차 판매 기회", placeholder="추가 제품 판매 가능성")
            
        with col8:
            growth_potential = st.selectbox("성장 가능성", ["매우 높음", "높음", "보통", "낮음", "매우 낮음"])
            risk_factors = st.text_area("리스크 요인", placeholder="거래 시 주의사항이나 위험요소")
        
        # 기타 정보
        st.subheader("📋 기타 정보")
        col9, col10 = st.columns(2)
        
        with col9:
            company_size = st.selectbox("회사 규모", ["대기업", "중견기업", "중소기업", "스타트업"])
            annual_revenue = st.number_input("연 매출 (USD)", min_value=0, step=100000)
            
        with col10:
            payment_terms = st.selectbox("결제 조건", ["현금", "NET 30", "NET 60", "NET 90", "기타"])
            website = st.text_input("웹사이트", placeholder="https://company.com")
        
        # 연락처 및 특이사항
        st.subheader("📞 추가 연락처")
        col11, col12 = st.columns(2)
        
        with col11:
            secondary_contact = st.text_input("보조 연락처", placeholder="부담당자 연락처")
            
        with col12:
            main_products = st.text_area("주요 제품", placeholder="고객이 생산하는 주요 제품")
            special_requirements = st.text_area("특별 요구사항", placeholder="고객의 특별한 요구사항")
        
        notes = st.text_area("전체 메모", placeholder="기타 특이사항 및 메모")
        
        submitted = st.form_submit_button(f"💾 {get_text('customer_register_btn')}", use_container_width=True, type="primary")
        
        if submitted:
            # 필수 항목 검증: 회사명, 담당자명, 연락처, 사업유형만 필수
            required_fields = []
            if not company_name or company_name.strip() == "":
                required_fields.append("회사명")
            if not contact_person or contact_person.strip() == "":
                required_fields.append("담당자명")
            if not contact_phone or contact_phone.strip() == "":
                required_fields.append("연락처")
            if not business_type or business_type.strip() == "":
                required_fields.append("사업유형")
            
            if required_fields:
                st.error(f"필수 항목을 입력해주세요: {', '.join(required_fields)} (* 표시 항목)")
            else:
                customer_data = {
                    'company_name': company_name,
                    'contact_person': contact_person,
                    'position': position,
                    'contact_phone': contact_phone,
                    'contact_email': contact_email,
                    'address': address,
                    'detail_address': detail_address,
                    'country': selected_country,
                    'city': selected_city,
                    'business_type': business_type,
                    'customer_grade': customer_grade,
                    'company_size': company_size,
                    'annual_revenue': annual_revenue,
                    'payment_terms': payment_terms,
                    'website': website,
                    'secondary_contact': secondary_contact,
                    'main_products': main_products,
                    'special_requirements': special_requirements,
                    'kam_manager': kam_manager,
                    'relationship_level': relationship_level,
                    'communication_frequency': communication_frequency,
                    'last_meeting_date': str(last_meeting_date),
                    'potential_value': potential_value,
                    'decision_maker': decision_maker,
                    'decision_process': decision_process,
                    'competitive_status': competitive_status,
                    'sales_strategy': sales_strategy,
                    'cross_sell_opportunity': cross_sell_opportunity,
                    'growth_potential': growth_potential,
                    'risk_factors': risk_factors,
                    'notes': notes
                }
                
                try:
                    customer_id = customer_manager.add_customer(customer_data)
                    if customer_id:
                        st.success(f"✅ 고객 등록 성공: {customer_id}")
                        st.balloons()
                        # 폼 리셋을 위한 세션 상태 클리어
                        if 'customer_form_reset' not in st.session_state:
                            st.session_state.customer_form_reset = 0
                        st.session_state.customer_form_reset += 1
                        st.rerun()
                    else:
                        st.error("❌ 고객 등록 실패: 알 수 없는 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"❌ 고객 등록 오류: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

def show_customer_edit(customer_manager, get_text=lambda x: x):
    """고객 편집 페이지"""
    st.header(f"✏️ {get_text('customer_edit')}")
    
    customers_data = customer_manager.get_all_customers()
    if len(customers_data) == 0:
        st.warning(get_text("no_customers_registered"))
        return
    
    # DataFrame으로 변환
    customers_df = pd.DataFrame(customers_data)
    
    # 필터링 옵션
    st.subheader(f"🔍 {get_text('customer_search_filter')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 회사명 검색
        search_company = st.text_input(get_text("company_name_search"), placeholder=get_text("company_name_placeholder"))
    
    with col2:
        # 사업 유형 필터
        business_types = [get_text("all_status")] + [get_text("business_types_mold"), get_text("business_types_injection"), 
                                                      get_text("business_types_mold_injection"), get_text("business_types_t1"), 
                                                      get_text("business_types_brand"), get_text("business_types_trade"), get_text("business_types_other")]
        selected_business_type = st.selectbox(get_text("business_type_label"), business_types)
    
    with col3:
        # 국가 필터
        countries = [get_text("all_status")] + sorted(customers_df['country'].dropna().unique().tolist())
        selected_country = st.selectbox(get_text("country_label"), countries)
    
    with col4:
        # 도시 필터 (선택된 국가에 따라 동적으로 변경)
        if selected_country != get_text("all_status"):
            cities_in_country = customers_df[customers_df['country'] == selected_country]['city'].dropna().unique().tolist()
            cities = [get_text("all_status")] + sorted(cities_in_country)
        else:
            cities = [get_text("all_status")] + sorted(customers_df['city'].dropna().unique().tolist())
        selected_city = st.selectbox(get_text("city_label"), cities)
    
    # 필터 적용
    filtered_df = customers_df.copy()
    
    # 회사명 검색 필터
    if search_company:
        filtered_df = filtered_df[filtered_df['company_name'].str.contains(search_company, case=False, na=False)]
    
    # 사업 유형 필터
    if selected_business_type != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['business_type'] == selected_business_type]
    
    # 국가 필터
    if selected_country != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['country'] == selected_country]
    
    # 도시 필터
    if selected_city != get_text("all_status"):
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    
    # 필터링 결과 표시
    st.info(get_text("filtering_result").format(count=len(filtered_df), total=len(customers_df)))
    
    if len(filtered_df) == 0:
        st.warning(get_text("no_matching_customers"))
        return
    
    # 필터된 고객 목록 다운로드 기능
    if st.button(f"📥 {get_text('download_filtered_customers')}"):
        csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"filtered_customers_{timestamp}.csv"
        
        st.download_button(
            label=get_text("template_file_download"),
            data=csv_data,
            file_name=filename,
            mime='text/csv'
        )
    
    # 고객 선택
    st.subheader(f"✏️ {get_text('select_customer_to_edit')}")
    customer_options = [f"{row['company_name']} - {row['contact_person']} ({row['customer_id']}) | {row.get('business_type', 'N/A')} | {row.get('city', 'N/A')}, {row.get('country', 'N/A')}" 
                       for _, row in filtered_df.iterrows()]
    
    if not customer_options:
        st.warning(get_text("no_matching_customers"))
        return
    
    # 수정 완료 후 선택 초기화를 위한 상태 관리
    default_index = 0
    if 'selected_customer_for_edit' in st.session_state:
        try:
            default_index = customer_options.index(st.session_state.selected_customer_for_edit) + 1
        except ValueError:
            default_index = 0
    
    selected_customer = st.selectbox(
        get_text("select_customer_dropdown"), 
        [""] + customer_options,
        index=default_index,
        key="customer_edit_selector"
    )
    
    # 선택 상태 저장
    if selected_customer:
        st.session_state.selected_customer_for_edit = selected_customer
    
    if selected_customer:
        # 선택된 고객 정보 가져오기
        selected_id = selected_customer.split("(")[1].split(")")[0]
        customer_data = customer_manager.get_customer_by_id(selected_id)
        
        if customer_data:
            # JSON 데이터 파싱
            import json
            notes_data = {}
            if customer_data.get('notes'):
                try:
                    notes_data = json.loads(customer_data['notes'])
                except json.JSONDecodeError:
                    notes_data = {}
            
            # 국가-도시 선택을 폼 밖에서 처리
            st.subheader(f"🌍 {get_text('edit_location_info')}")
            col_location1, col_location2 = st.columns(2)
            
            with col_location1:
                countries = [get_text("countries_korea"), get_text("countries_china"), get_text("countries_thailand"), 
                             get_text("countries_vietnam"), get_text("countries_indonesia"), get_text("countries_malaysia")]
                current_country = customer_data.get('country', '한국')
                country_index = countries.index(current_country) if current_country in countries else 0
                edit_selected_country = st.selectbox(get_text("select_country_required"), countries, index=country_index, key=f"customer_edit_country_{selected_id}")
                
            with col_location2:
                # 국가 변경 시 도시 목록 업데이트
                if f'prev_edit_customer_country_{selected_id}' not in st.session_state:
                    st.session_state[f'prev_edit_customer_country_{selected_id}'] = edit_selected_country
                
                if st.session_state[f'prev_edit_customer_country_{selected_id}'] != edit_selected_country:
                    st.session_state[f'prev_edit_customer_country_{selected_id}'] = edit_selected_country
                    st.rerun()
                
                # 국가별 도시 목록 가져오기
                cities = customer_manager.get_cities_by_country(edit_selected_country)
                city_options = ["직접 입력"] + cities if cities else ["직접 입력"]
                
                current_city = customer_data.get('city', '')
                if current_city in city_options:
                    city_index = city_options.index(current_city)
                    edit_selected_city_option = st.selectbox("도시", city_options, index=city_index, key=f"customer_edit_city_{selected_id}")
                else:
                    edit_selected_city_option = st.selectbox("도시", city_options, key=f"customer_edit_city_{selected_id}")
                
                # 직접 입력인 경우
                if edit_selected_city_option == "직접 입력":
                    edit_selected_city = st.text_input("도시명 직접 입력", value=current_city, placeholder="도시명을 입력하세요", key=f"customer_edit_city_manual_{selected_id}")
                else:
                    edit_selected_city = edit_selected_city_option
                    if edit_selected_city != current_city:
                        st.info(f"선택된 도시: {edit_selected_city}")
            
            # 고객 편집 폼 - 고유 키로 폼 구분
            edit_form_key = f"customer_edit_form_{selected_id}"
            with st.form(edit_form_key):
                st.subheader(f"🏢 {get_text('basic_info')}")
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input("회사명 *", value=customer_data.get('company_name', ''))
                    contact_person = st.text_input("담당자명 *", value=customer_data.get('contact_person', ''))
                    contact_phone = st.text_input("연락처 *", value=customer_data.get('phone', ''))
                    contact_email = st.text_input("이메일", value=customer_data.get('email', ''))
                    position = st.text_input("담당자 직책", value=notes_data.get('position', ''))
                
                with col2:
                    # 사업 유형 업데이트
                    business_types = ["금형산업", "사출산업", "금형&사출산업", "T1", "브랜드", "트레이드", "기타"]
                    current_business_type = customer_data.get('business_type', '기타')
                    business_type_index = business_types.index(current_business_type) if current_business_type in business_types else 6
                    business_type = st.selectbox("사업 유형 *", business_types, index=business_type_index)
                    
                    customer_grades = ["A급 (주요고객)", "B급 (일반고객)", "C급 (신규고객)", "잠재고객"]
                    current_grade = notes_data.get('customer_grade', 'C급 (신규고객)')
                    grade_index = customer_grades.index(current_grade) if current_grade in customer_grades else 2
                    customer_grade = st.selectbox("고객 등급", customer_grades, index=grade_index)
                
                # 주소 정보
                st.subheader(f"📍 {get_text('address_info')}")
                col3, col4 = st.columns(2)
                
                with col3:
                    address = st.text_input("기본 주소", value=customer_data.get('address', ''))
                    
                with col4:
                    detail_address = st.text_input("세부 주소", value=notes_data.get('detail_address', ''))
                
                # KAM 정보
                st.subheader("🎯 KAM 정보")
                col5, col6 = st.columns(2)
                
                with col5:
                    kam_manager = st.text_input("KAM 담당자", value=notes_data.get('kam_manager', ''))
                    
                    relationship_levels = ["1단계 (초기접촉)", "2단계 (관심표명)", "3단계 (협력검토)", "4단계 (파트너십)", "5단계 (전략적파트너)"]
                    current_rel_level = notes_data.get('relationship_level', '1단계 (초기접촉)')
                    rel_level_index = relationship_levels.index(current_rel_level) if current_rel_level in relationship_levels else 0
                    relationship_level = st.selectbox("관계 수준", relationship_levels, index=rel_level_index)
                    
                    comm_frequencies = ["주 1회", "월 2회", "월 1회", "분기 1회", "필요시"]
                    current_comm_freq = notes_data.get('communication_frequency', '월 1회')
                    comm_freq_index = comm_frequencies.index(current_comm_freq) if current_comm_freq in comm_frequencies else 2
                    communication_frequency = st.selectbox("소통 주기", comm_frequencies, index=comm_freq_index)
                
                with col6:
                    # potential_value 처리 - 안전한 변환
                    try:
                        potential_val = float(notes_data.get('potential_value', 0) or 0)
                    except (ValueError, TypeError):
                        potential_val = 0.0
                    potential_value = st.number_input("잠재 가치 (USD)", value=potential_val, min_value=0.0, step=1000.0)
                    decision_maker = st.text_input("의사결정권자", value=notes_data.get('decision_maker', ''))
                    
                    competitive_statuses = ["독점", "우위", "경쟁", "열세", "미확인"]
                    current_comp_status = notes_data.get('competitive_status', '미확인')
                    comp_status_index = competitive_statuses.index(current_comp_status) if current_comp_status in competitive_statuses else 4
                    competitive_status = st.selectbox("경쟁 상황", competitive_statuses, index=comp_status_index)
                
                # 기타 정보
                st.subheader("📋 기타 정보")
                col7, col8 = st.columns(2)
                
                with col7:
                    company_sizes = ["대기업", "중견기업", "중소기업", "스타트업"]
                    current_company_size = notes_data.get('company_size', '중소기업')
                    company_size_index = company_sizes.index(current_company_size) if current_company_size in company_sizes else 2
                    company_size = st.selectbox("회사 규모", company_sizes, index=company_size_index)
                    
                    # annual_revenue 처리 - 안전한 변환
                    try:
                        annual_rev = float(notes_data.get('annual_revenue', 0) or 0)
                    except (ValueError, TypeError):
                        annual_rev = 0.0
                    annual_revenue = st.number_input("연 매출 (USD)", value=annual_rev, min_value=0.0, step=100000.0)
                
                with col8:
                    payment_terms_options = ["현금", "NET 30", "NET 60", "NET 90", "기타"]
                    current_payment_terms = notes_data.get('payment_terms', 'NET 30')
                    payment_terms_index = payment_terms_options.index(current_payment_terms) if current_payment_terms in payment_terms_options else 1
                    payment_terms = st.selectbox("결제 조건", payment_terms_options, index=payment_terms_index)
                    
                    website = st.text_input("웹사이트", value=notes_data.get('website', ''))
                
                # 추가 연락처 및 메모
                st.subheader("📞 추가 정보")
                col9, col10 = st.columns(2)
                
                with col9:
                    secondary_contact = st.text_input("보조 연락처", value=notes_data.get('secondary_contact', ''))
                    
                    # last_meeting_date 처리
                    from datetime import datetime
                    try:
                        last_meeting_str = notes_data.get('last_meeting_date', '2025-08-28')
                        last_meeting_date = datetime.strptime(last_meeting_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        last_meeting_date = datetime.now().date()
                    last_meeting_date = st.date_input("최근 미팅 날짜", value=last_meeting_date)
                
                with col10:
                    main_products = st.text_area("주요 제품", value=notes_data.get('main_products', ''))
                    special_requirements = st.text_area("특별 요구사항", value=notes_data.get('special_requirements', ''))
                
                # 영업 전략 정보
                st.subheader("📈 영업 전략")
                col11, col12 = st.columns(2)
                
                with col11:
                    sales_strategy = st.text_area("영업 전략", value=notes_data.get('sales_strategy', ''))
                    growth_potentials = ["매우 높음", "높음", "보통", "낮음", "매우 낮음"]
                    current_growth = notes_data.get('growth_potential', '보통')
                    growth_index = growth_potentials.index(current_growth) if current_growth in growth_potentials else 2
                    growth_potential = st.selectbox("성장 가능성", growth_potentials, index=growth_index)
                
                with col12:
                    cross_sell_opportunity = st.text_area("교차 판매 기회", value=notes_data.get('cross_sell_opportunity', ''))
                    risk_factors = st.text_area("리스크 요인", value=notes_data.get('risk_factors', ''))
                
                # 의사결정 프로세스
                decision_process = st.text_area("의사결정 프로세스", value=notes_data.get('decision_process', ''))
                
                user_notes = st.text_area("전체 메모", value=notes_data.get('user_notes', ''))
                
                # 수정 버튼
                submitted = st.form_submit_button("💾 정보 수정", use_container_width=True, type="primary")
                
                if submitted:
                    if not company_name or not contact_person or not business_type:
                        st.error("필수 항목을 모두 입력해주세요.")
                    else:
                        # JSON 형태로 확장 정보 저장
                        extended_data = {
                            'position': position,
                            'contact_phone': contact_phone,
                            'contact_email': contact_email,
                            'detail_address': detail_address,
                            'customer_grade': customer_grade,
                            'company_size': company_size,
                            'annual_revenue': annual_revenue,
                            'payment_terms': payment_terms,
                            'website': website,
                            'secondary_contact': secondary_contact,
                            'main_products': main_products,
                            'special_requirements': special_requirements,
                            'kam_manager': kam_manager,
                            'relationship_level': relationship_level,
                            'communication_frequency': communication_frequency,
                            'last_meeting_date': str(last_meeting_date),
                            'potential_value': potential_value,
                            'decision_maker': decision_maker,
                            'decision_process': decision_process,
                            'competitive_status': competitive_status,
                            'sales_strategy': sales_strategy,
                            'cross_sell_opportunity': cross_sell_opportunity,
                            'growth_potential': growth_potential,
                            'risk_factors': risk_factors,
                            'user_notes': user_notes
                        }
                        
                        updated_data = {
                            'company_name': company_name,
                            'contact_person': contact_person,
                            'email': contact_email,
                            'phone': contact_phone,
                            'address': address,
                            'country': edit_selected_country,
                            'city': edit_selected_city,
                            'business_type': business_type,
                            'notes': json.dumps(extended_data, ensure_ascii=False)
                        }
                        
                        try:
                            customer_manager.update_customer(selected_id, updated_data)
                            st.success("✅ 고객 정보 수정 성공")
                            # 수정 완료 후 선택 초기화
                            if 'selected_customer_for_edit' in st.session_state:
                                del st.session_state.selected_customer_for_edit
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 고객 정보 수정 오류: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

def show_customer_statistics(customer_manager, get_text=lambda x: x):
    """고객 통계 페이지"""
    st.header(f"📊 {get_text('customer_statistics')}")
    
    customers_data = customer_manager.get_all_customers()
    if len(customers_data) == 0:
        st.warning(get_text("no_statistics_data"))
        return
    
    # DataFrame으로 변환
    customers_df = pd.DataFrame(customers_data)
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(get_text("total_customer_count"), len(customers_df))
    
    with col2:
        if 'country' in customers_df.columns:
            country_count = customers_df['country'].nunique()
            st.metric(get_text("countries_count"), country_count)
        else:
            st.metric(get_text("countries_count"), "N/A")
    
    with col3:
        if 'business_type' in customers_df.columns:
            business_count = customers_df['business_type'].nunique()
            st.metric(get_text("business_types_count"), business_count)
        else:
            st.metric(get_text("business_types_count"), "N/A")
    
    with col4:
        if 'customer_grade' in customers_df.columns:
            # NaN이 아닌 값만 필터링하고 문자열로 변환
            grade_series = customers_df['customer_grade'].dropna().astype(str)
            if len(grade_series) > 0:
                a_grade_count = len(grade_series[grade_series.str.contains('A', na=False)])
                st.metric(get_text("a_grade_customers"), a_grade_count)
            else:
                st.metric(get_text("a_grade_customers"), 0)
        else:
            st.metric(get_text("a_grade_customers"), "N/A")

def show_customer_bulk_registration(customer_manager, get_text=lambda x: x):
    """고객 대량 등록 페이지"""
    st.header(f"📤 {get_text('customer_bulk_registration')}")
    
    st.markdown(f"""
    {get_text('bulk_upload_description')}
    
    **{get_text('upload_format')}**
    - {get_text('file_format')}
    - {get_text('required_columns')}
    """)
    
    # 템플릿 다운로드
    if st.button(f"📥 {get_text('download_template')}"):
        template_data = {
            'company_name': ['샘플회사', ''],
            'contact_person': ['홍길동', ''],
            'business_type': ['제조업', ''],
            'country': ['한국', ''],
            'city': ['서울', '']
        }
        template_df = pd.DataFrame(template_data)
        
        csv = template_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label=get_text("template_file_download"),
            data=csv,
            file_name="customer_template.csv",
            mime="text/csv"
        )
    
    # 파일 업로드
    uploaded_file = st.file_uploader(get_text("csv_file_selection"), type=['csv'])
    
    if uploaded_file is not None:
        try:
            # 파일 읽기
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            st.subheader(get_text("uploaded_data_preview"))
            st.dataframe(df.head())
            
            if st.button(f"🚀 {get_text('execute_bulk_registration')}", type="primary"):
                success_count = 0
                error_count = 0
                
                for index, row in df.iterrows():
                    try:
                        customer_data = row.to_dict()
                        customer_manager.add_customer(customer_data)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        st.error(f"행 {index + 1} 등록 실패: {str(e)}")
                
                st.success(get_text("registration_complete").format(success=success_count, error=error_count))
                if success_count > 0:
                    notify.show_operation_success("등록", f"{success_count}개 고객", success_count)
                    st.rerun()
                    
        except Exception as e:
            st.error(get_text("file_processing_error").format(error=str(e)))