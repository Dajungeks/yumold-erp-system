"""
문서 인쇄 기능
ERP 시스템의 견적서, 송장, 주문서, 배송증 등 문서 인쇄 지원
"""

import streamlit as st
from datetime import datetime
import pandas as pd

def safe_multiply(a, b):
    """안전한 곱셈 함수 - None 값 처리"""
    try:
        a_val = float(a or 0)
        b_val = float(b or 0)
        return a_val * b_val
    except (ValueError, TypeError):
        return 0

class DocumentPrinter:
    def __init__(self):
        self.company_info = {
            'name': 'HRC Vietnam Co., Ltd.',
            'address': '베트남 하노이시 롱비엔구',
            'phone': '+84-24-1234-5678',
            'email': 'info@hrcvietnam.com',
            'tax_id': 'VN-123456789'
        }
    
    def inject_print_styles(self):
        """인쇄용 CSS 스타일 주입"""
        st.markdown("""
        <style>
        @media print {
            /* 페이지 설정 */
            @page {
                size: A4;
                margin: 1cm;
            }
            
            /* Streamlit 기본 요소 숨기기 */
            .stApp > header,
            .stApp > footer,
            .stSidebar,
            .stToolbar,
            .stDeployButton,
            .print-hide,
            button[kind="primary"],
            button[kind="secondary"],
            .stButton,
            .stSelectbox,
            .stTextInput,
            .stTextArea,
            .stDateInput,
            .stNumberInput {
                display: none !important;
            }
            
            /* 메인 컨테이너 */
            .main .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            
            /* 문서 스타일 */
            .print-document {
                background: white;
                color: black;
                font-family: Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.4;
            }
            
            /* 테이블 스타일 */
            .print-table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            
            .print-table th,
            .print-table td {
                border: 1px solid #000;
                padding: 8px;
                text-align: left;
            }
            
            .print-table th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            
            /* 페이지 분할 방지 */
            .print-no-break {
                page-break-inside: avoid;
            }
            
            /* 헤더 반복 */
            .print-table thead {
                display: table-header-group;
            }
            
            /* 총계 강조 */
            .print-total {
                font-weight: bold;
                border-top: 2px solid #000;
            }
        }
        
        /* 화면용 스타일 */
        .print-document {
            background: white;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        .print-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        
        .company-info h2 {
            margin: 0;
            color: #2c3e50;
        }
        
        .document-info {
            text-align: right;
        }
        
        .print-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .print-table th,
        .print-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        .print-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .print-total {
            font-weight: bold;
            background-color: #e9ecef;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def add_print_button(self, document_type="문서"):
        """인쇄 버튼 추가"""
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(f"🖨️ {document_type} 인쇄", key=f"print_{document_type}", help="브라우저 인쇄 기능을 사용합니다"):
                st.markdown("""
                <script>
                setTimeout(function() { window.print(); }, 100);
                </script>
                """, unsafe_allow_html=True)
                st.success("인쇄 대화상자가 열렸습니다. 브라우저에서 인쇄 설정을 확인하세요.")
    
    def create_invoice_document(self, invoice_data):
        """송장 문서 생성"""
        self.inject_print_styles()
        
        st.markdown(f"""
        <div class="print-document">
            <div class="print-header">
                <div class="company-info">
                    <h2>{self.company_info['name']}</h2>
                    <p>{self.company_info['address']}<br>
                    Tel: {self.company_info['phone']}<br>
                    Email: {self.company_info['email']}<br>
                    Tax ID: {self.company_info['tax_id']}</p>
                </div>
                <div class="document-info">
                    <h2>INVOICE</h2>
                    <p><strong>Invoice No:</strong> {invoice_data.get('invoice_no', 'INV-001')}<br>
                    <strong>Date:</strong> {invoice_data.get('date', datetime.now().strftime('%Y-%m-%d'))}<br>
                    <strong>Due Date:</strong> {invoice_data.get('due_date', 'N/A')}</p>
                </div>
            </div>
            
            <div class="print-no-break">
                <h3>Bill To:</h3>
                <p><strong>{invoice_data.get('customer_name', '고객명')}</strong><br>
                {invoice_data.get('customer_address', '고객 주소')}<br>
                Tel: {invoice_data.get('customer_phone', 'N/A')}<br>
                Email: {invoice_data.get('customer_email', 'N/A')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 항목 테이블
        if 'items' in invoice_data and invoice_data['items']:
            items_df = pd.DataFrame(invoice_data['items'])
            
            st.markdown("""
            <table class="print-table">
                <thead>
                    <tr>
                        <th>항목</th>
                        <th>수량</th>
                        <th>단가</th>
                        <th>금액</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            total_amount = 0
            for _, item in items_df.iterrows():
                amount = safe_multiply(item.get('quantity', 0), item.get('unit_price', 0))
                total_amount += amount
                
                st.markdown(f"""
                    <tr>
                        <td>{item.get('product_name', '')}</td>
                        <td>{item.get('quantity', 0):,}</td>
                        <td>{item.get('unit_price', 0):,.2f}</td>
                        <td>{amount:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                    <tr class="print-total">
                        <td colspan="3"><strong>총 금액</strong></td>
                        <td><strong>{total_amount:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
        
        self.add_print_button("송장")
    
    def create_quotation_document(self, quote_data):
        """견적서 문서 생성"""
        self.inject_print_styles()
        
        st.markdown(f"""
        <div class="print-document">
            <div class="print-header">
                <div class="company-info">
                    <h2>{self.company_info['name']}</h2>
                    <p>{self.company_info['address']}<br>
                    Tel: {self.company_info['phone']}<br>
                    Email: {self.company_info['email']}</p>
                </div>
                <div class="document-info">
                    <h2>견적서 (QUOTATION)</h2>
                    <p><strong>견적번호:</strong> {quote_data.get('quote_no', 'QUO-001')}<br>
                    <strong>작성일:</strong> {quote_data.get('date', datetime.now().strftime('%Y-%m-%d'))}<br>
                    <strong>유효기간:</strong> {quote_data.get('valid_until', 'N/A')}</p>
                </div>
            </div>
            
            <div class="print-no-break">
                <h3>견적 요청처:</h3>
                <p><strong>{quote_data.get('customer_name', '고객명')}</strong><br>
                {quote_data.get('customer_address', '고객 주소')}<br>
                담당자: {quote_data.get('contact_person', 'N/A')}<br>
                Tel: {quote_data.get('customer_phone', 'N/A')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 견적 항목 테이블
        if 'items' in quote_data and quote_data['items']:
            items_df = pd.DataFrame(quote_data['items'])
            
            st.markdown("""
            <table class="print-table">
                <thead>
                    <tr>
                        <th>제품명</th>
                        <th>규격</th>
                        <th>수량</th>
                        <th>단가</th>
                        <th>금액</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            total_amount = 0
            for _, item in items_df.iterrows():
                amount = safe_multiply(item.get('quantity', 0), item.get('unit_price', 0))
                total_amount += amount
                
                st.markdown(f"""
                    <tr>
                        <td>{item.get('product_name', '')}</td>
                        <td>{item.get('specification', '')}</td>
                        <td>{item.get('quantity', 0):,}</td>
                        <td>{item.get('unit_price', 0):,.2f}</td>
                        <td>{amount:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                    <tr class="print-total">
                        <td colspan="4"><strong>견적 총액</strong></td>
                        <td><strong>{total_amount:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
        
        # 견적 조건
        st.markdown(f"""
        <div class="print-no-break">
            <h3>견적 조건</h3>
            <ul>
                <li><strong>납기:</strong> {quote_data.get('delivery_time', '별도 협의')}</li>
                <li><strong>결제조건:</strong> {quote_data.get('payment_terms', '별도 협의')}</li>
                <li><strong>유효기간:</strong> {quote_data.get('valid_until', '견적일로부터 30일')}</li>
                <li><strong>기타사항:</strong> {quote_data.get('notes', '별도 협의 사항 없음')}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        self.add_print_button("견적서")
    
    def create_purchase_order_document(self, po_data):
        """주문서 문서 생성"""
        self.inject_print_styles()
        
        st.markdown(f"""
        <div class="print-document">
            <div class="print-header">
                <div class="company-info">
                    <h2>{self.company_info['name']}</h2>
                    <p>{self.company_info['address']}<br>
                    Tel: {self.company_info['phone']}<br>
                    Email: {self.company_info['email']}</p>
                </div>
                <div class="document-info">
                    <h2>구매 주문서 (PURCHASE ORDER)</h2>
                    <p><strong>주문번호:</strong> {po_data.get('po_no', 'PO-001')}<br>
                    <strong>주문일:</strong> {po_data.get('order_date', datetime.now().strftime('%Y-%m-%d'))}<br>
                    <strong>납기희망일:</strong> {po_data.get('delivery_date', 'N/A')}</p>
                </div>
            </div>
            
            <div class="print-no-break">
                <h3>공급업체:</h3>
                <p><strong>{po_data.get('supplier_name', '공급업체명')}</strong><br>
                {po_data.get('supplier_address', '공급업체 주소')}<br>
                담당자: {po_data.get('supplier_contact', 'N/A')}<br>
                Tel: {po_data.get('supplier_phone', 'N/A')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 주문 항목 테이블
        if 'items' in po_data and po_data['items']:
            items_df = pd.DataFrame(po_data['items'])
            
            st.markdown("""
            <table class="print-table">
                <thead>
                    <tr>
                        <th>품목코드</th>
                        <th>품목명</th>
                        <th>수량</th>
                        <th>단가</th>
                        <th>금액</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            total_amount = 0
            for _, item in items_df.iterrows():
                amount = safe_multiply(item.get('quantity', 0), item.get('unit_price', 0))
                total_amount += amount
                
                st.markdown(f"""
                    <tr>
                        <td>{item.get('product_code', '')}</td>
                        <td>{item.get('product_name', '')}</td>
                        <td>{item.get('quantity', 0):,}</td>
                        <td>{item.get('unit_price', 0):,.2f}</td>
                        <td>{amount:,.2f}</td>
                    </tr>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                    <tr class="print-total">
                        <td colspan="4"><strong>주문 총액</strong></td>
                        <td><strong>{total_amount:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
        
        self.add_print_button("주문서")
    
    def create_delivery_note_document(self, delivery_data):
        """배송증 문서 생성"""
        self.inject_print_styles()
        
        st.markdown(f"""
        <div class="print-document">
            <div class="print-header">
                <div class="company-info">
                    <h2>{self.company_info['name']}</h2>
                    <p>{self.company_info['address']}<br>
                    Tel: {self.company_info['phone']}</p>
                </div>
                <div class="document-info">
                    <h2>배송증 (DELIVERY NOTE)</h2>
                    <p><strong>배송번호:</strong> {delivery_data.get('delivery_no', 'DEL-001')}<br>
                    <strong>배송일:</strong> {delivery_data.get('delivery_date', datetime.now().strftime('%Y-%m-%d'))}<br>
                    <strong>운송업체:</strong> {delivery_data.get('carrier', 'N/A')}</p>
                </div>
            </div>
            
            <div class="print-no-break">
                <h3>배송지:</h3>
                <p><strong>{delivery_data.get('customer_name', '고객명')}</strong><br>
                {delivery_data.get('delivery_address', '배송 주소')}<br>
                연락처: {delivery_data.get('contact_phone', 'N/A')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 배송 품목 테이블
        if 'items' in delivery_data and delivery_data['items']:
            items_df = pd.DataFrame(delivery_data['items'])
            
            st.markdown("""
            <table class="print-table">
                <thead>
                    <tr>
                        <th>품목명</th>
                        <th>수량</th>
                        <th>단위</th>
                        <th>포장</th>
                        <th>비고</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            for _, item in items_df.iterrows():
                st.markdown(f"""
                    <tr>
                        <td>{item.get('product_name', '')}</td>
                        <td>{item.get('quantity', 0):,}</td>
                        <td>{item.get('unit', '')}</td>
                        <td>{item.get('packaging', '')}</td>
                        <td>{item.get('notes', '')}</td>
                    </tr>
                """, unsafe_allow_html=True)
            
            st.markdown("""
                </tbody>
            </table>
            """, unsafe_allow_html=True)
        
        # 서명란
        st.markdown("""
        <div class="print-no-break" style="margin-top: 40px;">
            <table class="print-table">
                <tr>
                    <td style="width: 50%; text-align: center; padding: 30px;">
                        <strong>발송자 서명</strong><br><br>
                        날짜: _______________
                    </td>
                    <td style="width: 50%; text-align: center; padding: 30px;">
                        <strong>수령자 서명</strong><br><br>
                        날짜: _______________
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        self.add_print_button("배송증")