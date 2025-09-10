"""
PDF 디자인 관리 페이지 - 단순화된 템플릿 편집 시스템
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

def show_pdf_design_page(pdf_design_manager, user_permissions, get_text):
    """PDF 디자인 관리 페이지를 표시합니다."""
    
    st.title("📄 PDF 디자인 관리")
    st.markdown("**견적서 PDF 템플릿을 커스터마이징할 수 있습니다.**")
    
    # 탭 기반 인터페이스
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 기본 설정", "🎨 헤더 디자인", "📊 테이블 스타일", "🔻 푸터 설정"
    ])
    
    with tab1:
        show_basic_settings()
    
    with tab2:
        show_header_design()
    
    with tab3:
        show_table_styles()
    
    with tab4:
        show_footer_settings()

def show_basic_settings():
    """기본 설정 섹션"""
    st.markdown("### 📋 기본 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**페이지 설정**")
        page_size = st.selectbox("페이지 크기", ["A4", "A3", "Letter", "Legal"], index=0)
        page_orientation = st.selectbox("페이지 방향", ["세로", "가로"], index=0)
        
        st.markdown("**여백 설정 (mm)**")
        margin_top = st.number_input("위쪽 여백", min_value=10, max_value=50, value=20, step=1)
        margin_bottom = st.number_input("아래쪽 여백", min_value=10, max_value=50, value=20, step=1)
        margin_left = st.number_input("왼쪽 여백", min_value=10, max_value=50, value=20, step=1)
        margin_right = st.number_input("오른쪽 여백", min_value=10, max_value=50, value=20, step=1)
    
    with col2:
        st.markdown("**색상 설정**")
        background_color = st.color_picker("배경 색상", "#FFFFFF", key="background_color")
        text_color = st.color_picker("텍스트 색상", "#000000", key="text_color")
        
        st.markdown("**템플릿 정보**")
        template_name = st.text_input("템플릿 이름", value="기본 견적서")
        template_description = st.text_area("템플릿 설명", 
                                          value="표준 견적서 템플릿입니다.",
                                          height=100)
        
        st.markdown("**언어 설정**")
        default_language = st.selectbox("기본 언어", ["한국어", "English", "Tiếng Việt"], index=0)
    
    # 저장 버튼
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 기본 설정 저장", type="primary", use_container_width=True, key="save_basic_settings"):
            # 기본 설정을 세션 상태에 저장
            basic_settings = {
                'page_size': page_size,
                'page_orientation': page_orientation,
                'margins': {
                    'top': margin_top,
                    'bottom': margin_bottom,
                    'left': margin_left,
                    'right': margin_right
                },
                'colors': {
                    'background': background_color,
                    'text': text_color
                },
                'template_info': {
                    'name': template_name,
                    'description': template_description,
                    'language': default_language
                }
            }
            
            st.session_state.basic_settings = basic_settings
            st.success("✅ 기본 설정이 성공적으로 저장되었습니다!")

def show_header_design():
    """헤더 디자인 섹션"""
    st.markdown("### 🎨 헤더 디자인")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**회사 정보**")
        company_name = st.text_input("회사명", value="YUMOLD VIETNAM")
        company_address = st.text_area("회사 주소", 
                                     value="Lot A2-CN, Tan Tao Industrial Park,\nTan Tao A Ward, Binh Tan District,\nHo Chi Minh City, Vietnam",
                                     height=100)
        
        st.markdown("**연락처 정보**")
        phone = st.text_input("전화번호", value="+84-28-3754-5678")
        email = st.text_input("이메일", value="info@yumoldvietnam.com")
        website = st.text_input("웹사이트", value="www.yumoldvietnam.com")
    
    with col2:
        st.markdown("**헤더 스타일**")
        header_height = st.slider("헤더 높이 (mm)", 30, 100, 60)
        header_bg_color = st.color_picker("헤더 배경색", "#F0F0F0", key="header_design_bg_color")
        header_text_color = st.color_picker("헤더 텍스트색", "#000000", key="header_design_text_color")
        
        st.markdown("**로고 설정**")
        show_logo = st.checkbox("로고 표시", value=True)
        
        if show_logo:
            logo_position = st.selectbox("로고 위치", ["왼쪽", "중앙", "오른쪽"], index=0)
            logo_size = st.slider("로고 크기 (%)", 50, 200, 100)
        else:
            logo_position = "왼쪽"
            logo_size = 100
        
        st.markdown("**폰트 설정**")
        header_font_size = st.slider("폰트 크기 (pt)", 8, 24, 12)
        header_font_weight = st.selectbox("폰트 굵기", ["보통", "굵게", "매우 굵게"], index=0)
    
    # 저장 버튼
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 헤더 설정 저장", type="primary", use_container_width=True, key="save_header_settings"):
            # 헤더 설정을 세션 상태에 저장
            header_settings = {
                'company_info': {
                    'name': company_name,
                    'address': company_address,
                    'phone': phone,
                    'email': email,
                    'website': website
                },
                'header_style': {
                    'height': header_height,
                    'bg_color': header_bg_color,
                    'text_color': header_text_color,
                    'font_size': header_font_size,
                    'font_weight': header_font_weight
                },
                'logo_settings': {
                    'show_logo': show_logo,
                    'position': logo_position if show_logo else "왼쪽",
                    'size': logo_size if show_logo else 100
                }
            }
            
            st.session_state.header_settings = header_settings
            st.success("✅ 헤더 설정이 성공적으로 저장되었습니다!")
            
        # 현재 저장된 설정 확인 (디버깅용)
        if st.button("🔍 현재 저장된 헤더 설정 확인", key="check_header_settings"):
            st.write("**현재 세션 상태의 헤더 설정:**")
            if 'header_settings' in st.session_state:
                st.json(st.session_state.header_settings)
            else:
                st.warning("저장된 헤더 설정이 없습니다. 위의 '헤더 설정 저장' 버튼을 먼저 클릭하세요.")

def show_table_styles():
    """테이블 스타일 섹션"""
    st.markdown("### 📊 테이블 스타일")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**테이블 기본 설정**")
        table_width = st.slider("테이블 너비 (%)", 50, 100, 100)
        table_align = st.selectbox("테이블 정렬", ["왼쪽", "중앙", "오른쪽"], index=0)
        
        st.markdown("**테이블 색상**")
        table_bg_color = st.color_picker("테이블 배경색", "#FFFFFF", key="table_bg_color")
        table_border_color = st.color_picker("테이블 테두리색", "#000000", key="table_border_color")
        
        st.markdown("**헤더 설정**")
        header_bg_color = st.color_picker("헤더 배경색", "#E0E0E0", key="header_bg_color")
        header_text_color = st.color_picker("헤더 텍스트색", "#000000", key="header_text_color")
        header_font_size = st.slider("헤더 폰트 크기 (pt)", 8, 18, 12)
        header_bold = st.checkbox("헤더 굵게", value=True)
    
    with col2:
        st.markdown("**테이블 행 설정**")
        row_height = st.slider("행 높이 (mm)", 5, 15, 8)
        row_font_size = st.slider("행 폰트 크기 (pt)", 8, 16, 10)
        
        st.markdown("**테두리 설정**")
        border_width = st.slider("테두리 두께 (pt)", 0.5, 3.0, 1.0, step=0.1)
        show_grid = st.checkbox("격자 표시", value=True)
        
        st.markdown("**자동 열 너비**")
        auto_column_width = st.checkbox("자동 열 너비 조정", value=True)
        
        st.markdown("**행 번갈아 색상**")
        alternate_rows = st.checkbox("행 번갈아 색상", value=True)
        
        if alternate_rows:
            alt_row_color = st.color_picker("번갈아 행 색상", "#F9F9F9")
        else:
            alt_row_color = "#F9F9F9"
    
    # 저장 버튼
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 테이블 스타일 저장", type="primary", use_container_width=True, key="save_table_settings"):
            # 테이블 설정을 세션 상태에 저장
            table_settings = {
                'basic': {
                    'width': table_width,
                    'align': table_align,
                    'bg_color': table_bg_color,
                    'border_color': table_border_color
                },
                'header': {
                    'bg_color': header_bg_color,
                    'text_color': header_text_color,
                    'font_size': header_font_size,
                    'bold': header_bold
                },
                'rows': {
                    'height': row_height,
                    'font_size': row_font_size,
                    'alternate_rows': alternate_rows,
                    'alt_row_color': alt_row_color
                },
                'borders': {
                    'width': border_width,
                    'show_grid': show_grid
                },
                'columns': {
                    'auto_width': auto_column_width
                }
            }
            
            st.session_state.table_settings = table_settings
            st.success("✅ 테이블 스타일이 성공적으로 저장되었습니다!")

def show_footer_settings():
    """푸터 설정 섹션"""
    st.markdown("### 🔻 푸터 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**푸터 내용**")
        footer_text = st.text_area("푸터 텍스트", 
                                  value="감사합니다. Thank you for your business.",
                                  height=100)
        
        st.markdown("**페이지 번호**")
        show_page_number = st.checkbox("페이지 번호 표시", value=True)
        if show_page_number:
            page_number_format = st.selectbox("페이지 번호 형식", 
                                            ["페이지 1", "Page 1", "1 / 총 페이지", "1 of Total"])
            page_number_position = st.selectbox("페이지 번호 위치", 
                                              ["왼쪽", "중앙", "오른쪽"], index=2)
        else:
            page_number_format = "페이지 1"
            page_number_position = "오른쪽"
        
        st.markdown("**날짜 정보**")
        show_date = st.checkbox("생성 날짜 표시", value=True)
        if show_date:
            date_format = st.selectbox("날짜 형식", 
                                     ["2025-07-04", "2025년 7월 4일", "July 4, 2025"])
        else:
            date_format = "2025-07-04"
    
    with col2:
        st.markdown("**푸터 스타일**")
        footer_height = st.slider("푸터 높이 (mm)", 10, 50, 20)
        footer_bg_color = st.color_picker("푸터 배경색", "#F5F5F5", key="footer_bg_color")
        footer_text_color = st.color_picker("푸터 텍스트색", "#666666", key="footer_text_color")
        
        st.markdown("**푸터 정렬**")
        footer_align = st.selectbox("푸터 정렬", ["왼쪽", "중앙", "오른쪽"], index=1)
        
        st.markdown("**푸터 폰트**")
        footer_font_size = st.slider("푸터 폰트 크기 (pt)", 6, 14, 9)
        footer_italic = st.checkbox("푸터 기울임", value=True)
        
        st.markdown("**푸터 선**")
        footer_border = st.checkbox("푸터 상단 선", value=True)
        if footer_border:
            footer_border_color = st.color_picker("푸터 선 색상", "#CCCCCC", key="footer_border_color")
            footer_border_width = st.slider("푸터 선 두께 (pt)", 0.5, 2.0, 1.0, step=0.1)
        else:
            footer_border_color = "#CCCCCC"
            footer_border_width = 1.0
    
    # 저장 버튼
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 푸터 설정 저장", type="primary", use_container_width=True, key="save_footer_settings"):
            # 푸터 설정을 세션 상태에 저장
            footer_settings = {
                "footer_text": footer_text,
                "show_page_number": show_page_number,
                "page_number_format": page_number_format,
                "page_number_position": page_number_position,
                "show_date": show_date,
                "date_format": date_format,
                "style": {
                    "height": footer_height,
                    "bg_color": footer_bg_color,
                    "text_color": footer_text_color,
                    "align": footer_align,
                    "font_size": footer_font_size,
                    "italic": footer_italic,
                    "border": footer_border,
                    "border_color": footer_border_color,
                    "border_width": footer_border_width
                }
            }
            
            st.session_state.footer_settings = footer_settings
            st.success("✅ 푸터 설정이 성공적으로 저장되었습니다!")