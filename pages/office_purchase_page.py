"""
사무용품 구매 관리 페이지
pages/office_purchase_page.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import json
from typing import Dict, List, Any

# 매니저 임포트
try:
    from managers.postgresql.postgresql_office_purchase_manager import PostgreSQLOfficePurchaseManager
except ImportError:
    from managers.legacy.office_purchase_manager import OfficePurchaseManager as PostgreSQLOfficePurchaseManager

# 다국어 지원
def get_text(key, lang='ko'):
    """다국어 텍스트 반환"""
    texts = {
        'ko': {
            'title': '사무용품 구매 관리',
            'new_purchase': '새 구매 등록',
            'purchase_list': '구매 목록',
            'statistics': '구매 통계',
            'search': '검색',
            'export': '내보내기',
            'purchase_id': '구매 ID',
            'purchase_date': '구매 날짜',
            'requester_name': '요청자',
            'department': '부서',
            'supplier_name': '공급업체',
            'total_amount': '총 금액',
            'status': '상태',
            'add_item': '물품 추가',
            'item_name': '물품명',
            'category': '카테고리',
            'quantity': '수량',
            'unit': '단위',
            'unit_price': '단가',
            'save': '저장',
            'cancel': '취소',
            'edit': '수정',
            'delete': '삭제',
            'view': '보기'
        },
        'en': {
            'title': 'Office Purchase Management',
            'new_purchase': 'New Purchase',
            'purchase_list': 'Purchase List',
            'statistics': 'Purchase Statistics',
            'search': 'Search',
            'export': 'Export',
            'purchase_id': 'Purchase ID',
            'purchase_date': 'Purchase Date',
            'requester_name': 'Requester',
            'department': 'Department',
            'supplier_name': 'Supplier',
            'total_amount': 'Total Amount',
            'status': 'Status',
            'add_item': 'Add Item',
            'item_name': 'Item Name',
            'category': 'Category',
            'quantity': 'Quantity',
            'unit': 'Unit',
            'unit_price': 'Unit Price',
            'save': 'Save',
            'cancel': 'Cancel',
            'edit': 'Edit',
            'delete': 'Delete',
            'view': 'View'
        }
    }
    return texts.get(lang, texts['ko']).get(key, key)

def init_session_state():
    """세션 상태 초기화"""
    if 'office_purchase_manager' not in st.session_state:
        st.session_state.office_purchase_manager = PostgreSQLOfficePurchaseManager()
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "purchase_list"
    
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = 'ko'
    
    if 'new_purchase_items' not in st.session_state:
        st.session_state.new_purchase_items = []
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    if 'selected_purchase_id' not in st.session_state:
        st.session_state.selected_purchase_id = None

def render_header():
    """헤더 렌더링"""
    lang = st.session_state.selected_language
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title(get_text('title', lang))
    
    with col2:
        # 언어 선택
        language_options = {'한국어': 'ko', 'English': 'en'}
        selected_lang_name = st.selectbox(
            "Language", 
            options=list(language_options.keys()),
            index=0 if lang == 'ko' else 1,
            key="language_selector"
        )
        st.session_state.selected_language = language_options[selected_lang_name]
    
    with col3:
        # 새로고침 버튼
        if st.button("🔄 새로고침"):
            st.rerun()

def render_status_badge(status):
    """상태 배지 렌더링"""
    status_colors = {
        'pending': '🟡',
        'approved': '🟢', 
        'ordered': '🔵',
        'received': '🟣',
        'completed': '✅',
        'cancelled': '❌'
    }
    
    status_names = {
        'pending': '대기중',
        'approved': '승인됨',
        'ordered': '주문됨', 
        'received': '입고됨',
        'completed': '완료',
        'cancelled': '취소됨'
    }
    
    icon = status_colors.get(status, '⚪')
    name = status_names.get(status, status)
    return f"{icon} {name}"

def render_new_purchase_form():
    """새 구매 등록 폼"""
    lang = st.session_state.selected_language
    
    st.subheader(get_text('new_purchase', lang))
    
    with st.form("new_purchase_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            requester_name = st.text_input(get_text('requester_name', lang), required=True)
            department = st.text_input(get_text('department', lang))
            purchase_date = st.date_input(get_text('purchase_date', lang), value=date.today())
            supplier_name = st.text_input(get_text('supplier_name', lang))
        
        with col2:
            purchase_purpose = st.text_area("구매 목적")
            payment_method = st.selectbox("결제 방법", ["현금", "카드", "계좌이체", "기타"])
            receipt_number = st.text_input("영수증 번호")
            status = st.selectbox("상태", ["pending", "approved", "ordered"])
        
        notes = st.text_area("메모")
        
        # 물품 목록 관리
        st.subheader("구매 물품 목록")
        
        # 물품 추가 폼
        with st.expander("물품 추가", expanded=True):
            item_col1, item_col2, item_col3, item_col4 = st.columns(4)
            
            with item_col1:
                item_name = st.text_input("물품명", key="new_item_name")
                category = st.selectbox("카테고리", 
                    ["사무용품", "IT장비", "소모품", "가구", "기타"], 
                    key="new_item_category")
            
            with item_col2:
                quantity = st.number_input("수량", min_value=1, value=1, key="new_item_quantity")
                unit = st.text_input("단위", value="EA", key="new_item_unit")
            
            with item_col3:
                unit_price = st.number_input("단가", min_value=0.0, format="%.2f", key="new_item_price")
                total_price = quantity * unit_price
                st.write(f"합계: {total_price:,.0f}원")
            
            with item_col4:
                item_notes = st.text_area("물품 메모", key="new_item_notes", height=100)
                
                if st.button("물품 추가"):
                    if item_name:
                        new_item = {
                            'item_name': item_name,
                            'category': category,
                            'quantity': quantity,
                            'unit': unit,
                            'unit_price': unit_price,
                            'total_price': total_price,
                            'item_notes': item_notes
                        }
                        st.session_state.new_purchase_items.append(new_item)
                        st.success(f"물품 '{item_name}' 추가됨")
                        st.rerun()
        
        # 현재 물품 목록 표시
        if st.session_state.new_purchase_items:
            st.write("**추가된 물품 목록:**")
            
            items_df = pd.DataFrame(st.session_state.new_purchase_items)
            
            # 물품 목록을 편집 가능한 형태로 표시
            edited_items = st.data_editor(
                items_df,
                column_config={
                    "item_name": "물품명",
                    "category": st.column_config.SelectboxColumn(
                        "카테고리",
                        options=["사무용품", "IT장비", "소모품", "가구", "기타"]
                    ),
                    "quantity": st.column_config.NumberColumn("수량", min_value=1),
                    "unit": "단위",
                    "unit_price": st.column_config.NumberColumn("단가", format="%.2f"),
                    "total_price": st.column_config.NumberColumn("합계", format="%.2f"),
                    "item_notes": "메모"
                },
                use_container_width=True,
                hide_index=True
            )
            
            # 총 금액 계산
            total_amount = edited_items['total_price'].sum()
            st.write(f"**총 구매 금액: {total_amount:,.0f}원**")
            
            # 물품 목록 초기화 버튼
            if st.button("물품 목록 초기화"):
                st.session_state.new_purchase_items = []
                st.rerun()
        
        # 폼 제출
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button(get_text('save', lang), type="primary")
        
        with col2:
            if st.form_submit_button("목록 초기화"):
                st.session_state.new_purchase_items = []
                st.rerun()
        
        if submitted:
            if not requester_name:
                st.error("요청자명은 필수 입력 사항입니다.")
                return
            
            # 구매 데이터 구성
            purchase_data = {
                'requester_name': requester_name,
                'department': department,
                'purchase_date': purchase_date,
                'purchase_purpose': purchase_purpose,
                'supplier_name': supplier_name,
                'payment_method': payment_method,
                'receipt_number': receipt_number,
                'status': status,
                'notes': notes,
                'items': st.session_state.new_purchase_items.copy() if st.session_state.new_purchase_items else []
            }
            
            # 구매 등록
            manager = st.session_state.office_purchase_manager
            success, message = manager.create_purchase_record(purchase_data)
            
            if success:
                st.success(message)
                st.session_state.new_purchase_items = []  # 물품 목록 초기화
                st.rerun()
            else:
                st.error(message)

def render_purchase_list():
    """구매 목록 표시"""
    lang = st.session_state.selected_language
    manager = st.session_state.office_purchase_manager
    
    st.subheader(get_text('purchase_list', lang))
    
    # 검색 및 필터
    with st.expander("검색 및 필터", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search_term = st.text_input("검색어")
        
        with col2:
            filter_department = st.text_input("부서 필터")
        
        with col3:
            filter_status = st.selectbox("상태 필터", 
                ["전체", "pending", "approved", "ordered", "received", "completed", "cancelled"])
        
        with col4:
            date_range = st.date_input("날짜 범위", 
                value=[date.today() - timedelta(days=30), date.today()],
                format="YYYY-MM-DD")
    
    # 데이터 조회
    if search_term or filter_department or filter_status != "전체" or len(date_range) == 2:
        # 필터링된 검색
        filters = {}
        if filter_department:
            filters['department'] = filter_department
        if filter_status != "전체":
            filters['status'] = filter_status
        if len(date_range) == 2:
            filters['start_date'] = date_range[0]
            filters['end_date'] = date_range[1]
        
        df = manager.search_purchases(search_term, filters)
    else:
        # 전체 목록 조회
        df = manager.get_all_purchases(limit=100)
    
    if df.empty:
        st.info("표시할 구매 기록이 없습니다.")
        return
    
    # 데이터 표시
    st.write(f"총 {len(df)}건의 구매 기록")
    
    # 상태별 요약
    if not df.empty:
        status_summary = df['status'].value_counts()
        
        cols = st.columns(len(status_summary))
        for i, (status, count) in enumerate(status_summary.items()):
            with cols[i]:
                st.metric(render_status_badge(status), count)
    
    # 구매 목록 테이블
    display_columns = ['purchase_id', 'purchase_date', 'requester_name', 'department', 
                      'supplier_name', 'total_amount', 'status', 'item_count']
    
    if not df.empty:
        # 상태 컬럼을 배지 형태로 변환
        df_display = df[display_columns].copy()
        df_display['status_display'] = df_display['status'].apply(render_status_badge)
        
        # 금액 포맷팅
        df_display['total_amount'] = df_display['total_amount'].apply(
            lambda x: f"{x:,.0f}원" if pd.notnull(x) else "0원"
        )
        
        # 컬럼명 한국어로 변경
        column_names = {
            'purchase_id': '구매ID',
            'purchase_date': '구매날짜', 
            'requester_name': '요청자',
            'department': '부서',
            'supplier_name': '공급업체',
            'total_amount': '총금액',
            'status_display': '상태',
            'item_count': '물품수'
        }
        
        df_display = df_display.rename(columns=column_names)
        
        # 테이블 표시 (상호작용 기능 포함)
        selected_rows = st.dataframe(
            df_display.drop('status', axis=1, errors='ignore'),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # 선택된 행 처리
        if selected_rows['selection']['rows']:
            selected_idx = selected_rows['selection']['rows'][0]
            selected_purchase_id = df.iloc[selected_idx]['purchase_id']
            
            # 상세 정보 표시
            render_purchase_detail(selected_purchase_id)

def render_purchase_detail(purchase_id: str):
    """구매 상세 정보 표시"""
    manager = st.session_state.office_purchase_manager
    
    with st.expander(f"구매 상세 정보: {purchase_id}", expanded=True):
        purchase_data = manager.get_purchase_by_id(purchase_id)
        
        if not purchase_data:
            st.error("구매 정보를 찾을 수 없습니다.")
            return
        
        # 기본 정보
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**기본 정보**")
            st.write(f"구매ID: {purchase_data['purchase_id']}")
            st.write(f"구매날짜: {purchase_data['purchase_date']}")
            st.write(f"요청자: {purchase_data['requester_name']}")
            st.write(f"부서: {purchase_data.get('department', 'N/A')}")
        
        with col2:
            st.write("**공급업체 정보**")
            st.write(f"공급업체: {purchase_data.get('supplier_name', 'N/A')}")
            st.write(f"결제방법: {purchase_data.get('payment_method', 'N/A')}")
            st.write(f"영수증번호: {purchase_data.get('receipt_number', 'N/A')}")
            st.write(f"상태: {render_status_badge(purchase_data['status'])}")
        
        with col3:
            st.write("**금액 정보**")
            st.write(f"총 금액: {purchase_data['total_amount']:,.0f}원")
            st.write(f"등록일시: {purchase_data['input_date']}")
        
        # 구매 목적 및 메모
        if purchase_data.get('purchase_purpose'):
            st.write("**구매 목적**")
            st.write(purchase_data['purchase_purpose'])
        
        if purchase_data.get('notes'):
            st.write("**메모**")
            st.write(purchase_data['notes'])
        
        # 물품 목록
        items = purchase_data.get('items', [])
        if items:
            st.write("**구매 물품 목록**")
            items_df = pd.DataFrame(items)
            
            if not items_df.empty:
                # 표시할 컬럼 선택
                display_columns = ['item_name', 'category', 'quantity', 'unit', 
                                 'unit_price', 'total_price', 'item_notes']
                available_columns = [col for col in display_columns if col in items_df.columns]
                
                column_names = {
                    'item_name': '물품명',
                    'category': '카테고리',
                    'quantity': '수량',
                    'unit': '단위',
                    'unit_price': '단가',
                    'total_price': '금액',
                    'item_notes': '메모'
                }
                
                items_display = items_df[available_columns].copy()
                items_display = items_display.rename(columns=column_names)
                
                # 금액 포맷팅
                if '금액' in items_display.columns:
                    items_display['금액'] = items_display['금액'].apply(
                        lambda x: f"{float(x):,.0f}원" if pd.notnull(x) else "0원"
                    )
                if '단가' in items_display.columns:
                    items_display['단가'] = items_display['단가'].apply(
                        lambda x: f"{float(x):,.0f}원" if pd.notnull(x) else "0원"
                    )
                
                st.dataframe(items_display, use_container_width=True, hide_index=True)
        
        # 액션 버튼
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("상태 변경", key=f"status_{purchase_id}"):
                st.session_state[f'show_status_form_{purchase_id}'] = True
        
        with col2:
            if st.button("편집", key=f"edit_{purchase_id}"):
                st.session_state.edit_mode = True
                st.session_state.selected_purchase_id = purchase_id
        
        with col3:
            if st.button("삭제", key=f"delete_{purchase_id}"):
                if st.session_state.get(f'confirm_delete_{purchase_id}'):
                    success, message = manager.delete_purchase(purchase_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.session_state[f'confirm_delete_{purchase_id}'] = True
                    st.warning("삭제하려면 다시 한 번 클릭하세요.")
        
        with col4:
            # CSV 다운로드
            if items:
                csv_data = pd.DataFrame([{
                    '구매ID': purchase_data['purchase_id'],
                    '구매날짜': purchase_data['purchase_date'],
                    '요청자': purchase_data['requester_name'],
                    '부서': purchase_data.get('department', ''),
                    '물품명': item['item_name'],
                    '카테고리': item['category'],
                    '수량': item['quantity'],
                    '단위': item['unit'],
                    '단가': item['unit_price'],
                    '금액': item['total_price']
                } for item in items])
                
                csv = csv_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "CSV 다운로드",
                    csv,
                    f"구매상세_{purchase_id}.csv",
                    "text/csv",
                    key=f"download_{purchase_id}"
                )
        
        # 상태 변경 폼
        if st.session_state.get(f'show_status_form_{purchase_id}'):
            with st.form(f"status_form_{purchase_id}"):
                new_status = st.selectbox(
                    "새 상태",
                    ["pending", "approved", "ordered", "received", "completed", "cancelled"],
                    index=["pending", "approved", "ordered", "received", "completed", "cancelled"].index(purchase_data['status'])
                )
                status_notes = st.text_area("상태 변경 메모")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("상태 변경"):
                        success, message = manager.update_purchase_status(purchase_id, new_status, status_notes)
                        if success:
                            st.success(message)
                            del st.session_state[f'show_status_form_{purchase_id}']
                            st.rerun()
                        else:
                            st.error(message)
                
                with col2:
                    if st.form_submit_button("취소"):
                        del st.session_state[f'show_status_form_{purchase_id}']
                        st.rerun()

def render_statistics():
    """구매 통계 대시보드"""
    lang = st.session_state.selected_language
    manager = st.session_state.office_purchase_manager
    
    st.subheader(get_text('statistics', lang))
    
    # 기간 선택
    col1, col2 = st.columns(2)
    with col1:
        period_months = st.selectbox("분석 기간", [1, 3, 6, 12], index=2, format_func=lambda x: f"최근 {x}개월")
    
    with col2:
        if st.button("통계 새로고침"):
            st.rerun()
    
    # 통계 데이터 조회
    stats = manager.get_purchase_statistics(period_months)
    
    if not stats:
        st.info("통계 데이터가 없습니다.")
        return
    
    # 주요 지표
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 구매 건수", f"{stats['total_purchases']:,}건")
    
    with col2:
        st.metric("총 구매 금액", f"{stats['total_amount']:,.0f}원")
    
    with col3:
        avg_amount = stats['average_amount']
        st.metric("평균 구매 금액", f"{avg_amount:,.0f}원")
    
    with col4:
        st.metric("활성 요청자", f"{stats['unique_requesters']}명")
    
    # 차트 섹션
    if stats.get('monthly_stats'):
        st.subheader("월별 구매 현황")
        
        monthly_df = pd.DataFrame(stats['monthly_stats'])
        monthly_df['month'] = pd.to_datetime(monthly_df['month'])
        monthly_df['month_str'] = monthly_df['month'].dt.strftime('%Y-%m')
        
        # 월별 구매 금액 및 건수 차트
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('월별 구매 금액', '월별 구매 건수'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 구매 금액 차트
        fig.add_trace(
            go.Bar(
                x=monthly_df['month_str'],
                y=monthly_df['amount'],
                name='구매 금액',
                text=[f"{x:,.0f}원" for x in monthly_df['amount']],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # 구매 건수 차트
        fig.add_trace(
            go.Bar(
                x=monthly_df['month_str'],
                y=monthly_df['count'],
                name='구매 건수',
                text=monthly_df['count'],
                textposition='outside'
            ),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # 카테고리별 통계
    if stats.get('category_stats'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("카테고리별 구매 금액")
            category_df = pd.DataFrame(stats['category_stats'])
            
            if not category_df.empty:
                fig = px.pie(
                    category_df, 
                    values='amount', 
                    names='category',
                    title="카테고리별 구매 금액 분포"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("카테고리별 구매 건수")
            
            if not category_df.empty:
                fig = px.bar(
                    category_df,
                    x='category',
                    y='count',
                    title="카테고리별 구매 건수"
                )
                fig.update_layout(xaxis_title="카테고리", yaxis_title="구매 건수")
                st.plotly_chart(fig, use_container_width=True)
    
    # 부서별 통계
    if stats.get('department_stats'):
        st.subheader("부서별 구매 현황")
        dept_df = pd.DataFrame(stats['department_stats'])
        
        if not dept_df.empty:
            # 상위 10개 부서만 표시
            dept_df_top = dept_df.head(10)
            
            fig = px.bar(
                dept_df_top,
                x='department',
                y='amount',
                title="부서별 구매 금액 (상위 10개)",
                text=[f"{x:,.0f}원" for x in dept_df_top['amount']]
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_title="부서", yaxis_title="구매 금액")
            st.plotly_chart(fig, use_container_width=True)
    
    # 상태별 통계
    if stats.get('status_stats'):
        st.subheader("상태별 구매 현황")
        status_df = pd.DataFrame(stats['status_stats'])
        
        if not status_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # 상태별 건수
                fig = px.bar(
                    status_df,
                    x='status',
                    y='count',
                    title="상태별 구매 건수"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 상태별 금액
                fig = px.bar(
                    status_df,
                    x='status',
                    y='amount',
                    title="상태별 구매 금액"
                )
                st.plotly_chart(fig, use_container_width=True)

def render_export_section():
    """내보내기 섹션"""
    manager = st.session_state.office_purchase_manager
    
    st.subheader("데이터 내보내기")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_start_date = st.date_input("시작 날짜", value=date.today().replace(day=1))
    
    with col2:
        export_end_date = st.date_input("종료 날짜", value=date.today())
    
    if st.button("CSV 내보내기"):
        df_export = manager.export_purchases_to_csv(export_start_date, export_end_date)
        
        if df_export is not None and not df_export.empty:
            csv = df_export.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                "📁 CSV 파일 다운로드",
                csv,
                f"사무용품구매_{export_start_date}_{export_end_date}.csv",
                "text/csv",
                key="export_csv"
            )
            
            st.success(f"{len(df_export)}건의 데이터를 내보낼 준비가 완료되었습니다.")
            
            # 미리보기
            st.subheader("내보내기 데이터 미리보기")
            st.dataframe(df_export.head(10), use_container_width=True)
        else:
            st.info("선택한 기간에 내보낼 데이터가 없습니다.")

def main():
    """메인 함수"""
    # 페이지 설정
    st.set_page_config(
        page_title="사무용품 구매 관리",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더 렌더링
    render_header()
    
    # 사이드바 메뉴
    with st.sidebar:
        st.title("메뉴")
        
        tab_options = {
            "구매 목록": "purchase_list",
            "새 구매 등록": "new_purchase", 
            "구매 통계": "statistics",
            "데이터 내보내기": "export"
        }
        
        selected_tab = st.radio(
            "선택하세요",
            options=list(tab_options.keys()),
            index=list(tab_options.values()).index(st.session_state.current_tab)
        )
        
        st.session_state.current_tab = tab_options[selected_tab]
        
        # 시스템 정보
        st.divider()
        st.subheader("시스템 정보")
        
        manager = st.session_state.office_purchase_manager
        if manager and hasattr(manager, 'table_created') and manager.table_created:
            st.success("데이터베이스 연결됨")
        else:
            st.error("데이터베이스 연결 실패")
        
        # 빠른 통계
        try:
            quick_stats = manager.get_purchase_statistics(1)  # 최근 1개월
            if quick_stats:
                st.metric("이번 달 구매", f"{quick_stats.get('total_purchases', 0)}건")
                st.metric("이번 달 금액", f"{quick_stats.get('total_amount', 0):,.0f}원")
        except:
            pass
    
    # 메인 콘텐츠
    if st.session_state.current_tab == "purchase_list":
        render_purchase_list()
    elif st.session_state.current_tab == "new_purchase":
        render_new_purchase_form()
    elif st.session_state.current_tab == "statistics":
        render_statistics()
    elif st.session_state.current_tab == "export":
        render_export_section()

if __name__ == "__main__":
    main()
