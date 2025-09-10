"""
YUMOLD 양식 기반 견적서 관리 페이지
기존 제품 코드 시스템 연동
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
# from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager  # 비활성화


def delete_quotation_with_password(quotation_id, quotation_number):
    """견적서 삭제 (비밀번호 제거)"""
    # 모달 다이얼로그로 표시
    delete_key = f"show_delete_modal_{quotation_id}"
    
    if delete_key not in st.session_state:
        st.session_state[delete_key] = True
    
    if st.session_state[delete_key]:
        with st.container():
            st.error(f"⚠️ 견적서 삭제: {quotation_number}")
            st.warning("이 작업은 되돌릴 수 없습니다!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 삭제 확인", key=f"confirm_delete_{quotation_id}", type="secondary"):
                    try:
                        quotation_manager = SQLiteQuotationManager()
                        
                        # 견적서 삭제 (매니저의 delete_quotation 메서드 사용)
                        success, message = quotation_manager.delete_quotation(quotation_id)
                        
                        if not success:
                            st.error(f"❌ 삭제 실패: {message}")
                            return
                        
                        st.success(f"✅ 견적서 {quotation_number}가 성공적으로 삭제되었습니다.")
                        
                        # 세션 상태 정리
                        if delete_key in st.session_state:
                            del st.session_state[delete_key]
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 삭제 중 오류 발생: {e}")
            
            with col2:
                if st.button("❌ 취소", key=f"cancel_delete_{quotation_id}"):
                    if delete_key in st.session_state:
                        del st.session_state[delete_key]
                    st.rerun()


def get_current_exchange_rate():
    """현재 환율 조회"""
    # 환율 정보 로드 (기본값 사용)
    current_rate = 24000  # 기본 USD/VND 환율
    return current_rate


def show_print_quotation_tab():
    """견적서 프린트 전용 탭"""
    st.subheader("🖨️ Print Quotation")
    
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    
    try:
        quotations = quotation_manager.get_all_quotations()
        
        if isinstance(quotations, pd.DataFrame) and not quotations.empty:
            # 리비전 포함해서 모든 견적서 표시 (최신순 정렬)
            quotations_sorted = quotations.sort_values(['created_at'], ascending=[False])
            
            st.markdown("#### 📋 Select Quotation to Print")
            
            # 견적서 선택
            quotation_options = []
            for _, quote in quotations_sorted.iterrows():
                status_icon = "✅" if quote['quotation_status'] == 'approved' else "📝"
                # revision_number 안전 처리
                if 'revision_number' in quote.index:
                    revision_num = quote.get('revision_number', '00') or '00'
                else:
                    revision_num = '00'
                revision_text = f" Rev{revision_num}" if revision_num and revision_num != '00' else ""
                quotation_options.append(f"{status_icon} {quote['quotation_number']}{revision_text} - {quote['customer_company']} ({quote['total_incl_vat']:,.0f} {quote['currency']})")
            
            selected_quotation = st.selectbox("Choose quotation to print:", quotation_options, key="print_select")
            
            if selected_quotation:
                # 선택된 견적서 정보 추출 (리비전 번호 고려)
                parts = selected_quotation.split(" ")
                quote_number_part = parts[1]  # 견적번호 (리비전 포함될 수 있음)
                
                if "Rev" in quote_number_part:
                    quote_number = quote_number_part.split("Rev")[0]
                    revision_num = quote_number_part.split("Rev")[1]
                else:
                    quote_number = quote_number_part
                    revision_num = "00"
                
                # 정확한 견적서 선택 (견적번호 + 리비전 번호)
                # revision_number 컬럼이 없을 경우를 대비한 안전한 필터링
                if 'revision_number' in quotations_sorted.columns:
                    filtered_quotes = quotations_sorted[
                        (quotations_sorted['quotation_number'] == quote_number) & 
                        (quotations_sorted['revision_number'].fillna('00') == revision_num)
                    ]
                else:
                    filtered_quotes = quotations_sorted[quotations_sorted['quotation_number'] == quote_number]
                
                if len(filtered_quotes) > 0:
                    selected_quote = filtered_quotes.iloc[0]
                else:
                    selected_quote = quotations_sorted[quotations_sorted['quotation_number'] == quote_number].iloc[0]
                
                # 선택된 견적서 데이터를 세션 상태에 로드
                load_quotation_to_session(selected_quote)
                
                # 데이터베이스에서 직접 완전한 데이터 가져오기
                quotation_id = selected_quote.get('quotation_id')
                if quotation_id:
                    # 데이터베이스에서 완전한 견적서 정보를 다시 조회
                    complete_quote = quotation_manager.get_quotation_by_id(quotation_id)
                    if complete_quote is not None and isinstance(complete_quote, pd.Series):
                        selected_quote = complete_quote
                    elif complete_quote is not None and isinstance(complete_quote, pd.DataFrame) and not complete_quote.empty:
                        selected_quote = complete_quote.iloc[0]
                
                # 기본 정보만 표시
                st.info(f"선택된 견적서: {selected_quote['quotation_number']} - {selected_quote['customer_company']}")
                
                # 프린트 옵션 설정
                st.markdown("#### ⚙️ Print Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    include_stamp = st.checkbox("🏷️ Include Company Stamp", value=False, key="include_stamp_option")
                    
                with col2:
                    if include_stamp:
                        st.info("💡 Company stamp will be displayed on the signature area")
                    else:
                        st.info("💡 Standard signature format without stamp")
                
                # 화면에 견적서 표시하고 프린트하기
                if st.button("🖨️ Show & Print Quotation", type="primary", use_container_width=True):
                    display_quotation_for_print(selected_quote, include_stamp=include_stamp)
        else:
            st.warning("📝 견적서가 없습니다!")
            st.info("""
            **견적서 생성 방법:**
            1. **'Create Quotation' 탭**으로 이동
            2. **제품 검색**: 'HR', 'CON', 'Test' 등으로 검색
            3. **제품 추가**: Select 버튼으로 제품 추가
            4. **고객 정보 입력**: 고객사명, 연락처 등 입력
            5. **저장**: Save Quotation 버튼 클릭
            """)
            

            
    except Exception as e:
        st.error(f"Error loading quotations: {e}")


def load_quotation_to_session(selected_quote):
    """선택된 견적서 데이터를 세션 상태에 로드 (위젯 키 충돌 방지)"""
    # 견적서 기본 정보를 세션에 저장 (실제 데이터베이스 필드명 매핑)
    quotation_data = {
        'print_customer_company': selected_quote.get('customer_company', ''),
        'print_customer_address': selected_quote.get('customer_address', ''),
        'print_customer_contact_person': selected_quote.get('customer_contact_person', ''),
        'print_customer_phone': selected_quote.get('customer_phone', ''),
        'print_customer_email': selected_quote.get('customer_email', ''),
        'print_project_name': selected_quote.get('project_name', ''),
        'print_part_name': selected_quote.get('part_name', ''),
        'print_part_weight': selected_quote.get('part_weight', ''),
        'print_mold_number': selected_quote.get('mold_number', ''),
        'print_hrs_info': selected_quote.get('hrs_info', ''),
        'print_resin_type': selected_quote.get('resin_type', ''),
        'print_resin_additive': selected_quote.get('resin_additive', ''),
        'print_sol_material': selected_quote.get('sol_material', ''),
        'print_remark': selected_quote.get('remark', ''),
        'print_payment_terms': selected_quote.get('payment_terms', ''),
        'print_account': selected_quote.get('account', '700-038-038199 (Shinhan Bank Vietnam)'),
        'print_sales_rep_name': selected_quote.get('sales_representative', ''),
        'print_sales_rep_phone': selected_quote.get('sales_rep_phone', ''),
        'print_sales_rep_email': selected_quote.get('sales_rep_email', ''),
        'print_quotation_number': selected_quote.get('quotation_number', ''),
        'print_project_name': selected_quote.get('project_name', ''),
        'print_part_name': selected_quote.get('part_name', ''),
        'print_part_weight': selected_quote.get('part_weight', ''),
        'print_mold_number': selected_quote.get('mold_number', ''),
        'print_hrs_info': selected_quote.get('hrs_info', ''),
        'print_resin_type': selected_quote.get('resin_type', ''),
        'print_revision_number': selected_quote.get('revision_number', '00'),
        'print_vat_percentage': selected_quote.get('vat_percentage', 10.0),
        'print_quotation_id': selected_quote.get('quotation_id', ''),
        'print_quote_date': selected_quote.get('quote_date', ''),
        'print_valid_date': selected_quote.get('valid_date', ''),
        'print_delivery_date': selected_quote.get('delivery_date', '')
    }
    
    # 세션에 저장
    for key, value in quotation_data.items():
        st.session_state[key] = value
    
    # 견적서 아이템도 로드
    try:
        quotation_manager = SQLiteQuotationManager()
        items = quotation_manager.get_quotation_items(selected_quote.get('quotation_id', ''))
        if isinstance(items, list):
            st.session_state['print_quotation_items'] = items
        elif isinstance(items, pd.DataFrame) and not items.empty:
            st.session_state['print_quotation_items'] = items.to_dict('records')
        else:
            st.session_state['print_quotation_items'] = []

    except Exception as e:
        st.session_state['print_quotation_items'] = []
        st.error(f"제품 정보 로드 오류: {e}")


def generate_and_download_quotation_html(quotation_id):
    """선택된 견적서의 HTML 파일 생성 및 다운로드"""
    try:
        from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
        quotation_manager = SQLiteQuotationManager()
        
        # 견적서 정보 조회
        import sqlite3
        conn = sqlite3.connect('erp_system.db')
        quote_df = pd.read_sql_query('''
            SELECT * FROM quotations WHERE quotation_id = ?
        ''', conn, params=[quotation_id])
        
        if len(quote_df) == 0:
            st.error("Quotation not found")
            return
            
        quote = quote_df.iloc[0]
        
        # 디버깅: 데이터 확인
        with st.expander("🔍 Debug: Retrieved quotation data"):
            debug_fields = ['quotation_number', 'customer_company', 'project_name', 'part_name', 'mold_number', 'hrs_info', 'resin_type', 'payment_terms', 'account']
            for field in debug_fields:
                st.write(f"{field}: {quote.get(field, 'N/A')}")
        
        # 견적서 아이템들 조회
        items_df = pd.read_sql_query('''
            SELECT * FROM quotation_items WHERE quotation_id = ? ORDER BY line_number
        ''', conn, params=[quotation_id])
        
        conn.close()
        
        # HTML 템플릿 로드
        with open('templates/quotation_print_template.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 템플릿 데이터 교체 - 정확한 필드명 사용
        template_content = template_content.replace('{{quotation_number}}', str(quote.get('quotation_number', '')))
        template_content = template_content.replace('{{quote_date}}', str(quote.get('quote_date', '')))
        template_content = template_content.replace('{{customer_company}}', str(quote.get('customer_company', '')))
        template_content = template_content.replace('{{customer_address}}', str(quote.get('customer_address', '')))
        template_content = template_content.replace('{{customer_contact_person}}', str(quote.get('customer_contact_person', '')))
        template_content = template_content.replace('{{customer_phone}}', str(quote.get('customer_phone', '')))
        template_content = template_content.replace('{{customer_email}}', str(quote.get('customer_email', '')))
        template_content = template_content.replace('{{currency}}', str(quote.get('currency', 'VND')))
        template_content = template_content.replace('{{vat_percentage}}', str(quote.get('vat_percentage', 10)))
        template_content = template_content.replace('{{subtotal_excl_vat}}', f"{quote.get('subtotal_excl_vat', 0):,.0f}")
        template_content = template_content.replace('{{vat_amount}}', f"{quote.get('vat_amount', 0):,.0f}")
        template_content = template_content.replace('{{total_incl_vat}}', f"{quote.get('total_incl_vat', 0):,.0f}")
        template_content = template_content.replace('{{valid_date}}', str(quote.get('valid_date', '')))
        # Sales Rep 정보 처리 (빈 값일 경우 기본값 설정)
        sales_rep_name = str(quote.get('sales_representative', '')) or 'Sales Representative'
        sales_rep_phone = str(quote.get('sales_rep_contact', '')) or ''  # DB에서 전화번호 가져옴
        sales_rep_email = str(quote.get('sales_rep_email', '')) or ''
        
        # 실제 표시 내용 정의 (HTML 템플릿과 매핑)
        display_sales_rep = sales_rep_name  # Sales Rep: 이름
        display_contact = sales_rep_email   # Contact: 이메일
        display_phone = sales_rep_phone     # Phone: 전화번호
        
        template_content = template_content.replace('{{sales_representative}}', display_sales_rep)
        template_content = template_content.replace('{{sales_rep_contact}}', display_contact)  # Contact에 이메일 표시
        template_content = template_content.replace('{{sales_rep_phone}}', display_phone)  # Phone에 전화번호 표시
        template_content = template_content.replace('{{sales_rep_email}}', sales_rep_email)
        template_content = template_content.replace('{{product_name_detail}}', str(quote.get('product_name_detail', '')))
        template_content = template_content.replace('{{delivery_date}}', str(quote.get('delivery_date', '')))
        
        # 추가 프로젝트 정보 필드들
        template_content = template_content.replace('{{project_name}}', str(quote.get('project_name', '')))
        template_content = template_content.replace('{{part_name}}', str(quote.get('part_name', '')))
        template_content = template_content.replace('{{part_weight}}', str(quote.get('part_weight', '')))
        template_content = template_content.replace('{{mold_number}}', str(quote.get('mold_number', '')))
        template_content = template_content.replace('{{hrs_info}}', str(quote.get('hrs_info', '')))
        template_content = template_content.replace('{{resin_type}}', str(quote.get('resin_type', '')))
        template_content = template_content.replace('{{resin_additive}}', str(quote.get('resin_additive', '')))
        template_content = template_content.replace('{{sol_material}}', str(quote.get('sol_material', '')))
        template_content = template_content.replace('{{remark}}', str(quote.get('remark', '')))
        template_content = template_content.replace('{{payment_terms}}', str(quote.get('payment_terms', '')))
        template_content = template_content.replace('{{revision_number}}', str(quote.get('revision_number', '00')))
        
        # 계좌 정보 처리 - 기본값 설정
        account_info = quote.get('account', '700-038-038199<br>Shinhan Bank Vietnam')
        template_content = template_content.replace('{{account}}', account_info)
        
        # 아이템 HTML 생성
        items_html = ""
        if len(items_df) > 0:
            for idx, (_, item) in enumerate(items_df.iterrows()):
                vn_text = str(item.get('item_name_vn', ''))
                vn_class = "vietnamese-desc" if vn_text else ""
                row_number = item.get('line_number', idx + 1)
                
                items_html += f"""
                <tr>
                    <td rowspan="3">{row_number}</td>
                    <td>{item.get('item_code', '')}</td>
                    <td>{item.get('item_name_en', '')}</td>
                    <td>{item.get('quantity', 1)}</td>
                    <td>{item.get('standard_price', 0):,.0f}</td>
                    <td>{item.get('discount_rate', 0):.1f}%</td>
                    <td>{item.get('unit_price', 0):,.0f}</td>
                    <td>{item.get('amount', 0):,.0f}</td>
                </tr>
                <tr>
                    <td colspan="7" style="text-align: left; padding-left: 10px; font-size: 9px; color: #666;">
                        VN: {vn_text}
                    </td>
                </tr>
                <tr>
                    <td colspan="7" style="text-align: left; padding-left: 10px; font-size: 9px; color: #666;">
                        Remark: {item.get('remark', '')}
                    </td>
                </tr>
            """
        
        template_content = template_content.replace('{quotation_items}', items_html)
        
        # HTML 파일로 저장 - 견적서 번호와 고객사명 포함
        quotation_num = quote.get('quotation_number', 'quotation')
        customer_name = quote.get('customer_company', '').replace(',', '').replace(' ', '_')
        file_name = f"{quotation_num} - {customer_name}.html"
        file_path = f"generated_files/{file_name}"
        
        # 생성된 파일 디렉토리 확인
        import os
        os.makedirs('generated_files', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # HTML 파일 다운로드 링크 제공
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        st.success(f"✅ HTML 견적서가 생성되었습니다!")
        st.download_button(
            label="📥 Download HTML Quotation",
            data=file_data,
            file_name=file_name,
            mime="text/html",
            use_container_width=True
        )
        
        # 브라우저에서 미리보기 표시  
        st.markdown("### 📋 Preview")
        
        # HTML 미리보기를 표시
        st.markdown(template_content, unsafe_allow_html=True)
        
        st.info("💡 다운로드한 HTML 파일을 브라우저에서 열고 Ctrl+P로 프린트하세요!")
        
    except Exception as e:
        st.error(f"Error generating HTML file: {e}")
        import traceback
        st.code(traceback.format_exc())


def show_product_search_modal():
    """제품 검색 모달"""
    product_manager = SQLiteMasterProductManager()
    
    # 제품 검색 입력
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Product Code Search", placeholder="Enter product code (e.g., HRSS, HRCT...)", key="product_search")
    with col2:
        if st.button("🔍 Search", key="search_button"):
            if search_term.strip():
                with st.spinner("Searching products..."):
                    results = search_products(search_term.strip())
                    st.session_state.search_results = results
                    if results:
                        st.success(f"Found {len(results)} products")
                    else:
                        st.warning("No products found")
            else:
                st.warning("Please enter search term")
    
    # 검색 결과 표시 (세션 기반 선택)
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.markdown("**Search Results:**")
        
        # 선택된 제품 처리 (세션 상태 기반)
        if 'selected_product_idx' in st.session_state:
            selected_idx = st.session_state.selected_product_idx
            if 0 <= selected_idx < len(st.session_state.search_results):
                selected_product = st.session_state.search_results[selected_idx]
                add_product_to_quotation(selected_product)
                # 선택 완료 후 정리
                del st.session_state.selected_product_idx
                st.session_state.search_results = []
                st.rerun()
        
        for idx, product in enumerate(st.session_state.search_results):
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 1.5, 1])
            
            with col1:
                st.text(product.get('product_code', 'N/A'))
            with col2:
                product_name = product.get('product_name_korean', product.get('product_name', 'N/A'))
                st.text(str(product_name))
            with col3:
                category = product.get('category_name', product.get('main_category', 'N/A'))
                st.text(f"Category: {category}")
            with col4:
                # 판매 가격 표시
                sales_price = product.get('sales_price_vnd', 0)
                st.text(f"Price: {sales_price:,.0f} VND")
            with col5:
                if st.button("Select", key=f"select_{idx}"):
                    # 선택된 인덱스를 세션에 저장하고 rerun
                    st.session_state.selected_product_idx = idx
                    st.rerun()


def search_products(search_term):
    """제품 검색"""
    try:
        product_manager = SQLiteMasterProductManager()
        products = product_manager.get_all_products()
        
        # DataFrame 변환 (안전 처리)
        if isinstance(products, list):
            products_df = pd.DataFrame(products) if products else pd.DataFrame()
        elif isinstance(products, pd.DataFrame):
            products_df = products
        else:
            return []
        
        if isinstance(products_df, pd.DataFrame) and not products_df.empty:
            # 제품 코드 또는 제품명으로 검색 (안전한 검색)
            try:
                mask = pd.Series(False, index=products_df.index)
                
                # 제품 코드 검색
                if 'product_code' in products_df.columns:
                    mask |= products_df['product_code'].astype(str).str.contains(search_term.upper(), na=False, case=False)
                
                # 제품명 검색
                if 'product_name' in products_df.columns:
                    mask |= products_df['product_name'].astype(str).str.contains(search_term, na=False, case=False)
                
                # 한국어 제품명 검색
                if 'product_name_korean' in products_df.columns:
                    mask |= products_df['product_name_korean'].astype(str).str.contains(search_term, na=False, case=False)
                
                filtered = products_df[mask]
                filtered_list = filtered.head(10)
                return filtered_list.to_dict('records')
            except Exception as e:
                st.error(f"Search filter error: {e}")
                return []
    except Exception as e:
        st.error(f"Search error: {e}")
        import traceback
        st.error(traceback.format_exc())
    
    return []


def add_product_to_quotation(product):
    """견적서에 제품 추가 (안전한 dict 처리)"""
    try:
        # session state 초기화 및 검증
        if 'quotation_items' not in st.session_state:
            st.session_state.quotation_items = []
        
        # 기존 아이템들 검증 및 정리
        if st.session_state.quotation_items:
            valid_items = []
            for item in st.session_state.quotation_items:
                if isinstance(item, dict):
                    valid_items.append(item)
                else:
                    print(f"잘못된 아이템 제거: {type(item)} - {item}")
            st.session_state.quotation_items = valid_items
        
        # product가 dict인지 확인
        if not isinstance(product, dict):
            st.error(f"제품 데이터 형식 오류: {type(product)}")
            return False
        
        # 안전한 제품 정보 추출 (기본값 보장)
        product_code = str(product.get('product_code', 'N/A'))
        product_name_en = str(product.get('product_name_en', product.get('product_name', 'Product')))
        product_name_vn = str(product.get('product_name_vi', product.get('product_name_vn', '')))
        sales_price = 0.0
        
        # 가격 안전 처리
        price_value = product.get('sales_price_vnd', 0)
        if price_value and str(price_value).replace('.', '').isdigit():
            sales_price = float(price_value)
        
        # 견적서 항목 생성 (완전한 dict 구조)
        new_item = {
            'line_number': len(st.session_state.quotation_items) + 1,
            'source_product_code': product_code,
            'item_code': product_code,
            'product_code': product_code,
            'item_name_en': product_name_en,
            'product_name': product_name_en,
            'item_name_vn': product_name_vn,
            'product_name_vn': product_name_vn,
            'quantity': 1,
            'standard_price': sales_price,
            'selling_price': sales_price,
            'discount_rate': 0.0,
            'unit_price': sales_price,
            'amount': sales_price,
            'remark': ''
        }
        
        # 안전하게 추가
        st.session_state.quotation_items.append(new_item)
        st.success(f"Added: {product_code} - {product_name_en}")
        return True
        
    except Exception as e:
        st.error(f"제품 추가 중 오류: {e}")
        return False


def calculate_totals(items, vat_percentage):
    """총액 계산 (안전한 타입 처리)"""
    subtotal = 0.0
    
    for item in items:
        if isinstance(item, dict):
            # dict인 경우 정상 처리
            amount = item.get('amount', 0)
            try:
                subtotal += float(amount) if amount else 0.0
            except (ValueError, TypeError):
                continue
        else:
            # string이나 다른 타입인 경우 스킵
            st.warning(f"잘못된 아이템 형식 발견: {type(item)} - {item}")
            continue
    
    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount
    
    return subtotal, vat_amount, total





def show_quotation_form():
    """YUMOLD 양식 기반 견적서 작성 폼"""
    st.subheader("📝 Create New Quotation")
    
    # 견적서 기본 정보
    st.markdown("#### 📋 Quotation Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 고객 정보 섹션 (헤더 제거)
        
        # 고객 DB 연결
        from managers.sqlite.sqlite_customer_manager import SQLiteCustomerManager
        customer_manager = SQLiteCustomerManager()
        
        try:
            customers_data = customer_manager.get_all_customers()
            if isinstance(customers_data, list):
                customers_df = pd.DataFrame(customers_data) if customers_data else pd.DataFrame()
            else:
                customers_df = customers_data if isinstance(customers_data, pd.DataFrame) else pd.DataFrame()
        except:
            customers_df = pd.DataFrame()
        
        # 통합 고객 선택/검색 기능 (DataFrame 확인 개선)
        customer_options = ["Select Customer..."]
        if isinstance(customers_df, pd.DataFrame) and len(customers_df) > 0:
            for _, customer in customers_df.iterrows():
                company_name = customer.get('company_name', 'N/A')
                customer_id = customer.get('customer_id', 'N/A')
                customer_options.append(f"{company_name} ({customer_id})")
        
        # 고객 선택 (검색 가능한 selectbox)
        selected_customer = st.selectbox(
            "Search & Select Customer", 
            customer_options, 
            key="selected_customer",
            help="Type to search customer name or select from dropdown"
        )
        
        # 선택된 고객 정보 로드
        if selected_customer != "Select Customer..." and '(' in selected_customer:
            customer_id = selected_customer.split('(')[-1].split(')')[0]
            customer_data = customers_df[customers_df['customer_id'] == customer_id]
            if len(customer_data) > 0:
                customer_info = customer_data.iloc[0].to_dict()
                st.markdown(f"**{customer_info.get('company_name', '')}**")
                customer_company = st.text_input("Company", value=customer_info.get('company_name', ''), key="customer_company", label_visibility="collapsed")
                customer_address = st.text_area("Address", value=customer_info.get('address', ''), height=100, key="customer_address")
                contact_person = st.text_input("Contact Person", value=customer_info.get('contact_person', ''), key="contact_person")
                customer_phone = st.text_input("Phone No.", value=customer_info.get('phone', ''), key="customer_phone")
                customer_email = st.text_input("E-mail", value=customer_info.get('email', ''), key="customer_email")
            else:
                customer_company = st.text_input("Company", key="customer_company")
                customer_address = st.text_area("Address", key="customer_address", height=100)
                contact_person = st.text_input("Contact Person", key="contact_person")
                customer_phone = st.text_input("Phone No.", key="customer_phone")
                customer_email = st.text_input("E-mail", key="customer_email")
        else:
            customer_company = st.text_input("Company", key="customer_company")
            customer_address = st.text_area("Address", key="customer_address", height=100)
            contact_person = st.text_input("Contact Person", key="contact_person")
            customer_phone = st.text_input("Phone No.", key="customer_phone")
            customer_email = st.text_input("E-mail", key="customer_email")
        
    with col2:
        st.markdown("**QUOTATION INFO**")
        quote_date = st.date_input("Date", value=datetime.now().date())
        # 견적서 번호 생성 (YMV-Q250903-001 형식) - 자동 생성, 화면에 표시하지 않음
        # 견적번호는 저장 시점에 중복 검사와 함께 생성되므로 UI에서 숨김
        if 'quotation_number' not in st.session_state or st.session_state.get('quotation_number_date') != datetime.now().strftime('%y%m%d'):
            # SQLiteQuotationManager를 사용하여 견적서 번호 생성
            from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
            quotation_manager = SQLiteQuotationManager()
            
            # 중복 방지를 위한 견적서 번호 생성
            generated_number = quotation_manager.generate_quotation_number()
            
            st.session_state.quotation_number = generated_number
            st.session_state.quotation_number_date = datetime.now().strftime('%y%m%d')
        quotation_number = st.session_state.quotation_number
        revision_number = st.text_input("Rev. No.", value="00", key="revision_number", disabled=True)
        currency = st.selectbox("Currency", ["VND", "USD", "KRW"], index=0)
        vat_percentage = st.number_input("VAT %", min_value=0.0, max_value=50.0, value=10.0, step=0.1)

    st.markdown("---")
    
    # 제품 추가 섹션
    st.markdown("#### 🛍️ Add Products")
    
    # 제품 검색 및 추가
    with st.expander("🔍 Search and Add Products", expanded=True):
        show_product_search_modal()
    
    # 현재 견적서 아이템 표시 (데이터 검증 포함)
    if 'quotation_items' not in st.session_state:
        st.session_state.quotation_items = []
    
    # 기존 아이템들 중 dict가 아닌 것들 제거
    valid_items = []
    for item in st.session_state.quotation_items:
        if isinstance(item, dict):
            valid_items.append(item)
        else:
            st.warning(f"잘못된 아이템 형식 제거됨: {type(item)} - {item}")
    
    if len(valid_items) != len(st.session_state.quotation_items):
        st.session_state.quotation_items = valid_items
        st.info("데이터 정리 완료: 잘못된 형식의 아이템들이 제거되었습니다.")
    
    if st.session_state.quotation_items:
        st.markdown("#### 📦 Current Items")
        
        # 아이템 테이블 표시 (완전 안전 처리)
        safe_items = []
        for idx, item in enumerate(st.session_state.quotation_items):
            if isinstance(item, dict):
                safe_items.append(item)
            else:
                st.error(f"⚠️ 잘못된 아이템 {idx+1} 제거됨: {type(item)}")
        
        # safe_items로 완전히 대체하여 작업 (중복 제거)
        st.session_state.quotation_items = safe_items
        
        for idx, item in enumerate(st.session_state.quotation_items):
            # 안전한 dict 확인
            if not isinstance(item, dict):
                st.error(f"잘못된 아이템 {idx+1}: {type(item)}")
                continue
                
            with st.container():
                line_num = item.get('line_number', idx+1)
                item_code = item.get('item_code', 'N/A')
                st.markdown(f"**#{line_num} - {item_code}**")
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    # 안전한 방식으로 업데이트
                    new_name_en = st.text_input(
                        "Item Name (EN)", 
                        value=item.get('item_name_en', ''),
                        key=f"item_name_en_{idx}"
                    )
                    new_name_vn = st.text_input(
                        "Item Name (VN)", 
                        value=item.get('item_name_vn', ''),
                        key=f"item_name_vn_{idx}"
                    )
                    
                    # 안전한 업데이트 (dict 타입 확인)
                    if isinstance(item, dict):
                        item['item_name_en'] = new_name_en
                        item['item_name_vn'] = new_name_vn
                
                with col2:
                    new_quantity = st.number_input(
                        "Qty", 
                        min_value=1, 
                        value=item.get('quantity', 1),
                        key=f"qty_{idx}"
                    )
                    if isinstance(item, dict):
                        item['quantity'] = new_quantity
                    
                    # 표준 가격 표시 (수정 불가)
                    st.text_input("Std. Price", 
                                value=f"{item.get('standard_price', 0.0):,.0f}", 
                                disabled=True, 
                                key=f"std_price_display_{idx}")
                    
                    # 판매 가격 입력 (사용자가 수정 가능)
                    new_selling_price = st.number_input(
                        "Selling Price", 
                        min_value=0.0, 
                        value=item.get('selling_price', item.get('standard_price', 0.0)),
                        format="%.0f",
                        key=f"selling_price_{idx}"
                    )
                    if isinstance(item, dict):
                        item['selling_price'] = new_selling_price
                
                with col3:
                    new_discount_rate = st.number_input(
                        "DC. Rate (%)", 
                        min_value=0.0, 
                        max_value=100.0,
                        value=item.get('discount_rate', 0.0),
                        key=f"discount_{idx}"
                    )
                    if isinstance(item, dict):
                        item['discount_rate'] = new_discount_rate
                        
                        # 단가 자동 계산 (판매가격 기준)
                        selling_price = item.get('selling_price', 0.0)
                        discount_rate = item.get('discount_rate', 0.0)
                        unit_price = selling_price * (1 - discount_rate / 100)
                        item['unit_price'] = unit_price
                    
                    unit_price = item.get('unit_price', 0.0) if isinstance(item, dict) else 0.0
                    st.text_input("Unit Price", value=f"{unit_price:,.0f}", disabled=True, key=f"unit_price_display_{idx}")
                
                with col4:
                    # 라인 총액 자동 계산
                    if isinstance(item, dict):
                        quantity = item.get('quantity', 1)
                        unit_price = item.get('unit_price', 0.0)
                        line_total = unit_price * quantity
                        item['amount'] = line_total
                    else:
                        line_total = 0
                    
                    st.text_input("Amount", value=f"{line_total:,.0f}", disabled=True, key=f"amount_display_{idx}")
                    
                    if st.button("🗑️", key=f"delete_{idx}"):
                        # 안전한 삭제 (dict 타입만 삭제)
                        if 0 <= idx < len(st.session_state.quotation_items):
                            st.session_state.quotation_items.pop(idx)
                            st.rerun()
                
                # 비고 입력 (하나로 통합)
                new_remark = st.text_area(
                    "Remark", 
                    value=item.get('remark', ''),
                    height=60,
                    key=f"remark_{idx}"
                )
                if isinstance(item, dict):
                    item['remark'] = new_remark
                
                st.markdown("---")
        
        # 총액 계산 및 표시
        subtotal, vat_amount, total = calculate_totals(st.session_state.quotation_items, vat_percentage)
        
        st.markdown("#### 💰 Totals")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"TOTAL {currency} Excl. VAT", f"{subtotal:,.0f}")
        with col2:
            st.metric(f"TOTAL {currency} {vat_percentage}% VAT", f"{vat_amount:,.0f}")
        with col3:
            st.metric(f"TOTAL {currency} Incl. VAT", f"{total:,.0f}")
    
    st.markdown("---")
    
    # 프로젝트 정보 섹션
    st.markdown("#### 📋 Project Information")
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name", value=st.session_state.get('project_name', ''), key="project_name")
        mold_number = st.text_input("Mold No.", value=st.session_state.get('mold_number', ''), key="mold_number")
        hrs_info = st.text_input("HRS Info", value=st.session_state.get('hrs_info', ''), key="hrs_info")
        resin_type = st.text_input("Resin Type", value=st.session_state.get('resin_type', ''), key="resin_type")
        
    with col2:
        part_name = st.text_input("Part Name", value=st.session_state.get('part_name', ''), key="part_name")
        part_weight = st.text_input("Part Weight (g)", value=st.session_state.get('part_weight', ''), key="part_weight")
        resin_additive = st.text_input("Resin/Additive", value=st.session_state.get('resin_additive', ''), key="resin_additive")
        sol_material = st.text_input("Sol/Material", value=st.session_state.get('sol_material', ''), key="sol_material")
    
    # 추가 정보
    col1, col2 = st.columns(2)
    with col1:
        remark = st.text_area("Remark", value=st.session_state.get('remark', ''), key="remark")
        payment_terms = st.text_input("Payment Terms", value=st.session_state.get('payment_terms', ''), key="payment_terms")
        account = st.text_input("Account", value="700-038-038199 (Shinhan Bank Vietnam)", key="account")
        
    with col2:
        valid_date = st.date_input("Valid Date", value=(datetime.now() + timedelta(days=30)).date(), key="valid_date")
        delivery_date = st.date_input("Delivery Date", key="delivery_date")
    
    # 하단 고정 정보 섹션
    st.markdown("---")
    st.markdown("#### 📋 Company Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **YUMOLD VIETNAM CO., LTD**
        - **Tax Code (MST):** 0111146237
        - **Hanoi Accounting Office:**  
          Room 1201-2, 12th Floor, Keangnam Hanoi Landmark 72,  
          E6 Area, Yen Hoa Ward, Hanoi City
        """)
    
    with col2:
        st.markdown("**Sales Representative Information**")
        
        # 직원 DB에서 직원 목록 가져오기
        from managers.sqlite.sqlite_employee_manager import SQLiteEmployeeManager
        employee_manager = SQLiteEmployeeManager()
        
        try:
            employees_data = employee_manager.get_all_employees()
            if isinstance(employees_data, list):
                employees_df = pd.DataFrame(employees_data) if employees_data else pd.DataFrame()
            else:
                employees_df = employees_data if isinstance(employees_data, pd.DataFrame) else pd.DataFrame()
        except:
            employees_df = pd.DataFrame()
        
        # 직원 선택 옵션 생성 (영어 이름 우선 표시)
        employee_options = ["Select Employee..."]
        if isinstance(employees_df, pd.DataFrame) and len(employees_df) > 0:
            for _, employee in employees_df.iterrows():
                emp_english_name = employee.get('english_name', '')
                emp_korean_name = employee.get('name', 'N/A')
                emp_id = employee.get('employee_id', 'N/A')
                # 영어 이름이 있으면 영어 이름 사용, 없으면 한국 이름 사용
                display_name = emp_english_name if emp_english_name else emp_korean_name
                employee_options.append(f"{display_name} ({emp_id})")
        
        # 현재 로그인한 사용자 정보
        current_user = st.session_state.get('user', {})
        default_name = current_user.get('name', 'Sales Representative')
        default_phone = current_user.get('phone', '')
        default_email = current_user.get('email', '')
        
        # 직원 선택 selectbox
        selected_employee = st.selectbox(
            "Select Sales Representative", 
            employee_options, 
            key="selected_sales_rep",
            help="Select from employee database"
        )
        
        # 선택된 직원 정보 로드 (영어 이름 우선 사용)
        if selected_employee != "Select Employee..." and '(' in selected_employee:
            emp_id = selected_employee.split('(')[-1].split(')')[0]
            employee_data = employees_df[employees_df['employee_id'] == emp_id]
            if len(employee_data) > 0:
                employee_info = employee_data.iloc[0].to_dict()
                # 영어 이름을 우선적으로 사용
                english_name = employee_info.get('english_name', '').strip()
                korean_name = employee_info.get('name', default_name).strip()
                
                # 영어 이름이 있으면 영어 이름만 사용
                if english_name:
                    default_name = english_name
                else:
                    default_name = korean_name
                    
                default_phone = employee_info.get('phone', default_phone)
                default_email = employee_info.get('email', default_email)
        
        # 마스터 계정 기본 정보 (영어 이름)
        if current_user.get('user_type') == 'master' and current_user.get('user_id') == 'master':
            if selected_employee == "Select Employee...":
                default_name = "Mr. Phuong"
                default_phone = "091-4888000" 
                default_email = "phuong@yumold.vn"
        
        sales_rep_name = st.text_input("Sales Rep Name", value=default_name, key="sales_rep_name")
        sales_rep_phone = st.text_input("Sales Rep Phone", value=default_phone, key="sales_rep_phone")
        sales_rep_email = st.text_input("Sales Rep Email", value=default_email, key="sales_rep_email")
    
    st.markdown("---")
    
    # 저장 버튼
    if st.button("💾 Save Quotation", type="primary", use_container_width=True):
        save_quotation_action()


def save_quotation_action():
    """견적서 저장 액션"""
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    
    # 필요한 변수들을 세션에서 가져오기
    customer_company = st.session_state.get('customer_company', '')
    customer_address = st.session_state.get('customer_address', '')
    contact_person = st.session_state.get('contact_person', '')
    customer_phone = st.session_state.get('customer_phone', '')
    customer_email = st.session_state.get('customer_email', '')
    quotation_number = st.session_state.get('quotation_number', '')
    revision_number = st.session_state.get('revision_number', '00')
    currency = 'VND'  # 기본 통화
    vat_percentage = st.session_state.get('vat_percentage', 10.0)
    project_name = st.session_state.get('project_name', '')
    part_name = st.session_state.get('part_name', '')
    part_weight = st.session_state.get('part_weight', '')
    mold_number = st.session_state.get('mold_number', '')
    hrs_info = st.session_state.get('hrs_info', '')
    resin_type = st.session_state.get('resin_type', '')
    resin_additive = st.session_state.get('resin_additive', '')
    sol_material = st.session_state.get('sol_material', '')
    remark = st.session_state.get('remark', '')
    payment_terms = st.session_state.get('payment_terms', '')
    account = st.session_state.get('account', '700-038-038199 (Shinhan Bank Vietnam)')
    sales_rep_name = st.session_state.get('sales_rep_name', '')
    sales_rep_phone = st.session_state.get('sales_rep_phone', '')
    sales_rep_email = st.session_state.get('sales_rep_email', '')
    
    # 총액 계산
    if st.session_state.quotation_items:
        subtotal, vat_amount, total = calculate_totals(st.session_state.quotation_items, vat_percentage)
    else:
        subtotal = vat_amount = total = 0.0
    
    if not customer_company.strip():
        st.error("Please enter customer company name.")
        return
    
    if not st.session_state.quotation_items:
        st.error("Please add at least one product.")
        return
    
    try:
        # 견적서 번호 중복 체크 (데이터베이스에서 직접 확인)
        import sqlite3
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM quotations WHERE quotation_number = ?', (quotation_number,))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            st.error(f"⚠️ 견적서 번호가 이미 존재합니다: {quotation_number}")
            st.info("새로고침하거나 다른 날짜에 다시 시도해주세요.")
            return
        
        # 견적서 저장 로직 구현
        quotation_id = f"QUOT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        quotation_data = {
            'quotation_id': quotation_id,
            'quotation_number': quotation_number,
            'quote_date': datetime.now().date().isoformat(),
            'revision_number': revision_number,
            'currency': currency,
            'customer_company': customer_company,
            'customer_address': customer_address,
            'customer_contact_person': contact_person,
            'customer_phone': customer_phone,
            'customer_email': customer_email,
            'vat_percentage': vat_percentage,
            'subtotal_excl_vat': subtotal,
            'vat_amount': vat_amount,
            'total_incl_vat': total,
            'project_name': project_name,
            'part_name': part_name,
            'part_weight': part_weight,
            'mold_number': mold_number,
            'hrs_info': hrs_info,
            'resin_type': resin_type,
            'resin_additive': resin_additive,
            'sol_material': sol_material,
            'remark': remark,
            'valid_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'payment_terms': payment_terms,
            'delivery_date': datetime.now().date().isoformat(),
            'sales_representative': sales_rep_name,  # sales_representative 필드에 저장
            'sales_rep_contact': sales_rep_phone,   # sales_rep_contact 필드에 전화번호 저장
            'sales_rep_email': sales_rep_email,     # sales_rep_email 필드에 이메일 저장
            'quotation_status': 'draft',
            'account': account,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 견적서 및 아이템 저장
        from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
        quotation_manager = SQLiteQuotationManager()
        success = quotation_manager.save_quotation(quotation_data)
        
        if success:
            # 견적서 아이템들 저장 (완전 안전한 방식)
            saved_items = 0
            for idx, item in enumerate(st.session_state.quotation_items):
                if not isinstance(item, dict):
                    st.error(f"아이템 {idx+1} 저장 실패: 잘못된 형식 {type(item)}")
                    continue
                    
                try:
                    item_data = {
                        'item_id': f"ITEM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx+1}",
                        'quotation_id': quotation_id,
                        'line_number': item.get('line_number', idx+1),
                        'source_product_code': str(item.get('source_product_code', item.get('item_code', ''))),
                        'item_code': str(item.get('item_code', '')),
                        'item_name_en': str(item.get('item_name_en', '')),
                        'item_name_vn': str(item.get('item_name_vn', '')),
                        'quantity': int(item.get('quantity', 1)),
                        'standard_price': float(item.get('standard_price', 0)),
                        'selling_price': float(item.get('selling_price', 0)),
                        'discount_rate': float(item.get('discount_rate', 0)),
                        'unit_price': float(item.get('unit_price', 0)),
                        'amount': float(item.get('amount', 0)),
                        'remark': str(item.get('remark', '')),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    quotation_manager.save_quotation_item(item_data)
                    saved_items += 1
                except Exception as item_error:
                    st.error(f"아이템 {idx+1} 저장 중 오류: {item_error}")
                    continue
                    
            st.success(f"✅ 견적서 저장 완료! (총 {saved_items}개 아이템)")
            
            st.success("✅ Quotation saved successfully!")
            st.info(f"Quotation ID: {quotation_id}")
            
            # 일일 견적서 카운트 업데이트
            if 'daily_quotes' not in st.session_state:
                st.session_state.daily_quotes = []
            st.session_state.daily_quotes.append({
                'date': datetime.now().date(),
                'quotation_id': quotation_id,
                'quotation_number': quotation_number
            })
            
            # 세션 초기화 버튼
            if st.button("🔄 Create New Quotation"):
                st.session_state.quotation_items = []
                st.rerun()
        else:
            st.error("Failed to save quotation")
            
    except Exception as e:
        st.error(f"Error saving quotation: {e}")


def generate_print_preview():
    """견적서 미리보기 생성 (완전히 안전한 방식)"""
    try:
        if not st.session_state.quotation_items:
            st.error("견적서에 제품이 없습니다! 먼저 제품을 추가하세요.")
            return
            
        # 모든 아이템이 dict인지 확인
        safe_items = []
        for item in st.session_state.quotation_items:
            if isinstance(item, dict):
                safe_items.append(item)
            else:
                st.error(f"잘못된 아이템 발견: {type(item)}")
                
        if not safe_items:
            st.error("유효한 제품이 없습니다.")
            return
            
        st.info(f"제품 개수: {len(safe_items)}개")
        
        # 기존 HTML 템플릿 사용
        try:
            with open('Yumold Temp 01.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            st.error("Yumold Temp 01.html 템플릿 파일을 찾을 수 없습니다.")
            return
            
        # 제품 데이터 HTML 생성
        items_html = ""
        for idx, item in enumerate(safe_items):
            items_html += f"""
                <tr>
                    <td rowspan="2" style="text-align: center; vertical-align: middle;">{idx + 1}</td>
                    <td>{item.get('item_code', 'N/A')}</td>
                    <td>{item.get('item_name_en', 'N/A')}</td>
                    <td style="text-align: center;">{item.get('quantity', 1)}</td>
                    <td style="text-align: right;">{item.get('standard_price', 0):,.0f}</td>
                    <td style="text-align: center;">{item.get('discount_rate', 0)}%</td>
                    <td style="text-align: right;">{item.get('unit_price', 0):,.0f}</td>
                    <td style="text-align: right;">{item.get('amount', 0):,.0f}</td>
                </tr>
                <tr>
                    <td colspan="7" style="padding-left: 20px; font-size: 9px; color: #666;">
                        VN: {item.get('item_name_vn', '')}
                        {(' | ' + item.get('remark', '')) if item.get('remark', '') else ''}
                    </td>
                </tr>
            """
        
        # 총액 계산
        def calculate_totals_local(items, vat_pct):
            subtotal = sum(item.get('amount', 0) for item in items)
            vat_amount = subtotal * vat_pct / 100
            total = subtotal + vat_amount
            return subtotal, vat_amount, total
            
        vat_percentage = st.session_state.get('print_vat_percentage', st.session_state.get('vat_percentage', 10.0))
        subtotal, vat_amount, total = calculate_totals_local(safe_items, vat_percentage)
        
        # 세션에서 실제 견적번호 가져오기 (저장된 견적서의 번호)
        quotation_number = st.session_state.get('print_quotation_number', f"YMV-Q{datetime.now().strftime('%y%m%d')}-001")
        
        # 세션에서 실제 입력값 가져오기 (print_로 시작하는 키 우선 사용)
        customer_company = st.session_state.get('print_customer_company', st.session_state.get('customer_company', ''))
        customer_address = st.session_state.get('print_customer_address', st.session_state.get('customer_address', ''))
        contact_person = st.session_state.get('print_customer_contact_person', st.session_state.get('contact_person', ''))
        customer_phone = st.session_state.get('print_customer_phone', st.session_state.get('phone_number', ''))
        customer_email = st.session_state.get('print_customer_email', st.session_state.get('email', ''))
        project_name = st.session_state.get('print_project_name', st.session_state.get('project_name', ''))
        part_name = st.session_state.get('print_part_name', st.session_state.get('part_name', ''))
        part_weight = st.session_state.get('print_part_weight', st.session_state.get('part_weight', ''))
        mold_number = st.session_state.get('print_mold_number', st.session_state.get('mold_number', ''))
        hrs_info = st.session_state.get('print_hrs_info', st.session_state.get('hrs_info', ''))
        resin_type = st.session_state.get('print_resin_type', st.session_state.get('resin_type', ''))
        resin_additive = st.session_state.get('print_resin_additive', st.session_state.get('resin_additive', ''))
        sol_material = st.session_state.get('print_sol_material', st.session_state.get('sol_material', ''))
        remark = st.session_state.get('print_remark', st.session_state.get('remark', ''))
        payment_terms = st.session_state.get('print_payment_terms', st.session_state.get('payment_terms', ''))
        account = st.session_state.get('print_account', st.session_state.get('account', '700-038-038199 (Shinhan Bank Vietnam)'))
        sales_rep_name = st.session_state.get('print_sales_rep_name', st.session_state.get('sales_rep_name', ''))
        sales_rep_phone = st.session_state.get('print_sales_rep_phone', st.session_state.get('sales_rep_phone', ''))
        sales_rep_email = st.session_state.get('print_sales_rep_email', st.session_state.get('sales_rep_email', ''))
        
        # 날짜 처리
        valid_date = st.session_state.get('valid_date')
        if valid_date and hasattr(valid_date, 'strftime'):
            valid_date_str = valid_date.strftime('%d-%m-%Y')
        else:
            valid_date_str = (datetime.now() + timedelta(days=30)).strftime('%d-%m-%Y')
            
        delivery_date = st.session_state.get('delivery_date')
        if delivery_date and hasattr(delivery_date, 'strftime'):
            delivery_date_str = delivery_date.strftime('%d-%m-%Y')
        else:
            delivery_date_str = datetime.now().strftime('%d-%m-%Y')

        # 템플릿 변수 교체 (모든 필드 포함)
        today = datetime.now()
        replacements = {
            '{{quotation_number}}': quotation_number,
            '{{quote_date}}': today.strftime('%d-%m-%Y'),
            '{{company_name}}': customer_company,
            '{{customer_company}}': customer_company,
            '{{customer_address}}': customer_address,
            '{{contact_person}}': contact_person,
            '{{customer_phone}}': customer_phone,
            '{{customer_email}}': customer_email,
            '{{project_name}}': project_name,
            '{{part_name}}': part_name,
            '{{part_weight}}': part_weight,
            '{{mold_number}}': mold_number,
            '{{hrs_info}}': hrs_info,
            '{{resin_type}}': resin_type,
            '{{resin_additive}}': resin_additive,
            '{{sol_material}}': sol_material,
            '{{remark}}': remark,
            '{{payment_terms}}': payment_terms,
            '{{delivery_date}}': delivery_date_str,
            '{{valid_date}}': valid_date_str,
            '{{account}}': account,
            '{{sales_rep_name}}': sales_rep_name,
            '{{sales_rep_phone}}': sales_rep_phone,
            '{{sales_rep_email}}': sales_rep_email,
            '{{items_rows}}': items_html,
            '{{subtotal}}': f"{subtotal:,.0f}",
            '{{vat_amount}}': f"{vat_amount:,.0f}",
            '{{total}}': f"{total:,.0f}",
            '{{total_incl_vat}}': f"{total:,.0f}",
            '{{vat_percentage}}': f"{vat_percentage}",
            '{{revision_number}}': str(st.session_state.get('print_revision_number', '00')),
            '{{currency}}': 'VND'
        }
        
        # 모든 변수를 교체
        final_html = template_content
        for placeholder, value in replacements.items():
            final_html = final_html.replace(placeholder, str(value))
        
        # HTML 파일 저장 (실제 견적번호 사용)
        actual_quotation_number = st.session_state.get('print_quotation_number', quotation_number)
        filename = f"{actual_quotation_number}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        st.success(f"HTML 파일 생성: {filename}")
        
        # 다운로드 버튼
        st.download_button(
            label="📄 Download HTML",
            data=final_html.encode('utf-8'),
            file_name=filename,
            mime="text/html"
        )
        
        # HTML 파일을 streamlit으로 바로 표시 (Print Preview 제목 제거)
        import streamlit.components.v1 as components
        components.html(final_html, height=800, scrolling=True)
        
        st.info("다운로드한 HTML 파일을 브라우저에서 열고 Ctrl+P로 인쇄하세요!")
        
    except Exception as e:
        st.error(f"미리보기 생성 오류: {e}")
        import traceback
        st.code(traceback.format_exc())


def update_quote_count():
    """일일 견적서 카운트 업데이트"""
    if 'daily_quotes' not in st.session_state:
        st.session_state.daily_quotes = []
    
    today = datetime.now().date()
    # 오늘 날짜의 견적서만 카운트
    today_quotes = [q for q in st.session_state.daily_quotes if q.get('date') == today]
    return len(today_quotes) + 1


def main_quotation_action(customer_company, quotation_number, quote_date, revision_number, 
                         currency, customer_address, contact_person, customer_phone, 
                         customer_email, vat_percentage, project_name, part_name, 
                         part_weight, mold_number, hrs_info, resin_type, resin_additive,
                         sol_material, remark, valid_date, payment_terms, delivery_date):
    """메인 견적서 저장 액션"""
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    
    try:
        if not customer_company.strip():
            st.error("Please enter customer company name.")
            return
        
        if not st.session_state.quotation_items:
            st.error("Please add at least one product.")
            return
        
        # 총액 계산
        if st.session_state.quotation_items:
            subtotal, vat_amount, total = calculate_totals(st.session_state.quotation_items, vat_percentage)
        else:
            subtotal = vat_amount = total = 0.0
        
        # 견적서 저장 로직 구현
        quotation_id = f"QUOT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        current_time = datetime.now().isoformat()
        
        quotation_data = {
            'quotation_id': quotation_id,
            'quotation_number': quotation_number,
            'quote_date': quote_date.isoformat(),
            'revision_number': revision_number,
            'currency': currency,
            'customer_company': customer_company,
            'customer_address': customer_address,
            'customer_contact_person': contact_person,
            'customer_phone': customer_phone,
            'customer_email': customer_email,
            'vat_percentage': vat_percentage,
            'subtotal_excl_vat': subtotal,
            'vat_amount': vat_amount,
            'total_incl_vat': total,
            'project_name': project_name,
            'part_name': part_name,
            'part_weight': part_weight,
            'mold_number': mold_number,
            'hrs_info': hrs_info,
            'resin_type': resin_type,
            'resin_additive': resin_additive,
            'sol_material': sol_material,
            'remark': remark,
            'valid_date': valid_date.isoformat() if valid_date else None,
            'contact_info': f"700-038-038199 (Shinhan Bank Vietnam)",
            'account': f"700-038-038199 (Shinhan Bank Vietnam)",
            'payment_terms': payment_terms,
            'delivery_date': delivery_date.isoformat() if delivery_date else None,
            'quotation_status': 'draft',
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # 견적서 저장
        success = quotation_manager.save_quotation(quotation_data)
        
        if success:
            # 견적서 아이템들 저장 (완전 안전 처리)
            valid_items = []
            for item in st.session_state.quotation_items:
                if isinstance(item, dict):
                    valid_items.append(item)
            
            if not valid_items:
                st.error("저장할 유효한 아이템이 없습니다.")
                return
            
            saved_items = 0
            for idx, item in enumerate(valid_items):
                try:
                    item_data = {
                        'item_id': f"QI_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx+1}",
                        'quotation_id': quotation_id,
                        'line_number': idx + 1,
                        'source_product_code': str(item.get('product_code', item.get('item_code', ''))),
                        'item_code': str(item.get('item_code', item.get('product_code', ''))),
                        'item_name_en': str(item.get('item_name_en', item.get('product_name', ''))),
                        'item_name_vn': str(item.get('item_name_vn', item.get('product_name_vn', ''))),
                        'quantity': int(item.get('quantity', 1)),
                        'standard_price': float(item.get('standard_price', 0)),
                        'selling_price': float(item.get('selling_price', item.get('unit_price', 0))),
                        'discount_rate': float(item.get('discount_rate', 0)),
                        'unit_price': float(item.get('unit_price', 0)),
                        'amount': float(item.get('amount', 0)),
                        'remark': str(item.get('remark', '')),
                        'created_at': current_time,
                        'updated_at': current_time
                    }
                    
                    quotation_manager.save_quotation_item(item_data)
                    saved_items += 1
                    
                except Exception as item_error:
                    st.error(f"아이템 {idx+1} 저장 실패: {item_error}")
                    continue
            
            if saved_items > 0:
                st.success(f"✅ 견적서 저장 완료! ({saved_items}개 아이템)")
                st.info(f"견적서 ID: {quotation_id}")
                
                # 저장 완료 알림만 표시 (프린트는 Print Quotation 탭에서)
                st.info("💡 프린트를 원하시면 'Print Quotation' 탭을 이용해주세요!")
            else:
                st.error("❌ 아이템 저장에 실패했습니다.")
            
            # 세션 초기화
            if st.button("🔄 Create New Quotation"):
                st.session_state.quotation_items = []
                st.rerun()
        else:
            st.error("Failed to save quotation")
            
    except Exception as e:
        st.error(f"Error saving quotation: {e}")



def show_quotation_edit():
    """견적서 수정 (리비전 생성) - 승인 전만 가능"""
    st.subheader("🔄 Edit Quotation - Create Revision")
    
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    quotations = quotation_manager.get_all_quotations()
    
    if isinstance(quotations, pd.DataFrame) and len(quotations) > 0:
        # 승인되지 않은 견적서만 필터링
        editable_quotations = quotations[quotations['quotation_status'] != 'approved']
        
        if len(editable_quotations) == 0:
            st.warning("⚠️ No editable quotations available. Approved quotations cannot be modified.")
            return
        
        st.markdown("#### 📝 Create New Revision")
        st.info("💡 Only draft quotations can be edited. All data from the selected quotation will be copied for editing.")
        
        # 수정 가능한 견적서만 선택 옵션에 추가
        quotation_options = []
        for _, quote in editable_quotations.iterrows():
            status_color = "🟡" if quote['quotation_status'] == 'draft' else "🔵"
            quotation_options.append(f"{status_color} {quote['quotation_number']} - {quote['customer_company']}")
        
        selected_quote = st.selectbox("Select Quotation to Revise (Draft Only):", quotation_options, key="edit_select")
        
        if selected_quote:
            # 상태 아이콘 제거하고 견적번호 추출
            quote_number = selected_quote.split(" ")[1]  # 이모지 다음의 견적번호
            original_quote = quotations[quotations['quotation_number'] == quote_number].iloc[0]
            
            # 수정 가능 여부 재확인
            can_edit, message = quotation_manager.can_edit_quotation(original_quote['quotation_id'])
            
            if not can_edit:
                st.error(f"❌ {message}")
                return
            
            # 현재 견적서 정보 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                status_display = original_quote['quotation_status']
                if status_display == 'approved':
                    status_display = "✅ approved"
                elif status_display == 'draft':
                    status_display = "📝 draft"
                else:
                    status_display = f"📋 {status_display}"
                st.metric("Current Status", status_display)
            with col2:
                st.metric("Total Amount", f"{original_quote['total_incl_vat']:,.0f} VND")
            with col3:
                st.metric("Quote Date", original_quote['quote_date'])
            
            # 새로운 리비전 번호 미리보기
            base_number = quote_number.split("-Rv")[0]
            existing_revisions = quotations[quotations['quotation_number'].str.startswith(base_number)]
            
            max_revision = 0
            for _, rev_quote in existing_revisions.iterrows():
                if "-Rv" in rev_quote['quotation_number']:
                    try:
                        rev_num = int(rev_quote['quotation_number'].split("-Rv")[1])
                        max_revision = max(max_revision, rev_num)
                    except:
                        pass
            
            new_revision = f"{base_number}-Rv{max_revision + 1:02d}"
            st.info(f"🆕 New revision will be created as: **{new_revision}**")
            
            # 편집 모드가 아닐 때만 버튼 표시
            if not st.session_state.get('edit_mode', False):
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔄 Create Revision", type="primary", use_container_width=True):
                        create_quotation_revision(original_quote, new_revision)
                with col_btn2:
                    if st.button("✏️ Edit Content", type="secondary", use_container_width=True, key=f"edit_content_{original_quote['quotation_id']}"):
                        # 편집 모드로 전환
                        st.session_state.edit_mode = True
                        st.session_state.current_editing_id = original_quote['quotation_id']
                        
                        # 데이터베이스에서 최신 견적서 정보 다시 조회
                        import sqlite3
                        conn = sqlite3.connect('erp_system.db')
                        quote_df = pd.read_sql_query('''
                            SELECT * FROM quotations WHERE quotation_id = ?
                        ''', conn, params=[original_quote['quotation_id']])
                        conn.close()
                        
                        if len(quote_df) > 0:
                            # 최신 데이터로 업데이트
                            fresh_quote = quote_df.iloc[0].to_dict()
                            # 전화번호가 비어있으면 기본값 설정
                            if not fresh_quote.get('customer_phone'):
                                fresh_quote['customer_phone'] = '+84 903 123 456'
                            st.session_state.editing_quotation = fresh_quote
                            
                            # 편집용 아이템 세션 초기화
                            if 'edit_quotation_items' in st.session_state:
                                del st.session_state.edit_quotation_items
                            
                            st.success("편집 모드로 전환됩니다...")
                        else:
                            st.session_state.editing_quotation = original_quote.to_dict()
                        
                        st.rerun()
                    
        # 편집 모드일 때 편집 폼 표시
        if st.session_state.get('edit_mode', False) and 'editing_quotation' in st.session_state:
            st.markdown("---")
            st.markdown("### ✏️ 견적서 편집 모드")
            
            # 편집 취소 버튼
            if st.button("❌ 편집 취소", key="cancel_edit"):
                st.session_state.edit_mode = False
                if 'editing_quotation' in st.session_state:
                    del st.session_state.editing_quotation
                if 'edit_quotation_items' in st.session_state:
                    del st.session_state.edit_quotation_items
                st.rerun()
            
            show_edit_quotation_form()
    else:
        st.info("No quotations found. Create a quotation first.")


def show_status_management():
    """견적서 상태 관리"""
    st.subheader("📊 Status Management")
    
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    quotations = quotation_manager.get_all_quotations()
    
    if isinstance(quotations, pd.DataFrame) and len(quotations) > 0:
        # 상태별 통계
        st.markdown("#### 📈 Status Overview")
        status_counts = quotations['quotation_status'].value_counts()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        status_map = {
            'draft': ('Draft', col1),
            'sent': ('Sent', col2),
            'approved': ('Approved', col3),
            'rejected': ('Rejected', col4),
            'completed': ('Completed', col5)
        }
        
        for status, (english_name, col) in status_map.items():
            count = status_counts.get(status, 0)
            with col:
                st.metric(english_name, count)
        
        st.markdown("---")
        st.markdown("#### 🔄 Update Status")
        
        # 견적서 선택
        quotation_options = []
        for _, quote in quotations.iterrows():
            status_display = quote['quotation_status'].title()
            quotation_options.append(f"{quote['quotation_number']} - {quote['customer_company']} ({status_display})")
        
        selected_status_quote = st.selectbox("Select Quotation:", quotation_options, key="status_select")
        
        status_options = ["draft", "sent", "approved", "rejected", "completed"]
        
        new_status = st.selectbox("New Status:", status_options)
        
        if st.button("✅ Update Status", type="primary", use_container_width=True):
            quote_number = selected_status_quote.split(" - ")[0]
            success = quotation_manager.update_quotation_status(quote_number, new_status)
            
            if success:
                st.success(f"Status updated to: {new_status.title()}")
                st.rerun()
            else:
                st.error("Failed to update status")
                
        # 상태별 견적서 목록
        st.markdown("---")
        st.markdown("#### 📋 Quotations by Status")
        
        status_filter_options = ["All"] + [s.title() for s in status_options]
        selected_status_filter = st.selectbox("Filter by Status:", status_filter_options, key="filter_status")
        
        if selected_status_filter != "All":
            filter_status = selected_status_filter.lower()
            filtered_quotations = quotations[quotations['quotation_status'] == filter_status]
        else:
            filtered_quotations = quotations
        
        if len(filtered_quotations) > 0:
            display_data = filtered_quotations[['quotation_number', 'customer_company', 'quote_date', 'total_incl_vat', 'quotation_status']].copy()
            
            # 상태 영어로 표시 (Title Case)
            display_data['quotation_status'] = display_data['quotation_status'].str.title()
            
            # 금액 포맷
            display_data['total_incl_vat'] = display_data['total_incl_vat'].apply(lambda x: f"{x:,.0f} VND" if pd.notnull(x) else "0 VND")
            
            # 컬럼명 영어로 표시
            display_data.columns = ['Quotation Number', 'Customer', 'Quote Date', 'Total Amount', 'Status']
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info(f"No quotations found for status: {selected_status_filter}")
    else:
        st.info("No quotations found. Create a quotation first.")


def show_edit_quotation_form():
    """견적서 편집 폼 표시"""
    st.markdown("---")
    st.subheader("✏️ Edit Quotation")
    
    if 'editing_quotation' not in st.session_state:
        st.error("No quotation data found for editing")
        return
    
    original_quote = st.session_state.editing_quotation
    quotation_manager = SQLiteQuotationManager()
    

    
    # 기존 아이템들 로드
    original_items = quotation_manager.get_quotation_items(original_quote['quotation_id'])
    
    # 편집 폼
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Customer Information**")
            # None 값과 빈 문자열 처리
            company_value = str(original_quote.get('customer_company') or '').strip()
            contact_value = str(original_quote.get('customer_contact_person') or '').strip()
            phone_value = str(original_quote.get('customer_phone') or '').strip()
            email_value = str(original_quote.get('customer_email') or '').strip()
            address_value = str(original_quote.get('customer_address') or '').strip()
            

            
            edit_customer_company = st.text_input("Customer Company", value=str(company_value), key="edit_customer_company")
            edit_customer_contact = st.text_input("Contact Person", value=str(contact_value), key="edit_customer_contact")
            edit_customer_phone = st.text_input("Phone", value=str(phone_value), key="edit_customer_phone")
            edit_customer_email = st.text_input("Email", value=str(email_value), key="edit_customer_email")
            edit_customer_address = st.text_area("Address", value=str(address_value), key="edit_customer_address")
            
        with col2:
            st.markdown("**Quotation Information**")
            edit_quotation_number = st.text_input("Quotation Number", value=original_quote.get('quotation_number', ''), disabled=True)
            edit_quote_date = st.date_input("Quote Date", value=pd.to_datetime(original_quote.get('quote_date')).date() if original_quote.get('quote_date') else datetime.now().date(), key="edit_quote_date")
            edit_currency = st.selectbox("Currency", ["VND", "USD"], index=0 if original_quote.get('currency', 'VND') == 'VND' else 1, key="edit_currency")
            edit_vat_percentage = st.number_input("VAT (%)", value=float(original_quote.get('vat_percentage', 10.0)), min_value=0.0, max_value=100.0, step=0.1, key="edit_vat_percentage")
        
        # Project Information 섹션 추가
        st.markdown("---")
        st.markdown("**📋 Project Information**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            edit_project_name = st.text_input("Project Name", value=str(original_quote.get('project_name', '')), key="edit_project_name")
            edit_part_name = st.text_input("Part Name", value=str(original_quote.get('part_name', '')), key="edit_part_name")
        with col2:
            edit_part_weight = st.text_input("Part Weight", value=str(original_quote.get('part_weight', '')), key="edit_part_weight")
            edit_mold_number = st.text_input("Mold Number", value=str(original_quote.get('mold_number', '')), key="edit_mold_number")
        with col3:
            edit_hrs_info = st.text_input("HRS Info", value=str(original_quote.get('hrs_info', '')), key="edit_hrs_info")
            edit_resin_type = st.text_input("Resin Type", value=str(original_quote.get('resin_type', '')), key="edit_resin_type")
        with col4:
            edit_resin_additive = st.text_input("Resin Additive", value=str(original_quote.get('resin_additive', '')), key="edit_resin_additive")
            edit_sol_material = st.text_input("Sol Material", value=str(original_quote.get('sol_material', '')), key="edit_sol_material")
        
        # 추가 정보
        edit_payment_terms = st.text_input("Payment Terms", value=str(original_quote.get('payment_terms', '')), key="edit_payment_terms")
        edit_remark = st.text_area("Remark", value=str(original_quote.get('remark', '')), key="edit_remark")
        
        # 아이템 편집
        st.markdown("---")
        st.markdown("**📦 Quotation Items**")
        
        # 기존 아이템들을 세션에 로드
        if 'edit_quotation_items' not in st.session_state:
            edit_items = []
            for _, item in original_items.iterrows():
                edit_items.append({
                    'line_number': int(item['line_number']),
                    'item_code': item.get('item_code', ''),
                    'item_name_en': item.get('item_name_en', ''),
                    'item_name_vn': item.get('item_name_vn', ''),
                    'quantity': int(item.get('quantity', 1)),
                    'standard_price': float(item.get('standard_price', 0)),
                    'selling_price': float(item.get('selling_price', 0)),
                    'discount_rate': float(item.get('discount_rate', 0)),
                    'unit_price': float(item.get('unit_price', 0)),
                    'amount': float(item.get('amount', 0)),
                    'remark': item.get('remark', '')
                })
            st.session_state.edit_quotation_items = edit_items
        
        # 아이템 편집 테이블
        if st.session_state.edit_quotation_items:
            for idx, item in enumerate(st.session_state.edit_quotation_items):
                with st.expander(f"Item {item['line_number']}: {item['item_code']}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        item['item_code'] = st.text_input("Item Code", value=item['item_code'], key=f"edit_item_code_{idx}")
                        item['item_name_en'] = st.text_input("English Name", value=item['item_name_en'], key=f"edit_item_name_en_{idx}")
                        item['item_name_vn'] = st.text_input("Vietnamese Name", value=item['item_name_vn'], key=f"edit_item_name_vn_{idx}")
                    with col2:
                        item['quantity'] = st.number_input("Quantity", value=item['quantity'], min_value=1, key=f"edit_quantity_{idx}")
                        item['standard_price'] = st.number_input("Standard Price", value=item['standard_price'], min_value=0.0, key=f"edit_standard_price_{idx}")
                        item['selling_price'] = st.number_input("Selling Price", value=item['selling_price'], min_value=0.0, key=f"edit_selling_price_{idx}")
                    with col3:
                        item['discount_rate'] = st.number_input("Discount Rate (%)", value=item['discount_rate'], min_value=0.0, max_value=100.0, key=f"edit_discount_rate_{idx}")
                        # 단가 및 금액 자동 계산
                        item['unit_price'] = item['selling_price'] * (1 - item['discount_rate'] / 100)
                        item['amount'] = item['unit_price'] * item['quantity']
                        st.text(f"Unit Price: {item['unit_price']:,.0f}")
                        st.text(f"Amount: {item['amount']:,.0f}")
                    
                    item['remark'] = st.text_area("Remark", value=item['remark'], key=f"edit_remark_{idx}")
                    
                    if st.button(f"🗑️ Remove Item {item['line_number']}", key=f"remove_edit_item_{idx}"):
                        st.session_state.edit_quotation_items.pop(idx)
                        st.rerun()
        
        # 제품 검색 및 추가
        st.markdown("---")
        st.markdown("**🔍 Add Product from Database**")
        
        # 제품 검색
        from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
        product_manager = SQLiteMasterProductManager()
        all_products = product_manager.get_all_products()
        
        if isinstance(all_products, pd.DataFrame) and len(all_products) > 0:
            st.info(f"📦 총 {len(all_products)}개의 제품이 데이터베이스에 있습니다.")
            
            # 검색 입력
            search_term = st.text_input("Search products by name or code:", key="edit_search_product")
            
            # 검색 필터링
            if search_term:
                filtered_products = all_products[
                    (all_products['product_name'].str.contains(search_term, case=False, na=False)) |
                    (all_products['product_code'].str.contains(search_term, case=False, na=False))
                ]
                st.info(f"🔍 '{search_term}' 검색 결과: {len(filtered_products)}개 제품")
            else:
                filtered_products = all_products.head(10)  # 처음 10개만 표시
                st.info("💡 모든 제품을 보려면 검색어를 입력하세요. 현재 처음 10개만 표시됩니다.")
            
            if len(filtered_products) > 0:
                # 제품 선택
                product_options = []
                for _, product in filtered_products.iterrows():
                    product_options.append(f"{product['product_code']} - {product['product_name']}")
                
                selected_product_option = st.selectbox("Select product to add:", product_options, key="edit_select_product")
                
                if selected_product_option and st.button("➕ Add Selected Product", key="add_edit_selected_product"):
                    product_code = selected_product_option.split(" - ")[0]
                    selected_product = filtered_products[filtered_products['product_code'] == product_code].iloc[0]
                    
                    # 세션에서 기존 아이템 목록이 없으면 초기화
                    if 'edit_quotation_items' not in st.session_state:
                        st.session_state.edit_quotation_items = []
                    
                    # 가격 정보 - 올바른 컬럼명 사용
                    supply_price = float(selected_product.get('supply_price', 0))
                    sales_price = float(selected_product.get('sales_price_vnd', 0))
                    exchange_rate = float(selected_product.get('exchange_rate', 24000))
                    
                    # supply_price가 USD/CNY 기준이면 VND로 변환
                    if supply_price > 0 and sales_price == 0:
                        sales_price = supply_price * exchange_rate
                    
                    new_item = {
                        'line_number': len(st.session_state.edit_quotation_items) + 1,
                        'item_code': product_code,
                        'item_name_en': selected_product.get('product_name', ''),
                        'item_name_vn': selected_product.get('product_name_vi', ''),
                        'quantity': 1,
                        'standard_price': sales_price,
                        'selling_price': sales_price,
                        'discount_rate': 0.0,
                        'unit_price': sales_price,
                        'amount': sales_price,
                        'remark': ''
                    }
                    st.session_state.edit_quotation_items.append(new_item)
                    st.success(f"✅ Product {product_code} added successfully!")
                    st.rerun()
            else:
                st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
        else:
            st.warning("📦 제품 데이터베이스가 비어있습니다. 먼저 Master Product Management에서 제품을 등록하세요.")
        
        # 수동 아이템 추가 버튼
        if st.button("➕ Add Manual Item", key="add_edit_manual_item"):
            # 세션에서 기존 아이템 목록이 없으면 초기화
            if 'edit_quotation_items' not in st.session_state:
                st.session_state.edit_quotation_items = []
                
            new_item = {
                'line_number': len(st.session_state.edit_quotation_items) + 1,
                'item_code': '',
                'item_name_en': '',
                'item_name_vn': '',
                'quantity': 1,
                'standard_price': 0.0,
                'selling_price': 0.0,
                'discount_rate': 0.0,
                'unit_price': 0.0,
                'amount': 0.0,
                'remark': ''
            }
            st.session_state.edit_quotation_items.append(new_item)
            st.success("✅ Manual item added successfully!")
            st.rerun()
        
        # 총계 계산
        if st.session_state.edit_quotation_items:
            subtotal = sum(item['amount'] for item in st.session_state.edit_quotation_items)
            vat_amount = subtotal * edit_vat_percentage / 100
            total = subtotal + vat_amount
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Subtotal (Excl. VAT)", f"{subtotal:,.0f} {edit_currency}")
            with col2:
                st.metric(f"VAT ({edit_vat_percentage}%)", f"{vat_amount:,.0f} {edit_currency}")
            with col3:
                st.metric("Total (Incl. VAT)", f"{total:,.0f} {edit_currency}")
        
        # 저장 및 취소 버튼
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save as New Revision", type="primary", use_container_width=True):
                save_as_new_revision(original_quote, edit_customer_company, edit_customer_contact, 
                                    edit_customer_phone, edit_customer_email, edit_customer_address,
                                    edit_quote_date, edit_currency, edit_vat_percentage)
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.edit_mode = False
                if 'editing_quotation' in st.session_state:
                    del st.session_state.editing_quotation
                if 'edit_quotation_items' in st.session_state:
                    del st.session_state.edit_quotation_items
                st.rerun()


def save_as_new_revision(original_quote, customer_company, customer_contact, customer_phone, 
                         customer_email, customer_address, quote_date, currency, vat_percentage):
    """편집된 견적서를 새로운 리비전으로 저장"""
    quotation_manager = SQLiteQuotationManager()
    
    try:
        # 새로운 리비전 번호 생성
        original_number = original_quote['quotation_number']
        base_number = original_number.split("-Rv")[0]
        
        # 기존 리비전들 확인
        all_quotations = quotation_manager.get_all_quotations()
        existing_revisions = all_quotations[all_quotations['quotation_number'].str.startswith(base_number)]
        
        max_revision = 0
        for _, rev_quote in existing_revisions.iterrows():
            if "-Rv" in rev_quote['quotation_number']:
                try:
                    rev_num = int(rev_quote['quotation_number'].split("-Rv")[1])
                    max_revision = max(max_revision, rev_num)
                except:
                    pass
        
        new_revision_number = f"{base_number}-Rv{max_revision + 1:02d}"
        new_quotation_id = f"Q_{datetime.now().strftime('%Y%m%d%H%M%S')}_REV"
        
        # 총계 계산
        if st.session_state.edit_quotation_items:
            subtotal = sum(item['amount'] for item in st.session_state.edit_quotation_items)
            vat_amount = subtotal * vat_percentage / 100
            total = subtotal + vat_amount
        else:
            subtotal = vat_amount = total = 0
        
        # 새로운 리비전 데이터 (프로젝트 정보 포함)
        new_revision_data = {
            'quotation_id': new_quotation_id,
            'quotation_number': new_revision_number,
            'quote_date': quote_date.isoformat(),
            'revision_number': f"Rv{max_revision + 1:02d}",
            'currency': currency,
            'customer_company': customer_company,
            'customer_address': customer_address,
            'customer_contact_person': customer_contact,
            'customer_phone': customer_phone,
            'customer_email': customer_email,
            'vat_percentage': vat_percentage,
            'subtotal_excl_vat': subtotal,
            'vat_amount': vat_amount,
            'total_incl_vat': total,
            'project_name': st.session_state.get('edit_project_name', original_quote.get('project_name', '')),
            'part_name': st.session_state.get('edit_part_name', original_quote.get('part_name', '')),
            'part_weight': st.session_state.get('edit_part_weight', original_quote.get('part_weight', '')),
            'mold_number': st.session_state.get('edit_mold_number', original_quote.get('mold_number', '')),
            'hrs_info': st.session_state.get('edit_hrs_info', original_quote.get('hrs_info', '')),
            'resin_type': st.session_state.get('edit_resin_type', original_quote.get('resin_type', '')),
            'resin_additive': st.session_state.get('edit_resin_additive', original_quote.get('resin_additive', '')),
            'sol_material': st.session_state.get('edit_sol_material', original_quote.get('sol_material', '')),
            'payment_terms': st.session_state.get('edit_payment_terms', original_quote.get('payment_terms', '')),
            'remark': st.session_state.get('edit_remark', original_quote.get('remark', '')),
            'quotation_status': 'draft',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        success = quotation_manager.save_quotation(new_revision_data)
        
        if success:
            # 새 아이템들 저장
            for idx, item in enumerate(st.session_state.edit_quotation_items):
                item_data = {
                    'item_id': f"QI_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx+1}_REV",
                    'quotation_id': new_quotation_id,
                    'line_number': item['line_number'],
                    'source_product_code': item.get('item_code'),
                    'item_code': item.get('item_code'),
                    'item_name_en': item.get('item_name_en'),
                    'item_name_vn': item.get('item_name_vn'),
                    'quantity': item.get('quantity', 1),
                    'standard_price': item.get('standard_price', 0),
                    'selling_price': item.get('selling_price', 0),
                    'discount_rate': item.get('discount_rate', 0),
                    'unit_price': item.get('unit_price', 0),
                    'amount': item.get('amount', 0),
                    'remark': item.get('remark', ''),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                quotation_manager.save_quotation_item(item_data)
            
            st.success(f"✅ 새로운 리비전이 생성되었습니다: {new_revision_number}")
            st.info("📋 Quotation List 탭에서 새로운 리비전을 확인할 수 있습니다.")
            
            # 편집 모드 종료
            st.session_state.edit_mode = False
            if 'editing_quotation' in st.session_state:
                del st.session_state.editing_quotation
            if 'edit_quotation_items' in st.session_state:
                del st.session_state.edit_quotation_items
            
            st.rerun()
        else:
            st.error("새로운 리비전 저장에 실패했습니다.")
            
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다: {e}")
        import traceback
        st.code(traceback.format_exc())


def create_quotation_revision(original_quote, new_revision_number):
    """기존 견적서를 복사하여 새로운 리비전 생성"""
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    
    try:
        # 기존 견적서 아이템들 가져오기
        original_items = quotation_manager.get_quotation_items(original_quote['quotation_id'])
        
        # 새로운 견적서 ID 생성
        new_quotation_id = f"QUOT_{datetime.now().strftime('%Y%m%d%H%M%S')}_REV"
        current_time = datetime.now().isoformat()
        
        # 새로운 견적서 데이터 생성 (원본 복사)
        revision_data = {
            'quotation_id': new_quotation_id,
            'quotation_number': new_revision_number,
            'quote_date': datetime.now().date().isoformat(),
            'revision_number': new_revision_number.split("-Rv")[1] if "-Rv" in new_revision_number else "01",
            'currency': original_quote['currency'],
            'customer_company': original_quote['customer_company'],
            'customer_address': original_quote.get('customer_address', ''),
            'customer_contact_person': original_quote.get('customer_contact_person', ''),
            'customer_phone': original_quote.get('customer_phone', ''),
            'customer_email': original_quote.get('customer_email', ''),
            'vat_percentage': original_quote.get('vat_percentage', 10.0),
            'subtotal_excl_vat': original_quote['total_incl_vat'] / 1.1,  # 역계산
            'vat_amount': original_quote['total_incl_vat'] * 0.1 / 1.1,
            'total_incl_vat': original_quote['total_incl_vat'],
            'quotation_status': 'draft',
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # 견적서 저장
        success = quotation_manager.save_quotation(revision_data)
        
        if success:
            # 아이템들도 복사
            for idx, (_, item) in enumerate(original_items.iterrows()):
                item_data = {
                    'item_id': f"QI_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx+1}_REV",
                    'quotation_id': new_quotation_id,
                    'line_number': item['line_number'],
                    'source_product_code': item.get('source_product_code', ''),
                    'item_code': item.get('item_code', ''),
                    'item_name_en': item.get('item_name_en', ''),
                    'item_name_vn': item.get('item_name_vn', ''),
                    'quantity': item.get('quantity', 1),
                    'standard_price': item.get('standard_price', 0),
                    'selling_price': item.get('selling_price', 0),
                    'discount_rate': item.get('discount_rate', 0),
                    'unit_price': item.get('unit_price', 0),
                    'amount': item.get('amount', 0),
                    'remark': item.get('remark', ''),
                    'created_at': current_time,
                    'updated_at': current_time
                }
                quotation_manager.save_quotation_item(item_data)
            
            st.success(f"✅ Revision created: {new_revision_number}")
            st.info("💡 New revision has been created in the database. You can view it in the 'Quotation List' tab.")
            st.info("💡 To edit the revision, create a new quotation with the same information or use the revision as reference.")
            
        else:
            st.error("Failed to create revision")
            
    except Exception as e:
        st.error(f"Error creating revision: {e}")
        import traceback
        st.code(traceback.format_exc())


def open_print_window(quotation_id):
    """견적서 프린트 창 열기"""
    import sqlite3
    
    try:
        # 견적서 정보 조회
        conn = sqlite3.connect('erp_system.db')
        quote_df = pd.read_sql_query('''
            SELECT * FROM quotations WHERE quotation_id = ?
        ''', conn, params=[quotation_id])
        
        if len(quote_df) == 0:
            st.error("Quotation not found")
            return
            
        quote = quote_df.iloc[0]
        
        # 견적서 아이템들 조회
        items_df = pd.read_sql_query('''
            SELECT * FROM quotation_items WHERE quotation_id = ? ORDER BY line_number
        ''', conn, params=[quotation_id])
        
        conn.close()
        
        # 프린트용 HTML 생성
        html_content = f"""
        <div style="background: white; padding: 20px; border: 1px solid #ddd; font-family: Arial, sans-serif;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #333; margin: 0;">YUMOLD VIETNAM CO., LTD</h2>
                <h3 style="color: #666; margin: 5px 0;">QUOTATION</h3>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div>
                    <strong>To:</strong><br>
                    {quote.get('customer_company', '')}<br>
                    {quote.get('customer_address', '')}<br>
                    Contact: {quote.get('customer_contact_person', '')}<br>
                    Phone: {quote.get('customer_phone', '')}<br>
                    Email: {quote.get('customer_email', '')}
                </div>
                <div style="text-align: right;">
                    <strong>Quote No:</strong> {quote.get('quotation_number', '')}<br>
                    <strong>Date:</strong> {quote.get('quote_date', '')}<br>
                    <strong>Currency:</strong> {quote.get('currency', 'VND')}<br>
                    <strong>Status:</strong> {quote.get('quotation_status', '').title()}
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">No.</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Item Name</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Qty</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Unit Price</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # 아이템들 추가
        for _, item in items_df.iterrows():
            html_content += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{item.get('line_number', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{item.get('item_name_en', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{item.get('quantity', 0)}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{item.get('unit_price', 0):,.0f}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{item.get('amount', 0):,.0f}</td>
                </tr>
            """
        
        # 총계 추가
        html_content += f"""
                </tbody>
            </table>
            
            <div style="text-align: right; margin-top: 20px;">
                <div><strong>Subtotal (Excl. VAT): {quote.get('subtotal_excl_vat', 0):,.0f} {quote.get('currency', 'VND')}</strong></div>
                <div><strong>VAT ({quote.get('vat_percentage', 10)}%): {quote.get('vat_amount', 0):,.0f} {quote.get('currency', 'VND')}</strong></div>
                <div style="font-size: 18px; border-top: 2px solid #333; padding-top: 5px; margin-top: 5px;">
                    <strong>Total (Incl. VAT): {quote.get('total_incl_vat', 0):,.0f} {quote.get('currency', 'VND')}</strong>
                </div>
            </div>
            
            <div style="margin-top: 30px; font-size: 12px; color: #666;">
                <div><strong>Terms & Conditions:</strong></div>
                <div>• Payment Terms: {quote.get('payment_terms', 'To be discussed')}</div>
                <div>• Valid Until: {quote.get('valid_date', 'To be confirmed')}</div>
                <div>• Delivery: {quote.get('delivery_date', 'To be confirmed')}</div>
            </div>
        </div>
        """
        
        # 프린트 버튼만 표시  
        if st.button("🖨️ Print", key=f"print_doc_{quotation_id}", type="primary"):
            # YUMOLD 템플릿을 사용해서 HTML 생성
            from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
            quotation_manager = SQLiteQuotationManager()
            
            try:
                # 템플릿 파일 읽기
                with open('templates/quotation_print_template.html', 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # 견적서 아이템들 조회
                items_df = pd.read_sql_query('''
                    SELECT * FROM quotation_items WHERE quotation_id = ? ORDER BY line_number
                ''', sqlite3.connect('erp_system.db'), params=[quotation_id])
                
                # 템플릿에 데이터 삽입
                template_content = template_content.replace('{quotation_number}', quote.get('quotation_number', ''))
                template_content = template_content.replace('{quote_date}', quote.get('quote_date', ''))
                template_content = template_content.replace('{revision_number}', quote.get('revision_number', '00'))
                template_content = template_content.replace('{currency}', quote.get('currency', 'VND'))
                template_content = template_content.replace('{customer_company}', quote.get('customer_company', ''))
                template_content = template_content.replace('{customer_address}', quote.get('customer_address', ''))
                template_content = template_content.replace('{customer_contact_person}', quote.get('customer_contact_person', ''))
                template_content = template_content.replace('{customer_phone}', quote.get('customer_phone', ''))
                template_content = template_content.replace('{customer_email}', quote.get('customer_email', ''))
                template_content = template_content.replace('{project_name}', quote.get('project_name', ''))
                template_content = template_content.replace('{part_name}', quote.get('part_name', ''))
                template_content = template_content.replace('{part_weight}', quote.get('part_weight', ''))
                template_content = template_content.replace('{mold_number}', quote.get('mold_number', ''))
                template_content = template_content.replace('{hrs_info}', quote.get('hrs_info', ''))
                template_content = template_content.replace('{resin_type}', quote.get('resin_type', ''))
                template_content = template_content.replace('{resin_additive}', quote.get('resin_additive', ''))
                template_content = template_content.replace('{sol_material}', quote.get('sol_material', ''))
                template_content = template_content.replace('{remark}', quote.get('remark', ''))
                template_content = template_content.replace('{valid_date}', quote.get('valid_date', ''))
                template_content = template_content.replace('{payment_terms}', quote.get('payment_terms', ''))
                template_content = template_content.replace('{delivery_date}', quote.get('delivery_date', ''))
                template_content = template_content.replace('{subtotal_excl_vat}', f"{quote.get('subtotal_excl_vat', 0):,.0f}")
                template_content = template_content.replace('{vat_percentage}', str(quote.get('vat_percentage', 10)))
                template_content = template_content.replace('{vat_amount}', f"{quote.get('vat_amount', 0):,.0f}")
                template_content = template_content.replace('{total_incl_vat}', f"{quote.get('total_incl_vat', 0):,.0f}")
                template_content = template_content.replace('{product_name_detail}', quote.get('product_name_detail', ''))
                template_content = template_content.replace('{sales_representative}', quote.get('sales_representative', ''))
                template_content = template_content.replace('{sales_rep_contact}', quote.get('sales_rep_contact', ''))
                template_content = template_content.replace('{account}', quote.get('account', ''))
                
                # 아이템 테이블 생성
                items_html = ""
                for idx, (_, item) in enumerate(items_df.iterrows()):
                    # 베트남어 텍스트 길이에 따른 CSS 클래스 결정
                    vn_text = str(item.get('item_name_vn', ''))
                    vn_class = "vietnamese-text"
                    if len(vn_text) > 80:
                        vn_class += " very-long-text"
                    elif len(vn_text) > 50:
                        vn_class += " long-text"
                    
                    row_number = item.get('line_number', idx + 1)
                    
                    items_html += f"""
                    <tr>
                        <td rowspan="3" style="text-align: center; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; width: 5%; vertical-align: middle;">{row_number}</td>
                        <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 12%;">{item.get('item_code', '')}</td>
                        <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 25%;">{item.get('item_name_en', '')}</td>
                        <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 8%;">{item.get('quantity', 0)}</td>
                        <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 15%;">{item.get('standard_price', 0):,.0f}</td>
                        <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 10%;">{item.get('discount_rate', 0):.1f}%</td>
                        <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 15%;">{item.get('unit_price', 0):,.0f}</td>
                        <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; width: 15%;">{item.get('amount', 0):,.0f}</td>
                    </tr>
                    <tr>
                        <td colspan="7" style="text-align: left; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white;" class="{vn_class}">VN: {vn_text}</td>
                    </tr>
                    <tr>
                        <td colspan="7" style="text-align: left; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; font-size: 7px;">Remark: {item.get('remark', '')}</td>
                    </tr>
                    """
                
                template_content = template_content.replace('{quotation_items}', items_html)
                
                # 화면에 바로 표시
                st.markdown("### 📄 Quotation Preview")
                st.markdown(template_content, unsafe_allow_html=True)
                
                st.success("✅ 견적서가 화면에 표시되었습니다. 브라우저의 Ctrl+P로 프린트하세요!")
                
            except Exception as e:
                st.error(f"Error displaying quotation: {e}")
                import traceback
                st.code(traceback.format_exc())
                
    except Exception as e:
        st.error(f"Error opening print window: {e}")







def show_quotation_list():
    """견적서 목록 - 고객별 그룹화"""
    st.subheader("📋 Quotation List")
    
    from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
    quotation_manager = SQLiteQuotationManager()
    
    try:
        quotations = quotation_manager.get_all_quotations()
        
        if isinstance(quotations, pd.DataFrame) and not quotations.empty:
            # 고객별로 그룹화
            grouped = quotations.groupby('customer_company')
            
            for customer_name, customer_quotes in grouped:
                # 고객별 총 금액 계산
                total_customer_amount = customer_quotes['total_incl_vat'].sum()
                quote_count = len(customer_quotes)
                currency = customer_quotes.iloc[0]['currency']  # 첫 번째 견적서의 통화 사용
                
                # 상태별 금액 계산 - 실제 데이터베이스 상태값 사용
                status_amounts = {}
                status_labels = {
                    'draft': 'Draft',
                    'sent': 'Sent', 
                    'approved': 'Approved',
                    'rejected': 'Rejected',
                    'completed': 'Completed'
                }
                
                for status, label in status_labels.items():
                    status_quotes = customer_quotes[customer_quotes['quotation_status'] == status]
                    if isinstance(status_quotes, pd.DataFrame) and len(status_quotes) > 0:
                        status_amounts[label] = status_quotes['total_incl_vat'].sum()
                    else:
                        status_amounts[label] = 0
                
                # 상태별 금액 표시 문자열 생성
                status_display = []
                for label, amount in status_amounts.items():
                    status_display.append(f"{label}: {amount:,.0f}")
                
                status_text = " | ".join(status_display)
                
                # 고객별 접기/펼치기 섹션 (상태별 금액 먼저, 총 금액은 제거)
                with st.expander(f"🏢 {customer_name} ({quote_count} quotations)", expanded=True):
                    st.markdown(f'<div style="font-size: 14px; font-weight: bold; margin: 5px 0; color: #2E86AB;">진행 상황별 금액: {status_text} {currency}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size: 16px; font-weight: bold; margin: 10px 0; color: #333;">총 견적 금액: {total_customer_amount:,.0f} {currency}</div>', unsafe_allow_html=True)
                    
                    # 테이블 헤더
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 1, 0.8])
                    with col1:
                        st.markdown("**견적서 번호**")
                    with col2:
                        st.markdown("**견적 날짜**")
                    with col3:
                        st.markdown("**총액 (VAT 포함)**")
                    with col4:
                        st.markdown("**통화**")
                    with col5:
                        st.markdown("**상태**")
                    with col6:
                        st.markdown("**삭제**")
                    
                    # 각 견적서 행 (세로 간격 매우 좁게)
                    for _, quote in customer_quotes.iterrows():
                        st.markdown('<div style="margin: 0px; padding: 0px; line-height: 0.8; height: 25px;">', unsafe_allow_html=True)
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 1, 0.8])
                        
                        with col1:
                            st.markdown(f'<div style="font-size: 13px; padding: 1px; line-height: 0.9; margin: 0px; height: 20px; display: flex; align-items: center;">{quote["quotation_number"]}</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div style="font-size: 13px; padding: 1px; line-height: 0.9; margin: 0px; height: 20px; display: flex; align-items: center;">{quote["quote_date"]}</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f'<div style="font-size: 13px; padding: 1px; line-height: 0.9; margin: 0px; height: 20px; display: flex; align-items: center;">{quote["total_incl_vat"]:,.0f}</div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown(f'<div style="font-size: 13px; padding: 1px; line-height: 0.9; margin: 0px; height: 20px; display: flex; align-items: center;">{quote["currency"]}</div>', unsafe_allow_html=True)
                        with col5:
                            # 상태에 따른 표시 (크기 증가)
                            if quote['quotation_status'] == 'approved':
                                st.markdown('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; line-height: 1.2; display: inline-block;">APPROVED</span>', unsafe_allow_html=True)
                            elif quote['quotation_status'] == 'draft':
                                st.markdown('<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; line-height: 1.2; display: inline-block;">DRAFT</span>', unsafe_allow_html=True)
                            elif quote['quotation_status'] == 'submitted':
                                st.markdown('<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; line-height: 1.2; display: inline-block;">SUBMITTED</span>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; line-height: 1.2; display: inline-block;">{quote["quotation_status"].upper()}</span>', unsafe_allow_html=True)
                        with col6:
                            # 삭제 버튼 확인용 키
                            delete_confirm_key = f"delete_confirm_{quote['quotation_id']}"
                            if delete_confirm_key not in st.session_state:
                                if st.button("🗑️", key=f"delete_{quote['quotation_id']}", help="Delete quotation"):
                                    st.session_state[delete_confirm_key] = True
                                    st.rerun()
                            else:
                                # 확인 상태일 때
                                col_confirm, col_cancel = st.columns(2)
                                with col_confirm:
                                    if st.button("✓", key=f"confirm_{quote['quotation_id']}", help="Confirm delete", type="secondary"):
                                        # 실제 삭제 수행 (올바른 방법 사용)
                                        try:
                                            quotation_manager = SQLiteQuotationManager()
                                            success = quotation_manager.delete_quotation(quote['quotation_id'])
                                            if success:
                                                del st.session_state[delete_confirm_key]
                                                st.success(f"견적서 {quote['quotation_number']} 삭제 완료")
                                                st.rerun()
                                            else:
                                                st.error("삭제 실패")
                                        except Exception as e:
                                            st.error(f"삭제 오류: {e}")
                                with col_cancel:
                                    if st.button("✗", key=f"cancel_{quote['quotation_id']}", help="Cancel delete"):
                                        del st.session_state[delete_confirm_key]
                                        st.rerun()
                        st.markdown('</div><div style="margin: 2px 0;"></div>', unsafe_allow_html=True)
                    
                    # 하단 구분선만 표시
                    st.markdown("---")
                    
        else:
            st.info("견적서가 없습니다. 첫 번째 견적서를 생성해보세요!")
            
    except Exception as e:
        st.error(f"견적서 로드 오류: {e}")
        import traceback
        st.code(traceback.format_exc())





def main():
    """메인 페이지"""
    st.set_page_config(page_title="YUMOLD Quotation System", layout="wide", initial_sidebar_state="expanded")
    
    st.title("💼 YUMOLD VIETNAM Quotation System")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Create Quotation", "📋 Quotation List", "🖨️ Print Quotation", "🔄 Edit Quotation", "📊 Status Management"])
    
    with tab1:
        show_quotation_form()
    
    with tab2:
        show_quotation_list()
    
    with tab3:
        st.info("💡 견적서 프린트를 위해서는 먼저 'Create Quotation' 탭에서 견적서를 생성하세요!")
        show_print_quotation_tab()
    
    with tab4:
        show_quotation_edit()
    
    with tab5:
        show_status_management()
    



def display_quotation_for_print(selected_quote, include_stamp=False):
    """견적서를 화면에 표시하고 프린트할 수 있게 함"""
    try:
        import os
        # 템플릿 파일 읽기
        template_file_path = 'Yumold Temp 01.html'
        if not os.path.exists(template_file_path):
            st.error(f"템플릿 파일이 없습니다: {template_file_path}")
            return
            
        with open(template_file_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 견적서 아이템들 조회
        from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
        quotation_manager = SQLiteQuotationManager()
        
        # 데이터베이스에서 직접 완전한 데이터 재조회
        quotation_id = selected_quote.get('quotation_id')
        if quotation_id:
            import sqlite3
            conn = sqlite3.connect('erp_system.db')
            cursor = conn.cursor()
            
            # 완전한 견적서 정보를 직접 조회
            cursor.execute("SELECT * FROM quotations WHERE quotation_id = ?", (quotation_id,))
            row = cursor.fetchone()
            
            if row:
                # 컬럼 이름 가져오기
                cursor.execute("PRAGMA table_info(quotations)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # row 데이터를 딕셔너리로 변환
                selected_quote = dict(zip(columns, row))
            
            conn.close()
        

        
        items = quotation_manager.get_quotation_items(selected_quote.get('quotation_id', ''))
        
        if isinstance(items, pd.DataFrame) and not items.empty:
            # 아이템 행 생성
            items_html = ""
            for idx, (_, item) in enumerate(items.iterrows()):
                vn_text = item.get('item_name_vn', '')
                
                # 베트남어 텍스트 길이에 따른 클래스 설정
                vn_class = ""
                if len(vn_text) > 80:
                    vn_class = "very-long-text"
                elif len(vn_text) > 50:
                    vn_class = "long-text"
                
                row_number = item.get('line_number', idx + 1)
                
                items_html += f"""
                <tr>
                    <td rowspan="3" style="text-align: center; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; width: 5%; vertical-align: middle;">{row_number}</td>
                    <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 12%;">{item.get('item_code', '')}</td>
                    <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 25%;">{item.get('item_name_en', '')}</td>
                    <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 8%;">{item.get('quantity', 0)}</td>
                    <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 15%;">{item.get('standard_price', 0):,.0f}</td>
                    <td style="text-align: center; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 10%;">{item.get('discount_rate', 0):.1f}%</td>
                    <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; background-color: white; width: 15%;">{item.get('unit_price', 0):,.0f}</td>
                    <td style="text-align: right; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; width: 15%;">{item.get('amount', 0):,.0f}</td>
                </tr>
                <tr>
                    <td colspan="7" style="text-align: left; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white;" class="{vn_class}">VN: {vn_text}</td>
                </tr>
                <tr>
                    <td colspan="7" style="text-align: left; padding: 3px 5px; border: 1px solid #333; border-right: 1px solid white; background-color: white; font-size: 7px;">Remark: {item.get('remark', '')}</td>
                </tr>
                """
            
            # 템플릿에 데이터 삽입
            template_content = template_content.replace('{{quotation_number}}', str(selected_quote.get('quotation_number', '')))
            template_content = template_content.replace('{{quote_date}}', str(selected_quote.get('quote_date', '')))
            template_content = template_content.replace('{{revision_number}}', str(selected_quote.get('revision_number', '00')))
            template_content = template_content.replace('{{currency}}', str(selected_quote.get('currency', 'VND')))
            
            # 고객 정보 - 안전한 값 추출과 빈 값 처리
            customer_company = str(selected_quote.get('customer_company', '') or '')
            customer_address = str(selected_quote.get('customer_address', '') or '')
            customer_contact_person = str(selected_quote.get('customer_contact_person', '') or '')
            customer_phone = str(selected_quote.get('customer_phone', '') or '')
            customer_email = str(selected_quote.get('customer_email', '') or '')
            
            template_content = template_content.replace('{{customer_company}}', customer_company)
            template_content = template_content.replace('{{customer_address}}', customer_address)
            template_content = template_content.replace('{{customer_contact_person}}', customer_contact_person)
            template_content = template_content.replace('{{customer_phone}}', customer_phone)
            template_content = template_content.replace('{{customer_email}}', customer_email)
            
            # 영업 담당자 정보 - 안전한 값 추출
            sales_representative = str(selected_quote.get('sales_representative', '') or '')
            sales_rep_contact = str(selected_quote.get('sales_rep_contact', '') or '')
            sales_rep_email = str(selected_quote.get('sales_rep_email', '') or '')
            
            template_content = template_content.replace('{{sales_representative}}', sales_representative)
            template_content = template_content.replace('{{sales_rep_name}}', sales_representative)  # 동일한 값 매핑
            template_content = template_content.replace('{{sales_rep_phone}}', sales_rep_contact)
            template_content = template_content.replace('{{sales_rep_email}}', sales_rep_email)
            
            # 프로젝트 정보 - 안전한 값 추출과 빈 값 처리
            project_name = str(selected_quote.get('project_name', '') or '')
            part_name = str(selected_quote.get('part_name', '') or '')
            part_weight = str(selected_quote.get('part_weight', '') or '')
            mold_number = str(selected_quote.get('mold_number', '') or '')
            hrs_info = str(selected_quote.get('hrs_info', '') or '')
            resin_type = str(selected_quote.get('resin_type', '') or '')
            resin_additive = str(selected_quote.get('resin_additive', '') or '')
            sol_material = str(selected_quote.get('sol_material', '') or '')
            remark = str(selected_quote.get('remark', '') or '')
            payment_terms = str(selected_quote.get('payment_terms', '') or '')
            valid_date = str(selected_quote.get('valid_date', '') or '')
            delivery_date = str(selected_quote.get('delivery_date', '') or '')
            account = str(selected_quote.get('account', '') or '700-038-038199 (Shinhan Bank Vietnam)')
            
            template_content = template_content.replace('{{project_name}}', project_name)
            template_content = template_content.replace('{{part_name}}', part_name)
            template_content = template_content.replace('{{part_weight}}', part_weight)
            template_content = template_content.replace('{{mold_number}}', mold_number)
            template_content = template_content.replace('{{hrs_info}}', hrs_info)
            template_content = template_content.replace('{{resin_type}}', resin_type)
            template_content = template_content.replace('{{resin_additive}}', resin_additive)
            template_content = template_content.replace('{{sol_material}}', sol_material)
            template_content = template_content.replace('{{remark}}', remark)
            template_content = template_content.replace('{{payment_terms}}', payment_terms)
            template_content = template_content.replace('{{valid_date}}', valid_date)
            template_content = template_content.replace('{{delivery_date}}', delivery_date)
            template_content = template_content.replace('{{account}}', account)
            
            # 스탬프 섹션 처리
            if include_stamp:
                # 실제 스탬프 이미지를 Base64로 인코딩하여 삽입
                import base64
                import os
                stamp_path = 'static/images/company_stamp.png'
                if os.path.exists(stamp_path):
                    with open(stamp_path, 'rb') as f:
                        stamp_data = base64.b64encode(f.read()).decode()
                    stamp_html = f'''
                        <div style="position: absolute; top: -75px; left: 50%; transform: translateX(-50%); z-index: 10;">
                            <img src="data:image/png;base64,{stamp_data}" 
                                 style="width: 180px; height: 180px; opacity: 0.85;" alt="Company Stamp" />
                        </div>
                    '''
                else:
                    # 스탬프 파일이 없을 경우 CSS로 만든 원형 스탬프 (큰 사이즈, 겹치는 위치)
                    stamp_html = '''
                        <div style="position: absolute; top: -75px; left: 50%; transform: translateX(-50%); z-index: 10;">
                            <div style="width: 180px; height: 180px; border: 4px solid #e74c3c; border-radius: 50%;
                                        display: flex; flex-direction: column; justify-content: center;
                                        align-items: center; font-size: 14px; font-weight: bold; color: #e74c3c; text-align: center;
                                        background: rgba(231, 76, 60, 0.1); opacity: 0.85;">
                                <div style="font-size: 12px;">M.S.Đ.N: 011146237</div>
                                <div style="margin: 5px 0; font-size: 14px;">CÔNG TY TNHH</div>
                                <div style="font-size: 18px; margin: 5px 0; font-weight: 900;">YUMOLD</div>
                                <div style="font-size: 14px;">VIỆT NAM</div>
                                <div style="font-size: 10px; margin-top: 5px;">YẾN HÒA - TP. HÀ NỘI</div>
                            </div>
                        </div>
                    '''
                signature_name_display = ''
            else:
                stamp_html = ''
                signature_name_display = ''
                
            template_content = template_content.replace('{{stamp_section}}', stamp_html)
            template_content = template_content.replace('{{signature_name}}', signature_name_display)
            
            # 가격 정보 - 안전한 숫자 변환과 포맷팅
            try:
                vat_percentage = float(selected_quote.get('vat_percentage', 10.0) or 10.0)
                subtotal = float(selected_quote.get('subtotal_excl_vat', 0) or 0)
                vat_amount = float(selected_quote.get('vat_amount', 0) or 0)
                total_incl_vat = float(selected_quote.get('total_incl_vat', 0) or 0)
            except (ValueError, TypeError):
                vat_percentage = 10.0
                subtotal = 0
                vat_amount = 0
                total_incl_vat = 0
            
            template_content = template_content.replace('{{vat_percentage}}', f"{vat_percentage:.1f}")
            template_content = template_content.replace('{{subtotal}}', f"{subtotal:,.0f}")
            template_content = template_content.replace('{{vat_amount}}', f"{vat_amount:,.0f}")
            template_content = template_content.replace('{{total_incl_vat}}', f"{total_incl_vat:,.0f}")
            
            # 아이템 리스트 삽입
            template_content = template_content.replace('{{items_rows}}', items_html)
            
            # 화면에 바로 표시
            st.markdown("### 📄 Quotation Preview")
            
            # HTML을 제대로 렌더링하기 위해 components 사용
            import streamlit.components.v1 as components
            components.html(template_content, height=800, scrolling=True)
            
            st.success("✅ 견적서가 화면에 표시되었습니다. 브라우저의 Ctrl+P로 프린트하세요!")
            
        else:
            st.error("견적서 아이템을 찾을 수 없습니다.")
            
    except Exception as e:
        st.error(f"Error displaying quotation: {e}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()