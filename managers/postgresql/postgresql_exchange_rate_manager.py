# -*- coding: utf-8 -*-
"""
PostgreSQL ExchangeRate 관리 매니저
"""

from .base_postgresql_manager import BasePostgreSQLManager
from datetime import datetime
import uuid
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PostgreSQLExchangeRateManager(BasePostgreSQLManager):
    """PostgreSQL ExchangeRate 관리 매니저"""
    
    def __init__(self):
        super().__init__()
        self.init_tables()
    
    def init_tables(self):
        """ExchangeRate 관련 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기본 환율 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS exchange_rates (
                        id SERIAL PRIMARY KEY,
                        item_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(200),
                        status VARCHAR(20) DEFAULT 'active',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 연간 관리 환율 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS yearly_management_rates (
                        id SERIAL PRIMARY KEY,
                        year INTEGER NOT NULL,
                        target_currency VARCHAR(10) NOT NULL,
                        rate DECIMAL(15,6) NOT NULL,
                        source VARCHAR(50) DEFAULT 'manual',
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(year, target_currency)
                    )
                """)
                
                self.log_info("ExchangeRate 관련 테이블 초기화 완료")
                conn.commit()
                
        except Exception as e:
            self.log_error(f"ExchangeRate 테이블 초기화 실패: {e}")
    
    def get_all_items(self):
        """모든 항목 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM exchange_rates ORDER BY created_date DESC")
                
                columns = [desc[0] for desc in cursor.description]
                items = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.log_error(f"항목 조회 실패: {e}")
            return []
    
    def get_statistics(self):
        """통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM exchange_rates")
                total_count = cursor.fetchone()[0]
                
                return {'total_count': total_count}
                
        except Exception as e:
            self.log_error(f"통계 조회 실패: {e}")
            return {'total_count': 0}
    
    def get_yearly_management_rates(self, year=None):
        """연간 관리 환율 조회
        
        Args:
            year (int, optional): 특정 연도 조회. None이면 전체 조회
            
        Returns:
            pandas.DataFrame: year, target_currency, rate 컬럼을 가진 DataFrame
        """
        try:
            query = """
                SELECT year, target_currency, rate, created_date, updated_date
                FROM yearly_management_rates
            """
            params = []
            
            if year is not None:
                query += " WHERE year = %s"
                params.append(year)
                
            query += " ORDER BY year DESC, target_currency"
            
            result = self.execute_query(query, params, fetch_all=True)
            
            if result:
                df = pd.DataFrame(result)
                logger.info(f"연간 관리 환율 조회 성공: {len(df)}건")
                return df
            else:
                logger.info("연간 관리 환율 데이터가 없습니다")
                return pd.DataFrame(columns=['year', 'target_currency', 'rate'])
                
        except Exception as e:
            logger.error(f"연간 관리 환율 조회 실패: {e}")
            return pd.DataFrame(columns=['year', 'target_currency', 'rate'])
    
    def add_yearly_management_rate(self, year, target_currency, rate, source='manual'):
        """연간 관리 환율 추가
        
        Args:
            year (int): 연도
            target_currency (str): 대상 통화 (예: CNY, VND, THB, KRW, IDR)
            rate (float): 환율
            source (str): 데이터 소스
            
        Returns:
            dict: 결과 정보
        """
        try:
            current_time = self.format_timestamp()
            
            query = """
                INSERT INTO yearly_management_rates (year, target_currency, rate, source, created_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (year, target_currency) 
                DO UPDATE SET 
                    rate = EXCLUDED.rate,
                    source = EXCLUDED.source,
                    updated_date = EXCLUDED.updated_date
                RETURNING id
            """
            
            params = (year, target_currency, rate, source, current_time, current_time)
            result = self.execute_query(query, params, fetch_one=True)
            
            logger.info(f"연간 관리 환율 저장 성공: {year}년 {target_currency} = {rate}")
            return {'success': True, 'id': result['id']}
            
        except Exception as e:
            logger.error(f"연간 관리 환율 저장 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_management_rate_by_year_currency(self, year, target_currency):
        """특정 연도와 통화의 관리 환율 조회
        
        Args:
            year (int): 연도
            target_currency (str): 대상 통화 (예: CNY, VND, THB, KRW, IDR, USD)
            
        Returns:
            float: 환율 값. 데이터가 없으면 None
        """
        try:
            query = """
                SELECT rate 
                FROM yearly_management_rates 
                WHERE year = %s AND target_currency = %s
                LIMIT 1
            """
            
            params = (year, target_currency)
            result = self.execute_query(query, params, fetch_one=True)
            
            if result:
                rate = float(result['rate'])
                logger.info(f"관리 환율 조회 성공: {year}년 {target_currency} = {rate}")
                return rate
            else:
                logger.info(f"관리 환율 데이터 없음: {year}년 {target_currency}")
                return None
                
        except Exception as e:
            logger.error(f"관리 환율 조회 실패: {e}")
            return None
    
    def update_yearly_management_rate(self, year, target_currency, rate):
        """연간 관리 환율 업데이트
        
        Args:
            year (int): 연도
            target_currency (str): 대상 통화
            rate (float): 새로운 환율
            
        Returns:
            dict: 결과 정보
        """
        try:
            current_time = self.format_timestamp()
            
            query = """
                UPDATE yearly_management_rates 
                SET rate = %s, updated_date = %s
                WHERE year = %s AND target_currency = %s
            """
            
            params = (rate, current_time, year, target_currency)
            rows_affected = self.execute_query(query, params)
            
            if rows_affected > 0:
                logger.info(f"연간 관리 환율 업데이트 성공: {year}년 {target_currency} = {rate}")
                return {'success': True, 'rows_affected': rows_affected}
            else:
                logger.warning(f"업데이트할 환율 데이터가 없습니다: {year}년 {target_currency}")
                return {'success': False, 'error': '업데이트할 데이터가 없습니다'}
                
        except Exception as e:
            logger.error(f"연간 관리 환율 업데이트 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_yearly_management_rate(self, year, target_currency):
        """연간 관리 환율 삭제
        
        Args:
            year (int): 연도
            target_currency (str): 대상 통화
            
        Returns:
            dict: 결과 정보
        """
        try:
            query = "DELETE FROM yearly_management_rates WHERE year = %s AND target_currency = %s"
            params = (year, target_currency)
            rows_affected = self.execute_query(query, params)
            
            if rows_affected > 0:
                logger.info(f"연간 관리 환율 삭제 성공: {year}년 {target_currency}")
                return {'success': True, 'rows_affected': rows_affected}
            else:
                logger.warning(f"삭제할 환율 데이터가 없습니다: {year}년 {target_currency}")
                return {'success': False, 'error': '삭제할 데이터가 없습니다'}
                
        except Exception as e:
            logger.error(f"연간 관리 환율 삭제 실패: {e}")
            return {'success': False, 'error': str(e)}
