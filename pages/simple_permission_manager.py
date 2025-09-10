import streamlit as st
import pandas as pd
from datetime import datetime

def show_simple_employee_permissions(employee_manager, auth_manager):
    """간단한 직원 권한 관리 페이지"""
    st.header("🔐 직원 권한 관리")
    
    # 직원 목록 가져오기
    employees = employee_manager.get_all_employees()
    if len(employees) == 0:
        st.warning("등록된 직원이 없습니다.")
        return
    
    # 직원 선택 (딕셔너리 리스트 기반)
    employee_options = {}
    for emp in employees:
        key = f"{emp['name']} ({emp['employee_id']})"
        employee_options[key] = emp['employee_id']
    
    selected_employee = st.selectbox("권한을 설정할 직원 선택", list(employee_options.keys()))
    
    if selected_employee:
        employee_id = employee_options[selected_employee]
        employee_name = selected_employee.split("(")[0].strip()
        
        st.markdown("---")
        
        # 현재 권한 상태 표시
        current_permissions = auth_manager.get_user_permissions(employee_id)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("현재 권한 상태")
            # 간단한 권한 요약
            basic_count = sum([
                current_permissions.get('can_access_employee_management', False),
                current_permissions.get('can_access_customer_management', False),
                current_permissions.get('can_access_product_management', False),
                current_permissions.get('can_access_quotation_management', False),
                current_permissions.get('can_access_supplier_management', False)
            ])
            
            st.metric("기본 시스템 권한", f"{basic_count}/5")
            
            business_count = sum([
                current_permissions.get('can_access_business_process_management', False),
                current_permissions.get('can_access_approval_management', False),
                current_permissions.get('can_access_cash_flow_management', False),
                current_permissions.get('can_access_sales_product_management', False)
            ])
            
            st.metric("비즈니스 프로세스 권한", f"{business_count}/4")
        
        with col2:
            st.subheader("권한 등급 선택")
            
            # 권한 레벨 선택
            permission_level = st.radio(
                "권한 등급을 선택하세요:",
                ["제한된 사용자", "일반 사용자", "고급 사용자", "관리자", "모든 권한"],
                key=f"permission_level_{employee_id}"
            )
            
            # 권한 등급별 설명
            if permission_level == "제한된 사용자":
                st.info("🔒 제한된 사용자: 개인 상태 관리, 환율 확인만 가능")
                new_permissions = get_limited_permissions()
            elif permission_level == "일반 사용자":
                st.info("👤 일반 사용자: 고객, 제품, 견적 관리 가능")
                new_permissions = get_normal_permissions()
            elif permission_level == "고급 사용자":
                st.info("⭐ 고급 사용자: 대부분의 비즈니스 기능 접근 가능")
                new_permissions = get_advanced_permissions()
            elif permission_level == "관리자":
                st.info("👑 관리자: 직원 관리 포함한 모든 기능 (삭제 권한 제외)")
                new_permissions = get_admin_permissions()
            else:  # 모든 권한
                st.info("🔓 모든 권한: 데이터 삭제 권한까지 포함한 전체 권한")
                new_permissions = get_full_permissions()
            
            # 권한 적용 버튼
            if st.button(f"✅ {employee_name}에게 {permission_level} 권한 적용", type="primary", use_container_width=True):
                try:
                    # 권한 업데이트
                    auth_manager.update_user_permissions(employee_id, new_permissions)
                    st.success(f"✅ {employee_name}의 권한이 '{permission_level}'로 업데이트되었습니다!")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 권한 업데이트 중 오류가 발생했습니다: {str(e)}")
        
        # 상세 권한 현황 표시
        st.markdown("---")
        st.subheader("상세 권한 현황")
        
        # 권한 목록을 테이블로 표시
        permission_data = []
        permission_labels = {
            'can_access_employee_management': '직원 관리',
            'can_access_customer_management': '고객 관리',
            'can_access_product_management': '제품 관리',
            'can_access_quotation_management': '견적 관리',
            'can_access_supplier_management': '공급업체 관리',
            'can_access_business_process_management': '비즈니스 프로세스',
            'can_access_approval_management': '승인 관리',
            'can_access_cash_flow_management': '현금 흐름 관리',
            'can_access_sales_product_management': '판매 제품 관리',
            'can_access_exchange_rate_management': '환율 관리',
            'can_access_pdf_design_management': 'PDF 관리',
            'can_access_personal_status': '개인 상태 관리',
            'can_delete_data': '데이터 삭제 권한'
        }
        
        for perm_key, perm_name in permission_labels.items():
            status = "✅ 허용" if current_permissions.get(perm_key, False) else "❌ 제한"
            permission_data.append({"권한": perm_name, "상태": status})
        
        df = pd.DataFrame(permission_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def get_limited_permissions():
    """제한된 사용자 권한"""
    return {
        'can_access_employee_management': False,
        'can_access_customer_management': False,
        'can_access_product_management': False,
        'can_access_quotation_management': False,
        'can_access_supplier_management': False,
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

def get_normal_permissions():
    """일반 사용자 권한"""
    return {
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
        'can_access_sales_product_management': True,
        'can_access_exchange_rate_management': True,
        'can_access_pdf_design_management': False,
        'can_access_personal_status': True,
        'can_access_vacation_management': False,
        'can_delete_data': False
    }

def get_advanced_permissions():
    """고급 사용자 권한"""
    return {
        'can_access_employee_management': False,
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
        'can_access_vacation_management': False,
        'can_delete_data': False
    }

def get_admin_permissions():
    """관리자 권한"""
    return {
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
        'can_delete_data': False
    }

def get_full_permissions():
    """모든 권한"""
    return {
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