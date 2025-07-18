#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from datetime import datetime

class MemberExtractorWithCompany:
    """조합원 명부에서 기업명을 포함한 특정 데이터만 추출"""
    
    def __init__(self):
        print("👥 조합원 데이터 추출기 (기업명 포함) 초기화")
        
    def find_data_start_row(self, df, expected_columns):
        """실제 데이터가 시작되는 행 찾기"""
        for idx, row in df.iterrows():
            row_str = ' '.join(str(cell) for cell in row if pd.notna(cell)).lower()
            matches = sum(1 for col in expected_columns if col in row_str)
            
            if matches >= 3:
                print(f"  🎯 데이터 시작 행 발견: {idx}행")
                print(f"  매칭된 컬럼: {matches}개")
                return idx
        
        print("  ❌ 적절한 헤더 행을 찾지 못함")
        return None
    
    def clean_phone(self, phone):
        """전화번호 정리"""
        if pd.isna(phone) or str(phone).strip() == '' or str(phone) == 'nan':
            return ''
        
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 11 and digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) >= 9:
            if digits.startswith('02'):
                if len(digits) == 9:
                    return f"02-{digits[2:5]}-{digits[5:]}"
                elif len(digits) == 10:
                    return f"02-{digits[2:6]}-{digits[6:]}"
            else:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return str(phone).strip()
    
    def clean_date(self, date_val):
        """날짜 정리 (Excel 시리얼 숫자 포함)"""
        if pd.isna(date_val) or str(date_val).strip() == '' or str(date_val) == 'nan':
            return ''
        
        try:
            # pandas datetime 객체인 경우
            if isinstance(date_val, datetime):
                return date_val.strftime('%Y-%m-%d')
            
            # 숫자인 경우 (Excel 시리얼 날짜)
            if isinstance(date_val, (int, float)):
                if 1 <= date_val <= 99999:  # 합리적인 범위 체크
                    excel_date = pd.to_datetime('1899-12-30') + pd.Timedelta(days=date_val)
                    return excel_date.strftime('%Y-%m-%d')
            
            # 문자열인 경우
            date_str = str(date_val).strip()
            
            # 순수 숫자 문자열인 경우 (Excel 시리얼 날짜)
            if date_str.isdigit():
                date_num = int(date_str)
                if 1 <= date_num <= 99999:
                    excel_date = pd.to_datetime('1899-12-30') + pd.Timedelta(days=date_num)
                    return excel_date.strftime('%Y-%m-%d')
            
            # 일반적인 날짜 문자열 형식들
            if len(date_str) >= 8:
                for fmt in ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d', '%Y%m%d']:
                    try:
                        parsed_date = datetime.strptime(date_str[:10], fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
        except Exception as e:
            print(f"    날짜 변환 오류 ({date_val}): {e}")
            pass
        
        return str(date_val).strip()
    
    def clean_company_name(self, company):
        """기업명 정리"""
        if pd.isna(company) or str(company).strip() == '' or str(company) == 'nan':
            return ''
        
        company_str = str(company).strip()
        return company_str
    
    def extract_member_data_with_company(self, file_path):
        """조합원 명부에서 기업명을 포함한 데이터 추출"""
        print(f"\n📊 조합원 명부 데이터 추출: {file_path}")
        
        try:
            # 전체 파일 읽기 (헤더 없이)
            df = pd.read_excel(file_path, header=None)
            print(f"  원본 크기: {len(df)}행 x {len(df.columns)}열")
            
            # 예상 컬럼들 (기업명 포함)
            expected_columns = ['연번', '상태', '이름', '연락처', '이메일', '구분', '분야', '기업', '단체']
            
            # 실제 데이터 시작 행 찾기
            data_start_row = self.find_data_start_row(df, expected_columns)
            
            if data_start_row is None:
                print("  ❌ 적절한 데이터 구조를 찾지 못했습니다")
                return None
            
            # 헤더 행을 기준으로 다시 읽기
            df = pd.read_excel(file_path, header=data_start_row)
            print(f"  실제 데이터: {len(df)}행")
            
            # 모든 컬럼 출력 (디버깅용)
            print(f"  모든 컬럼: {list(df.columns)}")
            
            # 핵심 컬럼 찾기 (기업명 포함)
            core_columns = {}
            for col in df.columns:
                col_str = str(col).lower()
                if '상태' in col_str:
                    core_columns['status'] = col
                elif '이름' in col_str:
                    core_columns['name'] = col
                elif '연락처' in col_str or '전화' in col_str:
                    core_columns['phone'] = col
                elif '이메일' in col_str or 'email' in col_str:
                    core_columns['email'] = col
                elif '구분' in col_str:
                    core_columns['category'] = col
                elif '분야' in col_str:
                    core_columns['field'] = col
                elif '기업' in col_str and '단체' in col_str:  # "기업/단체명" 같은 컬럼
                    core_columns['company'] = col
                elif '기업' in col_str or '단체' in col_str or '회사' in col_str:
                    if 'company' not in core_columns:  # 백업용
                        core_columns['company'] = col
            
            print(f"  핵심 컬럼 매핑: {core_columns}")
            
            if 'status' not in core_columns or 'name' not in core_columns:
                print("  ❌ '상태' 또는 '이름' 컬럼을 찾을 수 없습니다")
                return None
            
            # "가입" 상태인 사람들만 필터링
            status_column = core_columns['status']
            
            # 상태 컬럼의 고유값 확인
            unique_statuses = df[status_column].dropna().unique()
            print(f"  상태 컬럼의 고유값: {list(unique_statuses)}")
            
            # "가입" 키워드가 포함된 행 찾기
            active_members = df[df[status_column].astype(str).str.contains('가입', na=False)]
            print(f"  '가입' 상태 조합원: {len(active_members)}명")
            
            if len(active_members) == 0:
                print("  ❌ '가입' 상태인 조합원이 없습니다")
                return None
            
            # 필요한 데이터만 추출
            extracted_data = []
            
            for idx, row in active_members.iterrows():
                # 이름 확인 (필수)
                name = str(row.get(core_columns.get('name', ''), '')).strip()
                if not name or name == 'nan' or len(name) < 2:
                    continue
                
                member_data = {
                    '이름': name,
                    '연락처': self.clean_phone(row.get(core_columns.get('phone', ''), '')),
                    '구분': str(row.get(core_columns.get('category', ''), '')).strip(),
                    '이메일': str(row.get(core_columns.get('email', ''), '')).strip(),
                    '분야': str(row.get(core_columns.get('field', ''), '')).strip(),
                    '기업/단체명': self.clean_company_name(row.get(core_columns.get('company', ''), '')),
                    '원본행': idx
                }
                
                extracted_data.append(member_data)
            
            print(f"  ✅ 추출된 데이터: {len(extracted_data)}건")
            
            # DataFrame으로 변환
            result_df = pd.DataFrame(extracted_data)
            
            # 결과 출력
            if not result_df.empty:
                print(f"\n📋 추출된 데이터 미리보기:")
                print(result_df.head(10).to_string(index=False))
                
                print(f"\n📊 데이터 요약:")
                print(f"  총 조합원: {len(result_df)}명")
                
                # 기업명 보유 통계
                company_members = result_df[
                    (result_df['기업/단체명'] != '') & 
                    (result_df['기업/단체명'] != 'nan') & 
                    (~result_df['기업/단체명'].isna())
                ]
                print(f"  기업명 보유: {len(company_members)}명 ({len(company_members)/len(result_df)*100:.1f}%)")
                
                if len(company_members) > 0:
                    unique_companies = company_members['기업/단체명'].unique()
                    print(f"  등록된 기업: {len(unique_companies)}개")
                    print(f"    예시: {list(unique_companies)[:5]}{'...' if len(unique_companies) > 5 else ''}")
                
                # 구분별 통계
                if '구분' in result_df.columns:
                    category_counts = result_df['구분'].value_counts()
                    print(f"  구분별 현황:")
                    for category, count in category_counts.items():
                        if category and category != 'nan':
                            print(f"    {category}: {count}명")
                
                # 데이터 완성도
                phone_count = len(result_df[result_df['연락처'] != ''])
                email_count = len(result_df[result_df['이메일'] != ''])
                company_count = len(company_members)
                
                print(f"  데이터 완성도:")
                print(f"    연락처 보유: {phone_count}/{len(result_df)}명 ({phone_count/len(result_df)*100:.1f}%)")
                print(f"    이메일 보유: {email_count}/{len(result_df)}명 ({email_count/len(result_df)*100:.1f}%)")
                print(f"    기업명 보유: {company_count}/{len(result_df)}명 ({company_count/len(result_df)*100:.1f}%)")
            
            return result_df
            
        except Exception as e:
            print(f"  ❌ 데이터 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_extracted_data(self, df, output_file='extracted_members_with_company.csv'):
        """추출된 데이터 저장"""
        if df is None or df.empty:
            print("❌ 저장할 데이터가 없습니다")
            return False
        
        try:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"💾 추출된 데이터 저장: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    extractor = MemberExtractorWithCompany()
    
    # 파일 경로 (기업명 포함 파일)
    member_file = 'utt/조합원_후원자_기업명.xlsx'
    
    # 파일 존재 확인
    if not os.path.exists(member_file):
        print(f"❌ 파일을 찾을 수 없습니다: {member_file}")
        return
    
    # 데이터 추출
    result_df = extractor.extract_member_data_with_company(member_file)
    
    if result_df is not None and not result_df.empty:
        # 저장
        extractor.save_extracted_data(result_df, 'extracted_members_with_company.csv')
        
        print(f"\n🎉 데이터 추출 완료!")
        print(f"총 {len(result_df)}명의 '가입' 상태 조합원 데이터를 추출했습니다.")
        print(f"생성된 파일: extracted_members_with_company.csv")
        
        # 다음 단계 제안
        print(f"\n📋 다음 단계:")
        print(f"1. extracted_members_with_company.csv 파일 확인")
        print(f"2. 기존 extracted_members.csv를 이 파일로 교체")
        print(f"3. 매칭 시스템에서 기업명 매칭 활용")
        
    else:
        print(f"❌ 추출할 데이터가 없습니다")

if __name__ == "__main__":
    main()