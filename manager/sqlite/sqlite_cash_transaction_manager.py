"""
SQLite 현금 거래 관리자 - 현금 거래 기록, 추적 관리
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

class SQLiteCashTransactionManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현금 거래 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cash_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        transaction_date TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        category TEXT,
                        subcategory TEXT,
                        description TEXT,
                        amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        amount_vnd REAL DEFAULT 0,
                        amount_usd REAL DEFAULT 0,
                        exchange_rate REAL DEFAULT 1,
                        payment_method TEXT DEFAULT 'cash',
                        account_id TEXT,
                        account_name TEXT,
                        counterparty_id TEXT,
                        counterparty_name TEXT,
                        reference_id TEXT,
                        reference_type TEXT,
                        receipt_number TEXT,
                        invoice_number TEXT,
                        tax_rate REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        status TEXT DEFAULT 'completed',
                        created_by TEXT,
                        approved_by TEXT,
                        approval_date TEXT,
                        notes TEXT,
                        attachments TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 현금 계정 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cash_accounts (
                        account_id TEXT PRIMARY KEY,
                        account_name TEXT NOT NULL,
                        account_type TEXT DEFAULT 'cash',
                        currency TEXT DEFAULT 'VND',
                        current_balance REAL DEFAULT 0,
                        opening_balance REAL DEFAULT 0,
                        bank_name TEXT,
                        account_number TEXT,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 거래 카테고리 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_categories (
                        category_id TEXT PRIMARY KEY,
                        category_name TEXT NOT NULL,
                        parent_category TEXT,
                        category_type TEXT DEFAULT 'both',
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("현금 거래 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_cash_transactions(self, start_date=None, end_date=None, transaction_type=None, category=None, account_id=None):
        """현금 거래 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM cash_transactions WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND transaction_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND transaction_date <= ?"
                    params.append(end_date)
                if transaction_type:
                    query += " AND transaction_type = ?"
                    params.append(transaction_type)
                if category:
                    query += " AND category = ?"
                    params.append(category)
                if account_id:
                    query += " AND account_id = ?"
                    params.append(account_id)
                
                query += " ORDER BY transaction_date DESC, created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"현금 거래 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_cash_transaction(self, transaction_data):
        """현금 거래 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['transaction_id', 'transaction_date', 'transaction_type', 'amount']
                for field in required_fields:
                    if field not in transaction_data or transaction_data[field] is None:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                # 환율 적용하여 VND/USD 계산
                amount = transaction_data['amount']
                currency = transaction_data.get('currency', 'VND')
                exchange_rate = transaction_data.get('exchange_rate', 1)
                
                if currency == 'VND':
                    amount_vnd = amount
                    amount_usd = amount / exchange_rate if exchange_rate > 0 else 0
                else:  # USD
                    amount_usd = amount
                    amount_vnd = amount * exchange_rate
                
                transaction_record = {
                    'transaction_id': transaction_data['transaction_id'],
                    'transaction_date': transaction_data['transaction_date'],
                    'transaction_type': transaction_data['transaction_type'],
                    'category': transaction_data.get('category', ''),
                    'subcategory': transaction_data.get('subcategory', ''),
                    'description': transaction_data.get('description', ''),
                    'amount': amount,
                    'currency': currency,
                    'amount_vnd': amount_vnd,
                    'amount_usd': amount_usd,
                    'exchange_rate': exchange_rate,
                    'payment_method': transaction_data.get('payment_method', 'cash'),
                    'account_id': transaction_data.get('account_id', ''),
                    'account_name': transaction_data.get('account_name', ''),
                    'counterparty_id': transaction_data.get('counterparty_id', ''),
                    'counterparty_name': transaction_data.get('counterparty_name', ''),
                    'reference_id': transaction_data.get('reference_id', ''),
                    'reference_type': transaction_data.get('reference_type', ''),
                    'receipt_number': transaction_data.get('receipt_number', ''),
                    'invoice_number': transaction_data.get('invoice_number', ''),
                    'tax_rate': transaction_data.get('tax_rate', 0),
                    'tax_amount': transaction_data.get('tax_amount', 0),
                    'status': transaction_data.get('status', 'completed'),
                    'created_by': transaction_data.get('created_by', ''),
                    'approved_by': transaction_data.get('approved_by', ''),
                    'approval_date': transaction_data.get('approval_date', ''),
                    'notes': transaction_data.get('notes', ''),
                    'attachments': json.dumps(transaction_data.get('attachments', [])),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO cash_transactions (
                        transaction_id, transaction_date, transaction_type, category, subcategory,
                        description, amount, currency, amount_vnd, amount_usd,
                        exchange_rate, payment_method, account_id, account_name, counterparty_id,
                        counterparty_name, reference_id, reference_type, receipt_number, invoice_number,
                        tax_rate, tax_amount, status, created_by, approved_by,
                        approval_date, notes, attachments, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(transaction_record.values()))
                
                # 계정 잔액 업데이트
                if transaction_data.get('account_id'):
                    self._update_account_balance(transaction_data['account_id'], transaction_data['transaction_type'], amount_vnd)
                
                conn.commit()
                logger.info(f"현금 거래 추가 완료: {transaction_data['transaction_id']}")
                return True
                
        except Exception as e:
            logger.error(f"현금 거래 추가 실패: {str(e)}")
            return False

    def update_cash_transaction(self, transaction_id, updates):
        """현금 거래 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [transaction_id]
                
                cursor.execute(f'''
                    UPDATE cash_transactions 
                    SET {set_clause}
                    WHERE transaction_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"현금 거래 수정 완료: {transaction_id}")
                    return True
                else:
                    logger.warning(f"수정할 거래 없음: {transaction_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"현금 거래 수정 실패: {str(e)}")
            return False

    def delete_cash_transaction(self, transaction_id):
        """현금 거래 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 거래 정보 조회 (잔액 복원용)
                cursor.execute("SELECT account_id, transaction_type, amount_vnd FROM cash_transactions WHERE transaction_id = ?", (transaction_id,))
                result = cursor.fetchone()
                
                if result:
                    account_id, transaction_type, amount_vnd = result
                    
                    # 거래 삭제
                    cursor.execute("DELETE FROM cash_transactions WHERE transaction_id = ?", (transaction_id,))
                    
                    # 계정 잔액 복원
                    if account_id:
                        # 반대 타입으로 잔액 복원
                        reverse_type = 'expense' if transaction_type == 'income' else 'income'
                        self._update_account_balance(account_id, reverse_type, amount_vnd)
                    
                    conn.commit()
                    logger.info(f"현금 거래 삭제 완료: {transaction_id}")
                    return True
                else:
                    logger.warning(f"삭제할 거래 없음: {transaction_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"현금 거래 삭제 실패: {str(e)}")
            return False

    def get_cash_accounts(self, is_active=True):
        """현금 계정 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM cash_accounts"
                params = []
                
                if is_active is not None:
                    query += " WHERE is_active = ?"
                    params.append(1 if is_active else 0)
                
                query += " ORDER BY account_name"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"현금 계정 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_cash_account(self, account_data):
        """현금 계정 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                if 'account_id' not in account_data or not account_data['account_id']:
                    raise ValueError("계정 ID는 필수입니다")
                if 'account_name' not in account_data or not account_data['account_name']:
                    raise ValueError("계정 이름은 필수입니다")
                
                current_time = datetime.now().isoformat()
                
                account_record = {
                    'account_id': account_data['account_id'],
                    'account_name': account_data['account_name'],
                    'account_type': account_data.get('account_type', 'cash'),
                    'currency': account_data.get('currency', 'VND'),
                    'current_balance': account_data.get('current_balance', 0),
                    'opening_balance': account_data.get('opening_balance', 0),
                    'bank_name': account_data.get('bank_name', ''),
                    'account_number': account_data.get('account_number', ''),
                    'description': account_data.get('description', ''),
                    'is_active': account_data.get('is_active', 1),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO cash_accounts (
                        account_id, account_name, account_type, currency, current_balance,
                        opening_balance, bank_name, account_number, description,
                        is_active, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(account_record.values()))
                
                conn.commit()
                logger.info(f"현금 계정 추가 완료: {account_data['account_id']}")
                return True
                
        except Exception as e:
            logger.error(f"현금 계정 추가 실패: {str(e)}")
            return False

    def _update_account_balance(self, account_id, transaction_type, amount_vnd):
        """계정 잔액 업데이트 (내부 함수)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 현재 잔액 조회
                cursor.execute("SELECT current_balance FROM cash_accounts WHERE account_id = ?", (account_id,))
                result = cursor.fetchone()
                
                if result:
                    current_balance = result[0] or 0
                    
                    # 수입이면 잔액 증가, 지출이면 잔액 감소
                    if transaction_type == 'income':
                        new_balance = current_balance + amount_vnd
                    else:  # expense
                        new_balance = current_balance - amount_vnd
                    
                    # 잔액 업데이트
                    cursor.execute('''
                        UPDATE cash_accounts 
                        SET current_balance = ?, updated_date = ?
                        WHERE account_id = ?
                    ''', (new_balance, datetime.now().isoformat(), account_id))
                    
                    conn.commit()
                
        except Exception as e:
            logger.error(f"계정 잔액 업데이트 실패: {str(e)}")

    def get_transaction_summary(self, start_date=None, end_date=None, group_by='category'):
        """거래 요약 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if group_by == 'category':
                    query = '''
                        SELECT 
                            category,
                            transaction_type,
                            COUNT(*) as transaction_count,
                            SUM(amount_vnd) as total_vnd,
                            SUM(amount_usd) as total_usd,
                            AVG(amount_vnd) as avg_vnd
                        FROM cash_transactions
                        WHERE 1=1
                    '''
                elif group_by == 'date':
                    query = '''
                        SELECT 
                            DATE(transaction_date) as transaction_date,
                            transaction_type,
                            COUNT(*) as transaction_count,
                            SUM(amount_vnd) as total_vnd,
                            SUM(amount_usd) as total_usd
                        FROM cash_transactions
                        WHERE 1=1
                    '''
                else:  # monthly
                    query = '''
                        SELECT 
                            strftime('%Y-%m', transaction_date) as month,
                            transaction_type,
                            COUNT(*) as transaction_count,
                            SUM(amount_vnd) as total_vnd,
                            SUM(amount_usd) as total_usd
                        FROM cash_transactions
                        WHERE 1=1
                    '''
                
                params = []
                if start_date:
                    query += " AND transaction_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND transaction_date <= ?"
                    params.append(end_date)
                
                if group_by == 'category':
                    query += " GROUP BY category, transaction_type ORDER BY category, transaction_type"
                elif group_by == 'date':
                    query += " GROUP BY DATE(transaction_date), transaction_type ORDER BY transaction_date DESC"
                else:
                    query += " GROUP BY strftime('%Y-%m', transaction_date), transaction_type ORDER BY month DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"거래 요약 조회 실패: {str(e)}")
            return pd.DataFrame()

    def migrate_from_csv(self, transactions_csv_path=None, accounts_csv_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            # 현금 거래 데이터 마이그레이션
            if transactions_csv_path is None:
                transactions_csv_path = os.path.join("data", "cash_transactions.csv")
            
            if os.path.exists(transactions_csv_path):
                df = pd.read_csv(transactions_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        transaction_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in transaction_data.items():
                            if pd.isna(value):
                                if key in ['amount', 'amount_vnd', 'amount_usd', 'exchange_rate', 'tax_rate', 'tax_amount']:
                                    transaction_data[key] = 0
                                else:
                                    transaction_data[key] = ''
                        
                        self.add_cash_transaction(transaction_data)
                    
                    logger.info(f"현금 거래 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            # 현금 계정 데이터 마이그레이션
            if accounts_csv_path is None:
                accounts_csv_path = os.path.join("data", "cash_accounts.csv")
            
            if os.path.exists(accounts_csv_path):
                df = pd.read_csv(accounts_csv_path, encoding='utf-8-sig')
                
                if not df.empty:
                    for _, row in df.iterrows():
                        account_data = row.to_dict()
                        # NaN 값 처리
                        for key, value in account_data.items():
                            if pd.isna(value):
                                if key in ['current_balance', 'opening_balance', 'is_active']:
                                    account_data[key] = 0 if key != 'is_active' else 1
                                else:
                                    account_data[key] = ''
                        
                        self.add_cash_account(account_data)
                    
                    logger.info(f"현금 계정 CSV 데이터 마이그레이션 완료: {len(df)}건")
            
            return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False