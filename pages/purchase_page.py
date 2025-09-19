"""
구매 발주서 관리 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from managers.legacy.purchase_order_manager import PurchaseOrderManager
import json

def show_purchase_page(get_text):
    """구매품 관리 페이지를 표시"""
    st.title(f"🛒 {get_text('purchase_product_registration')}")
    st.markdown("---")
    
    # 매니저 초기화
    try:
        manager = PurchaseOrderManager()
    except Exception as e:
        st.error(f"구매 관리 시스템 초기화 오류: {e}")
        return
    
    # 메인 탭 구성
    main_tabs = st.tabs([
        "📋 발주서 목록",
        "➕ 새 발주서 작성", 
        "📊 통계 및 분석",
        "🔍 발주서 검색"
    ])
    
    with main_tabs[0]:
        show_purchase_order_list(manager)
    
    with main_tabs[1]:
        show_new_purchase_order(manager)
    
    with main_tabs[2]:
        show_purchase_statistics(manager)
    
    with main_tabs[3]:
        show_purchase_search(manager)

def show_purchase_order_list(manager):
    """발주서 목록 표시"""
    st.markdown("### 📋 발주서 목록")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "상태 필터",
            ["전체", "대기", "승인됨", "발주완료", "배송중", "완료", "취소"]
        )
    
    with col2:
        # 날짜 범위 필터
        date_from = st.date_input("시작일", value=None)
    
    with col3:
        date_to = st.date_input("종료일", value=None)
    
    # 발주서 데이터 조회
    try:
        if status_filter == "전체":
            df = manager.get_all_purchase_orders()
        else:
            df = manager.get_purchase_orders_by_status(status_filter)
        
        if df.empty:
            st.info("등록된 발주서가 없습니다.")
            return
        
        # 날짜 필터 적용
        if date_from or date_to:
            df['po_date'] = pd.to_datetime(df['po_date'])
            if date_from:
                df = df[df['po_date'] >= pd.to_datetime(date_from)]
            if date_to:
                df = df[df['po_date'] <= pd.to_datetime(date_to)]
        
        # 표시할 컬럼 선택
        display_columns = [
            'po_number', 'supplier_name', 'po_date', 
            'total_amount', 'currency', 'status'
        ]
        
        if 'item_count' in df.columns:
            display_columns.insert(-1, 'item_count')
        
        display_df = df[display_columns].copy()
        
        # 컬럼명 한글화
        column_mapping = {
            'po_number': '발주서번호',
            'supplier_name': '공급업체',
            'po_date': '발주일자',
            'total_amount': '총금액',
            'currency': '통화',
            'status': '상태',
            'item_count': '품목수'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # 금액 포맷팅
        if '총금액' in display_df.columns:
            display_df['총금액'] = display_df['총금액'].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) else "0"
            )
        
        # 데이터프레임 표시
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 상세 보기 선택
        if len(df) > 0:
            st.markdown("---")
            selected_po = st.selectbox(
                "상세 보기할 발주서 선택",
                options=df['po_number'].tolist(),
                key="po_detail_select"
            )
            
            if selected_po:
                show_purchase_order_detail(manager, df[df['po_number'] == selected_po]['po_id'].iloc[0])
    
    except Exception as e:
        st.error(f"발주서 목록 조회 오류: {e}")

def show_purchase_order_detail(manager, po_id):
    """발주서 상세 정보 표시"""
    try:
        po_data = manager.get_purchase_order_by_id(po_id)
        
        if not po_data:
            st.error("발주서를 찾을 수 없습니다.")
            return
        
        st.markdown("### 📄 발주서 상세 정보")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**발주서 번호:** {po_data.get('po_number', '')}")
            st.write(f"**공급업체:** {po_data.get('supplier_name', '')}")
            st.write(f"**발주일자:** {po_data.get('po_date', '')}")
        
        with col2:
            st.write(f"**배송예정일:** {po_data.get('delivery_date', '') or '미정'}")
            st.write(f"**상태:** {po_data.get('status', '')}")
            st.write(f"**총금액:** {po_data.get('total_amount', 0):,.0f} {po_data.get('currency', 'VND')}")
        
        # 제품 목록
        if po_data.get('products'):
            st.markdown("#### 📦 주문 제품 목록")
            
            products_df = pd.DataFrame(po_data['products'])
            
            if not products_df.empty:
                # 필요한 컬럼만 표시
                display_cols = ['product_name', 'quantity', 'unit', 'unit_price', 'total_price']
                available_cols = [col for col in display_cols if col in products_df.columns]
                
                if available_cols:
                    st.dataframe(
                        products_df[available_cols].rename(columns={
                            'product_name': '제품명',
                            'quantity': '수량',
                            'unit': '단위',
                            'unit_price': '단가',
                            'total_price': '총액'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
        
        # 상태 변경 버튼
        if po_data.get('status') == '대기':
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 승인", type="primary"):
                    if manager.approve_purchase_order(po_id, "시스템"):
                        st.success("발주서가 승인되었습니다!")
                        st.rerun()
                    else:
                        st.error("승인 처리에 실패했습니다.")
            
            with col2:
                if st.button("❌ 취소", type="secondary"):
                    if manager.update_purchase_order(po_id, {'status': '취소'}):
                        st.success("발주서가 취소되었습니다!")
                        st.rerun()
                    else:
                        st.error("취소 처리에 실패했습니다.")
    
    except Exception as e:
        st.error(f"발주서 상세 조회 오류: {e}")

def show_new_purchase_order(manager):
    """새 발주서 작성"""
    st.markdown("### ➕ 새 발주서 작성")
    
    with st.form("new_purchase_order"):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_name = st.text_input("공급업체명*", placeholder="공급업체명을 입력하세요")
            po_date = st.date_input("발주일자*", value=date.today())
            
        with col2:
            delivery_date = st.date_input("배송예정일", value=None)
            currency = st.selectbox("통화", ["VND", "USD", "KRW"], index=0)
        
        # 제품 정보 입력
        st.markdown("#### 📦 제품 정보")
        
        # 동적 제품 추가를 위한 세션 상태 관리
        if 'po_products' not in st.session_state:
            st.session_state.po_products = [{}]
        
        products = []
        
        for i, product in enumerate(st.session_state.po_products):
            st.markdown(f"**제품 {i+1}**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                product_name = st.text_input(f"제품명*", key=f"product_name_{i}", value=product.get('product_name', ''))
            
            with col2:
                quantity = st.number_input(f"수량*", min_value=0.0, key=f"quantity_{i}", value=product.get('quantity', 0.0))
            
            with col3:
                unit_price = st.number_input(f"단가*", min_value=0.0, key=f"unit_price_{i}", value=product.get('unit_price', 0.0))
            
            with col4:
                unit = st.text_input(f"단위", key=f"unit_{i}", value=product.get('unit', 'EA'))
            
            # 총액 자동 계산
            total_price = quantity * unit_price
            st.write(f"총액: {total_price:,.0f} {currency}")
            
            if product_name and quantity > 0 and unit_price > 0:
                products.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'unit': unit,
                    'total_price': total_price
                })
            
            st.markdown("---")
        
        # 제품 추가/제거 버튼
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("➕ 제품 추가"):
                st.session_state.po_products.append({})
                st.rerun()
        
        with col2:
            if len(st.session_state.po_products) > 1:
                if st.form_submit_button("➖ 마지막 제품 제거"):
                    st.session_state.po_products.pop()
                    st.rerun()
        
        # 기타 정보
        terms_conditions = st.text_area("계약조건 및 특이사항")
        
        # 발주서 생성
        submitted = st.form_submit_button("📄 발주서 생성", type="primary")
        
        if submitted:
            if not supplier_name:
                st.error("공급업체명은 필수입니다.")
            elif not products:
                st.error("최소 1개 이상의 제품을 입력해야 합니다.")
            else:
                # 발주서 데이터 생성
                po_data = {
                    'supplier_name': supplier_name,
                    'po_date': po_date,
                    'delivery_date': delivery_date,
                    'currency': currency,
                    'terms_conditions': terms_conditions,
                    'products': products,
                    'created_by': '시스템',
                    'status': '대기'
                }
                
                try:
                    if manager.create_purchase_order(po_data):
                        st.success("✅ 발주서가 성공적으로 생성되었습니다!")
                        st.session_state.po_products = [{}]  # 폼 초기화
                        st.rerun()
                    else:
                        st.error("❌ 발주서 생성에 실패했습니다.")
                
                except Exception as e:
                    st.error(f"발주서 생성 오류: {e}")

def show_purchase_statistics(manager):
    """구매 통계 및 분석"""
    st.markdown("### 📊 구매 통계 및 분석")
    
    try:
        stats = manager.get_purchase_order_statistics()
        
        if not stats:
            st.info("통계 데이터가 없습니다.")
            return
        
        # 전체 통계
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("전체 발주서", stats.get('total_pos', 0))
        
        with col2:
            st.metric("대기중", stats.get('pending_pos', 0))
        
        with col3:
            st.metric("승인됨", stats.get('approved_pos', 0))
        
        with col4:
            st.metric("완료", stats.get('completed_pos', 0))
        
        # 금액 통계
        col1, col2 = st.columns(2)
        
        with col1:
            total_amount = stats.get('total_amount', 0)
            st.metric("총 발주금액", f"{total_amount:,.0f} VND")
        
        with col2:
            avg_amount = stats.get('average_amount', 0)
            st.metric("평균 발주금액", f"{avg_amount:,.0f} VND")
        
        # 상태별 분포
        if stats.get('status_distribution'):
            st.markdown("#### 📈 상태별 분포")
            
            status_df = pd.DataFrame(
                list(stats['status_distribution'].items()),
                columns=['상태', '건수']
            )
            
            st.bar_chart(status_df.set_index('상태'))
        
        # 공급업체별 통계
        if stats.get('supplier_stats'):
            st.markdown("#### 🏭 주요 공급업체")
            
            supplier_df = pd.DataFrame(stats['supplier_stats'])
            
            if not supplier_df.empty:
                supplier_df['amount'] = supplier_df['amount'].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(
                    supplier_df.rename(columns={
                        'name': '공급업체',
                        'count': '발주건수',
                        'amount': '총발주금액'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
    
    except Exception as e:
        st.error(f"통계 조회 오류: {e}")

def show_purchase_search(manager):
    """발주서 검색"""
    st.markdown("### 🔍 발주서 검색")
    
    search_term = st.text_input(
        "검색어 입력",
        placeholder="발주서번호, 공급업체명, 제품명 등으로 검색"
    )
    
    if search_term:
        try:
            results = manager.search_purchase_orders(search_term)
            
            if results.empty:
                st.info("검색 결과가 없습니다.")
            else:
                st.write(f"**검색 결과: {len(results)}건**")
                
                # 결과 표시
                display_columns = [
                    'po_number', 'supplier_name', 'po_date', 
                    'total_amount', 'status'
                ]
                
                available_columns = [col for col in display_columns if col in results.columns]
                
                if available_columns:
                    display_df = results[available_columns].copy()
                    
                    # 컬럼명 한글화
                    column_mapping = {
                        'po_number': '발주서번호',
                        'supplier_name': '공급업체',
                        'po_date': '발주일자',
                        'total_amount': '총금액',
                        'status': '상태'
                    }
                    
                    display_df = display_df.rename(columns=column_mapping)
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"검색 오류: {e}")
    else:
        st.info("검색어를 입력하세요.")
