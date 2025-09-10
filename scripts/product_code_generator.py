import pandas as pd
import re
from datetime import datetime

class ProductCodeGenerator:
    """
    제품 코드 자동 생성 시스템
    기존 제품 코드 패턴을 분석하여 새로운 코드를 생성합니다.
    """
    
    def __init__(self, master_product_manager):
        self.master_product_manager = master_product_manager
        self.code_patterns = {
            'HR': {
                'pattern': 'YMV-{type}-{variant}-{size}-{sub_size}',
                'types': ['ST', 'CP', 'SC'],
                'variants': ['MAE', 'MCC', 'MAA', 'VL'],
                'sizes': ['20', '25', '35', '45', '60'],
                'sub_sizes': ['xx', '1.2', '1.5', '2.0', '3.0', '4.0', '5.0']
            },
            'HRC': {
                'pattern': 'YMV-HRC-{category}-{model}-{zone}',
                'categories': ['Temp', 'Timer'],
                'temp_models': ['YC60', 'SNT900'],
                'timer_models': ['YC60T', 'SNT900', 'MMDS08AT', 'MDS08BT'],
                'zones': ['01', '04', '05', '06', '07', '08', '09', '10', '11', '12', 'Special']
            },
            'MB': {
                'pattern': 'MB-{type}-{material}-{size}',
                'types': ['2P', '3P', 'HR'],
                'materials': ['SS400', 'S50C', 'SKD61', 'NAK80', 'P20'],
                'sizes': ['20', '25', '35', '45', '60']
            },
            'SERVICE': {
                'pattern': 'SV-{type}-{category}',
                'types': ['DESIGN', 'INSTALL', 'REPAIR', 'MAINTAIN'],
                'categories': ['HR', 'MB', 'HRC', 'GENERAL']
            },
            'SPARE': {
                'pattern': 'SP-{category}-{type}-{size}',
                'categories': ['HR', 'MB', 'HRC'],
                'types': ['HEATER', 'SENSOR', 'NOZZLE', 'VALVE', 'CONTROL'],
                'sizes': ['S', 'M', 'L', 'XL']
            }
        }
    
    def analyze_existing_codes(self, category):
        """기존 제품 코드를 분석하여 사용된 패턴을 확인합니다."""
        try:
            products = self.master_product_manager.get_all_products()
            if products is None or len(products) == 0:
                return []
            
            # 해당 카테고리의 제품 코드만 필터링
            category_products = products[products['main_category'] == category]
            existing_codes = category_products['product_code'].tolist()
            
            return existing_codes
        except Exception as e:
            print(f"기존 코드 분석 오류: {str(e)}")
            return []
    
    def generate_hr_code(self, product_type, variant, size_primary, size_secondary):
        """HR 제품 코드 생성 (YMV-ST-MAE-20-xx)"""
        # Single 제품의 경우 특별 처리
        if "Single" in product_type:
            if "Valve" in product_type:
                base_code = f"YMV-SV-{variant}-{size_primary}-{size_secondary}"
            else:  # Single Open
                base_code = f"YMV-SO-{variant}-{size_primary}-{size_secondary}"
        else:
            # 기본 코드 패턴
            base_code = f"YMV-{product_type}-{variant}-{size_primary}-{size_secondary}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('HR')
        if base_code in existing_codes:
            # 중복인 경우 접미사 추가
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def generate_hr_code_v2(self, system_type, product_type, size):
        """실제 데이터 패턴 기반 HR 제품 코드 생성"""
        # 실제 이미지 데이터 기반 코드 생성
        if system_type == "Valve":
            if product_type == "SI":  # Single Valve
                base_code = f"HR-Valve-SI-Single Valve-{size}"
            else:
                category4_mapping = {
                    "ST": "Standard",
                    "CP": "Cosmetic & Packaging",
                    "PET": "PET", 
                    "SE": "Super Engineering"
                }
                category4 = category4_mapping.get(product_type, "Standard")
                base_code = f"HR-Valve-{product_type}-{category4}-{size}"
        else:  # Open
            if product_type in ["SIRS", "SIRL"]:  # Single Open
                base_code = f"HR-Open-{product_type}-Single Open-{size}"
            else:
                category4_mapping = {
                    "ST": "Standard",
                    "CP": "Cosmetic & Packaging"
                }
                category4 = category4_mapping.get(product_type, "Standard")
                base_code = f"HR-Open-{product_type}-{category4}-{size}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('HR')
        if base_code in existing_codes:
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def generate_hr_code_simple(self, system_type, product_type, category4, gate_type, size):
        """간단한 HR 제품 코드 생성 (자동 번호 없음)"""
        # HR-Valve-ST-Standard-MAE-20 형식으로 생성
        base_code = f"HR-{system_type}-{product_type}-{category4}-{gate_type}-{size}"
        return base_code
    
    def check_duplicate_code(self, product_code, category='HR'):
        """제품 코드 중복 확인"""
        existing_codes = self.analyze_existing_codes(category)
        return product_code in existing_codes
    
    def generate_hr_code_v3(self, system_type, product_type, gate_type, size):
        """게이트 타입 포함 HR 제품 코드 생성"""
        # 실제 이미지 데이터 기반 코드 생성 (게이트 타입 포함)
        if system_type == "Valve":
            if product_type == "SIV":  # Single Valve
                base_code = f"HR-Valve-SIV-Single Valve-{gate_type}-{size}"
            else:
                category4_mapping = {
                    "ST": "Standard",
                    "CP": "Cosmetic & Packaging",
                    "PET": "PET", 
                    "SE": "Super Engineering"
                }
                category4 = category4_mapping.get(product_type, "Standard")
                base_code = f"HR-Valve-{product_type}-{category4}-{gate_type}-{size}"
        else:  # Open
            if product_type == "SIO":  # Single Open
                base_code = f"HR-Open-SIO-Single Open-{gate_type}-{size}"
            else:
                category4_mapping = {
                    "ST": "Standard",
                    "CP": "Cosmetic & Packaging"
                }
                category4 = category4_mapping.get(product_type, "Standard")
                base_code = f"HR-Open-{product_type}-{category4}-{gate_type}-{size}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('HR')
        if base_code in existing_codes:
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def generate_hrc_code(self, category, model, zone):
        """HRC 제품 코드 생성 (HRC-TEMP-YC60-1 또는 HRC-TIMER-MDS08AT-8)"""
        # 기본 코드 패턴: HRC-{category}-{model}-{zone}
        base_code = f"HRC-{category}-{model}-{zone}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('HRC')
        if base_code in existing_codes:
            # 중복인 경우 리비전 코드 추가
            counter = 1
            while f"{base_code}-RV{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-RV{counter:02d}"
        
        return base_code
    
    def generate_mb_code(self, mb_type, material, size):
        """MB 제품 코드 생성 (MB-2P-SS400-20)"""
        base_code = f"MB-{mb_type}-{material}-{size}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('MB')
        if base_code in existing_codes:
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def generate_service_code(self, service_type, category):
        """SERVICE 제품 코드 생성 (SV-DESIGN-HR)"""
        base_code = f"SV-{service_type}-{category}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('SERVICE')
        if base_code in existing_codes:
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def generate_spare_code(self, spare_type, **kwargs):
        """SPARE 제품 코드 생성"""
        
        if spare_type == "Heater":
            # SP-HEATER-Ø{diameter}-L{length} 또는 SP-HEATER-CTG-Ø{diameter}-L{length}-{wattage}W
            diameter = kwargs.get('diameter', '')
            length = kwargs.get('length', '')
            heater_type = kwargs.get('heater_type', 'Standard')
            wattage = kwargs.get('wattage', '')
            
            if heater_type == "Cartridge heater":
                if wattage and wattage > 0:
                    base_code = f"SP-HEATER-CTG-Ø{diameter}-L{length}-{wattage}W"
                else:
                    base_code = f"SP-HEATER-CTG-Ø{diameter}-L{length}"
            else:
                if wattage and wattage > 0:
                    base_code = f"SP-HEATER-Ø{diameter}-L{length}-{wattage}W"
                else:
                    base_code = f"SP-HEATER-Ø{diameter}-L{length}"
            
        elif spare_type == "Thermo Couple":
            sub_type = kwargs.get('sub_type', '')
            diameter = kwargs.get('diameter', '')
            length = kwargs.get('length', '')
            tc_type = kwargs.get('tc_type', '')
            
            if sub_type == "N/Z":
                # SP-TC-NZ-Ø{diameter}-L{length}
                base_code = f"SP-TC-NZ-Ø{diameter}-L{length}"
            elif sub_type == "M/F":
                # SP-TC-MF-{type}-L{length} (K Type, J Type 지원)
                base_code = f"SP-TC-MF-{tc_type}-L{length}"
            else:
                base_code = f"SP-TC-{sub_type}"
                
        elif spare_type == "Gate Bush":
            sub_type = kwargs.get('sub_type', '')
            size = kwargs.get('size', '')
            
            if sub_type == "ST":
                # SP-GB-ST-{size}
                base_code = f"SP-GB-ST-{size}"
            elif sub_type == "Special":
                # SP-GB-SP-OR-{size} (O-Ring)
                base_code = f"SP-GB-SP-OR-{size}"
            else:
                base_code = f"SP-GB-{sub_type}-{size}"
                
        elif spare_type == "Cylinder-ORing Set":
            cylinder_type = kwargs.get('cylinder_type', '')
            # SP-CY-OR-{cylinder_type}
            base_code = f"SP-CY-OR-{cylinder_type}"
            
        elif spare_type == "Cylinder-Set":
            cylinder_type = kwargs.get('cylinder_type', '')
            # SP-CY-SET-{cylinder_type}
            base_code = f"SP-CY-SET-{cylinder_type}"
            
        elif spare_type == "Valve Pin":
            size = kwargs.get('size', '')
            # SP-VP-{size}
            base_code = f"SP-VP-{size}"
            
        elif spare_type == "Tip":
            tip_config = kwargs.get('tip_config', '')
            # SP-TIP-{System}-{ProductType}-{GateType}-{Size} (예: SP-TIP-Valve-ST-MAE-20)
            base_code = f"SP-TIP-{tip_config}"
            
        else:
            # 기본 형식
            base_code = f"SP-{spare_type.upper().replace(' ', '')}"
        
        # 중복 확인
        existing_codes = self.analyze_existing_codes('SPARE')
        if base_code in existing_codes:
            counter = 1
            while f"{base_code}-{counter:02d}" in existing_codes:
                counter += 1
            return f"{base_code}-{counter:02d}"
        
        return base_code
    
    def get_available_options(self, category):
        """카테고리별 사용 가능한 옵션 반환"""
        return self.code_patterns.get(category, {})
    
    def validate_code_format(self, code, category):
        """제품 코드 형식 검증"""
        patterns = {
            'HR': r'^YMV-[A-Z]{2,3}-[A-Z]{2,3}-\d{2}-[x\d\.]+',
            'HRC': r'^YMV-HRC-[A-Z]{2,3}-\d{2}',
            'MB': r'^MB-[A-Z0-9]{2,3}-[A-Z0-9]{3,6}-\d{2}',
            'SERVICE': r'^SV-[A-Z]{4,8}-[A-Z]{2,7}',
            'SPARE': r'^SP-[A-Z]{2,3}-[A-Z]{4,7}-[A-Z]{1,2}'
        }
        
        pattern = patterns.get(category)
        if not pattern:
            return False
        
        return bool(re.match(pattern, code))
    
    def suggest_next_codes(self, category, count=5):
        """다음 사용 가능한 코드 제안"""
        existing_codes = self.analyze_existing_codes(category)
        suggestions = []
        
        if category == 'HR':
            # HR 제품의 다음 코드 제안
            for product_type in ['ST', 'CP']:
                for variant in ['MAE', 'MCC']:
                    for size in ['20', '25']:
                        for sub_size in ['xx', '1.2']:
                            code = self.generate_hr_code(product_type, variant, size, sub_size)
                            if code not in existing_codes:
                                suggestions.append(code)
                                if len(suggestions) >= count:
                                    return suggestions
        
        elif category == 'HRC':
            # HRC 제품의 다음 코드 제안
            for hrc_type in ['CT', 'CS']:
                for size in ['20', '25', '35']:
                    code = self.generate_hrc_code(hrc_type, size)
                    if code not in existing_codes:
                        suggestions.append(code)
                        if len(suggestions) >= count:
                            return suggestions
        
        return suggestions[:count]