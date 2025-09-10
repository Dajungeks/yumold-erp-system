"""
Multi-Category Manager (Category B~I)
카테고리 B부터 I까지 통합 관리하는 매니저 클래스
"""

import sqlite3
import uuid
from datetime import datetime
from managers.legacy.database_manager import DatabaseManager

class MultiCategoryManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.init_tables()
    
    def init_tables(self):
        """테이블 초기화"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Category B~I 통합 구성 요소 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS multi_category_components (
                    component_id TEXT PRIMARY KEY,
                    category_type TEXT NOT NULL,
                    component_level TEXT NOT NULL,
                    parent_component TEXT,
                    component_key TEXT NOT NULL,
                    component_name TEXT NOT NULL,
                    component_name_en TEXT,
                    component_name_vi TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_date TEXT,
                    updated_date TEXT,
                    UNIQUE(category_type, parent_component, component_key)
                )
            ''')
            
            # 카테고리 설정 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_config (
                    category_type TEXT PRIMARY KEY,
                    category_name TEXT,
                    product_code_prefix TEXT,
                    description TEXT,
                    is_enabled INTEGER DEFAULT 0,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
            
            # 기본 카테고리 설정 초기화 (B~I, 비활성화 상태)
            categories = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for cat in categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO category_config 
                    (category_type, category_name, product_code_prefix, description, is_enabled, created_date, updated_date)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                ''', (cat, f"Category {cat}", f"H{cat}", f"Category {cat} 구성 요소", current_time, current_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Multi-category 테이블 초기화 오류: {e}")
    
    # ===== 카테고리 설정 관리 =====
    
    def get_category_config(self, category_type):
        """카테고리 설정 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT category_type, category_name, product_code_prefix, description, is_enabled
                FROM category_config 
                WHERE category_type = ?
            ''', (category_type,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'category_type': result[0],
                    'category_name': result[1],
                    'product_code_prefix': result[2],
                    'description': result[3],
                    'is_enabled': bool(result[4])
                }
            return None
            
        except Exception as e:
            print(f"카테고리 설정 조회 오류: {e}")
            return None
    
    def update_category_config(self, category_type, category_name, product_code_prefix, description, is_enabled):
        """카테고리 설정 업데이트"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE category_config 
                SET category_name = ?, product_code_prefix = ?, description = ?, 
                    is_enabled = ?, updated_date = ?
                WHERE category_type = ?
            ''', (category_name, product_code_prefix, description, int(is_enabled), current_time, category_type))
            
            conn.commit()
            result = cursor.rowcount > 0
            conn.close()
            return result
            
        except Exception as e:
            print(f"카테고리 설정 업데이트 오류: {e}")
            return False
    
    # ===== 구성 요소 관리 =====
    
    def get_components_by_level(self, category_type, component_level, parent_component=None):
        """특정 레벨의 구성 요소 조회"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if parent_component:
                cursor.execute('''
                    SELECT component_id, component_key, component_name, description
                    FROM multi_category_components 
                    WHERE category_type = ? AND component_level = ? 
                      AND parent_component = ? AND is_active = 1
                    ORDER BY component_key
                ''', (category_type, component_level, parent_component))
            else:
                cursor.execute('''
                    SELECT component_id, component_key, component_name, description
                    FROM multi_category_components 
                    WHERE category_type = ? AND component_level = ? 
                      AND parent_component IS NULL AND is_active = 1
                    ORDER BY component_key
                ''', (category_type, component_level))
            
            results = cursor.fetchall()
            conn.close()
            
            return [{'component_id': r[0], 'component_key': r[1], 'component_name': r[2], 'description': r[3]} for r in results]
            
        except Exception as e:
            print(f"구성 요소 조회 오류: {e}")
            return []
    
    def add_component(self, category_type, component_level, parent_component, component_key, component_name, description=None):
        """구성 요소 추가"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            component_id = f"{category_type}_{component_level.upper()}_{uuid.uuid4().hex[:8].upper()}"
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO multi_category_components 
                (component_id, category_type, component_level, parent_component, 
                 component_key, component_name, description, is_active, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ''', (component_id, category_type, component_level, parent_component,
                  component_key, component_name, description, current_time, current_time))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"구성 요소 추가 오류: {e}")
            return False
    
    def update_component(self, component_id, component_key=None, component_name=None, description=None):
        """구성 요소 수정 (계층관계 자동 업데이트 포함)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 현재 데이터 조회 (카테고리, 레벨, 부모 정보 포함)
            cursor.execute('''
                SELECT component_key, component_name, description, category_type, component_level, parent_component
                FROM multi_category_components 
                WHERE component_id = ?
            ''', (component_id,))
            current_data = cursor.fetchone()
            
            if not current_data:
                conn.close()
                return False
            
            old_key, old_name, old_desc, category_type, component_level, parent_component = current_data
            
            # 기본값으로 현재 데이터 사용
            final_key = component_key if component_key is not None else old_key
            final_name = component_name if component_name is not None else old_name
            final_description = description if description is not None else old_desc
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 키가 변경되었는지 확인
            key_changed = (final_key != old_key)
            
            # 구성 요소 업데이트
            cursor.execute('''
                UPDATE multi_category_components 
                SET component_key = ?, component_name = ?, description = ?, updated_date = ?
                WHERE component_id = ?
            ''', (final_key, final_name, final_description, current_time, component_id))
            
            # 키가 변경된 경우 하위 계층의 parent_component 업데이트
            if key_changed:
                self._update_child_parent_components(cursor, category_type, component_level, old_key, final_key, parent_component)
            
            conn.commit()
            result = cursor.rowcount > 0
            conn.close()
            
            if key_changed:
                print(f"계층관계 업데이트 완료: {old_key} → {final_key}")
                # 키가 변경된 경우는 항상 성공으로 처리 (계층관계 업데이트가 완료되었으므로)
                return True
            
            return result
            
        except Exception as e:
            print(f"구성 요소 수정 오류: {e}")
            return False
    
    def delete_component_permanently(self, component_id):
        """구성 요소 완전 삭제 (계층적 삭제 포함)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 삭제할 구성 요소 정보 조회
            cursor.execute('''
                SELECT category_type, component_level, component_key, parent_component 
                FROM multi_category_components 
                WHERE component_id = ?
            ''', (component_id,))
            
            component_info = cursor.fetchone()
            if not component_info:
                conn.close()
                return False
                
            category_type, component_level, component_key, parent_component = component_info
            print(f"삭제 대상: {category_type}-{component_level} - {component_key}")
            
            # 계층적 삭제 수행
            self._delete_component_cascade(cursor, category_type, component_level, component_key, parent_component)
            
            # 마지막으로 해당 구성 요소 자체 삭제
            cursor.execute('DELETE FROM multi_category_components WHERE component_id = ?', (component_id,))
            deleted_self = cursor.rowcount
            print(f"본인 삭제: {deleted_self}개")
            
            conn.commit()
            conn.close()
            print(f"계층적 삭제 완료: {category_type}-{component_level} '{component_key}'")
            return True
            
        except Exception as e:
            print(f"구성 요소 완전 삭제 오류: {e}")
            return False
    
    def _update_child_parent_components(self, cursor, category_type, component_level, old_key, new_key, parent_component):
        """하위 계층의 parent_component 필드 업데이트 (무한 루프 방지)"""
        try:
            # 순환 참조 방지: old_key와 new_key가 같거나 서로 반대 관계면 업데이트 하지 않음
            if old_key == new_key:
                return
                
            # 순환 참조 방지: A → B, B → A 패턴 감지
            cursor.execute('''
                SELECT COUNT(*) FROM multi_category_components
                WHERE category_type = ? AND component_key = ? AND parent_component = ?
            ''', (category_type, old_key, new_key))
            circular_ref = cursor.fetchone()[0] > 0
            
            if circular_ref:
                print(f"순환 참조 감지됨: {old_key} ↔ {new_key} - 업데이트 중단")
                return
            
            # 현재 구성 요소의 이전 경로와 새 경로 생성
            if parent_component:
                old_path = f"{parent_component}-{old_key}"
                new_path = f"{parent_component}-{new_key}"
            else:
                old_path = old_key
                new_path = new_key
            
            # 직접 하위 요소들 업데이트 (parent_component가 old_key인 경우)
            cursor.execute('''
                UPDATE multi_category_components
                SET parent_component = ?, updated_date = ?
                WHERE category_type = ? AND parent_component = ? AND component_key != ?
            ''', (new_key, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), category_type, old_key, new_key))
            direct_updated = cursor.rowcount
            
            # 간접 하위 요소들 업데이트 (parent_component가 old_path로 시작하는 경우)
            cursor.execute('''
                UPDATE multi_category_components
                SET parent_component = REPLACE(parent_component, ?, ?), updated_date = ?
                WHERE category_type = ? AND parent_component LIKE ? AND component_key != ?
            ''', (old_path, new_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), category_type, f"{old_path}%", new_key))
            indirect_updated = cursor.rowcount
            
            total_updated = direct_updated + indirect_updated
            if total_updated > 0:
                print(f"하위 계층 업데이트: 직접 {direct_updated}개, 간접 {indirect_updated}개, 총 {total_updated}개")
                
        except Exception as e:
            print(f"하위 계층 업데이트 오류: {e}")
    
    def _delete_component_cascade(self, cursor, category_type, component_level, component_key, parent_component):
        """계층적 삭제 실행 (개선된 버전)"""
        try:
            # 현재 구성 요소의 경로 생성
            if parent_component:
                current_path = f"{parent_component}-{component_key}"
            else:
                current_path = component_key
            
            # 레벨별 하위 구성 요소 삭제 (순서 중요: 하위부터)
            levels = ['level6', 'level5', 'level4', 'level3', 'level2', 'level1']
            current_level_index = levels.index(component_level) if component_level in levels else 0
            
            total_deleted = 0
            for level in levels[:current_level_index]:
                # 직접 하위 요소 삭제
                cursor.execute('''
                    DELETE FROM multi_category_components 
                    WHERE category_type = ? AND component_level = ? 
                      AND parent_component = ?
                ''', (category_type, level, component_key))
                direct_deleted = cursor.rowcount
                
                # 간접 하위 요소 삭제 (경로에 포함된 경우)
                cursor.execute('''
                    DELETE FROM multi_category_components 
                    WHERE category_type = ? AND component_level = ? 
                      AND parent_component LIKE ?
                ''', (category_type, level, current_path + '-%'))
                indirect_deleted = cursor.rowcount
                
                level_total = direct_deleted + indirect_deleted
                total_deleted += level_total
                
                if level_total > 0:
                    print(f"삭제된 {level}: {level_total}개 (직접: {direct_deleted}, 간접: {indirect_deleted})")
            
            # 관련 제품 코드 삭제
            config = self.get_category_config(category_type)
            if config and config.get('product_code_prefix'):
                cursor.execute('''
                    DELETE FROM master_products 
                    WHERE product_code LIKE ? || '-%'
                ''', (config['product_code_prefix'],))
                deleted_products = cursor.rowcount
                if deleted_products > 0:
                    print(f"삭제된 제품 코드: {deleted_products}개")
            
            print(f"총 하위 요소 삭제: {total_deleted}개")
            
        except Exception as e:
            print(f"계층적 삭제 오류: {e}")
    
    def get_all_categories_data(self):
        """모든 카테고리의 데이터 조회 (등록된 코드 설명용)"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT category_type 
                FROM multi_category_components 
                WHERE is_active = 1
                ORDER BY category_type
            ''')
            
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            result = []
            for cat in categories:
                # 각 카테고리의 데이터 수집
                level1_data = self.get_components_by_level(cat, 'level1')
                if level1_data:
                    for l1 in level1_data:
                        # 하위 레벨 데이터 수집 로직 (필요시 구현)
                        result.append({
                            'category': cat,
                            'product': l1['component_name'],
                            'level1': l1['component_key'],
                            # 추후 level2~6 데이터 추가 가능
                        })
            
            return result
            
        except Exception as e:
            print(f"모든 카테고리 데이터 조회 오류: {e}")
            return []