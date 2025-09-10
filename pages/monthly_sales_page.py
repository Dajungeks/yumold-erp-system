"""
월별 매출관리 페이지 - 완전한 월별 매출 분석 및 관리 시스템
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.notification_helper import NotificationHelper

def show_monthly_sales_page(monthly_sales_manager, customer_manager, exchange_rate_manager):
    """월별 매출관리 메인 페이지"""
    
    st.header("📈 월별 매출관리")
    st.markdown("**월별 매출 현황, 분석, 목표 관리를 통합 제공합니다**")
    
    # 탭 구성 (마스터 권한에 따라 목표 설정 탭 추가)
    is_master = st.session_state.get('user_type') == 'master'
    
    if is_master:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 월별 현황",
            "🎯 목표 vs 실적", 
            "👥 고객별 분석",
            "📦 제품별 분석",
            "📈 트렌드 분석",
            "⚙️ 매출 관리",
            "🔧 목표 설정"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 월별 현황",
            "🎯 목표 vs 실적", 
            "👥 고객별 분석",
            "📦 제품별 분석",
            "📈 트렌드 분석",
            "⚙️ 매출 관리"
        ])
        tab7 = None  # 일반 사용자일 때는 None으로 설정
    
    with tab1:
        show_monthly_overview(monthly_sales_manager)
    
    with tab2:
        show_target_vs_actual(monthly_sales_manager)
    
    with tab3:
        show_customer_analysis(monthly_sales_manager)
    
    with tab4:
        show_product_analysis(monthly_sales_manager)
    
    with tab5:
        show_trend_analysis(monthly_sales_manager)
    
    with tab6:
        show_sales_management(monthly_sales_manager, customer_manager)
    
    # 마스터 권한자만 목표 설정 탭 표시
    if is_master and tab7 is not None:
        with tab7:
            show_target_settings(monthly_sales_manager)



def show_monthly_overview(monthly_sales_manager):
    """월별 현황 대시보드"""
    st.subheader("📊 월별 매출 현황")
    
    try:
        # 현재 월과 이전 월 데이터 조회
        current_month = datetime.now().strftime("%Y-%m")
        previous_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
        
        current_data = monthly_sales_manager.get_monthly_sales_summary(current_month)
        previous_data = monthly_sales_manager.get_monthly_sales_summary(previous_month)
        
        # 전체 요약 데이터
        all_summary = monthly_sales_manager.get_monthly_sales_summary()
        
        if len(all_summary) > 0:
            # 현재 월 데이터
            current_sales = current_data[0] if len(current_data) > 0 else {
                'total_sales_usd': 0, 'amount_vnd': 0, 'transaction_count': 0, 
                'quantity': 0, 'avg_profit_margin': 0
            }
            
            # 이전 월 데이터  
            previous_sales = previous_data[0] if len(previous_data) > 0 else {
                'total_sales_usd': 0, 'amount_vnd': 0, 'transaction_count': 0, 
                'quantity': 0, 'avg_profit_margin': 0
            }
            
            # 핵심 지표 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                sales_change = 0
                if previous_sales['amount_vnd'] > 0:
                    sales_change = ((current_sales['amount_vnd'] - previous_sales['amount_vnd']) / previous_sales['amount_vnd']) * 100
                
                st.metric(
                    "이번 달 매출 (VND)",
                    f"{current_sales['amount_vnd']:,.0f}₫",
                    f"{sales_change:+.1f}%"
                )
            
            with col2:
                st.metric(
                    "거래 건수",
                    f"{current_sales['transaction_count']:,}건",
                    f"평균 {current_sales['amount_vnd']/max(current_sales['transaction_count'], 1):,.0f}₫"
                )
            
            with col3:
                margin_change = current_sales['avg_profit_margin'] - previous_sales['avg_profit_margin']
                st.metric(
                    "평균 이익률",
                    f"{current_sales['avg_profit_margin']:.1%}",
                    f"{margin_change:+.1%}"
                )
            
            with col4:
                quantity_change = current_sales['quantity'] - previous_sales['quantity']
                st.metric(
                    "판매 수량",
                    f"{current_sales['quantity']:,}개",
                    f"{quantity_change:+,}개"
                )
            
            st.markdown("---")
            
            # 최근 6개월 매출 차트
            st.markdown("### 📈 최근 6개월 매출 추이")
            
            if len(all_summary) > 0:
                df_chart = pd.DataFrame(all_summary).tail(6)
                
                fig = go.Figure()
                
                # 매출 라인 (VND)
                fig.add_trace(go.Scatter(
                    x=df_chart['year_month'],
                    y=df_chart['amount_vnd'],
                    mode='lines+markers',
                    name='매출 (VND)',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))
                
                # 거래 건수 (보조축)
                fig.add_trace(go.Scatter(
                    x=df_chart['year_month'],
                    y=df_chart['transaction_count'],
                    mode='lines+markers',
                    name='거래 건수',
                    yaxis='y2',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="월별 매출 및 거래 건수 추이",
                    xaxis_title="월",
                    yaxis_title="매출 (VND)",
                    yaxis2=dict(
                        title="거래 건수",
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # 이번 달 상세 분석
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💰 이번 달 상세 현황")
                
                total_revenue = current_sales['total_sales_usd']
                total_cost = current_sales.get('total_cost_usd', total_revenue * 0.7)  # 기본 원가율 70%
                gross_profit = total_revenue - total_cost
                
                # VND 기준으로 계산
                total_revenue_vnd = current_sales['amount_vnd']
                total_cost_vnd = total_revenue_vnd * 0.7  # 기본 원가율 70%
                gross_profit_vnd = total_revenue_vnd - total_cost_vnd
                
                detail_data = {
                    "항목": ["총 매출", "총 원가", "총 이익", "평균 거래액", "평균 이익률"],
                    "금액 (VND)": [
                        f"{total_revenue_vnd:,.0f}₫",
                        f"{total_cost_vnd:,.0f}₫",
                        f"{gross_profit_vnd:,.0f}₫",
                        f"{(total_revenue_vnd/max(current_sales['transaction_count'], 1)):,.0f}₫",
                        f"{current_sales['avg_profit_margin']:.1%}"
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(detail_data),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                st.markdown("### 📊 월별 비교")
                
                comparison_data = {
                    "지표": ["매출 (VND)", "거래 건수", "평균 이익률", "판매 수량"],
                    "이번 달": [
                        f"{current_sales['amount_vnd']:,.0f}₫",
                        f"{current_sales['transaction_count']:,}건",
                        f"{current_sales['avg_profit_margin']:.1%}",
                        f"{current_sales['quantity']:,}개"
                    ],
                    "지난 달": [
                        f"{previous_sales['amount_vnd']:,.0f}₫",
                        f"{previous_sales['transaction_count']:,}건", 
                        f"{previous_sales['avg_profit_margin']:.1%}",
                        f"{previous_sales['quantity']:,}개"
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(comparison_data),
                    use_container_width=True,
                    hide_index=True
                )
        
        else:
            st.info("📋 매출 데이터가 없습니다. 매출 관리 탭에서 데이터를 추가해주세요.")
            
    except Exception as e:
        st.error(f"월별 현황 로드 중 오류: {str(e)}")

def show_target_vs_actual(monthly_sales_manager):
    """목표 vs 실적 분석"""
    st.subheader("🎯 목표 대비 실적 분석")
    
    try:
        # 월 선택
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # 2025년 1월부터 12월까지 선택 가능한 월 목록 생성
            available_months = [f"2025-{str(i).zfill(2)}" for i in range(1, 13)]
            
            # 최신 월부터 역순으로 정렬
            available_months.reverse()
            
            if available_months:
                target_month = st.selectbox(
                    "분석 월 선택 (2025년 1월부터)",
                    options=available_months
                )
            else:
                st.warning("2025년 1월 이후 데이터만 분석 가능합니다.")
                target_month = "2025-01"
        
        # 목표 vs 실적 데이터 조회
        target_data = monthly_sales_manager.get_target_vs_actual(target_month)
        
        if len(target_data) > 0:
            data = target_data[0]  # 선택된 월 데이터
            
            # 핵심 지표 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                target_vnd = data.get('target_amount_vnd', 3200000000)  # 기본 32억동
                st.metric(
                    "목표 매출 (VND)",
                    f"{target_vnd:,.0f}₫"
                )
            
            with col2:
                actual_vnd = data.get('actual_amount_vnd', data.get('actual_amount_usd', 0) * 24500)
                st.metric(
                    "실제 매출 (VND)",
                    f"{actual_vnd:,.0f}₫"
                )
            
            with col3:
                # VND 기준으로 달성률 계산
                achievement_rate = (actual_vnd / target_vnd * 100) if target_vnd > 0 else 0
                variance_vnd = actual_vnd - target_vnd
                
                achievement_color = "normal"
                if achievement_rate >= 100:
                    achievement_color = "inverse"
                elif achievement_rate < 80:
                    achievement_color = "off"
                    
                st.metric(
                    "달성률",
                    f"{achievement_rate:.1f}%",
                    f"{variance_vnd:+,.0f}₫"
                )
            
            with col4:
                st.metric(
                    "담당자",
                    data['responsible_person']
                )
            
            st.markdown("---")
            
            # 목표 vs 실적 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 목표 vs 실적 비교")
                
                fig = go.Figure(data=[
                    go.Bar(
                        name='목표',
                        x=['매출'],
                        y=[target_vnd],
                        marker_color='lightblue'
                    ),
                    go.Bar(
                        name='실제',
                        x=['매출'],
                        y=[actual_vnd],
                        marker_color='darkblue'
                    )
                ])
                
                fig.update_layout(
                    title=f"{target_month} 목표 vs 실적",
                    yaxis_title="매출 (VND)",
                    barmode='group',
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🎯 달성률 분석")
                
                # 도넛 차트로 달성률 표시
                achievement = data['achievement_rate']
                remaining = max(0, 100 - achievement)
                over_achievement = max(0, achievement - 100)
                
                if over_achievement > 0:
                    # 목표 초과 달성
                    fig = go.Figure(data=[go.Pie(
                        labels=['목표 달성', '초과 달성'],
                        values=[100, over_achievement],
                        hole=.6,
                        marker_colors=['green', 'gold']
                    )])
                    fig.add_annotation(text=f"{achievement:.1f}%<br>달성", 
                                     x=0.5, y=0.5, font_size=20, showarrow=False)
                else:
                    # 목표 미달성
                    fig = go.Figure(data=[go.Pie(
                        labels=['달성', '미달성'],
                        values=[achievement, remaining],
                        hole=.6,
                        marker_colors=['green', 'lightgray']
                    )])
                    fig.add_annotation(text=f"{achievement:.1f}%<br>달성", 
                                     x=0.5, y=0.5, font_size=20, showarrow=False)
                
                fig.update_layout(
                    title="달성률",
                    showlegend=True,
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # 전체 기간 목표 vs 실적
            st.markdown("### 📈 전체 기간 목표 vs 실적 추이")
            
            all_targets = monthly_sales_manager.get_target_vs_actual()
            
            if len(all_targets) > 0:
                df_targets = pd.DataFrame(all_targets)
                
                fig = go.Figure()
                
                # VND 기준으로 그래프 표시
                target_vnd_values = []
                actual_vnd_values = []
                
                for _, row in df_targets.iterrows():
                    # 목표 VND (기본 32억동)
                    target_vnd = row.get('target_amount_vnd', 3200000000)
                    target_vnd_values.append(target_vnd)
                    
                    # 실제 VND (0으로 기본값 설정)
                    actual_vnd = row.get('actual_amount_vnd', 0)
                    actual_vnd_values.append(actual_vnd)
                
                fig.add_trace(go.Scatter(
                    x=df_targets['year_month'],
                    y=target_vnd_values,
                    mode='lines+markers',
                    name='목표',
                    line=dict(color='red', dash='dash'),
                    hovertemplate='%{x}<br>목표: %{y:,.0f}₫<extra></extra>'
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_targets['year_month'],
                    y=actual_vnd_values,
                    mode='lines+markers',
                    name='실제',
                    line=dict(color='blue'),
                    hovertemplate='%{x}<br>실제: %{y:,.0f}₫<extra></extra>'
                ))
                
                fig.update_layout(
                    title="월별 목표 vs 실적 추이",
                    xaxis_title="월",
                    yaxis_title="매출 (VND)",
                    height=400,
                    yaxis=dict(tickformat=',.0f')
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("📋 해당 월의 목표 데이터가 없습니다.")
            
            # 목표 설정 폼
            with st.expander("🎯 매출 목표 설정"):
                with st.form("add_target_form_dashboard"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        target_amount_usd = st.number_input(
                            "목표 매출 (USD)",
                            min_value=0.0,
                            value=500000.0,
                            step=10000.0
                        )
                        
                        responsible_person = st.text_input(
                            "담당자",
                            value="영업팀"
                        )
                    
                    with col2:
                        target_quantity = st.number_input(
                            "목표 수량",
                            min_value=0,
                            value=100,
                            step=10
                        )
                        
                        description = st.text_area(
                            "설명",
                            value=f"{target_month} 월별 매출 목표"
                        )
                    
                    if st.form_submit_button("목표 설정"):
                        target_amount_vnd = target_amount_usd * 24500
                        
                        target_id = monthly_sales_manager.add_sales_target(
                            year_month=target_month,
                            target_type='monthly',
                            target_category='total_sales',
                            target_amount_vnd=target_amount_vnd,
                            target_amount_usd=target_amount_usd,
                            currency='USD',
                            target_quantity=target_quantity,
                            responsible_person=responsible_person,
                            description=description
                        )
                        
                        if target_id:
                            st.success(f"✅ 매출 목표가 설정되었습니다: {target_id}")
                            st.rerun()
                        else:
                            st.error("❌ 매출 목표 설정에 실패했습니다.")
            
    except Exception as e:
        st.error(f"목표 vs 실적 분석 중 오류: {str(e)}")

def show_customer_analysis(monthly_sales_manager):
    """고객별 매출 분석"""
    st.subheader("👥 고객별 매출 분석")
    
    try:
        # 월 선택
        col1, col2 = st.columns([1, 3])
        
        with col1:
            analysis_month = st.selectbox(
                "분석 월 선택",
                options=["전체"] + [
                    (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m") 
                    for i in range(6)
                ],
                key="customer_month"
            )
        
        # 고객별 매출 데이터 조회
        month_filter = None if analysis_month == "전체" else analysis_month
        customer_data = monthly_sales_manager.get_customer_sales_analysis(month_filter)
        
        if len(customer_data) > 0:
            df_customers = pd.DataFrame(customer_data)
            
            # 상위 10개 고객 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 상위 10개 고객 매출")
                
                top_customers = df_customers.head(10)
                
                fig = px.bar(
                    top_customers,
                    x='amount_usd',
                    y='customer_name',
                    orientation='h',
                    title="고객별 매출 (USD)",
                    labels={'amount_usd': '매출 (USD)', 'customer_name': '고객명'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🥧 매출 비중 분석")
                
                # 상위 5개 고객 + 기타
                top5 = df_customers.head(5)
                others_sales = df_customers.tail(len(df_customers)-5)['amount_usd'].sum()
                
                pie_data = top5.copy()
                if others_sales > 0:
                    pie_data = pd.concat([
                        pie_data,
                        pd.DataFrame([{
                            'customer_name': '기타',
                            'amount_usd': others_sales,
                            'sales_percentage': others_sales / df_customers['amount_usd'].sum() * 100
                        }])
                    ])
                
                fig = px.pie(
                    pie_data,
                    values='amount_usd',
                    names='customer_name',
                    title="고객별 매출 비중"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # 고객별 상세 분석 테이블
            st.markdown("### 📋 고객별 상세 분석")
            
            # 표시 형식 정리
            display_df = df_customers.copy()
            display_df['amount_usd'] = display_df['amount_usd'].apply(lambda x: f"${x:,.0f}")
            display_df['amount_vnd'] = display_df['amount_vnd'].apply(lambda x: f"{x:,.0f}₫")
            display_df['sales_percentage'] = display_df['sales_percentage'].apply(lambda x: f"{x:.1f}%")
            display_df['profit_margin'] = display_df['profit_margin'].apply(lambda x: f"{x:.1%}")
            
            # 컬럼명 한글화
            display_df = display_df.rename(columns={
                'customer_name': '고객명',
                'amount_usd': '매출(USD)',
                'amount_vnd': '매출(VND)',
                'quantity': '수량',
                'sales_id': '거래건수',
                'sales_percentage': '매출비중',
                'profit_margin': '평균이익률'
            })
            
            st.dataframe(
                display_df[['고객명', '매출(USD)', '매출(VND)', '수량', '거래건수', '매출비중', '평균이익률']],
                use_container_width=True,
                hide_index=True
            )
            
            # 다운로드 기능
            csv_data = df_customers.to_csv(index=False, encoding='utf-8')
            period_text = analysis_month if analysis_month != "전체" else "전체기간"
            
            st.download_button(
                label="📥 고객별 매출 데이터 다운로드",
                data=csv_data,
                file_name=f"customer_sales_analysis_{period_text}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        else:
            st.info("📋 고객별 매출 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"고객별 매출 분석 중 오류: {str(e)}")

def show_product_analysis(monthly_sales_manager):
    """제품별 매출 분석"""
    st.subheader("📦 제품별 매출 분석")
    
    try:
        # 월 선택
        col1, col2 = st.columns([1, 3])
        
        with col1:
            analysis_month = st.selectbox(
                "분석 월 선택",
                options=["전체"] + [
                    (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m") 
                    for i in range(6)
                ],
                key="product_month"
            )
        
        # 제품별 매출 데이터 조회
        month_filter = None if analysis_month == "전체" else analysis_month
        product_data = monthly_sales_manager.get_product_sales_analysis(month_filter)
        
        if len(product_data) > 0:
            df_products = pd.DataFrame(product_data)
            
            # 카테고리별 매출 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 카테고리별 매출")
                
                category_sales = df_products.groupby('category')['amount_usd'].sum().reset_index()
                
                fig = px.bar(
                    category_sales,
                    x='category',
                    y='amount_usd',
                    title="제품 카테고리별 매출",
                    labels={'amount_usd': '매출 (USD)', 'category': '카테고리'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🏆 베스트 셀러 제품")
                
                top_products = df_products.head(10)
                
                fig = px.bar(
                    top_products,
                    x='amount_usd',
                    y='product_name',
                    orientation='h',
                    title="상위 10개 제품 매출",
                    labels={'amount_usd': '매출 (USD)', 'product_name': '제품명'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # 제품 성과 분석
            st.markdown("### 📈 제품 성과 분석")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 평균 단가 vs 판매량 분석
                fig = px.scatter(
                    df_products,
                    x='quantity',
                    y='unit_price',
                    size='amount_usd',
                    color='category',
                    hover_name='product_name',
                    title="수량 vs 단가 vs 매출",
                    labels={'quantity': '판매 수량', 'unit_price': '평균 단가 (USD)'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 이익률 vs 매출 분석
                fig = px.scatter(
                    df_products,
                    x='amount_usd',
                    y='profit_margin',
                    size='quantity',
                    color='category',
                    hover_name='product_name',
                    title="매출 vs 이익률",
                    labels={'amount_usd': '매출 (USD)', 'profit_margin': '이익률'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # 제품별 상세 분석 테이블
            st.markdown("### 📋 제품별 상세 분석")
            
            # 표시 형식 정리
            display_df = df_products.copy()
            display_df['amount_usd'] = display_df['amount_usd'].apply(lambda x: f"${x:,.0f}")
            display_df['amount_vnd'] = display_df['amount_vnd'].apply(lambda x: f"{x:,.0f}₫")
            display_df['unit_price'] = display_df['unit_price'].apply(lambda x: f"${x:,.0f}")
            display_df['sales_percentage'] = display_df['sales_percentage'].apply(lambda x: f"{x:.1f}%")
            display_df['profit_margin'] = display_df['profit_margin'].apply(lambda x: f"{x:.1%}")
            
            # 컬럼명 한글화
            display_df = display_df.rename(columns={
                'category': '카테고리',
                'product_name': '제품명',
                'amount_usd': '매출(USD)',
                'amount_vnd': '매출(VND)',
                'quantity': '수량',
                'unit_price': '평균단가',
                'sales_id': '거래건수',
                'sales_percentage': '매출비중',
                'profit_margin': '평균이익률'
            })
            
            st.dataframe(
                display_df[['카테고리', '제품명', '매출(USD)', '매출(VND)', '수량', '평균단가', '거래건수', '매출비중', '평균이익률']],
                use_container_width=True,
                hide_index=True
            )
            
            # 다운로드 기능
            csv_data = df_products.to_csv(index=False, encoding='utf-8')
            period_text = analysis_month if analysis_month != "전체" else "전체기간"
            
            st.download_button(
                label="📥 제품별 매출 데이터 다운로드",
                data=csv_data,
                file_name=f"product_sales_analysis_{period_text}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        else:
            st.info("📋 제품별 매출 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"제품별 매출 분석 중 오류: {str(e)}")

def show_trend_analysis(monthly_sales_manager):
    """트렌드 분석"""
    st.subheader("📈 매출 트렌드 분석")
    
    try:
        # 트렌드 기간 선택
        col1, col2 = st.columns([1, 3])
        
        with col1:
            trend_months = st.selectbox(
                "분석 기간",
                options=[3, 6, 12],
                format_func=lambda x: f"최근 {x}개월"
            )
        
        # 트렌드 데이터 조회
        trend_data = monthly_sales_manager.get_sales_trend(trend_months)
        
        if len(trend_data) > 0:
            df_trend = pd.DataFrame(trend_data)
            df_trend['year_month'] = pd.to_datetime(df_trend['year_month'], format='%Y-%m', errors='coerce')
            df_trend = df_trend.sort_values('year_month')
            
            # 매출 트렌드 차트
            st.markdown("### 📊 월별 매출 트렌드")
            
            fig = go.Figure()
            
            # 매출 라인
            fig.add_trace(go.Scatter(
                x=df_trend['year_month'],
                y=df_trend['amount_usd'],
                mode='lines+markers',
                name='매출 (USD)',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            # 이동 평균선 추가
            if len(df_trend) >= 3:
                df_trend['ma3'] = df_trend['amount_usd'].rolling(window=3).mean()
                fig.add_trace(go.Scatter(
                    x=df_trend['year_month'],
                    y=df_trend['ma3'],
                    mode='lines',
                    name='3개월 이동평균',
                    line=dict(color='red', dash='dash')
                ))
            
            fig.update_layout(
                title="월별 매출 트렌드",
                xaxis_title="월",
                yaxis_title="매출 (USD)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 성장률 분석
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 월별 성장률")
                
                # 전월 대비 성장률 계산
                df_trend['growth_rate'] = df_trend['amount_usd'].pct_change() * 100
                
                fig = px.bar(
                    df_trend.dropna(),
                    x='year_month',
                    y='growth_rate',
                    title="전월 대비 성장률 (%)",
                    labels={'growth_rate': '성장률 (%)', 'year_month': '월'},
                    color='growth_rate',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 매출 패턴 분석")
                
                # 평균, 최대, 최소 매출
                avg_sales = df_trend['amount_usd'].mean()
                max_sales = df_trend['amount_usd'].max()
                min_sales = df_trend['amount_usd'].min()
                
                pattern_data = {
                    "지표": ["평균 매출", "최대 매출", "최소 매출", "표준편차"],
                    "값 (USD)": [
                        f"${avg_sales:,.0f}",
                        f"${max_sales:,.0f}",
                        f"${min_sales:,.0f}",
                        f"${df_trend['amount_usd'].std():,.0f}"
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(pattern_data),
                    use_container_width=True,
                    hide_index=True
                )
                
                # 변동성 지표
                cv = (df_trend['amount_usd'].std() / avg_sales) * 100
                st.metric("변동계수 (CV)", f"{cv:.1f}%")
            
            # 예측 분석
            st.markdown("### 🔮 매출 예측")
            
            if len(df_trend) >= 3:
                # 간단한 예측 표시
                st.info("📈 간단한 트렌드 기반 예측이 가능합니다.")
                
                # 성장률 통계 표시
                col1, col2, col3, col4 = st.columns(4)
                
                avg_growth = df_trend['growth_rate'].mean()
                
                with col1:
                    st.metric("평균 성장률", f"{avg_growth:+.1f}%")
                
                with col2:
                    positive_months = len(df_trend[df_trend['growth_rate'] > 0])
                    st.metric("성장월 수", f"{positive_months}/{len(df_trend)-1}개월")
                
                with col3:
                    best_month = df_trend.loc[df_trend['amount_usd'].idxmax(), 'year_month'].strftime("%Y-%m")
                    st.metric("최고 매출월", best_month)
                
                with col4:
                    volatility = df_trend['amount_usd'].std() / df_trend['amount_usd'].mean() * 100
                    st.metric("변동성", f"{volatility:.1f}%")
        
        else:
            st.info("📋 트렌드 분석을 위한 데이터가 부족합니다.")
            
    except Exception as e:
        st.error(f"트렌드 분석 중 오류: {str(e)}")

def show_sales_management(monthly_sales_manager, customer_manager):
    """매출 관리"""
    st.subheader("⚙️ 매출 데이터 관리")
    
    notification = NotificationHelper()
    
    # 관리 기능 탭
    tab1, tab2, tab3 = st.tabs([
        "📝 매출 등록",
        "🎯 목표 설정", 
        "📊 데이터 현황"
    ])
    
    with tab1:
        st.markdown("### 매출 기록 등록")
        
        with st.form("add_sales_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # 고객 선택
                try:
                    customers = customer_manager.get_all_customers()
                    customer_options = {
                        f"{customer['company_name']} ({customer['customer_id']})": customer['customer_id']
                        for customer in customers
                    }
                    
                    selected_customer = st.selectbox(
                        "고객 선택",
                        options=list(customer_options.keys())
                    )
                    customer_id = customer_options[selected_customer]
                    customer_name = selected_customer.split(" (")[0]
                    
                except:
                    customer_id = st.text_input("고객 ID", value="C001")
                    customer_name = st.text_input("고객명", value="테스트 고객")
                
                product_code = st.text_input("제품 코드", value="HR-001")
                product_name = st.text_input("제품명", value="Hot Runner Valve")
                
                category = st.selectbox(
                    "제품 카테고리",
                    options=["HR", "HRC", "MB", "SERVICE", "SPARE"]
                )
            
            with col2:
                quantity = st.number_input("수량", min_value=1, value=1)
                unit_price = st.number_input("단가", min_value=0.0, value=1500.0, step=100.0)
                
                currency = st.selectbox(
                    "통화",
                    options=["USD", "VND", "KRW"]
                )
                
                sales_rep = st.text_input("영업 담당자", value="김영수")
                
                payment_status = st.selectbox(
                    "결제 상태",
                    options=["pending", "partial", "paid"]
                )
            
            quotation_id = st.text_input("견적서 ID (선택)", value="")
            order_id = st.text_input("주문 ID (선택)", value="")
            
            if st.form_submit_button("매출 등록"):
                try:
                    sales_id = monthly_sales_manager.add_sales_record(
                        customer_id=customer_id,
                        customer_name=customer_name,
                        product_code=product_code,
                        product_name=product_name,
                        category=category,
                        quantity=quantity,
                        unit_price=unit_price,
                        currency=currency,
                        quotation_id=quotation_id if quotation_id else f"Q{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        order_id=order_id if order_id else f"O{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        sales_rep=sales_rep,
                        payment_status=payment_status
                    )
                    
                    if sales_id:
                        st.success(f"✅ 매출 기록이 성공적으로 등록되었습니다: {sales_id}")
                        st.rerun()
                    else:
                        st.error("❌ 매출 기록 등록에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    with tab2:
        st.markdown("### 매출 목표 설정")
        
        with st.form("add_target_form_sales_management"):
            col1, col2 = st.columns(2)
            
            with col1:
                target_month = st.text_input(
                    "목표 월 (YYYY-MM)",
                    value=datetime.now().strftime("%Y-%m")
                )
                
                target_amount_vnd = st.number_input(
                    "목표 매출 (VND)",
                    min_value=0.0,
                    value=3200000000.0,  # 32억동
                    step=100000000.0,    # 1억동 단위
                    format="%.0f"
                )
                
                target_quantity = st.number_input(
                    "목표 수량",
                    min_value=0,
                    value=100,
                    step=10
                )
            
            with col2:
                responsible_person = st.text_input(
                    "담당자",
                    value="영업팀"
                )
                
                target_type = st.selectbox(
                    "목표 유형",
                    options=["월별매출", "분기별매출", "연간매출"],
                    index=0
                )
                
                target_category = st.selectbox(
                    "목표 카테고리",
                    options=["전체매출", "신규고객", "제품카테고리"],
                    index=0
                )
            
            description = st.text_area(
                "설명",
                value=f"{target_month} 매출 목표"
            )
            
            if st.form_submit_button("목표 설정"):
                try:
                    target_amount_usd = target_amount_vnd / 24500  # VND를 USD로 환산
                    
                    target_id = monthly_sales_manager.add_sales_target(
                        year_month=target_month,
                        target_type=target_type,
                        target_category=target_category,
                        target_amount_vnd=target_amount_vnd,
                        target_amount_usd=target_amount_usd,
                        currency='VND',
                        target_quantity=target_quantity,
                        responsible_person=responsible_person,
                        description=description
                    )
                    
                    if target_id:
                        st.success(f"✅ 매출 목표가 설정되었습니다: {target_id}")
                        st.rerun()
                    else:
                        st.error("❌ 매출 목표 설정에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    with tab3:
        st.markdown("### 매출 데이터 현황")
        
        try:
            # 전체 데이터 현황
            all_sales = monthly_sales_manager.get_monthly_sales_summary()
            all_targets = monthly_sales_manager.get_sales_targets()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_sales = sum(sale['total_sales_usd'] for sale in all_sales)
                st.metric("총 매출 (USD)", f"${total_sales:,.0f}")
            
            with col2:
                total_transactions = sum(sale['transaction_count'] for sale in all_sales)
                st.metric("총 거래 건수", f"{total_transactions:,}건")
            
            with col3:
                st.metric("등록된 월 수", f"{len(all_sales)}개월")
            
            with col4:
                st.metric("설정된 목표", f"{len(all_targets)}개")
            
            # 최근 매출 기록
            if all_sales:
                st.markdown("### 📋 월별 매출 현황")
                
                df_display = pd.DataFrame(all_sales)
                df_display['total_sales_usd'] = df_display['total_sales_usd'].apply(lambda x: f"${x:,.0f}")
                df_display['amount_vnd'] = df_display['amount_vnd'].apply(lambda x: f"{x:,.0f}₫")
                df_display['avg_profit_margin'] = df_display['avg_profit_margin'].apply(lambda x: f"{x:.1%}")
                
                df_display = df_display.rename(columns={
                    'year_month': '월',
                    'total_sales_usd': '매출(USD)',
                    'amount_vnd': '매출(VND)',
                    'quantity': '수량',
                    'transaction_count': '거래건수',
                    'avg_profit_margin': '평균이익률'
                })
                
                st.dataframe(
                    df_display[['월', '매출(USD)', '매출(VND)', '수량', '거래건수', '평균이익률']],
                    use_container_width=True,
                    hide_index=True
                )
        
        except Exception as e:
            st.error(f"데이터 현황 조회 중 오류: {str(e)}")

def show_target_settings(monthly_sales_manager):
    """마스터 전용 목표 설정 관리"""
    st.subheader("🔧 매출 목표 설정 관리")
    st.markdown("**마스터 권한으로 기본 월별 목표 금액을 설정할 수 있습니다**")
    
    # 현재 기본 목표 확인
    try:
        current_targets = monthly_sales_manager.get_sales_targets("2025-08")
        current_amount = 3200000000  # 기본값 32억동
        if len(current_targets) > 0:
            current_amount = current_targets[0].get('target_amount_vnd', 3200000000)
        
        st.info(f"현재 월별 기본 목표: {current_amount:,.0f}₫ ({current_amount/1000000000:.1f}억동)")
        
        st.markdown("---")
        
        # 기본 목표 설정 폼
        with st.form("default_target_setting"):
            st.markdown("### 📊 기본 월별 목표 설정")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # VND 기준 입력 (억동 단위)
                target_billion = st.number_input(
                    "월별 목표 (억동 단위)",
                    min_value=0.1,
                    max_value=100.0,
                    value=current_amount/1000000000,
                    step=0.1,
                    help="예: 3.2 = 32억동"
                )
                
                target_vnd = int(target_billion * 1000000000)
                st.markdown(f"**설정 금액:** {target_vnd:,.0f}₫")
            
            with col2:
                # 적용 기간 선택
                apply_option = st.radio(
                    "적용 범위",
                    ["전체 2025년", "현재 월부터", "특정 월만"],
                    index=0,
                    help="설정할 목표의 적용 범위를 선택하세요"
                )
                
                if apply_option == "특정 월만":
                    specific_month = st.selectbox(
                        "특정 월 선택",
                        [f"2025-{str(i).zfill(2)}" for i in range(1, 13)],
                        index=7  # 기본값 8월
                    )
                else:
                    specific_month = "2025-01"  # 기본값
            
            # 제출 버튼
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("💾 목표 설정 적용", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    # 기존 목표 삭제 및 새 목표 설정
                    success_count = 0
                    
                    if apply_option == "전체 2025년":
                        # 전체 2025년 목표 재설정
                        months = [f"2025-{str(i).zfill(2)}" for i in range(1, 13)]
                        
                        # 기존 목표 삭제
                        import pandas as pd
                        import os
                        targets_file = 'data/sales_targets.csv'
                        if os.path.exists(targets_file):
                            df = pd.read_csv(targets_file, encoding='utf-8-sig')
                            df = df[~df['year_month'].str.startswith('2025')]
                            df.to_csv(targets_file, index=False, encoding='utf-8-sig')
                        
                        # 새 목표 설정
                        for month in months:
                            target_id = monthly_sales_manager.add_sales_target(
                                year_month=month,
                                target_type='전체매출',
                                target_category='전체',
                                target_amount_vnd=target_vnd,
                                target_amount_usd=int(target_vnd / 24500),  # 대략적 환율
                                currency='VND',
                                target_quantity=0,
                                responsible_person='전체팀',
                                description=f'{month} 월별 매출 목표 ({target_billion:.1f}억동)'
                            )
                            if target_id:
                                success_count += 1
                    
                    elif apply_option == "현재 월부터":
                        # 현재 월부터 연말까지 적용
                        from datetime import datetime
                        current_month = datetime.now().month
                        months = [f"2025-{str(i).zfill(2)}" for i in range(current_month, 13)]
                        
                        for month in months:
                            # 기존 목표 삭제 후 새로 설정
                            import pandas as pd
                            import os
                            targets_file = 'data/sales_targets.csv'
                            if os.path.exists(targets_file):
                                df = pd.read_csv(targets_file, encoding='utf-8-sig')
                                df = df[df['year_month'] != month]
                                df.to_csv(targets_file, index=False, encoding='utf-8-sig')
                            
                            # 새 목표 설정
                            target_id = monthly_sales_manager.add_sales_target(
                                year_month=month,
                                target_type='전체매출',
                                target_category='전체',
                                target_amount_vnd=target_vnd,
                                target_amount_usd=int(target_vnd / 24500),
                                currency='VND',
                                target_quantity=0,
                                responsible_person='전체팀',
                                description=f'{month} 월별 매출 목표 ({target_billion:.1f}억동)'
                            )
                            if target_id:
                                success_count += 1
                    
                    else:  # 특정 월만
                        # 기존 목표 삭제 후 새로 설정
                        import pandas as pd
                        import os
                        targets_file = 'data/sales_targets.csv'
                        if os.path.exists(targets_file):
                            df = pd.read_csv(targets_file, encoding='utf-8-sig')
                            df = df[df['year_month'] != specific_month]
                            df.to_csv(targets_file, index=False, encoding='utf-8-sig')
                        
                        # 새 목표 설정
                        target_id = monthly_sales_manager.add_sales_target(
                            year_month=specific_month,
                            target_type='전체매출',
                            target_category='전체',
                            target_amount_vnd=target_vnd,
                            target_amount_usd=int(target_vnd / 24500),
                            currency='VND',
                            target_quantity=0,
                            responsible_person='전체팀',
                            description=f'{specific_month} 월별 매출 목표 ({target_billion:.1f}억동)'
                        )
                        if target_id:
                            success_count = 1
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}개월의 목표가 성공적으로 설정되었습니다!")
                        
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("목표 설정에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"목표 설정 중 오류: {str(e)}")
        
        st.markdown("---")
        
        # 현재 설정된 목표 현황
        st.markdown("### 📋 현재 설정된 월별 목표")
        
        try:
            months_2025 = [f'2025-{str(i).zfill(2)}' for i in range(1, 13)]
            target_data = []
            
            for month in months_2025:
                targets = monthly_sales_manager.get_sales_targets(month)
                if len(targets) > 0:
                    target = targets[0]
                    amount_vnd = target.get('target_amount_vnd', 0)
                    target_data.append({
                        '월': month,
                        '목표금액(VND)': f"{amount_vnd:,.0f}₫",
                        '목표금액(억동)': f"{amount_vnd/1000000000:.1f}억동",
                        '담당자': target.get('responsible_person', 'N/A'),
                        '설명': target.get('description', 'N/A')
                    })
                else:
                    target_data.append({
                        '월': month,
                        '목표금액(VND)': "설정안됨",
                        '목표금액(억동)': "0.0억동",
                        '담당자': "-",
                        '설명': "-"
                    })
            
            if len(target_data) > 0:
                import pandas as pd
                df_targets = pd.DataFrame(target_data)
                st.dataframe(df_targets, use_container_width=True, hide_index=True)
                
                # 일괄 목표 삭제 기능 (위험한 작업)
                st.markdown("### ⚠️ 위험한 작업")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🗑️ 모든 2025년 목표 삭제", type="secondary"):
                        st.session_state.confirm_delete_targets = True
                
                if st.session_state.get('confirm_delete_targets', False):
                    with col2:
                        if st.button("⚠️ 정말 삭제", type="primary"):
                            try:
                                import pandas as pd
                                import os
                                targets_file = 'data/sales_targets.csv'
                                if os.path.exists(targets_file):
                                    df = pd.read_csv(targets_file, encoding='utf-8-sig')
                                    original_count = len(df[df['year_month'].str.startswith('2025')])
                                    df = df[~df['year_month'].str.startswith('2025')]
                                    df.to_csv(targets_file, index=False, encoding='utf-8-sig')
                                    st.success(f"✅ {original_count}개의 2025년 목표가 삭제되었습니다.")
                                    st.session_state.confirm_delete_targets = False
                                    st.rerun()
                                else:
                                    st.warning("목표 파일이 존재하지 않습니다.")
                            except Exception as e:
                                st.error(f"목표 삭제 중 오류: {str(e)}")
        
        except Exception as e:
            st.error(f"목표 현황 조회 중 오류: {str(e)}")
            
    except Exception as e:
        st.error(f"목표 설정 페이지 로드 중 오류: {str(e)}")