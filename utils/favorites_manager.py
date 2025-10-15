"""
즐겨찾기 관리 모듈
자주 쓰는 거래 빠른 입력
"""
import json
from pathlib import Path
from datetime import datetime


class FavoritesManager:
    """즐겨찾기 관리 클래스"""
    
    def __init__(self, favorites_file='data/favorites.json'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.favorites_file = self.project_root / favorites_file
        self.favorites = self.load_favorites()
    
    def load_favorites(self):
        """저장된 즐겨찾기 불러오기"""
        if self.favorites_file.exists():
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_favorites(self):
        """즐겨찾기 저장"""
        self.favorites_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)
    
    def add_favorite(self, name, amount, category, memo=""):
        """즐겨찾기 추가"""
        if any(f['name'] == name for f in self.favorites):
            return {'success': False, 'message': f'"{name}"는 이미 즐겨찾기에 있습니다'}
        
        if len(self.favorites) >= 20:
            return {'success': False, 'message': '즐겨찾기는 최대 20개까지 가능합니다'}
        
        favorite = {
            'id': len(self.favorites) + 1,
            'name': name,
            'amount': float(amount),
            'category': category,
            'memo': memo,
            'use_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_used': None
        }
        
        self.favorites.append(favorite)
        self.save_favorites()
        
        return {'success': True, 'message': f'"{name}"가 즐겨찾기에 추가되었습니다'}
    
    def remove_favorite(self, favorite_id):
        """즐겨찾기 삭제"""
        self.favorites = [f for f in self.favorites if f['id'] != favorite_id]
        self.save_favorites()
        return {'success': True, 'message': '즐겨찾기가 삭제되었습니다'}
    
    def use_favorite(self, favorite_id):
        """즐겨찾기 사용"""
        for favorite in self.favorites:
            if favorite['id'] == favorite_id:
                favorite['use_count'] += 1
                favorite['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.save_favorites()
                
                return {
                    'success': True,
                    'transaction': {
                        '적요': favorite['name'],
                        '금액': favorite['amount'],
                        '분류': favorite['category'],
                        '메모': favorite['memo']
                    }
                }
        
        return {'success': False, 'message': '즐겨찾기를 찾을 수 없습니다'}
    
    def get_all_favorites(self):
        """전체 즐겨찾기 조회"""
        return self.favorites
    
    def get_most_used(self, limit=5):
        """가장 많이 쓴 즐겨찾기"""
        sorted_favorites = sorted(
            self.favorites,
            key=lambda x: x.get('use_count', 0),
            reverse=True
        )
        return sorted_favorites[:limit]