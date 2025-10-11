import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from utils.preprocess import load_data, summarize_by_category, summarize_by_month

st.set_page_config(page_title="개인 가계부 분석기", layout="wide")

st.title("📊 개인 가계부 분석기")
st.write("CSV 파일을 업로드하면 자동으로 분석해드립니다.")

# 파일 업로드
uploaded_file = st.file_uploader("거래내역 CSV 업로드", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)

    st.subheader("원본 데이터 미리보기")
    st.dataframe(df.head())

    # 카테고리별 지출 합계
    st.subheader("카테고리별 지출 합계")
    cat_summary = summarize_by_category(df)
    fig1 = px.pie(cat_summary, values=cat_summary.values, names=cat_summary.index,
                  title="카테고리별 지출 비율")
    st.plotly_chart(fig1, use_container_width=True)

    # 월별 수입/지출 추이
    st.subheader("월별 수입/지출 추이")
    monthly = summarize_by_month(df)
    fig2 = px.bar(monthly, x=monthly.index.astype(str), y=["수입","지출"],
                  title="월별 수입/지출", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

    # 상세 통계
    st.subheader("📑 상세 통계")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("총 수입", f"{df[df['구분']=='수입']['금액'].sum():,} 원")
    with col2:
        st.metric("총 지출", f"{abs(df[df['구분']=='지출']['금액'].sum()):,} 원")

else:
    st.info("먼저 CSV 파일을 업로드하세요.")
