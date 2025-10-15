"""
전체 검색 엔진 모듈
적요, 메모, 카테고리 전체 검색
"""
import pandas as pd
import re


class SearchEngine:
    """검색 엔진 클래스"""
    
    def __init__(self):
        """초기화"""
        self.search_history = []
    
    def search(self, df, query, search_in=['적요', '메모', '분류']):
        """
        전체 검색
        
        Args:
            df: 거래내역 DataFrame
            query: 검색어
            search_in: 검색할 컬럼 리스트
            
        Returns:
            pd.DataFrame: 검색 결과
        """
        if not query or query.strip() == '':
            return df
        
        query_lower = query.lower().strip()
        
        # 검색 이력 저장
        if query_lower not in self.search_history:
            self.search_history.append(query_lower)
            if len(self.search_history) > 20:
                self.search_history.pop(0)
        
        # 각 컬럼에서 검색
        mask = pd.Series([False] * len(df))
        
        for col in search_in:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False)
        
        return df[mask]
    
    def advanced_search(self, df, filters):
        """
        고급 검색 (여러 조건 결합)
        
        Args:
            df: DataFrame
            filters: 필터 딕셔너리
        
        Returns:
            pd.DataFrame: 필터링된 결과
        """
        result = df.copy()
        
        # 텍스트 검색
        if filters.get('query'):
            result = self.search(result, filters['query'])
        
        # 날짜 범위
        if filters.get('date_from'):
            result = result[result['날짜'] >= pd.to_datetime(filters['date_from'])]
        
        if filters.get('date_to'):
            result = result[result['날짜'] <= pd.to_datetime(filters['date_to'])]
        
        # 금액 범위
        if filters.get('amount_min') is not None:
            result = result[result['금액_절대값'] >= filters['amount_min']]
        
        if filters.get('amount_max') is not None:
            result = result[result['금액_절대값'] <= filters['amount_max']]
        
        # 카테고리
        if filters.get('categories'):
            result = result[result['분류'].isin(filters['categories'])]
        
        # 구분 (수입/지출)
        if filters.get('transaction_type'):
            result = result[result['구분'] == filters['transaction_type']]
        
        return result
    
    def get_search_history(self):
        """검색 이력 조회"""
        return self.search_history[-10:][::-1]
    
    def clear_search_history(self):
        """검색 이력 삭제"""
        self.search_history = []