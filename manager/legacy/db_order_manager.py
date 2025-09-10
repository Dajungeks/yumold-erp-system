"""
SQLite 기반 주문 관리자
기존 order_manager.py의 SQLite 버전
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from .database_manager import DatabaseManager

class DBOrderManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 주문 관리자 초기화"""
        self.db_manager = DatabaseManager(db_path)
    
    def get_all_orders(self):
        """모든 주문 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders ORDER BY order_date DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_order_by_id(self, order_id):
        """특정 주문 정보 반환"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_order(self, order_data):
        """새 주문 추가"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO orders 
                    (order_id, quotation_id, customer_id, customer_name, order_date,
                     requested_delivery_date, confirmed_delivery_date, total_amount, 
                     currency, order_status, payment_status, payment_terms, 
                     special_instructions, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_data.get('order_id'),
                    order_data.get('quotation_id', ''),
                    order_data.get('customer_id'),
                    order_data.get('customer_name'),
                    order_data.get('order_date'),
                    order_data.get('requested_delivery_date', ''),
                    order_data.get('confirmed_delivery_date', ''),
                    order_data.get('total_amount', 0),
                    order_data.get('currency', 'VND'),
                    order_data.get('order_status', 'pending'),
                    order_data.get('payment_status', 'pending'),
                    order_data.get('payment_terms', ''),
                    order_data.get('special_instructions', ''),
                    order_data.get('created_by', '')
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 중복 ID
        except Exception as e:
            print(f"주문 추가 오류: {e}")
            return False
    
    def update_order(self, order_id, order_data):
        """주문 정보 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE orders 
                    SET quotation_id=?, customer_id=?, customer_name=?, order_date=?,
                        requested_delivery_date=?, confirmed_delivery_date=?, total_amount=?,
                        currency=?, order_status=?, payment_status=?, payment_terms=?,
                        special_instructions=?, updated_date=CURRENT_TIMESTAMP
                    WHERE order_id=?
                ''', (
                    order_data.get('quotation_id', ''),
                    order_data.get('customer_id'),
                    order_data.get('customer_name'),
                    order_data.get('order_date'),
                    order_data.get('requested_delivery_date', ''),
                    order_data.get('confirmed_delivery_date', ''),
                    order_data.get('total_amount', 0),
                    order_data.get('currency', 'VND'),
                    order_data.get('order_status', 'pending'),
                    order_data.get('payment_status', 'pending'),
                    order_data.get('payment_terms', ''),
                    order_data.get('special_instructions', ''),
                    order_id
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"주문 업데이트 오류: {e}")
            return False
    
    def update_order_status(self, order_id, new_status, updated_by):
        """주문 상태 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE orders 
                    SET order_status=?, updated_date=CURRENT_TIMESTAMP
                    WHERE order_id=?
                ''', (new_status, order_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"주문 상태 업데이트 오류: {e}")
            return False
    
    def update_payment_status(self, order_id, payment_status, updated_by):
        """결제 상태 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE orders 
                    SET payment_status=?, updated_date=CURRENT_TIMESTAMP
                    WHERE order_id=?
                ''', (payment_status, order_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"결제 상태 업데이트 오류: {e}")
            return False
    
    def update_delivery_date(self, order_id, delivery_date, updated_by):
        """배송일 업데이트"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE orders 
                    SET confirmed_delivery_date=?, updated_date=CURRENT_TIMESTAMP
                    WHERE order_id=?
                ''', (delivery_date, order_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"배송일 업데이트 오류: {e}")
            return False
    
    def delete_order(self, order_id):
        """주문 삭제"""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"주문 삭제 오류: {e}")
            return False
    
    def get_filtered_orders(self, status_filter=None, customer_filter=None, 
                           date_from=None, date_to=None, search_term=None):
        """필터링된 주문 목록 반환"""
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND order_status = ?"
            params.append(status_filter)
        
        if customer_filter:
            query += " AND customer_id = ?"
            params.append(customer_filter)
        
        if date_from:
            query += " AND order_date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND order_date <= ?"
            params.append(date_to)
        
        if search_term:
            query += " AND (order_id LIKE ? OR customer_name LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param])
        
        query += " ORDER BY order_date DESC"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_order_statistics(self):
        """주문 통계 반환"""
        with self.db_manager.get_connection() as conn:
            stats = {}
            
            # 총 주문 수
            cursor = conn.execute("SELECT COUNT(*) FROM orders")
            stats['total_orders'] = cursor.fetchone()[0]
            
            # 진행 중인 주문
            cursor = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status IN ('pending', 'confirmed', 'in_production')")
            stats['pending_orders'] = cursor.fetchone()[0]
            
            # 완료된 주문
            cursor = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'")
            stats['completed_orders'] = cursor.fetchone()[0]
            
            # 총 주문 금액
            cursor = conn.execute("SELECT SUM(total_amount) FROM orders")
            total_amount = cursor.fetchone()[0]
            stats['total_amount'] = total_amount if total_amount else 0
            
            # 평균 주문 금액
            if stats['total_orders'] > 0:
                stats['avg_order_value'] = stats['total_amount'] / stats['total_orders']
            else:
                stats['avg_order_value'] = 0
            
            # 상태별 분포
            cursor = conn.execute("SELECT order_status, COUNT(*) FROM orders GROUP BY order_status")
            stats['status_distribution'] = dict(cursor.fetchall())
            
            # 결제 상태별 분포
            cursor = conn.execute("SELECT payment_status, COUNT(*) FROM orders GROUP BY payment_status")
            stats['payment_distribution'] = dict(cursor.fetchall())
            
            return stats
    
    def get_delivery_schedule(self):
        """배송 예정 주문 목록"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM orders 
                WHERE order_status IN ('confirmed', 'in_production', 'shipped')
                AND requested_delivery_date IS NOT NULL
                ORDER BY requested_delivery_date
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_orders_by_customer(self, customer_id):
        """특정 고객의 주문 목록"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY order_date DESC", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_orders_by_status(self, status):
        """특정 상태의 주문 목록"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM orders WHERE order_status = ? ORDER BY order_date DESC", (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_order_trend(self, months=6):
        """월별 주문 추이"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    strftime('%Y-%m', order_date) as month,
                    COUNT(*) as order_count,
                    SUM(total_amount) as total_amount
                FROM orders 
                WHERE order_date >= date('now', '-{} months')
                GROUP BY strftime('%Y-%m', order_date)
                ORDER BY month
            '''.format(months))
            
            results = cursor.fetchall()
            return {
                'months': [row[0] for row in results],
                'order_counts': [row[1] for row in results],
                'total_amounts': [row[2] for row in results]
            }
    
    def generate_order_id(self):
        """새 주문 ID 생성"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT MAX(CAST(SUBSTR(order_id, 3) AS INTEGER)) FROM orders WHERE order_id LIKE 'ORD%'")
            max_id = cursor.fetchone()[0]
            if max_id:
                return f"ORD{max_id + 1:05d}"
            else:
                return "ORD00001"
    
    def export_to_dataframe(self):
        """주문 데이터를 DataFrame으로 반환"""
        orders = self.get_all_orders()
        return pd.DataFrame(orders)