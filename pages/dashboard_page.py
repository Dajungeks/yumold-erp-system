import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_dashboard_page(employee_manager, customer_manager, product_manager, quotation_manager, selected_submenu, get_text):
    """개선된 대시보드 페이지를 표시합니다."""
    
    # 노트 위젯 표시 (사이드바)
    if hasattr(st.session_state, 'note_manager') and st.session_state.note_manager:
        from components.note_widget import show_page_note_widget
        show_page_note_widget(st.session_state.note_manager, 'dashboard', get_text)

    # 기본 통계 수집 (재직 기준 직원 수)
    employee_count = employee_manager.get_active_employee_count()
    customer_count = len(customer_manager.get_all_customers())
    product_count = len(product_manager.get_all_products())
    quotation_count = len(quotation_manager.get_all_quotations())

    # 환영 메시지
    today_date = datetime.now().strftime('%Y년 %m월 %d일')
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; margin: 0;">🏢 {get_text('dashboard_title')}</h2>
        <p style="color: white; margin: 5px 0 0 0;">
            {get_text('dashboard_welcome').format(date=today_date)}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 통계 요약 카드 (개선된 디자인)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3;">
            <h3 style="color: #1976d2; margin: 0; font-size: 1.2em;">👥 {get_text('total_staff')}</h3>
            <p style="font-size: 2em; font-weight: bold; margin: 5px 0; color: #1976d2;">{employee_count}</p>
            <small style="color: #666;">{get_text('total_staff_desc')}</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 4px solid #4caf50;">
            <h3 style="color: #388e3c; margin: 0; font-size: 1.2em;">🏢 {get_text('total_customers')}</h3>
            <p style="font-size: 2em; font-weight: bold; margin: 5px 0; color: #388e3c;">{customer_count}</p>
            <small style="color: #666;">{get_text('total_customers_desc')}</small>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: #fff3e0; padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800;">
            <h3 style="color: #f57c00; margin: 0; font-size: 1.2em;">📦 {get_text('total_products')}</h3>
            <p style="font-size: 2em; font-weight: bold; margin: 5px 0; color: #f57c00;">{product_count}</p>
            <small style="color: #666;">{get_text('total_products_desc')}</small>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: #fce4ec; padding: 15px; border-radius: 10px; border-left: 4px solid #e91e63;">
            <h3 style="color: #c2185b; margin: 0; font-size: 1.2em;">💰 {get_text('total_quotations')}</h3>
            <p style="font-size: 2em; font-weight: bold; margin: 5px 0; color: #c2185b;">{quotation_count}</p>
            <small style="color: #666;">{get_text('total_quotations_desc')}</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 비즈니스 인사이트 섹션
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader(f"📊 {get_text('business_status')}")

        # 월별 견적서 현황
        st.markdown(f"#### 📈 {get_text('monthly_quotation_status')}")
        try:
            monthly_summary = quotation_manager.get_monthly_quotation_summary()
            if len(monthly_summary) > 0:
                # Plotly를 사용한 개선된 차트
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    name=get_text('quotation_count'),
                    x=monthly_summary['month'],
                    y=monthly_summary['quotation_count'],
                    yaxis='y',
                    marker_color='rgba(55, 83, 109, 0.8)'
                ))

                fig.add_trace(go.Scatter(
                    name=get_text('total_amount_usd'),
                    x=monthly_summary['month'],
                    y=monthly_summary['total_amount'],
                    yaxis='y2',
                    mode='lines+markers',
                    line=dict(color='rgba(255, 127, 14, 0.8)', width=3),
                    marker=dict(size=8)
                ))

                fig.update_layout(
                    title=get_text('monthly_quotation_chart_title'),
                    xaxis=dict(title=get_text('month')),
                    yaxis=dict(title=get_text('quotation_count'), side='left'),
                    yaxis2=dict(title=get_text('total_amount_usd'), side='right', overlaying='y'),
                    legend=dict(x=0.1, y=0.9),
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # 상세 데이터 테이블
                with st.expander(f"📋 {get_text('detail_data_view')}"):
                    st.dataframe(monthly_summary, use_container_width=True)
            else:
                st.info(get_text('no_monthly_data'))
        except Exception as e:
            st.warning(f"{get_text('monthly_data_error')}: {e}")

        # 제품 카테고리별 분포
        st.markdown(f"#### 📦 {get_text('product_category_distribution')}")
        try:
            product_stats = product_manager.get_product_count_by_category()
            if product_stats:
                categories = list(product_stats.keys())
                counts = list(product_stats.values())

                fig = px.pie(
                    values=counts, 
                    names=categories, 
                    title=get_text('product_category_chart_title'),
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(get_text('no_category_data'))
        except Exception as e:
            st.warning(f"{get_text('category_data_error')}: {e}")

        # 직원 상태별 현황
        st.markdown(f"#### 👥 {get_text('employee_status_overview')}")
        try:
            all_employees = employee_manager.get_all_employees()
            if len(all_employees) > 0:
                # 재직/퇴사 상태별 통계
                work_status_counts = all_employees['work_status'].value_counts() if 'work_status' in all_employees.columns else all_employees['status'].apply(lambda x: get_text('active_employee') if x == '활성' else get_text('resigned_employee')).value_counts()
                
                col_status1, col_status2 = st.columns(2)
                with col_status1:
                    st.metric(get_text('active_employee'), work_status_counts.get(get_text('active_employee'), work_status_counts.get('재직', 0)), help=get_text('total_staff_desc'))
                with col_status2:
                    st.metric(get_text('resigned_employee'), work_status_counts.get(get_text('resigned_employee'), work_status_counts.get('퇴사', 0)), help="퇴사한 직원")
                
                # 파이 차트로 시각화
                if len(work_status_counts) > 0:
                    fig = px.pie(
                        values=work_status_counts.values,
                        names=work_status_counts.index,
                        title=get_text('employee_status_chart_title'),
                        color_discrete_map={get_text('active_employee'): '#2E8B57', get_text('resigned_employee'): '#DC143C', '재직': '#2E8B57', '퇴사': '#DC143C'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"{get_text('employee_status_error')}: {e}")

        # 직급별 직원 현황
        st.markdown(f"#### 👔 {get_text('position_overview')}")
        try:
            position_stats = employee_manager.get_employee_count_by_position()
            if position_stats:
                positions = list(position_stats.keys())
                counts = list(position_stats.values())

                fig = px.bar(
                    x=positions, 
                    y=counts,
                    title=get_text('position_chart_title'),
                    labels={'x': get_text('position'), 'y': get_text('employee_count')},
                    color=counts,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=400, showlegend=False)
                fig.update_layout(xaxis={'tickangle': 45})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(get_text('no_position_data'))
        except Exception as e:
            st.warning(f"{get_text('position_data_error')}: {e}")

        # 공급업체별 제품 현황
        st.markdown(f"#### 🏭 {get_text('supplier_overview')}")
        try:
            supplier_stats = product_manager.get_product_count_by_supplier()
            if supplier_stats:
                suppliers = list(supplier_stats.keys())
                counts = list(supplier_stats.values())

                fig = px.bar(
                    x=suppliers, 
                    y=counts,
                    title=get_text('supplier_chart_title'),
                    labels={'x': get_text('supplier'), 'y': get_text('product_count')},
                    color=counts,
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(get_text('no_supplier_data'))
        except Exception as e:
            st.warning(f"{get_text('supplier_data_error')}: {e}")

    with col_right:
        # 시스템 상태 및 알림
        st.subheader(f"⚡ {get_text('system_status')}")

        # 승인 대기 알림
        if st.session_state.user_type == "master":
            try:
                if 'approval_manager' in st.session_state:
                    pending_requests = st.session_state.approval_manager.get_pending_requests()

                    if len(pending_requests) > 0:
                        st.warning(f"⚠️ {get_text('pending_approvals')}: **{len(pending_requests)}{get_text('requests_count')}**")

                        if st.button(f"🔍 {get_text('go_to_approval')}", use_container_width=True):
                            st.session_state.selected_system = "approval_management" 
                            st.rerun()
                    else:
                        st.success(f"✅ {get_text('all_approvals_processed')}")
            except Exception as e:
                st.error(f"{get_text('approval_data_error')}: {e}")

        # 가격 요약 정보
        st.markdown(f"#### 💰 {get_text('price_info_summary')}")
        try:
            price_summary = product_manager.get_price_summary()

            st.metric(
                get_text('avg_cost_usd'), 
                f"${price_summary['avg_cost_usd']:.2f}" if price_summary['avg_cost_usd'] > 0 else "N/A"
            )
            st.metric(
                get_text('avg_recommended_usd'), 
                f"${price_summary['avg_recommended_usd']:.2f}" if price_summary['avg_recommended_usd'] > 0 else "N/A"
            )

            if price_summary['avg_cost_usd'] > 0 and price_summary['avg_recommended_usd'] > 0:
                avg_margin = ((price_summary['avg_recommended_usd'] - price_summary['avg_cost_usd']) / price_summary['avg_cost_usd']) * 100
                st.metric(get_text('avg_margin_rate'), f"{avg_margin:.1f}%")
        except Exception as e:
            st.warning(f"{get_text('price_info_summary')}: {e}")

        # 표준 제품 코드 현황
        st.markdown(f"#### 🔧 {get_text('standard_product_code')}")
        try:
            if 'product_code_manager' in st.session_state:
                code_manager = st.session_state.product_code_manager
                total_codes = len(code_manager.get_all_product_codes())
                active_codes = len(code_manager.get_active_product_codes())

                st.metric(get_text('total_standard_codes'), f"{total_codes}개")
                st.metric(get_text('active_codes'), f"{active_codes}개")

                if total_codes > 0:
                    active_ratio = (active_codes / total_codes) * 100
                    st.metric(get_text('active_ratio'), f"{active_ratio:.1f}%")
        except Exception as e:
            st.warning(f"{get_text('standard_product_code')}: {e}")

        # 환율 정보
        st.markdown(f"#### 💱 {get_text('exchange_rate_status')}")
        try:
            if 'exchange_rate_manager' in st.session_state:
                exchange_mgr = st.session_state.exchange_rate_manager
                latest_rates = exchange_mgr.get_all_latest_rates()

                if len(latest_rates) > 0:
                    st.success(f"✅ {get_text('latest_exchange_available')}")

                    # 주요 환율 표시
                    for _, rate in latest_rates.head(3).iterrows():
                        currency = rate['currency_code']
                        rate_value = rate['rate']
                        st.metric(f"USD/{currency}", f"{rate_value:,.2f}")
                else:
                    st.warning(f"⚠️ {get_text('no_exchange_data')}")
        except Exception as e:
            st.warning(f"{get_text('exchange_rate_status')}: {e}")

    st.markdown("---")

    # 최근 활동 섹션
    st.subheader(f"📈 {get_text('recent_activities')}")

    col_activity1, col_activity2 = st.columns(2)

    with col_activity1:
        st.markdown(f"#### 🆕 {get_text('recent_products')}")
        try:
            all_products = product_manager.get_all_products()
            if len(all_products) > 0 and 'input_date' in all_products.columns:
                # 날짜 컬럼을 datetime으로 변환
                all_products['input_date'] = pd.to_datetime(all_products['input_date'], errors='coerce')
                recent_products = all_products.sort_values('input_date', ascending=False).head(5)

                for _, product in recent_products.iterrows():
                    if pd.notna(product['input_date']):
                        date_str = product['input_date'].strftime('%m/%d')
                    else:
                        date_str = "N/A"
                    st.write(f"**{product['product_name']}** ({date_str})")
                    st.caption(f"{get_text('category')}: {product.get('category', 'N/A')}")
            else:
                st.info(get_text('no_recent_products'))
        except Exception as e:
            st.warning(f"{get_text('recent_products_error')}: {e}")

    with col_activity2:
        st.markdown(f"#### 📋 {get_text('recent_quotations')}")
        try:
            all_quotations = quotation_manager.get_all_quotations()
            if len(all_quotations) > 0 and 'quotation_date' in all_quotations.columns:
                # 날짜 컬럼을 datetime으로 변환
                all_quotations['quotation_date'] = pd.to_datetime(all_quotations['quotation_date'], errors='coerce')
                recent_quotations = all_quotations.sort_values('quotation_date', ascending=False).head(5)

                for _, quotation in recent_quotations.iterrows():
                    if pd.notna(quotation['quotation_date']):
                        date_str = quotation['quotation_date'].strftime('%m/%d')
                    else:
                        date_str = "N/A"
                    st.write(f"**{quotation['quotation_number']}** ({date_str})")
                    st.caption(f"{get_text('customer')}: {quotation.get('customer_name', 'N/A')} | {get_text('amount')}: ${quotation.get('total_amount_usd', 0):,.0f}")
            else:
                st.info(get_text('no_recent_quotations'))
        except Exception as e:
            st.warning(f"{get_text('recent_quotations_error')}: {e}")

    # 시스템 알림
    st.markdown("---")
    st.subheader(f"🔔 {get_text('system_alerts')}")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        # 재고 부족 알림
        try:
            if 'inventory_manager' in st.session_state:
                inventory_mgr = st.session_state.inventory_manager
                low_stock_items = inventory_mgr.get_low_stock_items()
                
                if len(low_stock_items) > 0:
                    st.warning(f"⚠️ {get_text('low_stock_warning')}: {len(low_stock_items)}개")
                    with st.expander(get_text('low_stock_list')):
                        for _, item in low_stock_items.iterrows():
                            st.write(f"• {item['product_name']} ({get_text('current_stock')}: {item['current_stock']}, {get_text('minimum_stock')}: {item['minimum_stock']})")
                else:
                    st.success(f"✅ {get_text('all_stock_sufficient')}")
        except Exception as e:
            st.info(get_text('stock_info_unavailable'))
    
    with alert_col2:
        # 연체 인보이스 알림
        try:
            if 'invoice_manager' in st.session_state:
                invoice_mgr = st.session_state.invoice_manager
                overdue_invoices = invoice_mgr.get_overdue_invoices()
                
                if len(overdue_invoices) > 0:
                    st.error(f"🚨 {get_text('overdue_invoices')}: {len(overdue_invoices)}건")
                    total_overdue = overdue_invoices['total_amount'].sum()
                    st.write(f"{get_text('overdue_total')}: ${total_overdue:,.2f}")
                else:
                    st.success(f"✅ {get_text('no_overdue_invoices')}")
        except Exception as e:
            st.info(get_text('invoice_info_unavailable'))
