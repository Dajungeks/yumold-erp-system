import json
import os

class LanguageManager:
    def __init__(self):
        self.locales_dir = "locales"
        self.current_language = "ko"
        self.translations = {}
        self.ensure_locales_directory()
        self.load_language(self.current_language)
    
    def ensure_locales_directory(self):
        """Ensure locales directory exists"""
        os.makedirs(self.locales_dir, exist_ok=True)
    
    def load_language(self, language_code):
        """Load language translations"""
        try:
            locale_file = os.path.join(self.locales_dir, f"{language_code}.json")
            if os.path.exists(locale_file):
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.current_language = language_code
                return True
            else:
                print(f"Language file not found: {locale_file}")
                return False
        except Exception as e:
            print(f"Error loading language {language_code}: {e}")
            return False
    
    def set_language(self, language_code):
        """Set current language"""
        return self.load_language(language_code)
    
    def get_text(self, key, default=None):
        """Get translated text for key"""
        if default is None:
            default = key
        
        return self.translations.get(key, default)
    
    def get_current_language(self):
        """Get current language code"""
        return self.current_language
    
    def get_available_languages(self):
        """Get list of available languages"""
        languages = []
        try:
            for file in os.listdir(self.locales_dir):
                if file.endswith('.json'):
                    lang_code = file.replace('.json', '')
                    languages.append(lang_code)
        except Exception as e:
            print(f"Error getting available languages: {e}")
        
        return sorted(languages)
    
    def add_translation(self, key, value):
        """Add or update translation for current language"""
        self.translations[key] = value
    
    def save_current_language(self):
        """Save current language translations to file"""
        try:
            locale_file = os.path.join(self.locales_dir, f"{self.current_language}.json")
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving language file: {e}")
            return False
