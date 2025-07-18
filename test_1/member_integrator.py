import pandas as pd
import re
import logging

class MemberCSVIntegrator:
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('MemberIntegrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_csv_files(self, member_file, supporter_file):
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
        
        def try_load_csv(file_path):
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.logger.info(f"{file_path} 로드 성공 (인코딩: {encoding})")
                    return df
                except:
                    continue
            raise ValueError(f"{file_path} 로드 실패")
        
        member_df = try_load_csv(member_file)
        supporter_df = try_load_csv(supporter_file)
        return member_df, supporter_df
    
    def normalize_phone(self, phone):
        if pd.isna(phone) or not phone:
            return None
        
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 11 and digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return str(phone).strip()
    
    def normalize_name(self, name):
        if pd.isna(name) or not name:
            return None
        
        name = re.sub(r'\s+', '', str(name).strip())
        return name if len(name) >= 2 else None
    
    def normalize_amount(self, amount):
        if pd.isna(amount) or not amount:
            return 0.0
        
        if isinstance(amount, str):
            amount = re.sub(r'[^\d.]', '', amount)
        
        try:
            return float(amount)
        except:
            return 0.0
    
    def standardize_dataframe(self, df, source_type):
        standardized = df.copy()
        
        # 컬럼명 매핑
        column_mapping = {
            '이름': 'name', '성명': 'name', '회원명': 'name', '후원자명': 'name',
            '전화번호': 'phone', '연락처': 'phone', '휴대폰': 'phone',
            '이메일': 'email', '이메일주소': 'email', 'e-mail': 'email',
            '조합비': 'amount', '후원금': 'amount', '납입금액': 'amount', '후원금액': 'amount',
            '주소': 'address', '거주지': 'address',
            '가입일': 'join_date', '등록일': 'join_date', '후원시작일': 'join_date'
        }
        
        # 컬럼명 변경
        for old_col, new_col in column_mapping.items():
            if old_col in standardized.columns:
                standardized = standardized.rename(columns={old_col: new_col})
        
        # 필수 컬럼 생성
        required_columns = ['name', 'phone', 'email', 'amount', 'address', 'join_date']
        for col in required_columns:
            if col not in standardized.columns:
                standardized[col] = None
        
        # 데이터 정규화
        standardized['name'] = standardized['name'].apply(self.normalize_name)
        standardized['phone'] = standardized['phone'].apply(self.normalize_phone)
        standardized['amount'] = standardized['amount'].apply(self.normalize_amount)
        
        # 소스 정보 추가
        standardized['source_type'] = source_type
        
        # 유효하지 않은 행 제거
        standardized = standardized.dropna(subset=['name'])
        standardized = standardized[standardized['name'].str.len() >= 2]
        
        return standardized
    
    def calculate_similarity(self, member1, member2):
        similarity_score = 0.0
        
        # 이름 유사도
        if member1['name'] and member2['name']:
            if member1['name'] == member2['name']:
                similarity_score += 0.4
        
        # 전화번호 유사도
        if member1['phone'] and member2['phone']:
            if member1['phone'] == member2['phone']:
                similarity_score += 0.5
        
        # 이메일 유사도
        if member1['email'] and member2['email']:
            if str(member1['email']).lower() == str(member2['email']).lower():
                similarity_score += 0.1
        
        return similarity_score
    
    def find_duplicates(self, df):
        duplicate_groups = []
        processed_indices = set()
        
        for i, row1 in df.iterrows():
            if i in processed_indices:
                continue
            
            duplicate_group = [i]
            
            for j, row2 in df.iterrows():
                if j <= i or j in processed_indices:
                    continue
                
                similarity = self.calculate_similarity(row1.to_dict(), row2.to_dict())
                
                if similarity >= 0.85:
                    duplicate_group.append(j)
                    processed_indices.add(j)
            
            if len(duplicate_group) > 1:
                duplicate_groups.append(duplicate_group)
                for idx in duplicate_group:
                    processed_indices.add(idx)
        
        return duplicate_groups
    
    def merge_duplicate_group(self, df, duplicate_indices):
        group_members = df.loc[duplicate_indices]
        
        # 첫 번째를 기본으로 선택
        primary_idx = duplicate_indices[0]
        primary = group_members.loc[primary_idx].to_dict()
        
        # 병합된 레코드 생성
        merged = primary.copy()
        
        # 회원 타입 결정
        types = group_members['source_type'].unique()
        if len(types) > 1:
            merged['member_type'] = 'both'
        elif 'member' in types:
            merged['member_type'] = 'member'
        else:
            merged['member_type'] = 'supporter'
        
        # 병합 정보 추가
        merged['duplicate_flag'] = True
        merged['merged_count'] = len(duplicate_indices)
        
        return merged
    
    def integrate_members(self, member_file, supporter_file):
        self.logger.info("=== 조합원/후원자 명단 통합 시작 ===")
        
        # 1. 파일 로드
        member_df, supporter_df = self.load_csv_files(member_file, supporter_file)
        self.logger.info(f"조합원: {len(member_df)}행, 후원자: {len(supporter_df)}행")
        
        # 2. 데이터 표준화
        member_std = self.standardize_dataframe(member_df, 'member')
        supporter_std = self.standardize_dataframe(supporter_df, 'supporter')
        
        # 3. 데이터 통합
        combined_df = pd.concat([member_std, supporter_std], ignore_index=True)
        self.logger.info(f"통합 전 총 {len(combined_df)}건")
        
        # 4. 중복 탐지
        duplicate_groups = self.find_duplicates(combined_df)
        self.logger.info(f"중복 그룹 {len(duplicate_groups)}개 발견")
        
        # 5. 중복 병합
        integrated_records = []
        processed_indices = set()
        
        # 중복 그룹 병합
        for group in duplicate_groups:
            merged_record = self.merge_duplicate_group(combined_df, group)
            integrated_records.append(merged_record)
            processed_indices.update(group)
        
        # 중복되지 않은 레코드 추가
        for idx, row in combined_df.iterrows():
            if idx not in processed_indices:
                record = row.to_dict()
                record['member_type'] = record['source_type']
                record['duplicate_flag'] = False
                record['merged_count'] = 1
                integrated_records.append(record)
        
        result_df = pd.DataFrame(integrated_records)
        result_df = result_df.drop(['source_type'], axis=1, errors='ignore')
        result_df = result_df.reset_index(drop=True)
        
        self.logger.info(f"=== 통합 완료: {len(result_df)}건 ===")
        return result_df
    
    def save_results(self, result_df, output_file='통합_명단.csv'):
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        self.logger.info(f"통합 결과 저장: {output_file}")
        
        # 리포트 생성
        report = {
            'summary': {
                'total_members': len(result_df),
                'members_only': len(result_df[result_df['member_type'] == 'member']),
                'supporters_only': len(result_df[result_df['member_type'] == 'supporter']),
                'both': len(result_df[result_df['member_type'] == 'both']),
                'duplicates_merged': len(result_df[result_df['duplicate_flag'] == True])
            },
            'data_quality': {
                'complete_phone': len(result_df[result_df['phone'].notna()]),
                'complete_email': len(result_df[result_df['email'].notna()]),
                'has_amount': len(result_df[result_df['amount'] > 0])
            },
            'statistics': {
                'avg_amount': result_df['amount'].mean(),
                'total_amount': result_df['amount'].sum(),
                'max_amount': result_df['amount'].max(),
                'min_amount': result_df[result_df['amount'] > 0]['amount'].min() if len(result_df[result_df['amount'] > 0]) > 0 else 0
            }
        }
        
        return report

if __name__ == "__main__":
    integrator = MemberCSVIntegrator()
    
    try:
        result = integrator.integrate_members(
            member_file='utt/조합원_후원자명부.csv',
            supporter_file='utt/후원자_명부.csv'
        )
        
        print(f"✅ 고급 명부 통합 완료: {len(result)}명")
        print("\n미리보기:")
        print(result[['name', 'phone', 'member_type', 'amount', 'duplicate_flag']].head())
        
        # 결과 저장
        report = integrator.save_results(result, '통합_명단.csv')
        
        print(f"\n📊 통합 결과:")
        print(f"- 총 인원: {report['summary']['total_members']}명")
        print(f"- 조합원만: {report['summary']['members_only']}명")
        print(f"- 후원자만: {report['summary']['supporters_only']}명") 
        print(f"- 조합원+후원자: {report['summary']['both']}명")
        print(f"- 중복 병합: {report['summary']['duplicates_merged']}건")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()