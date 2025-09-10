"""
SQLite 시스템 설정 관리자 - 시스템 전체 설정 관리
CSV 기반에서 SQLite 기반으로 전환
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteSystemConfigManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 시스템 설정 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_configs (
                        config_id TEXT PRIMARY KEY,
                        config_key TEXT UNIQUE NOT NULL,
                        config_value TEXT,
                        config_type TEXT DEFAULT 'string',
                        category TEXT DEFAULT 'general',
                        description TEXT,
                        description_en TEXT,
                        description_vi TEXT,
                        is_required INTEGER DEFAULT 0,
                        is_encrypted INTEGER DEFAULT 0,
                        is_public INTEGER DEFAULT 1,
                        default_value TEXT,
                        validation_rules TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_by TEXT
                    )
                ''')
                
                # 설정 변경 히스토리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_history (
                        history_id TEXT PRIMARY KEY,
                        config_key TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        changed_by TEXT,
                        change_reason TEXT,
                        change_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 기본 시스템 설정 추가
                default_configs = [
                    ('company_name', '회사명', 'HanaRo International', 'string', 'company', '회사 이름', 'Company Name', 'Tên công ty', 1, 0, 1),
                    ('company_address', '회사주소', '베트남 호치민시', 'string', 'company', '회사 주소', 'Company Address', 'Địa chỉ công ty', 1, 0, 1),
                    ('company_phone', '회사전화', '+84-xxx-xxx-xxx', 'string', 'company', '회사 전화번호', 'Company Phone', 'Điện thoại công ty', 1, 0, 1),
                    ('company_email', '회사이메일', 'info@hanaro.com', 'email', 'company', '회사 이메일', 'Company Email', 'Email công ty', 1, 0, 1),
                    ('default_currency', '기본통화', 'VND', 'string', 'financial', '기본 통화', 'Default Currency', 'Tiền tệ mặc định', 1, 0, 1),
                    ('tax_rate', '세율', '10', 'decimal', 'financial', '기본 세율 (%)', 'Default Tax Rate (%)', 'Thuế suất mặc định (%)', 1, 0, 1),
                    ('decimal_places', '소수점자리', '2', 'integer', 'financial', '금액 소수점 자리수', 'Amount Decimal Places', 'Số chữ số thập phân', 1, 0, 1),
                    ('date_format', '날짜형식', 'YYYY-MM-DD', 'string', 'system', '날짜 표시 형식', 'Date Format', 'Định dạng ngày', 1, 0, 1),
                    ('timezone', '시간대', 'Asia/Ho_Chi_Minh', 'string', 'system', '시스템 시간대', 'System Timezone', 'Múi giờ hệ thống', 1, 0, 1),
                    ('default_language', '기본언어', 'ko', 'string', 'system', '기본 언어', 'Default Language', 'Ngôn ngữ mặc định', 1, 0, 1),
                    ('items_per_page', '페이지당항목수', '20', 'integer', 'ui', '페이지당 표시 항목 수', 'Items Per Page', 'Số mục mỗi trang', 1, 0, 1),
                    ('session_timeout', '세션타임아웃', '3600', 'integer', 'security', '세션 만료 시간 (초)', 'Session Timeout (seconds)', 'Thời gian hết phiên (giây)', 1, 0, 0),
                    # 제품 카테고리 설정
                    ('product_categories', '제품카테고리', 'HR,HRC,MB,SERVICE,SPARE,ROBOT', 'list', 'product', '제품 메인 카테고리', 'Product Main Categories', 'Danh mục sản phẩm chính', 1, 0, 1),
                    ('hr_subcategories', 'HR서브카테고리', 'Valve,Open,Nozzle,Tip,Insert', 'list', 'product', 'HR 서브 카테고리', 'HR Sub Categories', 'Danh mục phụ HR', 1, 0, 1),
                    ('hrc_system_types', 'HRC시스템타입', '8,10,12,15,20', 'list', 'product', 'HRC 시스템 타입', 'HRC System Types', 'Loại hệ thống HRC', 1, 0, 1),
                    ('hrc_product_types', 'HRC제품타입', '100,200,300,400,500', 'list', 'product', 'HRC 제품 타입', 'HRC Product Types', 'Loại sản phẩm HRC', 1, 0, 1),
                    ('mb_materials', 'MB재질', 'P20,718,SKD61,NAK80,2738,2343,H13', 'list', 'product', 'MB 재질 종류', 'MB Materials', 'Vật liệu MB', 1, 0, 1),
                    ('service_types', '서비스타입', 'Machining,Assembly,Repair,Consulting', 'list', 'product', '서비스 타입', 'Service Types', 'Loại dịch vụ', 1, 0, 1),
                    ('spare_types', '부품타입', 'Heater,Sensor,Thermocouple,Cable,Connector', 'list', 'product', '부품 타입', 'Spare Types', 'Loại phụ tùng', 1, 0, 1),
                    ('backup_frequency', '백업빈도', 'daily', 'string', 'system', '백업 주기', 'Backup Frequency', 'Tần suất sao lưu', 1, 0, 0),
                    ('max_file_size', '최대파일크기', '10485760', 'integer', 'system', '최대 업로드 파일 크기 (bytes)', 'Max Upload File Size (bytes)', 'Kích thước tệp tải lên tối đa (bytes)', 1, 0, 1),
                    ('enable_notifications', '알림활성화', 'true', 'boolean', 'system', '시스템 알림 활성화', 'Enable System Notifications', 'Bật thông báo hệ thống', 1, 0, 1)
                ]
                
                for config in default_configs:
                    config_id = f"CONFIG_{config[0].upper()}"
                    cursor.execute('''
                        INSERT OR IGNORE INTO system_configs 
                        (config_id, config_key, config_value, config_type, category, 
                         description, description_en, description_vi, is_required, is_encrypted, is_public)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (config_id, config[0], config[2], config[3], config[4], 
                          config[5], config[6], config[7], config[8], config[9], config[10]))
                
                conn.commit()
                logger.info("시스템 설정 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_configs(self, category=None, is_public=None):
        """시스템 설정 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM system_configs WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                if is_public is not None:
                    query += " AND is_public = ?"
                    params.append(1 if is_public else 0)
                
                query += " ORDER BY category, config_key"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"시스템 설정 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_config_value(self, config_key, default_value=None):
        """특정 설정값 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_value, config_type FROM system_configs WHERE config_key = ?", (config_key,))
                result = cursor.fetchone()
                
                if result:
                    value, config_type = result
                    # 타입에 따른 변환
                    if config_type == 'boolean':
                        return value.lower() in ('true', '1', 'yes', 'on')
                    elif config_type == 'integer':
                        return int(value) if value else 0
                    elif config_type == 'decimal':
                        return float(value) if value else 0.0
                    elif config_type == 'json':
                        return json.loads(value) if value else {}
                    elif config_type == 'list':
                        return [item.strip() for item in value.split(',') if item.strip()] if value else []
                    else:  # string, email, etc.
                        return value
                else:
                    return default_value
                
        except Exception as e:
            logger.error(f"설정값 조회 실패: {str(e)}")
            return default_value

    def set_config_value(self, config_key, config_value, updated_by='', change_reason=''):
        """설정값 변경"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 값 조회
                cursor.execute("SELECT config_value FROM system_configs WHERE config_key = ?", (config_key,))
                result = cursor.fetchone()
                old_value = result[0] if result else None
                
                current_time = datetime.now().isoformat()
                
                if old_value is not None:
                    # 기존 설정 업데이트
                    cursor.execute('''
                        UPDATE system_configs 
                        SET config_value = ?, updated_date = ?, updated_by = ?
                        WHERE config_key = ?
                    ''', (str(config_value), current_time, updated_by, config_key))
                else:
                    # 새 설정 추가
                    config_id = f"CONFIG_{config_key.upper()}"
                    cursor.execute('''
                        INSERT INTO system_configs 
                        (config_id, config_key, config_value, created_date, updated_date, updated_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (config_id, config_key, str(config_value), current_time, current_time, updated_by))
                
                # 변경 히스토리 추가
                history_id = f"HIST_{datetime.now().strftime('%Y%m%d%H%M%S')}_{config_key}"
                cursor.execute('''
                    INSERT INTO config_history 
                    (history_id, config_key, old_value, new_value, changed_by, change_reason, change_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (history_id, config_key, old_value, str(config_value), updated_by, change_reason, current_time))
                
                conn.commit()
                logger.info(f"설정값 변경 완료: {config_key} = {config_value}")
                return True
                
        except Exception as e:
            logger.error(f"설정값 변경 실패: {str(e)}")
            return False
    
    def get_product_categories(self):
        """제품 메인 카테고리 목록을 반환"""
        return self.get_config_value('product_categories', [])
    
    def get_hr_subcategories(self):
        """HR 서브 카테고리 목록을 반환"""
        return self.get_config_value('hr_subcategories', [])
    
    def get_hrc_system_types(self):
        """HRC 시스템 타입 목록을 반환"""
        return self.get_config_value('hrc_system_types', [])
    
    def get_hrc_product_types(self):
        """HRC 제품 타입 목록을 반환"""
        return self.get_config_value('hrc_product_types', [])
    
    def get_mb_materials(self):
        """MB 재질 목록을 반환"""
        return self.get_config_value('mb_materials', [])
    
    def get_service_types(self):
        """서비스 타입 목록을 반환"""
        return self.get_config_value('service_types', [])
    
    def get_spare_types(self):
        """부품 타입 목록을 반환"""
        return self.get_config_value('spare_types', [])
    
    def update_product_categories(self, categories, updated_by=''):
        """제품 메인 카테고리 업데이트"""
        if isinstance(categories, list):
            categories = ','.join(categories)
        return self.set_config_value('product_categories', categories, updated_by, '제품 카테고리 업데이트')
    
    def update_hr_subcategories(self, subcategories, updated_by=''):
        """HR 서브 카테고리 업데이트"""
        if isinstance(subcategories, list):
            subcategories = ','.join(subcategories)
        return self.set_config_value('hr_subcategories', subcategories, updated_by, 'HR 서브 카테고리 업데이트')

    def add_config(self, config_data):
        """새 설정 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['config_key']
                for field in required_fields:
                    if field not in config_data or not config_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                config_id = f"CONFIG_{config_data['config_key'].upper()}"
                
                config_record = {
                    'config_id': config_id,
                    'config_key': config_data['config_key'],
                    'config_value': config_data.get('config_value', ''),
                    'config_type': config_data.get('config_type', 'string'),
                    'category': config_data.get('category', 'general'),
                    'description': config_data.get('description', ''),
                    'description_en': config_data.get('description_en', ''),
                    'description_vi': config_data.get('description_vi', ''),
                    'is_required': config_data.get('is_required', 0),
                    'is_encrypted': config_data.get('is_encrypted', 0),
                    'is_public': config_data.get('is_public', 1),
                    'default_value': config_data.get('default_value', ''),
                    'validation_rules': config_data.get('validation_rules', ''),
                    'created_date': current_time,
                    'updated_date': current_time,
                    'updated_by': config_data.get('created_by', '')
                }
                
                cursor.execute('''
                    INSERT INTO system_configs (
                        config_id, config_key, config_value, config_type, category,
                        description, description_en, description_vi, is_required, is_encrypted,
                        is_public, default_value, validation_rules, created_date, updated_date, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(config_record.values()))
                
                conn.commit()
                logger.info(f"시스템 설정 추가 완료: {config_data['config_key']}")
                return True
                
        except Exception as e:
            logger.error(f"시스템 설정 추가 실패: {str(e)}")
            return False

    def get_config_history(self, config_key=None, limit=50):
        """설정 변경 히스토리 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM config_history WHERE 1=1"
                params = []
                
                if config_key:
                    query += " AND config_key = ?"
                    params.append(config_key)
                
                query += " ORDER BY change_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"설정 변경 히스토리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_categories(self):
        """설정 카테고리 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        category,
                        COUNT(*) as config_count
                    FROM system_configs 
                    GROUP BY category 
                    ORDER BY category
                '''
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"설정 카테고리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def backup_configs(self):
        """설정 백업"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM system_configs", conn)
                
                backup_file = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = os.path.join("backups", backup_file)
                
                os.makedirs("backups", exist_ok=True)
                
                # JSON 형태로 백업
                configs_dict = {}
                for _, row in df.iterrows():
                    configs_dict[row['config_key']] = {
                        'value': row['config_value'],
                        'type': row['config_type'],
                        'category': row['category'],
                        'description': row['description']
                    }
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(configs_dict, f, ensure_ascii=False, indent=2)
                
                logger.info(f"설정 백업 완료: {backup_path}")
                return backup_path
                
        except Exception as e:
            logger.error(f"설정 백업 실패: {str(e)}")
            return None

    def restore_configs(self, backup_path):
        """설정 복원"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"백업 파일 없음: {backup_path}")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                configs_dict = json.load(f)
            
            restored_count = 0
            for config_key, config_info in configs_dict.items():
                success = self.set_config_value(
                    config_key, 
                    config_info['value'], 
                    'system', 
                    f'백업에서 복원: {backup_path}'
                )
                if success:
                    restored_count += 1
            
            logger.info(f"설정 복원 완료: {restored_count}개 설정")
            return True
            
        except Exception as e:
            logger.error(f"설정 복원 실패: {str(e)}")
            return False

    def migrate_from_csv(self, configs_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            if configs_csv_path is None:
                configs_csv_path = os.path.join("data", "system_configs.csv")
            
            if os.path.exists(configs_csv_path):
                df = pd.read_csv(configs_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        config_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in config_data.items():
                            if pd.isna(value):
                                if key in ['is_required', 'is_encrypted', 'is_public']:
                                    config_data[key] = 0 if key in ['is_required', 'is_encrypted'] else 1
                                else:
                                    config_data[key] = ''
                        
                        self.add_config(config_data)
                    
                    logger.info(f"시스템 설정 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False