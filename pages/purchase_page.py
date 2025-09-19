"""
구매품 등록 페이지 - 총무 메뉴의 구매품 관리 기능
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from managers.legacy.purchase_order_manager import PurchaseOrderManager as PurchaseManager

def show_purchase_page(get_text):
    """구매품 관리 페이지를 표시"""
    st.title(f"🛒 {get_text('purchase_product_registration')}")
    st.markdown("---")
    
    manager = PurchaseManager()
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📊 {get_text('purchase_overview')}",
        f"➕ {get_text('purchase_registration')}", 
        f"🔍 {get_text('purchase_list')}",
        f"⚙️ {get_text('purchase_management')}"
    ])
    
    with tab1:
        show_purchase_overview(manager, get_text)
    
    with tab2:
        show_purchase_registration(manager, get_text)
    
    with tab3:
        show_purchase_list(manager, get_text)
    
    with tab4:
        show_purchase_management(manager, get_text)

def show_purchase_overview(manager, get_text):
    """구매품 현황 대시보드"""
    st.subheader(f"📊 {get_text('purchase_overview_dashboard')}")
    
    # 통계 조회
    stats = manager.get_statistics()
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"📦 {get_text('total_items')}",
            value=f"{stats['total_items']:,}개"
        )
    
    with col2:
        planned_count = stats['status_stats'].get('planned', 0)
        st.metric(
            label=f"📋 {get_text('planned_purchase')}",
            value=f"{planned_count:,}개"
        )
    
    with col3:
        completed_count = stats['status_stats'].get('completed', 0)
        st.metric(
            label=f"✅ {get_text('completed_purchase')}",
            value=f"{completed_count:,}개"
        )
    
    with col4:
        st.metric(
            label=f"💰 {get_text('total_purchase_amount')}",
            value=f"${stats['total_amount']:,.2f}"
        )
    
    st.markdown("---")
    
    # 상태별 차트
    if stats['status_stats']:
        st.subheader(f"📈 {get_text('purchase_status_distribution')}")
        
        status_labels = {
            'planned': get_text('status_planned'),
            'ordered': get_text('status_ordered'), 
            'delivered': get_text('status_delivered'),
            'completed': get_text('status_completed'),
            'cancelled': get_text('status_cancelled')
        }
        
        chart_data = []
        for status, count in stats['status_stats'].items():
            chart_data.append({
                '상태': status_labels.get(status, status),
                '개수': count
            })
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.bar_chart(df_chart.set_index('상태'))
    
    # 최근 등록된 구매품
    st.subheader("🕐 최근 등록된 구매품")
    recent_items = manager.get_purchase_items()
    
    if not recent_items.empty:
        recent_items_display = recent_items.head(5)[['item_name', 'category', 'quantity', 'unit_price', 'status', 'created_date']]
        recent_items_display.columns = ['구매품명', '카테고리', '수량', '단가($)', '상태', '등록일']
        st.dataframe(recent_items_display, use_container_width=True)
    else:
        st.info("등록된 구매품이 없습니다.")

def show_purchase_registration(manager, get_text):
    """구매품 등록 폼"""
    st.subheader("➕ 새 구매품 등록")
    
    # 폼 리셋 상태 관리
    if 'purchase_form_reset' not in st.session_state:
        st.session_state.purchase_form_reset = False
    
    # 폼 초기값 설정
    if st.session_state.purchase_form_reset:
        # 리셋된 초기값들
        default_item_name = ""
        default_item_name_en = ""
        default_item_name_vi = ""
        default_category_index = 0
        default_unit_index = 0
        default_subcategory = ""
        default_quantity = 1
        default_unit_price = 0.0
        default_description = ""
        default_specifications = ""
        default_currency_index = 0
        default_priority_index = 1  # normal
        default_supplier_name = ""
        default_supplier_contact = ""
        default_purchase_date = datetime.now().date()
        default_delivery_date = datetime.now().date() + timedelta(days=7)
        default_status_index = 0  # planned
        default_requested_by = st.session_state.get('user_name', '')
        default_notes = ""
        
        # 리셋 상태 해제
        st.session_state.purchase_form_reset = False
    else:
        # 일반 초기값들
        default_item_name = ""
        default_item_name_en = ""
        default_item_name_vi = ""
        default_category_index = 0
        default_unit_index = 0
        default_subcategory = ""
        default_quantity = 1
        default_unit_price = 0.0
        default_description = ""
        default_specifications = ""
        default_currency_index = 0
        default_priority_index = 1  # normal
        default_supplier_name = ""
        default_supplier_contact = ""
        default_purchase_date = datetime.now().date()
        default_delivery_date = datetime.now().date() + timedelta(days=7)
        default_status_index = 0  # planned
        default_requested_by = st.session_state.get('user_name', '')
        default_notes = ""
    
    # 폼 리셋 버튼
    col_reset, col_spacer = st.columns([1, 4])
    with col_reset:
        if st.button("🔄 폼 리셋", type="secondary"):
            st.session_state.purchase_form_reset = True
            st.rerun()
    
    with st.form("purchase_registration_form"):
        # 기본 정보
        st.markdown("### 📝 기본 정보")
        col1, col2 = st.columns(2)
        
        categories = [""] + manager.get_categories()
        units = ["EA", "KG", "M", "L", "SET", "BOX"]
        currencies = ["USD", "KRW", "VND", "EUR", "JPY"]
        priorities = ["low", "normal", "high", "urgent"]
        statuses = ["planned", "ordered", "delivered", "completed", "cancelled"]
        
        with col1:
            item_name = st.text_input("구매품명 *", value=default_item_name, placeholder="예: 사무용 의자")
            item_name_en = st.text_input("영문명", value=default_item_name_en, placeholder="예: Office Chair")
            category = st.selectbox("카테고리 *", categories, index=default_category_index)
            unit = st.selectbox("단위", units, index=default_unit_index)
        
        with col2:
            item_name_vi = st.text_input("베트남어명", value=default_item_name_vi, placeholder="예: Ghế văn phòng")
            subcategory = st.text_input("서브카테고리", value=default_subcategory, placeholder="예: 회전의자")
            quantity = st.number_input("수량 *", min_value=1, value=default_quantity, step=1)
            unit_price = st.number_input("단가 ($) *", min_value=0.0, value=default_unit_price, step=0.01)
        
        # 상세 정보
        st.markdown("### 📋 상세 정보")
        col3, col4 = st.columns(2)
        
        with col3:
            description = st.text_area("설명", value=default_description, placeholder="구매품에 대한 자세한 설명")
            specifications = st.text_area("사양", value=default_specifications, placeholder="크기, 색상, 재질 등")
        
        with col4:
            currency = st.selectbox("통화", currencies, index=default_currency_index)
            priority = st.selectbox("우선순위", priorities, index=default_priority_index)
        
        # 공급업체 정보
        st.markdown("### 🏢 공급업체 정보")
        col5, col6 = st.columns(2)
        
        with col5:
            supplier_name = st.text_input("공급업체명", value=default_supplier_name)
            supplier_contact = st.text_input("연락처", value=default_supplier_contact)
        
        with col6:
            purchase_date = st.date_input("구매 예정일", value=default_purchase_date)
            expected_delivery_date = st.date_input("배송 예정일", value=default_delivery_date)
        
        # 추가 정보
        st.markdown("### 📝 추가 정보")
        col7, col8 = st.columns(2)
        
        with col7:
            status = st.selectbox("상태", statuses, index=default_status_index)
            requested_by = st.text_input("요청자", value=default_requested_by)
        
        with col8:
            notes = st.text_area("비고", value=default_notes, placeholder="특별한 요구사항이나 메모")
        
        # 제출 버튼들
        col_submit, col_submit_reset = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("💾 구매품 등록", type="primary", use_container_width=True)
        
        with col_submit_reset:
            submit_and_reset = st.form_submit_button("💾 등록 후 폼 리셋", type="secondary", use_container_width=True)
        
        if submitted or submit_and_reset:
            # 필수 필드 검증
            if not item_name or not category or quantity <= 0 or unit_price < 0:
                st.error("필수 항목을 모두 입력해주세요. (구매품명, 카테고리, 수량, 단가)")
                return
            
            # 구매품 데이터 준비
            item_data = {
                'item_name': item_name,
                'item_name_en': item_name_en,
                'item_name_vi': item_name_vi,
                'category': category,
                'subcategory': subcategory,
                'description': description,
                'specifications': specifications,
                'unit': unit,
                'quantity': quantity,
                'unit_price': unit_price,
                'currency': currency,
                'supplier_name': supplier_name,
                'supplier_contact': supplier_contact,
                'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                'expected_delivery_date': expected_delivery_date.strftime('%Y-%m-%d'),
                'status': status,
                'priority': priority,
                'requested_by': requested_by,
                'notes': notes
            }
            
            # 구매품 등록
            success, message = manager.add_purchase_item(item_data)
            
            if success:
                st.success(f"✅ {message}")
                
                # 등록 후 폼 리셋 버튼이 눌렸다면 폼 리셋
                if submit_and_reset:
                    st.session_state.purchase_form_reset = True
                    st.info("📝 폼이 리셋되었습니다. 새로운 구매품을 등록할 수 있습니다.")
                
                st.rerun()
            else:
                st.error(f"❌ {message}")

def show_purchase_list(manager, get_text):
    """구매품 목록 표시"""
    st.subheader("🔍 구매품 목록")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 검색", placeholder="구매품명, 설명, 공급업체 검색")
    
    with col2:
        category_filter = st.selectbox("카테고리 필터", ["전체"] + manager.get_categories())
    
    with col3:
        status_filter = st.selectbox("상태 필터", [
            "전체", "planned", "ordered", "delivered", "completed", "cancelled"
        ])
    
    # 검색 및 필터링
    if search_term or category_filter != "전체" or status_filter != "전체":
        filtered_items = manager.search_purchase_items(
            search_term=search_term,
            category_filter=category_filter if category_filter != "전체" else "",
            status_filter=status_filter if status_filter != "전체" else ""
        )
    else:
        filtered_items = manager.get_purchase_items()
    
    # 결과 표시
    if not filtered_items.empty:
        st.info(f"📦 총 {len(filtered_items)}개의 구매품이 조회되었습니다.")
        
        # 컬럼 선택 및 표시
        display_columns = [
            'item_name', 'category', 'quantity', 'unit', 'unit_price', 
            'total_price', 'currency', 'supplier_name', 'status', 'created_date'
        ]
        
        # 한글 컬럼명으로 변경
        display_df = filtered_items[display_columns].copy()
        display_df.columns = [
            '구매품명', '카테고리', '수량', '단위', '단가', 
            '총액', '통화', '공급업체', '상태', '등록일'
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        # CSV 다운로드
        csv_buffer = io.StringIO()
        display_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv_buffer.getvalue().encode('utf-8-sig'),
            file_name=f"purchase_items_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("조건에 맞는 구매품이 없습니다.")

def show_purchase_management(manager, get_text):
    """구매품 편집 및 삭제"""
    st.subheader("⚙️ 구매품 관리")
    
    # 관리할 구매품 선택
    items = manager.get_purchase_items()
    
    if not items.empty:
        # 구매품 선택
        item_options = []
        for _, item in items.iterrows():
            option = f"{item['item_id']} - {item['item_name']} ({item['category']})"
            item_options.append(option)
        
        selected_item = st.selectbox(
            "관리할 구매품을 선택하세요:",
            options=["선택하세요..."] + item_options
        )
        
        if selected_item and selected_item != "선택하세요...":
            item_id = selected_item.split(" - ")[0]
            item_data = items[items['item_id'] == item_id].iloc[0]
            
            # 편집/삭제 탭
            edit_tab, delete_tab = st.tabs(["✏️ 편집", "🗑️ 삭제"])
            
            with edit_tab:
                show_purchase_edit(manager, item_id, item_data, get_text)
            
            with delete_tab:
                show_purchase_delete(manager, item_id, item_data, get_text)
    else:
        st.info("관리할 구매품이 없습니다.")

def show_purchase_edit(manager, item_id, item_data, get_text):
    """구매품 편집 폼"""
    st.subheader(f"✏️ 구매품 편집: {item_data['item_name']}")
    
    with st.form("purchase_edit_form"):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("구매품명", value=item_data.get('item_name', ''))
            category = st.selectbox("카테고리", manager.get_categories(), 
                                  index=manager.get_categories().index(item_data.get('category', '')) 
                                  if item_data.get('category', '') in manager.get_categories() else 0)
            quantity = st.number_input("수량", min_value=1, value=int(item_data.get('quantity', 1)))
        
        with col2:
            description = st.text_area("설명", value=item_data.get('description', ''))
            unit_price = st.number_input("단가 ($)", min_value=0.0, value=float(item_data.get('unit_price', 0)))
            status = st.selectbox("상태", 
                                ["planned", "ordered", "delivered", "completed", "cancelled"],
                                index=["planned", "ordered", "delivered", "completed", "cancelled"].index(item_data.get('status', 'planned')))
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("💾 수정 저장", type="primary", use_container_width=True)
        
        with col_cancel:
            cancelled = st.form_submit_button("❌ 수정 취소", type="secondary", use_container_width=True)
        
        if submitted:
            updated_data = {
                'item_name': item_name,
                'category': category,
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                'status': status
            }
            
            success, message = manager.update_purchase_item(item_id, updated_data)
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")
        
        elif cancelled:
            st.info("🔄 수정이 취소되었습니다.")
            st.rerun()

def show_purchase_delete(manager, item_id, item_data, get_text):
    """구매품 삭제"""
    st.subheader(f"🗑️ 구매품 삭제: {item_data['item_name']}")
    
    st.warning("⚠️ 삭제하려는 구매품 정보:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text(f"ID: {item_data.get('item_id', 'N/A')}")
        st.text(f"구매품명: {item_data.get('item_name', 'N/A')}")
        st.text(f"카테고리: {item_data.get('category', 'N/A')}")
    
    with col2:
        st.text(f"수량: {item_data.get('quantity', 'N/A')} {item_data.get('unit', '')}")
        st.text(f"단가: ${item_data.get('unit_price', 'N/A')}")
        st.text(f"상태: {item_data.get('status', 'N/A')}")
    
    # 삭제 확인
    if 'delete_purchase_confirm' not in st.session_state:
        st.session_state.delete_purchase_confirm = False
    
    if not st.session_state.delete_purchase_confirm:
        if st.button("🗑️ 삭제하기", type="secondary"):
            st.session_state.delete_purchase_confirm = True
            st.rerun()
    else:
        st.error("⚠️ 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다!")
        
        col_yes, col_no = st.columns(2)
        
        with col_yes:
            if st.button("✅ 확인", type="primary"):
                success, message = manager.delete_purchase_item(item_id)
                
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.delete_purchase_confirm = False
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    st.session_state.delete_purchase_confirm = False
        
        with col_no:
            if st.button("❌ 취소"):
                st.session_state.delete_purchase_confirm = False
                st.rerun()
