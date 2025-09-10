# -*- coding: utf-8 -*-
"""
ERP 다국어 문서 출력 시스템
- 송장, 견적서, 발주서, 출고서 출력
- 한국어/영어/베트남어 완전 지원
- 실시간 DB 연동
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime

def show_document_print_page(get_text):
    """다국어 문서 출력 페이지"""
    
    # A4 1장 최적화 CSS
    st.markdown("""
    <style>
    /* A4 1장 최적화 레이아웃 */
    .document-print-container {
        max-width: 210mm;
        margin: 0 auto;
        background: white;
        padding: 10mm;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        font-family: 'Arial', sans-serif;
        font-size: 10px;
        line-height: 1.2;
    }
    
    .document-header {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #333;
    }
    
    .company-section h3 {
        font-size: 14px;
        margin-bottom: 5px;
        color: #333;
    }
    
    .company-details {
        font-size: 9px;
        line-height: 1.3;
        color: #666;
    }
    
    .document-info {
        text-align: right;
    }
    
    .document-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
    }
    
    .doc-meta {
        font-size: 9px;
        line-height: 1.4;
    }
    
    .info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
    }
    
    .info-box {
        border: 1px solid #ddd;
        padding: 8px;
        border-radius: 3px;
    }
    
    .info-box h4 {
        font-size: 11px;
        margin-bottom: 5px;
        color: #333;
        border-bottom: 1px solid #eee;
        padding-bottom: 3px;
    }
    
    .info-row {
        display: grid;
        grid-template-columns: 70px 1fr;
        gap: 5px;
        margin-bottom: 3px;
        font-size: 9px;
    }
    
    .info-label {
        font-weight: bold;
        color: #666;
    }
    
    .compact-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 8px;
    }
    
    .compact-table th {
        background: #f8f9fa;
        border: 1px solid #333;
        padding: 4px 3px;
        text-align: center;
        font-weight: bold;
        font-size: 8px;
    }
    
    .compact-table td {
        border: 1px solid #333;
        padding: 3px;
        text-align: center;
        font-size: 8px;
    }
    
    .compact-table td:nth-child(2),
    .compact-table td:nth-child(3) {
        text-align: left;
    }
    
    .summary-section {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 15px;
        margin-top: 10px;
    }
    
    .total-box {
        border: 1px solid #333;
        padding: 8px;
        background: #f8f9fa;
        min-width: 200px;
    }
    
    .total-row {
        display: grid;
        grid-template-columns: 100px 1fr;
        gap: 5px;
        margin-bottom: 3px;
        font-size: 9px;
    }
    
    .total-final {
        font-weight: bold;
        background: #333;
        color: white;
        padding: 3px;
        border-radius: 2px;
    }
    
    /* 프린트 전용 CSS */
    @media print {
        /* Streamlit 요소 숨김 */
        .css-1d391kg, .css-1cypcdb, .css-17eq0hr, .css-1rs6os, .css-1vq4p4l,
        .css-1kyxreq, .st-emotion-cache-1cypcdb, .st-emotion-cache-17eq0hr,
        [data-testid="stSidebar"], [data-testid="stSidebarNav"],
        section[data-testid="stSidebar"], .print-button-container,
        .control-section, .stSelectbox, .stButton, .stDivider {
            display: none !important;
        }
        
        /* 메인 컨텐츠 전체 폭 */
        .main .block-container {
            padding: 0 !important;
            max-width: none !important;
            margin: 0 !important;
        }
        
        /* A4 페이지 설정 */
        @page {
            size: A4;
            margin: 15mm;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-size: 10px;
            line-height: 1.2;
        }
        
        .document-print-container {
            max-width: none;
            margin: 0;
            padding: 0;
            box-shadow: none;
            background: white;
            height: auto;
            max-height: 257mm;
            overflow: hidden;
        }
        
        /* 테이블 페이지 분할 방지 */
        .compact-table {
            page-break-inside: avoid;
        }
        
        /* 서명란 페이지 분할 방지 */
        .summary-section {
            page-break-inside: avoid;
        }
    }
    
    /* 프린트 버튼 */
    .print-button-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    
    .print-button {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    
    .control-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 프린트 버튼 JavaScript
    st.markdown("""
    <div class="print-button-container">
        <button class="print-button" onclick="window.print()">
            🖨️ 화면 출력
        </button>
    </div>
    """, unsafe_allow_html=True)
    
    st.title(f"🖨️ {get_text('document_print_system')}")
    st.markdown(get_text('document_print_desc'))
    
    # 세션 상태에서 매니저들 가져오기 (디버깅용 메시지)
    available_managers = []
    for key in st.session_state.keys():
        if isinstance(key, str) and 'manager' in key:
            available_managers.append(key)
    
    # 기존 ERP 시스템의 매니저들 사용
    customer_manager = None
    system_config_manager = None
    quotation_manager = None
    order_manager = None
    
    # 다양한 가능한 매니저 키 확인
    for key in st.session_state.keys():
        if isinstance(key, str):  # 문자열 키만 처리
            if 'customer' in key.lower() and 'manager' in key.lower():
                customer_manager = st.session_state[key]
            elif 'config' in key.lower() and 'manager' in key.lower():
                system_config_manager = st.session_state[key]
            elif 'quotation' in key.lower() and 'manager' in key.lower():
                quotation_manager = st.session_state[key]
            elif 'order' in key.lower() and 'manager' in key.lower():
                order_manager = st.session_state[key]
    
    # 디버깅 정보
    if not customer_manager:
        st.warning("고객 매니저를 찾을 수 없습니다. 기본 데이터를 사용합니다.")
    if not system_config_manager:
        st.warning("시스템 설정 매니저를 찾을 수 없습니다. 기본 설정을 사용합니다.")
    
    # 회사 정보 로드
    company_data = get_company_data(system_config_manager, get_text)
    
    # 고객 목록 로드
    customers_data = get_customers_data(customer_manager, get_text)
    
    # 견적서 및 주문 데이터 로드 (JSON 직렬화 안전)
    quotations_data = get_quotations_data(quotation_manager, get_text) if quotation_manager else []
    orders_data = get_orders_data(order_manager, get_text) if order_manager else []
    
    # 데이터 안전성 확인
    quotations_data = quotations_data if isinstance(quotations_data, list) else []
    orders_data = orders_data if isinstance(orders_data, list) else []
    
    # 문서 출력 제어 섹션
    with st.container():
        st.markdown('<div class="control-section">', unsafe_allow_html=True)
        st.subheader("📄 문서 선택 및 검색")
        
        # 1단계: 문서 타입 선택
        col1, col2, col3 = st.columns(3)
        
        with col1:
            doc_type = st.selectbox(
                '문서 타입',
                ['견적서', '발주서', '출고서', '지출요청서'],
                key='doc_type_select'
            )
        
        with col2:
            search_mode = st.selectbox(
                '데이터 선택',
                ['새 문서 작성', '기존 문서 검색'],
                key='search_mode'
            )
        
        with col3:
            if search_mode == '기존 문서 검색':
                # 문서번호 검색
                if doc_type == '견적서':
                    doc_numbers = get_quotation_numbers(quotation_manager)
                    prefix = 'Q'
                elif doc_type == '발주서':
                    doc_numbers = get_order_numbers(order_manager)
                    prefix = 'PO'
                elif doc_type == '출고서':
                    doc_numbers = get_delivery_numbers()
                    prefix = 'DN'
                else:  # 지출요청서
                    doc_numbers = get_expense_numbers()
                    prefix = 'EX'
                
                if doc_numbers:
                    selected_doc = st.selectbox(
                        f'{doc_type} 번호',
                        doc_numbers,
                        key='selected_doc_number'
                    )
                else:
                    st.info(f'등록된 {doc_type}가 없습니다.')
                    selected_doc = None
            else:
                selected_doc = None
        
        # 2단계: 기본 설정
        col1, col2, col3 = st.columns(3)
        
        with col1:
            language = st.selectbox(
                '언어',
                ['한국어', 'English', 'Tiếng Việt'],
                key='language_select'
            )
        
        with col2:
            vat_apply = st.checkbox('부가세 적용', value=True)
        
        with col3:
            vat_rate = st.number_input('부가세율 (%)', min_value=0.0, max_value=30.0, value=10.0, step=0.1)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 데이터 로드 및 기본값 설정
    if search_mode == '기존 문서 검색' and selected_doc:
        # 선택된 문서의 데이터 로드
        if doc_type == '견적서':
            doc_data = load_quotation_data(quotation_manager, selected_doc)
        elif doc_type == '발주서':
            doc_data = load_order_data(order_manager, selected_doc)
        elif doc_type == '출고서':
            doc_data = load_delivery_data(selected_doc)
        else:  # 지출요청서
            doc_data = load_expense_data(selected_doc)
    else:
        # 새 문서 기본값
        doc_data = get_default_document_data(doc_type)
    
    # 실제 문서 레이아웃 시작
    st.markdown('<div class="document-print-container">', unsafe_allow_html=True)
    
    # 문서 헤더
    st.markdown(f"""
    <div class="document-header">
        <div class="company-section">
            <h3>{doc_data.get('company_name', 'HanaRo International')}</h3>
            <div class="company-details">
                주소: {doc_data.get('company_address', '베트남 호치민시')}<br>
                전화: {doc_data.get('company_phone', '+84-28-1234-5678')}<br>
                이메일: {doc_data.get('company_email', 'info@hanaro.com')}<br>
                사업자번호: {doc_data.get('business_number', '0123456789')}
            </div>
        </div>
        <div class="document-info">
            <div class="document-title">{doc_type}</div>
            <div class="doc-meta">
                문서번호: <strong>{doc_data.get('doc_number', generate_doc_number(doc_type))}</strong><br>
                발행일: <strong>{doc_data.get('doc_date', datetime.now().strftime('%Y-%m-%d'))}</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 고객 및 문서 정보
    st.markdown(f"""
    <div class="info-grid">
        <div class="info-box">
            <h4>👥 고객 정보</h4>
            <div class="info-row">
                <span class="info-label">회사:</span>
                <span>{doc_data.get('customer_company', '고객사명')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">담당:</span>
                <span>{doc_data.get('customer_contact', '담당자명')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">전화:</span>
                <span>{doc_data.get('customer_phone', '전화번호')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">이메일:</span>
                <span>{doc_data.get('customer_email', '이메일')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">주소:</span>
                <span>{doc_data.get('customer_address', '고객 주소')}</span>
            </div>
        </div>
        
        <div class="info-box">
            <h4>📄 {get_document_info_title(doc_type)}</h4>
            <div class="info-row">
                <span class="info-label">{get_validity_label(doc_type)}:</span>
                <span>{doc_data.get('validity', get_default_validity(doc_type))}</span>
            </div>
            <div class="info-row">
                <span class="info-label">{get_payment_label(doc_type)}:</span>
                <span>{doc_data.get('payment_terms', '현금')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">{get_delivery_label(doc_type)}:</span>
                <span>{doc_data.get('delivery_terms', '즉시')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">담당자:</span>
                <span>{doc_data.get('manager', '김철수')}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 품목 테이블 (최대 8줄로 제한)
    items_data = doc_data.get('items', get_default_items(doc_type))
    
    # 테이블 HTML 생성
    table_headers = get_table_headers(doc_type)
    table_html = f"""
    <table class="compact-table">
        <thead>
            <tr>
                {''.join([f'<th>{header}</th>' for header in table_headers])}
            </tr>
        </thead>
        <tbody>
    """
    
    # 최대 8개 항목만 표시
    for i, item in enumerate(items_data[:8]):
        # item이 딕셔너리인지 확인하여 안전하게 처리
        if isinstance(item, dict):
            name = item.get('name', '')
            spec = item.get('spec', '')
            qty = item.get('qty', 0)
            unit = item.get('unit', 'EA')
            price = item.get('price', 0)
            amount = item.get('amount', 0)
            note = item.get('note', '')
        else:
            # item이 딕셔너리가 아닌 경우 기본값 사용
            name = str(item) if item else ''
            spec = ''
            qty = 0
            unit = 'EA'
            price = 0
            amount = 0
            note = ''
        
        table_html += f"""
            <tr>
                <td>{i+1}</td>
                <td>{name}</td>
                <td>{spec}</td>
                <td>{qty:,}</td>
                <td>{unit}</td>
                <td>{price:,}</td>
                <td>{amount:,}</td>
                <td>{note}</td>
            </tr>
        """
    
    # 빈 줄 추가 (최대 8줄 맞춤)
    for i in range(len(items_data), 8):
        table_html += "<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"
    
    table_html += """
        </tbody>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # 합계 및 서명란 - 데이터 타입 안전하게 처리
    subtotal = 0
    for item in items_data:
        if isinstance(item, dict):
            subtotal += item.get('amount', 0)
    
    vat_amount = int(subtotal * vat_rate / 100) if vat_apply else 0
    total = subtotal + vat_amount
    
    st.markdown(f"""
    <div class="summary-section">
        <div>
            <div style="font-size: 9px; padding: 10px; border: 1px solid #ddd;">
                <strong>비고:</strong> {get_document_note(doc_type)}<br>
                <strong>특이사항:</strong> {doc_data.get('special_note', '특별한 사항 없음')}
            </div>
        </div>
        
        <div class="total-box">
            <div class="total-row">
                <span>소계:</span>
                <span>{subtotal:,}원</span>
            </div>
            {'<div class="total-row"><span>부가세 (' + str(vat_rate) + '%):</span><span>' + f'{vat_amount:,}' + '원</span></div>' if vat_apply else ''}
            <div class="total-row total-final">
                <span>총 금액:</span>
                <span>{total:,}원</span>
            </div>
            <div style="margin-top: 10px; font-size: 8px; text-align: center;">
                <strong>발주처 서명:</strong> ________________<br><br>
                <strong>수주처 서명:</strong> ________________
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 프린트 안내
    st.success("""
    🖨️ **A4 1장 최적화 프린트:**
    - 우측 하단 '🖨️ 화면 출력' 버튼 클릭 또는 Ctrl+P
    - 사이드바 자동 숨김, A4 용지 완전 최적화
    - 품목 8개 이내 권장 (한 페이지 내 모든 내용 표시)
    """)

def get_company_data(config_manager, get_text):
    """회사 정보를 언어별로 로드"""
    try:
        # 현재 언어 가져오기
        current_lang = st.session_state.get('language', 'ko')
        
        # 실제 회사 정보 DB에서 로드
        try:
            if config_manager and hasattr(config_manager, 'get_config'):
                # 시스템 설정에서 회사 정보 가져오기
                company_configs = {
                    'company_name': config_manager.get_config('company_name', 'HanaRo International'),
                    'company_address': config_manager.get_config('company_address', '베트남 호치민시'),
                    'company_phone': config_manager.get_config('company_phone', '+84-28-1234-5678'),
                    'company_email': config_manager.get_config('company_email', 'info@hanaro.com'),
                    'business_number': config_manager.get_config('business_number', '0123456789'),
                    'representative': config_manager.get_config('representative_name', '김대표'),
                    'website': config_manager.get_config('company_website', 'www.hanaro.com')
                }
            else:
                # 기본값 사용
                company_configs = {
                    'company_name': 'HanaRo International',
                    'company_address': '베트남 호치민시',
                    'company_phone': '+84-28-1234-5678',
                    'company_email': 'info@hanaro.com',
                    'business_number': '0123456789',
                    'representative': '김대표',
                    'website': 'www.hanaro.com'
                }
            
            company_data = {
                'ko': {
                    'name': company_configs['company_name'],
                    'address': company_configs['company_address'],
                    'phone': company_configs['company_phone'],
                    'fax': company_configs['company_phone'].replace('xxx', '999'),  # 팩스번호 기본값
                    'email': company_configs['company_email'],
                    'businessNumber': company_configs['business_number'],
                    'representative': company_configs['representative'],
                    'website': company_configs['website']
                },
                'en': {
                    'name': company_configs['company_name'] + ' Co., Ltd.',
                    'address': company_configs['company_address'].replace('베트남', 'Vietnam').replace('호치민시', 'Ho Chi Minh City'),
                    'phone': company_configs['company_phone'],
                    'fax': company_configs['company_phone'].replace('xxx', '999'),
                    'email': company_configs['company_email'],
                    'businessNumber': company_configs['business_number'],
                    'representative': company_configs['representative'] + ' (CEO)',
                    'website': company_configs['website']
                },
                'vi': {
                    'name': 'Công ty TNHH ' + company_configs['company_name'],
                    'address': company_configs['company_address'].replace('베트남', 'Việt Nam').replace('호치민시', 'Thành phố Hồ Chí Minh'),
                    'phone': company_configs['company_phone'],
                    'fax': company_configs['company_phone'].replace('xxx', '999'),
                    'email': company_configs['company_email'],
                    'businessNumber': company_configs['business_number'],
                    'representative': 'Giám đốc ' + company_configs['representative'],
                    'website': company_configs['website']
                }
            }
        except Exception as e:
            st.error(f"회사 정보 로드 중 오류: {str(e)}")
            # 기본값 사용
            company_data = {
                'ko': {
                    'name': 'HanaRo International',
                    'address': '베트남 호치민시',
                    'phone': '+84-xxx-xxx-xxx',
                    'fax': '+84-xxx-xxx-999', 
                    'email': 'info@hanaro.com',
                    'businessNumber': '0123456789',
                    'representative': '김대표',
                    'website': 'www.hanaro.com'
                },
                'en': {
                    'name': 'HanaRo International Co., Ltd.',
                    'address': 'Ho Chi Minh City, Vietnam',
                    'phone': '+84-xxx-xxx-xxx',
                    'fax': '+84-xxx-xxx-999',
                    'email': 'info@hanaro.com', 
                    'businessNumber': '0123456789',
                    'representative': 'Kim CEO',
                    'website': 'www.hanaro.com'
                },
                'vi': {
                    'name': 'Công ty TNHH HanaRo International',
                    'address': 'Thành phố Hồ Chí Minh, Việt Nam',
                    'phone': '+84-xxx-xxx-xxx',
                    'fax': '+84-xxx-xxx-999',
                    'email': 'info@hanaro.com',
                    'businessNumber': '0123456789',
                    'representative': 'Giám đốc Kim',
                    'website': 'www.hanaro.com'
                }
            }
        
        return company_data
        
    except Exception as e:
        st.error(f"회사 정보 로드 오류: {str(e)}")
        return None

# 문서 번호 생성 함수
def generate_doc_number(doc_type):
    from datetime import datetime
    date_str = datetime.now().strftime('%Y%m%d')
    if doc_type == '견적서':
        return f"Q{date_str}0001"
    elif doc_type == '발주서':
        return f"PO{date_str}0001"
    elif doc_type == '출고서':
        return f"DN{date_str}0001"
    else:  # 지출요청서
        return f"EX{date_str}0001"

# 문서 데이터 로드 함수들
def get_quotation_numbers(quotation_manager):
    """SQLite에서 견적서 번호 목록 가져오기"""
    try:
        if quotation_manager and hasattr(quotation_manager, 'get_all_quotations'):
            quotations = quotation_manager.get_all_quotations()
            if isinstance(quotations, list) and quotations:
                return [q.get('quotation_id', q.get('id', '')) for q in quotations if q.get('quotation_id') or q.get('id')]
        return []
    except Exception as e:
        st.warning(f"견적서 데이터 로드 오류: {str(e)}")
        return []

def get_order_numbers(order_manager):
    """SQLite에서 발주서 번호 목록 가져오기"""
    try:
        if order_manager and hasattr(order_manager, 'get_all_orders'):
            orders = order_manager.get_all_orders()
            if isinstance(orders, list) and orders:
                return [o.get('order_id', o.get('id', '')) for o in orders if o.get('order_id') or o.get('id')]
        return []
    except Exception as e:
        st.warning(f"발주서 데이터 로드 오류: {str(e)}")
        return []

def get_delivery_numbers():
    """SQLite에서 출고서 번호 목록 가져오기"""
    # TODO: 출고서 매니저 구현 후 연동
    return []

def get_expense_numbers():
    """SQLite에서 지출요청서 번호 목록 가져오기"""
    # TODO: 지출요청서 매니저 구현 후 연동
    return []

def load_expense_data(expense_id):
    """SQLite에서 지출요청서 상세 데이터 로드"""
    # TODO: 지출요청서 매니저 구현 후 연동
    return get_default_document_data('지출요청서')

def load_quotation_data(quotation_manager, quotation_id):
    """SQLite에서 견적서 상세 데이터 로드"""
    try:
        if quotation_manager and hasattr(quotation_manager, 'get_quotation_by_id'):
            return quotation_manager.get_quotation_by_id(quotation_id)
        return get_default_document_data('견적서')
    except Exception as e:
        st.error(f"견적서 데이터 로드 오류: {str(e)}")
        return get_default_document_data('견적서')

def load_order_data(order_manager, order_id):
    """SQLite에서 발주서 상세 데이터 로드"""
    try:
        if order_manager and hasattr(order_manager, 'get_order_by_id'):
            return order_manager.get_order_by_id(order_id)
        return get_default_document_data('발주서')
    except Exception as e:
        st.error(f"발주서 데이터 로드 오류: {str(e)}")
        return get_default_document_data('발주서')

def load_delivery_data(delivery_id):
    """SQLite에서 출고서 상세 데이터 로드"""
    # TODO: 출고서 매니저 구현 후 연동
    return get_default_document_data('출고서')

def get_default_document_data(doc_type):
    """문서 타입별 기본 데이터 반환"""
    from datetime import datetime
    base_data = {
        'company_name': 'HanaRo International',
        'company_address': '베트남 호치민시',
        'company_phone': '+84-28-1234-5678',
        'company_email': 'info@hanaro.com',
        'business_number': '0123456789',
        'doc_number': generate_doc_number(doc_type),
        'doc_date': datetime.now().strftime('%Y-%m-%d'),
        'customer_company': '고객사명',
        'customer_contact': '담당자명',
        'customer_phone': '전화번호',
        'customer_email': '이메일',
        'customer_address': '고객 주소',
        'manager': '김철수'
    }
    
    if doc_type == '견적서':
        quote_data = {
            'validity': '30일',
            'payment_terms': '현금',
            'delivery_terms': '즉시',
            'items': [
                {'name': 'HRC-T8-100', 'spec': '8mm x 100mm', 'qty': 10, 'unit': 'EA', 'price': 15000, 'amount': 150000, 'note': '표준형'},
                {'name': 'HRC-T12-200', 'spec': '12mm x 200mm', 'qty': 5, 'unit': 'EA', 'price': 25000, 'amount': 125000, 'note': '고급형'}
            ]
        }
        base_data.update(quote_data)
    elif doc_type == '발주서':
        purchase_data = {
            'validity': '납기: 2주',
            'payment_terms': '계좌이체',
            'delivery_terms': 'FOB',
            'items': [
                {'name': 'HRC-Component-A', 'spec': '표준 규격', 'qty': 20, 'unit': 'SET', 'price': 35000, 'amount': 700000, 'note': '급속 납기'}
            ]
        }
        base_data.update(purchase_data)
    elif doc_type == '출고서':
        delivery_data = {
            'validity': '출고일',
            'payment_terms': '출고 완료',
            'delivery_terms': '직배송',
            'items': [
                {'name': 'HRC-Product-X', 'spec': '출고 품목', 'qty': 15, 'unit': 'EA', 'price': 0, 'amount': 0, 'note': '출고 완료'}
            ]
        }
        base_data.update(delivery_data)
    elif doc_type == '지출요청서':
        expense_data = {
            'requester_name': '요청자명',
            'department': '총무부',
            'position': '주임',
            'contact': '연락처',
            'expense_reason': '사무용품 구매',
            'estimated_amount': 500000,
            'expense_date': datetime.now().strftime('%Y-%m-%d'),
            'approver': '법인장',
            'validity': '지출일자',
            'payment_terms': '승인 후 지급',
            'delivery_terms': '즉시',
            'items': [
                {'category': '사무용품', 'description': '프린터 용지 및 토너', 'amount': 150000, 'note': '사무실 용'},
                {'category': '업무추진비', 'description': '고객 접대비', 'amount': 200000, 'note': '중요 고객 미팅'},
                {'category': '교통비', 'description': '출장 교통비', 'amount': 150000, 'note': '화상 미팅 출장'}
            ]
        }
        base_data.update(expense_data)
    
    return base_data

def get_document_info_title(doc_type):
    if doc_type == '견적서':
        return '견적 정보'
    elif doc_type == '발주서':
        return '발주 정보'
    elif doc_type == '출고서':
        return '출고 정보'
    else:  # 지출요청서
        return '지출 정보'

def get_validity_label(doc_type):
    if doc_type == '견적서':
        return '유효기간'
    elif doc_type == '발주서':
        return '납기일'
    elif doc_type == '출고서':
        return '출고일'
    else:  # 지출요청서
        return '지출사유'

def get_payment_label(doc_type):
    if doc_type == '출고서':
        return '출고상태'
    elif doc_type == '지출요청서':
        return '지급방법'
    else:
        return '결제조건'

def get_delivery_label(doc_type):
    if doc_type == '발주서':
        return '인도조건'
    elif doc_type == '출고서':
        return '운송방법'
    elif doc_type == '지출요청서':
        return '지출유형'
    else:
        return '인도조건'

def get_default_validity(doc_type):
    if doc_type == '견적서':
        return '30일'
    elif doc_type == '발주서':
        return '2주일'
    elif doc_type == '지출요청서':
        return '원력전표 및 승인'
    else:
        return '즉시'

def get_table_headers(doc_type):
    base_headers = ['번호', '품목명', '규격', '수량', '단위']
    
    if doc_type == '출고서':
        return base_headers + ['출고량', '비고']
    else:
        return base_headers + ['단가', '금액', '비고']

def get_default_items(doc_type):
    if doc_type == '견적서':
        return [
            {'name': 'HRC-T8-100', 'spec': '8mm x 100mm', 'qty': 10, 'unit': 'EA', 'price': 15000, 'amount': 150000, 'note': '표준형'},
            {'name': 'HRC-T12-200', 'spec': '12mm x 200mm', 'qty': 5, 'unit': 'EA', 'price': 25000, 'amount': 125000, 'note': '고급형'}
        ]
    elif doc_type == '발주서':
        return [
            {'name': 'HRC-Component-A', 'spec': '표준 규격', 'qty': 20, 'unit': 'SET', 'price': 35000, 'amount': 700000, 'note': '급속 납기'}
        ]
    elif doc_type == '출고서':
        return [
            {'name': 'HRC-Product-X', 'spec': '출고 품목', 'qty': 15, 'unit': 'EA', 'price': 0, 'amount': 0, 'note': '출고 완료'}
        ]
    else:  # 지출요청서
        return [
            {'category': '사무용품', 'description': '프린터 용지 및 토너', 'amount': 150000, 'note': '사무실 용'},
            {'category': '업무추진비', 'description': '고객 접대비', 'amount': 200000, 'note': '중요 고객 미팅'}
        ]

def get_document_note(doc_type):
    if doc_type == '견적서':
        return '견적 유효기간 내 발주 바랍니다.'
    elif doc_type == '발주서':
        return '납기일 준수 및 품질 대로 납품 바랍니다.'
    elif doc_type == '출고서':
        return '출고 내역을 확인하시고 수령 바랍니다.'
    else:  # 지출요청서
        return '위 내역에 대한 지출을 요청드립니다.'

def get_customers_data(customer_manager, get_text):
    """SQLite에서 실제 고객 데이터 로드"""
    try:
        import sqlite3
        
        # SQLite에서 실제 고객 데이터 직접 로드
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.execute('''
            SELECT customer_id, company_name, contact_person, email, phone, 
                   country, city, address, business_type
            FROM customers 
            WHERE status = 'active'
            ORDER BY company_name
        ''')
        
        customers_list = []
        for row in cursor.fetchall():
            customer_id, company_name, contact_person, email, phone, country, city, address, business_type = row
            customers_list.append({
                'customer_id': customer_id,
                'company_name': company_name,
                'contact_person': contact_person,
                'email': email,
                'phone': phone,
                'country': country,
                'city': city,
                'address': address,
                'business_type': business_type
            })
        
        conn.close()
        
        if not customers_list:
            # 마이그레이션된 데이터가 없는 경우에만 샘플 데이터 사용
            customers_list = [{
                'customer_id': 'sample1',
                'company_name': '샘플 고객사 A',
                'contact_person': '김담당자',
                'phone': '+84-28-1234-5678',
                'email': 'contact@sample-a.com',
                'address': '베트남 호치민시 1구',
                'business_number': '1234567890'
            }]
            
        customers_data = {}
        
        for customer in customers_list:
            customer_id = str(customer.get('customer_id', ''))
            
            # 기본 정보
            base_company = customer.get('company_name', '샘플 고객사')
            base_contact = customer.get('contact_person', '담당자')
            base_address = customer.get('address', '베트남 호치민시')
            base_phone = customer.get('phone', '+84-xxx-xxx-xxx')
            base_email = customer.get('email', 'contact@customer.com')
            base_business = customer.get('business_number', '1234567890')
            
            customers_data[customer_id] = {
                'ko': {
                    'company': base_company,
                    'contact': base_contact,
                    'department': customer.get('department', '영업팀'),
                    'address': base_address,
                    'phone': base_phone,
                    'email': base_email,
                    'businessNumber': base_business
                },
                'en': {
                    'company': base_company + ' Co., Ltd.',
                    'contact': base_contact + ' (Manager)',
                    'department': customer.get('department', 'Sales Team'),
                    'address': base_address.replace('베트남', 'Vietnam').replace('호치민시', 'Ho Chi Minh City'),
                    'phone': base_phone,
                    'email': base_email,
                    'businessNumber': base_business
                },
                'vi': {
                    'company': 'Công ty ' + base_company,
                    'contact': 'Ông/Bà ' + base_contact,
                    'department': customer.get('department', 'Phòng Kinh doanh'),
                    'address': base_address.replace('베트남', 'Việt Nam').replace('호치민시', 'TP. Hồ Chí Minh'),
                    'phone': base_phone,
                    'email': base_email,
                    'businessNumber': base_business
                }
            }
        
        return customers_data
        
    except Exception as e:
        st.warning(f"고객 정보 로드 중 오류가 발생했습니다: {str(e)}")
        return {}

def get_quotations_data(quotation_manager, get_text):
    """견적서 데이터 로드"""
    try:
        if quotation_manager and hasattr(quotation_manager, 'get_quotations_dataframe'):
            quotations_df = quotation_manager.get_quotations_dataframe()
            if not quotations_df.empty:
                # DataFrame을 dict로 변환하고 JSON 직렬화 가능하도록 처리
                records = quotations_df.to_dict('records')
                return [convert_to_json_serializable(record) for record in records]
            return []
        elif quotation_manager and hasattr(quotation_manager, 'get_all_quotations'):
            data = quotation_manager.get_all_quotations()
            return [convert_to_json_serializable(item) for item in data] if isinstance(data, list) else []
        else:
            return []
    except Exception as e:
        st.warning(f"견적서 데이터 로드 중 오류: {str(e)}")
        return []

def get_orders_data(order_manager, get_text):
    """주문 데이터 로드"""
    try:
        if order_manager and hasattr(order_manager, 'get_orders_dataframe'):
            orders_df = order_manager.get_orders_dataframe()
            if not orders_df.empty:
                # DataFrame을 dict로 변환하고 JSON 직렬화 가능하도록 처리
                records = orders_df.to_dict('records')
                return [convert_to_json_serializable(record) for record in records]
            return []
        elif order_manager and hasattr(order_manager, 'get_all_orders'):
            data = order_manager.get_all_orders()
            return [convert_to_json_serializable(item) for item in data] if isinstance(data, list) else []
        else:
            return []
    except Exception as e:
        st.warning(f"주문 데이터 로드 중 오류: {str(e)}")
        return []

def convert_to_json_serializable(obj):
    """JSON 직렬화 가능한 형태로 변환"""
    import pandas as pd
    import numpy as np
    from datetime import datetime, date
    
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
    elif hasattr(obj, 'dtype') and 'int' in str(obj.dtype):
        return int(obj)
    elif hasattr(obj, 'dtype') and 'float' in str(obj.dtype):
        return float(obj)
    elif pd.isna(obj) or obj is None:
        return None
    elif hasattr(obj, 'to_dict'):
        return convert_to_json_serializable(obj.to_dict())
    else:
        return str(obj)

# 기존 HTML 생성 함수는 더 이상 사용하지 않음
def generate_print_system_html_legacy(company_data, customers_data, quotations_data, orders_data, get_text):
    """문서 출력 시스템 HTML 생성"""
    
    # 언어별 번역 데이터 준비
    translations_js = {
        'ko': {
            'dataLabel': '데이터 선택:',
            'refreshBtn': '새로고침',
            'docSelectTitle': '문서 타입 선택',
            'taxSettingsTitle': '부가세 설정',
            'vatApplyLabel': '부가세 적용',
            'vatRateLabel': '부가세율:',
            'quote': '견적서',
            'purchase': '발주서',
            'delivery': '출고서',
            'payment': '지불요청서',
            'docNumberLabel': '문서번호:',
            'docDateLabel': '발행일:',
            'customerInfoTitle': '고객 정보',
            'documentInfoTitle': '문서 정보',
            'companyLabel': '회사:',
            'contactLabel': '담당:',
            'addressLabel': '주소:',
            'phoneLabel': '전화:',
            'emailLabel': '이메일:',
            'validityLabel': '유효기간:',
            'paymentLabel': '결제조건:',
            'deliveryLabel': '배송조건:',
            'managerLabel': '담당자:',
            'noHeader': '번호',
            'itemHeader': '품목명',
            'specHeader': '규격',
            'qtyHeader': '수량',
            'unitHeader': '단위',
            'priceHeader': '단가',
            'amountHeader': '금액',
            'remarkHeader': '비고',
            'subtotalLabel': '소계',
            'vatLabel': '부가세',
            'shippingLabel': '배송비',
            'totalLabel': '총 금액',
            'supplierSignature': '공급자 서명',
            'customerSignature': '구매자 서명',
            'previewBtn': '🖨️ 바로 프린트',
            'downloadBtn': '📄 HTML 다운로드',
            'printBtn': '문서 프린트',
            'validateBtn': '유효성 검사 후 프린트'
        },
        'en': {
            'dataLabel': 'Select Data:',
            'refreshBtn': 'Refresh',
            'docSelectTitle': 'Select Document Type',
            'taxSettingsTitle': 'Tax Settings',
            'vatApplyLabel': 'Apply VAT',
            'vatRateLabel': 'VAT Rate:',
            'quote': 'Quotation',
            'purchase': 'Purchase Order',
            'delivery': 'Delivery Note',
            'payment': 'Payment Request',
            'docNumberLabel': 'Doc Number:',
            'docDateLabel': 'Issue Date:',
            'customerInfoTitle': 'Customer Information',
            'documentInfoTitle': 'Document Information',
            'companyLabel': 'Company:',
            'contactLabel': 'Contact:',
            'addressLabel': 'Address:',
            'phoneLabel': 'Phone:',
            'emailLabel': 'Email:',
            'validityLabel': 'Valid Until:',
            'paymentLabel': 'Payment Terms:',
            'deliveryLabel': 'Delivery Terms:',
            'managerLabel': 'Manager:',
            'noHeader': 'No.',
            'itemHeader': 'Item',
            'specHeader': 'Specification',
            'qtyHeader': 'Qty',
            'unitHeader': 'Unit',
            'priceHeader': 'Price',
            'amountHeader': 'Amount',
            'remarkHeader': 'Remark',
            'subtotalLabel': 'Subtotal',
            'vatLabel': 'VAT',
            'shippingLabel': 'Shipping',
            'totalLabel': 'Total Amount',
            'supplierSignature': 'Supplier Signature',
            'customerSignature': 'Customer Signature',
            'previewBtn': '🖨️ Direct Print',
            'downloadBtn': '📄 Download HTML',
            'printBtn': 'Print Document',
            'validateBtn': 'Validate & Print'
        },
        'vi': {
            'dataLabel': 'Chọn Dữ liệu:',
            'refreshBtn': 'Làm mới',
            'docSelectTitle': 'Chọn Loại Tài liệu',
            'taxSettingsTitle': 'Cài đặt Thuế',
            'vatApplyLabel': 'Áp dụng VAT',
            'vatRateLabel': 'Thuế suất VAT:',
            'quote': 'Báo giá',
            'purchase': 'Đơn đặt hàng',
            'delivery': 'Phiếu giao hàng',
            'payment': 'Yêu cầu thanh toán',
            'docNumberLabel': 'Số tài liệu:',
            'docDateLabel': 'Ngày phát hành:',
            'customerInfoTitle': 'Thông tin Khách hàng',
            'documentInfoTitle': 'Thông tin Tài liệu',
            'companyLabel': 'Công ty:',
            'contactLabel': 'Liên hệ:',
            'addressLabel': 'Địa chỉ:',
            'phoneLabel': 'Điện thoại:',
            'emailLabel': 'Email:',
            'validityLabel': 'Có hiệu lực đến:',
            'paymentLabel': 'Điều khoản thanh toán:',
            'deliveryLabel': 'Điều khoản giao hàng:',
            'managerLabel': 'Người phụ trách:',
            'noHeader': 'STT',
            'itemHeader': 'Mặt hàng',
            'specHeader': 'Thông số',
            'qtyHeader': 'SL',
            'unitHeader': 'Đơn vị',
            'priceHeader': 'Đơn giá',
            'amountHeader': 'Thành tiền',
            'remarkHeader': 'Ghi chú',
            'subtotalLabel': 'Tạm tính',
            'vatLabel': 'VAT',
            'shippingLabel': 'Phí vận chuyển',
            'totalLabel': 'Tổng cộng',
            'supplierSignature': 'Chữ ký Nhà cung cấp',
            'customerSignature': 'Chữ ký Khách hàng',
            'previewBtn': '🖨️ In trực tiếp',
            'downloadBtn': '📄 Tải HTML',
            'printBtn': 'In tài liệu',
            'validateBtn': 'Kiểm tra & In'
        }
    }
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP Multi-Language Document Printing System</title>
    <style>
        /* 기본 스타일 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            font-size: 11px;
        }}

        .container {{
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
            min-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            background: #f5f5f5 !important;
        }}

        /* 언어 선택 및 문서 선택 */
        .controls-section {{
            background: white !important;
            padding: 12px 20px !important;
            border-bottom: 2px solid #e0e0e0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            flex-shrink: 0 !important;
            margin-bottom: 0 !important;
            width: 100% !important;
            position: relative !important;
        }}

        .controls-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .language-selector {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        .lang-btn {{
            padding: 6px 12px;
            border: 1px solid #666;
            border-radius: 4px;
            background: white;
            color: #333;
            cursor: pointer;
            font-size: 10px;
            transition: all 0.3s;
        }}

        .lang-btn:hover {{
            background: #f5f5f5;
        }}

        .lang-btn.active {{
            background: #333;
            color: white;
        }}

        .document-selector {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .doc-btn {{
            padding: 8px 16px;
            border: 1px solid #666;
            border-radius: 5px;
            background: white;
            color: #333;
            cursor: pointer;
            font-size: 11px;
            transition: background 0.3s;
        }}

        .doc-btn:hover {{
            background: #f5f5f5;
        }}

        .doc-btn.active {{
            background: #333;
            color: white;
        }}

        .data-controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        .data-select {{
            padding: 6px 10px;
            border: 1px solid #666;
            border-radius: 4px;
            font-size: 10px;
        }}

        .refresh-btn {{
            padding: 6px 12px;
            background: #666;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
        }}

        /* 부가세 설정 */
        .tax-controls {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}

        .tax-controls h3 {{
            font-size: 11px;
            margin-bottom: 8px;
            color: #333;
        }}

        .tax-options {{
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }}

        .tax-checkbox {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 10px;
            cursor: pointer;
        }}

        .tax-checkbox input[type="checkbox"] {{
            width: 14px;
            height: 14px;
            cursor: pointer;
        }}

        .vat-rate-input {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 10px;
        }}

        .vat-rate-input input[type="number"] {{
            width: 50px;
            padding: 3px 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: 10px;
            text-align: center;
        }}

        .vat-rate-input input[type="number"]:disabled {{
            background: #f5f5f5;
            color: #999;
        }}

        /* 문서 컨테이너 */
        .document-container {{
            flex: 1 !important;
            display: flex !important;
            justify-content: center !important;
            align-items: flex-start !important;
            padding: 40px 20px !important;
            background: #f5f5f5 !important;
            overflow: auto !important;
            width: 100% !important;
            max-width: none !important;
        }}

        .document {{
            width: 210mm !important;
            min-height: 297mm !important;
            background: white !important;
            position: relative !important;
            box-sizing: border-box !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
            border-radius: 8px !important;
            padding: 20mm !important;
            font-size: 12px !important;
            line-height: 1.4 !important;
            transform: scale(0.8) !important;
            transform-origin: top center !important;
            margin: 0 auto 40px auto !important;
        }}

        /* 문서 헤더 */
        .document-header {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 3px solid #333;
            align-items: start;
        }}

        .company-info {{
            flex: 1;
        }}

        .company-logo {{
            width: 64px;
            height: 64px;
            background: white;
            border: 2px solid #333;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
            font-weight: bold;
            font-size: 19px;
            margin-bottom: 10px;
        }}

        .company-name {{
            font-size: 19px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}

        .company-details {{
            font-size: 10px;
            color: #666;
            line-height: 1.4;
        }}

        .document-title {{
            text-align: right;
            flex: 1;
        }}

        .doc-type {{
            font-size: 26px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}

        .doc-number {{
            font-size: 11px;
            color: #666;
        }}

        /* 고객 정보 - 컴팩트 버전 */
        .customer-section {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
            margin-bottom: 20px;
            padding: 15px 0;
        }}

        .customer-info {{
            background: #f8f9fa;
            padding: 8px 10px;
            border-radius: 4px;
            border-left: 3px solid #333;
        }}

        .document-info {{
            background: #f8f9fa;
            padding: 8px 10px;
            border-radius: 4px;
            border-left: 3px solid #666;
        }}

        .section-title {{
            font-weight: bold;
            margin-bottom: 6px;
            color: #333;
            font-size: 10px;
            text-transform: uppercase;
        }}

        .info-compact {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            font-size: 9px;
        }}

        .info-item {{
            display: flex;
            align-items: center;
            margin-bottom: 2px;
        }}

        .info-label {{
            font-weight: bold;
            color: #555;
            min-width: 45px;
            margin-right: 4px;
        }}

        .info-value {{
            color: #333;
            flex: 1;
        }}

        .doc-info-compact {{
            font-size: 9px;
        }}

        .doc-info-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 3px;
        }}

        .doc-info-label {{
            font-weight: bold;
            color: #555;
        }}

        .doc-info-value {{
            color: #333;
        }}

        /* 품목 테이블 */
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            font-size: 11px;
            table-layout: fixed;
        }}

        .items-table th:nth-child(1) {{ width: 8%; }}  /* 번호 */
        .items-table th:nth-child(2) {{ width: 25%; }} /* 품목명 */
        .items-table th:nth-child(3) {{ width: 15%; }} /* 규격 */
        .items-table th:nth-child(4) {{ width: 8%; }}  /* 수량 */
        .items-table th:nth-child(5) {{ width: 8%; }}  /* 단위 */
        .items-table th:nth-child(6) {{ width: 12%; }} /* 단가 */
        .items-table th:nth-child(7) {{ width: 12%; }} /* 금액 */
        .items-table th:nth-child(8) {{ width: 12%; }} /* 비고 */

        .items-table th {{
            background: #f8f9fa;
            border: 1px solid #333;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
            color: #333;
        }}

        .items-table td {{
            border: 1px solid #333;
            padding: 10px 8px;
            text-align: left;
            vertical-align: top;
        }}

        .items-table .number-cell {{
            text-align: right;
        }}

        .items-table .center-cell {{
            text-align: center;
        }}

        /* 합계 섹션 */
        .totals-section {{
            margin-top: 10px;
            display: flex;
            justify-content: flex-end;
        }}

        .totals-table {{
            width: 300px;
            border-collapse: collapse;
        }}

        .totals-table td {{
            padding: 8px 12px;
            border: 1px solid #333;
            font-size: 11px;
        }}

        .totals-table .label {{
            background: #f8f9fa;
            font-weight: bold;
            text-align: right;
            width: 150px;
        }}

        .totals-table .amount {{
            text-align: right;
            font-weight: bold;
        }}

        .total-final {{
            background: #333 !important;
            color: white !important;
            font-size: 13px;
        }}

        /* 서명 섹션 */
        .signature-section {{
            margin-top: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}

        .signature-box {{
            text-align: center;
            border: 1px solid #ddd;
            padding: 30px 16px;
            border-radius: 5px;
        }}

        .signature-title {{
            font-weight: bold;
            margin-bottom: 24px;
        }}

        .signature-line {{
            border-bottom: 1px solid #333;
            margin-bottom: 8px;
            height: 32px;
        }}

        /* 프린트 컨트롤 */
        .print-controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
            background: white;
            padding: 12px;
            border-radius: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
        }}

        .print-btn {{
            padding: 10px 16px;
            border: none;
            border-radius: 20px;
            background: #333;
            color: white;
            cursor: pointer;
            font-size: 11px;
            font-weight: 500;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .print-btn:hover {{
            background: #555;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}

        .preview-btn {{
            background: linear-gradient(45deg, #28a745, #20c997);
            border: none;
            color: white;
        }}

        .preview-btn:hover {{
            background: linear-gradient(45deg, #20c997, #28a745);
            transform: translateY(-2px);
        }}
        
        .download-btn {{
            background: linear-gradient(45deg, #007bff, #6f42c1);
            border: none;
            color: white;
        }}
        
        .download-btn:hover {{
            background: linear-gradient(45deg, #6f42c1, #007bff);
            transform: translateY(-2px);
        }}

        /* 프린트 스타일 */
        @media print {{
            .controls-section,
            .print-controls,
            .container > :not(.document-container) {{
                display: none !important;
            }}

            @page {{
                size: A4;
                margin: 1cm;
            }}

            .document-container {{
                box-shadow: none;
                border-radius: 0;
                margin: 0;
                padding: 0;
            }}

            .document {{
                width: 100%;
                min-height: auto;
                margin: 0;
                padding: 0;
                box-shadow: none;
            }}

            .company-logo {{
                background: white !important;
                color: black !important;
                border: 2px solid black;
            }}

            .doc-type {{
                color: black !important;
            }}

            .total-final {{
                background: white !important;
                color: black !important;
                border: 2px solid black !important;
                -webkit-print-color-adjust: exact;
            }}

            .items-table {{
                page-break-inside: avoid;
            }}

            .totals-section {{
                page-break-inside: avoid;
            }}

            .signature-section {{
                page-break-inside: avoid;
            }}

            .items-table thead {{
                display: table-header-group;
            }}
        }}

        /* 반응형 디자인 */
        @media (max-width: 1400px) {{
            .document {{
                transform: scale(0.7);
            }}
        }}

        @media (max-width: 1200px) {{
            .document {{
                transform: scale(0.6);
                width: 90vw;
                max-width: 210mm;
            }}
            
            .print-controls {{
                position: static;
                margin-top: 20px;
                justify-content: center;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
        }}

        @media (max-width: 768px) {{
            .controls-row {{
                flex-direction: column;
                gap: 15px;
                align-items: stretch;
            }}

            .document {{
                transform: scale(0.5);
                width: 95vw;
            }}

            .document-header {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}

            .customer-section {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}

            .signature-section {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}

            .language-selector,
            .document-selector,
            .data-controls,
            .tax-options {{
                justify-content: center;
                flex-wrap: wrap;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 컨트롤 섹션 -->
        <div class="controls-section">
            <div class="controls-row">
                <div class="language-selector">
                    <span>Language:</span>
                    <button class="lang-btn active" onclick="changeLanguage('ko')">한국어</button>
                    <button class="lang-btn" onclick="changeLanguage('en')">English</button>
                    <button class="lang-btn" onclick="changeLanguage('vi')">Tiếng Việt</button>
                </div>
                
                <div class="data-controls">
                    <span id="dataLabel">데이터 선택:</span>
                    <select class="data-select" id="customerSelect" onchange="loadCustomerData()">
                        <!-- 동적으로 로드됨 -->
                    </select>
                    <button class="refresh-btn" onclick="refreshData()" id="refreshBtn">새로고침</button>
                </div>
            </div>
            
            <div class="controls-row">
                <div>
                    <h3 id="docSelectTitle">문서 타입 선택</h3>
                    <div class="document-selector">
                        <button class="doc-btn active" onclick="selectDocumentType('quote', event)" id="quoteBtn">견적서</button>
                        <button class="doc-btn" onclick="selectDocumentType('purchase', event)" id="purchaseBtn">발주서</button>
                        <button class="doc-btn" onclick="selectDocumentType('delivery', event)" id="deliveryBtn">출고서</button>
                        <button class="doc-btn" onclick="selectDocumentType('payment', event)" id="paymentBtn">지불요청서</button>
                    </div>
                </div>
                
                <div class="tax-controls">
                    <h3 id="taxSettingsTitle">부가세 설정</h3>
                    <div class="tax-options">
                        <label class="tax-checkbox">
                            <input type="checkbox" id="vatApply" checked onchange="updateVatSettings()">
                            <span id="vatApplyLabel">부가세 적용</span>
                        </label>
                        <div class="vat-rate-input">
                            <label for="vatRate" id="vatRateLabel">부가세율:</label>
                            <input type="number" id="vatRate" value="10" min="0" max="30" step="0.1" onchange="updateVatSettings()">
                            <span>%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 문서 컨테이너 -->
        <div class="document-container">
            <div class="document" id="document">
                <!-- 문서 헤더 -->
                <div class="document-header">
                    <div class="company-info">
                        <div class="company-logo">LOGO</div>
                        <div class="company-name" id="companyName">회사명 (주)</div>
                        <div class="company-details" id="companyDetails">
                            주소: 서울특별시 강남구 테헤란로 123<br>
                            전화: 02-1234-5678<br>
                            이메일: info@company.com<br>
                            사업자등록번호: 123-45-67890
                        </div>
                    </div>
                    <div class="document-title">
                        <div class="doc-type" id="docType">견적서</div>
                        <div class="doc-number">
                            <span id="docNumberLabel">문서번호:</span> <span id="docNumber">Q202508220001</span><br>
                            <span id="docDateLabel">발행일:</span> <span id="docDate">2025-08-22</span>
                        </div>
                    </div>
                </div>

                <!-- 고객 및 문서 정보 -->
                <div class="customer-section">
                    <div class="customer-info">
                        <div class="section-title" id="customerInfoTitle">고객 정보</div>
                        <div class="info-compact">
                            <div class="info-item">
                                <span class="info-label" id="companyLabel">회사:</span>
                                <span class="info-value" id="customerCompany">고객사명</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label" id="contactLabel">담당:</span>
                                <span class="info-value" id="customerContact">담당자명</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label" id="phoneLabel">전화:</span>
                                <span class="info-value" id="customerPhone">전화번호</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label" id="emailLabel">이메일:</span>
                                <span class="info-value" id="customerEmail">이메일</span>
                            </div>
                        </div>
                        <div style="margin-top: 4px; font-size: 8px;">
                            <span class="info-label" id="addressLabel">주소:</span>
                            <span class="info-value" id="customerAddress">고객 주소</span>
                        </div>
                    </div>
                    
                    <div class="document-info">
                        <div class="section-title" id="documentInfoTitle">문서 정보</div>
                        <div class="doc-info-compact">
                            <div class="doc-info-row">
                                <span class="doc-info-label" id="validityLabel">유효기간:</span>
                                <span class="doc-info-value" id="docValidity">2025-09-22</span>
                            </div>
                            <div class="doc-info-row">
                                <span class="doc-info-label" id="paymentLabel">결제조건:</span>
                                <span class="doc-info-value" id="docPayment">현금 30일</span>
                            </div>
                            <div class="doc-info-row">
                                <span class="doc-info-label" id="deliveryLabel">배송조건:</span>
                                <span class="doc-info-value" id="docDelivery">착불</span>
                            </div>
                            <div class="doc-info-row">
                                <span class="doc-info-label" id="managerLabel">담당자:</span>
                                <span class="doc-info-value" id="docManager">영업담당</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 품목 테이블 -->
                <table class="items-table">
                    <thead>
                        <tr>
                            <th class="center-cell" id="noHeader">번호</th>
                            <th id="itemHeader">품목명</th>
                            <th id="specHeader">규격</th>
                            <th class="center-cell" id="qtyHeader">수량</th>
                            <th class="center-cell" id="unitHeader">단위</th>
                            <th class="number-cell" id="priceHeader">단가</th>
                            <th class="number-cell" id="amountHeader">금액</th>
                            <th id="remarkHeader">비고</th>
                        </tr>
                    </thead>
                    <tbody id="itemsTableBody">
                        <!-- 동적으로 로드됨 -->
                    </tbody>
                </table>

                <!-- 합계 섹션 -->
                <div class="totals-section">
                    <table class="totals-table">
                        <tr>
                            <td class="label" id="subtotalLabel">소계</td>
                            <td class="amount" id="subtotalAmount">0 VND</td>
                        </tr>
                        <tr>
                            <td class="label" id="vatLabel">부가세</td>
                            <td class="amount" id="vatAmount">0 VND</td>
                        </tr>
                        <tr>
                            <td class="label" id="shippingLabel">배송비</td>
                            <td class="amount" id="shippingAmount">750,000 VND</td>
                        </tr>
                        <tr class="total-final">
                            <td class="label total-final" id="totalLabel">총 금액</td>
                            <td class="amount total-final" id="totalAmount">0 VND</td>
                        </tr>
                    </table>
                </div>

                <!-- 서명 섹션 -->
                <div class="signature-section">
                    <div class="signature-box">
                        <div class="signature-title" id="supplierSignature">공급자 서명</div>
                        <div class="signature-line"></div>
                        <div>(인)</div>
                    </div>
                    <div class="signature-box">
                        <div class="signature-title" id="customerSignature">구매자 서명</div>
                        <div class="signature-line"></div>
                        <div>(인)</div>
                    </div>
                </div>
            </div>

            <!-- 프린트 컨트롤 -->
            <div class="print-controls">
                <button class="print-btn preview-btn" onclick="showPrintPreview()" id="previewBtn">🖨️ 바로 프린트</button>
                <button class="print-btn download-btn" onclick="downloadPrintDocument()" id="downloadBtn">📄 HTML 다운로드</button>
                <button class="print-btn" onclick="printDocument()" id="printBtn">문서 프린트</button>
                <button class="print-btn" onclick="validateAndPrint()" id="validateBtn">유효성 검사 후 프린트</button>
            </div>
        </div>
    </div>

    <script>
        // 전역 변수
        let currentLanguage = 'ko';
        let currentDocType = 'quote';
        let currentCustomer = 'customer1';
        
        // 다국어 번역 데이터
        const translations = {json.dumps(translations_js, ensure_ascii=False)};
        
        // 회사 정보 데이터
        const companyDatabase = {json.dumps(company_data, ensure_ascii=False)};
        
        // 고객 정보 데이터  
        const customersDatabase = {json.dumps(customers_data, ensure_ascii=False)};
        
        // 견적서 및 주문 데이터
        const quotationsDatabase = {json.dumps(quotations_data, ensure_ascii=False)};
        const ordersDatabase = {json.dumps(orders_data, ensure_ascii=False)};
        
        // 문서 타입 설정 (ERP 시스템과 동일한 형식)
        const documentTypes = {{
            'quote': {{ prefix: 'Q' }},      // 견적서: QYYYYMMDD####
            'purchase': {{ prefix: 'P' }},   // 발주서: PYYYYMMDD####
            'delivery': {{ prefix: 'D' }},   // 출고서: DYYYYMMDD####
            'payment': {{ prefix: 'PAY' }}   // 지불요청서: PAYYYYYMMDD####
        }};

        // 문서번호 생성 함수 (ERP 시스템과 동일한 방식)
        function generateDocumentNumber(type) {{
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const dateStr = `${{year}}${{month}}${{day}}`;
            
            const prefix = documentTypes[type].prefix;
            
            // 기본적으로 0001부터 시작 (실제로는 각 매니저에서 DB 조회해서 다음 번호 생성)
            const sequenceNum = '0001';
            
            return `${{prefix}}${{dateStr}}${{sequenceNum}}`;
        }}

        // 실제 데이터베이스에서 로드할 품목 데이터 (현재는 샘플)
        const sampleItems = {{
            // 모든 고객에 대한 기본 샘플 품목
            'default': [
                {{
                    'ko': {{ name: '산업용 히터', spec: 'SUS304, 3kW', qty: 2, unit: '개', price: 1500000, remark: '납기 1주일' }},
                    'en': {{ name: 'Industrial Heater', spec: 'SUS304, 3kW', qty: 2, unit: 'pcs', price: 1500000, remark: '1 week delivery' }},
                    'vi': {{ name: 'Máy sưởi công nghiệp', spec: 'SUS304, 3kW', qty: 2, unit: 'cái', price: 1500000, remark: 'Giao hàng 1 tuần' }}
                }},
                {{
                    'ko': {{ name: '온도 센서', spec: 'PT100, -50~200°C', qty: 5, unit: '개', price: 250000, remark: '교정성적서 포함' }},
                    'en': {{ name: 'Temperature Sensor', spec: 'PT100, -50~200°C', qty: 5, unit: 'pcs', price: 250000, remark: 'Includes calibration cert' }},
                    'vi': {{ name: 'Cảm biến nhiệt độ', spec: 'PT100, -50~200°C', qty: 5, unit: 'cái', price: 250000, remark: 'Bao gồm giấy hiệu chuẩn' }}
                }},
                {{
                    'ko': {{ name: '압력 게이지', spec: '0-10 bar, 디지털', qty: 3, unit: '개', price: 180000, remark: '국제 인증' }},
                    'en': {{ name: 'Pressure Gauge', spec: '0-10 bar, Digital', qty: 3, unit: 'pcs', price: 180000, remark: 'International certified' }},
                    'vi': {{ name: 'Đồng hồ áp suất', spec: '0-10 bar, Kỹ thuật số', qty: 3, unit: 'cái', price: 180000, remark: 'Chứng nhận quốc tế' }}
                }}
            ]
        }};

        // 페이지 로드 시 초기화
        document.addEventListener('DOMContentLoaded', function() {{
            loadCustomerList();
            loadCustomerData();
            loadCompanyData();
            updateLanguage();
            
            // 현재 날짜 설정
            document.getElementById('docDate').textContent = new Date().toISOString().split('T')[0];
            
            // 초기 문서번호 생성 (ERP 견적서 방식)
            const initialDocNumber = generateDocumentNumber(currentDocType);
            document.getElementById('docNumber').textContent = initialDocNumber;
        }});

        // 언어 변경
        function changeLanguage(lang) {{
            currentLanguage = lang;
            
            // 언어 버튼 활성화
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 언어 업데이트
            updateLanguage();
            loadCustomerList();
            loadCustomerData();
            updateVatSettings();
        }}

        // 언어별 텍스트 업데이트
        function updateLanguage() {{
            const t = translations[currentLanguage];
            
            // 각 요소별 텍스트 업데이트
            Object.keys(t).forEach(key => {{
                const element = document.getElementById(key);
                if (element) {{
                    element.textContent = t[key];
                }}
            }});
            
            // 문서 타입 버튼 업데이트
            document.getElementById('quoteBtn').textContent = t.quote;
            document.getElementById('purchaseBtn').textContent = t.purchase;
            document.getElementById('deliveryBtn').textContent = t.delivery;
            document.getElementById('paymentBtn').textContent = t.payment;
            
            // 현재 문서 타입 업데이트
            document.getElementById('docType').textContent = t[currentDocType];
            
            // 회사 정보 로드
            loadCompanyData();
        }}

        // 회사 정보 로드
        function loadCompanyData() {{
            const companyData = companyDatabase[currentLanguage];
            
            if (!companyData) return;
            
            // 회사 이름 업데이트
            document.getElementById('companyName').textContent = companyData.name;
            
            // 회사 상세 정보 업데이트
            let companyDetailsHtml = '';
            if (currentLanguage === 'ko') {{
                companyDetailsHtml = `
                    주소: ${{companyData.address}}<br>
                    전화: ${{companyData.phone}}<br>
                    팩스: ${{companyData.fax}}<br>
                    이메일: ${{companyData.email}}<br>
                    사업자등록번호: ${{companyData.businessNumber}}<br>
                    대표자: ${{companyData.representative}}<br>
                    웹사이트: ${{companyData.website}}
                `;
            }} else if (currentLanguage === 'en') {{
                companyDetailsHtml = `
                    Address: ${{companyData.address}}<br>
                    Phone: ${{companyData.phone}}<br>
                    Fax: ${{companyData.fax}}<br>
                    Email: ${{companyData.email}}<br>
                    Business No: ${{companyData.businessNumber}}<br>
                    CEO: ${{companyData.representative}}<br>
                    Website: ${{companyData.website}}
                `;
            }} else {{
                companyDetailsHtml = `
                    Địa chỉ: ${{companyData.address}}<br>
                    Điện thoại: ${{companyData.phone}}<br>
                    Fax: ${{companyData.fax}}<br>
                    Email: ${{companyData.email}}<br>
                    Mã số thuế: ${{companyData.businessNumber}}<br>
                    Giám đốc: ${{companyData.representative}}<br>
                    Website: ${{companyData.website}}
                `;
            }}
            
            document.getElementById('companyDetails').innerHTML = companyDetailsHtml;
        }}

        // 문서 타입 변경
        function changeDocumentType(type) {{
            currentDocType = type;
            const config = documentTypes[type];
            
            // 버튼 활성화
            document.querySelectorAll('.doc-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 문서 내용 업데이트
            const t = translations[currentLanguage];
            document.getElementById('docType').textContent = t[type];
            
            // 실시간 문서번호 생성
            const newDocNumber = generateDocumentNumber(type);
            document.getElementById('docNumber').textContent = newDocNumber;
        }}

        // 고객 목록 로드
        function loadCustomerList() {{
            const customerSelect = document.getElementById('customerSelect');
            customerSelect.innerHTML = '';
            
            // 기본 옵션 추가
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '고객을 선택하세요';
            customerSelect.appendChild(defaultOption);
            
            Object.keys(customersDatabase).forEach(customerId => {{
                const customerData = customersDatabase[customerId][currentLanguage];
                if (customerData && customerData.company) {{
                    const option = document.createElement('option');
                    option.value = customerId;
                    option.textContent = customerData.company;
                    customerSelect.appendChild(option);
                }}
            }});
            
            // 고객이 없으면 샘플 고객 추가
            if (customerSelect.options.length === 1) {{
                const sampleOption = document.createElement('option');
                sampleOption.value = 'sample';
                sampleOption.textContent = '샘플 고객사 (Demo)';
                customerSelect.appendChild(sampleOption);
            }}
        }}

        // 고객 데이터 로드
        function loadCustomerData() {{
            currentCustomer = document.getElementById('customerSelect').value;
            
            if (!currentCustomer || currentCustomer === '') {{
                // 기본값으로 초기화
                document.getElementById('customerCompany').textContent = '고객사명';
                document.getElementById('customerContact').textContent = '담당자명';
                document.getElementById('customerAddress').textContent = '고객 주소';
                document.getElementById('customerPhone').textContent = '전화번호';
                document.getElementById('customerEmail').textContent = '이메일';
                loadItemsData();
                return;
            }}
            
            // 샘플 고객 처리
            if (currentCustomer === 'sample') {{
                const sampleCustomer = {{
                    'ko': {{
                        company: '샘플 고객사',
                        contact: '김담당자',
                        department: '구매팀',
                        address: '베트남 호치민시 1구 레탄톤거리 123',
                        phone: '+84-28-1234-5678',
                        email: 'contact@sample.com'
                    }},
                    'en': {{
                        company: 'Sample Customer Co., Ltd.',
                        contact: 'Kim Manager',
                        department: 'Purchasing Team',
                        address: '123 Le Thanh Ton St., District 1, Ho Chi Minh City, Vietnam',
                        phone: '+84-28-1234-5678',
                        email: 'contact@sample.com'
                    }},
                    'vi': {{
                        company: 'Công ty Khách hàng Mẫu',
                        contact: 'Ông Kim',
                        department: 'Phòng Mua hàng',
                        address: '123 Đường Lê Thánh Tôn, Quận 1, TP. Hồ Chí Minh, Việt Nam',
                        phone: '+84-28-1234-5678',
                        email: 'contact@sample.com'
                    }}
                }}[currentLanguage];
                
                document.getElementById('customerCompany').textContent = sampleCustomer.company;
                document.getElementById('customerContact').textContent = sampleCustomer.contact + (sampleCustomer.department ? ` (${{sampleCustomer.department}})` : '');
                document.getElementById('customerAddress').textContent = sampleCustomer.address;
                document.getElementById('customerPhone').textContent = sampleCustomer.phone;
                document.getElementById('customerEmail').textContent = sampleCustomer.email;
                loadItemsData();
                return;
            }}
            
            if (!customersDatabase[currentCustomer]) return;
            
            // 고객 정보 로드
            const customerData = customersDatabase[currentCustomer][currentLanguage];
            if (!customerData) return;
            
            document.getElementById('customerCompany').textContent = customerData.company || '';
            document.getElementById('customerContact').textContent = customerData.contact + (customerData.department ? ` (${{customerData.department}})` : '');
            document.getElementById('customerAddress').textContent = customerData.address || '';
            document.getElementById('customerPhone').textContent = customerData.phone || '';
            document.getElementById('customerEmail').textContent = customerData.email || '';
            
            // 품목 데이터 로드
            loadItemsData();
        }}

        // 품목 데이터 로드
        function loadItemsData() {{
            // 현재 고객의 품목이 있으면 사용, 없으면 기본 품목 사용
            const items = sampleItems[currentCustomer] || sampleItems['default'] || [];
            const tbody = document.getElementById('itemsTableBody');
            tbody.innerHTML = '';
            
            let subtotal = 0;
            
            if (items.length === 0) {{
                // 데이터가 없을 때 안내 행 추가
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td colspan="8" style="text-align: center; padding: 20px; color: #666;">
                        품목 데이터가 없습니다. 실제 주문이나 견적 데이터를 연동하여 품목을 표시할 수 있습니다.
                    </td>
                `;
            }} else {{
                items.forEach((item, index) => {{
                    const itemData = item[currentLanguage];
                    const amount = itemData.qty * itemData.price;
                    subtotal += amount;
                    
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td class="center-cell">${{index + 1}}</td>
                        <td>${{itemData.name}}</td>
                        <td>${{itemData.spec}}</td>
                        <td class="center-cell">${{itemData.qty}}</td>
                        <td class="center-cell">${{itemData.unit}}</td>
                        <td class="number-cell">${{formatCurrency(itemData.price)}}</td>
                        <td class="number-cell">${{formatCurrency(amount)}}</td>
                        <td>${{itemData.remark}}</td>
                    `;
                }});
            }}
            
            // 합계 계산
            updateTotals(subtotal);
        }}

        // 합계 업데이트
        function updateTotals(subtotal) {{
            const vatApply = document.getElementById('vatApply').checked;
            const vatRate = parseFloat(document.getElementById('vatRate').value) || 0;
            
            const vat = vatApply ? Math.round(subtotal * vatRate / 100) : 0;
            const shipping = 750000; // VND 고정
            const total = subtotal + vat + shipping;
            
            document.getElementById('subtotalAmount').textContent = formatCurrency(subtotal);
            document.getElementById('vatAmount').textContent = formatCurrency(vat);
            document.getElementById('shippingAmount').textContent = formatCurrency(shipping);
            document.getElementById('totalAmount').textContent = formatCurrency(total);
        }}

        // 부가세 설정 업데이트
        function updateVatSettings() {{
            const vatApply = document.getElementById('vatApply').checked;
            const vatRateInput = document.getElementById('vatRate');
            
            vatRateInput.disabled = !vatApply;
            loadItemsData();
        }}

        // 통화 포맷 (VND 통일)
        function formatCurrency(amount) {{
            return new Intl.NumberFormat('vi-VN').format(amount) + ' VND';
        }}

        // 데이터 새로고침
        function refreshData() {{
            loadCustomerList();
            loadCustomerData();
            loadCompanyData();
        }}

        // 문서 타입 변경 함수
        function selectDocumentType(type, event) {{
            event.preventDefault();
            
            // 모든 버튼에서 active 클래스 제거
            document.querySelectorAll('.doc-btn').forEach(btn => btn.classList.remove('active'));
            
            // 클릭된 버튼에 active 클래스 추가
            event.target.classList.add('active');
            
            // 전역 변수 업데이트
            currentDocType = type;
            
            // 문서 정보 업데이트
            updateDocumentDisplay();
            
            // 부가세 설정 표시/숨김 처리 (지불요청서는 부가세 불필요)
            const taxControls = document.querySelector('.tax-controls');
            if (type === 'payment') {{
                taxControls.style.display = 'none';
            }} else {{
                taxControls.style.display = 'block';
            }}
        }}

        // 프린트 기능
        function printDocument() {{
            window.print();
        }}

        // HTML 다운로드 기능
        function downloadPrintDocument() {{
            try {{
                console.log('HTML 다운로드 시작');
                
                // 완전한 HTML 문서 생성
                const documentHtml = generateOptimizedPrintDocument();
                
                // 파일 다운로드 준비
                const blob = new Blob([documentHtml], {{ type: 'text/html;charset=utf-8' }});
                const url = URL.createObjectURL(blob);
                
                // 다운로드 링크 생성
                const downloadLink = document.createElement('a');
                downloadLink.href = url;
                
                // 파일명 생성 (문서타입_날짜_시간.html)
                const now = new Date();
                const timestamp = now.toISOString().slice(0,19).replace(/:/g, '-');
                const docTypeText = translations[currentLanguage][currentDocType] || currentDocType;
                downloadLink.download = `${{docTypeText}}_${{timestamp}}.html`;
                
                // 다운로드 실행
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                // 메모리 정리
                URL.revokeObjectURL(url);
                
                console.log('HTML 다운로드 완료');
                alert('HTML 파일이 다운로드되었습니다. 파일을 브라우저에서 열어 프린트하세요.');
                
            }} catch (error) {{
                console.error('다운로드 오류:', error);
                alert('HTML 다운로드 중 오류가 발생했습니다: ' + error.message);
            }}
        }}
        
        // 현재 창에서 프린트
        function showPrintPreview() {{
            try {{
                console.log('현재 창 프린트 모드');
                
                // 프린트 전용 스타일 추가
                const printStyles = `
                    <style id="print-only-styles">
                        @media print {{
                            body * {{ visibility: hidden; }}
                            .document-container, .document-container * {{ visibility: visible; }}
                            .document-container {{ 
                                position: absolute !important;
                                left: 0 !important;
                                top: 0 !important;
                                width: 100% !important;
                                margin: 0 !important;
                            }}
                            .print-controls {{ display: none !important; }}
                            .control-panel {{ display: none !important; }}
                        }}
                    </style>
                `;
                
                // 기존 프린트 스타일 제거
                const existingStyles = document.getElementById('print-only-styles');
                if (existingStyles) existingStyles.remove();
                
                // 새 프린트 스타일 추가
                document.head.insertAdjacentHTML('beforeend', printStyles);
                
                // 프린트 실행
                setTimeout(() => {{
                    window.print();
                }}, 100);
                
            }} catch (error) {{
                console.error('프린트 오류:', error);
                alert('프린트 중 오류가 발생했습니다: ' + error.message);
            }}
        }}
        
        // 프린트 최적화된 문서 생성
        function generateOptimizedPrintDocument() {{
            const t = translations[currentLanguage];
            const companyData = companyDatabase[currentLanguage];
            const docNumber = document.getElementById('docNumber').textContent;
            const docDate = document.getElementById('docDate').textContent;
            
            // 현재 고객 정보 수집
            const customerData = {{
                company: document.getElementById('customerCompany').textContent || '고객명 입력',
                contact: document.getElementById('customerContact').textContent || '담당자명',
                phone: document.getElementById('customerPhone').textContent || '전화번호',
                email: document.getElementById('customerEmail').textContent || '이메일',
                address: document.getElementById('customerAddress').textContent || '주소'
            }};
            
            // 샘플 품목 데이터
            const sampleItems = sampleData[currentLanguage];
            const subtotal = sampleItems.reduce((sum, item) => sum + (item.qty * item.price), 0);
            const vatRate = document.getElementById('vatRate')?.value || 10;
            const vatAmount = Math.round(subtotal * vatRate / 100);
            const total = subtotal + vatAmount;
            
            return `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>${{t[currentDocType]}} - ${{docNumber}}</title>
                    <style>
                        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                        
                        body {{
                            font-family: 'Arial', sans-serif;
                            line-height: 1.6;
                            color: #333;
                            background: #f5f5f5;
                            padding: 30px;
                        }}
                        
                        .print-container {{
                            max-width: 900px;
                            margin: 0 auto;
                            background: white;
                            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
                            border-radius: 12px;
                            overflow: hidden;
                        }}
                        
                        .document {{
                            width: 100%;
                            background: white;
                            padding: 40mm 30mm;
                            font-size: 13px;
                            line-height: 1.5;
                        }}
                        
                        .document-header {{
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 40px;
                            margin-bottom: 40px;
                            border-bottom: 3px solid #333;
                            padding-bottom: 25px;
                        }}
                        
                        .company-info h1 {{
                            font-size: 26px;
                            color: #333;
                            margin-bottom: 15px;
                            font-weight: bold;
                        }}
                        
                        .company-details {{
                            font-size: 12px;
                            line-height: 1.8;
                            color: #555;
                        }}
                        
                        .document-title {{
                            text-align: right;
                        }}
                        
                        .document-title h2 {{
                            font-size: 32px;
                            color: #333;
                            margin-bottom: 15px;
                            font-weight: bold;
                        }}
                        
                        .document-info {{
                            font-size: 13px;
                            text-align: right;
                            line-height: 1.8;
                        }}
                        
                        .customer-section {{
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 40px;
                            margin-bottom: 40px;
                        }}
                        
                        .info-section h3 {{
                            font-size: 16px;
                            color: #333;
                            margin-bottom: 20px;
                            border-bottom: 2px solid #ddd;
                            padding-bottom: 8px;
                            font-weight: bold;
                        }}
                        
                        .info-compact {{
                            display: grid;
                            grid-template-columns: 120px 1fr;
                            gap: 15px;
                            font-size: 12px;
                            line-height: 1.8;
                        }}
                        
                        .info-compact div:nth-child(odd) {{
                            font-weight: bold;
                            color: #666;
                        }}
                        
                        .items-table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 30px 0;
                            font-size: 12px;
                        }}
                        
                        .items-table th,
                        .items-table td {{
                            border: 1px solid #333;
                            padding: 12px 8px;
                            text-align: center;
                        }}
                        
                        .items-table th {{
                            background: #f8f9fa;
                            font-weight: bold;
                            font-size: 11px;
                        }}
                        
                        .items-table td:nth-child(2),
                        .items-table td:nth-child(3),
                        .items-table td:nth-child(8) {{
                            text-align: left;
                        }}
                        
                        .items-table td:nth-child(6),
                        .items-table td:nth-child(7) {{
                            text-align: right;
                        }}
                        
                        .totals-section {{
                            margin: 40px 0;
                            display: flex;
                            justify-content: flex-end;
                        }}
                        
                        .totals-table {{
                            border-collapse: collapse;
                            width: 350px;
                        }}
                        
                        .totals-table td {{
                            padding: 12px 15px;
                            border: 1px solid #333;
                            font-size: 12px;
                        }}
                        
                        .totals-table .label {{
                            background: #f8f9fa;
                            font-weight: bold;
                            text-align: right;
                            width: 180px;
                        }}
                        
                        .totals-table .amount {{
                            text-align: right;
                            font-weight: bold;
                        }}
                        
                        .total-final {{
                            background: #333 !important;
                            color: white !important;
                            font-size: 14px !important;
                            font-weight: bold !important;
                        }}
                        
                        .signature-section {{
                            margin-top: 50px;
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 40px;
                        }}
                        
                        .signature-box {{
                            text-align: center;
                            border: 2px solid #ddd;
                            padding: 40px 20px;
                            border-radius: 8px;
                            background: #fafafa;
                        }}
                        
                        .signature-title {{
                            font-weight: bold;
                            margin-bottom: 30px;
                            font-size: 14px;
                        }}
                        
                        .signature-line {{
                            border-bottom: 2px solid #333;
                            margin-bottom: 15px;
                            height: 40px;
                        }}
                        
                        .print-controls {{
                            background: #2c3e50;
                            padding: 25px;
                            text-align: center;
                            display: flex;
                            justify-content: center;
                            gap: 20px;
                        }}
                        
                        .print-btn {{
                            background: white;
                            color: #2c3e50;
                            border: 2px solid white;
                            padding: 12px 30px;
                            border-radius: 25px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: bold;
                            transition: all 0.3s;
                        }}
                        
                        .print-btn:hover {{
                            background: #3498db;
                            color: white;
                            border-color: #3498db;
                        }}
                        
                        .close-btn {{
                            background: transparent;
                            color: white;
                            border: 2px solid white;
                        }}
                        
                        .close-btn:hover {{
                            background: #e74c3c;
                            border-color: #e74c3c;
                        }}
                        
                        @media print {{
                            body {{ 
                                background: white; 
                                padding: 0; 
                                font-size: 12px;
                            }}
                            .print-container {{ 
                                box-shadow: none; 
                                border-radius: 0;
                                max-width: none;
                            }}
                            .print-controls {{ 
                                display: none; 
                            }}
                            .document {{ 
                                margin: 0; 
                                padding: 20mm;
                            }}
                            
                            .document-header {{
                                page-break-after: avoid;
                            }}
                            
                            .items-table {{
                                page-break-inside: avoid;
                            }}
                            
                            .signature-section {{
                                page-break-before: avoid;
                            }}
                        }}
                        
                        @page {{
                            size: A4;
                            margin: 15mm;
                        }}
                    </style>
                </head>
                <body>
                    <div class="print-container">
                        <div class="document">
                            <div class="document-header">
                                <div class="company-info">
                                    <h1>${{companyData.name}}</h1>
                                    <div class="company-details">
                                        ${{currentLanguage === 'ko' ? 
                                            `주소: ${{companyData.address}}<br>전화: ${{companyData.phone}}<br>팩스: ${{companyData.fax}}<br>이메일: ${{companyData.email}}<br>사업자등록번호: ${{companyData.businessNumber}}` :
                                            currentLanguage === 'en' ?
                                            `Address: ${{companyData.address}}<br>Phone: ${{companyData.phone}}<br>Fax: ${{companyData.fax}}<br>Email: ${{companyData.email}}<br>Business No: ${{companyData.businessNumber}}` :
                                            `Địa chỉ: ${{companyData.address}}<br>Điện thoại: ${{companyData.phone}}<br>Fax: ${{companyData.fax}}<br>Email: ${{companyData.email}}<br>Mã số thuế: ${{companyData.businessNumber}}`
                                        }}
                                    </div>
                                </div>
                                <div class="document-title">
                                    <h2>${{t[currentDocType]}}</h2>
                                    <div class="document-info">
                                        ${{t.docNumberLabel}}: <strong>${{docNumber}}</strong><br>
                                        ${{t.docDateLabel}}: <strong>${{docDate}}</strong>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="customer-section">
                                <div class="info-section">
                                    <h3>${{t.customerInfoTitle}}</h3>
                                    <div class="info-compact">
                                        <div>${{t.companyLabel}}:</div><div>${{customerData.company}}</div>
                                        <div>${{t.contactLabel}}:</div><div>${{customerData.contact}}</div>
                                        <div>${{t.phoneLabel}}:</div><div>${{customerData.phone}}</div>
                                        <div>${{t.emailLabel}}:</div><div>${{customerData.email}}</div>
                                        <div>${{t.addressLabel}}:</div><div>${{customerData.address}}</div>
                                    </div>
                                </div>
                                <div class="info-section">
                                    <h3>${{t.documentInfoTitle}}</h3>
                                    <div class="info-compact">
                                        <div>${{t.validityLabel}}:</div><div>30일</div>
                                        <div>${{t.paymentLabel}}:</div><div>현금</div>
                                        <div>${{t.deliveryLabel}}:</div><div>즉시</div>
                                        <div>${{t.managerLabel}}:</div><div>김철수</div>
                                    </div>
                                </div>
                            </div>
                            
                            <table class="items-table">
                                <thead>
                                    <tr>
                                        <th width="5%">${{t.noHeader}}</th>
                                        <th width="20%">${{t.itemHeader}}</th>
                                        <th width="25%">${{t.specHeader}}</th>
                                        <th width="8%">${{t.qtyHeader}}</th>
                                        <th width="8%">${{t.unitHeader}}</th>
                                        <th width="12%">${{t.priceHeader}}</th>
                                        <th width="12%">${{t.amountHeader}}</th>
                                        <th width="10%">${{t.remarkHeader}}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{sampleItems.map((item, index) => `
                                        <tr>
                                            <td>${{index + 1}}</td>
                                            <td>${{item.name}}</td>
                                            <td>${{item.spec}}</td>
                                            <td>${{item.qty}}</td>
                                            <td>${{item.unit}}</td>
                                            <td>${{item.price.toLocaleString()}}</td>
                                            <td>${{(item.qty * item.price).toLocaleString()}}</td>
                                            <td>${{item.remark}}</td>
                                        </tr>
                                    `).join('')}}
                                </tbody>
                            </table>
                            
                            <div class="totals-section">
                                <table class="totals-table">
                                    <tr>
                                        <td class="label">${{t.subtotalLabel}}</td>
                                        <td class="amount">${{subtotal.toLocaleString()}}</td>
                                    </tr>
                                    <tr>
                                        <td class="label">${{t.vatLabel}} (${{vatRate}}%)</td>
                                        <td class="amount">${{vatAmount.toLocaleString()}}</td>
                                    </tr>
                                    <tr>
                                        <td class="label">${{t.shippingLabel}}</td>
                                        <td class="amount">0</td>
                                    </tr>
                                    <tr class="total-final">
                                        <td class="label">${{t.totalLabel}}</td>
                                        <td class="amount">${{total.toLocaleString()}}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <div class="signature-section">
                                <div class="signature-box">
                                    <div class="signature-title">${{t.supplierSignature}}</div>
                                    <div class="signature-line"></div>
                                    <div>날짜: ___________</div>
                                </div>
                                <div class="signature-box">
                                    <div class="signature-title">${{t.customerSignature}}</div>
                                    <div class="signature-line"></div>
                                    <div>날짜: ___________</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="print-controls">
                            <button class="print-btn" onclick="window.print()">🖨️ 프린트</button>
                            <button class="print-btn close-btn" onclick="window.close()">✕ 닫기</button>
                        </div>
                    </div>
                </body>
                </html>
            `;
        }}

        // 유효성 검사 후 프린트
        function validateAndPrint() {{
            const t = translations[currentLanguage];
            const errors = [];
            
            // 고객 정보 검사
            const customerCompany = document.getElementById('customerCompany').textContent;
            if (!customerCompany || customerCompany.trim() === '') {{
                errors.push('고객 정보가 없습니다.');
            }}
            
            // 품목 검사
            const items = document.querySelectorAll('#itemsTableBody tr');
            if (items.length === 0) {{
                errors.push('품목이 없습니다.');
            }}
            
            if (errors.length > 0) {{
                alert('다음 오류를 수정해주세요:\\n\\n' + errors.join('\\n'));
                return;
            }}
            
            alert('유효성 검사를 통과했습니다. 프린트를 시작합니다.');
            printDocument();
        }}

        // 키보드 단축키
        document.addEventListener('keydown', function(e) {{
            if (e.ctrlKey && e.key === 'p') {{
                e.preventDefault();
                printDocument();
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html_content