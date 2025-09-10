"""
고객 데이터 구조 업데이트 스크립트
- detail_address 필드 추가
- 사업 유형을 새로운 카테고리로 업데이트
"""

import pandas as pd
import os
from datetime import datetime

def update_customer_structure():
    """고객 데이터 구조를 업데이트합니다."""
    
    data_file = "data/customers.csv"
    
    # 백업 생성
    if os.path.exists(data_file):
        backup_file = f"backups/customers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs("backups", exist_ok=True)
        
        # 기존 파일 백업
        import shutil
        shutil.copy2(data_file, backup_file)
        print(f"기존 고객 데이터 백업: {backup_file}")
        
        # 기존 데이터 로드
        df = pd.read_csv(data_file, encoding='utf-8-sig')
        print(f"기존 데이터 로드 완료: {len(df)}개 레코드")
        
        # detail_address 필드 추가 (없을 경우)
        if 'detail_address' not in df.columns:
            df['detail_address'] = ''
            print("detail_address 필드 추가 완료")
        
        # 사업 유형 매핑
        old_to_new_business_types = {
            '제조업': '금형산업',
            '무역업': '트레이드',
            '유통업': '트레이드',
            '서비스업': '기타',
            'IT/소프트웨어': '기타',
            '건설업': '기타',
            '운송업': '기타',
            '금융업': '기타',
            '기타': '기타'
        }
        
        # 사업 유형 업데이트
        df['business_type'] = df['business_type'].map(old_to_new_business_types).fillna('기타')
        print("사업 유형 카테고리 업데이트 완료")
        
        # 전체 컬럼 정의 (최신 구조)
        all_columns = [
            'customer_id', 'company_name', 'contact_person', 'contact_phone', 
            'contact_email', 'address', 'detail_address', 'country', 'city', 'business_type',
            'tax_id', 'notes', 'status', 'input_date', 'updated_date', 'position',
            'company_size', 'annual_revenue', 'customer_grade', 'payment_terms',
            'website', 'fax', 'secondary_contact', 'main_products', 
            'special_requirements', 'kam_manager', 'relationship_level',
            'communication_frequency', 'last_meeting_date', 'potential_value',
            'decision_maker', 'decision_process', 'competitive_status',
            'sales_strategy', 'cross_sell_opportunity', 'growth_potential', 'risk_factors'
        ]
        
        # 누락된 컬럼 추가
        for col in all_columns:
            if col not in df.columns:
                df[col] = ''
        
        # 컬럼 순서 재정렬
        df = df.reindex(columns=all_columns)
        
        # 업데이트된 데이터 저장
        df.to_csv(data_file, index=False, encoding='utf-8-sig')
        print(f"고객 데이터 구조 업데이트 완료: {len(df)}개 레코드")
        
        # 업데이트 통계
        business_type_counts = df['business_type'].value_counts()
        print("\n사업 유형별 고객 수:")
        for bt, count in business_type_counts.items():
            print(f"  - {bt}: {count}개")
            
    else:
        print("고객 데이터 파일이 존재하지 않습니다.")

if __name__ == "__main__":
    update_customer_structure()