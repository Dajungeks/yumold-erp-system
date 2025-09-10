# -*- coding: utf-8 -*-
"""
SQLite 기반 배송 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class SQLiteShippingManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 배송 매니저 초기화"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """배송 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS shipments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shipping_id TEXT UNIQUE NOT NULL,
                        quotation_id TEXT,
                        quotation_number TEXT,
                        customer_id TEXT,
                        customer_name TEXT,
                        customer_contact TEXT,
                        customer_address TEXT,
                        shipping_date TEXT,
                        delivery_date TEXT,
                        estimated_delivery TEXT,
                        shipping_method TEXT,
                        shipping_company TEXT,
                        tracking_number TEXT,
                        shipping_cost REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        weight REAL,
                        dimensions TEXT,
                        package_count INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'preparing',
                        notes TEXT,
                        products_json TEXT,
                        created_by TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 배송 추적 이벤트 테이블
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS shipping_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shipping_id TEXT NOT NULL,
                        event_date TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_description TEXT,
                        location TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (shipping_id) REFERENCES shipments(shipping_id)
                    )
                ''')
                
                # 배송업체 관리 테이블
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS shipping_companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT UNIQUE NOT NULL,
                        company_code TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        website TEXT,
                        service_area TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 기본 배송업체 데이터 삽입
                self._insert_default_companies(conn)
                
                conn.commit()
                logger.info("배송 테이블 초기화 완료")
        except Exception as e:
            logger.error(f"배송 테이블 초기화 오류: {e}")
    
    def generate_shipping_id(self):
        """새 배송 ID 생성"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT shipping_id FROM shipments 
                    WHERE shipping_id LIKE 'SH%' 
                    ORDER BY shipping_id DESC LIMIT 1
                ''')
                result = cursor.fetchone()
                
                if result:
                    last_id = result['shipping_id']
                    number = int(last_id[2:]) + 1
                else:
                    number = 1
                
                return f"SH{number:06d}"
        except Exception as e:
            logger.error(f"배송 ID 생성 오류: {e}")
            return f"SH{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_all_shipments(self):
        """모든 배송 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT shipping_id, quotation_id, quotation_number, customer_id, customer_name,
                           customer_contact, customer_address, shipping_date, delivery_date,
                           estimated_delivery, shipping_method, shipping_company, tracking_number,
                           shipping_cost, currency, weight, dimensions, package_count, status,
                           notes, created_by, created_date, updated_date
                    FROM shipments
                    ORDER BY created_date DESC
                ''')
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"배송 목록 조회 오류: {e}")
            return []
    
    def get_shipments_dataframe(self):
        """배송 정보를 DataFrame으로 가져옵니다."""
        try:
            shipments_list = self.get_all_shipments()
            if shipments_list:
                return pd.DataFrame(shipments_list)
            else:
                return pd.DataFrame({
                    'shipping_id': [],
                    'quotation_number': [],
                    'customer_name': [],
                    'shipping_date': [],
                    'delivery_date': [],
                    'status': [],
                    'tracking_number': [],
                    'shipping_company': []
                })
        except Exception as e:
            logger.error(f"배송 DataFrame 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_shipment_by_id(self, shipping_id):
        """특정 배송 정보를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM shipments WHERE shipping_id = ?
                ''', (str(shipping_id),))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"배송 조회 오류: {e}")
            return None
    
    def add_shipment(self, shipment_data):
        """새 배송을 추가합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                shipping_id = shipment_data.get('shipping_id') or self.generate_shipping_id()
                
                # 제품 정보를 JSON으로 저장
                products_json = json.dumps(shipment_data.get('products', []), ensure_ascii=False)
                
                conn.execute('''
                    INSERT INTO shipments (
                        shipping_id, quotation_id, quotation_number, customer_id, customer_name,
                        customer_contact, customer_address, shipping_date, delivery_date,
                        estimated_delivery, shipping_method, shipping_company, tracking_number,
                        shipping_cost, currency, weight, dimensions, package_count, status,
                        notes, products_json, created_by, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    shipping_id,
                    shipment_data.get('quotation_id', ''),
                    shipment_data.get('quotation_number', ''),
                    shipment_data.get('customer_id', ''),
                    shipment_data.get('customer_name', ''),
                    shipment_data.get('customer_contact', ''),
                    shipment_data.get('customer_address', ''),
                    shipment_data.get('shipping_date', ''),
                    shipment_data.get('delivery_date', ''),
                    shipment_data.get('estimated_delivery', ''),
                    shipment_data.get('shipping_method', ''),
                    shipment_data.get('shipping_company', ''),
                    shipment_data.get('tracking_number', ''),
                    float(shipment_data.get('shipping_cost', 0)),
                    shipment_data.get('currency', 'VND'),
                    float(shipment_data.get('weight', 0)),
                    shipment_data.get('dimensions', ''),
                    int(shipment_data.get('package_count', 1)),
                    shipment_data.get('status', 'preparing'),
                    shipment_data.get('notes', ''),
                    products_json,
                    shipment_data.get('created_by', ''),
                    current_time,
                    current_time
                ))
                
                # 배송 생성 이벤트 추가
                self.add_shipping_event(
                    shipping_id, 
                    current_time, 
                    'created', 
                    '배송이 생성되었습니다.',
                    ''
                )
                
                conn.commit()
                return shipping_id
        except Exception as e:
            logger.error(f"배송 추가 오류: {e}")
            return None
    
    def update_shipment(self, shipping_id, shipment_data):
        """배송 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 제품 정보를 JSON으로 저장
                products_json = json.dumps(shipment_data.get('products', []), ensure_ascii=False)
                
                conn.execute('''
                    UPDATE shipments SET
                        quotation_id = ?, quotation_number = ?, customer_id = ?, customer_name = ?,
                        customer_contact = ?, customer_address = ?, shipping_date = ?, delivery_date = ?,
                        estimated_delivery = ?, shipping_method = ?, shipping_company = ?, tracking_number = ?,
                        shipping_cost = ?, currency = ?, weight = ?, dimensions = ?, package_count = ?,
                        status = ?, notes = ?, products_json = ?, updated_date = ?
                    WHERE shipping_id = ?
                ''', (
                    shipment_data.get('quotation_id', ''),
                    shipment_data.get('quotation_number', ''),
                    shipment_data.get('customer_id', ''),
                    shipment_data.get('customer_name', ''),
                    shipment_data.get('customer_contact', ''),
                    shipment_data.get('customer_address', ''),
                    shipment_data.get('shipping_date', ''),
                    shipment_data.get('delivery_date', ''),
                    shipment_data.get('estimated_delivery', ''),
                    shipment_data.get('shipping_method', ''),
                    shipment_data.get('shipping_company', ''),
                    shipment_data.get('tracking_number', ''),
                    float(shipment_data.get('shipping_cost', 0)),
                    shipment_data.get('currency', 'VND'),
                    float(shipment_data.get('weight', 0)),
                    shipment_data.get('dimensions', ''),
                    int(shipment_data.get('package_count', 1)),
                    shipment_data.get('status', 'preparing'),
                    shipment_data.get('notes', ''),
                    products_json,
                    current_time,
                    str(shipping_id)
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"배송 업데이트 오류: {e}")
            return False
    
    def delete_shipment(self, shipping_id):
        """배송을 삭제합니다."""
        try:
            with self.get_connection() as conn:
                # 관련 이벤트도 함께 삭제
                conn.execute('DELETE FROM shipping_events WHERE shipping_id = ?', (str(shipping_id),))
                conn.execute('DELETE FROM shipments WHERE shipping_id = ?', (str(shipping_id),))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"배송 삭제 오류: {e}")
            return False
    
    def add_shipping_event(self, shipping_id, event_date, event_type, description, location=''):
        """배송 추적 이벤트를 추가합니다."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO shipping_events (
                        shipping_id, event_date, event_type, event_description, location
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (shipping_id, event_date, event_type, description, location))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"배송 이벤트 추가 오류: {e}")
            return False
    
    def get_shipping_events(self, shipping_id):
        """특정 배송의 추적 이벤트를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT event_date, event_type, event_description, location
                    FROM shipping_events
                    WHERE shipping_id = ?
                    ORDER BY event_date DESC
                ''', (str(shipping_id),))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"배송 이벤트 조회 오류: {e}")
            return []
    
    def get_filtered_shipments(self, status_filter=None, company_filter=None, date_filter=None, search_term=None):
        """필터링된 배송 목록을 DataFrame으로 가져옵니다."""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT shipping_id, quotation_number, customer_name, shipping_date,
                           delivery_date, estimated_delivery, shipping_method, shipping_company,
                           tracking_number, status, shipping_cost, currency, created_date
                    FROM shipments
                    WHERE 1=1
                '''
                params = []
                
                if status_filter:
                    query += " AND status = ?"
                    params.append(status_filter)
                
                if company_filter:
                    query += " AND shipping_company = ?"
                    params.append(company_filter)
                
                if date_filter:
                    query += " AND DATE(shipping_date) = ?"
                    params.append(date_filter)
                
                if search_term:
                    query += " AND (customer_name LIKE ? OR quotation_number LIKE ? OR tracking_number LIKE ?)"
                    search_param = f"%{search_term}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY created_date DESC"
                
                cursor = conn.execute(query, params)
                results = cursor.fetchall()
                shipments_list = [dict(row) for row in results]
                
                if shipments_list:
                    return pd.DataFrame(shipments_list)
                else:
                    return pd.DataFrame({
                        'shipping_id': [],
                        'quotation_number': [],
                        'customer_name': [],
                        'shipping_date': [],
                        'delivery_date': [],
                        'status': [],
                        'tracking_number': [],
                        'shipping_company': []
                    })
        except Exception as e:
            logger.error(f"필터링된 배송 목록 조회 오류: {e}")
            return pd.DataFrame()
    
    def _insert_default_companies(self, conn):
        """기본 배송업체 데이터 삽입"""
        default_companies = [
            ("한진택배", "HANJIN", "1588-0011", "cs@hanjin.co.kr", "https://www.hanjin.co.kr", "국내"),
            ("CJ대한통운", "CJ", "1588-1255", "cs@cjlogistics.com", "https://www.cjlogistics.com", "국내/국제"),
            ("로젠택배", "LOGEN", "1588-9988", "cs@ilogen.com", "https://www.ilogen.com", "국내"),
            ("우체국택배", "KOREAPOST", "1588-1300", "cs@epost.go.kr", "https://service.epost.go.kr", "국내"),
            ("DHL", "DHL", "1588-0001", "info@dhl.com", "https://www.dhl.co.kr", "국제"),
            ("FedEx", "FEDEX", "080-023-8000", "info@fedex.com", "https://www.fedex.com/kr", "국제"),
            ("UPS", "UPS", "1588-6886", "info@ups.com", "https://www.ups.com/kr", "국제"),
            ("TNT", "TNT", "1588-0588", "info@tnt.com", "https://www.tnt.com/kr", "국제")
        ]
        
        for company_data in default_companies:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO shipping_companies 
                    (company_name, company_code, contact_phone, contact_email, website, service_area, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, 'system')
                ''', company_data)
            except Exception as e:
                logger.warning(f"기본 배송업체 삽입 오류 ({company_data[0]}): {e}")
    
    def get_shipping_companies(self):
        """활성화된 배송 회사 목록을 가져옵니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT company_name FROM shipping_companies 
                    WHERE is_active = 1
                    ORDER BY company_name
                ''')
                results = cursor.fetchall()
                return [row['company_name'] for row in results]
        except Exception as e:
            logger.error(f"배송 회사 목록 조회 오류: {e}")
            # 오류 시 기본 목록 반환
            return ["한진택배", "CJ대한통운", "로젠택배", "우체국택배", "DHL", "FedEx", "UPS", "TNT"]
    
    def get_shipping_statistics(self):
        """배송 통계를 가져옵니다."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # 전체 배송 수
                cursor = conn.execute('SELECT COUNT(*) FROM shipments')
                stats['total_shipments'] = cursor.fetchone()[0]
                
                # 상태별 통계
                cursor = conn.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM shipments 
                    GROUP BY status
                ''')
                stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # 배송 회사별 통계
                cursor = conn.execute('''
                    SELECT shipping_company, COUNT(*) as count 
                    FROM shipments 
                    WHERE shipping_company IS NOT NULL AND shipping_company != ''
                    GROUP BY shipping_company
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                stats['by_company'] = {row['shipping_company']: row['count'] for row in cursor.fetchall()}
                
                # 월별 배송 통계
                cursor = conn.execute('''
                    SELECT strftime('%Y-%m', shipping_date) as month, COUNT(*) as count
                    FROM shipments
                    WHERE shipping_date IS NOT NULL AND shipping_date != ''
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                ''')
                stats['by_month'] = {row['month']: row['count'] for row in cursor.fetchall()}
                
                # 평균 배송비
                cursor = conn.execute('SELECT AVG(shipping_cost) FROM shipments WHERE shipping_cost > 0')
                result = cursor.fetchone()[0]
                stats['average_cost'] = float(result) if result else 0
                
                return stats
        except Exception as e:
            logger.error(f"배송 통계 조회 오류: {e}")
            return {
                'total_shipments': 0,
                'by_status': {},
                'by_company': {},
                'by_month': {},
                'average_cost': 0
            }
    
    def get_all_shipping_companies(self):
        """모든 배송 회사 정보를 가져옵니다 (관리용)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT id, company_name, company_code, contact_phone, contact_email, 
                           website, service_area, is_active, created_by, created_date
                    FROM shipping_companies 
                    ORDER BY company_name
                ''')
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"전체 배송 회사 조회 오류: {e}")
            return []
    
    def add_shipping_company(self, company_data, created_by=''):
        """새 배송업체를 추가합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('''
                    INSERT INTO shipping_companies (
                        company_name, company_code, contact_phone, contact_email, 
                        website, service_area, created_by, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company_data.get('company_name', ''),
                    company_data.get('company_code', ''),
                    company_data.get('contact_phone', ''),
                    company_data.get('contact_email', ''),
                    company_data.get('website', ''),
                    company_data.get('service_area', ''),
                    created_by,
                    current_time,
                    current_time
                ))
                
                conn.commit()
                logger.info(f"배송업체 추가 완료: {company_data.get('company_name')}")
                return True
        except Exception as e:
            logger.error(f"배송업체 추가 오류: {e}")
            return False
    
    def update_shipping_company(self, company_id, company_data):
        """배송업체 정보를 업데이트합니다."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('''
                    UPDATE shipping_companies SET
                        company_name = ?, company_code = ?, contact_phone = ?, 
                        contact_email = ?, website = ?, service_area = ?, 
                        is_active = ?, updated_date = ?
                    WHERE id = ?
                ''', (
                    company_data.get('company_name', ''),
                    company_data.get('company_code', ''),
                    company_data.get('contact_phone', ''),
                    company_data.get('contact_email', ''),
                    company_data.get('website', ''),
                    company_data.get('service_area', ''),
                    int(company_data.get('is_active', 1)),
                    current_time,
                    company_id
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"배송업체 업데이트 오류: {e}")
            return False
    
    def delete_shipping_company(self, company_id):
        """배송업체를 삭제합니다 (비활성화)."""
        try:
            with self.get_connection() as conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 완전 삭제 대신 비활성화
                conn.execute('''
                    UPDATE shipping_companies SET
                        is_active = 0, updated_date = ?
                    WHERE id = ?
                ''', (current_time, company_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"배송업체 삭제 오류: {e}")
            return False
    
    def get_quotation_shipping_data(self, quotation_id, quotation_manager):
        """견적서 ID로 배송에 필요한 데이터를 가져옵니다."""
        try:
            if quotation_manager and hasattr(quotation_manager, 'get_quotation_by_id'):
                quotation = quotation_manager.get_quotation_by_id(quotation_id)
                if quotation:
                    # 견적서에서 배송에 필요한 정보 추출
                    shipping_data = {
                        'quotation_id': quotation_id,
                        'quotation_number': quotation.get('quotation_number', quotation.get('quotation_id', '')),
                        'customer_id': quotation.get('customer_id', ''),
                        'customer_name': quotation.get('customer_name', ''),
                        'customer_contact': quotation.get('customer_phone', quotation.get('customer_contact', '')),
                        'customer_address': quotation.get('customer_address', ''),
                        'customer_email': quotation.get('customer_email', ''),
                        'products': quotation.get('products', []),
                        'total_amount': quotation.get('total_amount', 0),
                        'currency': quotation.get('currency', 'VND')
                    }
                    return shipping_data
            return None
        except Exception as e:
            logger.error(f"견적서 배송 데이터 조회 오류: {e}")
            return None
    
    def check_admin_permission(self, user_role):
        """법인장 권한 확인"""
        return user_role in ['법인장', 'admin', 'CEO']