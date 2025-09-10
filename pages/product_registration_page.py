import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager
from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager

def get_management_rates():
    """관리 환율을 가져옵니다."""
    try:
        rate_manager = SQLiteExchangeRateManager()
        current_year = datetime.now().year
        
        # 현재 연도 관리 환율 조회
        current_year_data = rate_manager.get_yearly_management_rates(current_year)
        
        if current_year_data.empty:
            # 현재 연도 데이터가 없으면 전년도 조회
            previous_year = current_year - 1
            previous_year_data = rate_manager.get_yearly_management_rates(previous_year)
            
            if not previous_year_data.empty:
                # 전년도 데이터가 있으면 사용
                management_rates = {}
                for _, row in previous_year_data.iterrows():
                    management_rates[row['target_currency']] = row['rate']
                return management_rates, previous_year
        else:
            # 현재 연도 데이터 사용
            management_rates = {}
            for _, row in current_year_data.iterrows():
                management_rates[row['target_currency']] = row['rate']
            return management_rates, current_year
        
        # 데이터가 없으면 기본값 반환 (World Bank WDI 기준)
        return {
            'KRW': 1363.4,
            'CNY': 7.2,
            'VND': 24164.9,
            'THB': 35.3,
            'IDR': 15855.4
        }, current_year
        
    except Exception as e:
        print(f"관리 환율 조회 오류: {e}")
        # 오류 시 기본값 반환 (World Bank WDI 기준)
        return {
            'KRW': 1363.4,
            'CNY': 7.2,
            'VND': 24164.9,
            'THB': 35.3,
            'IDR': 15855.4
        }, datetime.now().year

def get_english_name_from_system_settings(product_code):
    """시스템 설정에서 제품 코드의 영어명을 조회합니다. 사용자가 직접 입력한 데이터만 사용합니다."""
    if not product_code:
        return None
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        # 제품 코드의 첫 번째 부분에서 제품명 조회
        parts = product_code.split('-')
        if not parts:
            return None
            
        first_part = parts[0]  # HR, CON, HRC 등
        
        # 모든 카테고리의 level1에서 해당 코드의 제품명 조회
        # "제품명"이 아닌 실제 사용자가 입력한 제품명만 반환
        cursor.execute('''
            SELECT description
            FROM multi_category_components
            WHERE component_key = ? AND component_level = 'level1' 
            AND is_active = 1 AND description != '제품명'
            LIMIT 1
        ''', (first_part,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        
        return None
            
    except Exception as e:
        print(f"시스템 설정 영어명 조회 오류: {e}")
        return None

def get_product_names_from_code(product_code):
    """제품 코드에서 시스템 설정의 영어명과 마스터 제품의 베트남어명을 반환합니다."""
    if not product_code:
        return {"en": None, "vi": None}
    
    try:
        import sqlite3
        
        # 시스템 설정에서 영어명 조회
        english_name = get_english_name_from_system_settings(product_code)
        
        # 마스터 제품에서 베트남어명 조회
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name_vi
            FROM master_products 
            WHERE product_code = ? 
            LIMIT 1
        ''', (product_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        vietnamese_name = result[0] if result and result[0] else None
        
        return {
            "en": english_name,
            "vi": vietnamese_name
        }
            
    except Exception as e:
        print(f"제품명 조회 오류: {e}")
        return {"en": None, "vi": None}

def get_product_name_from_code(product_code):
    """제품 코드에서 마스터 제품 데이터베이스에 등록된 제품명을 반환합니다."""
    names = get_product_names_from_code(product_code)
    # 영어 > 베트남어 순으로 우선순위 (실제 등록된 것만)
    return names["en"] or names["vi"]



def reset_product_form():
    """제품 등록 폼 리셋 함수"""
    # 선택 관련 세션 상태 초기화
    reset_keys = [
        'selected_catalog_prod_reg',
        'selected_code_prod_reg',
        'product_name_en_prod_reg',
        'product_name_vi_prod_reg',
        'supplier_prod_reg',
        'unit_prod_reg',
        'supply_currency_prod_reg',
        'supply_price_prod_reg',
        'exchange_rate_prod_reg',
        'sales_price_vnd_prod_reg'
    ]
    
    for key in reset_keys:
        if key in st.session_state:
            del st.session_state[key]

def show_product_registration_page(master_product_manager, finished_product_manager, product_code_manager, user_permissions, get_text):
    """제품 등록 페이지"""
    # 매니저가 전달되지 않은 경우 초기화
    if not master_product_manager:
        from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
        master_product_manager = SQLiteMasterProductManager()
    
    # 탭 생성
    tab1, tab2 = st.tabs(["제품 등록", "등록된 제품"])
    
    with tab1:
        show_product_registration(master_product_manager)
    
    with tab2:
        show_registered_products(master_product_manager)

def show_product_registration(master_product_manager):
    """제품 등록 폼"""
    
    # 환율 안내문 추가
    st.info("📋 **안내사항**: 제품 등록시 사용되는 환율은 관리 환율을 적용한다")
    
    # 완성된 제품 코드 목록 가져오기
    completed_codes = get_completed_product_codes()
    
    if not completed_codes:
        st.warning("⚠️ 제품 코드가 없습니다. 시스템 설정에서 먼저 코드를 생성해주세요.")
        return
    
    # 공급업체 목록 가져오기
    supplier_list = get_supplier_list()
    
    # 제품 코드 선택
    col1, col2 = st.columns(2)
    
    categories = list(set([item['category'] for item in completed_codes]))
    
    # 동적 카탈로그 매핑 생성
    category_mapping = {}
    for category in categories:
        if 'Category A' in category:
            category_mapping['카탈로그 A'] = category
        elif 'Category B' in category:
            category_mapping['카탈로그 B'] = category
        elif 'Category C' in category:
            category_mapping['카탈로그 C'] = category
        elif 'Category D' in category:
            category_mapping['카탈로그 D'] = category
        elif 'Category E' in category:
            category_mapping['카탈로그 E'] = category
        elif 'Category F' in category:
            category_mapping['카탈로그 F'] = category
        elif 'Category G' in category:
            category_mapping['카탈로그 G'] = category
        elif 'Category H' in category:
            category_mapping['카탈로그 H'] = category
        elif 'Category I' in category:
            category_mapping['카탈로그 I'] = category
    
    selected_code = None
    
    if category_mapping:
        with col1:
            catalog_options = ["카탈로그 선택"] + list(category_mapping.keys())
            selected_catalog = st.selectbox("카탈로그", catalog_options, key="selected_catalog_prod_reg")
        
        if selected_catalog and selected_catalog != "카탈로그 선택":
            selected_category = category_mapping[selected_catalog]
            catalog_codes = [item for item in completed_codes if item['category'] == selected_category]
            
            with col2:
                if catalog_codes:
                    code_options = ["제품 코드 선택"] + [item['code'] for item in catalog_codes]
                    selected_code = st.selectbox(f"제품 코드 ({len(catalog_codes)}개)", code_options, key="selected_code_prod_reg")
                    
                    if selected_code and selected_code != "제품 코드 선택":
                        st.success(f"✅ {selected_code}")
                    else:
                        selected_code = None
                else:
                    st.warning("코드가 없습니다")
                    selected_code = None
    
    # 환율 관리 연동 버튼 (form 밖에 위치)
    if selected_code:
        col_info, col_mgmt = st.columns([3, 1])
        with col_info:
            st.write(f"**등록할 제품**: `{selected_code}`")
        with col_mgmt:
            if st.button("🔧 환율 관리", key="goto_exchange_mgmt", help="환율 관리 메뉴로 이동"):
                st.session_state.selected_system = "exchange_rate_management"
                st.rerun()
    
    # 제품 정보 입력 (form 제거하여 실시간 업데이트 가능)
    if selected_code:
        # 환율 매니저 초기화
        rate_manager = SQLiteExchangeRateManager()
        
        # 기존 데이터에서 추천 옵션 생성
        try:
            master_product_manager = SQLiteMasterProductManager()
            existing_products = master_product_manager.get_master_products()
            
            # 베트남어 제품명만 추천 데이터로 수집 (중복 제거 및 유효성 검사 강화)
            product_names_vi = sorted(list(set([
                name.strip() for name in existing_products['product_name_vi'].dropna() 
                if name and isinstance(name, str) and name.strip() and len(name.strip()) > 2
            ])))
            supplier_names = sorted(list(set([
                name.strip() for name in existing_products['supplier_name'].dropna() 
                if name and isinstance(name, str) and name.strip() and len(name.strip()) > 2
            ])))
            
            # 추천 목록 크기 제한 (최대 10개)
            product_names_vi = product_names_vi[:10]
            supplier_names = supplier_names[:10]
        except:
            product_names_vi = []
            supplier_names = []
        
        # 선택된 제품 코드에서 실제 등록된 제품명만 조회
        auto_product_names = get_product_names_from_code(selected_code)
        auto_product_name = get_product_name_from_code(selected_code)
        
        # 기본 정보
        st.subheader("📝 제품 정보 입력")
        
        # 영어명 등록 상태 표시
        if auto_product_names["en"]:
            st.success(f"✅ 코드 `{selected_code}`의 영어명: **{auto_product_names['en']}**")
        else:
            st.warning(f"⚠️ 코드 `{selected_code}`의 영어명이 시스템 설정에 등록되지 않았습니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            # 영어명은 자동으로 표시 (시스템 설정에서 관리됨)
            if auto_product_names["en"]:
                # 자동으로 가져온 영어명을 읽기 전용으로 표시
                st.text_input(
                    "제품명 (영어)", 
                    value=auto_product_names["en"],
                    disabled=True,
                    help="시스템 설정에서 관리되는 제품명입니다."
                )
                product_name_en = auto_product_names["en"]
            else:
                # 등록된 영어명이 없는 경우 안내 메시지
                st.text_input(
                    "제품명 (영어)", 
                    value="시스템 설정에서 등록 필요",
                    disabled=True,
                    help="이 제품 코드의 영어명은 시스템 설정에서 먼저 등록해야 합니다."
                )
                product_name_en = ""
            
            # 공급업체 선택 (YMK를 기본값으로 설정)
            all_suppliers = []
            
            # YMK를 첫 번째로 추가
            all_suppliers.append("YMK")
            
            # 기존 supplier_list에서 추가 (YMK 제외)
            for s in supplier_list:
                if s and s != "공급업체 선택" and s.strip() not in all_suppliers and s.strip() != "YMK":
                    all_suppliers.append(s.strip())
            # 추천 supplier_names에서 추가 (중복 없이, YMK 제외)
            for s in supplier_names:
                if s and s.strip() not in all_suppliers and s.strip() != "YMK":
                    all_suppliers.append(s.strip())
            
            # YMK를 제외한 나머지 정렬
            other_suppliers = sorted(all_suppliers[1:])
            all_suppliers = ["YMK"] + other_suppliers
                
            supplier_name = st.selectbox("공급업체", all_suppliers, index=0, key="supplier_prod_reg")
            
        with col2:
            # 베트남어명은 사용자가 입력 (기존 값이 있으면 표시)
            default_name_vi = auto_product_names["vi"] if auto_product_names["vi"] else ""
            
            # 베트남어 제품명 추천 옵션 (항상 표시)
            if product_names_vi:
                st.caption("💡 추천 제품명:")
                selected_recommend_vi = st.selectbox(
                    "추천에서 선택 (선택사항)", 
                    ["선택하지 않음"] + product_names_vi, 
                    key="recommend_name_vi_prod_reg",
                    help="추천 제품명을 선택하면 아래 입력란에 자동 입력됩니다"
                )
                # 추천 선택 시 value 설정
                if selected_recommend_vi != "선택하지 않음":
                    default_name_vi = selected_recommend_vi
                
            # 제품명 베트남어 입력 (사용자가 직접 입력)
            product_name_vi = st.text_input(
                "제품명 (베트남어)", 
                value=default_name_vi,
                placeholder="Tên tiếng Việt", 
                key="product_name_vi_prod_reg",
                help="제품의 베트남어명을 입력하세요."
            )
                    
            unit = st.selectbox("단위", ["EA", "SET", "KG", "M", "L"], index=0, key="unit_prod_reg")
        
        # 가격 정보
        st.subheader("💰 가격 정보")
        
        # 환율 자동 업데이트 시스템
        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1, 1.5, 1.5])
        with col1:
            supply_currency = st.selectbox("공급가 통화", ["USD", "CNY", "VND", "KRW"], key="supply_currency_prod_reg")
        with col2:
            supply_price = st.number_input("공급가", min_value=0.0, step=1.0, key="supply_price_prod_reg")
        with col3:
            # 연도 선택 드롭다운
            current_year = datetime.now().year
            year_options = list(range(current_year, current_year - 5, -1))  # 최근 5년
            selected_year = st.selectbox("환율 연도", year_options, key="exchange_year_prod_reg")
        
        with col4:
            # 환율 자동 업데이트 시스템 (Streamlit의 컴포넌트 반응성 활용)
            auto_exchange_rate = None
            help_text = ""
            
            try:
                if supply_currency != "VND":
                    # DB에서 관리 환율 조회 (통화/연도 변경 시마다 실행)
                    auto_exchange_rate = rate_manager.get_management_rate_by_year_currency(selected_year, supply_currency)
                    
                    if auto_exchange_rate and auto_exchange_rate > 0:
                        help_text = f"✅ 자동 적용: {selected_year}년 {supply_currency} 관리 환율 ({auto_exchange_rate:,.2f})"
                    else:
                        # 기본값 설정 (관리 환율이 없는 경우)
                        default_rates = {"USD": 24000.0, "CNY": 3400.0, "KRW": 18.0}
                        auto_exchange_rate = default_rates.get(supply_currency, 24000.0)
                        help_text = f"⚠️ 관리 환율 없음: {selected_year}년 {supply_currency} 기본값 적용 ({auto_exchange_rate:,.2f})"
                else:
                    auto_exchange_rate = 1.0  # VND인 경우
                    help_text = "VND → VND (동일 통화)"
                        
            except Exception as e:
                # 오류 발생 시 기본값 사용
                default_rates = {"USD": 24000.0, "CNY": 3400.0, "KRW": 18.0, "VND": 1.0}
                auto_exchange_rate = default_rates.get(supply_currency, 24000.0)
                help_text = f"❌ 오류: 기본값 사용 ({auto_exchange_rate:,.2f})"
            
            # 환율 입력 필드 (동적 키 방식으로 자동 업데이트)
            # 통화와 연도 조합으로 고유 키 생성하여 위젯 재생성 유도
            dynamic_key = f"exchange_rate_{supply_currency}_{selected_year}_prod_reg"
            
            if supply_currency != "VND":
                exchange_rate = st.number_input(
                    "환율 (→VND)", 
                    min_value=0.0, 
                    value=float(auto_exchange_rate), 
                    step=100.0,
                    help=help_text, 
                    key=dynamic_key  # 동적 키 사용 - 통화/연도 변경시 새 위젯 생성
                )
            else:
                exchange_rate = 1.0
                st.number_input(
                    "환율 (→VND)", 
                    value=1.0, 
                    disabled=True, 
                    help=help_text, 
                    key=f"exchange_rate_vnd_{selected_year}_prod_reg"  # VND도 동적 키 사용
                )
        with col5:
            # 판매가는 환율과 독립적으로 입력받음
            sales_price_vnd = st.number_input("판매가 (VND)", min_value=0.0, step=1000.0, key="sales_price_vnd_prod_reg")
        
        # 환율 계산값을 실시간으로 표시 (form 밖에서)
        if supply_price > 0 and exchange_rate > 0:
            calculated_vnd = supply_price * exchange_rate
            st.info(f"💡 **환율 계산값**: {calculated_vnd:,.0f} VND")
        
        # 관리 환율 정보 표시
        st.markdown("---")
        st.markdown("### 📊 관리 환율 참고")
        
        # 관리 환율 테이블 표시
        try:
                # 전체 데이터를 가져와서 피벗 테이블 형태로 표시
            all_management_data = rate_manager.get_yearly_management_rates()
            
            if all_management_data.empty:
                # 데이터가 없는 경우 - 빈 테이블 구조만 표시
                empty_data = pd.DataFrame({
                    '연도': [],
                    'CNY (CN)': [],
                    'VND (VN)': [],
                    'THB (TH)': [],
                    'KRW (KR)': [],
                    'IDR (ID)': []
                })
                st.dataframe(empty_data, use_container_width=True, hide_index=True)
            else:
                # 피벗 테이블 생성
                pivot_data = all_management_data.pivot_table(
                    values='rate',
                    index='year',
                    columns='target_currency',
                    aggfunc='first'
                ).reset_index()
                
                # 연도순 정렬 (최신년도 상단)
                pivot_data = pivot_data.sort_values('year', ascending=False)
                
                # 통화 컬럼 순서 정렬
                currency_columns = [col for col in pivot_data.columns if col != 'year']
                # 이미지 순서대로 정렬: CNY, VND, THB, KRW, IDR
                preferred_order = ['CNY', 'VND', 'THB', 'KRW', 'IDR']
                sorted_columns = []
                for currency in preferred_order:
                    if currency in currency_columns:
                        sorted_columns.append(currency)
                # 나머지 통화 추가
                for currency in currency_columns:
                    if currency not in sorted_columns:
                        sorted_columns.append(currency)
                
                # 컬럼 순서 재배치
                ordered_columns = ['year'] + sorted_columns
                pivot_data = pivot_data[ordered_columns]
                
                # 컬럼명 변경
                column_names = {'year': '연도'}
                country_code_map = {
                    'CNY': 'CNY (CN)',
                    'VND': 'VND (VN)', 
                    'THB': 'THB (TH)',
                    'KRW': 'KRW (KR)',
                    'IDR': 'IDR (ID)'
                }
                
                for col in sorted_columns:
                    column_names[col] = country_code_map.get(col, col)
                
                # 컬럼명 변경
                pivot_data = pivot_data.rename(columns=column_names)
                
                # NaN 값을 '0.00'으로 처리하고 숫자 포맷 적용
                for col in pivot_data.columns:
                    if col != '연도':
                        pivot_data[col] = pivot_data[col].fillna(0).astype(float).map(
                            lambda x: f"{x:.2f}"
                        )
                
                # 테이블 표시
                st.dataframe(pivot_data, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"환율 데이터 조회 중 오류가 발생했습니다: {str(e)}")
        
        # 등록 버튼
        if st.button("✅ 제품 등록", key="register_product_btn", type="primary", use_container_width=True):
            # 필수 항목 확인
            if not product_name_en or not product_name_vi or not supplier_name:
                st.error("제품명과 공급업체는 필수입니다.")
                return
            
            # 중복 코드 확인 (활성 상태만)
            try:
                existing_products = master_product_manager.get_master_products()
                if not existing_products.empty:
                    active_codes = existing_products[existing_products['status'] == 'active']['product_code'].tolist()
                    if selected_code in active_codes:
                        st.error(f"❌ 제품 코드 '{selected_code}'는 이미 등록되어 있습니다. 다른 코드를 선택하거나 기존 제품을 삭제한 후 등록해주세요.")
                        return
            except Exception as e:
                st.warning(f"중복 확인 중 오류: {str(e)}")
            
            try:
                # 제품 데이터 구성 (master_product_id 자동 생성)
                from datetime import datetime as dt
                master_product_id = f"MP_{selected_code.replace('-', '_')}_{dt.now().strftime('%Y%m%d%H%M%S')}"
                
                # 선택된 코드에서 카테고리 정보 추출 (completed_codes에서 가져옴)
                selected_item = None
                for item in completed_codes:
                    if item['code'] == selected_code:
                        selected_item = item
                        break
                
                # 카테고리 정보 설정 (코드 생성 시 포함된 정보 우선 사용)
                if selected_item and 'category_type' in selected_item:
                    category_name = f"카테고리{selected_item['category_type']}"
                else:
                    # 백업: 패턴 기반 분류 (임시)
                    auto_category = get_category_from_product_code_pattern(selected_code)
                    if auto_category != "미분류":
                        category_name = f"카테고리{auto_category}"
                    else:
                        category_name = None
                
                # generated_product_codes 테이블에서 코드 상태 업데이트
                try:
                    conn = sqlite3.connect('erp_system.db')
                    cursor = conn.cursor()
                    
                    # 기존 code_id 사용 (이미 시스템 설정에서 생성됨)
                    code_id = selected_item['code_id'] if selected_item and 'code_id' in selected_item else None
                    
                    if code_id:
                        # 기존 레코드 업데이트 (status = used, product_name 추가)
                        cursor.execute('''
                            UPDATE generated_product_codes 
                            SET product_name = ?, status = ?
                            WHERE code_id = ?
                        ''', (product_name_en, 'used', code_id))
                    else:
                        # 백업: 새 코드 정보 저장 (기존 방식)
                        from datetime import datetime as dt
                        code_id = f"PC_{selected_code.replace('-', '_')}_{dt.now().strftime('%Y%m%d%H%M%S')}"
                        
                        category_type = selected_item.get('category_type', auto_category) if selected_item else auto_category
                        
                        cursor.execute('''
                            INSERT INTO generated_product_codes 
                            (code_id, product_code, category, category_type, product_name, status, created_date, created_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (code_id, selected_code, 
                              selected_item.get('category', f'Category {auto_category}') if selected_item else f'Category {auto_category}',
                              category_type, product_name_en, 'used', 
                              dt.now().isoformat(), 'system'))
                    
                    conn.commit()
                    conn.close()
                    print(f"코드 정보 DB 저장 완료: {code_id}")
                except Exception as e:
                    print(f"제품 코드 정보 저장 중 오류: {e}")
                
                product_data = {
                    'master_product_id': master_product_id,
                    'product_code': selected_code,
                    'product_name': product_name_en,
                    'product_name_en': product_name_en,
                    'product_name_vi': product_name_vi,
                    'supplier_name': supplier_name,
                    'category_name': category_name,  # 자동 카테고리 추가
                    'unit': unit,
                    'supply_currency': supply_currency,
                    'supply_price': supply_price,
                    'exchange_rate': exchange_rate,
                    'sales_price_vnd': sales_price_vnd,
                    'status': 'active'
                }
                
                # 시스템 설정 기반 카테고리 자동 분류
                category_from_system = get_category_from_system_settings(selected_code)
                if category_from_system != "미분류":
                    product_data['category_name'] = f"카테고리{category_from_system}"
                else:
                    product_data['category_name'] = "미분류"
                
                # add_master_product 메서드 반환값 처리
                result = master_product_manager.add_master_product(product_data)
                
                # 반환값이 튜플인지 단일값인지 확인
                if isinstance(result, tuple):
                    success, message = result
                    if success:
                        st.success(f"✅ 제품 등록 완료: {selected_code} (Category {category_from_system})")
                        # 폼 리셋을 위한 세션 상태 초기화
                        reset_product_form()
                        st.rerun()
                    else:
                        st.error(f"❌ 등록 실패: {message}")
                elif isinstance(result, bool):
                    if result:
                        st.success(f"✅ 제품 등록 완료: {selected_code}")
                        # 폼 리셋을 위한 세션 상태 초기화
                        reset_product_form()
                        st.rerun()
                    else:
                        st.error("❌ 제품 등록에 실패했습니다.")
                else:
                    # 문자열이나 기타 반환값
                    st.success(f"✅ 제품 등록 완료: {selected_code}")
                    # 폼 리셋을 위한 세션 상태 초기화
                    reset_product_form()
                    st.rerun()
                    
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                print(f"제품 등록 오류 상세: {e}")
    else:
        st.info("제품 코드를 선택해주세요.")

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
    """시스템 설정에서 제품 코드의 카테고리 정보를 가져옵니다. (DB 저장 정보 우선, 패턴 보조)"""
    try:
        # 1순위: generated_product_codes 테이블에서 저장된 카테고리 정보 조회
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT category_type FROM generated_product_codes WHERE product_code = ?', (product_code,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        
        # 2순위: 제품 코드 패턴 기반 분류 (임시 백업)
        pattern_category = get_category_from_product_code_pattern(product_code)
        if pattern_category != "미분류":
            return pattern_category
        
        # 2순위: 기존 시스템 설정 기반 분류 (복잡한 매칭)
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

def convert_category_display(category_name):
    """카테고리명을 A, B, C 형태로 변환"""
    if not category_name or category_name == "미분류":
        return "미분류"
    
    # Category A, Category B 형태를 A, B로 변환
    if "Category A" in category_name:
        return "A"
    elif "Category B" in category_name:
        return "B"
    elif "Category C" in category_name:
        return "C"
    elif "Category D" in category_name:
        return "D"
    elif "Category E" in category_name:
        return "E"
    elif "Category F" in category_name:
        return "F"
    elif "Category G" in category_name:
        return "G"
    elif "Category H" in category_name:
        return "H"
    elif "Category I" in category_name:
        return "I"
    
    return category_name

def show_registered_products(master_product_manager):
    """등록된 제품 목록 (A~I 모든 카테고리별 탭으로 구성)"""
    try:
        # 올바른 메서드명 사용
        master_products = master_product_manager.get_master_products()
        
        # 전체 제품 수 표시
        total_products = len(master_products) if not master_products.empty else 0
        st.subheader(f"📋 등록된 제품 ({total_products}개)")
        
        # CSS로 간격 줄이기
        st.markdown("""
        <style>
        .product-row {
            margin-bottom: 5px !important;
            padding: 5px 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 모든 카테고리 순서 정의 (A~I + 미분류)
        all_categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', '미분류']
        
        # 각 카테고리별 제품 분류
        categorized_products = {}
        for category in all_categories:
            categorized_products[category] = []
        
        # 등록된 제품을 카테고리별로 분류 (시스템 설정 기반)
        if not master_products.empty:
            for index, product in master_products.iterrows():
                product_code = product.get('product_code', '')
                # 1순위: 저장된 카테고리 정보 사용
                stored_category = product.get('category_name', '')
                if stored_category and stored_category != '':
                    # 카테고리A -> A, 카테고리B -> B로 변환
                    if '카테고리' in stored_category:
                        category_letter = stored_category.replace('카테고리', '')
                        if category_letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                            categorized_products[category_letter].append(product)
                            continue
                
                # 2순위: 시스템 설정에서 카테고리 정보 가져오기
                category_type = get_category_from_system_settings(product_code)
                
                if category_type in categorized_products:
                    categorized_products[category_type].append(product)
                else:
                    # 시스템 설정에 없는 코드는 미분류로 처리
                    categorized_products['미분류'].append(product)
        
        # 모든 카테고리 탭 생성 (순서대로) - Category A, Category B 형식
        tab_names = []
        for category in all_categories:
            product_count = len(categorized_products[category])
            if category == '미분류':
                tab_names.append(f"미분류 ({product_count}개)")
            else:
                tab_names.append(f"Category {category} ({product_count}개)")
        
        tabs = st.tabs(tab_names)
        
        # 각 탭에서 해당 카테고리 제품 표시
        for i, category in enumerate(all_categories):
            products = categorized_products[category]
            with tabs[i]:
                st.markdown(f"### 📂 카테고리 {category}")
                
                if products:
                    # 제품이 있는 경우
                    show_products_by_category(products, master_product_manager)
                else:
                    # 제품이 없는 경우 안내 메시지
                    st.info(f"카테고리 {category}에 등록된 제품이 없습니다.")
                    st.markdown("**등록 방법:**")
                    st.markdown("1. 시스템 설정에서 카테고리 제품 코드를 생성하세요")
                    st.markdown("2. '제품 등록' 탭에서 해당 코드로 제품을 등록하세요")
            
    except Exception as e:
        st.error(f"제품 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
        print(f"제품 목록 오류 상세: {e}")

def show_products_by_category(products, master_product_manager):
    """특정 카테고리의 제품들을 표시"""
    for product in products:
        # 제품 정보를 한 줄로 구성
        product_name = product.get('product_name_en') or product.get('product_name_vi') or 'N/A'
        sales_price = product.get('sales_price_vnd', 0)
        supply_price = product.get('supply_price', 0)
        supply_currency = product.get('supply_currency', 'CNY')
        
        # 가격 정보 구성 (판매가 + 공급가)
        sales_text = f"{sales_price:,.0f} VND" if sales_price > 0 else "판매가 미설정"
        supply_text = f"{supply_price:,.2f} {supply_currency}" if supply_price > 0 else "공급가 미설정"
        price_text = f"💰 {sales_text} | 📦 {supply_text}"
        
        # 한 줄로 표시 (세로 간격 최소화)
        col1, col2, col3 = st.columns([7, 1, 1])
        
        with col1:
            # 시스템 설정 기반 카테고리 정보
            product_code = product.get('product_code', '')
            category_display = get_category_from_system_settings(product_code)
            st.markdown(f"**🏷️ {product['product_code']}** | 📝 {product_name} | {price_text}", 
                      help=f"제품코드: {product['product_code']} | 카테고리: {category_display}")
        
        with col2:
            # 수정 버튼
            if st.button("✏️ 수정", key=f"edit_{product['master_product_id']}", use_container_width=True):
                st.session_state[f"edit_mode_{product['master_product_id']}"] = True
                st.rerun()
            
        with col3:
            # 삭제 버튼
            if st.button("🗑️ 삭제", key=f"delete_{product['master_product_id']}", use_container_width=True, type="secondary"):
                if st.session_state.get(f"confirm_delete_{product['master_product_id']}", False):
                    # 실제 완전 삭제 실행
                    try:
                        result = master_product_manager.delete_master_product(
                            product['master_product_id'], 
                            hard_delete=True
                        )
                        if result:
                            st.success(f"✅ 제품 완전 삭제 완료: {product['product_code']}")
                            if f"confirm_delete_{product['master_product_id']}" in st.session_state:
                                del st.session_state[f"confirm_delete_{product['master_product_id']}"]
                            st.rerun()
                        else:
                            st.error("❌ 삭제 실패")
                    except Exception as e:
                        st.error(f"❌ 삭제 중 오류: {str(e)}")
                else:
                    # 삭제 확인 요청
                    st.session_state[f"confirm_delete_{product['master_product_id']}"] = True
                    st.rerun()
        
        # 삭제 확인 메시지
        if st.session_state.get(f"confirm_delete_{product['master_product_id']}", False):
            st.warning(f"⚠️ '{product['product_code']}' 제품을 정말 삭제하시겠습니까? 삭제 버튼을 다시 클릭하세요.")
            col_cancel, _ = st.columns([1, 3])
            with col_cancel:
                if st.button("❌ 취소", key=f"cancel_delete_{product['master_product_id']}"):
                    del st.session_state[f"confirm_delete_{product['master_product_id']}"]
                    st.rerun()
        
        # 수정 모드
        if st.session_state.get(f"edit_mode_{product['master_product_id']}", False):
            show_edit_product_form(master_product_manager, product)

def show_edit_product_form(master_product_manager, product):
    """제품 수정 폼"""
    with st.expander("✏️ 제품 정보 수정", expanded=True):
        with st.form(f"edit_form_{product['master_product_id']}"):
            st.write(f"**수정할 제품**: `{product['product_code']}`")
            
            # 기본 정보
            col1, col2 = st.columns(2)
            with col1:
                product_name_en = st.text_input(
                    "제품명 (영어)", 
                    value=product.get('product_name_en', ''),
                    key=f"edit_name_en_{product['master_product_id']}"
                )
                supplier_name = st.text_input(
                    "공급업체", 
                    value=product.get('supplier_name', ''),
                    key=f"edit_supplier_{product['master_product_id']}"
                )
                
            with col2:
                product_name_vi = st.text_input(
                    "제품명 (베트남어)", 
                    value=product.get('product_name_vi', ''),
                    key=f"edit_name_vi_{product['master_product_id']}"
                )
                unit_options = ["EA", "SET", "KG", "M", "L"]
                current_unit = product.get('unit', 'EA')
                unit_index = unit_options.index(current_unit) if current_unit in unit_options else 0
                unit = st.selectbox(
                    "단위", 
                    unit_options, 
                    index=unit_index,
                    key=f"edit_unit_{product['master_product_id']}"
                )
            
            # 가격 정보
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                currency_options = ["CNY", "USD", "VND", "KRW"]
                current_currency = product.get('supply_currency', 'CNY')
                currency_index = currency_options.index(current_currency) if current_currency in currency_options else 0
                supply_currency = st.selectbox(
                    "공급가 통화", 
                    currency_options, 
                    index=currency_index,
                    key=f"edit_currency_{product['master_product_id']}"
                )
            with col2:
                supply_price = st.number_input(
                    "공급가", 
                    min_value=0.0, 
                    value=float(product.get('supply_price', 0)),
                    step=1000.0,
                    key=f"edit_supply_price_{product['master_product_id']}"
                )
            with col3:
                exchange_rate = st.number_input(
                    "환율 (→VND)", 
                    min_value=0.0, 
                    value=float(product.get('exchange_rate', 24000)),
                    step=100.0,
                    key=f"edit_exchange_rate_{product['master_product_id']}"
                )
            with col4:
                calculated_vnd = supply_price * exchange_rate if supply_price > 0 and exchange_rate > 0 else 0.0
                sales_price_vnd = st.number_input(
                    "판매가 (VND)", 
                    min_value=0.0, 
                    value=float(product.get('sales_price_vnd', calculated_vnd)),
                    step=1000.0,
                    key=f"edit_sales_price_{product['master_product_id']}"
                )
            
            # 버튼
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 저장", use_container_width=True, type="primary")
            with col2:
                cancelled = st.form_submit_button("❌ 취소", use_container_width=True)
            
            if submitted:
                # 필수 항목 확인
                if not product_name_en or not product_name_vi or not supplier_name:
                    st.error("제품명과 공급업체는 필수입니다.")
                    return
                
                try:
                    # 수정할 데이터 구성
                    updates = {
                        'product_name': product_name_en,
                        'product_name_en': product_name_en,
                        'product_name_vi': product_name_vi,
                        'supplier_name': supplier_name,
                        'unit': unit,
                        'supply_currency': supply_currency,
                        'supply_price': supply_price,
                        'exchange_rate': exchange_rate,
                        'sales_price_vnd': sales_price_vnd
                    }
                    
                    # 제품 정보 업데이트
                    result = master_product_manager.update_master_product(
                        product['master_product_id'], 
                        updates
                    )
                    
                    if result:
                        st.success(f"✅ 제품 정보 수정 완료: {product['product_code']}")
                        # 수정 모드 해제
                        del st.session_state[f"edit_mode_{product['master_product_id']}"]
                        st.rerun()
                    else:
                        st.error("❌ 수정 실패")
                        
                except Exception as e:
                    st.error(f"수정 중 오류 발생: {str(e)}")
                    print(f"제품 수정 오류 상세: {e}")
            
            if cancelled:
                # 수정 모드 해제
                del st.session_state[f"edit_mode_{product['master_product_id']}"]
                st.rerun()

def get_completed_product_codes():
    """모든 카테고리(A~I)에서 6단계 조합을 생성합니다."""
    try:
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        all_codes = []
        
        # Category A (HR Products) - 기존 hr_product_components 테이블
        try:
            query_a = '''
                SELECT DISTINCT
                    (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key || '-' || l6.component_key) as product_code,
                    (COALESCE(s.description, s.component_name) || ' / ' || 
                     COALESCE(p.description, p.component_name) || ' / ' || 
                     COALESCE(g.description, g.component_name) || ' / ' || 
                     COALESCE(sz.description, sz.component_name) || ' / ' || 
                     COALESCE(l5.description, l5.component_name) || ' / ' || 
                     COALESCE(l6.description, l6.component_name)) as description
                FROM hr_product_components s
                JOIN hr_product_components p ON p.parent_component = s.component_key
                JOIN hr_product_components g ON g.parent_component = (s.component_key || '-' || p.component_key)
                JOIN hr_product_components sz ON sz.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key)
                JOIN hr_product_components l5 ON l5.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key)
                JOIN hr_product_components l6 ON l6.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key)
                WHERE s.component_type = 'system_type'
                  AND p.component_type = 'product_type'
                  AND g.component_type = 'gate_type'
                  AND sz.component_type = 'size'
                  AND l5.component_type = 'level5'
                  AND l6.component_type = 'level6'
                  AND s.is_active = 1 AND p.is_active = 1 AND g.is_active = 1 AND sz.is_active = 1 AND l5.is_active = 1 AND l6.is_active = 1
                ORDER BY s.component_key, p.component_key, g.component_key, sz.component_key, l5.component_key, l6.component_key
            '''
            
            cursor.execute(query_a)
            results_a = cursor.fetchall()
            
            for code, description in results_a:
                all_codes.append({
                    'code': code,
                    'description': description,
                    'category': 'Category A - HR Products'
                })
        except Exception as e:
            print(f"Category A 조합 생성 오류: {e}")
        
        # Category B~I - multi_category_components 테이블에서 6단계 조합 생성
        categories = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        category_names = {
            'B': 'Controller Products',
            'C': 'Controller Products', 
            'D': 'Controller Products',
            'E': 'Controller Products',
            'F': 'Controller Products',
            'G': 'Controller Products',
            'H': 'Controller Products',
            'I': 'Controller Products'
        }
        
        for cat in categories:
            try:
                # 각 카테고리별로 6단계가 모두 완성된 조합만 생성
                query_multi = '''
                    SELECT DISTINCT
                        (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key || '-' || l5.component_key || '-' || l6.component_key) as product_code,
                        (COALESCE(l1.description, l1.component_name) || ' / ' || 
                         COALESCE(l2.description, l2.component_name) || ' / ' || 
                         COALESCE(l3.description, l3.component_name) || ' / ' || 
                         COALESCE(l4.description, l4.component_name) || ' / ' || 
                         COALESCE(l5.description, l5.component_name) || ' / ' || 
                         COALESCE(l6.description, l6.component_name)) as description
                    FROM multi_category_components l1
                    JOIN multi_category_components l2 ON l2.category_type = ? AND l2.component_level = 'level2' AND l2.parent_component = l1.component_key
                    JOIN multi_category_components l3 ON l3.category_type = ? AND l3.component_level = 'level3' AND l3.parent_component = (l1.component_key || '-' || l2.component_key)
                    JOIN multi_category_components l4 ON l4.category_type = ? AND l4.component_level = 'level4' AND l4.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key)
                    JOIN multi_category_components l5 ON l5.category_type = ? AND l5.component_level = 'level5' AND l5.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key)
                    JOIN multi_category_components l6 ON l6.category_type = ? AND l6.component_level = 'level6' AND l6.parent_component = (l1.component_key || '-' || l2.component_key || '-' || l3.component_key || '-' || l4.component_key || '-' || l5.component_key)
                    WHERE l1.category_type = ? AND l1.component_level = 'level1' AND l1.is_active = 1
                      AND l2.is_active = 1 AND l3.is_active = 1 AND l4.is_active = 1 AND l5.is_active = 1 AND l6.is_active = 1
                    ORDER BY l1.component_key, l2.component_key, l3.component_key, l4.component_key, l5.component_key, l6.component_key
                '''
                
                cursor.execute(query_multi, (cat, cat, cat, cat, cat, cat))
                results_multi = cursor.fetchall()
                
                for code, description in results_multi:
                    # 각 코드에 대해 code_id 미리 생성 및 저장
                    code_id = ensure_code_exists_in_db(code, f'Category {cat} - {category_names[cat]}', cat, description)
                    all_codes.append({
                        'code': code,
                        'description': description,
                        'category': f'Category {cat} - {category_names[cat]}',
                        'category_type': cat,
                        'code_id': code_id  # 생성된 code_id 포함
                    })
                    
            except Exception as e:
                print(f"Category {cat} 조합 생성 오류: {e}")
        
        conn.close()
        return all_codes
            
    except Exception as e:
        print(f"전체 조합 생성 오류: {e}")
        return []

def ensure_code_exists_in_db(product_code, category, category_type, description):
    """제품 코드가 generated_product_codes에 없으면 생성하여 저장합니다."""
    try:
        import sqlite3
        from datetime import datetime as dt
        
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        # 이미 존재하는지 확인
        cursor.execute('SELECT code_id FROM generated_product_codes WHERE product_code = ?', (product_code,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        # 새로운 code_id 생성
        code_id = f"PC_{product_code.replace('-', '_')}_{dt.now().strftime('%Y%m%d%H%M%S')}"
        
        # DB에 저장 (status = available)
        cursor.execute('''
            INSERT INTO generated_product_codes 
            (code_id, product_code, category, category_type, status, created_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (code_id, product_code, category, category_type, 'available', 
              dt.now().isoformat(), 'system'))
        
        conn.commit()
        conn.close()
        return code_id
        
    except Exception as e:
        print(f"코드 DB 저장 오류 {product_code}: {e}")
        # 실패 시에도 임시 code_id 반환
        from datetime import datetime as dt
        return f"PC_{product_code.replace('-', '_')}_{dt.now().strftime('%Y%m%d%H%M%S')}"

def get_supplier_list():
    """공급업체 리스트를 가져옵니다."""
    try:
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        # suppliers 테이블에서 company_name 컬럼 사용
        cursor.execute('''
            SELECT DISTINCT company_name 
            FROM suppliers 
            WHERE status = '활성' AND company_name IS NOT NULL
            ORDER BY company_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            supplier_names = [row[0] for row in results if row[0]]
            return supplier_names
        else:
            # 데이터가 없으면 기본값 반환
            return [
                "중국 공급업체", 
                "미국 공급업체", 
                "베트남 공급업체", 
                "한국 공급업체"
            ]
            
    except Exception as e:
        print(f"공급업체 조회 오류: {e}")
        return [
            "중국 공급업체", 
            "미국 공급업체", 
            "베트남 공급업체", 
            "한국 공급업체"
        ]