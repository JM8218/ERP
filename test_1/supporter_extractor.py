#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from datetime import datetime

class SupporterExtractor:
    """후원자 명부에서 특정 데이터만 추출"""
    
    def __init__(self):
        print("📊 후원자 데이터 추출기 초기화")
        
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
    
    def clean_amount(self, amount_val):
        """금액 정리"""
        if pd.isna(amount_val) or str(amount_val).strip() == '' or str(amount_val) == 'nan':
            return ''
        
        # 숫자인 경우
        if isinstance(amount_val, (int, float)):
            return str(int(amount_val)) if amount_val > 0 else ''
        
        # 문자열인 경우
        amount_str = str(amount_val).strip()
        
        # 순수 숫자인지 확인
        if amount_str.replace(',', '').replace('.', '').isdigit():
            try:
                num_amount = float(amount_str.replace(',', ''))
                return str(int(num_amount)) if num_amount > 0 else ''
            except:
                pass
        
        # 숫자가 아니면 텍스트 그대로 반환 (일시후원 등)
        return amount_str
    
    def normalize_supporter_type(self, type1, type2):
        """후원자 유형 정규화"""
        type_str = f"{str(type1 or '')} {str(type2 or '')}".strip().lower()
        
        if '정기' in type_str or 'regular' in type_str:
            return '정기후원'
        elif '일시' in type_str or 'onetime' in type_str or '단발' in type_str:
            return '일시후원'
        elif '후원' in type_str or 'support' in type_str:
            return '후원자'
        else:
            return type_str.strip() or '미분류'
    
    def extract_supporter_data(self, file_path):
        """후원자 명부에서 데이터 추출"""
        print(f"\n📊 후원자 명부 데이터 추출: {file_path}")
        
        try:
            # 전체 파일 읽기 (헤더 없이)
            df = pd.read_excel(file_path, header=None)
            print(f"  원본 크기: {len(df)}행 x {len(df.columns)}열")
            
            # 예상 컬럼들
            expected_columns = ['연번', '상태', '유형', '이름', '연락처', '이메일', '약정일', '납입', '약정금액']
            
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
            
            # 핵심 컬럼 찾기 (수정된 부분)
            core_columns = {}
            for col in df.columns:
                col_str = str(col).lower()
                print(f"  컬럼 검사: '{col}' -> '{col_str}'")  # 디버깅 출력
                
                if '상태' in col_str:
                    core_columns['status'] = col
                elif '이름' in col_str:
                    core_columns['name'] = col
                elif '연락처' in col_str or '전화' in col_str:
                    core_columns['phone'] = col
                elif '이메일' in col_str or 'email' in col_str:
                    core_columns['email'] = col
                elif '유형' in col_str and 'type1' not in core_columns:
                    core_columns['type1'] = col
                elif ('유형' in col_str or 'type' in col_str) and 'type1' in core_columns:
                    core_columns['type2'] = col
                elif '최초' in col_str and ('약정일' in col_str or '가입일' in col_str):
                    core_columns['first_date'] = col
                elif '납입' in col_str and '개월' in col_str:
                    core_columns['payment_months'] = col
                # 월납입약정금액 컬럼 찾기 로직 수정
                elif ('월납입' in col_str or '약정금액' in col_str or '금액' in col_str) and 'amount' not in core_columns:
                    # 일시후원 관련 컬럼은 제외
                    if '일시' not in col_str and '단발' not in col_str:
                        core_columns['amount'] = col
                        print(f"    ✅ 금액 컬럼 발견: {col}")
            
            print(f"  핵심 컬럼 매핑: {core_columns}")
            
            # 금액 컬럼이 없는 경우 모든 컬럼을 다시 확인
            if 'amount' not in core_columns:
                print("  ⚠️ 금액 컬럼을 찾지 못했습니다. 모든 컬럼을 재검사합니다.")
                for col in df.columns:
                    col_str = str(col).lower()
                    if '금액' in col_str or '원' in col_str or 'amount' in col_str:
                        print(f"    금액 관련 컬럼 후보: {col}")
                        if 'amount' not in core_columns:
                            core_columns['amount'] = col
                            print(f"    ✅ 금액 컬럼으로 설정: {col}")
            
            if 'status' not in core_columns:
                print("  ❌ '상태' 컬럼을 찾을 수 없습니다")
                return None
            
            # "등록" 상태인 사람들만 필터링
            status_column = core_columns['status']
            
            # 상태 컬럼의 고유값 확인
            unique_statuses = df[status_column].dropna().unique()
            print(f"  상태 컬럼의 고유값: {list(unique_statuses)}")
            
            # "등록" 키워드가 포함된 행 찾기
            active_supporters = df[df[status_column].astype(str).str.contains('등록', na=False)]
            print(f"  '등록' 상태 후원자: {len(active_supporters)}명")
            
            if len(active_supporters) == 0:
                print("  ❌ '등록' 상태인 후원자가 없습니다")
                return None
            
            # 필요한 데이터만 추출
            extracted_data = []
            
            for idx, row in active_supporters.iterrows():
                # 이름 확인 (필수)
                name = str(row.get(core_columns.get('name', ''), '')).strip()
                if not name or name == 'nan' or len(name) < 2:
                    continue
                
                # 유형 정보
                type1 = row.get(core_columns.get('type1', ''), '')
                type2 = row.get(core_columns.get('type2', ''), '')
                supporter_type = self.normalize_supporter_type(type1, type2)
                
                # 납입 개월 수 (정기후원인 경우)
                payment_months = ''
                if 'payment_months' in core_columns:
                    months_val = row.get(core_columns['payment_months'], '')
                    if pd.notna(months_val) and str(months_val).strip() != 'nan':
                        payment_months = str(months_val).strip()
                
                # 월 납입 약정금액 (수정된 부분)
                amount = ''
                if 'amount' in core_columns:
                    amount_val = row.get(core_columns['amount'], '')
                    amount = self.clean_amount(amount_val)
                    print(f"    이름: {name}, 원본 금액: {amount_val}, 정리된 금액: {amount}")  # 디버깅
                
                supporter_data = {
                    '유형': supporter_type,
                    '이름': name,
                    '연락처': self.clean_phone(row.get(core_columns.get('phone', ''), '')),
                    '이메일': str(row.get(core_columns.get('email', ''), '')).strip(),
                    '최초약정일': self.clean_date(row.get(core_columns.get('first_date', ''), '')),
                    '납입개월수': payment_months,
                    '월납입약정금액': amount,
                    '원본행': idx
                }
                
                extracted_data.append(supporter_data)
            
            print(f"  ✅ 추출된 데이터: {len(extracted_data)}건")
            
            # DataFrame으로 변환
            result_df = pd.DataFrame(extracted_data)
            
            # 결과 출력
            if not result_df.empty:
                print(f"\n📋 추출된 데이터 미리보기:")
                print(result_df.head(10).to_string(index=False))
                
                print(f"\n📊 데이터 요약:")
                print(f"  총 인원: {len(result_df)}명")
                
                # 유형별 통계
                if '유형' in result_df.columns:
                    type_counts = result_df['유형'].value_counts()
                    print(f"  유형별 현황:")
                    for supporter_type, count in type_counts.items():
                        if supporter_type and supporter_type != 'nan':
                            print(f"    {supporter_type}: {count}명")
                
                # 데이터 완성도
                phone_count = len(result_df[result_df['연락처'] != ''])
                email_count = len(result_df[result_df['이메일'] != ''])
                date_count = len(result_df[result_df['최초약정일'] != ''])
                amount_count = len(result_df[result_df['월납입약정금액'] != ''])
                
                print(f"  데이터 완성도:")
                print(f"    연락처 보유: {phone_count}/{len(result_df)}명 ({phone_count/len(result_df)*100:.1f}%)")
                print(f"    이메일 보유: {email_count}/{len(result_df)}명 ({email_count/len(result_df)*100:.1f}%)")
                print(f"    최초약정일 보유: {date_count}/{len(result_df)}명 ({date_count/len(result_df)*100:.1f}%)")
                print(f"    약정금액 보유: {amount_count}/{len(result_df)}명 ({amount_count/len(result_df)*100:.1f}%)")
            
            return result_df
            
        except Exception as e:
            print(f"  ❌ 데이터 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_extracted_data(self, df, output_file='extracted_supporters.csv'):
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
    extractor = SupporterExtractor()
    
    # 파일 경로
    supporter_file = 'utt/후원자_명부.xlsx'
    
    # 파일 존재 확인
    if not os.path.exists(supporter_file):
        print(f"❌ 파일을 찾을 수 없습니다: {supporter_file}")
        return
    
    # 데이터 추출
    result_df = extractor.extract_supporter_data(supporter_file)
    
    if result_df is not None and not result_df.empty:
        # 저장
        extractor.save_extracted_data(result_df, 'extracted_supporters.csv')
        
        print(f"\n🎉 데이터 추출 완료!")
        print(f"총 {len(result_df)}명의 '등록' 상태 후원자 데이터를 추출했습니다.")
        print(f"생성된 파일: extracted_supporters.csv")
        
        # 추가 분석 제안
        print(f"\n📋 다음 단계:")
        print(f"1. extracted_supporters.csv 파일 확인")
        print(f"2. 조합원 데이터와 통합")
        print(f"3. 거래내역과 매칭 준비")
        
    else:
        print(f"❌ 추출할 데이터가 없습니다")

if __name__ == "__main__":
    main()