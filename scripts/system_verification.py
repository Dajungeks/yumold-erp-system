"""
Ver06 ERP 시스템 전체 검증 스크립트
모든 Manager의 정상 작동 여부, 통계 정확성, 더미 데이터 존재 여부 검증
"""

import pandas as pd
import os
from datetime import datetime
import json

def verify_customer_manager():
    """고객 관리자 검증"""
    print("=" * 60)
    print("🏢 고객 관리자(CustomerManager) 검증")
    print("=" * 60)
    
    try:
        from customer_manager import CustomerManager
        cm = CustomerManager()
        
        # 데이터 로드
        customers = cm.get_all_customers()
        print(f"✓ 총 고객 수: {len(customers)}개")
        
        # 실제 데이터 여부 확인
        if len(customers) > 0:
            sample = customers[0]
            print(f"✓ 샘플 고객: {sample.get('company_name', 'N/A')}")
            print(f"✓ 국가: {sample.get('country', 'N/A')}")
            print(f"✓ 사업유형: {sample.get('business_type', 'N/A')}")
            
            # KAM 정보 확인
            kam_fields = ['kam_manager', 'relationship_level', 'potential_value']
            kam_data = {field: sample.get(field, 'N/A') for field in kam_fields}
            print(f"✓ KAM 정보: {kam_data}")
        
        # 통계 확인
        stats = cm.get_customer_statistics()
        print(f"✓ 통계 - 총 고객: {stats.get('total_customers', 0)}")
        print(f"✓ 통계 - 국가별: {len(stats.get('by_country', {}))}")
        print(f"✓ 통계 - 사업유형별: {len(stats.get('by_business_type', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 고객 관리자 오류: {str(e)}")
        return False

def verify_employee_manager():
    """직원 관리자 검증"""
    print("\n" + "=" * 60)
    print("👥 직원 관리자(EmployeeManager) 검증")
    print("=" * 60)
    
    try:
        from employee_manager import EmployeeManager
        em = EmployeeManager()
        
        # 데이터 로드
        employees = em.get_all_employees()
        print(f"✓ 총 직원 수: {len(employees)}개")
        
        # 실제 데이터 여부 확인
        if len(employees) > 0:
            sample = employees[0]
            print(f"✓ 샘플 직원: {sample.get('name', 'N/A')} ({sample.get('employee_id', 'N/A')})")
            print(f"✓ 부서: {sample.get('department', 'N/A')}")
            print(f"✓ 직급: {sample.get('position', 'N/A')}")
            print(f"✓ 재직상태: {sample.get('work_status', 'N/A')}")
        
        # 활성 직원 수 확인
        try:
            active_count = em.get_active_employee_count()
            print(f"✓ 재직 중 직원 수: {active_count}")
        except Exception as e:
            print(f"❌ 재직 직원 수 조회 오류: {e}")
            return False
        
        # 직급별 통계
        try:
            position_stats = em.get_employee_count_by_position()
            print(f"✓ 직급별 통계: {position_stats}")
        except Exception as e:
            print(f"❌ 직급별 통계 조회 오류: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 직원 관리자 오류: {str(e)}")
        return False

def verify_quotation_manager():
    """견적서 관리자 검증"""
    print("\n" + "=" * 60)
    print("📋 견적서 관리자(QuotationManager) 검증")
    print("=" * 60)
    
    try:
        from quotation_manager import QuotationManager
        qm = QuotationManager()
        
        # 데이터 로드
        quotations = qm.get_all_quotations()
        print(f"✓ 총 견적서 수: {len(quotations)}개")
        
        # 실제 데이터 여부 확인
        if len(quotations) > 0:
            sample = quotations[0]
            print(f"✓ 샘플 견적서: {sample.get('quotation_id', 'N/A')}")
            print(f"✓ 고객명: {sample.get('customer_name', 'N/A')}")
            print(f"✓ 상태: {sample.get('status', 'N/A')}")
            print(f"✓ 총액: {sample.get('total_amount', 'N/A')}")
            
            # 제품 정보 확인
            products = sample.get('products', [])
            if isinstance(products, str):
                try:
                    products = json.loads(products)
                except:
                    products = []
            print(f"✓ 제품 개수: {len(products) if products else 0}")
        
        # 상태별 통계 확인
        draft_count = len([q for q in quotations if q.get('status') == 'draft'])
        sent_count = len([q for q in quotations if q.get('status') == 'sent'])
        approved_count = len([q for q in quotations if q.get('status') == 'approved'])
        
        print(f"✓ 상태별 통계 - 초안: {draft_count}, 발송: {sent_count}, 승인: {approved_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 견적서 관리자 오류: {str(e)}")
        return False

def verify_cash_flow_manager():
    """현금 흐름 관리자 검증"""
    print("\n" + "=" * 60)
    print("💰 현금 흐름 관리자(CashFlowManager) 검증")
    print("=" * 60)
    
    try:
        from cash_flow_manager import CashFlowManager
        cfm = CashFlowManager()
        
        # 데이터 로드
        cfm.load_cash_flow()
        
        # 거래 내역 확인
        transactions = cfm.get_all_transactions()
        print(f"✓ 총 거래 내역: {len(transactions)}개")
        
        # 실제 데이터 여부 확인
        if len(transactions) > 0:
            sample = transactions[0]
            print(f"✓ 샘플 거래: {sample.get('description', 'N/A')}")
            print(f"✓ 금액: ${sample.get('amount', 0):,.2f}")
            print(f"✓ 유형: {sample.get('transaction_type', 'N/A')}")
            print(f"✓ 계좌: {sample.get('account', 'N/A')}")
        
        # 현금 흐름 요약
        try:
            summary = cfm.get_cash_flow_summary()
            print(f"✓ 총 수입: ${summary.get('total_inflow', 0):,.2f}")
            print(f"✓ 총 지출: ${summary.get('total_outflow', 0):,.2f}")
            print(f"✓ 순 현금 흐름: ${summary.get('net_flow', 0):,.2f}")
        except Exception as e:
            print(f"❌ 현금 흐름 요약 오류: {e}")
            return False
        
        # 월별 현금 흐름
        try:
            monthly = cfm.get_monthly_cash_flow()
            if hasattr(monthly, '__len__'):
                print(f"✓ 월별 데이터: {len(monthly)}개월")
            else:
                print(f"✓ 월별 데이터 타입: {type(monthly)}")
        except Exception as e:
            print(f"❌ 월별 현금 흐름 오류: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 현금 흐름 관리자 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_product_managers():
    """제품 관리자들 검증"""
    print("\n" + "=" * 60)
    print("🛠️ 제품 관리자들 검증")
    print("=" * 60)
    
    try:
        # 마스터 제품 관리자
        from master_product_manager import MasterProductManager
        mpm = MasterProductManager()
        
        all_products = mpm.get_all_products()
        print(f"✓ 마스터 제품 총 개수: {len(all_products)}개")
        
        hr_products = mpm.get_products_by_category('HR')
        mb_products = mpm.get_products_by_category('MB')
        print(f"✓ HR 제품: {len(hr_products)}개, MB 제품: {len(mb_products)}개")
        
        # 판매 제품 관리자
        from sales_product_manager import SalesProductManager
        spm = SalesProductManager()
        
        sales_prices = spm.get_all_prices()
        print(f"✓ 판매 가격 설정: {len(sales_prices)}개")
        
        # 공급 제품 관리자
        from supply_product_manager import SupplyProductManager
        supm = SupplyProductManager()
        
        supply_prices = supm.get_all_prices()
        print(f"✓ 공급 가격 설정: {len(supply_prices)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 제품 관리자들 오류: {str(e)}")
        return False

def verify_approval_manager():
    """승인 관리자 검증"""
    print("\n" + "=" * 60)
    print("✅ 승인 관리자(ApprovalManager) 검증")
    print("=" * 60)
    
    try:
        from approval_manager import ApprovalManager
        am = ApprovalManager()
        
        # 모든 요청 확인
        all_requests = am.get_all_requests()
        print(f"✓ 총 승인 요청: {len(all_requests)}개")
        
        # 대기 중 요청
        pending_requests = am.get_pending_requests()
        print(f"✓ 대기 중 요청: {len(pending_requests)}개")
        
        # 실제 데이터 여부 확인
        if len(all_requests) > 0:
            sample = all_requests[0]
            print(f"✓ 샘플 요청: {sample.get('request_type', 'N/A')}")
            print(f"✓ 요청자: {sample.get('requester_name', 'N/A')}")
            print(f"✓ 상태: {sample.get('status', 'N/A')}")
        
        # 통계 확인
        try:
            stats = am.get_approval_statistics()
            print(f"✓ 승인 통계: {stats}")
        except Exception as e:
            print(f"❌ 승인 통계 오류: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 승인 관리자 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_exchange_rate_manager():
    """환율 관리자 검증"""
    print("\n" + "=" * 60)
    print("💱 환율 관리자(ExchangeRateManager) 검증")
    print("=" * 60)
    
    try:
        from exchange_rate_manager import ExchangeRateManager
        erm = ExchangeRateManager()
        
        # 최신 환율 확인
        latest_rates = erm.get_latest_rates()
        print(f"✓ 최신 환율 데이터: {len(latest_rates)}개 통화")
        
        # 주요 통화 환율 확인
        major_currencies = ['VND', 'THB', 'CNY', 'KRW', 'JPY']
        for currency in major_currencies:
            rate = erm.get_rate_by_currency(currency)
            if rate:
                print(f"✓ {currency}: {rate}")
        
        # 지원 통화 목록
        supported = erm.get_supported_currencies()
        print(f"✓ 지원 통화: {len(supported)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 환율 관리자 오류: {str(e)}")
        return False

def check_dummy_data():
    """더미 데이터 존재 여부 검사"""
    print("\n" + "=" * 60)
    print("🔍 더미 데이터 검사")
    print("=" * 60)
    
    dummy_indicators = [
        'test', 'dummy', 'sample', 'example', 'fake', 'mock',
        '테스트', '더미', '샘플', '예시', '가짜'
    ]
    
    # CSV 파일들 검사
    data_files = [
        'data/customers.csv',
        'data/employees.csv', 
        'data/quotations.csv',
        'data/cash_flow_transactions.csv',
        'data/approvals.csv'
    ]
    
    dummy_found = []
    
    for file_path in data_files:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                # 텍스트 컬럼에서 더미 데이터 검색
                text_columns = df.select_dtypes(include=['object']).columns
                
                for col in text_columns:
                    for index, value in df[col].items():
                        if pd.notna(value) and isinstance(value, str):
                            value_lower = value.lower()
                            for indicator in dummy_indicators:
                                if indicator in value_lower:
                                    dummy_found.append({
                                        'file': file_path,
                                        'column': col,
                                        'row': index,
                                        'value': value,
                                        'indicator': indicator
                                    })
                                    
            except Exception as e:
                print(f"❌ {file_path} 검사 중 오류: {str(e)}")
    
    if dummy_found:
        print("⚠️ 더미 데이터 발견:")
        for item in dummy_found[:10]:  # 처음 10개만 표시
            print(f"  - {item['file']} / {item['column']} / Row {item['row']}: {item['value']}")
        
        if len(dummy_found) > 10:
            print(f"  ... 추가 {len(dummy_found) - 10}개 발견")
    else:
        print("✓ 더미 데이터 없음")
    
    return len(dummy_found) == 0

def verify_data_consistency():
    """데이터 일관성 검증"""
    print("\n" + "=" * 60)
    print("🔧 데이터 일관성 검증")
    print("=" * 60)
    
    issues = []
    
    try:
        # 고객 ID와 견적서 고객명 일치성 확인
        from customer_manager import CustomerManager
        from quotation_manager import QuotationManager
        
        cm = CustomerManager()
        qm = QuotationManager()
        
        customers = cm.get_all_customers()
        quotations = qm.get_all_quotations()
        
        customer_names = {c.get('company_name') for c in customers if c.get('company_name')}
        quotation_customers = {q.get('customer_name') for q in quotations if q.get('customer_name')}
        
        orphaned_quotations = quotation_customers - customer_names
        if orphaned_quotations:
            issues.append(f"견적서에 존재하지 않는 고객: {orphaned_quotations}")
        
        print(f"✓ 고객-견적서 연결: {len(customer_names)}개 고객, {len(quotation_customers)}개 견적서 고객")
        
    except Exception as e:
        issues.append(f"고객-견적서 일관성 검사 오류: {str(e)}")
    
    if issues:
        print("⚠️ 일관성 문제 발견:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ 데이터 일관성 양호")
        return True

def main():
    """메인 검증 함수"""
    print("Ver06 ERP 시스템 전체 검증 시작")
    print("=" * 80)
    
    results = {
        'customer_manager': verify_customer_manager(),
        'employee_manager': verify_employee_manager(),
        'quotation_manager': verify_quotation_manager(),
        'cash_flow_manager': verify_cash_flow_manager(),
        'product_managers': verify_product_managers(),
        'approval_manager': verify_approval_manager(),
        'exchange_rate_manager': verify_exchange_rate_manager(),
        'no_dummy_data': check_dummy_data(),
        'data_consistency': verify_data_consistency()
    }
    
    print("\n" + "=" * 80)
    print("🏁 검증 결과 요약")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for component, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{component:20}: {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 검증을 통과했습니다!")
    else:
        print("⚠️ 일부 항목에서 문제가 발견되었습니다.")
    
    return results

if __name__ == "__main__":
    main()