# -*- coding: utf-8 -*-
"""
납품 확인서 관리 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from managers.sqlite.sqlite_quotation_manager import SQLiteQuotationManager

def show_shipping_page(shipping_manager=None, quotation_manager=None, get_text=lambda x: x):
    """납품 확인서 관리 페이지를 표시합니다."""
    
    st.title("📄 Delivery Confirmation Management")
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "📋 Approved Quotations", 
        "📄 Generate Delivery Confirmation",
        "📊 Delivery History"
    ])
    
    with tab1:
        show_approved_quotations()
    
    with tab2:
        show_delivery_confirmation_generator()
    
    with tab3:
        show_delivery_history()

def show_approved_quotations():
    """승인된 견적서 목록을 표시합니다."""
    st.header("📋 Approved Quotations")
    
    quotation_manager = SQLiteQuotationManager()
    quotations = quotation_manager.get_all_quotations()
    
    if isinstance(quotations, pd.DataFrame) and len(quotations) > 0:
        # 승인된 견적서만 필터링
        approved_quotations = quotations[quotations['quotation_status'] == 'approved']
        
        if len(approved_quotations) > 0:
            st.info(f"📊 Total approved quotations ready for delivery: {len(approved_quotations)}")
            
            # 승인된 견적서 테이블 표시
            display_data = approved_quotations[['quotation_number', 'customer_company', 'quote_date', 'total_incl_vat', 'currency']].copy()
            
            # 금액 포맷
            display_data['total_incl_vat'] = display_data['total_incl_vat'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
            
            # 컬럼명 한글화
            display_data.columns = ['견적서 번호', '고객사', '견적 날짜', '총액', '통화']
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)
            
            # 고객사별 총계
            customer_totals = approved_quotations.groupby('customer_company')['total_incl_vat'].sum().sort_values(ascending=False)
            
            st.markdown("#### 📈 Customer Summary")
            for customer, total in customer_totals.items():
                st.metric(customer, f"{total:,.0f} VND")
                
        else:
            st.warning("No approved quotations found. Quotations must be approved before delivery confirmation can be generated.")
    else:
        st.info("No quotations found in the system.")

def show_delivery_confirmation_generator():
    """납품 확인서 생성기를 표시합니다."""
    st.header("📄 Generate Delivery Confirmation")
    
    quotation_manager = SQLiteQuotationManager()
    quotations = quotation_manager.get_all_quotations()
    
    if isinstance(quotations, pd.DataFrame) and len(quotations) > 0:
        # 승인된 견적서만 필터링
        approved_quotations = quotations[quotations['quotation_status'] == 'approved']
        
        if len(approved_quotations) > 0:
            # 견적서 선택
            quotation_options = []
            for _, quote in approved_quotations.iterrows():
                quotation_options.append(f"{quote['quotation_number']} - {quote['customer_company']}")
            
            selected_quotation = st.selectbox("Select Approved Quotation:", quotation_options)
            
            if selected_quotation:
                quote_number = selected_quotation.split(" - ")[0]
                selected_quote = approved_quotations[approved_quotations['quotation_number'] == quote_number].iloc[0]
                
                # 선택된 견적서 정보 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Customer", selected_quote['customer_company'])
                with col2:
                    st.metric("Total Amount", f"{selected_quote['total_incl_vat']:,.0f} VND")
                with col3:
                    st.metric("Quote Date", selected_quote['quote_date'])
                
                # 납품 정보 입력
                st.markdown("#### 📅 Delivery Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    delivery_date = st.date_input("Delivery Date", datetime.now().date())
                with col2:
                    delivery_person = st.text_input("Delivery Person", "E T.L")
                
                delivery_notes = st.text_area("Delivery Notes (Optional)", placeholder="Enter any special notes about the delivery...")
                
                if st.button("📄 Generate Delivery Confirmation", type="primary", use_container_width=True):
                    generate_delivery_confirmation_document(selected_quote, delivery_date, delivery_person, delivery_notes, quotation_manager)
        else:
            st.warning("No approved quotations available for delivery confirmation.")
    else:
        st.info("No quotations found in the system.")

def generate_delivery_confirmation_document(quote_data, delivery_date, delivery_person, delivery_notes, quotation_manager):
    """납품 확인서 문서를 생성합니다."""
    try:
        # 견적서 아이템들 가져오기
        quote_items = quotation_manager.get_quotation_items(quote_data['quotation_id'])
        
        # HTML 템플릿 생성
        html_content = create_delivery_confirmation_template(quote_data, quote_items, delivery_date, delivery_person, delivery_notes)
        
        # 파일명 생성
        delivery_number = f"DELV-{quote_data['quotation_number']}-{delivery_date.strftime('%Y%m%d')}"
        filename = f"{delivery_number}.html"
        
        # HTML 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        st.success(f"✅ Delivery confirmation generated: {filename}")
        
        # 미리보기 표시
        st.markdown("---")
        st.markdown("### 📋 Delivery Confirmation Preview")
        
        # CSS 기반 미리보기로 변경
        st.markdown(f"""
        <div style="
            border: 2px solid #2E8B57; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 20px 0; 
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-height: 800px; 
            overflow-y: auto;
        ">
        {html_content.replace('<html lang="ko">', '').replace('</html>', '').replace('<body>', '').replace('</body>', '').replace('<head>', '').replace('</head>', '')}
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error generating delivery confirmation: {e}")
        import traceback
        st.code(traceback.format_exc())

def create_delivery_confirmation_template(quote_data, quote_items, delivery_date, delivery_person, delivery_notes):
    """납품 확인서 CSS 템플릿을 생성합니다."""
    
    # 제품 항목들 HTML 생성
    items_rows = ""
    if isinstance(quote_items, pd.DataFrame) and len(quote_items) > 0:
        for idx, (_, item) in enumerate(quote_items.iterrows()):
            items_rows += f"""
            <tr>
                <td style="text-align: center; padding: 12px; border: 1px solid #ddd;">{idx + 1}</td>
                <td style="padding: 12px; border: 1px solid #ddd; font-weight: 500;">{item.get('item_code', '')}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">
                    <strong>{item.get('item_name_en', '')}</strong><br>
                    <small style="color: #666; font-style: italic;">{item.get('item_name_vn', '')}</small>
                </td>
                <td style="text-align: center; padding: 12px; border: 1px solid #ddd; font-weight: 500;">{item.get('quantity', 1)}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{item.get('remark', '')}</td>
            </tr>
            """
    
    # 현재 날짜
    current_date = datetime.now().strftime('%d-%m-%Y')
    delivery_date_str = delivery_date.strftime('%d-%m-%Y')
    
    # CSS 기반 납품 확인서 템플릿
    html_template = f"""
    <style>
        .delivery-document {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 30px;
            background: white;
            line-height: 1.6;
            color: #333;
            border-radius: 10px;
        }}
        
        .header-section {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 40px;
            padding-bottom: 25px;
            border-bottom: 3px solid #2E8B57;
        }}
        
        .customer-info {{
            flex: 1;
            margin-right: 20px;
        }}
        
        .customer-info h3 {{
            color: #2E8B57;
            font-size: 20px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .customer-info div {{
            margin-bottom: 5px;
            font-size: 14px;
        }}
        
        .company-info {{
            text-align: right;
            flex: 1;
        }}
        
        .company-info h2 {{
            color: #2E8B57;
            font-size: 26px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .company-info div {{
            font-size: 14px;
            margin-bottom: 5px;
        }}
        
        .document-title {{
            text-align: center;
            margin: 40px 0;
        }}
        
        .document-title h1 {{
            color: #2E8B57;
            font-size: 36px;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}
        
        .document-title .subtitle {{
            color: #666;
            font-size: 16px;
            font-style: italic;
        }}
        
        .reference-section {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
            margin: 30px 0;
            border-radius: 8px;
            border-left: 5px solid #2E8B57;
        }}
        
        .reference-section div {{
            margin-bottom: 8px;
            font-size: 15px;
        }}
        
        .reference-section strong {{
            color: #2E8B57;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .info-box {{
            background: white;
            padding: 20px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .info-label {{
            font-weight: 600;
            color: #2E8B57;
            font-size: 16px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-box div {{
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .products-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .products-table th {{
            background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
            color: white;
            padding: 15px 12px;
            text-align: center;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 13px;
        }}
        
        .products-table td {{
            padding: 12px;
            border: 1px solid #e9ecef;
            vertical-align: top;
        }}
        
        .products-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .products-table tr:hover {{
            background-color: #e8f5e8;
            transition: background-color 0.2s ease;
        }}
        
        .delivery-notes {{
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border-radius: 8px;
            border-left: 5px solid #ffc107;
        }}
        
        .delivery-notes strong {{
            color: #856404;
            font-size: 16px;
            margin-bottom: 10px;
            display: block;
        }}
        
        .signature-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 50px;
        }}
        
        .signature-card {{
            background: white;
            border: 2px solid #2E8B57;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .signature-title {{
            font-weight: 600;
            color: #2E8B57;
            font-size: 16px;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .signature-line {{
            border-bottom: 2px solid #333;
            height: 80px;
            margin: 25px 0 15px 0;
            position: relative;
        }}
        
        .signature-line::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 20px;
            height: 2px;
            background: #2E8B57;
        }}
        
        .signature-field {{
            margin-bottom: 12px;
            font-size: 14px;
            color: #555;
        }}
        
        .signature-field strong {{
            color: #2E8B57;
        }}
    </style>
    
    <div class="delivery-document">
        <div class="header-section">
            <div class="customer-info">
                <h3>{quote_data['customer_company']}</h3>
                <div><strong>Address:</strong> {quote_data.get('customer_address', 'N/A')}</div>
                <div><strong>Contact:</strong> {quote_data.get('customer_contact_person', 'N/A')}</div>
                <div><strong>Phone:</strong> {quote_data.get('customer_phone', 'N/A')}</div>
                <div><strong>Email:</strong> {quote_data.get('customer_email', 'N/A')}</div>
            </div>
            <div class="company-info">
                <h2>YUMOLD VIETNAM</h2>
                <div>Ho Chi Minh City, Vietnam</div>
                <div>Tel: +84-xxx-xxx-xxxx</div>
                <div>Email: info@yumold.vn</div>
                <div>Website: www.yumold.vn</div>
            </div>
        </div>

        <div class="document-title">
            <h1>DELIVERY CONFIRMATION</h1>
            <div class="subtitle">납품 확인서</div>
        </div>

        <div class="reference-section">
            <div><strong>Reference Quotation:</strong> {quote_data['quotation_number']}</div>
            <div><strong>Original Quote Date:</strong> {quote_data['quote_date']}</div>
            <div><strong>Delivery Confirmation Number:</strong> DELV-{quote_data['quotation_number']}-{delivery_date.strftime('%Y%m%d')}</div>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <div class="info-label">Delivery Information</div>
                <div><strong>Delivery Date:</strong> {delivery_date_str}</div>
                <div><strong>Delivered By:</strong> {delivery_person}</div>
                <div><strong>Document Date:</strong> {current_date}</div>
            </div>
            <div class="info-box">
                <div class="info-label">Customer Information</div>
                <div><strong>Company:</strong> {quote_data['customer_company']}</div>
                <div><strong>Total Value:</strong> {quote_data['total_incl_vat']:,.0f} {quote_data['currency']}</div>
                <div><strong>Status:</strong> Ready for Delivery</div>
            </div>
        </div>

        <table class="products-table">
            <thead>
                <tr>
                    <th style="width: 5%;">No.</th>
                    <th style="width: 15%;">Product Code</th>
                    <th style="width: 45%;">Product Name / Description</th>
                    <th style="width: 10%;">Quantity</th>
                    <th style="width: 25%;">Remarks</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>
        
        {"<div class='delivery-notes'><strong>Delivery Notes:</strong><br>" + delivery_notes + "</div>" if delivery_notes else ""}

        <div class="signature-grid">
            <div class="signature-card">
                <div class="signature-title">Customer Confirmation</div>
                <div class="signature-line"></div>
                <div class="signature-field"><strong>Name:</strong> ________________</div>
                <div class="signature-field"><strong>Position:</strong> ________________</div>
                <div class="signature-field"><strong>Date:</strong> ________________</div>
                <div class="signature-field"><strong>Signature:</strong> ________________</div>
            </div>
            <div class="signature-card">
                <div class="signature-title">YUMOLD Vietnam</div>
                <div class="signature-line"></div>
                <div class="signature-field"><strong>Name:</strong> {delivery_person}</div>
                <div class="signature-field"><strong>Position:</strong> Delivery Representative</div>
                <div class="signature-field"><strong>Date:</strong> {delivery_date_str}</div>
                <div class="signature-field"><strong>Signature:</strong> ________________</div>
            </div>
        </div>
    </div>
    """
    
    return html_template

def show_delivery_history():
    """납품 이력을 표시합니다."""
    st.header("📊 Delivery History")
    
    st.info("💡 This section will track completed deliveries and their confirmation documents.")
    
    # 향후 구현: 납품 완료된 항목들을 별도 테이블로 관리
    st.markdown("""
    ### 🚀 Coming Soon Features:
    - Track completed deliveries
    - Generate delivery reports
    - Customer delivery statistics
    - Delivery confirmation document archive
    """)
    
    # 임시로 모든 견적서 중 완료된 것들 표시
    quotation_manager = SQLiteQuotationManager()
    quotations = quotation_manager.get_all_quotations()
    
    if isinstance(quotations, pd.DataFrame) and len(quotations) > 0:
        completed_quotations = quotations[quotations['quotation_status'] == 'completed']
        
        if len(completed_quotations) > 0:
            st.markdown("#### 📋 Completed Orders (Potential Deliveries)")
            
            display_data = completed_quotations[['quotation_number', 'customer_company', 'quote_date', 'total_incl_vat']].copy()
            display_data['total_incl_vat'] = display_data['total_incl_vat'].apply(lambda x: f"{x:,.0f} VND")
            display_data.columns = ['견적서 번호', '고객사', '견적 날짜', '총액']
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info("No completed orders found.")
    else:
        st.info("No quotations found in the system.")