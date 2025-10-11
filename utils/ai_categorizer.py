"""
AI 기반 카테고리 자동 분류 모듈
적요(거래 내역 설명)를 기반으로 카테고리를 자동으로 예측
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import os


class CategoryClassifier:
    """카테고리 자동 분류기"""
    
    def __init__(self, model_path='models/category_model.pkl'):
        """
        Args:
            model_path: 학습된 모델 저장 경로
        """
        self.model_path = model_path
        self.pipeline = None
        self.categories = [
            '식비', '교통', '쇼핑', '여가', '카페', 
            '구독', '의료', '교육', '급여', '기타'
        ]
        
        # 카테고리별 키워드 사전
        self.keyword_dict = {
            '식비': ['마트', '이마트', '롯데마트', '편의점', 'gs25', 'cu', '세븐일레븐', '배달', '치킨', '피자', '쿠팡이츠', '배달의민족', '요기요'],
            '교통': ['택시', '버스', '지하철', '카카오t', '우버', '주차', '톨게이트', '기름', '주유', '카카오택시'],
            '쇼핑': ['쿠팡', '올리브영', '다이소', '무신사', '29cm', '옷', '의류', '신발'],
            '여가': ['영화', 'cgv', '롯데시네마', '메가박스', '노래방', 'pc방', '볼링', '놀이공원'],
            '카페': ['스타벅스', '카페', '커피', '이디야', '투썸', '할리스', '빽다방', '컴포즈', '메가커피'],
            '구독': ['넷플릭스', '유튜브', '멜론', 'spotify', '구독', '프리미엄', '왓챠'],
            '의료': ['병원', '약국', '치과', '한의원', '의원', '클리닉'],
            '교육': ['학원', '인강', '교육', '책', '강의', '수강', '교보문고'],
            '급여': ['월급', '급여', '인센티브', '보너스', '상여'],
            '기타': []
        }
    
    def _keyword_based_predict(self, text):
        """
        키워드 기반 예측 (규칙 기반)
        
        Args:
            text: 거래 내역 설명
            
        Returns:
            str: 예측된 카테고리 또는 None
        """
        text_lower = str(text).lower()
        
        for category, keywords in self.keyword_dict.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return None
    
    def train(self, df):
        """
        학습 데이터로 모델 학습
        
        Args:
            df: '적요'와 '분류' 컬럼이 있는 DataFrame
        """
        # 학습 데이터 준비
        X = df['적요'].fillna('')
        y = df['분류']
        
        # TF-IDF + Naive Bayes 파이프라인
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                analyzer='char'  # 한글은 character 단위가 효과적
            )),
            ('clf', MultinomialNB())
        ])
        
        # 모델 학습
        self.pipeline.fit(X, y)
        
        # 모델 저장
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
        
        print(f"✅ 모델 학습 완료: {len(df)}건의 데이터로 학습됨")
    
    def load_model(self):
        """저장된 모델 로드"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.pipeline = pickle.load(f)
            print(f"✅ 모델 로드 완료: {self.model_path}")
            return True
        return False
    
    def predict(self, text):
        """
        단일 텍스트에 대한 카테고리 예측
        
        Args:
            text: 거래 내역 설명
            
        Returns:
            str: 예측된 카테고리
        """
        # 1. 키워드 기반 예측 시도
        keyword_result = self._keyword_based_predict(text)
        if keyword_result:
            return keyword_result
        
        # 2. AI 모델 예측
        if self.pipeline is None:
            if not self.load_model():
                return '기타'  # 모델 없으면 기타로 분류
        
        try:
            prediction = self.pipeline.predict([str(text)])[0]
            return prediction
        except:
            return '기타'
    
    def predict_batch(self, texts):
        """
        여러 텍스트에 대한 배치 예측
        
        Args:
            texts: 텍스트 리스트 또는 Series
            
        Returns:
            list: 예측된 카테고리 리스트
        """
        predictions = []
        
        for text in texts:
            predictions.append(self.predict(text))
        
        return predictions
    
    def auto_categorize_dataframe(self, df):
        """
        DataFrame의 '적요' 컬럼을 기반으로 '분류' 자동 생성
        
        Args:
            df: '적요' 컬럼이 있는 DataFrame
            
        Returns:
            pd.DataFrame: '분류_AI' 컬럼이 추가된 DataFrame
        """
        if '적요' not in df.columns:
            raise ValueError("'적요' 컬럼이 필요합니다")
        
        df['분류_AI'] = self.predict_batch(df['적요'])
        
        return df
    
    def evaluate(self, df):
        """
        모델 성능 평가 (실제 분류와 비교)
        
        Args:
            df: '적요'와 '분류' 컬럼이 있는 DataFrame
            
        Returns:
            dict: 정확도 및 평가 지표
        """
        if self.pipeline is None:
            if not self.load_model():
                return {'accuracy': 0.0, 'message': '모델이 없습니다'}
        
        X = df['적요'].fillna('')
        y_true = df['분류']
        y_pred = self.predict_batch(X)
        
        # 정확도 계산
        correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
        accuracy = correct / len(y_true) if len(y_true) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': len(y_true),
            'message': f'정확도: {accuracy*100:.1f}% ({correct}/{len(y_true)})'
        }