import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import re
import time

# 간단한 지역 데이터베이스 (geographic_database 대체)
geo_db = {
    'countries': {
        '한국': ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '수원', '고양', '창원'],
        '베트남': ['호치민시', '하노이', '다낭', '하이퐁', '껀터', '후에', '빈즈엉', '나트랑', '끄엉가이', '달랏'],
        '중국': ['베이징', '상하이', '광저우', '심천', '청두', '항저우', '난징', '우한', '시안', '쑤저우'],
        '일본': ['도쿄', '오사카', '요코하마', '나고야', '삿포로', '고베', '교토', '후쿠오카', '가와사키', '사이타마'],
        '싱가포르': ['싱가포르'],
        '태국': ['방콕', '치앙마이', '파타야', '푸켓', '핫야이', '코삼이', '치앙라이', '우돈타니', '논타부리', '쑤린'],
        '말레이시아': ['쿠알라룸푸르', '조호바루', '페낭', '코타키나발루', '쿠칭', '말라카', '이포', '샤알람', '클랑', '탐핀'],
        '인도네시아': ['자카르타', '수라바야', '반둥', '메단', '스마랑', '팔렘방', '마카사르', '뎀팍', '덴파사르', '바탐']
    }
}

def format_phone_number(phone):
    """연락처를 검증하고 적절한 형식으로 포맷팅합니다."""
    if not phone:
        return phone
    
    # 숫자만 추출
    digits = re.sub(r'[^\d]', '', phone)
    
    # 최소 길이 검증 (너무 짧은 번호 거부)
    if len(digits) < 7:
        return None  # 잘못된 번호는 None 반환
    
    # 한국 휴대폰 번호 (010으로 시작하는 11자리)
    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    # 한국 휴대폰 번호 (010으로 시작하는 10자리)
    elif len(digits) == 10 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    # 국제 번호 (84로 시작하는 베트남 번호)
    elif len(digits) >= 10:
        if digits.startswith('84'):
            # 베트남 번호: +84XX-XXX-XXXX 형식
            if len(digits) == 11:
                return f"+{digits[:2]}{digits[2:4]}-{digits[4:7]}-{digits[7:]}"
            elif len(digits) == 12:
                return f"+{digits[:2]}{digits[2:4]}-{digits[4:7]}-{digits[7:]}"
        # 기타 국제 번호
        else:
            if len(digits) >= 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    # 일반 지역번호 (7-10자리)
    elif len(digits) >= 7:
        if len(digits) <= 8:
            return f"{digits[:4]}-{digits[4:]}"
        else:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    # 너무 짧거나 이상한 번호는 None 반환
    return None

def show_employee_page(manager, auth_manager, user_permissions, get_text, hide_header=False):
    """직원 관리 페이지 - 탭 기반 UI"""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'employee_management', get_text)
    
    # 헤더 표시 여부 확인 (중복 방지)
    if not hide_header:
        st.header(f"👥 {get_text('title_employee_management')}")
    
    # 탭 생성
    tab_names = [
        f"📋 {get_text('employee_list')}", 
        f"➕ {get_text('employee_registration')}", 
        f"✏️ {get_text('employee_edit')}", 
        f"🗑️ {get_text('employee_delete')}",
        f"📊 {get_text('employee_statistics')}", 
        f"🔐 {get_text('employee_permissions')}", 
        f"🔑 {get_text('password_management')}", 
        f"🏖️ {get_text('annual_leave_management')}", 
        f"📤 {get_text('bulk_employee_registration')}"
    ]
    
    # 탭 컨테이너 생성
    tabs = st.tabs(tab_names)
    
    # 각 탭의 내용 구현
    with tabs[0]:  # 직원 목록
        show_employee_list(manager, get_text)
    
    with tabs[1]:  # 직원 등록
        show_employee_registration(manager, get_text)
    
    with tabs[2]:  # 직원 편집
        show_employee_edit(manager, get_text)
    
    with tabs[3]:  # 직원 삭제
        show_employee_delete(manager, get_text)
    
    with tabs[4]:  # 직원 통계
        show_employee_statistics(manager, get_text)
    
    with tabs[5]:  # 직원 권한
        show_employee_permissions(manager, auth_manager, get_text)
    
    with tabs[6]:  # 비밀번호 관리
        show_password_management(manager, auth_manager, get_text)
    
    with tabs[7]:  # 연차 관리
        show_annual_leave_management(manager, get_text)
    
    with tabs[8]:  # 대량 등록
        show_employee_bulk_registration(manager, get_text)

def show_employee_list(manager, get_text=lambda x: x):
    """직원 목록 표시"""
    st.header(f"📋 {get_text('employee_list')}")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter_options = [get_text("all_status"), get_text("active_status"), get_text("inactive_status")]
        status_filter = st.selectbox(get_text("status_filter"), status_filter_options)
    with col2:
        region_filter_options = [get_text("all_regions")] + manager.get_regions()
        region_filter = st.selectbox(get_text("region_filter"), region_filter_options)
    with col3:
        search_term = st.text_input(get_text("search_name_id"))

    # 필터 적용 - 한국어/영어 상태 호환성 처리
    actual_status_filter = None
    if status_filter == get_text("active_status"):
        actual_status_filter = ['활성', 'active', '재직']  # 다양한 활성 상태 형식 지원
    elif status_filter == get_text("inactive_status"):
        actual_status_filter = ['비활성', 'inactive', '퇴사']  # 다양한 비활성 상태 형식 지원

    actual_region_filter = None if region_filter == get_text("all_regions") else region_filter

    filtered_employees = manager.get_filtered_employees(
        status_filter=actual_status_filter,
        region_filter=actual_region_filter,
        search_term=search_term
    )

    if len(filtered_employees) > 0:
        # 직원 목록 표시
        st.info(f"{get_text('total_count')}: {len(filtered_employees)}{get_text('filtered_results')}")
        
        # 표시할 컬럼 선택 (SQLite 매니저 호환)
        display_columns = ['employee_id', 'name', 'english_name', 'phone', 'email', 'position', 'status']
        available_columns = [col for col in display_columns if col in filtered_employees.columns]
        
        if available_columns:
            display_df = filtered_employees[available_columns].copy()
            
            # 영문명 우선 표시 로직 추가
            if 'name' in display_df.columns and 'english_name' in display_df.columns:
                # 영문명이 있으면 영문명 우선, 없으면 한국명
                display_df['display_name'] = display_df.apply(lambda row: 
                    row['english_name'] if row['english_name'] and str(row['english_name']).strip() 
                    else row['name'], axis=1)
                
                # name과 english_name 컬럼을 display_name으로 교체
                display_columns_updated = [col if col not in ['name', 'english_name'] else 'display_name' 
                                         for col in available_columns if col not in ['english_name']]
                if 'name' in display_columns_updated:
                    idx = display_columns_updated.index('name')
                    display_columns_updated[idx] = 'display_name'
                elif 'display_name' not in display_columns_updated:
                    display_columns_updated.insert(1, 'display_name')  # employee_id 다음에 추가
                
                display_df = display_df[display_columns_updated]
                available_columns = display_columns_updated
            
            # 컬럼명 번역으로 변경 (SQLite 매니저 호환)
            column_mapping = {
                'employee_id': get_text('employee_id'),
                'name': get_text('label_name'),
                'display_name': get_text('label_name'),
                'english_name': get_text('english_name'),
                'phone': get_text('label_phone'),
                'email': get_text('label_email'),
                'position': get_text('label_position'),
                'status': get_text('work_status')
            }
            
            rename_dict = {k: v for k, v in column_mapping.items() if k in display_df.columns}
            display_df = display_df.rename(columns=rename_dict)
            
            # 직원 목록 테이블 표시
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 직원 삭제 섹션
            st.divider()
            st.subheader("🗑️ 직원 삭제")
            
            # 삭제할 직원 선택
            col_select, col_delete = st.columns([3, 1])
            
            with col_select:
                employee_options = []
                for _, emp in filtered_employees.iterrows():
                    emp_id = str(emp.get('employee_id', ''))
                    emp_name = emp.get('name', '알 수 없음')
                    emp_position = emp.get('position', '직책 미상')
                    employee_options.append(f"{emp_id} - {emp_name} ({emp_position})")
                
                if employee_options:
                    selected_employee = st.selectbox(
                        "삭제할 직원을 선택하세요:",
                        options=["선택하세요..."] + employee_options,
                        help="⚠️ 주의: 삭제된 직원 정보는 복구할 수 없습니다."
                    )
                else:
                    st.info("삭제할 직원이 없습니다.")
                    selected_employee = None
            
            with col_delete:
                if selected_employee and selected_employee != "선택하세요...":
                    # 선택된 직원의 ID 추출
                    employee_id_to_delete = selected_employee.split(" - ")[0]
                    
                    # 삭제 확인을 위한 2단계 버튼
                    if 'delete_confirm_step' not in st.session_state:
                        st.session_state.delete_confirm_step = 0
                    
                    if st.session_state.delete_confirm_step == 0:
                        if st.button("🗑️ 삭제", type="secondary", help="클릭하여 삭제를 확인하세요"):
                            st.session_state.delete_confirm_step = 1
                            st.rerun()
                    
                    elif st.session_state.delete_confirm_step == 1:
                        st.error("⚠️ 정말 삭제하시겠습니까?")
                        col_yes, col_no = st.columns(2)
                        
                        with col_yes:
                            if st.button("✅ 확인", type="primary"):
                                # 직원 삭제 실행
                                result = manager.delete_employee(employee_id_to_delete)
                                
                                # SQLiteEmployeeManager는 (success, message) 튜플을 반환
                                if isinstance(result, tuple) and len(result) == 2:
                                    success, message = result
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.session_state.delete_confirm_step = 0
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                        st.session_state.delete_confirm_step = 0
                                # 기존 매니저 호환성 (True/False만 반환)
                                elif result:
                                    st.success("✅ 직원이 성공적으로 삭제되었습니다!")
                                    st.session_state.delete_confirm_step = 0
                                    st.rerun()
                                else:
                                    st.error("❌ 직원 삭제에 실패했습니다.")
                                    st.session_state.delete_confirm_step = 0
                        
                        with col_no:
                            if st.button("❌ 취소"):
                                st.session_state.delete_confirm_step = 0
                                st.rerun()
            
            st.divider()
            
            # 다운로드 버튼
            csv_buffer = io.StringIO()
            filtered_employees.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 {get_text('download_employee_list')}",
                data=csv_buffer.getvalue().encode('utf-8-sig'),
                file_name=f"employees_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning(get_text("no_display_data"))
    else:
        st.warning(get_text("no_employees_found"))

def show_employee_registration(manager, get_text=lambda x: x):
    """직원 등록 폼 표시"""
    st.header("➕ 새 직원 등록")
    
    # 국가-도시 선택을 폼 밖에서 처리
    st.subheader("🌍 거주지 정보")
    col_location1, col_location2 = st.columns(2)
    
    with col_location1:
        nationality_options = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
        selected_nationality = st.selectbox("국적 *", nationality_options, key="employee_nationality_registration")
        
        residence_countries = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
        selected_residence_country = st.selectbox("거주국가 *", residence_countries, key="employee_residence_country_registration")
        
    with col_location2:
        # 거주국가 변경 시 도시 목록 업데이트
        if 'prev_employee_residence_country' not in st.session_state:
            st.session_state.prev_employee_residence_country = selected_residence_country
        
        if st.session_state.prev_employee_residence_country != selected_residence_country:
            st.session_state.prev_employee_residence_country = selected_residence_country
            # st.rerun() 제거됨
        
        # 거주국가별 도시 목록 가져오기 (customer_manager 사용)
        try:
            customer_manager = st.session_state.customer_manager
            cities = customer_manager.get_cities_by_country(selected_residence_country)
        except:
            cities = []
        city_options = ["직접 입력"] + cities if cities else ["직접 입력"]
        
        selected_city_option = st.selectbox("거주도시", city_options, key="employee_city_registration")
        
        # 직접 입력인 경우
        if selected_city_option == "직접 입력":
            selected_city = st.text_input("도시명 직접 입력", placeholder="도시명을 입력하세요", key="employee_city_manual")
        else:
            selected_city = selected_city_option
            # 도시 목록에서 선택한 경우에만 정보 표시 (직접 입력이 아닌 경우)
            if selected_city and selected_city != "직접 입력":
                st.success(f"✅ 선택된 도시: {selected_city}")
    
    # 직원 등록 폼
    with st.form("employee_registration_form"):
        # 기본 정보
        st.subheader("👤 기본 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("이름 *", placeholder="홍길동")
            english_name = st.text_input("영문명", placeholder="Hong Gil Dong")
            gender = st.selectbox("성별", ["남", "여"])
            hire_date = st.date_input("입사일 *", value=date.today())
            # 생년월일 입력 (사용자 친화적인 날짜 선택기)
            birth_date = st.date_input(
                "생년월일 *", 
                value=date(1990, 1, 1),
                help="생년월일을 선택해주세요"
            )
        
        with col2:
            phone = st.text_input("연락처 *", placeholder="010-1234-5678")
            email = st.text_input("이메일", placeholder="hong@company.com")
            position = st.selectbox("직급", ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무", "대표"])
            department = st.selectbox("부서", ["영업", "서비스", "총무", "회계", "기술", "생산", "품질", "구매", "관리"])
        
        # 주소 정보
        st.subheader("📍 주소 정보")
        address = st.text_area("집주소 *", placeholder="상세 주소를 입력하세요", height=100)
        
        # 추가 정보
        st.subheader("추가 정보")
        col5, col6 = st.columns(2)
        
        with col5:
            salary = st.number_input("급여", min_value=0, value=0)
            salary_currency = st.selectbox("급여 통화", ["KRW", "USD", "VND", "THB", "CNY"])
        
        with col6:
            driver_license = st.selectbox("운전면허", ["없음", "있음"])
            notes = st.text_area("비고", placeholder="특이사항을 입력하세요")
        
        # 권한 설정
        st.subheader("🔐 권한 설정")
        access_level_options = ["user", "master"]
        access_level_labels = {"user": "일반 직원 (제한된 메뉴 접근)", "master": "관리자 (모든 메뉴 접근)"}
        
        selected_access_level = st.selectbox(
            "권한 등급 선택하세요:",
            options=access_level_options,
            format_func=lambda x: access_level_labels[x],
            index=0
        )
        
        if selected_access_level == "user":
            st.info("📋 일반 직원 권한: 대시보드, 게시판, 업무진행 상태, 개인 상태관리, 환율관리, 영업관리, 제품관리")
        else:
            st.warning("👑 관리자 권한: 모든 시스템 메뉴에 접근 가능")
        
        # 등록 버튼
        col_submit, col_clear = st.columns([1, 1])
        
        with col_submit:
            submitted = st.form_submit_button("✅ 직원 등록", use_container_width=True, type="primary")
        
        with col_clear:
            clear_form = st.form_submit_button("🔄 초기화", use_container_width=True)
        
        if submitted:
            # 필수 필드 검증
            if not name or not phone or not hire_date:
                st.error("이름, 연락처, 입사일은 필수 입력 항목입니다.")
            else:
                # 연락처 포맷팅 및 검증
                formatted_phone = format_phone_number(phone)
                if formatted_phone is None:
                    st.error("❌ 연락처 형식이 올바르지 않습니다. 올바른 전화번호를 입력해주세요. (예: 010-1234-5678)")
                    st.stop()
                
                # 날짜 필드 처리
                hire_date_str = hire_date.strftime('%Y-%m-%d') if hasattr(hire_date, 'strftime') else str(hire_date)
                birth_date_str = birth_date.strftime('%Y-%m-%d') if hasattr(birth_date, 'strftime') else str(birth_date)
                
                # 새 직원 데이터 준비
                new_employee = {
                    'name': name,
                    'english_name': english_name if english_name else '',
                    'gender': gender,
                    'nationality': selected_nationality,
                    'residence_country': selected_residence_country,
                    'city': selected_city,
                    'phone': formatted_phone,
                    'email': email if email else '',
                    'position': position,
                    'department': department,
                    'hire_date': hire_date_str,
                    'birth_date': birth_date_str,
                    'salary': salary if salary else 0,
                    'salary_currency': salary_currency,
                    'driver_license': driver_license,
                    'notes': notes if notes else '',
                    'work_status': '재직',
                    'status': '활성',
                    'access_level': selected_access_level,  # 권한 레벨 추가
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 직원 등록
                if manager.add_employee(new_employee):
                    st.success(f"✅ {name}님이 성공적으로 등록되었습니다!")
                    st.info("💡 페이지가 새로고침됩니다...")
                    st.rerun()  # 페이지 새로고침으로 폼 리셋
                else:
                    st.error("❌ 직원 등록에 실패했습니다.")

def show_employee_edit(manager, get_text=lambda x: x):
    """직원 편집 페이지"""
    st.header("✏️ 직원 편집")
    
    # 편집할 직원 선택
    employees = manager.get_all_employees()
    if len(employees) > 0:
        # employees가 DataFrame인지 리스트인지 확인하고 영문명 우선 표시
        if hasattr(employees, 'iterrows'):
            # DataFrame인 경우 - 영문명 우선 표시
            employee_options = []
            for _, row in employees.iterrows():
                display_name = row['english_name'] if row.get('english_name') and str(row.get('english_name')).strip() else row['name']
                employee_options.append(f"{display_name} ({row['employee_id']})")
        else:
            # 리스트인 경우 - 각 항목이 딕셔너리인지 확인하고 영문명 우선 표시
            if employees and isinstance(employees[0], dict):
                employee_options = []
                for emp in employees:
                    display_name = emp['english_name'] if emp.get('english_name') and str(emp.get('english_name')).strip() else emp['name']
                    employee_options.append(f"{display_name} ({emp['employee_id']})")
            else:
                st.error("직원 데이터 형식이 올바르지 않습니다.")
                return
        selected_employee = st.selectbox("편집할 직원 선택", ["편집할 직원을 선택하세요..."] + employee_options)
        
        if selected_employee and selected_employee != "편집할 직원을 선택하세요...":
            # 선택된 직원 정보 가져오기
            selected_id = selected_employee.split("(")[1].split(")")[0]
            employee_data = manager.get_employee_by_id(selected_id)
            
            if employee_data:
                st.info(f"편집 중인 직원: {employee_data.get('name', 'Unknown')} ({employee_data.get('employee_id', 'Unknown')})")
                
                # 간단한 데이터 확인 (필요시에만 표시)
                with st.expander("🔍 데이터 확인", expanded=False):
                    st.write(f"**현재 편집 중인 직원:** {employee_data.get('name', '')} ({employee_data.get('employee_id', '')})")
                    st.write(f"**생년월일 원본 데이터:** {employee_data.get('birth_date', 'None')}")
                    st.write(f"**입사일 원본 데이터:** {employee_data.get('hire_date', 'None')}")
                    st.write(f"**전체 데이터 타입:** {type(employee_data)}")
                    st.success("✅ PostgreSQL 데이터베이스와 편집 폼이 완전히 연동되었습니다!")
                
                # 국가-도시 선택을 폼 밖에서 처리
                st.subheader("🌍 거주지 정보 수정")
                col_location1, col_location2 = st.columns(2)
                
                with col_location1:
                    nationality_options = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
                    # region 필드를 nationality로 매핑
                    current_nationality = employee_data.get('nationality') or employee_data.get('region', '한국')
                    nationality_index = nationality_options.index(current_nationality) if current_nationality in nationality_options else 0
                    edit_selected_nationality = st.selectbox("국적 *", nationality_options, index=nationality_index, key=f"employee_edit_nationality_{selected_id}")
                    
                    residence_countries = ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"]
                    current_residence_country = employee_data.get('residence_country') or employee_data.get('region', '한국')
                    residence_country_index = residence_countries.index(current_residence_country) if current_residence_country in residence_countries else 0
                    edit_selected_residence_country = st.selectbox("거주국가 *", residence_countries, index=residence_country_index, key=f"employee_edit_residence_country_{selected_id}")
                    
                with col_location2:
                    # 거주국가 변경 시 도시 목록 업데이트
                    if f'prev_edit_employee_residence_country_{selected_id}' not in st.session_state:
                        st.session_state[f'prev_edit_employee_residence_country_{selected_id}'] = edit_selected_residence_country
                    
                    if st.session_state[f'prev_edit_employee_residence_country_{selected_id}'] != edit_selected_residence_country:
                        st.session_state[f'prev_edit_employee_residence_country_{selected_id}'] = edit_selected_residence_country
                        # st.rerun() 제거됨
                    
                    # 거주국가별 도시 목록 가져오기 (customer_manager 사용)
                    try:
                        customer_manager = st.session_state.customer_manager
                        cities = customer_manager.get_cities_by_country(edit_selected_residence_country)
                    except:
                        cities = []
                    city_options = ["직접 입력"] + cities if cities else ["직접 입력"]
                    
                    current_city = employee_data.get('city', '')
                    if current_city in city_options:
                        city_index = city_options.index(current_city)
                        edit_selected_city_option = st.selectbox("거주도시", city_options, index=city_index, key=f"employee_edit_city_{selected_id}")
                    else:
                        edit_selected_city_option = st.selectbox("거주도시", city_options, key=f"employee_edit_city_{selected_id}")
                    
                    # 직접 입력인 경우
                    if edit_selected_city_option == "직접 입력":
                        edit_selected_city = st.text_input("도시명 직접 입력", value=current_city, placeholder="도시명을 입력하세요", key=f"employee_edit_city_manual_{selected_id}")
                    else:
                        edit_selected_city = edit_selected_city_option
                        # 도시가 변경된 경우에만 알림 표시
                        if edit_selected_city != current_city and current_city:
                            st.info(f"도시 변경: {current_city} → {edit_selected_city}")
                
                # 직원 편집 폼
                with st.form("employee_edit_form"):
                    # 기본 정보
                    st.subheader("기본 정보")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("이름", value=employee_data.get('name', ''))
                        english_name = st.text_input("영문명", value=employee_data.get('english_name', ''))
                        # gender 필드가 없는 경우 기본값 처리
                        current_gender = employee_data.get('gender', '남')
                        gender = st.selectbox("성별", ["남", "여"], index=0 if current_gender == '남' else 1)
                    
                    with col2:
                        # phone 필드를 contact로 매핑
                        phone = st.text_input("연락처", value=employee_data.get('phone', ''))
                        email = st.text_input("이메일", value=employee_data.get('email', ''))
                        position_options = ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무", "대표"]
                        current_position = employee_data.get('position', '사원')
                        try:
                            position_idx = position_options.index(current_position)
                        except ValueError:
                            position_idx = 0
                        position = st.selectbox("직급", position_options, index=position_idx)
                    
                    # 주소 정보
                    st.subheader("📍 주소 정보")
                    address = st.text_area("집주소", value=employee_data.get('address', ''), placeholder="상세 주소를 입력하세요", height=100, key=f"edit_address_{selected_id}")
                    
                    # 업무 정보
                    st.subheader("업무 정보")
                    col5, col6 = st.columns(2)
                    
                    with col5:
                        # 부서 선택
                        dept_options = ["영업", "서비스", "총무", "회계", "기술", "생산", "품질", "구매", "관리"]
                        current_dept = employee_data.get('department', '영업')
                        try:
                            dept_idx = dept_options.index(current_dept)
                        except ValueError:
                            dept_idx = 0
                        department = st.selectbox("부서", dept_options, index=dept_idx)
                        
                        # 입사일
                        hire_date_str = employee_data.get('hire_date', '2025-01-01')
                        try:
                            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
                        except:
                            hire_date = date.today()
                        hire_date = st.date_input("입사일", value=hire_date)
                    
                    with col6:
                        # 생년월일 (PostgreSQL에서 정상적으로 가져옴)
                        birth_date_str = employee_data.get('birth_date', '1990-01-01')
                        try:
                            # 다양한 날짜 형식 처리
                            if birth_date_str and isinstance(birth_date_str, str):
                                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                            elif hasattr(birth_date_str, 'date'):  # datetime 객체인 경우
                                birth_date = birth_date_str.date()
                            elif isinstance(birth_date_str, date):  # date 객체인 경우
                                birth_date = birth_date_str
                            else:
                                birth_date = date(1990, 1, 1)
                        except:
                            birth_date = date(1990, 1, 1)
                        # 생년월일 입력 (사용자 친화적인 날짜 선택기)
                        birth_date = st.date_input(
                            "생년월일", 
                            value=birth_date,
                            key=f"birth_date_{selected_id}",
                            help="생년월일을 선택해주세요"
                        )
                        
                        # 재직 상태 (status 필드를 work_status로 매핑)
                        status_options = ["재직", "퇴사", "휴직"]
                        current_status = employee_data.get('work_status') or ('재직' if employee_data.get('status') == 'active' else '퇴사')
                        try:
                            status_idx = status_options.index(current_status)
                        except ValueError:
                            status_idx = 0
                        work_status = st.selectbox("재직 상태", status_options, index=status_idx)
                    
                    # 추가 정보
                    st.subheader("추가 정보")
                    col7, col8 = st.columns(2)
                    
                    with col7:
                        # 급여 필드 (현재 DB에 없는 필드이므로 기본값 사용)
                        salary = st.number_input("급여", min_value=0, value=int(employee_data.get('salary', 0)))
                        
                        salary_currency_options = ["KRW", "USD", "VND", "THB", "CNY"]
                        current_currency = employee_data.get('salary_currency', 'KRW')
                        try:
                            currency_idx = salary_currency_options.index(current_currency)
                        except ValueError:
                            currency_idx = 0
                        salary_currency = st.selectbox("급여 통화", salary_currency_options, index=currency_idx)
                    
                    with col8:
                        # 운전면허 필드 (현재 DB에 없는 필드이므로 기본값 사용)
                        license_options = ["없음", "있음"]
                        current_license = employee_data.get('driver_license', '없음')
                        try:
                            license_idx = license_options.index(current_license)
                        except ValueError:
                            license_idx = 0
                        driver_license = st.selectbox("운전면허", license_options, index=license_idx)
                        
                        # 비고 필드 (현재 DB에 없는 필드이므로 기본값 사용)
                        notes = st.text_area("비고", value=employee_data.get('notes', ''))
                    
                    # 권한 설정 (편집 폼에 추가)
                    st.subheader("🔐 권한 설정")
                    access_level_options = ["user", "master"]
                    access_level_labels = {"user": "일반 직원 (제한된 메뉴 접근)", "master": "관리자 (모든 메뉴 접근)"}
                    
                    current_access_level = employee_data.get('access_level', 'user')
                    access_level_index = 0 if current_access_level == 'user' else 1
                    
                    selected_access_level = st.selectbox(
                        "권한 등급 선택하세요:",
                        options=access_level_options,
                        format_func=lambda x: access_level_labels[x],
                        index=access_level_index,
                        key=f"edit_access_level_{selected_id}"
                    )
                    
                    if selected_access_level == "user":
                        st.info("📋 일반 직원 권한: 대시보드, 게시판, 업무진행 상태, 개인 상태관리, 환율관리, 영업관리, 제품관리")
                    else:
                        st.warning("👑 관리자 권한: 모든 시스템 메뉴에 접근 가능")
                    
                    # 수정 버튼
                    col_submit, col_cancel = st.columns([1, 1])
                    
                    with col_submit:
                        submitted = st.form_submit_button("✅ 정보 수정", use_container_width=True, type="primary")
                    
                    with col_cancel:
                        cancel = st.form_submit_button("❌ 취소", use_container_width=True)
                    
                    if submitted:
                        # 수정된 직원 데이터 준비 (SQLite 필드명에 맞춤)
                        updated_employee = {
                            'name': name,
                            'english_name': english_name,
                            'gender': gender,
                            'nationality': edit_selected_nationality,
                            'residence_country': edit_selected_residence_country,
                            'city': edit_selected_city,
                            'address': address,
                            'phone': phone,  # PostgreSQL에서는 phone 필드 사용
                            'email': email,
                            'position': position,
                            'department': department,
                            'hire_date': hire_date.strftime('%Y-%m-%d'),
                            'birth_date': birth_date.strftime('%Y-%m-%d'),
                            'salary': salary,
                            'salary_currency': salary_currency,
                            'driver_license': driver_license,
                            'notes': notes,
                            'work_status': work_status,
                            'status': 'active' if work_status == '재직' else 'inactive',
                            'region': edit_selected_nationality,  # region은 nationality와 동일
                            'access_level': selected_access_level  # 권한 레벨 추가
                            # updated_date는 PostgreSQL 매니저에서 자동 추가
                        }
                        
                        # 직원 정보 수정
                        result = manager.update_employee(selected_id, updated_employee)
                        
                        # SQLiteEmployeeManager는 (success, message) 튜플을 반환
                        if isinstance(result, tuple) and len(result) == 2:
                            success, message = result
                            if success:
                                st.success(f"✅ {message}")
                                st.info("💡 수정된 내용이 저장되었습니다.")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        # 기존 매니저 호환성 (True/False만 반환)
                        elif result:
                            st.success(f"✅ {name}님의 정보가 성공적으로 수정되었습니다!")
                            st.info("💡 수정된 내용이 저장되었습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 직원 정보 수정에 실패했습니다.")
                            st.warning("다시 시도해주세요. 문제가 지속되면 관리자에게 문의하세요.")
                    
                    if cancel:
                        st.info("직원 정보 수정이 취소되었습니다.")
                        st.rerun()
            else:
                st.error("선택한 직원의 정보를 찾을 수 없습니다.")
        else:
            # 직원을 선택하지 않은 경우
            st.info("👆 위에서 편집할 직원을 선택하세요.")
            
            # 빈 편집 폼 표시 (비활성화된 상태)
            with st.form("empty_employee_edit_form"):
                st.subheader("📝 직원 정보 편집")
                st.info("직원을 선택하면 해당 직원의 정보가 로드됩니다.")
                
                # 비활성화된 폼 필드들
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("이름", value="", disabled=True, placeholder="직원을 선택하세요")
                    st.text_input("영문명", value="", disabled=True, placeholder="직원을 선택하세요")
                    st.selectbox("성별", ["남", "여"], disabled=True)
                
                with col2:
                    st.text_input("연락처", value="", disabled=True, placeholder="직원을 선택하세요")
                    st.text_input("이메일", value="", disabled=True, placeholder="직원을 선택하세요")
                    st.selectbox("직급", ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무", "대표"], disabled=True)
                
                # 비활성화된 버튼
                st.form_submit_button("✏️ 정보 수정", disabled=True, help="먼저 편집할 직원을 선택하세요")
    else:
        st.warning("등록된 직원이 없습니다.")

def show_employee_statistics(manager, get_text=lambda x: x):
    """직원 통계 분석"""
    st.header("📊 직원 통계 분석")
    
    # 직원 데이터 가져오기
    import pandas as pd
    from datetime import datetime, date
    import plotly.express as px
    import plotly.graph_objects as go
    
    employees_data = manager.get_all_employees()
    
    # DataFrame 또는 리스트인지 확인
    if isinstance(employees_data, pd.DataFrame):
        if len(employees_data) == 0:
            st.warning("등록된 직원이 없습니다.")
            return
        employees = employees_data.to_dict('records')
    elif isinstance(employees_data, list):
        if len(employees_data) == 0:
            st.warning("등록된 직원이 없습니다.")
            return
        employees = employees_data
    else:
        st.warning("등록된 직원이 없습니다.")
        return
    
    total_employees = len(employees)
    
    # 상단 요약 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 직원 수", f"{total_employees}명")
    
    with col2:
        active_employees = sum(1 for emp in employees if emp.get('work_status') in ['재직', 'active'])
        st.metric("재직 중", f"{active_employees}명")
    
    with col3:
        resigned_employees = sum(1 for emp in employees if emp.get('work_status') == '퇴사')
        st.metric("퇴사", f"{resigned_employees}명")
    
    with col4:
        on_leave_employees = sum(1 for emp in employees if emp.get('work_status') == '휴직')
        st.metric("휴직", f"{on_leave_employees}명")
    
    st.divider()
    
    # 1. 성별 통계
    st.subheader("👥 성별 분포")
    gender_counts = {}
    for emp in employees:
        gender = emp.get('gender', '미분류')
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
    
    if gender_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 성별 파이 차트
            fig_gender = px.pie(
                values=list(gender_counts.values()), 
                names=list(gender_counts.keys()), 
                title="성별 분포"
            )
            st.plotly_chart(fig_gender, use_container_width=True)
        
        with col2:
            # 성별 통계 표
            gender_df = pd.DataFrame({'성별': list(gender_counts.keys()), '인원수': list(gender_counts.values())})
            gender_df['비율'] = (gender_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(gender_df, use_container_width=True, hide_index=True)
    
    # 2. 국적별 통계
    st.subheader("🌏 국적별 분포")
    nationality_counts = {}
    for emp in employees:
        nationality = emp.get('nationality', '미분류')
        nationality_counts[nationality] = nationality_counts.get(nationality, 0) + 1
    
    if nationality_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 국적별 바 차트
            fig_nationality = px.bar(
                x=list(nationality_counts.keys()), 
                y=list(nationality_counts.values()),
                title="국적별 인원수"
            )
            fig_nationality.update_xaxes(title="국적")
            fig_nationality.update_yaxes(title="인원수")
            st.plotly_chart(fig_nationality, use_container_width=True)
        
        with col2:
            # 국적별 통계 표
            nationality_df = pd.DataFrame({'국적': list(nationality_counts.keys()), '인원수': list(nationality_counts.values())})
            nationality_df['비율'] = (nationality_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(nationality_df, use_container_width=True, hide_index=True)
    
    # 3. 나이별 통계 (20대, 30대, 40대, 50대, 60대, 70대)
    st.subheader("📅 연령대별 분포")
    
    def get_age_group(birth_date_str):
        try:
            if not birth_date_str or birth_date_str == '':
                return '미분류'
            
            if isinstance(birth_date_str, str):
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
            else:
                return '미분류'
                
            today = datetime.now()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
                
            if age < 20:
                return '10대'
            elif age < 30:
                return '20대'
            elif age < 40:
                return '30대'
            elif age < 50:
                return '40대'
            elif age < 60:
                return '50대'
            elif age < 70:
                return '60대'
            else:
                return '70대+'
        except:
            return '미분류'
    
    age_group_counts = {}
    for emp in employees:
        age_group = get_age_group(emp.get('birth_date', ''))
        age_group_counts[age_group] = age_group_counts.get(age_group, 0) + 1
    
    if age_group_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 연령대별 바 차트
            age_order = ['10대', '20대', '30대', '40대', '50대', '60대', '70대+', '미분류']
            ordered_ages = [age for age in age_order if age in age_group_counts.keys()]
            ordered_counts = [age_group_counts[age] for age in ordered_ages]
            
            fig_age = px.bar(
                x=ordered_ages, 
                y=ordered_counts,
                title="연령대별 인원수"
            )
            fig_age.update_xaxes(title="연령대")
            fig_age.update_yaxes(title="인원수")
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            # 연령대별 통계 표
            age_df = pd.DataFrame({'연령대': ordered_ages, '인원수': [age_group_counts[age] for age in ordered_ages]})
            age_df['비율'] = (age_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(age_df, use_container_width=True, hide_index=True)
    
    # 4. 거주지별 통계
    st.subheader("🏠 거주지별 분포")
    residence_counts = {}
    for emp in employees:
        residence = emp.get('residence_country', '미분류')
        if residence:
            city = emp.get('city', '')
            if city:
                full_residence = f"{residence} - {city}"
            else:
                full_residence = residence
        else:
            full_residence = '미분류'
        residence_counts[full_residence] = residence_counts.get(full_residence, 0) + 1
    
    if residence_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 거주지별 파이 차트
            fig_residence = px.pie(
                values=list(residence_counts.values()), 
                names=list(residence_counts.keys()), 
                title="거주지별 분포"
            )
            st.plotly_chart(fig_residence, use_container_width=True)
        
        with col2:
            # 거주지별 통계 표
            residence_df = pd.DataFrame({'거주지': list(residence_counts.keys()), '인원수': list(residence_counts.values())})
            residence_df['비율'] = (residence_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(residence_df, use_container_width=True, hide_index=True)
    
    # 5. 부서별 통계
    st.subheader("🏢 부서별 분포")
    dept_counts = {}
    for emp in employees:
        dept = emp.get('department', '미분류')
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    
    if dept_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 부서별 바 차트
            fig_dept = px.bar(
                x=list(dept_counts.keys()), 
                y=list(dept_counts.values()),
                title="부서별 인원수"
            )
            fig_dept.update_xaxes(title="부서")
            fig_dept.update_yaxes(title="인원수")
            st.plotly_chart(fig_dept, use_container_width=True)
        
        with col2:
            # 부서별 통계 표
            dept_df = pd.DataFrame({'부서': list(dept_counts.keys()), '인원수': list(dept_counts.values())})
            dept_df['비율'] = (dept_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(dept_df, use_container_width=True, hide_index=True)
    
    # 6. 직급별 통계 
    st.subheader("👔 직급별 분포")
    position_counts = {}
    for emp in employees:
        position = emp.get('position', '미분류')
        position_counts[position] = position_counts.get(position, 0) + 1
    
    if position_counts:
        col1, col2 = st.columns(2)
        with col1:
            # 직급별 바 차트
            fig_position = px.bar(
                x=list(position_counts.keys()), 
                y=list(position_counts.values()),
                title="직급별 인원수"
            )
            fig_position.update_xaxes(title="직급")
            fig_position.update_yaxes(title="인원수")
            st.plotly_chart(fig_position, use_container_width=True)
        
        with col2:
            # 직급별 통계 표
            position_df = pd.DataFrame({'직급': list(position_counts.keys()), '인원수': list(position_counts.values())})
            position_df['비율'] = (position_df['인원수'] / total_employees * 100).round(1)
            st.dataframe(position_df, use_container_width=True, hide_index=True)

def show_employee_permissions(manager, auth_manager, get_text=lambda x: x):
    """직원 권한 관리 페이지"""
    st.header("🔐 직원 권한 관리")
    
    # 직원 목록 가져오기
    employees = manager.get_all_employees()
    
    # DataFrame인지 확인하고 적절히 처리
    import pandas as pd
    if isinstance(employees, pd.DataFrame):
        if len(employees) == 0:
            st.warning("등록된 직원이 없습니다.")
            return
    else:
        if not employees or len(employees) == 0:
            st.warning("등록된 직원이 없습니다.")
            return
    
    # 직원 선택
    if isinstance(employees, list):
        employee_options = [f"{emp['name']} ({emp['employee_id']})" for emp in employees if isinstance(emp, dict)]
    else:
        employee_options = [f"{row['name']} ({row['employee_id']})" for _, row in employees.iterrows()]
    
    selected_employee = st.selectbox(
        "권한을 설정할 직원 선택:",
        employee_options,
        key="permission_employee_select"
    )
    
    if selected_employee:
        # 직원 ID 추출
        selected_id = selected_employee.split("(")[1].split(")")[0]
        employee_name = selected_employee.split("(")[0].strip()
        
        # 현재 직원 정보 가져오기 (DB에서 최신 정보 조회)
        employee_data = manager.get_employee_by_id(selected_id)
        if not employee_data or len(employee_data) == 0:
            st.error("직원 정보를 찾을 수 없습니다.")
            return
        
        # 권한 정보를 명시적으로 재조회
        current_access_level = employee_data.get('access_level', 'user')
        
        st.markdown("---")
        st.subheader(f"👤 {employee_name}의 권한 관리")
        
        # 현재 권한 상태 표시
        st.subheader("현재 권한 상태")
        col1, col2 = st.columns(2)
        
        with col1:
            if current_access_level == 'ceo':
                st.success("👑 법인장 권한")
                st.write("**접근 가능한 메뉴:**")
                st.write("• 모든 시스템 메뉴")
            elif current_access_level == 'admin':
                st.warning("👔 총무 권한")
                st.write("**접근 가능한 메뉴:**")
                st.write("• 총무 전용 메뉴 포함")
            elif current_access_level == 'master':
                st.success("🔧 마스터 권한")
                st.write("**접근 가능한 메뉴:**")
                st.write("• 모든 시스템 메뉴")
            else:
                st.info("📋 일반 직원")
                st.write("**접근 가능한 메뉴:**")
                st.write("• 기본 메뉴만")
        
        with col2:
            # 권한 변경 섹션
            st.write("**권한 등급 선택:**")
            
            # 3단계 권한 옵션
            access_options = {
                'user': '📋 일반 직원',
                'admin': '👔 총무',
                'ceo': '👑 법인장'
            }
            
            # 현재 권한에 따른 기본값 설정
            if current_access_level == 'user':
                current_index = 0
            elif current_access_level == 'admin':
                current_index = 1
            elif current_access_level == 'ceo':
                current_index = 2
            else:  # master 또는 기타
                current_index = 0
            
            # 라디오 버튼으로 권한 선택
            selected_access_label = st.radio(
                "권한 등급을 선택하세요:",
                list(access_options.values()),
                index=current_index,
                key="access_level_radio"
            )
            
            # 선택된 라벨에서 키 찾기
            new_access_level = None
            for key, value in access_options.items():
                if value == selected_access_label:
                    new_access_level = key
                    break
        
            # 권한 변경 버튼
            if st.button("권한 적용", type="primary"):
                if new_access_level == current_access_level:
                    st.info("현재와 동일한 권한입니다.")
                else:
                    update_data = {'access_level': new_access_level}
                    success, message = manager.update_employee(selected_id, update_data)
                    if success:
                        level_name = access_options.get(new_access_level or 'user', '일반 직원')
                        st.success(f"✅ {employee_name}님의 권한이 {level_name}로 변경되었습니다!")
                        st.rerun()  # 페이지 새로고침으로 최신 권한 반영
                    else:
                        st.error(f"❌ 권한 변경에 실패했습니다: {message}")
    
    # 상세 권한 현황 표시
    st.markdown("---")
    st.subheader("📊 상세 권한 현황")
    
    # 모든 직원의 권한 정보를 테이블로 표시 (최신 데이터 재조회)
    fresh_employees = manager.get_all_employees()  # 최신 데이터 재조회
    permission_data = []
    
    # 권한 정보 처리 (디버그 제거)
    
    for emp in (fresh_employees if isinstance(fresh_employees, list) else fresh_employees.to_dict('records')):
        if isinstance(emp, dict):
            access_level = emp.get('access_level', 'user')
            
            # 권한 라벨 설정
            if access_level == 'ceo':
                permission_label = '👑 법인장'
            elif access_level == 'admin':
                permission_label = '👔 총무'
            elif access_level == 'master':
                permission_label = '🔧 마스터'
            else:
                permission_label = '📋 일반 직원'
            
            permission_data.append({
                '직원명': emp.get('name', ''),
                '사번': emp.get('employee_id', ''),
                '부서': emp.get('department', ''),
                '직급': emp.get('position', ''),
                '권한': permission_label,
                '상태': emp.get('work_status', '')
            })
    
    if permission_data:
        import pandas as pd
        df = pd.DataFrame(permission_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    return
    
    # 권한 관리 기능 구현
    employees = manager.get_all_employees()
    if len(employees) > 0:
        employee_options = [f"{emp['name']} ({emp['employee_id']})" for emp in employees]
        selected_employee = st.selectbox("권한을 설정할 직원 선택", employee_options)
        
        if selected_employee:
            selected_id = selected_employee.split("(")[1].split(")")[0]
            employee_name = selected_employee.split("(")[0].strip()
            
            # 권한 설정 섹션
            st.markdown("---")
            st.subheader(f"👤 {employee_name}의 권한 설정")
            
            # 현재 권한 표시
            current_permissions = auth_manager.get_user_permissions(selected_id)
            
            # 현재 권한 요약 표시
            st.subheader("📋 현재 권한 요약")
            
            # 권한 상태 시각화
            col_status1, col_status2, col_status3 = st.columns(3)
            
            with col_status1:
                st.write("**기본 시스템**")
                basic_permissions = [
                    ('직원 관리', current_permissions.get('can_access_employee_management', False)),
                    ('고객 관리', current_permissions.get('can_access_customer_management', False)),
                    ('제품 관리', current_permissions.get('can_access_product_management', False)),
                    ('견적 관리', current_permissions.get('can_access_quotation_management', False)),
                    ('공급업체 관리', current_permissions.get('can_access_supplier_management', False))
                ]
                for name, status in basic_permissions:
                    icon = "✅" if status else "❌"
                    st.write(f"{icon} {name}")
            
            with col_status2:
                st.write("**비즈니스 프로세스**")
                business_permissions = [
                    ('비즈니스 프로세스', current_permissions.get('can_access_business_process_management', False)),
                    ('발주 관리', current_permissions.get('can_access_purchase_order_management', False)),
                    ('재고 관리', current_permissions.get('can_access_inventory_management', False)),
                    ('배송 관리', current_permissions.get('can_access_shipping_management', False)),
                    ('승인 관리', current_permissions.get('can_access_approval_management', False))
                ]
                for name, status in business_permissions:
                    icon = "✅" if status else "❌"
                    st.write(f"{icon} {name}")
            
            with col_status3:
                st.write("**재무/시스템 관리**")
                finance_permissions = [
                    ('현금 흐름 관리', current_permissions.get('can_access_cash_flow_management', False)),
                    ('인보이스 관리', current_permissions.get('can_access_invoice_management', False)),
                    ('표준 판매가 관리', current_permissions.get('can_access_sales_product_management', False)),
                    ('환율 현황', current_permissions.get('can_access_exchange_rate_management', False)),
                    ('PDF 디자인 관리', current_permissions.get('can_access_pdf_design_management', False))
                ]
                for name, status in finance_permissions:
                    icon = "✅" if status else "❌"
                    st.write(f"{icon} {name}")
            
            # 특수 권한 표시
            st.write("**특수 권한**")
            col_special1, col_special2 = st.columns(2)
            with col_special1:
                personal_status = "✅" if current_permissions.get('can_access_personal_status', False) else "❌"
                vacation_mgmt = "✅" if current_permissions.get('can_access_vacation_management', False) else "❌"
                st.write(f"{personal_status} 개인 상태 관리")
                st.write(f"{vacation_mgmt} 휴가 관리")
            with col_special2:
                delete_data = "✅" if current_permissions.get('can_delete_data', False) else "❌"
                st.write(f"{delete_data} 데이터 삭제 권한")
            
            # JSON 상세 정보는 expander로
            with st.expander("권한 JSON 상세 정보"):
                st.json(current_permissions)
            
            # 빠른 설정 버튼들 (폼 밖에서)
            st.subheader("🚀 빠른 권한 설정")
            st.info("아래 버튼을 클릭하면 해당 권한 세트가 자동으로 적용됩니다.")
            
            col_preset1, col_preset2, col_preset3 = st.columns(3)
            
            # 권한 프리셋 세션 상태 키
            preset_key = f"permission_preset_{selected_id}"
            
            # 빠른 설정 - 모든 권한 허용
            with col_preset1:
                if st.button("🔓 모든 권한 허용", type="secondary", use_container_width=True, key=f"all_perms_{selected_id}"):
                    all_permissions = {
                        'can_access_employee_management': True,
                        'can_access_customer_management': True,
                        'can_access_product_management': True,
                        'can_access_quotation_management': True,
                        'can_access_supplier_management': True,
                        'can_access_business_process_management': True,
                        'can_access_purchase_order_management': True,
                        'can_access_inventory_management': True,
                        'can_access_shipping_management': True,
                        'can_access_approval_management': True,
                        'can_access_cash_flow_management': True,
                        'can_access_invoice_management': True,
                        'can_access_sales_product_management': True,
                        'can_access_exchange_rate_management': True,
                        'can_access_pdf_design_management': True,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': True,
                        'can_delete_data': True
                    }
                    st.session_state[preset_key] = all_permissions
                    st.success("✅ 모든 권한이 선택되었습니다! 아래 폼에서 확인 후 '권한 저장'을 클릭하세요.")
                    # st.rerun() 제거됨
            
            # 빠른 설정 - 기본 직원 권한
            with col_preset2:
                if st.button("👤 기본 직원 권한", type="secondary", use_container_width=True, key=f"basic_perms_{selected_id}"):
                    basic_permissions = {
                        'can_access_employee_management': False,
                        'can_access_customer_management': True,
                        'can_access_product_management': True,
                        'can_access_quotation_management': True,
                        'can_access_supplier_management': True,
                        'can_access_business_process_management': False,
                        'can_access_purchase_order_management': False,
                        'can_access_inventory_management': False,
                        'can_access_shipping_management': False,
                        'can_access_approval_management': False,
                        'can_access_cash_flow_management': False,
                        'can_access_invoice_management': False,
                        'can_access_sales_product_management': False,
                        'can_access_exchange_rate_management': True,
                        'can_access_pdf_design_management': False,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': False,
                        'can_delete_data': False
                    }
                    st.session_state[preset_key] = basic_permissions
                    st.success("✅ 기본 직원 권한이 선택되었습니다! 아래 폼에서 확인 후 '권한 저장'을 클릭하세요.")
                    # st.rerun() 제거됨
            
            # 빠른 설정 - 관리자 권한
            with col_preset3:
                if st.button("⚡ 관리자 권한", type="secondary", use_container_width=True, key=f"admin_perms_{selected_id}"):
                    admin_permissions = {
                        'can_access_employee_management': True,
                        'can_access_customer_management': True,
                        'can_access_product_management': True,
                        'can_access_quotation_management': True,
                        'can_access_supplier_management': True,
                        'can_access_business_process_management': True,
                        'can_access_purchase_order_management': True,
                        'can_access_inventory_management': True,
                        'can_access_shipping_management': True,
                        'can_access_approval_management': True,
                        'can_access_cash_flow_management': True,
                        'can_access_invoice_management': True,
                        'can_access_sales_product_management': True,
                        'can_access_exchange_rate_management': True,
                        'can_access_pdf_design_management': True,
                        'can_access_personal_status': True,
                        'can_access_vacation_management': True,
                        'can_delete_data': False  # 삭제 권한은 별도
                    }
                    st.session_state[preset_key] = admin_permissions
                    st.success("✅ 관리자 권한이 선택되었습니다! 아래 폼에서 확인 후 '권한 저장'을 클릭하세요.")
                    # st.rerun() 제거됨
            
            st.markdown("---")
            
            # 권한 설정 폼
            with st.form("permission_form"):
                st.subheader("🔧 세부 권한 설정")
                st.info("개별 권한을 세밀하게 조정하려면 아래 체크박스를 사용하세요.")
                
                # 프리셋이나 현재 권한 사용
                preset_permissions = st.session_state.get(preset_key, current_permissions)
                
                # 전체 시스템 권한들
                permissions = {}
                
                # 기본 시스템 권한들
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**기본 시스템**")
                    permissions['can_access_employee_management'] = st.checkbox("직원 관리", value=preset_permissions.get('can_access_employee_management', False))
                    permissions['can_access_customer_management'] = st.checkbox("고객 관리", value=preset_permissions.get('can_access_customer_management', False))
                    permissions['can_access_product_management'] = st.checkbox("제품 관리", value=preset_permissions.get('can_access_product_management', False))
                    permissions['can_access_quotation_management'] = st.checkbox("견적 관리", value=preset_permissions.get('can_access_quotation_management', False))
                    permissions['can_access_supplier_management'] = st.checkbox("공급업체 관리", value=preset_permissions.get('can_access_supplier_management', False))
                
                with col2:
                    st.write("**비즈니스 프로세스**")
                    permissions['can_access_business_process_management'] = st.checkbox("비즈니스 프로세스", value=preset_permissions.get('can_access_business_process_management', False))
                    permissions['can_access_purchase_order_management'] = st.checkbox("발주 관리", value=preset_permissions.get('can_access_purchase_order_management', False))
                    permissions['can_access_inventory_management'] = st.checkbox("재고 관리", value=preset_permissions.get('can_access_inventory_management', False))
                    permissions['can_access_shipping_management'] = st.checkbox("배송 관리", value=preset_permissions.get('can_access_shipping_management', False))
                    permissions['can_access_approval_management'] = st.checkbox("승인 관리", value=preset_permissions.get('can_access_approval_management', False))
                
                with col3:
                    st.write("**재무/시스템 관리**")
                    permissions['can_access_cash_flow_management'] = st.checkbox("현금 흐름 관리", value=preset_permissions.get('can_access_cash_flow_management', False))
                    permissions['can_access_invoice_management'] = st.checkbox("인보이스 관리", value=preset_permissions.get('can_access_invoice_management', False))
                    permissions['can_access_sales_product_management'] = st.checkbox("표준 판매가 관리", value=preset_permissions.get('can_access_sales_product_management', False))
                    permissions['can_access_exchange_rate_management'] = st.checkbox("환율 현황", value=preset_permissions.get('can_access_exchange_rate_management', False))
                    permissions['can_access_pdf_design_management'] = st.checkbox("PDF 디자인 관리", value=preset_permissions.get('can_access_pdf_design_management', False))
                
                st.markdown("---")
                st.write("**특수 권한**")
                col_special1, col_special2 = st.columns(2)
                
                with col_special1:
                    # 개인 상태 관리는 모든 직원이 기본적으로 접근 가능
                    permissions['can_access_personal_status'] = st.checkbox("개인 상태 관리", value=preset_permissions.get('can_access_personal_status', True))
                    permissions['can_access_vacation_management'] = st.checkbox("휴가 관리", value=preset_permissions.get('can_access_vacation_management', False))
                
                with col_special2:
                    permissions['can_delete_data'] = st.checkbox("데이터 삭제 권한", value=preset_permissions.get('can_delete_data', False))
                
                submitted = st.form_submit_button("권한 저장", type="primary")
                
                if submitted:
                    try:
                        # 권한 업데이트
                        success = auth_manager.update_user_permissions(selected_id, permissions)
                        
                        if success:
                            # 프리셋 세션 상태 초기화
                            if preset_key in st.session_state:
                                del st.session_state[preset_key]
                            
                            st.success(f"✅ {employee_name}의 권한이 성공적으로 업데이트되었습니다!")
                            
                            # st.rerun() 제거됨
                        else:
                            st.error("❌ 권한 업데이트에 실패했습니다.")
                    except Exception as e:
                        st.error(f"❌ 권한 업데이트 중 오류가 발생했습니다: {str(e)}")
    else:
        st.warning("등록된 직원이 없습니다.")

def show_employee_bulk_registration(manager, get_text=lambda x: x):
    """직원 대량 등록 페이지"""
    st.header("📤 직원 대량 등록")
    
    # 템플릿 다운로드
    st.subheader("1. 템플릿 다운로드")
    template_data = pd.DataFrame({
        'name': ['홍길동', '김철수'],
        'english_name': ['Hong Gil Dong', 'Kim Chul Soo'],
        'gender': ['남', '남'],
        'nationality': ['한국', '한국'],
        'residence_country': ['한국', '한국'],
        'city': ['서울', '부산'],
        'contact': ['010-1234-5678', '010-9876-5432'],
        'email': ['hong@company.com', 'kim@company.com'],
        'position': ['사원', '대리'],
        'hire_date': ['2024-01-01', '2024-01-15'],
        'birth_date': ['1990-01-01', '1985-05-15'],
        'salary': [3000000, 4000000],
        'salary_currency': ['KRW', 'KRW'],
        'driver_license': ['1종보통', '2종보통'],
        'notes': ['', '']
    })
    
    csv_buffer = io.StringIO()
    template_data.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 템플릿 다운로드",
        data=csv_buffer.getvalue().encode('utf-8-sig'),
        file_name="employee_template.csv",
        mime="text/csv"
    )
    
    # 파일 업로드
    st.subheader("2. 파일 업로드")
    uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # 파일 읽기
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            st.subheader("3. 데이터 미리보기")
            st.dataframe(df.head(), use_container_width=True)
            
            # 대량 등록 버튼
            if st.button("🚀 대량 등록 실행", type="primary"):
                success_count = 0
                error_count = 0
                error_messages = []
                
                for row_num, row in enumerate(df, 1):
                    try:
                        employee_data = {
                            'name': row['name'],
                            'english_name': row.get('english_name', ''),
                            'gender': row.get('gender', '남'),
                            'nationality': row.get('nationality', '한국'),
                            'residence_country': row.get('residence_country', '한국'),
                            'city': row.get('city', ''),
                            'contact': format_phone_number(row.get('contact', '')),
                            'email': row.get('email', ''),
                            'position': row.get('position', '사원'),
                            'hire_date': row.get('hire_date', ''),
                            'birth_date': row.get('birth_date', ''),
                            'salary': row.get('salary', 0),
                            'salary_currency': row.get('salary_currency', 'KRW'),
                            'driver_license': row.get('driver_license', ''),
                            'notes': row.get('notes', ''),
                            'work_status': '재직',
                            'status': '활성',
                            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        if manager.add_employee(employee_data):
                            success_count += 1
                        else:
                            error_count += 1
                            error_messages.append(f"행 {row_num}: {row['name']} - 등록 실패")
                    
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"행 {row_num}: {str(e)}")
                
                # 결과 표시
                if success_count > 0:
                    st.success(f"✅ {success_count}명의 직원이 성공적으로 등록되었습니다!")
                
                if error_count > 0:
                    st.error(f"❌ {error_count}명의 직원 등록이 실패했습니다.")
                    with st.expander("오류 상세 내용"):
                        for error in error_messages:
                            st.write(f"- {error}")
                
                if success_count > 0:
                    st.info("등록이 완료되었습니다.")
        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")
            st.info("UTF-8 인코딩으로 저장된 CSV 파일을 업로드해주세요.")

def show_annual_leave_management(manager, get_text=lambda x: x):
    """연차 관리 탭"""
    st.header("🏖️ 연차 관리")
    
    # 모든 직원 데이터 가져오기
    employees_df = manager.get_all_employees()
    
    if len(employees_df) == 0:
        st.info("등록된 직원이 없습니다.")
        return
    
    # 직원별 연차 현황 표시
    st.subheader("📊 직원별 연차 현황")
    
    # 연차 현황 요약 테이블 (휴가 사용량 포함)
    annual_leave_data = []
    
    # VacationManager import
    from managers.sqlite.sqlite_vacation_manager import SQLiteVacationManager
    vacation_manager = SQLiteVacationManager()
    
    # DataFrame과 list 처리
    import pandas as pd
    if isinstance(employees_df, pd.DataFrame):
        employees_list = employees_df.to_dict('records')
    else:
        employees_list = employees_df if employees_df else []
    
    for employee in employees_list:
        employee_id = str(employee['employee_id'])
        name = employee.get('name', 'N/A')
        annual_days = employee.get('annual_leave_days', 15)
        if pd.isna(annual_days):
            annual_days = 15
        
        # 휴가 사용량 계산
        vacation_summary = vacation_manager.get_vacation_summary(employee_id)
        used_days = vacation_summary.get('used_vacation_days', 0)
        remaining_days = vacation_summary.get('remaining_vacation_days', annual_days)
        
        # 휴가 상태 표시
        used_days = used_days or 0
        remaining_days = remaining_days or annual_days
        
        if used_days == 0:
            vacation_status = "😊 미사용"
        elif remaining_days <= 2:
            vacation_status = "⚠️ 잔여 적음"
        elif used_days >= annual_days * 0.8:
            vacation_status = "📈 많이 사용"
        else:
            vacation_status = "✅ 정상"
        
        annual_leave_data.append({
            '사번': employee_id,
            '이름': name,
            '연차 일수': int(annual_days),
            '사용일': f"{used_days}일",
            '잔여일': f"{remaining_days}일",
            '휴가 상태': vacation_status,
            '부서': employee.get('department', ''),
            '직급': employee.get('position', '')
        })
    
    if annual_leave_data:
        df_display = pd.DataFrame(annual_leave_data)
        st.dataframe(df_display, use_container_width=True)
        
        # 연차 일수 수정 섹션
        st.subheader("✏️ 연차 일수 수정")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # 직원 선택
            employee_options = [f"{emp['사번']} - {emp['이름']}" for emp in annual_leave_data]
            selected_employee = st.selectbox("수정할 직원 선택", employee_options)
        
        with col2:
            # 새로운 연차 일수 입력
            new_annual_days = st.number_input("새 연차 일수", min_value=0, max_value=30, value=15)
        
        with col3:
            # 수정 버튼
            if st.button("연차 수정", type="primary"):
                if selected_employee:
                    employee_id = selected_employee.split(' - ')[0]
                    
                    # 연차 일수 업데이트
                    if manager.update_annual_leave_days(employee_id, new_annual_days):
                        st.success(f"직원 {employee_id}의 연차가 {new_annual_days}일로 수정되었습니다.")
                        # st.rerun() 제거됨
                    else:
                        st.error("연차 수정에 실패했습니다.")
        
        # 일괄 연차 설정 섹션
        st.subheader("🔄 일괄 연차 설정")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            bulk_annual_days = st.number_input("일괄 설정할 연차 일수", min_value=0, max_value=30, value=15)
        
        with col2:
            if st.button("모든 직원 일괄 설정", type="secondary"):
                success_count = 0
                # employees_df 대신 employees_list 사용
                employees_data = manager.get_all_employees()
                if isinstance(employees_data, pd.DataFrame):
                    employees_list = employees_data.to_dict('records')
                else:
                    employees_list = employees_data if employees_data else []
                    
                for employee in employees_list:
                    employee_id = str(employee['employee_id'])
                    if manager.update_annual_leave_days(employee_id, bulk_annual_days):
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"{success_count}명의 직원 연차가 {bulk_annual_days}일로 설정되었습니다.")
                    # st.rerun() 제거됨
                else:
                    st.error("일괄 설정에 실패했습니다.")
        
        # 연차 통계
        st.subheader("📈 연차 통계")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_employees = len(annual_leave_data)
            st.metric("전체 직원 수", f"{total_employees}명")
        
        with col2:
            avg_annual_days = sum(emp['연차 일수'] for emp in annual_leave_data) / len(annual_leave_data)
            st.metric("평균 연차 일수", f"{avg_annual_days:.1f}일")
        
        with col3:
            total_annual_days = sum(emp['연차 일수'] for emp in annual_leave_data)
            st.metric("총 연차 일수", f"{total_annual_days}일")
    
    else:
        st.info("연차 데이터가 없습니다.")

def show_password_management(manager, auth_manager, get_text=lambda x: x):
    """비밀번호 관리 기능 - 개선된 UI"""
    st.header("🔑 직원 비밀번호 관리")
    
    # 직원 목록 가져오기
    import pandas as pd
    import psycopg2
    from datetime import datetime
    
    employees_data = manager.get_all_employees()
    
    # DataFrame과 list 처리
    if isinstance(employees_data, pd.DataFrame):
        if len(employees_data) == 0:
            st.info("등록된 직원이 없습니다.")
            return
        employees_list = employees_data.to_dict('records')
    elif isinstance(employees_data, list):
        if len(employees_data) == 0:
            st.info("등록된 직원이 없습니다.")
            return
        employees_list = employees_data
    else:
        st.info("등록된 직원이 없습니다.")
        return
    
    # 탭으로 기능 분리
    tab1, tab2, tab3 = st.tabs(["🔐 개별 비밀번호 재설정", "👥 일괄 초기화", "📊 계정 상태"])
    
    with tab1:
        st.subheader("👤 개별 비밀번호 재설정")
        
        # 직원 검색 필터
        col_search, col_dept = st.columns([2, 1])
        with col_search:
            search_term = st.text_input("🔍 직원 검색 (이름/사번)", placeholder="검색어 입력...")
        with col_dept:
            departments = list(set([emp.get('department', '전체') for emp in employees_list]))
            departments = ['전체'] + sorted([d for d in departments if d])
            selected_dept = st.selectbox("부서 필터", departments)
        
        # 필터링된 직원 목록
        filtered_employees = []
        for emp in employees_list:
            if search_term and search_term.lower() not in emp.get('name', '').lower() and search_term not in str(emp.get('employee_id', '')):
                continue
            if selected_dept != '전체' and emp.get('department', '') != selected_dept:
                continue
            filtered_employees.append(emp)
        
        if filtered_employees:
            # 직원 카드 형태로 표시
            st.markdown("---")
            
            # 직원 선택
            employee_options = []
            for emp in filtered_employees:
                employee_id = str(emp['employee_id'])
                name = emp.get('name', '')
                dept = emp.get('department', '')
                position = emp.get('position', '')
                employee_options.append({
                    'label': f"{employee_id} - {name} ({dept} / {position})",
                    'id': employee_id,
                    'name': name
                })
            
            selected_index = st.selectbox(
                "직원 선택",
                range(len(employee_options)),
                format_func=lambda x: employee_options[x]['label'],
                key="emp_select_for_password"
            )
            
            if selected_index is not None:
                selected_emp = employee_options[selected_index]
                
                # 선택된 직원 정보 카드
                with st.container():
                    st.info(f"**선택된 직원:** {selected_emp['name']} (사번: {selected_emp['id']})")
                    
                    # 비밀번호 설정 폼
                    with st.form("password_reset_form", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_password = st.text_input(
                                "새 비밀번호",
                                type="password",
                                placeholder="새 비밀번호 입력",
                                help="최소 4자리 이상"
                            )
                        
                        with col2:
                            confirm_password = st.text_input(
                                "비밀번호 확인",
                                type="password",
                                placeholder="비밀번호 다시 입력"
                            )
                        
                        # PostgreSQL 직접 연결 사용
                        use_default = st.checkbox("기본 비밀번호(1111)로 초기화", value=False)
                        
                        submitted = st.form_submit_button("🔄 비밀번호 재설정", use_container_width=True, type="primary")
                        
                        if submitted:
                            if use_default:
                                # 기본 비밀번호로 설정
                                try:
                                    conn = psycopg2.connect(
                                        host=st.secrets["postgres"]["host"],
                                        port=st.secrets["postgres"]["port"],
                                        database=st.secrets["postgres"]["database"],
                                        user=st.secrets["postgres"]["user"],
                                        password=st.secrets["postgres"]["password"]
                                    )
                                    cursor = conn.cursor()
                                    
                                    cursor.execute("""
                                        UPDATE employees 
                                        SET password = NULL,
                                            password_change_required = TRUE,
                                            login_attempts = 0,
                                            account_locked_until = NULL
                                        WHERE employee_id = %s
                                    """, (selected_emp['id'],))
                                    
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    
                                    st.success(f"✅ {selected_emp['name']}님의 비밀번호가 기본값(1111)으로 초기화되었습니다.")
                                except Exception as e:
                                    st.error(f"오류 발생: {e}")
                            else:
                                # 새 비밀번호로 설정
                                if not new_password:
                                    st.error("비밀번호를 입력해주세요.")
                                elif new_password != confirm_password:
                                    st.error("비밀번호가 일치하지 않습니다.")
                                elif len(new_password) < 4:
                                    st.error("비밀번호는 최소 4자리 이상이어야 합니다.")
                                else:
                                    try:
                                        import bcrypt
                                        
                                        # bcrypt 해시 생성
                                        hashed = bcrypt.hashpw(
                                            new_password.encode('utf-8'),
                                            bcrypt.gensalt()
                                        ).decode('utf-8')
                                        
                                        conn = psycopg2.connect(
                                            host=st.secrets["postgres"]["host"],
                                            port=st.secrets["postgres"]["port"],
                                            database=st.secrets["postgres"]["database"],
                                            user=st.secrets["postgres"]["user"],
                                            password=st.secrets["postgres"]["password"]
                                        )
                                        cursor = conn.cursor()
                                        
                                        cursor.execute("""
                                            UPDATE employees 
                                            SET password = %s,
                                                password_changed_date = NOW(),
                                                password_change_required = FALSE,
                                                login_attempts = 0,
                                                account_locked_until = NULL
                                            WHERE employee_id = %s
                                        """, (hashed, selected_emp['id']))
                                        
                                        conn.commit()
                                        cursor.close()
                                        conn.close()
                                        
                                        st.success(f"✅ {selected_emp['name']}님의 비밀번호가 변경되었습니다.")
                                    except Exception as e:
                                        st.error(f"오류 발생: {e}")
        else:
            st.warning("검색 결과가 없습니다.")
    
    with tab2:
        st.subheader("👥 일괄 비밀번호 초기화")
        
        st.warning("⚠️ 선택한 모든 직원의 비밀번호가 기본값(1111)으로 초기화됩니다.")
        
        # 부서별 선택
        col1, col2 = st.columns(2)
        
        with col1:
            dept_options = ['전체'] + sorted(list(set([emp.get('department', '') for emp in employees_list if emp.get('department')])))
            selected_bulk_dept = st.selectbox("부서 선택", dept_options, key="bulk_dept")
        
        with col2:
            if selected_bulk_dept == '전체':
                target_count = len(employees_list)
            else:
                target_count = len([emp for emp in employees_list if emp.get('department') == selected_bulk_dept])
            st.metric("대상 직원 수", f"{target_count}명")
        
        # 안전 확인
        confirm_text = st.text_input("확인을 위해 'RESET'을 입력하세요", placeholder="RESET")
        
        if st.button("🔄 일괄 초기화", type="secondary", use_container_width=True):
            if confirm_text != "RESET":
                st.error("확인 문자를 정확히 입력해주세요.")
            else:
                try:
                    conn = psycopg2.connect(
                        host=st.secrets["postgres"]["host"],
                        port=st.secrets["postgres"]["port"],
                        database=st.secrets["postgres"]["database"],
                        user=st.secrets["postgres"]["user"],
                        password=st.secrets["postgres"]["password"]
                    )
                    cursor = conn.cursor()
                    
                    if selected_bulk_dept == '전체':
                        cursor.execute("""
                            UPDATE employees 
                            SET password = NULL,
                                password_change_required = TRUE,
                                login_attempts = 0,
                                account_locked_until = NULL
                        """)
                    else:
                        cursor.execute("""
                            UPDATE employees 
                            SET password = NULL,
                                password_change_required = TRUE,
                                login_attempts = 0,
                                account_locked_until = NULL
                            WHERE department = %s
                        """, (selected_bulk_dept,))
                    
                    affected_rows = cursor.rowcount
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    st.success(f"✅ {affected_rows}명의 비밀번호가 초기화되었습니다.")
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    
    with tab3:
        st.subheader("📊 계정 상태 현황")
        
        # 상태 통계
        col1, col2, col3, col4 = st.columns(4)
        
        total_count = len(employees_list)
        with col1:
            st.metric("전체 직원", f"{total_count}명")
        
        # PostgreSQL에서 실제 상태 조회
        try:
            conn = psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                port=st.secrets["postgres"]["port"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"]
            )
            cursor = conn.cursor()
            
            # 비밀번호 설정 상태 조회
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN password IS NOT NULL THEN 1 END) as password_set,
                    COUNT(CASE WHEN password_change_required = TRUE THEN 1 END) as change_required,
                    COUNT(CASE WHEN account_locked_until > NOW() THEN 1 END) as locked
                FROM employees
            """)
            
            result = cursor.fetchone()
            password_set = result[0] if result else 0
            change_required = result[1] if result else 0
            locked_count = result[2] if result else 0
            
            with col2:
                st.metric("비밀번호 설정됨", f"{password_set}명")
            with col3:
                st.metric("변경 필요", f"{change_required}명", delta="-" if change_required > 0 else None)
            with col4:
                st.metric("계정 잠김", f"{locked_count}명", delta="-" if locked_count > 0 else None)
            
            # 상세 테이블
            st.markdown("---")
            cursor.execute("""
                SELECT 
                    employee_id,
                    name,
                    department,
                    CASE 
                        WHEN password IS NULL THEN '미설정'
                        ELSE '설정됨'
                    END as password_status,
                    CASE 
                        WHEN password_change_required = TRUE THEN '필요'
                        ELSE '-'
                    END as change_status,
                    login_attempts,
                    CASE 
                        WHEN account_locked_until > NOW() THEN '잠김'
                        ELSE '정상'
                    END as lock_status
                FROM employees
                ORDER BY employee_id
            """)
            
            results = cursor.fetchall()
            
            if results:
                df = pd.DataFrame(results, columns=[
                    '사번', '이름', '부서', '비밀번호', '변경필요', '로그인시도', '계정상태'
                ])
                
                # 스타일링 적용
                def highlight_status(row):
                    styles = [''] * len(row)
                    if row['계정상태'] == '잠김':
                        styles = ['background-color: #ffcccc'] * len(row)
                    elif row['변경필요'] == '필요':
                        styles = ['background-color: #ffffcc'] * len(row)
                    return styles
                
                styled_df = df.style.apply(highlight_status, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # 범례
                col_legend1, col_legend2, col_legend3 = st.columns(3)
                with col_legend1:
                    st.caption("🔴 계정 잠김")
                with col_legend2:
                    st.caption("🟡 비밀번호 변경 필요")
                with col_legend3:
                    st.caption("⚪ 정상")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"상태 조회 중 오류: {e}")


def show_employee_delete(manager, get_text=lambda x: x):
    """직원 삭제 전용 탭"""
    st.header("🗑️ 직원 삭제")
    
    # 안전 경고
    st.warning("⚠️ **주의**: 삭제된 직원 정보는 복구할 수 없습니다. 신중하게 선택하세요.")
    
    # 현재 직원 목록 가져오기
    employees = manager.get_all_employees()
    
    if len(employees) == 0:
        st.info("삭제할 직원이 없습니다.")
        return
    
    # 직원 목록 표시 (삭제용)
    st.subheader("📋 현재 직원 목록")
    
    # 표시용 데이터프레임 준비
    display_columns = ['employee_id', 'name', 'english_name', 'position', 'department', 'work_status']
    available_columns = [col for col in display_columns if col in employees.columns]
    
    if available_columns:
        display_df = employees[available_columns].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # 삭제할 직원 선택
        st.subheader("🎯 삭제할 직원 선택")
        
        col_select, col_info = st.columns([2, 2])
        
        with col_select:
            employee_options = []
            for _, emp in employees.iterrows():
                emp_id = str(emp.get('employee_id', ''))
                emp_name = emp.get('name', '알 수 없음')
                emp_position = emp.get('position', '직책 미상')
                emp_department = emp.get('department', '부서 미상')
                employee_options.append(f"{emp_id} - {emp_name} ({emp_position}, {emp_department})")
            
            selected_employee = st.selectbox(
                "직원을 선택하세요:",
                options=["선택하세요..."] + employee_options,
                key="delete_employee_select"
            )
        
        with col_info:
            if selected_employee and selected_employee != "선택하세요...":
                # 선택된 직원의 상세 정보 표시
                employee_id_to_delete = selected_employee.split(" - ")[0]
                employee_info = manager.get_employee_by_id(employee_id_to_delete)
                
                if employee_info:
                    st.info("**선택된 직원 정보:**")
                    st.write(f"**사번**: {employee_info.get('employee_id', '')}")
                    st.write(f"**이름**: {employee_info.get('name', '')}")
                    st.write(f"**영문명**: {employee_info.get('english_name', '')}")
                    st.write(f"**직급**: {employee_info.get('position', '')}")
                    st.write(f"**부서**: {employee_info.get('department', '')}")
                    st.write(f"**입사일**: {employee_info.get('hire_date', '')}")
                    st.write(f"**상태**: {employee_info.get('work_status', '')}")
        
        # 삭제 실행 섹션
        if selected_employee and selected_employee != "선택하세요...":
            st.divider()
            st.subheader("🚨 삭제 실행")
            
            employee_id_to_delete = selected_employee.split(" - ")[0]
            
            # 삭제 확인을 위한 2단계 프로세스
            if 'delete_step' not in st.session_state:
                st.session_state.delete_step = 0
                
            if 'selected_employee_for_delete' not in st.session_state:
                st.session_state.selected_employee_for_delete = ""
            
            # 선택이 바뀌면 단계 초기화
            if st.session_state.selected_employee_for_delete != selected_employee:
                st.session_state.selected_employee_for_delete = selected_employee
                st.session_state.delete_step = 0
            
            col_delete_btn, col_status = st.columns([1, 2])
            
            with col_delete_btn:
                if st.session_state.delete_step == 0:
                    if st.button("🗑️ 삭제하기", type="secondary", use_container_width=True):
                        st.session_state.delete_step = 1
                        st.rerun()
                
                elif st.session_state.delete_step == 1:
                    st.error("⚠️ **정말 삭제하시겠습니까?**")
                    
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ 확인", type="primary", use_container_width=True):
                            # 직원 삭제 실행
                            with st.spinner("직원을 삭제하는 중..."):
                                result = manager.delete_employee(employee_id_to_delete)
                                
                                # SQLiteEmployeeManager는 (success, message) 튜플을 반환
                                if isinstance(result, tuple) and len(result) == 2:
                                    success, message = result
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.session_state.delete_step = 0
                                        st.session_state.selected_employee_for_delete = ""
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                        st.session_state.delete_step = 0
                                # 기존 매니저 호환성 (True/False만 반환)
                                elif result:
                                    st.success("✅ 직원이 성공적으로 삭제되었습니다!")
                                    st.session_state.delete_step = 0
                                    st.session_state.selected_employee_for_delete = ""
                                    st.rerun()
                                else:
                                    st.error("❌ 직원 삭제에 실패했습니다.")
                                    st.session_state.delete_step = 0
                    
                    with col_no:
                        if st.button("❌ 취소", use_container_width=True):
                            st.session_state.delete_step = 0
                            st.rerun()
            
            with col_status:
                if st.session_state.delete_step == 0:
                    st.info("💡 **안내**: 삭제하기 버튼을 클릭하여 삭제를 시작하세요.")
                elif st.session_state.delete_step == 1:
                    st.error("🚨 **최종 확인**: 이 작업은 되돌릴 수 없습니다!")
    
    else:
        st.error("직원 데이터를 표시할 수 없습니다.")
    
    # 추가 안내
    st.divider()
    st.info("""
    **📌 삭제 관련 안내**:
    - 삭제된 직원 정보는 완전히 제거되며 복구할 수 없습니다
    - 삭제하기 전에 필요한 정보를 별도로 백업하세요  
    - 퇴사 처리가 목적이라면 '직원 편집' 탭에서 근무상태를 '퇴사'로 변경하는 것을 고려하세요
    """)
