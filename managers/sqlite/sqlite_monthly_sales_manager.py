"""
SQLite 월별 매출 관리자 - 월별 매출 분석, 트렌드, 목표 관리
CSV 기반에서 SQLite 기반으로 전환
"""

import sqlite3
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from utils.currency_helper import CurrencyHelper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteMonthlySalesManager:
    def __init__(self, db_path="erp_system.db"):
        self.db_path = db_path
        self.currency_helper = CurrencyHelper()
        self._init_tables()
        
    def _init_tables(self):
        """SQLite 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 월별 매출 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monthly_sales (
                        sales_id TEXT PRIMARY KEY,
                        year_month TEXT NOT NULL,
                        customer_id TEXT,
                        customer_name TEXT,
                        product_code TEXT,
                        product_name TEXT,
                        category TEXT,
                        quantity INTEGER DEFAULT 0,
                        unit_price REAL DEFAULT 0,
                        total_amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        amount_vnd REAL DEFAULT 0,
                        amount_usd REAL DEFAULT 0,
                        sales_date TEXT,
                        quotation_id TEXT,
                        order_id TEXT,
                        payment_status TEXT DEFAULT 'pending',
                        sales_rep TEXT,
                        profit_margin REAL DEFAULT 0,
                        cost_amount REAL DEFAULT 0,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 매출 목표 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sales_targets (
                        target_id TEXT PRIMARY KEY,
                        year_month TEXT NOT NULL,
                        target_type TEXT DEFAULT 'revenue',
                        target_category TEXT,
                        target_amount_vnd REAL DEFAULT 0,
                        target_amount_usd REAL DEFAULT 0,
                        currency TEXT DEFAULT 'VND',
                        target_quantity INTEGER DEFAULT 0,
                        responsible_person TEXT,
                        description TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("월별 매출 관련 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"테이블 초기화 실패: {str(e)}")
            raise

    def get_monthly_sales(self, year=None, month=None):
        """월별 매출 데이터 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM monthly_sales"
                params = []
                
                if year and month:
                    query += " WHERE year_month = ?"
                    params.append(f"{year}-{month:02d}")
                elif year:
                    query += " WHERE year_month LIKE ?"
                    params.append(f"{year}-%")
                
                query += " ORDER BY sales_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"월별 매출 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_monthly_sales(self, sales_data):
        """월별 매출 데이터 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['sales_id', 'year_month']
                for field in required_fields:
                    if field not in sales_data or not sales_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                # 현재 시간
                current_time = datetime.now().isoformat()
                
                # 기본값 설정
                sales_record = {
                    'sales_id': sales_data['sales_id'],
                    'year_month': sales_data['year_month'],
                    'customer_id': sales_data.get('customer_id', ''),
                    'customer_name': sales_data.get('customer_name', ''),
                    'product_code': sales_data.get('product_code', ''),
                    'product_name': sales_data.get('product_name', ''),
                    'category': sales_data.get('category', ''),
                    'quantity': sales_data.get('quantity', 0),
                    'unit_price': sales_data.get('unit_price', 0),
                    'total_amount': sales_data.get('total_amount', 0),
                    'currency': sales_data.get('currency', 'VND'),
                    'amount_vnd': sales_data.get('amount_vnd', 0),
                    'amount_usd': sales_data.get('amount_usd', 0),
                    'sales_date': sales_data.get('sales_date', current_time),
                    'quotation_id': sales_data.get('quotation_id', ''),
                    'order_id': sales_data.get('order_id', ''),
                    'payment_status': sales_data.get('payment_status', 'pending'),
                    'sales_rep': sales_data.get('sales_rep', ''),
                    'profit_margin': sales_data.get('profit_margin', 0),
                    'cost_amount': sales_data.get('cost_amount', 0),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO monthly_sales (
                        sales_id, year_month, customer_id, customer_name, product_code,
                        product_name, category, quantity, unit_price, total_amount,
                        currency, amount_vnd, amount_usd, sales_date, quotation_id,
                        order_id, payment_status, sales_rep, profit_margin, cost_amount,
                        created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(sales_record.values()))
                
                conn.commit()
                logger.info(f"월별 매출 추가 완료: {sales_data['sales_id']}")
                return True
                
        except Exception as e:
            logger.error(f"월별 매출 추가 실패: {str(e)}")
            return False

    def update_monthly_sales(self, sales_id, updates):
        """월별 매출 데이터 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 업데이트할 필드들 준비
                updates['updated_date'] = datetime.now().isoformat()
                
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [sales_id]
                
                cursor.execute(f'''
                    UPDATE monthly_sales 
                    SET {set_clause}
                    WHERE sales_id = ?
                ''', values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"월별 매출 수정 완료: {sales_id}")
                    return True
                else:
                    logger.warning(f"수정할 매출 데이터 없음: {sales_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"월별 매출 수정 실패: {str(e)}")
            return False

    def delete_monthly_sales(self, sales_id):
        """월별 매출 데이터 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM monthly_sales WHERE sales_id = ?", (sales_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"월별 매출 삭제 완료: {sales_id}")
                    return True
                else:
                    logger.warning(f"삭제할 매출 데이터 없음: {sales_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"월별 매출 삭제 실패: {str(e)}")
            return False

    def get_sales_targets(self, year=None, month=None):
        """매출 목표 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM sales_targets"
                params = []
                
                if year and month:
                    query += " WHERE year_month = ?"
                    params.append(f"{year}-{month:02d}")
                elif year:
                    query += " WHERE year_month LIKE ?"
                    params.append(f"{year}-%")
                
                query += " ORDER BY year_month DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"매출 목표 조회 실패: {str(e)}")
            return pd.DataFrame()

    def add_sales_target(self, target_data):
        """매출 목표 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 필수 필드 확인
                required_fields = ['target_id', 'year_month']
                for field in required_fields:
                    if field not in target_data or not target_data[field]:
                        raise ValueError(f"필수 필드 누락: {field}")
                
                current_time = datetime.now().isoformat()
                
                target_record = {
                    'target_id': target_data['target_id'],
                    'year_month': target_data['year_month'],
                    'target_type': target_data.get('target_type', 'revenue'),
                    'target_category': target_data.get('target_category', ''),
                    'target_amount_vnd': target_data.get('target_amount_vnd', 0),
                    'target_amount_usd': target_data.get('target_amount_usd', 0),
                    'currency': target_data.get('currency', 'VND'),
                    'target_quantity': target_data.get('target_quantity', 0),
                    'responsible_person': target_data.get('responsible_person', ''),
                    'description': target_data.get('description', ''),
                    'created_date': current_time,
                    'updated_date': current_time
                }
                
                cursor.execute('''
                    INSERT INTO sales_targets (
                        target_id, year_month, target_type, target_category,
                        target_amount_vnd, target_amount_usd, currency, target_quantity,
                        responsible_person, description, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(target_record.values()))
                
                conn.commit()
                logger.info(f"매출 목표 추가 완료: {target_data['target_id']}")
                return True
                
        except Exception as e:
            logger.error(f"매출 목표 추가 실패: {str(e)}")
            return False

    def get_sales_summary(self, year, month=None):
        """매출 요약 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if month:
                    query = """
                        SELECT 
                            COUNT(*) as total_sales,
                            SUM(total_amount) as total_revenue,
                            SUM(amount_vnd) as total_vnd,
                            SUM(amount_usd) as total_usd,
                            AVG(profit_margin) as avg_profit_margin,
                            category,
                            COUNT(*) as category_count
                        FROM monthly_sales 
                        WHERE year_month = ?
                        GROUP BY category
                    """
                    params = [f"{year}-{month:02d}"]
                else:
                    query = """
                        SELECT 
                            COUNT(*) as total_sales,
                            SUM(total_amount) as total_revenue,
                            SUM(amount_vnd) as total_vnd,
                            SUM(amount_usd) as total_usd,
                            AVG(profit_margin) as avg_profit_margin,
                            year_month,
                            COUNT(*) as monthly_count
                        FROM monthly_sales 
                        WHERE year_month LIKE ?
                        GROUP BY year_month
                        ORDER BY year_month
                    """
                    params = [f"{year}-%"]
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"매출 요약 조회 실패: {str(e)}")
            return pd.DataFrame()

    def sync_with_real_data(self):
        """실제 ERP 데이터(견적서, 주문, 현금흐름)와 동기화"""
        try:
            # 주문 데이터에서 매출 데이터 생성
            with sqlite3.connect(self.db_path) as conn:
                # 완료된 주문들을 매출 데이터로 변환
                query = """
                    SELECT DISTINCT
                        o.order_id,
                        strftime('%Y-%m', o.order_date) as year_month,
                        o.customer_id,
                        c.company_name as customer_name,
                        oi.product_code,
                        oi.product_name,
                        p.category,
                        oi.quantity,
                        oi.unit_price,
                        oi.total_price as total_amount,
                        o.currency,
                        CASE WHEN o.currency = 'VND' THEN oi.total_price ELSE 0 END as amount_vnd,
                        CASE WHEN o.currency = 'USD' THEN oi.total_price ELSE 0 END as amount_usd,
                        o.order_date as sales_date,
                        o.quotation_id,
                        o.order_id,
                        o.status as payment_status,
                        o.created_by as sales_rep,
                        0 as profit_margin,
                        0 as cost_amount
                    FROM orders o
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    LEFT JOIN customers c ON o.customer_id = c.customer_id
                    LEFT JOIN products p ON oi.product_code = p.product_code
                    WHERE o.status IN ('완료', 'completed', 'paid')
                        AND oi.product_code IS NOT NULL
                """
                
                orders_df = pd.read_sql_query(query, conn)
                
                if not orders_df.empty:
                    # 기존 매출 데이터와 중복 제거
                    for _, row in orders_df.iterrows():
                        sales_id = f"SALES_{row['order_id']}_{row['product_code']}"
                        
                        # 이미 존재하는지 확인
                        existing_query = "SELECT COUNT(*) FROM monthly_sales WHERE sales_id = ?"
                        cursor = conn.cursor()
                        cursor.execute(existing_query, (sales_id,))
                        
                        if cursor.fetchone()[0] == 0:  # 존재하지 않으면 추가
                            sales_data = {
                                'sales_id': sales_id,
                                'year_month': row['year_month'],
                                'customer_id': row['customer_id'],
                                'customer_name': row['customer_name'],
                                'product_code': row['product_code'],
                                'product_name': row['product_name'],
                                'category': row['category'],
                                'quantity': row['quantity'],
                                'unit_price': row['unit_price'],
                                'total_amount': row['total_amount'],
                                'currency': row['currency'],
                                'amount_vnd': row['amount_vnd'],
                                'amount_usd': row['amount_usd'],
                                'sales_date': row['sales_date'],
                                'quotation_id': row['quotation_id'],
                                'order_id': row['order_id'],
                                'payment_status': 'completed',
                                'sales_rep': row['sales_rep'],
                                'profit_margin': 0,
                                'cost_amount': 0
                            }
                            self.add_monthly_sales(sales_data)
                
                logger.info("실제 데이터와 동기화 완료")
                return True
                
        except Exception as e:
            logger.error(f"실제 데이터 동기화 실패: {str(e)}")
            return False

    def migrate_from_csv(self, csv_file_path=None):
        """기존 CSV 데이터를 SQLite로 마이그레이션"""
        try:
            if csv_file_path is None:
                csv_file_path = os.path.join("data", "monthly_sales.csv")
            
            if os.path.exists(csv_file_path):
                df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
                
                if not df.empty:
                    # 각 행을 SQLite에 삽입
                    for _, row in df.iterrows():
                        sales_data = row.to_dict()
                        # NaN 값을 적절한 기본값으로 변경
                        for key, value in sales_data.items():
                            if pd.isna(value):
                                if key in ['quantity', 'unit_price', 'total_amount', 'amount_vnd', 'amount_usd', 'profit_margin', 'cost_amount']:
                                    sales_data[key] = 0
                                else:
                                    sales_data[key] = ''
                        
                        self.add_monthly_sales(sales_data)
                    
                    logger.info(f"CSV 데이터 마이그레이션 완료: {len(df)}건")
                    return True
                else:
                    logger.info("CSV 파일이 비어있음")
                    return True
            else:
                logger.info("CSV 파일이 존재하지 않음")
                return True
                
        except Exception as e:
            logger.error(f"CSV 마이그레이션 실패: {str(e)}")
            return False
    def get_monthly_sales_summary(self, year_month=None):
        """월별 매출 요약 정보를 가져옵니다."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        year_month,
                        COUNT(*) as total_transactions,
                        SUM(amount_vnd) as total_vnd,
                        SUM(amount_usd) as total_usd,
                        AVG(amount_vnd) as avg_vnd,
                        AVG(amount_usd) as avg_usd
                    FROM monthly_sales
                """
                params = []
                if year_month:
                    query += " WHERE year_month = ?"
                    params.append(year_month)
                
                query += " GROUP BY year_month ORDER BY year_month DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"월별 매출 요약 조회 오류: {e}")
            return pd.DataFrame()

    def get_target_vs_actual(self, year_month=None):
        """목표 대비 실적 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        t.year_month,
                        t.target_amount_vnd,
                        t.target_amount_usd,
                        COALESCE(s.actual_vnd, 0) as actual_vnd,
                        COALESCE(s.actual_usd, 0) as actual_usd
                    FROM sales_targets t
                    LEFT JOIN (
                        SELECT 
                            year_month,
                            SUM(amount_vnd) as actual_vnd,
                            SUM(amount_usd) as actual_usd
                        FROM monthly_sales
                        GROUP BY year_month
                    ) s ON t.year_month = s.year_month
                """
                params = []
                if year_month:
                    query += " WHERE t.year_month = ?"
                    params.append(year_month)
                
                query += " ORDER BY t.year_month DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"목표 대비 실적 분석 오류: {e}")
            return pd.DataFrame()

    def get_customer_sales_analysis(self, year_month=None):
        """고객별 매출 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        customer_name,
                        COUNT(*) as transaction_count,
                        SUM(amount_vnd) as total_vnd,
                        SUM(amount_usd) as total_usd,
                        AVG(amount_vnd) as avg_vnd
                    FROM monthly_sales
                """
                params = []
                if year_month:
                    query += " WHERE year_month = ?"
                    params.append(year_month)
                
                query += " GROUP BY customer_name ORDER BY total_vnd DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"고객별 매출 분석 오류: {e}")
            return pd.DataFrame()

    def get_product_sales_analysis(self, year_month=None):
        """제품별 매출 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        product_name,
                        category,
                        SUM(quantity) as total_quantity,
                        SUM(amount_vnd) as total_vnd,
                        SUM(amount_usd) as total_usd,
                        AVG(unit_price) as avg_price
                    FROM monthly_sales
                """
                params = []
                if year_month:
                    query += " WHERE year_month = ?"
                    params.append(year_month)
                
                query += " GROUP BY product_name, category ORDER BY total_vnd DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"제품별 매출 분석 오류: {e}")
            return pd.DataFrame()

    def get_sales_trend(self, months=12):
        """매출 트렌드 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        year_month,
                        SUM(amount_vnd) as total_vnd,
                        SUM(amount_usd) as total_usd,
                        COUNT(*) as transaction_count
                    FROM monthly_sales
                    WHERE year_month >= datetime("now", "-{} months")
                    GROUP BY year_month
                    ORDER BY year_month
                """.format(months)
                
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            logger.error(f"매출 트렌드 분석 오류: {e}")
            return pd.DataFrame()

