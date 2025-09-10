"""
SQLite 환율 관리자 - 환율 정보 관리, 실시간 환율 조회
CSV 기반에서 SQLite 기반으로 전환
"""

import sqlite3
import pandas as pd
import os
import json
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteExchangeRateManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self.api_key = os.getenv('OPEN_EXCHANGE_RATES_API_KEY', '')
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 환율 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_rates (
                        rate_id TEXT PRIMARY KEY,
                        base_currency TEXT NOT NULL,
                        target_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        rate_date TEXT NOT NULL,
                        source TEXT DEFAULT 'manual',
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(base_currency, target_currency, rate_date)
                    )
                ''')
                
                # 환율 히스토리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_rate_history (
                        history_id TEXT PRIMARY KEY,
                        base_currency TEXT NOT NULL,
                        target_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        rate_date TEXT NOT NULL,
                        source TEXT DEFAULT 'api',
                        high_rate REAL,
                        low_rate REAL,
                        change_rate REAL DEFAULT 0,
                        change_percentage REAL DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 분기별 기준 환율 테이블 (한국은행 기준)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quarterly_exchange_rates (
                        quarter_id TEXT PRIMARY KEY,
                        year INTEGER NOT NULL,
                        quarter INTEGER NOT NULL,
                        base_currency TEXT NOT NULL DEFAULT 'KRW',
                        target_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        source TEXT DEFAULT 'bok',
                        is_active INTEGER DEFAULT 1,
                        created_by TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(year, quarter, base_currency, target_currency)
                    )
                ''')
                
                # 연도별 관리 환율 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS yearly_management_rates (
                        management_rate_id TEXT PRIMARY KEY,
                        year INTEGER NOT NULL,
                        base_currency TEXT NOT NULL DEFAULT 'USD',
                        target_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(year, base_currency, target_currency)
                    )
                ''')
                
                # 통화 정보 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS currencies (
                        currency_code TEXT PRIMARY KEY,
                        currency_name TEXT NOT NULL,
                        currency_name_en TEXT,
                        currency_name_vi TEXT,
                        symbol TEXT,
                        decimal_places INTEGER DEFAULT 2,
                        is_base INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        country TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 기본 통화 정보 추가
                default_currencies = [
                    ('VND', '베트남 동', 'Vietnamese Dong', 'Đồng Việt Nam', '₫', 0, 1, 1, 'Vietnam'),
                    ('USD', '미국 달러', 'US Dollar', 'Đô la Mỹ', '$', 2, 0, 1, 'United States'),
                    ('KRW', '한국 원', 'Korean Won', 'Won Hàn Quốc', '₩', 0, 0, 1, 'South Korea'),
                    ('EUR', '유로', 'Euro', 'Euro', '€', 2, 0, 1, 'European Union'),
                    ('JPY', '일본 엔', 'Japanese Yen', 'Yên Nhật', '¥', 0, 0, 1, 'Japan'),
                    ('CNY', '중국 위안', 'Chinese Yuan', 'Nhân dân tệ', '¥', 2, 0, 1, 'China')
                ]
                
                cursor.executemany('''
                    INSERT OR IGNORE INTO currencies 
                    (currency_code, currency_name, currency_name_en, currency_name_vi, 
                     symbol, decimal_places, is_base, is_active, country)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', default_currencies)
                
                conn.commit()
                logger.info("환율 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def add_quarterly_rate(self, year, quarter, target_currency, rate, created_by='admin'):
        """분기별 기준 환율 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                quarter_id = f"Q{year}_{quarter}_{target_currency}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO quarterly_exchange_rates 
                    (quarter_id, year, quarter, target_currency, rate, created_by, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (quarter_id, year, quarter, target_currency, rate, created_by, 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                conn.commit()
                return True, f"분기별 환율이 성공적으로 저장되었습니다."
                
        except Exception as e:
            logger.error(f"분기별 환율 추가 실패: {str(e)}")
            return False, f"오류: {str(e)}"

    def get_quarterly_rates(self, year=None, quarter=None):
        """분기별 환율 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        qer.year,
                        qer.quarter,
                        qer.target_currency,
                        c.currency_name,
                        qer.rate,
                        qer.created_by,
                        qer.created_date,
                        qer.updated_date
                    FROM quarterly_exchange_rates qer
                    LEFT JOIN currencies c ON qer.target_currency = c.currency_code
                    WHERE qer.is_active = 1
                """
                params = []
                
                if year:
                    query += " AND qer.year = ?"
                    params.append(year)
                    
                if quarter:
                    query += " AND qer.quarter = ?"
                    params.append(quarter)
                    
                query += " ORDER BY qer.year DESC, qer.quarter DESC, qer.target_currency"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"분기별 환율 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_current_quarter_rate(self, target_currency):
        """현재 분기 환율 조회"""
        try:
            current_date = datetime.now()
            current_year = current_date.year
            current_quarter = (current_date.month - 1) // 3 + 1
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT rate FROM quarterly_exchange_rates 
                    WHERE year = ? AND quarter = ? AND target_currency = ? AND is_active = 1
                ''', (current_year, current_quarter, target_currency))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"현재 분기 환율 조회 실패: {str(e)}")
            return None

    def get_latest_rates(self):
        """최신 환율 정보를 가져옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        base_currency,
                        target_currency,
                        rate,
                        rate_date,
                        source
                    FROM exchange_rates
                    WHERE is_active = 1
                    ORDER BY rate_date DESC, created_date DESC
                """
                
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"최신 환율 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_exchange_rates(self, base_currency=None, target_currency=None, date=None, is_active=True):
        """환율 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM exchange_rates WHERE 1=1"
                params = []
                
                if is_active is not None:
                    query += " AND is_active = ?"
                    params.append(1 if is_active else 0)
                if base_currency:
                    query += " AND base_currency = ?"
                    params.append(base_currency)
                if target_currency:
                    query += " AND target_currency = ?"
                    params.append(target_currency)
                if date:
                    query += " AND rate_date = ?"
                    params.append(date)
                
                query += " ORDER BY rate_date DESC, created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"환율 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_exchange_rate(self, rate_data):
        """환율 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['base_currency', 'target_currency', 'rate', 'rate_date']
                for field in required_fields:
                    if field not in rate_data or rate_data[field] is None:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                rate_id = f"{rate_data['base_currency']}_{rate_data['target_currency']}_{rate_data['rate_date']}"
                
                rate_record = {
                    'rate_id': rate_id,
                    'base_currency': rate_data['base_currency'],
                    'target_currency': rate_data['target_currency'],
                    'rate': rate_data['rate'],
                    'rate_date': rate_data['rate_date'],
                    'source': rate_data.get('source', 'manual'),
                    'is_active': rate_data.get('is_active', 1),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO exchange_rates (
                        rate_id, base_currency, target_currency, rate, rate_date,
                        source, is_active, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(rate_record.values()))
                
                # 히스토리에도 추가
                history_id = f"HIST_{current_time}_{rate_data['base_currency']}_{rate_data['target_currency']}"
                cursor.execute('''
                    INSERT INTO exchange_rate_history (
                        history_id, base_currency, target_currency, rate, rate_date, source
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (history_id, rate_data['base_currency'], rate_data['target_currency'],
                      rate_data['rate'], rate_data['rate_date'], rate_data.get('source', 'manual')))
                
                conn.commit()
                logger.info(f"환율 추가 완료: {rate_data['base_currency']}/{rate_data['target_currency']} = {rate_data['rate']}")
                return True
                
        except Exception as e:
            logger.error(f"환율 추가 실패: {str(e)}")
            return False

    def get_latest_rate(self, base_currency, target_currency):
        """최신 환율 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM exchange_rates 
                    WHERE base_currency = ? AND target_currency = ? AND is_active = 1
                    ORDER BY rate_date DESC, created_date DESC
                    LIMIT 1
                '''
                df = pd.read_sql_query(query, conn, params=[base_currency, target_currency])
                
                if not df.empty:
                    return df.iloc[0]
                else:
                    # 역방향 환율 확인
                    query = '''
                        SELECT *, (1.0/rate) as reversed_rate FROM exchange_rates 
                        WHERE base_currency = ? AND target_currency = ? AND is_active = 1
                        ORDER BY rate_date DESC, created_date DESC
                        LIMIT 1
                    '''
                    df = pd.read_sql_query(query, conn, params=[target_currency, base_currency])
                    if not df.empty:
                        result = df.iloc[0].copy()
                        result['rate'] = result['reversed_rate']
                        result['base_currency'] = base_currency
                        result['target_currency'] = target_currency
                        return result
                
                return None
                
        except Exception as e:
            logger.error(f"최신 환율 조회 실패: {str(e)}")
            return None

    def convert_currency(self, amount, from_currency, to_currency, rate_date=None):
        """환율 변환"""
        try:
            if from_currency == to_currency:
                return amount
            
            # 지정된 날짜의 환율 조회
            if rate_date:
                with sqlite3.connect(self.db_path) as conn:
                    query = '''
                        SELECT rate FROM exchange_rates 
                        WHERE base_currency = ? AND target_currency = ? 
                            AND rate_date <= ? AND is_active = 1
                        ORDER BY rate_date DESC, created_date DESC
                        LIMIT 1
                    '''
                    cursor = conn.cursor()
                    cursor.execute(query, (from_currency, to_currency, rate_date))
                    result = cursor.fetchone()
                    
                    if result:
                        return amount * result[0]
                    else:
                        # 역방향 확인
                        cursor.execute(query, (to_currency, from_currency, rate_date))
                        result = cursor.fetchone()
                        if result:
                            return amount / result[0]
            
            # 최신 환율 사용
            rate_info = self.get_latest_rate(from_currency, to_currency)
            if rate_info is not None:
                return amount * rate_info['rate']
            
            logger.warning(f"환율 정보 없음: {from_currency} -> {to_currency}")
            return amount
            
        except Exception as e:
            logger.error(f"환율 변환 실패: {str(e)}")
            return amount

    def fetch_rates_from_api(self):
        """API로부터 환율 정보 가져오기"""
        try:
            if not self.api_key:
                logger.warning("환율 API 키가 설정되지 않음")
                return False
            
            url = f"https://openexchangerates.org/api/latest.json?app_id={self.api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                base_currency = data.get('base', 'USD')
                rates = data.get('rates', {})
                timestamp = data.get('timestamp', 0)
                rate_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                # VND 환율 추가
                if 'VND' in rates:
                    rate_data = {
                        'base_currency': base_currency,
                        'target_currency': 'VND',
                        'rate': rates['VND'],
                        'rate_date': rate_date,
                        'source': 'api'
                    }
                    self.add_exchange_rate(rate_data)
                
                # 기타 주요 통화 환율 추가
                major_currencies = ['KRW', 'EUR', 'JPY', 'CNY']
                for currency in major_currencies:
                    if currency in rates:
                        rate_data = {
                            'base_currency': base_currency,
                            'target_currency': currency,
                            'rate': rates[currency],
                            'rate_date': rate_date,
                            'source': 'api'
                        }
                        self.add_exchange_rate(rate_data)
                
                logger.info(f"API로부터 환율 정보 업데이트 완료: {rate_date}")
                return True
            else:
                logger.error(f"환율 API 호출 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"환율 API 호출 실패: {str(e)}")
            return False

    def get_currencies(self, is_active=True):
        """통화 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM currencies"
                params = []
                
                if is_active is not None:
                    query += " WHERE is_active = ?"
                    params.append(1 if is_active else 0)
                
                query += " ORDER BY is_base DESC, currency_code"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"통화 목록 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_rate_history(self, base_currency, target_currency, days=30):
        """환율 히스토리 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                query = '''
                    SELECT * FROM exchange_rate_history 
                    WHERE base_currency = ? AND target_currency = ? 
                        AND rate_date >= ?
                    ORDER BY rate_date DESC
                '''
                df = pd.read_sql_query(query, conn, params=[base_currency, target_currency, start_date])
                return df
                
        except Exception as e:
            logger.error(f"환율 히스토리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, rates_csv_path=None, currencies_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 환율 데이터 마이그레이션
            if rates_csv_path is None:
                rates_csv_path = os.path.join("data", "exchange_rates.csv")
            
            if os.path.exists(rates_csv_path):
                df = pd.read_csv(rates_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        rate_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in rate_data.items():
                            if pd.isna(value):
                                if key in ['rate', 'is_active']:
                                    rate_data[key] = 1 if key == 'rate' else 1
                                else:
                                    rate_data[key] = ''
                        
                        # CSV 구조에 맞게 필드 매핑
                        if 'currency_code' in rate_data and 'target_currency' not in rate_data:
                            rate_data['target_currency'] = rate_data['currency_code']
                        if 'base_currency' not in rate_data:
                            rate_data['base_currency'] = 'KRW'  # 기본값
                        
                        # 필수 필드 확인
                        if 'target_currency' in rate_data and rate_data['target_currency']:
                            self.add_exchange_rate(rate_data)
                        else:
                            logger.warning(f"필수 필드 누락으로 환율 데이터 스킵: {rate_data.get('rate_id', 'N/A')}")
                    
                    logger.info(f"환율 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 통화 정보 데이터 마이그레이션
            if currencies_csv_path is None:
                currencies_csv_path = os.path.join("data", "currencies.csv")
            
            if os.path.exists(currencies_csv_path):
                df = pd.read_csv(currencies_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        for _, row in df.iterrows():
                            currency_data = row.to_dict()
                            # NaN 값 처리
                            for key, value in currency_data.items():
                                if pd.isna(value):
                                    if key in ['decimal_places', 'is_base', 'is_active']:
                                        currency_data[key] = 0 if key == 'decimal_places' else 1
                                    else:
                                        currency_data[key] = ''
                            
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO currencies
                                    (currency_code, currency_name, currency_name_en, currency_name_vi,
                                     symbol, decimal_places, is_base, is_active, country)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    currency_data.get('currency_code', ''),
                                    currency_data.get('currency_name', ''),
                                    currency_data.get('currency_name_en', ''),
                                    currency_data.get('currency_name_vi', ''),
                                    currency_data.get('symbol', ''),
                                    currency_data.get('decimal_places', 2),
                                    currency_data.get('is_base', 0),
                                    currency_data.get('is_active', 1),
                                    currency_data.get('country', '')
                                ))
                            except sqlite3.IntegrityError:
                                # 중복 데이터 스킵
                                pass
                        
                        conn.commit()
                    
                    logger.info(f"통화 정보 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False

    # 연도별 관리 환율 관련 메서드들
    def add_yearly_management_rate(self, year, target_currency, rate, description=None, created_by='admin'):
        """연도별 관리 환율 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                management_rate_id = f"YMR_{year}_{target_currency}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO yearly_management_rates 
                    (management_rate_id, year, target_currency, rate, description, created_by, updated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (management_rate_id, year, target_currency, rate, description, created_by, 
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                conn.commit()
                return True, f"연도별 관리 환율이 성공적으로 저장되었습니다."
                
        except Exception as e:
            logger.error(f"연도별 관리 환율 추가 실패: {str(e)}")
            return False, f"오류: {str(e)}"

    def get_yearly_management_rates(self, year=None):
        """연도별 관리 환율 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        ymr.year,
                        ymr.base_currency,
                        ymr.target_currency,
                        ymr.rate,
                        ymr.description,
                        ymr.created_by,
                        ymr.created_date,
                        ymr.updated_date,
                        c.currency_name
                    FROM yearly_management_rates ymr
                    LEFT JOIN currencies c ON ymr.target_currency = c.currency_code
                    WHERE ymr.is_active = 1
                """
                params = []
                
                if year:
                    query += " AND ymr.year = ?"
                    params.append(year)
                
                query += " ORDER BY ymr.year DESC, ymr.target_currency"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"연도별 관리 환율 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_management_rate_by_year_currency(self, year, currency):
        """특정 연도/통화의 관리 환율 조회 (USD 기준으로 각 통화별 환율)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # USD → VND/CNY/KRW 등의 환율 조회
                if currency == "VND":
                    cursor.execute('''
                        SELECT rate FROM yearly_management_rates 
                        WHERE year = ? AND base_currency = 'USD' AND target_currency = 'VND' AND is_active = 1
                    ''', (year,))
                    result = cursor.fetchone()
                    return result[0] if result else None
                
                elif currency == "CNY":
                    cursor.execute('''
                        SELECT rate FROM yearly_management_rates 
                        WHERE year = ? AND base_currency = 'USD' AND target_currency = 'CNY' AND is_active = 1
                    ''', (year,))
                    result = cursor.fetchone()
                    return result[0] if result else None
                
                elif currency == "KRW":
                    cursor.execute('''
                        SELECT rate FROM yearly_management_rates 
                        WHERE year = ? AND base_currency = 'USD' AND target_currency = 'KRW' AND is_active = 1
                    ''', (year,))
                    result = cursor.fetchone()
                    return result[0] if result else None
                
                elif currency == "USD":
                    # USD → VND 환율을 반환 (USD가 선택된 경우)
                    cursor.execute('''
                        SELECT rate FROM yearly_management_rates 
                        WHERE year = ? AND base_currency = 'USD' AND target_currency = 'VND' AND is_active = 1
                    ''', (year,))
                    result = cursor.fetchone()
                    return result[0] if result else None
                
                else:
                    # 기타 통화는 USD 기준으로 조회
                    cursor.execute('''
                        SELECT rate FROM yearly_management_rates 
                        WHERE year = ? AND base_currency = 'USD' AND target_currency = ? AND is_active = 1
                    ''', (year, currency))
                    result = cursor.fetchone()
                    return result[0] if result else None
                
        except Exception as e:
            logger.error(f"관리 환율 조회 실패: {str(e)}")
            return None

    def update_yearly_management_rate(self, year, target_currency, rate, description=None, updated_by='admin'):
        """연도별 관리 환율 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE yearly_management_rates 
                    SET rate = ?, description = ?, created_by = ?, updated_date = ?
                    WHERE year = ? AND target_currency = ? AND is_active = 1
                ''', (rate, description, updated_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                      year, target_currency))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True, f"{year}년 {target_currency} 관리 환율이 수정되었습니다."
                else:
                    return False, "수정할 데이터를 찾을 수 없습니다."
                
        except Exception as e:
            logger.error(f"연도별 관리 환율 수정 실패: {str(e)}")
            return False, f"오류: {str(e)}"

    def delete_yearly_management_rate(self, year, target_currency):
        """연도별 관리 환율 삭제 (비활성화)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE yearly_management_rates 
                    SET is_active = 0, updated_date = ?
                    WHERE year = ? AND target_currency = ?
                ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), year, target_currency))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True, f"{year}년 {target_currency} 관리 환율이 삭제되었습니다."
                else:
                    return False, "삭제할 데이터를 찾을 수 없습니다."
                
        except Exception as e:
            logger.error(f"연도별 관리 환율 삭제 실패: {str(e)}")
            return False, f"오류: {str(e)}"

    def get_latest_management_rates(self):
        """최신 연도의 관리 환율 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 가장 최신 연도 찾기
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(year) FROM yearly_management_rates WHERE is_active = 1')
                result = cursor.fetchone()
                
                if result and result[0]:
                    latest_year = result[0]
                    return self.get_yearly_management_rates(latest_year)
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            logger.error(f"최신 관리 환율 조회 실패: {str(e)}")
            return pd.DataFrame()

    def bulk_insert_management_rates(self, year, rates_data, created_by='admin'):
        """연도별 관리 환율 대량 입력"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                success_count = 0
                
                for currency, rate in rates_data.items():
                    try:
                        management_rate_id = f"YMR_{year}_{currency}"
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO yearly_management_rates 
                            (management_rate_id, year, target_currency, rate, created_by, updated_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (management_rate_id, year, currency, rate, created_by, 
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        success_count += 1
                    except Exception as e:
                        logger.error(f"{currency} 환율 입력 실패: {str(e)}")
                
                conn.commit()
                return True, f"{success_count}개 통화의 {year}년 관리 환율이 저장되었습니다."
                
        except Exception as e:
            logger.error(f"관리 환율 대량 입력 실패: {str(e)}")
            return False, f"오류: {str(e)}"