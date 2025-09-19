import pandas as pd
import psycopg2
from datetime import datetime
import json
import streamlit as st
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class PurchaseOrderManager:
    def __init__(self):
        self.create_tables()
    
    @contextmanager
    def get_db_connection(self):
        """안전한 데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                port=st.secrets["postgres"]["port"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"],
                connect_timeout=10,
                application_name="YMV_ERP_PurchaseOrder"
            )
            conn.autocommit = False
            yield conn
        except Exception as e:
            logger.error(f"데이터베이스 연결 오류: {e}")
            yield None
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def create_tables(self):
        """발주서 관련 테이블 생성"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 발주서 메인 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_orders (
                        po_id VARCHAR(50) PRIMARY KEY,
                        po_number VARCHAR(50) UNIQUE NOT NULL,
                        quotation_id VARCHAR(50),
                        supplier_id VARCHAR(50),
                        supplier_name VARCHAR(200),
                        po_date DATE,
                        delivery_date DATE,
                        total_amount DECIMAL(15,2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'VND',
                        terms_conditions TEXT,
                        status VARCHAR(20) DEFAULT '대기',
                        created_by VARCHAR(100),
                        approved_by VARCHAR(100),
                        approved_date TIMESTAMP,
                        input_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 발주서 제품 상세 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_order_items (
                        item_id SERIAL PRIMARY KEY,
                        po_id VARCHAR(50) REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
                        product_code VARCHAR(100),
                        product_name VARCHAR(300),
                        specification TEXT,
                        unit VARCHAR(50),
                        quantity DECIMAL(10,2),
                        unit_price DECIMAL(10,2),
                        total_price DECIMAL(15,2),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_date ON purchase_orders(po_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_poi_po_id ON purchase_order_items(po_id)")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"테이블 생성 오류: {e}")
            return False
    
    def generate_po_number(self):
        """발주서 번호를 생성합니다."""
        try:
            today = datetime.now()
            prefix = f"PO{today.strftime('%Y%m')}"
            
            with self.get_db_connection() as conn:
                if conn is None:
                    return f"PO{today.strftime('%Y%m')}001"
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT po_number FROM purchase_orders 
                    WHERE po_number LIKE %s 
                    ORDER BY po_number DESC LIMIT 1
                """, (f"{prefix}%",))
                
                result = cursor.fetchone()
                
                if result:
                    last_number = result[0]
                    try:
                        suffix = int(last_number.replace(prefix, ''))
                        next_num = suffix + 1
                    except:
                        next_num = 1
                else:
                    next_num = 1
                
                return f"{prefix}{next_num:03d}"
                
        except Exception as e:
            logger.error(f"발주서 번호 생성 중 오류: {e}")
            return f"PO{datetime.now().strftime('%Y%m')}001"
    
    def create_purchase_order(self, po_data):
        """새 발주서를 생성합니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 발주서 번호가 없으면 생성
                if 'po_number' not in po_data or not po_data['po_number']:
                    po_data['po_number'] = self.generate_po_number()
                
                # 발주서 ID 생성
                if 'po_id' not in po_data or not po_data['po_id']:
                    po_data['po_id'] = f"POID{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # 제품 목록 분리
                products = po_data.pop('products', [])
                
                # 발주서 메인 정보 저장
                columns = [
                    'po_id', 'po_number', 'quotation_id', 'supplier_id', 'supplier_name',
                    'po_date', 'delivery_date', 'total_amount', 'currency',
                    'terms_conditions', 'status', 'created_by'
                ]
                
                values = [po_data.get(col) for col in columns]
                placeholders = ', '.join(['%s'] * len(columns))
                
                cursor.execute(f"""
                    INSERT INTO purchase_orders ({', '.join(columns)})
                    VALUES ({placeholders})
                """, values)
                
                # 제품 상세 정보 저장
                if products:
                    for product in products:
                        cursor.execute("""
                            INSERT INTO purchase_order_items 
                            (po_id, product_code, product_name, specification, unit, 
                             quantity, unit_price, total_price, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            po_data['po_id'],
                            product.get('product_code'),
                            product.get('product_name'),
                            product.get('specification'),
                            product.get('unit'),
                            product.get('quantity'),
                            product.get('unit_price'),
                            product.get('total_price'),
                            product.get('notes')
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"발주서 생성 중 오류: {e}")
            return False
    
    def get_all_purchase_orders(self):
        """모든 발주서 정보를 가져옵니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT po_id, po_number, quotation_id, supplier_id, supplier_name,
                           po_date, delivery_date, total_amount, currency, terms_conditions,
                           status, created_by, approved_by, approved_date, input_date, updated_date
                    FROM purchase_orders
                    ORDER BY input_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                df = pd.DataFrame(data, columns=columns)
                
                # 각 발주서의 제품 목록 추가
                if not df.empty:
                    for idx, row in df.iterrows():
                        products = self.get_purchase_order_items(row['po_id'])
                        df.at[idx, 'products'] = products
                
                return df
                
        except Exception as e:
            logger.error(f"발주서 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_order_by_id(self, po_id):
        """특정 발주서 정보를 가져옵니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return None
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM purchase_orders WHERE po_id = %s
                """, (po_id,))
                
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    po_data = dict(zip(columns, result))
                    
                    # 제품 목록 추가
                    po_data['products'] = self.get_purchase_order_items(po_id)
                    
                    return po_data
                
                return None
                
        except Exception as e:
            logger.error(f"발주서 조회 중 오류: {e}")
            return None
    
    def get_purchase_order_items(self, po_id):
        """발주서의 제품 목록을 가져옵니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT product_code, product_name, specification, unit,
                           quantity, unit_price, total_price, notes
                    FROM purchase_order_items
                    WHERE po_id = %s
                    ORDER BY item_id
                """, (po_id,))
                
                columns = [desc[0] for desc in cursor.description]
                items = cursor.fetchall()
                
                return [dict(zip(columns, item)) for item in items]
                
        except Exception as e:
            logger.error(f"발주서 제품 조회 중 오류: {e}")
            return []
    
    def update_purchase_order(self, po_id, po_data):
        """발주서 정보를 업데이트합니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 제품 목록 분리
                products = po_data.pop('products', None)
                
                # 발주서 메인 정보 업데이트
                if po_data:
                    set_clauses = []
                    values = []
                    
                    for key, value in po_data.items():
                        if key != 'po_id':
                            set_clauses.append(f"{key} = %s")
                            values.append(value)
                    
                    if set_clauses:
                        set_clauses.append("updated_date = CURRENT_TIMESTAMP")
                        values.append(po_id)
                        
                        cursor.execute(f"""
                            UPDATE purchase_orders 
                            SET {', '.join(set_clauses)}
                            WHERE po_id = %s
                        """, values)
                
                # 제품 목록 업데이트
                if products is not None:
                    # 기존 제품 목록 삭제
                    cursor.execute("DELETE FROM purchase_order_items WHERE po_id = %s", (po_id,))
                    
                    # 새 제품 목록 삽입
                    for product in products:
                        cursor.execute("""
                            INSERT INTO purchase_order_items 
                            (po_id, product_code, product_name, specification, unit, 
                             quantity, unit_price, total_price, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            po_id,
                            product.get('product_code'),
                            product.get('product_name'),
                            product.get('specification'),
                            product.get('unit'),
                            product.get('quantity'),
                            product.get('unit_price'),
                            product.get('total_price'),
                            product.get('notes')
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"발주서 업데이트 중 오류: {e}")
            return False
    
    def approve_purchase_order(self, po_id, approved_by):
        """발주서를 승인합니다."""
        try:
            return self.update_purchase_order(po_id, {
                'status': '승인됨',
                'approved_by': approved_by,
                'approved_date': datetime.now()
            })
        except Exception as e:
            logger.error(f"발주서 승인 중 오류: {e}")
            return False
    
    def get_purchase_orders_by_status(self, status):
        """상태별 발주서를 가져옵니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM purchase_orders 
                    WHERE status = %s
                    ORDER BY input_date DESC
                """, (status,))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"상태별 발주서 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_order_statistics(self):
        """발주서 통계를 가져옵니다."""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return {}
                
                cursor = conn.cursor()
                
                # 기본 통계
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_pos,
                        COUNT(CASE WHEN status = '대기' THEN 1 END) as pending_pos,
                        COUNT(CASE WHEN status = '승인됨' THEN 1 END) as approved_pos,
                        COUNT(CASE WHEN status = '완료' THEN 1 END) as completed_pos,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(AVG(total_amount), 0) as average_amount
                    FROM purchase_orders
                """)
                
                basic_stats = cursor.fetchone()
                
                # 상태별 분포
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM purchase_orders
                    GROUP BY status
                """)
                status_dist = dict(cursor.fetchall())
                
                # 공급업체별 분포
                cursor.execute("""
                    SELECT supplier_name, COUNT(*) as count
                    FROM purchase_orders
                    WHERE supplier_name IS NOT NULL
                    GROUP BY supplier_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                supplier_dist = dict(cursor.fetchall())
                
                return {
                    'total_pos': basic_stats[0],
                    'pending_pos': basic_stats[1],
                    'approved_pos': basic_stats[2],
                    'completed_pos': basic_stats[3],
                    'total_amount': float(basic_stats[4]),
                    'average_amount': float(basic_stats[5]),
                    'status_distribution': status_dist,
                    'supplier_distribution': supplier_dist
                }
                
        except Exception as e:
            logger.error(f"발주서 통계 조회 중 오류: {e}")
            return {}
