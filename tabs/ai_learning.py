"""
AI 학습 탭
모델 학습, 평가, 실시간 예측
"""
import streamlit as st


def render(df, classifier):
    """
    AI 학습 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        classifier: CategoryClassifier 인스턴스
    """
    st.subheader("🤖 AI 모델 학습 및 평가")
    
    st.markdown("""
    ### AI 자동 분류란?
    - '적요' (거래 내역 설명)를 분석하여 자동으로 카테고리를 예측합니다
    - 예: "스타벅스" → 카페, "이마트" → 식비, "CGV" → 여가
    
    ### 학습 방법
    1. 카테고리가 포함된 CSV/Excel 파일 업로드
    2. 아래 '모델 학습' 버튼 클릭
    3. 이후 카테고리 없는 데이터도 자동 분류 가능!
    
    ⚠️ **주의:** 정확한 학습을 위해 최소 100건 이상의 데이터를 권장합니다.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        _render_model_status(df, classifier)
    
    with col2:
        _render_model_training(df, classifier)
    
    st.markdown("---")
    
    _render_realtime_prediction(classifier)


def _render_model_status(df, classifier):
    """모델 상태"""
    st.markdown("### 📊 현재 모델 상태")
    
    if classifier.pipeline is None:
        st.warning("⚠️ 학습된 모델이 없습니다")
    else:
        st.success("✅ 모델 로드 완료")
        
        if st.button("🎯 모델 정확도 평가"):
            if '분류' in df.columns and len(df) > 0:
                with st.spinner('평가 중...'):
                    result = classifier.evaluate(df)
                    st.metric("정확도", f"{result['accuracy']*100:.1f}%")
                    st.caption(f"{result['correct']}건 정확 / 전체 {result['total']}건")
            else:
                st.error("'분류' 컬럼이 있는 데이터가 필요합니다")


def _render_model_training(df, classifier):
    """모델 학습"""
    st.markdown("### 🎓 모델 학습")
    
    if '분류' in df.columns and '적요' in df.columns:
        st.info(f"현재 데이터: {len(df)}건")
        
        if len(df) < 50:
            st.warning("⚠️ 데이터가 너무 적습니다. 최소 50건 이상 권장합니다.")
        
        if st.button("🚀 모델 학습 시작", type="primary"):
            with st.spinner('학습 중... (수십 초 소요)'):
                try:
                    classifier.train(df)
                    st.success("✅ 학습 완료!")
                    st.balloons()
                except Exception as e:
                    st.error(f"학습 실패: {str(e)}")
    else:
        st.warning("학습을 위해서는 '적요'와 '분류' 컬럼이 필요합니다")


def _render_realtime_prediction(classifier):
    """실시간 예측"""
    st.markdown("### 🧪 실시간 예측 테스트")
    
    test_text = st.text_input(
        "적요 입력",
        placeholder="예: 스타벅스, 이마트, CGV 등",
        help="거래 내역 설명을 입력하면 AI가 카테고리를 예측합니다"
    )
    
    if test_text:
        predicted_category = classifier.predict(test_text)
        st.success(f"🎯 예측 카테고리: **{predicted_category}**")