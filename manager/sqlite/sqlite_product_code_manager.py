"""
SQLite 제품 코드 관리자 - 제품 코드 체계 관리
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

class SQLiteProductCodeManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 제품 코드 체계 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_code_rules (
                        rule_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        code_prefix TEXT NOT NULL,
                        code_pattern TEXT NOT NULL,
                        code_length INTEGER DEFAULT 8,
                        description TEXT,
                        description_en TEXT,
                        description_vi TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 제품 코드 시퀀스 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_code_sequences (
                        sequence_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        prefix TEXT NOT NULL,
                        last_number INTEGER DEFAULT 0,
                        current_year INTEGER,
                        current_month INTEGER,
                        reset_frequency TEXT DEFAULT 'never',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, subcategory, prefix)
                    )
                ''')
                
                # 생성된 제품 코드 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS generated_product_codes (
                        code_id TEXT PRIMARY KEY,
                        product_code TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        prefix TEXT,
                        sequence_number INTEGER,
                        product_id TEXT,
                        product_name TEXT,
                        status TEXT DEFAULT 'active',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT
                    )
                ''')
                
                # 기본 코드 규칙 추가
                default_rules = [
                    ('HRC', 'HRC제품', 'HRC', 'HRC{YYYY}{MM}{000}', 11, 'HRC 제품 코드 규칙', 'HRC Product Code Rule', 'Quy tắc mã sản phẩm HRC'),
                    ('HEAT', '열처리', 'HEAT', 'HEAT{YY}{000}', 8, '열처리 장비 코드', 'Heat Treatment Code', 'Mã thiết bị xử lý nhiệt'),
                    ('ROBOT', '로봇', 'ROBOT', 'ROB{YY}{000}', 8, '로봇 장비 코드', 'Robot Equipment Code', 'Mã thiết bị robot'),
                    ('SPARE', '부품', 'SPARE', 'SP{YY}{0000}', 8, '부품 코드', 'Spare Parts Code', 'Mã phụ tùng'),
                    ('TOOL', '공구', 'TOOL', 'TL{YY}{000}', 8, '공구 코드', 'Tool Code', 'Mã công cụ'),
                    ('MAT', '재료', 'MAT', 'MT{YY}{000}', 8, '재료 코드', 'Material Code', 'Mã nguyên liệu'),
                    ('SVC', '서비스', 'SVC', 'SV{YY}{000}', 8, '서비스 코드', 'Service Code', 'Mã dịch vụ')
                ]
                
                for rule in default_rules:
                    rule_id = f"RULE_{rule[0]}"
                    cursor.execute('''
                        INSERT OR IGNORE INTO product_code_rules 
                        (rule_id, category, code_prefix, code_pattern, code_length, 
                         description, description_en, description_vi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (rule_id, rule[1], rule[2], rule[3], rule[4], rule[5], rule[6], rule[7]))
                
                conn.commit()
                logger.info("제품 코드 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_code_rules(self, category=None, is_active=True):
        """제품 코드 규칙 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM product_code_rules WHERE 1=1"
                params = []
                
                if is_active is not None:
                    query += " AND is_active = ?"
                    params.append(1 if is_active else 0)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY category, code_prefix"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"제품 코드 규칙 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_code_rule(self, rule_data):
        """제품 코드 규칙 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['category', 'code_prefix', 'code_pattern']
                for field in required_fields:
                    if field not in rule_data or not rule_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                rule_id = f"RULE_{rule_data['category'].upper()}_{rule_data['code_prefix']}"
                
                rule_record = {
                    'rule_id': rule_id,
                    'category': rule_data['category'],
                    'subcategory': rule_data.get('subcategory', ''),
                    'code_prefix': rule_data['code_prefix'],
                    'code_pattern': rule_data['code_pattern'],
                    'code_length': rule_data.get('code_length', 8),
                    'description': rule_data.get('description', ''),
                    'description_en': rule_data.get('description_en', ''),
                    'description_vi': rule_data.get('description_vi', ''),
                    'is_active': rule_data.get('is_active', 1),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO product_code_rules (
                        rule_id, category, subcategory, code_prefix, code_pattern,
                        code_length, description, description_en, description_vi,
                        is_active, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(rule_record.values()))
                
                conn.commit()
                logger.info(f"제품 코드 규칙 추가 완료: {rule_id}")
                return True
                
        except Exception as e:
            logger.error(f"제품 코드 규칙 추가 실패: {str(e)}")
            return False

    def generate_product_code(self, category, subcategory=None, product_name='', created_by=''):
        """제품 코드 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 해당 카테고리의 코드 규칙 조회
                cursor.execute('''
                    SELECT code_prefix, code_pattern, code_length 
                    FROM product_code_rules 
                    WHERE category = ? AND is_active = 1
                    ORDER BY created_date DESC
                    LIMIT 1
                ''', (category,))
                
                rule_result = cursor.fetchone()
                if not rule_result:
                    logger.error(f"코드 규칙을 찾을 수 없음: {category}")
                    return None
                
                code_prefix, code_pattern, code_length = rule_result
                
                # 시퀀스 조회 및 업데이트
                sequence_id = f"SEQ_{category}_{code_prefix}"
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                cursor.execute('''
                    SELECT last_number, current_year, current_month, reset_frequency
                    FROM product_code_sequences 
                    WHERE category = ? AND prefix = ?
                ''', (category, code_prefix))
                
                seq_result = cursor.fetchone()
                
                if seq_result:
                    last_number, seq_year, seq_month, reset_frequency = seq_result
                    
                    # 재설정 조건 확인
                    if reset_frequency == 'yearly' and seq_year != current_year:
                        last_number = 0
                    elif reset_frequency == 'monthly' and (seq_year != current_year or seq_month != current_month):
                        last_number = 0
                    
                    next_number = last_number + 1
                    
                    # 시퀀스 업데이트
                    cursor.execute('''
                        UPDATE product_code_sequences 
                        SET last_number = ?, current_year = ?, current_month = ?, updated_date = ?
                        WHERE category = ? AND prefix = ?
                    ''', (next_number, current_year, current_month, datetime.now().isoformat(), category, code_prefix))
                else:
                    # 새 시퀀스 생성
                    next_number = 1
                    cursor.execute('''
                        INSERT INTO product_code_sequences 
                        (sequence_id, category, subcategory, prefix, last_number, 
                         current_year, current_month, reset_frequency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (sequence_id, category, subcategory or '', code_prefix, 
                          next_number, current_year, current_month, 'never'))
                
                # 코드 패턴 적용
                product_code = self._apply_code_pattern(code_pattern, {
                    'YYYY': str(current_year),
                    'YY': str(current_year)[-2:],
                    'MM': f"{current_month:02d}",
                    '000': f"{next_number:03d}",
                    '0000': f"{next_number:04d}",
                    '00000': f"{next_number:05d}"
                })
                
                # 생성된 코드 저장
                code_id = f"CODE_{product_code}"
                cursor.execute('''
                    INSERT INTO generated_product_codes 
                    (code_id, product_code, category, subcategory, prefix, 
                     sequence_number, product_name, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (code_id, product_code, category, subcategory or '', 
                      code_prefix, next_number, product_name, created_by))
                
                conn.commit()
                logger.info(f"제품 코드 생성 완료: {product_code}")
                return product_code
                
        except Exception as e:
            logger.error(f"제품 코드 생성 실패: {str(e)}")
            return None

    def _apply_code_pattern(self, pattern, replacements):
        """코드 패턴 적용"""
        result = pattern
        for placeholder, value in replacements.items():
            result = result.replace(f"{{{placeholder}}}", value)
        return result

    def validate_product_code(self, product_code, category=None):
        """제품 코드 유효성 검증"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 코드 확인
                cursor.execute("SELECT COUNT(*) FROM generated_product_codes WHERE product_code = ?", (product_code,))
                if cursor.fetchone()[0] > 0:
                    return {'valid': False, 'reason': '이미 사용 중인 코드'}
                
                # 카테고리별 규칙 확인
                if category:
                    cursor.execute('''
                        SELECT code_prefix, code_length 
                        FROM product_code_rules 
                        WHERE category = ? AND is_active = 1
                    ''', (category,))
                    
                    rule_result = cursor.fetchone()
                    if rule_result:
                        code_prefix, expected_length = rule_result
                        
                        if not product_code.startswith(code_prefix):
                            return {'valid': False, 'reason': f'코드는 {code_prefix}로 시작해야 함'}
                        
                        if len(product_code) != expected_length:
                            return {'valid': False, 'reason': f'코드 길이는 {expected_length}자여야 함'}
                
                return {'valid': True, 'reason': '유효한 코드'}
                
        except Exception as e:
            logger.error(f"제품 코드 검증 실패: {str(e)}")
            return {'valid': False, 'reason': '검증 중 오류 발생'}

    def get_generated_codes(self, category=None, status='active', limit=100):
        """생성된 제품 코드 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM generated_product_codes WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY created_date DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"생성된 제품 코드 조회 실패: {str(e)}")
            return pd.DataFrame()

    def assign_code_to_product(self, product_code, product_id, product_name, assigned_by=''):
        """제품에 코드 할당"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE generated_product_codes 
                    SET product_id = ?, product_name = ?, updated_date = ?
                    WHERE product_code = ?
                ''', (product_id, product_name, datetime.now().isoformat(), product_code))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"제품 코드 할당 완료: {product_code} -> {product_id}")
                    return True
                else:
                    logger.warning(f"할당할 제품 코드 없음: {product_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"제품 코드 할당 실패: {str(e)}")
            return False

    def get_code_statistics(self):
        """제품 코드 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        category,
                        prefix,
                        COUNT(*) as total_codes,
                        SUM(CASE WHEN product_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_codes,
                        SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as unassigned_codes,
                        MAX(sequence_number) as max_sequence
                    FROM generated_product_codes
                    GROUP BY category, prefix
                    ORDER BY category, prefix
                '''
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"제품 코드 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_all_codes(self):
        """모든 생성된 제품 코드 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        code_id,
                        product_code as full_code,
                        category,
                        subcategory,
                        prefix,
                        sequence_number,
                        product_id,
                        product_name,
                        status,
                        created_date,
                        created_by
                    FROM generated_product_codes 
                    WHERE status = 'active'
                    ORDER BY created_date DESC
                """
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"모든 제품 코드 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, rules_csv_path=None, codes_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 코드 규칙 데이터 마이그레이션
            if rules_csv_path is None:
                rules_csv_path = os.path.join("data", "product_code_rules.csv")
            
            if os.path.exists(rules_csv_path):
                df = pd.read_csv(rules_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        rule_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in rule_data.items():
                            if pd.isna(value):
                                if key in ['code_length', 'is_active']:
                                    rule_data[key] = 8 if key == 'code_length' else 1
                                else:
                                    rule_data[key] = ''
                        
                        self.add_code_rule(rule_data)
                    
                    logger.info(f"제품 코드 규칙 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 생성된 코드 데이터 마이그레이션
            if codes_csv_path is None:
                codes_csv_path = os.path.join("data", "generated_product_codes.csv")
            
            if os.path.exists(codes_csv_path):
                df = pd.read_csv(codes_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        for _, row in df.iterrows():
                            code_data = row.to_dict()
                            # NaN 값 처리
                            for key, value in code_data.items():
                                if pd.isna(value):
                                    if key == 'sequence_number':
                                        code_data[key] = 0
                                    else:
                                        code_data[key] = ''
                            
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO generated_product_codes
                                    (code_id, product_code, category, subcategory, prefix,
                                     sequence_number, product_id, product_name, status, created_by)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    code_data.get('code_id', f"CODE_{code_data.get('product_code', '')}"),
                                    code_data.get('product_code', ''),
                                    code_data.get('category', ''),
                                    code_data.get('subcategory', ''),
                                    code_data.get('prefix', ''),
                                    code_data.get('sequence_number', 0),
                                    code_data.get('product_id', ''),
                                    code_data.get('product_name', ''),
                                    code_data.get('status', 'active'),
                                    code_data.get('created_by', '')
                                ))
                            except sqlite3.IntegrityError:
                                # 중복 데이터 스킵
                                pass
                        
                        conn.commit()
                    
                    logger.info(f"생성된 제품 코드 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False