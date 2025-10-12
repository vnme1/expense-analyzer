"""
상세 분석 탭
카테고리별 지출 상세 막대그래프 + 테이블
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.preprocess import summarize_by_category


def render(df):
    """
    상세 분석 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
    """
    st.subheader("🔍 카테고리별 상세 분석")
    
    category_summary = summarize_by_category(df)
    
    if not category_summary.empty:
        # 막대그래프
        fig = px.bar(
            x=category_summary.index,
            y=category_summary.values,
            labels={'x': '카테고리', 'y': '지출액 (원)'},
            title="카테고리별 지출 상세",
            color=category_summary.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 상세 테이블
        st.markdown("### 📋 카테고리별 지출 내역")
        detail_df = pd.DataFrame({
            '카테고리': category_summary.index,
            '지출액': category_summary.values,
            '비율(%)': (category_summary.values / category_summary.sum() * 100).round(1)
        })
        
        st.dataframe(
            detail_df.style.format({
                '지출액': '{:,.0f}원',
                '비율(%)': '{:.1f}%'
            }),
            use_container_width=True
        )
    else:
        st.info("지출 데이터가 없습니다")