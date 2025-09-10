"""
비즈니스 프로세스 관리 페이지 (새 버전)
판매/서비스 전문 회사를 위한 간소화된 프로세스 관리
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

def show_business_process_page(business_process_manager, quotation_manager, user_permissions, get_text):
    """비즈니스 프로세스 관리 메인 페이지"""
    st.title("🔄 비즈니스 프로세스 관리")
    st.markdown("견적서 → 주문 → 발주 → 입고 → 배송 → 납품 → 정산")
    
    # 탭 생성
    tab_names = ["📊 현재 진행 상황", "➕ 워크플로우 생성", "📈 프로세스 통계", "⚙️ 단계별 관리"]
    tabs = st.tabs(tab_names)
    
    # 각 탭의 내용 구현
    with tabs[0]:  # 현재 진행 상황
        show_current_workflows(business_process_manager)
    
    with tabs[1]:  # 워크플로우 생성
        show_workflow_creation(business_process_manager, quotation_manager)
    
    with tabs[2]:  # 프로세스 통계
        show_simple_statistics(business_process_manager)
    
    with tabs[3]:  # 단계별 관리
        show_stage_management_simple(business_process_manager)

def show_current_workflows(business_process_manager):
    """현재 진행 중인 워크플로우 표시"""
    st.header("📊 현재 진행 상황")
    
    try:
        # 모든 워크플로우 가져오기
        workflows_df = business_process_manager.get_all_workflows()
        
        if len(workflows_df) == 0:
            st.info("💡 현재 진행 중인 워크플로우가 없습니다. '워크플로우 생성' 탭에서 새로운 프로세스를 시작하세요.")
            return
        
        # DataFrame을 딕셔너리 리스트로 변환
        workflows = workflows_df.to_dict('records')
        
        # 진행 중인 워크플로우만 필터링
        active_workflows = [w for w in workflows if w.get('status') == '진행중']
        
        if len(active_workflows) == 0:
            st.info("현재 진행 중인 워크플로우가 없습니다.")
            return
        
        # 워크플로우별 카드 형태 표시
        for workflow in active_workflows:
            with st.expander(f"🔹 {workflow.get('quotation_number', 'N/A')} - {workflow.get('customer_name', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**📋 기본 정보**")
                    st.write(f"견적번호: {workflow.get('quotation_number', 'N/A')}")
                    st.write(f"고객명: {workflow.get('customer_name', 'N/A')}")
                    st.write(f"금액: ${workflow.get('total_amount_usd', 0):,.2f}")
                
                with col2:
                    st.write("**📅 진행 상황**")
                    st.write(f"현재 단계: {workflow.get('current_stage', 'N/A')}")
                    st.write(f"생성일: {workflow.get('created_date', 'N/A')}")
                    st.write(f"상태: {workflow.get('status', 'N/A')}")
                
                with col3:
                    st.write("**⚡ 액션**")
                    if st.button("다음 단계로 진행", key=f"advance_{workflow.get('workflow_id')}"):
                        user_id = st.session_state.get('user_id', 'system')
                        success = business_process_manager.advance_workflow_stage(
                            workflow.get('workflow_id'), 
                            user_id
                        )
                        if success:
                            st.success("다음 단계로 진행되었습니다!")
                            st.rerun()
                        else:
                            st.error("단계 진행 중 오류가 발생했습니다.")
                    
                    if st.button("상세 보기", key=f"detail_{workflow.get('workflow_id')}"):
                        show_workflow_details(workflow)
    
    except Exception as e:
        st.error(f"워크플로우 조회 중 오류가 발생했습니다: {str(e)}")

def show_workflow_creation(business_process_manager, quotation_manager):
    """워크플로우 생성 탭"""
    st.header("➕ 워크플로우 생성")
    st.info("💡 승인된 견적서에서 비즈니스 프로세스를 시작합니다.")
    
    try:
        # 견적서 선택
        quotations_data = quotation_manager.get_all_quotations()
        
        # 데이터 타입에 따른 처리
        if isinstance(quotations_data, pd.DataFrame):
            if len(quotations_data) == 0:
                st.warning("견적서가 없습니다. 먼저 견적서를 생성해주세요.")
                return
            quotations = quotations_data.to_dict('records')
        elif isinstance(quotations_data, list):
            if len(quotations_data) == 0:
                st.warning("견적서가 없습니다. 먼저 견적서를 생성해주세요.")
                return
            quotations = quotations_data
        else:
            st.warning("견적서 데이터를 불러올 수 없습니다.")
            return
        
        # 승인된 견적서만 필터링 (승인 또는 승인됨 상태)
        approved_quotations = [q for q in quotations if q.get('status') in ['승인', '승인됨']]
        
        if len(approved_quotations) == 0:
            st.warning("승인된 견적서가 없습니다. 견적 관리에서 견적서를 승인해주세요.")
            return
        
        # 이미 워크플로우가 생성된 견적서 제외
        existing_workflows = business_process_manager.get_all_workflows()
        if len(existing_workflows) > 0:
            existing_workflow_quotations = set()
            if isinstance(existing_workflows, pd.DataFrame):
                existing_workflow_quotations = set(existing_workflows['quotation_number'].tolist())
            else:
                existing_workflow_quotations = set([w.get('quotation_number') for w in existing_workflows])
            
            # 워크플로우가 없는 견적서만 필터링
            available_quotations = [q for q in approved_quotations 
                                  if q.get('quotation_number') not in existing_workflow_quotations]
        else:
            available_quotations = approved_quotations
        
        if len(available_quotations) == 0:
            st.info("모든 승인된 견적서에 대해 이미 워크플로우가 생성되었습니다.")
            return
        
        # 견적서 선택 드롭다운
        quotation_options = [f"{q.get('quotation_number', 'N/A')} - {q.get('customer_name', 'N/A')} (${q.get('total_amount', 0):,.2f})" 
                           for q in available_quotations]
        
        selected_option = st.selectbox("승인된 견적서 선택", ["선택하세요..."] + quotation_options)
        
        if selected_option != "선택하세요...":
            # 선택된 견적서 정보 가져오기
            quotation_number = selected_option.split(" - ")[0]
            selected_quotation = next(q for q in available_quotations if q.get('quotation_number') == quotation_number)
            
            # 견적서 정보 표시
            st.subheader("📋 선택된 견적서 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**견적번호**: {selected_quotation.get('quotation_number', 'N/A')}")
                st.write(f"**고객명**: {selected_quotation.get('customer_name', 'N/A')}")
                st.write(f"**총액**: ${selected_quotation.get('total_amount', 0):,.2f}")
            
            with col2:
                st.write(f"**생성일**: {selected_quotation.get('created_date', 'N/A')}")
                st.write(f"**유효기한**: {selected_quotation.get('valid_until', 'N/A')}")
                st.write(f"**상태**: {selected_quotation.get('status', 'N/A')}")
            
            # 워크플로우 생성 버튼
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🚀 비즈니스 프로세스 시작", type="primary", use_container_width=True):
                    user_id = st.session_state.get('user_id', 'system')
                    workflow_id = business_process_manager.create_workflow_from_quotation(
                        selected_quotation, 
                        user_id
                    )
                    
                    if workflow_id:
                        st.success(f"✅ 비즈니스 프로세스가 시작되었습니다!\n워크플로우 ID: {workflow_id}")
                        st.rerun()
                    else:
                        st.error("❌ 워크플로우 생성에 실패했습니다.")
    
    except Exception as e:
        st.error(f"워크플로우 생성 중 오류가 발생했습니다: {str(e)}")

def show_simple_statistics(business_process_manager):
    """간단한 통계 표시"""
    st.header("📈 프로세스 통계")
    
    try:
        stats = business_process_manager.get_workflow_statistics()
        
        if not stats:
            st.info("통계 데이터가 없습니다.")
            return
        
        # 기본 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("전체 프로젝트", stats.get('total_workflows', 0))
        
        with col2:
            st.metric("진행 중", stats.get('active_workflows', 0))
        
        with col3:
            st.metric("완료", stats.get('completed_workflows', 0))
        
        with col4:
            completion_rate = 0
            if stats.get('total_workflows', 0) > 0:
                completion_rate = (stats.get('completed_workflows', 0) / stats.get('total_workflows', 0)) * 100
            st.metric("완료율", f"{completion_rate:.1f}%")
        
        # 단계별 분포 차트
        if 'stage_distribution' in stats:
            stage_data = stats['stage_distribution']
            if stage_data:
                st.subheader("📊 단계별 분포")
                df_data = list(stage_data.items())
                df = pd.DataFrame(df_data, columns=['단계', '프로젝트 수'])
                fig = px.bar(df, x='단계', y='프로젝트 수', title="현재 단계별 프로젝트 분포")
                st.plotly_chart(fig, use_container_width=True)
        
        # 총 금액 정보
        if stats.get('total_amount', 0) > 0:
            st.subheader("💰 총 프로젝트 금액")
            st.metric("총 금액", f"${stats.get('total_amount', 0):,.2f}")
    
    except Exception as e:
        st.error(f"통계 조회 중 오류가 발생했습니다: {str(e)}")

def show_stage_management_simple(business_process_manager):
    """간단한 단계별 관리"""
    st.header("⚙️ 단계별 관리")
    st.info("각 단계별로 대기 중인 작업들을 확인하고 관리합니다.")
    
    # 9단계 프로세스 정의
    stages = [
        "견적서 승인", "주문 확정", "발주서 생성", 
        "재고 입고", "배송 준비", "납품 완료", 
        "정산 처리"
    ]
    
    for stage in stages:
        with st.expander(f"📋 {stage} 대기 목록"):
            try:
                stage_workflows = business_process_manager.get_workflows_by_stage(stage)
                
                if len(stage_workflows) == 0:
                    st.info(f"{stage} 단계에서 대기 중인 프로젝트가 없습니다.")
                    continue
                
                for workflow in stage_workflows:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{workflow.get('quotation_number', 'N/A')}** - {workflow.get('customer_name', 'N/A')}")
                        st.write(f"금액: ${workflow.get('total_amount_usd', 0):,.2f}")
                    
                    with col2:
                        if st.button("처리 완료", key=f"complete_{workflow.get('workflow_id')}_{stage}"):
                            user_id = st.session_state.get('user_id', 'system')
                            success = business_process_manager.advance_workflow_stage(
                                workflow.get('workflow_id'), 
                                user_id
                            )
                            if success:
                                st.success("단계가 완료되었습니다!")
                                st.rerun()
                            else:
                                st.error("처리 중 오류가 발생했습니다.")
            
            except Exception as e:
                st.error(f"{stage} 단계 조회 중 오류: {str(e)}")

def show_workflow_details(workflow):
    """워크플로우 상세 정보 표시"""
    st.subheader("🔍 워크플로우 상세 정보")
    
    # 기본 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**기본 정보**")
        st.write(f"워크플로우 ID: {workflow.get('workflow_id', 'N/A')}")
        st.write(f"견적번호: {workflow.get('quotation_number', 'N/A')}")
        st.write(f"고객명: {workflow.get('customer_name', 'N/A')}")
        st.write(f"총액: ${workflow.get('total_amount_usd', 0):,.2f}")
    
    with col2:
        st.write("**진행 상황**")
        st.write(f"현재 단계: {workflow.get('current_stage', 'N/A')}")
        st.write(f"상태: {workflow.get('status', 'N/A')}")
        st.write(f"생성일: {workflow.get('created_date', 'N/A')}")
        st.write(f"최종 수정일: {workflow.get('last_updated', 'N/A')}")
    
    # 단계별 진행 상황
    if 'stages' in workflow and workflow['stages']:
        st.write("**단계별 진행 상황**")
        stages = workflow['stages']
        
        for stage in stages:
            status_icon = "✅" if stage.get('status') == '완료' else "🟡" if stage.get('status') == '진행중' else "⚪"
            st.write(f"{status_icon} {stage.get('stage_name', 'N/A')} - {stage.get('status', 'N/A')}")
            if stage.get('completed_date'):
                st.write(f"   완료일: {stage.get('completed_date')}")