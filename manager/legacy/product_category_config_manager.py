"""
제품 카테고리 설정 관리자
- 제품 분류(HR, HRC, MB 등)의 동적 관리
- 서브 카테고리 및 재질 정보 관리
"""

import sqlite3
import pandas as pd
from datetime import datetime
import uuid
from .database_manager import DatabaseManager

class ProductCategoryConfigManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.init_category_settings_table()
        self.migrate_existing_categories()
    
    def init_category_settings_table(self):
        """제품 카테고리 설정 테이블 초기화"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 제품 카테고리 설정 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_category_settings (
                    setting_id TEXT PRIMARY KEY,
                    category_type TEXT NOT NULL,
                    parent_category TEXT,
                    category_key TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    category_name_en TEXT,
                    category_name_vi TEXT,
                    display_order INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT,
                    created_date TEXT,
                    updated_date TEXT,
                    created_by TEXT
                )
            ''')
            
            # HR 제품 코드 구성 요소 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hr_product_components (
                    component_id TEXT PRIMARY KEY,
                    component_type TEXT NOT NULL,
                    parent_component TEXT,
                    component_key TEXT NOT NULL,
                    component_name TEXT NOT NULL,
                    component_name_en TEXT,
                    component_name_vi TEXT,
                    display_order INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT,
                    created_date TEXT,
                    updated_date TEXT,
                    created_by TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"카테고리 설정 테이블 초기화 오류: {e}")
    
    def migrate_existing_categories(self):
        """기존 하드코딩된 카테고리를 DB로 마이그레이션"""
        try:
            # HR 구성 요소 테이블 확인
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM hr_product_components')
            hr_count = cursor.fetchone()[0]
            conn.close()
            
            # 기존 데이터가 있는지 확인 (HR 구성 요소는 별도 확인)
            if self.get_categories_count() > 0 and hr_count > 0:
                return  # 이미 마이그레이션됨
            
            # 기본 카테고리 데이터
            categories_data = [
                # 메인 카테고리
                ('MC001', 'main_category', None, 'MB', 'MB (Mold Base)', 'Mold Base', 'Đế khuôn', 1, '금형 베이스'),
                ('MC002', 'main_category', None, 'HRC', 'HRC (Controller)', 'Controller', 'Bộ điều khiển vòi phun nóng', 2, '컨트롤러'),
                ('MC003', 'main_category', None, 'HR', 'HR (Hot Runner)', 'Hot Runner', 'Vòi phun nóng', 3, '핫러너 시스템'),
                ('MC004', 'main_category', None, 'MB+HR', 'MB+HR (Mold Base + Hot Runner)', 'Mold Base + Hot Runner', 'Đế khuôn + Vòi phun nóng', 4, '금형베이스+핫러너'),
                ('MC005', 'main_category', None, 'ROBOT', 'ROBOT', 'Robot', 'Robot', 5, '로봇 시스템'),
                ('MC006', 'main_category', None, 'SPARE-HR', 'SPARE-HR', 'HR Spare Parts', 'Phụ tung HR', 6, 'HR 예비부품'),
                ('MC007', 'main_category', None, 'SPARE-MB', 'SPARE-MB', 'MB Spare Parts', 'Phụ tung MB', 7, 'MB 예비부품'),
                ('MC008', 'main_category', None, 'SPARE-ROBOT', 'SPARE-ROBOT', 'Robot Spare Parts', 'Phụ tung Robot', 8, '로봇 예비부품'),
                ('MC009', 'main_category', None, 'SERVICE', 'SERVICE', 'Service', 'Dịch vụ', 9, '서비스'),
                
                # HR 서브카테고리
                ('SC001', 'sub_category', 'HR', 'Valve', 'Valve', 'Valve', 'Van', 1, '밸브형 핫러너'),
                ('SC002', 'sub_category', 'HR', 'Open', 'Open', 'Open', 'Mở', 2, '오픈형 핫러너'),
                
                # Robot 서브카테고리
                ('SC009', 'sub_category', 'ROBOT', 'INDUSTRIAL', 'Industrial Robot', 'Industrial Robot', 'Robot Công nghiệp', 1, '산업용 로봇'),
                ('SC010', 'sub_category', 'ROBOT', 'COLLABORATIVE', 'Collaborative Robot', 'Collaborative Robot', 'Robot Hợp tác', 2, '협동 로봇'),
                
                # HRC 서브카테고리
                ('SC003', 'sub_category', 'HRC', 'HRCT', 'HRCT', 'HRC Temperature', 'HRC Nhiệt độ', 1, 'HRC 온도 제어기'),
                ('SC004', 'sub_category', 'HRC', 'HRCS', 'HRCS', 'HRC Sequential', 'HRC Tuần tự', 2, 'HRC 시간 제어기'),
                
                # MB 서브카테고리
                ('SC006', 'sub_category', 'MB', '2P', '2P', '2 Plate', '2 Tấm', 1, '2판식 금형'),
                ('SC007', 'sub_category', 'MB', '3P', '3P', '3 Plate', '3 Tấm', 2, '3판식 금형'),
                ('SC008', 'sub_category', 'MB', 'HR', 'HR', 'Hot Runner', 'Vòi phun nóng', 3, '핫러너용 금형'),
            ]
            
            # MB 재질
            mb_materials = [
                ('MT001', 'mb_material', 'MB', 'SS400', 'SS400', 'SS400', 'SS400', 1, '일반구조용 압연강재'),
                ('MT002', 'mb_material', 'MB', 'S50C', 'S50C', 'S50C', 'S50C', 2, '탄소강'),
                ('MT003', 'mb_material', 'MB', 'SKD61', 'SKD61', 'SKD61', 'SKD61', 3, '열간공구강'),
                ('MT004', 'mb_material', 'MB', 'NAK80', 'NAK80', 'NAK80', 'NAK80', 4, '예비경화강'),
                ('MT005', 'mb_material', 'MB', 'P20', 'P20', 'P20', 'P20', 5, '예비경화강'),
                ('MT006', 'mb_material', 'MB', 'SCM440', 'SCM440', 'SCM440', 'SCM440', 6, '크롬몰리브덴강'),
                ('MT007', 'mb_material', 'MB', 'FC300', 'FC300', 'FC300', 'FC300', 7, '주철'),
                ('MT008', 'mb_material', 'MB', 'A5052', 'A5052', 'A5052', 'A5052', 8, '알루미늄 합금'),
                ('MT009', 'mb_material', 'MB', 'STAVAX', 'STAVAX', 'STAVAX', 'STAVAX', 9, '스테인리스강'),
                ('MT010', 'mb_material', 'MB', 'HPM38', 'HPM38', 'HPM38', 'HPM38', 10, '예비경화강'),
            ]
            
            # Service 타입
            service_types = [
                ('ST001', 'service_type', 'SERVICE', 'DESIGN', 'DESIGN', 'Design', 'Thiết kế', 1, '설계 서비스'),
                ('ST002', 'service_type', 'SERVICE', 'INSTALL', 'INSTALL', 'Installation', 'Lắp đặt', 2, '설치 서비스'),
                ('ST003', 'service_type', 'SERVICE', 'REPAIR', 'REPAIR', 'Repair', 'Sửa chữa', 3, '수리 서비스'),
                ('ST004', 'service_type', 'SERVICE', 'MAINTAIN', 'MAINTAIN', 'Maintenance', 'Bảo trì', 4, '유지보수 서비스'),
            ]
            
            # Spare 타입
            spare_types = [
                ('SP001', 'spare_type', 'SPARE', 'HEATER', 'HEATER', 'Heater', 'Máy sưởi', 1, '히터'),
                ('SP002', 'spare_type', 'SPARE', 'SENSOR', 'SENSOR', 'Sensor', 'Cảm biến', 2, '센서'),
                ('SP003', 'spare_type', 'SPARE', 'NOZZLE', 'NOZZLE', 'Nozzle', 'Vòi phun', 3, '노즐'),
                ('SP004', 'spare_type', 'SPARE', 'VALVE', 'VALVE', 'Valve', 'Van', 4, '밸브'),
                ('SP005', 'spare_type', 'SPARE', 'CONTROL', 'CONTROL', 'Control Unit', 'Bộ điều khiển', 5, '제어 장치'),
            ]
            
            # HR 제품 코드 구성 요소 데이터
            hr_components_data = [
                # System Type
                ('HR_ST_001', 'system_type', None, 'Valve', 'Valve', 'Valve', 'Van', 1, '밸브형 핫러너'),
                ('HR_ST_002', 'system_type', None, 'Open', 'Open', 'Open', 'Mở', 2, '오픈형 핫러너'),
                ('HR_ST_003', 'system_type', None, 'Robot', 'Robot', 'Robot', 'Robot', 3, '로봇 시스템'),
                
                # Product Type for Valve
                ('HR_PT_V001', 'product_type', 'Valve', 'ST', 'Standard', 'Standard', 'Tiêu chuẩn', 1, 'Valve 표준형'),
                ('HR_PT_V002', 'product_type', 'Valve', 'CP', 'Cosmetic & Packaging', 'Cosmetic & Packaging', 'Mỹ phẩm & Bao bì', 2, 'Valve 화장품/포장용'),
                ('HR_PT_V003', 'product_type', 'Valve', 'PET', 'PET', 'PET', 'PET', 3, 'Valve PET용'),
                ('HR_PT_V004', 'product_type', 'Valve', 'SE', 'Super Engineering', 'Super Engineering', 'Siêu kỹ thuật', 4, 'Valve 수퍼엔지니어링용'),
                ('HR_PT_V005', 'product_type', 'Valve', 'SIV', 'Single Valve', 'Single Valve', 'Van đơn', 5, 'Valve 단일형'),
                
                # Product Type for Open
                ('HR_PT_O001', 'product_type', 'Open', 'ST', 'Standard', 'Standard', 'Tiêu chuẩn', 1, 'Open 표준형'),
                ('HR_PT_O002', 'product_type', 'Open', 'CP', 'Cosmetic & Packaging', 'Cosmetic & Packaging', 'Mỹ phẩm & Bao bì', 2, 'Open 화장품/포장용'),
                ('HR_PT_O003', 'product_type', 'Open', 'SIO', 'Single Open', 'Single Open', 'Mở đơn', 3, 'Open 단일형'),
                
                # Product Type for Robot
                ('HR_PT_R001', 'product_type', 'Robot', 'IND', 'Industrial', 'Industrial', 'Công nghiệp', 1, '산업용 로봇'),
                ('HR_PT_R002', 'product_type', 'Robot', 'COL', 'Collaborative', 'Collaborative', 'Hợp tác', 2, '협동 로봇'),
                
                # Gate Type for Valve-ST
                ('HR_GT_VST001', 'gate_type', 'Valve-ST', 'MAE', 'MAE', 'MAE', 'MAE', 1, 'Valve ST MAE 게이트'),
                ('HR_GT_VST002', 'gate_type', 'Valve-ST', 'MCC', 'MCC', 'MCC', 'MCC', 2, 'Valve ST MCC 게이트'),
                ('HR_GT_VST003', 'gate_type', 'Valve-ST', 'MAA', 'MAA', 'MAA', 'MAA', 3, 'Valve ST MAA 게이트'),
                
                # Gate Type for Valve-CP
                ('HR_GT_VCP001', 'gate_type', 'Valve-CP', 'VL', 'VL', 'VL', 'VL', 1, 'Valve CP VL 게이트'),
                ('HR_GT_VCP002', 'gate_type', 'Valve-CP', 'SC', 'SC', 'SC', 'SC', 2, 'Valve CP SC 게이트'),
                
                # Gate Type for Open-ST
                ('HR_GT_OST001', 'gate_type', 'Open-ST', 'MCC', 'MCC', 'MCC', 'MCC', 1, 'Open ST MCC 게이트'),
                ('HR_GT_OST002', 'gate_type', 'Open-ST', 'MEA', 'MEA', 'MEA', 'MEA', 2, 'Open ST MEA 게이트'),
                
                # Gate Type for Robot-IND
                ('HR_GT_RIND001', 'gate_type', 'Robot-IND', 'ARM', 'ARM', 'ARM', 'ARM', 1, '로봇 암 타입'),
                ('HR_GT_RIND002', 'gate_type', 'Robot-IND', 'GRIP', 'GRIP', 'GRIP', 'GRIP', 2, '그립 타입'),
                
                # Size for Valve-ST
                ('HR_SZ_VST001', 'size', 'Valve-ST', '20', '20', '20', '20', 1, 'Valve ST 20 사이즈'),
                ('HR_SZ_VST002', 'size', 'Valve-ST', '25', '25', '25', '25', 2, 'Valve ST 25 사이즈'),
                ('HR_SZ_VST003', 'size', 'Valve-ST', '35', '35', '35', '35', 3, 'Valve ST 35 사이즈'),
                ('HR_SZ_VST004', 'size', 'Valve-ST', '45', '45', '45', '45', 4, 'Valve ST 45 사이즈'),
                
                # Size for Open-ST
                ('HR_SZ_OST001', 'size', 'Open-ST', '20', '20', '20', '20', 1, 'Open ST 20 사이즈'),
                ('HR_SZ_OST002', 'size', 'Open-ST', '25', '25', '25', '25', 2, 'Open ST 25 사이즈'),
                ('HR_SZ_OST003', 'size', 'Open-ST', '35', '35', '35', '35', 3, 'Open ST 35 사이즈'),
                ('HR_SZ_OST004', 'size', 'Open-ST', '45', '45', '45', '45', 4, 'Open ST 45 사이즈'),
                
                # Size for Robot-IND
                ('HR_SZ_RIND001', 'size', 'Robot-IND', 'S', 'S', 'S', 'S', 1, '소형'),
                ('HR_SZ_RIND002', 'size', 'Robot-IND', 'M', 'M', 'M', 'M', 2, '중형'),
                ('HR_SZ_RIND003', 'size', 'Robot-IND', 'L', 'L', 'L', 'L', 3, '대형'),
                
                # Robot Application Types
                ('ROBOT_APP001', 'robot_application', 'ROBOT', 'INJECTION', 'Injection Molding', 'Injection Molding', 'Ép phun', 1, '사출 성형용 로봇'),
                ('ROBOT_APP002', 'robot_application', 'ROBOT', 'ASSEMBLY', 'Assembly', 'Assembly', 'Lắp ráp', 2, '조립용 로봇'),
                ('ROBOT_APP003', 'robot_application', 'ROBOT', 'PACKAGING', 'Packaging', 'Packaging', 'Đóng gói', 3, '포장용 로봇'),
                ('ROBOT_APP004', 'robot_application', 'ROBOT', 'WELDING', 'Welding', 'Welding', 'Hàn', 4, '용접용 로봇'),
                ('ROBOT_APP005', 'robot_application', 'ROBOT', 'PAINTING', 'Painting', 'Painting', 'Sơn', 5, '도장용 로봇'),
                
                # Robot Payloads (kg)
                ('ROBOT_PL001', 'robot_payload', 'ROBOT', '3', '3kg', '3kg', '3kg', 1, '3kg까지 처리 가능'),
                ('ROBOT_PL002', 'robot_payload', 'ROBOT', '6', '6kg', '6kg', '6kg', 2, '6kg까지 처리 가능'),
                ('ROBOT_PL003', 'robot_payload', 'ROBOT', '10', '10kg', '10kg', '10kg', 3, '10kg까지 처리 가능'),
                ('ROBOT_PL004', 'robot_payload', 'ROBOT', '20', '20kg', '20kg', '20kg', 4, '20kg까지 처리 가능'),
                ('ROBOT_PL005', 'robot_payload', 'ROBOT', '50', '50kg', '50kg', '50kg', 5, '50kg까지 처리 가능'),
                
                # Robot Reach (mm)
                ('ROBOT_RE001', 'robot_reach', 'ROBOT', '500', '500mm', '500mm', '500mm', 1, '500mm 도달 범위'),
                ('ROBOT_RE002', 'robot_reach', 'ROBOT', '900', '900mm', '900mm', '900mm', 2, '900mm 도달 범위'),
                ('ROBOT_RE003', 'robot_reach', 'ROBOT', '1400', '1400mm', '1400mm', '1400mm', 3, '1400mm 도달 범위'),
                ('ROBOT_RE004', 'robot_reach', 'ROBOT', '1800', '1800mm', '1800mm', '1800mm', 4, '1800mm 도달 범위'),
                ('ROBOT_RE005', 'robot_reach', 'ROBOT', '2600', '2600mm', '2600mm', '2600mm', 5, '2600mm 도달 범위'),
                
                # Robot Axes
                ('ROBOT_AX001', 'robot_axes', 'ROBOT', '4', '4축', '4-axis', '4 trục', 1, '4축 SCARA 로봇'),
                ('ROBOT_AX002', 'robot_axes', 'ROBOT', '5', '5축', '5-axis', '5 trục', 2, '5축 로봇'),
                ('ROBOT_AX003', 'robot_axes', 'ROBOT', '6', '6축', '6-axis', '6 trục', 3, '6축 관절 로봇'),
                ('ROBOT_AX004', 'robot_axes', 'ROBOT', '7', '7축', '7-axis', '7 trục', 4, '7축 협동 로봇'),
            ]
            
            # 모든 데이터 삽입
            all_categories = categories_data + mb_materials + service_types + spare_types
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 기존 카테고리 데이터 삽입
            if self.get_categories_count() == 0:
                for category in all_categories:
                    cursor.execute('''
                        INSERT INTO product_category_settings 
                        (setting_id, category_type, parent_category, category_key, category_name, 
                         category_name_en, category_name_vi, display_order, is_active, description,
                         created_date, updated_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'system')
                    ''', (*category, current_time, current_time))
            
            # HR 구성 요소 데이터 삽입 (별도 확인)
            if hr_count == 0:
                for component in hr_components_data:
                    cursor.execute('''
                        INSERT INTO hr_product_components 
                        (component_id, component_type, parent_component, component_key, component_name, 
                         component_name_en, component_name_vi, display_order, is_active, description,
                         created_date, updated_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'system')
                    ''', (*component, current_time, current_time))
            
            conn.commit()
            conn.close()
            
            print("기존 카테고리 데이터 마이그레이션 완료")
            
        except Exception as e:
            print(f"카테고리 마이그레이션 오류: {e}")
    
    def get_categories_count(self):
        """현재 등록된 카테고리 수 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM product_category_settings')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def get_main_categories(self):
        """메인 카테고리 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_name, category_name_en, category_name_vi
                FROM product_category_settings 
                WHERE category_type = 'main_category' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            categories = cursor.fetchall()
            conn.close()
            
            # 카테고리 키만 반환 (기존 코드와 호환성 위해)
            return [cat[0] for cat in categories]
            
        except Exception as e:
            print(f"메인 카테고리 조회 오류: {e}")
            # 폴백: 기존 하드코딩된 값
            return ['MB', 'HRC', 'HR', 'MB+HR', 'ROBOT', 'SPARE-HR', 'SPARE-MB', 'SPARE-ROBOT', 'SERVICE']
    
    # ========== HR 제품 코드 구성 요소 관리 ==========
    
    def get_hr_system_types(self):
        """HR System Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'system_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HR System Type 조회 오류: {e}")
            return ['Valve', 'Open']
    
    def get_hr_product_types(self, system_type=None):
        """HR Product Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if system_type:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'product_type' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (system_type,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'product_type' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HR Product Type 조회 오류: {e}")
            return ['ST', 'CP', 'SE', 'SIV', 'SIO']
    
    def get_hr_gate_types(self, system_type=None, product_type=None):
        """HR Gate Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if system_type and product_type:
                parent_key = f"{system_type}-{product_type}"
                cursor.execute('''
                    SELECT DISTINCT component_key 
                    FROM hr_product_components 
                    WHERE component_type = 'gate_type' 
                    AND parent_component = ? 
                    AND is_active = 1
                    ORDER BY component_key
                ''', (parent_key,))
            else:
                cursor.execute('''
                    SELECT DISTINCT component_key 
                    FROM hr_product_components 
                    WHERE component_type = 'gate_type' 
                    AND is_active = 1
                    ORDER BY component_key
                ''')
            
            gate_types = [row[0] for row in cursor.fetchall()]
            conn.close()
            return gate_types
            
        except Exception as e:
            print(f"HR Gate Type 조회 오류: {e}")
            return ['MAE', 'MCC', 'VL', 'SC']
    
    def get_hr_sizes(self, system_type=None, product_type=None, gate_type=None):
        """HR Size 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if system_type and product_type and gate_type:
                parent_key = f"{system_type}-{product_type}-{gate_type}"
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'gate_type' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HR Gate Type 조회 오류: {e}")
            return ['MAE', 'MCC', 'VL', 'SC']
    
    def get_hr_sizes(self, system_type=None, product_type=None, gate_type=None):
        """HR Size 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if system_type and product_type and gate_type:
                parent_key = f"{system_type}-{product_type}-{gate_type}"
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'size' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (parent_key,))
            elif system_type and product_type:
                parent_key = f"{system_type}-{product_type}"
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'size' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (parent_key,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'size' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HR Size 조회 오류: {e}")
            return ['20', '25', '35', '45']
    
    def add_hr_component(self, component_type, parent_component, component_key, component_name, 
                        component_name_en=None, component_name_vi=None, description=None):
        """HR 구성 요소 추가
        
        Args:
            component_type: 구성 요소 타입 (예: 'gate_type', 'size' 등)
            parent_component: 부모 구성 요소 (예: 'Valve-SE', 'Valve-ST' 등)
            component_key: 구성 요소 키 (예: 'MVA', 'MAE' 등)
            component_name: 구성 요소 이름
            component_name_en: 영어 이름 (선택)
            component_name_vi: 베트남어 이름 (선택)
            description: 설명 (선택)
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 중복 확인
            cursor.execute('''
                SELECT component_id FROM hr_product_components 
                WHERE component_type = ? AND component_key = ? AND parent_component = ?
            ''', (component_type, component_key, parent_component))
            
            if cursor.fetchone():
                conn.close()
                return False
            
            # 새로운 ID 생성
            component_id = f"HR_{component_type.upper()[:2]}_{str(uuid.uuid4())[:8].upper()}"
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 표시 순서 계산
            cursor.execute('''
                SELECT COALESCE(MAX(display_order), 0) + 1 
                FROM hr_product_components 
                WHERE component_type = ? AND parent_component = ?
            ''', (component_type, parent_component))
            display_order = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO hr_product_components 
                (component_id, component_type, parent_component, component_key, component_name,
                 component_name_en, component_name_vi, display_order, is_active, description,
                 created_date, updated_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'user')
            ''', (component_id, component_type, parent_component, component_key, component_name,
                  component_name_en, None, display_order, description, 
                  current_time, current_time))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"HR 구성 요소 추가 오류: {e}")
            return False
    
    def update_hr_component(self, component_id, component_key=None, component_name=None, 
                           component_name_en=None, component_name_vi=None, description=None):
        """HR 구성 요소 수정"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 현재 데이터 조회
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi, description 
                FROM hr_product_components 
                WHERE component_id = ?
            ''', (component_id,))
            
            current_data = cursor.fetchone()
            if not current_data:
                conn.close()
                return False
            
            # 기본값으로 현재 데이터 사용
            final_key = component_key if component_key is not None else current_data[0]
            final_name = component_name if component_name is not None else current_data[1]
            final_name_en = component_name_en if component_name_en is not None else current_data[2]
            final_name_vi = component_name_vi if component_name_vi is not None else current_data[3]
            final_description = description if description is not None else current_data[4]
            
            cursor.execute('''
                UPDATE hr_product_components 
                SET component_key = ?, component_name = ?, component_name_en = ?, 
                    component_name_vi = ?, description = ?, updated_date = ?
                WHERE component_id = ?
            ''', (final_key, final_name, final_name_en, final_name_vi, final_description, 
                  current_time, component_id))
            
            conn.commit()
            result = cursor.rowcount > 0
            conn.close()
            return result
            
        except Exception as e:
            print(f"HR 구성 요소 수정 오류: {e}")
            return False
    
    
    def delete_all_hr_components(self):
        """모든 HR 구성 요소를 완전히 삭제"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            print("모든 HR 구성 요소 완전 삭제 시작")
            
            # 1. 모든 master_products에서 HR 관련 제품 삭제
            cursor.execute("DELETE FROM master_products WHERE product_code LIKE 'HR-%'")
            deleted_products = cursor.rowcount
            print(f"삭제된 제품 코드: {deleted_products}개")
            
            # 2. 모든 hr_product_components 테이블 완전 정리
            cursor.execute("DELETE FROM hr_product_components")
            deleted_components = cursor.rowcount
            print(f"삭제된 모든 구성 요소: {deleted_components}개")
            
            conn.commit()
            conn.close()
            print("모든 HR 구성 요소 완전 삭제 완료")
            return True
            
        except Exception as e:
            print(f"모든 HR 구성 요소 삭제 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def delete_hr_component_permanently(self, component_id):
        """HR 구성 요소 완전 삭제 (물리적 삭제) - 계층적 삭제 포함"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 먼저 삭제할 구성 요소 정보 조회
            cursor.execute('''
                SELECT component_type, component_key, parent_component 
                FROM hr_product_components 
                WHERE component_id = ?
            ''', (component_id,))
            
            component_info = cursor.fetchone()
            if not component_info:
                conn.close()
                return False
                
            component_type, component_key, parent_component = component_info
            print(f"삭제 대상: {component_type} - {component_key}")
            
            # 계층적 삭제 수행 (항목에 따라)
            if component_type == 'system_type':
                # A-1 삭제시 모든 하위 계층 삭제
                self._delete_system_type_cascade(cursor, component_key)
            elif component_type == 'product_type':
                # A-2 삭제시 A-3~A-6 삭제
                self._delete_product_type_cascade(cursor, component_key, parent_component)
            elif component_type == 'gate_type':
                # A-3 삭제시 A-4~A-6 삭제
                self._delete_gate_type_cascade(cursor, component_key, parent_component)
            elif component_type == 'size':
                # A-4 삭제시 A-5~A-6 삭제
                self._delete_size_cascade(cursor, component_key, parent_component)
            elif component_type == 'level5':
                # A-5 삭제시 A-6 삭제
                self._delete_level5_cascade(cursor, component_key, parent_component)
            elif component_type == 'level6':
                # A-6은 최하위이므로 자신만 삭제
                self._delete_level6_cascade(cursor, component_key, parent_component)
            
            # 마지막으로 해당 구성 요소 자체 삭제
            cursor.execute('''
                DELETE FROM hr_product_components 
                WHERE component_id = ?
            ''', (component_id,))
            deleted_self = cursor.rowcount
            print(f"본인 삭제: {deleted_self}개")
            
            conn.commit()
            conn.close()
            print(f"계층적 삭제 완료: {component_type} '{component_key}'")
            return True
            
        except Exception as e:
            print(f"HR 구성 요소 완전 삭제 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _delete_system_type_cascade(self, cursor, system_type):
        """System Type 계층적 삭제 - 완전히 삭제"""
        print(f"System Type '{system_type}' 계층적 삭제 시작")
        
        # 1. 관련 제품 코드들 삭제 (master_products)
        cursor.execute('''
            DELETE FROM master_products 
            WHERE product_code LIKE 'HR-' || ? || '-%'
        ''', (self._get_system_type_code(system_type),))
        deleted_products = cursor.rowcount
        print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. 모든 하위 구성 요소들 삭제 (다단계로 확실히 삭제)
        # A-2부터 A-6까지 차례대로 삭제
        
        # A-6 (level6) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level6' 
              AND parent_component LIKE ? || '%'
        ''', (system_type + '-',))
        deleted_l6 = cursor.rowcount
        print(f"삭제된 A-6 (level6): {deleted_l6}개")
        
        # A-5 (level5) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level5' 
              AND parent_component LIKE ? || '%'
        ''', (system_type + '-',))
        deleted_l5 = cursor.rowcount
        print(f"삭제된 A-5 (level5): {deleted_l5}개")
        
        # A-4 (size) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'size' 
              AND parent_component LIKE ? || '%'
        ''', (system_type + '-',))
        deleted_size = cursor.rowcount
        print(f"삭제된 A-4 (size): {deleted_size}개")
        
        # A-3 (gate_type) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'gate_type' 
              AND parent_component LIKE ? || '%'
        ''', (system_type + '-',))
        deleted_gate = cursor.rowcount
        print(f"삭제된 A-3 (gate_type): {deleted_gate}개")
        
        # A-2 (product_type) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'product_type' 
              AND parent_component = ?
        ''', (system_type,))
        deleted_product = cursor.rowcount
        print(f"삭제된 A-2 (product_type): {deleted_product}개")
    
    def _delete_product_type_cascade(self, cursor, product_type, system_type):
        """A-2 삭제 → A-3부터 A-6까지 관련 계층 삭제"""
        parent_key = f"{system_type}-{product_type}"
        print(f"A-2 삭제: '{product_type}' (parent: {system_type})")
        
        # 1. 관련 제품 코드들 삭제
        cursor.execute('''
            DELETE FROM master_products 
            WHERE product_code LIKE 'HR-' || ? || '-' || ? || '-%'
        ''', (self._get_system_type_code(system_type), product_type))
        deleted_products = cursor.rowcount
        print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. A-6 (level6) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level6' 
              AND parent_component LIKE ? || '-%-%-%-%'
        ''', (parent_key,))
        deleted_l6 = cursor.rowcount
        print(f"삭제된 A-6 (level6): {deleted_l6}개")
        
        # 3. A-5 (level5) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level5' 
              AND parent_component LIKE ? || '-%-%-%'
        ''', (parent_key,))
        deleted_l5 = cursor.rowcount
        print(f"삭제된 A-5 (level5): {deleted_l5}개")
        
        # 4. A-4 (size) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'size' 
              AND parent_component LIKE ? || '-%-%'
        ''', (parent_key,))
        deleted_size = cursor.rowcount
        print(f"삭제된 A-4 (size): {deleted_size}개")
        
        # 5. A-3 (gate_type) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'gate_type' 
              AND parent_component = ?
        ''', (parent_key,))
        deleted_gate = cursor.rowcount
        print(f"삭제된 A-3 (gate_type): {deleted_gate}개")
    
    def _delete_gate_type_cascade(self, cursor, gate_type, parent_component):
        """A-3 삭제 → A-4부터 A-6까지 관련 계층 삭제"""
        parent_key = f"{parent_component}-{gate_type}"
        print(f"A-3 삭제: '{gate_type}' (parent: {parent_component})")
        
        # 1. 관련 제품 코드들 삭제
        parts = parent_component.split('-')
        if len(parts) >= 2:
            system_type, product_type = parts[0], parts[1]
            cursor.execute('''
                DELETE FROM master_products 
                WHERE product_code LIKE 'HR-' || ? || '-' || ? || '-' || ? || '-%'
            ''', (self._get_system_type_code(system_type), product_type, gate_type))
            deleted_products = cursor.rowcount
            print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. A-6 (level6) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level6' 
              AND parent_component LIKE ? || '-%-%'
        ''', (parent_key,))
        deleted_l6 = cursor.rowcount
        print(f"삭제된 A-6 (level6): {deleted_l6}개")
        
        # 3. A-5 (level5) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level5' 
              AND parent_component LIKE ? || '-%'
        ''', (parent_key,))
        deleted_l5 = cursor.rowcount
        print(f"삭제된 A-5 (level5): {deleted_l5}개")
        
        # 4. A-4 (size) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'size' 
              AND parent_component = ?
        ''', (parent_key,))
        deleted_size = cursor.rowcount
        print(f"삭제된 A-4 (size): {deleted_size}개")
    
    def _delete_size_cascade(self, cursor, size_key, parent_component):
        """A-4 삭제 → A-5부터 A-6까지 관련 계층 삭제"""
        parent_key = f"{parent_component}-{size_key}"
        print(f"A-4 삭제: '{size_key}' (parent: {parent_component})")
        
        # 1. 관련 제품 코드들 삭제
        parts = parent_component.split('-')
        if len(parts) >= 3:
            system_type, product_type, gate_type = parts[0], parts[1], parts[2]
            cursor.execute('''
                DELETE FROM master_products 
                WHERE product_code LIKE 'HR-' || ? || '-' || ? || '-' || ? || '-' || ? || '-%'
            ''', (self._get_system_type_code(system_type), product_type, gate_type, size_key))
            deleted_products = cursor.rowcount
            print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. A-6 (level6) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level6' 
              AND parent_component LIKE ? || '-%'
        ''', (parent_key,))
        deleted_l6 = cursor.rowcount
        print(f"삭제된 A-6 (level6): {deleted_l6}개")
        
        # 3. A-5 (level5) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level5' 
              AND parent_component = ?
        ''', (parent_key,))
        deleted_l5 = cursor.rowcount
        print(f"삭제된 A-5 (level5): {deleted_l5}개")
    
    def _delete_level5_cascade(self, cursor, level5_key, parent_component):
        """A-5 삭제 → A-6까지 관련 계층 삭제"""
        parent_key = f"{parent_component}-{level5_key}"
        print(f"A-5 삭제: '{level5_key}' (parent: {parent_component})")
        
        # 1. 관련 제품 코드들 삭제
        parts = parent_component.split('-')
        if len(parts) >= 4:
            system_type, product_type, gate_type, size_key = parts[0], parts[1], parts[2], parts[3]
            cursor.execute('''
                DELETE FROM master_products 
                WHERE product_code LIKE 'HR-' || ? || '-' || ? || '-' || ? || '-' || ? || '-' || ? || '-%'
            ''', (self._get_system_type_code(system_type), product_type, gate_type, size_key, level5_key))
            deleted_products = cursor.rowcount
            print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. A-6 (level6) 삭제
        cursor.execute('''
            DELETE FROM hr_product_components 
            WHERE component_type = 'level6' 
              AND parent_component = ?
        ''', (parent_key,))
        deleted_l6 = cursor.rowcount
        print(f"삭제된 A-6 (level6): {deleted_l6}개")
    
    def _delete_level6_cascade(self, cursor, level6_key, parent_component):
        """A-6 삭제 → A-6 자신만 삭제"""
        print(f"A-6 삭제: '{level6_key}' (parent: {parent_component})")
        
        # 1. 관련 제품 코드들 삭제
        parts = parent_component.split('-')
        if len(parts) >= 5:
            system_type, product_type, gate_type, size_key, level5_key = parts[0], parts[1], parts[2], parts[3], parts[4]
            cursor.execute('''
                DELETE FROM master_products 
                WHERE product_code LIKE 'HR-' || ? || '-' || ? || '-' || ? || '-' || ? || '-' || ? || '-' || ?
            ''', (self._get_system_type_code(system_type), product_type, gate_type, size_key, level5_key, level6_key))
            deleted_products = cursor.rowcount
            print(f"삭제된 제품 코드: {deleted_products}개")
        
        # 2. A-6 자신만 삭제 (더 이상 하위 계층 없음)
        print("A-6은 최하위 계층이므로 자신만 삭제됩니다.")
    
    def _get_system_type_code(self, system_type):
        """System Type을 코드로 변환"""
        if system_type == "Valve":
            return "VV"
        elif system_type == "Open":
            return "OP"
        else:
            return system_type[:2].upper()
    
    def delete_inactive_hr_components(self):
        """비활성 HR 구성 요소 완전 삭제"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 비활성 관련 제품 코드들 먼저 삭제
            cursor.execute('''
                DELETE FROM master_products 
                WHERE product_code LIKE 'HR-%'
                  AND product_code IN (
                    SELECT DISTINCT (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key || '-' || l6.component_key)
                    FROM hr_product_components s
                    JOIN hr_product_components p ON p.parent_component = s.component_key
                    JOIN hr_product_components g ON g.parent_component = (s.component_key || '-' || p.component_key)
                    JOIN hr_product_components sz ON sz.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key)
                    JOIN hr_product_components l5 ON l5.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key)
                    JOIN hr_product_components l6 ON l6.parent_component = (s.component_key || '-' || p.component_key || '-' || g.component_key || '-' || sz.component_key || '-' || l5.component_key)
                    WHERE s.component_type = 'system_type'
                      AND p.component_type = 'product_type'
                      AND g.component_type = 'gate_type'
                      AND sz.component_type = 'size'
                      AND l5.component_type = 'level5'
                      AND l6.component_type = 'level6'
                      AND (s.is_active = 0 OR p.is_active = 0 OR g.is_active = 0 OR sz.is_active = 0 OR l5.is_active = 0 OR l6.is_active = 0)
                  )
            ''')
            deleted_products = cursor.rowcount
            
            # 비활성 HR 구성 요소 삭제
            cursor.execute('DELETE FROM hr_product_components WHERE is_active = 0')
            deleted_components = cursor.rowcount
            
            conn.commit()
            conn.close()
            return deleted_components
            
        except Exception as e:
            print(f"비활성 HR 구성 요소 삭제 오류: {e}")
            return 0
    
    def clear_all_hr_components(self):
        """모든 HR 구성 요소 완전 삭제"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 모든 HR 구성 요소 삭제
            cursor.execute('DELETE FROM hr_product_components')
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            return deleted_count
            
        except Exception as e:
            print(f"모든 HR 구성 요소 삭제 오류: {e}")
            return 0
    
    # ========== HRC 제품 코드 구성 요소 관리 (HR 스타일) ==========
    
    def get_hrc_types(self):
        """HRC Type 목록 조회 (HRCT, HRCS 등)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'hrc_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC Type 조회 오류: {e}")
            return ['HRCT', 'HRCS']
    
    def get_hrc_product_types(self, hrc_type=None):
        """HRC 제품 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if hrc_type:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_product_type' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (hrc_type,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_product_type' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC 제품 타입 조회 오류: {e}")
            if hrc_type == "HRCT":
                return ['TEMP']
            elif hrc_type == "HRCS":
                return ['TIMER']
            else:
                return ['TEMP', 'TIMER']
    
    def get_hrc_model_types(self, hrc_type=None, product_type=None):
        """HRC 모델 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if hrc_type and product_type:
                parent_key = f"{hrc_type}-{product_type}"
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_model_type' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (parent_key,))
            elif hrc_type:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_model_type' AND parent_component LIKE ? AND is_active = 1 
                    ORDER BY display_order
                ''', (f"{hrc_type}-%",))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_model_type' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC 모델 타입 조회 오류: {e}")
            if hrc_type == "HRCT" and product_type == "TEMP":
                return ['YC60', 'SNT900']
            elif hrc_type == "HRCS" and product_type == "TIMER":
                return ['YC60T', 'MDS08AT', 'MDS08BT']
            else:
                return ['YC60', 'SNT900', 'YC60T', 'MDS08AT', 'MDS08BT']

    # ========== 기존 HRC 제품 코드 구성 요소 관리 (호환성) ==========
    
    def get_hrc_subtypes(self):
        """HRC 서브타입 목록 조회 (HRCT, HRCS)"""
        return ['HRCT', 'HRCS']
    
    def get_hrct_categories(self):
        """HRCT 카테고리 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'hrct_category' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRCT 카테고리 조회 오류: {e}")
            return ['TEMP']
    
    def get_hrcs_categories(self):
        """HRCS 카테고리 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'hrcs_category' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRCS 카테고리 조회 오류: {e}")
            return ['TIMER']
    
    def get_hrc_categories(self):
        """HRC 카테고리 목록 조회 (호환성 유지)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'hrc_category' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC 카테고리 조회 오류: {e}")
            return ['TEMP', 'TIMER']
    
    def get_hrct_models(self, category=None):
        """HRCT 모델 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrct_model' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (category,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrct_model' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRCT 모델 조회 오류: {e}")
            if category == "TEMP":
                return ['YC60', 'SNT900']
            else:
                return ['YC60', 'SNT900']
    
    def get_hrcs_models(self, category=None):
        """HRCS 모델 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrcs_model' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (category,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrcs_model' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRCS 모델 조회 오류: {e}")
            if category == "TIMER":
                return ['YC60T', 'MDS08AT', 'MDS08BT']
            else:
                return ['YC60T', 'MDS08AT', 'MDS08BT']

    # ========== HRC 자동 제품 생성 (HR과 동일한 방식) ==========
    
    def create_hrc_products_for_zone(self, zone_key):
        """새로운 HRC 존 번호에 대해 자동으로 제품 생성 (HR 사이즈와 동일한 방식)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            master_manager = SQLiteMasterProductManager()
            
            products_created = 0
            
            # 모든 HRC Type 조회
            hrc_types = self.get_hrc_types()
            
            for hrc_type in hrc_types:
                # 각 HRC Type의 제품 타입 조회
                product_types = self.get_hrc_product_types(hrc_type)
                
                for product_type in product_types:
                    # 각 제품 타입의 모델 조회
                    models = self.get_hrc_models(hrc_type, product_type)
                    
                    for model in models:
                        # HRC 제품 코드 생성: HRC-{Type}-{ProductType}-{Model}-{Zone}
                        # Type 코드 변환 (HRCT -> CT, HRCS -> CS)
                        type_code = "CT" if hrc_type == "HRCT" else "CS" if hrc_type == "HRCS" else hrc_type[:2]
                        
                        product_code = f"HRC-{type_code}-{product_type}-{model}-{zone_key}"
                        
                        # 제품명 생성
                        hrc_type_name = "온도 제어기" if hrc_type == "HRCT" else "시간 제어기" if hrc_type == "HRCS" else hrc_type
                        product_name = f"HRC {hrc_type_name} {product_type} {model} Zone{zone_key}"
                        product_name_en = f"HRC {hrc_type} {product_type} {model} Zone{zone_key}"
                        
                        # 제품 데이터 준비
                        product_data = {
                            'product_code': product_code,
                            'product_name': product_name,
                            'product_name_en': product_name_en,
                            'product_name_vi': product_name_en,  # 영어와 동일
                            'category_name': 'HRC',
                            'subcategory_name': hrc_type,
                            'specifications': f"Zone{zone_key},{model},{product_type}",
                            'description': f"HRC {hrc_type_name} {model} 모델 Zone{zone_key}",
                            'unit': 'EA',
                            'status': 'active'
                        }
                        
                        # 제품 추가 (중복 체크는 SQLiteMasterProductManager에서 처리)
                        result = master_manager.add_master_product(product_data)
                        if result:
                            products_created += 1
                            print(f"HRC 제품 생성: {product_code} - {product_name}")
            
            return products_created
            
        except Exception as e:
            print(f"HRC 자동 제품 생성 오류: {e}")
            return 0
    
    def get_hrc_types(self):
        """HRC Type 목록 조회 (HRCT, HRCS)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'hrc_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"HRC Type 조회 오류: {e}")
            return ['HRCT', 'HRCS']  # 기본값
    
    def get_hrc_product_types(self, hrc_type):
        """특정 HRC Type의 제품 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'hrc_product_type' 
                  AND parent_component = ? AND is_active = 1 
                ORDER BY display_order
            ''', (hrc_type,))
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"HRC 제품 타입 조회 오류: {e}")
            # 기본값
            if hrc_type == "HRCT":
                return ['TEMP']
            elif hrc_type == "HRCS":
                return ['TIMER']
            else:
                return []
    
    def get_hrc_models(self, hrc_type, product_type):
        """특정 HRC Type과 제품 타입의 모델 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'hrc_model_type' 
                  AND parent_component = ? AND sub_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (hrc_type, product_type))
            
            models = cursor.fetchall()
            conn.close()
            
            return [m[0] for m in models]
            
        except Exception as e:
            print(f"HRC 모델 조회 오류: {e}")
            # 기본값
            if hrc_type == "HRCT" and product_type == "TEMP":
                return ['YC60', 'SNT900']
            elif hrc_type == "HRCS" and product_type == "TIMER":
                return ['YC60T', 'MDS08AT', 'MDS08BT']
            else:
                return []

    # ========== ROBOT 자동 제품 생성 (HR과 동일한 방식) ==========
    
    def create_robot_product_for_reach(self, application, axes, payload, reach):
        """새로운 ROBOT Reach에 대해 자동으로 제품 생성 (HR 사이즈와 동일한 방식)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            master_manager = SQLiteMasterProductManager()
            
            # ROBOT 제품 코드 생성: ROBOT-{Application}-{Axes}-{Payload}-{Reach}
            # Application 코드 변환 (Industrial -> IND, Collaborative -> COL)
            app_code = "IND" if application == "Industrial" else "COL" if application == "Collaborative" else application[:3].upper()
            
            product_code = f"ROBOT-{app_code}-{axes}-{payload}-{reach}"
            
            # 제품명 생성
            product_name = f"ROBOT {application} {axes}축 {payload}kg {reach}mm"
            product_name_en = f"ROBOT {application} {axes}Axis {payload}kg {reach}mm"
            
            # 제품 데이터 준비
            product_data = {
                'product_code': product_code,
                'product_name': product_name,
                'product_name_en': product_name_en,
                'product_name_vi': product_name_en,  # 영어와 동일
                'category_name': 'ROBOT',
                'subcategory_name': application,
                'specifications': f"{axes}축,{payload}kg,{reach}mm,{application}",
                'description': f"ROBOT {application} {axes}축 최대 {payload}kg 페이로드 {reach}mm 도달거리",
                'unit': 'EA',
                'status': 'active'
            }
            
            # 제품 추가 (중복 체크는 SQLiteMasterProductManager에서 처리)
            result = master_manager.add_master_product(product_data)
            if result:
                print(f"ROBOT 제품 생성: {product_code} - {product_name}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"ROBOT 자동 제품 생성 오류: {e}")
            return False
    
    def get_robot_applications(self):
        """ROBOT Application 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'robot_application' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            apps = cursor.fetchall()
            conn.close()
            
            return [app[0] for app in apps]
            
        except Exception as e:
            print(f"ROBOT Application 조회 오류: {e}")
            return ['Industrial', 'Collaborative']  # 기본값
    
    def get_robot_axes(self, application):
        """특정 Application의 축 수 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'robot_axes' 
                  AND parent_component = ? AND is_active = 1 
                ORDER BY display_order
            ''', (application,))
            
            axes = cursor.fetchall()
            conn.close()
            
            return [ax[0] for ax in axes]
            
        except Exception as e:
            print(f"ROBOT 축 수 조회 오류: {e}")
            # 기본값
            return ['6', '7']  # 기본 6축, 7축
    
    def get_robot_payloads(self, application, axes):
        """특정 Application과 축 수의 Payload 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'robot_payload' 
                  AND parent_component = ? AND sub_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (application, axes))
            
            payloads = cursor.fetchall()
            conn.close()
            
            return [pl[0] for pl in payloads]
            
        except Exception as e:
            print(f"ROBOT Payload 조회 오류: {e}")
            # 기본값
            if application == "Industrial":
                return ['5', '10', '20', '50']
            else:
                return ['3', '5', '10']
    
    def get_robot_reaches(self, application, axes, payload):
        """특정 Application, 축수, Payload의 Reach 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            parent_key = f"{application}-{axes}-{payload}"
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'robot_reach' 
                  AND parent_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (parent_key,))
            
            reaches = cursor.fetchall()
            conn.close()
            
            return [r[0] for r in reaches]
            
        except Exception as e:
            print(f"ROBOT Reach 조회 오류: {e}")
            # 기본값
            if application == "Industrial":
                return ['800', '1400', '1800', '2600']
            else:
                return ['500', '850', '1300']

    # ========== MB 자동 제품 생성 (HR과 동일한 방식) ==========
    
    def create_mb_product_for_size(self, mb_type, subcategory, material, size):
        """새로운 MB Size에 대해 자동으로 제품 생성 (HR 사이즈와 동일한 방식)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            master_manager = SQLiteMasterProductManager()
            
            # MB 제품 코드 생성: MB-{Type}-{SubCategory}-{Material}-{Size}
            # Type 코드 변환 (HEATING -> HT, INSULATION -> IN)
            type_code = "HT" if mb_type == "HEATING" else "IN" if mb_type == "INSULATION" else mb_type[:2].upper()
            
            product_code = f"MB-{type_code}-{subcategory}-{material}-{size}"
            
            # 제품명 생성
            product_name = f"MB {mb_type} {subcategory} {material} {size}"
            product_name_en = f"MB {mb_type} {subcategory} {material} {size}"
            
            # 제품 데이터 준비
            product_data = {
                'product_code': product_code,
                'product_name': product_name,
                'product_name_en': product_name_en,
                'product_name_vi': product_name_en,  # 영어와 동일
                'category_name': 'MB',
                'subcategory_name': mb_type,
                'specifications': f"{size},{material},{subcategory},{mb_type}",
                'description': f"MB {mb_type} {subcategory} {material} 소재 {size} 사이즈",
                'unit': 'EA',
                'status': 'active'
            }
            
            # 제품 추가 (중복 체크는 SQLiteMasterProductManager에서 처리)
            result = master_manager.add_master_product(product_data)
            if result:
                print(f"MB 제품 생성: {product_code} - {product_name}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"MB 자동 제품 생성 오류: {e}")
            return False
    
    def get_mb_types(self):
        """MB Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'mb_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"MB Type 조회 오류: {e}")
            return ['HEATING', 'INSULATION']  # 기본값
    
    def get_mb_subcategories(self, mb_type):
        """특정 MB Type의 SubCategory 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'mb_subcategory' 
                  AND parent_component = ? AND is_active = 1 
                ORDER BY display_order
            ''', (mb_type,))
            
            subcategories = cursor.fetchall()
            conn.close()
            
            return [sc[0] for sc in subcategories]
            
        except Exception as e:
            print(f"MB SubCategory 조회 오류: {e}")
            # 기본값
            if mb_type == "HEATING":
                return ['ELEMENT', 'PLATE', 'WIRE']
            elif mb_type == "INSULATION":
                return ['BOARD', 'SHEET', 'FOAM']
            else:
                return []
    
    def get_mb_materials(self, mb_type, subcategory):
        """특정 MB Type과 SubCategory의 Material 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'mb_material' 
                  AND parent_component = ? AND sub_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (mb_type, subcategory))
            
            materials = cursor.fetchall()
            conn.close()
            
            return [m[0] for m in materials]
            
        except Exception as e:
            print(f"MB Material 조회 오류: {e}")
            # 기본값
            if mb_type == "HEATING":
                return ['CERAMIC', 'METAL', 'SILICON']
            else:
                return ['FIBER', 'FOAM', 'CERAMIC']
    
    def get_mb_sizes(self, mb_type, subcategory, material):
        """특정 MB Type, SubCategory, Material의 Size 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            parent_key = f"{mb_type}-{subcategory}-{material}"
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'mb_size' 
                  AND parent_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (parent_key,))
            
            sizes = cursor.fetchall()
            conn.close()
            
            return [s[0] for s in sizes]
            
        except Exception as e:
            print(f"MB Size 조회 오류: {e}")
            # 기본값
            if mb_type == "HEATING":
                return ['100W', '500W', '1KW', '5KW', '10KW']
            else:
                return ['10MM', '20MM', '50MM', '100MM']

    # ========== SERVICE 자동 제품 생성 (HR과 동일한 방식) ==========
    
    def create_service_product_for_spec(self, service_type, category, detail, spec):
        """새로운 SERVICE Spec에 대해 자동으로 제품 생성 (HR 사이즈와 동일한 방식)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            master_manager = SQLiteMasterProductManager()
            
            # SERVICE 제품 코드 생성: SERVICE-{Type}-{Category}-{Detail}-{Spec}
            # Type 코드 변환 (INSTALLATION -> INS, MAINTENANCE -> MNT)
            type_code = "INS" if service_type == "INSTALLATION" else "MNT" if service_type == "MAINTENANCE" else "RPR" if service_type == "REPAIR" else service_type[:3].upper()
            
            product_code = f"SERVICE-{type_code}-{category}-{detail}-{spec}"
            
            # 제품명 생성
            product_name = f"SERVICE {service_type} {category} {detail} {spec}"
            product_name_en = f"SERVICE {service_type} {category} {detail} {spec}"
            
            # 제품 데이터 준비
            product_data = {
                'product_code': product_code,
                'product_name': product_name,
                'product_name_en': product_name_en,
                'product_name_vi': product_name_en,  # 영어와 동일
                'category_name': 'SERVICE',
                'subcategory_name': service_type,
                'specifications': f"{spec},{detail},{category},{service_type}",
                'description': f"SERVICE {service_type} {category} {detail} {spec} 서비스",
                'unit': 'SERVICE',
                'status': 'active'
            }
            
            # 제품 추가 (중복 체크는 SQLiteMasterProductManager에서 처리)
            result = master_manager.add_master_product(product_data)
            if result:
                print(f"SERVICE 제품 생성: {product_code} - {product_name}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"SERVICE 자동 제품 생성 오류: {e}")
            return False
    
    def get_service_types(self):
        """SERVICE Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'service_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"SERVICE Type 조회 오류: {e}")
            return ['INSTALLATION', 'MAINTENANCE', 'REPAIR', 'TRAINING']  # 기본값
    
    def get_service_categories(self, service_type):
        """특정 SERVICE Type의 Category 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'service_category' 
                  AND parent_component = ? AND is_active = 1 
                ORDER BY display_order
            ''', (service_type,))
            
            categories = cursor.fetchall()
            conn.close()
            
            return [cat[0] for cat in categories]
            
        except Exception as e:
            print(f"SERVICE Category 조회 오류: {e}")
            # 기본값
            return ['HR', 'HRC', 'MB', 'ROBOT', 'GENERAL']
    
    def get_service_details(self, service_type, category):
        """특정 SERVICE Type과 Category의 Detail 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'service_detail' 
                  AND parent_component = ? AND sub_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (service_type, category))
            
            details = cursor.fetchall()
            conn.close()
            
            return [det[0] for det in details]
            
        except Exception as e:
            print(f"SERVICE Detail 조회 오류: {e}")
            # 기본값
            if service_type == "INSTALLATION":
                return ['SETUP', 'CONFIG', 'TEST']
            elif service_type == "MAINTENANCE":
                return ['CLEAN', 'CHECK', 'REPLACE']
            else:
                return ['ONSITE', 'REMOTE', 'SUPPORT']
    
    def get_service_specs(self, service_type, category, detail):
        """특정 SERVICE Type, Category, Detail의 Spec 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            parent_key = f"{service_type}-{category}-{detail}"
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'service_spec' 
                  AND parent_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (parent_key,))
            
            specs = cursor.fetchall()
            conn.close()
            
            return [spec[0] for spec in specs]
            
        except Exception as e:
            print(f"SERVICE Spec 조회 오류: {e}")
            # 기본값
            return ['BASIC', 'STANDARD', 'PREMIUM']

    # ========== SPARE 자동 제품 생성 (HR과 동일한 방식) ==========
    
    def create_spare_product_for_spec(self, spare_type, subcategory, detail, spec):
        """새로운 SPARE Spec에 대해 자동으로 제품 생성 (HR 사이즈와 동일한 방식)"""
        try:
            from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
            master_manager = SQLiteMasterProductManager()
            
            # SPARE 제품 코드 생성: SPARE-{Type}-{SubCategory}-{Detail}-{Spec}
            # Type 코드 변환 (ELECTRONIC -> ELT, MECHANICAL -> MCH)
            type_code = "ELT" if spare_type == "ELECTRONIC" else "MCH" if spare_type == "MECHANICAL" else "CON" if spare_type == "CONSUMABLE" else spare_type[:3].upper()
            
            product_code = f"SPARE-{type_code}-{subcategory}-{detail}-{spec}"
            
            # 제품명 생성
            product_name = f"SPARE {spare_type} {subcategory} {detail} {spec}"
            product_name_en = f"SPARE {spare_type} {subcategory} {detail} {spec}"
            
            # 제품 데이터 준비
            product_data = {
                'product_code': product_code,
                'product_name': product_name,
                'product_name_en': product_name_en,
                'product_name_vi': product_name_en,  # 영어와 동일
                'category_name': 'SPARE',
                'subcategory_name': spare_type,
                'specifications': f"{spec},{detail},{subcategory},{spare_type}",
                'description': f"SPARE {spare_type} {subcategory} {detail} {spec} 부품",
                'unit': 'EA',
                'status': 'active'
            }
            
            # 제품 추가 (중복 체크는 SQLiteMasterProductManager에서 처리)
            result = master_manager.add_master_product(product_data)
            if result:
                print(f"SPARE 제품 생성: {product_code} - {product_name}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"SPARE 자동 제품 생성 오류: {e}")
            return False
    
    def get_spare_types(self):
        """SPARE Type 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'spare_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"SPARE Type 조회 오류: {e}")
            return ['ELECTRONIC', 'MECHANICAL', 'CONSUMABLE']  # 기본값
    
    def get_spare_subcategories(self, spare_type):
        """특정 SPARE Type의 SubCategory 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'spare_subcategory' 
                  AND parent_component = ? AND is_active = 1 
                ORDER BY display_order
            ''', (spare_type,))
            
            subcategories = cursor.fetchall()
            conn.close()
            
            return [sc[0] for sc in subcategories]
            
        except Exception as e:
            print(f"SPARE SubCategory 조회 오류: {e}")
            # 기본값
            if spare_type == "ELECTRONIC":
                return ['SENSOR', 'BOARD', 'CABLE']
            elif spare_type == "MECHANICAL":
                return ['BEARING', 'GEAR', 'BELT']
            else:
                return ['FILTER', 'SEAL', 'OIL']
    
    def get_spare_details(self, spare_type, subcategory):
        """특정 SPARE Type과 SubCategory의 Detail 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'spare_detail' 
                  AND parent_component = ? AND sub_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (spare_type, subcategory))
            
            details = cursor.fetchall()
            conn.close()
            
            return [det[0] for det in details]
            
        except Exception as e:
            print(f"SPARE Detail 조회 오류: {e}")
            # 기본값
            return ['OEM', 'COMPATIBLE', 'AFTERMARKET']
    
    def get_spare_specs(self, spare_type, subcategory, detail):
        """특정 SPARE Type, SubCategory, Detail의 Spec 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            parent_key = f"{spare_type}-{subcategory}-{detail}"
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'spare_spec' 
                  AND parent_component = ? 
                  AND is_active = 1 
                ORDER BY display_order
            ''', (parent_key,))
            
            specs = cursor.fetchall()
            conn.close()
            
            return [spec[0] for spec in specs]
            
        except Exception as e:
            print(f"SPARE Spec 조회 오류: {e}")
            # 기본값
            return ['STD', 'PREMIUM', 'ECONOMY']
    
    def get_hrc_models(self, hrc_category=None):
        """HRC 모델 목록 조회 (호환성 유지)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if hrc_category:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_model' AND parent_component = ? AND is_active = 1 
                    ORDER BY display_order
                ''', (hrc_category,))
            else:
                cursor.execute('''
                    SELECT component_key, component_name, component_name_en, component_name_vi 
                    FROM hr_product_components 
                    WHERE component_type = 'hrc_model' AND is_active = 1 
                    ORDER BY display_order
                ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC 모델 조회 오류: {e}")
            if hrc_category == "TEMP":
                return ['YC60', 'SNT900']
            elif hrc_category == "TIMER":
                return ['YC60T', 'MDS08AT', 'MDS08BT']
            else:
                return ['YC60', 'SNT900', 'YC60T', 'MDS08AT', 'MDS08BT']
    
    def get_hrc_zones(self, hrc_category=None):
        """HRC 존 번호 목록 조회 (HRCT, HRCS 공통)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'hrc_zone' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"HRC 존 조회 오류: {e}")
            return ['1', '4', '6', '8', '12', '18', '24', '30', '32', '36', '40', '42', '48', 'Special']
    
    # ========== SERVICE 제품 코드 구성 요소 관리 ==========
    
    def get_service_types(self):
        """SERVICE 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'service_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"SERVICE 타입 조회 오류: {e}")
            return ['INSTALLATION', 'MAINTENANCE', 'REPAIR', 'TRAINING', 'DESIGN']
    
    def get_service_fields(self):
        """SERVICE 적용 분야 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'service_field' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"SERVICE 분야 조회 오류: {e}")
            return ['HR', 'HRC', 'MB', 'GENERAL']
    
    # ========== SPARE 제품 코드 구성 요소 관리 ==========
    
    def get_spare_types(self):
        """SPARE 부품 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'spare_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"SPARE 타입 조회 오류: {e}")
            return ['Heater', 'Thermo Couple', 'Gate Bush', 'Cylinder-ORing Set', 
                   'Cylinder-Set', 'Valve Pin', 'Tip', 'Spring', 'Nozzle', 'Manifold']
    
    # ========== ROBOT 제품 코드 구성 요소 관리 ==========
    
    def get_robot_types(self):
        """ROBOT 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'robot_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"ROBOT 타입 조회 오류: {e}")
            return ['INDUSTRIAL', 'COLLABORATIVE']
    
    def get_robot_applications(self):
        """ROBOT 애플리케이션 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'robot_application' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"ROBOT 애플리케이션 조회 오류: {e}")
            return ['INJECTION', 'ASSEMBLY', 'WELDING', 'PAINTING', 'MATERIAL_HANDLING']
    
    def get_robot_payloads(self):
        """ROBOT 페이로드 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'robot_payload' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"ROBOT 페이로드 조회 오류: {e}")
            return ['5', '10', '20', '50', '100', '200']
    
    def get_robot_reaches(self):
        """ROBOT 도달거리 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'robot_reach' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"ROBOT 도달거리 조회 오류: {e}")
            return ['500', '700', '900', '1200', '1500', '2000']
    
    def get_robot_axes(self):
        """ROBOT 축 수 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'robot_axes' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"ROBOT 축 수 조회 오류: {e}")
            return ['4', '5', '6', '7']
    
    # ========== MB 제품 코드 구성 요소 관리 ==========
    
    def get_mb_types(self):
        """MB 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key, component_name, component_name_en, component_name_vi 
                FROM hr_product_components 
                WHERE component_type = 'mb_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components]
            
        except Exception as e:
            print(f"MB 타입 조회 오류: {e}")
            return ['Standard', 'Custom', 'High-Temp']
    
    def get_mb_materials(self):
        """MB 재질 목록 조회 - HR 방식과 동일 (호환성 유지)"""
        return self.get_hr_components_list('mb_material')
    
    def get_hr_components_for_management(self, component_type, parent_component=None):
        """HR 구성 요소 관리용 상세 정보 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if parent_component:
                cursor.execute('''
                    SELECT component_id, component_type, parent_component, component_key, 
                           component_name, component_name_en, component_name_vi, 
                           display_order, is_active, description, created_date, updated_date
                    FROM hr_product_components 
                    WHERE component_type = ? AND parent_component = ?
                    ORDER BY display_order, component_key
                ''', (component_type, parent_component))
            else:
                cursor.execute('''
                    SELECT component_id, component_type, parent_component, component_key, 
                           component_name, component_name_en, component_name_vi, 
                           display_order, is_active, description, created_date, updated_date
                    FROM hr_product_components 
                    WHERE component_type = ?
                    ORDER BY display_order, component_key
                ''', (component_type,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            print(f"{component_type} 관리용 조회 오류: {e}")
            return []
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"HR 구성 요소 삭제 오류: {e}")
            return False
    

    
    def get_sub_categories(self, parent_category):
        """특정 메인 카테고리의 서브 카테고리 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_name
                FROM product_category_settings 
                WHERE category_type = 'sub_category' AND parent_category = ? AND is_active = 1 
                ORDER BY display_order
            ''', (parent_category,))
            
            categories = cursor.fetchall()
            conn.close()
            
            return [cat[0] for cat in categories]
            
        except Exception as e:
            print(f"서브 카테고리 조회 오류: {e}")
            # 폴백값
            if parent_category == 'HR':
                return ['Valve', 'Open']
            elif parent_category == 'HRC':
                return ['HRCT', 'HRCS', 'MTC']
            elif parent_category == 'MB':
                return ['2P', '3P', 'HR']
            return []
    
    def get_mb_materials(self):
        """MB 재질 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_name
                FROM product_category_settings 
                WHERE category_type = 'mb_material' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            materials = cursor.fetchall()
            conn.close()
            
            return [mat[0] for mat in materials]
            
        except Exception as e:
            print(f"MB 재질 조회 오류: {e}")
            # 폴백값
            return ['SS400', 'S50C', 'SKD61', 'NAK80', 'P20', 'SCM440', 'FC300', 'A5052', 'STAVAX', 'HPM38']
    
    def get_service_types(self):
        """서비스 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_name
                FROM product_category_settings 
                WHERE category_type = 'service_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"서비스 타입 조회 오류: {e}")
            return ['DESIGN', 'INSTALL', 'REPAIR', 'MAINTAIN']
    
    def get_spare_types(self):
        """예비부품 타입 목록 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_name
                FROM product_category_settings 
                WHERE category_type = 'spare_type' AND is_active = 1 
                ORDER BY display_order
            ''')
            
            types = cursor.fetchall()
            conn.close()
            
            return [t[0] for t in types]
            
        except Exception as e:
            print(f"예비부품 타입 조회 오류: {e}")
            return ['HEATER', 'SENSOR', 'NOZZLE', 'VALVE', 'CONTROL']
    
    def add_category(self, category_type, parent_category, key, name, name_en=None, name_vi=None, description=None):
        """새 카테고리 추가"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 다음 표시 순서 계산
            cursor.execute('''
                SELECT COALESCE(MAX(display_order), 0) + 1 
                FROM product_category_settings 
                WHERE category_type = ? AND parent_category = ?
            ''', (category_type, parent_category))
            
            next_order = cursor.fetchone()[0]
            
            # 새 ID 생성
            setting_id = str(uuid.uuid4())[:8].upper()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO product_category_settings 
                (setting_id, category_type, parent_category, category_key, category_name, 
                 category_name_en, category_name_vi, display_order, is_active, description,
                 created_date, updated_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'admin')
            ''', (setting_id, category_type, parent_category, key, name, 
                  name_en, name_vi, next_order, description, current_time, current_time))
            
            conn.commit()
            conn.close()
            
            return True, setting_id
            
        except Exception as e:
            print(f"카테고리 추가 오류: {e}")
            return False, str(e)
    
    def update_category(self, setting_id, name, name_en=None, name_vi=None, description=None):
        """카테고리 수정"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE product_category_settings 
                SET category_name = ?, category_name_en = ?, category_name_vi = ?, 
                    description = ?, updated_date = ?
                WHERE setting_id = ?
            ''', (name, name_en, name_vi, description, current_time, setting_id))
            
            conn.commit()
            conn.close()
            
            return True, "카테고리 수정 완료"
            
        except Exception as e:
            print(f"카테고리 수정 오류: {e}")
            return False, str(e)
    
    def delete_category(self, setting_id):
        """카테고리 삭제 (사용 중인 경우 비활성화)"""
        try:
            # 사용 중인지 확인
            usage_count = self.get_category_usage_count(setting_id)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if usage_count > 0:
                # 사용 중이면 비활성화
                cursor.execute('''
                    UPDATE product_category_settings 
                    SET is_active = 0, updated_date = ?
                    WHERE setting_id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), setting_id))
                message = f"카테고리가 비활성화되었습니다. ({usage_count}개 제품에서 사용 중)"
            else:
                # 사용하지 않으면 완전 삭제
                cursor.execute('DELETE FROM product_category_settings WHERE setting_id = ?', (setting_id,))
                message = "카테고리가 삭제되었습니다."
            
            conn.commit()
            conn.close()
            
            return True, message
            
        except Exception as e:
            print(f"카테고리 삭제 오류: {e}")
            return False, str(e)
    
    def get_category_usage_count(self, setting_id):
        """특정 카테고리를 사용하는 제품 수 조회"""
        try:
            # 카테고리 정보 조회
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_key, category_type, parent_category 
                FROM product_category_settings 
                WHERE setting_id = ?
            ''', (setting_id,))
            
            result = cursor.fetchone()
            if not result:
                return 0
            
            category_key, category_type, parent_category = result
            
            # 제품 테이블에서 사용 횟수 확인
            if category_type == 'main_category':
                cursor.execute('SELECT COUNT(*) FROM products WHERE main_category = ?', (category_key,))
            elif category_type == 'sub_category':
                if parent_category == 'HR':
                    cursor.execute('SELECT COUNT(*) FROM products WHERE sub_category_hr = ?', (category_key,))
                elif parent_category == 'HRC':
                    cursor.execute('SELECT COUNT(*) FROM products WHERE sub_category_hrc = ?', (category_key,))
                elif parent_category == 'MB':
                    cursor.execute('SELECT COUNT(*) FROM products WHERE sub_category_mb = ?', (category_key,))
                else:
                    return 0
            elif category_type == 'mb_material':
                cursor.execute('SELECT COUNT(*) FROM products WHERE sub_category_mb_material = ?', (category_key,))
            else:
                return 0
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"카테고리 사용 횟수 조회 오류: {e}")
            return 0
    
    def get_all_categories_with_info(self, category_type=None):
        """카테고리 정보와 사용 현황을 포함한 전체 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if category_type:
                cursor.execute('''
                    SELECT * FROM product_category_settings 
                    WHERE category_type = ? 
                    ORDER BY display_order
                ''', (category_type,))
            else:
                cursor.execute('''
                    SELECT * FROM product_category_settings 
                    ORDER BY category_type, display_order
                ''')
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            categories = []
            for row in rows:
                category_dict = dict(zip(columns, row))
                # 사용 횟수 추가
                category_dict['usage_count'] = self.get_category_usage_count(category_dict['setting_id'])
                categories.append(category_dict)
            
            conn.close()
            
            return categories
            
        except Exception as e:
            print(f"카테고리 정보 조회 오류: {e}")
            return []
    
    def get_mb_subcategories(self, mb_type):
        """특정 MB Type의 서브 카테고리 조회 - HRC와 동일한 방식"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = 'mb_sub_category' 
                AND parent_component = ? 
                AND is_active = 1 
                ORDER BY display_order, component_key
            ''', (mb_type,))
            
            subcategories = cursor.fetchall()
            conn.close()
            
            return [sc[0] for sc in subcategories] if subcategories else []
            
        except Exception as e:
            print(f"MB 서브 카테고리 조회 오류: {e}")
            return []
    
    def get_hr_components_list(self, component_type):
        """HR 구성 요소 목록 조회 (재사용 가능한 범용 메서드)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT component_key
                FROM hr_product_components 
                WHERE component_type = ? AND is_active = 1 
                ORDER BY display_order, component_key
            ''', (component_type,))
            
            components = cursor.fetchall()
            conn.close()
            
            return [comp[0] for comp in components] if components else []
            
        except Exception as e:
            print(f"{component_type} 조회 오류: {e}")
            return []
    
    def get_mb_materials(self):
        """MB 재질 목록 조회 - HR 방식과 동일 (호환성 유지)"""
        return self.get_hr_components_list('mb_material')