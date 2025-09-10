import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import re

def format_phone_number(phone):
    """연락처를 010-XXXX-XXXX 형식으로 포맷팅합니다."""
    if not phone:
        return phone
    
    # 숫자만 추출
    digits = re.sub(r'[^\d]', '', phone)
    
    # 11자리 숫자인 경우 포맷팅
    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) >= 3:
        # 길이에 따라 포맷팅
        if len(digits) <= 3:
            return digits
        elif len(digits) <= 7:
            return f"{digits[:3]}-{digits[3:]}"
        elif len(digits) <= 11:
            if digits.startswith('010'):
                if len(digits) <= 7:
                    return f"{digits[:3]}-{digits[3:]}"
                else:
                    return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    return phone

def show_employee_page(manager, auth_manager, user_permissions, get_text):
    """직원 관리 페이지 - 서브메뉴 기반 UI"""
    
    # 사이드바에서 선택된 서브메뉴 가져오기
    selected_submenu = st.session_state.get('employee_management_submenu_selector', "직원 목록")
    
    # 선택된 서브메뉴에 따른 분기 처리
    if selected_submenu == "직원 목록":
        st.header("📋 직원 목록")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter_options = ["전체", "활성", "비활성"]
            status_filter = st.selectbox("상태 필터", status_filter_options)
        with col2:
            region_filter_options = ["전체"] + manager.get_regions()
            region_filter = st.selectbox("지역 필터", region_filter_options)
        with col3:
            search_term = st.text_input("검색 (이름, 사번, 영문이름)")

        # 필터 적용
        actual_status_filter = None
        if status_filter == "활성":
            actual_status_filter = '활성'
        elif status_filter == "비활성":
            actual_status_filter = '비활성'

        actual_region_filter = None if region_filter == "전체" else region_filter

        filtered_employees = manager.get_filtered_employees(
            status_filter=actual_status_filter,
            region_filter=actual_region_filter,
            search_term=search_term
        )

        if len(filtered_employees) > 0:
            # 직원 목록 표시
            st.info(f"총 {len(filtered_employees)}명의 직원이 조회되었습니다.")
            
            # 표시할 컬럼 선택
            display_columns = ['employee_id', 'name', 'english_name', 'contact', 'email', 'position', 'work_status']
            available_columns = [col for col in display_columns if col in filtered_employees.columns]
            
            if available_columns:
                display_df = filtered_employees[available_columns].copy()
                
                # 컬럼명 한국어로 변경
                column_mapping = {
                    'employee_id': '사번',
                    'name': '이름',
                    'english_name': '영문명',
                    'contact': '연락처',
                    'email': '이메일',
                    'position': '직급',
                    'work_status': '근무상태'
                }
                
                rename_dict = {k: v for k, v in column_mapping.items() if k in display_df.columns}
                display_df = display_df.rename(columns=rename_dict)
                
                # 직원 목록 테이블 표시
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 다운로드 버튼
                csv_buffer = io.StringIO()
                filtered_employees.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 직원 목록 다운로드",
                    data=csv_buffer.getvalue().encode('utf-8-sig'),
                    file_name=f"employees_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("표시할 수 있는 직원 정보가 없습니다.")
        else:
            st.warning("조건에 맞는 직원이 없습니다.")

    elif selected_submenu == "직원 등록":
        st.header("➕ 새 직원 등록")
        
        with st.form("employee_registration_form"):
            # 기본 정보
            st.subheader("기본 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("이름 *", placeholder="홍길동")
                english_name = st.text_input("영문명", placeholder="Hong Gil Dong")
                gender = st.selectbox("성별", ["남", "여"])
                hire_date = st.date_input("입사일 *", value=date.today())
            
            with col2:
                contact = st.text_input("연락처 *", placeholder="010-1234-5678")
                email = st.text_input("이메일", placeholder="hong@company.com")
                position = st.selectbox("직급", ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무"])
                birth_date = st.date_input("생년월일", value=date(1990, 1, 1))
            
            # 주소 정보
            st.subheader("주소 정보")
            col3, col4 = st.columns(2)
            
            with col3:
                nationality = st.selectbox("국적 *", ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"])
                residence_country = st.selectbox("거주국가 *", ["한국", "중국", "태국", "베트남", "인도네시아", "말레이시아"])
            
            with col4:
                # 거주국가에 따른 도시 목록
                cities = manager.get_cities_by_country(residence_country)
                city_options = [""] + cities if cities else [""]
                city = st.selectbox("도시", city_options)
            
            # 추가 정보
            st.subheader("추가 정보")
            col5, col6 = st.columns(2)
            
            with col5:
                salary = st.number_input("급여", min_value=0, value=0)
                salary_currency = st.selectbox("급여 통화", ["KRW", "USD", "VND", "THB", "CNY"])
            
            with col6:
                driver_license = st.text_input("운전면허", placeholder="1종보통")
                notes = st.text_area("비고", placeholder="특이사항을 입력하세요")
            
            # 등록 버튼
            col_submit, col_clear = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button("✅ 직원 등록", use_container_width=True, type="primary")
            
            with col_clear:
                clear_form = st.form_submit_button("🔄 초기화", use_container_width=True)
            
            if submitted:
                # 필수 필드 검증
                if not name or not contact or not hire_date:
                    st.error("이름, 연락처, 입사일은 필수 입력 항목입니다.")
                else:
                    # 연락처 포맷팅
                    formatted_contact = format_phone_number(contact)
                    
                    # 새 직원 데이터 준비
                    new_employee = {
                        'name': name,
                        'english_name': english_name,
                        'gender': gender,
                        'nationality': nationality,
                        'residence_country': residence_country,
                        'city': city,
                        'contact': formatted_contact,
                        'email': email,
                        'position': position,
                        'hire_date': hire_date.strftime('%Y-%m-%d'),
                        'birth_date': birth_date.strftime('%Y-%m-%d'),
                        'salary': salary,
                        'salary_currency': salary_currency,
                        'driver_license': driver_license,
                        'notes': notes,
                        'work_status': '재직',
                        'status': '활성',
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 직원 등록
                    if manager.add_employee(new_employee):
                        st.success(f"✅ {name}님이 성공적으로 등록되었습니다!")
                        st.rerun()
                    else:
                        st.error("❌ 직원 등록에 실패했습니다.")

    # 탭 3: 직원 편집
    with tab3:
        st.header("✏️ 직원 편집")
        
        # 편집할 직원 선택
        employees = manager.get_all_employees()
        if len(employees) > 0:
            employee_options = [f"{emp['name']} ({emp['employee_id']})" for _, emp in employees.iterrows()]
            selected_employee = st.selectbox("편집할 직원 선택", employee_options)
            
            if selected_employee:
                # 선택된 직원 정보 가져오기
                selected_id = selected_employee.split("(")[1].split(")")[0]
                employee_data = manager.get_employee_by_id(selected_id)
                
                if employee_data:
                    with st.form("employee_edit_form"):
                        # 기본 정보
                        st.subheader("기본 정보")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            name = st.text_input("이름", value=employee_data.get('name', ''))
                            english_name = st.text_input("영문명", value=employee_data.get('english_name', ''))
                            gender = st.selectbox("성별", ["남", "여"], index=0 if employee_data.get('gender') == '남' else 1)
                        
                        with col2:
                            contact = st.text_input("연락처", value=employee_data.get('contact', ''))
                            email = st.text_input("이메일", value=employee_data.get('email', ''))
                            position = st.selectbox("직급", ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무"], 
                                                  index=0 if not employee_data.get('position') else 
                                                  ["사원", "대리", "과장", "차장", "부장", "이사", "상무", "전무"].index(employee_data.get('position', '사원')))
                        
                        # 근무 상태
                        st.subheader("근무 상태")
                        work_status = st.selectbox("근무 상태", ["재직", "휴직", "퇴사"], 
                                                 index=0 if employee_data.get('work_status') == '재직' else 
                                                 1 if employee_data.get('work_status') == '휴직' else 2)
                        
                        # 수정 버튼
                        submitted = st.form_submit_button("💾 정보 수정", use_container_width=True, type="primary")
                        
                        if submitted:
                            # 수정된 데이터 준비
                            updated_data = {
                                'name': name,
                                'english_name': english_name,
                                'gender': gender,
                                'contact': format_phone_number(contact),
                                'email': email,
                                'position': position,
                                'work_status': work_status,
                                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            # 직원 정보 수정
                            if manager.update_employee(selected_id, updated_data):
                                st.success(f"✅ {name}님의 정보가 성공적으로 수정되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 직원 정보 수정에 실패했습니다.")
        else:
            st.warning("등록된 직원이 없습니다.")

    # 탭 4: 직원 통계
    with tab4:
        st.header("📊 직원 통계")
        
        employees = manager.get_all_employees()
        if len(employees) > 0:
            # 전체 통계
            total_employees = len(employees)
            active_employees = len(employees[employees['work_status'] == '재직']) if 'work_status' in employees.columns else total_employees
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 직원 수", total_employees)
            
            with col2:
                st.metric("재직 직원 수", active_employees)
            
            with col3:
                st.metric("퇴사 직원 수", total_employees - active_employees)
            
            # 직급별 통계
            if 'position' in employees.columns:
                st.subheader("직급별 현황")
                position_counts = employees['position'].value_counts()
                st.bar_chart(position_counts)
            
            # 근무 상태별 통계
            if 'work_status' in employees.columns:
                st.subheader("근무 상태별 현황")
                status_counts = employees['work_status'].value_counts()
                st.bar_chart(status_counts)
            
            # 최근 입사자
            st.subheader("최근 입사자")
            if 'hire_date' in employees.columns:
                recent_employees = employees.sort_values('hire_date', ascending=False).head(5)
                display_cols = ['employee_id', 'name', 'position', 'hire_date']
                available_cols = [col for col in display_cols if col in recent_employees.columns]
                if available_cols:
                    st.dataframe(recent_employees[available_cols], use_container_width=True, hide_index=True)
        else:
            st.warning("등록된 직원이 없습니다.")