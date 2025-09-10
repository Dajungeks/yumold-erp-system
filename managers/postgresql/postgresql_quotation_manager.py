# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 견적서 관리 시스템
"""

import pandas as pd
from datetime import datetime
import logging
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLQuotationManager(BasePostgreSQLManager):
    def __init__(self):
        """PostgreSQL 기반 견적서 매니저 초기화"""
        super().__init__()
        self.quotations_table = "quotations"
        self.items_table = "quotation_items"
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """견적서 관련 테이블 존재 확인 및 생성"""
        # quotations 테이블 생성
        quotations_sql = """
            CREATE TABLE IF NOT EXISTS quotations (
                id SERIAL PRIMARY KEY,
                quotation_id VARCHAR(50) UNIQUE NOT NULL,
                customer_id VARCHAR(50) NOT NULL,
                quotation_number VARCHAR(100),
                quotation_date DATE,
                delivery_date DATE,
                currency VARCHAR(10) DEFAULT 'USD',
                exchange_rate DECIMAL(10,4),
                total_amount DECIMAL(15,2),
                status VARCHAR(20) DEFAULT 'draft',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revision_number INTEGER DEFAULT 0,
                original_quotation_id VARCHAR(50),
                project_name VARCHAR(200),
                project_description TEXT,
                payment_terms TEXT,
                validity_period VARCHAR(100),
                delivery_terms TEXT,
                sales_rep_name VARCHAR(100),
                sales_rep_email VARCHAR(255),
                customer_company_name VARCHAR(200),
                customer_contact_person VARCHAR(100),
                customer_email VARCHAR(255),
                customer_phone VARCHAR(50),
                customer_address TEXT
            );
        """
        
        # quotation_items 테이블 생성
        items_sql = """
            CREATE TABLE IF NOT EXISTS quotation_items (
                id SERIAL PRIMARY KEY,
                quotation_id VARCHAR(50) NOT NULL,
                item_number INTEGER,
                product_name VARCHAR(200),
                product_code VARCHAR(100),
                specification TEXT,
                quantity INTEGER,
                unit_price DECIMAL(15,2),
                total_price DECIMAL(15,2),
                unit VARCHAR(20),
                lead_time VARCHAR(100),
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quotation_id) REFERENCES quotations(quotation_id)
            );
        """
        
        self.create_table_if_not_exists(self.quotations_table, quotations_sql)
        self.create_table_if_not_exists(self.items_table, items_sql)
    
    def get_all_quotations(self):
        """모든 견적서 정보를 가져옵니다."""
        query = """
            SELECT quotation_id, customer_id, quotation_number, quotation_date,
                   delivery_date, currency, exchange_rate, total_amount, status,
                   project_name, sales_rep_name, customer_company_name,
                   created_date, updated_date, revision_number
            FROM quotations
            ORDER BY created_date DESC
        """
        try:
            return self.execute_query(query, fetch_all=True)
        except Exception as e:
            logger.error(f"견적서 목록 조회 오류: {e}")
            return []
    
    def get_quotations_dataframe(self):
        """견적서 정보를 DataFrame으로 가져옵니다."""
        try:
            quotations_list = self.get_all_quotations()
            return pd.DataFrame(quotations_list)
        except Exception as e:
            logger.error(f"견적서 DataFrame 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_quotation_by_id(self, quotation_id):
        """특정 견적서 정보를 가져옵니다."""
        query = "SELECT * FROM quotations WHERE quotation_id = %s"
        try:
            return self.execute_query(query, (quotation_id,), fetch_one=True)
        except Exception as e:
            logger.error(f"견적서 조회 오류: {e}")
            return None
    
    def get_quotation_items(self, quotation_id):
        """견적서의 모든 아이템을 가져옵니다."""
        query = """
            SELECT * FROM quotation_items 
            WHERE quotation_id = %s 
            ORDER BY item_number
        """
        try:
            return self.execute_query(query, (quotation_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"견적서 아이템 조회 오류: {e}")
            return []
    
    def add_quotation(self, quotation_data, items_data=None):
        """새 견적서를 추가합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 견적서 ID 자동 생성
            quotation_id = self._generate_quotation_id()
            
            # 견적서 번호 생성
            quotation_number = self._generate_quotation_number()
            
            # 견적서 메인 데이터 삽입
            quotation_query = """
                INSERT INTO quotations (
                    quotation_id, customer_id, quotation_number, quotation_date,
                    delivery_date, currency, exchange_rate, total_amount, status,
                    notes, project_name, project_description, payment_terms,
                    validity_period, delivery_terms, sales_rep_name, sales_rep_email,
                    customer_company_name, customer_contact_person, customer_email,
                    customer_phone, customer_address, revision_number,
                    created_date, updated_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            quotation_params = (
                quotation_id,
                quotation_data.get('customer_id'),
                quotation_number,
                quotation_data.get('quotation_date'),
                quotation_data.get('delivery_date'),
                quotation_data.get('currency', 'USD'),
                quotation_data.get('exchange_rate'),
                quotation_data.get('total_amount', 0),
                quotation_data.get('status', 'draft'),
                quotation_data.get('notes'),
                quotation_data.get('project_name'),
                quotation_data.get('project_description'),
                quotation_data.get('payment_terms'),
                quotation_data.get('validity_period'),
                quotation_data.get('delivery_terms'),
                quotation_data.get('sales_rep_name'),
                quotation_data.get('sales_rep_email'),
                quotation_data.get('customer_company_name'),
                quotation_data.get('customer_contact_person'),
                quotation_data.get('customer_email'),
                quotation_data.get('customer_phone'),
                quotation_data.get('customer_address'),
                quotation_data.get('revision_number', 0),
                current_time,
                current_time
            )
            
            result = self.execute_query(quotation_query, quotation_params, fetch_one=True)
            
            # 견적서 아이템 추가
            if items_data:
                self._add_quotation_items(quotation_id, items_data)
            
            return {
                'success': True, 
                'quotation_id': quotation_id, 
                'quotation_number': quotation_number,
                'id': result['id']
            }
            
        except Exception as e:
            logger.error(f"견적서 추가 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def _add_quotation_items(self, quotation_id, items_data):
        """견적서 아이템들을 추가합니다."""
        items_query = """
            INSERT INTO quotation_items (
                quotation_id, item_number, product_name, product_code,
                specification, quantity, unit_price, total_price, unit,
                lead_time, notes, created_date, updated_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        current_time = self.format_timestamp()
        batch_data = []
        
        for idx, item in enumerate(items_data, 1):
            batch_data.append((
                quotation_id,
                idx,
                item.get('product_name'),
                item.get('product_code'),
                item.get('specification'),
                item.get('quantity', 1),
                item.get('unit_price', 0),
                item.get('total_price', 0),
                item.get('unit'),
                item.get('lead_time'),
                item.get('notes'),
                current_time,
                current_time
            ))
        
        if batch_data:
            self.execute_many(items_query, batch_data)
    
    def _generate_quotation_id(self):
        """견적서 ID 자동 생성"""
        query = """
            SELECT quotation_id FROM quotations 
            WHERE quotation_id LIKE 'QUO%' 
            ORDER BY quotation_id DESC LIMIT 1
        """
        try:
            result = self.execute_query(query, fetch_one=True)
            if result:
                last_id = result['quotation_id']
                number = int(last_id[3:]) + 1
                return f"QUO{number:06d}"
            else:
                return "QUO000001"
        except Exception as e:
            logger.error(f"견적서 ID 생성 오류: {e}")
            return "QUO000001"
    
    def _generate_quotation_number(self):
        """견적서 번호 생성 (YYYY-MM-NNNN 형식)"""
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
        
        query = """
            SELECT quotation_number FROM quotations 
            WHERE quotation_number LIKE %s 
            ORDER BY quotation_number DESC LIMIT 1
        """
        
        try:
            result = self.execute_query(query, (f"{year_month}-%",), fetch_one=True)
            if result:
                last_number = result['quotation_number']
                sequence = int(last_number.split('-')[-1]) + 1
                return f"{year_month}-{sequence:04d}"
            else:
                return f"{year_month}-0001"
        except Exception as e:
            logger.error(f"견적서 번호 생성 오류: {e}")
            return f"{year_month}-0001"
    
    def update_quotation(self, quotation_id, quotation_data, items_data=None):
        """견적서 정보를 업데이트합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 견적서 메인 정보 업데이트
            set_clauses = []
            params = []
            
            for field, value in quotation_data.items():
                if field not in ['quotation_id', 'id']:
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            set_clauses.append("updated_date = %s")
            params.append(current_time)
            params.append(quotation_id)
            
            quotation_query = f"""
                UPDATE quotations 
                SET {', '.join(set_clauses)}
                WHERE quotation_id = %s
            """
            
            self.execute_query(quotation_query, params)
            
            # 아이템 업데이트 (기존 아이템 삭제 후 재추가)
            if items_data is not None:
                self.execute_query(
                    "DELETE FROM quotation_items WHERE quotation_id = %s", 
                    (quotation_id,)
                )
                self._add_quotation_items(quotation_id, items_data)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"견적서 업데이트 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_quotation(self, quotation_id):
        """견적서를 삭제합니다."""
        try:
            # 아이템 먼저 삭제 (외래키 제약조건)
            self.execute_query(
                "DELETE FROM quotation_items WHERE quotation_id = %s", 
                (quotation_id,)
            )
            
            # 견적서 메인 삭제
            rows_affected = self.execute_query(
                "DELETE FROM quotations WHERE quotation_id = %s", 
                (quotation_id,)
            )
            
            return {'success': True, 'rows_affected': rows_affected}
        except Exception as e:
            logger.error(f"견적서 삭제 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_quotations(self, search_term):
        """견적서 검색"""
        query = """
            SELECT * FROM quotations 
            WHERE quotation_number ILIKE %s 
               OR project_name ILIKE %s 
               OR customer_company_name ILIKE %s
               OR quotation_id ILIKE %s
            ORDER BY created_date DESC
        """
        search_pattern = f"%{search_term}%"
        try:
            return self.execute_query(
                query, 
                (search_pattern, search_pattern, search_pattern, search_pattern), 
                fetch_all=True
            )
        except Exception as e:
            logger.error(f"견적서 검색 오류: {e}")
            return []
    
    def get_quotations_by_customer(self, customer_id):
        """고객별 견적서 조회"""
        query = "SELECT * FROM quotations WHERE customer_id = %s ORDER BY created_date DESC"
        try:
            return self.execute_query(query, (customer_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"고객별 견적서 조회 오류: {e}")
            return []
    
    def get_quotation_statistics(self):
        """견적서 통계 정보"""
        query = """
            SELECT 
                COUNT(*) as total_quotations,
                COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_quotations,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_quotations,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_quotations,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_quotations,
                SUM(total_amount) as total_value,
                AVG(total_amount) as average_value
            FROM quotations
        """
        try:
            return self.execute_query(query, fetch_one=True)
        except Exception as e:
            logger.error(f"견적서 통계 조회 오류: {e}")
            return {}
    
    def create_revision(self, original_quotation_id, revision_data=None):
        """견적서 리비전 생성"""
        try:
            # 원본 견적서 조회
            original = self.get_quotation_by_id(original_quotation_id)
            if not original:
                return {'success': False, 'error': '원본 견적서를 찾을 수 없습니다.'}
            
            # 원본 아이템 조회
            original_items = self.get_quotation_items(original_quotation_id)
            
            # 새 견적서 데이터 준비
            new_quotation_data = dict(original)
            new_quotation_data.update(revision_data or {})
            
            # 리비전 번호 증가
            new_quotation_data['revision_number'] = original['revision_number'] + 1
            new_quotation_data['original_quotation_id'] = original_quotation_id
            new_quotation_data['status'] = 'draft'
            
            # 리비전 생성
            result = self.add_quotation(new_quotation_data, original_items)
            
            return result
            
        except Exception as e:
            logger.error(f"견적서 리비전 생성 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_quotation_with_items(self, quotation_id):
        """견적서와 아이템을 함께 조회"""
        try:
            quotation = self.get_quotation_by_id(quotation_id)
            if quotation:
                items = self.get_quotation_items(quotation_id)
                quotation['items'] = items
            return quotation
        except Exception as e:
            logger.error(f"견적서 전체 조회 오류: {e}")
            return None