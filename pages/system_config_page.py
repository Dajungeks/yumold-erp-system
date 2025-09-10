"""
시스템 설정 페이지
"""
import streamlit as st
from notification_helper import NotificationHelper

def show_system_config_page(managers, selected_submenu, get_text):
    """시스템 설정 페이지"""
    
    # 알림 헬퍼 초기화
    notif = NotificationHelper()
    
    system_config_manager = managers.get('system_config_manager')
    if not system_config_manager:
        st.error("시스템 설정 매니저가 로드되지 않았습니다.")
        return
    
    if selected_submenu == "시스템 정보":
        show_system_info_tab(system_config_manager, notif)
    elif selected_submenu == "시스템 설정":
        show_system_settings_tab(system_config_manager, notif)
    elif selected_submenu == "시스템 초기화":
        show_system_reset_tab(system_config_manager, notif)
    elif selected_submenu == "설정 이력":
        show_config_history_tab(system_config_manager, notif)
    else:
        show_system_info_tab(system_config_manager, notif)

def show_system_info_tab(system_config_manager, notif):
    """시스템 정보 탭"""
    st.subheader("🔧 시스템 정보")
    
    try:
        # 각 설정 값을 개별적으로 가져오기
        system_name = system_config_manager.get_config_value('system_name', '금도((金道)) Geumdo [ Golden Way ]')
        system_symbol = system_config_manager.get_config_value('system_symbol', '📊')
        theme_color = system_config_manager.get_config_value('theme_color', '#1976d2')
        company_name = system_config_manager.get_config_value('company_name', 'YUMOLD VIET NAM COMPANY LIMITED')
        company_logo = system_config_manager.get_config_value('company_logo', '🏭')
        
        # 현재 설정 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 시스템 정보")
            st.info(f"**시스템 이름:** {system_name}")
            st.info(f"**시스템 심볼:** {system_symbol}")
            st.info(f"**테마 색상:** {theme_color}")
        
        with col2:
            st.markdown("### 🏭 회사 정보")
            st.info(f"**회사 이름:** {company_name}")
            st.info(f"**회사 로고:** {company_logo}")
        
        # 미리보기
        st.markdown("---")
        st.markdown("### 👀 미리보기")
        
        system_title = f"{system_symbol} {system_name}"
        company_info = f"{company_logo} {company_name}"
        
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {theme_color}, #42a5f5); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h2 style="margin: 0; color: white;">{system_title}</h2>
            <p style="margin: 5px 0; color: #e3f2fd;">{company_info}</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"시스템 정보 로딩 중 오류가 발생했습니다: {str(e)}")

def show_system_settings_tab(system_config_manager, notif):
    """시스템 설정 탭"""
    st.subheader("⚙️ 시스템 설정")
    
    try:
        # 현재 설정 값들 가져오기
        current_system_name = system_config_manager.get_config_value('system_name', '금도((金道)) Geumdo [ Golden Way ]')
        current_system_symbol = system_config_manager.get_config_value('system_symbol', '📊')
        current_theme_color = system_config_manager.get_config_value('theme_color', '#1976d2')
        current_company_name = system_config_manager.get_config_value('company_name', 'YUMOLD VIET NAM COMPANY LIMITED')
        current_company_logo = system_config_manager.get_config_value('company_logo', '🏭')
        
        # 추가 회사 정보
        current_company_name_en = system_config_manager.get_config_value('company_name_en', 'YUMOLD VIET NAM COMPANY LIMITED')
        current_company_name_vn = system_config_manager.get_config_value('company_name_vn', 'CÔNG TY TNHH YUMOLD VIỆT NAM')
        current_company_tax_number = system_config_manager.get_config_value('company_tax_number', '0111146237')
        current_company_address_hanoi_en = system_config_manager.get_config_value('company_address_hanoi_en', 'Room 1201-2, 12th Floor, Keangnam Hanoi Landmark 72, E6 Area, Me Tri Ward, Nam Tu Liem District, Hanoi City, Vietnam')
        current_company_address_hanoi_vn = system_config_manager.get_config_value('company_address_hanoi_vn', 'P.1201-2, tầng 12 Keangnam Hanoi Landmark 72, khu E6, Phường Yên Hòa, Thành phố Hà Nội, Việt Nam')
        current_company_address_bacninh_en = system_config_manager.get_config_value('company_address_bacninh_en', '6th Floor, No. 255 Le Thanh Tong Street, Vo Cuong Ward, Bac Ninh City, Bac Ninh Province, Vietnam')
        current_company_address_bacninh_vn = system_config_manager.get_config_value('company_address_bacninh_vn', 'Tầng6, số nhà 255, Đường Lê Thánh Tông,Phường Võ Cường, Thành phố Bắc Ninh, Tỉnh Bắc Ninh, Việt Nam')
        
        with st.form("system_settings_form"):
            st.markdown("### 📊 시스템 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                system_name = st.text_input(
                    "시스템 이름",
                    value=current_system_name,
                    help="메인 대시보드에 표시될 시스템 이름"
                )
                
                system_symbol = st.text_input(
                    "시스템 심볼",
                    value=current_system_symbol,
                    help="시스템 이름 앞에 표시될 이모지 또는 심볼"
                )
                
                theme_color = st.color_picker(
                    "테마 색상",
                    value=current_theme_color,
                    help="시스템의 주요 테마 색상"
                )
            
            with col2:
                company_name = st.text_input(
                    "회사 이름 (기본)",
                    value=current_company_name,
                    help="기본 회사 이름"
                )
                
                company_logo = st.text_input(
                    "회사 로고",
                    value=current_company_logo,
                    help="회사 로고 (이모지 또는 텍스트)"
                )
            
            # 상세 회사 정보 섹션
            st.markdown("---")
            st.markdown("### 🏢 회사 상세 정보")
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("**영어 정보**")
                company_name_en = st.text_input(
                    "회사명 (영어)",
                    value=current_company_name_en,
                    help="영어 회사명"
                )
                
                company_address_hanoi_en = st.text_area(
                    "하노이 주소 (영어)",
                    value=current_company_address_hanoi_en,
                    height=80,
                    help="하노이 회계사무소 주소 (영어)"
                )
                
                company_address_bacninh_en = st.text_area(
                    "박닌 주소 (영어)",
                    value=current_company_address_bacninh_en,
                    height=80,
                    help="박닌 영업사무소 주소 (영어)"
                )
            
            with col4:
                st.markdown("**베트남어 정보**")
                company_name_vn = st.text_input(
                    "회사명 (베트남어)",
                    value=current_company_name_vn,
                    help="베트남어 회사명"
                )
                
                company_address_hanoi_vn = st.text_area(
                    "하노이 주소 (베트남어)",
                    value=current_company_address_hanoi_vn,
                    height=80,
                    help="하노이 회계사무소 주소 (베트남어)"
                )
                
                company_address_bacninh_vn = st.text_area(
                    "박닌 주소 (베트남어)",
                    value=current_company_address_bacninh_vn,
                    height=80,
                    help="박닌 영업사무소 주소 (베트남어)"
                )
            
            # 세금번호
            company_tax_number = st.text_input(
                "세금번호 (Tax NO)",
                value=current_company_tax_number,
                help="베트남 세금 등록번호"
            )
            
            # 미리보기
            st.markdown("---")
            st.markdown("### 👀 실시간 미리보기")
            
            preview_title = f"{system_symbol} {system_name}"
            preview_company = f"{company_logo} {company_name}"
            
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, {theme_color}, #42a5f5); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; color: white;">{preview_title}</h2>
                <p style="margin: 5px 0; color: #e3f2fd;">{preview_company}</p>
            </div>
            """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("💾 설정 저장", use_container_width=True)
            
            if submitted:
                new_config = {
                    'system_name': system_name,
                    'system_symbol': system_symbol,
                    'theme_color': theme_color,
                    'company_name': company_name,
                    'company_logo': company_logo,
                    'company_name_en': company_name_en,
                    'company_name_vn': company_name_vn,
                    'company_tax_number': company_tax_number,
                    'company_address_hanoi_en': company_address_hanoi_en,
                    'company_address_hanoi_vn': company_address_hanoi_vn,
                    'company_address_bacninh_en': company_address_bacninh_en,
                    'company_address_bacninh_vn': company_address_bacninh_vn
                }
                
                try:
                    # 각 설정 값을 개별적으로 저장
                    system_config_manager.set_config_value('system_name', system_name, 'admin', '시스템 이름 업데이트')
                    system_config_manager.set_config_value('system_symbol', system_symbol, 'admin', '시스템 심볼 업데이트')
                    system_config_manager.set_config_value('theme_color', theme_color, 'admin', '테마 색상 업데이트')
                    system_config_manager.set_config_value('company_name', company_name, 'admin', '회사 이름 업데이트')
                    system_config_manager.set_config_value('company_logo', company_logo, 'admin', '회사 로고 업데이트')
                    
                    # 상세 회사 정보 저장
                    system_config_manager.set_config_value('company_name_en', company_name_en, 'admin', '영어 회사명 업데이트')
                    system_config_manager.set_config_value('company_name_vn', company_name_vn, 'admin', '베트남어 회사명 업데이트')
                    system_config_manager.set_config_value('company_tax_number', company_tax_number, 'admin', '세금번호 업데이트')
                    system_config_manager.set_config_value('company_address_hanoi_en', company_address_hanoi_en, 'admin', '하노이 주소(영어) 업데이트')
                    system_config_manager.set_config_value('company_address_hanoi_vn', company_address_hanoi_vn, 'admin', '하노이 주소(베트남어) 업데이트')
                    system_config_manager.set_config_value('company_address_bacninh_en', company_address_bacninh_en, 'admin', '박닌 주소(영어) 업데이트')
                    system_config_manager.set_config_value('company_address_bacninh_vn', company_address_bacninh_vn, 'admin', '박닌 주소(베트남어) 업데이트')
                    
                    notif.success("시스템 설정이 성공적으로 저장되었습니다!")
                    st.rerun()
                except Exception as save_error:
                    notif.error(f"시스템 설정 저장 중 오류가 발생했습니다: {str(save_error)}")
    
    except Exception as e:
        st.error(f"시스템 설정 로딩 중 오류가 발생했습니다: {str(e)}")

def show_system_reset_tab(system_config_manager, notif):
    """시스템 초기화 탭"""
    st.subheader("🔄 시스템 초기화")
    
    st.warning("⚠️ 주의: 이 기능은 모든 시스템 설정을 기본값으로 되돌립니다.")
    
    try:
        # 현재 설정 가져오기
        current_configs = {
            'system_name': system_config_manager.get_config_value('system_name', '금도((金道)) Geumdo [ Golden Way ]'),
            'system_symbol': system_config_manager.get_config_value('system_symbol', '📊'),
            'theme_color': system_config_manager.get_config_value('theme_color', '#1976d2'),
            'company_name': system_config_manager.get_config_value('company_name', 'YUMOLD VIET NAM COMPANY LIMITED'),
            'company_logo': system_config_manager.get_config_value('company_logo', '🏭')
        }
        
        st.markdown("### 현재 설정")
        st.json(current_configs)
        
        st.markdown("### 기본 설정으로 초기화")
        
        if st.button("🔄 기본값으로 초기화", type="primary"):
            try:
                # 기본값으로 리셋
                system_config_manager.set_config_value('system_name', '금도((金道)) Geumdo [ Golden Way ]', 'admin', '기본값 초기화')
                system_config_manager.set_config_value('system_symbol', '📊', 'admin', '기본값 초기화')
                system_config_manager.set_config_value('theme_color', '#1976d2', 'admin', '기본값 초기화')
                system_config_manager.set_config_value('company_name', 'YUMOLD VIET NAM COMPANY LIMITED', 'admin', '기본값 초기화')
                system_config_manager.set_config_value('company_logo', '🏭', 'admin', '기본값 초기화')
                
                notif.success("시스템 설정이 기본값으로 초기화되었습니다!")
                st.rerun()
            except Exception as reset_error:
                notif.error(f"시스템 초기화 중 오류가 발생했습니다: {str(reset_error)}")
    
    except Exception as e:
        st.error(f"시스템 초기화 로딩 중 오류가 발생했습니다: {str(e)}")

def show_config_history_tab(system_config_manager, notif):
    """설정 이력 탭"""
    st.subheader("📜 설정 변경 이력")
    
    try:
        # 설정 이력 가져오기
        history_data = system_config_manager.get_config_history(limit=50)
        
        # 현재 설정 가져오기
        current_configs = {
            'system_name': system_config_manager.get_config_value('system_name', '금도((金道)) Geumdo [ Golden Way ]'),
            'system_symbol': system_config_manager.get_config_value('system_symbol', '📊'),
            'theme_color': system_config_manager.get_config_value('theme_color', '#1976d2'),
            'company_name': system_config_manager.get_config_value('company_name', 'YUMOLD VIET NAM COMPANY LIMITED'),
            'company_logo': system_config_manager.get_config_value('company_logo', '🏭')
        }
        
        if history_data and len(history_data) > 0:
            st.markdown("### 최근 변경 이력")
            
            # 리스트로 변환 (특정 포맷에 맞게)
            if isinstance(history_data[0], dict):
                df = pd.DataFrame(history_data)
            else:
                # 튜플 형태라면 컴럼명 설정
                df = pd.DataFrame(history_data, columns=['ID', '설정키', '이전값', '새값', '변경자', '사유', '날짜'])
            
            # 최신 5개만 표시
            st.dataframe(df.head(5), use_container_width=True)
            
            if len(df) > 5:
                if st.checkbox("전체 이력 보기"):
                    st.dataframe(df, use_container_width=True)
        else:
            st.info("아직 설정 변경 이력이 없습니다.")
        
        st.markdown("### 현재 전체 설정")
        st.json(current_configs)
        
    except Exception as e:
        st.error(f"설정 이력 로딩 중 오류가 발생했습니다: {str(e)}")