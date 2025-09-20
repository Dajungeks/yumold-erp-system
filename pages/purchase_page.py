"""
사무용품 구매 기록 페이지 - 총무팀용
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import psycopg2
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 사무용품 구매 관리자 클래스 (파일 내부에 포함)
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
            st.error(f"구매 기록 생성 중 오류: {e}")
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

# 메인 페이지 함수들
def show_purchase_page(get_text):
    """사무용품 구매 기록 페이지를 표시"""
    st.title("사무용품 구매 기록")
    st.markdown("회사 내부용 물품 구매 이력을 관리합니다")
    st.markdown("---")
    
    # 매니저 초기화
    try:
        manager = OfficePurchaseManager()
    except Exception as e:
        st.error(f"구매 관리 시스템 초기화 오류: {e}")
        return
    
    # 메인 탭 구성
    main_tabs = st.tabs([
        "구매 기록 목록",
        "새 구매 기록 등록", 
        "구매 통계",
        "검색"
    ])
    
    with main_tabs[0]:
        show_purchase_list(manager)
    
    with main_tabs[1]:
        show_new_purchase_form(manager)
    
    with main_tabs[2]:
        show_purchase_statistics(manager)
    
    with main_tabs[3]:
        show_purchase_search(manager)

def show_purchase_list(manager):
    """구매 기록 목록 표시"""
    st.markdown("### 구매 기록 목록")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 기간 필터
        period_option = st.selectbox(
            "기간 선택",
            ["전체", "오늘", "일주일", "한달", "직접 선택"]
        )
    
    with col2:
        if period_option == "직접 선택":
            start_date = st.date_input("시작일", value=date.today() - timedelta(days=30))
        else:
            start_date = None
    
    with col3:
        if period_option == "직접 선택":
            end_date = st.date_input("종료일", value=date.today())
        else:
            end_date = None
    
    # 구매 기록 조회
    try:
        # 기간에 따른 데이터 조회
        if period_option == "전체":
            df = manager.get_all_purchases()
        elif period_option == "오늘":
            today = date.today()
            df = manager.get_purchases_by_period(today, today)
        elif period_option == "일주일":
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            df = manager.get_purchases_by_period(start_date, end_date)
        elif period_option == "한달":
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            df = manager.get_purchases_by_period(start_date, end_date)
        elif period_option == "직접 선택" and start_date and end_date:
            df = manager.get_purchases_by_period(start_date, end_date)
        else:
            df = manager.get_all_purchases()
        
        if df.empty:
            st.info("등록된 구매 기록이 없습니다.")
            return
        
        # 표시할 컬럼 선택
        display_columns = [
            'purchase_date', 'requester_name', 'department', 
            'supplier_name', 'total_amount', 'payment_method'
        ]
        
        if 'item_count' in df.columns:
            display_columns.append('item_count')
        
        available_columns = [col for col in display_columns if col in df.columns]
        display_df = df[available_columns].copy()
        
        # 컬럼명 한글화
        column_mapping = {
            'purchase_date': '구매일자',
            'requester_name': '요청자',
            'department': '부서',
            'supplier_name': '구매처',
            'total_amount': '총금액',
            'payment_method': '결제방법',
            'item_count': '물품수'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # 금액 포맷팅
        if '총금액' in display_df.columns:
            display_df['총금액'] = display_df['총금액'].apply(
                lambda x: f"{x:,.0f}원" if pd.notna(x) else "0원"
            )
        
        # 데이터프레임 표시
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 상세 보기 선택
        if len(df) > 0:
            st.markdown("---")
            purchase_options = [f"{row['purchase_date']} - {row['requester_name']} ({row['supplier_name']})" 
                              for _, row in df.iterrows()]
            
            selected_idx = st.selectbox(
                "상세 보기할 구매 기록 선택",
                range(len(purchase_options)),
                format_func=lambda x: purchase_options[x],
                key="purchase_detail_select"
            )
            
            if selected_idx is not None:
                selected_purchase_id = df.iloc[selected_idx]['purchase_id']
                show_purchase_detail(manager, selected_purchase_id)
    
    except Exception as e:
        st.error(f"구매 기록 목록 조회 오류: {e}")

def show_purchase_detail(manager, purchase_id):
    """구매 기록 상세 정보 표시"""
    try:
        purchase_data = manager.get_purchase_by_id(purchase_id)
        
        if not purchase_data:
            st.error("구매 기록을 찾을 수 없습니다.")
            return
        
        st.markdown("### 구매 기록 상세 정보")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**구매일자:** {purchase_data.get('purchase_date', '')}")
            st.write(f"**요청자:** {purchase_data.get('requester_name', '')}")
            st.write(f"**부서:** {purchase_data.get('department', '') or '미입력'}")
            st.write(f"**구매 목적:** {purchase_data.get('purchase_purpose', '') or '미입력'}")
        
        with col2:
            st.write(f"**구매처:** {purchase_data.get('supplier_name', '') or '미입력'}")
            st.write(f"**총금액:** {purchase_data.get('total_amount', 0):,.0f}원")
            st.write(f"**결제방법:** {purchase_data.get('payment_method', '') or '미입력'}")
            st.write(f"**영수증번호:** {purchase_data.get('receipt_number', '') or '미입력'}")
        
        # 비고
        if purchase_data.get('notes'):
            st.write(f"**비고:** {purchase_data.get('notes')}")
        
        # 물품 목록
        if purchase_data.get('items'):
            st.markdown("#### 구매 물품 목록")
            
            items_df = pd.DataFrame(purchase_data['items'])
            
            if not items_df.empty:
                # 필요한 컬럼만 표시
                display_cols = ['item_name', 'category', 'quantity', 'unit', 'unit_price', 'total_price']
                available_cols = [col for col in display_cols if col in items_df.columns]
                
                if available_cols:
                    display_items = items_df[available_cols].copy()
                    
                    # 컬럼명 한글화
                    display_items = display_items.rename(columns={
                        'item_name': '물품명',
                        'category': '분류',
                        'quantity': '수량',
                        'unit': '단위',
                        'unit_price': '단가',
                        'total_price': '총액'
                    })
                    
                    # 금액 포맷팅
                    if '단가' in display_items.columns:
                        display_items['단가'] = display_items['단가'].apply(lambda x: f"{x:,.0f}원")
                    if '총액' in display_items.columns:
                        display_items['총액'] = display_items['총액'].apply(lambda x: f"{x:,.0f}원")
                    
                    st.dataframe(display_items, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"구매 기록 상세 조회 오류: {e}")

def show_new_purchase_form(manager):
    """새 구매 기록 등록"""
    st.markdown("### 새 구매 기록 등록")
    
    with st.form("new_purchase_record"):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            requester_name = st.text_input("요청자명*", placeholder="홍길동")
            department = st.text_input("부서", placeholder="총무팀")
            purchase_date = st.date_input("구매일자*", value=date.today())
            purchase_purpose = st.text_input("구매 목적", placeholder="사무용품 보충")
            
        with col2:
            supplier_name = st.text_input("구매처", placeholder="다이소, 쿠팡, 이마트 등")
            payment_method = st.selectbox("결제방법", 
                ["회사카드", "현금", "계좌이체", "개인카드(후환급)", "기타"])
            receipt_number = st.text_input("영수증번호", placeholder="선택사항")
            notes = st.text_area("비고", placeholder="특이사항이나 메모")
        
        # 물품 정보 입력
        st.markdown("#### 구매 물품 정보")
        
        items = []
        
        # 고정된 5개 물품 입력 슬롯
        for i in range(5):
            st.markdown(f"**물품 {i+1} (선택사항)**")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                item_name = st.text_input(f"물품명", key=f"item_name_{i}")
            
            with col2:
                category = st.selectbox(f"분류", 
                    ["사무용품", "IT장비", "소모품", "간식", "청소용품", "기타"],
                    key=f"category_{i}")
            
            with col3:
                quantity = st.number_input(f"수량", min_value=0.0, key=f"quantity_{i}")
            
            with col4:
                unit_price = st.number_input(f"단가(원)", min_value=0.0, key=f"unit_price_{i}")
            
            with col5:
                unit = st.text_input(f"단위", value="개", key=f"unit_{i}")
            
            # 유효한 물품 정보가 있으면 추가
            if item_name and quantity > 0 and unit_price > 0:
                total_price = quantity * unit_price
                st.write(f"소계: {total_price:,.0f}원")
                
                items.append({
                    'item_name': item_name,
                    'category': category,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'unit': unit,
                    'total_price': total_price
                })
            
            if i < 4:  # 마지막이 아니면 구분선
                st.markdown("---")
        
        # 총액 표시
        if items:
            total_amount = sum(item['total_price'] for item in items)
            st.markdown(f"### 총 구매금액: **{total_amount:,.0f}원**")
        
        # 구매 기록 등록
        submitted = st.form_submit_button("구매 기록 등록", type="primary")
        
        if submitted:
            # 입력 검증
            if not requester_name:
                st.error("요청자명은 필수입니다.")
                return
            
            if not items:
                st.error("최소 1개 이상의 물품을 입력해야 합니다.")
                return
            
            # 구매 데이터 준비
            purchase_data = {
                'requester_name': requester_name,
                'department': department if department else None,
                'purchase_date': purchase_date,
                'purchase_purpose': purchase_purpose if purchase_purpose else None,
                'supplier_name': supplier_name if supplier_name else None,
                'payment_method': payment_method if payment_method != "기타" else None,
                'receipt_number': receipt_number if receipt_number else None,
                'notes': notes if notes else None,
                'items': items,
                'status': '완료'
            }
            
            # 구매 기록 등록 시도
            try:
                st.info("구매 기록을 등록하는 중...")
                
                result = manager.create_purchase_record(purchase_data)
                
                if result:
                    st.success("구매 기록이 성공적으로 등록되었습니다!")
                    st.balloons()
                    
                    # 등록된 구매 ID 표시
                    if 'purchase_id' in purchase_data:
                        st.info(f"구매 기록 ID: {purchase_data['purchase_id']}")
                    
                    st.rerun()
                else:
                    st.error("구매 기록 등록에 실패했습니다.")
                
            except Exception as e:
                st.error(f"구매 기록 등록 중 오류가 발생했습니다: {str(e)}")

def show_purchase_statistics(manager):
    """구매 통계 및 분석"""
    st.markdown("### 구매 통계 및 분석")
    
    try:
        stats = manager.get_purchase_statistics()
        
        if not stats:
            st.info("통계 데이터가 없습니다.")
            return
        
        # 전체 통계
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 구매 건수", stats.get('total_purchases', 0))
        
        with col2:
            total_amount = stats.get('total_amount', 0)
            st.metric("총 구매금액", f"{total_amount:,.0f}원")
        
        with col3:
            avg_amount = stats.get('average_amount', 0)
            st.metric("평균 구매금액", f"{avg_amount:,.0f}원")
        
        with col4:
            st.metric("구매 요청자 수", stats.get('unique_requesters', 0))
        
        # 카테고리별 분포
        if stats.get('category_stats'):
            st.markdown("#### 물품 카테고리별 구매 현황")
            
            category_df = pd.DataFrame(stats['category_stats'])
            
            if not category_df.empty:
                # 차트 표시
                st.bar_chart(category_df.set_index('category')['amount'])
                
                # 상세 테이블
                category_df['amount'] = category_df['amount'].apply(lambda x: f"{x:,.0f}원")
                category_df = category_df.rename(columns={
                    'category': '카테고리',
                    'count': '구매건수',
                    'amount': '총구매금액'
                })
                
                st.dataframe(category_df, use_container_width=True, hide_index=True)
        
        # 부서별 통계
        if stats.get('department_stats'):
            st.markdown("#### 부서별 구매 현황")
            
            dept_df = pd.DataFrame(stats['department_stats'])
            
            if not dept_df.empty:
                dept_df['amount'] = dept_df['amount'].apply(lambda x: f"{x:,.0f}원")
                dept_df = dept_df.rename(columns={
                    'department': '부서',
                    'count': '구매건수',
                    'amount': '총구매금액'
                })
                
                st.dataframe(dept_df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"통계 조회 오류: {e}")

def show_purchase_search(manager):
    """구매 기록 검색"""
    st.markdown("### 구매 기록 검색")
    
    search_term = st.text_input(
        "검색어 입력",
        placeholder="요청자명, 부서, 구매처, 물품명 등으로 검색"
    )
    
    if search_term:
        try:
            results = manager.search_purchases(search_term)
            
            if results.empty:
                st.info("검색 결과가 없습니다.")
            else:
                st.write(f"**검색 결과: {len(results)}건**")
                
                # 결과 표시
                display_columns = [
                    'purchase_date', 'requester_name', 'department',
                    'supplier_name', 'total_amount'
                ]
                
                available_columns = [col for col in display_columns if col in results.columns]
                
                if available_columns:
                    display_df = results[available_columns].copy()
                    
                    # 컬럼명 한글화
                    column_mapping = {
                        'purchase_date': '구매일자',
                        'requester_name': '요청자',
                        'department': '부서',
                        'supplier_name': '구매처',
                        'total_amount': '총금액'
                    }
                    
                    display_df = display_df.rename(columns=column_mapping)
                    
                    # 금액 포맷팅
                    if '총금액' in display_df.columns:
                        display_df['총금액'] = display_df['총금액'].apply(
                            lambda x: f"{x:,.0f}원" if pd.notna(x) else "0원"
                        )
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"검색 오류: {e}")
    else:
        st.info("검색어를 입력하세요.")
        
        # 최근 구매 기록 미리보기
        try:
            recent_df = manager.get_all_purchases()
            if not recent_df.empty:
                st.markdown("#### 최근 구매 기록 (최대 5건)")
                
                recent_5 = recent_df.head(5)
                display_cols = ['purchase_date', 'requester_name', 'supplier_name', 'total_amount']
                available_cols = [col for col in display_cols if col in recent_5.columns]
                
                if available_cols:
                    preview_df = recent_5[available_cols].copy()
                    preview_df = preview_df.rename(columns={
                        'purchase_date': '구매일자',
                        'requester_name': '요청자',
                        'supplier_name': '구매처',
                        'total_amount': '총금액'
                    })
                    
                    if '총금액' in preview_df.columns:
                        preview_df['총금액'] = preview_df['총금액'].apply(
                            lambda x: f"{x:,.0f}원" if pd.notna(x) else "0원"
                        )
                    
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)
        except:
            pass
