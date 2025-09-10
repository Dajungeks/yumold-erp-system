"""
향상된 PDF 디자인 관리 - 간단하고 직관적인 버전
"""
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

def show_enhanced_pdf_design_page(pdf_design_manager, quotation_manager, customer_manager, user_permissions, get_text):
    """향상된 PDF 디자인 관리 페이지"""
    
    st.markdown("### 🎨 Studio Modern PDF 디자인 관리")
    st.markdown("**깔끔하고 모던한 견적서 템플릿 - 실시간 설정 변경과 즉시 테스트 가능**")
    
    # 현재 설정 로드
    settings_file = 'data/simple_pdf_settings.json'
    current_settings = load_current_settings(settings_file)
    
    # 메인 레이아웃
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("#### ⚙️ 디자인 설정")
        
        # 회사 정보 섹션
        with st.expander("🏢 회사 기본 정보", expanded=True):
            company_name = st.text_input("회사명", 
                                       value=current_settings.get("company_name", ""),
                                       key="company_name_input")
            
            company_subtitle = st.text_input("회사 부제목", 
                                           value=current_settings.get("company_subtitle", ""),
                                           key="company_subtitle_input")
            
            company_address = st.text_area("회사 주소", 
                                         value=current_settings.get("company_address", ""),
                                         height=80,
                                         key="company_address_input")
            
            col_contact1, col_contact2 = st.columns(2)
            with col_contact1:
                company_phone = st.text_input("전화번호", 
                                            value=current_settings.get("company_phone", ""),
                                            key="company_phone_input")
            
            with col_contact2:
                company_email = st.text_input("이메일", 
                                            value=current_settings.get("company_email", ""),
                                            key="company_email_input")
        
        # 디자인 스타일 섹션
        with st.expander("🎨 디자인 & 색상", expanded=True):
            quotation_title = st.text_input("견적서 제목", 
                                           value=current_settings.get("quotation_title", "QUOTATION"),
                                           key="quotation_title_input")
            
            col_color1, col_color2 = st.columns(2)
            with col_color1:
                header_color = st.color_picker("헤더 색상", 
                                              value=current_settings.get("header_color", "#000000"),
                                              key="header_color_picker")
                table_header_color = st.color_picker("테이블 헤더 색상", 
                                                    value=current_settings.get("table_header_color", "#000000"),
                                                    key="table_header_color_picker")
            
            with col_color2:
                title_color = st.color_picker("제목 색상", 
                                             value=current_settings.get("title_color", "#000000"),
                                             key="title_color_picker")
                border_color = st.color_picker("테두리 색상", 
                                              value=current_settings.get("border_color", "#000000"),
                                              key="border_color_picker")
            
            # 폰트 크기 설정
            col_font1, col_font2, col_font3 = st.columns(3)
            with col_font1:
                font_size_company = st.slider("회사명 폰트", 8, 20, 
                                             value=current_settings.get("font_size_company", 12),
                                             key="font_company_slider")
            with col_font2:
                font_size_title = st.slider("제목 폰트", 20, 50, 
                                           value=current_settings.get("font_size_title", 32),
                                           key="font_title_slider")
            with col_font3:
                font_size_table = st.slider("테이블 폰트", 8, 18, 
                                           value=current_settings.get("font_size_table", 14),
                                           key="font_table_slider")
        
        # 추가 옵션
        with st.expander("📄 문서 옵션", expanded=False):
            show_subtitle = st.checkbox("회사 부제목 표시", 
                                       value=current_settings.get("show_company_subtitle", True),
                                       key="show_subtitle_checkbox")
            
            show_border = st.checkbox("테이블 테두리 표시", 
                                     value=current_settings.get("show_border", True),
                                     key="show_border_checkbox")
            
            footer_text = st.text_area("푸터 텍스트", 
                                      value=current_settings.get("footer_text", ""),
                                      height=60,
                                      key="footer_text_input")
    
    with col2:
        st.markdown("#### 🛠️ 관리 도구")
        
        # 새로운 설정 딕셔너리 생성
        new_settings = {
            "company_name": company_name,
            "company_subtitle": company_subtitle,
            "company_address": company_address,
            "company_phone": company_phone,
            "company_email": company_email,
            "quotation_title": quotation_title,
            "header_color": header_color,
            "title_color": title_color,
            "table_header_color": table_header_color,
            "border_color": border_color,
            "font_size_company": font_size_company,
            "font_size_title": font_size_title,
            "font_size_table": font_size_table,
            "show_company_subtitle": show_subtitle,
            "show_border": show_border,
            "footer_text": footer_text
        }
        
        # 액션 버튼들
        if st.button("💾 설정 저장", type="primary", use_container_width=True):
            if save_settings(settings_file, new_settings):
                st.success("✅ 설정이 저장되었습니다!")
                st.rerun()
            else:
                st.error("❌ 저장에 실패했습니다.")
        
        if st.button("🔄 기본값 복원", use_container_width=True):
            if reset_to_defaults(settings_file):
                st.success("✅ 기본 설정으로 복원되었습니다!")
                st.rerun()
        
        if st.button("🧪 실제 적용 테스트", use_container_width=True):
            test_pdf_application(pdf_design_manager, quotation_manager, new_settings)
        
        # 설정 미리보기
        st.markdown("---")
        st.markdown("**📊 현재 설정 요약**")
        
        with st.expander("설정 미리보기", expanded=False):
            st.json({
                "회사명": company_name,
                "견적서 제목": quotation_title,
                "헤더 색상": header_color,
                "제목 폰트 크기": font_size_title,
                "부제목 표시": show_subtitle,
                "테두리 표시": show_border
            })

def test_pdf_application(pdf_design_manager, quotation_manager, settings):
    """실제 PDF 생성 테스트"""
    st.markdown("#### 🧪 실제 적용 테스트 결과")
    
    with st.spinner("PDF 생성 테스트 중..."):
        try:
            # 1. 설정 임시 저장
            temp_file = 'data/temp_test_settings.json'
            save_settings(temp_file, settings)
            
            # 2. 견적서 데이터 가져오기
            test_data = get_test_quotation_data(quotation_manager)
            
            # 3. 3개 언어로 PDF 생성 테스트
            languages = [("한국어", "ko"), ("English", "en"), ("Tiếng Việt", "vi")]
            results = {}
            
            for lang_name, lang_code in languages:
                try:
                    pdf_bytes = pdf_design_manager.generate_quotation_pdf(
                        test_data,
                        template_name="studio_modern",
                        session_settings=settings,
                        language=lang_code
                    )
                    
                    if pdf_bytes:
                        results[lang_name] = {
                            "success": True,
                            "size": len(pdf_bytes),
                            "data": pdf_bytes
                        }
                        st.success(f"✅ {lang_name} PDF 생성 성공 ({len(pdf_bytes):,} bytes)")
                    else:
                        results[lang_name] = {"success": False}
                        st.error(f"❌ {lang_name} PDF 생성 실패")
                        
                except Exception as e:
                    results[lang_name] = {"success": False, "error": str(e)}
                    st.error(f"❌ {lang_name} PDF 오류: {e}")
            
            # 4. 다운로드 버튼 제공
            st.markdown("---")
            st.markdown("**📥 테스트 PDF 다운로드**")
            
            successful_results = [r for r in results.values() if r.get("success")]
            num_successful = len(successful_results)
            
            if num_successful > 0:
                download_cols = st.columns(num_successful)
                col_idx = 0
            
                for lang_name, result in results.items():
                    if result.get("success"):
                        with download_cols[col_idx]:
                            st.download_button(
                                label=f"{lang_name} PDF",
                                data=result["data"],
                                file_name=f"test_{lang_name}_{datetime.now().strftime('%m%d_%H%M')}.pdf",
                                mime="application/pdf",
                                key=f"download_{lang_name}",
                                use_container_width=True
                            )
                        col_idx += 1
            else:
                st.warning("생성된 PDF가 없어 다운로드 버튼을 표시할 수 없습니다.")
            
            # 5. 테스트 요약
            total_tests = len(languages)
            successful_tests = len([r for r in results.values() if r.get("success")])
            
            if successful_tests == total_tests:
                st.success(f"🎉 모든 테스트 통과! ({successful_tests}/{total_tests})")
            else:
                st.warning(f"⚠️ 일부 테스트 실패 ({successful_tests}/{total_tests})")
            
            # 임시 파일 정리
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            st.error(f"❌ 테스트 중 오류 발생: {e}")

def get_test_quotation_data(quotation_manager):
    """실제 견적서 데이터 가져오기 (테스트 아닌 실제 데이터)"""
    try:
        # SQLite에서 최신 견적서 데이터 조회
        if hasattr(quotation_manager, 'get_all_quotations'):
            quotations = quotation_manager.get_all_quotations()
            if quotations and len(quotations) > 0:
                # 가장 최신 견적서 사용
                latest_quotation = quotations[0]  # 이미 DESC 정렬되어 있음
                
                if 'quotation_number' in latest_quotation and latest_quotation['quotation_number']:
                    st.info(f"📄 SQLite에서 최신 견적서 사용: {latest_quotation.get('quotation_number', 'N/A')}")
                    return latest_quotation
                
    except Exception as e:
        st.error(f"SQLite 견적서 데이터 로드 실패: {e}")
        print(f"SQLite 견적서 데이터 로드 실패: {e}")
    
    # 실제 데이터가 없을 때만 샘플 데이터 반환
    st.warning("⚠️ 실제 견적서 데이터를 찾을 수 없어 샘플 데이터를 사용합니다. 먼저 견적서를 생성해주세요.")
    return {
        'quotation_id': 'SAMPLE001',
        'quotation_number': 'Q' + datetime.now().strftime('%Y%m%d') + '001',
        'customer_name': '샘플 고객사',
        'customer_id': 'C001',
        'quote_date': datetime.now().strftime('%Y-%m-%d'),
        'valid_until': (datetime.now() + pd.Timedelta(days=30)).strftime('%Y-%m-%d'),
        'currency': 'USD',
        'total_amount': 0.00,
        'status': '진행중',
        'project_name': '샘플 프로젝트',
        'contact_person': '담당자명',
        'contact_detail': 'contact@example.com',
        'quotation_title': '견적서',
        'remark': '실제 견적서 데이터를 생성하면 여기에 표시됩니다',
        'sales_representative': '영업담당자',
        'sales_rep_contact': '010-0000-0000',
        'sales_rep_email': 'sales@company.com',
        'products_json': json.dumps([])  # 빈 제품 리스트
    }

def load_current_settings(settings_file):
    """현재 설정 로드"""
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"설정 파일 로드 실패: {e}")
    
    # 기본값 반환
    return {
        "company_name": "Studio Shodwe",
        "company_subtitle": "www.reallygreatsite.com",
        "company_address": "123 Anywhere St., Any City",
        "company_phone": "Tel: +84 35 342 7562",
        "company_email": "hello@reallygreatsite.com", 
        "quotation_title": "QUOTATION",
        "header_color": "#2B4F3E",
        "title_color": "#2B4F3E",
        "table_header_color": "#F5F3F0",
        "border_color": "#CCCCCC",
        "font_size_company": 16,
        "font_size_title": 24,
        "font_size_table": 10,
        "show_company_subtitle": True,
        "show_border": True,
        "footer_text": "Terms & Conditions: Payment due within 30 days. Prices are valid for 30 days from quotation date."
    }

def save_settings(settings_file, settings):
    """설정 저장"""
    try:
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"설정 저장 실패: {e}")
        return False

def reset_to_defaults(settings_file):
    """기본값으로 리셋"""
    default_settings = {
        "company_name": "Studio Shodwe",
        "company_subtitle": "www.reallygreatsite.com",
        "company_address": "123 Anywhere St., Any City", 
        "company_phone": "Tel: +84 35 342 7562",
        "company_email": "hello@reallygreatsite.com",
        "quotation_title": "QUOTATION",
        "header_color": "#2B4F3E",
        "title_color": "#2B4F3E",
        "table_header_color": "#F5F3F0",
        "border_color": "#CCCCCC",
        "font_size_company": 16,
        "font_size_title": 24,
        "font_size_table": 10,
        "show_company_subtitle": True,
        "show_border": True,
        "footer_text": "Terms & Conditions: Payment due within 30 days. Prices are valid for 30 days from quotation date."
    }
    
    return save_settings(settings_file, default_settings)