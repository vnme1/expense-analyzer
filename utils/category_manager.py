"""
카테고리 관리 모듈
카테고리 추가, 수정, 삭제, 병합 기능
"""
import json
import os
from pathlib import Path


class CategoryManager:
    """카테고리 관리 클래스"""
    
    # 기본 카테고리 목록
    DEFAULT_CATEGORIES = [
        '식비', '교통', '쇼핑', '여가', '카페', 
        '구독', '의료', '교육', '급여', '기타'
    ]
    
    def __init__(self, categories_file='data/categories.json'):
        """
        Args:
            categories_file: 카테고리 데이터 저장 파일 경로
        """
        self.project_root = Path(__file__).parent.parent
        self.categories_file = self.project_root / categories_file
        self.categories = self.load_categories()
    
    def load_categories(self):
        """저장된 카테고리 불러오기"""
        if self.categories_file.exists():
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.DEFAULT_CATEGORIES.copy()
    
    def save_categories(self):
        """카테고리 저장하기"""
        self.categories_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.categories_file, 'w', encoding='utf-8') as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)
    
    def get_all_categories(self):
        """전체 카테고리 조회"""
        return self.categories.copy()
    
    def add_category(self, category_name):
        """
        카테고리 추가
        
        Args:
            category_name: 추가할 카테고리명
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if not category_name or category_name.strip() == '':
            return {'success': False, 'message': '카테고리 이름을 입력해주세요'}
        
        category_name = category_name.strip()
        
        if category_name in self.categories:
            return {'success': False, 'message': f'"{category_name}"는 이미 존재하는 카테고리입니다'}
        
        self.categories.append(category_name)
        self.save_categories()
        
        return {'success': True, 'message': f'"{category_name}" 카테고리가 추가되었습니다'}
    
    def delete_category(self, category_name):
        """
        카테고리 삭제
        
        Args:
            category_name: 삭제할 카테고리명
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if category_name not in self.categories:
            return {'success': False, 'message': f'"{category_name}"는 존재하지 않는 카테고리입니다'}
        
        if category_name == '기타':
            return {'success': False, 'message': '"기타" 카테고리는 삭제할 수 없습니다'}
        
        self.categories.remove(category_name)
        self.save_categories()
        
        return {'success': True, 'message': f'"{category_name}" 카테고리가 삭제되었습니다'}
    
    def rename_category(self, old_name, new_name):
        """
        카테고리 이름 변경
        
        Args:
            old_name: 기존 카테고리명
            new_name: 새 카테고리명
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if old_name not in self.categories:
            return {'success': False, 'message': f'"{old_name}"는 존재하지 않는 카테고리입니다'}
        
        if not new_name or new_name.strip() == '':
            return {'success': False, 'message': '새 카테고리 이름을 입력해주세요'}
        
        new_name = new_name.strip()
        
        if new_name in self.categories and new_name != old_name:
            return {'success': False, 'message': f'"{new_name}"는 이미 존재하는 카테고리입니다'}
        
        idx = self.categories.index(old_name)
        self.categories[idx] = new_name
        self.save_categories()
        
        return {'success': True, 'message': f'"{old_name}" → "{new_name}"으로 변경되었습니다'}
    
    def merge_categories(self, source_categories, target_category):
        """
        여러 카테고리를 하나로 병합
        
        Args:
            source_categories: 병합할 카테고리 리스트
            target_category: 대상 카테고리명
            
        Returns:
            dict: 성공 여부 및 메시지
        """
        if not source_categories or len(source_categories) == 0:
            return {'success': False, 'message': '병합할 카테고리를 선택해주세요'}
        
        if not target_category or target_category.strip() == '':
            return {'success': False, 'message': '대상 카테고리를 입력해주세요'}
        
        target_category = target_category.strip()
        
        # 대상 카테고리가 없으면 추가
        if target_category not in self.categories:
            self.categories.append(target_category)
        
        # 소스 카테고리 삭제 (대상 카테고리는 제외)
        for cat in source_categories:
            if cat != target_category and cat in self.categories:
                self.categories.remove(cat)
        
        self.save_categories()
        
        merged_str = ', '.join(source_categories)
        return {
            'success': True, 
            'message': f'{merged_str} → "{target_category}"로 병합되었습니다',
            'source_categories': source_categories,
            'target_category': target_category
        }
    
    def reset_to_default(self):
        """기본 카테고리로 초기화"""
        self.categories = self.DEFAULT_CATEGORIES.copy()
        self.save_categories()
        
        return {'success': True, 'message': '기본 카테고리로 초기화되었습니다'}
    
    def apply_category_changes_to_dataframe(self, df, rename_map=None, merge_info=None):
        """
        DataFrame에 카테고리 변경사항 적용
        
        Args:
            df: 거래내역 DataFrame
            rename_map: {old_name: new_name} 딕셔너리
            merge_info: {'source_categories': [...], 'target_category': '...'} 딕셔너리
            
        Returns:
            pd.DataFrame: 변경 적용된 DataFrame
        """
        df_copy = df.copy()
        
        # 이름 변경 적용
        if rename_map:
            df_copy['분류'] = df_copy['분류'].replace(rename_map)
        
        # 병합 적용
        if merge_info:
            source_cats = merge_info['source_categories']
            target_cat = merge_info['target_category']
            
            mask = df_copy['분류'].isin(source_cats)
            df_copy.loc[mask, '분류'] = target_cat
        
        return df_copy
    
    def get_category_statistics(self, df):
        """
        카테고리별 통계
        
        Args:
            df: 거래내역 DataFrame
            
        Returns:
            dict: 카테고리별 사용 현황
        """
        category_counts = df['분류'].value_counts().to_dict()
        
        stats = {}
        for cat in self.categories:
            stats[cat] = {
                'count': category_counts.get(cat, 0),
                'exists': cat in category_counts
            }
        
        return stats