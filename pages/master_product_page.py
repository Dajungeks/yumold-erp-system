import streamlit as st
import pandas as pd
from datetime import datetime
from master_product_manager import MasterProductManager
from sales_product_manager import SalesProductManager  
from supply_product_manager import SupplyProductManager
from notification_helper import NotificationHelper
from product_code_generator import ProductCodeGenerator
from product_edit_functions import show_product_edit, show_product_delete

# NotificationHelper는 정적 메서드를 사용합니다

def show_master_product_page(master_product_manager, sales_product_manager, supply_product_manager, user_permissions, get_text):
    """통합 제품 관리 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'master_product_management', get_text)
    
    st.title(f"🗃️ {get_text('master_product_management')}")
    st.markdown("---")
    
    # 관리 전용 탭 구성
    st.info(f"📢 **{get_text('product_registration_guide')}**")
    st.markdown(f"""
    - **{get_text('non_mb_product_registration')}**
    - **{get_text('mb_product_registration')}**  
    - **{get_text('master_product_management_info')}**
    """)
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        f"📊 {get_text('master_product_status')}", 
        f"🔍 {get_text('product_search')}", 
        f"✏️ {get_text('product_edit')}",
        f"🗑️ {get_text('product_delete')}",
        f"💰 {get_text('price_management_integration')}", 
        f"📈 {get_text('product_statistics')}"
    ])
    
    with tab1:
        show_master_product_overview(master_product_manager, get_text)
    
    with tab2:
        show_product_search(master_product_manager, get_text)
    
    with tab3:
        from product_edit_functions import show_product_edit
        show_product_edit(master_product_manager, get_text)
    
    with tab4:
        from product_edit_functions import show_product_delete
        show_product_delete(master_product_manager, get_text)
    
    with tab5:
        show_price_management_integration(master_product_manager, sales_product_manager, supply_product_manager, get_text)
    
    with tab6:
        show_product_statistics(master_product_manager, get_text)

def show_master_product_overview(master_product_manager, get_text):
    """마스터 제품 현황 개요를 표시합니다."""
    import pandas as pd
    import plotly.express as px
    
    st.header(f"📊 {get_text('master_product_database_status')}")
    
    # 통계 조회
    stats = master_product_manager.get_statistics()
    
    if stats:
        # 전체 현황 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label=f"📦 {get_text('total_products')}",
                value=f"{stats.get('total_products', 0):,}개"
            )
        
        with col2:
            st.metric(
                label="✅ 활성 제품",
                value=f"{stats.get('active_products', 0):,}개"
            )
        
        with col3:
            st.metric(
                label="💰 판매가 설정",
                value=f"{stats.get('with_sales_price', 0):,}개"
            )
        
        with col4:
            st.metric(
                label="🏭 공급가 설정",
                value=f"{stats.get('with_supply_price', 0):,}개"
            )
        
        st.markdown("---")
        
        # 가격이 적용된 제품 목록 표시
        st.subheader("💰 가격이 적용된 제품 목록")
        
        # 표시 방식 선택
        col_view1, col_view2 = st.columns([1, 3])
        with col_view1:
            view_mode = st.selectbox("표시 방식", ["전체 보기", "카테고리별 보기"], key="product_view_mode")
        with col_view2:
            st.info("🔍 공급가 또는 판매가가 설정된 제품만 표시됩니다.")
        
        # 가격이 적용된 제품 조회
        priced_products = get_priced_products(master_product_manager)
        
        if not priced_products.empty:
            # 제품 코드 기반으로 카테고리 자동 분류
            priced_products = auto_classify_products_by_code(priced_products)
            # 필요한 컬럼만 선택하여 표시
            display_columns = []
            available_columns = priced_products.columns.tolist()
            
            # 카테고리 컬럼 찾기 (자동 분류된 카테고리 우선 사용)
            category_col = None
            if '카테고리' in available_columns:
                category_col = '카테고리'
                display_columns.append('카테고리')
            elif 'auto_category' in available_columns:
                category_col = 'auto_category'
                display_columns.append('auto_category')
            elif 'category_name' in available_columns:
                category_col = 'category_name'
                display_columns.append('category_name')
            elif 'main_category' in available_columns:
                category_col = 'main_category'
                display_columns.append('main_category')
            elif 'category' in available_columns:
                category_col = 'category'
                display_columns.append('category')
            elif 'product_category' in available_columns:
                category_col = 'product_category'
                display_columns.append('product_category')
            
            # 제품 코드 컬럼 찾기
            if 'product_code' in available_columns:
                display_columns.append('product_code')
            
            # 제품명 컬럼 추가
            if 'product_name' in available_columns:
                display_columns.append('product_name')
            elif 'product_name_ko' in available_columns:
                display_columns.append('product_name_ko')
            
            # 공급가 컬럼 찾기
            if 'supply_price' in available_columns:
                display_columns.append('supply_price')
            elif 'cost_price' in available_columns:
                display_columns.append('cost_price')
            
            # 판매가 컬럼 찾기  
            if 'sales_price_vnd' in available_columns:
                display_columns.append('sales_price_vnd')
            elif 'sales_price' in available_columns:
                display_columns.append('sales_price')
            elif 'selling_price' in available_columns:
                display_columns.append('selling_price')
            
            # 표시할 데이터프레임 생성
            if display_columns:
                display_df = priced_products[display_columns].copy()
                
                # 컬럼명 한국어로 변경
                column_mapping = {
                    '카테고리': '카테고리',  # 이미 한국어인 경우
                    'auto_category': '카테고리',
                    'category_name': '카테고리',
                    'main_category': '카테고리',
                    'category': '카테고리',
                    'product_category': '카테고리',
                    'product_code': '제품 코드',
                    'supply_price': '공급가 (KRW)',
                    'cost_price': '공급가 (KRW)',
                    'sales_price_vnd': '판매가 (VND)',
                    'sales_price': '판매가 (VND)',
                    'selling_price': '판매가 (VND)',
                    'product_name': '제품명',
                    'product_name_ko': '제품명',
                    'currency': '통화',
                    'supplier': '공급업체'
                }
                
                display_df = display_df.rename(columns=column_mapping)
                
                # 카테고리 표시를 A, B, C... 형식으로 변경 (이미 자동 분류에서 처리됨)
                def format_category_label(category_name):
                    """카테고리 표시 포맷"""
                    if pd.isna(category_name) or category_name == "미분류" or category_name == "" or category_name is None:
                        return "미분류"
                    
                    # 이미 A, B, C 형식이면 그대로 반환
                    if len(str(category_name)) == 1 and str(category_name).upper() in 'ABCDEFGHI':
                        return str(category_name).upper()
                    
                    return str(category_name)
                
                # 카테고리 컬럼이 있으면 포맷 적용
                if '카테고리' in display_df.columns:
                    display_df['카테고리'] = display_df['카테고리'].apply(format_category_label)
                
                # 가격 컬럼 포맷팅
                for col in display_df.columns:
                    if '공급가' in col or '판매가' in col:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "-")
                
                # 작은 폰트와 조정된 간격 스타일
                st.markdown("""
                <style>
                .small-font .stDataFrame {
                    font-size: 12px !important;
                    line-height: 1.2 !important;
                }
                .small-font .stDataFrame td {
                    padding: 4px 8px !important;
                    vertical-align: middle !important;
                }
                .small-font .stDataFrame th {
                    padding: 6px 8px !important;
                    font-size: 13px !important;
                    font-weight: bold !important;
                }
                .category-header {
                    background-color: #f0f2f6;
                    padding: 8px 12px;
                    margin: 10px 0 5px 0;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #1f2937;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # 표시 방식에 따라 다르게 렌더링
                if view_mode == "카테고리별 보기" and '카테고리' in display_df.columns:
                    # A~I 모든 카테고리 탭으로 표시 (데이터 유무와 관계없이)
                    all_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', '미분류']
                    
                    # 모든 카테고리에 대해 데이터 준비
                    category_data = {}
                    for category in all_categories:
                        category_df = display_df[display_df['카테고리'] == category].copy()
                        category_data[category] = category_df  # 빈 DataFrame이어도 포함
                    
                    # 모든 카테고리 탭 생성 (Category A~I 형식으로)
                    tab_labels = []
                    for cat in all_categories:
                        if cat == '미분류':
                            tab_labels.append("미분류")
                        else:
                            tab_labels.append(f"Category {cat}")
                    tabs = st.tabs(tab_labels)
                    
                    for i, category in enumerate(all_categories):
                        with tabs[i]:
                            category_df = category_data[category]
                            
                            if not category_df.empty:
                                # 데이터가 있는 경우
                                category_label = "미분류" if category == '미분류' else f"Category {category}"
                                st.markdown(f'<div class="category-header">📁 {category_label} ({len(category_df)}개 제품)</div>', unsafe_allow_html=True)
                                
                                # 카테고리 컬럼 제거 (이미 탭에 표시됨)
                                category_display_df = category_df.drop(columns=['카테고리'])
                                
                                # 데이터프레임 표시
                                st.markdown('<div class="small-font">', unsafe_allow_html=True)
                                st.dataframe(category_display_df, use_container_width=True, hide_index=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                # 데이터가 없는 경우
                                category_label = "미분류" if category == '미분류' else f"Category {category}"
                                st.info(f"{category_label}에 등록된 제품이 없습니다.")
                                st.markdown("---")
                                st.markdown("💡 **제품을 등록하려면:**")
                                st.markdown("1. 시스템 설정에서 카테고리 완성된 코드 구조를 먼저 설정하세요")
                                st.markdown("2. 제품 등록에서 해당 코드로 제품을 등록하면 자동으로 이 카테고리에 분류됩니다")
                else:
                    # 전체 보기
                    st.markdown('<div class="small-font">', unsafe_allow_html=True)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.caption(f"📊 총 {len(display_df)}개의 가격이 설정된 제품")
            else:
                st.warning("표시할 수 있는 컬럼이 없습니다.")
        else:
            st.warning("💰 가격이 설정된 제품이 없습니다.")
    else:
        st.warning("마스터 제품 데이터가 없습니다.")

def auto_classify_products_by_code(products_df):
    """제품 코드를 기반으로 시스템 설정에서 카테고리를 자동 분류"""
    import pandas as pd
    import sqlite3
    
    def get_category_from_product_code_pattern(product_code):
        """제품 코드 패턴에 따라 자동으로 카테고리를 결정합니다."""
        if not product_code:
            return "미분류"
        
        # 제품 코드 패턴 기반 카테고리 분류
        if product_code.startswith('HR-'):
            return "A"
        elif product_code.startswith('CON-') or product_code.startswith('SNT-'):
            return "B"
        else:
            return "미분류"

    def get_category_from_system_settings(product_code):
        """시스템 설정에서 제품 코드의 카테고리 정보를 가져옵니다. (패턴 기반 우선)"""
        try:
            # 1순위: 제품 코드 패턴 기반 분류
            pattern_category = get_category_from_product_code_pattern(product_code)
            if pattern_category != "미분류":
                return pattern_category
            
            # 2순위: 시스템 설정 기반 분류 (복잡한 매칭)
            conn = sqlite3.connect('erp_system.db')
            cursor = conn.cursor()
            
            # 제품 코드를 6개 파트로 분할
            code_parts = product_code.split('-')
            if len(code_parts) < 6:
                conn.close()
                return "미분류"
            
            # multi_category_components 테이블에서 모든 카테고리 (A~I) 확인
            cursor.execute('''
                SELECT DISTINCT l1.category_type
                FROM multi_category_components l1
                JOIN multi_category_components l2 ON l2.parent_component = l1.component_key AND l1.category_type = l2.category_type
                JOIN multi_category_components l3 ON l3.parent_component = (l1.component_key || '-' || l2.component_key) AND l1.category_type = l3.category_type
                JOIN multi_category_components l4 ON l4.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key) AND l1.category_type = l4.category_type
                JOIN multi_category_components l5 ON l5.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key) AND l1.category_type = l5.category_type
                JOIN multi_category_components l6 ON l6.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key || '-' || l5.component_key) AND l1.category_type = l6.category_type
                WHERE l1.component_key = ? AND l2.component_key = ? AND l3.component_key = ?
                AND l4.component_key = ? AND l5.component_key = ? AND l6.component_key = ?
                AND l1.component_level = 'level1' AND l2.component_level = 'level2' AND l3.component_level = 'level3'
                AND l4.component_level = 'level4' AND l5.component_level = 'level5' AND l6.component_level = 'level6'
                AND l1.is_active = 1 AND l2.is_active = 1 AND l3.is_active = 1 
                AND l4.is_active = 1 AND l5.is_active = 1 AND l6.is_active = 1
            ''', (code_parts[0], code_parts[1], code_parts[2], code_parts[3], code_parts[4], code_parts[5]))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            
            return "미분류"
            
        except Exception as e:
            print(f"카테고리 조회 오류: {e}")
            return "미분류"
    
    try:
        # 제품 데이터프레임이 비어있으면 그대로 반환
        if products_df.empty:
            return products_df
            
        # 카테고리 컬럼 추가
        products_df = products_df.copy()
        
        # 각 제품에 대해 카테고리 조회 (저장된 카테고리 우선, 없으면 시스템 설정에서 조회)
        categories = []
        for idx, row in products_df.iterrows():
            # 1순위: 이미 저장된 카테고리 정보 사용
            stored_category = row.get('category_name', '')
            if stored_category and stored_category != '' and not pd.isna(stored_category):
                # 저장된 카테고리에서 알파벳만 추출 (카테고리A -> A, 카테고리B -> B)
                if '카테고리' in stored_category:
                    category_letter = stored_category.replace('카테고리', '')
                    if category_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                        categories.append(category_letter)
                    else:
                        categories.append("미분류")
                else:
                    categories.append("미분류")
            else:
                # 2순위: 시스템 설정에서 조회
                product_code = row.get('product_code', '')
                if product_code:
                    category = get_category_from_system_settings(product_code)
                    categories.append(category)
                else:
                    categories.append("미분류")
        
        # 카테고리 컬럼 추가
        products_df['카테고리'] = categories
        
        return products_df
        
    except Exception as e:
        print(f"자동 분류 중 오류: {e}")
        # 오류 발생 시 카테고리 컬럼만 추가하고 모두 미분류로 설정
        if not products_df.empty:
            products_df = products_df.copy()
            products_df['카테고리'] = "미분류"
        return products_df
        
        # 각 카테고리별로 완성된 코드 경로 생성
        for cat_type, levels in category_components.items():
            completed_codes_by_category[cat_type] = set()
            
            # 재귀적으로 완성된 코드 경로 생성
            def generate_complete_paths(current_path='', current_level='level1', max_depth=10):
                if current_level not in levels or max_depth <= 0:
                    if current_path and len(current_path.split('-')) >= 3:  # 최소 3개 컴포넌트
                        completed_codes_by_category[cat_type].add(current_path)
                    return
                
                for component in levels[current_level]:
                    parent = component['parent']
                    key = component['key']
                    
                    # 부모 조건 확인
                    if not parent:  # level1
                        new_path = key
                    elif not current_path:  # 부모가 있는데 현재 경로가 없으면 스킵
                        continue
                    elif current_path.endswith(parent):  # 부모가 현재 경로 끝과 매치
                        new_path = f"{current_path}-{key}"
                    elif parent in current_path:  # 부모가 경로 중간에 있음
                        new_path = f"{current_path}-{key}"
                    else:
                        continue
                    
                    # 다음 레벨로 진행
                    next_level_num = int(current_level[-1]) + 1
                    next_level = f"level{next_level_num}"
                    
                    # 현재 경로도 저장 (완성된 코드가 될 수 있음)
                    if len(new_path.split('-')) >= 3:
                        completed_codes_by_category[cat_type].add(new_path)
                    
                    generate_complete_paths(new_path, next_level, max_depth - 1)
            
            generate_complete_paths()
        
        conn.close()
        
        def extract_category_from_master_product(master_product_row):
            """master_products 테이블의 기존 카테고리 정보를 사용해서 카테고리 추출"""
            try:
                # 이미 등록된 카테고리 ID에서 카테고리 추출
                if 'category_id' in master_product_row and pd.notna(master_product_row['category_id']):
                    category_id = str(master_product_row['category_id']).strip()
                    
                    # CAT_A → A, CAT_B → B 형식으로 변환
                    if category_id.startswith('CAT_'):
                        category_letter = category_id.replace('CAT_', '')
                        if category_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                            return category_letter
                
                # category_name에서도 확인
                if 'category_name' in master_product_row and pd.notna(master_product_row['category_name']):
                    category_name = str(master_product_row['category_name']).strip()
                    
                    # 카테고리A → A, 카테고리B → B 형식으로 변환
                    if '카테고리' in category_name:
                        category_letter = category_name.replace('카테고리', '')
                        if category_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                            return category_letter
                
                return "미분류"
                
            except Exception as e:
                print(f"카테고리 추출 오류: {e}")
                return "미분류"
        
        # 카테고리 컬럼 추가 (기존 master_products의 카테고리 정보 사용)
        products_df['카테고리'] = products_df.apply(extract_category_from_master_product, axis=1)
        
        return products_df
        
    except Exception as e:
        print(f"자동 카테고리 분류 오류: {e}")
        products_df['카테고리'] = "미분류"
        return products_df

def get_priced_products(master_product_manager):
    """가격이 설정된 제품만 조회합니다."""
    import pandas as pd
    import sqlite3
    
    try:
        # 가격이 설정된 제품만 직접 쿼리 (category_id, category_name 포함)
        conn = sqlite3.connect('erp_system.db')
        
        query = '''
        SELECT master_product_id, product_code, product_name, product_name_en, product_name_vi,
               category_id, category_name, brand, model, description, unit, 
               supply_currency, supply_price, exchange_rate, sales_price_vnd,
               supplier_name, status, created_date, updated_date
        FROM master_products 
        WHERE (supply_price > 0 OR sales_price_vnd > 0) AND status != 'deleted'
        ORDER BY created_date DESC
        '''
        
        priced_products = pd.read_sql_query(query, conn)
        conn.close()
        
        return priced_products
        
    except Exception as e:
        print(f"가격 설정된 제품 조회 오류: {e}")
        return pd.DataFrame()

def show_product_search(master_product_manager, get_text):
    """제품 검색 기능을 표시합니다."""
    import pandas as pd
    
    st.header("🔍 제품 검색 및 상세 정보")
    
    # 검색 필터
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 시스템 설정에서 카테고리 가져오기
        try:
            from managers.sqlite.sqlite_system_config_manager import SQLiteSystemConfigManager
            system_config = SQLiteSystemConfigManager()
            categories = system_config.get_product_categories()
            if not categories:
                st.warning("⚠️ 시스템 설정에서 제품 카테고리를 먼저 설정해주세요. (법인장 → 시스템 설정)")
                categories = []
        except Exception as e:
            st.error(f"시스템 설정 로드 오류: {e}")
            categories = master_product_manager.get_categories()
        
        # categories가 리스트인지 확인하고 안전하게 처리
        if isinstance(categories, list):
            category_options = ["전체"] + categories
        else:
            category_options = ["전체"]
            
        category_filter = st.selectbox(
            "카테고리 선택",
            options=category_options,
            key="search_category"
        )
    
    with col2:
        status_filter = st.selectbox(
            "상태 선택",
            options=["전체", "활성", "삭제됨"],
            key="search_status"
        )
    
    with col3:
        search_code = st.text_input(
            "제품 코드 검색",
            placeholder="제품 코드 입력...",
            key="search_code"
        )
    
    with col4:
        search_name = st.text_input(
            "제품명 검색",
            placeholder="제품명 입력...",
            key="search_name"
        )
    
    # 제품 조회
    all_products = master_product_manager.get_all_products()
    
    # DataFrame이 아닌 경우 (list) DataFrame으로 변환
    if isinstance(all_products, list):
        import pandas as pd
        if len(all_products) > 0:  # 빈 리스트가 아닌 경우만
            all_products = pd.DataFrame(all_products)
        else:
            all_products = pd.DataFrame()
    
    # 데이터 존재 여부 확인
    has_data = False
    if all_products is not None:
        if isinstance(all_products, list):
            has_data = len(all_products) > 0
        elif isinstance(all_products, pd.DataFrame):
            has_data = len(all_products) > 0
    
    if has_data:
        # 필터 적용 (안전한 컬럼 접근)
        filtered_products = all_products.copy()
        
        try:
            if category_filter != "전체" and 'category_name' in filtered_products.columns:
                filtered_products = filtered_products[
                    filtered_products['category_name'] == category_filter
                ]
            
            # 상태 필터 적용
            if status_filter == "활성" and 'status' in filtered_products.columns:
                filtered_products = filtered_products[
                    filtered_products['status'] == 'active'
                ]
            elif status_filter == "삭제됨" and 'status' in filtered_products.columns:
                filtered_products = filtered_products[
                    filtered_products['status'] == 'inactive'
                ]
            
            if search_code and 'product_code' in filtered_products.columns:
                filtered_products = filtered_products[
                    filtered_products['product_code'].str.contains(search_code, case=False, na=False)
                ]
            
            if search_name:
                mask = None
                if 'product_name' in filtered_products.columns:
                    mask = filtered_products['product_name'].str.contains(search_name, case=False, na=False)
                if 'product_name_en' in filtered_products.columns:
                    en_mask = filtered_products['product_name_en'].str.contains(search_name, case=False, na=False)
                    mask = en_mask if mask is None else (mask | en_mask)
                if mask is not None:
                    filtered_products = filtered_products[mask]
                    
        except Exception as e:
            st.error(f"필터 적용 중 오류: {e}")
            filtered_products = all_products.copy()
        
        # 카테고리 포맷 함수 개선
        def format_category_display(category_name):
            """카테고리를 A, B, C... 형식으로 변환"""
            if pd.isna(category_name) or not category_name:
                return "미분류"
            
            # 문자열로 변환하여 안전하게 처리
            category_str = str(category_name).strip()
            
            # 빈 문자열이거나 미분류 관련 키워드
            if not category_str or category_str in ["미분류", "미분류 카테고리", "nan", "None"]:
                return "미분류"
            
            # 카테고리 매핑 (더 포괄적)
            category_mapping = {
                "카테고리A": "A", "카테고리B": "B", "카테고리C": "C",
                "카테고리D": "D", "카테고리E": "E", "카테고리F": "F", 
                "카테고리G": "G", "카테고리H": "H", "카테고리I": "I",
                # 영어 버전도 추가
                "Category A": "A", "Category B": "B", "Category C": "C",
                "Category D": "D", "Category E": "E", "Category F": "F",
                "Category G": "G", "Category H": "H", "Category I": "I",
                # 약어 버전
                "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", 
                "F": "F", "G": "G", "H": "H", "I": "I"
            }
            
            # 매핑된 값이 있으면 반환, 없으면 원본 반환 (첫 글자를 대문자로)
            mapped_value = category_mapping.get(category_str, None)
            if mapped_value:
                return mapped_value
            
            # 매핑되지 않은 경우, 첫 번째 문자를 대문자로 변환 시도
            if len(category_str) >= 1:
                first_char = category_str[0].upper()
                if first_char in "ABCDEFGHI":
                    return first_char
            
            # 모든 매핑에 실패하면 원본 반환
            return category_str
        
        # 검색 결과 표시
        col_result, col_view = st.columns([2, 1])
        with col_result:
            st.markdown(f"**검색 결과: {len(filtered_products)}개 제품**")
        with col_view:
            view_type = st.selectbox("보기 방식", ["목록 보기", "카테고리별 보기"], key="product_search_view")
        
        # 완성된 제품 표시 플로우 호출
        complete_product_display_flow(filtered_products, view_type, format_category_display)


def render_product_list(page_products, format_category_display):
    """일반 목록 형태로 제품 표시 (간단 코드 형태)"""
    products_to_show = page_products.to_dict('records') if hasattr(page_products, 'to_dict') else page_products
    for product in products_to_show:
        # 간단한 코드와 제품명만 표시
        with st.expander(f"📦 {product.get('product_code', 'N/A')}"):
            st.code(product.get('product_code', 'N/A'), language='text')


def render_product_details_col2(product, col2):
    """제품 상세 정보의 두 번째 컬럼 렌더링"""
    with col2:
        st.write("**제품 상세 정보**")
        st.write(f"- 설명: {product.get('description', 'N/A')}")
        st.write(f"- 사양: {product.get('specifications', 'N/A')}")
        st.write(f"- 중량: {product.get('weight', 0)}kg")
        st.write(f"- 치수: {product.get('dimensions', 'N/A')}")
        st.write(f"- 제조국: {product.get('origin_country', 'N/A')}")
        st.write(f"- 제조사: {product.get('manufacturer', 'N/A')}")
        
        st.write("**재고 정보**")
        status_color = "🟢" if product.get('status') == 'active' else "🔴"
        st.write(f"- 상태: {status_color} {product.get('status', 'unknown')}")
        st.write(f"- 판매 가능: {'✅' if product.get('is_sellable', 0) else '❌'}")
        st.write(f"- 구매 가능: {'✅' if product.get('is_purchasable', 0) else '❌'}")
        st.write(f"- 재고 추적: {'✅' if product.get('is_trackable', 0) else '❌'}")
        st.write(f"- 최소 재고: {product.get('min_stock_level', 0)}")
        st.write(f"- 최대 재고: {product.get('max_stock_level', 0)}")
        
        st.write("**시스템 정보**")
        st.write(f"- 데이터 출처: {product.get('data_source', 'N/A')}")
        st.write(f"- 생성일: {product.get('created_date', 'N/A')}")


def complete_product_display_flow(filtered_products, view_type, format_category_display):
    """제품 표시 흐름 완성"""
    if len(filtered_products) > 0:
        # 페이지네이션
        items_per_page = 20
        total_pages = (len(filtered_products) - 1) // items_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox(
                "페이지 선택",
                options=list(range(1, total_pages + 1)),
                key="search_page"
            )
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_products = filtered_products.iloc[start_idx:end_idx]
        else:
            page_products = filtered_products
        
        # 카테고리별 보기와 목록 보기 분기
        if view_type == "카테고리별 보기":
            render_category_view(page_products, format_category_display)
        else:
            render_product_list(page_products, format_category_display)
    else:
        st.info("검색 조건에 맞는 제품이 없습니다.")


def render_category_view(page_products, format_category_display):
    """카테고리별 보기 렌더링 - A~I 모든 카테고리 탭 표시"""
    # 카테고리별로 그룹화
    if hasattr(page_products, 'copy'):
        products_df = page_products.copy()
    else:
        products_df = pd.DataFrame(page_products)
    
    # 카테고리 컬럼 찾기
    category_col = None
    for col in ['category_name', 'main_category', 'category']:
        if col in products_df.columns:
            category_col = col
            break
    
    if category_col:
        # 카테고리 포맷 적용
        products_df['display_category'] = products_df[category_col].apply(format_category_display)
        
        # A~I 모든 카테고리를 순서대로 표시 (데이터 유무와 관계없이)
        all_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', '미분류']
        
        # 각 카테고리별 데이터 준비 (저장된 카테고리 우선 사용)
        category_data = {}
        for category in all_categories:
            # 먼저 display_category로 필터링
            category_products = products_df[products_df['display_category'] == category]
            
            # display_category가 없으면 저장된 카테고리 정보로 직접 매칭
            if len(category_products) == 0 and '카테고리' in products_df.columns:
                if category != '미분류':
                    # 카테고리A, 카테고리B 등으로 저장된 제품들 찾기
                    stored_category_name = f'카테고리{category}'
                    category_products = products_df[products_df['카테고리'] == category]
                else:
                    # 미분류: 카테고리 정보가 없거나 빈 제품들
                    category_products = products_df[
                        (products_df['카테고리'].isna()) | 
                        (products_df['카테고리'] == '') | 
                        (products_df['카테고리'] == '미분류')
                    ]
            
            category_data[category] = category_products
        
        # 모든 카테고리 탭 생성 (A~I 순서로)
        tab_labels = []
        for cat in all_categories:
            if cat == '미분류':
                tab_labels.append("미분류")
            else:
                tab_labels.append(f"Category {cat}")
        tabs = st.tabs(tab_labels)
        
        for i, category in enumerate(all_categories):
            with tabs[i]:
                category_products = category_data[category]
                
                if len(category_products) > 0:
                    # 데이터가 있는 경우
                    st.markdown(f"### 📁 카테고리 {category} 제품 목록 ({len(category_products)}개)")
                    
                    # 해당 카테고리 제품들 표시
                    for _, product in category_products.iterrows():
                        product_dict = product.to_dict()
                        display_category = format_category_display(product_dict.get('category_name', 'N/A'))
                        
                        with st.expander(f"📦 {product_dict['product_code']} - {product_dict.get('product_name', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**기본 정보**")
                                st.write(f"- 제품 ID: {product_dict.get('master_product_id', 'N/A')}")
                                st.write(f"- 제품 코드: {product_dict.get('product_code', 'N/A')}")
                                st.write(f"- 제품명: {product_dict.get('product_name', 'N/A')}")
                                st.write(f"- 영어명: {product_dict.get('product_name_en', 'N/A')}")
                                st.write(f"- 베트남어명: {product_dict.get('product_name_vi', 'N/A')}")
                                
                                st.write("**카테고리 정보**")
                                st.write(f"- 카테고리: {display_category}")
                                st.write(f"- 서브카테고리: {product_dict.get('subcategory_name', 'N/A')}")
                                st.write(f"- 브랜드: {product_dict.get('brand', 'N/A')}")
                                st.write(f"- 모델: {product_dict.get('model', 'N/A')}")
                                st.write(f"- 단위: {product_dict.get('unit', 'EA')}")
                                
                                # 상태 표시
                                status = product_dict.get('status', 'unknown')
                                if status == 'active':
                                    st.success(f"✅ 상태: 활성")
                                elif status == 'inactive':
                                    st.error(f"🗑️ 상태: 삭제됨")
                                else:
                                    st.info(f"ℹ️ 상태: {status}")
                            
                            with col2:
                                render_product_details_col2(product_dict, col2)
                else:
                    # 데이터가 없는 경우
                    st.info(f"카테고리 {category}에 등록된 제품이 없습니다.")
                    st.markdown("---")
                    st.markdown("💡 **제품을 등록하려면:**")
                    st.markdown("1. 시스템 설정에서 카테고리 완성된 코드 구조를 먼저 설정하세요")
                    st.markdown("2. 제품 등록에서 해당 코드로 제품을 등록하면 자동으로 이 카테고리에 분류됩니다")
    else:
        # 카테고리 컬럼이 없으면 일반 목록으로 표시
        st.warning("카테고리 정보가 없어 일반 목록으로 표시합니다.")
        render_product_list(page_products, format_category_display)

def show_price_management_integration(master_product_manager, sales_product_manager, supply_product_manager, get_text):
    """가격 관리 시스템 연동을 표시합니다."""
    import pandas as pd
    
    st.header("💰 가격 관리 시스템 연동")
    
    # 판매가 설정 섹션
    st.subheader("📈 판매가 설정 (HR, HRC 제품)")
    
    # 판매가 설정 가능한 제품 조회
    sales_products = sales_product_manager.get_master_products_for_sales()
    
    # DataFrame이 아닌 경우 (list) DataFrame으로 변환
    if isinstance(sales_products, list):
        import pandas as pd
        sales_products = pd.DataFrame(sales_products)
    
    if len(sales_products) > 0:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 컬럼명 확인 및 대체
            name_col = 'product_name_korean' if 'product_name_korean' in sales_products.columns else 'product_name'
            code_col = 'product_code' if 'product_code' in sales_products.columns else sales_products.columns[0]
            
            selected_sales_product = st.selectbox(
                "판매가 설정할 제품 선택",
                options=sales_products[code_col].tolist(),
                format_func=lambda x: f"{x} - {sales_products[sales_products[code_col]==x][name_col].iloc[0] if len(sales_products[sales_products[code_col]==x]) > 0 else x}",
                key="sales_product_select"
            )
        
        with col2:
            if st.button("💰 판매가 설정", key="set_sales_price"):
                # 세션 상태에 메뉴 변경 정보 저장
                st.session_state['selected_menu'] = 'sales_product_management'
                st.session_state['product_for_price_setting'] = selected_sales_product
                
                # 페이지 리로드로 메뉴 변경
                st.rerun()
    else:
        st.info("판매가 설정 가능한 제품이 없습니다.")
    
    st.markdown("---")
    
    # 공급가 설정 섹션
    st.subheader("🏭 공급가 설정 (MB 제품)")
    
    # MB 제품 조회 (임시로 빈 DataFrame 반환)
    try:
        mb_products = supply_product_manager.get_master_mb_products() if hasattr(supply_product_manager, 'get_master_mb_products') else pd.DataFrame()
        # DataFrame이 아닌 경우 (list) DataFrame으로 변환
        if isinstance(mb_products, list):
            import pandas as pd
            mb_products = pd.DataFrame(mb_products)
    except Exception as e:
        import pandas as pd
        mb_products = pd.DataFrame()
    
    if len(mb_products) > 0:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 컬럼명 확인 및 대체
            mb_name_col = 'product_name_korean' if 'product_name_korean' in mb_products.columns else 'product_name'
            mb_code_col = 'product_code' if 'product_code' in mb_products.columns else mb_products.columns[0]
            
            selected_mb_product = st.selectbox(
                "공급가 설정할 MB 제품 선택",
                options=mb_products[mb_code_col].tolist(),
                format_func=lambda x: f"{x} - {mb_products[mb_products[mb_code_col]==x][mb_name_col].iloc[0] if len(mb_products[mb_products[mb_code_col]==x]) > 0 else x}",
                key="mb_product_select"
            )
        
        with col2:
            if st.button("🏭 공급가 설정", key="set_supply_price"):
                # 세션 상태에 메뉴 변경 정보 저장
                st.session_state['selected_menu'] = 'supply_product_management'
                st.session_state['product_for_supply_setting'] = selected_mb_product
                
                # 페이지 리로드로 메뉴 변경
                st.rerun()
    else:
        st.info("공급가 설정 가능한 MB 제품이 없습니다.")

def show_product_statistics(master_product_manager, get_text):
    """제품 통계를 표시합니다."""
    import pandas as pd
    import plotly.express as px
    
    st.header("📈 제품 통계 분석")
    
    all_products = master_product_manager.get_all_products()
    
    if all_products is not None and isinstance(all_products, pd.DataFrame) and not all_products.empty:
        # DataFrame이 아닌 경우 (list) DataFrame으로 변환
        if isinstance(all_products, list):
            import pandas as pd
            all_products = pd.DataFrame(all_products)
        
        # 기본 통계
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 카테고리별 분포")
            # 카테고리 컬럼 확인
            if hasattr(all_products, 'columns'):
                category_col = 'main_category' if 'main_category' in all_products.columns else 'category_name' if 'category_name' in all_products.columns else all_products.columns[0] if len(all_products.columns) > 0 else None
                if category_col:
                    category_counts = all_products[category_col].value_counts()
                else:
                    st.info("카테고리 정보가 없습니다.")
                    return
            else:
                st.info("제품 데이터 형식이 올바르지 않습니다.")
                return
            
            for category, count in category_counts.items():
                percentage = (count / len(all_products)) * 100
                st.write(f"**{category}**: {count}개 ({percentage:.1f}%)")
        
        with col2:
            st.subheader("💰 가격 설정 현황")
            # SQLite 구조에서는 가격 설정 정보가 별도 테이블에 있으므로 기본값 사용
            total_products = len(all_products)
            
            # 판매 가능/구매 가능 제품 수로 대체
            sellable_count = len(all_products[all_products['is_sellable'] == 1]) if 'is_sellable' in all_products.columns else 0
            purchasable_count = len(all_products[all_products['is_purchasable'] == 1]) if 'is_purchasable' in all_products.columns else 0
            
            st.write(f"**판매 가능**: {sellable_count}개")
            st.write(f"**구매 가능**: {purchasable_count}개")
            st.write(f"**총 제품**: {total_products}개")
        
        st.markdown("---")
        
        # 데이터 출처별 분포
        st.subheader("📁 데이터 출처별 분포")
        if 'data_source' in all_products.columns:
            source_counts = all_products['data_source'].value_counts()
        else:
            # data_source 컬럼이 없으면 임시 데이터 생성
            source_counts = pd.Series(['sqlite'] * len(all_products), name='data_source').value_counts()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            import plotly.express as px
            
            source_df = pd.DataFrame(
                list(source_counts.items()),
                columns=['데이터 출처', '제품 수']
            )
            
            fig = px.bar(
                source_df,
                x='데이터 출처',
                y='제품 수',
                title="데이터 출처별 제품 수"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            for source, count in source_counts.items():
                st.metric(
                    label=source,
                    value=f"{count:,}개"
                )
    else:
        st.warning("분석할 제품 데이터가 없습니다.")

def show_data_management(master_product_manager):
    """데이터 관리 기능을 표시합니다."""
    st.header("⚙️ 데이터 관리")
    
    # 데이터 새로고침
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 데이터 새로고침", key="refresh_data"):
            NotificationHelper.show_success("데이터가 새로고침되었습니다.")
            st.rerun()
    
    with col2:
        if st.button("📊 통계 업데이트", key="update_stats"):
            stats = master_product_manager.get_statistics()
            NotificationHelper.show_success(f"통계가 업데이트되었습니다. 총 {stats.get('total_products', 0)}개 제품")
    
    with col3:
        if st.button("💾 백업 생성", key="create_backup"):
            # 백업 기능 (실제 구현 시 추가)
            NotificationHelper.show_info("백업이 생성되었습니다.")
    
    st.markdown("---")
    
    # 데이터 현황 요약
    st.subheader("📋 데이터 현황 요약")
    
    stats = master_product_manager.get_statistics()
    
    if stats:
        summary_data = {
            "항목": [
                "총 제품 수",
                "활성 제품",
                "HR 제품", 
                "MB 제품",
                "HRC 제품",
                "견적서 사용 가능",
                "판매가 설정 완료",
                "공급가 설정 완료"
            ],
            "수량": [
                f"{stats.get('total_products', 0):,}개",
                f"{stats.get('active_products', 0):,}개",
                f"{stats.get('categories', {}).get('HR', 0):,}개",
                f"{stats.get('categories', {}).get('MB', 0):,}개", 
                f"{stats.get('categories', {}).get('HRC', 0):,}개",
                f"{stats.get('quotation_available', 0):,}개",
                f"{stats.get('with_sales_price', 0):,}개",
                f"{stats.get('with_supply_price', 0):,}개"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.warning("통계 데이터를 로드할 수 없습니다.")
    
    # 시스템 정보
    st.markdown("---")
    st.subheader("ℹ️ 시스템 정보")
    
    system_info = {
        "마스터 제품 DB": "1,111개 제품 (HR: 347개, MB: 723개, HRC: 82개)",
        "데이터 출처": "HR_CODE.csv, MB_Code.csv 실제 데이터",
        "연동 시스템": "견적서, 판매 제품 관리, 외주 공급가 관리",
        "지원 언어": "한국어, 영어, 베트남어",
        "지원 통화": "USD, CNY, VND, THB, IDR, MYR, KRW"
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}**: {value}")


def show_product_registration(master_product_manager):
    """제품 등록 기능"""
    st.subheader("➕ 신규 제품 등록")
    
    # 코드 생성기 초기화
    code_generator = ProductCodeGenerator(master_product_manager)
    
    # 제품 카테고리 선택
    st.markdown("### 1️⃣ 제품 카테고리 선택")
    category = st.selectbox(
        "제품 카테고리 *",
        ["HR", "HRC", "MB", "SERVICE", "SPARE"],
        help="등록할 제품의 주요 카테고리를 선택하세요"
    )
    
    # 카테고리별 제품 등록 폼
    if category == "HR":
        register_hr_product(master_product_manager, code_generator)
    elif category == "HRC":
        register_hrc_product(master_product_manager, code_generator)
    elif category == "MB":
        register_mb_product(master_product_manager, code_generator)
    elif category == "SERVICE":
        register_service_product(master_product_manager, code_generator)
    elif category == "SPARE":
        register_spare_product(master_product_manager, code_generator)


def register_hr_product(master_product_manager, code_generator):
    """HR 제품 등록"""
    st.markdown("### 🔥 Hot Runner 제품 등록")
    st.info("Hot Runner 시스템 제품을 등록합니다. (YMV-ST-MAE-20-xx 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        # ProductCategoryConfigManager 가져오기
        try:
            from product_category_config_manager import ProductCategoryConfigManager
            config_manager = ProductCategoryConfigManager()
        except Exception as e:
            st.error(f"카테고리 설정 관리자 로드 오류: {e}")
            return
        
        # System Type 선택 (데이터베이스에서 가져오기)
        system_type_options = [""] + config_manager.get_hr_system_types()
        system_type = st.selectbox("System Type", system_type_options, index=0, help="등록된 System Type 중에서 선택하세요")
        
        # System Type에 따른 제품 타입 선택 (동적)
        if system_type:
            product_type_options = [""] + config_manager.get_hr_product_types(system_type)
            product_type_help = f"{system_type}에 등록된 제품 타입 중에서 선택하세요"
        else:
            product_type_options = [""]
            product_type_help = "먼저 System Type을 선택하세요"
        
        product_type = st.selectbox("제품 타입", product_type_options, index=0, help=product_type_help)
        
        # 게이트 타입 선택 (동적)
        if system_type and product_type:
            gate_options = [""] + config_manager.get_hr_gate_types(system_type, product_type)
            gate_help = f"{system_type}-{product_type}에 등록된 게이트 타입 중에서 선택하세요"
        else:
            gate_options = [""]
            gate_help = "먼저 System Type과 제품 타입을 선택하세요"
        
        gate_type = st.selectbox("게이트 타입", gate_options, index=0, help=gate_help)
        
        # 사이즈 선택 (동적)
        if system_type and product_type:
            size_options = [""] + config_manager.get_hr_sizes(system_type, product_type)
            size_help = f"{system_type}-{product_type}에 등록된 사이즈 중에서 선택하세요"
        else:
            size_options = [""]
            size_help = "먼저 System Type과 제품 타입을 선택하세요"
        
        size = st.selectbox("사이즈", size_options, index=0, help=size_help)
        
        # 시퀀스 번호 (제품명)
        seq_number = st.text_input("시퀀스 번호 (01~99)", placeholder="01", max_chars=2, help="01~99 숫자")
        
        # 제품 코드 자동 생성
        generated_code = ""
        if system_type and product_type and gate_type and size and seq_number:
            generated_code = f"HR-{system_type}-{product_type}-{gate_type}-{size}-{seq_number}"
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
        else:
            st.info("모든 옵션을 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성 제안
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        if system_type and product_type and gate_type and size:
            # 한국어 제품명 생성
            if system_type == "Valve":
                suggested_korean = f"핫러너 밸브 {product_type} {gate_type} {size}"
            else:  # Open
                suggested_korean = f"핫러너 오픈 {product_type} {gate_type} {size}"
            
            # 영어 제품명 생성
            suggested_english = f"Hot Runner {system_type} {product_type} {gate_type} {size}"
            
            # 베트남어 제품명 생성
            if system_type == "Valve":
                suggested_vietnamese = f"Van Hot Runner {product_type} {gate_type} {size}"
            else:
                suggested_vietnamese = f"Mở Hot Runner {product_type} {gate_type} {size}"
        
        product_name_korean = st.text_input("한국어 제품명 *", value=suggested_korean, placeholder="예: 핫러너 밸브 표준 MAE 20")
        product_name_english = st.text_input("영어 제품명 *", value=suggested_english, placeholder="예: Hot Runner Valve Standard MAE 20")
        product_name_vietnamese = st.text_input("베트남어 제품명", value=suggested_vietnamese, placeholder="예: Van Hot Runner Chuẩn MAE 20")
        
        specifications = st.text_input("기술 사양", value="", placeholder="H30,34,1.0")
        unit_of_measure = st.selectbox("단위", ["EA", "SET", "PC"], index=0)
    
    # 등록 버튼
    if st.button("📝 HR 제품 등록", type="primary"):
        # 필수 필드 검증
        if not generated_code:
            NotificationHelper.show_error("모든 제품 코드 구성 요소를 선택해주세요.")
        elif not product_name_korean or not product_name_english:
            NotificationHelper.show_error("한국어 제품명과 영어 제품명은 필수입니다.")
        else:
            try:
                # 제품 데이터 구성
                product_data = {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'product_name_vietnamese': product_name_vietnamese,
                    'main_category': 'HR',
                    'sub_category': system_type,
                    'product_type': product_type,
                    'gate_type': gate_type,
                    'size': size,
                    'seq_number': seq_number,
                    'specifications': specifications,
                    'unit_of_measure': unit_of_measure,
                    'hs_code': '84779039',
                    'status': 'active',
                    'data_source': 'MANUAL_REGISTRATION'
                }
                
                # 제품 등록
                result, message = master_product_manager.add_product(product_data)
                if result:
                    NotificationHelper.show_operation_success("등록", generated_code)
                    st.rerun()
                else:
                    NotificationHelper.show_error(message)
                    
            except Exception as e:
                NotificationHelper.show_error(f"등록 중 오류가 발생했습니다: {str(e)}")


def register_hrc_product(master_product_manager, code_generator):
    """HRC 제품 등록"""
    st.markdown("### 🎛️ Controller 제품 등록")
    st.info("Controller 제품을 등록합니다. (HRC-HRCT-TEMP-YC60-Zone01 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        
        from product_category_config_manager import ProductCategoryConfigManager
        config_manager = ProductCategoryConfigManager()
        
        # 1단계: HRC 카테고리 선택 (HRCT/HRCS)
        hrc_categories = ["HRCT", "HRCS"]
        hrc_category = st.selectbox("HRC 카테고리", [""] + hrc_categories, index=0, help="HRCT(온도제어) 또는 HRCS(시간제어) 선택")
        
        # 2단계: 서브카테고리 선택
        if hrc_category == "HRCT":
            sub_categories = config_manager.get_hrct_categories()
        elif hrc_category == "HRCS":
            sub_categories = config_manager.get_hrcs_categories()
        else:
            sub_categories = []
        
        hrc_sub_category = st.selectbox("서브카테고리", [""] + sub_categories, index=0)
        
        # 3단계: 모델 선택
        if hrc_category == "HRCT" and hrc_sub_category:
            models = config_manager.get_hrct_models(hrc_sub_category)
        elif hrc_category == "HRCS" and hrc_sub_category:
            models = config_manager.get_hrcs_models(hrc_sub_category)
        else:
            models = []
        
        model = st.selectbox("모델", [""] + models, index=0)
        
        # 4단계: 존 번호 선택 (공통)
        zones = config_manager.get_hrc_zones()
        zone = st.selectbox("존 번호", [""] + zones, index=0)
        
        # Special 선택 시 수동 입력
        if zone == "Special":
            zone = st.text_input("존 번호 직접 입력", placeholder="예: 24, SP01, CUSTOM 등")
        
        # 모델과 존에 따른 유닛 정보 자동 설정
        unit_info = ""
        if model == "YC60" and zone:
            try:
                zone_num = int(zone)
                if zone_num <= 6:
                    unit_info = "6Z,BOX"
                elif zone_num <= 8:
                    unit_info = "8Z,BOX"
                else:
                    unit_info = "12Z,BOX"
            except ValueError:
                # 숫자가 아닌 경우 (Special 존)
                unit_info = "Custom,BOX"
        elif model == "SNT900" and zone:
            zone_map = {
                "0112": "SN3AM", "1324": "SN6M", "2436": "SN9M", 
                "2560": "SN15M", "4992": "SN23M", "97140": "SN35M"
            }
            unit_info = zone_map.get(zone, "Custom,Unit")
        elif model == "YC60T" and zone:
            try:
                zone_num = int(zone)
                if zone_num <= 6:
                    unit_info = "6Z,BOX"
                elif zone_num <= 8:
                    unit_info = "8Z,BOX"
                else:
                    unit_info = "12Z,BOX"
            except ValueError:
                # 숫자가 아닌 경우 (Special 존)
                unit_info = "Custom,BOX"
        elif model in ["MDS08AT", "MDS08BT"] and zone:
            if zone == "8":
                unit_info = "8Z,Pendant"
            else:
                unit_info = "Custom,Pendant"
        
        if unit_info:
            st.info(f"유닛 정보: {unit_info}")
        
        # Cable 포함/미포함 선택
        cable_included = st.selectbox("Cable 포함 여부", ["", "포함", "미포함"], index=0, help="케이블 포함 여부를 선택하세요")
        
        # 자동 코드 생성
        generated_code = ""
        if hrc_category and model and zone and cable_included:
            # Cable 정보를 코드에 포함
            cable_suffix = "C" if cable_included == "포함" else "NC"
            generated_code = f"{code_generator.generate_hrc_code(hrc_category, model, zone)}-{cable_suffix}"
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
        else:
            st.info("카테고리, 모델, 존, Cable 포함 여부를 모두 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        suggested_vietnamese = ""
        
        if hrc_category and model and zone and cable_included and unit_info:
            cable_text_kr = "케이블 포함" if cable_included == "포함" else "케이블 미포함"
            cable_text_en = "with Cable" if cable_included == "포함" else "without Cable"
            cable_text_vn = "có cáp" if cable_included == "포함" else "không có cáp"
            
            if hrc_category == "TEMP":
                suggested_korean = f"온도 제어기 {model} Zone {zone} {unit_info} ({cable_text_kr})"
                suggested_english = f"Temperature Controller {model} Zone {zone} {unit_info} ({cable_text_en})"
                suggested_vietnamese = f"Bộ điều khiển nhiệt độ {model} Zone {zone} {unit_info} ({cable_text_vn})"
            else:  # TIMER
                suggested_korean = f"타이머 제어기 {model} Zone {zone} {unit_info} ({cable_text_kr})"
                suggested_english = f"Timer Controller {model} Zone {zone} {unit_info} ({cable_text_en})"
                suggested_vietnamese = f"Bộ điều khiển thời gian {model} Zone {zone} {unit_info} ({cable_text_vn})"
        
        product_name_korean = st.text_input("한국어 제품명 *", value=suggested_korean, placeholder="예: 온도 제어기 YC60 Zone 01")
        product_name_english = st.text_input("영어 제품명 *", value=suggested_english, placeholder="예: Temperature Controller YC60 Zone 01")
        product_name_vietnamese = st.text_input("베트남어 제품명", value=suggested_vietnamese, placeholder="예: Bộ điều khiển nhiệt độ YC60 Zone 01")
    
    # 등록 버튼
    if st.button("📝 HRC 제품 등록", type="primary"):
        # 필수 필드 검증
        if not generated_code:
            NotificationHelper.show_error("카테고리, 모델, 존, Cable 포함 여부를 모두 선택해주세요.")
        elif not product_name_korean or not product_name_english:
            NotificationHelper.show_error("한국어 제품명과 영어 제품명은 필수입니다.")
        else:
            try:
                product_data = {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'product_name_vietnamese': product_name_vietnamese,
                    'main_category': 'HRC',
                    'sub_category_hrc': hrc_category,
                    'model': model,
                    'zone': zone,
                    'unit_info': unit_info,
                    'cable_included': cable_included,
                    'unit_of_measure': 'EA',
                    'hs_code': '85371010',
                    'status': 'active',
                    'data_source': 'MANUAL_REGISTRATION'
                }
                
                result, message = master_product_manager.add_product(product_data)
                if result:
                    NotificationHelper.show_operation_success("등록", generated_code)
                    st.rerun()
                else:
                    NotificationHelper.show_error(message)
                    
            except Exception as e:
                NotificationHelper.show_error(f"등록 중 오류가 발생했습니다: {str(e)}")


def register_mb_product(master_product_manager, code_generator):
    """MB 제품 등록"""
    st.markdown("### 🔧 Mold Base 제품 등록")
    st.info("Mold Base 제품을 등록합니다. (MB-2P-SS400-20 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        mb_type = st.selectbox("MB 타입", ["", "2P", "3P", "HR"], index=0, help="2P=2 Plate, 3P=3 Plate, HR=Hot Runner")
        material = st.selectbox("재질", ["", "SS400", "S50C", "SKD61", "NAK80", "P20", "SCM440"], index=0)
        size = st.selectbox("사이즈", ["", "20", "25", "35", "45", "60", "80"], index=0)
        
        # 자동 코드 생성
        generated_code = ""
        if mb_type and material and size:
            generated_code = code_generator.generate_mb_code(mb_type, material, size)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
        else:
            st.info("MB 타입, 재질, 사이즈를 모두 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        if mb_type and material and size:
            suggested_korean = f"몰드베이스 {mb_type} {material} {size}"
            suggested_english = f"Mold Base {mb_type} {material} {size}"
        
        product_name_korean = st.text_input("한국어 제품명 *", value=suggested_korean, placeholder="예: 몰드베이스 2P SS400 20")
        product_name_english = st.text_input("영어 제품명 *", value=suggested_english, placeholder="예: Mold Base 2P SS400 20")
    
    # 등록 버튼
    if st.button("📝 MB 제품 등록", type="primary"):
        # 필수 필드 검증
        if not generated_code:
            NotificationHelper.show_error("MB 타입, 재질, 사이즈를 모두 선택해주세요.")
        elif not product_name_korean or not product_name_english:
            NotificationHelper.show_error("한국어 제품명과 영어 제품명은 필수입니다.")
        else:
            try:
                product_data = {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'main_category': 'MB',
                    'sub_category': mb_type,
                    'material_type': material,
                    'size_primary': size,
                    'unit_of_measure': 'EA',
                    'hs_code': '84809090',
                    'status': 'active',
                    'data_source': 'MANUAL_REGISTRATION'
                }
                
                result, message = master_product_manager.add_product(product_data)
                if result:
                    NotificationHelper.show_operation_success("등록", generated_code)
                    st.rerun()
                else:
                    NotificationHelper.show_error(message)
                    
            except Exception as e:
                NotificationHelper.show_error(f"등록 중 오류가 발생했습니다: {str(e)}")


def register_service_product(master_product_manager, code_generator):
    """SERVICE 제품 등록"""
    st.markdown("### 🔧 서비스 제품 등록")
    st.info("서비스 제품을 등록합니다. (SV-DESIGN-HR 형식)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 제품 코드 구성")
        service_type = st.selectbox("서비스 타입", ["", "DESIGN", "INSTALL", "REPAIR", "MAINTAIN", "TRAINING"], index=0)
        category = st.selectbox("적용 분야", ["", "HR", "MB", "HRC", "GENERAL"], index=0)
        
        # 자동 코드 생성
        generated_code = ""
        if service_type and category:
            generated_code = code_generator.generate_service_code(service_type, category)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
        else:
            st.info("서비스 타입과 적용 분야를 선택하면 제품 코드가 자동 생성됩니다.")
    
    with col2:
        st.markdown("#### 🏷️ 제품 정보")

        
        # 제품명 자동 생성
        suggested_korean = ""
        suggested_english = ""
        if service_type and category:
            service_names = {
                "DESIGN": "설계 서비스",
                "INSTALL": "설치 서비스", 
                "REPAIR": "수리 서비스",
                "MAINTAIN": "유지보수 서비스",
                "TRAINING": "교육 서비스"
            }
            suggested_korean = f"{service_names.get(service_type, service_type)} ({category})"
            suggested_english = f"{service_type.title()} Service ({category})"
        
        product_name_korean = st.text_input("한국어 제품명 *", value=suggested_korean, placeholder="예: 설계 서비스 (HR)")
        product_name_english = st.text_input("영어 제품명 *", value=suggested_english, placeholder="예: Design Service (HR)")
    
    # 등록 버튼
    if st.button("📝 서비스 제품 등록", type="primary"):
        # 필수 필드 검증
        if not generated_code:
            NotificationHelper.show_error("서비스 타입과 적용 분야를 모두 선택해주세요.")
        elif not product_name_korean or not product_name_english:
            NotificationHelper.show_error("한국어 제품명과 영어 제품명은 필수입니다.")
        else:
            try:
                product_data = {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'main_category': 'SERVICE',
                    'sub_category': service_type,
                    'product_variant': category,
                    'unit_of_measure': 'HR',
                    'status': 'active',
                    'data_source': 'MANUAL_REGISTRATION'
                }
                
                result, message = master_product_manager.add_product(product_data)
                if result:
                    NotificationHelper.show_operation_success("등록", generated_code)
                    st.rerun()
                else:
                    NotificationHelper.show_error(message)
                    
            except Exception as e:
                NotificationHelper.show_error(f"등록 중 오류가 발생했습니다: {str(e)}")


def register_spare_product(master_product_manager, code_generator):
    """SPARE 제품 등록"""
    st.markdown("### 🔧 SPARE 부품 등록")
    st.info("다양한 SPARE 부품을 등록합니다.")
    
    # SPARE 타입 선택
    spare_type = st.selectbox(
        "SPARE 부품 타입 *",
        ["", "Heater", "Thermo Couple", "Gate Bush", "Cylinder-ORing Set", "Cylinder-Set", "Valve Pin", "Tip"],
        index=0,
        help="등록할 SPARE 부품의 타입을 선택하세요"
    )
    
    if spare_type == "Heater":
        register_heater_spare(master_product_manager, code_generator)
    elif spare_type == "Thermo Couple":
        register_thermo_couple_spare(master_product_manager, code_generator)
    elif spare_type == "Gate Bush":
        register_gate_bush_spare(master_product_manager, code_generator)
    elif spare_type == "Cylinder-ORing Set":
        register_cylinder_oring_spare(master_product_manager, code_generator)
    elif spare_type == "Cylinder-Set":
        register_cylinder_set_spare(master_product_manager, code_generator)
    elif spare_type == "Valve Pin":
        register_valve_pin_spare(master_product_manager, code_generator)
    elif spare_type == "Tip":
        register_tip_spare(master_product_manager, code_generator)

def register_heater_spare(master_product_manager, code_generator):
    """Heater SPARE 등록"""
    st.markdown("#### 🔥 Heater 등록")
    st.info("Heater: 이미지 사양 기준으로 직경과 길이를 선택하고, 용량(W)을 입력할 수 있습니다.")
    
    # 참조 이미지 표시
    with st.expander("📋 Heater 사양 참조 (클릭하여 보기)"):
        st.markdown("**카트리지 히터 용량표 (220V/240V 기준):**")
        st.image("attached_assets/image_1753958083562.png", caption="카트리지 히터 길이별 용량 사양표", width=600)
        
        st.markdown("**히터 상세 사양:**")
        st.image("attached_assets/image_1753957727368.png", caption="히터 구조 및 공차 (-0.2) 사양", width=700)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 히터 사양 입력**")
        
        # Heater Type 선택
        heater_type = st.selectbox("Heater Type", ["", "Standard", "Cartridge heater"], index=0, help="Standard=일반 히터, Cartridge heater=카트리지 히터")
        
        if heater_type == "Cartridge heater":
            # 카트리지 히터 전용 선택
            st.markdown("**카트리지 히터 사양 선택**")
            
            # 외경 선택 (카트리지 히터 전용)
            diameter_options = ["", "8", "10", "12", "15", "20"]
            diameter = st.selectbox("Ø (외경)", diameter_options, index=0, help="카트리지 히터 외경 (공차: -0.2)")
            
            # 길이 선택 (카트리지 히터 전용)
            length_options = ["", "100", "200", "300", "400", "500"]
            length_str = st.selectbox("L (길이)", length_options, index=0, help="카트리지 히터 길이 (mm)")
            length = int(length_str) if length_str else 0
            
            # 용량 선택 (카트리지 히터 사양표 기준)
            wattage_options = []
            if diameter and length_str:
                # 용량표 기준 옵션 생성
                wattage_ranges = {
                    ("8", "100"): ["100W", "150W", "200W"],
                    ("8", "200"): ["200W", "250W", "300W"],
                    ("8", "300"): ["300W", "400W", "500W"],
                    ("8", "400"): ["300W", "450W", "600W"],
                    ("8", "500"): ["300W", "500W", "700W"],
                    
                    ("10", "100"): ["100W", "150W", "200W"],
                    ("10", "200"): ["200W", "300W", "400W"],
                    ("10", "300"): ["300W", "450W", "600W"],
                    ("10", "400"): ["300W", "500W", "700W"],
                    ("10", "500"): ["300W", "550W", "800W"],
                    
                    ("12", "100"): ["100W", "200W", "300W"],
                    ("12", "200"): ["200W", "300W", "400W"],
                    ("12", "300"): ["300W", "500W", "700W"],
                    ("12", "400"): ["300W", "550W", "800W"],
                    ("12", "500"): ["300W", "650W", "1000W"],
                    
                    ("15", "100"): ["200W", "350W", "500W"],
                    ("15", "200"): ["300W", "500W", "700W"],
                    ("15", "300"): ["300W", "650W", "1000W"],
                    ("15", "400"): ["300W", "700W", "1100W"],
                    ("15", "500"): ["300W", "800W", "1200W"],
                    
                    ("20", "100"): ["300W", "500W", "700W"],
                    ("20", "200"): ["500W", "700W", "900W"],
                    ("20", "300"): ["500W", "750W", "1000W"],
                    ("20", "400"): ["500W", "800W", "1100W"],
                    ("20", "500"): ["300W", "900W", "1500W"]
                }
                
                wattage_options = [""] + wattage_ranges.get((diameter, length_str), [])
            
            wattage_str = st.selectbox("W (용량)", wattage_options, index=0, help="카트리지 히터 용량 (220V/240V 기준)")
            wattage = int(wattage_str.replace("W", "")) if wattage_str and wattage_str != "" else 0
            
        else:
            # Standard 히터 선택
            st.markdown("**Standard 히터 사양 선택**")
            
            # 직경 선택 (Standard 히터용 - 전체 옵션)
            diameter_options = ["", "12", "15", "18", "20", "22", "24", "25", "32", "35", "42", "45"]
            diameter = st.selectbox("Ø (직경)", diameter_options, index=0, help="외경 공차: -0.2")
            
            # 길이 입력
            length = st.number_input("L (길이)", min_value=0, value=0, step=10, help="히터 길이 (mm)")
            
            # 용량 입력 (선택사항)
            wattage = st.number_input("W (용량)", min_value=0, value=0, step=50, help="히터 용량 (W) - 선택사항")
    
    with col2:
        st.markdown("**🔗 제품 정보 생성**")
        
        generated_code = ""
        if diameter and length > 0 and heater_type:
            generated_code = code_generator.generate_spare_code(
                "Heater", 
                diameter=diameter, 
                length=length, 
                heater_type=heater_type,
                wattage=wattage if wattage > 0 else ""
            )
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            # 제품명 자동 생성
            heater_desc = "카트리지 히터" if heater_type == "Cartridge heater" else "히터"
            wattage_desc = f" {wattage}W" if wattage > 0 else ""
            tolerance_desc = f" (외경공차: -0.2)"
            
            product_name_korean = st.text_input("한국어 제품명", value=f"{heater_desc} Ø{diameter} L{length}{wattage_desc}{tolerance_desc}")
            product_name_english = st.text_input("영어 제품명", value=f"{'Cartridge ' if heater_type == 'Cartridge heater' else ''}Heater Ø{diameter} L{length}{wattage_desc}")
            product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Máy sưởi {'cartridge ' if heater_type == 'Cartridge heater' else ''}Ø{diameter} L{length}{wattage_desc}")
        else:
            st.info("히터 타입, Ø, L을 입력하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="")
            product_name_english = st.text_input("영어 제품명", value="")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="")
    
    if st.button("📝 Heater 등록", type="primary", key="register_heater"):
        if generated_code and product_name_korean and product_name_english and heater_type:
            # 사양 정보 구성
            specs_parts = [f'Ø{diameter} L{length}']
            if wattage > 0:
                specs_parts.append(f'{wattage}W')
            if heater_type == "Cartridge heater":
                specs_parts.append('220V/240V')
            specs_parts.append('외경공차: -0.2')
            
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': f'Heater {heater_type}',
                'product_variant': heater_type,
                'size_primary': diameter,
                'size_secondary': str(length),
                'wattage': str(wattage) if wattage > 0 else '',
                'specifications': ' / '.join(specs_parts),
                'tolerance': '-0.2',
                'voltage': '220V/240V' if heater_type == "Cartridge heater" else ''
            })
        else:
            NotificationHelper.show_error("히터 타입, 직경, 길이, 제품명을 모두 입력해주세요.")

def register_thermo_couple_spare(master_product_manager, code_generator):
    """Thermo Couple SPARE 등록"""
    st.markdown("#### 🌡️ Thermo Couple 등록")
    
    # 타입 선택
    tc_type = st.selectbox("Thermo Couple 타입", ["", "N/Z", "M/F"], index=0)
    
    if tc_type == "N/Z":
        st.info("N/Z Thermo Couple: Ø 1.0 또는 1.5 선택, L은 입력")
        col1, col2 = st.columns(2)
        
        with col1:
            diameter = st.selectbox("Ø (직경)", ["", "1.0", "1.5"], index=0)
            length = st.number_input("L (길이)", min_value=0, value=0, step=5)
        
        with col2:
            generated_code = ""
            if diameter and length > 0:
                generated_code = code_generator.generate_spare_code("Thermo Couple", sub_type="N/Z", diameter=diameter, length=length)
                st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
                
                product_name_korean = st.text_input("한국어 제품명", value=f"N/Z 써모커플 Ø{diameter} L{length}")
                product_name_english = st.text_input("영어 제품명", value=f"N/Z Thermo Couple Ø{diameter} L{length}")
                product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Cặp nhiệt điện N/Z Ø{diameter} L{length}")
            else:
                st.info("Ø와 L을 입력하면 제품 코드가 자동 생성됩니다.")
                product_name_korean = st.text_input("한국어 제품명", value="")
                product_name_english = st.text_input("영어 제품명", value="")
                product_name_vietnamese = st.text_input("베트남어 제품명", value="")
        
        if st.button("📝 N/Z Thermo Couple 등록", type="primary", key="register_tc_nz"):
            if generated_code and product_name_korean and product_name_english:
                register_spare_common(master_product_manager, {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'product_name_vietnamese': product_name_vietnamese,
                    'sub_category': 'Thermo Couple N/Z',
                    'size_primary': diameter,
                    'size_secondary': str(length),
                    'specifications': f'N/Z Type Ø{diameter} L{length}'
                })
            else:
                NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")
    
    elif tc_type == "M/F":
        st.info("M/F Thermo Couple: K Type 또는 J Type 선택, L은 입력")
        col1, col2 = st.columns(2)
        
        with col1:
            mf_type = st.selectbox("M/F Type", ["", "K", "J"], index=0, help="K Type=K형 써모커플, J Type=J형 써모커플")
            length = st.number_input("L (길이)", min_value=0, value=0, step=5, key="mf_length")
        
        with col2:
            generated_code = ""
            if mf_type and length > 0:
                generated_code = code_generator.generate_spare_code("Thermo Couple", sub_type="M/F", tc_type=mf_type, length=length)
                st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
                
                product_name_korean = st.text_input("한국어 제품명", value=f"M/F 써모커플 {mf_type} Type L{length}")
                product_name_english = st.text_input("영어 제품명", value=f"M/F Thermo Couple {mf_type} Type L{length}")
                product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Cặp nhiệt điện M/F {mf_type} Type L{length}")
            else:
                st.info("Type과 L을 입력하면 제품 코드가 자동 생성됩니다.")
                product_name_korean = st.text_input("한국어 제품명", value="", key="mf_korean")
                product_name_english = st.text_input("영어 제품명", value="", key="mf_english")
                product_name_vietnamese = st.text_input("베트남어 제품명", value="", key="mf_vietnamese")
        
        if st.button("📝 M/F Thermo Couple 등록", type="primary", key="register_tc_mf"):
            if generated_code and product_name_korean and product_name_english:
                register_spare_common(master_product_manager, {
                    'product_code': generated_code,
                    'product_name_korean': product_name_korean,
                    'product_name_english': product_name_english,
                    'product_name_vietnamese': product_name_vietnamese,
                    'sub_category': 'Thermo Couple M/F',
                    'product_variant': mf_type,
                    'size_secondary': str(length),
                    'specifications': f'M/F {mf_type} Type L{length}'
                })
            else:
                NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_gate_bush_spare(master_product_manager, code_generator):
    """Gate Bush SPARE 등록"""
    st.markdown("#### 🔩 Gate Bush 등록")
    st.info("ST (non O-ring): 20,25,35,45 / Special (O-Ring): 20,25,35,45")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bush_type = st.selectbox("Gate Bush 타입", ["", "ST", "Special"], index=0, help="ST=non O-ring, Special=O-Ring")
        size = st.selectbox("사이즈", ["", "20", "25", "35", "45"], index=0)
    
    with col2:
        generated_code = ""
        if bush_type and size:
            generated_code = code_generator.generate_spare_code("Gate Bush", sub_type=bush_type, size=size)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            # 제품명 자동 생성
            type_desc = "non O-ring" if bush_type == "ST" else "O-Ring"
            product_name_korean = st.text_input("한국어 제품명", value=f"게이트 부시 {bush_type} {size} ({type_desc})")
            product_name_english = st.text_input("영어 제품명", value=f"Gate Bush {bush_type} {size} ({type_desc})")
            product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Ống lót cổng {bush_type} {size} ({type_desc})")
        else:
            st.info("타입과 사이즈를 선택하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="")
            product_name_english = st.text_input("영어 제품명", value="")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="")
    
    if st.button("📝 Gate Bush 등록", type="primary", key="register_gate_bush"):
        if generated_code and product_name_korean and product_name_english:
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': 'Gate Bush',
                'product_variant': bush_type,
                'size_primary': size,
                'specifications': f'{bush_type} Type Size {size}'
            })
        else:
            NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_cylinder_oring_spare(master_product_manager, code_generator):
    """Cylinder O-Ring Set SPARE 등록"""
    st.markdown("#### ⭕ Cylinder O-Ring Set 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cylinder_type = st.selectbox("Cylinder 타입", ["", "GYTJ32", "GYTJ48", "GYTJ58", "GYTJ68", "GYTJ78", "GYTJ88"], index=0)
    
    with col2:
        generated_code = ""
        if cylinder_type:
            generated_code = code_generator.generate_spare_code("Cylinder-ORing Set", cylinder_type=cylinder_type)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            product_name_korean = st.text_input("한국어 제품명", value=f"실린더 O-링 세트 {cylinder_type}")
            product_name_english = st.text_input("영어 제품명", value=f"Cylinder O-Ring Set {cylinder_type}")
            product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Bộ vòng đệm xi lanh {cylinder_type}")
        else:
            st.info("Cylinder 타입을 선택하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="")
            product_name_english = st.text_input("영어 제품명", value="")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="")
    
    if st.button("📝 Cylinder O-Ring Set 등록", type="primary", key="register_cyl_oring"):
        if generated_code and product_name_korean and product_name_english:
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': 'Cylinder O-Ring Set',
                'product_variant': cylinder_type,
                'specifications': f'Cylinder O-Ring Set for {cylinder_type}'
            })
        else:
            NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_cylinder_set_spare(master_product_manager, code_generator):
    """Cylinder Set SPARE 등록"""
    st.markdown("#### 🔧 Cylinder Set 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cylinder_type = st.selectbox("Cylinder 타입", ["", "GYTJ32", "GYTJ48", "GYTJ58", "GYTJ68", "GYTJ78", "GYTJ88"], index=0, key="cyl_set_type")
    
    with col2:
        generated_code = ""
        if cylinder_type:
            generated_code = code_generator.generate_spare_code("Cylinder-Set", cylinder_type=cylinder_type)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            product_name_korean = st.text_input("한국어 제품명", value=f"실린더 세트 {cylinder_type}", key="cyl_set_korean")
            product_name_english = st.text_input("영어 제품명", value=f"Cylinder Set {cylinder_type}", key="cyl_set_english")
            product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Bộ xi lanh {cylinder_type}", key="cyl_set_vietnamese")
        else:
            st.info("Cylinder 타입을 선택하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="", key="cyl_set_korean_empty")
            product_name_english = st.text_input("영어 제품명", value="", key="cyl_set_english_empty")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="", key="cyl_set_vietnamese_empty")
    
    if st.button("📝 Cylinder Set 등록", type="primary", key="register_cyl_set"):
        if generated_code and product_name_korean and product_name_english:
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': 'Cylinder Set',
                'product_variant': cylinder_type,
                'specifications': f'Complete Cylinder Set for {cylinder_type}'
            })
        else:
            NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_valve_pin_spare(master_product_manager, code_generator):
    """Valve Pin SPARE 등록"""
    st.markdown("#### 📌 Valve Pin 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pin_size = st.selectbox("Valve Pin 사이즈", ["", "4", "6", "8", "10"], index=0)
    
    with col2:
        generated_code = ""
        if pin_size:
            generated_code = code_generator.generate_spare_code("Valve Pin", size=pin_size)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            product_name_korean = st.text_input("한국어 제품명", value=f"밸브 핀 {pin_size}")
            product_name_english = st.text_input("영어 제품명", value=f"Valve Pin {pin_size}")
            product_name_vietnamese = st.text_input("베트남어 제품명", value=f"Chốt van {pin_size}")
        else:
            st.info("Valve Pin 사이즈를 선택하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="")
            product_name_english = st.text_input("영어 제품명", value="")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="")
    
    if st.button("📝 Valve Pin 등록", type="primary", key="register_valve_pin"):
        if generated_code and product_name_korean and product_name_english:
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': 'Valve Pin',
                'size_primary': pin_size,
                'specifications': f'Valve Pin Size {pin_size}'
            })
        else:
            NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_tip_spare(master_product_manager, code_generator):
    """Tip SPARE 등록"""
    st.markdown("#### 💡 Tip 등록")
    st.info("Tip: HR 등록과 같은 체계적 선택 방식 - System Type → 제품 타입 → 게이트 타입 → 사이즈")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 제품 코드 구성**")
        
        # System Type 선택
        tip_system = st.selectbox("System Type", ["", "Valve", "Open"], index=0, help="Valve=밸브 타입, Open=오픈 타입")
        
        # 제품 타입 선택 (System Type에 따라 달라짐)
        product_type_options = []
        if tip_system == "Valve":
            product_type_options = ["", "ST", "CP", "PET", "SE", "SIV"]
        elif tip_system == "Open":
            product_type_options = ["", "ST", "CP", "SIO"]
        
        product_type = st.selectbox("제품 타입", product_type_options, index=0, 
                                   help="ST=Standard, CP=Cosmetic & Packaging, PET=PET, SE=Super Engineering, SIV=Single Valve, SIO=Single Open")
        
        # 게이트 타입 선택 (제품 타입에 따라 달라짐)
        gate_type_options = []
        if product_type == "ST":
            if tip_system == "Valve":
                gate_type_options = ["", "MAE", "MCC", "MAA"]
            else:  # Open
                gate_type_options = ["", "MCC", "MEA"]
        elif product_type == "CP":
            if tip_system == "Valve":
                gate_type_options = ["", "VL", "SC"]
            else:  # Open
                gate_type_options = ["", "CL", "CC"]
        elif product_type == "PET":
            gate_type_options = ["", "MCC"]
        elif product_type == "SE":
            gate_type_options = ["", "MAA", "MCC"]
        elif product_type == "SIV":
            gate_type_options = ["", "VSL", "VTC", "VSS", "CVF"]
        elif product_type == "SIO":
            gate_type_options = ["", "RS", "RL"]
        
        gate_type = st.selectbox("게이트 타입", gate_type_options, index=0, 
                                help="게이트 방식 (제품 타입에 따라 선택 가능한 옵션이 달라집니다)")
        
        # 사이즈 선택 (제품 타입에 따라 달라짐)
        size_options = []
        if product_type == "ST":
            size_options = ["", "20", "25", "35", "45"]
        elif product_type == "CP":
            size_options = ["", "12", "15", "18", "22"]
        elif product_type == "PET":
            size_options = ["", "25", "32", "35"]
        elif product_type == "SE":
            size_options = ["", "15", "18", "25"]
        elif product_type in ["SIV", "SIO"]:
            size_options = ["", "24", "32", "42"]
        
        tip_size = st.selectbox("사이즈", size_options, index=0, help="제품 타입별 표준 사이즈 옵션")
    
    with col2:
        st.markdown("**🔗 제품 정보 생성**")
        
        generated_code = ""
        if tip_system and product_type and gate_type and tip_size:
            # Tip 구성: SP-TIP-{System}-{ProductType}-{GateType}-{Size}
            tip_config = f"{tip_system}-{product_type}-{gate_type}-{tip_size}"
            generated_code = code_generator.generate_spare_code("Tip", tip_config=tip_config)
            st.success(f"🔗 생성된 제품 코드: **{generated_code}**")
            
            # 제품명 자동 생성
            system_desc = {"Valve": "밸브", "Open": "오픈"}.get(tip_system, tip_system)
            product_desc = {
                "ST": "Standard", "CP": "Cosmetic & Packaging", "PET": "PET", 
                "SE": "Super Engineering", "SIV": "Single Valve", "SIO": "Single Open"
            }.get(product_type, product_type)
            
            product_name_korean = st.text_input("한국어 제품명", 
                                              value=f"팁 {system_desc} {product_desc} {gate_type} {tip_size}")
            product_name_english = st.text_input("영어 제품명", 
                                                value=f"Tip {tip_system} {product_desc} {gate_type} {tip_size}")
            product_name_vietnamese = st.text_input("베트남어 제품명", 
                                                   value=f"Đầu tip {tip_system} {product_desc} {gate_type} {tip_size}")
        else:
            st.info("모든 항목을 선택하면 제품 코드가 자동 생성됩니다.")
            product_name_korean = st.text_input("한국어 제품명", value="")
            product_name_english = st.text_input("영어 제품명", value="")
            product_name_vietnamese = st.text_input("베트남어 제품명", value="")
    
    if st.button("📝 Tip 등록", type="primary", key="register_tip"):
        if generated_code and product_name_korean and product_name_english:
            register_spare_common(master_product_manager, {
                'product_code': generated_code,
                'product_name_korean': product_name_korean,
                'product_name_english': product_name_english,
                'product_name_vietnamese': product_name_vietnamese,
                'sub_category': 'Tip',
                'product_variant': f'{tip_system} {product_type}',
                'size_primary': tip_size,
                'gate_type': gate_type,
                'specifications': f'{tip_system} {product_type} {gate_type} Size {tip_size}'
            })
        else:
            NotificationHelper.show_error("모든 필수 정보를 입력해주세요.")

def register_spare_common(master_product_manager, product_data):
    """SPARE 제품 공통 등록 처리"""
    try:
        # 공통 필드 추가
        common_data = {
            'main_category': 'SPARE',
            'unit_of_measure': 'EA',
            'status': 'active',
            'data_source': 'MANUAL_REGISTRATION',
            'quotation_available': True,
            'is_standard_product': True,
            'quality_grade': 'A'
        }
        
        # 데이터 병합
        final_data = {**common_data, **product_data}
        
        result, message = master_product_manager.add_product(final_data)
        if result:
            NotificationHelper.show_operation_success("등록", final_data['product_code'])
            st.rerun()
        else:
            NotificationHelper.show_error(message)
            
    except Exception as e:
        NotificationHelper.show_error(f"등록 중 오류가 발생했습니다: {str(e)}")