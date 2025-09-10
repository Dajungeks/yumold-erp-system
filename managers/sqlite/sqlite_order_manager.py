# -*- coding: utf-8 -*-
"""
SQLite 기반 주문 관리 시스템
견적서에서 주문으로 전환하여 관리하는 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class SQLiteOrderManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 주문 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """주문 관련 테이블 초기화"""
        with self.get_connection() as conn:
            # orders 테이블 (database_manager.py에 이미 정의됨)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    quotation_id TEXT,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT,
                    order_date TEXT,
                    requested_delivery_date TEXT,
                    confirmed_delivery_date TEXT,
                    total_amount REAL,
                    currency TEXT DEFAULT 'VND',
                    order_status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'pending',
                    payment_terms TEXT,
                    special_instructions TEXT,
                    created_by TEXT,
                    notes TEXT,
                    sales_rep TEXT,
                    sales_contact TEXT,
                    sales_phone TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # order_items 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    order_id TEXT NOT NULL,
                    product_code TEXT,
                    product_name TEXT,
                    quantity REAL,
                    unit_price REAL,
                    total_price REAL,
                    currency TEXT,
                    specifications TEXT,
                    delivery_notes TEXT,
                    production_status TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            ''')
            
            # order_status_history 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS order_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id TEXT UNIQUE NOT NULL,
                    order_id TEXT NOT NULL,
                    previous_status TEXT,
                    new_status TEXT,
                    changed_by TEXT,
                    changed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    reason TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            ''')
            
            conn.commit()
            logger.info("주문 관련 테이블 초기화 완료")
    
    def get_delivery_schedule(self):
        """배송 일정을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        order_id,
                        customer_name,
                        requested_delivery_date,
                        confirmed_delivery_date,
                        order_status,
                        total_amount,
                        currency
                    FROM orders 
                    WHERE order_status IN ('confirmed', 'processing', 'ready') 
                    AND (requested_delivery_date IS NOT NULL OR confirmed_delivery_date IS NOT NULL)
                    ORDER BY COALESCE(confirmed_delivery_date, requested_delivery_date) ASC
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"배송 일정 조회 오류: {e}")
            return pd.DataFrame()
    
    def generate_order_id(self):
        """주문 ID를 생성합니다. (ORD + YYYYMMDD + 순서번호)"""
        today = datetime.now().strftime("%Y%m%d")
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM orders 
                WHERE order_id LIKE ?
            ''', (f"ORD{today}%",))
            
            count = cursor.fetchone()[0]
            sequence = count + 1
            
        return f"ORD{today}{sequence:03d}"
    
    def create_order_from_quotation(self, quotation_data, created_by, order_details=None):
        """견적서에서 주문을 생성합니다."""
        try:
            with self.get_connection() as conn:
                order_id = self.generate_order_id()
                
                # 고객 정보 확인 및 가져오기
                customer_company = quotation_data.get('customer_company', '')
                customer_id = None
                
                # 고객 ID 찾기
                if customer_company:
                    cursor = conn.execute('SELECT customer_id FROM customers WHERE company_name = ?', (customer_company,))
                    result = cursor.fetchone()
                    if result:
                        customer_id = result[0]
                        logger.info(f"고객 ID 찾음: {customer_id} for {customer_company}")
                    else:
                        logger.warning(f"고객을 찾을 수 없음: {customer_company}")
                        # 고객이 없으면 기본값으로 생성
                        customer_id = "C_TEMP_001"
                else:
                    logger.error("고객 회사명이 없습니다")
                    customer_id = "C_TEMP_001"
                
                # 기본 주문 정보
                order_data = {
                    'order_id': order_id,
                    'quotation_id': quotation_data.get('quotation_id'),
                    'customer_id': customer_id,
                    'customer_name': customer_company,
                    'order_date': datetime.now().strftime('%Y-%m-%d'),
                    'requested_delivery_date': order_details.get('requested_delivery_date') if order_details else None,
                    'confirmed_delivery_date': None,
                    'total_amount': quotation_data.get('total_incl_vat', quotation_data.get('total_amount_vnd', 0)),
                    'currency': quotation_data.get('currency', 'VND'),
                    'order_status': 'pending',
                    'payment_status': 'pending',
                    'payment_terms': order_details.get('payment_terms') if order_details else '',
                    'special_instructions': order_details.get('special_instructions') if order_details else '',
                    'created_by': created_by,
                    'notes': order_details.get('notes') if order_details else ''
                }
                
                # 주문 기본 정보 삽입
                conn.execute('''
                    INSERT INTO orders (
                        order_id, quotation_id, customer_id, customer_name, order_date,
                        requested_delivery_date, total_amount, currency, order_status,
                        payment_status, payment_terms, special_instructions, created_by, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_data['order_id'], order_data['quotation_id'], 
                    order_data['customer_id'], order_data['customer_name'], 
                    order_data['order_date'], order_data['requested_delivery_date'],
                    order_data['total_amount'], order_data['currency'],
                    order_data['order_status'], order_data['payment_status'],
                    order_data['payment_terms'], order_data['special_instructions'],
                    order_data['created_by'], order_data['notes']
                ))
                
                # 견적서 제품 정보를 주문 아이템으로 변환
                products_json = quotation_data.get('products_json', '[]')
                if isinstance(products_json, str):
                    try:
                        products = json.loads(products_json)
                    except:
                        products = []
                else:
                    products = products_json if isinstance(products_json, list) else []
                
                # 주문 아이템 삽입
                for idx, product in enumerate(products):
                    if isinstance(product, dict):
                        item_id = f"{order_id}_ITEM{idx+1:03d}"
                        
                        conn.execute('''
                            INSERT INTO order_items (
                                item_id, order_id, product_code, product_name,
                                quantity, unit_price, total_price, currency,
                                specifications, production_status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            item_id, order_id,
                            product.get('product_code', ''),
                            product.get('product_name', ''),
                            float(product.get('quantity', 1)),
                            float(product.get('unit_price', 0)),
                            float(product.get('total_price', 0)),
                            product.get('unit_price_currency', 'VND'),
                            product.get('description', ''),
                            'pending'
                        ))
                
                # 상태 변경 이력 추가
                self._add_status_history(conn, order_id, None, 'pending', created_by, '주문 생성')
                
                conn.commit()
                logger.info(f"주문 생성 성공: {order_id}")
                return order_id
                
        except Exception as e:
            logger.error(f"주문 생성 실패: {str(e)}")
            logger.error(f"견적서 데이터: {quotation_data}")
            logger.error(f"고객 회사명: {quotation_data.get('customer_company', 'None')}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None
    
    def _add_status_history(self, conn, order_id, previous_status, new_status, changed_by, notes=""):
        """주문 상태 변경 이력 추가"""
        history_id = f"{order_id}_HIST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn.execute('''
            INSERT INTO order_status_history (
                history_id, order_id, previous_status, new_status, 
                changed_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (history_id, order_id, previous_status, new_status, changed_by, notes))
    
    def get_all_orders(self):
        """모든 주문을 DataFrame으로 반환 (기존 CSV 매니저와 동일한 인터페이스)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        order_id, quotation_id, customer_id, customer_name,
                        order_date, requested_delivery_date, confirmed_delivery_date,
                        total_amount, currency, order_status, payment_status,
                        payment_terms, special_instructions, created_by,
                        notes, created_date as last_updated
                    FROM orders
                    ORDER BY created_date DESC
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"주문 목록 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_order_by_id(self, order_id):
        """특정 주문 정보 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM orders WHERE order_id = ?
                ''', (order_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"주문 조회 오류: {str(e)}")
            return None
    
    def update_order(self, order_id, update_data):
        """주문 정보 업데이트"""
        try:
            with self.get_connection() as conn:
                set_clauses = []
                values = []
                
                # 업데이트 가능한 필드 확장
                allowed_fields = [
                    'customer_name', 'order_date', 'total_amount', 'currency', 'payment_terms', 
                    'special_instructions', 'order_status', 'payment_status', 'factory_etd',
                    'logistics_etd', 'customs_eta', 'ymv_eta', 'transport_method', 'remarks'
                ]
                
                for key, value in update_data.items():
                    if key in allowed_fields:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if set_clauses:
                    query = f"UPDATE orders SET {', '.join(set_clauses)}, updated_date = CURRENT_TIMESTAMP WHERE order_id = ?"
                    values.append(order_id)
                    
                    conn.execute(query, values)
                    conn.commit()
                    logger.info(f"주문 업데이트 성공: {order_id}")
                    return True
                else:
                    logger.warning("업데이트할 필드가 없습니다")
                    return False
                    
        except Exception as e:
            logger.error(f"주문 업데이트 실패: {str(e)}")
            return False
    

    
    def update_payment_status(self, order_id, new_payment_status, updated_by):
        """결제 상태 업데이트"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE orders SET payment_status = ?, updated_date = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                ''', (new_payment_status, order_id))
                
                conn.commit()
                logger.info(f"결제 상태 업데이트: {order_id} → {new_payment_status}")
                return True
                
        except Exception as e:
            logger.error(f"결제 상태 업데이트 실패: {str(e)}")
            return False
    
    def update_delivery_date(self, order_id, delivery_date, updated_by):
        """배송일 업데이트"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE orders SET confirmed_delivery_date = ?, updated_date = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                ''', (delivery_date, order_id))
                
                conn.commit()
                logger.info(f"배송일 업데이트: {order_id} → {delivery_date}")
                return True
                
        except Exception as e:
            logger.error(f"배송일 업데이트 실패: {str(e)}")
            return False

    def create_dual_mode_order(self, order_data):
        """듀얼 모드 주문 생성 (판매재고/재고 모드)"""
        try:
            logger.info(f"듀얼 모드 주문 생성 시작: {order_data}")
            with self.get_connection() as conn:
                # 주문 ID 생성
                order_id = f"ORD{datetime.now().strftime('%Y%m%d')}" + f"{self._get_next_order_sequence():03d}"
                
                if order_data['mode'] == 'sales_inventory':
                    # 판매재고 모드
                    quotation_data = order_data['quotation_data']
                    
                    conn.execute('''
                        INSERT INTO orders (
                            order_id, quotation_id, customer_id, customer_name,
                            order_date, total_amount, currency, order_status,
                            payment_status, created_by, notes,
                            supplier_name, factory_etd, logistics_etd, transport_method,
                            customs_eta, ymv_eta, delivery_target, customer_delivery_date, remarks,
                            sales_rep, sales_contact, sales_phone
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order_id,
                        quotation_data.get('quotation_number'),
                        self._get_customer_id_by_company(conn, quotation_data.get('customer_company')),
                        quotation_data.get('customer_company'),
                        datetime.now().strftime('%Y-%m-%d'),
                        quotation_data.get('total_incl_vat', quotation_data.get('total_amount', 0)),
                        quotation_data.get('currency', 'VND'),
                        'pending',
                        'pending',
                        order_data['created_by'],
                        f"판매재고 주문 - {quotation_data.get('quotation_number')}",
                        order_data['supplier_name'],
                        order_data['factory_etd'],
                        order_data['logistics_etd'],
                        order_data['transport_method'],
                        order_data['customs_eta'],
                        order_data.get('customer_delivery_date'),  # ymv_eta로 사용
                        order_data['delivery_target'],
                        order_data.get('customer_delivery_date'),
                        order_data.get('remarks', ''),
                        order_data.get('sales_rep', ''),
                        order_data.get('sales_contact', ''),
                        order_data.get('sales_phone', '')
                    ))
                    
                elif order_data['mode'] == 'inventory':
                    # 재고 모드
                    product_data = order_data['product_data']
                    
                    conn.execute('''
                        INSERT INTO orders (
                            order_id, customer_id, customer_name, order_date,
                            total_amount, currency, order_status, payment_status,
                            created_by, notes, supplier_name, factory_etd,
                            logistics_etd, transport_method, customs_eta, ymv_eta,
                            remarks, product_code, product_name,
                            sales_rep, sales_contact, sales_phone
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order_id,
                        'INVENTORY',  # 재고 주문은 특별한 customer_id
                        f"재고 주문 - {product_data.get('product_code')}",
                        datetime.now().strftime('%Y-%m-%d'),
                        product_data.get('supply_price', 0),
                        product_data.get('supply_currency', 'USD'),
                        'pending',
                        'pending',
                        order_data['created_by'],
                        f"재고 주문 - {product_data.get('product_code')}",
                        order_data['supplier_name'],
                        order_data['factory_etd'],
                        order_data['logistics_etd'],
                        order_data['transport_method'],
                        order_data['customs_eta'],
                        order_data['ymv_eta'],
                        order_data.get('remarks', ''),
                        product_data.get('product_code'),
                        product_data.get('product_name'),
                        order_data.get('sales_rep', ''),
                        order_data.get('sales_contact', ''),
                        order_data.get('sales_phone', '')
                    ))
                
                # 상태 변경 이력 추가
                self._add_status_history(conn, order_id, None, 'pending', order_data['created_by'], f"{order_data['mode']} 모드 주문 생성")
                
                conn.commit()
                logger.info(f"듀얼 모드 주문 생성 성공: {order_id} ({order_data['mode']})")
                return order_id
                
        except Exception as e:
            logger.error(f"듀얼 모드 주문 생성 실패: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None
    
    def _get_next_order_sequence(self):
        """오늘 날짜 기준 다음 주문 시퀀스 번호"""
        try:
            with self.get_connection() as conn:
                today = datetime.now().strftime('%Y%m%d')
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM orders WHERE order_id LIKE ?",
                    (f"ORD{today}%",)
                )
                count = cursor.fetchone()[0]
                return count + 1
        except:
            return 1
    
    def _get_customer_id_by_company(self, conn, company_name):
        """회사명으로 고객 ID 찾기"""
        if not company_name:
            return None
        
        cursor = conn.execute('SELECT customer_id FROM customers WHERE company_name = ?', (company_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_order_items(self, order_id):
        """주문의 아이템 목록 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM order_items 
                    WHERE order_id = ?
                    ORDER BY item_id
                '''
                
                df = pd.read_sql_query(query, conn, params=[order_id,])
                return df
                
        except Exception as e:
            logger.error(f"주문 아이템 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def update_order_status(self, order_id, new_status, changed_by, notes=""):
        """주문 상태 업데이트"""
        try:
            with self.get_connection() as conn:
                # 현재 상태 조회
                cursor = conn.execute('SELECT order_status FROM orders WHERE order_id = ?', (order_id,))
                current_row = cursor.fetchone()
                
                if not current_row:
                    return False
                
                previous_status = current_row['order_status']
                
                # 상태 업데이트
                conn.execute('''
                    UPDATE orders 
                    SET order_status = ?, updated_date = CURRENT_TIMESTAMP 
                    WHERE order_id = ?
                ''', (new_status, order_id))
                
                # 이력 추가
                self._add_status_history(conn, order_id, previous_status, new_status, changed_by, notes)
                
                conn.commit()
                logger.info(f"주문 상태 업데이트 성공: {order_id} -> {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"주문 상태 업데이트 실패: {str(e)}")
            return False
    
    def delete_order(self, order_id):
        """주문 삭제 (연관 데이터 모두 삭제)"""
        try:
            with self.get_connection() as conn:
                # 트랜잭션으로 안전하게 삭제
                conn.execute('DELETE FROM order_status_history WHERE order_id = ?', (order_id,))
                conn.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
                conn.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
                
                conn.commit()
                logger.info(f"주문 삭제 성공: {order_id}")
                return True
                
        except Exception as e:
            logger.error(f"주문 삭제 실패: {str(e)}")
            return False
    
    def search_orders(self, search_term=""):
        """주문 검색 (ID 또는 고객명)"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM orders 
                    WHERE order_id LIKE ? OR customer_name LIKE ?
                    ORDER BY created_date DESC
                '''
                
                search_pattern = f"%{search_term}%"
                df = pd.read_sql_query(query, conn, params=[search_pattern, search_pattern])
                return df
                
        except Exception as e:
            logger.error(f"주문 검색 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_orders_by_status(self, status):
        """특정 상태의 주문들 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM orders 
                    WHERE order_status = ?
                    ORDER BY created_date DESC
                '''
                
                df = pd.read_sql_query(query, conn, params=[status,])
                return df
                
        except Exception as e:
            logger.error(f"상태별 주문 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_orders_by_date_range(self, start_date, end_date):
        """날짜 범위별 주문 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM orders 
                    WHERE order_date BETWEEN ? AND ?
                    ORDER BY order_date DESC
                '''
                
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                return df
                
        except Exception as e:
            logger.error(f"날짜별 주문 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_filtered_orders(self, status_filter=None, customer_filter=None, date_from=None, date_to=None, search_term=None):
        """필터링된 주문 목록 조회 (기존 CSV 매니저와 완전 호환)"""
        try:
            with self.get_connection() as conn:
                base_query = "SELECT * FROM orders"
                conditions = []
                params = []
                
                if status_filter and status_filter != "전체":
                    conditions.append("order_status = ?")
                    params.append(status_filter)
                
                if customer_filter:
                    conditions.append("(customer_name LIKE ? OR customer_id LIKE ?)")
                    customer_param = f"%{customer_filter}%"
                    params.extend([customer_param, customer_param])
                
                if date_from:
                    conditions.append("DATE(order_date) >= ?")
                    params.append(date_from)
                
                if date_to:
                    conditions.append("DATE(order_date) <= ?")
                    params.append(date_to)
                
                if search_term:
                    conditions.append("(order_id LIKE ? OR customer_name LIKE ?)")
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param])
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=list(params) if params else None)
                
                # CSV 매니저와의 호환성을 위해 딕셔너리 리스트로 반환하는 옵션 추가
                if hasattr(self, '_return_dict_records') and getattr(self, '_return_dict_records', False):
                    return df.to_dict('records') if not df.empty else []
                
                return df
                
        except Exception as e:
            logger.error(f"필터링된 주문 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_order_statistics(self):
        """주문 통계 정보"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(CASE WHEN order_status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
                        SUM(CASE WHEN order_status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_orders,
                        SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
                        SUM(total_amount) as total_value,
                        AVG(total_amount) as average_value
                    FROM orders
                ''')
                
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"주문 통계 조회 오류: {str(e)}")
            return {}