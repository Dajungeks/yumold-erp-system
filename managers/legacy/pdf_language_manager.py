"""
PDF 템플릿 다국어 지원 관리자
고정 항목들을 영어, 베트남어, 태국어, 한국어로 번역 제공
"""

class PDFLanguageManager:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'vi': 'Tiếng Việt',
            'th': 'ไทย',
            'ko': '한국어'
        }
        
        # PDF 템플릿 고정 항목 다국어 번역
        self.translations = {
            # 헤더 정보
            'quotation': {
                'en': 'QUOTATION',
                'vi': 'BÁO GIÁ',
                'th': 'ใบเสนอราคา',
                'ko': '견적서'
            },
            'invoice': {
                'en': 'INVOICE',
                'vi': 'HÓA ĐƠN',
                'th': 'ใบแจ้งหนี้',
                'ko': '송장'
            },
            'company_name': {
                'en': 'YUMOLD VIETNAM CO., LTD.',
                'vi': 'CÔNG TY TNHH YUMOLD VIỆT NAM',
                'th': 'บริษัท ยูโมลด์ เวียดนาม จำกัด',
                'ko': '유몰드 베트남 유한회사'
            },
            
            # 고객 정보
            'customer_name': {
                'en': 'Customer Name',
                'vi': 'Tên Khách Hàng',
                'th': 'ชื่อลูกค้า',
                'ko': '고객명'
            },
            'contact_person': {
                'en': 'Contact Person',
                'vi': 'Người Liên Hệ',
                'th': 'ผู้ติดต่อ',
                'ko': '담당자'
            },
            'address': {
                'en': 'Address',
                'vi': 'Địa Chỉ',
                'th': 'ที่อยู่',
                'ko': '주소'
            },
            'phone': {
                'en': 'Phone',
                'vi': 'Điện Thoại',
                'th': 'โทรศัพท์',
                'ko': '전화번호'
            },
            'email': {
                'en': 'Email',
                'vi': 'Email',
                'th': 'อีเมล',
                'ko': '이메일'
            },
            
            # 견적서 정보
            'quotation_number': {
                'en': 'Quotation No.',
                'vi': 'Số Báo Giá',
                'th': 'เลขที่ใบเสนอราคา',
                'ko': '견적번호'
            },
            'quotation_date': {
                'en': 'Date',
                'vi': 'Ngày',
                'th': 'วันที่',
                'ko': '날짜'
            },
            'valid_until': {
                'en': 'Valid Until',
                'vi': 'Có Hiệu Lực Đến',
                'th': 'มีผลถึง',
                'ko': '유효기한'
            },
            'prepared_by': {
                'en': 'Prepared By',
                'vi': 'Người Lập',
                'th': 'ผู้จัดทำ',
                'ko': '작성자'
            },
            
            # 제품 테이블 헤더
            'item_no': {
                'en': 'Item No.',
                'vi': 'STT',
                'th': 'ลำดับ',
                'ko': '번호'
            },
            'product_code': {
                'en': 'Product Code',
                'vi': 'Mã Sản Phẩm',
                'th': 'รหัสสินค้า',
                'ko': '제품코드'
            },
            'product_name': {
                'en': 'Product Name',
                'vi': 'Tên Sản Phẩm',
                'th': 'ชื่อสินค้า',
                'ko': '제품명'
            },
            'description': {
                'en': 'Description',
                'vi': 'Mô Tả',
                'th': 'รายละเอียด',
                'ko': '설명'
            },
            'quantity': {
                'en': 'Quantity',
                'vi': 'Số Lượng',
                'th': 'จำนวน',
                'ko': '수량'
            },
            'unit': {
                'en': 'Unit',
                'vi': 'Đơn Vị',
                'th': 'หน่วย',
                'ko': '단위'
            },
            'unit_price': {
                'en': 'Unit Price',
                'vi': 'Đơn Giá',
                'th': 'ราคาต่อหน่วย',
                'ko': '단가'
            },
            'total_price': {
                'en': 'Total Price',
                'vi': 'Thành Tiền',
                'th': 'รวมเงิน',
                'ko': '합계금액'
            },
            
            # 합계 정보
            'subtotal': {
                'en': 'Subtotal',
                'vi': 'Tạm Tính',
                'th': 'รวมย่อย',
                'ko': '소계'
            },
            'tax': {
                'en': 'Tax (VAT)',
                'vi': 'Thuế VAT',
                'th': 'ภาษี',
                'ko': '세금'
            },
            'discount': {
                'en': 'Discount',
                'vi': 'Giảm Giá',
                'th': 'ส่วนลด',
                'ko': '할인'
            },
            'total_amount': {
                'en': 'Total Amount',
                'vi': 'Tổng Cộng',
                'th': 'ยอดรวม',
                'ko': '총금액'
            },
            
            # 결제 정보
            'payment_terms': {
                'en': 'Payment Terms',
                'vi': 'Điều Kiện Thanh Toán',
                'th': 'เงื่อนไขการชำระเงิน',
                'ko': '결제조건'
            },
            'delivery_terms': {
                'en': 'Delivery Terms',
                'vi': 'Điều Kiện Giao Hàng',
                'th': 'เงื่อนไขการส่งมอบ',
                'ko': '배송조건'
            },
            'warranty': {
                'en': 'Warranty',
                'vi': 'Bảo Hành',
                'th': 'การรับประกัน',
                'ko': '보증'
            },
            
            # 푸터 정보
            'thank_you': {
                'en': 'Thank you for your business!',
                'vi': 'Cảm ơn quý khách đã hợp tác!',
                'th': 'ขอบคุณที่ให้ความไว้วางใจ!',
                'ko': '거래해 주셔서 감사합니다!'
            },
            'signature': {
                'en': 'Authorized Signature',
                'vi': 'Chữ Ký Người Đại Diện',
                'th': 'ลายเซ็นผู้มีอำนาจ',
                'ko': '서명'
            },
            'stamp': {
                'en': 'Company Stamp',
                'vi': 'Dấu Công Ty',
                'th': 'ตราประทับบริษัท',
                'ko': '회사직인'
            },
            
            # 통화 표시
            'currency_usd': {
                'en': 'USD',
                'vi': 'USD',
                'th': 'ดอลลาร์สหรัฐ',
                'ko': '달러'
            },
            'currency_vnd': {
                'en': 'VND',
                'vi': 'VNĐ',
                'th': 'เวียดนามดอง',
                'ko': '베트남동'
            },
            'currency_thb': {
                'en': 'THB',
                'vi': 'THB',
                'th': 'บาท',
                'ko': '태국바트'
            },
            'currency_krw': {
                'en': 'KRW',
                'vi': 'KRW',
                'th': 'วอนเกาหลี',
                'ko': '원'
            },
            
            # 기타 정보
            'notes': {
                'en': 'Notes',
                'vi': 'Ghi Chú',
                'th': 'หมายเหตุ',
                'ko': '비고'
            },
            'terms_conditions': {
                'en': 'Terms & Conditions',
                'vi': 'Điều Khoản & Điều Kiện',
                'th': 'ข้อกำหนดและเงื่อนไข',
                'ko': '약관 및 조건'
            }
        }
    
    def get_supported_languages(self):
        """지원되는 언어 목록을 반환합니다."""
        return self.supported_languages
    
    def get_text(self, key, language='en'):
        """특정 언어의 텍스트를 반환합니다."""
        if key in self.translations:
            return self.translations[key].get(language, self.translations[key]['en'])
        return key
    
    def get_all_texts(self, language='en'):
        """특정 언어의 모든 텍스트를 딕셔너리로 반환합니다."""
        result = {}
        for key, translations in self.translations.items():
            result[key] = translations.get(language, translations['en'])
        return result
    
    def validate_language(self, language):
        """언어 코드가 유효한지 확인합니다."""
        return language in self.supported_languages
    
    def get_language_name(self, language_code):
        """언어 코드에 해당하는 언어명을 반환합니다."""
        return self.supported_languages.get(language_code, 'Unknown')