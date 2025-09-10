# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from business_process_manager_v2 import BusinessProcessManagerV2
from quotation_manager import QuotationManager
from employee_manager import EmployeeManager

# CSS 스타일 정의
st.markdown("""
<style>
    .workflow-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .workflow-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-weight: bold;
        font-size: 1.1em;
    }
    .workflow-type-sales {
        background: linear-gradient(90deg, #e3f2fd, #bbdefb);
    }
    .workflow-type-service {
        background: linear-gradient(90deg, #f3e5f5, #e1bee7);
    }
    .workflow-type-mixed {
        background: linear-gradient(90deg, #fff3e0, #ffcc80);
    }
    .progress-bar {
        background-color: #f0f0f0;
        border-radius: 10px;
        height: 20px;
        margin: 5px 0;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    .progress-sales {
        background: linear-gradient(90deg, #2196f3, #1976d2);
    }
    .progress-service {
        background: linear-gradient(90deg, #9c27b0, #7b1fa2);
    }
    .button-group {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stage-indicator {
        display: flex;
        align-items: center;
        margin: 5px 0;
    }
    .stage-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .stage-completed {
        background-color: #4caf50;
    }
    .stage-active {
        background-color: #ff9800;
    }
    .stage-waiting {
        background-color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_managers():
    """매니저 클래스들 초기화"""
    if 'bp_manager_v2' not in st.session_state:
        st.session_state.bp_manager_v2 = BusinessProcessManagerV2()
    if 'quotation_manager' not in st.session_state:
        st.session_state.quotation_manager = QuotationManager()
    if 'employee_manager' not in st.session_state:
        st.session_state.employee_manager = EmployeeManager()

def render_progress_bar(progress, process_type):
    """진행률 바 렌더링"""
    progress_class = f"progress-{process_type}"
    return f"""
    <div class="progress-bar">
        <div class="progress-fill {progress_class}" style="width: {progress}%"></div>
    </div>
    <small>{progress:.1f}%</small>
    """

def render_workflow_card(workflow):
    """워크플로우 카드 렌더링"""
    workflow_type = workflow['workflow_type']
    type_class = f"workflow-type-{workflow_type}"
    
    # 워크플로우 타입별 아이콘
    type_icons = {
        'sales': '📈',
        'service': '🔧', 
        'mixed': '🔄'
    }
    
    type_names = {
        'sales': '판매',
        'service': '서비스',
        'mixed': '복합'
    }
    
    card_html = f"""
    <div class="workflow-card {type_class}">
        <div class="workflow-header">
            <span>{type_icons[workflow_type]} {workflow['quotation_number']} - {workflow['customer_name']}</span>
            <span>타입: {type_names[workflow_type]}</span>
        </div>
        <div style="margin-bottom: 10px;">
            <strong>제품:</strong> {', '.join(json.loads(workflow['product_types']))}
        </div>
    """
    
    # 판매 프로세스 진행률
    if workflow['has_sales_items']:
        card_html += f"""
        <div>
            <strong>📈 판매 진행률:</strong>
            {render_progress_bar(workflow['sales_progress'], 'sales')}
            <small>현재: {workflow['sales_current_stage']}</small>
        </div>
        """
    
    # 서비스 프로세스 진행률
    if workflow['has_service_items']:
        card_html += f"""
        <div>
            <strong>🔧 서비스 진행률:</strong>
            {render_progress_bar(workflow['service_progress'], 'service')}
            <small>현재: {workflow['service_current_stage']}</small>
        </div>
        """
    
    # 전체 진행률
    card_html += f"""
        <div>
            <strong>🎯 전체 진행률:</strong>
            {render_progress_bar(workflow['overall_progress'], 'sales')}
        </div>
        <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
            생성일: {workflow['created_date'][:10]} | 최종 업데이트: {workflow['last_updated'][:10]}
        </div>
    </div>
    """
    
    return card_html

def render_stage_progress(stages_json, process_type):
    """단계별 진행 상황 시각화"""
    try:
        stages = json.loads(stages_json)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            for i, stage in enumerate(stages):
                status = stage['status']
                stage_name = stage['stage_name']
                
                if status == '완료':
                    dot_class = 'stage-completed'
                    status_text = '✅'
                elif status == '진행중':
                    dot_class = 'stage-active'
                    status_text = '🔄'
                else:
                    dot_class = 'stage-waiting'
                    status_text = '⏳'
                
                st.markdown(f"""
                <div class="stage-indicator">
                    <div class="stage-dot {dot_class}"></div>
                    <span>{i+1}. {stage_name} {status_text}</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            completed_count = sum(1 for stage in stages if stage['status'] == '완료')
            progress = (completed_count / len(stages)) * 100
            
            fig = go.Figure(data=[
                go.Pie(
                    values=[completed_count, len(stages) - completed_count],
                    labels=['완료', '미완료'],
                    hole=0.7,
                    marker_colors=['#4caf50', '#e0e0e0']
                )
            ])
            fig.update_layout(
                height=200,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False
            )
            fig.add_annotation(
                text=f"{progress:.0f}%",
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"단계 정보 표시 중 오류: {e}")

def main():
    """메인 페이지"""
    st.title("🔄 비즈니스 프로세스 관리 시스템 V2")
    
    # 매니저 초기화
    initialize_managers()
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 프로세스 대시보드",
        "➕ 새 프로세스 생성", 
        "📋 진행중 프로세스 관리",
        "✏️ 프로세스 편집/수정",
        "📈 성과 분석"
    ])
    
    # 탭 1: 프로세스 대시보드
    with tab1:
        render_dashboard_tab()
    
    # 탭 2: 새 프로세스 생성
    with tab2:
        render_creation_tab()
    
    # 탭 3: 진행중 프로세스 관리
    with tab3:
        render_management_tab()
    
    # 탭 4: 프로세스 편집/수정
    with tab4:
        render_editing_tab()
    
    # 탭 5: 성과 분석
    with tab5:
        render_analytics_tab()

def render_dashboard_tab():
    """대시보드 탭 렌더링"""
    st.header("📊 프로세스 현황 대시보드")
    
    # 통계 정보 가져오기
    stats = st.session_state.bp_manager_v2.get_workflow_statistics()
    
    if not stats:
        st.info("아직 생성된 워크플로우가 없습니다.")
        return
    
    # 상단 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 판매 프로세스</h3>
            <h2>{stats.get('sales_workflows', 0)}건</h2>
            <p>진행중</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔧 서비스 프로세스</h3>
            <h2>{stats.get('service_workflows', 0)}건</h2>
            <p>진행중</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔄 복합 프로세스</h3>
            <h2>{stats.get('mixed_workflows', 0)}건</h2>
            <p>진행중</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 평균 진행률</h3>
            <h2>{stats.get('average_progress', 0):.1f}%</h2>
            <p>전체 평균</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 제품 타입별 분포 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 제품 타입별 분포")
        product_dist = stats.get('product_type_distribution', {})
        if product_dist:
            fig = px.pie(
                values=list(product_dist.values()),
                names=list(product_dist.keys()),
                title="제품 타입별 워크플로우 분포"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("제품 데이터가 없습니다.")
    
    with col2:
        st.subheader("📊 프로세스 상태")
        status_data = {
            '활성': stats.get('active_workflows', 0),
            '완료': stats.get('completed_workflows', 0)
        }
        fig = px.bar(
            x=list(status_data.keys()),
            y=list(status_data.values()),
            title="워크플로우 상태별 분포"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 최근 워크플로우 목록
    st.subheader("🕒 최근 업데이트된 워크플로우")
    workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
    
    if len(workflows_df) > 0:
        # 최신 순으로 정렬
        recent_workflows = workflows_df.sort_values('last_updated', ascending=False).head(5)
        
        for _, workflow in recent_workflows.iterrows():
            st.markdown(render_workflow_card(workflow), unsafe_allow_html=True)
    else:
        st.info("표시할 워크플로우가 없습니다.")

def render_creation_tab():
    """새 프로세스 생성 탭"""
    st.header("➕ 새 워크플로우 생성")
    
    # 승인된 견적서 목록 가져오기
    quotations_df = st.session_state.quotation_manager.get_all_quotations()
    approved_quotations = quotations_df[quotations_df['status'] == 'approved']
    
    if len(approved_quotations) == 0:
        st.warning("승인된 견적서가 없습니다. 먼저 견적서를 승인해주세요.")
        return
    
    # 견적서 선택
    st.subheader("1. 견적서 선택")
    quotation_options = {}
    for _, quot in approved_quotations.iterrows():
        display_text = f"{quot['quotation_number']} - {quot['customer_name']} ({quot['total_amount_usd']:,.0f} USD)"
        quotation_options[display_text] = quot['quotation_id']
    
    selected_quotation_display = st.selectbox(
        "승인된 견적서를 선택하세요:",
        options=list(quotation_options.keys())
    )
    
    if selected_quotation_display:
        selected_quotation_id = quotation_options[selected_quotation_display]
        selected_quotation = approved_quotations[approved_quotations['quotation_id'] == selected_quotation_id].iloc[0]
        
        # 선택된 견적서 정보 표시
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **견적서 정보**
            - 번호: {selected_quotation['quotation_number']}
            - 고객: {selected_quotation['customer_name']}
            - 금액: {selected_quotation['total_amount_usd']:,.0f} USD
            - 생성일: {selected_quotation['created_date'][:10]}
            """)
        
        with col2:
            # 제품 분석 결과 표시
            analysis_result = st.session_state.bp_manager_v2.analyze_quotation_products(selected_quotation_id)
            
            if analysis_result['success']:
                product_info = analysis_result['data']
                st.success(f"""
                **자동 분석 결과**
                - 제품 타입: {', '.join(product_info['product_types'])}
                - 판매 제품: {'있음' if product_info['has_sales_items'] else '없음'}
                - 서비스 제품: {'있음' if product_info['has_service_items'] else '없음'}
                - 프로세스 타입: {product_info['workflow_type'].upper()}
                """)
                
                # 워크플로우 생성 버튼
                st.subheader("2. 워크플로우 생성")
                
                col1, col2 = st.columns(2)
                with col1:
                    sales_team = st.selectbox("판매팀 담당자:", ['영업1팀', '영업2팀', '해외영업팀'])
                    
                with col2:
                    service_team = st.selectbox("서비스팀 담당자:", ['기술팀', '설치팀', '유지보수팀'])
                
                notes = st.text_area("초기 메모:", placeholder="워크플로우 생성 시 특이사항이나 메모를 입력하세요.")
                
                if st.button("🚀 워크플로우 생성", type="primary", use_container_width=True):
                    # 워크플로우 생성
                    success, message = st.session_state.bp_manager_v2.create_workflow_from_quotation(
                        quotation_id=selected_quotation_id,
                        assigned_sales_team=sales_team,
                        assigned_service_team=service_team,
                        notes=notes
                    )
                    
                    if success:
                        st.success(message)
                        
                        
                        # 생성된 워크플로우 정보 표시
                        new_workflow = st.session_state.bp_manager_v2.get_workflow_by_quotation_id(selected_quotation_id)
                        if new_workflow is not None:
                            st.subheader("✅ 생성된 워크플로우")
                            st.markdown(render_workflow_card(new_workflow), unsafe_allow_html=True)
                    else:
                        st.error(message)
            else:
                st.error(f"제품 분석 실패: {analysis_result['message']}")

def render_management_tab():
    """진행중 프로세스 관리 탭"""
    st.header("📋 진행중 프로세스 관리")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        workflow_type_filter = st.selectbox(
            "프로세스 타입:",
            ["전체", "판매", "서비스", "복합"],
            key="mgmt_type_filter"
        )
    
    with col2:
        status_filter = st.selectbox(
            "상태:",
            ["전체", "활성", "완료"],
            key="mgmt_status_filter"
        )
    
    with col3:
        sort_option = st.selectbox(
            "정렬:",
            ["최신순", "오래된순", "진행률높은순", "진행률낮은순"],
            key="mgmt_sort"
        )
    
    # 워크플로우 목록 가져오기
    workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
    
    if len(workflows_df) == 0:
        st.info("생성된 워크플로우가 없습니다.")
        return
    
    # 필터링 적용
    filtered_df = workflows_df.copy()
    
    # 타입 필터
    type_mapping = {"판매": "sales", "서비스": "service", "복합": "mixed"}
    if workflow_type_filter != "전체":
        filtered_df = filtered_df[filtered_df['workflow_type'] == type_mapping[workflow_type_filter]]
    
    # 상태 필터
    status_mapping = {"활성": "active", "완료": "completed"}
    if status_filter != "전체":
        filtered_df = filtered_df[filtered_df['overall_status'] == status_mapping[status_filter]]
    
    # 정렬
    if sort_option == "최신순":
        filtered_df = filtered_df.sort_values('last_updated', ascending=False)
    elif sort_option == "오래된순":
        filtered_df = filtered_df.sort_values('created_date', ascending=True)
    elif sort_option == "진행률높은순":
        filtered_df = filtered_df.sort_values('overall_progress', ascending=False)
    elif sort_option == "진행률낮은순":
        filtered_df = filtered_df.sort_values('overall_progress', ascending=True)
    
    st.write(f"총 {len(filtered_df)}개의 워크플로우")
    
    # 워크플로우 카드들 표시
    for _, workflow in filtered_df.iterrows():
        with st.container():
            # 워크플로우 기본 정보 카드
            st.markdown(render_workflow_card(workflow), unsafe_allow_html=True)
            
            # 상세 조작 버튼들
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"📝 상세보기", key=f"detail_{workflow['workflow_id']}"):
                    st.session_state[f"show_detail_{workflow['workflow_id']}"] = True
            
            with col2:
                if workflow['has_sales_items'] and workflow['sales_current_stage'] != '정산 완료':
                    if st.button(f"📈 판매 진행", key=f"advance_sales_{workflow['workflow_id']}"):
                        success, message = st.session_state.bp_manager_v2.advance_sales_stage(
                            workflow['workflow_id'], 
                            st.session_state.get('current_user', 'system')
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            with col3:
                if workflow['has_service_items'] and workflow['service_current_stage'] != '비용 정산 완료':
                    # 서비스 진행 버튼 (특별 처리)
                    current_stage = workflow['service_current_stage']
                    if current_stage == '비용 정산 대기중':
                        # 승인/거부 선택 버튼
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            if st.button(f"✅ 승인", key=f"approve_{workflow['workflow_id']}"):
                                success, message = st.session_state.bp_manager_v2.advance_service_stage_with_decision(
                                    workflow['workflow_id'], 'approve', st.session_state.get('current_user', 'system')
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        with subcol2:
                            if st.button(f"❌ 거부", key=f"reject_{workflow['workflow_id']}"):
                                success, message = st.session_state.bp_manager_v2.advance_service_stage_with_decision(
                                    workflow['workflow_id'], 'reject', st.session_state.get('current_user', 'system')
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    else:
                        if st.button(f"🔧 서비스 진행", key=f"advance_service_{workflow['workflow_id']}"):
                            success, message = st.session_state.bp_manager_v2.advance_service_stage(
                                workflow['workflow_id'], 
                                st.session_state.get('current_user', 'system')
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            with col4:
                if st.button(f"✏️ 편집", key=f"edit_{workflow['workflow_id']}"):
                    st.session_state.selected_workflow_for_edit = workflow['workflow_id']
                    st.switch_page("pages/business_process_v2_page.py")
            
            # 상세 정보 표시 (토글)
            if st.session_state.get(f"show_detail_{workflow['workflow_id']}", False):
                st.subheader("📋 상세 단계 진행 상황")
                
                if workflow['has_sales_items']:
                    st.write("**📈 판매 프로세스**")
                    render_stage_progress(workflow['sales_stages_json'], 'sales')
                
                if workflow['has_service_items']:
                    st.write("**🔧 서비스 프로세스**")
                    render_stage_progress(workflow['service_stages_json'], 'service')
                
                if st.button(f"🔼 접기", key=f"hide_detail_{workflow['workflow_id']}"):
                    st.session_state[f"show_detail_{workflow['workflow_id']}"] = False
                    st.rerun()
            
            st.markdown("---")

def render_editing_tab():
    """프로세스 편집/수정 탭"""
    st.header("✏️ 프로세스 편집/수정")
    
    # 워크플로우 선택
    workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
    
    if len(workflows_df) == 0:
        st.info("편집할 워크플로우가 없습니다.")
        return
    
    # 선택된 워크플로우가 있는지 확인
    selected_workflow_id = st.session_state.get('selected_workflow_for_edit', None)
    
    workflow_options = {}
    for _, workflow in workflows_df.iterrows():
        display_text = f"{workflow['quotation_number']} - {workflow['customer_name']} ({workflow['workflow_type'].upper()})"
        workflow_options[display_text] = workflow['workflow_id']
    
    selected_display = st.selectbox(
        "편집할 워크플로우를 선택하세요:",
        options=list(workflow_options.keys()),
        index=list(workflow_options.values()).index(selected_workflow_id) if selected_workflow_id in workflow_options.values() else 0
    )
    
    selected_workflow_id = workflow_options[selected_display]
    selected_workflow = workflows_df[workflows_df['workflow_id'] == selected_workflow_id].iloc[0]
    
    # 기본 정보 편집
    st.subheader("📝 기본 정보 편집")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_sales_team = st.selectbox(
            "판매팀 담당자:",
            ['영업1팀', '영업2팀', '해외영업팀'],
            index=['영업1팀', '영업2팀', '해외영업팀'].index(selected_workflow['assigned_sales_team'])
        )
        
    with col2:
        new_service_team = st.selectbox(
            "서비스팀 담당자:",
            ['기술팀', '설치팀', '유지보수팀'],
            index=['기술팀', '설치팀', '유지보수팀'].index(selected_workflow['assigned_service_team'])
        )
    
    new_notes = st.text_area(
        "메모:",
        value=selected_workflow['notes'],
        height=100
    )
    
    if st.button("💾 기본 정보 저장", type="primary"):
        success, message = st.session_state.bp_manager_v2.update_workflow(
            workflow_id=selected_workflow_id,
            assigned_sales_team=new_sales_team,
            assigned_service_team=new_service_team,
            notes=new_notes
        )
        
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    
    st.markdown("---")
    
    # 단계별 상태 수정
    st.subheader("🔧 단계별 상태 수정")
    
    # 판매 프로세스 단계 수정
    if selected_workflow['has_sales_items']:
        st.write("**📈 판매 프로세스 단계 수정**")
        
        sales_stages = json.loads(selected_workflow['sales_stages_json'])
        
        for i, stage in enumerate(sales_stages):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"{i+1}. {stage['stage_name']}")
            
            with col2:
                new_status = st.selectbox(
                    "상태:",
                    ['대기', '진행중', '완료'],
                    index=['대기', '진행중', '완료'].index(stage['status']),
                    key=f"sales_stage_{i}_status"
                )
            
            with col3:
                if st.button(f"저장", key=f"save_sales_stage_{i}"):
                    # 단계 상태 업데이트 로직
                    st.info("단계 상태가 업데이트되었습니다.")
    
    # 서비스 프로세스 단계 수정
    if selected_workflow['has_service_items']:
        st.write("**🔧 서비스 프로세스 단계 수정**")
        
        service_stages = json.loads(selected_workflow['service_stages_json'])
        
        for i, stage in enumerate(service_stages):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"{i+1}. {stage['stage_name']}")
            
            with col2:
                new_status = st.selectbox(
                    "상태:",
                    ['대기', '진행중', '완료'],
                    index=['대기', '진행중', '완료'].index(stage['status']),
                    key=f"service_stage_{i}_status"
                )
            
            with col3:
                if st.button(f"저장", key=f"save_service_stage_{i}"):
                    # 단계 상태 업데이트 로직
                    st.info("단계 상태가 업데이트되었습니다.")
    
    st.markdown("---")
    
    # 워크플로우 삭제 (위험 구역)
    st.subheader("⚠️ 위험 구역")
    st.warning("아래 작업은 되돌릴 수 없습니다. 신중히 진행해주세요.")
    
    if st.checkbox("워크플로우 삭제 확인"):
        if st.button("🗑️ 워크플로우 삭제", type="secondary"):
            success, message = st.session_state.bp_manager_v2.delete_workflow(selected_workflow_id)
            
            if success:
                st.success(message)
                st.session_state.selected_workflow_for_edit = None
                st.rerun()
            else:
                st.error(message)

def render_analytics_tab():
    """성과 분석 탭"""
    st.header("📈 성과 분석")
    
    workflows_df = st.session_state.bp_manager_v2.get_all_workflows()
    
    if len(workflows_df) == 0:
        st.info("분석할 데이터가 없습니다.")
        return
    
    # 기간 필터
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("시작일:", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("종료일:", value=datetime.now())
    
    # 필터링된 데이터
    workflows_df['created_date'] = pd.to_datetime(workflows_df['created_date'])
    filtered_df = workflows_df[
        (workflows_df['created_date'].dt.date >= start_date) & 
        (workflows_df['created_date'].dt.date <= end_date)
    ]
    
    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체 워크플로우", len(filtered_df))
    
    with col2:
        completed_count = len(filtered_df[filtered_df['overall_status'] == 'completed'])
        st.metric("완료된 워크플로우", completed_count)
    
    with col3:
        if len(filtered_df) > 0:
            completion_rate = (completed_count / len(filtered_df)) * 100
            st.metric("완료율", f"{completion_rate:.1f}%")
        else:
            st.metric("완료율", "0%")
    
    with col4:
        if len(filtered_df) > 0:
            avg_progress = filtered_df['overall_progress'].mean()
            st.metric("평균 진행률", f"{avg_progress:.1f}%")
        else:
            st.metric("평균 진행률", "0%")
    
    # 차트들
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 프로세스 타입별 분포")
        type_counts = filtered_df['workflow_type'].value_counts()
        type_labels = {'sales': '판매', 'service': '서비스', 'mixed': '복합'}
        type_counts.index = [type_labels.get(x, x) for x in type_counts.index]
        
        fig = px.pie(values=type_counts.values, names=type_counts.index)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 월별 생성 추이")
        monthly_data = filtered_df.groupby(filtered_df['created_date'].dt.to_period('M')).size()
        monthly_data.index = monthly_data.index.astype(str)
        
        fig = px.line(x=monthly_data.index, y=monthly_data.values)
        fig.update_layout(xaxis_title="월", yaxis_title="워크플로우 수")
        st.plotly_chart(fig, use_container_width=True)
    
    # 상세 분석 표
    st.subheader("📋 상세 분석 표")
    
    analysis_df = filtered_df[[
        'quotation_number', 'customer_name', 'workflow_type', 
        'overall_progress', 'overall_status', 'created_date', 'total_amount_usd'
    ]].copy()
    
    analysis_df['workflow_type'] = analysis_df['workflow_type'].map(
        {'sales': '판매', 'service': '서비스', 'mixed': '복합'}
    )
    analysis_df['overall_status'] = analysis_df['overall_status'].map(
        {'active': '활성', 'completed': '완료'}
    )
    
    analysis_df.columns = ['견적번호', '고객명', '타입', '진행률(%)', '상태', '생성일', '금액(USD)']
    
    st.dataframe(analysis_df, use_container_width=True)

if __name__ == "__main__":
    main()