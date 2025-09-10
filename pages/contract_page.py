# -*- coding: utf-8 -*-
"""
계약서 관리 페이지
계약서 등록, 조회, 수정, 삭제 및 통계 기능을 제공합니다.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go
from contract_manager import ContractManager

def show_contract_page(get_text):
    """계약서 관리 페이지를 표시합니다."""
    st.title(f"📝 {get_text('contract_management')}")
    st.markdown("---")
    
    # 계약서 매니저 초기화
    if 'contract_manager' not in st.session_state:
        st.session_state.contract_manager = ContractManager()
    
    contract_manager = st.session_state.contract_manager
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📊 {get_text('contract_overview')}", 
        f"📝 {get_text('contract_registration')}", 
        f"🔍 {get_text('contract_management_with_edit')}",
        f"⚠️ {get_text('expiry_alerts')}",
        f"📈 {get_text('contract_statistics')}"
    ])
    
    with tab1:
        show_contract_overview(contract_manager, get_text)
    
    with tab2:
        show_contract_registration(contract_manager, get_text)
    
    with tab3:
        show_contract_management_with_edit_delete(contract_manager, get_text)
    
    with tab4:
        show_expiry_alerts(contract_manager, get_text)
    
    with tab5:
        show_contract_statistics(contract_manager, get_text)
    
    # 자동 상태 업데이트 (만료된 계약서 확인)
    check_and_update_expired_contracts(contract_manager)

def show_contract_overview(contract_manager, get_text):
    """계약서 현황 대시보드"""
    st.header(f"📊 {get_text('contract_overview_dashboard')}")
    
    # 통계 가져오기
    stats = contract_manager.get_contract_statistics()
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(get_text('total_contracts'), f"{stats.get('total_contracts', 0)}개")
    
    with col2:
        st.metric(get_text('active_contracts'), f"{stats.get('active_contracts', 0)}개")
    
    with col3:
        st.metric(get_text('expired_contracts'), f"{stats.get('expired_contracts', 0)}개")
    
    with col4:
        total_amount = stats.get('total_amount', 0)
        st.metric(get_text('total_contract_amount'), f"${total_amount:,.0f}")
    
    st.markdown("---")
    
    # 만료 예정 계약 알림
    expiring_contracts = contract_manager.get_expiring_contracts(30)
    if len(expiring_contracts) > 0:
        st.warning(f"⚠️ **{get_text('expiring_contracts_30_days')}**: {len(expiring_contracts)}건")
        
        # 만료 예정 계약 목록 표시
        st.subheader(f"🔔 {get_text('expiring_contracts_list')}")
        display_cols = ['contract_id', 'contract_name', 'counterpart_name', 'end_date', 'status']
        st.dataframe(
            expiring_contracts[display_cols],
            use_container_width=True,
            hide_index=True
        )
    
    # 최근 계약서 목록
    st.subheader("📋 최근 계약서")
    recent_contracts = contract_manager.get_all_contracts().head(10)
    if len(recent_contracts) > 0:
        display_cols = ['contract_id', 'contract_name', 'contract_type', 'counterpart_name', 'status', 'created_date']
        st.dataframe(
            recent_contracts[display_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("등록된 계약서가 없습니다.")

def show_contract_registration(contract_manager, get_text):
    """계약서 등록 폼"""
    st.header(f"📝 {get_text('new_contract_registration')}")
    
    # 성공 메시지 처리
    if 'show_success_message' in st.session_state:
        st.success(f"✅ 계약서가 성공적으로 등록되었습니다! (ID: {st.session_state.show_success_message})")
        del st.session_state.show_success_message
    
    # 폼 키에 타임스탬프 추가하여 완전한 리셋 보장
    if 'form_reset_key' not in st.session_state:
        st.session_state.form_reset_key = str(int(time.time()))
    
    form_key = f"contract_registration_form_{st.session_state.form_reset_key}"
    
    with st.form(form_key, clear_on_submit=True):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            contract_name = st.text_input(f"{get_text('contract_name')}*", placeholder=get_text('contract_name_placeholder'), key="reg_contract_name")
            contract_type = st.selectbox(f"{get_text('contract_type')}*", contract_manager.get_contract_types(), key="reg_contract_type")
            counterpart_type = st.selectbox(get_text('counterpart_type'), [get_text('customer'), get_text('supplier'), get_text('partner'), get_text('other')], key="reg_counterpart_type")
            counterpart_name = st.text_input(f"{get_text('counterpart_name')}*", placeholder=get_text('counterpart_name_placeholder'), key="reg_counterpart_name")
        
        with col2:
            start_date = st.date_input(f"{get_text('start_date')}*", value=datetime.now().date(), key="reg_start_date")
            end_date = st.date_input(f"{get_text('end_date')}*", key="reg_end_date")
            contract_amount = st.number_input(get_text('contract_amount'), min_value=0.0, step=1000.0, key="reg_contract_amount")
            currency = st.selectbox(get_text('currency'), contract_manager.get_currency_options(), key="reg_currency")
        
        # 추가 정보
        payment_terms = st.text_area(get_text('payment_terms'), placeholder=get_text('payment_terms_placeholder'), key="reg_payment_terms")
        responsible_person = st.text_input(get_text('responsible_person'), placeholder=get_text('responsible_person_placeholder'), key="reg_responsible_person")
        notes = st.text_area(get_text('special_notes'), placeholder=get_text('special_notes_placeholder'), key="reg_notes")
        
        # 제출 버튼
        submitted = st.form_submit_button(get_text('register_contract'), type="primary")
        
        if submitted:
            # 필수 필드 검증
            errors = []
            if not contract_name or not contract_name.strip():
                errors.append("계약서명을 입력해주세요.")
            if not counterpart_name or not counterpart_name.strip():
                errors.append("계약 상대방을 입력해주세요.")
            if not end_date:
                errors.append("계약 종료일을 선택해주세요.")
            elif end_date <= start_date:
                errors.append("종료일은 시작일보다 늦어야 합니다.")
            
            # 계약 기간 유효성 검증
            if start_date and end_date:
                period_days = (end_date - start_date).days
                if period_days > 3650:  # 10년
                    errors.append("계약 기간이 너무 깁니다. (최대 10년)")
                elif period_days <= 0:
                    errors.append("유효하지 않은 계약 기간입니다.")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # 계약 기간 정보 표시
                period_days = (end_date - start_date).days
                period_months = period_days // 30
                st.info(f"📅 계약 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} (약 {period_months}개월, {period_days}일)")
                # 중복 확인 (같은 이름과 상대방으로 등록된 계약이 있는지)
                existing_contracts = contract_manager.get_all_contracts()
                if len(existing_contracts) > 0:
                    duplicate = existing_contracts[
                        (existing_contracts['contract_name'] == contract_name) & 
                        (existing_contracts['counterpart_name'] == counterpart_name)
                    ]
                    if len(duplicate) > 0:
                        st.error(f"동일한 계약서가 이미 존재합니다: {contract_name} (상대방: {counterpart_name})")
                        st.stop()
                
                # 계약서 데이터 준비
                contract_data = {
                    'contract_name': contract_name,
                    'contract_type': contract_type,
                    'counterpart_type': counterpart_type,
                    'counterpart_name': counterpart_name,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'contract_amount': contract_amount,
                    'currency': currency,
                    'payment_terms': payment_terms,
                    'status': '진행중',
                    'responsible_person': responsible_person,
                    'notes': notes
                }
                
                # 계약서 등록
                success, contract_id = contract_manager.add_contract(contract_data)
                
                if success:
                    # 등록 성공 확인 메시지 (디버깅용)
                    st.write("**등록된 데이터 확인:**")
                    st.json({
                        "contract_id": contract_id,
                        "계약서명": contract_name,
                        "시작일": start_date.strftime('%Y-%m-%d'),
                        "종료일": end_date.strftime('%Y-%m-%d'),
                        "계약기간": f"{period_days}일 ({period_months}개월)",
                        "상대방": counterpart_name,
                        "금액": f"{contract_amount:,.0f} {currency}"
                    })
                    
                    # 폼 리셋을 위해 새로운 키 생성
                    st.session_state.form_reset_key = str(int(time.time()))
                    st.session_state.show_success_message = contract_id
                    
                    # 잠시 후 리로드
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("계약서 등록에 실패했습니다.")

def show_contract_management_with_edit_delete(contract_manager, get_text):
    """계약서 관리 및 편집"""
    st.header("🔍 계약서 관리")
    
    # 검색 및 필터링
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("검색", placeholder="계약서명, 상대방명 등으로 검색")
    
    with col2:
        status_filter = st.selectbox("상태 필터", ["전체"] + contract_manager.get_contract_statuses())
    
    with col3:
        type_filter = st.selectbox("유형 필터", ["전체"] + contract_manager.get_contract_types())
    
    # 계약서 목록 가져오기
    contracts_df = contract_manager.get_all_contracts()
    
    # 필터링 적용
    if len(contracts_df) > 0:
        # 검색어 필터링
        if search_term:
            contracts_df = contract_manager.search_contracts(search_term)
        
        # 상태 필터링
        if status_filter != "전체":
            contracts_df = contracts_df[contracts_df['status'] == status_filter]
        
        # 유형 필터링
        if type_filter != "전체":
            contracts_df = contracts_df[contracts_df['contract_type'] == type_filter]
    
    # 계약서 목록 표시
    if len(contracts_df) > 0:
        st.subheader(f"📋 계약서 목록 ({len(contracts_df)}건)")
        
        # 계약서 선택
        for idx, row in contracts_df.iterrows():
            with st.expander(f"📄 {row['contract_name']} ({row['contract_id']})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # 상태에 따른 아이콘과 색상
                    status_icons = {
                        '준비중': '📝',
                        '진행중': '✅', 
                        '일시정지': '⏸️',
                        '만료': '⏰',
                        '해지': '❌',
                        '완료': '🏆'
                    }
                    status_icon = status_icons.get(row['status'], '📄')
                    
                    st.write(f"**유형**: {row['contract_type']}")
                    st.write(f"**상대방**: {row['counterpart_name']}")
                    # 날짜 정보 처리 및 기간 계산
                    try:
                        if pd.notna(row['start_date']) and pd.notna(row['end_date']):
                            start_date_str = pd.to_datetime(row['start_date']).strftime('%Y-%m-%d')
                            end_date_str = pd.to_datetime(row['end_date']).strftime('%Y-%m-%d')
                            
                            # 기간 계산
                            start_date_obj = pd.to_datetime(row['start_date']).date()
                            end_date_obj = pd.to_datetime(row['end_date']).date()
                            period_days = (end_date_obj - start_date_obj).days
                            period_months = period_days // 30
                            
                            st.write(f"**기간**: {start_date_str} ~ {end_date_str}")
                            st.write(f"**계약 기간**: {period_days}일 (약 {period_months}개월)")
                        else:
                            st.write(f"**기간**: 날짜 정보 없음")
                            st.warning("⚠️ 계약 시작일 또는 종료일이 누락되었습니다.")
                    except Exception as e:
                        st.write(f"**기간**: 날짜 처리 오류")
                        st.error(f"날짜 처리 중 오류: {e}")
                    st.write(f"**금액**: {row['contract_amount']:,.0f} {row['currency']}")
                    st.write(f"**상태**: {status_icon} {row['status']}")
                
                with col2:
                    if st.button("🔄 상태변경", key=f"status_{row['contract_id']}"):
                        st.session_state.status_update_id = row['contract_id']
                        st.rerun()
                    
                    if st.button("✏️ 수정", key=f"edit_{row['contract_id']}"):
                        st.session_state.edit_contract_id = row['contract_id']
                        st.rerun()
                
                with col3:
                    if st.button("📊 히스토리", key=f"history_{row['contract_id']}"):
                        st.session_state.view_history_id = row['contract_id']
                        st.rerun()
                    
                    if st.button("🗑️ 삭제", key=f"delete_{row['contract_id']}"):
                        if st.session_state.get('confirm_delete') == row['contract_id']:
                            success, message = contract_manager.delete_contract(row['contract_id'])
                            if success:
                                st.success("계약서가 삭제되었습니다.")
                                del st.session_state.confirm_delete
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.session_state.confirm_delete = row['contract_id']
                            st.warning("삭제하시겠습니까? 삭제 버튼을 다시 클릭하세요.")
                
                # 상태 업데이트 폼 표시
                if st.session_state.get('status_update_id') == row['contract_id']:
                    show_status_update_form(contract_manager, row['contract_id'], row)
                
                # 상태 히스토리 표시
                if st.session_state.get('view_history_id') == row['contract_id']:
                    show_status_history(contract_manager, row['contract_id'])
        
        # 계약서 편집 폼
        if 'edit_contract_id' in st.session_state:
            show_contract_edit_form(contract_manager, st.session_state.edit_contract_id)
    else:
        st.info("조건에 맞는 계약서가 없습니다.")

def show_status_update_form(contract_manager, contract_id, contract_data):
    """상태 업데이트 폼"""
    st.markdown("---")
    st.subheader("🔄 계약서 상태 업데이트")
    
    current_status = contract_data['status']
    allowed_statuses = contract_manager.get_allowed_status_transitions(current_status)
    
    if not allowed_statuses:
        st.info(f"'{current_status}' 상태에서는 더 이상 상태를 변경할 수 없습니다.")
        if st.button("닫기", key="close_status_form"):
            if 'status_update_id' in st.session_state:
                del st.session_state.status_update_id
            st.rerun()
        return
    
    with st.form(f"status_update_form_{contract_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**현재 상태**: {current_status}")
            new_status = st.selectbox("새 상태 선택", allowed_statuses)
            
        with col2:
            reason = st.text_area("상태 변경 사유", placeholder="상태 변경 이유를 입력하세요")
            updated_by = st.text_input("변경자", value=st.session_state.get('current_user_name', ''), placeholder="변경자명")
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("상태 변경", type="primary")
        
        with col_cancel:
            cancelled = st.form_submit_button("취소")
        
        if submitted:
            if not reason.strip():
                st.error("상태 변경 사유를 입력해주세요.")
            else:
                success, message = contract_manager.update_contract_status(
                    contract_id, new_status, reason, updated_by
                )
                
                if success:
                    st.success(f"✅ {message}")
                    if 'status_update_id' in st.session_state:
                        del st.session_state.status_update_id
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        if cancelled:
            if 'status_update_id' in st.session_state:
                del st.session_state.status_update_id
            st.rerun()

def show_status_history(contract_manager, contract_id):
    """상태 변경 히스토리 표시"""
    st.markdown("---")
    st.subheader("📊 계약서 상태 히스토리")
    
    history_df = contract_manager.get_status_history(contract_id)
    
    if len(history_df) == 0:
        st.info("상태 변경 이력이 없습니다.")
    else:
        # 최신 순으로 정렬
        history_df = history_df.sort_values('update_date', ascending=False)
        
        for _, record in history_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{record['old_status']}** → **{record['new_status']}**")
                    if record['reason']:
                        st.write(f"사유: {record['reason']}")
                
                with col2:
                    st.write(f"변경일: {record['update_date']}")
                    if record['updated_by']:
                        st.write(f"변경자: {record['updated_by']}")
                
                with col3:
                    # 상태에 따른 아이콘
                    if record['new_status'] == '완료':
                        st.write("🏆")
                    elif record['new_status'] == '해지':
                        st.write("❌")
                    elif record['new_status'] == '진행중':
                        st.write("✅")
                    else:
                        st.write("📄")
            
            st.markdown("---")
    
    if st.button("히스토리 닫기", key="close_history"):
        if 'view_history_id' in st.session_state:
            del st.session_state.view_history_id
        st.rerun()

def check_and_update_expired_contracts(contract_manager):
    """만료된 계약서를 자동으로 확인하고 상태 업데이트"""
    try:
        df = contract_manager.get_all_contracts()
        if len(df) == 0:
            return
        
        today = datetime.now().date()
        
        # 만료되었지만 아직 상태가 '진행중'인 계약서 찾기
        expired_contracts = df[
            (pd.to_datetime(df['end_date']).dt.date < today) & 
            (df['status'] == '진행중')
        ]
        
        # 자동으로 만료 상태로 변경
        for _, contract in expired_contracts.iterrows():
            contract_manager.update_contract_status(
                contract['contract_id'], 
                '만료', 
                "계약 기간 종료로 인한 자동 만료",
                "시스템"
            )
        
        # 만료 예정 알림 (7일 내)
        expiring_soon = df[
            (pd.to_datetime(df['end_date']).dt.date <= today + timedelta(days=7)) &
            (pd.to_datetime(df['end_date']).dt.date >= today) &
            (df['status'] == '진행중')
        ]
        
        if len(expiring_soon) > 0:
            st.sidebar.warning(f"⚠️ {len(expiring_soon)}건의 계약이 7일 내 만료 예정입니다!")
        
    except Exception as e:
        print(f"자동 만료 처리 오류: {e}")
        st.rerun()

def show_contract_edit_form(contract_manager, contract_id):
    """계약서 편집 폼"""
    st.subheader("✏️ 계약서 수정")
    
    # 기존 계약서 데이터 로드
    contract_data = contract_manager.get_contract_by_id(contract_id)
    
    if not contract_data:
        st.error("계약서를 찾을 수 없습니다.")
        if st.button("돌아가기"):
            del st.session_state.edit_contract_id
            st.rerun()
        return
    
    # 편집 폼
    with st.form("edit_contract_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            contract_name = st.text_input("계약서명", value=contract_data.get('contract_name', ''))
            contract_type = st.selectbox("계약 유형", 
                                        ["구매계약", "판매계약", "서비스계약", "임대계약", "기타"],
                                        index=["구매계약", "판매계약", "서비스계약", "임대계약", "기타"].index(contract_data.get('contract_type', '기타')) if contract_data.get('contract_type', '기타') in ["구매계약", "판매계약", "서비스계약", "임대계약", "기타"] else 4)
            counterpart_type = st.selectbox("상대방 유형", 
                                           ["고객", "공급업체", "기타"],
                                           index=["고객", "공급업체", "기타"].index(contract_data.get('counterpart_type', '기타')) if contract_data.get('counterpart_type', '기타') in ["고객", "공급업체", "기타"] else 2)
            counterpart_name = st.text_input("상대방명", value=contract_data.get('counterpart_name', ''))
        
        with col2:
            from datetime import datetime
            import pandas as pd
            
            # 안전한 날짜 변환 함수
            def safe_date_parse(date_value, default_date='2025-01-01'):
                if date_value is None:
                    return datetime.strptime(default_date, '%Y-%m-%d').date()
                elif isinstance(date_value, str):
                    try:
                        return datetime.strptime(date_value, '%Y-%m-%d').date()
                    except:
                        return datetime.strptime(default_date, '%Y-%m-%d').date()
                elif isinstance(date_value, pd.Timestamp):
                    return date_value.date()
                elif hasattr(date_value, 'date'):
                    return date_value.date()
                else:
                    return datetime.strptime(default_date, '%Y-%m-%d').date()
            
            # 안전한 날짜 처리 - NaT 값 확인
            start_date_value = contract_data.get('start_date')
            end_date_value = contract_data.get('end_date')
            
            # NaT 값인지 확인하고 기본값 사용
            if pd.isna(start_date_value) or start_date_value is pd.NaT:
                start_date_parsed = datetime.strptime('2025-01-01', '%Y-%m-%d').date()
            else:
                start_date_parsed = safe_date_parse(start_date_value, '2025-01-01')
            
            if pd.isna(end_date_value) or end_date_value is pd.NaT:
                end_date_parsed = datetime.strptime('2025-12-31', '%Y-%m-%d').date()
            else:
                end_date_parsed = safe_date_parse(end_date_value, '2025-12-31')
            
            start_date = st.date_input("계약 시작일", value=start_date_parsed)
            end_date = st.date_input("계약 종료일", value=end_date_parsed)
            contract_amount = st.number_input("계약 금액", value=float(contract_data.get('contract_amount', 0)), min_value=0.0)
            currency = st.selectbox("통화", ["USD", "VND", "KRW"],
                                   index=["USD", "VND", "KRW"].index(contract_data.get('currency', 'USD')) if contract_data.get('currency', 'USD') in ["USD", "VND", "KRW"] else 0)
        
        payment_terms = st.text_area("결제 조건", value=contract_data.get('payment_terms', ''))
        responsible_person = st.text_input("담당자", value=contract_data.get('responsible_person', ''))
        notes = st.text_area("비고", value=contract_data.get('notes', ''))
        
        # 상태 변경
        status = st.selectbox("상태", ["진행중", "완료", "취소", "만료"],
                             index=["진행중", "완료", "취소", "만료"].index(contract_data.get('status', '진행중')) if contract_data.get('status', '진행중') in ["진행중", "완료", "취소", "만료"] else 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            submit_button = st.form_submit_button("✅ 수정 완료", use_container_width=True)
        with col2:
            if st.form_submit_button("❌ 취소", use_container_width=True):
                del st.session_state.edit_contract_id
                st.rerun()
        
        if submit_button:
            # 수정된 데이터 준비
            updated_data = {
                'contract_name': contract_name,
                'contract_type': contract_type,
                'counterpart_type': counterpart_type,
                'counterpart_name': counterpart_name,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'contract_amount': contract_amount,
                'currency': currency,
                'payment_terms': payment_terms,
                'status': status,
                'responsible_person': responsible_person,
                'notes': notes
            }
            
            # 계약서 업데이트
            success, message = contract_manager.update_contract(contract_id, updated_data)
            
            if success:
                st.success("✅ 계약서가 성공적으로 수정되었습니다!")
                del st.session_state.edit_contract_id
                st.rerun()
            else:
                st.error(f"수정 실패: {message}")
            st.rerun()
        return
    


def show_expiry_alerts(contract_manager, get_text):
    """만료 알림 관리"""
    st.header("⚠️ 계약 만료 알림")
    
    # 알림 설정
    col1, col2 = st.columns(2)
    
    with col1:
        days_ahead = st.slider("알림 기간 (일)", min_value=7, max_value=90, value=30)
    
    with col2:
        st.metric("알림 대상 계약", f"{len(contract_manager.get_expiring_contracts(days_ahead))}건")
    
    # 만료 예정 계약서
    expiring_contracts = contract_manager.get_expiring_contracts(days_ahead)
    
    if len(expiring_contracts) > 0:
        st.subheader(f"📅 {days_ahead}일 내 만료 예정 계약서")
        
        # 만료까지 남은 일수 계산
        today = datetime.now()
        expiring_contracts['days_until_expiry'] = (expiring_contracts['end_date'] - today).dt.days
        
        # 긴급도별 분류
        urgent = expiring_contracts[expiring_contracts['days_until_expiry'] <= 7]
        warning = expiring_contracts[(expiring_contracts['days_until_expiry'] > 7) & 
                                   (expiring_contracts['days_until_expiry'] <= 30)]
        
        if len(urgent) > 0:
            st.error(f"🚨 **긴급 (7일 이내)**: {len(urgent)}건")
            display_cols = ['contract_id', 'contract_name', 'counterpart_name', 'end_date', 'days_until_expiry']
            st.dataframe(urgent[display_cols], use_container_width=True, hide_index=True)
        
        if len(warning) > 0:
            st.warning(f"⚠️ **주의 (8-30일)**: {len(warning)}건")
            display_cols = ['contract_id', 'contract_name', 'counterpart_name', 'end_date', 'days_until_expiry']
            st.dataframe(warning[display_cols], use_container_width=True, hide_index=True)
    else:
        st.success(f"✅ {days_ahead}일 내 만료 예정인 계약서가 없습니다.")

def show_contract_statistics(contract_manager, get_text):
    """계약서 통계 분석"""
    st.header("📈 계약서 통계 분석")
    
    # 통계 데이터 가져오기
    stats = contract_manager.get_contract_statistics()
    contracts_df = contract_manager.get_all_contracts()
    
    if len(contracts_df) == 0:
        st.info("통계를 표시할 계약서 데이터가 없습니다.")
        return
    
    # 차트 생성
    col1, col2 = st.columns(2)
    
    with col1:
        # 계약 유형별 파이 차트
        st.subheader("📊 계약 유형별 분포")
        if stats.get('contracts_by_type'):
            fig_type = px.pie(
                values=list(stats['contracts_by_type'].values()),
                names=list(stats['contracts_by_type'].keys()),
                title="계약 유형별 분포"
            )
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")
    
    with col2:
        # 계약 상태별 파이 차트
        st.subheader("📊 계약 상태별 분포")
        if stats.get('contracts_by_status'):
            fig_status = px.pie(
                values=list(stats['contracts_by_status'].values()),
                names=list(stats['contracts_by_status'].keys()),
                title="계약 상태별 분포"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")
    
    # 월별 계약 금액 추이
    st.subheader("📈 월별 계약 동향")
    if len(contracts_df) > 0:
        # 월별 계약 건수 및 금액
        contracts_df['month'] = pd.to_datetime(contracts_df['created_date']).dt.to_period('M')
        monthly_stats = contracts_df.groupby('month').agg({
            'contract_id': 'count',
            'contract_amount': 'sum'
        }).reset_index()
        
        monthly_stats['month'] = monthly_stats['month'].astype(str)
        
        fig_monthly = go.Figure()
        
        # 계약 건수
        fig_monthly.add_trace(go.Scatter(
            x=monthly_stats['month'],
            y=monthly_stats['contract_id'],
            mode='lines+markers',
            name='계약 건수',
            yaxis='y'
        ))
        
        # 계약 금액 (보조 축)
        fig_monthly.add_trace(go.Scatter(
            x=monthly_stats['month'],
            y=monthly_stats['contract_amount'],
            mode='lines+markers',
            name='계약 금액',
            yaxis='y2'
        ))
        
        fig_monthly.update_layout(
            title='월별 계약 건수 및 금액 추이',
            xaxis_title='월',
            yaxis=dict(title='계약 건수', side='left'),
            yaxis2=dict(title='계약 금액', side='right', overlaying='y'),
            legend=dict(x=0, y=1)
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # 상세 통계 테이블
    st.subheader("📋 상세 통계")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**계약 유형별 통계**")
        if stats.get('contracts_by_type'):
            type_data = list(stats['contracts_by_type'].items())
            type_df = pd.DataFrame(type_data, columns=['계약 유형', '건수'])
            st.dataframe(type_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.write("**계약 상태별 통계**")
        if stats.get('contracts_by_status'):
            status_data = list(stats['contracts_by_status'].items())
            status_df = pd.DataFrame(status_data, columns=['상태', '건수'])
            st.dataframe(status_df, use_container_width=True, hide_index=True)