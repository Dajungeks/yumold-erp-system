"""
UI 표시 도우미
"""

import streamlit as st
import pandas as pd

class DisplayHelper:
    @staticmethod
    def show_success(message):
        """성공 메시지 표시"""
        st.success(message)
    
    @staticmethod
    def show_error(message):
        """에러 메시지 표시"""
        st.error(message)
    
    @staticmethod
    def show_warning(message):
        """경고 메시지 표시"""
        st.warning(message)
    
    @staticmethod
    def show_info(message):
        """정보 메시지 표시"""
        st.info(message)
    
    @staticmethod
    def format_dataframe(df):
        """데이터프레임 포맷팅"""
        if df.empty:
            st.write("데이터가 없습니다.")
            return
        
        st.dataframe(df, use_container_width=True)
    
    @staticmethod
    def create_metric_card(title, value, delta=None):
        """메트릭 카드 생성"""
        st.metric(title, value, delta)

def display_customer_table(customers_df, get_text=lambda x: x):
    """고객 테이블 표시"""
    if customers_df.empty:
        st.warning(get_text("no_customer_data_to_display"))
        return
    
    # 컬럼명 한국어로 변경
    display_df = customers_df.copy()
    column_mapping = {
        'customer_id': get_text('customer_id'),
        'company_name': get_text('company_name'),
        'contact_person': get_text('contact_person'),
        'email': get_text('email'),
        'phone': get_text('phone'),
        'country': get_text('country'),
        'city': get_text('city'),
        'address': get_text('address'),
        'business_type': get_text('business_type'),
        'status': get_text('status'),
        'created_date': get_text('created_date')
    }
    
    # 존재하는 컬럼만 이름 변경
    for old_col, new_col in column_mapping.items():
        if old_col in display_df.columns:
            display_df = display_df.rename(columns={old_col: new_col})
    
    st.dataframe(display_df, use_container_width=True)

def display_product_table(products_df):
    """제품 테이블 표시"""
    if products_df.empty:
        st.warning("표시할 제품 데이터가 없습니다.")
        return
    st.dataframe(products_df, use_container_width=True)

def display_supplier_table(suppliers_df):
    """공급업체 테이블 표시"""
    if suppliers_df.empty:
        st.warning("표시할 공급업체 데이터가 없습니다.")
        return
    st.dataframe(suppliers_df, use_container_width=True)