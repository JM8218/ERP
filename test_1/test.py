#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from datetime import datetime

# 외부 모듈 import 제거 - 기본 라이브러리만 사용
def create_test_files():
    """테스트용 파일들 생성 (utt 폴더에)"""
    print("테스트 파일 생성 중...")
    
    # utt 폴더 생성 (없으면)
    if not os.path.exists('utt'):
        os.makedirs('utt')
        print("✅ utt 폴더 생성됨")
    
    # 1. NH 거래내역
    nh_data = [
        ['거래일자', '거래시간', '출금금액', '입금금액', '잔액', '거래내용', '입금자'],
        ['총 5건', '', '', '', '', '', ''],
        ['20241201', '143022', '', '50000', '1500000', '입금', '김철수'],
        ['20241202', '101545', '', '30000', '1530000', '입금', '이영희'],
        ['20241203', '161230', '', '100000', '1630000', '입금', '박민수'],
        ['내부이체_공과금1', '', '', '', '', '', ''],
        ['관리점수수료', '', '1000', '', '1629000', '수수료', ''],
        ['20241205', '094512', '', '25000', '1654000', '입금', '정미영']
    ]
    
    with open('utt/NH_거래내역.csv', 'w', encoding='utf-8-sig', newline='') as f:
        for row in nh_data:
            f.write(','.join(str(x) for x in row) + '\n')
    
    # 2. SH 거래내역
    sh_data = [
        ['날짜', '시간', '금액', '입금자명', '메모'],
        ['총 3건', '', '', '', ''],
        ['2024-12-01', '14:30', '50000', '김철수', '후원금'],
        ['2024-12-03', '16:12', '75000', '최진우', '조합비'],
        ['관리수수료', '', '2000', '', '수수료'],
        ['2024-12-04', '10:45', '40000', '송은정', '후원금']
    ]
    
    with open('utt/SH_거래내역.csv', 'w', encoding='utf-8-sig', newline='') as f:
        for row in sh_data:
            f.write(','.join(str(x) for x in row) + '\n')
    
    # 3. Donus 거래내역
    donus_data = [
        ['Date', 'Amount', 'Donor Name', 'Payment Method', 'Note'],
        ['Total 4 transactions', '', '', '', ''],
        ['2024-12-02', '30000', '이영희', 'Card', 'Monthly donation'],
        ['2024-12-04', '60000', '한지민', 'Bank Transfer', 'Special donation'],
        ['Fee', '500', '', '', 'Processing fee'],
        ['2024-12-06', '35000', '오준석', 'Card', 'Regular support']
    ]
    
    with open('utt/Donus_거래내역.csv', 'w', encoding='utf-8-sig', newline='') as f:
        for row in donus_data:
            f.write(','.join(str(x) for x in row) + '\n')
    
    # 4. 조합원 명부
    member_data = [
        ['이름', '전화번호', '이메일', '납입금액', '회원타입'],
        ['김철수', '010-1234-5678', 'kim@email.com', '50000', '조합원'],
        ['박민수', '010-2345-6789', 'park@email.com', '100000', '조합원'], 
        ['정미영', '010-3456-7890', 'jung@email.com', '25000', '조합원'],
        ['최진우', '010-4567-8901', 'choi@email.com', '75000', '조합원']
    ]
    
    with open('utt/조합원_후원자명부.csv', 'w', encoding='utf-8-sig', newline='') as f:
        for row in member_data:
            f.write(','.join(str(x) for x in row) + '\n')
    
    # 5. 후원자 명부
    supporter_data = [
        ['이름', '연락처', '이메일주소', '후원금액', '후원방식'],
        ['이영희', '010-9876-5432', 'lee@email.com', '30000', '월정기'],
        ['한지민', '010-8765-4321', 'han@email.com', '60000', '일시불'],
        ['송은정', '010-7654-3210', 'song@email.com', '40000', '월정기'],
        ['오준석', '010-6543-2109', 'oh@email.com', '35000', '월정기']
    ]
    
    with open('utt/후원자_명부.csv', 'w', encoding='utf-8-sig', newline='') as f:
        for row in supporter_data:
            f.write(','.join(str(x) for x in row) + '\n')
    
    print("✅ 테스트 파일 생성 완료! (utt 폴더에 저장됨)")
    return True

def simple_file_check():
    """간단한 파일 확인"""
    print("\n=== 파일 확인 ===")
    
    files_to_check = [
        'utt/NH_거래내역.csv',
        'utt/SH_거래내역.csv', 
        'utt/Donus_거래내역.csv',
        'utt/조합원_후원자명부.csv',
        'utt/후원자_명부.csv'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
            
            # 파일 내용 미리보기
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    print(f"   첫 줄: {first_line}")
            except Exception as e:
                print(f"   읽기 오류: {e}")
        else:
            print(f"❌ {file_path} (없음)")

def test_pandas_read():
    """pandas로 파일 읽기 테스트"""
    print("\n=== Pandas 파일 읽기 테스트 ===")
    
    # 1. 조합원 명부 읽기
    try:
        member_df = pd.read_csv('utt/조합원_후원자명부.csv', encoding='utf-8-sig')
        print(f"✅ 조합원 명부: {len(member_df)}행, {len(member_df.columns)}열")
        print(f"   컬럼: {list(member_df.columns)}")
        print(f"   미리보기:\n{member_df.head(2)}")
    except Exception as e:
        print(f"❌ 조합원 명부 읽기 실패: {e}")
    
    # 2. 후원자 명부 읽기
    try:
        supporter_df = pd.read_csv('utt/후원자_명부.csv', encoding='utf-8-sig')
        print(f"\n✅ 후원자 명부: {len(supporter_df)}행, {len(supporter_df.columns)}열")
        print(f"   컬럼: {list(supporter_df.columns)}")
        print(f"   미리보기:\n{supporter_df.head(2)}")
    except Exception as e:
        print(f"❌ 후원자 명부 읽기 실패: {e}")
    
    # 3. 거래내역 읽기
    banks = ['NH', 'SH', 'Donus']
    for bank in banks:
        try:
            df = pd.read_csv(f'utt/{bank}_거래내역.csv', encoding='utf-8-sig')
            print(f"\n✅ {bank} 거래내역: {len(df)}행, {len(df.columns)}열")
            print(f"   컬럼: {list(df.columns)}")
            print(f"   미리보기:\n{df.head(2)}")
        except Exception as e:
            print(f"❌ {bank} 거래내역 읽기 실패: {e}")

def simple_integration_test():
    """간단한 통합 테스트 (외부 모듈 없이)"""
    print("\n=== 간단한 통합 테스트 ===")
    
    try:
        # 명부 파일 읽기
        member_df = pd.read_csv('utt/조합원_후원자명부.csv', encoding='utf-8-sig')
        supporter_df = pd.read_csv('utt/후원자_명부.csv', encoding='utf-8-sig')
        
        print(f"조합원 데이터: {len(member_df)}행")
        print(f"후원자 데이터: {len(supporter_df)}행")
        
        # 간단한 컬럼 매핑
        member_df_std = member_df.copy()
        supporter_df_std = supporter_df.copy()
        
        # 컬럼명 통일
        if '연락처' in supporter_df_std.columns:
            supporter_df_std = supporter_df_std.rename(columns={'연락처': '전화번호'})
        if '이메일주소' in supporter_df_std.columns:
            supporter_df_std = supporter_df_std.rename(columns={'이메일주소': '이메일'})
        if '후원금액' in supporter_df_std.columns:
            supporter_df_std = supporter_df_std.rename(columns={'후원금액': '납입금액'})
        
        # 타입 정보 추가
        member_df_std['타입'] = '조합원'
        supporter_df_std['타입'] = '후원자'
        
        # 통합
        combined_df = pd.concat([member_df_std, supporter_df_std], ignore_index=True)
        print(f"통합 후: {len(combined_df)}행")
        
        # 중복 확인 (이름 기준)
        if '이름' in combined_df.columns:
            duplicated_names = combined_df[combined_df.duplicated('이름', keep=False)]
            if not duplicated_names.empty:
                print(f"중복 이름 발견: {len(duplicated_names)}건")
                print(duplicated_names[['이름', '전화번호', '타입']])
            else:
                print("중복 이름 없음")
        
        # 결과 저장
        combined_df.to_csv('간단_통합_명단.csv', index=False, encoding='utf-8-sig')
        print("✅ 간단_통합_명단.csv 저장 완료")
        
        return combined_df
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def simple_transaction_test():
    """간단한 거래내역 테스트"""
    print("\n=== 간단한 거래내역 테스트 ===")
    
    banks = ['NH', 'SH', 'Donus']
    all_transactions = []
    
    for bank in banks:
        try:
            df = pd.read_csv(f'utt/{bank}_거래내역.csv', encoding='utf-8-sig')
            print(f"\n{bank} 거래내역 원본: {len(df)}행")
            
            # 노이즈 제거 (간단한 버전)
            if bank == 'NH':
                # 농협: '총 N건', '내부이체', '수수료' 등 제거
                valid_rows = []
                for idx, row in df.iterrows():
                    depositor = str(row.get('입금자', ''))
                    if depositor and not any(noise in depositor for noise in ['총', '내부이체', '수수료']):
                        if len(depositor.strip()) >= 2:
                            valid_rows.append({
                                'bank': 'NH_농협',
                                'date': str(row.get('거래일자', '')),
                                'amount': str(row.get('입금금액', '')),
                                'depositor': depositor.strip(),
                                'memo': str(row.get('거래내용', ''))
                            })
                
            elif bank == 'SH':
                # 신협: '총 N건', '관리', '수수료' 등 제거
                valid_rows = []
                for idx, row in df.iterrows():
                    depositor = str(row.get('입금자명', ''))
                    if depositor and not any(noise in depositor for noise in ['총', '관리', '수수료']):
                        if len(depositor.strip()) >= 2:
                            valid_rows.append({
                                'bank': 'SH_신협',
                                'date': str(row.get('날짜', '')),
                                'amount': str(row.get('금액', '')),
                                'depositor': depositor.strip(),
                                'memo': str(row.get('메모', ''))
                            })
                            
            elif bank == 'Donus':
                # 도너스: 'Total', 'Fee' 등 제거
                valid_rows = []
                for idx, row in df.iterrows():
                    depositor = str(row.get('Donor Name', ''))
                    if depositor and not any(noise in depositor for noise in ['Total', 'Fee']):
                        if len(depositor.strip()) >= 2:
                            valid_rows.append({
                                'bank': 'Donus_도너스',
                                'date': str(row.get('Date', '')),
                                'amount': str(row.get('Amount', '')),
                                'depositor': depositor.strip(),
                                'memo': str(row.get('Note', ''))
                            })
            
            print(f"{bank} 유효 거래: {len(valid_rows)}건")
            all_transactions.extend(valid_rows)
            
        except Exception as e:
            print(f"❌ {bank} 처리 실패: {e}")
    
    if all_transactions:
        transaction_df = pd.DataFrame(all_transactions)
        print(f"\n총 통합 거래: {len(transaction_df)}건")
        
        # 결과 저장
        transaction_df.to_csv('간단_통합_거래내역.csv', index=False, encoding='utf-8-sig')
        print("✅ 간단_통합_거래내역.csv 저장 완료")
        
        return transaction_df
    else:
        print("❌ 처리된 거래 없음")
        return None

def run_simple_test():
    """간단한 테스트 실행"""
    print("🚀 간단한 통합 시스템 테스트 시작")
    print("=" * 50)
    
    # 현재 작업 디렉토리 확인
    print(f"📁 현재 디렉토리: {os.getcwd()}")
    
    # 1. 테스트 파일 생성
    if not create_test_files():
        print("❌ 테스트 파일 생성 실패")
        return
    
    # 2. 파일 확인
    simple_file_check()
    
    # 3. Pandas 읽기 테스트
    test_pandas_read()
    
    # 4. 간단한 명부 통합
    member_result = simple_integration_test()
    
    # 5. 간단한 거래내역 통합
    transaction_result = simple_transaction_test()
    
    # 6. 간단한 매칭
    if member_result is not None and transaction_result is not None:
        print("\n=== 간단한 매칭 테스트 ===")
        
        # 이름 기준 매칭
        member_names = set(member_result['이름'].str.strip())
        transaction_names = set(transaction_result['depositor'].str.strip())
        
        matched = member_names.intersection(transaction_names)
        unmatched_members = member_names - transaction_names
        unmatched_depositors = transaction_names - member_names
        
        print(f"✅ 매칭 결과:")
        print(f"   전체 회원: {len(member_names)}명")
        print(f"   전체 입금자: {len(transaction_names)}명")
        print(f"   매칭된 이름: {len(matched)}개 - {list(matched)}")
        
        if unmatched_members:
            print(f"   미매칭 회원: {list(unmatched_members)}")
        if unmatched_depositors:
            print(f"   미매칭 입금자: {list(unmatched_depositors)}")
    
    # 7. 결과 파일 확인
    print("\n=== 생성된 파일 확인 ===")
    output_files = [
        '간단_통합_명단.csv',
        '간단_통합_거래내역.csv'
    ]
    
    for file in output_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size:,} bytes)")
        else:
            print(f"❌ {file} (없음)")
    
    print("\n🎉 간단한 테스트 완료!")
    print("다음 단계:")
    print("1. member_integrator.py 파일을 test_1 폴더에 추가")
    print("2. bank_transaction_integrator.py 파일을 test_1 폴더에 추가") 
    print("3. 고급 통합 기능 테스트")

if __name__ == "__main__":
    try:
        run_simple_test()
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()