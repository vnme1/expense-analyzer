"""
월별 추이 탭
월별 수입/지출/잔액 라인차트 + 테이블
"""
import streamlit as st
import plotly.graph_objects as go
from utils.preprocess import summarize_by_month


def render(df):
    """
    월별 추이 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
    """
    st.subheader("📅 월별 수입/지출 추이")
    
    monthly_summary = summarize_by_month(df)
    
    # 라인 차트
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['수입'],
        mode='lines+markers',
        name='수입',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=10)
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['지출'],
        mode='lines+markers',
        name='지출',
        line=dict(color='#FF5252', width=3),
        marker=dict(size=10)
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['잔액'],
        mode='lines+markers',
        name='잔액',
        line=dict(color='#2196F3', width=3, dash='dot'),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        xaxis_title="월",
        yaxis_title="금액 (원)",
        legend=dict(orientation="h", y=1.1),
        xaxis=dict(type='category')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 상세 테이블
    st.markdown("### 📊 월별 상세 내역")
    monthly_display = monthly_summary.copy()
    monthly_display.columns = ['수입', '지출', '잔액']
    
    st.dataframe(
        monthly_display.style.format('{:,.0f}원'),
        use_container_width=True
    )