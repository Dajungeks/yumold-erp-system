"""
시스템 설정 관리 모듈
"""
import pandas as pd
import os
from datetime import datetime
import json

class SystemConfigManager:
    def __init__(self):
        self.data_dir = "data"
        self.config_file = os.path.join(self.data_dir, "system_config.json")
        self.ensure_data_directory()
        self.ensure_config_file()
    
    def ensure_data_directory(self):
        """데이터 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def ensure_config_file(self):
        """설정 파일이 존재하는지 확인하고 없으면 기본값으로 생성합니다."""
        if not os.path.exists(self.config_file):
            default_config = {
                "system_name": "금도((金道)) Geumdo [ Golden Way ]",
                "system_symbol": "📊",
                "company_name": "YUMOLD VIETNAM",
                "company_logo": "🏭",
                "theme_color": "#1976d2",
                "last_updated": datetime.now().isoformat(),
                "updated_by": "system"
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    def get_system_config(self):
        """시스템 설정을 가져옵니다."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 파일 읽기 오류: {e}")
            return {
                "system_name": "금도((金道)) Geumdo [ Golden Way ]",
                "system_symbol": "📊",
                "company_name": "YUMOLD VIETNAM",
                "company_logo": "🏭",
                "theme_color": "#1976d2"
            }
    
    def update_system_config(self, config_data, updated_by="admin"):
        """시스템 설정을 업데이트합니다."""
        try:
            current_config = self.get_system_config()
            current_config.update(config_data)
            current_config["last_updated"] = datetime.now().isoformat()
            current_config["updated_by"] = updated_by
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"설정 업데이트 오류: {e}")
            return False
    
    def get_system_title(self):
        """시스템 제목을 가져옵니다."""
        config = self.get_system_config()
        return f"{config.get('system_symbol', '📊')} {config.get('system_name', '금도((金道)) Geumdo [ Golden Way ]')}"
    
    def get_company_info(self):
        """회사 정보를 가져옵니다."""
        config = self.get_system_config()
        return {
            "name": config.get('company_name', 'YUMOLD VIETNAM'),
            "logo": config.get('company_logo', '🏭')
        }
    
    def reset_to_default(self):
        """설정을 기본값으로 초기화합니다."""
        default_config = {
            "system_name": "금도((金道)) Geumdo [ Golden Way ]",
            "system_symbol": "📊",
            "company_name": "YUMOLD VIETNAM", 
            "company_logo": "🏭",
            "theme_color": "#1976d2",
            "last_updated": datetime.now().isoformat(),
            "updated_by": "system"
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"설정 초기화 오류: {e}")
            return False
    
    def get_config_history(self):
        """설정 변경 이력을 가져옵니다."""
        config = self.get_system_config()
        return {
            "last_updated": config.get('last_updated', 'Unknown'),
            "updated_by": config.get('updated_by', 'Unknown')
        }