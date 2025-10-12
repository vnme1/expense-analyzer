"""
예산 관리 탭
예산 설정, 현황, 알림, AI 추천
"""
import streamlit as st
import plotly.graph_objects as go


def render(df, budget_manager):
    """
    예산 관리 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        budget_manager: BudgetManager 인스턴스
    """
    st.subheader("💰 예산 관리")
    
    # 월 선택
    available_months = budget_manager.get_available_months(df)
    
    if available_months:
        current_month = available_months[-1]
        if budget_manager.check_and_reset_if_needed(current_month):
            st.success(f"✅ {current_month} 예산이 자동으로 생성되었습니다!")
    
    col_mode, col_month, col_settings = st.columns([1, 2, 1])
    
    with col_mode:
        analysis_mode = st.radio(
            "분석 모드",
            options=["📅 전체 기간", "📆 월별"],
            horizontal=True
        )
    
    target_month = None
    
    with col_month:
        if analysis_mode == "📆 월별":
            if available_months:
                target_month = st.selectbox(
                    "분석할 월 선택",
                    options=available_months,
                    index=len(available_months) - 1
                )
                st.info(f"💡 {target_month} 기준으로 예산을 분석합니다")
            else:
                st.warning("⚠️ 데이터가 없습니다")
        else:
            st.info(f"💡 전체 기간 기준")
    
    with col_settings:
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state['show_budget_settings'] = not st.session_state.get('show_budget_settings', False)
    
    # 설정 패널
    if st.session_state.get('show_budget_settings', False):
        _render_settings(budget_manager, available_months)
    
    st.markdown("---")
    
    # 알림
    alerts = budget_manager.get_alerts(df, target_month)
    if alerts:
        st.markdown("### 🔔 알림")
        for alert in alerts:
            if alert['level'] == 'error':
                st.error(alert['message'])
            elif alert['level'] == 'warning':
                st.warning(alert['message'])
            else:
                st.info(alert['message'])
        st.markdown("---")
    
    # 요약 지표
    summary = budget_manager.get_monthly_summary(df, target_month)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💵 총 예산", f"{summary['총_예산']:,.0f}원")
    with col2:
        st.metric("💸 총 지출", f"{summary['총_지출']:,.0f}원")
    with col3:
        st.metric("💰 총 잔여", f"{summary['총_잔여']:,.0f}원")
    with col4:
        st.metric("📊 전체 사용률", f"{summary['전체_사용률']:.1f}%")
    
    st.markdown("---")
    
    # 예산 설정 & 현황
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        _render_budget_settings(df, budget_manager, target_month)
    
    with col_right:
        _render_budget_status(df, budget_manager, target_month)
    
    # 월별 비교 (데이터가 충분할 때)
    if len(available_months) > 1:
        st.markdown("---")
        _render_monthly_comparison(df, budget_manager)


def _render_settings(budget_manager, available_months):
    """예산 설정 패널"""
    with st.expander("⚙️ 예산 설정", expanded=True):
        st.markdown("### 🔄 자동 갱신")
        
        auto_reset = st.checkbox(
            "매월 자동으로 기본 예산 적용",
            value=budget_manager.is_auto_reset_enabled()
        )
        
        if auto_reset != budget_manager.is_auto_reset_enabled():
            budget_manager.set_auto_reset(auto_reset)
            st.success("✅ 자동 갱신 설정이 변경되었습니다")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 예산 템플릿")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("**기본 예산 → 특정 월로 복사**")
            
            if budget_manager.budgets['default']:
                copy_to_month = st.text_input("대상 월 (예: 2025-02)")
                
                if st.button("📋 복사 실행", use_container_width=True):
                    if copy_to_month and len(copy_to_month) == 7:
                        budget_manager.copy_default_to_month(copy_to_month)
                        st.success(f"✅ {copy_to_month}로 복사되었습니다")
                        st.rerun()
                    else:
                        st.error("⚠️ 올바른 형식으로 입력하세요")
            else:
                st.info("기본 예산을 먼저 설정해주세요")
        
        with col_t2:
            st.markdown("**월별 예산 삭제**")
            
            monthly_budgets = budget_manager.get_monthly_budgets_list()
            
            if monthly_budgets:
                delete_month = st.selectbox("삭제할 월 선택", options=monthly_budgets)
                
                if st.button("🗑️ 삭제 실행", use_container_width=True):
                    budget_manager.delete_monthly_budget(delete_month)
                    st.success(f"✅ {delete_month} 예산이 삭제되었습니다")
                    st.rerun()
            else:
                st.info("설정된 월별 예산이 없습니다")


def _render_budget_settings(df, budget_manager, target_month):
    """예산 설정 섹션"""
    st.markdown("### ⚙️ 예산 설정")
    
    if target_month and target_month in budget_manager.budgets['monthly']:
        st.info(f"📆 **{target_month} 전용 예산**을 설정합니다")
    else:
        st.info("📅 **기본 예산** (모든 월에 적용)")
    
    categories = df['분류'].unique().tolist()
    selected_category = st.selectbox("카테고리 선택", categories)
    
    current_budget = budget_manager.get_budget(selected_category, target_month)
    st.info(f"현재 예산: {current_budget:,.0f}원")
    
    new_budget = st.number_input(
        "새 예산 설정 (원)",
        min_value=0,
        value=int(current_budget) if current_budget > 0 else 100000,
        step=10000
    )
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 예산 저장", type="primary"):
            budget_manager.set_budget(selected_category, new_budget, target_month)
            st.success(f"✅ 예산이 {new_budget:,.0f}원으로 설정되었습니다!")
            st.rerun()
    
    with col_btn2:
        if st.button("🗑️ 예산 삭제"):
            budget_manager.delete_budget(selected_category, target_month)
            st.success(f"✅ 예산이 삭제되었습니다!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 AI 예산 추천")
    
    if 'suggested_budgets' not in st.session_state:
        st.session_state['suggested_budgets'] = None
    
    if st.button("🔮 예산 추천 받기"):
        suggested = budget_manager.suggest_budget(df)
        st.session_state['suggested_budgets'] = suggested
    
    if st.session_state['suggested_budgets']:
        st.markdown("**추천 예산:**")
        
        for cat, amount in st.session_state['suggested_budgets'].items():
            st.write(f"- **{cat}**: {amount:,.0f}원")
        
        st.markdown("")
        
        col_apply1, col_apply2 = st.columns([1, 1])
        
        with col_apply1:
            if st.button("📥 추천 예산 일괄 적용", type="primary", use_container_width=True):
                for cat, amount in st.session_state['suggested_budgets'].items():
                    budget_manager.set_budget(cat, amount, target_month)
                
                st.success("✅ 추천 예산이 일괄 적용되었습니다!")
                st.session_state['suggested_budgets'] = None
                st.rerun()
        
        with col_apply2:
            if st.button("❌ 추천 취소", use_container_width=True):
                st.session_state['suggested_budgets'] = None
                st.rerun()


def _render_budget_status(df, budget_manager, target_month):
    """예산 현황 섹션"""
    st.markdown("### 📊 예산 현황")
    
    analysis = budget_manager.analyze_spending(df, target_month)
    
    if not analysis.empty:
        st.dataframe(
            analysis.style.format({
                '예산': '{:,.0f}원',
                '지출': '{:,.0f}원',
                '잔여': '{:,.0f}원',
                '사용률(%)': '{:.1f}%'
            }),
            use_container_width=True
        )
        
        st.markdown("### 📈 카테고리별 사용률")
        
        fig = go.Figure()
        
        for _, row in analysis.iterrows():
            color = '#EF4444' if row['사용률(%)'] >= 100 else \
                    '#F59E0B' if row['사용률(%)'] >= 80 else \
                    '#10B981'
            
            fig.add_trace(go.Bar(
                x=[min(row['사용률(%)'], 100)],
                y=[row['카테고리']],
                orientation='h',
                name=row['카테고리'],
                marker_color=color,
                text=f"{row['사용률(%)']:.1f}%",
                textposition='inside',
                showlegend=False
            ))
        
        fig.update_layout(
            xaxis_title="사용률 (%)",
            xaxis_range=[0, 100],
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("예산이 설정된 카테고리가 없습니다")


def _render_monthly_comparison(df, budget_manager):
    """월별 예산 비교"""
    st.markdown("### 📊 월별 예산 사용률 추이")
    
    comparison_df = budget_manager.get_monthly_comparison(df)
    
    if not comparison_df.empty:
        fig_comparison = go.Figure()
        
        fig_comparison.add_trace(go.Scatter(
            x=comparison_df['월'],
            y=comparison_df['예산'],
            mode='lines+markers',
            name='예산',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=10)
        ))
        
        fig_comparison.add_trace(go.Scatter(
            x=comparison_df['월'],
            y=comparison_df['지출'],
            mode='lines+markers',
            name='지출',
            line=dict(color='#EF4444', width=3),
            marker=dict(size=10)
        ))
        
        fig_comparison.update_layout(
            xaxis_title="월",
            yaxis_title="금액 (원)",
            legend=dict(orientation="h", y=1.1),
            height=400
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # 사용률 차트
        fig_usage = go.Figure()
        
        fig_usage.add_trace(go.Scatter(
            x=comparison_df['월'],
            y=comparison_df['사용률(%)'],
            mode='lines+markers',
            name='사용률',
            line=dict(color='#F59E0B', width=3),
            marker=dict(size=12),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)'
        ))
        
        fig_usage.add_hline(y=80, line_dash="dash", line_color="red")
        fig_usage.add_hline(y=60, line_dash="dash", line_color="orange")
        
        fig_usage.update_layout(
            xaxis_title="월",
            yaxis_title="사용률 (%)",
            yaxis_range=[0, max(comparison_df['사용률(%)'].max() + 10, 110)],
            height=300
        )
        
        st.plotly_chart(fig_usage, use_container_width=True)
        
        st.markdown("### 📋 월별 상세 내역")
        st.dataframe(
            comparison_df.style.format({
                '예산': '{:,.0f}원',
                '지출': '{:,.0f}원',
                '잔여': '{:,.0f}원',
                '사용률(%)': '{:.1f}%'
            }),
            use_container_width=True
        )