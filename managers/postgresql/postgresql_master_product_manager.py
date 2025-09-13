# -*- coding: utf-8 -*-
"""
PostgreSQL MasterProduct 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid

class PostgreSQLMasterProductManager(BasePostgreSQLManager):
    """PostgreSQL MasterProduct 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """MasterProduct 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기본 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS master_products (
                        id SERIAL PRIMARY KEY,
                        item_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(200),
                        status VARCHAR(20) DEFAULT 'active',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 추가 컬럼들을 안전하게 추가 (이미 존재하면 무시)
                try:
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS product_code VARCHAR(100) UNIQUE")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS product_name_en VARCHAR(500)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS product_name_vi VARCHAR(500)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS supplier_name VARCHAR(300)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS category_name VARCHAR(200)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS unit VARCHAR(50)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS supply_currency VARCHAR(10)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS supply_price DECIMAL(15,2)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS exchange_rate DECIMAL(15,4)")
                    cursor.execute("ALTER TABLE master_products ADD COLUMN IF NOT EXISTS sales_price_vnd DECIMAL(15,2)")
                except Exception as e:
                    # 컬럼이 이미 존재하거나 다른 오류가 발생해도 계속 진행
                    self.log_info(f"컬럼 추가 중 정보: {e}")
                
                # 인덱스 생성
                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_master_products_code ON master_products(product_code)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_master_products_supplier ON master_products(supplier_name)")
                except Exception as e:
                    self.log_info(f"인덱스 생성 중 정보: {e}")
                
                # HR 제품 코드 구성 요소 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hr_product_components (
                        component_id VARCHAR(50) PRIMARY KEY,
                        component_type VARCHAR(50) NOT NULL,
                        parent_component VARCHAR(100),
                        component_key VARCHAR(50) NOT NULL,
                        component_name VARCHAR(200) NOT NULL,
                        component_name_en VARCHAR(200),
                        component_name_vi VARCHAR(200),
                        display_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT true,
                        description TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(50)
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hr_components_type 
                    ON hr_product_components(component_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hr_components_parent 
                    ON hr_product_components(parent_component)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hr_components_key 
                    ON hr_product_components(component_key)
                """)
                
                # 초기 데이터 체크 및 삽입
                cursor.execute("SELECT COUNT(*) FROM hr_product_components")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    self._insert_initial_hr_components(cursor)
                
                self.log_info("MasterProduct 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"MasterProduct 테이블 초기화 실패: {e}")
    
    def _insert_initial_hr_components(self, cursor):
        """초기 HR 컴포넌트 데이터 삽입"""
        try:
            # System Types
            system_types = [
                ('HR_ST_001', 'system_type', None, 'Valve', 'Valve', 'Valve', 'Van', 1, True, '밸브형 핫러너'),
                ('HR_ST_002', 'system_type', None, 'Open', 'Open', 'Open', 'Mở', 2, True, '오픈형 핫러너'),
                ('HR_ST_003', 'system_type', None, 'Robot', 'Robot', 'Robot', 'Robot', 3, True, '로봇 시스템'),
            ]
            
            # Product Types for Valve
            product_types_valve = [
                ('HR_PT_V001', 'product_type', 'Valve', 'ST', 'Standard', 'Standard', 'Tiêu chuẩn', 1, True, 'Valve 표준형'),
                ('HR_PT_V002', 'product_type', 'Valve', 'CP', 'Cosmetic & Packaging', 'Cosmetic & Packaging', 'Mỹ phẩm & Bao bì', 2, True, 'Valve 화장품/포장용'),
                ('HR_PT_V003', 'product_type', 'Valve', 'PET', 'PET', 'PET', 'PET', 3, True, 'Valve PET용'),
                ('HR_PT_V004', 'product_type', 'Valve', 'SE', 'Super Engineering', 'Super Engineering', 'Siêu kỹ thuật', 4, True, 'Valve 수퍼엔지니어링용'),
                ('HR_PT_V005', 'product_type', 'Valve', 'SIV', 'Single Valve', 'Single Valve', 'Van đơn', 5, True, 'Valve 단일형'),
            ]
            
            # Product Types for Open
            product_types_open = [
                ('HR_PT_O001', 'product_type', 'Open', 'ST', 'Standard', 'Standard', 'Tiêu chuẩn', 1, True, 'Open 표준형'),
                ('HR_PT_O002', 'product_type', 'Open', 'CP', 'Cosmetic & Packaging', 'Cosmetic & Packaging', 'Mỹ phẩm & Bao bì', 2, True, 'Open 화장품/포장용'),
                ('HR_PT_O003', 'product_type', 'Open', 'SIO', 'Single Open', 'Single Open', 'Mở đơn', 3, True, 'Open 단일형'),
            ]
            
            # Gate Types for Valve-ST
            gate_types_valve_st = [
                ('HR_GT_VST001', 'gate_type', 'Valve-ST', 'MAE', 'MAE', 'MAE', 'MAE', 1, True, 'Valve ST MAE 게이트'),
                ('HR_GT_VST002', 'gate_type', 'Valve-ST', 'MCC', 'MCC', 'MCC', 'MCC', 2, True, 'Valve ST MCC 게이트'),
                ('HR_GT_VST003', 'gate_type', 'Valve-ST', 'MAA', 'MAA', 'MAA', 'MAA', 3, True, 'Valve ST MAA 게이트'),
            ]
            
            # Gate Types for Open-ST
            gate_types_open_st = [
                ('HR_GT_OST001', 'gate_type', 'Open-ST', 'MCC', 'MCC', 'MCC', 'MCC', 1, True, 'Open ST MCC 게이트'),
                ('HR_GT_OST002', 'gate_type', 'Open-ST', 'MEA', 'MEA', 'MEA', 'MEA', 2, True, 'Open ST MEA 게이트'),
            ]
            
            # Sizes for Valve-ST-MAE
            sizes_valve_st = [
                ('HR_SZ_VSTMAE001', 'size', 'Valve-ST-MAE', '20', '20', '20', '20', 1, True, 'Valve ST MAE 20 사이즈'),
                ('HR_SZ_VSTMAE002', 'size', 'Valve-ST-MAE', '25', '25', '25', '25', 2, True, 'Valve ST MAE 25 사이즈'),
                ('HR_SZ_VSTMAE003', 'size', 'Valve-ST-MAE', '35', '35', '35', '35', 3, True, 'Valve ST MAE 35 사이즈'),
                ('HR_SZ_VSTMAE004', 'size', 'Valve-ST-MAE', '45', '45', '45', '45', 4, True, 'Valve ST MAE 45 사이즈'),
            ]
            
            # Level 5 components for Valve-ST-MAE-20
            level5_components = [
                ('HR_L5_VSTMAE20001', 'level5', 'Valve-ST-MAE-20', 'A', 'Type A', 'Type A', 'Type A', 1, True, 'Level 5 Type A'),
                ('HR_L5_VSTMAE20002', 'level5', 'Valve-ST-MAE-20', 'B', 'Type B', 'Type B', 'Type B', 2, True, 'Level 5 Type B'),
                ('HR_L5_VSTMAE20003', 'level5', 'Valve-ST-MAE-20', 'C', 'Type C', 'Type C', 'Type C', 3, True, 'Level 5 Type C'),
            ]
            
            # Level 6 components for Valve-ST-MAE-20-A
            level6_components = [
                ('HR_L6_VSTMAE20A001', 'level6', 'Valve-ST-MAE-20-A', '01', 'Standard', 'Standard', 'Standard', 1, True, 'Level 6 Standard'),
                ('HR_L6_VSTMAE20A002', 'level6', 'Valve-ST-MAE-20-A', '02', 'Premium', 'Premium', 'Premium', 2, True, 'Level 6 Premium'),
                ('HR_L6_VSTMAE20A003', 'level6', 'Valve-ST-MAE-20-A', '03', 'Special', 'Special', 'Special', 3, True, 'Level 6 Special'),
            ]
            
            # 모든 컴포넌트 데이터 삽입
            all_components = (system_types + product_types_valve + product_types_open + 
                            gate_types_valve_st + gate_types_open_st + sizes_valve_st + 
                            level5_components + level6_components)
            
            for component in all_components:
                cursor.execute("""
                    INSERT INTO hr_product_components 
                    (component_id, component_type, parent_component, component_key, 
                     component_name, component_name_en, component_name_vi, display_order, 
                     is_active, description, created_date, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'system')
                """, component)
            
            self.log_info(f"초기 HR 컴포넌트 데이터 {len(all_components)}개 삽입 완료")
            
        except Exception as e:
            self.log_error(f"초기 HR 컴포넌트 데이터 삽입 실패: {e}")
    
    def get_all_items(self) -> 'pd.DataFrame':
        """모든 항목을 DataFrame으로 조회"""
        try:
            import pandas as pd
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # item_id를 master_product_id로 별칭 처리하여 호환성 확보
                cursor.execute("""
                    SELECT *, id AS master_product_id 
                    FROM master_products 
                    ORDER BY created_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                if items:
                    return pd.DataFrame(items)
                else:
                    return pd.DataFrame()
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_master_products(self) -> 'pd.DataFrame':
        """마스터 제품 목록 조회 (SQLite 호환)"""
        return self.get_all_items()
    
    def get_all_products(self) -> 'pd.DataFrame':
        """모든 제품 조회 (호환성을 위한 별칭)"""
        return self.get_all_items()
    
    def get_products_dataframe(self) -> 'pd.DataFrame':
        """제품 DataFrame 조회 (호환성을 위한 별칭)"""
        return self.get_all_items()
    
    def get_statistics(self):
        """통계 조회"""
        try:
            query = "SELECT COUNT(*) as total_count FROM master_products"
            result = self.execute_query(query, fetch_one=True)
            
            return {'total_count': result['total_count'] if result else 0}
            
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
    
    def get_hr_components_for_management(self, component_type):
        """HR 컴포넌트 관리용 목록 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 지정된 컴포넌트 타입의 데이터 조회
                query = """
                    SELECT component_id, component_type, parent_component, component_key, 
                           component_name, component_name_en, component_name_vi,
                           display_order, is_active, description, created_date, updated_date
                    FROM hr_product_components 
                    WHERE component_type = %s 
                    ORDER BY display_order, component_key
                """
                
                cursor.execute(query, (component_type,))
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    component = dict(zip(columns, row))
                    results.append(component)
                
                self.log_info(f"HR 컴포넌트 조회 완료: {component_type} - {len(results)}개")
                return results
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 조회 실패 ({component_type}): {e}")
            return []
    
    def get_hr_component_by_key(self, component_key):
        """특정 컴포넌트 키로 HR 컴포넌트 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT component_id, component_type, parent_component, component_key, 
                           component_name, component_name_en, component_name_vi,
                           display_order, is_active, description, created_date, updated_date
                    FROM hr_product_components 
                    WHERE component_key = %s AND is_active = true
                """
                
                cursor.execute(query, (component_key,))
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                
                if row:
                    return dict(zip(columns, row))
                else:
                    return None
                    
        except Exception as e:
            self.log_error(f"HR 컴포넌트 개별 조회 실패 ({component_key}): {e}")
            return None
    
    def add_hr_component(self, component_data):
        """HR 컴포넌트 추가"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 컴포넌트 ID 생성
                component_id = f"HR_{component_data['component_type'].upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                query = """
                    INSERT INTO hr_product_components 
                    (component_id, component_type, parent_component, component_key,
                     component_name, component_name_en, component_name_vi, 
                     display_order, is_active, description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    component_id,
                    component_data.get('component_type'),
                    component_data.get('parent_component'),
                    component_data.get('component_key'),
                    component_data.get('component_name'),
                    component_data.get('component_name_en', ''),
                    component_data.get('component_name_vi', ''),
                    component_data.get('display_order', 0),
                    component_data.get('is_active', True),
                    component_data.get('description', ''),
                    'system'
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 추가 완료: {component_data['component_key']}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 추가 실패: {e}")
            return False
    
    def update_hr_component(self, component_key, component_data):
        """HR 컴포넌트 수정"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    UPDATE hr_product_components 
                    SET component_name = %s, component_name_en = %s, component_name_vi = %s,
                        display_order = %s, is_active = %s, description = %s, 
                        updated_date = CURRENT_TIMESTAMP
                    WHERE component_key = %s
                """
                
                values = (
                    component_data.get('component_name'),
                    component_data.get('component_name_en', ''),
                    component_data.get('component_name_vi', ''),
                    component_data.get('display_order', 0),
                    component_data.get('is_active', True),
                    component_data.get('description', ''),
                    component_key
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 수정 완료: {component_key}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 수정 실패: {e}")
            return False
    
    def deactivate_hr_component(self, component_key):
        """HR 컴포넌트 비활성화 (삭제 대신)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    UPDATE hr_product_components 
                    SET is_active = false, updated_date = CURRENT_TIMESTAMP
                    WHERE component_key = %s
                """
                
                cursor.execute(query, (component_key,))
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 비활성화 완료: {component_key}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 비활성화 실패: {e}")
            return False
    
    def delete_hr_component_permanently(self, component_id):
        """HR 컴포넌트 영구 삭제"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "DELETE FROM hr_product_components WHERE component_id = %s"
                cursor.execute(query, (component_id,))
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 영구 삭제 완료: {component_id}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 영구 삭제 실패: {e}")
            return False
    
    def add_hr_component_with_params(self, component_type, parent_component, component_key, component_name, component_name_en=None, component_name_vi=None, description=None):
        """HR 컴포넌트 추가 (시스템 설정 페이지 호환)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 컴포넌트 ID 생성
                component_id = f"HR_{component_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                query = """
                    INSERT INTO hr_product_components 
                    (component_id, component_type, parent_component, component_key,
                     component_name, component_name_en, component_name_vi, 
                     display_order, is_active, description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    component_id,
                    component_type,
                    parent_component,
                    component_key,
                    component_name,
                    component_name_en or '',
                    component_name_vi or '',
                    0,  # display_order
                    True,  # is_active
                    description or '',
                    'system'
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 추가 완료: {component_key}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 추가 실패 (호환 메서드): {e}")
            return False
    
    # 시스템 설정 페이지 호환성을 위한 별칭 메서드
    def add_hr_component(self, *args, **kwargs):
        """HR 컴포넌트 추가 (overloaded method)"""
        # 첫 번째 인자가 딕셔너리인 경우 (원래 메서드)
        if len(args) == 1 and isinstance(args[0], dict):
            return self._add_hr_component_with_dict(args[0])
        # 여러 인자인 경우 (호환 메서드)
        else:
            return self.add_hr_component_with_params(*args, **kwargs)
    
    def _add_hr_component_with_dict(self, component_data):
        """원래 add_hr_component 메서드 (딕셔너리 버전)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 컴포넌트 ID 생성
                component_id = f"HR_{component_data['component_type'].upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                query = """
                    INSERT INTO hr_product_components 
                    (component_id, component_type, parent_component, component_key,
                     component_name, component_name_en, component_name_vi, 
                     display_order, is_active, description, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    component_id,
                    component_data.get('component_type'),
                    component_data.get('parent_component'),
                    component_data.get('component_key'),
                    component_data.get('component_name'),
                    component_data.get('component_name_en', ''),
                    component_data.get('component_name_vi', ''),
                    component_data.get('display_order', 0),
                    component_data.get('is_active', True),
                    component_data.get('description', ''),
                    'system'
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 추가 완료: {component_data['component_key']}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 추가 실패: {e}")
            return False
    
    def update_hr_component(self, component_id, component_key=None, component_name=None, description=None, **kwargs):
        """HR 컴포넌트 업데이트 (시스템 설정 페이지 호환)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 현재 컴포넌트 정보 조회
                cursor.execute("SELECT * FROM hr_product_components WHERE component_id = %s", (component_id,))
                current = cursor.fetchone()
                
                if not current:
                    self.log_error(f"업데이트할 컴포넌트가 없습니다: {component_id}")
                    return False
                
                # 업데이트 쿼리 구성
                update_parts = []
                values = []
                
                if component_key is not None:
                    update_parts.append("component_key = %s")
                    values.append(component_key)
                
                if component_name is not None:
                    update_parts.append("component_name = %s")
                    values.append(component_name)
                
                if description is not None:
                    update_parts.append("description = %s")
                    values.append(description)
                
                # 추가 필드들 처리
                for key, value in kwargs.items():
                    if key in ['component_name_en', 'component_name_vi', 'display_order', 'is_active']:
                        update_parts.append(f"{key} = %s")
                        values.append(value)
                
                update_parts.append("updated_date = CURRENT_TIMESTAMP")
                values.append(component_id)
                
                query = f"UPDATE hr_product_components SET {', '.join(update_parts)} WHERE component_id = %s"
                cursor.execute(query, values)
                conn.commit()
                
                self.log_info(f"HR 컴포넌트 업데이트 완료: {component_id}")
                return True
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 업데이트 실패: {e}")
            return False
    
    def get_hr_system_types(self):
        """HR 시스템 타입 목록 조회 (키만 반환)"""
        try:
            components = self.get_hr_components_for_management('system_type')
            active_components = [comp for comp in components if comp.get('is_active', True)]
            return [comp['component_key'] for comp in active_components]
            
        except Exception as e:
            self.log_error(f"HR 시스템 타입 목록 조회 실패: {e}")
            return []
    
    def get_hr_product_types(self, system_type):
        """특정 시스템 타입의 제품 타입 목록 조회"""
        try:
            components = self.get_hr_components_for_management('product_type')
            filtered_components = [
                comp for comp in components 
                if comp.get('parent_component') == system_type and comp.get('is_active', True)
            ]
            return [comp['component_key'] for comp in filtered_components]
            
        except Exception as e:
            self.log_error(f"HR 제품 타입 목록 조회 실패 ({system_type}): {e}")
            return []
    
    def get_hr_components_by_parent(self, component_type, parent_component):
        """부모 컴포넌트로 필터링된 HR 컴포넌트 목록 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT component_id, component_type, parent_component, component_key, 
                           component_name, component_name_en, component_name_vi,
                           display_order, is_active, description, created_date, updated_date
                    FROM hr_product_components 
                    WHERE component_type = %s AND parent_component = %s AND is_active = true
                    ORDER BY display_order, component_key
                """
                
                cursor.execute(query, (component_type, parent_component))
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    component = dict(zip(columns, row))
                    results.append(component)
                
                return results
                
        except Exception as e:
            self.log_error(f"부모별 HR 컴포넌트 조회 실패 ({component_type}, {parent_component}): {e}")
            return []
    
    def get_hr_component_count(self, component_type, active_only=True):
        """HR 컴포넌트 타입별 개수 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if active_only:
                    query = "SELECT COUNT(*) FROM hr_product_components WHERE component_type = %s AND is_active = true"
                else:
                    query = "SELECT COUNT(*) FROM hr_product_components WHERE component_type = %s"
                
                cursor.execute(query, (component_type,))
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.log_error(f"HR 컴포넌트 개수 조회 실패: {e}")
            return 0
    
    def add_master_product(self, product_data):
        """마스터 제품 추가 - (success: bool, message: str) 튜플 반환"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # product_code 중복 체크
                product_code = product_data.get('product_code')
                if product_code:
                    cursor.execute("SELECT COUNT(*) FROM master_products WHERE product_code = %s", (product_code,))
                    if cursor.fetchone()[0] > 0:
                        return (False, "중복 코드")
                
                query = """
                    INSERT INTO master_products 
                    (product_code, product_name, product_name_en, product_name_vi, 
                     supplier_name, category_name, unit, supply_currency, supply_price, 
                     exchange_rate, sales_price_vnd, status, created_date, updated_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """
                
                values = (
                    product_data.get('product_code'),
                    product_data.get('name', product_data.get('product_name', '')),
                    product_data.get('product_name_en'),
                    product_data.get('product_name_vi'),
                    product_data.get('supplier_name'),
                    product_data.get('category_name'),
                    product_data.get('unit'),
                    product_data.get('supply_currency'),
                    product_data.get('supply_price'),
                    product_data.get('exchange_rate'),
                    product_data.get('sales_price_vnd'),
                    'active'
                )
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                conn.commit()
                
                if result:
                    product_id = result[0]
                    self.log_info(f"마스터 제품 추가 완료: {product_data.get('product_code')} (ID: {product_id})")
                    return (True, f"제품이 성공적으로 등록되었습니다 (ID: {product_id})")
                else:
                    self.log_error("마스터 제품 추가 실패: 결과 없음")
                    return (False, "제품 등록 실패: 결과 없음")
                
        except Exception as e:
            error_msg = str(e)
            if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                return (False, "중복 코드")
            
            self.log_error(f"마스터 제품 추가 실패: {e}")
            return (False, f"제품 등록 실패: {error_msg}")
    
    def add_item(self, product_data):
        """마스터 제품 추가 (호환성 메서드)"""
        return self.add_master_product(product_data)
