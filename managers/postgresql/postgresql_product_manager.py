# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 공급 제품 관리 매니저
협정 공급가 및 환율 변동 관리를 위한 완전한 PostgreSQL 구현
"""

import pandas as pd
from datetime import datetime
import logging
import uuid
import psycopg2
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLSupplyProductManager(BasePostgreSQLManager):
    """PostgreSQL 기반 공급 제품 관리 매니저"""
    
    def __init__(self):
        """PostgreSQL 기반 공급 제품 매니저 초기화"""
        super().__init__()
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """공급 제품 관련 테이블들을 생성합니다"""
        try:
            # 1. 공급업체 협정 테이블
            supplier_agreements_sql = """
                CREATE TABLE IF NOT EXISTS supplier_agreements (
                    id SERIAL PRIMARY KEY,
                    agreement_id VARCHAR(50) UNIQUE NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    product_code VARCHAR(100) NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    supplier_id VARCHAR(50) NOT NULL,
                    supplier_name VARCHAR(200) NOT NULL,
                    agreement_price_usd DECIMAL(15,4) DEFAULT 0,
                    agreement_price_local DECIMAL(15,4) DEFAULT 0,
                    local_currency VARCHAR(10) DEFAULT 'CNY',
                    base_exchange_rate DECIMAL(15,6) DEFAULT 0,
                    agreement_start_date DATE,
                    agreement_end_date DATE,
                    minimum_quantity INTEGER DEFAULT 1,
                    payment_terms VARCHAR(100) DEFAULT 'NET 30',
                    agreement_conditions TEXT,
                    created_by VARCHAR(50) DEFAULT 'system',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """
            
            # 2. 공급가 변동 이력 테이블
            supply_price_history_sql = """
                CREATE TABLE IF NOT EXISTS supply_price_history (
                    id SERIAL PRIMARY KEY,
                    price_history_id VARCHAR(50) UNIQUE NOT NULL,
                    agreement_id VARCHAR(50) NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    supplier_id VARCHAR(50) NOT NULL,
                    old_price_usd DECIMAL(15,4) DEFAULT 0,
                    new_price_usd DECIMAL(15,4) DEFAULT 0,
                    old_price_local DECIMAL(15,4) DEFAULT 0,
                    new_price_local DECIMAL(15,4) DEFAULT 0,
                    exchange_rate_at_change DECIMAL(15,6) DEFAULT 0,
                    change_reason TEXT,
                    change_date DATE,
                    effective_date DATE,
                    created_by VARCHAR(50) DEFAULT 'system',
                    notes TEXT,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            # 3. 환율 영향 분석 테이블
            exchange_rate_impact_sql = """
                CREATE TABLE IF NOT EXISTS exchange_rate_impact (
                    id SERIAL PRIMARY KEY,
                    impact_id VARCHAR(50) UNIQUE NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    supplier_id VARCHAR(50) NOT NULL,
                    agreement_id VARCHAR(50) NOT NULL,
                    base_exchange_rate DECIMAL(15,6) DEFAULT 0,
                    current_exchange_rate DECIMAL(15,6) DEFAULT 0,
                    rate_change_percent DECIMAL(10,2) DEFAULT 0,
                    agreement_price_usd DECIMAL(15,4) DEFAULT 0,
                    current_equivalent_usd DECIMAL(15,4) DEFAULT 0,
                    price_impact_usd DECIMAL(15,4) DEFAULT 0,
                    price_impact_percent DECIMAL(10,2) DEFAULT 0,
                    analysis_date DATE,
                    alert_level VARCHAR(20) DEFAULT 'LOW',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            # 4. MOQ별 가격 설정 테이블
            moq_pricing_sql = """
                CREATE TABLE IF NOT EXISTS moq_pricing (
                    id SERIAL PRIMARY KEY,
                    moq_id VARCHAR(50) UNIQUE NOT NULL,
                    agreement_id VARCHAR(50) NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    supplier_id VARCHAR(50) NOT NULL,
                    min_quantity INTEGER DEFAULT 1,
                    max_quantity INTEGER DEFAULT 999999,
                    tier_name VARCHAR(100),
                    price_usd DECIMAL(15,4) DEFAULT 0,
                    price_local DECIMAL(15,4) DEFAULT 0,
                    discount_percent DECIMAL(5,2) DEFAULT 0,
                    effective_date DATE,
                    created_by VARCHAR(50) DEFAULT 'system',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            # 5. 실제 구매 데이터 테이블
            actual_purchases_sql = """
                CREATE TABLE IF NOT EXISTS actual_purchases (
                    id SERIAL PRIMARY KEY,
                    purchase_id VARCHAR(50) UNIQUE NOT NULL,
                    product_id VARCHAR(50) NOT NULL,
                    supplier_id VARCHAR(50) NOT NULL,
                    agreement_id VARCHAR(50) NOT NULL,
                    purchase_order_id VARCHAR(100),
                    quantity INTEGER DEFAULT 0,
                    actual_price_usd DECIMAL(15,4) DEFAULT 0,
                    actual_price_local DECIMAL(15,4) DEFAULT 0,
                    exchange_rate_at_purchase DECIMAL(15,6) DEFAULT 0,
                    purchase_date DATE,
                    delivery_date DATE,
                    agreement_variance_percent DECIMAL(10,2) DEFAULT 0,
                    total_amount_usd DECIMAL(15,2) DEFAULT 0,
                    total_amount_local DECIMAL(15,2) DEFAULT 0,
                    payment_terms_actual VARCHAR(100),
                    quality_rating INTEGER DEFAULT 5,
                    delivery_rating INTEGER DEFAULT 5,
                    notes TEXT,
                    created_by VARCHAR(50) DEFAULT 'system',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            # 테이블 생성 실행
            self.create_table_if_not_exists("supplier_agreements", supplier_agreements_sql)
            self.create_table_if_not_exists("supply_price_history", supply_price_history_sql)
            self.create_table_if_not_exists("exchange_rate_impact", exchange_rate_impact_sql)
            self.create_table_if_not_exists("moq_pricing", moq_pricing_sql)
            self.create_table_if_not_exists("actual_purchases", actual_purchases_sql)
            
            # 성능 최적화를 위한 인덱스 생성
            self._create_performance_indexes()
            
            logger.info("공급 제품 관리 테이블들이 성공적으로 생성되었습니다.")
            
        except Exception as e:
            logger.error(f"테이블 생성 중 오류: {e}")
            raise
    
    def _create_performance_indexes(self):
        """성능 최적화를 위한 인덱스 생성"""
        try:
            indexes_sql = [
                # supplier_agreements 인덱스
                "CREATE INDEX IF NOT EXISTS idx_supplier_agreements_agreement_id ON supplier_agreements(agreement_id);",
                "CREATE INDEX IF NOT EXISTS idx_supplier_agreements_product_supplier ON supplier_agreements(product_id, supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_supplier_agreements_dates ON supplier_agreements(agreement_start_date, agreement_end_date);",
                "CREATE INDEX IF NOT EXISTS idx_supplier_agreements_active ON supplier_agreements(is_active);",
                
                # supply_price_history 인덱스
                "CREATE INDEX IF NOT EXISTS idx_supply_price_history_agreement_id ON supply_price_history(agreement_id);",
                "CREATE INDEX IF NOT EXISTS idx_supply_price_history_product_id ON supply_price_history(product_id);",
                "CREATE INDEX IF NOT EXISTS idx_supply_price_history_dates ON supply_price_history(change_date, effective_date);",
                
                # exchange_rate_impact 인덱스
                "CREATE INDEX IF NOT EXISTS idx_exchange_rate_impact_product_supplier ON exchange_rate_impact(product_id, supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_exchange_rate_impact_analysis_date ON exchange_rate_impact(analysis_date);",
                "CREATE INDEX IF NOT EXISTS idx_exchange_rate_impact_alert_level ON exchange_rate_impact(alert_level);",
                
                # moq_pricing 인덱스
                "CREATE INDEX IF NOT EXISTS idx_moq_pricing_agreement_id ON moq_pricing(agreement_id);",
                "CREATE INDEX IF NOT EXISTS idx_moq_pricing_product_supplier ON moq_pricing(product_id, supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_moq_pricing_active ON moq_pricing(is_active);",
                "CREATE INDEX IF NOT EXISTS idx_moq_pricing_effective_date ON moq_pricing(effective_date);",
                
                # actual_purchases 인덱스
                "CREATE INDEX IF NOT EXISTS idx_actual_purchases_agreement_id ON actual_purchases(agreement_id);",
                "CREATE INDEX IF NOT EXISTS idx_actual_purchases_product_supplier ON actual_purchases(product_id, supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_actual_purchases_purchase_date ON actual_purchases(purchase_date);",
                "CREATE INDEX IF NOT EXISTS idx_actual_purchases_delivery_date ON actual_purchases(delivery_date);"
            ]
            
            for index_sql in indexes_sql:
                self.execute_query(index_sql)
            
            logger.info("성능 최적화 인덱스들이 성공적으로 생성되었습니다.")
            
        except Exception as e:
            logger.warning(f"인덱스 생성 중 오류 (무시 가능): {e}")
    
    def get_master_mb_products(self):
        """MB 제품만 마스터 제품 DB에서 조회합니다"""
        try:
            from config.database_config import get_master_product_manager
            master_manager = get_master_product_manager()
            
            # PostgreSQL 연결 확인
            if not hasattr(self, 'database_url') or not self.database_url:
                logger.error("PostgreSQL 연결이 설정되지 않았습니다.")
                return pd.DataFrame()
            
            all_products = master_manager.get_all_products()
            
            if len(all_products) == 0:
                logger.warning("마스터 제품 데이터가 없습니다.")
                return pd.DataFrame()
            
            # PostgreSQL 마스터 매니저와의 호환성 처리
            # Legacy CSV 기반 스키마와 PostgreSQL 스키마 간의 차이 해결
            if 'main_category' in all_products.columns:
                # Legacy 스키마인 경우 - MB 제품만 필터링
                mb_products = all_products[all_products['main_category'] == 'MB']
                return mb_products
            else:
                # PostgreSQL 기본 스키마인 경우 - 모든 제품 반환하고 경고 로그
                logger.warning("PostgreSQL 마스터 제품 매니저에 main_category 컬럼이 없습니다. 모든 제품을 반환합니다.")
                
                # 필요한 컬럼들을 기본값으로 추가하여 호환성 유지
                if 'product_id' not in all_products.columns:
                    all_products['product_id'] = all_products.get('item_id', all_products.index.astype(str))
                if 'product_code' not in all_products.columns:
                    all_products['product_code'] = all_products.get('name', 'UNKNOWN')
                if 'product_name_korean' not in all_products.columns:
                    all_products['product_name_korean'] = all_products.get('name', 'Unknown Product')
                if 'main_category' not in all_products.columns:
                    all_products['main_category'] = 'MB'  # 기본값
                
                return all_products
                
        except Exception as e:
            logger.error(f"마스터 MB 제품 조회 오류: {e}")
            # 연결 실패 시 빈 DataFrame 반환
            return pd.DataFrame()
    
    def sync_with_master_mb_product(self, master_product_data, supplier_data):
        """마스터 MB 제품과 동기화하여 공급 협정을 생성합니다"""
        try:
            # 안전한 컬럼 접근을 위한 헬퍼 함수
            def safe_get(data, key, default=''):
                if isinstance(data, dict):
                    return data.get(key, default)
                elif hasattr(data, key):
                    return getattr(data, key, default)
                else:
                    return default
            
            # 마스터 제품 데이터에서 안전하게 값 추출
            product_id = safe_get(master_product_data, 'product_id', f'SYNC_{datetime.now().strftime("%Y%m%d%H%M%S")}')
            product_code = safe_get(master_product_data, 'product_code', safe_get(master_product_data, 'name', 'UNKNOWN'))
            product_name = safe_get(master_product_data, 'product_name_korean', safe_get(master_product_data, 'name', 'Unknown Product'))
            
            # 공급업체 데이터에서 안전하게 값 추출
            supplier_id = safe_get(supplier_data, 'supplier_id', 'UNKNOWN_SUPPLIER')
            supplier_name = safe_get(supplier_data, 'supplier_name', 'Unknown Supplier')
            
            return self.create_supplier_agreement(
                product_id=product_id,
                product_code=product_code,
                product_name=product_name,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                agreement_price_usd=0.0,  # 사용자가 입력
                agreement_price_local=0.0,
                local_currency='CNY',  # MB 제품은 기본적으로 CNY
                base_exchange_rate=7.0,  # 기본 환율
                agreement_start_date=datetime.now().strftime('%Y-%m-%d'),
                agreement_end_date=datetime.now().strftime('%Y-%m-%d'),
                minimum_quantity=1,
                payment_terms='30일',
                created_by='system'
            )
        except Exception as e:
            logger.error(f"마스터 MB 제품 동기화 오류: {e}")
            return False, str(e)
    
    def generate_agreement_id(self):
        """협정 ID를 생성합니다 (UUID 기반 - 동시성 안전)"""
        try:
            # UUID 기반 ID 생성으로 동시성 문제 해결
            unique_id = str(uuid.uuid4()).replace('-', '')[:8].upper()
            agreement_id = f'AG{unique_id}'
            
            # 중복 확인 (극히 드물지만 안전장치)
            check_query = "SELECT COUNT(*) as count FROM supplier_agreements WHERE agreement_id = %s"
            result = self.execute_query(check_query, (agreement_id,), fetch_one=True)
            
            if result and result['count'] > 0:
                # 중복 시 타임스탬프 추가
                timestamp = datetime.now().strftime('%H%M%S')
                agreement_id = f'AG{timestamp}{unique_id[:5]}'
                logger.warning(f"협정 ID 중복 발생, 새 ID 생성: {agreement_id}")
            
            return agreement_id
            
        except Exception as e:
            logger.error(f"협정 ID 생성 중 오류: {e}")
            # 폴백: 타임스탬프 기반 ID
            fallback_id = f'AG{datetime.now().strftime("%Y%m%d%H%M%S")}'[:12]
            logger.info(f"폴백 ID 사용: {fallback_id}")
            return fallback_id
    
    def create_supplier_agreement(self, product_id, product_code, product_name,
                                supplier_id, supplier_name, agreement_price_usd,
                                agreement_price_local, local_currency, base_exchange_rate,
                                agreement_start_date, agreement_end_date,
                                minimum_quantity=1, payment_terms='NET 30',
                                agreement_conditions='', created_by='system'):
        """공급업체와의 협정을 생성합니다"""
        try:
            # 입력 데이터 검증
            if not product_id or not supplier_id:
                return False, "product_id와 supplier_id는 필수입니다."
            
            # PostgreSQL 연결 상태 확인
            if not hasattr(self, 'database_url') or not self.database_url:
                return False, "PostgreSQL 연결이 설정되지 않았습니다."
            
            agreement_id = self.generate_agreement_id()
            current_time = self.format_timestamp()
            
            query = """
                INSERT INTO supplier_agreements (
                    agreement_id, product_id, product_code, product_name,
                    supplier_id, supplier_name, agreement_price_usd, 
                    agreement_price_local, local_currency, base_exchange_rate,
                    agreement_start_date, agreement_end_date, minimum_quantity,
                    payment_terms, agreement_conditions, created_by,
                    created_date, is_active
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            params = (
                agreement_id, product_id, product_code, product_name,
                supplier_id, supplier_name, agreement_price_usd,
                agreement_price_local, local_currency, base_exchange_rate,
                agreement_start_date, agreement_end_date, minimum_quantity,
                payment_terms, agreement_conditions, created_by,
                current_time, True
            )
            
            result = self.execute_query(query, params, fetch_one=True)
            logger.info(f"공급업체 협정 생성 완료: {agreement_id}")
            return True, agreement_id
            
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL 오류 - 공급업체 협정 생성: {e}")
            return False, f"데이터베이스 오류: {str(e)}"
        except Exception as e:
            logger.error(f"공급업체 협정 생성 중 오류: {e}")
            return False, str(e)
    
    def get_all_agreements(self):
        """모든 협정 데이터를 가져옵니다 (견적서에서 사용)"""
        return self.get_active_agreements()
    
    def get_active_agreements(self, product_id=None, supplier_id=None):
        """활성 협정을 조회합니다"""
        try:
            base_query = """
                SELECT agreement_id, product_id, product_code, product_name,
                       supplier_id, supplier_name, agreement_price_usd, 
                       agreement_price_local, local_currency, base_exchange_rate,
                       agreement_start_date, agreement_end_date, minimum_quantity,
                       payment_terms, agreement_conditions, created_by,
                       created_date, is_active
                FROM supplier_agreements 
                WHERE is_active = TRUE
            """
            
            params = []
            if product_id:
                base_query += " AND product_id = %s"
                params.append(product_id)
            if supplier_id:
                base_query += " AND supplier_id = %s"
                params.append(supplier_id)
            
            base_query += " ORDER BY created_date DESC"
            
            results = self.execute_query(base_query, params, fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"활성 협정 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def analyze_exchange_rate_impact(self, exchange_rate_manager):
        """환율 변동이 협정가에 미치는 영향을 분석합니다"""
        try:
            # 활성 협정 조회
            active_agreements = self.get_active_agreements()
            
            if len(active_agreements) == 0:
                return pd.DataFrame()
            
            impact_records = []
            
            for _, agreement in active_agreements.iterrows():
                local_currency = agreement['local_currency']
                base_rate = float(agreement['base_exchange_rate'])
                
                # 현재 환율 조회
                current_rate_info = exchange_rate_manager.get_rate_by_currency(local_currency)
                current_rate = float(current_rate_info['rate']) if current_rate_info else base_rate
                
                # 환율 변동률 계산
                rate_change_percent = ((current_rate - base_rate) / base_rate) * 100 if base_rate > 0 else 0
                
                # 현재 환율 기준 USD 환산가
                current_equivalent_usd = float(agreement['agreement_price_local']) / current_rate if current_rate > 0 else 0
                
                # 가격 영향 계산
                price_impact_usd = current_equivalent_usd - float(agreement['agreement_price_usd'])
                price_impact_percent = (price_impact_usd / float(agreement['agreement_price_usd'])) * 100 if float(agreement['agreement_price_usd']) > 0 else 0
                
                # 알림 레벨 결정
                alert_level = 'LOW'
                if abs(price_impact_percent) > 10:
                    alert_level = 'HIGH'
                elif abs(price_impact_percent) > 5:
                    alert_level = 'MEDIUM'
                
                impact_id = f"IM{datetime.now().strftime('%Y%m%d%H%M%S')}{len(impact_records):03d}"
                
                # DB에 영향 분석 결과 저장
                self._save_exchange_rate_impact(
                    impact_id, agreement['product_id'], agreement['supplier_id'],
                    agreement['agreement_id'], base_rate, current_rate,
                    rate_change_percent, float(agreement['agreement_price_usd']),
                    current_equivalent_usd, price_impact_usd, price_impact_percent,
                    alert_level
                )
                
                impact_record = {
                    'impact_id': impact_id,
                    'product_id': agreement['product_id'],
                    'supplier_id': agreement['supplier_id'],
                    'agreement_id': agreement['agreement_id'],
                    'base_exchange_rate': base_rate,
                    'current_exchange_rate': current_rate,
                    'rate_change_percent': round(rate_change_percent, 2),
                    'agreement_price_usd': float(agreement['agreement_price_usd']),
                    'current_equivalent_usd': round(current_equivalent_usd, 2),
                    'price_impact_usd': round(price_impact_usd, 2),
                    'price_impact_percent': round(price_impact_percent, 2),
                    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                    'alert_level': alert_level
                }
                
                impact_records.append(impact_record)
            
            return pd.DataFrame(impact_records) if impact_records else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"환율 영향 분석 중 오류: {e}")
            return pd.DataFrame()
    
    def _save_exchange_rate_impact(self, impact_id, product_id, supplier_id, agreement_id,
                                  base_rate, current_rate, rate_change_percent,
                                  agreement_price_usd, current_equivalent_usd,
                                  price_impact_usd, price_impact_percent, alert_level):
        """환율 영향 분석 결과를 DB에 저장합니다"""
        try:
            query = """
                INSERT INTO exchange_rate_impact (
                    impact_id, product_id, supplier_id, agreement_id,
                    base_exchange_rate, current_exchange_rate, rate_change_percent,
                    agreement_price_usd, current_equivalent_usd, price_impact_usd,
                    price_impact_percent, analysis_date, alert_level
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (impact_id) DO UPDATE SET
                    current_exchange_rate = EXCLUDED.current_exchange_rate,
                    rate_change_percent = EXCLUDED.rate_change_percent,
                    current_equivalent_usd = EXCLUDED.current_equivalent_usd,
                    price_impact_usd = EXCLUDED.price_impact_usd,
                    price_impact_percent = EXCLUDED.price_impact_percent,
                    analysis_date = EXCLUDED.analysis_date,
                    alert_level = EXCLUDED.alert_level
            """
            
            params = (
                impact_id, product_id, supplier_id, agreement_id,
                base_rate, current_rate, round(rate_change_percent, 2),
                agreement_price_usd, round(current_equivalent_usd, 2),
                round(price_impact_usd, 2), round(price_impact_percent, 2),
                datetime.now().strftime('%Y-%m-%d'), alert_level
            )
            
            self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"환율 영향 분석 결과 저장 중 오류: {e}")
    
    def get_price_variance_alerts(self, threshold_percent=5):
        """가격 변동 알림을 가져옵니다"""
        try:
            query = """
                SELECT impact_id, product_id, supplier_id, agreement_id,
                       base_exchange_rate, current_exchange_rate, rate_change_percent,
                       agreement_price_usd, current_equivalent_usd, price_impact_usd,
                       price_impact_percent, analysis_date, alert_level
                FROM exchange_rate_impact 
                WHERE ABS(price_impact_percent) > %s
                ORDER BY ABS(price_impact_percent) DESC
            """
            
            results = self.execute_query(query, (threshold_percent,), fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"가격 변동 알림 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def update_agreement_price(self, agreement_id, new_price_usd, new_price_local,
                             change_reason, created_by='system'):
        """협정 가격을 업데이트합니다"""
        try:
            # 기존 협정 정보 조회
            query = "SELECT * FROM supplier_agreements WHERE agreement_id = %s"
            agreement = self.execute_query(query, (agreement_id,), fetch_one=True)
            
            if not agreement:
                return False, "협정을 찾을 수 없습니다."
            
            old_price_usd = float(agreement['agreement_price_usd'])
            old_price_local = float(agreement['agreement_price_local'])
            
            # 가격 변동 이력 기록
            history_id = f"PH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self._save_price_history(
                history_id, agreement_id, agreement['product_id'], agreement['supplier_id'],
                old_price_usd, new_price_usd, old_price_local, new_price_local,
                new_price_local / new_price_usd if new_price_usd > 0 else 0,
                change_reason, created_by
            )
            
            # 협정 가격 업데이트
            update_query = """
                UPDATE supplier_agreements 
                SET agreement_price_usd = %s, agreement_price_local = %s
                WHERE agreement_id = %s
            """
            self.execute_query(update_query, (new_price_usd, new_price_local, agreement_id))
            
            return True, history_id
            
        except Exception as e:
            logger.error(f"협정 가격 업데이트 중 오류: {e}")
            return False, str(e)
    
    def _save_price_history(self, history_id, agreement_id, product_id, supplier_id,
                           old_price_usd, new_price_usd, old_price_local, new_price_local,
                           exchange_rate, change_reason, created_by):
        """가격 변동 이력을 저장합니다"""
        try:
            query = """
                INSERT INTO supply_price_history (
                    price_history_id, agreement_id, product_id, supplier_id,
                    old_price_usd, new_price_usd, old_price_local, new_price_local,
                    exchange_rate_at_change, change_reason, change_date,
                    effective_date, created_by, notes
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            notes = f'가격 변경: {old_price_usd} -> {new_price_usd} USD'
            
            params = (
                history_id, agreement_id, product_id, supplier_id,
                old_price_usd, new_price_usd, old_price_local, new_price_local,
                exchange_rate, change_reason, current_date, current_date,
                created_by, notes
            )
            
            self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"가격 변동 이력 저장 중 오류: {e}")
    
    def get_supplier_performance_analysis(self, supplier_id=None):
        """공급업체 성과 분석을 수행합니다"""
        try:
            base_query = """
                SELECT s.supplier_id, s.supplier_name,
                       COUNT(s.agreement_id) as total_agreements,
                       SUM(CASE WHEN s.is_active THEN 1 ELSE 0 END) as active_agreements,
                       AVG(s.agreement_price_usd) as avg_price_usd,
                       COUNT(h.price_history_id) as price_changes
                FROM supplier_agreements s
                LEFT JOIN supply_price_history h ON s.agreement_id = h.agreement_id
            """
            
            params = []
            if supplier_id:
                base_query += " WHERE s.supplier_id = %s"
                params.append(supplier_id)
            
            base_query += """
                GROUP BY s.supplier_id, s.supplier_name
                ORDER BY total_agreements DESC
            """
            
            results = self.execute_query(base_query, params, fetch_all=True)
            supplier_summary = pd.DataFrame(results) if results else pd.DataFrame()
            
            # 전체 통계
            total_query = "SELECT COUNT(*) as total FROM supplier_agreements"
            if supplier_id:
                total_query += " WHERE supplier_id = %s"
            
            total_result = self.execute_query(total_query, params if supplier_id else [], fetch_one=True)
            total_agreements = total_result['total'] if total_result else 0
            
            active_query = "SELECT COUNT(*) as active FROM supplier_agreements WHERE is_active = TRUE"
            if supplier_id:
                active_query += " AND supplier_id = %s"
            
            active_result = self.execute_query(active_query, params if supplier_id else [], fetch_one=True)
            active_agreements = active_result['active'] if active_result else 0
            
            price_changes_query = "SELECT COUNT(*) as changes FROM supply_price_history"
            if supplier_id:
                price_changes_query += " WHERE supplier_id = %s"
            
            changes_result = self.execute_query(price_changes_query, params if supplier_id else [], fetch_one=True)
            price_changes = changes_result['changes'] if changes_result else 0
            
            average_price_stability = (total_agreements - price_changes) / total_agreements * 100 if total_agreements > 0 else 0
            
            return {
                'total_agreements': total_agreements,
                'active_agreements': active_agreements,
                'price_changes': price_changes,
                'average_price_stability': round(average_price_stability, 2),
                'supplier_summary': supplier_summary
            }
            
        except Exception as e:
            logger.error(f"공급업체 성과 분석 중 오류: {e}")
            return {
                'total_agreements': 0,
                'active_agreements': 0,
                'price_changes': 0,
                'average_price_stability': 0,
                'supplier_summary': pd.DataFrame()
            }
    
    def create_moq_pricing(self, agreement_id, product_id, supplier_id, 
                          pricing_tiers, created_by='system'):
        """MOQ별 가격 체계를 생성합니다"""
        try:
            moq_ids = []
            
            for i, tier in enumerate(pricing_tiers):
                moq_id = f"MOQ{datetime.now().strftime('%Y%m%d%H%M%S')}{i:03d}"
                
                query = """
                    INSERT INTO moq_pricing (
                        moq_id, agreement_id, product_id, supplier_id,
                        min_quantity, max_quantity, tier_name, price_usd,
                        price_local, discount_percent, effective_date,
                        created_by, is_active
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                params = (
                    moq_id, agreement_id, product_id, supplier_id,
                    tier['min_quantity'], tier.get('max_quantity', 999999),
                    tier['tier_name'], tier['price_usd'],
                    tier.get('price_local', tier['price_usd']),
                    tier.get('discount_percent', 0),
                    datetime.now().strftime('%Y-%m-%d'),
                    created_by, True
                )
                
                self.execute_query(query, params)
                moq_ids.append(moq_id)
            
            return True, f"MOQ 가격 {len(moq_ids)}개 등록 완료"
            
        except Exception as e:
            logger.error(f"MOQ 가격 생성 중 오류: {e}")
            return False, str(e)
    
    def get_moq_pricing(self, agreement_id=None, product_id=None):
        """MOQ별 가격을 조회합니다"""
        try:
            base_query = """
                SELECT moq_id, agreement_id, product_id, supplier_id,
                       min_quantity, max_quantity, tier_name, price_usd,
                       price_local, discount_percent, effective_date,
                       created_by, is_active
                FROM moq_pricing 
                WHERE is_active = TRUE
            """
            
            params = []
            if agreement_id:
                base_query += " AND agreement_id = %s"
                params.append(agreement_id)
            if product_id:
                base_query += " AND product_id = %s"
                params.append(product_id)
            
            base_query += " ORDER BY min_quantity"
            
            results = self.execute_query(base_query, params, fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"MOQ 가격 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def record_actual_purchase(self, product_id, supplier_id, agreement_id,
                             purchase_order_id, quantity, actual_price_usd,
                             actual_price_local, exchange_rate_at_purchase,
                             purchase_date, delivery_date=None,
                             payment_terms_actual='', quality_rating=5,
                             delivery_rating=5, notes='', created_by='system'):
        """실제 구매 데이터를 기록합니다"""
        try:
            # 협정가 조회
            query = "SELECT agreement_price_usd FROM supplier_agreements WHERE agreement_id = %s"
            agreement = self.execute_query(query, (agreement_id,), fetch_one=True)
            
            if not agreement:
                return False, "협정 정보를 찾을 수 없습니다."
            
            agreement_price_usd = float(agreement['agreement_price_usd'])
            
            # 협정가 대비 편차 계산
            variance_percent = 0
            if agreement_price_usd > 0:
                variance_percent = ((actual_price_usd - agreement_price_usd) / agreement_price_usd) * 100
            
            purchase_id = f"PUR{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            insert_query = """
                INSERT INTO actual_purchases (
                    purchase_id, product_id, supplier_id, agreement_id,
                    purchase_order_id, quantity, actual_price_usd, actual_price_local,
                    exchange_rate_at_purchase, purchase_date, delivery_date,
                    agreement_variance_percent, total_amount_usd, total_amount_local,
                    payment_terms_actual, quality_rating, delivery_rating,
                    notes, created_by, created_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                purchase_id, product_id, supplier_id, agreement_id,
                purchase_order_id, quantity, actual_price_usd, actual_price_local,
                exchange_rate_at_purchase, purchase_date, delivery_date or purchase_date,
                round(variance_percent, 2), quantity * actual_price_usd, quantity * actual_price_local,
                payment_terms_actual, quality_rating, delivery_rating,
                notes, created_by, self.format_timestamp()
            )
            
            self.execute_query(insert_query, params)
            return True, purchase_id
            
        except Exception as e:
            logger.error(f"실제 구매 데이터 기록 중 오류: {e}")
            return False, str(e)
    
    def get_purchase_history(self, product_id=None, supplier_id=None, start_date=None, end_date=None):
        """구매 이력을 조회합니다"""
        try:
            base_query = """
                SELECT purchase_id, product_id, supplier_id, agreement_id,
                       purchase_order_id, quantity, actual_price_usd, actual_price_local,
                       exchange_rate_at_purchase, purchase_date, delivery_date,
                       agreement_variance_percent, total_amount_usd, total_amount_local,
                       payment_terms_actual, quality_rating, delivery_rating,
                       notes, created_by, created_date
                FROM actual_purchases 
                WHERE 1=1
            """
            
            params = []
            if product_id:
                base_query += " AND product_id = %s"
                params.append(product_id)
            if supplier_id:
                base_query += " AND supplier_id = %s"
                params.append(supplier_id)
            if start_date:
                base_query += " AND purchase_date >= %s"
                params.append(start_date)
            if end_date:
                base_query += " AND purchase_date <= %s"
                params.append(end_date)
            
            base_query += " ORDER BY purchase_date DESC"
            
            results = self.execute_query(base_query, params, fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"구매 이력 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def delete_agreement(self, agreement_id, created_by='system'):
        """협정을 삭제합니다 (비활성화)"""
        try:
            query = """
                UPDATE supplier_agreements 
                SET is_active = FALSE 
                WHERE agreement_id = %s
            """
            rows_affected = self.execute_query(query, (agreement_id,))
            
            if rows_affected > 0:
                return True, "협정이 성공적으로 비활성화되었습니다."
            else:
                return False, "해당 협정을 찾을 수 없습니다."
                
        except Exception as e:
            logger.error(f"협정 삭제 중 오류: {e}")
            return False, str(e)
    
    def get_agreements_dataframe(self):
        """협정 데이터를 DataFrame으로 반환합니다"""
        return self.get_active_agreements()
    
    def get_price_history_dataframe(self):
        """가격 변동 이력을 DataFrame으로 반환합니다"""
        try:
            query = """
                SELECT price_history_id, agreement_id, product_id, supplier_id,
                       old_price_usd, new_price_usd, old_price_local, new_price_local,
                       exchange_rate_at_change, change_reason, change_date,
                       effective_date, created_by, notes
                FROM supply_price_history 
                ORDER BY change_date DESC
            """
            
            results = self.execute_query(query, fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"가격 변동 이력 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_exchange_rate_impact_dataframe(self):
        """환율 영향 분석 데이터를 DataFrame으로 반환합니다"""
        try:
            query = """
                SELECT impact_id, product_id, supplier_id, agreement_id,
                       base_exchange_rate, current_exchange_rate, rate_change_percent,
                       agreement_price_usd, current_equivalent_usd, price_impact_usd,
                       price_impact_percent, analysis_date, alert_level
                FROM exchange_rate_impact 
                ORDER BY analysis_date DESC
            """
            
            results = self.execute_query(query, fetch_all=True)
            return pd.DataFrame(results) if results else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"환율 영향 분석 데이터 조회 중 오류: {e}")
            return pd.DataFrame()
