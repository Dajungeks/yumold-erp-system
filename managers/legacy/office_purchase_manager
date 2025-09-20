"""
사무용품 구매 관리자 - 회사 내부용 물품 구매 기록
"""

import pandas as pd
import psycopg2
from datetime import datetime, date
import streamlit as st
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class OfficePurchaseManager:
    """사무용품 구매 관리 클래스"""
    
    def __init__(self):
        """클래스 초기화"""
        self.table_created = True
        
        # 연결 테스트
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    logger.warning("데이터베이스 연결 실패")
                    self.table_created = False
                else:
                    logger.info("OfficePurchaseManager 초기화 완료")
        except Exception as e:
            logger.error(f"초기화 중 오류: {e}")
            self.table_created = False
    
    @contextmanager
    def get_db_connection(self):
        """안전한 데이터베이스 연결"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                port=st.secrets["postgres"]["port"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"],
                connect_timeout=10,
                application_name="YMV_ERP_OfficePurchase"
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
    
    def generate_purchase_id(self) -> str:
        """구매 ID 자동 생성"""
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
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                
                return f"{prefix}{next_num:03d}"
                
        except Exception as e:
            logger.error(f"구매 ID 생성 중 오류: {e}")
            return f"OFF{datetime.now().strftime('%Y%m%d')}001"
    
    def create_purchase_record(self, purchase_data: Dict[str, Any]) -> bool:
        """새 구매 기록 생성"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return False
                
                cursor = conn.cursor()
                
                # 필수 데이터 검증
                if not purchase_data.get('requester_name'):
                    st.error("요청자명은 필수입니다.")
                    return False
                
                if not purchase_data.get('purchase_date'):
                    purchase_data['purchase_date'] = date.today()
                
                # ID 생성
                if not purchase_data.get('purchase_id'):
                    purchase_data['purchase_id'] = self.generate_purchase_id()
                
                # 제품 목록 분리
                items = purchase_data.pop('items', [])
                
                # 총 금액 계산
                if items:
                    total_amount = sum(
                        float(item.get('total_price', 0)) for item in items
                    )
                    purchase_data['total_amount'] = total_amount
                
                # 메인 구매 정보 저장
                main_columns = [
                    'purchase_id', 'purchase_date', 'requester_name', 'department',
                    'purchase_purpose', 'supplier_name', 'total_amount', 
                    'payment_method', 'receipt_number', 'status', 'notes'
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
                            
                        cursor.execute("""
                            INSERT INTO office_purchase_items 
                            (purchase_id, item_name, category, quantity, unit, 
                             unit_price, total_price, item_notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            purchase_data['purchase_id'],
                            item.get('item_name'),
                            item.get('category', '기타'),
                            item.get('quantity', 1),
                            item.get('unit', 'EA'),
                            item.get('unit_price', 0),
                            item.get('total_price', 0),
                            item.get('item_notes', '')
                        ))
                
                conn.commit()
                logger.info(f"구매 기록 생성 완료: {purchase_data['purchase_id']}")
                return True
                
        except Exception as e:
            logger.error(f"구매 기록 생성 중 오류: {e}")
            return False
    
    def get_all_purchases(self) -> pd.DataFrame:
        """모든 구매 기록 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT purchase_id, purchase_date, requester_name, department,
                           supplier_name, total_amount, payment_method, status,
                           input_date, notes
                    FROM office_purchases
                    ORDER BY purchase_date DESC, input_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                if not data:
                    return pd.DataFrame(columns=columns)
                
                df = pd.DataFrame(data, columns=columns)
                
                # 각 구매의 물품 수 추가
                df['item_count'] = df['purchase_id'].apply(
                    lambda pid: self._get_item_count(pid)
                )
                
                return df
                
        except Exception as e:
            logger.error(f"구매 기록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def _get_item_count(self, purchase_id: str) -> int:
        """구매의 물품 항목 수 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return 0
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM office_purchase_items WHERE purchase_id = %s
                """, (purchase_id,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"항목 수 조회 오류: {e}")
            return 0
    
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
    
    def get_purchases_by_period(self, start_date: date, end_date: date) -> pd.DataFrame:
        """기간별 구매 기록 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM office_purchases 
                    WHERE purchase_date BETWEEN %s AND %s
                    ORDER BY purchase_date DESC
                """, (start_date, end_date))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"기간별 구매 기록 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_purchase_statistics(self) -> Dict[str, Any]:
        """구매 통계 조회"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return {}
                
                cursor = conn.cursor()
                
                # 기본 통계
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_purchases,
                        COALESCE(SUM(total_amount), 0) as total_amount,
                        COALESCE(AVG(total_amount), 0) as average_amount,
                        COUNT(DISTINCT requester_name) as unique_requesters,
                        COUNT(DISTINCT department) as unique_departments
                    FROM office_purchases
                """)
                
                basic_stats = cursor.fetchone()
                
                # 카테고리별 통계
                cursor.execute("""
                    SELECT 
                        poi.category,
                        COUNT(*) as item_count,
                        SUM(poi.total_price) as category_total
                    FROM office_purchase_items poi
                    JOIN office_purchases po ON poi.purchase_id = po.purchase_id
                    GROUP BY poi.category
                    ORDER BY category_total DESC
                """)
                category_stats = cursor.fetchall()
                
                # 부서별 통계
                cursor.execute("""
                    SELECT 
                        department,
                        COUNT(*) as purchase_count,
                        SUM(total_amount) as department_total
                    FROM office_purchases
                    WHERE department IS NOT NULL
                    GROUP BY department
                    ORDER BY department_total DESC
                """)
                department_stats = cursor.fetchall()
                
                # 월별 통계
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('month', purchase_date) as month,
                        COUNT(*) as count,
                        SUM(total_amount) as amount
                    FROM office_purchases
                    WHERE purchase_date >= CURRENT_DATE - INTERVAL '12 months'
                    GROUP BY DATE_TRUNC('month', purchase_date)
                    ORDER BY month
                """)
                monthly_stats = cursor.fetchall()
                
                return {
                    'total_purchases': basic_stats[0] if basic_stats else 0,
                    'total_amount': float(basic_stats[1]) if basic_stats else 0,
                    'average_amount': float(basic_stats[2]) if basic_stats else 0,
                    'unique_requesters': basic_stats[3] if basic_stats else 0,
                    'unique_departments': basic_stats[4] if basic_stats else 0,
                    'category_stats': [
                        {'category': row[0], 'count': row[1], 'amount': float(row[2] or 0)}
                        for row in category_stats
                    ],
                    'department_stats': [
                        {'department': row[0], 'count': row[1], 'amount': float(row[2] or 0)}
                        for row in department_stats
                    ],
                    'monthly_stats': [
                        {'month': row[0], 'count': row[1], 'amount': float(row[2] or 0)}
                        for row in monthly_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"구매 통계 조회 중 오류: {e}")
            return {}
    
    def search_purchases(self, search_term: str) -> pd.DataFrame:
        """구매 기록 검색"""
        try:
            with self.get_db_connection() as conn:
                if conn is None:
                    return pd.DataFrame()
                
                cursor = conn.cursor()
                search_pattern = f"%{search_term}%"
                
                cursor.execute("""
                    SELECT DISTINCT po.* FROM office_purchases po
                    LEFT JOIN office_purchase_items poi ON po.purchase_id = poi.purchase_id
                    WHERE po.requester_name ILIKE %s 
                       OR po.department ILIKE %s
                       OR po.supplier_name ILIKE %s
                       OR poi.item_name ILIKE %s
                       OR poi.category ILIKE %s
                    ORDER BY po.purchase_date DESC
                """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            logger.error(f"구매 기록 검색 중 오류: {e}")
            return pd.DataFrame()
