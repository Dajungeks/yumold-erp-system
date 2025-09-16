import streamlit as st
import psycopg2
import bcrypt
from datetime import datetime

def show_password_admin_page():
    """마스터 전용 비밀번호 관리 페이지"""
    
    # 마스터 권한 확인
    if st.session_state.get('access_level') != 'master':
        st.error("❌ 마스터 권한이 필요합니다.")
        return
    
    st.header("🔐 직원 비밀번호 관리 (마스터 전용)")
    
    tab1, tab2 = st.tabs(["비밀번호 초기화", "비밀번호 정책 설정"])
    
    with tab1:
        st.subheader("직원 비밀번호 초기화")
        
        try:
            conn = psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                port=st.secrets["postgres"]["port"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"]
            )
            cursor = conn.cursor()
            
            # 직원 목록 가져오기
            cursor.execute("""
                SELECT employee_id, name, department, position
                FROM employees
                ORDER BY employee_id
            """)
            employees = cursor.fetchall()
            
            if employees:
                # 직원 선택
                employee_options = [f"{emp[0]} - {emp[1]} ({emp[2]} {emp[3]})" for emp in employees]
                selected = st.selectbox("직원 선택", employee_options)
                
                if selected:
                    selected_id = selected.split(" - ")[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_password = st.text_input("새 비밀번호", type="password")
                        confirm_password = st.text_input("비밀번호 확인", type="password")
                    
                    with col2:
                        st.info("""
                        **비밀번호 요구사항:**
                        - 최소 8자 이상
                        - 대문자 포함
                        - 소문자 포함
                        - 숫자 포함
                        """)
                    
                    if st.button("비밀번호 초기화", type="primary"):
                        if new_password != confirm_password:
                            st.error("비밀번호가 일치하지 않습니다")
                        elif len(new_password) < 8:
                            st.error("비밀번호는 8자 이상이어야 합니다")
                        else:
                            # bcrypt 해시 생성
                            hashed = bcrypt.hashpw(
                                new_password.encode('utf-8'),
                                bcrypt.gensalt()
                            ).decode('utf-8')
                            
                            # DB 업데이트
                            cursor.execute("""
                                UPDATE employees 
                                SET password = %s,
                                    password_changed_date = NOW(),
                                    password_change_required = FALSE,
                                    login_attempts = 0,
                                    account_locked_until = NULL
                                WHERE employee_id = %s
                            """, (hashed, selected_id))
                            
                            conn.commit()
                            st.success(f"✅ {selected_id}의 비밀번호가 초기화되었습니다.")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
    
    with tab2:
        st.subheader("비밀번호 정책")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("최소 길이", "8자")
            st.metric("로그인 시도 제한", "5회")
        with col2:
            st.metric("계정 잠금 시간", "5분")
            st.metric("비밀번호 변경 주기", "90일")
