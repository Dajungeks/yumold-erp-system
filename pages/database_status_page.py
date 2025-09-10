# -*- coding: utf-8 -*-
"""
데이터베이스 상태 및 설정 페이지
"""

import streamlit as st
import os
from config.database_config import DatabaseConfig, get_database_status

def show_database_status_page():
    """데이터베이스 상태 페이지 표시"""
    
    st.title("🗄️ 데이터베이스 상태 및 설정")
    
    # 현재 데이터베이스 상태 조회
    db_status = get_database_status()
    
    # 데이터베이스 상태 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 현재 데이터베이스 상태")
        
        # 현재 사용 중인 데이터베이스
        current_db = db_status['type']
        if current_db == 'postgresql':
            st.success(f"🐘 **PostgreSQL** 사용 중")
        else:
            st.info(f"🗃️ **SQLite** 사용 중")
        
        # 사용 가능한 데이터베이스들
        st.write("### 사용 가능한 데이터베이스")
        
        # SQLite 상태
        if db_status['sqlite_available']:
            st.success("✅ SQLite - 사용 가능")
        else:
            st.error("❌ SQLite - 사용 불가")
        
        # PostgreSQL 상태
        if db_status['postgresql_available']:
            if db_status.get('postgresql_connected', False):
                st.success("✅ PostgreSQL - 연결됨")
            else:
                st.warning("⚠️ PostgreSQL - 사용 가능하지만 연결 실패")
                if 'postgresql_error' in db_status:
                    st.error(f"오류: {db_status['postgresql_error']}")
        else:
            st.info("ℹ️ PostgreSQL - 설정되지 않음")
    
    with col2:
        st.subheader("⚙️ 데이터베이스 설정")
        
        # 데이터베이스 변경 옵션
        if db_status['sqlite_available'] and db_status['postgresql_available']:
            st.write("### 데이터베이스 변경")
            
            current_selection = 'postgresql' if current_db == 'postgresql' else 'sqlite'
            
            new_db = st.radio(
                "사용할 데이터베이스 선택:",
                options=['sqlite', 'postgresql'],
                format_func=lambda x: {
                    'sqlite': '🗃️ SQLite (파일 기반)',
                    'postgresql': '🐘 PostgreSQL (서버 기반)'
                }[x],
                index=0 if current_selection == 'sqlite' else 1,
                key="db_selection"
            )
            
            if st.button("데이터베이스 변경", type="primary"):
                DatabaseConfig.set_database_type(new_db)
                st.success(f"데이터베이스가 {new_db.upper()}로 변경되었습니다!")
                st.info("변경사항이 적용되려면 페이지를 새로고침하세요.")
                st.rerun()
        
        else:
            st.write("### 설정 정보")
            if not db_status['postgresql_available']:
                st.info("PostgreSQL을 사용하려면 DATABASE_URL 환경변수를 설정하세요.")
    
    # 상세 정보 섹션
    st.write("---")
    st.subheader("🔍 상세 정보")
    
    # PostgreSQL 변환된 매니저들
    st.write("### PostgreSQL 지원 매니저")
    pg_managers = [
        "✅ Employee Manager (직원 관리)",
        "✅ Customer Manager (고객 관리)", 
        "✅ Quotation Manager (견적서 관리)",
        "✅ Order Manager (주문 관리)"
    ]
    
    for manager in pg_managers:
        st.write(manager)
    
    st.write("### SQLite 전용 매니저 (변환 대기 중)")
    sqlite_managers = [
        "🔄 Product Manager (제품 관리)",
        "🔄 Supplier Manager (공급업체 관리)",
        "🔄 Approval Manager (승인 관리)",
        "🔄 Cash Flow Manager (현금 흐름 관리)",
        "🔄 기타 21개 매니저"
    ]
    
    for manager in sqlite_managers:
        st.write(manager)
    
    # 환경 변수 정보
    if st.checkbox("환경 변수 정보 표시"):
        st.write("### 환경 변수")
        if os.getenv('DATABASE_URL'):
            st.write("- **DATABASE_URL**: 설정됨 ✅")
        else:
            st.write("- **DATABASE_URL**: 설정되지 않음 ❌")
        
        # 기타 PostgreSQL 관련 환경변수들
        pg_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGDATABASE']
        for var in pg_vars:
            value = os.getenv(var)
            if value:
                st.write(f"- **{var}**: {value}")
            else:
                st.write(f"- **{var}**: 설정되지 않음")
    
    # 테스트 섹션
    st.write("---")
    st.subheader("🧪 연결 테스트")
    
    if st.button("현재 데이터베이스 연결 테스트"):
        with st.spinner("연결 테스트 중..."):
            try:
                if current_db == 'postgresql':
                    from managers.postgresql.postgresql_employee_manager import PostgreSQLEmployeeManager
                    test_manager = PostgreSQLEmployeeManager()
                    employees = test_manager.get_employee_statistics()
                    st.success(f"✅ PostgreSQL 연결 성공! (직원 수: {employees.get('total_employees', 0)})")
                else:
                    from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
                    test_manager = SQLiteEmployeeManager()
                    employees = test_manager.get_all_employees()
                    st.success(f"✅ SQLite 연결 성공! (직원 수: {len(employees)})")
            except Exception as e:
                st.error(f"❌ 연결 테스트 실패: {str(e)}")

if __name__ == "__main__":
    show_database_status_page()