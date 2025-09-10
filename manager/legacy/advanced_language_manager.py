"""
고급 다국어 관리 시스템
- 3개 언어 완벽 지원 (한국어, 영어, 베트남어)
- 번역 누락 자동 감지
- 새 언어 쉬운 추가
- 하드코딩 텍스트 자동 치환
"""
import json
import os
import re
from typing import Dict, List, Set, Optional, Any
# Import streamlit only when needed to avoid circular imports
try:
    import streamlit as st
except ImportError:
    # Fallback for when streamlit is not available
    class MockStreamlit:
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
    st = MockStreamlit()
from datetime import datetime

class AdvancedLanguageManager:
    def __init__(self):
        self.locales_dir = "locales"
        self.supported_languages = {
            "ko": {"name": "한국어", "flag": "🇰🇷", "enabled": True},
            "en": {"name": "English", "flag": "🇺🇸", "enabled": True}, 
            "vi": {"name": "Tiếng Việt", "flag": "🇻🇳", "enabled": True}
        }
        self.current_language = "ko"
        self.translations = {}
        self.missing_keys = set()
        self.translation_stats = {}
        self.ensure_infrastructure()
    
    def ensure_infrastructure(self):
        """다국어 인프라 초기화"""
        os.makedirs(self.locales_dir, exist_ok=True)
        self.load_all_languages()
        self.validate_translations()
    
    def load_all_languages(self):
        """모든 언어 파일 로드"""
        for lang_code in self.supported_languages.keys():
            self.load_language_file(lang_code)
    
    def load_language(self, language_code: str) -> bool:
        """특정 언어 파일 로드 (메서드명 호환성)"""
        return self.load_language_file(language_code)
    
    def load_language_file(self, language_code: str) -> bool:
        """특정 언어 파일 로드"""
        try:
            locale_file = os.path.join(self.locales_dir, f"{language_code}.json")
            if os.path.exists(locale_file):
                with open(locale_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if language_code not in self.translations:
                        self.translations[language_code] = {}
                    self.translations[language_code].update(content)
                return True
            else:
                self.translations[language_code] = {}
                return self.create_empty_language_file(language_code)
        except Exception as e:
            print(f"ERROR: 언어 파일 로드 오류 {language_code}: {e}")
            return False
    
    def create_empty_language_file(self, language_code: str) -> bool:
        """빈 언어 파일 생성"""
        try:
            empty_structure = {
                "_meta": {
                    "language_code": language_code,
                    "language_name": self.supported_languages[language_code]["name"],
                    "created_date": datetime.now().isoformat(),
                    "completion_rate": 0
                },
                # 기본 구조
                "app": {},
                "menu": {},
                "buttons": {},
                "labels": {},
                "messages": {},
                "errors": {},
                "success": {},
                "warnings": {}
            }
            return self.save_language_file(language_code, empty_structure)
        except Exception as e:
            print(f"ERROR: 빈 언어 파일 생성 오류 {language_code}: {e}")
            return False
    
    def set_language(self, language_code: str) -> bool:
        """현재 언어 설정"""
        if language_code in self.supported_languages:
            self.current_language = language_code
            # Streamlit 세션 상태 설정 (사용 가능한 경우)
            try:
                import streamlit as st_real
                if hasattr(st_real, 'session_state'):
                    if 'language' not in st_real.session_state:
                        st_real.session_state.language = language_code
                    st_real.session_state.language = language_code
            except:
                pass
            return True
        return False
    
    def get_text(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """번역 텍스트 가져오기 (포맷팅 지원)"""
        if default is None:
            default = key
            
        # 현재 언어에서 키 찾기
        current_lang = self.current_language
        if current_lang in self.translations:
            text = self._get_nested_key(self.translations[current_lang], key)
            if text:
                # 변수 치환 (예: {name}, {count} 등)
                if kwargs:
                    try:
                        return text.format(**kwargs)
                    except KeyError as e:
                        print(f"WARNING: 번역 변수 오류: {key} - {e}")
                        return text
                return text
        
        # 누락된 키 기록
        self.missing_keys.add(f"{current_lang}:{key}")
        
        # 기본값 반환
        if kwargs and default:
            try:
                return default.format(**kwargs)
            except:
                pass
        return default
    
    def _get_nested_key(self, data: dict, key: str) -> Optional[str]:
        """중첩된 키 접근 (예: menu.customer.title)"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def validate_translations(self) -> Dict[str, Any]:
        """번역 완성도 검증"""
        validation_result = {
            "total_keys": 0,
            "languages": {},
            "missing_keys": {},
            "common_keys": set()
        }
        
        # 모든 키 수집
        all_keys = set()
        for lang_code, translations in self.translations.items():
            keys = self._extract_all_keys(translations)
            all_keys.update(keys)
            
        validation_result["total_keys"] = len(all_keys)
        validation_result["common_keys"] = all_keys
        
        # 각 언어별 완성도 검사
        for lang_code in self.supported_languages.keys():
            if lang_code in self.translations:
                lang_keys = set(self._extract_all_keys(self.translations[lang_code]))
                missing = all_keys - lang_keys
                completion_rate = ((len(all_keys) - len(missing)) / len(all_keys) * 100) if all_keys else 100
                
                validation_result["languages"][lang_code] = {
                    "completion_rate": completion_rate,
                    "missing_count": len(missing),
                    "total_keys": len(lang_keys)
                }
                validation_result["missing_keys"][lang_code] = list(missing)
        
        return validation_result
    
    def _extract_all_keys(self, data: dict, prefix: str = "") -> List[str]:
        """모든 중첩 키 추출"""
        keys = []
        for key, value in data.items():
            if key.startswith('_'):  # 메타데이터 제외
                continue
                
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                keys.extend(self._extract_all_keys(value, full_key))
            elif isinstance(value, str):
                keys.append(full_key)
        
        return keys
    
    def add_language(self, language_code: str, language_name: str, flag: str = "🌐") -> bool:
        """새 언어 추가"""
        if language_code not in self.supported_languages:
            self.supported_languages[language_code] = {
                "name": language_name,
                "flag": flag,
                "enabled": True
            }
            return self.create_empty_language_file(language_code)
        return False
    
    def auto_translate_missing(self, target_lang: str, source_lang: str = "ko") -> Dict[str, Any]:
        """누락된 번역 자동 복사 (수동 번역 기반)"""
        if target_lang not in self.translations or source_lang not in self.translations:
            return {"error": "언어 파일 없음"}
        
        source_keys = set(self._extract_all_keys(self.translations[source_lang]))
        target_keys = set(self._extract_all_keys(self.translations[target_lang]))
        missing_keys = source_keys - target_keys
        
        added_count = 0
        for key in missing_keys:
            source_text = self._get_nested_key(self.translations[source_lang], key)
            if source_text:
                self._set_nested_key(self.translations[target_lang], key, f"[번역필요] {source_text}")
                added_count += 1
        
        if added_count > 0:
            self.save_language_file(target_lang, self.translations[target_lang])
        
        return {"added": added_count, "missing": len(missing_keys)}
    
    def _set_nested_key(self, data: dict, key: str, value: str):
        """중첩 키에 값 설정"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_language_file(self, language_code: str, data: dict) -> bool:
        """언어 파일 저장"""
        try:
            locale_file = os.path.join(self.locales_dir, f"{language_code}.json")
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"ERROR: 언어 파일 저장 오류 {language_code}: {e}")
            return False
    
    def save_current_language(self) -> bool:
        """현재 언어 파일 저장"""
        if self.current_language in self.translations:
            return self.save_language_file(self.current_language, self.translations[self.current_language])
        return False
    
    def get_language_selector_options(self) -> Dict[str, str]:
        """언어 선택기 옵션 반환"""
        options = {}
        for code, info in self.supported_languages.items():
            if info["enabled"]:
                options[code] = f"{info['flag']} {info['name']}"
        return options
    
    def get_completion_stats(self) -> Dict[str, float]:
        """언어별 완성도 통계"""
        validation = self.validate_translations()
        return {
            lang: info["completion_rate"] 
            for lang, info in validation["languages"].items()
        }
    
    def scan_hardcoded_text(self, file_path: str) -> List[Dict[str, str]]:
        """하드코딩된 텍스트 스캔"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 한국어 패턴 찾기
            korean_pattern = r'[가-힣]+[^"\']*'
            hardcoded_texts = []
            
            # st.success, st.error, st.warning 내부 한국어 찾기
            streamlit_functions = ['st.success', 'st.error', 'st.warning', 'st.info']
            
            for func in streamlit_functions:
                pattern = rf'{func}\(["\']([^"\']*[가-힣][^"\']*)["\']'
                matches = re.finditer(pattern, content)
                for match in matches:
                    hardcoded_texts.append({
                        'function': func,
                        'text': match.group(1),
                        'line': content[:match.start()].count('\n') + 1,
                        'suggestion': f'get_text("{func.replace("st.", "msg_")}_key", "{match.group(1)}")'
                    })
            
            return hardcoded_texts
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def generate_translation_report(self) -> str:
        """번역 상태 보고서 생성"""
        validation = self.validate_translations()
        report = []
        
        report.append("# 🌍 다국어 지원 현황 보고서\n")
        report.append(f"**총 번역 키 수**: {validation['total_keys']}개\n")
        
        for lang_code, stats in validation["languages"].items():
            lang_info = self.supported_languages[lang_code]
            completion = stats["completion_rate"]
            
            report.append(f"## {lang_info['flag']} {lang_info['name']}")
            report.append(f"- **완성도**: {completion:.1f}%")
            report.append(f"- **번역된 키**: {stats['total_keys']}개")
            report.append(f"- **누락된 키**: {stats['missing_count']}개")
            
            if stats['missing_count'] > 0:
                report.append(f"- **누락 키 목록**: {', '.join(validation['missing_keys'][lang_code][:10])}")
                if len(validation['missing_keys'][lang_code]) > 10:
                    report.append(f"  (외 {len(validation['missing_keys'][lang_code]) - 10}개)")
            report.append("")
        
        return "\n".join(report)

# 전역 인스턴스
advanced_lang_manager = AdvancedLanguageManager()

def get_text(key: str, default: Optional[str] = None, **kwargs) -> str:
    """전역 번역 함수"""
    return advanced_lang_manager.get_text(key, default, **kwargs)

def set_language(language_code: str) -> bool:
    """전역 언어 설정 함수"""
    return advanced_lang_manager.set_language(language_code)

def get_current_language() -> str:
    """현재 언어 코드 반환"""
    return advanced_lang_manager.current_language