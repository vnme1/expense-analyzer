"""
자동 저장 및 백업 관리 모듈
"""
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import shutil


class AutoSaveManager:
    """자동 저장 및 백업 관리 클래스"""
    
    def __init__(self, base_dir='data'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.base_dir = self.project_root / base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.main_file = self.base_dir / 'user_expenses.csv'
        self.backup_dir = self.base_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def has_saved_data(self):
        """저장된 데이터가 있는지 확인"""
        return self.main_file.exists() and os.path.getsize(self.main_file) > 0
    
    def load_saved_data(self):
        """저장된 데이터 불러오기"""
        if self.has_saved_data():
            try:
                df = pd.read_csv(self.main_file, encoding='utf-8-sig')
                return df
            except Exception as e:
                print(f"데이터 로드 실패: {e}")
                return None
        return None
    
    def save_data(self, df):
        """데이터 저장"""
        try:
            df.to_csv(self.main_file, index=False, encoding='utf-8-sig')
            return {'success': True, 'message': '데이터가 저장되었습니다'}
        except Exception as e:
            return {'success': False, 'message': f'저장 실패: {str(e)}'}
    
    def merge_data(self, uploaded_df):
        """
        업로드된 데이터와 기존 데이터 병합
        
        Args:
            uploaded_df: 업로드된 DataFrame
            
        Returns:
            pd.DataFrame: 병합된 DataFrame
        """
        existing_df = self.load_saved_data()
        
        if existing_df is not None:
            # 중복 제거 (날짜, 적요, 금액이 같은 경우)
            combined = pd.concat([existing_df, uploaded_df], ignore_index=True)
            
            # 날짜를 datetime으로 변환
            combined['날짜'] = pd.to_datetime(combined['날짜'])
            
            # 중복 제거
            combined = combined.drop_duplicates(subset=['날짜', '적요', '금액'], keep='first')
            
            # 날짜순 정렬
            combined = combined.sort_values('날짜')
            
            return combined
        
        return uploaded_df
    
    def create_backup(self):
        """
        백업 생성 (일일 자동 백업)
        
        Returns:
            dict: 백업 결과
        """
        if not self.has_saved_data():
            return {'success': False, 'message': '백업할 데이터가 없습니다'}
        
        try:
            # 백업 파일명 생성 (날짜별)
            today = datetime.now().strftime('%Y%m%d')
            backup_file = self.backup_dir / f'backup_{today}.csv'
            
            # 오늘 백업이 이미 있으면 스킵
            if backup_file.exists():
                return {'success': True, 'message': '오늘 백업이 이미 존재합니다', 'skipped': True}
            
            # 백업 생성
            shutil.copy2(self.main_file, backup_file)
            
            return {'success': True, 'message': f'백업 생성: {backup_file.name}', 'skipped': False}
        
        except Exception as e:
            return {'success': False, 'message': f'백업 실패: {str(e)}'}
    
    def get_backup_list(self):
        """백업 파일 목록 조회"""
        backups = []
        
        for file in sorted(self.backup_dir.glob('backup_*.csv'), reverse=True):
            file_stat = file.stat()
            backups.append({
                'filename': file.name,
                'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f"{file_stat.st_size / 1024:.1f} KB",
                'path': file
            })
        
        return backups
    
    def restore_from_backup(self, backup_filename):
        """
        백업에서 복원
        
        Args:
            backup_filename: 백업 파일명
            
        Returns:
            dict: 복원 결과
        """
        backup_file = self.backup_dir / backup_filename
        
        if not backup_file.exists():
            return {'success': False, 'message': '백업 파일을 찾을 수 없습니다'}
        
        try:
            # 현재 데이터 백업 (복원 전)
            if self.has_saved_data():
                emergency_backup = self.backup_dir / f'before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                shutil.copy2(self.main_file, emergency_backup)
            
            # 백업에서 복원
            shutil.copy2(backup_file, self.main_file)
            
            return {'success': True, 'message': f'{backup_filename}에서 복원되었습니다'}
        
        except Exception as e:
            return {'success': False, 'message': f'복원 실패: {str(e)}'}
    
    def delete_backup(self, backup_filename):
        """백업 파일 삭제"""
        backup_file = self.backup_dir / backup_filename
        
        if not backup_file.exists():
            return {'success': False, 'message': '백업 파일을 찾을 수 없습니다'}
        
        try:
            os.remove(backup_file)
            return {'success': True, 'message': f'{backup_filename}이 삭제되었습니다'}
        except Exception as e:
            return {'success': False, 'message': f'삭제 실패: {str(e)}'}
    
    def cleanup_old_backups(self, keep_days=30):
        """
        오래된 백업 정리
        
        Args:
            keep_days: 보관 기간 (일)
        """
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        deleted = []
        for file in self.backup_dir.glob('backup_*.csv'):
            if file.stat().st_mtime < cutoff_time:
                try:
                    os.remove(file)
                    deleted.append(file.name)
                except:
                    pass
        
        return {'success': True, 'deleted_count': len(deleted), 'deleted_files': deleted}
    
    def export_all_data(self):
        """전체 데이터 내보내기 (백업 포함)"""
        if not self.has_saved_data():
            return None
        
        try:
            df = pd.read_csv(self.main_file, encoding='utf-8-sig')
            return df
        except:
            return None
    
    def get_data_info(self):
        """저장된 데이터 정보 조회"""
        if not self.has_saved_data():
            return None
        
        try:
            df = pd.read_csv(self.main_file, encoding='utf-8-sig')
            file_stat = self.main_file.stat()
            
            return {
                'record_count': len(df),
                'file_size': f"{file_stat.st_size / 1024:.1f} KB",
                'last_modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'date_range': f"{df['날짜'].min()} ~ {df['날짜'].max()}" if '날짜' in df.columns else '-'
            }
        except:
            return None