"""
PDF 디자인 매니저 - Studio Modern 스타일 전용
"""
import json
import os
import pandas as pd
from language_manager import LanguageManager
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class PDFDesignManager:
    def __init__(self):
        """PDF 디자인 매니저 초기화"""
        # 언어 매니저 초기화
        self.language_manager = LanguageManager()
        
        # 유니코드 폰트 등록
        self.unicode_font = "DejaVuSans"
        self.unicode_font_bold = "DejaVuSans-Bold"
        
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(self.unicode_font, font_path))
                print(f"Unicode font registered: {font_path}")
            
            if os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont(self.unicode_font_bold, font_bold_path))
                print(f"Unicode bold font registered: {font_bold_path}")
                
        except Exception as e:
            print(f"폰트 등록 실패: {e}")
            self.unicode_font = "Helvetica"
            self.unicode_font_bold = "Helvetica-Bold"
        
        # 회사 설정 로드
        self.load_company_settings()
    
    def load_company_settings(self):
        """회사 설정 로드"""
        try:
            settings = self.load_simple_settings()
            if settings:
                self.company_name = settings.get('company_name', '')
                self.company_subtitle = settings.get('company_subtitle', '')
                self.company_address = settings.get('company_address', '')
                self.company_phone = settings.get('company_phone', '')
                self.company_email = settings.get('company_email', '')
                self.quotation_title = settings.get('quotation_title', 'QUOTATION')
                self.footer_text = settings.get('footer_text', '')
            else:
                # 기본값 설정
                self.company_name = 'Studio Shodwe'
                self.company_subtitle = 'www.reallygreatsite.com'
                self.company_address = '123 Anywhere St., Any City'
                self.company_phone = 'Tel: +84 35 342 7562'
                self.company_email = 'hello@reallygreatsite.com'
                self.quotation_title = 'QUOTATION'
                self.footer_text = ''
                
        except Exception as e:
            print(f"회사 설정 로드 실패: {e}")
            # 기본값 설정
            self.company_name = 'Studio Shodwe'
            self.company_subtitle = 'www.reallygreatsite.com'
            self.company_address = '123 Anywhere St., Any City'
            self.company_phone = 'Tel: +84 35 342 7562'
            self.company_email = 'hello@reallygreatsite.com'
            self.quotation_title = 'QUOTATION'
            self.footer_text = ''

    def generate_quotation_pdf(self, quotation_data, template_name="studio_modern", session_settings=None, language="ko"):
        """Studio Modern 스타일 견적서 PDF를 생성합니다."""
        try:
            # 언어 설정
            self.language_manager.set_language(language)
            
            def get_text(key, default=None):
                return self.language_manager.get_text(key, default or key)
            
            # Studio Modern 렌더러 사용
            from pdf_studio_modern_renderer import StudioModernPDFRenderer
            renderer = StudioModernPDFRenderer(
                self.language_manager, 
                self.unicode_font, 
                self.unicode_font_bold
            )
            
            # 세션 설정 로드
            if session_settings:
                settings = session_settings
            else:
                settings = self.load_simple_settings()
            
            return renderer.generate_pdf(quotation_data, settings, get_text)
            
        except Exception as e:
            print(f"PDF 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_simple_settings(self):
        """간단한 PDF 설정 로드"""
        try:
            settings_file = 'data/simple_pdf_settings.json'
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
        
        # 기본 설정 반환
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

    def save_simple_settings(self, settings):
        """간단한 PDF 설정 저장"""
        try:
            settings_file = 'data/simple_pdf_settings.json'
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # 저장 후 설정 다시 로드
            self.load_company_settings()
            return True
            
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
            
    def get_available_templates(self):
        """사용 가능한 템플릿 목록 (Studio Modern 만)"""
        return {
            "studio_modern": {
                "name": "Studio Modern",
                "description": "깔끔하고 모던한 디자인",
                "preview": "studio_modern_preview.png"
            }
        }