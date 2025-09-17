"""
총무 전용 지출요청서 관리 페이지
- 지출요청서 작성
- 내 요청서 진행상태 확인 
- 승인 처리는 법인장만 가능
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from managers.sqlite.sqlite_expense_request_manager import SQLiteExpenseRequestManager as SQLiteExpenseManager
from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager

def show_expense_request_admin_page(expense_manager, user_id, user_name, get_text):
    """총무 전용 지출요청서 관리 페이지"""
    
    # 매니저 초기화 (매개변수로 전달받은 것 사용, 없으면 SQLite 기반으로 생성)
    if not expense_manager:
        expense_manager = SQLiteExpenseManager()
    employee_manager = SQLiteEmployeeManager()
    
    # 현재 사용자 정보 (매개변수 우선 사용)
    current_user_id = user_id or st.session_state.get('user_id', '')
    current_user_name = user_name or st.session_state.get('user_name', '')
    
    # 탭 메뉴 (총무 전용) - 하드코딩으로 수정
    tab1, tab2, tab3 = st.tabs([
        "📝 지출요청서 작성", 
        "📋 내 요청서 진행상태", 
        "📊 요청서 통계"
    ])
    
    with tab1:
        show_expense_request_form_multi_items(expense_manager, current_user_id, current_user_name, get_text)
    
    with tab2:
        show_my_requests_status(expense_manager, current_user_id, get_text)
    
    with tab3:
        show_request_statistics(expense_manager, current_user_id, get_text)

def show_expense_request_form_multi_items(expense_manager, current_user_id, current_user_name, get_text):
    """다중 항목을 지원하는 지출요청서 작성 폼"""
    st.header("📝 지출요청서 작성 (다중 항목)")
    
    st.info("💡 여러 개의 지출 항목을 한 번에 요청할 수 있습니다.")
    
    # 세션 스테이트 초기화
    if 'expense_items' not in st.session_state:
        st.session_state.expense_items = [{
            'item_description': '',
            'item_category': '교통비',
            'item_amount': 0,
            'vendor': '',
            'item_notes': ''
        }]
    
    # 기본 정보 저장을 위한 세션 상태 초기화
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'expense_title': '',
            'expense_category': '교통비',
            'request_date': datetime.now().date(),
            'expected_date': datetime.now().date(),
            'currency': 'VND',
            'expense_description': '',
            'notes': ''
        }
    
    # 항목 관리 버튼들 (form 밖에서 처리)
    st.subheader("💰 지출 항목 관리")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("➕ 항목 추가", help="새로운 지출 항목을 추가합니다"):
            st.session_state.expense_items.append({
                'item_description': '',
                'item_category': '교통비',
                'item_amount': 0,
                'vendor': '',
                'item_notes': ''
            })
            st.rerun()
    
    with col_btn2:
        if st.button("➖ 마지막 항목 삭제", help="마지막 지출 항목을 삭제합니다") and len(st.session_state.expense_items) > 1:
            st.session_state.expense_items.pop()
            st.rerun()
    
    with col_btn3:
        st.write(f"**현재 항목 수: {len(st.session_state.expense_items)}개**")
    
    with st.form("expense_request_form_multi", clear_on_submit=True):
        # 헤더 정보
        st.subheader("📋 지출요청서 기본 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            expense_title = st.text_input(
                "지출요청서 제목*",
                value=st.session_state.form_data['expense_title'],
                placeholder="예: 2025년 9월 출장 경비",
                help="지출요청서의 전체 제목을 입력하세요"
            )
            
            expense_category = st.selectbox(
                "전체 카테고리*", 
                ['교통비', '숙박비', '식비', '회의비', '사무용품', '통신비', '기타'],
                index=['교통비', '숙박비', '식비', '회의비', '사무용품', '통신비', '기타'].index(st.session_state.form_data['expense_category']),
                help="이번 지출요청서의 주요 카테고리를 선택하세요"
            )
            
            request_date = st.date_input(
                "신청일*",
                value=st.session_state.form_data['request_date'],
                help="지출요청서를 신청하는 날짜를 선택하세요"
            )
        
        with col2:
            expected_date = st.date_input(
                "지출 예정일*",
                value=st.session_state.form_data['expected_date'],
                help="지출이 예상되는 날짜를 선택하세요"
            )
            
            currency = st.selectbox(
                "통화*",
                ['VND', 'USD', 'KRW'],
                index=['VND', 'USD', 'KRW'].index(st.session_state.form_data['currency']),
                help="지출 통화를 선택하세요"
            )
        
        expense_description = st.text_area(
            "지출요청서 전체 설명*",
            value=st.session_state.form_data['expense_description'],
            placeholder="이번 지출요청서의 전체적인 목적과 배경을 설명하세요",
            height=80
        )
        
        # 지출 항목들 
        st.subheader("💰 지출 항목 상세")
        st.markdown("*각 지출 항목을 상세히 입력해주세요.*")
        
        # 각 항목 입력 필드들 - 세션 상태에서 복원
        total_amount = 0
        items_data = []
        
        for i in range(len(st.session_state.expense_items)):
            with st.expander(f"📝 항목 #{i+1}", expanded=True):
                col_item1, col_item2 = st.columns(2)
                
                with col_item1:
                    item_description = st.text_input(
                        "항목 설명*",
                        value=st.session_state.expense_items[i].get('item_description', ''),
                        key=f"desc_{i}",
                        placeholder="예: 서울-부산 고속버스 왕복",
                        help="이 항목의 구체적인 설명을 입력하세요"
                    )
                    
                    item_category = st.selectbox(
                        "항목 카테고리*",
                        ['교통비', '숙박비', '식비', '회의비', '사무용품', '통신비', '기타'],
                        index=['교통비', '숙박비', '식비', '회의비', '사무용품', '통신비', '기타'].index(
                            st.session_state.expense_items[i].get('item_category', '교통비')
                        ),
                        key=f"cat_{i}",
                        help="이 항목의 카테고리를 선택하세요"
                    )
                
                with col_item2:
                    item_amount = st.number_input(
                        f"금액 ({currency})*",
                        value=int(st.session_state.expense_items[i].get('item_amount', 0)),
                        key=f"amount_{i}",
                        min_value=0,
                        step=1000,
                        format="%d",
                        help=f"이 항목의 금액을 {currency}로 입력하세요"
                    )
                    
                    vendor = st.text_input(
                        "업체명",
                        value=st.session_state.expense_items[i].get('vendor', ''),
                        key=f"vendor_{i}",
                        placeholder="예: 코레일, 현대백화점",
                        help="관련 업체명을 입력하세요 (선택사항)"
                    )
                
                item_notes = st.text_area(
                    "항목별 메모",
                    value=st.session_state.expense_items[i].get('item_notes', ''),
                    key=f"notes_{i}",
                    placeholder="이 항목에 대한 추가 설명이나 메모",
                    height=60,
                    help="이 항목에 대한 추가 정보나 메모 (선택사항)"
                )
                
                # 세션 상태에 현재 입력값 저장
                st.session_state.expense_items[i] = {
                    'item_description': item_description,
                    'item_category': item_category,
                    'item_amount': item_amount,
                    'vendor': vendor,
                    'item_notes': item_notes
                }
                
                # 항목 데이터 수집
                if item_description and item_amount > 0:
                    items_data.append({
                        'item_description': item_description,
                        'item_category': item_category,
                        'item_amount': item_amount,
                        'item_currency': currency,
                        'vendor': vendor,
                        'item_notes': item_notes
                    })
                    total_amount += item_amount
        
        # 총 금액 표시
        if total_amount > 0:
            st.success(f"💰 **총 지출 금액: {total_amount:,.0f} {currency}**")
        
        # 첨부파일 및 메모
        st.subheader("📎 첨부파일 및 메모")
        
        uploaded_files = st.file_uploader(
            "첨부파일",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'],
            help="관련 파일들을 업로드하세요 (선택사항)"
        )
        
        attachment_info = ""
        if uploaded_files:
            st.write("업로드된 파일:")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size:,} bytes)")
                attachment_info += f"{file.name}({file.size:,}bytes); "
        
        notes = st.text_area(
            "추가 메모",
            value=st.session_state.form_data['notes'],
            placeholder="전체 지출요청서에 대한 추가 메모나 특이사항을 입력하세요",
            height=80
        )
        
        # 현재 입력된 기본 정보를 세션에 저장
        st.session_state.form_data.update({
            'expense_title': expense_title,
            'expense_category': expense_category,
            'request_date': request_date,
            'expected_date': expected_date,
            'currency': currency,
            'expense_description': expense_description,
            'notes': notes
        })
        
        # 제출 버튼
        submit_btn = st.form_submit_button(
            "📤 지출요청서 제출",
            type="primary",
            use_container_width=True
        )
        
        if submit_btn:
            # 필수 필드 검증
            if not expense_title or not expense_description or not items_data:
                st.error("❌ 필수 항목을 모두 입력해주세요. (제목, 설명, 최소 1개 항목)")
                return
            
            # 유효한 항목이 있는지 확인
            valid_items = [item for item in items_data if item['item_description'] and item['item_amount'] > 0]
            if not valid_items:
                st.error("❌ 최소 1개의 유효한 지출 항목이 필요합니다. (설명과 금액 필수)")
                return
            
            try:
                # 요청서 헤더 데이터
                request_data = {
                    'requester_id': current_user_id,
                    'requester_name': current_user_name,
                    'expense_title': expense_title,
                    'category': expense_category,
                    'currency': currency,
                    'request_date': request_date.strftime('%Y-%m-%d'),
                    'expected_date': expected_date.strftime('%Y-%m-%d'),
                    'expense_description': expense_description,
                    'notes': notes if notes else ''
                }
                
                # PostgreSQL 직접 처리로 변경
                import psycopg2
                #from datetime import datetime

                conn = psycopg2.connect(
                    host=st.secrets["postgres"]["host"],
                    port=st.secrets["postgres"]["port"],
                    database=st.secrets["postgres"]["database"],
                    user=st.secrets["postgres"]["user"],
                    password=st.secrets["postgres"]["password"]
                )
                cursor = conn.cursor()

                # 요청번호 생성
                request_number = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
                request_id = request_number

                # 메인 지출요청서 추가 (승인자 정보 포함)
                cursor.execute("""
                    INSERT INTO expense_requests (
                        request_id, request_number, employee_id, employee_name,
                        expense_title, total_amount, currency, expected_date,
                        expense_description, notes, status, request_date,
                        created_at, updated_at, category,
                        first_approver_id, first_approver_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    request_id,
                    request_number,
                    current_user_id,
                    current_user_name,
                    expense_title,
                    total_amount,
                    currency,
                    expected_date.strftime('%Y-%m-%d'),
                    expense_description,
                    notes if notes else '',
                    'pending',
                    request_date.strftime('%Y-%m-%d'),
                    datetime.now(),
                    datetime.now(),
                    expense_category,
                    '2508001',  # 법인장 ID
                    '김충성'     # 법인장 이름
                ))

                expense_request_id = cursor.fetchone()[0]

                # 승인 데이터 생성
                cursor.execute("""
                    INSERT INTO expense_approvals (
                        approval_id, request_id, approver_id, approver_name, status
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    f"APPR_{expense_request_id}",
                    expense_request_id,
                    '2508001',
                    '김충성',
                    'pending'
                ))

                # 각 항목 저장
                for item in valid_items:
                    cursor.execute("""
                        INSERT INTO expense_items (
                            request_id, item_description, item_category,
                            item_amount, item_currency, vendor, item_notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        expense_request_id,
                        item['item_description'],
                        item.get('item_category', ''),
                        float(item['item_amount']),
                        item.get('item_currency', currency),  # currency 변수 사용
                        item.get('vendor', ''),
                        item.get('item_notes', '')
                    ))

                conn.commit()
                cursor.close()
                conn.close()

                request_id = expense_request_id
                
                if request_id:
                    # 성공 메시지 표시
                    st.success(f"✅ 지출요청서가 성공적으로 제출되었습니다!")
                    st.info(f"📋 요청서 번호: {request_number}")
                    st.info(f"💰 총 금액: {total_amount:,.0f} {currency}")
                    st.info(f"📦 총 항목 수: {len(valid_items)}개")
                    # 나머지 코드 계속...
                    # 제출된 항목들 요약 표시
                    with st.expander("📝 제출된 항목 요약", expanded=False):
                        for i, item in enumerate(valid_items, 1):
                            st.write(f"**{i}. {item['item_description']}**")
                            st.write(f"   - 카테고리: {item['item_category']}")
                            st.write(f"   - 금액: {item['item_amount']:,.0f} {currency}")
                            if item['vendor']:
                                st.write(f"   - 업체: {item['vendor']}")
                            if item['item_notes']:
                                st.write(f"   - 메모: {item['item_notes']}")
                            st.divider()
                    
                    # 세션 스테이트 완전 초기화 (새로운 요청서 작성 준비)
                    st.session_state.expense_items = [{
                        'item_description': '',
                        'item_category': '교통비',
                        'item_amount': 0,
                        'vendor': '',
                        'item_notes': ''
                    }]
                    
                    st.session_state.form_data = {
                        'expense_title': '',
                        'expense_category': '교통비',
                        'request_date': datetime.now().date(),
                        'expected_date': datetime.now().date(),
                        'currency': 'VND',
                        'expense_description': '',
                        'notes': ''
                    }
                    
                    st.info("🔄 새로운 지출요청서 작성을 위해 폼이 초기화되었습니다.")
                    
                else:
                    st.error("❌ 지출요청서 제출 중 오류가 발생했습니다.")
                    
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

def show_expense_request_form_admin_backup(expense_manager, current_user_id, current_user_name, get_text):
    """총무용 지출요청서 작성 폼"""
    st.header(f"📝 {get_text('expense_request_form')}")
    
    st.info(f"💡 {get_text('auto_approval_info')}")
    
    with st.form("expense_request_form_admin", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('basic_information'))
            
            # 동적 지출 유형 목록
            expense_types_list = [
                get_text('expense_types.transportation'),
                get_text('expense_types.accommodation'),
                get_text('expense_types.meal'),
                get_text('expense_types.meeting'),
                get_text('expense_types.office_supplies'),
                get_text('expense_types.communication'),
                get_text('expense_types.other')
            ]
            
            expense_type = st.selectbox(
                f"{get_text('expense_type')}*", 
                expense_types_list,
                help=get_text('select_expense_type')
            )
            
            amount = st.number_input(
                f"{get_text('expense_amount_vnd')}*", 
                min_value=0,
                step=1000,
                format="%d",
                help=get_text('enter_expense_amount')
            )
            
            expense_date = st.date_input(
                f"{get_text('expense_date')}*",
                value=datetime.now().date(),
                help=get_text('select_expense_date')
            )
        
        with col2:
            st.subheader(get_text('detailed_information'))
            
            purpose = st.text_area(
                f"{get_text('expense_purpose')}*",
                placeholder=get_text('enter_purpose'),
                height=100
            )
            
            vendor = st.text_input(
                get_text('vendor_name'),
                placeholder=get_text('vendor_placeholder')
            )
            
            priority_options = [
                get_text('priority_normal'),
                get_text('priority_urgent'), 
                get_text('priority_high')
            ]
            
            priority = st.selectbox(
                get_text('priority'),
                priority_options,
                help=get_text('select_priority')
            )
        
        st.subheader(get_text('attachments_memo'))
        
        # 파일 업로드 기능 (key를 사용해서 초기화 가능하게 함)
        if 'file_uploader_key' not in st.session_state:
            st.session_state.file_uploader_key = 0
        
        uploaded_files = st.file_uploader(
            get_text('file_upload'),
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'],
            help=get_text('file_upload_help'),
            key=f"file_upload_{st.session_state.file_uploader_key}"
        )
        
        # 업로드된 파일 목록 표시
        attachment_info = ""
        if uploaded_files:
            st.write(f"{get_text('uploaded_files')}")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size:,} bytes)")
                attachment_info += f"{file.name}({file.size:,}bytes); "
        
        additional_notes = st.text_area(
            get_text('additional_notes'),
            placeholder=get_text('additional_notes_placeholder'),
            height=60
        )
        
        submitted = st.form_submit_button(f"📤 {get_text('submit_request')}", type="primary", use_container_width=True)
        
        if submitted:
            if not expense_type or not amount or not purpose:
                st.error(f"❌ {get_text('required_fields_error')}")
                return
            
            # 요청서 데이터 생성 (필드명을 데이터베이스 스키마에 맞춤)
            request_data = {
                'requester_id': current_user_id,
                'requester_name': current_user_name,
                'expense_title': expense_type,  # expense_type → expense_title
                'category': expense_type,  # 카테고리 추가
                'amount': amount,
                'currency': 'VND',
                'expected_date': expense_date.strftime('%Y-%m-%d'),  # expense_date → expected_date
                'expense_description': purpose,  # purpose → expense_description
                'vendor': vendor if vendor else '',
                'priority': priority,
                'attachment': attachment_info if attachment_info else '',  # attachments → attachment
                'notes': additional_notes if additional_notes else '',  # additional_notes → notes
                'status': 'pending'
            }
            
            # 승인자 설정 (기본: 법인장)
            try:
                employee_manager = SQLiteEmployeeManager()
                # 딕셔너리 리스트 형태로 직원 데이터 가져오기
                all_employees = employee_manager.get_all_employees_list()
                
                # 법인장(master) 권한을 가진 직원 찾기
                # 데이터 타입 검증 (체크리스트 4-3)
                if not isinstance(all_employees, list):
                    st.error(f"❌ {get_text('employee_data_error')}")
                    st.write(f"디버깅: 데이터 타입 = {type(all_employees)}")
                    return
                
                if len(all_employees) == 0:
                    st.error(f"❌ {get_text('no_employees_error')}")
                    return
                
                # 법인장 찾기 (타입 안전성 확보) - ceo와 master 둘 다 확인
                masters = []
                for emp in all_employees:
                    if isinstance(emp, dict) and emp.get('access_level') in ['master', 'ceo']:
                        masters.append(emp)
                
                if not masters:
                    st.error(f"❌ {get_text('no_approver_error')}")
                    return
                
                # 첫 번째 법인장을 최종 승인자로 설정
                final_approver = masters[0]
                
                # 승인자 정보가 딕셔너리인지 확인
                if not isinstance(final_approver, dict):
                    st.error(f"❌ {get_text('approver_info_error')}")
                    return
                
                # 승인자 정보를 request_data에 추가 (새 매니저 방식)
                request_data['first_approver'] = {
                    'approver_id': final_approver.get('employee_id', ''),
                    'approver_name': final_approver.get('name', '')
                }
                
                # 요청서 생성
                success, message = expense_manager.create_expense_request(request_data)
                
                if success:
                    st.success(f"✅ {message}")
                    approver_name = final_approver.get('name', '알 수 없음')
                    approver_id = final_approver.get('employee_id', '알 수 없음')
                    st.info(f"📋 승인자: {approver_name} ({approver_id})")
                    
                    # 파일 업로더 초기화를 위해 key 변경
                    st.session_state.file_uploader_key += 1
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ 요청서 제출 중 오류가 발생했습니다: {str(e)}")

def show_my_requests_status(expense_manager, user_id, get_text):
    """내 요청서 진행상태 확인"""
    st.header("📋 내 요청서 진행상태")
    
    # 내 요청서 목록 가져오기
    my_requests = expense_manager.get_my_requests(user_id)
    
    if not my_requests:
        st.info("📄 등록된 지출요청서가 없습니다.")
        return
    
    # 상태별 필터링
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("상태 필터", ["전체", "대기", "진행중", "승인", "반려", "완료"])
    with col2:
        sort_order = st.selectbox("정렬 순서", ["최신순", "오래된순", "금액 높은순", "금액 낮은순"])
    
    # 필터링 적용
    filtered_requests = my_requests.copy()
    
    if status_filter != "전체":
        filtered_requests = [req for req in filtered_requests if req.get('status', '').strip() == status_filter]
    
    # 정렬 적용
    if sort_order == "최신순":
        filtered_requests.sort(key=lambda x: x.get('request_date', ''), reverse=True)
    elif sort_order == "오래된순":
        filtered_requests.sort(key=lambda x: x.get('request_date', ''))
    elif sort_order == "금액 높은순":
        filtered_requests.sort(key=lambda x: float(x.get('amount', 0)), reverse=True)
    elif sort_order == "금액 낮은순":
        filtered_requests.sort(key=lambda x: float(x.get('amount', 0)))
    
    st.write(f"**총 {len(filtered_requests)}건의 요청서**")
    
    # 요청서 목록 표시
    for i, request in enumerate(filtered_requests):
        with st.expander(f"📄 {request.get('expense_type', 'N/A')} - {request.get('amount', 0):,} VND ({request.get('status', 'N/A')})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**요청서 ID:** {request.get('request_id', 'N/A')}")
                st.write(f"**지출 유형:** {request.get('expense_type', 'N/A')}")
                st.write(f"**금액:** {request.get('amount', 0):,} {request.get('currency', 'VND')}")
                st.write(f"**지출 예정일:** {request.get('expense_date', 'N/A')}")
            
            with col2:
                st.write(f"**상태:** {request.get('status', 'N/A')}")
                st.write(f"**신청일:** {request.get('request_date', 'N/A')}")
                st.write(f"**우선순위:** {request.get('priority', 'N/A')}")
                
                # 승인 진행상태 표시 (기본 상태만 표시)
                st.write(f"**승인 상태:** {request.get('status', 'N/A')}")
            
            st.write(f"**목적:** {request.get('purpose', 'N/A')}")
            
            if request.get('vendor'):
                st.write(f"**업체:** {request.get('vendor')}")
            
            if request.get('additional_notes'):
                st.write(f"**메모:** {request.get('additional_notes')}")
            
            # 액션 버튼들 추가
            st.divider()
            
            # 상태에 따른 버튼 표시 (디버깅 정보 추가)
            current_status = request.get('status', '').strip()
            
            if current_status in ['pending', '대기', 'PENDING']:
                # 대기 상태인 경우: 프린트, 취소, 삭제 버튼
                col_action1, col_action2, col_action3 = st.columns(3)
                
                with col_action1:
                    if st.button(f"🖨️ 프린트", key=f"print_{request.get('request_id', i)}", use_container_width=True):
                        st.session_state[f'show_print_{request.get("request_id", i)}'] = True
                        st.rerun()
                
                with col_action2:
                    if st.button(f"❌ 취소", key=f"cancel_{request.get('request_id', i)}", use_container_width=True):
                        if st.session_state.get(f'confirm_cancel_{request.get("request_id", i)}', False):
                            # 취소 실행
                            try:
                                success, message = expense_manager.cancel_expense_request(request.get('request_id'))
                                if success:
                                    st.success(message)
                                    st.session_state[f'confirm_cancel_{request.get("request_id", i)}'] = False
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"취소 중 오류 발생: {str(e)}")
                        else:
                            # 취소 확인
                            st.session_state[f'confirm_cancel_{request.get("request_id", i)}'] = True
                            st.warning("정말 취소하시겠습니까? 다시 클릭하면 취소됩니다.")
                
                with col_action3:
                    if st.button(f"🗑️ 삭제", key=f"delete_{request.get('request_id', i)}", use_container_width=True):
                        if st.session_state.get(f'confirm_delete_{request.get("request_id", i)}', False):
                            # 삭제 실행
                            try:
                                success, message = expense_manager.delete_expense_request(request.get('request_id'), user_id)
                                if success:
                                    st.success(message)
                                    st.session_state[f'confirm_delete_{request.get("request_id", i)}'] = False
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"삭제 중 오류 발생: {str(e)}")
                        else:
                            # 삭제 확인
                            st.session_state[f'confirm_delete_{request.get("request_id", i)}'] = True
                            st.error("⚠️ 삭제하면 복구할 수 없습니다! 다시 클릭하면 삭제됩니다.")
                    
            else:
                # 다른 상태인 경우: 프린트 버튼만
                col_print1, col_print2, col_print3 = st.columns(3)
                
                with col_print1:
                    if st.button(f"🖨️ 프린트", key=f"print_{request.get('request_id', i)}", use_container_width=True):
                        st.session_state[f'show_print_{request.get("request_id", i)}'] = True
                        st.rerun()
                
                with col_print2:
                    st.write("") # 빈 공간
                    
                with col_print3:
                    st.write("") # 빈 공간
            
            # 프린트 미리보기 표시
            if st.session_state.get(f'show_print_{request.get("request_id", i)}', False):
                show_print_preview(request, get_text, request.get('request_id', i))

def show_request_statistics(expense_manager, user_id, get_text):
    """요청서 통계"""
    st.header("📊 내 요청서 통계")
    
    try:
        # 내 요청서 목록 가져오기
        my_requests = expense_manager.get_my_requests(user_id)
        
        if not my_requests:
            st.info("📄 통계를 표시할 요청서가 없습니다.")
            return
        
        # 통계 계산
        total_requests = len(my_requests)
        total_amount = sum(float(req.get('amount', 0)) for req in my_requests)
        
        # 상태별 분류
        status_counts = {}
        for req in my_requests:
            status = req.get('status', '미정').strip()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 유형별 분류
        type_amounts = {}
        for req in my_requests:
            expense_type = req.get('expense_type', '기타')
            amount = float(req.get('amount', 0))
            type_amounts[expense_type] = type_amounts.get(expense_type, 0) + amount
        
        # 메트릭 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 요청서", f"{total_requests}건")
        
        with col2:
            st.metric("총 금액", f"{total_amount:,.0f} VND")
        
        with col3:
            approved_count = status_counts.get('승인', 0)
            st.metric("승인된 요청", f"{approved_count}건")
        
        with col4:
            pending_count = status_counts.get('대기', 0)
            st.metric("대기 중", f"{pending_count}건")
        
        # 상태별 차트
        if status_counts:
            st.subheader("📈 상태별 현황")
            status_data = {'상태': list(status_counts.keys()), '건수': list(status_counts.values())}
            status_df = pd.DataFrame(status_data)
            st.bar_chart(status_df.set_index('상태'))
        
        # 유형별 차트
        if type_amounts:
            st.subheader("💰 유형별 지출액")
            type_data = {'유형': list(type_amounts.keys()), '금액': list(type_amounts.values())}
            type_df = pd.DataFrame(type_data)
            st.bar_chart(type_df.set_index('유형'))
        
        # 상세 테이블
        st.subheader("📋 요청서 목록")
        if my_requests:
            df_data = []
            for req in my_requests:
                df_data.append({
                    '요청서ID': req.get('request_id', ''),
                    '유형': req.get('expense_type', ''),
                    '금액': f"{float(req.get('amount', 0)):,.0f} VND",
                    '상태': req.get('status', ''),
                    '신청일': req.get('request_date', '')[:10] if req.get('request_date') else '',
                    '우선순위': req.get('priority', '')
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ 통계 조회 중 오류가 발생했습니다: {str(e)}")

def show_print_preview(request, get_text, request_id):
    """지출요청서 프린트 미리보기 및 CSS 프린트 기능"""
    
    # 자동 프린트 스크립트 초기화 (가장 먼저 수행)
    auto_print_script = ""
    if st.session_state.get(f'print_triggered_{request_id}', False):
        auto_print_script = "setTimeout(function() { safePrint(); }, 500);"
        st.session_state[f'print_triggered_{request_id}'] = False
    
    # 프린트 CSS와 JavaScript
    print_css_js = """
    <style>
    @media print {
        /* 프린트 시에만 적용되는 스타일 */
        .print-container {
            width: 100%;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            font-family: 'Arial', sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
        }
        
        .print-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
        }
        
        .print-title {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .print-subtitle {
            font-size: 14pt;
            color: #666;
        }
        
        .print-section {
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .print-section-title {
            font-size: 14pt;
            font-weight: bold;
            color: #333;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }
        
        .print-info-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        
        .print-info-table td {
            padding: 8px 12px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .print-info-table .label {
            background-color: #f8f9fa;
            font-weight: bold;
            width: 30%;
        }
        
        .print-info-table .value {
            width: 70%;
        }
        
        .print-amount {
            font-size: 16pt;
            font-weight: bold;
            color: #d63384;
            text-align: center;
            padding: 10px;
            border: 2px solid #d63384;
            margin: 15px 0;
        }
        
        .print-signature {
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
        }
        
        .signature-box {
            width: 45%;
            text-align: center;
            border-top: 1px solid #000;
            padding-top: 10px;
        }
        
        .no-print {
            display: none !important;
        }
        
        /* Streamlit 특정 요소 숨기기 */
        .stApp > header,
        .stApp > .main > .block-container > .stTabs,
        .stSidebar,
        button,
        .stButton {
            display: none !important;
        }
        
        .main > .block-container {
            padding-top: 0 !important;
        }
    }
    
    @media screen {
        /* 화면에서 보기 위한 스타일 */
        .print-container {
            max-width: 800px;
            margin: 20px auto;
            padding: 30px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        .print-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
        }
        
        .print-title {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .print-subtitle {
            font-size: 16px;
            color: #666;
        }
        
        .print-section {
            margin-bottom: 25px;
        }
        
        .print-section-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }
        
        .print-info-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .print-info-table td {
            padding: 12px 15px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .print-info-table .label {
            background-color: #f8f9fa;
            font-weight: bold;
            width: 30%;
        }
        
        .print-info-table .value {
            width: 70%;
        }
        
        .print-amount {
            font-size: 20px;
            font-weight: bold;
            color: #d63384;
            text-align: center;
            padding: 15px;
            border: 2px solid #d63384;
            margin: 20px 0;
            border-radius: 5px;
        }
        
        .print-signature {
            margin-top: 50px;
            display: flex;
            justify-content: space-between;
        }
        
        .signature-box {
            width: 45%;
            text-align: center;
            border-top: 2px solid #333;
            padding-top: 15px;
        }
    }
    </style>
    """
    
    # 현재 날짜
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    # 상태에 따른 한글 변환
    status_korean = {
        'pending': '대기',
        'approved': '승인',
        'rejected': '반려',
        'completed': '완료'
    }.get(request.get('status', ''), request.get('status', ''))
    
    # 우선순위 한글 변환
    priority_korean = {
        'normal': '보통',
        'urgent': '긴급',
        'high': '높음'
    }.get(request.get('priority', ''), request.get('priority', ''))
    
    # HTML 템플릿
    print_html = f"""
    <style>
    @media print {{
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        .no-print {{ display: none !important; }}
        .print-container {{ width: 100%; margin: 0; padding: 20px; }}
    }}
    
    .print-container {{
        max-width: 800px;
        margin: 20px auto;
        padding: 40px;
        border: 2px solid #333;
        font-family: Arial, sans-serif;
        background: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    
    .print-header {{
        text-align: center;
        border-bottom: 3px solid #333;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }}
    
    .print-title {{
        font-size: 28px;
        font-weight: bold;
        color: #d32f2f;
        margin: 20px 0;
    }}
    
    .print-info-table {{
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #333;
        margin: 20px 0;
    }}
    
    .print-info-table th, .print-info-table td {{
        padding: 15px 12px;
        border: 1px solid #333;
        text-align: left;
    }}
    
    .print-info-table .label {{
        background: #f5f5f5;
        font-weight: bold;
        width: 30%;
    }}
    
    .print-section-title {{
        font-size: 18px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        color: #333;
    }}
    </style>
    <div class="print-container">
        <!-- 헤더 -->
        <div class="print-header">
            <div class="print-title">지출 요청서</div>
            <div class="print-subtitle">Expense Request Form</div>
        </div>
        
        <!-- 기본 정보 -->
        <div class="print-section">
            <div class="print-section-title">📋 기본 정보</div>
            <table class="print-info-table">
                <tr>
                    <td class="label">요청서 번호</td>
                    <td class="value">{request.get('request_id', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">요청자</td>
                    <td class="value">{request.get('requester_name', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">요청 일시</td>
                    <td class="value">{request.get('request_date', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">상태</td>
                    <td class="value">{status_korean}</td>
                </tr>
            </table>
        </div>
        
        <!-- 지출 정보 -->
        <div class="print-section">
            <div class="print-section-title">💰 지출 정보</div>
            <table class="print-info-table">
                <tr>
                    <td class="label">지출 유형</td>
                    <td class="value">{request.get('expense_type', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">지출 예정일</td>
                    <td class="value">{request.get('expense_date', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">업체명</td>
                    <td class="value">{request.get('vendor', '미입력') if request.get('vendor') else '미입력'}</td>
                </tr>
                <tr>
                    <td class="label">우선순위</td>
                    <td class="value">{priority_korean}</td>
                </tr>
            </table>
            
            <div class="print-amount">
                요청 금액: {float(request.get('amount', 0)):,.0f} {request.get('currency', 'VND')}
            </div>
        </div>
        
        <!-- 상세 정보 -->
        <div class="print-section">
            <div class="print-section-title">📝 상세 정보</div>
            <table class="print-info-table">
                <tr>
                    <td class="label">지출 목적</td>
                    <td class="value">{request.get('purpose', 'N/A')}</td>
                </tr>
                <tr>
                    <td class="label">첨부 파일</td>
                    <td class="value">{request.get('attachments', '없음') if request.get('attachments') else '없음'}</td>
                </tr>
                <tr>
                    <td class="label">추가 메모</td>
                    <td class="value">{request.get('additional_notes', '없음') if request.get('additional_notes') else '없음'}</td>
                </tr>
            </table>
        </div>
        
        <!-- 서명란 -->
        <div class="print-signature">
            <div class="signature-box">
                <div style="margin-bottom: 40px;">요청자</div>
                <div>{request.get('requester_name', 'N/A')}</div>
                <div style="font-size: 12px; margin-top: 5px;">서명: ________________</div>
            </div>
            <div class="signature-box">
                <div style="margin-bottom: 40px;">승인자</div>
                <div>법인장</div>
                <div style="font-size: 12px; margin-top: 5px;">서명: ________________</div>
            </div>
        </div>
        
        <!-- 출력 정보 -->
        <div style="text-align: center; margin-top: 30px; font-size: 10pt; color: #666;">
            출력일시: {current_date} | 시스템: ERP 통합관리시스템
        </div>
    </div>
    """
    
    # JavaScript 프린트 함수
    print_js = """
    <script>
    function printExpenseRequest() {
        window.print();
    }
    
    // 자동으로 프린트 대화상자 열기 (선택적)
    // setTimeout(function() {
    //     window.print();
    // }, 500);
    </script>
    """
    
    # 컨테이너로 감싸기
    with st.container():
        st.markdown("### 🖨️ 지출요청서 프린트 미리보기")
        
        # 프린트 버튼 
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🖨️ 프린트하기", key=f"print_btn_{request_id}", help="브라우저 프린트 대화상자를 엽니다"):
                # 프린트 상태 저장
                st.session_state[f'print_triggered_{request_id}'] = True
                st.rerun()
        with col2:
            if st.button("❌ 닫기", key=f"close_print_{request_id}"):
                st.session_state[f'show_print_{request_id}'] = False
                st.rerun()
        
        st.divider()
        
        # 실제 데이터 추출 및 디버깅
        # st.write("DEBUG - 원본 request 데이터:", request)  # 디버그용 - 일시적으로 주석 처리
        
        # 고유한 문서 ID 생성
        doc_id = request.get('request_id', request.get('id', request_id))
        if not doc_id:
            import time
            doc_id = int(time.time() * 1000) % 999  # timestamp 기반 고유 ID
        
        # 지출요청서의 항목들 조회 (다중 항목 지원)
        from managers.sqlite.sqlite_expense_request_manager import SQLiteExpenseRequestManager
        expense_mgr = SQLiteExpenseRequestManager()
        items = expense_mgr.get_expense_items(doc_id)
        
        # 기본 정보 추출
        requester_name = request.get('requester_name', 'N/A')
        request_date = request.get('request_date', request.get('created_at', 'N/A'))
        if request_date and request_date != 'N/A':
            request_date = str(request_date)[:10]  # 날짜만 표시 - 문자열로 변환
        else:
            request_date = datetime.now().strftime('%Y-%m-%d')  # 기본값
        expense_title = request.get('expense_title', request.get('category', 'N/A'))
        currency = request.get('currency', 'VND')
        
        # expected_date 수정 - 실제 필드명에 맞춰 확인
        expected_date = request.get('expected_date', 'N/A')
        if expected_date == 'N/A':
            expected_date = request.get('expense_date', 'N/A')  # 다른 필드명도 확인
        if expected_date and expected_date != 'N/A':
            expected_date = str(expected_date)[:10]  # 날짜만 표시 - 문자열로 변환
        
        # expense_description 수정
        expense_description = request.get('expense_description', 'N/A')
        if expense_description == 'N/A':
            expense_description = request.get('purpose', request.get('notes', 'N/A'))
        
        # notes 수정
        notes = request.get('notes', '없음')
        if not notes or notes == '없음':
            notes = request.get('additional_notes', '없음')
        
        # 총 금액 계산 (다중 항목 지원)
        if items:
            total_amount = sum(float(item.get('item_amount', 0)) for item in items)
            # 다중 항목 테이블 HTML 생성
            items_table_html = '<div style="margin: 15px 0; font-weight: bold; font-size: 12px;">📋 지출 항목 상세 (EXPENSE ITEMS DETAIL / CHI TIẾT CÁC KHOẢN CHI)</div>'
            items_table_html += '<table class="expense-info-table">'
            items_table_html += '<tr style="background: #f0f0f0;">'
            items_table_html += '<th style="width: 40%;">항목 설명<br/><span style="font-size: 8px; font-weight: normal;">(Item Description / Mô tả hạng mục)</span></th>'
            items_table_html += '<th style="width: 15%;">카테고리<br/><span style="font-size: 8px; font-weight: normal;">(Category / Danh mục)</span></th>'
            items_table_html += '<th style="width: 20%;">금액<br/><span style="font-size: 8px; font-weight: normal;">(Amount / Số tiền)</span></th>'
            items_table_html += '<th style="width: 15%;">업체<br/><span style="font-size: 8px; font-weight: normal;">(Vendor / Nhà cung cấp)</span></th>'
            items_table_html += '<th style="width: 10%;">메모<br/><span style="font-size: 8px; font-weight: normal;">(Notes / Ghi chú)</span></th>'
            items_table_html += '</tr>'
            
            for item in items:
                items_table_html += '<tr>'
                items_table_html += f'<td>{item.get("item_description", "N/A")}</td>'
                items_table_html += f'<td>{item.get("item_category", "N/A")}</td>'
                items_table_html += f'<td style="text-align: right; font-weight: bold;">{float(item.get("item_amount", 0)):,.0f} {item.get("item_currency", currency)}</td>'
                items_table_html += f'<td>{item.get("vendor", "미입력") if item.get("vendor") else "미입력"}</td>'
                items_table_html += f'<td>{item.get("item_notes", "없음") if item.get("item_notes") else "없음"}</td>'
                items_table_html += '</tr>'
            items_table_html += '</table>'
        else:
            # 기존 단일 항목 지원 (후방 호환성)
            total_amount = float(request.get('amount', request.get('total_amount', 0)))
            items_table_html = '<div style="margin: 15px 0; font-size: 11px; color: #666;">※ 단일 항목 지출요청서</div>'
        
        # 새로운 프린트 기능 - 실제 데이터로 치환 (f-string을 사용하지 않고 format() 사용)
        new_print_html = """
        <style>
        .expense-print-doc {{
            max-width: 210mm;
            margin: 5px auto;
            padding: 12px;
            padding-bottom: 80px;
            border: 1px solid #333;
            font-family: 'Malgun Gothic', Arial, sans-serif;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            line-height: 1.1;
            font-size: 11px;
            page-break-inside: avoid;
            position: relative;
            min-height: 600px;
        }}
        .expense-header {{
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 8px;
            margin-bottom: 10px;
        }}
        .expense-title {{
            font-size: 16px;
            font-weight: bold;
            color: #d32f2f;
            margin: 6px 0 4px 0;
            text-decoration: underline;
            line-height: 1.1;
        }}
        .expense-info-table {{
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #333;
            margin: 6px 0;
        }}
        .expense-info-table th, .expense-info-table td {{
            padding: 4px 6px;
            border: 1px solid #333;
            text-align: left;
            vertical-align: middle;
            font-size: 10px;
            line-height: 1.1;
        }}
        .expense-info-table th {{
            background: #f5f5f5;
            font-weight: bold;
            width: 30%;
            color: #333;
        }}
        .expense-info-table td {{
            background: #ffffff;
            font-size: 10px;
        }}
        .expense-amount-row {{
            background: #fff3e0 !important;
            color: #d84315;
            font-weight: bold;
            font-size: 18px;
        }}
        .expense-signature {{
            margin-top: 30px;
            display: flex;
            justify-content: space-between;
            page-break-inside: avoid;
            position: absolute;
            bottom: 20px;
            left: 12px;
            right: 12px;
        }}
        .expense-sig-box {{
            width: 45%;
            text-align: center;
            border: 1px solid #333;
            padding: 12px 10px;
            background: #fafafa;
            font-size: 9px;
            line-height: 1.1;
        }}
        .print-btn-new {{
            background: #1976d2;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            margin: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }}
        .print-btn-new:hover {{ 
            background: #1565c0; 
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        @media print {{
            @page {{
                margin: 0 !important;
                size: A4 !important;
            }}
            * {{
                visibility: hidden !important;
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }}
            .expense-print-doc, .expense-print-doc * {{
                visibility: visible !important;
            }}
            html, body {{ 
                margin: 0 !important; 
                padding: 0 !important; 
                font-family: 'Malgun Gothic', Arial, sans-serif !important;
                font-size: 12px !important;
                background: white !important;
                line-height: 1.1 !important;
                width: 100% !important;
                height: 100% !important;
            }}
            .no-print {{ 
                display: none !important; 
                visibility: hidden !important;
            }}
            .expense-print-doc {{ 
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 210mm !important;
                height: 297mm !important;
                margin: 0 !important; 
                box-shadow: none !important; 
                border: none !important;
                max-width: none !important;
                padding: 15mm !important;
                font-size: 12px !important;
                background: white !important;
                line-height: 1.1 !important;
                overflow: hidden !important;
            }}
            .expense-header {{ 
                text-align: center !important;
                border-bottom: 1px solid #333 !important; 
                padding-bottom: 6px !important;
                margin-bottom: 8px !important;
            }}
            .expense-title {{
                font-size: 14px !important;
                font-weight: bold !important;
                color: black !important;
                margin: 4px 0 3px 0 !important;
                text-decoration: underline !important;
                line-height: 1.0 !important;
            }}
            .expense-info-table {{
                width: 100% !important;
                border-collapse: collapse !important;
                border: 1px solid #333 !important;
                margin: 5px 0 !important;
                font-size: 12px !important;
            }}
            .expense-info-table th, .expense-info-table td {{
                padding: 6px 8px !important;
                font-size: 11px !important;
                border: 1px solid #333 !important;
                text-align: left !important;
                vertical-align: middle !important;
                line-height: 1.1 !important;
            }}
            .expense-info-table th {{
                background: #f5f5f5 !important;
                font-weight: bold !important;
                width: 30% !important;
                color: black !important;
            }}
            .expense-amount-row {{
                background: #fff3e0 !important;
                color: black !important;
                font-weight: bold !important;
                font-size: 18px !important;
            }}
            .expense-signature {{
                margin-top: 30px !important;
                display: flex !important;
                justify-content: space-between !important;
                page-break-inside: avoid !important;
                position: absolute !important;
                bottom: 20mm !important;
                left: 15mm !important;
                right: 15mm !important;
            }}
            .expense-sig-box {{
                width: 45% !important;
                text-align: center !important;
                border: 1px solid #333 !important;
                padding: 12px 10px !important;
                background: #fafafa !important;
                font-size: 9px !important;
                line-height: 1.1 !important;
            }}
            /* 지출 항목 상세 테이블 스타일 */
            .expense-info-table th:nth-child(1),
            .expense-info-table td:nth-child(1) {{
                width: 40% !important;
                max-width: 40% !important;
            }}
            .expense-info-table th:nth-child(2),
            .expense-info-table td:nth-child(2) {{
                width: 15% !important;
                max-width: 15% !important;
            }}
            .expense-info-table th:nth-child(3),
            .expense-info-table td:nth-child(3) {{
                width: 20% !important;
                max-width: 20% !important;
            }}
            .expense-info-table th:nth-child(4),
            .expense-info-table td:nth-child(4) {{
                width: 15% !important;
                max-width: 15% !important;
            }}
            .expense-info-table th:nth-child(5),
            .expense-info-table td:nth-child(5) {{
                width: 10% !important;
                max-width: 10% !important;
            }}
            /* 다중 항목 테이블의 컴팩트한 레이아웃 */
            .expense-info-table[style*="background: #f0f0f0"] {{
                table-layout: fixed !important;
                width: 100% !important;
            }}
            .expense-info-table td {{
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                white-space: normal !important;
            }}
        }}
        </style>
        
        <div class="expense-print-doc" id="expensePrintContent">
            <div class="expense-header">
                <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 4px; line-height: 1.1;">
                    유몰드 베트남 (YUMOLD VIETNAM CO., LTD)
                </div>
                <div style="font-size: 9px; margin-bottom: 4px; line-height: 1.1;">📍 Lot A2-4, Song Than 2 Industrial Park, An Phu Ward, Thuan An City, Binh Duong Province</div>
                <div class="expense-title">지출요청서 (EXPENSE REQUEST)</div>
                <div style="font-size: 9px; color: #666; margin-top: 3px; line-height: 1.1;">문서번호: EXP-{request_date_clean}-{doc_id_formatted}</div>
            </div>
            
            <table class="expense-info-table">
                <tr>
                    <th>요청자 (Requester)</th>
                    <td>{requester_name}</td>
                </tr>
                <tr>
                    <th>요청일 (Request Date)</th>
                    <td>{request_date}</td>
                </tr>
                <tr>
                    <th>지출 유형 (Expense Type)</th>
                    <td>{expense_title}</td>
                </tr>
                <tr class="expense-amount-row">
                    <th>총 지출 금액 (Total Amount)</th>
                    <td>{total_amount:,.0f} {currency}</td>
                </tr>
                <tr>
                    <th>지출 예정일 (Expected Date)</th>
                    <td>{expected_date}</td>
                </tr>
                <tr>
                    <th>지출 목적 (Purpose)</th>
                    <td>{expense_description}</td>
                </tr>
                <tr>
                    <th>메모 (Notes)</th>
                    <td>{notes}</td>
                </tr>
            </table>
            
            <!-- 지출 항목 상세 테이블 -->
            {items_table_html}
            
            <div class="expense-signature">
                <div class="expense-sig-box">
                    <div style="font-weight: bold; margin-bottom: 15px; font-size: 9px;">신청자 (Requester)</div>
                    <div style="height: 25px; border-bottom: 1px solid #333; margin-bottom: 8px;"></div>
                    <div style="font-weight: bold; font-size: 9px;">{requester_name}</div>
                </div>
                <div class="expense-sig-box">
                    <div style="font-weight: bold; margin-bottom: 15px; font-size: 9px;">승인자 (Approver)</div>
                    <div style="height: 25px; border-bottom: 1px solid #333; margin-bottom: 8px;"></div>
                    <div style="font-weight: bold; font-size: 9px;">법인장</div>
                </div>
            </div>
        </div>
        
        <div class="no-print" style="text-align: center; margin: 20px 0;">
            <button onclick="safePrint()" class="print-btn-new">🖨️ 프린트하기</button>
        </div>
        
        <script>
        // 프린트 전용 스타일 추가
        function addEnhancedPrintStyles() {{{{
            var printStyle = document.createElement('style');
            printStyle.innerHTML = `
            @media print {{{{
                * {{{{
                    visibility: hidden !important;
                }}}}
                .expense-print-doc, .expense-print-doc * {{{{
                    visibility: visible !important;
                }}}}
                .expense-print-doc {{{{
                    position: absolute !important;
                    left: 0 !important;
                    top: 0 !important;
                    width: 100% !important;
                    height: auto !important;
                    margin: 0 !important;
                    padding: 10mm !important;
                    box-shadow: none !important;
                    border: none !important;
                    background: white !important;
                    font-size: 12px !important;
                }}}}
                .no-print {{{{
                    display: none !important;
                    visibility: hidden !important;
                }}}}
                body {{{{
                    margin: 0 !important;
                    padding: 0 !important;
                    background: white !important;
                }}}}
            }}}}`;
            document.head.appendChild(printStyle);
        }}}}
        
        // 스타일 적용
        addEnhancedPrintStyles();
        
        // 강제 프린트 함수
        function safePrint() {{{{
            // 현재 페이지에서 직접 프린트하는 방식으로 변경
            window.print();
        }}}}
        
        // 백업용 새 창 프린트 함수 (필요시 사용)
        function safePrintNewWindow() {{{{
            var printWindow = window.open('', '_blank');
            var printContent = document.querySelector('.expense-print-doc').outerHTML;
            
            printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>지출요청서</title>
                <style>
                    @page {{{{
                        margin: 0;
                        size: A4;
                    }}}}
                    * {{{{
                        -webkit-print-color-adjust: exact;
                        color-adjust: exact;
                    }}}}
                    body {{{{
                        margin: 0;
                        padding: 0;
                        font-family: 'Malgun Gothic', Arial, sans-serif;
                        font-size: 12px;
                        background: white;
                        line-height: 1.1;
                        width: 100%;
                        height: 100%;
                    }}}}
                    .expense-print-doc {{{{
                        position: absolute;
                        left: 0;
                        top: 0;
                        width: 210mm;
                        height: 297mm;
                        margin: 0;
                        box-shadow: none;
                        border: none;
                        max-width: none;
                        padding: 15mm;
                        font-size: 12px;
                        background: white;
                        line-height: 1.1;
                        overflow: hidden;
                    }}}}
                    .expense-header {{{{
                        text-align: center;
                        border-bottom: 1px solid #333;
                        padding-bottom: 6px;
                        margin-bottom: 8px;
                    }}}}
                    .expense-title {{{{
                        font-size: 14px;
                        font-weight: bold;
                        color: black;
                        margin: 4px 0 3px 0;
                        text-decoration: underline;
                        line-height: 1.0;
                    }}}}
                    .expense-info-table {{{{
                        width: 100%;
                        border-collapse: collapse;
                        border: 1px solid #333;
                        margin: 5px 0;
                        font-size: 12px;
                        table-layout: fixed;
                    }}}}
                    .expense-info-table th, .expense-info-table td {{{{
                        padding: 6px 8px;
                        font-size: 11px;
                        border: 1px solid #333;
                        text-align: left;
                        vertical-align: middle;
                        line-height: 1.1;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        white-space: normal;
                    }}}}
                    .expense-info-table th {{{{
                        background: #f5f5f5;
                        font-weight: bold;
                        width: 30%;
                        color: black;
                    }}}}
                    .expense-amount-row {{{{
                        background: #fff3e0;
                        color: black;
                        font-weight: bold;
                        font-size: 18px;
                    }}}}
                    .expense-signature {{{{
                        margin-top: 30px;
                        display: flex;
                        justify-content: space-between;
                        page-break-inside: avoid;
                        position: absolute;
                        bottom: 20mm;
                        left: 15mm;
                        right: 15mm;
                    }}}}
                    .expense-sig-box {{{{
                        width: 45%;
                        text-align: center;
                        border: 1px solid #333;
                        padding: 12px 10px;
                        background: #fafafa;
                        font-size: 9px;
                        line-height: 1.1;
                    }}}}
                    /* 지출 항목 상세 테이블 스타일 */
                    .expense-info-table th:nth-child(1),
                    .expense-info-table td:nth-child(1) {{{{
                        width: 40%;
                        max-width: 40%;
                    }}}}
                    .expense-info-table th:nth-child(2),
                    .expense-info-table td:nth-child(2) {{{{
                        width: 15%;
                        max-width: 15%;
                    }}}}
                    .expense-info-table th:nth-child(3),
                    .expense-info-table td:nth-child(3) {{{{
                        width: 20%;
                        max-width: 20%;
                    }}}}
                    .expense-info-table th:nth-child(4),
                    .expense-info-table td:nth-child(4) {{{{
                        width: 15%;
                        max-width: 15%;
                    }}}}
                    .expense-info-table th:nth-child(5),
                    .expense-info-table td:nth-child(5) {{{{
                        width: 10%;
                        max-width: 10%;
                    }}}}
                    .no-print {{ display: none; }}
                </style>
            </head>
            <body>
                ` + printContent + `
            </body>
            </html>
            `);
            
            printWindow.document.close();
            printWindow.focus();
            
            // 프린트 준비 완료 후 프린트 실행
            printWindow.onload = function() {{{{
                setTimeout(function() {{{{
                    printWindow.print();
                    // 프린트 대화상자 닫힌 후 창 닫기
                    setTimeout(function() {{{{
                        printWindow.close();
                    }}}}, 1000);
                }}}}, 500);
            }}}};
        }}}}
        
        // 자동 프린트 트리거 체크
        {auto_print_script}
        </script>
        """.format(
            request_date=request_date,
            request_date_clean=request_date.replace('-', '') if request_date and '-' in str(request_date) else request_date,
            doc_id=doc_id,
            doc_id_formatted=str(doc_id).zfill(3),
            requester_name=requester_name,
            expense_title=expense_title,
            total_amount=total_amount,
            currency=currency,
            expected_date=expected_date,
            expense_description=expense_description,
            notes=notes,
            items_table_html=items_table_html,
            auto_print_script=auto_print_script
        )
        
        st.components.v1.html(new_print_html, height=800, scrolling=True)
        
        st.success("📄 지출요청서를 프린트할 준비가 완료되었습니다. 위의 버튼들을 사용하세요!")
