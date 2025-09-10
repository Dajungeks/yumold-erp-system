import streamlit as st
import pandas as pd
from datetime import datetime
import io
from utils.display_helper import display_product_table

def show_product_page(product_manager, supplier_manager, product_code_manager, user_permissions, get_text):
    """제품 관리 페이지 - 탭 기반 UI"""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'product_management', get_text)
    
    # 탭 생성
    tab_names = [
        f"📦 {get_text('product_list')}", 
        f"➕ {get_text('product_registration')}", 
        f"✏️ {get_text('product_edit')}", 
        f"📊 {get_text('product_statistics')}", 
        f"🔧 {get_text('product_code_management')}", 
        f"📤 {get_text('bulk_product_operations')}"
    ]
    
    # 탭 컨테이너 생성
    tabs = st.tabs(tab_names)
    
    # 각 탭의 내용 구현
    with tabs[0]:  # 제품 목록
        show_product_list(product_manager, get_text)
    
    with tabs[1]:  # 제품 등록
        show_product_registration(product_manager, supplier_manager, get_text)
    
    with tabs[2]:  # 제품 수정
        show_product_edit(product_manager, supplier_manager, get_text)
    
    with tabs[3]:  # 제품 통계
        show_product_statistics(product_manager, get_text)
    
    with tabs[4]:  # 제품 코드 관리
        show_product_code_management(product_code_manager, get_text)
    
    with tabs[5]:  # 대량 작업
        show_product_bulk_operations(product_manager, get_text)

def show_product_list(product_manager, get_text=lambda x: x):
    """제품 목록 표시"""
    st.header("📦 제품 목록")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ["전체"] + product_manager.get_categories()
        category_filter = st.selectbox("카테고리 필터", categories)
    
    with col2:
        suppliers = ["전체"] + product_manager.get_suppliers()
        supplier_filter = st.selectbox("공급업체 필터", suppliers)
    
    with col3:
        search_term = st.text_input("검색 (제품명, 제품코드)")
    
    # 필터 적용
    category_filter = None if category_filter == "전체" else category_filter
    supplier_filter = None if supplier_filter == "전체" else supplier_filter
    
    filtered_products = product_manager.get_filtered_products(
        category_filter=category_filter,
        supplier_filter=supplier_filter,
        search_term=search_term
    )
    
    if len(filtered_products) > 0:
        # 통합 테이블 표시 함수 사용
        display_product_table(filtered_products)
    else:
        st.warning("조건에 맞는 제품이 없습니다.")

def show_product_registration(product_manager, supplier_manager, get_text=lambda x: x):
    """제품 등록 폼 표시"""
    st.header("➕ 제품 등록")
    
    with st.form("product_registration_form"):
        st.subheader("📦 기본 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            product_name_ko = st.text_input("제품명 (한국어) *")
            product_name_en = st.text_input("제품명 (영어)")
            product_name_vi = st.text_input("제품명 (베트남어)")
            
            # 표준 카테고리 구조 적용
            main_categories = ['MB', 'HRC', 'HR', 'MB+HR', 'ROBOT', 'SPARE-HR', 'SPARE-MB', 'SPARE-ROBOT', 'SERVICE']
            main_category = st.selectbox("메인 카테고리 *", main_categories)
            
        with col2:
            # 공급업체 선택
            suppliers_df = supplier_manager.get_all_suppliers()
            if len(suppliers_df) > 0:
                supplier_options = [(row['supplier_name'], row['supplier_id']) for _, row in suppliers_df.iterrows()]
                supplier_names = ["선택하세요"] + [name for name, _ in supplier_options]
                selected_supplier_name = st.selectbox("공급업체 *", supplier_names)
                if selected_supplier_name != "선택하세요":
                    selected_supplier_id = next(id for name, id in supplier_options if name == selected_supplier_name)
                else:
                    selected_supplier_id = ""
                    selected_supplier_name = ""
            else:
                st.warning("등록된 공급업체가 없습니다.")
                selected_supplier_id = ""
                selected_supplier_name = ""
            
            specifications = st.text_area("규격 및 사양")
        
        st.subheader("📋 세부 카테고리")
        
        # MB 카테고리 처리
        if main_category == 'MB':
            col3, col4 = st.columns(2)
            with col3:
                sub_category_mb = st.selectbox("MB 서브카테고리", ['2P', '3P', 'HR'], key='mb_sub')
            with col4:
                mb_materials = ['SS400', 'S50C', 'SKD61', 'NAK80', 'P20', 'SCM440', 'FC300', 'A5052', 'STAVAX', 'HPM38']
                sub_category_mb_material = st.selectbox("MB 재질", mb_materials, key='mb_material')
        
        # HRC 카테고리 처리 (HR과 동일한 selectbox 방식)
        elif main_category == 'HRC':
            from product_category_config_manager import ProductCategoryConfigManager
            config_manager = ProductCategoryConfigManager()
            
            col3, col4 = st.columns(2)
            with col3:
                # HRC Type 선택
                hrc_types = config_manager.get_hrc_types()
                selected_hrc_type = st.selectbox("HRC Type", [""] + hrc_types, key='hrc_type')
                
                # 제품 타입 선택
                if selected_hrc_type:
                    product_types = config_manager.get_hrc_product_types(selected_hrc_type)
                    selected_product_type = st.selectbox("제품 타입", [""] + product_types, key='hrc_product_type')
                else:
                    selected_product_type = st.selectbox("제품 타입", [""], disabled=True, key='hrc_product_type_disabled')
            
            with col4:
                # 모델 타입 선택
                if selected_hrc_type and selected_product_type:
                    model_types = config_manager.get_hrc_model_types(selected_hrc_type, selected_product_type)
                    selected_model_type = st.selectbox("모델 타입", [""] + model_types, key='hrc_model_type')
                else:
                    selected_model_type = st.selectbox("모델 타입", [""], disabled=True, key='hrc_model_type_disabled')
                
                # 존 번호 선택
                zones = config_manager.get_hrc_zones()
                selected_zone = st.selectbox("존 번호", [""] + zones, key='hrc_zone')
            
            # HRC 구성 요소들을 하나의 문자열로 결합
            hrc_components = []
            if selected_hrc_type:
                hrc_components.append(selected_hrc_type)
            if selected_product_type:
                hrc_components.append(selected_product_type)
            if selected_model_type:
                hrc_components.append(selected_model_type)
            if selected_zone:
                hrc_components.append(f"Zone{selected_zone}")
            sub_category_hrc = "-".join(hrc_components) if hrc_components else ""
        
        # HR 카테고리 처리 
        elif main_category == 'HR':
            from product_category_config_manager import ProductCategoryConfigManager
            config_manager = ProductCategoryConfigManager()
            
            col3, col4 = st.columns(2)
            with col3:
                # System Type 선택
                system_types = config_manager.get_hr_system_types()
                selected_system_type = st.selectbox("System Type", [""] + system_types, key='hr_system_type')
                
                # Gate Type 선택
                if selected_system_type:
                    product_types = config_manager.get_hr_product_types(selected_system_type)
                    selected_product_type = st.selectbox("Product Type", [""] + product_types, key='hr_product_type')
                else:
                    selected_product_type = st.selectbox("Product Type", [""], disabled=True, key='hr_product_type_disabled')
            
            with col4:
                # Gate Type 선택
                if selected_system_type and selected_product_type:
                    gate_types = config_manager.get_hr_gate_types(selected_system_type, selected_product_type)
                    selected_gate_type = st.selectbox("Gate Type", [""] + gate_types, key='hr_gate_type')
                else:
                    selected_gate_type = st.selectbox("Gate Type", [""], disabled=True, key='hr_gate_type_disabled')
                
                # Size 선택
                if selected_system_type and selected_product_type and selected_gate_type:
                    sizes = config_manager.get_hr_sizes(selected_system_type, selected_product_type, selected_gate_type)
                    selected_size = st.selectbox("Size", [""] + sizes, key='hr_size')
                else:
                    selected_size = st.selectbox("Size", [""], disabled=True, key='hr_size_disabled')
            
            # HR 구성 요소들을 하나의 문자열로 결합
            hr_components = []
            if selected_system_type:
                hr_components.append(selected_system_type)
            if selected_product_type:
                hr_components.append(selected_product_type)
            if selected_gate_type:
                hr_components.append(selected_gate_type)
            if selected_size:
                hr_components.append(selected_size)
            sub_category_hr = "-".join(hr_components) if hr_components else ""
        
        # ROBOT 카테고리 처리
        elif main_category == 'ROBOT':
            from product_category_config_manager import ProductCategoryConfigManager
            config_manager = ProductCategoryConfigManager()
            
            col3, col4 = st.columns(2)
            with col3:
                # Application Type 선택
                app_types = [comp['component_key'] for comp in config_manager.get_hr_components_for_management('robot_application')]
                selected_app_type = st.selectbox("Application Type", [""] + app_types, key='robot_app_type')
                
                # Payload 선택
                payloads = [comp['component_key'] for comp in config_manager.get_hr_components_for_management('robot_payload')]
                selected_payload = st.selectbox("Payload (kg)", [""] + payloads, key='robot_payload')
            
            with col4:
                # Reach 선택
                reaches = [comp['component_key'] for comp in config_manager.get_hr_components_for_management('robot_reach')]
                selected_reach = st.selectbox("Reach (mm)", [""] + reaches, key='robot_reach')
                
                # Axes 선택
                axes = [comp['component_key'] for comp in config_manager.get_hr_components_for_management('robot_axes')]
                selected_axes = st.selectbox("Axes", [""] + axes, key='robot_axes')
            
            # Robot 구성 요소들을 하나의 문자열로 결합
            robot_components = []
            if selected_app_type:
                robot_components.append(selected_app_type)
            if selected_payload:
                robot_components.append(f"{selected_payload}kg")
            if selected_reach:
                robot_components.append(f"{selected_reach}mm")
            if selected_axes:
                robot_components.append(f"{selected_axes}axis")
            sub_category_robot = "-".join(robot_components) if robot_components else ""
            
        # 기본값들 설정
        if main_category not in ['MB']:
            sub_category_mb = ""
            sub_category_mb_material = ""
        if main_category not in ['HRC']:
            sub_category_hrc = ""
        if main_category not in ['HR']:
            sub_category_hr = ""
            selected_system_type = ""
            selected_product_type = ""
            selected_gate_type = ""
            selected_size = ""
        if main_category not in ['ROBOT']:
            sub_category_robot = ""
            selected_app_type = ""
            selected_payload = ""
            selected_reach = ""
            selected_axes = ""
        
        st.subheader("📋 추가 정보")
        col5, col6 = st.columns(2)
        
        with col5:
            usage = st.text_area("용도")
            
        with col6:
            notes = st.text_area("비고")
        
        submitted = st.form_submit_button("💾 제품 등록", use_container_width=True, type="primary")
        
        if submitted:
            # 기본값 설정
            if 'sub_category_mb' not in locals():
                sub_category_mb = ''
            if 'sub_category_hrc' not in locals():
                sub_category_hrc = ''
            if 'sub_category_hr' not in locals():
                sub_category_hr = ''
            if 'sub_category_robot' not in locals():
                sub_category_robot = ''
            if 'sub_category_mb_material' not in locals():
                sub_category_mb_material = ''
            
            if not product_name_ko or not main_category:
                st.error("필수 항목을 모두 입력해주세요. (* 표시 항목)")
            else:
                # 공급업체 정보 안전하게 처리
                safe_supplier_id = selected_supplier_id if selected_supplier_id else ""
                safe_supplier_name = selected_supplier_name if selected_supplier_name != "선택하세요" else ""
                
                # HR 구성 요소 개별 저장
                hr_system_type = selected_system_type if main_category == 'HR' and 'selected_system_type' in locals() else ''
                hr_product_type = selected_product_type if main_category == 'HR' and 'selected_product_type' in locals() else ''
                hr_gate_type = selected_gate_type if main_category == 'HR' and 'selected_gate_type' in locals() else ''
                hr_size = selected_size if main_category == 'HR' and 'selected_size' in locals() else ''

                # HRC 구성 요소 개별 저장
                hrc_type = selected_hrc_type if main_category == 'HRC' and 'selected_hrc_type' in locals() else ''
                hrc_product_type_val = selected_product_type if main_category == 'HRC' and 'selected_product_type' in locals() else ''
                hrc_model_type_val = selected_model_type if main_category == 'HRC' and 'selected_model_type' in locals() else ''
                hrc_zone = selected_zone if main_category == 'HRC' and 'selected_zone' in locals() else ''

                # Robot 구성 요소 개별 저장
                robot_app_type = selected_app_type if main_category == 'ROBOT' and 'selected_app_type' in locals() else ''
                robot_payload = selected_payload if main_category == 'ROBOT' and 'selected_payload' in locals() else ''
                robot_reach = selected_reach if main_category == 'ROBOT' and 'selected_reach' in locals() else ''
                robot_axes = selected_axes if main_category == 'ROBOT' and 'selected_axes' in locals() else ''

                product_data = {
                    'product_name': product_name_ko,
                    'product_name_english': product_name_en,
                    'product_name_vietnamese': product_name_vi,
                    'main_category': main_category,
                    'sub_category_mb': sub_category_mb if main_category == 'MB' else '',
                    'sub_category_hrc': sub_category_hrc if main_category == 'HRC' else '',
                    'sub_category_hr': sub_category_hr if main_category == 'HR' else '',
                    'sub_category_robot': sub_category_robot if main_category == 'ROBOT' else '',
                    'sub_category_mb_material': sub_category_mb_material if main_category in ['MB', 'MB+HR', 'SPARE-MB'] else '',
                    'hr_system_type': hr_system_type,
                    'hr_product_type': hr_product_type,
                    'hr_gate_type': hr_gate_type,
                    'hr_size': hr_size,
                    'hrc_type': hrc_type,
                    'hrc_product_type': hrc_product_type_val,
                    'hrc_model_type': hrc_model_type_val,
                    'hrc_zone': hrc_zone,
                    'robot_app_type': robot_app_type,
                    'robot_payload': robot_payload,
                    'robot_reach': robot_reach,
                    'robot_axes': robot_axes,
                    'supplier_id': safe_supplier_id,
                    'supplier_name': safe_supplier_name,
                    'specifications': specifications,
                    'description': usage,
                    'notes': notes
                }
                
                try:
                    product_id = product_manager.add_product(product_data)
                    st.success(f"제품이 성공적으로 등록되었습니다! 제품 ID: {product_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"제품 등록 중 오류가 발생했습니다: {str(e)}")

def show_product_edit(product_manager, supplier_manager, get_text=lambda x: x):
    """제품 편집 페이지"""
    st.header("✏️ 제품 수정")
    
    # Master Product Manager에서 HRC 제품 포함해서 가져오기
    from master_product_manager import MasterProductManager
    master_manager = MasterProductManager()
    
    # 카테고리별 제품 필터링 옵션 추가
    col1, col2 = st.columns(2)
    
    with col1:
        category_filter = st.selectbox("카테고리 필터", ["전체", "MB", "HRC", "HR", "ROBOT", "SERVICE", "SPARE"])
    
    with col2:
        # 검색 기능
        search_term = st.text_input("제품 검색", placeholder="제품명 또는 제품코드 입력")
    
    # 제품 목록 가져오기
    try:
        if category_filter == "전체":
            products_df = master_manager.get_all_products()
        else:
            products_df = master_manager.get_products_by_category(category_filter)
        
        # 검색 필터 적용
        if search_term:
            mask = (products_df['product_name_korean'].str.contains(search_term, case=False, na=False) |
                   products_df['product_code'].str.contains(search_term, case=False, na=False))
            products_df = products_df[mask]
        
        if len(products_df) == 0:
            if category_filter != "전체":
                st.warning(f"{category_filter} 카테고리에 등록된 제품이 없습니다.")
            else:
                st.warning("등록된 제품이 없습니다.")
            return
        
        # 제품 선택 드롭다운 - HRC 제품 포함
        product_options = []
        for _, row in products_df.iterrows():
            product_name = row.get('product_name_korean', row.get('product_name', 'Unknown'))
            product_code = row.get('product_code', 'Unknown')
            category = row.get('main_category', 'Unknown')
            product_options.append(f"[{category}] {product_name} ({product_code})")
        
        selected_product = st.selectbox("수정할 제품 선택", [""] + product_options)
        
    except Exception as e:
        st.error(f"제품 목록 조회 중 오류: {e}")
        return
    
    if selected_product:
        # 선택된 제품 정보 가져오기
        selected_code = selected_product.split("(")[1].split(")")[0]
        product_data = product_manager.get_product_by_code(selected_code)
        
        if product_data:
            with st.form("product_edit_form"):
                st.subheader("📦 기본 정보")
                col1, col2 = st.columns(2)
                
                with col1:
                    product_name_ko = st.text_input("제품명 (한국어) *", value=product_data.get('product_name_ko', ''))
                    product_name_en = st.text_input("제품명 (영어)", value=product_data.get('product_name_en', ''))
                    product_name_vi = st.text_input("제품명 (베트남어)", value=product_data.get('product_name_vi', ''))
                
                with col2:
                    categories = ["HR", "HRC", "Service", "Spare", "Machine", "Tool"]
                    current_category = product_data.get('category1', 'HR')
                    category_index = categories.index(current_category) if current_category in categories else 0
                    category1 = st.selectbox("카테고리1 *", categories, index=category_index)
                    
                    specifications = st.text_area("규격 및 사양", value=product_data.get('specifications', ''))
                
                # 수정 버튼
                submitted = st.form_submit_button("💾 정보 수정", use_container_width=True, type="primary")
                
                if submitted:
                    if not product_name_ko or not category1:
                        st.error("필수 항목을 모두 입력해주세요.")
                    else:
                        updated_data = {
                            'product_name_ko': product_name_ko,
                            'product_name_en': product_name_en,
                            'product_name_vi': product_name_vi,
                            'category1': category1,
                            'specifications': specifications
                        }
                        
                        try:
                            product_manager.update_product(selected_code, updated_data)
                            st.success("제품 정보가 성공적으로 수정되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"제품 정보 수정 중 오류가 발생했습니다: {str(e)}")

def show_product_statistics(product_manager, get_text=lambda x: x):
    """제품 통계 페이지"""
    st.header("📊 제품 통계")
    
    products_df = product_manager.get_all_products()
    if len(products_df) == 0:
        st.warning("통계를 표시할 제품 데이터가 없습니다.")
        return
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 제품 수", len(products_df))
    
    with col2:
        if 'category1' in products_df.columns:
            category_count = products_df['category1'].nunique()
            st.metric("카테고리 수", category_count)
        else:
            st.metric("카테고리 수", "N/A")
    
    with col3:
        if 'supplier_id' in products_df.columns:
            supplier_count = products_df['supplier_id'].nunique()
            st.metric("공급업체 수", supplier_count)
        else:
            st.metric("공급업체 수", "N/A")
    
    with col4:
        hr_count = len(products_df[products_df['category1'] == 'HR']) if 'category1' in products_df.columns else 0
        st.metric("HR 제품 수", hr_count)

def show_product_code_management(product_code_manager, get_text=lambda x: x):
    """제품 코드 관리 페이지"""
    st.header("🔧 제품 코드 관리")
    
    st.info("표준 제품 코드 체계를 관리합니다.")
    
    # 간단한 코드 생성 도구
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 코드 생성")
        category = st.selectbox("카테고리", ["HR", "HRC", "Service", "Spare"])
        sequence = st.number_input("순서번호", min_value=1, max_value=999, value=1)
        
        if st.button("코드 생성"):
            new_code = f"{category}-{sequence:03d}"
            st.success(f"생성된 코드: {new_code}")
    
    with col2:
        st.subheader("📊 코드 통계")
        st.info("코드 생성 및 사용 통계")

def show_product_bulk_operations(product_manager, get_text=lambda x: x):
    """제품 대량 작업 페이지"""
    st.header("📤 대량 작업")
    
    tab1, tab2 = st.tabs(["📥 대량 등록", "📊 데이터 내보내기"])
    
    with tab1:
        st.subheader("제품 대량 등록")
        
        st.markdown("""
        CSV 파일을 업로드하여 여러 제품을 한번에 등록할 수 있습니다.
        """)
        
        # 템플릿 다운로드
        if st.button("📥 템플릿 다운로드"):
            template_data = {
                'product_name_ko': ['샘플제품', ''],
                'product_name_en': ['Sample Product', ''],
                'category1': ['HR', ''],
                'supplier_id': ['SUP001', ''],
                'specifications': ['샘플 규격', '']
            }
            template_df = pd.DataFrame(template_data)
            
            csv = template_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="템플릿 파일 다운로드",
                data=csv,
                file_name="product_template.csv",
                mime="text/csv"
            )
        
        # 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일 선택", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                
                st.subheader("업로드된 데이터 미리보기")
                st.dataframe(df.head())
                
                if st.button("🚀 대량 등록 실행", type="primary"):
                    success_count = 0
                    error_count = 0
                    
                    for index, row in df.iterrows():
                        try:
                            product_data = row.to_dict()
                            product_manager.add_product(product_data)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"행 {index + 1} 등록 실패: {str(e)}")
                    
                    st.success(f"등록 완료: {success_count}개, 실패: {error_count}개")
                    if success_count > 0:
                        st.rerun()
                        
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    
    with tab2:
        st.subheader("데이터 내보내기")
        
        products_df = product_manager.get_all_products()
        if len(products_df) > 0:
            csv = products_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📊 전체 제품 데이터 다운로드",
                data=csv,
                file_name=f"products_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("내보낼 제품 데이터가 없습니다.")