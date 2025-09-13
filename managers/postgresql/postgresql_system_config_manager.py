# -*- coding: utf-8 -*-
"""
PostgreSQL SystemConfig 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLSystemConfigManager(BasePostgreSQLManager):
    """PostgreSQL SystemConfig 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """SystemConfig 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 시스템 설정 테이블 (SQLite와 호환)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_configs (
                        id SERIAL PRIMARY KEY,
                        config_id VARCHAR(50) UNIQUE NOT NULL,
                        config_key VARCHAR(100) UNIQUE NOT NULL,
                        config_value TEXT,
                        config_type VARCHAR(20) DEFAULT 'string',
                        category VARCHAR(50) DEFAULT 'general',
                        description TEXT,
                        description_en TEXT,
                        description_vi TEXT,
                        is_required INTEGER DEFAULT 0,
                        is_encrypted INTEGER DEFAULT 0,
                        is_public INTEGER DEFAULT 1,
                        default_value TEXT,
                        validation_rules TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by VARCHAR(100)
                    )
                """)
                
                # 설정 변경 히스토리 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_config_history (
                        id SERIAL PRIMARY KEY,
                        history_id VARCHAR(50) UNIQUE NOT NULL,
                        config_key VARCHAR(100) NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        change_reason TEXT,
                        changed_by VARCHAR(100),
                        changed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log_info("SystemConfig 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"SystemConfig 테이블 초기화 실패: {e}")
    
    def get_config_value(self, config_key, default_value=None):
        """특정 설정값 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_value, config_type FROM system_configs WHERE config_key = %s", [config_key])
                result = cursor.fetchone()
                
                if result:
                    value, config_type = result
                    # 타입에 따른 변환
                    if config_type == 'boolean':
                        return str(value).lower() in ('true', '1', 'yes', 'on') if value else False
                    elif config_type == 'integer':
                        return int(value) if value else 0
                    elif config_type == 'decimal':
                        return float(value) if value else 0.0
                    elif config_type == 'json':
                        import json
                        return json.loads(value) if value else {}
                    elif config_type == 'list':
                        return [item.strip() for item in str(value).split(',') if item.strip()] if value else []
                    else:
                        return value if value is not None else default_value
                else:
                    return default_value
                    
        except Exception as e:
            self.log_error(f"설정값 조회 실패: {e}")
            return default_value
    
    def set_config_value(self, config_key, config_value, updated_by='', change_reason=''):
        """설정값 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 값 조회 (히스토리용)
                cursor.execute("SELECT config_value FROM system_configs WHERE config_key = %s", [config_key])
                old_result = cursor.fetchone()
                old_value = old_result[0] if old_result else None
                
                # 설정값 업데이트
                cursor.execute("""
                    INSERT INTO system_configs (config_id, config_key, config_value, updated_by, updated_date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (config_key) 
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        updated_by = EXCLUDED.updated_by,
                        updated_date = EXCLUDED.updated_date
                """, [f"config_{config_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}", config_key, str(config_value), updated_by, datetime.now()])
                
                # 히스토리 기록
                if change_reason or old_value != str(config_value):
                    import uuid
                    history_id = f"hist_{uuid.uuid4().hex[:8]}"
                    cursor.execute("""
                        INSERT INTO system_config_history 
                        (history_id, config_key, old_value, new_value, change_reason, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [history_id, config_key, old_value, str(config_value), change_reason, updated_by])
                
                conn.commit()
                return True, "설정값이 업데이트되었습니다."
                
        except Exception as e:
            self.log_error(f"설정값 업데이트 실패: {e}")
            return False, f"설정값 업데이트 실패: {e}"
    
    def get_configs(self, category=None, is_public=None) -> 'pd.DataFrame':
        """조건에 따른 설정을 DataFrame으로 조회"""
        try:
            import pandas as pd
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM system_configs WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                if is_public is not None:
                    query += " AND is_public = %s"
                    params.append(1 if is_public else 0)
                
                query += " ORDER BY category, config_key"
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                configs = []
                
                for row in cursor.fetchall():
                    config = dict(zip(columns, row))
                    configs.append(config)
                
                if configs:
                    return pd.DataFrame(configs)
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"설정 조회 실패: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_all_items(self) -> 'pd.DataFrame':
        """모든 항목을 DataFrame으로 조회 (get_configs 호출)"""
        return self.get_configs()
    
    def add_config(self, config_data):
        """새 설정 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                config_id = config_data.get('config_id', f"config_{config_data.get('config_key', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                cursor.execute("""
                    INSERT INTO system_configs (
                        config_id, config_key, config_value, config_type, category,
                        description, description_en, description_vi,
                        is_required, is_encrypted, is_public, default_value,
                        validation_rules, updated_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    config_id,
                    config_data.get('config_key'),
                    config_data.get('config_value', ''),
                    config_data.get('config_type', 'string'),
                    config_data.get('category', 'general'),
                    config_data.get('description', ''),
                    config_data.get('description_en', ''),
                    config_data.get('description_vi', ''),
                    1 if config_data.get('is_required', False) else 0,
                    1 if config_data.get('is_encrypted', False) else 0,
                    1 if config_data.get('is_public', True) else 0,
                    config_data.get('default_value', ''),
                    config_data.get('validation_rules', ''),
                    config_data.get('updated_by', '')
                ])
                
                conn.commit()
                return True, "설정이 추가되었습니다."
                
        except Exception as e:
            self.log_error(f"설정 추가 실패: {e}")
            return False, f"설정 추가 실패: {e}"
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM system_configs")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
