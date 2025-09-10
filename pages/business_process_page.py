"""
비즈니스 프로세스 관리 페이지
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def show_business_process_page(business_process_manager, quotation_manager, user_permissions, get_text, hide_header=False):
    """비즈니스 프로세스 관리 메인 페이지"""
    if not hide_header:
        st.title(f"🔄 {get_text('business_process_management')}")
    
    # 탭 생성
    tab_names = [f"📊 {get_text('workflow_overview')}", f"📋 {get_text('task_assignment')}", f"📈 {get_text('process_analytics')}", f"➕ {get_text('workflow_creation')}"]
    
    # 탭 컨테이너 생성
    tabs = st.tabs(tab_names)
    
    # 각 탭의 내용 구현
    with tabs[0]:  # 워크플로우 현황
        show_workflow_status(business_process_manager, get_text)
    
    with tabs[1]:  # 단계별 관리
        show_stage_management(business_process_manager, get_text)
    
    with tabs[2]:  # 프로세스 통계
        show_process_statistics(business_process_manager, get_text)
    
    with tabs[3]:  # 워크플로우 생성
        show_workflow_creation(business_process_manager, quotation_manager, get_text)


def show_workflow_status(business_process_manager, get_text=lambda x: x):
    """워크플로우 현황 탭 내용"""
    st.header(f"📊 {get_text('workflow_overview')}")
    
    # 모든 워크플로우 가져오기
    workflows_df = business_process_manager.get_all_workflows()
    
    # 디버그 정보 출력
    st.info(get_text("total_workflows_registered").format(count=len(workflows_df)))
    
    if len(workflows_df) > 0:
        # DataFrame을 딕셔너리 리스트로 변환
        workflows = workflows_df.to_dict('records')
        # 현재 단계별 분류
        current_stage = st.selectbox(
            get_text("stage_filtering"),
            [get_text("all")] + [
                get_text("quotation_approval"), 
                get_text("purchase_order_creation"), 
                get_text("inventory_receiving"), 
                get_text("shipping_preparation"), 
                get_text("invoice_issuance"), 
                get_text("payment_completion")
            ]
        )
        
        if current_stage != get_text("all"):
            filtered_workflows = [w for w in workflows if w.get('current_stage') == current_stage]
        else:
            filtered_workflows = workflows
        
        if len(filtered_workflows) > 0:
            for workflow in filtered_workflows:
                with st.expander(f"{workflow['quotation_number']} - {workflow['customer_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**{get_text('quotation_number')}:** {workflow['quotation_number']}")
                        st.write(f"**{get_text('customer_name')}:** {workflow['customer_name']}")
                        st.write(f"**{get_text('total_amount_usd')}:** ${workflow.get('total_amount_usd', 0):,.2f}")
                    
                    with col2:
                        st.write(f"**{get_text('created_date_label')}:** {workflow.get('created_date', '')}")
                        st.write(f"**{get_text('current_stage')}:** {workflow.get('current_stage', '')}")
                        st.write(f"**{get_text('status')}:** {workflow.get('status', '')}")
                    
                    # 단계 진행 및 편집 버튼
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if workflow.get('status') != "완료" and st.button(get_text("advance_to_next_stage"), key=f"advance_{workflow['workflow_id']}"):
                            completed_by = st.session_state.get('user_id', 'system')
                            success = business_process_manager.advance_workflow_stage(
                                workflow['workflow_id'], 
                                completed_by, 
                                get_text("manual_progress")
                            )
                            if success:
                                st.success(get_text("stage_advanced_success"))
                                st.rerun()
                            else:
                                st.error(get_text("stage_advance_failed"))
                    
                    with col_btn2:
                        if st.button(get_text("edit"), key=f"edit_{workflow['workflow_id']}"):
                            st.session_state['edit_workflow_id'] = workflow['workflow_id']
                            st.rerun()
                    
                    with col_btn3:
                        if st.button(get_text("delete"), key=f"delete_{workflow['workflow_id']}", type="secondary"):
                            st.session_state['delete_workflow_id'] = workflow['workflow_id']
                            st.rerun()
        else:
            st.warning(get_text("no_matching_workflows"))
    else:
        st.warning(get_text("no_registered_workflows"))
    
    # 편집 모달 표시
    if 'edit_workflow_id' in st.session_state:
        show_edit_workflow_modal(business_process_manager, st.session_state['edit_workflow_id'])
    
    # 삭제 확인 모달 표시
    if 'delete_workflow_id' in st.session_state:
        show_delete_workflow_modal(business_process_manager, st.session_state['delete_workflow_id'])


def show_stage_management(business_process_manager):
    """단계별 관리 탭 내용"""
    st.header(f"📋 {get_text('stage_management')}")
    
    # 단계별 탭 생성
    tabs = st.tabs([
        get_text("quotation_approval"), 
        get_text("purchase_order_creation"), 
        get_text("inventory_receiving"), 
        get_text("shipping_preparation"), 
        get_text("invoice_issuance"), 
        get_text("payment_completion")
    ])
    
    stage_names = [
        get_text("quotation_approval"), 
        get_text("purchase_order_creation"), 
        get_text("inventory_receiving"), 
        get_text("shipping_preparation"), 
        get_text("invoice_issuance"), 
        get_text("payment_completion")
    ]
    
    for i, tab in enumerate(tabs):
        with tab:
            stage_name = stage_names[i]
            st.subheader(f"{stage_name} {get_text('waiting_list')}")
            
            stage_workflows = business_process_manager.get_workflows_by_stage(stage_name)
            
            if len(stage_workflows) > 0:
                for workflow in stage_workflows:
                    with st.expander(f"{workflow['quotation_number']} - {workflow['customer_name']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**{get_text('quotation_number')}:** {workflow['quotation_number']}")
                            st.write(f"**{get_text('customer_name')}:** {workflow['customer_name']}")
                            st.write(f"**{get_text('total_amount')}:** ${workflow.get('total_amount_usd', 0):,.2f}")
                        
                        with col2:
                            st.write(f"**{get_text('created_date_label')}:** {workflow.get('created_date', '')}")
                            st.write(f"**단계 시작일:** {workflow.get('stage_start_date', '')}")
                            
                        # 단계 완료 버튼
                        if st.button(f"{stage_name} 완료", key=f"complete_{stage_name}_{workflow['workflow_id']}"):
                            completed_by = st.session_state.get('user_id', 'system')
                            success = business_process_manager.advance_workflow_stage(
                                workflow['workflow_id'], 
                                completed_by, 
                                f"{stage_name} 완료"
                            )
                            if success:
                                st.success(f"{stage_name}이(가) 완료되었습니다.")
                                st.rerun()
                            else:
                                st.error("단계 완료에 실패했습니다.")
            else:
                st.info(f"{stage_name} 대기 중인 워크플로우가 없습니다.")


def show_process_statistics(business_process_manager):
    """프로세스 통계 탭 내용"""
    st.header("📈 프로세스 통계")
    
    # 통계 가져오기
    stats = business_process_manager.get_workflow_statistics()
    
    if stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 워크플로우", stats.get('total_workflows', 0))
        
        with col2:
            st.metric("진행 중", stats.get('in_progress', 0))
        
        with col3:
            st.metric("완료", stats.get('completed', 0))
        
        # 단계별 분포 차트
        if 'stage_distribution' in stats:
            stage_data = stats['stage_distribution']
            if stage_data:
                df = pd.DataFrame(list(stage_data.items()), columns=['단계', '워크플로우 수'])
                fig = px.bar(df, x='단계', y='워크플로우 수', title="단계별 워크플로우 분포")
                st.plotly_chart(fig, use_container_width=True)
        
        # 월별 생성 추이
        if 'monthly_creation' in stats:
            monthly_data = stats['monthly_creation']
            if monthly_data:
                df = pd.DataFrame(list(monthly_data.items()), columns=['월', '생성 수'])
                fig = px.line(df, x='월', y='생성 수', title="월별 워크플로우 생성 추이")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("통계 데이터가 없습니다.")


def show_workflow_creation(business_process_manager, quotation_manager):
    """워크플로우 생성 탭 내용"""
    st.header("➕ 워크플로우 생성")
    
    # 견적서 선택
    quotations_df = quotation_manager.get_all_quotations()
    
    if len(quotations_df) > 0:
        # DataFrame을 딕셔너리 리스트로 변환
        quotations = quotations_df.to_dict('records')
        # 승인된 견적서만 필터링 (승인 또는 승인됨 상태)
        approved_quotations = [q for q in quotations if q.get('status') in ['승인', '승인됨']]
        
        if len(approved_quotations) > 0:
            quotation_options = [f"{q['quotation_number']} - {q['customer_name']}" for q in approved_quotations]
            selected_quotation = st.selectbox("승인된 견적서 선택", quotation_options)
            
            if selected_quotation:
                quotation_number = selected_quotation.split(' - ')[0]
                selected_quotation_data = next(q for q in approved_quotations if q['quotation_number'] == quotation_number)
                
                # 견적서 정보 표시
                st.subheader("선택된 견적서 정보")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**견적서 번호:** {selected_quotation_data['quotation_number']}")
                    st.write(f"**고객명:** {selected_quotation_data['customer_name']}")
                
                with col2:
                    st.write(f"**총 금액:** ${selected_quotation_data.get('total_amount_usd', 0):,.2f}")
                    st.write(f"**생성일:** {selected_quotation_data.get('created_date', '')}")
                
                # 워크플로우 생성 버튼
                if st.button("워크플로우 생성"):
                    created_by = st.session_state.get('user_id', 'system')
                    workflow_id = business_process_manager.create_workflow_from_quotation(
                        selected_quotation_data, 
                        created_by
                    )
                    
                    if workflow_id:
                        st.success(f"워크플로우가 생성되었습니다. ID: {workflow_id}")
                        st.rerun()
                    else:
                        st.error("워크플로우 생성에 실패했습니다.")
        else:
            st.warning("승인된 견적서가 없습니다.")
    else:
        st.warning("견적서가 없습니다.")


def show_edit_workflow_modal(business_process_manager, workflow_id):
    """워크플로우 편집 모달"""
    st.subheader("✏️ 워크플로우 편집")
    
    # 현재 워크플로우 정보 가져오기
    workflows_df = business_process_manager.get_all_workflows()
    workflow = workflows_df[workflows_df['workflow_id'] == workflow_id].iloc[0]
    
    with st.form("edit_workflow_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_status = st.selectbox(
                "상태", 
                ["진행중", "완료", "보류", "취소"],
                index=["진행중", "완료", "보류", "취소"].index(workflow.get('status', '진행중'))
            )
            
            new_assigned_sales = st.text_input(
                "판매 담당팀", 
                value=workflow.get('assigned_sales_team', '')
            )
        
        with col2:
            new_assigned_service = st.text_input(
                "서비스 담당팀", 
                value=workflow.get('assigned_service_team', '')
            )
            
            new_notes = st.text_area(
                "메모", 
                value=workflow.get('notes', ''),
                height=100
            )
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            if st.form_submit_button("💾 저장", type="primary"):
                updates = {
                    'status': new_status,
                    'assigned_sales_team': new_assigned_sales,
                    'assigned_service_team': new_assigned_service,
                    'notes': new_notes
                }
                
                success, message = business_process_manager.update_workflow(workflow_id, updates)
                if success:
                    st.success("워크플로우가 성공적으로 업데이트되었습니다!")
                    del st.session_state['edit_workflow_id']
                    st.rerun()
                else:
                    st.error(f"업데이트 실패: {message}")
        
        with col_cancel:
            if st.form_submit_button("❌ 취소"):
                del st.session_state['edit_workflow_id']
                st.rerun()


def show_delete_workflow_modal(business_process_manager, workflow_id):
    """워크플로우 삭제 확인 모달"""
    st.subheader("🗑️ 워크플로우 삭제")
    
    # 현재 워크플로우 정보 가져오기
    workflows_df = business_process_manager.get_all_workflows()
    workflow = workflows_df[workflows_df['workflow_id'] == workflow_id].iloc[0]
    
    st.warning(f"정말로 워크플로우 '{workflow.get('quotation_number', '')} - {workflow.get('customer_name', '')}'를 삭제하시겠습니까?")
    st.error("이 작업은 되돌릴 수 없습니다!")
    
    col_delete, col_cancel = st.columns(2)
    
    with col_delete:
        if st.button("🗑️ 삭제", type="primary"):
            # 워크플로우 삭제
            try:
                workflows_df = workflows_df[workflows_df['workflow_id'] != workflow_id]
                workflows_df.to_csv(business_process_manager.workflow_file, index=False, encoding='utf-8-sig')
                st.success("워크플로우가 삭제되었습니다!")
                del st.session_state['delete_workflow_id']
                st.rerun()
            except Exception as e:
                st.error(f"삭제 실패: {str(e)}")
    
    with col_cancel:
        if st.button("❌ 취소"):
            del st.session_state['delete_workflow_id']
            st.rerun()