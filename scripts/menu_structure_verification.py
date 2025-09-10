"""
메뉴 구조 검증 스크립트
각 메뉴의 서브메뉴 연결 상태와 기능 구현 여부를 확인합니다.
"""

import os
from ui_config import SIDEBAR_MENU_STRUCTURE

def check_menu_structure():
    """전체 메뉴 구조를 검증합니다."""
    print("=== Ver06 ERP 시스템 메뉴 구조 검증 ===\n")
    
    # 1. UI 설정 파일 검증
    print("1. UI 설정 파일 검증:")
    print(f"   총 메뉴 수: {len(SIDEBAR_MENU_STRUCTURE)}")
    
    for menu_key, menu_info in SIDEBAR_MENU_STRUCTURE.items():
        print(f"   ✓ {menu_key}: {menu_info['title']}")
        print(f"     - 아이콘: {menu_info['icon']}")
        print(f"     - 서브메뉴 수: {len(menu_info['submenu_options'])}")
        for submenu in menu_info['submenu_options']:
            print(f"       • {submenu}")
        print()
    
    # 2. 페이지 파일 존재 여부 확인
    print("2. 페이지 파일 존재 여부 확인:")
    expected_pages = [
        'dashboard_page.py',
        'employee_page.py', 
        'personal_status_page.py',
        'customer_page.py',
        'product_page.py',
        'quotation_page.py',
        'supplier_page.py',
        'sales_product_page.py',
        'supply_product_page.py',
        'exchange_rate_page.py',
        'business_process_page.py',
        'shipping_page.py',
        'approval_page.py',
        'cash_flow_page.py',
        'pdf_design_page.py',
        'system_guide_page.py'
    ]
    
    pages_dir = 'pages'
    for page_file in expected_pages:
        page_path = os.path.join(pages_dir, page_file)
        if os.path.exists(page_path):
            print(f"   ✓ {page_file} - 존재")
        else:
            print(f"   ✗ {page_file} - 누락")
    
    # 3. 매니저 클래스 확인
    print("\n3. 매니저 클래스 확인:")
    expected_managers = [
        'employee_manager.py',
        'customer_manager.py',
        'product_manager.py',
        'quotation_manager.py',
        'supplier_manager.py',
        'business_process_manager.py',
        'approval_manager.py',
        'exchange_rate_manager.py',
        'auth_manager.py',
        'product_code_manager.py',
        'sales_product_manager.py',
        'supply_product_manager.py',
        'pdf_design_manager.py',
        'vacation_manager.py',
        'cash_flow_manager.py',
        'shipping_manager.py',
        'inventory_manager.py',
        'invoice_manager.py'
    ]
    
    for manager_file in expected_managers:
        if os.path.exists(manager_file):
            print(f"   ✓ {manager_file} - 존재")
        else:
            print(f"   ✗ {manager_file} - 누락")
    
    # 4. menu_dashboard.py의 함수 매핑 확인
    print("\n4. menu_dashboard.py 함수 매핑 상태:")
    dashboard_functions = [
        'show_main_dashboard',
        'show_employee_dashboard',
        'show_customer_dashboard', 
        'show_product_dashboard',
        'show_quotation_dashboard',
        'show_supplier_dashboard',
        'show_sales_product_dashboard',
        'show_supply_product_dashboard',
        'show_exchange_rate_dashboard',
        'show_business_process_dashboard',
        'show_shipping_dashboard',
        'show_approval_dashboard',
        'show_cash_flow_dashboard',
        'show_pdf_design_dashboard',
        'show_system_guide_dashboard',
        'show_personal_status_dashboard'
    ]
    
    menu_dashboard_path = 'pages/menu_dashboard.py'
    if os.path.exists(menu_dashboard_path):
        with open(menu_dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for func_name in dashboard_functions:
                if f"def {func_name}" in content:
                    print(f"   ✓ {func_name} - 구현됨")
                else:
                    print(f"   ✗ {func_name} - 누락됨")
    else:
        print("   ✗ menu_dashboard.py 파일이 존재하지 않습니다.")
    
    print("\n=== 검증 완료 ===")

if __name__ == "__main__":
    check_menu_structure()