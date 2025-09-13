# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 주문 관리 시스템
"""

import pandas as pd
from datetime import datetime
import logging
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLOrderManager(BasePostgreSQLManager):
    def __init__(self):
        """PostgreSQL 기반 주문 매니저 초기화"""
        super().__init__()
        self.orders_table = "orders"
        self.items_table = "order_items"
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """주문 관련 테이블 존재 확인 및 생성"""
        # orders 테이블 생성
        orders_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50) UNIQUE NOT NULL,
                quotation_id VARCHAR(50),
                customer_id VARCHAR(50) NOT NULL,
                order_number VARCHAR(100),
                order_date DATE,
                delivery_date DATE,
                currency VARCHAR(10) DEFAULT 'USD',
                exchange_rate DECIMAL(10,4),
                total_amount DECIMAL(15,2),
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                customer_company_name VARCHAR(200),
                customer_contact_person VARCHAR(100),
                customer_email VARCHAR(255),
                customer_phone VARCHAR(50),
                customer_address TEXT,
                project_name VARCHAR(200),
                payment_terms TEXT,
                delivery_terms TEXT,
                sales_rep_name VARCHAR(100),
                sales_rep_email VARCHAR(255)
            );
        """
        
        # order_items 테이블 생성
        items_sql = """
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50) NOT NULL,
                item_number INTEGER,
                product_name VARCHAR(200),
                product_code VARCHAR(100),
                specification TEXT,
                quantity INTEGER,
                unit_price DECIMAL(15,2),
                total_price DECIMAL(15,2),
                unit VARCHAR(20),
                delivery_status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            );
        """
        
        self.create_table_if_not_exists(self.orders_table, orders_sql)
        self.create_table_if_not_exists(self.items_table, items_sql)
    
    def get_all_orders(self) -> pd.DataFrame:
        """모든 주문 정보를 DataFrame으로 가져옵니다."""
        query = """
            SELECT order_id, quotation_id, customer_id, order_number, order_date,
                   delivery_date, currency, exchange_rate, total_amount, status,
                   project_name, sales_rep_name, customer_company_name,
                   created_date, updated_date
            FROM orders
            ORDER BY created_date DESC
        """
        try:
            result = self.execute_query(query, fetch_all=True)
            if result:
                return pd.DataFrame(result)
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"주문 목록 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_orders_dataframe(self) -> pd.DataFrame:
        """주문 정보를 DataFrame으로 가져옵니다. (기존 호환성 유지)"""
        return self.get_all_orders()
    
    def get_order_by_id(self, order_id):
        """특정 주문 정보를 가져옵니다."""
        query = "SELECT * FROM orders WHERE order_id = %s"
        try:
            return self.execute_query(query, (order_id,), fetch_one=True)
        except Exception as e:
            logger.error(f"주문 조회 오류: {e}")
            return None
    
    def get_order_items(self, order_id) -> pd.DataFrame:
        """주문의 모든 아이템을 DataFrame으로 가져옵니다."""
        query = """
            SELECT * FROM order_items 
            WHERE order_id = %s 
            ORDER BY item_number
        """
        try:
            result = self.execute_query(query, (order_id,), fetch_all=True)
            if result:
                return pd.DataFrame(result)
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"주문 아이템 조회 오류: {e}")
            return pd.DataFrame()
    
    def add_order(self, order_data, items_data=None):
        """새 주문을 추가합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 주문 ID 자동 생성
            order_id = self._generate_order_id()
            
            # 주문 번호 생성
            order_number = self._generate_order_number()
            
            # 주문 메인 데이터 삽입
            order_query = """
                INSERT INTO orders (
                    order_id, quotation_id, customer_id, order_number, order_date,
                    delivery_date, currency, exchange_rate, total_amount, status,
                    notes, customer_company_name, customer_contact_person,
                    customer_email, customer_phone, customer_address, project_name,
                    payment_terms, delivery_terms, sales_rep_name, sales_rep_email,
                    created_date, updated_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            order_params = (
                order_id,
                order_data.get('quotation_id'),
                order_data.get('customer_id'),
                order_number,
                order_data.get('order_date'),
                order_data.get('delivery_date'),
                order_data.get('currency', 'USD'),
                order_data.get('exchange_rate'),
                order_data.get('total_amount', 0),
                order_data.get('status', 'pending'),
                order_data.get('notes'),
                order_data.get('customer_company_name'),
                order_data.get('customer_contact_person'),
                order_data.get('customer_email'),
                order_data.get('customer_phone'),
                order_data.get('customer_address'),
                order_data.get('project_name'),
                order_data.get('payment_terms'),
                order_data.get('delivery_terms'),
                order_data.get('sales_rep_name'),
                order_data.get('sales_rep_email'),
                current_time,
                current_time
            )
            
            result = self.execute_query(order_query, order_params, fetch_one=True)
            
            # 주문 아이템 추가
            if items_data:
                self._add_order_items(order_id, items_data)
            
            return {
                'success': True, 
                'order_id': order_id, 
                'order_number': order_number,
                'id': result['id']
            }
            
        except Exception as e:
            logger.error(f"주문 추가 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def _add_order_items(self, order_id, items_data):
        """주문 아이템들을 추가합니다."""
        items_query = """
            INSERT INTO order_items (
                order_id, item_number, product_name, product_code,
                specification, quantity, unit_price, total_price, unit,
                delivery_status, notes, created_date, updated_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        current_time = self.format_timestamp()
        batch_data = []
        
        for idx, item in enumerate(items_data, 1):
            batch_data.append((
                order_id,
                idx,
                item.get('product_name'),
                item.get('product_code'),
                item.get('specification'),
                item.get('quantity', 1),
                item.get('unit_price', 0),
                item.get('total_price', 0),
                item.get('unit'),
                item.get('delivery_status', 'pending'),
                item.get('notes'),
                current_time,
                current_time
            ))
        
        if batch_data:
            self.execute_many(items_query, batch_data)
    
    def _generate_order_id(self):
        """주문 ID 자동 생성"""
        query = """
            SELECT order_id FROM orders 
            WHERE order_id LIKE 'ORD%' 
            ORDER BY order_id DESC LIMIT 1
        """
        try:
            result = self.execute_query(query, fetch_one=True)
            if result:
                last_id = result['order_id']
                number = int(last_id[3:]) + 1
                return f"ORD{number:06d}"
            else:
                return "ORD000001"
        except Exception as e:
            logger.error(f"주문 ID 생성 오류: {e}")
            return "ORD000001"
    
    def _generate_order_number(self):
        """주문 번호 생성 (PO-YYYY-MM-NNNN 형식)"""
        today = datetime.now()
        year_month = today.strftime("%Y-%m")
        
        query = """
            SELECT order_number FROM orders 
            WHERE order_number LIKE %s 
            ORDER BY order_number DESC LIMIT 1
        """
        
        try:
            result = self.execute_query(query, (f"PO-{year_month}-%",), fetch_one=True)
            if result:
                last_number = result['order_number']
                sequence = int(last_number.split('-')[-1]) + 1
                return f"PO-{year_month}-{sequence:04d}"
            else:
                return f"PO-{year_month}-0001"
        except Exception as e:
            logger.error(f"주문 번호 생성 오류: {e}")
            return f"PO-{year_month}-0001"
    
    def update_order(self, order_id, order_data, items_data=None):
        """주문 정보를 업데이트합니다."""
        try:
            current_time = self.format_timestamp()
            
            # 주문 메인 정보 업데이트
            set_clauses = []
            params = []
            
            for field, value in order_data.items():
                if field not in ['order_id', 'id']:
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            set_clauses.append("updated_date = %s")
            params.append(current_time)
            params.append(order_id)
            
            order_query = f"""
                UPDATE orders 
                SET {', '.join(set_clauses)}
                WHERE order_id = %s
            """
            
            self.execute_query(order_query, params)
            
            # 아이템 업데이트 (기존 아이템 삭제 후 재추가)
            if items_data is not None:
                self.execute_query(
                    "DELETE FROM order_items WHERE order_id = %s", 
                    (order_id,)
                )
                self._add_order_items(order_id, items_data)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"주문 업데이트 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_order(self, order_id):
        """주문을 삭제합니다."""
        try:
            # 아이템 먼저 삭제 (외래키 제약조건)
            self.execute_query(
                "DELETE FROM order_items WHERE order_id = %s", 
                (order_id,)
            )
            
            # 주문 메인 삭제
            rows_affected = self.execute_query(
                "DELETE FROM orders WHERE order_id = %s", 
                (order_id,)
            )
            
            return {'success': True, 'rows_affected': rows_affected}
        except Exception as e:
            logger.error(f"주문 삭제 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_order_from_quotation(self, quotation_id, order_data=None):
        """견적서에서 주문 생성"""
        try:
            # PostgreSQL Quotation Manager import
            from .postgresql_quotation_manager import PostgreSQLQuotationManager
            
            quotation_manager = PostgreSQLQuotationManager()
            quotation = quotation_manager.get_quotation_with_items(quotation_id)
            
            if not quotation:
                return {'success': False, 'error': '견적서를 찾을 수 없습니다.'}
            
            # 견적서 데이터를 주문 데이터로 변환
            new_order_data = {
                'quotation_id': quotation_id,
                'customer_id': quotation['customer_id'],
                'currency': quotation['currency'],
                'exchange_rate': quotation['exchange_rate'],
                'total_amount': quotation['total_amount'],
                'customer_company_name': quotation['customer_company_name'],
                'customer_contact_person': quotation['customer_contact_person'],
                'customer_email': quotation['customer_email'],
                'customer_phone': quotation['customer_phone'],
                'customer_address': quotation['customer_address'],
                'project_name': quotation['project_name'],
                'payment_terms': quotation['payment_terms'],
                'delivery_terms': quotation['delivery_terms'],
                'sales_rep_name': quotation['sales_rep_name'],
                'sales_rep_email': quotation['sales_rep_email']
            }
            
            # 추가 주문 데이터로 업데이트
            if order_data:
                new_order_data.update(order_data)
            
            # 견적서 아이템을 주문 아이템으로 변환
            order_items = []
            for item in quotation.get('items', []):
                order_items.append({
                    'product_name': item['product_name'],
                    'product_code': item['product_code'],
                    'specification': item['specification'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'total_price': item['total_price'],
                    'unit': item['unit'],
                    'notes': item['notes']
                })
            
            # 주문 생성
            return self.add_order(new_order_data, order_items)
            
        except Exception as e:
            logger.error(f"견적서에서 주문 생성 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_orders_by_customer(self, customer_id):
        """고객별 주문 조회"""
        query = "SELECT * FROM orders WHERE customer_id = %s ORDER BY created_date DESC"
        try:
            return self.execute_query(query, (customer_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"고객별 주문 조회 오류: {e}")
            return []
    
    def get_orders_by_status(self, status):
        """상태별 주문 조회"""
        query = "SELECT * FROM orders WHERE status = %s ORDER BY created_date DESC"
        try:
            return self.execute_query(query, (status,), fetch_all=True)
        except Exception as e:
            logger.error(f"상태별 주문 조회 오류: {e}")
            return []
    
    def get_order_statistics(self):
        """주문 통계 정보"""
        query = """
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_orders,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_orders,
                COUNT(CASE WHEN status = 'shipped' THEN 1 END) as shipped_orders,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
                SUM(total_amount) as total_value,
                AVG(total_amount) as average_value
            FROM orders
        """
        try:
            return self.execute_query(query, fetch_one=True)
        except Exception as e:
            logger.error(f"주문 통계 조회 오류: {e}")
            return {}
    
    def get_order_with_items(self, order_id):
        """주문과 아이템을 함께 조회"""
        try:
            order = self.get_order_by_id(order_id)
            if order:
                items = self.get_order_items(order_id)
                order['items'] = items
            return order
        except Exception as e:
            logger.error(f"주문 전체 조회 오류: {e}")
            return None
    
    def get_filtered_orders(self, status_filter=None, customer_filter=None, date_from=None, date_to=None, search_term=None):
        """필터링된 주문 목록 조회 (기존 CSV 매니저와 완전 호환)"""
        try:
            base_query = "SELECT * FROM orders"
            conditions = []
            params = []
            
            if status_filter and status_filter != "전체":
                conditions.append("status = %s")
                params.append(status_filter)
            
            if customer_filter:
                conditions.append("(customer_company_name ILIKE %s OR customer_id ILIKE %s)")
                customer_param = f"%{customer_filter}%"
                params.extend([customer_param, customer_param])
            
            if date_from:
                conditions.append("order_date >= %s")
                params.append(date_from)
            
            if date_to:
                conditions.append("order_date <= %s")
                params.append(date_to)
            
            if search_term:
                conditions.append("""
                    (order_number ILIKE %s OR 
                     customer_company_name ILIKE %s OR 
                     project_name ILIKE %s OR 
                     notes ILIKE %s)
                """)
                search_param = f"%{search_term}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            if conditions:
                query = f"{base_query} WHERE {' AND '.join(conditions)}"
            else:
                query = base_query
            
            query += " ORDER BY order_date DESC"
            
            result = self.execute_query(query, params, fetch_all=True)
            return pd.DataFrame(result) if result else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"필터링된 주문 조회 오류: {e}")
            return pd.DataFrame()
