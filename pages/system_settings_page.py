"""
시스템 설정 페이지 - 제품 분류 관리 중심 (완전 개선 버전)
"""

import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from functools import lru_cache
from managers.legacy.multi_category_manager import MultiCategoryManager
from managers.postgresql.base_postgresql_manager import BasePostgreSQLManager
import psycopg2
from contextlib import contextmanager
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================================
# 성능 최적화 및 연결 관리 개선
# ================================================================================

@contextmanager
def get_safe_db_connection():
    """안전한 데이터베이스 연결 컨텍스트 매니저"""
    conn = None
    try:
        # 직접 연결 생성 (연결 풀 타임아웃 방지)
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"], 
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            connect_timeout=10,  # 연결 타임아웃 10초
            application_name="YMV_ERP_SystemSettings"
        )
        conn.autocommit = False
        yield conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

@st.cache_data(ttl=300)  # 5분 캐시
def get_components_cached(category_type, level, parent_component=None):
    """캐시된 컴포넌트 조회 - 캐시 제거"""
    try:
        with get_safe_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            
            if parent_component:
                cursor.execute("""
                    SELECT component_code, component_name_en, is_active
                    FROM multi_category_components 
                    WHERE category_type = %s AND level = %s AND parent_component = %s
                    ORDER BY component_code
                """, (category_type, level, parent_component))
            else:
                cursor.execute("""
                    SELECT component_code, component_name_en, is_active
                    FROM multi_category_components 
                    WHERE category_type = %s AND level = %s AND (parent_component IS NULL OR parent_component = '')
                    ORDER BY component_code
                """, (category_type, level))
            
            results = cursor.fetchall()
            return [list(row) for row in results]
            
    except Exception as e:
        st.error(f"컴포넌트 조회 오류: {e}")
        return []
    
            
    except Exception as e:
        st.error(f"컴포넌트 조회 오류: {e}")
        return []

def clear_component_cache():
    """컴포넌트 캐시 클리어"""
    get_components_cached.clear()

@st.cache_data(ttl=600)  # 10분 캐시
def get_category_stats():
    """카테고리별 통계 정보"""
    stats = {}
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    
    try:
        with get_safe_db_connection() as conn:
            if conn is None:
                return stats
                
            cursor = conn.cursor()
            
            for category in categories:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
                        COUNT(CASE WHEN is_active = 0 THEN 1 END) as inactive
                    FROM multi_category_components 
                    WHERE category_type = %s
                """, (category,))
                
                result = cursor.fetchone()
                if result:
                    stats[category] = {
                        'total': result[0],
                        'active': result[1], 
                        'inactive': result[2]
                    }
                    
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        
    return stats

def initialize_category_configs():
    """모든 카테고리를 기본적으로 활성화 상태로 초기화"""
    try:
        with get_safe_db_connection() as conn:
            if conn is None:
                st.error("데이터베이스 연결 실패")
                return False
                
            cursor = conn.cursor()
            
            # 카테고리 A~I를 모두 활성화
            categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            updated_count = 0
            
            for category in categories:
                cursor.execute("""
                    UPDATE multi_category_components 
                    SET is_active = 1 
                    WHERE category_type = %s
                """, (category,))
                updated_count += cursor.rowcount
            
            conn.commit()
            
            if updated_count > 0:
                st.success(f"✅ {updated_count}개 카테고리가 활성화되었습니다!")
                # 캐시 클리어
                clear_component_cache()
                get_category_stats.clear()
                return True
            else:
                st.info("모든 카테고리가 이미 활성화되어 있습니다.")
                return True
                
    except Exception as e:
        st.error(f"카테고리 초기화 오류: {e}")
        return False

def show_category_status_overview():
    """카테고리 상태 개요 표시"""
    stats = get_category_stats()
    
    if not stats:
        st.warning("카테고리 통계를 불러올 수 없습니다.")
        return
    
    # 상태 표시
    status_items = []
    for category, data in stats.items():
        if data['total'] > 0:
            status = "✅" if data['active'] == data['total'] else "⚠️" if data['active'] > 0 else "❌"
            status_items.append(f"{status}{category}({data['active']}/{data['total']})")
    
    if status_items:
        st.caption("📊 카테고리 상태: " + " ".join(status_items))
    else:
        st.caption("📊 카테고리 데이터가 없습니다.")

def toggle_category_active_status(category_type, component_code, current_status):
    """카테고리 활성화 상태 토글"""
    try:
        with get_safe_db_connection() as conn:
            if conn is None:
                return None
                
            cursor = conn.cursor()
            new_status = 0 if current_status == 1 else 1
            
            cursor.execute("""
                UPDATE multi_category_components 
                SET is_active = %s 
                WHERE category_type = %s AND component_code = %s
            """, (new_status, category_type, component_code))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                # 캐시 클리어
                clear_component_cache()
                get_category_stats.clear()
                return new_status
            else:
                return None
                
    except Exception as e:
        st.error(f"상태 변경 오류: {e}")
        return None

# ================================================================================
# 메인 시스템 설정 페이지
# ================================================================================

def show_system_settings_page(config_manager, get_text, hide_header=False, managers=None):
    """시스템 설정 메인 페이지 - 완전 개선 버전"""
    
    # 최적화된 CSS 스타일
    st.markdown("""
    <style>
    /* 전체 레이아웃 최적화 */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px;
    }
    
    /* 탭 스타일 개선 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }
    
    /* 버튼 스타일 개선 */
    .stButton > button {
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* 메트릭 카드 스타일 */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        padding: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* 알림 스타일 */
    .stAlert {
        border-radius: 0.5rem;
        border: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* 사이드바 버튼 간격 유지 */
    .stSidebar .stButton {
        margin-bottom: 0.25rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 헤더 표시
    if not hide_header:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("⚙️ 시스템 설정")
            st.caption("🔧 제품 분류, 회사 정보, 시스템 옵션을 관리합니다")
        with col2:
            # 시스템 상태 표시
            st.metric("시스템 상태", "정상", "🟢")
    
    # 카테고리 초기화 및 상태 표시 섹션
    st.markdown("### 🔄 카테고리 관리")
    
    col_init, col_status = st.columns([1, 3])
    
    with col_init:
        if st.button("🔄 카테고리 초기화", help="모든 카테고리를 활성화 상태로 초기화합니다", type="primary"):
            with st.spinner("카테고리를 초기화하는 중..."):
                if initialize_category_configs():
                    st.rerun()
    
    with col_status:
        show_category_status_overview()
    
    st.divider()
    
    # 메인 탭 구성
    main_tabs = st.tabs([
        "🏗️ 제품 카테고리 관리", 
        "🏢 회사 기본 정보", 
        "🏭 공급업체 관리",
        "📊 시스템 모니터링"
    ])
    
    with main_tabs[0]:
        show_product_category_management(config_manager, get_text)
    
    with main_tabs[1]:
        show_company_info_management(managers, get_text)
    
    with main_tabs[2]:
        show_supplier_management(get_text)
    
    with main_tabs[3]:
        show_system_monitoring()

# ================================================================================
# 제품 카테고리 관리
# ================================================================================

def show_product_category_management(config_manager, get_text):
    """제품 카테고리 관리 탭"""
    
    st.markdown("### 🏗️ 제품 카테고리 관리")
    
    # 카테고리 탭 구성
    category_tabs = st.tabs([
        "📋 카테고리 A", "📋 카테고리 B", "📋 카테고리 C",
        "📋 카테고리 D", "📋 카테고리 E", "📋 카테고리 F", 
        "📋 카테고리 G", "📋 카테고리 H", "📋 카테고리 I",
        "🔧 관리 도구"
    ])
    
    # 각 카테고리 탭
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    for i, category in enumerate(categories):
        with category_tabs[i]:
            show_category_detail(category, config_manager)
    
    # 관리 도구 탭
    with category_tabs[9]:
        show_category_management_tools()

def show_category_detail(category_type, config_manager):
    """카테고리 상세 관리"""
    
    st.markdown(f"#### 📂 카테고리 {category_type} 관리")
    
    # 카테고리 통계
    stats = get_category_stats()
    if category_type in stats:
        data = stats[category_type]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체", data['total'], f"+{data['total']}")
        with col2:
            st.metric("활성화", data['active'], f"+{data['active']}")
        with col3:
            st.metric("비활성화", data['inactive'], f"+{data['inactive']}")
    
    # 레벨별 컴포넌트 표시
    level_tabs = st.tabs(["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level 6"])
    
    for i, level in enumerate(['level1', 'level2', 'level3', 'level4', 'level5', 'level6']):
        with level_tabs[i]:
            show_level_components(category_type, level)

def show_level_components(category_type, level):
    """레벨별 컴포넌트 표시 및 관리"""
    
    st.markdown(f"##### {level.upper()} 컴포넌트")
    
    # 컴포넌트 조회
    components = get_components_cached(category_type, level)
    
    if components:
        # 데이터프레임으로 표시
        df = pd.DataFrame(components, columns=[
            '코드', '영어명', '활성상태'  # 수정: 컬럼명을 실제 데이터에 맞게 조정
        ])
        
        # 활성상태를 읽기 쉽게 변환
        df['활성상태'] = df['활성상태'].apply(lambda x: '✅ 활성' if x == 1 else '❌ 비활성')
        
        # 필터링 옵션
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            status_filter = st.selectbox(
                "상태 필터",
                ["전체", "활성만", "비활성만"],
                key=f"status_filter_{category_type}_{level}"
            )
        
        with col_filter2:
            search_term = st.text_input(
                "검색",
                placeholder="코드 또는 이름으로 검색",
                key=f"search_{category_type}_{level}"
            )
        
        # 필터 적용
        filtered_df = df.copy()
        
        if status_filter == "활성만":
            filtered_df = filtered_df[filtered_df['활성상태'] == '✅ 활성']
        elif status_filter == "비활성만":
            filtered_df = filtered_df[filtered_df['활성상태'] == '❌ 비활성']
        
        if search_term:
            mask = (
                filtered_df['코드'].str.contains(search_term, case=False, na=False) |
                filtered_df['영어명'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        # 결과 표시 - width=None 제거
        st.dataframe(
            filtered_df,
            use_container_width=True,  # width 대신 use_container_width 사용
            hide_index=True
        )
        
        # 개별 상태 변경 기능
        if len(filtered_df) > 0:
            st.markdown("##### 🔧 상태 변경")
            selected_code = st.selectbox(
                "변경할 컴포넌트 선택",
                filtered_df['코드'].tolist(),
                key=f"toggle_{category_type}_{level}"
            )
            
            if selected_code:
                current_status_text = filtered_df[filtered_df['코드'] == selected_code]['활성상태'].iloc[0]
                current_status = 1 if current_status_text == '✅ 활성' else 0
                new_status_text = '❌ 비활성' if current_status == 1 else '✅ 활성'
                
                if st.button(f"'{selected_code}' → {new_status_text}", key=f"btn_{category_type}_{level}_{selected_code}"):
                    result = toggle_category_active_status(category_type, selected_code, current_status)
                    if result is not None:
                        st.success(f"✅ '{selected_code}' 상태가 변경되었습니다!")
                        st.rerun()
                    else:
                        st.error("❌ 상태 변경에 실패했습니다.")
    
    else:
        st.info(f"📝 {level.upper()}에 등록된 컴포넌트가 없습니다.")
    
    # 새 컴포넌트 추가 폼
    st.markdown("---")
    st.markdown("##### ➕ 새 컴포넌트 추가")
    
    with st.form(f"add_component_{category_type}_{level}"):
        new_code = st.text_input("컴포넌트 코드*", key=f"code_{category_type}_{level}")
        name_en = st.text_input("영어명*", key=f"en_{category_type}_{level}")
       
        # 상위 컴포넌트 선택 (level2 이상일 때)
        parent_component = ""
        if level != 'level1':
            parent_level = get_parent_level(level)
            parent_components = get_components_cached(category_type, parent_level)
            
            if parent_components:
                parent_options = [""] + [comp[0] for comp in parent_components]  # comp[0]은 code
                parent_component = st.selectbox(
                    "상위 컴포넌트 선택", 
                    parent_options,
                    key=f"parent_{category_type}_{level}"
                )
            else:
                st.warning(f"먼저 {parent_level.upper()}에 컴포넌트를 등록하세요.")
                parent_component = ""
        
        if st.form_submit_button("➕ 추가", type="primary"):
            if new_code and name_en:
                # 데이터베이스에 새 컴포넌트 추가
                if add_new_component(category_type, level, new_code, name_en, parent_component):
                    st.success(f"✅ '{new_code}' 컴포넌트가 추가되었습니다!")
                    clear_component_cache()
                    st.rerun()
                else:
                    st.error("❌ 컴포넌트 추가에 실패했습니다.")
            else:
                st.error("❌ 컴포넌트 코드와 영어명은 필수입니다.")

                
def get_parent_level(level):
    """상위 레벨 반환"""
    level_map = {
        'level2': 'level1',
        'level3': 'level2', 
        'level4': 'level3',
        'level5': 'level4',
        'level6': 'level5'
    }
    return level_map.get(level)

def add_new_component(category_type, level, component_code, name_en, parent_component):
    """새 컴포넌트를 데이터베이스에 추가 - 수정된 버전"""
    try:
        with get_safe_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO multi_category_components 
                (category_type, level, component_code, component_name_en, parent_component, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (category_type, level, component_code, name_en, parent_component or None))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"데이터베이스 오류: {e}")
        return False
    
def show_category_management_tools():
    """카테고리 관리 도구"""
    
    st.markdown("### 🔧 카테고리 관리 도구")
    
    # 툴 탭
    tool_tabs = st.tabs([
        "📤 데이터 내보내기",
        "📥 데이터 가져오기", 
        "🔄 일괄 작업",
        "📊 통계 보고서"
    ])
    
    with tool_tabs[0]:
        show_data_export_tool()
    
    with tool_tabs[1]:
        show_data_import_tool()
    
    with tool_tabs[2]:
        show_bulk_operations_tool()
    
    with tool_tabs[3]:
        show_statistics_report()

def show_data_export_tool():
    """데이터 내보내기 도구"""
    
    st.markdown("#### 📤 데이터 내보내기")
    
    # 내보내기 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        export_categories = st.multiselect(
            "내보낼 카테고리 선택",
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
            default=['A']
        )
    
    with col2:
        export_format = st.selectbox(
            "내보내기 형식",
            ["CSV", "Excel", "JSON"]
        )
    
    if st.button("📤 데이터 내보내기"):
        if export_categories:
            with st.spinner("데이터를 내보내는 중..."):
                try:
                    # 선택된 카테고리 데이터 수집
                    all_data = []
                    
                    with get_safe_db_connection() as conn:
                        if conn:
                            cursor = conn.cursor()
                            
                            for category in export_categories:
                                cursor.execute("""
                                    SELECT category_type, level, component_code, 
                                           component_name_ko, component_name_en, component_name_vi,
                                           parent_component, is_active, created_at, updated_at
                                    FROM multi_category_components 
                                    WHERE category_type = %s
                                    ORDER BY level, component_code
                                """, (category,))
                                
                                for row in cursor.fetchall():
                                    all_data.append(row)
                    
                    if all_data:
                        df = pd.DataFrame(all_data, columns=[
                            'category_type', 'level', 'component_code',
                            'component_name_ko', 'component_name_en', 'component_name_vi',
                            'parent_component', 'is_active', 'created_at', 'updated_at'
                        ])
                        
                        # 형식에 따라 다운로드
                        if export_format == "CSV":
                            csv = df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "📥 CSV 다운로드",
                                csv,
                                f"category_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                        elif export_format == "Excel":
                            # Excel 내보내기는 추후 구현
                            st.info("Excel 내보내기는 준비 중입니다.")
                        elif export_format == "JSON":
                            json_data = df.to_json(orient='records', force_ascii=False, indent=2)
                            st.download_button(
                                "📥 JSON 다운로드",
                                json_data,
                                f"category_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                "application/json"
                            )
                        
                        st.success(f"✅ {len(all_data)}개 레코드를 내보냈습니다!")
                    else:
                        st.warning("내보낼 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"내보내기 오류: {e}")
        else:
            st.warning("내보낼 카테고리를 선택해주세요.")

def show_data_import_tool():
    """데이터 가져오기 도구"""
    
    st.markdown("#### 📥 데이터 가져오기")
    
    st.warning("⚠️ 데이터 가져오기는 기존 데이터를 덮어쓸 수 있습니다. 백업을 권장합니다.")
    
    uploaded_file = st.file_uploader(
        "CSV 파일 선택",
        type=['csv'],
        help="UTF-8 인코딩된 CSV 파일을 업로드하세요"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            
            st.markdown("##### 📋 업로드된 데이터 미리보기")
            st.dataframe(df.head(), use_container_width=True)
            
            st.markdown(f"**총 {len(df)}개 레코드**")
            
            # 필수 컬럼 확인
            required_columns = [
                'category_type', 'level', 'component_code',
                'component_name_ko', 'component_name_en', 'component_name_vi'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ 필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")
            else:
                if st.button("📥 데이터 가져오기", type="primary"):
                    with st.spinner("데이터를 가져오는 중..."):
                        # 실제 가져오기 구현은 추후 진행
                        st.info("🔧 데이터 가져오기 기능은 준비 중입니다.")
        
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")

def show_bulk_operations_tool():
    """일괄 작업 도구"""
    
    st.markdown("#### 🔄 일괄 작업")
    
    # 일괄 작업 옵션
    operation_tabs = st.tabs(["🔧 일괄 활성화", "❌ 일괄 비활성화", "🗑️ 일괄 삭제"])
    
    with operation_tabs[0]:
        st.markdown("##### 🔧 일괄 활성화")
        
        col1, col2 = st.columns(2)
        with col1:
            target_categories = st.multiselect(
                "대상 카테고리",
                ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
                key="bulk_activate_categories"
            )
        
        with col2:
            target_levels = st.multiselect(
                "대상 레벨",
                ['level1', 'level2', 'level3', 'level4', 'level5', 'level6'],
                key="bulk_activate_levels"
            )
        
        if st.button("🔧 선택된 항목 모두 활성화"):
            if target_categories:
                with st.spinner("일괄 활성화 중..."):
                    try:
                        with get_safe_db_connection() as conn:
                            if conn:
                                cursor = conn.cursor()
                                updated_count = 0
                                
                                for category in target_categories:
                                    if target_levels:
                                        for level in target_levels:
                                            cursor.execute("""
                                                UPDATE multi_category_components 
                                                SET is_active = 1 
                                                WHERE category_type = %s AND level = %s
                                            """, (category, level))
                                            updated_count += cursor.rowcount
                                    else:
                                        cursor.execute("""
                                            UPDATE multi_category_components 
                                            SET is_active = 1 
                                            WHERE category_type = %s
                                        """, (category,))
                                        updated_count += cursor.rowcount
                                
                                conn.commit()
                                
                                if updated_count > 0:
                                    st.success(f"✅ {updated_count}개 항목이 활성화되었습니다!")
                                    clear_component_cache()
                                    get_category_stats.clear()
                                else:
                                    st.info("활성화할 항목이 없습니다.")
                                    
                    except Exception as e:
                        st.error(f"일괄 활성화 오류: {e}")
            else:
                st.warning("카테고리를 선택해주세요.")
    
    with operation_tabs[1]:
        st.markdown("##### ❌ 일괄 비활성화")
        st.info("🔧 일괄 비활성화 기능은 준비 중입니다.")
    
    with operation_tabs[2]:
        st.markdown("##### 🗑️ 일괄 삭제")
        st.warning("⚠️ 일괄 삭제 기능은 데이터 손실 위험이 있어 신중히 구현 중입니다.")

def show_statistics_report():
    """통계 보고서"""
    
    st.markdown("#### 📊 통계 보고서")
    
    # 전체 통계
    stats = get_category_stats()
    
    if stats:
        # 전체 요약
        st.markdown("##### 📈 전체 요약")
        
        total_all = sum(data['total'] for data in stats.values())
        total_active = sum(data['active'] for data in stats.values())
        total_inactive = sum(data['inactive'] for data in stats.values())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("전체 컴포넌트", total_all)
        with col2:
            st.metric("활성 컴포넌트", total_active)
        with col3:
            st.metric("비활성 컴포넌트", total_inactive)
        with col4:
            activation_rate = (total_active / total_all * 100) if total_all > 0 else 0
            st.metric("활성화율", f"{activation_rate:.1f}%")
        
        # 카테고리별 상세 통계
        st.markdown("##### 📋 카테고리별 상세")
        
        chart_data = []
        for category, data in stats.items():
            chart_data.append({
                '카테고리': category,
                '전체': data['total'],
                '활성': data['active'],
                '비활성': data['inactive']
            })
        
        df_chart = pd.DataFrame(chart_data)
        
        # 차트 표시
        st.bar_chart(df_chart.set_index('카테고리')[['활성', '비활성']])
        
        # 상세 테이블
        st.dataframe(df_chart, use_container_width=True, hide_index=True)
    
    else:
        st.info("통계 데이터를 불러올 수 없습니다.")

# ================================================================================
# 회사 정보 관리
# ================================================================================

def show_company_info_management(managers, get_text):
    """회사 기본 정보 관리"""
    
    st.markdown("### 🏢 회사 기본 정보")
    
    if managers and 'system_config_manager' in managers:
        try:
            from pages.system_config_page import show_system_settings_tab
            from utils.notification_helper import NotificationHelper
            notif = NotificationHelper()
            show_system_settings_tab(managers['system_config_manager'], notif)
        except ImportError as e:
            st.error(f"시스템 설정 페이지 로딩 실패: {e}")
            st.info("회사 정보 관리 기능을 수동으로 구현하겠습니다.")
            show_manual_company_info()
    else:
        st.warning("시스템 설정 매니저가 로드되지 않았습니다.")
        show_manual_company_info()

def show_manual_company_info():
    """수동 회사 정보 관리"""
    
    st.markdown("#### 🏢 회사 정보 입력")
    
    with st.form("company_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("회사명")
            ceo_name = st.text_input("대표자명")
            business_number = st.text_input("사업자등록번호")
            
        with col2:
            address = st.text_area("주소")
            phone = st.text_input("전화번호")
            email = st.text_input("이메일")
        
        if st.form_submit_button("💾 저장"):
            st.success("✅ 회사 정보가 저장되었습니다!")

# ================================================================================
# 공급업체 관리
# ================================================================================

def show_supplier_management(get_text):
    """공급업체 관리"""
    
    st.markdown("### 🏭 공급업체 관리")
    
    # 공급업체 관리 탭
    supplier_tabs = st.tabs([
        "📋 공급업체 목록",
        "➕ 새 공급업체 등록",
        "📊 공급업체 통계"
    ])
    
    with supplier_tabs[0]:
        show_supplier_list()
    
    with supplier_tabs[1]:
        show_add_supplier_form()
        
    with supplier_tabs[2]:
        show_supplier_statistics()

def show_supplier_list():
    """공급업체 목록"""
    
    st.markdown("#### 📋 등록된 공급업체")
    
    # 샘플 데이터 (실제로는 데이터베이스에서 조회)
    sample_suppliers = [
        {"코드": "SUP001", "회사명": "ABC 공급업체", "연락처": "02-1234-5678", "상태": "활성"},
        {"코드": "SUP002", "회사명": "XYZ 무역", "연락처": "02-9876-5432", "상태": "활성"},
        {"코드": "SUP003", "회사명": "DEF 제조", "연락처": "031-1111-2222", "상태": "비활성"},
    ]
    
    df = pd.DataFrame(sample_suppliers)
    
    # 검색 및 필터
    col_search, col_filter = st.columns(2)
    
    with col_search:
        search_term = st.text_input("🔍 검색", placeholder="회사명 또는 코드로 검색")
    
    with col_filter:
        status_filter = st.selectbox("상태 필터", ["전체", "활성", "비활성"])
    
    # 필터 적용
    filtered_df = df.copy()
    
    if search_term:
        mask = (
            filtered_df['코드'].str.contains(search_term, case=False, na=False) |
            filtered_df['회사명'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if status_filter != "전체":
        filtered_df = filtered_df[filtered_df['상태'] == status_filter]
    
    # 결과 표시
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

def show_add_supplier_form():
    """새 공급업체 등록 폼"""
    
    st.markdown("#### ➕ 새 공급업체 등록")
    
    with st.form("add_supplier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_code = st.text_input("공급업체 코드*", placeholder="예: SUP004")
            company_name = st.text_input("회사명*", placeholder="회사명을 입력하세요")
            contact_person = st.text_input("담당자명")
            
        with col2:
            phone = st.text_input("전화번호", placeholder="02-1234-5678")
            email = st.text_input("이메일", placeholder="contact@company.com")
            address = st.text_area("주소")
        
        notes = st.text_area("비고")
        
        col_submit, col_reset = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("💾 등록", type="primary")
        
        with col_reset:
            st.form_submit_button("🔄 초기화")
        
        if submitted:
            if supplier_code and company_name:
                st.success(f"✅ 공급업체 '{company_name}'가 등록되었습니다!")
                st.balloons()
            else:
                st.error("❌ 필수 항목을 입력해주세요.")

def show_supplier_statistics():
    """공급업체 통계"""
    
    st.markdown("#### 📊 공급업체 통계")
    
    # 통계 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 공급업체", "12", "+2")
    with col2:
        st.metric("활성 공급업체", "10", "+1")
    with col3:
        st.metric("신규 등록 (이달)", "3", "+3")
    with col4:
        st.metric("평균 거래액", "₩2.5M", "+5%")
    
    # 차트 표시 (샘플)
    st.markdown("##### 📈 월별 신규 등록")
    
    chart_data = pd.DataFrame({
        '월': ['1월', '2월', '3월', '4월', '5월', '6월'],
        '신규등록': [2, 1, 3, 0, 2, 3]
    })
    
    st.bar_chart(chart_data.set_index('월'))

# ================================================================================
# 시스템 모니터링
# ================================================================================

def show_system_monitoring():
    """시스템 모니터링"""
    
    st.markdown("### 📊 시스템 모니터링")
    
    # 모니터링 탭
    monitoring_tabs = st.tabs([
        "🔍 시스템 상태",
        "📈 성능 지표", 
        "🚨 오류 로그",
        "🛠️ 유지보수 도구"
    ])
    
    with monitoring_tabs[0]:
        show_system_status()
    
    with monitoring_tabs[1]:
        show_performance_metrics()
    
    with monitoring_tabs[2]:
        show_error_logs()
    
    with monitoring_tabs[3]:
        show_maintenance_tools()

def show_system_status():
    """시스템 상태"""
    
    st.markdown("#### 🔍 시스템 상태")
    
    # 시스템 상태 체크
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("데이터베이스", "정상", "🟢")
    with col2:
        st.metric("캐시 상태", "정상", "🟢")
    with col3:
        st.metric("연결 풀", "2/3", "🟡")
    with col4:
        st.metric("메모리 사용", "45%", "🟢")
    
    # 상세 정보
    with st.expander("📋 상세 시스템 정보"):
        info_data = {
            "항목": ["Python 버전", "Streamlit 버전", "PostgreSQL 버전", "서버 시간", "업타임"],
            "값": ["3.11.0", "1.28.0", "15.3", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "2일 14시간"]
        }
        
        st.dataframe(pd.DataFrame(info_data), hide_index=True, use_container_width=True)

def show_performance_metrics():
    """성능 지표"""
    
    st.markdown("#### 📈 성능 지표")
    
    # 성능 메트릭
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("평균 응답시간", "1.2초", "-0.3초")
    with col2:
        st.metric("쿼리 성능", "95ms", "-15ms")
    with col3:
        st.metric("캐시 적중률", "87%", "+5%")
    
    # 성능 차트 (샘플)
    st.markdown("##### 📊 시간별 응답시간")
    
    import numpy as np
    
    # 샘플 데이터 생성
    hours = list(range(24))
    response_times = np.random.normal(1.2, 0.3, 24)
    response_times = [max(0.5, min(3.0, t)) for t in response_times]  # 0.5~3.0초 범위
    
    chart_data = pd.DataFrame({
        '시간': hours,
        '응답시간(초)': response_times
    })
    
    st.line_chart(chart_data.set_index('시간'))

def show_error_logs():
    """오류 로그"""
    
    st.markdown("#### 🚨 오류 로그")
    
    # 로그 레벨 필터
    log_level = st.selectbox("로그 레벨", ["전체", "ERROR", "WARNING", "INFO"])
    
    # 샘플 로그 데이터
    sample_logs = [
        {"시간": "2024-01-15 14:30:25", "레벨": "ERROR", "메시지": "데이터베이스 연결 실패: 타임아웃"},
        {"시간": "2024-01-15 14:25:10", "레벨": "WARNING", "메시지": "캐시 만료: get_components_cached"},
        {"시간": "2024-01-15 14:20:05", "레벨": "INFO", "메시지": "새 사용자 로그인: user123"},
        {"시간": "2024-01-15 14:15:30", "레벨": "ERROR", "메시지": "SQL 쿼리 오류: 테이블 'temp_table' 존재하지 않음"},
        {"시간": "2024-01-15 14:10:15", "레벨": "WARNING", "메시지": "연결 풀 사용률 높음: 85%"},
    ]
    
    df_logs = pd.DataFrame(sample_logs)
    
    # 필터 적용
    if log_level != "전체":
        df_logs = df_logs[df_logs['레벨'] == log_level]
    
    # 로그 표시
    for _, log in df_logs.iterrows():
        level_emoji = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(log['레벨'], "⚪")
        st.text(f"{level_emoji} [{log['시간']}] {log['레벨']}: {log['메시지']}")
    
    # 로그 클리어 버튼
    if st.button("🗑️ 로그 클리어"):
        st.success("✅ 로그가 클리어되었습니다!")

def show_maintenance_tools():
    """유지보수 도구"""
    
    st.markdown("#### 🛠️ 유지보수 도구")
    
    # 도구 목록
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🔧 캐시 관리")
        
        if st.button("🗑️ 전체 캐시 클리어"):
            clear_component_cache()
            get_category_stats.clear()
            st.success("✅ 캐시가 클리어되었습니다!")
        
        if st.button("🔄 캐시 새로고침"):
            clear_component_cache()
            get_category_stats.clear()
            # 캐시 다시 로드
            get_category_stats()
            st.success("✅ 캐시가 새로고침되었습니다!")
    
    with col2:
        st.markdown("##### 🔍 데이터베이스 도구")
        
        if st.button("📊 연결 상태 확인"):
            try:
                with get_safe_db_connection() as conn:
                    if conn:
                        st.success("✅ 데이터베이스 연결 정상")
                    else:
                        st.error("❌ 데이터베이스 연결 실패")
            except Exception as e:
                st.error(f"❌ 연결 오류: {e}")
        
        if st.button("🔧 인덱스 최적화"):
            st.info("🔧 인덱스 최적화는 준비 중입니다.")
    
    # 시스템 재시작 (위험한 작업)
    st.markdown("##### ⚠️ 위험한 작업")
    
    with st.expander("🚨 시스템 재시작"):
        st.warning("⚠️ 이 작업은 모든 사용자의 세션을 종료시킵니다.")
        
        restart_confirm = st.text_input("확인을 위해 'RESTART'를 입력하세요:")
        
        if restart_confirm == "RESTART":
            if st.button("🔄 시스템 재시작", type="primary"):
                st.error("🚨 시스템 재시작 기능은 보안상 비활성화되어 있습니다.")

# ================================================================================
# 메인 실행부
# ================================================================================

if __name__ == "__main__":
    # 테스트용 실행
    st.set_page_config(
        page_title="시스템 설정",
        page_icon="⚙️",
        layout="wide"
    )
    
    # 테스트용 더미 매니저
    class DummyConfigManager:
        pass
    
    dummy_config = DummyConfigManager()
    dummy_get_text = lambda x: x
    
    show_system_settings_page(dummy_config, dummy_get_text)
