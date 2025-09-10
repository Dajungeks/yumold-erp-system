"""
주문 관리 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_order_page(order_manager, quotation_manager, customer_manager, current_user_id, get_text):
    """주문 관리 메인 페이지"""
    st.title(f"📦 {get_text('order_management')}")
    
    # 탭 구성 (배송 일정 탭 제거 - 주문 목록에 이미 포함)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📋 {get_text('order_list')}", 
        f"➕ {get_text('order_creation')}", 
        f"📊 {get_text('order_statistics')}", 
        f"📈 {get_text('order_analysis')}", 
        f"🔍 {get_text('order_search')}"
    ])
    
    with tab1:
        show_order_list(order_manager, get_text)
    
    with tab2:
        show_order_creation(order_manager, quotation_manager, customer_manager, current_user_id, get_text)
    
    with tab3:
        show_order_statistics(order_manager, get_text)
    
    with tab4:
        show_order_analysis(order_manager, get_text)
    
    with tab5:
        show_order_search(order_manager, get_text)

def show_order_list(order_manager, get_text):
    """주문 목록 표시"""
    st.subheader(f"📋 {get_text('order_list')}")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_options = [get_text("all"), "pending", "confirmed", "in_production", "shipped", "delivered", "cancelled"]
        status_labels = {
            get_text("all"): get_text("all"), 
            "pending": get_text("order_status_pending"), 
            "confirmed": get_text("order_status_confirmed"), 
            "in_production": get_text("order_status_in_production"), 
            "shipped": get_text("order_status_shipped"), 
            "delivered": get_text("order_status_delivered"), 
            "cancelled": get_text("order_status_cancelled")
        }
        status_filter = st.selectbox(get_text('order_status_filter'), status_options, 
                                   format_func=lambda x: status_labels.get(x, x))
    
    with col2:
        customer_filter = st.text_input(get_text('customer_name_search'))
    
    with col3:
        date_range = st.date_input(get_text('order_date_range'), 
                                 value=(datetime.now().date() - timedelta(days=30), datetime.now().date()),
                                 help=get_text("date_range_help"))
    
    # 주문 목록 조회
    try:
        # date_range 안전 처리
        if hasattr(date_range, '__len__') and len(date_range) >= 2:
            date_from, date_to = date_range[0], date_range[1]
        elif hasattr(date_range, '__len__') and len(date_range) >= 1:
            date_from = date_to = date_range[0]
        elif date_range:
            date_from = date_to = date_range
        else:
            date_from = date_to = None
        
        orders = order_manager.get_filtered_orders(
            status_filter=None if status_filter == get_text("all") else status_filter,
            customer_filter=customer_filter if customer_filter else None,
            date_from=date_from,
            date_to=date_to
        )
        
        # DataFrame 또는 리스트 처리
        if hasattr(orders, 'empty'):
            # DataFrame인 경우
            if not orders.empty:
                orders = orders.to_dict('records')
            else:
                orders = []
        
        if orders is not None and len(orders) > 0:
            # 페이지네이션
            items_per_page = 10
            total_pages = (len(orders) - 1) // items_per_page + 1
            
            if total_pages > 1:
                page = st.selectbox("페이지", range(1, total_pages + 1))
                start_idx = (page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_orders = orders[start_idx:end_idx]
            else:
                page_orders = orders
            
            # 주문 목록 2줄 표시
            for order in page_orders:
                order_id = order.get('order_id', 'N/A')
                customer_company = order.get('customer_name', order.get('customer_company', 'N/A'))
                total_amount = order.get('total_amount', 0)
                currency = order.get('currency', 'VND')
                factory_etd = order.get('factory_etd', 'N/A')
                customs_eta = order.get('customs_eta', 'N/A')
                ymv_eta = order.get('ymv_eta', 'N/A')
                
                with st.container():
                    # 첫 번째 줄
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        st.markdown(f"**🆔 {order_id}**")
                    with col2:
                        st.markdown(f"**💰 {total_amount:,.0f} {currency}**")
                    with col3:
                        st.markdown(f"**📅 공급출고:** {factory_etd}")
                    with col4:
                        # 수정 및 삭제 버튼
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=f"edit_{order_id}", help="수정"):
                                st.session_state[f"show_edit_{order_id}"] = True
                                st.rerun()
                        with col_delete:
                            selected = st.checkbox("선택", key=f"select_{order_id}", help="선택", label_visibility="collapsed")
                            if selected:
                                if st.button("🗑️", key=f"delete_{order_id}", help="삭제", type="secondary"):
                                    if order_manager.delete_order(order_id):
                                        st.success(f"주문 {order_id} 삭제 완료")
                                        st.rerun()
                                    else:
                                        st.error("삭제 실패")
                    
                    # 두 번째 줄
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        st.markdown(f"**👤 {customer_company}**")
                    with col2:
                        # 주문 상태 표시
                        order_status = order.get('order_status', 'pending')
                        status_icon = {
                            'pending': '⏳', 'confirmed': '✅', 'in_production': '🏭',
                            'shipped': '🚚', 'delivered': '📦', 'cancelled': '❌'
                        }.get(order_status, '❓')
                        st.markdown(f"**{status_icon} {order_status.upper()}**")
                    with col3:
                        st.markdown(f"**🏪 세관입고:** {customs_eta}")
                    with col4:
                        st.markdown(f"**📦 배송일:** {ymv_eta}")
                    
                    # 세 번째 줄 - 비고 표시 (있는 경우)
                    remarks = order.get('remarks', '')
                    if remarks:
                        col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📝 비고:** {remarks}")
                        with col2:
                            pass
                        with col3:
                            pass
                        with col4:
                            pass
                    
                    # 주문 수정 폼
                    if st.session_state.get(f"show_edit_{order_id}", False):
                        with st.expander(f"주문 수정: {order_id}", expanded=True):
                            show_order_edit_form(order_manager, order, order_id)
                    
                    st.divider()
                    

            
            current_page = page if total_pages > 1 else 1
            st.info(f"총 {len(orders)}개의 주문이 있습니다. (페이지 {current_page}/{total_pages})")
        else:
            st.info("조건에 맞는 주문이 없습니다.")
            
    except Exception as e:
        st.error(f"주문 목록 로드 중 오류: {str(e)}")

def show_order_management_with_edit_delete(order_manager, order):
    """주문 관리 (수정/삭제 포함)"""
    order_id = order['order_id']
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # 상태 변경
    with col1:
        current_status = order.get('order_status', 'pending')
        status_options = ["pending", "confirmed", "in_production", "shipped", "delivered", "cancelled"]
        current_index = status_options.index(current_status) if current_status in status_options else 0
        
        new_status = st.selectbox("상태", 
                                status_options,
                                index=current_index,
                                key=f"status_{order_id}")
        if st.button("상태 변경", key=f"update_status_{order_id}"):
            if order_manager.update_order_status(order_id, new_status, "system"):
                st.success("상태가 업데이트되었습니다.")
                st.rerun()
    
    # 결제 상태 변경
    with col2:
        current_payment = order.get('payment_status', 'pending')
        payment_options = ["pending", "partial", "paid", "overdue"]
        payment_index = payment_options.index(current_payment) if current_payment in payment_options else 0
        
        payment_status = st.selectbox("결제상태", 
                                    payment_options,
                                    index=payment_index,
                                    key=f"payment_{order_id}")
        if st.button("결제 변경", key=f"update_payment_{order_id}"):
            if order_manager.update_payment_status(order_id, payment_status, "system"):
                st.success("결제상태가 업데이트되었습니다.")
                st.rerun()
    
    # 배송일 변경
    with col3:
        delivery_date = st.date_input("배송일", key=f"delivery_{order_id}")
        if st.button("배송일 설정", key=f"set_delivery_{order_id}"):
            if order_manager.update_delivery_date(order_id, delivery_date.strftime('%Y-%m-%d'), "system"):
                st.success("배송일이 설정되었습니다.")
                st.rerun()
    
    # 주문 수정
    with col4:
        if st.button("수정", key=f"edit_{order_id}"):
            show_order_edit_form(order_manager, order)
    
    # 주문 상세보기
    with col5:
        if st.button("상세보기", key=f"detail_{order_id}"):
            show_order_details(order_manager, order_id)
    
    # 주문 삭제
    with col6:
        if st.button("🗑️", key=f"delete_{order_id}", help="주문 삭제"):
            if st.session_state.get(f"confirm_delete_{order_id}", False):
                if order_manager.delete_order(order_id):
                    st.success("주문이 삭제되었습니다.")
                    st.rerun()
                else:
                    st.error("주문 삭제에 실패했습니다.")
            else:
                st.session_state[f"confirm_delete_{order_id}"] = True
                st.rerun()

def show_order_edit_form(order_manager, order):
    """주문 수정 폼"""
    st.subheader(f"주문 수정: {order['order_id']}")
    
    with st.form(f"edit_order_form_{order['order_id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("고객명", value=order.get('customer_name', ''))
            order_date = st.date_input("주문일", 
                                     value=pd.to_datetime(order.get('order_date', '')).date() if order.get('order_date') else datetime.now().date())
            total_amount = st.number_input("총액", value=float(order.get('total_amount', 0)))
            
        with col2:
            currency = st.selectbox("통화", ["VND", "USD", "KRW"], 
                                  index=["VND", "USD", "KRW"].index(order.get('currency', 'VND')))
            payment_terms = st.text_input("결제 조건", value=order.get('payment_terms', ''))
            special_instructions = st.text_area("특별 지시사항", value=order.get('special_instructions', ''))
        
        submitted = st.form_submit_button("수정 완료")
        
        if submitted:
            update_data = {
                'customer_name': customer_name,
                'order_date': order_date.strftime('%Y-%m-%d'),
                'total_amount': total_amount,
                'currency': currency,
                'payment_terms': payment_terms,
                'special_instructions': special_instructions
            }
            
            if order_manager.update_order(order['order_id'], update_data):
                st.success("주문이 성공적으로 수정되었습니다.")
                st.rerun()
            else:
                st.error("주문 수정에 실패했습니다.")

def show_order_management(order_manager, order_id):
    """주문 상세 관리"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # 상태 변경
    with col1:
        new_status = st.selectbox("상태 변경", 
                                ["pending", "confirmed", "in_production", "shipped", "delivered", "cancelled"],
                                key=f"status_{order_id}")
        if st.button("상태 업데이트", key=f"update_status_{order_id}"):
            if order_manager.update_order_status(order_id, new_status, "system"):
                st.success("상태가 업데이트되었습니다.")
                st.rerun()
    
    # 결제 상태 변경
    with col2:
        payment_status = st.selectbox("결제상태", 
                                    ["pending", "partial", "paid", "overdue"],
                                    key=f"payment_{order_id}")
        if st.button("결제상태 업데이트", key=f"update_payment_{order_id}"):
            if order_manager.update_payment_status(order_id, payment_status, "system"):
                st.success("결제상태가 업데이트되었습니다.")
                st.rerun()
    
    # 배송일 설정
    with col3:
        delivery_date = st.date_input("확정 배송일", key=f"delivery_{order_id}")
        if st.button("배송일 설정", key=f"set_delivery_{order_id}"):
            if order_manager.update_delivery_date(order_id, delivery_date.strftime('%Y-%m-%d'), "system"):
                st.success("배송일이 설정되었습니다.")
                st.rerun()
    
    # 주문 상세 정보
    with col4:
        if st.button("상세 정보", key=f"detail_{order_id}"):
            st.session_state[f"show_detail_{order_id}"] = True
    
    # 주문 삭제
    with col5:
        if st.button("🗑️ 삭제", key=f"delete_{order_id}", type="secondary"):
            st.session_state[f"confirm_delete_{order_id}"] = True
        
        # 삭제 확인 대화상자
        if st.session_state.get(f"confirm_delete_{order_id}"):
            st.error("⚠️ 주문을 삭제하시겠습니까?")
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                if st.button("✅ 삭제", key=f"confirm_yes_{order_id}"):
                    if order_manager.delete_order(order_id):
                        st.success("주문이 삭제되었습니다.")
                        del st.session_state[f"confirm_delete_{order_id}"]
                        st.rerun()
                    else:
                        st.error("주문 삭제에 실패했습니다.")
            
            with col_no:
                if st.button("❌ 취소", key=f"confirm_no_{order_id}"):
                    del st.session_state[f"confirm_delete_{order_id}"]
                    st.rerun()
    
    # 상세 정보 표시
    if st.session_state.get(f"show_detail_{order_id}"):
        show_order_details(order_manager, order_id)

def show_order_details(order_manager, order_id):
    """주문 상세 정보 표시"""
    order = order_manager.get_order_by_id(order_id)
    order_items = order_manager.get_order_items(order_id)
    order_history = order_manager.get_order_history(order_id)
    
    if order:
        st.markdown("---")
        st.subheader(f"주문 상세: {order_id}")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**기본 정보**")
            st.write(f"주문 ID: {order['order_id']}")
            st.write(f"견적서 ID: {order.get('quotation_id', 'N/A')}")
            st.write(f"고객: {order['customer_name']}")
            st.write(f"주문일: {order['order_date']}")
            st.write(f"요청 배송일: {order.get('requested_delivery_date', 'N/A')}")
            st.write(f"확정 배송일: {order.get('confirmed_delivery_date', 'N/A')}")
        
        with col2:
            st.markdown("**상태 정보**")
            st.write(f"주문 상태: {order['order_status']}")
            st.write(f"결제 상태: {order['payment_status']}")
            st.write(f"총액: {order['total_amount']:,.0f} {order['currency']}")
            st.write(f"결제 조건: {order.get('payment_terms', 'N/A')}")
            st.write(f"생성자: {order['created_by']}")
            st.write(f"최종 수정: {order['last_updated']}")
        
        # 주문 상품 목록
        if order_items:
            st.markdown("**주문 상품**")
            items_df = pd.DataFrame(order_items)
            st.dataframe(items_df[['product_code', 'product_name', 'quantity', 'unit_price', 'total_price', 'currency']], 
                        use_container_width=True)
        
        # 상태 변경 이력
        if order_history:
            st.markdown("**상태 변경 이력**")
            history_df = pd.DataFrame(order_history)
            st.dataframe(history_df[['changed_date', 'previous_status', 'new_status', 'changed_by', 'notes']], 
                        use_container_width=True)
        
        if st.button("닫기", key=f"close_detail_{order_id}"):
            st.session_state[f"show_detail_{order_id}"] = False
            st.rerun()

def show_order_creation(order_manager, quotation_manager, customer_manager, current_user_id, get_text):
    """듀얼 모드 주문 생성"""
    st.subheader(f"➕ {get_text('order_creation')}")
    
    # 모드 선택
    order_mode = st.radio(
        "주문 모드 선택:",
        ["판매재고 모드 (견적서 기반)", "재고 모드 (제품 코드 기반)"],
        key="order_mode_selector"
    )
    
    # 공급사 데이터 로드
    from managers.sqlite.sqlite_supplier_manager import SQLiteSupplierManager
    supplier_manager = SQLiteSupplierManager()
    suppliers_df = supplier_manager.get_all_suppliers()
    
    if order_mode == "판매재고 모드 (견적서 기반)":
        show_sales_inventory_order_form(quotation_manager, order_manager, suppliers_df, current_user_id)
    else:
        show_inventory_order_form(order_manager, suppliers_df, current_user_id)

def show_sales_inventory_order_form(quotation_manager, order_manager, suppliers_df, current_user_id):
    """판매재고 모드 주문 생성 폼"""
    # Form 밖에서 먼저 데이터 준비
    quotations_df = quotation_manager.get_all_quotations()
    if quotations_df is None or (hasattr(quotations_df, 'empty') and quotations_df.empty):
        st.warning("견적서가 없습니다. 먼저 견적서를 생성해주세요.")
        return
        
    # DataFrame을 딕셔너리 리스트로 변환
    if hasattr(quotations_df, 'to_dict'):
        quotations_list = quotations_df.to_dict('records')
    else:
        quotations_list = quotations_df if isinstance(quotations_df, list) else []
    
    # 이미 주문이 생성된 견적서 필터링
    existing_orders = order_manager.get_all_orders()
    used_quotation_ids = set()
    
    # DataFrame 또는 리스트 안전하게 확인
    has_orders = False
    if existing_orders is not None:
        if hasattr(existing_orders, 'empty'):
            has_orders = not existing_orders.empty
        elif isinstance(existing_orders, list):
            has_orders = len(existing_orders) > 0
    
    if has_orders:
        if hasattr(existing_orders, 'to_dict'):
            orders_list = existing_orders.to_dict('records')
        else:
            orders_list = existing_orders if isinstance(existing_orders, list) else []
        
        for order in orders_list:
            if order.get('quotation_id'):
                used_quotation_ids.add(order['quotation_id'])
    
    # 주문이 없는 견적서만 필터링
    available_quotations = [q for q in quotations_list 
                          if isinstance(q, dict) and q.get('quotation_id') not in used_quotation_ids]
    
    quotation_options = [f"{row['quotation_number']} - {row['customer_company']}" 
                       for row in available_quotations]
    
    if not quotation_options:
        st.warning("주문 가능한 견적서가 없습니다. 모든 견적서가 이미 주문으로 변환되었거나 견적서가 없습니다.")
        return
    
    with st.form("sales_inventory_order_form"):
        st.subheader("📄 견적서 정보")
        
        selected_quotation = st.selectbox("견적서 번호", ["선택하세요"] + quotation_options, key="quotation_select")
        
        if selected_quotation == "선택하세요":
            selected_quotation_data = None
        else:
            quotation_number = selected_quotation.split(" - ")[0]
            selected_quotation_data = next((q for q in available_quotations if q['quotation_number'] == quotation_number), None)
        
        if not selected_quotation_data and selected_quotation != "선택하세요":
            st.error("선택한 견적서 데이터를 찾을 수 없습니다.")
            selected_quotation_data = None
        
        # 견적서 정보 표시
        if selected_quotation_data:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**고객:** {selected_quotation_data.get('customer_company', 'N/A')}")
                # 총액 필드명 수정 - total_incl_vat 사용
                total_amount = selected_quotation_data.get('total_incl_vat', selected_quotation_data.get('total_amount', 0))
                st.info(f"**총액:** {total_amount:,.0f} {selected_quotation_data.get('currency', 'VND')}")
            with col2:
                st.info(f"**프로젝트:** {selected_quotation_data.get('project_name', 'N/A')}")
                st.info(f"**납기:** {selected_quotation_data.get('delivery_date', 'N/A')}")
        else:
            st.warning("견적서를 선택하세요.")
        
        st.subheader("👤 영업 담당자 정보")
        
        col1, col2, col3 = st.columns(3)
        
        # 직원 데이터 가져오기
        from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
        employee_manager = SQLiteEmployeeManager()
        employees_df = employee_manager.get_all_employees()
        
        # 직원 정보 변수 초기화
        sales_rep = ""
        sales_contact = ""
        sales_phone = ""
        
        with col1:
            if not employees_df.empty:
                employee_names = ["선택하세요"] + employees_df['name'].tolist()
                selected_employee = st.selectbox("영업 담당자", employee_names, key="sales_rep_select")
                
                if selected_employee != "선택하세요":
                    employee_info = employees_df[employees_df['name'] == selected_employee].iloc[0]
                    sales_rep = employee_info['name']
                    sales_contact = employee_info['email']
                    sales_phone = employee_info['phone']
            else:
                sales_rep = st.text_input("영업 담당자", key="sales_rep_manual", value="")
                
        with col2:
            if not employees_df.empty and 'selected_employee' in locals() and selected_employee != "선택하세요":
                st.text_input("Contact (E-mail)", value=sales_contact, disabled=True, key="sales_contact_display")
            else:
                sales_contact = st.text_input("Contact (E-mail)", key="sales_contact_manual", value=sales_contact)
        
        with col3:
            if not employees_df.empty and 'selected_employee' in locals() and selected_employee != "선택하세요":
                st.text_input("Phone", value=sales_phone, disabled=True, key="sales_phone_display")
            else:
                sales_phone = st.text_input("Phone", key="sales_phone_manual", value=sales_phone)

        st.subheader("🏭 공급 및 물류 정보")
        
        # 2번째 줄: 공급처, 운송수단, 물류 일정 선택
        st.write("**공급 및 운송 정보**")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            # 공급처 선택 (판매재고 모드)
            if suppliers_df is None or (hasattr(suppliers_df, 'empty') and suppliers_df.empty):
                supplier_name = st.text_input("공급처", placeholder="직접 입력", key="sales_supplier")
            else:
                supplier_options = ["선택하세요"] + suppliers_df['company_name'].tolist()
                selected_supplier = st.selectbox("공급처", supplier_options, key="sales_supplier_select")
                supplier_name = selected_supplier if selected_supplier != "선택하세요" else ""
        
        with col2:
            transport_method = st.selectbox("운송수단", ["AIR", "ROAD", "SEA"], key="sales_transport")
            
        with col3:
            factory_etd = st.date_input("공장 출고일", key="sales_factory_etd")
            
        with col4:
            logistics_etd = st.date_input("물류 출고일", key="sales_logistics_etd")
            
        with col5:
            customs_eta = st.date_input("세관 입고일", key="sales_customs_eta")
            
        with col6:
            ymv_eta = st.date_input("배송일", key="sales_delivery_date")
        
        # 3번째 줄: 배송 일정
        st.write("**배송 정보**")
        delivery_target = st.radio("배송 대상", ["고객 직배송", "YMV 입고"], horizontal=True)
        
        customer_delivery_date = None
        if delivery_target == "고객 직배송":
            customer_delivery_date = st.date_input("고객 배송일 (필수)")
        else:
            customer_delivery_date = st.date_input("고객 배송일 (선택)", value=None)
        
        remarks = st.text_area("비고 (최대 100자)", max_chars=100)
        
        # 필수 조건 검사 (판매재고 모드)
        can_submit = bool(selected_quotation_data and supplier_name)
        submitted = st.form_submit_button("주문 생성")
        
        if submitted:
            # 추가 검증
            if not selected_quotation_data:
                st.error("견적서를 선택해주세요.")
                st.rerun()
                
            if not supplier_name:
                st.error("공급처를 선택하거나 입력해주세요.")
                st.rerun()
            
            if delivery_target == "고객 직배송" and not customer_delivery_date:
                st.error("고객 직배송 선택 시 고객 배송일은 필수입니다.")
                return
            
            # 날짜 유효성 검사
            dates = [factory_etd, logistics_etd, customs_eta, ymv_eta]
            if customer_delivery_date:
                dates.append(customer_delivery_date)
                
            for i in range(len(dates) - 1):
                if dates[i] > dates[i + 1]:
                    st.error(f"날짜 순서가 올바르지 않습니다: {dates[i]} > {dates[i + 1]}")
                    return
            
            # 주문 생성 데이터 준비
            order_data = {
                'mode': 'sales_inventory',
                'quotation_data': selected_quotation_data,
                'supplier_name': supplier_name,
                'factory_etd': factory_etd.strftime('%Y-%m-%d'),
                'logistics_etd': logistics_etd.strftime('%Y-%m-%d'),
                'transport_method': transport_method,
                'customs_eta': customs_eta.strftime('%Y-%m-%d'),
                'delivery_target': delivery_target,
                'customer_delivery_date': customer_delivery_date.strftime('%Y-%m-%d') if customer_delivery_date else None,
                'remarks': remarks,
                'created_by': current_user_id,
                'sales_rep': sales_rep,
                'sales_contact': sales_contact,
                'sales_phone': sales_phone
            }
            
            # 주문 생성 실행
            try:
                order_id = order_manager.create_dual_mode_order(order_data)
                
                if order_id:
                    st.success(f"판매재고 주문이 성공적으로 생성되었습니다! 주문 ID: {order_id}")
                    # 폼 상태 초기화
                    for key in st.session_state.keys():
                        if key.startswith(('quotation_select', 'sales_supplier', 'sales_transport', 
                                         'sales_factory_etd', 'sales_logistics_etd', 'sales_customs_eta', 
                                         'sales_delivery_date')):
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("주문 생성에 실패했습니다.")
            except Exception as e:
                st.error(f"주문 생성 중 오류 발생: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

def show_inventory_order_form(order_manager, suppliers_df, current_user_id):
    """재고 모드 주문 생성 폼"""
    with st.form("inventory_order_form"):
        st.subheader("📦 제품 정보")
        
        # 제품 코드 선택 - DB에서 로드
        from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
        master_product_manager = SQLiteMasterProductManager()
        products_df = master_product_manager.get_all_products()
        
        if products_df is not None and not products_df.empty:
            # DB에서 제품 로드
            product_options = [f"{row['product_code']} - {row['product_name']}" 
                              for _, row in products_df.iterrows()]
            selected_product = st.selectbox("제품 코드", ["선택하세요"] + product_options)
            
            if selected_product == "선택하세요":
                selected_product_data = None
            else:
                product_code = selected_product.split(" - ")[0]
                selected_product_data = products_df[products_df['product_code'] == product_code].iloc[0].to_dict()
        else:
            # DB가 비어있으면 수동 입력
            st.info("제품 데이터베이스가 비어있습니다. 수동 입력을 사용합니다.")
            
            product_code = st.text_input("제품 코드")
            product_name = st.text_input("제품명")
            import_price = st.number_input("수입가격", min_value=0.0, value=100.0)
            import_currency = st.selectbox("수입 통화", ["USD", "KRW", "VND"])
            
            if not product_code or not product_name:
                selected_product_data = None
            else:
                selected_product_data = {
                    'product_code': product_code,
                    'product_name': product_name,
                    'supply_price': import_price,
                    'supply_currency': import_currency
                }
        

        
        # 제품 정보 표시
        if selected_product_data:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**제품명:** {selected_product_data['product_name']}")
            with col2:
                # DB 필드명 사용
                supply_price = selected_product_data.get('supply_price', 0)
                supply_currency = selected_product_data.get('supply_currency', 'USD')
                st.info(f"**공급가격:** {supply_price:,.2f} {supply_currency}")
        else:
            st.warning("제품을 선택하세요.")
        
        st.subheader("👤 영업 담당자 정보")
        
        col1, col2, col3 = st.columns(3)
        
        # 직원 데이터 가져오기
        from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
        employee_manager = SQLiteEmployeeManager()
        employees_df = employee_manager.get_all_employees()
        
        # 직원 정보 변수 초기화
        sales_rep = ""
        sales_contact = ""
        sales_phone = ""
        
        with col1:
            if not employees_df.empty:
                employee_names = ["선택하세요"] + employees_df['name'].tolist()
                selected_employee = st.selectbox("영업 담당자", employee_names, key="inv_sales_rep_select")
                
                if selected_employee != "선택하세요":
                    employee_info = employees_df[employees_df['name'] == selected_employee].iloc[0]
                    sales_rep = employee_info['name']
                    sales_contact = employee_info['email']
                    sales_phone = employee_info['phone']
            else:
                sales_rep = st.text_input("영업 담당자", key="inv_sales_rep_manual", value="")
                
        with col2:
            if not employees_df.empty and 'selected_employee' in locals() and selected_employee != "선택하세요":
                st.text_input("Contact (E-mail)", value=sales_contact, disabled=True, key="inv_sales_contact_display")
            else:
                sales_contact = st.text_input("Contact (E-mail)", key="inv_sales_contact_manual", value=sales_contact)
        
        with col3:
            if not employees_df.empty and 'selected_employee' in locals() and selected_employee != "선택하세요":
                st.text_input("Phone", value=sales_phone, disabled=True, key="inv_sales_phone_display")
            else:
                sales_phone = st.text_input("Phone", key="inv_sales_phone_manual", value=sales_phone)

        st.subheader("🏭 공급 및 물류 정보")
        
        # 2번째 줄: 공급처, 운송수단, 물류 일정 선택
        st.write("**공급 및 운송 정보**")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            # 공급처 선택 (재고 모드)
            if suppliers_df is None or (hasattr(suppliers_df, 'empty') and suppliers_df.empty):
                supplier_name = st.text_input("공급처", placeholder="직접 입력", key="inv_supplier")
            else:
                supplier_options = ["선택하세요"] + suppliers_df['company_name'].tolist()
                selected_supplier = st.selectbox("공급처", supplier_options, key="inv_supplier_select")
                supplier_name = selected_supplier if selected_supplier != "선택하세요" else ""
        
        with col2:
            transport_method = st.selectbox("운송수단", ["AIR", "ROAD", "SEA"], key="inv_transport")
            
        with col3:
            factory_etd = st.date_input("공장 출고일", key="inv_factory_etd")
            
        with col4:
            logistics_etd = st.date_input("물류 출고일", key="inv_logistics_etd")
            
        with col5:
            customs_eta = st.date_input("세관 입고일", key="inv_customs_eta")
            
        with col6:
            ymv_eta = st.date_input("YMV 입고일", key="inv_ymv_eta")
        
        # 3번째 줄: 날짜 선택 (배송 관련)
        st.write("**배송 일정**")
        delivery_target = st.radio("배송 대상", ["고객 직배송", "YMV 입고"], horizontal=True)
        
        customer_delivery_date = None
        if delivery_target == "고객 직배송":
            customer_delivery_date = st.date_input("고객 배송일 (필수)")
        else:
            customer_delivery_date = st.date_input("고객 배송일 (선택)", value=None)
        
        remarks = st.text_area("비고 (최대 100자)", max_chars=100)
        
        # 필수 조건 검사 (재고 모드)
        can_submit = bool(selected_product_data and supplier_name)
        submitted = st.form_submit_button("주문 생성")
        
        if submitted:
            # 추가 검증
            if not selected_product_data:
                st.error("제품을 선택해주세요.")
                st.rerun()
                
            if not supplier_name:
                st.error("공급처를 선택하거나 입력해주세요.")
                st.rerun()
            
            # 날짜 유효성 검사
            dates = [factory_etd, logistics_etd, customs_eta, ymv_eta]
            for i in range(len(dates) - 1):
                if dates[i] > dates[i + 1]:
                    st.error(f"날짜 순서가 올바르지 않습니다: {dates[i]} > {dates[i + 1]}")
                    return
            
            # 주문 생성 - product_data 처리 및 디버깅
            try:
                product_data = selected_product_data if isinstance(selected_product_data, dict) else selected_product_data.to_dict()
                st.write("DEBUG - product_data:", product_data)  # 디버깅용
                
                order_data = {
                    'mode': 'inventory',
                    'product_data': product_data,
                    'supplier_name': supplier_name,
                    'factory_etd': factory_etd.strftime('%Y-%m-%d'),
                    'logistics_etd': logistics_etd.strftime('%Y-%m-%d'),
                    'transport_method': transport_method,
                    'customs_eta': customs_eta.strftime('%Y-%m-%d'),
                    'ymv_eta': ymv_eta.strftime('%Y-%m-%d'),
                    'delivery_target': delivery_target,
                    'customer_delivery_date': customer_delivery_date.strftime('%Y-%m-%d') if customer_delivery_date else None,
                    'remarks': remarks,
                    'created_by': current_user_id,
                    'sales_rep': sales_rep,
                    'sales_contact': sales_contact,
                    'sales_phone': sales_phone
                }
                st.write("DEBUG - order_data:", order_data)  # 디버깅용
                
                order_id = order_manager.create_dual_mode_order(order_data)
                st.write("DEBUG - order_id result:", order_id)  # 디버깅용
                
            except Exception as e:
                st.error(f"주문 생성 중 오류 발생: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                return
            
            if order_id:
                st.success(f"재고 주문이 성공적으로 생성되었습니다! 주문 ID: {order_id}")
                # 폼 상태 초기화
                for key in st.session_state.keys():
                    if key.startswith(('inventory_supplier', 'inventory_transport', 
                                     'inventory_factory_etd', 'inventory_logistics_etd', 
                                     'inventory_customs_eta', 'inventory_delivery_date')):
                        del st.session_state[key]
                st.rerun()
            else:
                st.error("주문 생성에 실패했습니다.")

def show_order_statistics(order_manager, get_text):
    """주문 통계 표시 - 실제 데이터 기반"""
    st.subheader(f"📊 {get_text('order_statistics_title')}")
    
    try:
        # 실제 주문 데이터 가져오기
        all_orders = order_manager.get_all_orders()
        
        if all_orders is None or (hasattr(all_orders, 'empty') and all_orders.empty) or (isinstance(all_orders, list) and len(all_orders) == 0):
            st.info(get_text("no_order_data"))
            return
        
        # DataFrame으로 변환
        orders_df = pd.DataFrame(all_orders)
        
        # 기본 통계 계산
        total_orders = len(orders_df)
        pending_orders = len(orders_df[orders_df['order_status'].isin(['pending', 'confirmed', 'in_production'])])
        completed_orders = len(orders_df[orders_df['order_status'].isin(['delivered'])])
        
        # 총 금액 계산 (숫자형으로 변환)
        orders_df['total_amount_num'] = pd.to_numeric(orders_df['total_amount'], errors='coerce')
        total_amount = orders_df['total_amount_num'].sum()
        
        # 메트릭 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(get_text('total_orders'), total_orders)
        
        with col2:
            st.metric(get_text('pending_orders'), pending_orders)
        
        with col3:
            st.metric(get_text('completed_orders'), completed_orders)
        
        with col4:
            if total_amount > 0:
                st.metric(get_text('total_amount'), f"{total_amount:,.0f} VND")
            else:
                st.metric(get_text('total_amount'), "0 VND")
        
        # 차트 섹션
        col1, col2 = st.columns(2)
        
        with col1:
            # 실제 상태별 분포
            status_counts = orders_df['order_status'].value_counts()
            if len(status_counts) > 0:
                # 상태 라벨 번역 (안전한 get_text 호출)
                status_labels = {}
                try:
                    status_labels = {
                        'confirmed': get_text('status_confirmed') if callable(get_text) else 'Confirmed',
                        'pending': get_text('status_pending') if callable(get_text) else 'Pending', 
                        'in_production': get_text('status_in_production') if callable(get_text) else 'In Production',
                        'shipped': get_text('status_shipped') if callable(get_text) else 'Shipped',
                        'delivered': get_text('status_delivered') if callable(get_text) else 'Delivered',
                        'cancelled': get_text('status_cancelled') if callable(get_text) else 'Cancelled'
                    }
                except Exception:
                    status_labels = {
                        'confirmed': 'Confirmed',
                        'pending': 'Pending', 
                        'in_production': 'In Production',
                        'shipped': 'Shipped',
                        'delivered': 'Delivered',
                        'cancelled': 'Cancelled'
                    }
                
                # 번역된 라벨로 변경
                translated_labels = [status_labels.get(status, status) for status in status_counts.index]
                
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=translated_labels,
                    title=get_text('order_status_breakdown')
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info(get_text("no_status_data"))
        
        with col2:
            # 실제 월별 트렌드 (order_date 기준)
            if 'order_date' in orders_df.columns:
                try:
                    # 날짜 변환
                    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'], errors='coerce')
                    orders_df = orders_df.dropna(subset=['order_date'])
                    
                    if len(orders_df) > 0:
                        # 월별 그룹화
                        monthly_counts = orders_df.groupby(orders_df['order_date'].dt.to_period('M')).size()
                        
                        if len(monthly_counts) > 0:
                            fig_trend = px.line(
                                x=monthly_counts.index.astype(str),
                                y=monthly_counts.values,
                                title=get_text('monthly_order_trend'),
                                labels={'x': '월', 'y': get_text('order_count')}
                            )
                            st.plotly_chart(fig_trend, use_container_width=True)
                        else:
                            st.info(get_text("no_trend_data"))
                    else:
                        st.info(get_text("invalid_date_data"))
                except Exception as e:
                    st.warning(f"{get_text('trend_chart_error')}: {str(e)}")
                    st.info(get_text("check_date_format"))
            else:
                st.info(get_text("no_order_date"))
                
    except Exception as e:
        st.error(f"{get_text('order_loading_error')}: {str(e)}")
        st.info(get_text("check_order_data"))

def show_delivery_schedule(order_manager, get_text):
    """배송 일정"""
    st.subheader(f"🚚 {get_text('delivery_schedule')}")
    
    try:
        delivery_orders = order_manager.get_delivery_schedule()
        
        # DataFrame 또는 리스트 안전하게 확인
        has_data = False
        if delivery_orders is not None:
            if isinstance(delivery_orders, list):
                has_data = len(delivery_orders) > 0
            elif hasattr(delivery_orders, 'empty'):
                has_data = not delivery_orders.empty
                if has_data:
                    delivery_orders = delivery_orders.to_dict('records')
        
        if has_data:
            st.markdown(f"### {get_text('delivery_scheduled_orders')}")
            
            for order in delivery_orders:
                with st.expander(f"{order['order_id']} - {order['customer_name']} (배송예정: {order['requested_delivery_date']})", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**{get_text('order_date')}:** {order['order_date']}")
                        st.write(f"**{get_text('total_amount')}:** {order['total_amount']:,.0f} {order['currency']}")
                    
                    with col2:
                        st.write(f"**{get_text('current_status')}:** {order['order_status']}")
                        st.write(f"**{get_text('payment_status')}:** {order['payment_status']}")
                    
                    with col3:
                        # 배송일 업데이트
                        new_delivery_date = st.date_input(get_text('delivery_date_change'), 
                                                        value=pd.to_datetime(order['requested_delivery_date']).date(),
                                                        key=f"delivery_update_{order['order_id']}")
                        if st.button(get_text('delivery_date_update'), key=f"update_delivery_{order['order_id']}"):
                            if order_manager.update_delivery_date(order['order_id'], 
                                                               new_delivery_date.strftime('%Y-%m-%d'), 
                                                               "system"):
                                st.success(get_text('delivery_date_updated'))
                                st.rerun()
            
            # 배송 일정 캘린더 뷰
            st.markdown(f"### {get_text('delivery_calendar')}")
            delivery_df = pd.DataFrame(delivery_orders)
            delivery_df['requested_delivery_date'] = pd.to_datetime(delivery_df['requested_delivery_date'])
            
            # 간단한 일정 표시
            calendar_data = delivery_df.groupby(delivery_df['requested_delivery_date'].dt.date).agg({
                'order_id': 'count',
                'customer_name': lambda x: ', '.join(x[:3]) + ('...' if len(x) > 3 else '')
            }).reset_index()
            
            calendar_data.columns = [get_text('delivery_date'), get_text('order_count'), get_text('customer')]
            st.dataframe(calendar_data, use_container_width=True)
        
        else:
            st.info("배송 예정인 주문이 없습니다.")
    
    except Exception as e:
        st.error(f"배송 일정 로드 중 오류: {str(e)}")

def show_order_analysis(order_manager, get_text):
    """주문 분석"""
    st.subheader(f"📈 {get_text('order_analysis')}")
    
    try:
        orders = order_manager.get_all_orders()
        
        # DataFrame 또는 리스트 안전하게 확인
        has_order_data = False
        if orders is not None:
            if isinstance(orders, list):
                has_order_data = len(orders) > 0
            elif hasattr(orders, 'empty'):
                has_order_data = not orders.empty
                if has_order_data:
                    orders = orders.to_dict('records')
        
        if has_order_data:
            df = pd.DataFrame(orders)
            df['order_date'] = pd.to_datetime(df['order_date'])
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
            
            # 기간별 분석
            st.markdown("### 시간별 주문 분석")
            
            # 일별 주문 추이
            daily_orders = df.groupby(df['order_date'].dt.date).agg({
                'order_id': 'count',
                'total_amount': 'sum'
            }).reset_index()
            daily_orders.columns = ['날짜', '주문건수', '총금액']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(daily_orders, x='날짜', y='주문건수', title="일별 주문 건수")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(daily_orders, x='날짜', y='총금액', title="일별 주문 금액")
                st.plotly_chart(fig, use_container_width=True)
            
            # 고객별 분석
            st.markdown("### 고객별 주문 분석")
            customer_analysis = df.groupby('customer_name').agg({
                'order_id': 'count',
                'total_amount': 'sum'
            }).reset_index().sort_values('total_amount', ascending=False)
            customer_analysis.columns = ['고객명', '주문건수', '총주문금액']
            
            col1, col2 = st.columns(2)
            
            with col1:
                top_customers = customer_analysis.head(10)
                fig = px.bar(top_customers, x='고객명', y='총주문금액', title="상위 10개 고객 (주문금액 기준)")
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**고객별 주문 현황**")
                st.dataframe(customer_analysis.head(10), use_container_width=True)
        
        else:
            st.info("분석할 주문 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"주문 분석 중 오류: {str(e)}")

def show_order_search(order_manager, get_text):
    """주문 검색"""
    st.subheader(f"🔍 {get_text('order_search')}")
    
    # 검색 옵션
    search_type = st.radio("검색 유형", ["주문 ID", "고객명", "견적서 ID", "날짜 범위"])
    
    if search_type == "주문 ID":
        order_id = st.text_input("주문 ID 입력")
        if order_id and st.button("검색"):
            order = order_manager.get_order_by_id(order_id)
            if order:
                show_order_details(order_manager, order_id)
            else:
                st.warning("해당 주문을 찾을 수 없습니다.")
    
    elif search_type == "고객명":
        customer_name = st.text_input("고객명 입력")
        if customer_name and st.button("검색"):
            orders = order_manager.get_filtered_orders(customer_filter=customer_name)
            
            # DataFrame 또는 리스트 안전하게 확인
            has_data = False
            if orders is not None:
                if isinstance(orders, list):
                    has_data = len(orders) > 0
                elif hasattr(orders, 'empty'):
                    has_data = not orders.empty
                    if has_data:
                        orders = orders.to_dict('records')
            
            if has_data:
                st.success(f"{len(orders)}개의 주문을 찾았습니다.")
                display_search_results(orders)
            else:
                st.warning("해당 고객의 주문을 찾을 수 없습니다.")
    
    elif search_type == "견적서 ID":
        quotation_id = st.text_input("견적서 ID 입력")
        if quotation_id and st.button("검색"):
            all_orders = order_manager.get_all_orders()
            matching_orders = [o for o in all_orders if o.get('quotation_id') == quotation_id]
            if matching_orders:
                st.success(f"{len(matching_orders)}개의 주문을 찾았습니다.")
                display_search_results(matching_orders)
            else:
                st.warning("해당 견적서로 생성된 주문을 찾을 수 없습니다.")
    
    elif search_type == "날짜 범위":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일")
        with col2:
            end_date = st.date_input("종료일")
        
        if st.button("검색"):
            orders = order_manager.get_filtered_orders(
                date_from=start_date,
                date_to=end_date
            )
            
            # DataFrame 또는 리스트 안전하게 확인
            has_search_data = False
            if orders is not None:
                if isinstance(orders, list):
                    has_search_data = len(orders) > 0
                elif hasattr(orders, 'empty'):
                    has_search_data = not orders.empty
                    if has_search_data:
                        orders = orders.to_dict('records')
            
            if has_search_data:
                st.success(f"{len(orders)}개의 주문을 찾았습니다.")
                display_search_results(orders)
            else:
                st.warning("해당 기간에 주문이 없습니다.")

def display_search_results(orders):
    """검색 결과 표시"""
    # DataFrame 또는 리스트 안전하게 확인
    has_results = False
    if orders is not None:
        if isinstance(orders, list):
            has_results = len(orders) > 0
        elif hasattr(orders, 'empty'):
            has_results = not orders.empty
            if has_results:
                orders = orders.to_dict('records')
    
    if has_results:
        df = pd.DataFrame(orders)
        display_columns = ['order_id', 'customer_name', 'order_date', 'order_status', 'payment_status', 'total_amount', 'currency']
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            st.dataframe(df[available_columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

def show_order_delete_page(order_manager, get_text):
    """주문 삭제 전용 페이지"""
    st.subheader("🗑️ 주문 삭제")
    
    st.warning("⚠️ 주의: 주문을 삭제하면 복구할 수 없습니다. 신중하게 선택하세요.")
    
    # 삭제할 주문 검색
    search_term = st.text_input("🔍 삭제할 주문 검색 (주문ID 또는 고객명)")
    
    if search_term:
        try:
            # 주문 검색
            all_orders = order_manager.get_all_orders()
            matching_orders = []
            
            for order in all_orders:
                if (search_term.lower() in order.get('order_id', '').lower() or 
                    search_term.lower() in order.get('customer_name', '').lower()):
                    matching_orders.append(order)
            
            if matching_orders:
                st.info(f"검색 결과: {len(matching_orders)}건")
                
                for order in matching_orders:
                    with st.expander(f"주문 {order['order_id']} - {order['customer_name']} ({order['order_status']})"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**주문일:** {order['order_date']}")
                            st.write(f"**고객:** {order['customer_name']}")
                            st.write(f"**총액:** {order['total_amount']:,.0f} {order['currency']}")
                        
                        with col2:
                            st.write(f"**상태:** {order['order_status']}")
                            st.write(f"**결제상태:** {order['payment_status']}")
                            st.write(f"**생성자:** {order['created_by']}")
                        
                        with col3:
                            delete_key = f"delete_confirm_{order['order_id']}"
                            
                            if st.button(f"🗑️ 삭제", key=f"delete_btn_{order['order_id']}", type="secondary"):
                                st.session_state[delete_key] = True
                            
                            # 삭제 확인
                            if st.session_state.get(delete_key):
                                st.error("⚠️ 정말 삭제하시겠습니까?")
                                
                                col_confirm, col_cancel = st.columns(2)
                                with col_confirm:
                                    if st.button("✅ 확인", key=f"confirm_{order['order_id']}"):
                                        if order_manager.delete_order(order['order_id']):
                                            st.success(f"주문 {order['order_id']}이 삭제되었습니다.")
                                            del st.session_state[delete_key]
                                            st.rerun()
                                        else:
                                            st.error("주문 삭제에 실패했습니다.")
                                
                                with col_cancel:
                                    if st.button("❌ 취소", key=f"cancel_{order['order_id']}"):
                                        del st.session_state[delete_key]
                                        st.rerun()
            else:
                st.info("검색 결과가 없습니다.")
                
        except Exception as e:
            st.error(f"주문 검색 중 오류: {str(e)}")
    else:
        st.info("🔍 검색어를 입력하여 삭제할 주문을 찾으세요.")

def show_order_edit_form(order_manager, order, order_id):
    """주문 수정 폼"""
    from datetime import datetime
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 주문 상태 수정
        current_status = order.get('order_status', 'pending')
        status_options = ["pending", "confirmed", "in_production", "shipped", "delivered", "cancelled"]
        status_labels = {
            "pending": "⏳ 대기중", "confirmed": "✅ 확인됨", 
            "in_production": "🏭 생산중", "shipped": "🚚 배송중", 
            "delivered": "📦 배송완료", "cancelled": "❌ 취소됨"
        }
        current_index = status_options.index(current_status) if current_status in status_options else 0
        new_status = st.selectbox("주문 상태", status_options, 
                                index=current_index, key=f"edit_status_{order_id}",
                                format_func=lambda x: status_labels.get(x, x))
    
    with col2:
        # 결제 상태 수정
        current_payment = order.get('payment_status', 'pending')
        payment_options = ["pending", "partial", "paid", "overdue"]
        payment_labels = {
            "pending": "💳 대기중", "partial": "💰 부분결제", 
            "paid": "✅ 완료", "overdue": "⚠️ 연체"
        }
        payment_index = payment_options.index(current_payment) if current_payment in payment_options else 0
        new_payment = st.selectbox("결제 상태", payment_options,
                                 index=payment_index, key=f"edit_payment_{order_id}",
                                 format_func=lambda x: payment_labels.get(x, x))
    
    with col3:
        # 배송일 수정
        try:
            if order.get('ymv_eta'):
                current_delivery = datetime.strptime(order['ymv_eta'], '%Y-%m-%d').date()
            else:
                current_delivery = None
        except:
            current_delivery = None
            
        new_delivery = st.date_input("배송일", value=current_delivery, key=f"edit_delivery_{order_id}")
    
    # 비고 수정
    st.write("**비고**")
    current_remarks = order.get('remarks', '')
    new_remarks = st.text_area("비고 (최대 100자)", value=current_remarks, 
                              max_chars=100, key=f"edit_remarks_{order_id}",
                              help="주문에 대한 특별 사항이나 메모를 입력하세요")
    
    # 물류 일정 수정
    st.write("**물류 일정 수정**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            current_factory = datetime.strptime(order.get('factory_etd', '2025-09-02'), '%Y-%m-%d').date() if order.get('factory_etd') else None
        except:
            current_factory = None
        new_factory_etd = st.date_input("공장 출고일", value=current_factory, key=f"edit_factory_{order_id}")
    
    with col2:
        try:
            current_logistics = datetime.strptime(order.get('logistics_etd', '2025-09-02'), '%Y-%m-%d').date() if order.get('logistics_etd') else None
        except:
            current_logistics = None
        new_logistics_etd = st.date_input("물류 출고일", value=current_logistics, key=f"edit_logistics_{order_id}")
    
    with col3:
        try:
            current_customs = datetime.strptime(order.get('customs_eta', '2025-09-02'), '%Y-%m-%d').date() if order.get('customs_eta') else None
        except:
            current_customs = None
        new_customs_eta = st.date_input("세관 입고일", value=current_customs, key=f"edit_customs_{order_id}")
    
    with col4:
        current_transport = order.get('transport_method', 'AIR')
        new_transport = st.selectbox("운송수단", ["AIR", "ROAD", "SEA"], 
                                   index=["AIR", "ROAD", "SEA"].index(current_transport) if current_transport in ["AIR", "ROAD", "SEA"] else 0,
                                   key=f"edit_transport_{order_id}")
    
    # 저장 및 취소 버튼
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 저장", key=f"save_edit_{order_id}", type="primary"):
            # 업데이트할 데이터 준비
            update_data = {
                'order_status': new_status,
                'payment_status': new_payment,
                'ymv_eta': new_delivery.strftime('%Y-%m-%d') if new_delivery else None,
                'factory_etd': new_factory_etd.strftime('%Y-%m-%d') if new_factory_etd else None,
                'logistics_etd': new_logistics_etd.strftime('%Y-%m-%d') if new_logistics_etd else None,
                'customs_eta': new_customs_eta.strftime('%Y-%m-%d') if new_customs_eta else None,
                'transport_method': new_transport,
                'remarks': new_remarks
            }
            
            try:
                # 주문 업데이트 실행
                success = order_manager.update_order(order_id, update_data)
                if success:
                    st.success("주문이 성공적으로 수정되었습니다!")
                    # 수정 폼 숨기기
                    if f"show_edit_{order_id}" in st.session_state:
                        del st.session_state[f"show_edit_{order_id}"]
                    st.rerun()
                else:
                    st.error("주문 수정에 실패했습니다.")
            except Exception as e:
                st.error(f"수정 중 오류 발생: {str(e)}")
    
    with col_cancel:
        if st.button("❌ 취소", key=f"cancel_edit_{order_id}"):
            # 수정 폼 숨기기
            if f"show_edit_{order_id}" in st.session_state:
                del st.session_state[f"show_edit_{order_id}"]
            st.rerun()