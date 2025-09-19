"""
PostgreSQL 기반 구매 발주서 관리자
프로젝트 표준에 맞춰 정상화된 버전
"""

import pandas as pd
import psycopg2
from datetime import datetime, date
import json
import streamlit as st
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Any

# 로깅 설정
logger = logging.getLogger(__name__)

class PurchaseOrderManager:
    """구매 발주서 관리 클래스 - PostgreSQL 기반"""
    
    def __init__(self):
        """클래스 초기화 및 테이블 생성"""
        self.table_created = self._create_tables()
        if not self.table_created:
            logger.warning("데이터베이스 테이블 생성에 실패했습니다.")
    
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
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            yield None
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def _create_tables(self) -> bool:
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
                        supplier_name VARCHAR(200) NOT NULL,
                        po_date DATE NOT NULL,
                        delivery_date DATE,
                        total_amount DECIMAL(15,2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'VND',
                        terms_conditions TEXT,
                        status VARCHAR(20) DEFAULT '대기' CHECK (status IN ('대기', '승인됨', '발주완료', '배송중', '완료', '취소')),
                        created_by VARCHAR(100),
                        approved_by VARCHAR(100),
                        approved_date TIMESTAMP,
                        input_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                """)
                
                # 발주서 제품 상세 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_order_items (
                        item_id SERIAL PRIMARY KEY,
                        po_id VARCHAR(50) NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
                        product_code VARCHAR(100),
                        product_name VARCHAR(300) NOT NULL,
                        specification TEXT,
                        unit VARCHAR(50) DEFAULT 'EA',
                        quantity DECIMAL(10,3) NOT NULL CHECK (quantity > 0),
                        unit_price DECIMAL(12,2) NOT NULL CHECK (unit_price >= 0),
                        total_price DECIMAL(15,2) NOT NULL CHECK (total_price >= 0),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 발주서 상태 변경 히스토리 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_order_history (
                        history_id SERIAL PRIMARY KEY,
                        po_id VARCHAR(50) NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
                        previous_status VARCHAR(20),
                        new_status VARCHAR(20) NOT NULL,
                        changed_by VARCHAR(100),
                        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                """)
                
                # 인덱스 생성
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number)",
                    "CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status)",
                    "CREATE INDEX IF NOT EXISTS idx_po_date ON purchase_orders(po_date)",
                    "CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id)",
                    "CREATE INDEX IF NOT EXISTS idx_po_supplier_name ON purchase_orders(supplier_name)",
                    "CREATE INDEX IF NOT EXISTS idx_poi_po_id ON purchase_order_items(po_id)",
                    "CREATE INDEX IF NOT EXISTS idx_poi_product ON purchase_order_items(product_code)",
                    "CREATE INDEX IF NOT EXISTS idx_poh_po_id ON purchase_order_history(po_id)",
                    "CREATE INDEX IF NOT EXISTS idx_poh_date ON purchase_order_history(changed_at)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                # 트리거 생성 (업데이트 시 updated_date 자동 갱신)
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_date_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_date = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql'
                """)
                
                cursor.execute("""
                    DROP TRIGGER IF EXISTS update_purchase_orders_updated_date ON purchase_orders;
                    CREATE TRIGGER update_purchase_orders_updated_date
                        BEFORE UPDATE ON purchase_orders
                        FOR EACH ROW EXECUTE FUNCTION update_updated_date_column()
                """)
                
                conn.commit()
                logger.info("발주서 테이블 생성/업데이트 완료")
                return True
                
        except Exception as e:
            logger.error(f"테이블 생성 오류: {e}")
            return False
    
    def generate_po_number(self) -> str:
        """발주서 번호 자동 생성"""
        try:
            today = datetime.now()
            prefix = f"PO{today.strftime('%Y%m')}"
            
            with self.get_db_connection() as conn:
                if conn is None:
                    return f"{prefix}001"
                
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
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                
                return f"{prefix}{next_num:03d}"
                
        except Exception as e:
            logger.error(f"발주서 번호 생성 중 오류: {e}")
            return f"PO{datetime.now().strftime('%Y%m')}001"
    
    def create_purchase_order(self, po_data: Dict[str, Any]) -> bool:
        """새 발주서 생성"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 필수 데이터 검증
                if not po_data.get('supplier_name'):
                    logger.error("공급업체명은 필수입니다.")
                    return False
                
                if not po_data.get('po_date'):
                    po_data['po_date'] = date.today()
                
                # ID 및 번호 생성
                if not po_data.get('po_number'):
                    po_data['po_number'] = self.generate_po_number()
                
                if not po_data.get('po_id'):
                    po_data['po_id'] = f"POID{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # 제품 목록 분리
                products = po_data.pop('products', [])
                
                # 총 금액 계산
                if products:
                    total_amount = sum(
                        float(item.get('total_price', 0)) for item in products
                    )
                    po_data['total_amount'] = total_amount
                
                # 발주서 메인 정보 저장
                main_columns = [
                    'po_id', 'po_number', 'quotation_id', 'supplier_id', 'supplier_name',
                    'po_date', 'delivery_date', 'total_amount', 'currency',
                    'terms_conditions', 'status', 'created_by', 'notes'
                ]
                
                values = [po_data.get(col) for col in main_columns]
                placeholders = ', '.join(['%s'] * len(main_columns))
                
                cursor.execute(f"""
                    INSERT INTO purchase_orders ({', '.join(main_columns)})
                    VALUES ({placeholders})
                """, values)
                
                # 제품 상세 정보 저장
                if products:
                    for product in products:
                        if not product.get('product_name'):
                            continue
                            
                        cursor.execute("""
                            INSERT INTO purchase_order_items 
                            (po_id, product_code, product_name, specification, unit, 
                             quantity, unit_price, total_price, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            po_data['po_id'],
                            product.get('product_code', ''),
                            product.get('product_name'),
                            product.get('specification', ''),
                            product.get('unit', 'EA'),
                            product.get('quantity', 0),
                            product.get('unit_price', 0),
                            product.get('total_price', 0),
                            product.get('notes', '')
                        ))
                
                # 히스토리 기록
                cursor.execute("""
                    INSERT INTO purchase_order_history 
                    (po_id, new_status, changed_by, notes)
                    VALUES (%s, %s, %s, %s)
                """, (
                    po_data['po_id'],
                    po_data.get('status', '대기'),
                    po_data.get('created_by', ''),
                    '발주서 생성'
                ))
                
                conn.commit()
                logger.info(f"발주서 생성 완료: {po_data['po_number']}")
                return True
                
        except Exception as e:
            logger.error(f"발주서 생성 중 오류: {e}")
            return False
    
    def get_all_purchase_orders(self) -> pd.DataFrame:
        """모든 발주서 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT po_id, po_number, quotation_id, supplier_id, supplier_name,
                           po_date, delivery_date, total_amount, currency, terms_conditions,
                           status, created_by, approved_by, approved_date, 
                           input_date, updated_date, notes
                    FROM purchase_orders
                    ORDER BY input_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                if not data:
                    return pd.DataFrame(columns=columns)
                
                df = pd.DataFrame(data, columns=columns)
                
                # 각 발주서의 제품 수량 추가
                df['item_count'] = df['po_id'].apply(
                    lambda po_id: self._get_item_count(po_id)
                )
                
                return df
                
        except Exception as e:
            logger.error(f"발주서 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def _get_item_count(self, po_id: str) -> int:
        """발주서의 제품 항목 수 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return 0
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM purchase_order_items WHERE po_id = %s
                """, (po_id,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"항목 수 조회 오류: {e}")
            return 0
    
    def get_purchase_order_by_id(self, po_id: str) -> Optional[Dict[str, Any]]:
        """특정 발주서 상세 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return None
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM purchase_orders WHERE po_id = %s
                """, (po_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                po_data = dict(zip(columns, result))
                
                # 제품 목록 추가
                po_data['products'] = self.get_purchase_order_items(po_id)
                
                # 상태 변경 히스토리 추가
                po_data['history'] = self._get_status_history(po_id)
                
                return po_data
                
        except Exception as e:
            logger.error(f"발주서 조회 중 오류: {e}")
            return None
    
    def get_purchase_order_items(self, po_id: str) -> List[Dict[str, Any]]:
        """발주서의 제품 목록 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT item_id, product_code, product_name, specification, unit,
                           quantity, unit_price, total_price, notes, created_at
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
    
    def _get_status_history(self, po_id: str) -> List[Dict[str, Any]]:
        """발주서 상태 변경 히스토리 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT previous_status, new_status, changed_by, changed_at, notes
                    FROM purchase_order_history
                    WHERE po_id = %s
                    ORDER BY changed_at
                """, (po_id,))
                
                columns = [desc[0] for desc in cursor.description]
                history = cursor.fetchall()
                
                return [dict(zip(columns, record)) for record in history]
                
        except Exception as e:
            logger.error(f"상태 히스토리 조회 오류: {e}")
            return []
    
    def update_purchase_order(self, po_id: str, po_data: Dict[str, Any]) -> bool:
        """발주서 정보 업데이트"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 기존 데이터 조회
                current_data = self.get_purchase_order_by_id(po_id)
                if not current_data:
                    logger.error(f"발주서를 찾을 수 없습니다: {po_id}")
                    return False
                
                # 제품 목록 분리
                products = po_data.pop('products', None)
                
                # 상태 변경 감지
                old_status = current_data.get('status')
                new_status = po_data.get('status')
                
                # 발주서 메인 정보 업데이트
                if po_data:
                    set_clauses = []
                    values = []
                    
                    for key, value in po_data.items():
                        if key not in ['po_id', 'input_date']:
                            set_clauses.append(f"{key} = %s")
                            values.append(value)
                    
                    if set_clauses:
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
                    
                    # 새 제품 목록 삽입 및 총액 계산
                    total_amount = 0
                    for product in products:
                        if not product.get('product_name'):
                            continue
                            
                        item_total = float(product.get('total_price', 0))
                        total_amount += item_total
                        
                        cursor.execute("""
                            INSERT INTO purchase_order_items 
                            (po_id, product_code, product_name, specification, unit, 
                             quantity, unit_price, total_price, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            po_id,
                            product.get('product_code', ''),
                            product.get('product_name'),
                            product.get('specification', ''),
                            product.get('unit', 'EA'),
                            product.get('quantity', 0),
                            product.get('unit_price', 0),
                            item_total,
                            product.get('notes', '')
                        ))
                    
                    # 총액 업데이트
                    cursor.execute("""
                        UPDATE purchase_orders SET total_amount = %s WHERE po_id = %s
                    """, (total_amount, po_id))
                
                # 상태 변경 히스토리 기록
                if new_status and old_status != new_status:
                    cursor.execute("""
                        INSERT INTO purchase_order_history 
                        (po_id, previous_status, new_status, changed_by, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        po_id,
                        old_status,
                        new_status,
                        po_data.get('updated_by', ''),
                        f"상태 변경: {old_status} → {new_status}"
                    ))
                
                conn.commit()
                logger.info(f"발주서 업데이트 완료: {po_id}")
                return True
                
        except Exception as e:
            logger.error(f"발주서 업데이트 중 오류: {e}")
            return False
    
    def approve_purchase_order(self, po_id: str, approved_by: str) -> bool:
        """발주서 승인"""
        try:
            return self.update_purchase_order(po_id, {
                'status': '승인됨',
                'approved_by': approved_by,
                'approved_date': datetime.now(),
                'updated_by': approved_by
            })
        except Exception as e:
            logger.error(f"발주서 승인 중 오류: {e}")
            return False
    
    def get_purchase_orders_by_status(self, status: str) -> pd.DataFrame:
        """상태별 발주서 조회"""
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
    
    def get_purchase_order_statistics(self) -> Dict[str, Any]:
        """발주서 통계 조회"""
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
                    ORDER BY count DESC
                """)
                status_dist = dict(cursor.fetchall())
                
                # 공급업체별 분포
                cursor.execute("""
                    SELECT supplier_name, COUNT(*) as count, SUM(total_amount) as total_amount
                    FROM purchase_orders
                    WHERE supplier_name IS NOT NULL
                    GROUP BY supplier_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                supplier_stats = cursor.fetchall()
                
                # 월별 발주 현황
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('month', po_date) as month,
                        COUNT(*) as count,
                        SUM(total_amount) as amount
                    FROM purchase_orders
                    WHERE po_date >= CURRENT_DATE - INTERVAL '12 months'
                    GROUP BY DATE_TRUNC('month', po_date)
                    ORDER BY month
                """)
                monthly_stats = cursor.fetchall()
                
                return {
                    'total_pos': basic_stats[0] if basic_stats else 0,
                    'pending_pos': basic_stats[1] if basic_stats else 0,
                    'approved_pos': basic_stats[2] if basic_stats else 0,
                    'completed_pos': basic_stats[3] if basic_stats else 0,
                    'total_amount': float(basic_stats[4]) if basic_stats else 0,
                    'average_amount': float(basic_stats[5]) if basic_stats else 0,
                    'status_distribution': status_dist,
                    'supplier_stats': [
                        {'name': row[0], 'count': row[1], 'amount': float(row[2] or 0)}
                        for row in supplier_stats
                    ],
                    'monthly_stats': [
                        {'month': row[0], 'count': row[1], 'amount': float(row[2] or 0)}
                        for row in monthly_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"발주서 통계 조회 중 오류: {e}")
            return {}
    
    def delete_purchase_order(self, po_id: str) -> bool:
        """발주서 삭제 (상태를 '취소'로 변경)"""
        try:
            return self.update_purchase_order(po_id, {
                'status': '취소'
            })
        except Exception as e:
            logger.error(f"발주서 삭제 중 오류: {e}")
            return False
    
    def search_purchase_orders(self, search_term: str) -> pd.DataFrame:
        """발주서 검색"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                search_pattern = f"%{search_term}%"
                
                cursor.execute("""
                    SELECT DISTINCT po.* FROM purchase_orders po
                    LEFT JOIN purchase_order_items poi ON po.po_id = poi.po_id
                    WHERE po.po_number ILIKE %s 
                       OR po.supplier_name ILIKE %s
                       OR poi.product_name ILIKE %s
                       OR poi.product_code ILIKE %s
                    ORDER BY po.input_date DESC
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"발주서 검색 중 오류: {e}")
            return pd.DataFrame()
