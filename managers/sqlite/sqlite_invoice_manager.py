"""
SQLite 인보이스 관리자 - 인보이스 생성, 관리
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

class SQLiteInvoiceManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 인보이스 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id TEXT PRIMARY KEY,
                        invoice_number TEXT UNIQUE NOT NULL,
                        order_id TEXT,
                        quotation_id TEXT,
                        customer_id TEXT NOT NULL,
                        customer_name TEXT,
                        customer_address TEXT,
                        customer_contact TEXT,
                        issue_date TEXT NOT NULL,
                        due_date TEXT,
                        payment_terms TEXT DEFAULT '30 days',
                        subtotal REAL DEFAULT 0,
                        tax_rate REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        discount_rate REAL DEFAULT 0,
                        discount_amount REAL DEFAULT 0,
                        total_amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        amount_vnd REAL DEFAULT 0,
                        amount_usd REAL DEFAULT 0,
                        exchange_rate REAL DEFAULT 1,
                        status TEXT DEFAULT 'draft',
                        payment_status TEXT DEFAULT 'pending',
                        payment_date TEXT,
                        payment_method TEXT,
                        payment_reference TEXT,
                        notes TEXT,
                        terms_conditions TEXT,
                        created_by TEXT,
                        approved_by TEXT,
                        approval_date TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인보이스 항목 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invoice_items (
                        item_id TEXT PRIMARY KEY,
                        invoice_id TEXT NOT NULL,
                        product_code TEXT,
                        product_name TEXT NOT NULL,
                        description TEXT,
                        quantity INTEGER DEFAULT 1,
                        unit_price REAL DEFAULT 0,
                        discount_rate REAL DEFAULT 0,
                        discount_amount REAL DEFAULT 0,
                        line_total REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        tax_rate REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
                    )
                ''')
                
                # 인보이스 결제 내역 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invoice_payments (
                        payment_id TEXT PRIMARY KEY,
                        invoice_id TEXT NOT NULL,
                        payment_date TEXT NOT NULL,
                        payment_amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        payment_method TEXT DEFAULT 'bank_transfer',
                        payment_reference TEXT,
                        exchange_rate REAL DEFAULT 1,
                        amount_vnd REAL DEFAULT 0,
                        amount_usd REAL DEFAULT 0,
                        notes TEXT,
                        created_by TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
                    )
                ''')
                
                conn.commit()
                logger.info("인보이스 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_invoices(self, status=None, customer_id=None, date_from=None, date_to=None):
        """인보이스 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM invoices WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if customer_id:
                    query += " AND customer_id = ?"
                    params.append(customer_id)
                if date_from:
                    query += " AND issue_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND issue_date <= ?"
                    params.append(date_to)
                
                query += " ORDER BY issue_date DESC, created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"인보이스 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_invoice(self, invoice_data, items_data=None):
        """인보이스 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['invoice_id', 'invoice_number', 'customer_id', 'issue_date']
                for field in required_fields:
                    if field not in invoice_data or not invoice_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 환율 계산
                currency = invoice_data.get('currency', 'VND')
                exchange_rate = invoice_data.get('exchange_rate', 1)
                total_amount = invoice_data.get('total_amount', 0)
                
                if currency == 'VND':
                    amount_vnd = total_amount
                    amount_usd = total_amount / exchange_rate if exchange_rate > 0 else 0
                else:  # USD
                    amount_usd = total_amount
                    amount_vnd = total_amount * exchange_rate
                
                invoice_record = {
                    'invoice_id': invoice_data['invoice_id'],
                    'invoice_number': invoice_data['invoice_number'],
                    'order_id': invoice_data.get('order_id', ''),
                    'quotation_id': invoice_data.get('quotation_id', ''),
                    'customer_id': invoice_data['customer_id'],
                    'customer_name': invoice_data.get('customer_name', ''),
                    'customer_address': invoice_data.get('customer_address', ''),
                    'customer_contact': invoice_data.get('customer_contact', ''),
                    'issue_date': invoice_data['issue_date'],
                    'due_date': invoice_data.get('due_date', ''),
                    'payment_terms': invoice_data.get('payment_terms', '30 days'),
                    'subtotal': invoice_data.get('subtotal', 0),
                    'tax_rate': invoice_data.get('tax_rate', 0),
                    'tax_amount': invoice_data.get('tax_amount', 0),
                    'discount_rate': invoice_data.get('discount_rate', 0),
                    'discount_amount': invoice_data.get('discount_amount', 0),
                    'total_amount': total_amount,
                    'currency': currency,
                    'amount_vnd': amount_vnd,
                    'amount_usd': amount_usd,
                    'exchange_rate': exchange_rate,
                    'status': invoice_data.get('status', 'draft'),
                    'payment_status': invoice_data.get('payment_status', 'pending'),
                    'payment_date': invoice_data.get('payment_date', ''),
                    'payment_method': invoice_data.get('payment_method', ''),
                    'payment_reference': invoice_data.get('payment_reference', ''),
                    'notes': invoice_data.get('notes', ''),
                    'terms_conditions': invoice_data.get('terms_conditions', ''),
                    'created_by': invoice_data.get('created_by', ''),
                    'approved_by': invoice_data.get('approved_by', ''),
                    'approval_date': invoice_data.get('approval_date', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO invoices (
                        invoice_id, invoice_number, order_id, quotation_id, customer_id,
                        customer_name, customer_address, customer_contact, issue_date, due_date,
                        payment_terms, subtotal, tax_rate, tax_amount, discount_rate,
                        discount_amount, total_amount, currency, amount_vnd, amount_usd,
                        exchange_rate, status, payment_status, payment_date, payment_method,
                        payment_reference, notes, terms_conditions, created_by, approved_by,
                        approval_date, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(invoice_record.values()))
                
                # 인보이스 항목 추가
                if items_data:
                    for item in items_data:
                        item_record = {
                            'item_id': item.get('item_id', f"{invoice_data['invoice_id']}_ITEM_{len(items_data)}"),
                            'invoice_id': invoice_data['invoice_id'],
                            'product_code': item.get('product_code', ''),
                            'product_name': item.get('product_name', ''),
                            'description': item.get('description', ''),
                            'quantity': item.get('quantity', 1),
                            'unit_price': item.get('unit_price', 0),
                            'discount_rate': item.get('discount_rate', 0),
                            'discount_amount': item.get('discount_amount', 0),
                            'line_total': item.get('line_total', 0),
                            'currency': item.get('currency', currency),
                            'tax_rate': item.get('tax_rate', 0),
                            'tax_amount': item.get('tax_amount', 0),
                            'created_date': current_time
                        }
                        
                        cursor.execute('''
                            INSERT INTO invoice_items (
                                item_id, invoice_id, product_code, product_name, description,
                                quantity, unit_price, discount_rate, discount_amount, line_total,
                                currency, tax_rate, tax_amount, created_date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', tuple(item_record.values()))
                
                conn.commit()
                logger.info(f"인보이스 추가 완료: {invoice_data['invoice_id']}")
                return True
                
        except Exception as e:
            logger.error(f"인보이스 추가 실패: {str(e)}")
            return False

    def update_invoice(self, invoice_id, updates):
        """인보이스 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [invoice_id]
                
                cursor.execute(f'''
                    UPDATE invoices 
                    SET {set_clause}
                    WHERE invoice_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"인보이스 수정 완료: {invoice_id}")
                    return True
                else:
                    logger.warning(f"수정할 인보이스 없음: {invoice_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"인보이스 수정 실패: {str(e)}")
            return False

    def get_invoice_items(self, invoice_id):
        """인보이스 항목 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY created_date"
                df = pd.read_sql_query(query, conn, params=[invoice_id])
                return df
                
        except Exception as e:
            logger.error(f"인보이스 항목 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_payment(self, payment_data):
        """결제 내역 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['payment_id', 'invoice_id', 'payment_date', 'payment_amount']
                for field in required_fields:
                    if field not in payment_data or not payment_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 환율 계산
                currency = payment_data.get('currency', 'VND')
                exchange_rate = payment_data.get('exchange_rate', 1)
                payment_amount = payment_data['payment_amount']
                
                if currency == 'VND':
                    amount_vnd = payment_amount
                    amount_usd = payment_amount / exchange_rate if exchange_rate > 0 else 0
                else:  # USD
                    amount_usd = payment_amount
                    amount_vnd = payment_amount * exchange_rate
                
                payment_record = {
                    'payment_id': payment_data['payment_id'],
                    'invoice_id': payment_data['invoice_id'],
                    'payment_date': payment_data['payment_date'],
                    'payment_amount': payment_amount,
                    'currency': currency,
                    'payment_method': payment_data.get('payment_method', 'bank_transfer'),
                    'payment_reference': payment_data.get('payment_reference', ''),
                    'exchange_rate': exchange_rate,
                    'amount_vnd': amount_vnd,
                    'amount_usd': amount_usd,
                    'notes': payment_data.get('notes', ''),
                    'created_by': payment_data.get('created_by', ''),
                    'created_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO invoice_payments (
                        payment_id, invoice_id, payment_date, payment_amount, currency,
                        payment_method, payment_reference, exchange_rate, amount_vnd, amount_usd,
                        notes, created_by, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(payment_record.values()))
                
                # 인보이스 결제 상태 업데이트
                self._update_invoice_payment_status(payment_data['invoice_id'])
                
                conn.commit()
                logger.info(f"결제 내역 추가 완료: {payment_data['payment_id']}")
                return True
                
        except Exception as e:
            logger.error(f"결제 내역 추가 실패: {str(e)}")
            return False

    def _update_invoice_payment_status(self, invoice_id):
        """인보이스 결제 상태 업데이트 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 총 결제 금액과 인보이스 금액 비교
                cursor.execute('''
                    SELECT 
                        i.total_amount,
                        COALESCE(SUM(p.payment_amount), 0) as paid_amount
                    FROM invoices i
                    LEFT JOIN invoice_payments p ON i.invoice_id = p.invoice_id
                    WHERE i.invoice_id = ?
                    GROUP BY i.invoice_id, i.total_amount
                ''', (invoice_id,))
                
                result = cursor.fetchone()
                if result:
                    total_amount, paid_amount = result
                    
                    if paid_amount >= total_amount:
                        payment_status = 'paid'
                    elif paid_amount > 0:
                        payment_status = 'partially_paid'
                    else:
                        payment_status = 'pending'
                    
                    cursor.execute('''
                        UPDATE invoices 
                        SET payment_status = ?, updated_date = ?
                        WHERE invoice_id = ?
                    ''', (payment_status, datetime.now().isoformat(), invoice_id))
                    
                    conn.commit()
                
        except Exception as e:
            logger.error(f"인보이스 결제 상태 업데이트 실패: {str(e)}")

    def get_invoice_payments(self, invoice_id):
        """인보이스 결제 내역 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM invoice_payments 
                    WHERE invoice_id = ? 
                    ORDER BY payment_date DESC
                '''
                df = pd.read_sql_query(query, conn, params=[invoice_id])
                return df
                
        except Exception as e:
            logger.error(f"인보이스 결제 내역 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_invoice_statistics(self, date_from=None, date_to=None):
        """인보이스 통계"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT 
                        status,
                        payment_status,
                        COUNT(*) as count,
                        SUM(total_amount) as total_amount,
                        SUM(amount_vnd) as total_vnd,
                        SUM(amount_usd) as total_usd,
                        AVG(total_amount) as avg_amount
                    FROM invoices
                    WHERE 1=1
                '''
                params = []
                
                if date_from:
                    query += " AND issue_date >= ?"
                    params.append(date_from)
                if date_to:
                    query += " AND issue_date <= ?"
                    params.append(date_to)
                
                query += " GROUP BY status, payment_status ORDER BY status, payment_status"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"인보이스 통계 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, invoices_csv_path=None, items_csv_path=None, payments_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 인보이스 데이터 마이그레이션
            if invoices_csv_path is None:
                invoices_csv_path = os.path.join("data", "invoices.csv")
            
            if os.path.exists(invoices_csv_path):
                df = pd.read_csv(invoices_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        invoice_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in invoice_data.items():
                            if pd.isna(value):
                                if key in ['subtotal', 'tax_rate', 'tax_amount', 'discount_rate', 'discount_amount', 'total_amount', 'amount_vnd', 'amount_usd', 'exchange_rate']:
                                    invoice_data[key] = 0
                                else:
                                    invoice_data[key] = ''
                        
                        self.add_invoice(invoice_data)
                    
                    logger.info(f"인보이스 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 인보이스 항목 마이그레이션은 복잡하므로 별도 처리
            # 결제 내역도 마찬가지
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False