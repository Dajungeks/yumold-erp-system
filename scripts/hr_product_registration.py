"""
HR 카테고리 신규 제품 등록 시스템
2-6단계 직접 입력 방식 구현
"""

import streamlit as st
import sqlite3
from datetime import datetime

def show_hr_product_registration():
    """HR 카테고리 제품 등록 페이지"""
    
    st.header("🔥 HR 카테고리 신규 제품 등록")
    st.caption("히터 제품의 새로운 분류를 단계별로 입력하여 등록합니다")
    
    # 1단계: HR 카테고리 표시 (고정)
    st.markdown("### 1단계: 메인 카테고리")
    st.success("✅ HR (히터) 카테고리가 선택되었습니다")
    
    # 제품 등록 폼
    with st.form("hr_product_registration"):
        
        # 2단계: System Type 직접 입력
        st.markdown("### 2단계: System Type 입력")
        system_type = st.text_input(
            "System Type", 
            placeholder="예: Open, Valve, Custom 등",
            help="히터의 시스템 타입을 직접 입력하세요"
        )
        
        # 3단계: 제품 타입 직접 입력
        st.markdown("### 3단계: 제품 타입 입력")
        product_type = st.text_input(
            "제품 타입",
            placeholder="예: ST, CP, SE, PT, SV 등",
            help="제품의 세부 타입을 직접 입력하세요"
        )
        
        # 4단계: 게이트 타입 직접 입력  
        st.markdown("### 4단계: 게이트 타입 입력")
        gate_type = st.text_input(
            "게이트 타입",
            placeholder="예: MAE, MCC, VV, CC 등",
            help="게이트의 타입을 직접 입력하세요"
        )
        
        # 5단계: 사이즈 직접 입력
        st.markdown("### 5단계: 사이즈 입력")
        size = st.text_input(
            "사이즈",
            placeholder="예: 20, 25, 35 등",
            help="노즐 사이즈나 제품 사이즈를 입력하세요"
        )
        
        # 6단계: 제품 이름 직접 입력
        st.markdown("### 6단계: 제품 이름 입력")
        product_name = st.text_input(
            "제품 이름",
            placeholder="예: HR-Open-ST-MAE-20 또는 사용자 정의 이름",
            help="최종 제품명을 입력하세요"
        )
        
        # 추가 정보 입력
        st.markdown("### 추가 정보 (선택사항)")
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_area(
                "제품 설명",
                placeholder="제품의 상세 설명을 입력하세요",
                height=100
            )
            unit_price = st.number_input(
                "단가 (VND)",
                min_value=0.0,
                step=1000.0,
                help="제품의 단가를 입력하세요"
            )
        
        with col2:
            currency = st.selectbox(
                "통화",
                ["VND", "USD", "KRW"],
                index=0
            )
            status = st.selectbox(
                "상태",
                ["active", "inactive", "development"],
                index=0,
                format_func=lambda x: {"active": "활성", "inactive": "비활성", "development": "개발중"}.get(x, x)
            )
        
        # 자동 생성된 제품 코드 미리보기
        if system_type and product_type and gate_type and size:
            auto_code = f"HR-{system_type}-{product_type}-{gate_type}-{size}"
            st.markdown("### 📋 자동 생성 제품 코드 미리보기")
            st.info(f"제안 제품 코드: **{auto_code}**")
            
            if not product_name:
                st.warning("제품 이름이 비어있으면 자동 생성 코드가 사용됩니다")
        
        # 등록 버튼
        submitted = st.form_submit_button("🔄 HR 제품 등록", type="primary")
        
        if submitted:
            # 필수 필드 검증
            if not all([system_type, product_type, gate_type, size]):
                st.error("2-5단계 항목은 모두 필수 입력입니다.")
                return
            
            # 제품 이름이 없으면 자동 생성
            if not product_name:
                product_name = f"HR-{system_type}-{product_type}-{gate_type}-{size}"
            
            # 제품 코드 생성 (중복 확인용)
            product_code = f"HR-{system_type}-{product_type}-{gate_type}-{size}"
            
            # 데이터베이스에 저장
            success = save_hr_product(
                product_code=product_code,
                product_name=product_name,
                system_type=system_type,
                product_type=product_type,
                gate_type=gate_type,
                size=size,
                description=description,
                unit_price=unit_price if unit_price > 0 else None,
                currency=currency,
                status=status
            )
            
            if success:
                st.success(f"✅ HR 제품 '{product_name}'이 성공적으로 등록되었습니다!")
                
                
                # 등록된 제품 정보 표시
                st.markdown("### 📋 등록된 제품 정보")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**제품 코드**: {product_code}")
                    st.write(f"**제품명**: {product_name}")
                    st.write(f"**System Type**: {system_type}")
                    st.write(f"**제품 타입**: {product_type}")
                
                with col2:
                    st.write(f"**게이트 타입**: {gate_type}")
                    st.write(f"**사이즈**: {size}")
                    st.write(f"**단가**: {unit_price:,.0f} {currency}" if unit_price else "단가: 미설정")
                    status_map = {'active': '활성', 'inactive': '비활성', 'development': '개발중'}
                    st.write(f"**상태**: {status_map[status]}")
                
            else:
                st.error("❌ 제품 등록 중 오류가 발생했습니다. 다시 시도해주세요.")

def save_hr_product(product_code, product_name, system_type, product_type, gate_type, size, description, unit_price, currency, status):
    """HR 제품을 데이터베이스에 저장"""
    
    try:
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        # 중복 제품 코드 확인
        cursor.execute("SELECT COUNT(*) FROM products WHERE product_code = ?", (product_code,))
        if cursor.fetchone()[0] > 0:
            st.warning(f"⚠️ 제품 코드 '{product_code}'가 이미 존재합니다.")
            return False
        
        # 제품 정보 저장
        cursor.execute('''
            INSERT INTO products (
                product_code, product_name, category, subcategory, description,
                unit_price, currency, status, created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_code,
            product_name, 
            'HR',
            f"{system_type}|{product_type}|{gate_type}|{size}",  # 구분자로 세부 정보 저장
            description,
            unit_price,
            currency,
            status,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # HR 제품 상세 정보 저장 (별도 테이블이 있다면)
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hr_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT UNIQUE NOT NULL,
                    system_type TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    gate_type TEXT NOT NULL,
                    size TEXT NOT NULL,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_code) REFERENCES products(product_code)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO hr_products (product_code, system_type, product_type, gate_type, size)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_code, system_type, product_type, gate_type, size))
            
        except Exception as e:
            # HR 상세 테이블 생성/저장 실패 시에도 계속 진행
            print(f"HR 상세 정보 저장 실패 (무시): {e}")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"데이터베이스 저장 오류: {e}")
        return False

def show_hr_product_list():
    """등록된 HR 제품 목록을 표시하고 수정/삭제 기능을 제공합니다."""
    
    try:
        # 데이터베이스 연결
        from database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # HR 제품 목록 조회 (새로운 master_products 테이블에서)
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.product_code,
            p.category_name,
            p.subcategory_1,
            p.subcategory_2,
            p.subcategory_3,
            p.subcategory_4,
            p.unit_price,
            p.currency,
            p.status,
            p.created_at,
            p.updated_at
        FROM master_products p 
        WHERE p.category_name = 'HR'
        ORDER BY p.created_at DESC
        """
        
        products = db_manager.execute_query(query)
        
        if products and len(products) > 0:
            # 탭으로 목록 보기와 편집/삭제 구분
            list_tabs = st.tabs(["📋 제품 목록", "✏️ 제품 편집", "🗑️ 제품 삭제"])
            
            with list_tabs[0]:
                # DataFrame으로 변환하여 목록 표시
                import pandas as pd
                df = pd.DataFrame(products)
                
                # 컬럼명 한글화
                column_mapping = {
                    'product_name': '제품명',
                    'product_code': '제품코드',
                    'category_name': '카테고리',
                    'subcategory_1': 'System Type',
                    'subcategory_2': '제품 타입',
                    'subcategory_3': '게이트 타입',
                    'subcategory_4': '사이즈',
                    'unit_price': '단가',
                    'currency': '통화',
                    'status': '상태',
                    'created_at': '등록일'
                }
                
                # 표시할 컬럼만 선택하고 이름 변경
                display_columns = ['product_name', 'product_code', 'subcategory_1', 'subcategory_2', 'subcategory_3', 'subcategory_4', 'unit_price', 'currency', 'status', 'created_at']
                df_display = df[display_columns].rename(columns=column_mapping)
                
                # 상태 한글화
                def translate_status(status):
                    status_map = {'active': '활성', 'inactive': '비활성', 'development': '개발중'}
                    return status_map.get(status, status)
                
                df_display['상태'] = df_display['상태'].apply(translate_status)
                
                st.dataframe(df_display, use_container_width=True)
                st.caption(f"총 {len(products)}개의 HR 제품이 등록되어 있습니다.")
            
            with list_tabs[1]:
                # 제품 편집
                st.subheader("✏️ HR 제품 편집")
                
                # 편집할 제품 선택
                product_options = []
                for product in products:
                    option = f"{product['product_code']} - {product['product_name']}"
                    product_options.append(option)
                
                selected_product_display = st.selectbox(
                    "편집할 제품을 선택하세요:", 
                    product_options, 
                    key="edit_product_select"
                )
                
                if selected_product_display:
                    # 선택된 제품 정보 가져오기
                    selected_index = product_options.index(selected_product_display)
                    selected_product = products[selected_index]
                    
                    st.divider()
                    st.markdown("**현재 제품 정보**")
                    
                    # 편집 폼
                    with st.form("edit_hr_product_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_system_type = st.text_input(
                                "System Type", 
                                value=selected_product.get('subcategory_1', ''),
                                placeholder="예: Open, Semi-Close"
                            )
                            edit_product_type = st.text_input(
                                "제품 타입", 
                                value=selected_product.get('subcategory_2', ''),
                                placeholder="예: ST, LT, DT"
                            )
                            edit_gate_type = st.text_input(
                                "게이트 타입", 
                                value=selected_product.get('subcategory_3', ''),
                                placeholder="예: MAE, MAET"
                            )
                        
                        with col2:
                            edit_size = st.text_input(
                                "사이즈", 
                                value=selected_product.get('subcategory_4', ''),
                                placeholder="예: 20, 30, 50"
                            )
                            edit_product_name = st.text_input(
                                "제품명", 
                                value=selected_product.get('product_name', '')
                            )
                            edit_unit_price = st.number_input(
                                "단가", 
                                value=float(selected_product.get('unit_price', 0)) if selected_product.get('unit_price') else 0.0,
                                min_value=0.0
                            )
                        
                        edit_currency = st.selectbox(
                            "통화", 
                            ["KRW", "USD", "EUR", "JPY", "VND"],
                            index=["KRW", "USD", "EUR", "JPY", "VND"].index(selected_product.get('currency', 'KRW'))
                        )
                        
                        edit_status = st.selectbox(
                            "상태",
                            ["active", "inactive", "development"],
                            index=["active", "inactive", "development"].index(selected_product.get('status', 'active')),
                            format_func=lambda x: {"active": "활성", "inactive": "비활성", "development": "개발중"}.get(x, x)
                        )
                        
                        # 수정된 제품 코드 미리보기
                        if edit_system_type and edit_product_type and edit_gate_type and edit_size:
                            new_product_code = f"HR-{edit_system_type}-{edit_product_type}-{edit_gate_type}-{edit_size}"
                            st.info(f"🔄 새 제품 코드: {new_product_code}")
                        
                        # 수정 버튼
                        edit_submitted = st.form_submit_button("✏️ 제품 정보 수정", type="primary")
                        
                        if edit_submitted:
                            try:
                                # 새 제품 코드 생성
                                new_product_code = f"HR-{edit_system_type}-{edit_product_type}-{edit_gate_type}-{edit_size}"
                                
                                # 제품 정보 업데이트
                                update_query = """
                                UPDATE master_products 
                                SET product_name = ?, 
                                    product_code = ?,
                                    subcategory_1 = ?,
                                    subcategory_2 = ?,
                                    subcategory_3 = ?,
                                    subcategory_4 = ?,
                                    unit_price = ?,
                                    currency = ?,
                                    status = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE product_id = ?
                                """
                                
                                params = (
                                    edit_product_name,
                                    new_product_code,
                                    edit_system_type,
                                    edit_product_type,
                                    edit_gate_type,
                                    edit_size,
                                    edit_unit_price,
                                    edit_currency,
                                    edit_status,
                                    selected_product['product_id']
                                )
                                
                                db_manager.execute_query(update_query, params)
                                
                                st.success("✅ 제품 정보가 성공적으로 수정되었습니다!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ 제품 수정 중 오류가 발생했습니다: {str(e)}")
            
            with list_tabs[2]:
                # 제품 삭제
                st.subheader("🗑️ HR 제품 삭제")
                st.warning("⚠️ 삭제된 제품은 복구할 수 없습니다. 신중히 선택해주세요.")
                
                # 삭제할 제품 선택
                delete_product_options = []
                for product in products:
                    option = f"{product['product_code']} - {product['product_name']}"
                    delete_product_options.append(option)
                
                selected_delete_product = st.selectbox(
                    "삭제할 제품을 선택하세요:", 
                    delete_product_options, 
                    key="delete_product_select"
                )
                
                if selected_delete_product:
                    # 선택된 제품 정보 표시
                    delete_index = delete_product_options.index(selected_delete_product)
                    delete_product = products[delete_index]
                    
                    st.divider()
                    st.markdown("**삭제할 제품 정보**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**제품코드**: {delete_product['product_code']}")
                        st.write(f"**제품명**: {delete_product['product_name']}")
                        st.write(f"**System Type**: {delete_product['subcategory_1']}")
                    
                    with col2:
                        st.write(f"**제품 타입**: {delete_product['subcategory_2']}")
                        st.write(f"**게이트 타입**: {delete_product['subcategory_3']}")
                        st.write(f"**사이즈**: {delete_product['subcategory_4']}")
                    
                    # 삭제 확인
                    st.divider()
                    delete_confirm = st.checkbox(f"'{delete_product['product_name']}' 제품을 삭제하겠습니다.", key="delete_confirm")
                    
                    if delete_confirm:
                        if st.button("🗑️ 제품 삭제 실행", type="secondary"):
                            try:
                                delete_query = "DELETE FROM master_products WHERE product_id = ?"
                                db_manager.execute_query(delete_query, (delete_product['product_id'],))
                                
                                st.success("✅ 제품이 성공적으로 삭제되었습니다!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ 제품 삭제 중 오류가 발생했습니다: {str(e)}")
            
        else:
            st.info("등록된 HR 제품이 없습니다.")
            
    except Exception as e:
        st.error(f"HR 제품 목록 조회 중 오류가 발생했습니다: {str(e)}")
        print(f"Error in show_hr_product_list: {e}")  # 디버깅용

if __name__ == "__main__":
    # 테스트용 실행
    show_hr_product_registration()
    st.divider()
    show_hr_product_list()