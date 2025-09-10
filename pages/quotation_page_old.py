"""
견적서 관리 페이지 - 새로운 제품 연동 시스템
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager
from managers.sqlite.sqlite_customer_manager import SQLiteCustomerManager
from managers.sqlite.sqlite_master_product_manager import SQLiteMasterProductManager
from managers.sqlite.sqlite_exchange_rate_manager import SQLiteExchangeRateManager

def get_exchange_rate():
    """현재 환율 정보 가져오기"""
    try:
        exchange_manager = SQLiteExchangeRateManager()
        current_year = datetime.now().year
        
        # 연도별 관리 환율 조회 (메서드가 존재하는지 확인)
        try:
            # 메서드가 존재하면 호출
            rate_method = getattr(exchange_manager, 'get_yearly_management_rate', None)
            if rate_method:
                rate_data = rate_method('USD', current_year)
                if rate_data:
                    return rate_data.get('rate_vnd_per_usd', 24500)
        except:
            pass
        
        # 실시간 환율 조회
        live_rates = exchange_manager.get_latest_rates()
        if isinstance(live_rates, pd.DataFrame) and len(live_rates) > 0:
            usd_rate = live_rates[live_rates['currency_code'] == 'USD']
            if len(usd_rate) > 0:
                return usd_rate.iloc[0]['rate_to_usd']
    except:
        pass
    
    return 24500  # 기본값

def show_quotation_form():
    """New quotation creation form"""
    st.subheader("📝 Create New Quotation")
    
    quotation_manager = SQLiteQuotationManager()
    customer_manager = SQLiteCustomerManager()
    product_manager = SQLiteMasterProductManager()
    
    # Simple customer input (no database connection needed)
    
    # Customer information input (outside form)
    st.markdown("#### 📋 Quotation Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Direct customer information input
        customer_name = st.text_input("Company Name", key="customer_name")
        contact_person = st.text_input("Contact Person", key="contact_person")
        customer_phone = st.text_input("Phone", key="customer_phone")
        customer_email = st.text_input("Email", key="customer_email")
        

        
        # Quote date and validity period
        quote_date = st.date_input("Quote Date", value=datetime.now().date())
        valid_until = st.date_input("Valid Until", value=(datetime.now() + timedelta(days=30)).date())
    
    with col2:
        st.markdown("##### Quote Conditions Setup")
    
    # Quotation details form
    with st.form("new_quotation_form"):
        # Delivery setup (TBD/Days after PO)
        delivery_type = st.radio("Delivery", ["TBD", "Days after PO"], key="delivery_type")
        if delivery_type == "Days after PO":
            delivery_days = st.number_input("Days after PO", min_value=1, max_value=365, value=30, key="delivery_days")
            delivery_period = f"{delivery_days} days after PO"
        else:
            delivery_period = "TBD"
        
        # Payment terms setup
        payment_type = st.selectbox("Payment Terms", [
            "Under negotiation", 
            "100% T/T in advance", 
            "Custom Split Payment",
            "Net payment after invoice",
            "Custom input"
        ], key="payment_type")
        
        payment_details = {}
        payment_terms = payment_type
        
        if payment_type == "Custom Split Payment":
            st.markdown("##### Split Payment Setup")
            
            # Split type selection
            split_template = st.selectbox("Split Template", [
                "30% deposit, 70% before shipment",
                "Custom percentage"
            ], key="split_template")
            
            if split_template == "30% deposit, 70% before shipment":
                po_percentage = 30.0
                delivery_percentage = 70.0
                st.info("💡 Default template: 30% deposit, 70% before shipment")
            else:
                col_payment1, col_payment2 = st.columns(2)
                with col_payment1:
                    po_percentage = st.number_input("First payment (%)", min_value=0.0, max_value=100.0, value=30.0, step=5.0, key="po_percentage")
                with col_payment2:
                    delivery_percentage = st.number_input("Second payment (%)", min_value=0.0, max_value=100.0, value=70.0, step=5.0, key="delivery_percentage")
            
            # Percentage total check
            total_percentage = po_percentage + delivery_percentage
            if total_percentage != 100:
                st.warning(f"⚠️ Split ratio total: {total_percentage}% (Must be 100%)")
            else:
                st.success(f"✅ Split ratio: {po_percentage}% + {delivery_percentage}% = 100%")
            
            payment_details = {
                "po_percentage": po_percentage,
                "delivery_percentage": delivery_percentage
            }
            payment_terms = f"{po_percentage}% deposit, {delivery_percentage}% before shipment"
            
        elif payment_type == "Net payment after invoice":
            net_days = st.number_input("Payment due (days)", min_value=1, max_value=365, value=30, step=5, key="net_days")
            payment_terms = f"Net {net_days} days after invoice date"
            payment_details = {"net_days": net_days}
            
        elif payment_type == "Custom input":
            custom_payment = st.text_area("Custom Payment Terms", 
                                        placeholder="e.g., 50% upon order confirmation, 50% upon delivery\nor L/C at sight\nor other special conditions", 
                                        height=80, key="custom_payment")
            payment_terms = custom_payment if custom_payment else "Under negotiation"
            payment_details = {"custom_text": custom_payment}
        
        # Information section
        st.markdown("##### Information")
        
        # Common information
        common_info = st.text_area("Common Information", placeholder="Enter common quotation information", height=60, key="common_info")
        
        # Basic information
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            resin_1 = st.text_input("Resin 1", placeholder="e.g., PVC")
            solenoid_voltage = st.selectbox("Solenoid", ["DC24V", "AC220V"], index=0)
        with col2_2:
            resin_2 = st.text_input("Resin 2", placeholder="e.g., ABS")
            mold_no = st.text_input("Mold No", placeholder="Mold number")
        
        project_name = st.text_input("Product Name & Project", placeholder="Project name")
        
        # Product addition section
        st.markdown("#### 📦 Add Products")
        
        # Get product list
        products_df = product_manager.get_master_products()
        product_options = ["Select Product..."]
        
        if isinstance(products_df, pd.DataFrame) and len(products_df) > 0:
            for _, product in products_df.iterrows():
                product_code = product.get('product_code', 'N/A')
                product_name_en = product.get('product_name_en', 'N/A')
                product_options.append(f"{product_code} - {product_name_en}")
        
        # Product selection and information display
        if 'quotation_items' not in st.session_state:
            st.session_state.quotation_items = []
        
        col3, col4 = st.columns([2, 1])
        
        with col3:
            selected_product = st.selectbox("Product Code", product_options, key="product_select")
            
            # Display selected product information
            if selected_product != "Select Product...":
                product_code = selected_product.split(' - ')[0]
                product_data = products_df[products_df['product_code'] == product_code]
                product_info = product_data.iloc[0].to_dict() if len(product_data) > 0 else {}
                
                if len(product_info) > 0:
                    st.success("✅ Auto-loaded Information:")
                    st.write(f"• English Name: {product_info.get('product_name_en', 'N/A')}")
                    st.write(f"• Vietnamese Name: {product_info.get('product_name_vi', 'N/A')}")
                    st.write(f"• Sales Price: {product_info.get('sales_price_vnd', 0):,.0f} VND")
        
        with col4:
            if selected_product != "Select Product...":
                product_code = selected_product.split(' - ')[0]
                product_data = products_df[products_df['product_code'] == product_code]
                product_info = product_data.iloc[0].to_dict() if len(product_data) > 0 else {}
                
                if len(product_info) > 0:
                    quantity = st.number_input("Quantity", min_value=1, value=1, key="quantity")
                    unit = st.selectbox("Unit", ["EA", "SET", "PCS", "KG"], index=0, key="unit")
                    discount_rate = st.number_input("Discount Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="discount")
                    
                    # Part Name and Part Weight
                    part_name = st.text_input("Part Name", placeholder="Part name", key="part_name")
                    part_weight = st.number_input("Part Weight (kg)", min_value=0.0, value=0.0, step=0.1, key="part_weight")
                    
                    remark = st.text_area("Remark (200 chars)", max_chars=200, height=80, key="remark")
                    
                    # Add product button (using form_submit_button)
                    add_product = st.form_submit_button("Add Product", type="primary")
                    if add_product:
                        unit_price = float(product_info.get('sales_price_vnd', 0))
                        line_total = quantity * unit_price * (1 - discount_rate / 100)
                        
                        item_data = {
                            'line_number': len(st.session_state.quotation_items) + 1,
                            'product_code': product_code,
                            'product_name_en': product_info.get('product_name_en', ''),
                            'product_name_vi': product_info.get('product_name_vi', ''),
                            'quantity': quantity,
                            'unit': unit,
                            'unit_price': unit_price,
                            'discount_rate': discount_rate,
                            'line_total': line_total,
                            'part_name': part_name,
                            'part_weight': part_weight,
                            'remark': remark
                        }
                        
                        st.session_state.quotation_items.append(item_data)
                        st.success("Product added successfully!")
                        st.rerun()
        
        # Display added products list
        if st.session_state.quotation_items:
            st.markdown("#### 📋 Added Products List")
            
            # Product list table
            items_data = []
            for i, item in enumerate(st.session_state.quotation_items):
                part_info = ""
                if item.get('part_name'):
                    part_info += f"Part Name: {item['part_name']}\n"
                if item.get('part_weight', 0) > 0:
                    part_info += f"Part Weight: {item['part_weight']} kg\n"
                if item.get('remark'):
                    part_info += f"Remark: {item['remark']}"
                
                items_data.append({
                    'Item': item['line_number'],
                    'Product Code': item['product_code'],
                    'Product Name': f"{item['product_name_en']}\n{item['product_name_vi']}",
                    'Part Info': part_info.strip() if part_info.strip() else "N/A",
                    'Quantity': f"{item['quantity']} {item['unit']}",
                    'Unit Price': f"{item['unit_price']:,.0f} VND",
                    'Discount': f"{item['discount_rate']}%",
                    'Amount': f"{item['line_total']:,.0f} VND"
                })
            
            if items_data:
                df_display = pd.DataFrame(items_data)
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Save button
        submitted = st.form_submit_button("💾 Save Quotation", type="primary")
        
        if submitted:
            if not st.session_state.quotation_items:
                st.error("Please add at least one product.")
                return
            
            # Customer information handling - simple direct input
            if not customer_name.strip():
                st.error("Please enter company name.")
                return
            
            # Generate simple customer ID
            customer_id = f"CUST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Amount calculation (tax removed)
            subtotal = sum(item['line_total'] for item in st.session_state.quotation_items)
            total_amount = subtotal  # Subtotal equals total amount without tax
            exchange_rate = get_exchange_rate()
            usd_reference = total_amount / exchange_rate
            
            # Prepare quotation data
            quotation_data = {
                'quotation_date': quote_date.isoformat(),
                'validity_date': valid_until.isoformat(),
                'quotation_status': 'draft',
                'employee_id': st.session_state.get('user_info', {}).get('user_id', 'admin'),
                'customer_id': customer_id,
                'customer_contact_person': contact_person,
                'customer_phone': customer_phone,
                'customer_email': customer_email,
                'delivery_period': delivery_period,
                'payment_terms': payment_terms,
                'payment_details': json.dumps(payment_details) if payment_details else '',
                'resin_1': resin_1,
                'resin_2': resin_2,
                'solenoid_voltage': solenoid_voltage,
                'mold_no': mold_no,
                'project_name': project_name,
                'common_info': common_info,
                'subtotal': subtotal,
                'total_amount': total_amount,
                'currency': 'VND',
                'exchange_rate': exchange_rate,
                'usd_reference': usd_reference
            }
            
            try:
                # Create quotation
                quotation_id, quotation_number = quotation_manager.create_quotation(quotation_data)
                
                # Add product lines
                for item in st.session_state.quotation_items:
                    item_data = {
                        'product_code': item['product_code'],
                        'product_base_info': {
                            'product_name_en': item['product_name_en'],
                            'product_name_vi': item['product_name_vi']
                        },
                        'custom_product_info': {
                            'quantity': item['quantity'],
                            'unit': item['unit'],
                            'discount_rate': item['discount_rate']
                        },
                        'pricing_info': {
                            'unit_price': item['unit_price'],
                            'line_total': item['line_total']
                        },
                        'part_info': {
                            'part_name': item.get('part_name', ''),
                            'part_weight': item.get('part_weight', 0)
                        },
                        'line_notes': item['remark']
                    }
                    quotation_manager.add_quotation_item(quotation_id, item_data)
                
                st.success(f"✅ Quotation saved successfully! Quote Number: {quotation_number}")
                
                # Reset session
                st.session_state.quotation_items = []
                st.rerun()
            except Exception as e:
                st.error(f"Error saving quotation: {e}")

    # Product list delete function (outside form)
    if st.session_state.quotation_items:
        col_clear = st.columns([3, 1])
        with col_clear[1]:
            if st.button("🗑️ Clear All", type="secondary"):
                st.session_state.quotation_items = []
                st.rerun()

    # Amount calculation (executed outside form) - tax removed
    if st.session_state.quotation_items:
        subtotal = sum(item['line_total'] for item in st.session_state.quotation_items)
        total_amount = subtotal  # Subtotal equals total amount without tax
        
        # Exchange rate information
        exchange_rate = get_exchange_rate()
        usd_reference = total_amount / exchange_rate
        
        st.markdown("##### 💰 Amount Calculation")
        col5, col6 = st.columns([1, 1])
        with col5:
            st.info("💱 Exchange Rate Info")
            st.write(f"VND/USD: {exchange_rate:,.1f}")
            st.write(f"USD Reference: ${usd_reference:,.2f}")
        with col6:
            st.success("💰 Total Amount")
            st.write(f"**Total Amount: {total_amount:,.0f} VND**")
            st.write(f"(Tax excluded)")

def show_quotation_list():
    """Quotation list inquiry"""
    st.subheader("📊 Quotation List")
    
    quotation_manager = SQLiteQuotationManager()
    quotations_df = quotation_manager.get_all_quotations()
    
    if isinstance(quotations_df, pd.DataFrame) and len(quotations_df) > 0:
        # Filtering options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Status Filter", ["All", "draft", "sent", "approved", "ordered"])
        
        with col2:
            year_options = ["All"] + [str(year) for year in range(2020, 2030)]
            year_filter = st.selectbox("Year Filter", year_options)
        
        with col3:
            search_term = st.text_input("Search", placeholder="Quote number, customer name...")
        
        # Apply filters
        filtered_df = quotations_df.copy()
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['quotation_status'] == status_filter]
        
        if year_filter != "All" and isinstance(filtered_df, pd.DataFrame):
            try:
                date_mask = filtered_df['quotation_date'].astype(str).str.contains(year_filter, na=False)
                filtered_df = filtered_df[date_mask]
            except:
                pass
        
        if search_term and isinstance(filtered_df, pd.DataFrame):
            try:
                number_mask = filtered_df['quotation_number'].astype(str).str.contains(search_term, case=False, na=False)
                customer_mask = filtered_df['customer_id'].astype(str).str.contains(search_term, case=False, na=False)
                filtered_df = filtered_df[number_mask | customer_mask]
            except:
                pass
        
        # Display list
        if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) > 0:
            try:
                display_df = filtered_df[['quotation_number', 'customer_id', 'total_amount', 'quotation_status', 'quotation_date']].copy()
                display_df.columns = ['Quote Number', 'Customer', 'Total Amount (VND)', 'Status', 'Date']
                if isinstance(display_df, pd.DataFrame) and 'Total Amount (VND)' in display_df.columns:
                    display_df['Total Amount (VND)'] = display_df['Total Amount (VND)'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x != 0 else "0")
            except Exception as e:
                st.error(f"Data processing error: {e}")
                display_df = pd.DataFrame()
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Statistical information
            col4, col5, col6, col7 = st.columns(4)
            
            with col4:
                st.metric("Total Quotes", len(filtered_df))
            
            with col5:
                total_amount = filtered_df['total_amount'].sum()
                st.metric("Total Amount", f"{total_amount:,.0f} VND")
            
            with col6:
                avg_amount = filtered_df['total_amount'].mean()
                st.metric("Average Amount", f"{avg_amount:,.0f} VND")
            
            with col7:
                approved_count = len(filtered_df[filtered_df['quotation_status'] == 'approved'])
                approval_rate = (approved_count / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
                st.metric("승인율", f"{approval_rate:.1f}%")
        
        else:
            st.info("조건에 맞는 견적서가 없습니다.")
    
    else:
        st.info("등록된 견적서가 없습니다.")

def show_quotation_print_section():
    """견적서 인쇄 섹션"""
    st.subheader("🖨️ 견적서 인쇄")
    
    quotation_manager = SQLiteQuotationManager()
    quotations_df = quotation_manager.get_all_quotations()
    
    if isinstance(quotations_df, pd.DataFrame) and len(quotations_df) > 0:
        quotation_options = {}
        for _, quot in quotations_df.iterrows():
            display_text = f"{quot.get('quotation_number', 'N/A')} - {quot.get('customer_id', 'N/A')}"
            quotation_options[display_text] = quot.get('quotation_id')
        
        if quotation_options:
            selected_quotation = st.selectbox("인쇄할 견적서 선택:", list(quotation_options.keys()))
            
            if selected_quotation:
                quotation_id = quotation_options[selected_quotation]
                show_quotation_print_view(quotation_id)
        else:
            st.info("인쇄할 견적서가 없습니다.")
    else:
        st.info("등록된 견적서가 없습니다.")

def show_quotation_print_view(quotation_id):
    """견적서 인쇄 뷰"""
    quotation_manager = SQLiteQuotationManager()
    
    # 견적서 기본 정보
    quotation = quotation_manager.get_quotation_by_id(quotation_id)
    if not quotation:
        st.error("견적서를 찾을 수 없습니다.")
        return
    
    # 견적서 라인 아이템
    items = quotation_manager.get_quotation_items(quotation_id)
    
    # CSS 스타일
    st.markdown("""
    <style>
    .print-container {
        background: white;
        padding: 30px;
        border: 1px solid #ddd;
        border-radius: 10px;
        margin: 20px 0;
    }
    .company-header {
        text-align: center;
        border-bottom: 3px solid #2E7D32;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }
    .quotation-title {
        color: #2E7D32;
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .info-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 4px solid #2E7D32;
    }
    .total-section {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        border: 2px solid #2E7D32;
    }
    .product-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    .product-table th, .product-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .product-table th {
        background-color: #2E7D32;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 인쇄용 컨테이너
    st.markdown("""
    <div class="print-container">
    <div class="company-header">
        <h1 class="quotation-title">QUOTATION / 견적서</h1>
        <p><strong>YMK Vietnam Co., Ltd.</strong></p>
        <p>📧 contact@ymk.vn | 📞 +84-xxx-xxx-xxxx</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 회사 정보와 고객 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="info-section">
        <h4>고객정보 / Thông tin khách hàng:</h4>
        <p><strong>회사명:</strong> {quotation.get('customer_id', 'N/A')}</p>
        <p><strong>담당자:</strong> {quotation.get('customer_contact_person', 'N/A')}</p>
        <p><strong>연락처:</strong> {quotation.get('customer_phone', 'N/A')}</p>
        <p><strong>이메일:</strong> {quotation.get('customer_email', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="info-section">
        <h4>Quote Information:</h4>
        <p><strong>Quote Number:</strong> {quotation.get('quotation_number', 'N/A')}</p>
        <p><strong>Quote Date:</strong> {quotation.get('quotation_date', 'N/A')}</p>
        <p><strong>Valid Until:</strong> {quotation.get('validity_date', 'N/A')}</p>
        <p><strong>Delivery:</strong> {quotation.get('delivery_period', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 공통정보 섹션 (새로 추가된 필드)
    if quotation.get('common_info'):
        st.markdown(f"""
        <div class="info-section">
        <h4>Common Information:</h4>
        <p>{quotation.get('common_info', '')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Information 섹션
    st.markdown(f"""
    <div class="info-section">
    <h4>Information:</h4>
    <p>• Resin 1: {quotation.get('resin_1', 'N/A')} • Resin 2: {quotation.get('resin_2', 'N/A')}</p>
    <p>• Solenoid: {quotation.get('solenoid_voltage', 'DC24V')} • Mold No: {quotation.get('mold_no', 'N/A')}</p>
    <p>• Project Name: {quotation.get('project_name', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 제품 목록 테이블
    if isinstance(items, pd.DataFrame) and len(items) > 0:
        st.markdown("### 📦 Product List")
        
        table_html = """
        <table class="product-table">
        <thead>
            <tr>
                <th>Item</th>
                <th>Product Code</th>
                <th>Product Name</th>
                <th>Part Info</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for _, item in items.iterrows():
            # Part 정보 구성
            part_info_list = []
            if item.get('part_info'):
                try:
                    part_info = json.loads(item.get('part_info', '{}')) if isinstance(item.get('part_info'), str) else (item.get('part_info') or {})
                    if part_info and part_info.get('part_name'):
                        part_info_list.append(f"Part Name: {part_info['part_name']}")
                    if part_info and part_info.get('part_weight', 0) > 0:
                        part_info_list.append(f"Weight: {part_info['part_weight']} kg")
                except:
                    pass
            
            if item.get('line_notes'):
                part_info_list.append(f"Remark: {item['line_notes']}")
            
            part_info_display = "<br>".join(part_info_list) if part_info_list else "N/A"
            
            # 제품 기본 정보
            product_info = item.get('product_base_info', {})
            if isinstance(product_info, str):
                try:
                    product_info = json.loads(product_info)
                except:
                    product_info = {}
            
            product_names = f"{(product_info or {}).get('product_name_en', 'N/A')}<br>{(product_info or {}).get('product_name_vi', 'N/A')}"
            
            # 커스텀 제품 정보
            custom_info = item.get('custom_product_info', {})
            if isinstance(custom_info, str):
                try:
                    custom_info = json.loads(custom_info)
                except:
                    custom_info = {}
            
            # 가격 정보
            pricing_info = item.get('pricing_info', {})
            if isinstance(pricing_info, str):
                try:
                    pricing_info = json.loads(pricing_info)
                except:
                    pricing_info = {}
            
            quantity = (custom_info or {}).get('quantity', 1)
            unit = (custom_info or {}).get('unit', 'EA')
            unit_price = (pricing_info or {}).get('unit_price', 0)
            line_total = (pricing_info or {}).get('line_total', 0)
            
            table_html += f"""
            <tr>
                <td>{item.get('line_number', 'N/A')}</td>
                <td>{item.get('product_code', 'N/A')}</td>
                <td>{product_names}</td>
                <td>{part_info_display}</td>
                <td>{quantity} {unit}</td>
                <td>{unit_price:,.0f} VND</td>
                <td>{line_total:,.0f} VND</td>
            </tr>
            """
        
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
    
    # Amount calculation (tax excluded)
    st.markdown(f"""
    <div class="total-section">
    <h4>Amount Calculation:</h4>
    <p><strong>• Total Amount: {quotation.get('total_amount', 0):,.0f} VND</strong></p>
    <p>• USD Reference: ${quotation.get('usd_reference', 0):,.2f} USD</p>
    <p>• Exchange Rate: {quotation.get('exchange_rate', 24500):,.1f} VND/USD</p>
    <p><em>* Tax excluded</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Terms (including payment details)
    payment_details_text = ""
    try:
        payment_details_json = quotation.get('payment_details', '{}')
        payment_details = json.loads(payment_details_json) if payment_details_json else {}
        if payment_details:
            payment_details_text = f"<br>  - At PO: {payment_details.get('po_percentage', 0)}%<br>  - Upon delivery: {payment_details.get('delivery_percentage', 0)}%"
    except:
        pass
    
    st.markdown(f"""
    <div class="info-section">
    <h4>Quotation Terms:</h4>
    <p>• Delivery: {quotation.get('delivery_period', 'TBD')}</p>
    <p>• Payment Terms: {quotation.get('payment_terms', 'Under negotiation')}{payment_details_text}</p>
    <p>• Shipping: Customer designated location</p>
    <p>• Installation: Separate negotiation</p>
    <p>• Price excludes tax</p>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Print button
    st.markdown("---")
    if st.button("🖨️ Print (Ctrl+P)", type="primary"):
        st.info("💡 Press Ctrl+P to use browser print function.")

def main():
    """Main function"""
    st.title("📋 Quotation Management System")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📝 Create New Quotation", "📊 Quotation List", "🖨️ Print Quotation"])
    
    with tab1:
        show_quotation_form()
    
    with tab2:
        show_quotation_list()
    
    with tab3:
        show_quotation_print_section()

if __name__ == "__main__":
    main()