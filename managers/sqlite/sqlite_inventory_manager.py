# -*- coding: utf-8 -*-
"""
SQLite 기반 재고 관리 시스템
"""

import sqlite3
import pandas as pd
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class SQLiteInventoryManager:
    def __init__(self, db_path="erp_system.db"):
        """SQLite 기반 재고 매니저 초기화"""
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """재고 관련 테이블 초기화"""
        with self.get_connection() as conn:
            # 재고 현황 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    product_id TEXT,
                    product_code TEXT,
                    product_name TEXT NOT NULL,
                    category TEXT,
                    location TEXT,
                    warehouse TEXT,
                    current_stock REAL DEFAULT 0,
                    reserved_stock REAL DEFAULT 0,
                    available_stock REAL DEFAULT 0,
                    minimum_stock REAL DEFAULT 0,
                    maximum_stock REAL DEFAULT 0,
                    unit_cost REAL DEFAULT 0,
                    currency TEXT DEFAULT 'VND',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    notes TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            ''')
            
            # 재고 이동 이력 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inventory_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movement_id TEXT UNIQUE NOT NULL,
                    item_id TEXT NOT NULL,
                    movement_type TEXT NOT NULL CHECK (movement_type IN ('in', 'out', 'adjustment', 'transfer')),
                    quantity REAL NOT NULL,
                    unit_cost REAL DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    reference_id TEXT,
                    reference_type TEXT,
                    location_from TEXT,
                    location_to TEXT,
                    movement_date TEXT NOT NULL,
                    created_by TEXT,
                    notes TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
                )
            ''')
            
            # 재고 조정 기록 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inventory_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adjustment_id TEXT UNIQUE NOT NULL,
                    item_id TEXT NOT NULL,
                    adjustment_date TEXT NOT NULL,
                    old_quantity REAL NOT NULL,
                    new_quantity REAL NOT NULL,
                    adjustment_quantity REAL NOT NULL,
                    adjustment_reason TEXT,
                    adjusted_by TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'completed',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
                )
            ''')
            
            conn.commit()
            logger.info("재고 관련 테이블 초기화 완료")
    
    def generate_item_id(self):
        """재고 아이템 ID 생성"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM inventory_items')
            count = cursor.fetchone()[0]
            return f"INV{count+1:06d}"
    
    def add_inventory_item(self, item_data):
        """재고 아이템 추가"""
        try:
            with self.get_connection() as conn:
                # ID 자동 생성
                if 'item_id' not in item_data or not item_data['item_id']:
                    item_data['item_id'] = self.generate_item_id()
                
                # 중복 확인 (제품 코드로)
                if item_data.get('product_code'):
                    cursor = conn.execute('SELECT COUNT(*) FROM inventory_items WHERE product_code = ?', 
                                        (item_data['product_code'],))
                    if cursor.fetchone()[0] > 0:
                        return False, "이미 등록된 제품입니다."
                
                # 기본값 설정
                current_stock = float(item_data.get('current_stock', 0))
                reserved_stock = float(item_data.get('reserved_stock', 0))
                available_stock = current_stock - reserved_stock
                
                # 데이터 삽입
                conn.execute('''
                    INSERT INTO inventory_items (
                        item_id, product_id, product_code, product_name, category,
                        location, warehouse, current_stock, reserved_stock, available_stock,
                        minimum_stock, maximum_stock, unit_cost, currency, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_data['item_id'],
                    item_data.get('product_id', ''),
                    item_data.get('product_code', ''),
                    item_data['product_name'],
                    item_data.get('category', ''),
                    item_data.get('location', ''),
                    item_data.get('warehouse', ''),
                    current_stock,
                    reserved_stock,
                    available_stock,
                    float(item_data.get('minimum_stock', 0)),
                    float(item_data.get('maximum_stock', 0)),
                    float(item_data.get('unit_cost', 0)),
                    item_data.get('currency', 'VND'),
                    item_data.get('notes', '')
                ))
                
                # 초기 재고 이동 기록 생성 (재고 추가)
                if current_stock > 0:
                    self._add_inventory_movement(
                        conn, item_data['item_id'], 'in', current_stock,
                        float(item_data.get('unit_cost', 0)), 
                        reference_type='initial_stock',
                        notes='초기 재고 등록'
                    )
                
                conn.commit()
                logger.info(f"재고 아이템 추가 성공: {item_data['item_id']}")
                return True, "재고 아이템이 성공적으로 추가되었습니다."
                
        except Exception as e:
            logger.error(f"재고 아이템 추가 오류: {str(e)}")
            return False, f"재고 아이템 추가 중 오류가 발생했습니다: {str(e)}"
    
    def _add_inventory_movement(self, conn, item_id, movement_type, quantity, unit_cost=0, 
                              reference_id="", reference_type="", location_from="", location_to="", notes=""):
        """재고 이동 기록 추가 (내부 함수)"""
        movement_id = f"MOV{datetime.now().strftime('%Y%m%d%H%M%S')}{item_id[-3:]}"
        total_cost = quantity * unit_cost
        
        conn.execute('''
            INSERT INTO inventory_movements (
                movement_id, item_id, movement_type, quantity, unit_cost, total_cost,
                reference_id, reference_type, location_from, location_to, 
                movement_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            movement_id, item_id, movement_type, quantity, unit_cost, total_cost,
            reference_id, reference_type, location_from, location_to,
            datetime.now().strftime('%Y-%m-%d'), notes
        ))
    
    def update_stock(self, item_id, movement_type, quantity, unit_cost=0, reference_id="", reference_type="", notes=""):
        """재고 수량 업데이트"""
        try:
            with self.get_connection() as conn:
                # 현재 재고 정보 조회
                cursor = conn.execute('SELECT * FROM inventory_items WHERE item_id = ?', (item_id,))
                item = cursor.fetchone()
                
                if not item:
                    return False, "해당 재고 아이템을 찾을 수 없습니다."
                
                current_stock = float(item['current_stock'])
                reserved_stock = float(item['reserved_stock'])
                
                # 재고 수량 계산
                if movement_type == 'in':
                    new_stock = current_stock + quantity
                elif movement_type == 'out':
                    new_stock = current_stock - quantity
                    if new_stock < 0:
                        return False, "재고가 부족합니다."
                elif movement_type == 'adjustment':
                    # 조정의 경우 quantity는 조정 후 수량
                    new_stock = quantity
                else:
                    return False, "잘못된 이동 유형입니다."
                
                available_stock = new_stock - reserved_stock
                
                # 재고 수량 업데이트
                conn.execute('''
                    UPDATE inventory_items 
                    SET current_stock = ?, available_stock = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                ''', (new_stock, available_stock, item_id))
                
                # 재고 이동 기록 추가
                self._add_inventory_movement(
                    conn, item_id, movement_type, 
                    quantity if movement_type != 'adjustment' else (new_stock - current_stock),
                    unit_cost, reference_id, reference_type, notes=notes
                )
                
                # 조정의 경우 별도 조정 기록
                if movement_type == 'adjustment':
                    adjustment_id = f"ADJ{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    conn.execute('''
                        INSERT INTO inventory_adjustments (
                            adjustment_id, item_id, adjustment_date, old_quantity, 
                            new_quantity, adjustment_quantity, adjustment_reason, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        adjustment_id, item_id, datetime.now().strftime('%Y-%m-%d'),
                        current_stock, new_stock, new_stock - current_stock,
                        reference_type, notes
                    ))
                
                conn.commit()
                logger.info(f"재고 업데이트 성공: {item_id} - {movement_type} {quantity}")
                return True, "재고가 성공적으로 업데이트되었습니다."
                
        except Exception as e:
            logger.error(f"재고 업데이트 오류: {str(e)}")
            return False, f"재고 업데이트 중 오류가 발생했습니다: {str(e)}"
    
    def get_all_inventory(self):
        """전체 재고 현황 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM inventory_items
                    WHERE status = 'active'
                    ORDER BY product_name
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"재고 현황 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_low_stock_items(self):
        """부족 재고 아이템 조회"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM inventory_items
                    WHERE status = 'active' 
                    AND current_stock <= minimum_stock
                    ORDER BY (current_stock - minimum_stock)
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"부족 재고 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_inventory_movements(self, item_id=None, start_date=None, end_date=None):
        """재고 이동 이력 조회"""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT im.*, ii.product_name
                    FROM inventory_movements im
                    JOIN inventory_items ii ON im.item_id = ii.item_id
                '''
                
                conditions = []
                params = []
                
                if item_id:
                    conditions.append("im.item_id = ?")
                    params.append(item_id)
                
                if start_date:
                    conditions.append("DATE(im.movement_date) >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("DATE(im.movement_date) <= ?")
                    params.append(end_date)
                
                if conditions:
                    query = base_query + " WHERE " + " AND ".join(conditions)
                else:
                    query = base_query
                
                query += " ORDER BY im.created_date DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"재고 이동 이력 조회 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_inventory_valuation(self):
        """재고 평가액 계산"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        category,
                        warehouse,
                        SUM(current_stock * unit_cost) as total_value,
                        SUM(current_stock) as total_quantity,
                        COUNT(*) as item_count
                    FROM inventory_items
                    WHERE status = 'active'
                    GROUP BY category, warehouse
                    ORDER BY total_value DESC
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            logger.error(f"재고 평가액 계산 오류: {str(e)}")
            return pd.DataFrame()
    
    def reserve_stock(self, item_id, quantity, reference_id="", notes=""):
        """재고 예약"""
        try:
            with self.get_connection() as conn:
                # 현재 재고 정보 조회
                cursor = conn.execute('SELECT * FROM inventory_items WHERE item_id = ?', (item_id,))
                item = cursor.fetchone()
                
                if not item:
                    return False, "해당 재고 아이템을 찾을 수 없습니다."
                
                current_stock = float(item['current_stock'])
                reserved_stock = float(item['reserved_stock'])
                available_stock = float(item['available_stock'])
                
                # 예약 가능 수량 확인
                if quantity > available_stock:
                    return False, f"예약 가능 수량이 부족합니다. (가능: {available_stock})"
                
                # 예약 수량 업데이트
                new_reserved = reserved_stock + quantity
                new_available = current_stock - new_reserved
                
                conn.execute('''
                    UPDATE inventory_items 
                    SET reserved_stock = ?, available_stock = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                ''', (new_reserved, new_available, item_id))
                
                conn.commit()
                logger.info(f"재고 예약 성공: {item_id} - {quantity}")
                return True, "재고가 성공적으로 예약되었습니다."
                
        except Exception as e:
            logger.error(f"재고 예약 오류: {str(e)}")
            return False, f"재고 예약 중 오류가 발생했습니다: {str(e)}"
    
    def release_reservation(self, item_id, quantity):
        """재고 예약 해제"""
        try:
            with self.get_connection() as conn:
                # 현재 재고 정보 조회
                cursor = conn.execute('SELECT * FROM inventory_items WHERE item_id = ?', (item_id,))
                item = cursor.fetchone()
                
                if not item:
                    return False, "해당 재고 아이템을 찾을 수 없습니다."
                
                current_stock = float(item['current_stock'])
                reserved_stock = float(item['reserved_stock'])
                
                # 해제 수량 검증
                if quantity > reserved_stock:
                    return False, "예약 해제 수량이 예약 수량보다 큽니다."
                
                # 예약 수량 업데이트
                new_reserved = reserved_stock - quantity
                new_available = current_stock - new_reserved
                
                conn.execute('''
                    UPDATE inventory_items 
                    SET reserved_stock = ?, available_stock = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                ''', (new_reserved, new_available, item_id))
                
                conn.commit()
                logger.info(f"재고 예약 해제 성공: {item_id} - {quantity}")
                return True, "재고 예약이 성공적으로 해제되었습니다."
                
        except Exception as e:
            logger.error(f"재고 예약 해제 오류: {str(e)}")
            return False, f"재고 예약 해제 중 오류가 발생했습니다: {str(e)}"
    
    def search_inventory(self, search_term=""):
        """재고 검색"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM inventory_items
                    WHERE (product_name LIKE ? OR product_code LIKE ? OR category LIKE ?)
                    AND status = 'active'
                    ORDER BY product_name
                '''
                
                search_pattern = f"%{search_term}%"
                df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, search_pattern))
                return df
                
        except Exception as e:
            logger.error(f"재고 검색 오류: {str(e)}")
            return pd.DataFrame()