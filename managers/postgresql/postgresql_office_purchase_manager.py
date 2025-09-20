"""
PostgreSQL 사무용품 구매 관리자 - 표준화된 PostgreSQL 전용 버전
managers/postgresql/postgresql_office_purchase_manager.py
"""

import pandas as pd
import psycopg2
from datetime import datetime, date
import streamlit as st
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Any, Tuple
from .base_postgresql_manager import BasePostgreSQLManager

logger = logging.getLogger(__name__)

class PostgreSQLOfficePurchaseManager(BasePostgreSQLManager):
    """PostgreSQL 사무용품 구매 관리 클래스"""
    
    def __init__(self):
        """클래스 초기화"""
        super().__init__()
        self.table_name = "office_purchases"
        self.items_table = "office_purchase_items"
        
        # 테이블 생성 확인
        self._ensure_tables_exist()
        
        logger.info("PostgreSQLOfficePurchaseManager 초기화 완료")
    
    def _ensure_tables_exist(self):
        """필요한 테이블들이 존재하는지 확인하고 생성"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 메인 구매 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS office_purchases (
                        id SERIAL PRIMARY KEY,
                        purchase_id VARCHAR(50) UNIQUE NOT NULL,
                        purchase_date DATE NOT NULL,
                        requester_name VARCHAR(100) NOT NULL,
                        department VARCHAR(100),
                        purchase_purpose TEXT,
                        supplier_name VARCHAR(200),
                        total_amount DECIMAL(15,2) DEFAULT 0,
                        payment_method VARCHAR(50),
                        receipt_number VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'pending',
                        notes TEXT,
                        input_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(100)
                    )
                """)
                
                # 구매 물품 상세 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS office_purchase_items (
                        item_id SERIAL PRIMARY KEY,
                        purchase_id VARCHAR(50) NOT NULL,
                        item_name VARCHAR(200) NOT NULL,
                        category VARCHAR(50) DEFAULT '기타',
                        quantity INTEGER DEFAULT 1,
                        unit VARCHAR(20) DEFAULT 'EA',
                        unit_price DECIMAL(10,2) DEFAULT 0,
                        total_price DECIMAL(12,2) DEFAULT 0,
                        item_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (purchase_id) REFERENCES office_purchases(purchase_id) 
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_office_purchases_date 
                    ON office_purchases(purchase_date DESC)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_office_purchases_requester 
                    ON office_purchases(requester_name)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_office_purchase_items_purchase_id 
                    ON office_purchase_items(purchase_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_office_purchase_items_category 
                    ON office_purchase_items(category)
                """)
                
                # 트리거 생성 (updated_at 자동 업데이트)
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_office_purchases_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql'
                """)
                
                cursor.execute("""
                    DROP TRIGGER IF EXISTS trigger_office_purchases_updated_at 
                    ON office_purchases
                """)
                
                cursor.execute("""
                    CREATE TRIGGER trigger_office_purchases_updated_at
                        BEFORE UPDATE ON office_purchases
                        FOR EACH ROW EXECUTE FUNCTION update_office_purchases_updated_at()
                """)
                
                conn.commit()
                logger.info("사무용품 구매 테이블 생성/확인 완료")
                return True
                
        except Exception as e:
            logger.error(f"테이블 생성 중 오류: {e}")
            return False
    
    def generate_purchase_id(self) -> str:
        """구매 ID 자동 생성 (형식: OFF20241220001)"""
        try:
            today = datetime.now()
            prefix = f"OFF{today.strftime('%Y%m%d')}"
            
            with self.get_db_connection() as conn:
                if conn is None:
                    return f"{prefix}001"
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT purchase_id FROM office_purchases 
                    WHERE purchase_id LIKE %s 
                    ORDER BY purchase_id DESC LIMIT 1
                """, (f"{prefix}%",))
                
                result = cursor.fetchone()
                
                if result:
                    last_id = result[0]
                    try:
                        suffix = int(last_id.replace(prefix, ''))
                        next_num = suffix + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
                
                return f"{prefix}{next_num:03d}"
                
        except Exception as e:
            logger.error(f"구매 ID 생성 중 오류: {e}")
            return f"OFF{datetime.now().strftime('%Y%m%d')}001"
    
    def create_purchase_record(self, purchase_data: Dict[str, Any]) -> Tuple[bool, str]:
        """새 구매 기록 생성"""
        try:
            # 데이터 검증
            validation_result = self._validate_purchase_data(purchase_data)
            if not validation_result[0]:
                return False, validation_result[1]
            
            with self.get_db_connection() as conn:
                if conn is None:
                    return False, "데이터베이스 연결 실패"
                
                cursor = conn.cursor()
                
                # ID 생성
                if not purchase_data.get('purchase_id'):
                    purchase_data['purchase_id'] = self.generate_purchase_id()
                
                # 기본값 설정
                if not purchase_data.get('purchase_date'):
                    purchase_data['purchase_date'] = date.today()
                
                if not purchase_data.get('status'):
                    purchase_data['status'] = 'pending'
                
                # 제품 목록 분리
                items = purchase_data.pop('items', [])
                
                # 총 금액 계산
                if items:
                    total_amount = sum(
                        float(item.get('total_price', 0)) for item in items
                        if item.get('total_price')
                    )
                    purchase_data['total_amount'] = total_amount
                
                # 메인 구매 정보 저장
                main_columns = [
                    'purchase_id', 'purchase_date', 'requester_name', 'department',
                    'purchase_purpose', 'supplier_name', 'total_amount', 
                    'payment_method', 'receipt_number', 'status', 'notes', 'created_by'
                ]
                
                values = [purchase_data.get(col) for col in main_columns]
                placeholders = ', '.join(['%s'] * len(main_columns))
                
                cursor.execute(f"""
                    INSERT INTO office_purchases ({', '.join(main_columns)})
                    VALUES ({placeholders})
                """, values)
                
                # 물품 상세 정보 저장
                if items:
                    for item in items:
                        if not item.get('item_name'):
                            continue
                        
                        # 물품별 총액 계산
                        unit_price = float(item.get('unit_price', 0))
                        quantity = float(item.get('quantity', 1))
                        total_price = unit_price * quantity
                        
                        cursor.execute("""
                            INSERT INTO office_purchase_items 
                            (purchase_id, item_name, category, quantity, unit, 
                             unit_price, total_price, item_notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            purchase_data['purchase_id'],
                            item.get('item_name'),
                            item.get('category', '기타'),
                            quantity,
                            item.get('unit', 'EA'),
                            unit_price,
                            total_price,
                            item.get('item_notes', '')
                        ))
                
                conn.commit()
                logger.info(f"구매 기록 생성 완료: {purchase_data['purchase_id']}")
                return True, f"구매 기록이 성공적으로 생성되었습니다. (ID: {purchase_data['purchase_id']})"
                
        except psycopg2.IntegrityError as e:
            logger.error(f"데이터 무결성 오류: {e}")
            return False, "중복된 구매 ID이거나 필수 데이터가 누락되었습니다."
        except Exception as e:
            logger.error(f"구매 기록 생성 중 오류: {e}")
            return False, f"구매 기록 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _validate_purchase_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """구매 데이터 유효성 검증"""
        required_fields = ['requester_name']
        
        for field in required_fields:
            if not data.get(field):
                return False, f"{field}는 필수 입력 항목입니다."
        
        # 날짜 검증
        if data.get('purchase_date'):
            if isinstance(data['purchase_date'], str):
                try:
                    data['purchase_date'] = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
                except ValueError:
                    return False, "구매 날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"
        
        # 금액 검증
        if data.get('total_amount'):
            try:
                data['total_amount'] = float(data['total_amount'])
                if data['total_amount'] < 0:
                    return False, "구매 금액은 0 이상이어야 합니다."
            except (ValueError, TypeError):
                return False, "구매 금액은 숫자여야 합니다."
        
        return True, "검증 완료"
    
    def get_all_purchases(self, limit: int = 1000, offset: int = 0) -> pd.DataFrame:
        """모든 구매 기록 조회 (페이징 지원)"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        p.purchase_id, p.purchase_date, p.requester_name, p.department,
                        p.supplier_name, p.total_amount, p.payment_method, p.status,
                        p.input_date, p.notes,
                        COUNT(i.item_id) as item_count
                    FROM office_purchases p
                    LEFT JOIN office_purchase_items i ON p.purchase_id = i.purchase_id
                    GROUP BY p.id, p.purchase_id, p.purchase_date, p.requester_name, 
                             p.department, p.supplier_name, p.total_amount, 
                             p.payment_method, p.status, p.input_date, p.notes
                    ORDER BY p.purchase_date DESC, p.input_date DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                if not data:
                    return pd.DataFrame(columns=columns)
                
                df = pd.DataFrame(data, columns=columns)
                
                # 타입 변환
                if 'total_amount' in df.columns:
                    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
                
                return df
                
        except Exception as e:
            logger.error(f"구매 기록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_by_id(self, purchase_id: str) -> Optional[Dict[str, Any]]:
        """특정 구매 기록 상세 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return None
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM office_purchases WHERE purchase_id = %s
                """, (purchase_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                purchase_data = dict(zip(columns, result))
                
                # 물품 목록 추가
                purchase_data['items'] = self.get_purchase_items(purchase_id)
                
                return purchase_data
                
        except Exception as e:
            logger.error(f"구매 기록 조회 중 오류: {e}")
            return None
    
    def get_purchase_items(self, purchase_id: str) -> List[Dict[str, Any]]:
        """구매의 물품 목록 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT item_id, item_name, category, quantity, unit,
                           unit_price, total_price, item_notes, created_at
                    FROM office_purchase_items
                    WHERE purchase_id = %s
                    ORDER BY item_id
                """, (purchase_id,))
                
                columns = [desc[0] for desc in cursor.description]
                items = cursor.fetchall()
                
                return [dict(zip(columns, item)) for item in items]
                
        except Exception as e:
            logger.error(f"구매 물품 조회 중 오류: {e}")
            return []
    
    def update_purchase_status(self, purchase_id: str, status: str, notes: str = "") -> Tuple[bool, str]:
        """구매 상태 업데이트"""
        try:
            valid_statuses = ['pending', 'approved', 'ordered', 'received', 'completed', 'cancelled']
            if status not in valid_statuses:
                return False, f"유효하지 않은 상태입니다. 사용 가능한 상태: {', '.join(valid_statuses)}"
            
            with self.get_db_connection() as conn:
                if conn is None:
                    return False, "데이터베이스 연결 실패"
                
                cursor = conn.cursor()
                
                # 기존 레코드 확인
                cursor.execute("SELECT status FROM office_purchases WHERE purchase_id = %s", (purchase_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "해당 구매 기록을 찾을 수 없습니다."
                
                old_status = result[0]
                
                # 상태 업데이트
                update_query = """
                    UPDATE office_purchases 
                    SET status = %s, notes = COALESCE(notes, '') || %s
                    WHERE purchase_id = %s
                """
                
                status_note = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 상태 변경: {old_status} → {status}"
                if notes:
                    status_note += f" ({notes})"
                
                cursor.execute(update_query, (status, status_note, purchase_id))
                conn.commit()
                
                logger.info(f"구매 상태 업데이트: {purchase_id} -> {status}")
                return True, f"구매 상태가 '{status}'로 업데이트되었습니다."
                
        except Exception as e:
            logger.error(f"구매 상태 업데이트 중 오류: {e}")
            return False, f"상태 업데이트 중 오류가 발생했습니다: {str(e)}"
    
    def get_purchases_by_period(self, start_date: date, end_date: date) -> pd.DataFrame:
        """기간별 구매 기록 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, COUNT(i.item_id) as item_count
                    FROM office_purchases p
                    LEFT JOIN office_purchase_items i ON p.purchase_id = i.purchase_id
                    WHERE p.purchase_date BETWEEN %s AND %s
                    GROUP BY p.id
                    ORDER BY p.purchase_date DESC
                """, (start_date, end_date))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"기간별 구매 기록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_statistics(self, period_months: int = 12) -> Dict[str, Any]:
        """구매 통계 조회 (최근 N개월)"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return {}
                
                cursor = conn.cursor()
                
                # 기본 통계 (전체)
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_purchases,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(AVG(total_amount), 0) as average_amount,
                        COUNT(DISTINCT requester_name) as unique_requesters,
                        COUNT(DISTINCT department) as unique_departments,
                        COUNT(DISTINCT supplier_name) as unique_suppliers
                    FROM office_purchases
                    WHERE purchase_date >= CURRENT_DATE - INTERVAL '%s months'
                """, (period_months,))
                
                basic_stats = cursor.fetchone()
                
                # 카테고리별 통계
                cursor.execute("""
                    SELECT 
                        poi.category,
                        COUNT(*) as item_count,
                        SUM(poi.total_price) as category_total,
                        AVG(poi.unit_price) as avg_unit_price
                    FROM office_purchase_items poi
                    JOIN office_purchases po ON poi.purchase_id = po.purchase_id
                    WHERE po.purchase_date >= CURRENT_DATE - INTERVAL '%s months'
                    GROUP BY poi.category
                    ORDER BY category_total DESC
                """, (period_months,))
                category_stats = cursor.fetchall()
                
                # 부서별 통계
                cursor.execute("""
                    SELECT 
                        department,
                        COUNT(*) as purchase_count,
                        SUM(total_amount) as department_total,
                        AVG(total_amount) as avg_purchase_amount
                    FROM office_purchases
                    WHERE department IS NOT NULL 
                      AND purchase_date >= CURRENT_DATE - INTERVAL '%s months'
                    GROUP BY department
                    ORDER BY department_total DESC
                """, (period_months,))
                department_stats = cursor.fetchall()
                
                # 월별 통계
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('month', purchase_date) as month,
                        COUNT(*) as count,
                        SUM(total_amount) as amount,
                        COUNT(DISTINCT requester_name) as requesters
                    FROM office_purchases
                    WHERE purchase_date >= CURRENT_DATE - INTERVAL '%s months'
                    GROUP BY DATE_TRUNC('month', purchase_date)
                    ORDER BY month DESC
                """, (period_months,))
                monthly_stats = cursor.fetchall()
                
                # 상태별 통계
                cursor.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        SUM(total_amount) as amount
                    FROM office_purchases
                    WHERE purchase_date >= CURRENT_DATE - INTERVAL '%s months'
                    GROUP BY status
                    ORDER BY count DESC
                """, (period_months,))
                status_stats = cursor.fetchall()
                
                return {
                    'period_months': period_months,
                    'total_purchases': basic_stats[0] if basic_stats else 0,
                    'total_amount': float(basic_stats[1]) if basic_stats else 0,
                    'average_amount': float(basic_stats[2]) if basic_stats else 0,
                    'unique_requesters': basic_stats[3] if basic_stats else 0,
                    'unique_departments': basic_stats[4] if basic_stats else 0,
                    'unique_suppliers': basic_stats[5] if basic_stats else 0,
                    'category_stats': [
                        {
                            'category': row[0], 
                            'count': row[1], 
                            'amount': float(row[2] or 0),
                            'avg_unit_price': float(row[3] or 0)
                        }
                        for row in category_stats
                    ],
                    'department_stats': [
                        {
                            'department': row[0], 
                            'count': row[1], 
                            'amount': float(row[2] or 0),
                            'avg_amount': float(row[3] or 0)
                        }
                        for row in department_stats
                    ],
                    'monthly_stats': [
                        {
                            'month': row[0], 
                            'count': row[1], 
                            'amount': float(row[2] or 0),
                            'requesters': row[3]
                        }
                        for row in monthly_stats
                    ],
                    'status_stats': [
                        {
                            'status': row[0],
                            'count': row[1],
                            'amount': float(row[2] or 0)
                        }
                        for row in status_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"구매 통계 조회 중 오류: {e}")
            return {}
    
    def search_purchases(self, search_term: str, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """구매 기록 검색 (고급 필터 지원)"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                
                # 기본 검색 조건
                where_conditions = []
                params = []
                
                if search_term:
                    search_pattern = f"%{search_term}%"
                    where_conditions.append("""
                        (po.requester_name ILIKE %s 
                         OR po.department ILIKE %s
                         OR po.supplier_name ILIKE %s
                         OR poi.item_name ILIKE %s
                         OR poi.category ILIKE %s)
                    """)
                    params.extend([search_pattern] * 5)
                
                # 추가 필터 적용
                if filters:
                    if filters.get('department'):
                        where_conditions.append("po.department = %s")
                        params.append(filters['department'])
                    
                    if filters.get('status'):
                        where_conditions.append("po.status = %s")
                        params.append(filters['status'])
                    
                    if filters.get('category'):
                        where_conditions.append("poi.category = %s")
                        params.append(filters['category'])
                    
                    if filters.get('start_date'):
                        where_conditions.append("po.purchase_date >= %s")
                        params.append(filters['start_date'])
                    
                    if filters.get('end_date'):
                        where_conditions.append("po.purchase_date <= %s")
                        params.append(filters['end_date'])
                    
                    if filters.get('min_amount'):
                        where_conditions.append("po.total_amount >= %s")
                        params.append(filters['min_amount'])
                    
                    if filters.get('max_amount'):
                        where_conditions.append("po.total_amount <= %s")
                        params.append(filters['max_amount'])
                
                # WHERE 절 구성
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                query = f"""
                    SELECT DISTINCT po.*,
                           COUNT(poi.item_id) OVER (PARTITION BY po.purchase_id) as item_count
                    FROM office_purchases po
                    LEFT JOIN office_purchase_items poi ON po.purchase_id = poi.purchase_id
                    {where_clause}
                    ORDER BY po.purchase_date DESC, po.input_date DESC
                """
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"구매 기록 검색 중 오류: {e}")
            return pd.DataFrame()
    
    def delete_purchase(self, purchase_id: str) -> Tuple[bool, str]:
        """구매 기록 삭제 (관련 물품도 함께 삭제)"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False, "데이터베이스 연결 실패"
                
                cursor = conn.cursor()
                
                # 기존 레코드 확인
                cursor.execute("SELECT purchase_id FROM office_purchases WHERE purchase_id = %s", (purchase_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "해당 구매 기록을 찾을 수 없습니다."
                
                # 연관된 물품들이 외래키 제약으로 자동 삭제됨 (CASCADE)
                cursor.execute("DELETE FROM office_purchases WHERE purchase_id = %s", (purchase_id,))
                
                conn.commit()
                logger.info(f"구매 기록 삭제 완료: {purchase_id}")
                return True, "구매 기록이 성공적으로 삭제되었습니다."
                
        except Exception as e:
            logger.error(f"구매 기록 삭제 중 오류: {e}")
            return False, f"삭제 중 오류가 발생했습니다: {str(e)}"
    
    def export_purchases_to_csv(self, start_date: date = None, end_date: date = None) -> Optional[pd.DataFrame]:
        """구매 기록을 CSV 내보내기용 DataFrame으로 변환"""
        try:
            # 기간 설정
            if not start_date:
                start_date = date.today().replace(day=1)  # 이번 달 1일
            if not end_date:
                end_date = date.today()
            
            # 구매 기록 조회
            df_purchases = self.get_purchases_by_period(start_date, end_date)
            
            if df_purchases.empty:
                return None
            
            # 물품 정보 추가
            purchase_details = []
            for _, purchase in df_purchases.iterrows():
                items = self.get_purchase_items(purchase['purchase_id'])
                
                if items:
                    for item in items:
                        detail = {
                            '구매ID': purchase['purchase_id'],
                            '구매날짜': purchase['purchase_date'],
                            '요청자': purchase['requester_name'],
                            '부서': purchase['department'],
                            '구매목적': purchase['purchase_purpose'],
                            '공급업체': purchase['supplier_name'],
                            '결제방법': purchase['payment_method'],
                            '상태': purchase['status'],
                            '물품명': item['item_name'],
                            '카테고리': item['category'],
                            '수량': item['quantity'],
                            '단위': item['unit'],
                            '단가': item['unit_price'],
                            '금액': item['total_price'],
                            '물품메모': item['item_notes'],
                            '총구매금액': purchase['total_amount'],
                            '등록일시': purchase['input_date']
                        }
                        purchase_details.append(detail)
                else:
                    # 물품이 없는 경우도 포함
                    detail = {
                        '구매ID': purchase['purchase_id'],
                        '구매날짜': purchase['purchase_date'],
                        '요청자': purchase['requester_name'],
                        '부서': purchase['department'],
                        '구매목적': purchase['purchase_purpose'],
                        '공급업체': purchase['supplier_name'],
                        '결제방법': purchase['payment_method'],
                        '상태': purchase['status'],
                        '물품명': '',
                        '카테고리': '',
                        '수량': 0,
                        '단위': '',
                        '단가': 0,
                        '금액': 0,
                        '물품메모': '',
                        '총구매금액': purchase['total_amount'],
                        '등록일시': purchase['input_date']
                    }
                    purchase_details.append(detail)
            
            return pd.DataFrame(purchase_details)
            
        except Exception as e:
            logger.error(f"CSV 내보내기 중 오류: {e}")
            return None
