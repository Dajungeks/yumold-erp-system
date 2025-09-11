"""
메뉴 대시보드 모듈 - 각 메뉴별 대시보드 함수 정의
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

def show_main_dashboard(managers, selected_submenu, get_text):
    """메인 대시보드 - 지연 로딩 최적화"""
    # 시스템 설정에서 동적으로 제목 가져오기
    system_config_manager = managers.get('system_config_manager')
    dashboard_title = get_text("dashboard_title")
    st.subheader(f"📊 {dashboard_title}")
    
    # 지연 로딩을 위한 데이터 선택
    st.info("⚡ 성능 최적화: 원하는 데이터만 로드하여 빠른 반응성을 제공합니다.")
    
    # 로딩할 데이터 유형 선택
    data_options = {
        "all": "🔄 전체 데이터 로드",
        "employees": "👥 직원 데이터만",
        "customers": "🏢 고객 데이터만", 
        "products": "📦 제품 데이터만",
        "quotations": "📋 견적서 데이터만",
        "vacations": "🏖️ 휴가 데이터만"
    }
    
    selected_data = st.selectbox(
        "로드할 데이터를 선택하세요:",
        options=list(data_options.keys()),
        format_func=lambda x: data_options[x],
        key="dashboard_data_selector"
    )
    
    # 로드 버튼
    load_button = st.button("📊 선택된 데이터 로드", type="primary", key="load_dashboard_data")
    
    if load_button or st.session_state.get('dashboard_data_loaded', False):
        if load_button:
            st.session_state.dashboard_data_loaded = True
            
        try:
            # 초기값 설정
            employee_count = 0
            customer_count = 0
            product_count = 0
            quotation_count = 0
            
            # 선택된 데이터만 지연 로딩
            if selected_data in ["all", "employees"]:
                with st.spinner("👥 직원 데이터 로딩 중..."):
                    employee_manager = managers.get('employee_manager')
                    if employee_manager:
                        try:
                            employees = employee_manager.get_all_employees()
                            employee_count = len(employees) if len(employees) > 0 else 0
                        except:
                            employee_count = 0
            
            if selected_data in ["all", "customers"]:
                with st.spinner("🏢 고객 데이터 로딩 중..."):
                    customer_manager = managers.get('customer_manager')
                    if customer_manager:
                        try:
                            customers = customer_manager.get_all_customers()
                            customer_count = len(customers) if len(customers) > 0 else 0
                        except:
                            customer_count = 0
            
            if selected_data in ["all", "products"]:
                with st.spinner("📦 제품 데이터 로딩 중..."):
                    product_manager = managers.get('product_manager')
                    if product_manager:
                        try:
                            products = product_manager.get_all_products()
                            product_count = len(products) if len(products) > 0 else 0
                        except:
                            product_count = 0
            
            if selected_data in ["all", "quotations"]:
                with st.spinner("📋 견적서 데이터 로딩 중..."):
                    quotation_manager = managers.get('quotation_manager')
                    if quotation_manager:
                        try:
                            quotations = quotation_manager.get_all_quotations()
                            quotation_count = len(quotations) if len(quotations) > 0 else 0
                        except Exception as e:
                            quotation_count = 0
                    else:
                        quotation_count = 0
        
            # 휴가 및 근무 인원 통계 계산 (지연 로딩)
            working_employees = 0
            vacation_employees = 0
            active_employees = 0
            
            if selected_data in ["all", "vacations", "employees"]:
                with st.spinner("🏖️ 휴가 데이터 로딩 중..."):
                    vacation_manager = managers.get('vacation_manager')
                    employee_manager = managers.get('employee_manager')
                    if employee_manager and vacation_manager:
                        try:
                            employees = employee_manager.get_all_employees()
                            if len(employees) > 0:
                                # 재직 중인 직원 수 계산
                                active_employees = len(employees[employees['work_status'] == '재직']) if 'work_status' in employees.columns else employee_count
                                
                                # 오늘 날짜로 현재 휴가 중인 직원 계산
                                today = datetime.now().date()
                                today_str = today.strftime('%Y-%m-%d')
                                
                                all_vacations = vacation_manager.get_all_vacation_requests()
                                if len(all_vacations) > 0:
                                    # 승인된 휴가 중 오늘 날짜에 해당하는 것
                                    approved_vacations = all_vacations[all_vacations['status'] == '승인']
                                    
                                    current_vacation_employees = set()
                                    for _, vacation in approved_vacations.iterrows():
                                        try:
                                            start_date = datetime.strptime(vacation['start_date'], '%Y-%m-%d').date()
                                            end_date = datetime.strptime(vacation['end_date'], '%Y-%m-%d').date()
                                            
                                            if start_date <= today <= end_date:
                                                current_vacation_employees.add(vacation['employee_id'])
                                        except Exception as vacation_e:
                                            continue
                                    
                                    vacation_employees = len(current_vacation_employees)
                                
                                working_employees = max(0, active_employees - vacation_employees)
                        except Exception as e:
                            working_employees = employee_count
                            vacation_employees = 0
                            active_employees = employee_count
                    else:
                        working_employees = employee_count
                        vacation_employees = 0
                        active_employees = employee_count
            
            # 전체 통계 카드 (6개 컬럼)
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.success(f"**👥 {get_text('total_staff')}**")
                st.metric(label=get_text("total_staff"), value=employee_count)
            
            with col2:
                st.info(f"**💼 {get_text('outstanding_tasks')}**")
                st.metric(label=get_text("outstanding_tasks"), value=working_employees)
            
            with col3:
                st.warning(f"**🏖️ {get_text('overdue_tasks')}**")
                st.metric(label=get_text("overdue_tasks"), value=vacation_employees)
            
            with col4:
                st.info(f"**🏢 {get_text('total_customers')}**")
                st.metric(label=get_text("total_customers"), value=customer_count)
            
            with col5:
                st.warning(f"**📦 {get_text('total_products')}**")
                st.metric(label=get_text("total_products"), value=product_count)
            
            with col6:
                st.error(f"**📋 {get_text('outstanding_approvals')}**")
                st.metric(label=get_text("outstanding_approvals"), value=quotation_count)
            
            st.markdown("---")
            
            # 상세 통계 섹션
            st.subheader(f"📊 {get_text('detailed_stats')}")
            
            # 4개 컬럼으로 상세 통계 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"#### 🎯 {get_text('customer_health')}")
                # 견적 상태별 통계
                quotation_manager = managers.get('quotation_manager')
                if quotation_manager:
                    try:
                        quotations = quotation_manager.get_all_quotations()
                        if len(quotations) > 0:
                            draft_count = len([q for q in quotations if q.get('status', '') == '임시저장'])
                            pending_count = len([q for q in quotations if q.get('status', '') == '대기'])
                            approved_count = len([q for q in quotations if q.get('status', '') == '승인'])
                        else:
                            draft_count = pending_count = approved_count = 0
                    except:
                        draft_count = pending_count = approved_count = 0
                else:
                    draft_count = pending_count = approved_count = 0
                
                st.metric(get_text("total_customer_num"), customer_count)
            
            with col2:
                st.markdown(f"#### 💰 {get_text('overdue_tasks_stat')}")
                # 승인 대기 현황
                approval_manager = managers.get('approval_manager')
                pending_approvals = 0
                if approval_manager:
                    try:
                        pending_requests = approval_manager.get_pending_requests()
                        pending_approvals = len(pending_requests) if len(pending_requests) > 0 else 0
                    except:
                        pending_approvals = 0
                
                st.metric(get_text("overdue_count"), pending_approvals)
            
            with col3:
                st.markdown(f"#### 🏭 {get_text('product_stats')}")
                # 제품 카테고리별 통계 (간단히)
                st.metric(get_text("total_quotations"), product_count)
            
            with col4:
                st.markdown(f"#### 📈 {get_text('business_health')}")
                # 전체 업무 효율성
                if employee_count > 0:
                    work_efficiency = round((working_employees / employee_count) * 100, 1) if employee_count > 0 else 0
                else:
                    work_efficiency = 0
                st.metric(get_text("completion_rate"), f"{work_efficiency}%")
            
            st.markdown("---")
            
            # 추가 상세 통계
            st.subheader(f"📈 {get_text('additional_stats')}")
            
            # 두 번째 통계 줄
            col5, col6, col7, col8 = st.columns(4)
            
            # 공급업체 수 계산
            supplier_count = 0
            supplier_manager = managers.get('supplier_manager')
            if supplier_manager:
                try:
                    suppliers = supplier_manager.get_all_suppliers()
                    supplier_count = len(suppliers) if len(suppliers) > 0 else 0
                except:
                    supplier_count = 0
            
            # 승인 대기 수 계산
            pending_approvals = 0
            approval_manager = managers.get('approval_manager')
            if approval_manager:
                try:
                    pending_requests = approval_manager.get_pending_requests()
                    pending_approvals = len(pending_requests) if len(pending_requests) > 0 else 0
                except:
                    pending_approvals = 0
            
            # 재직 직원 수 계산
            active_employees = 0
            employee_manager = managers.get('employee_manager')
            if employee_manager:
                try:
                    employees = employee_manager.get_all_employees()
                    if len(employees) > 0 and 'work_status' in employees.columns:
                        active_employees = (employees['work_status'] == '재직').sum()
                    else:
                        active_employees = employee_count
                except:
                    active_employees = 0
            
            # 판매 제품 수 계산
            sales_products = 0
            sales_product_manager = managers.get('sales_product_manager')
            if sales_product_manager:
                try:
                    sales_data = sales_product_manager.get_all_prices()
                    sales_products = len(sales_data) if len(sales_data) > 0 else 0
                except:
                    sales_products = 0
            
            with col5:
                st.info(f"**🏭 {get_text('supplier_count_label')}**")
                st.metric(label=get_text("registered_suppliers"), value=supplier_count)
            
            with col6:
                st.warning(f"**⏳ {get_text('pending_approvals_label')}**")
                st.metric(label=get_text("pending_count"), value=pending_approvals)
            
            with col7:
                st.success(f"**👨‍💼 {get_text('active_employees_label')}**")
                st.metric(label=get_text("currently_working"), value=active_employees)
            
            with col8:
                st.info(f"**💰 {get_text('sales_products_label')}**")
                st.metric(label=get_text("priced_products"), value=sales_products)
            
            st.markdown("---")
            
            # 서브메뉴별 안내
            if selected_submenu == "전체 현황":
                st.info(f"💡 {get_text('dashboard_info_overview')}")
            elif selected_submenu == "직원 통계":
                st.info(f"💡 {get_text('dashboard_info_employee')}")
            elif selected_submenu == "고객 통계":
                st.info(f"💡 {get_text('dashboard_info_customer')}")
            elif selected_submenu == "매출 현황":
                st.info(f"💡 {get_text('dashboard_info_sales')}")
            elif selected_submenu == "승인 대기":
                st.info(f"💡 {get_text('dashboard_info_approval')}")
            elif selected_submenu == "최근 활동":
                st.info(f"💡 {get_text('dashboard_info_activity')}")
                
        except Exception as e:
            st.error(f"대시보드 로딩 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("📊 데이터를 로드하려면 위의 버튼을 클릭하세요.")

def show_employee_dashboard(managers, selected_submenu, get_text):
    """직원 관리 대시보드"""
    st.subheader("📊 직원 관리 현황")
    
    employee_manager = managers.get('employee_manager')
    if not employee_manager:
        st.error("직원 매니저가 로드되지 않았습니다.")
        return
    
    try:
        # 직원 통계
        employees = employee_manager.get_all_employees()
        if len(employees) > 0:
            # DataFrame에서 재직 직원 수 계산
            if 'work_status' in employees.columns:
                work_status_mask = employees['work_status'] == '재직'
                active_count = work_status_mask.sum()
            else:
                active_count = len(employees)
            total_count = len(employees)
        else:
            active_count = 0
            total_count = 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 직원 수", total_count, help="등록된 전체 직원 수")
        with col2:
            st.metric("재직 직원 수", active_count, help="현재 재직 중인 직원 수")
        
        st.markdown("---")
        st.subheader("🎯 주요 업무")
        
        # 서브메뉴 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs([
            get_text("employee_list"), 
            get_text("employee_registration"), 
            get_text("employee_edit"), 
            get_text("employee_statistics")
        ])
        
        with tab1:
            st.info("💡 전체 직원 목록을 확인하고 검색할 수 있습니다.")
            if st.button(f"{get_text('employee_list')}으로 이동", key="goto_employee_list"):
                st.session_state.selected_submenu = get_text("employee_list")
                st.rerun()
        
        with tab2:
            st.info("💡 새로운 직원을 등록할 수 있습니다.")
            if st.button(f"{get_text('employee_registration')}으로 이동", key="goto_employee_register"):
                st.session_state.selected_submenu = get_text("employee_registration")
                st.rerun()
        
        with tab3:
            st.info("💡 기존 직원의 정보를 수정할 수 있습니다.")
            if st.button(f"{get_text('employee_edit')}으로 이동", key="goto_employee_edit"):
                st.session_state.selected_submenu = get_text("employee_edit")
                st.rerun()
        
        with tab4:
            st.info("💡 직원 현황을 지역별, 직급별로 분석할 수 있습니다.")
            if st.button(f"{get_text('employee_statistics')}으로 이동", key="goto_employee_stats"):
                st.session_state.selected_submenu = get_text("employee_statistics")
                st.rerun()
    
    except Exception as e:
        st.error(f"직원 대시보드 로딩 중 오류가 발생했습니다: {str(e)}")

def show_customer_dashboard(managers, selected_submenu, get_text):
    """고객 관리 대시보드"""
    st.subheader("📊 고객 관리 현황")
    
    customer_manager = managers.get('customer_manager')
    if not customer_manager:
        st.error("고객 매니저가 로드되지 않았습니다.")
        return
    
    try:
        # 고객 통계
        customers = customer_manager.get_all_customers()
        customer_count = len(customers) if len(customers) > 0 else 0
        
        st.metric("총 고객 수", customer_count, help="등록된 전체 고객 수")
        
        st.markdown("---")
        st.subheader("🎯 주요 업무")
        
        # 서브메뉴 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs([
            get_text("customer_list"), 
            get_text("customer_registration"), 
            get_text("customer_edit"), 
            get_text("customer_statistics")
        ])
        
        with tab1:
            st.info("💡 전체 고객 목록을 확인하고 검색할 수 있습니다.")
            if st.button(f"{get_text('customer_list')}으로 이동", key="goto_customer_list"):
                st.session_state.selected_submenu = get_text("customer_list")
                st.rerun()
        
        with tab2:
            st.info("💡 새로운 고객을 등록하고 KAM 정보를 설정할 수 있습니다.")
            if st.button(f"{get_text('customer_registration')}으로 이동", key="goto_customer_register"):
                st.session_state.selected_submenu = get_text("customer_registration")
                st.rerun()
        
        with tab3:
            st.info("💡 기존 고객의 정보와 KAM 데이터를 수정할 수 있습니다.")
            if st.button(f"{get_text('customer_edit')}으로 이동", key="goto_customer_edit"):
                st.session_state.selected_submenu = get_text("customer_edit")
                st.rerun()
        
        with tab4:
            st.info("💡 고객 현황을 지역별, 업종별로 분석할 수 있습니다.")
            if st.button(f"{get_text('customer_statistics')}으로 이동", key="goto_customer_stats"):
                st.session_state.selected_submenu = get_text("customer_statistics")
                st.rerun()
    
    except Exception as e:
        st.error(f"고객 대시보드 로딩 중 오류가 발생했습니다: {str(e)}")

def show_product_dashboard(managers, selected_submenu, get_text):
    """제품 관리 대시보드"""
    st.subheader("📊 제품 관리 현황")
    
    product_manager = managers.get('product_manager')
    if not product_manager:
        st.error("제품 매니저가 로드되지 않았습니다.")
        return
    
    try:
        # 제품 통계
        products = product_manager.get_all_products()
        product_count = len(products) if len(products) > 0 else 0
        
        st.metric("총 제품 수", product_count, help="등록된 전체 제품 수")
        
        st.markdown("---")
        st.subheader("🎯 주요 업무")
        
        # 서브메뉴 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs(["제품 목록", "제품 등록", "제품 편집", "제품 통계"])
        
        with tab1:
            st.info("💡 전체 제품 목록을 확인하고 검색할 수 있습니다.")
            if st.button("제품 목록으로 이동", key="goto_product_list"):
                st.session_state.selected_submenu = "제품 목록"
                st.rerun()
        
        with tab2:
            st.info("💡 새로운 제품을 등록하고 다국어 정보를 설정할 수 있습니다.")
            if st.button("제품 등록으로 이동", key="goto_product_register"):
                st.session_state.selected_submenu = "제품 등록"
                st.rerun()
        
        with tab3:
            st.info("💡 기존 제품의 정보와 사양을 수정할 수 있습니다.")
            if st.button("제품 편집으로 이동", key="goto_product_edit"):
                st.session_state.selected_submenu = "제품 편집"
                st.rerun()
        
        with tab4:
            st.info("💡 제품 현황을 카테고리별, 공급업체별로 분석할 수 있습니다.")
            if st.button("제품 통계로 이동", key="goto_product_stats"):
                st.session_state.selected_submenu = "제품 통계"
                st.rerun()
    
    except Exception as e:
        st.error(f"제품 대시보드 로딩 중 오류가 발생했습니다: {str(e)}")



def show_supplier_dashboard(managers, selected_submenu, get_text):
    """공급업체 관리 대시보드"""
    st.subheader("📊 공급업체 관리 현황")
    
    supplier_manager = managers.get('supplier_manager')
    if not supplier_manager:
        st.error("공급업체 매니저가 로드되지 않았습니다.")
        return
    
    try:
        # 공급업체 통계
        suppliers = supplier_manager.get_all_suppliers()
        supplier_count = len(suppliers) if len(suppliers) > 0 else 0
        
        st.metric("총 공급업체 수", supplier_count, help="등록된 전체 공급업체 수")
        
        st.markdown("---")
        st.subheader("🎯 주요 업무")
        
        # 서브메뉴 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs(["공급업체 목록", "공급업체 등록", "공급업체 편집", "공급업체 통계"])
        
        with tab1:
            st.info("💡 전체 공급업체 목록을 확인하고 연락처를 조회할 수 있습니다.")
            if st.button("공급업체 목록으로 이동", key="goto_supplier_list"):
                st.session_state.selected_submenu = "공급업체 목록"
                st.rerun()
        
        with tab2:
            st.info("💡 새로운 공급업체를 등록하고 계약 정보를 설정할 수 있습니다.")
            if st.button("공급업체 등록으로 이동", key="goto_supplier_register"):
                st.session_state.selected_submenu = "공급업체 등록"
                st.rerun()
        
        with tab3:
            st.info("💡 기존 공급업체의 정보와 계약 조건을 수정할 수 있습니다.")
            if st.button("공급업체 편집으로 이동", key="goto_supplier_edit"):
                st.session_state.selected_submenu = "공급업체 편집"
                st.rerun()
        
        with tab4:
            st.info("💡 공급업체 현황을 지역별, 유형별로 분석할 수 있습니다.")
            if st.button("공급업체 통계로 이동", key="goto_supplier_stats"):
                st.session_state.selected_submenu = "공급업체 통계"
                st.rerun()
    
    except Exception as e:
        st.error(f"공급업체 대시보드 로딩 중 오류가 발생했습니다: {str(e)}")

def show_sales_product_dashboard(managers, selected_submenu, get_text):
    """판매 제품 관리 대시보드"""
    st.subheader("📊 판매 제품 관리 현황")
    
    sales_product_manager = managers.get('sales_product_manager')
    if not sales_product_manager:
        st.error("판매 제품 매니저가 로드되지 않았습니다.")
        return
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "표준 판매가 관리":
        st.info("💡 제품별 판매 가격을 설정하고 관리할 수 있습니다.")
    elif selected_submenu == "가격 설정":
        st.info("💡 새로운 제품의 판매 가격을 등록할 수 있습니다.")
    elif selected_submenu == "가격 분석":
        st.info("💡 가격 변동과 수익성을 분석할 수 있습니다.")
    elif selected_submenu == "가격 히스토리":
        st.info("💡 과거 가격 변동 이력을 확인할 수 있습니다.")
    elif selected_submenu == "환율 적용":
        st.info("💡 환율 변동에 따른 가격 조정을 관리할 수 있습니다.")

def show_supply_product_dashboard(managers, selected_submenu, get_text):
    """외주 공급가 관리 대시보드"""
    st.subheader("📊 외주 공급가 관리 현황")
    
    supply_product_manager = managers.get('supply_product_manager')
    if not supply_product_manager:
        st.error("외주 공급가 매니저가 로드되지 않았습니다.")
        return
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "외주 공급가 관리":
        st.info("💡 MB 제품의 외주 공급가를 설정하고 관리할 수 있습니다.")
    elif selected_submenu == "공급가 설정":
        st.info("💡 새로운 MB 제품의 공급가를 등록할 수 있습니다.")
    elif selected_submenu == "공급가 분석":
        st.info("💡 공급가 변동과 비용 효율성을 분석할 수 있습니다.")
    elif selected_submenu == "공급가 히스토리":
        st.info("💡 과거 공급가 변동 이력을 확인할 수 있습니다.")
    elif selected_submenu == "공급업체별 가격":
        st.info("💡 공급업체별 가격 비교와 협상 내역을 관리할 수 있습니다.")

def show_contract_dashboard(managers, selected_submenu, get_text):
    """계약서 현황 관리 대시보드"""
    st.subheader("📊 계약서 현황 관리")
    st.info("🚧 계약서 현황 관리 시스템")
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "계약서 현황":
        st.info("💡 전체 계약서 현황을 확인하고 만료 예정 계약을 관리할 수 있습니다.")
    elif selected_submenu == "계약서 등록":
        st.info("💡 새로운 계약서를 등록하고 계약 조건을 설정할 수 있습니다.")
    elif selected_submenu == "계약서 관리":
        st.info("💡 기존 계약서를 검색, 수정, 삭제할 수 있습니다.")
    elif selected_submenu == "만료 알림":
        st.info("💡 계약 만료 예정 알림을 확인하고 갱신을 관리할 수 있습니다.")
    elif selected_submenu == "계약서 통계":
        st.info("💡 계약서 현황과 통계를 분석할 수 있습니다.")

def show_exchange_rate_dashboard(managers, selected_submenu, get_text):
    """환율 관리 대시보드 (한국은행 기준 수동 입력)"""
    st.subheader("📊 환율 관리 현황")
    
    exchange_rate_manager = managers.get('exchange_rate_manager')
    if not exchange_rate_manager:
        st.error("환율 매니저가 로드되지 않았습니다.")
        return
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "환율 관리":
        st.info("💡 실시간 환율 정보를 확인하고 업데이트할 수 있습니다.")
    elif selected_submenu == "환율 업데이트":
        st.info("💡 최신 환율을 가져오고 수동으로 조정할 수 있습니다.")
    elif selected_submenu == "환율 통계":
        st.info("💡 환율 변동 추이와 통계를 분석할 수 있습니다.")
    elif selected_submenu == "환율 검색":
        st.info("💡 특정 기간의 환율 정보를 검색할 수 있습니다.")
    elif selected_submenu == "환율 분석":
        st.info("💡 환율 변동이 가격에 미치는 영향을 분석할 수 있습니다.")
    elif selected_submenu == "환율 히스토리":
        st.info("💡 과거 환율 변동 이력과 트렌드를 확인할 수 있습니다.")

def show_business_process_dashboard(managers, selected_submenu, get_text):
    """비즈니스 프로세스 관리 대시보드"""
    st.subheader("📊 비즈니스 프로세스 관리 현황")
    
    business_process_manager = managers.get('business_process_manager')
    if not business_process_manager:
        st.error("비즈니스 프로세스 매니저가 로드되지 않았습니다.")
        return
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "비즈니스 프로세스 관리":
        st.info("💡 전체 비즈니스 프로세스와 워크플로우를 관리할 수 있습니다.")
    elif selected_submenu == "워크플로우 생성":
        st.info("💡 새로운 업무 워크플로우를 생성하고 설정할 수 있습니다.")
    elif selected_submenu == "워크플로우 편집":
        st.info("💡 기존 워크플로우의 단계와 설정을 수정할 수 있습니다.")
    elif selected_submenu == "워크플로우 통계":
        st.info("💡 워크플로우 실행 현황과 효율성을 분석할 수 있습니다.")
    elif selected_submenu == "진행 상황 관리":
        st.info("💡 현재 진행 중인 업무의 상태를 추적하고 관리할 수 있습니다.")

def show_shipping_dashboard(managers, selected_submenu, get_text):
    """배송 관리 대시보드"""
    st.subheader("📊 배송 관리 현황")
    st.info("🚧 배송 관리 시스템은 개발 중입니다.")
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "배송 관리":
        st.info("💡 전체 배송 현황을 확인하고 관리할 수 있습니다.")
    elif selected_submenu == "배송 등록":
        st.info("💡 새로운 배송을 등록하고 추적 정보를 설정할 수 있습니다.")
    elif selected_submenu == "배송 편집":
        st.info("💡 기존 배송 정보를 수정할 수 있습니다.")
    elif selected_submenu == "배송 통계":
        st.info("💡 배송 현황과 통계를 분석할 수 있습니다.")
    elif selected_submenu == "배송 추적":
        st.info("💡 배송 상태를 추적하고 확인할 수 있습니다.")
    elif selected_submenu == "배송 검색":
        st.info("💡 배송 정보를 검색하고 필터링할 수 있습니다.")

def show_quotation_dashboard(managers, selected_submenu, get_text):
    """견적 관리 대시보드 - 새 시스템으로 리디렉션"""
    from pages.quotation_page import main as show_quotation_page
    show_quotation_page()

def show_approval_dashboard(managers, selected_submenu, get_text):
    """승인 관리 대시보드"""
    st.subheader("📊 승인 관리 현황")
    
    approval_manager = managers.get('approval_manager')
    if not approval_manager:
        st.error("승인 매니저가 로드되지 않았습니다.")
        return
    
    try:
        # 승인 통계
        pending_requests = approval_manager.get_pending_requests()
        pending_count = len(pending_requests) if len(pending_requests) > 0 else 0
        st.metric("대기 중인 승인", pending_count, help="현재 승인 대기 중인 요청 수")
    except:
        st.warning("승인 데이터를 불러올 수 없습니다.")
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["승인 관리", "승인 대기", "승인 통계", "승인 검색"])
    
    with tab1:
        st.info("💡 전체 승인 요청을 확인하고 처리할 수 있습니다.")
        if st.button("승인 관리로 이동", key="goto_approval_management"):
            st.session_state.selected_submenu = "승인 관리"
            st.rerun()
    
    with tab2:
        st.info("💡 승인 대기 중인 요청을 우선적으로 처리할 수 있습니다.")
        if st.button("승인 대기로 이동", key="goto_approval_pending"):
            st.session_state.selected_submenu = "승인 대기"
            st.rerun()
    
    with tab3:
        st.info("💡 승인 현황과 통계를 분석할 수 있습니다.")
        if st.button("승인 통계로 이동", key="goto_approval_stats"):
            st.session_state.selected_submenu = "승인 통계"
            st.rerun()
    
    with tab4:
        st.info("💡 승인 요청을 검색하고 필터링할 수 있습니다.")
        if st.button("승인 검색으로 이동", key="goto_approval_search"):
            st.session_state.selected_submenu = "승인 검색"
            st.rerun()

def show_order_dashboard(managers, selected_submenu, get_text):
    """주문 관리 대시보드"""
    from pages.order_page import show_order_page
    
    # 필요한 매니저들 추출
    order_manager = managers.get('order_manager')
    quotation_manager = managers.get('quotation_manager')
    customer_manager = managers.get('customer_manager')
    
    if not all([order_manager, quotation_manager, customer_manager]):
        st.error("주문 관리에 필요한 시스템 구성요소를 불러올 수 없습니다.")
        return
    
    show_order_page(order_manager, quotation_manager, customer_manager, None, get_text)

def show_cash_flow_dashboard(managers, selected_submenu, get_text):
    """현금 흐름 관리 대시보드"""
    st.subheader("📊 현금 흐름 관리 현황")
    st.info("🚧 현금 흐름 관리 시스템은 개발 중입니다.")
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "현금 흐름 관리":
        st.info("💡 전체 현금 흐름을 확인하고 관리할 수 있습니다.")
    elif selected_submenu == "현금 흐름 등록":
        st.info("💡 새로운 현금 흐름 거래를 등록할 수 있습니다.")
    elif selected_submenu == "현금 흐름 편집":
        st.info("💡 기존 현금 흐름 데이터를 수정할 수 있습니다.")
    elif selected_submenu == "현금 흐름 통계":
        st.info("💡 현금 흐름 현황과 통계를 분석할 수 있습니다.")
    elif selected_submenu == "현금 흐름 분석":
        st.info("💡 현금 흐름 패턴과 트렌드를 분석할 수 있습니다.")
    elif selected_submenu == "현금 흐름 검색":
        st.info("💡 현금 흐름 거래를 검색하고 필터링할 수 있습니다.")

def show_pdf_design_dashboard(managers, selected_submenu, get_text):
    """PDF 디자인 관리 대시보드"""
    st.subheader("📊 PDF 디자인 관리 현황")
    
    pdf_design_manager = managers.get('pdf_design_manager')
    if not pdf_design_manager:
        st.error("PDF 디자인 매니저가 로드되지 않았습니다.")
        return
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "PDF 템플릿 편집":
        st.info("💡 견적서 PDF 템플릿의 디자인과 레이아웃을 편집할 수 있습니다.")
    elif selected_submenu == "PDF 미리보기":
        st.info("💡 편집한 템플릿의 실제 모습을 미리 확인할 수 있습니다.")
    elif selected_submenu == "PDF 설정":
        st.info("💡 PDF 생성 관련 설정을 관리할 수 있습니다.")
    elif selected_submenu == "PDF 생성":
        st.info("💡 PDF 문서를 생성하고 다운로드할 수 있습니다.")
    elif selected_submenu == "PDF 다운로드":
        st.info("💡 생성된 PDF 파일을 다운로드할 수 있습니다.")
    elif selected_submenu == "PDF 관리":
        st.info("💡 PDF 파일과 템플릿을 관리할 수 있습니다.")

def show_system_guide_dashboard(managers, selected_submenu, get_text):
    """시스템 가이드 대시보드"""
    st.subheader("📚 시스템 가이드")
    
    st.markdown("""
    ### 🔍 시스템 정보
    - **버전**: 금도((金道)) Geumdo [ Golden Way ]
    - **언어 지원**: 한국어, English, Tiếng Việt
    - **통화 지원**: VND, USD, KRW, CNY, THB, IDR
    - **주요 기능**: 16개 통합 관리 모듈
    """)
    
    st.markdown("---")
    st.subheader("🎯 주요 가이드")
    
    # 서브메뉴별 안내
    if selected_submenu == "시스템 개요":
        st.info("💡 금도((金道)) Geumdo [ Golden Way ] 시스템의 전체 구조와 기능을 소개합니다.")
    elif selected_submenu == "사용자 가이드":
        st.info("💡 각 기능별 상세한 사용 방법을 설명합니다.")
    elif selected_submenu == "기능 설명":
        st.info("💡 모든 메뉴와 기능에 대한 상세 설명을 제공합니다.")
    elif selected_submenu == "FAQ":
        st.info("💡 자주 묻는 질문과 답변을 확인할 수 있습니다.")
    elif selected_submenu == "업데이트 내역":
        st.info("💡 시스템 업데이트 이력과 변경사항을 확인할 수 있습니다.")
    elif selected_submenu == "문의하기":
        st.info("💡 기술 지원 문의와 피드백을 보낼 수 있습니다.")

def show_personal_status_dashboard(managers, selected_submenu, get_text):
    """개인 상태 관리 대시보드"""
    st.subheader("👤 개인 상태 관리")
    
    vacation_manager = managers.get('vacation_manager')
    approval_manager = managers.get('approval_manager')
    
    # 개인 통계 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**📅 연차 현황**")
        st.metric(label="사용/총 연차", value="0/15")
    
    with col2:
        st.warning("**📋 승인 요청**")
        st.metric(label="대기 중인 요청", value=0)
    
    st.markdown("---")
    st.subheader("🎯 주요 업무")
    
    # 서브메뉴별 안내
    if selected_submenu == "개인 상태 조회":
        st.info("💡 개인의 근무 현황과 휴가 정보를 확인할 수 있습니다.")
    elif selected_submenu == "휴가 신청":
        st.info("💡 연차, 병가, 경조사 등의 휴가를 신청할 수 있습니다.")
    elif selected_submenu == "개인정보 수정 요청":
        st.info("💡 개인정보 변경이 필요할 때 승인 요청을 보낼 수 있습니다.")
    elif selected_submenu == "비밀번호 변경":
        st.info("💡 로그인 비밀번호를 변경할 수 있습니다.")
    elif selected_submenu == "내 요청 내역":
        st.info("💡 과거 신청한 휴가 및 승인 요청 내역을 확인할 수 있습니다.")
    elif selected_submenu == "개인 통계":
        st.info("💡 개인의 활동 통계와 현황을 확인할 수 있습니다.")

def show_finished_product_dashboard(managers, selected_submenu, get_text):
    """완성품 관리 대시보드"""
    st.subheader("📊 완성품 관리 현황")
    
    finished_product_manager = managers.get('finished_product_manager')
    if not finished_product_manager:
        st.error("완성품 매니저가 로드되지 않았습니다.")
        return
    
    try:
        finished_products = finished_product_manager.get_all_finished_products()
        
        if not finished_products.empty:
            # 통계 표시
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 완성품", len(finished_products))
            with col2:
                active_products = len(finished_products[finished_products['status'] == 'active'])
                st.metric("활성 제품", active_products)
            with col3:
                price_set = len(finished_products.dropna(subset=['selling_price_vnd']))
                st.metric("가격 설정 완료", price_set)
            with col4:
                categories = finished_products['category'].dropna().nunique()
                st.metric("카테고리", categories)
            
            st.markdown("---")
            st.subheader("🎯 주요 업무")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("➕ 새 완성품 등록", use_container_width=True):
                    st.session_state.selected_system = "finished_product_management"
                    st.rerun()
            
            with col_b:
                if st.button("💰 가격 관리", use_container_width=True):
                    st.session_state.selected_system = "finished_product_management"
                    st.rerun()
            
            with col_c:
                if st.button("🔍 완성품 조회", use_container_width=True):
                    st.session_state.selected_system = "finished_product_management"
                    st.rerun()
                    
            # 최근 등록 완성품
            st.subheader("📋 최근 등록 완성품")
            recent_products = finished_products.head(5)
            display_cols = ['product_code', 'product_name_ko', 'category', 'selling_price_vnd']
            available_cols = [col for col in display_cols if col in recent_products.columns]
            
            if available_cols:
                display_df = recent_products[available_cols].copy()
                if 'selling_price_vnd' in display_df.columns:
                    display_df['selling_price_vnd'] = display_df['selling_price_vnd'].apply(
                        lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "-"
                    )
                display_df.columns = ['제품코드', '제품명', '카테고리', '판매가(VND)']
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("📢 등록된 완성품이 없습니다.")
            st.markdown("""
            ### 🎯 완성품 관리 시작하기
            완성품 관리는 견적서, 발주서, 출고 확인서에 사용되는 **완성된 제품 코드**를 관리합니다.
            
            **주요 기능:**
            - ✅ 완성품 코드별 관리 (예: HR-OP-CP-CC-10-00)
            - 💰 다화폐 가격 관리 (VND/USD)
            - 🌐 다국어 제품명 지원
            - 📄 문서 연동 (견적서/발주서/출고확인서)
            """)
            
            if st.button("🚀 첫 완성품 등록하기", use_container_width=True):
                st.session_state.selected_system = "finished_product_management"
                st.rerun()
                
    except Exception as e:
        st.error(f"완성품 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")

def show_product_registration_dashboard(managers, selected_submenu, get_text):
    """통합 제품 등록 대시보드"""
    st.subheader("📊 제품 등록 현황")
    
    master_product_manager = managers.get('master_product_manager')
    finished_product_manager = managers.get('finished_product_manager')
    product_code_manager = managers.get('product_code_manager')
    
    try:
        # 각 DB에서 데이터 조회
        master_count = 0
        finished_count = 0
        code_count = 0
        
        if master_product_manager:
            master_products = master_product_manager.get_all_products()
            master_count = len(master_products) if not master_products.empty else 0
        
        if finished_product_manager:
            finished_products = finished_product_manager.get_all_finished_products()
            finished_count = len(finished_products) if not finished_products.empty else 0
        
        if product_code_manager:
            product_codes = product_code_manager.get_all_codes()
            code_count = len(product_codes) if not product_codes.empty else 0
        
        # 통계 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("마스터 제품", master_count)
        with col2:
            st.metric("완성품", finished_count)
        with col3:
            st.metric("제품 코드", code_count)
        with col4:
            total_products = master_count + finished_count
            st.metric("총 제품", total_products)
        
        st.markdown("---")
        st.subheader("🎯 주요 업무")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("➕ 새 제품 등록", use_container_width=True):
                st.session_state.selected_system = "product_registration"
                st.rerun()
        
        with col_b:
            if st.button("🔧 제품 관리", use_container_width=True):
                st.session_state.selected_system = "product_registration"
                st.rerun()
        
        with col_c:
            if st.button("🔍 제품 조회", use_container_width=True):
                st.session_state.selected_system = "product_registration"
                st.rerun()
        
        # 시스템 안내
        st.markdown("### 🎯 통합 제품 등록 시스템")
        st.markdown("""
        **주요 기능:**
        - 🎯 **마스터 제품**: 기본 제품 정보와 가격 관리
        - ✅ **완성품**: 견적서/발주서용 완성 제품 관리
        - 🔧 **제품 코드**: HR-XX-XX-XX-XX-XX 형식 코드 생성 및 관리
        - 🔗 **DB 연동**: 제품 코드 DB와 연결하여 추가 정보 입력 가능
        """)
        
        if total_products == 0:
            st.info("📢 등록된 제품이 없습니다. 첫 제품을 등록해보세요!")
            
            if st.button("🚀 첫 제품 등록하기", use_container_width=True):
                st.session_state.selected_system = "product_registration"
                st.rerun()
                
    except Exception as e:
        st.error(f"제품 등록 대시보드 로딩 중 오류가 발생했습니다: {str(e)}")
