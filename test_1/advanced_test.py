#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from datetime import datetime
from member_integrator import MemberCSVIntegrator

def test_member_integration():
    """고급 명부 통합 테스트"""
    print("🚀 고급 명부 통합 테스트 시작")
    print("=" * 50)
    
    try:
        # MemberCSVIntegrator 사용
        integrator = MemberCSVIntegrator()
        
        result = integrator.integrate_members(
            member_file='utt/조합원_후원자명부.csv',
            supporter_file='utt/후원자_명부.csv'
        )
        
        print(f"\n✅ 고급 명부 통합 완료: {len(result)}명")
        
        # 상세 정보 출력
        print(f"\n📋 컬럼 정보:")
        print(f"전체 컬럼: {list(result.columns)}")
        
        print(f"\n📊 미리보기:")
        if 'duplicate_flag' in result.columns:
            display_cols = ['name', 'phone', 'member_type', 'amount', 'duplicate_flag']
        else:
            display_cols = ['name', 'phone', 'member_type', 'amount']
        
        available_cols = [col for col in display_cols if col in result.columns]
        print(result[available_cols].head())
        
        # 결과 저장 및 리포트 생성
        report = integrator.save_results(result, '통합_명단.csv')
        
        print(f"\n📈 통합 결과 요약:")
        print(f"- 총 인원: {report['summary']['total_members']}명")
        print(f"- 조합원만: {report['summary']['members_only']}명") 
        print(f"- 후원자만: {report['summary']['supporters_only']}명")
        print(f"- 조합원+후원자: {report['summary']['both']}명")
        print(f"- 중복 병합: {report['summary']['duplicates_merged']}건")
        
        print(f"\n💰 납입 통계:")
        print(f"- 총 예상 납입액: {report['statistics']['total_amount']:,.0f}원")
        print(f"- 평균 납입액: {report['statistics']['avg_amount']:,.0f}원")
        print(f"- 최대 납입액: {report['statistics']['max_amount']:,.0f}원")
        print(f"- 최소 납입액: {report['statistics']['min_amount']:,.0f}원")
        
        print(f"\n📁 생성된 파일:")
        output_files = ['통합_명단.csv', '통합_명단_report.txt']
        for file in output_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"✅ {file} ({size:,} bytes)")
            else:
                print(f"❌ {file} (없음)")
        
        return result
        
    except Exception as e:
        print(f"❌ 고급 통합 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_with_simple():
    """간단한 통합과 고급 통합 비교"""
    print(f"\n🔍 통합 결과 비교")
    print("=" * 30)
    
    # 간단한 통합 결과 확인
    if os.path.exists('간단_통합_명단.csv'):
        simple_df = pd.read_csv('간단_통합_명단.csv', encoding='utf-8-sig')
        print(f"간단한 통합: {len(simple_df)}명")
    else:
        print("간단한 통합 결과 없음")
        return
    
    # 고급 통합 결과 확인
    if os.path.exists('통합_명단.csv'):
        advanced_df = pd.read_csv('통합_명단.csv', encoding='utf-8-sig')
        print(f"고급 통합: {len(advanced_df)}명")
        
        # 차이점 분석
        print(f"\n📊 비교 분석:")
        print(f"- 인원 차이: {len(simple_df) - len(advanced_df)}명")
        
        if 'duplicate_flag' in advanced_df.columns:
            duplicates = advanced_df[advanced_df['duplicate_flag'] == True]
            print(f"- 중복 처리: {len(duplicates)}건")
        
        # 데이터 품질 비교
        simple_phone_complete = len(simple_df[simple_df['전화번호'].notna()])
        advanced_phone_complete = len(advanced_df[advanced_df['phone'].notna()]) if 'phone' in advanced_df.columns else 0
        
        print(f"- 전화번호 완성도: 간단({simple_phone_complete}) vs 고급({advanced_phone_complete})")
        
    else:
        print("고급 통합 결과 없음")

def test_data_quality():
    """데이터 품질 검증"""
    print(f"\n🔍 데이터 품질 검증")
    print("=" * 30)
    
    if not os.path.exists('통합_명단.csv'):
        print("통합 명단 파일이 없습니다.")
        return
    
    df = pd.read_csv('통합_명단.csv', encoding='utf-8-sig')
    
    print(f"📋 전체 정보:")
    print(f"- 총 레코드: {len(df)}개")
    print(f"- 총 컬럼: {len(df.columns)}개")
    print(f"- 컬럼 목록: {list(df.columns)}")
    
    # 필수 필드 확인
    essential_fields = ['name', 'phone', 'email', 'amount']
    print(f"\n✅ 필수 필드 완성도:")
    
    for field in essential_fields:
        if field in df.columns:
            complete_count = len(df[df[field].notna()])
            complete_rate = (complete_count / len(df)) * 100
            print(f"- {field}: {complete_count}/{len(df)} ({complete_rate:.1f}%)")
        else:
            print(f"- {field}: 컬럼 없음")
    
    # 전화번호 형식 확인
    if 'phone' in df.columns:
        phone_pattern_count = len(df[df['phone'].str.match(r'010-\d{4}-\d{4}', na=False)])
        print(f"\n📞 전화번호 형식:")
        print(f"- 표준 형식(010-XXXX-XXXX): {phone_pattern_count}개")
    
    # 금액 통계
    if 'amount' in df.columns:
        valid_amounts = df[df['amount'] > 0]
        print(f"\n💰 금액 통계:")
        print(f"- 유효 금액: {len(valid_amounts)}개")
        if len(valid_amounts) > 0:
            print(f"- 평균: {valid_amounts['amount'].mean():,.0f}원")
            print(f"- 최대: {valid_amounts['amount'].max():,.0f}원")
            print(f"- 최소: {valid_amounts['amount'].min():,.0f}원")

def test_file_access():
    """파일 접근 테스트"""
    print(f"\n📁 파일 접근 테스트")
    print("=" * 30)
    
    # 필요한 입력 파일 확인
    input_files = [
        'utt/조합원_후원자명부.csv',
        'utt/후원자_명부.csv',
        'utt/NH_거래내역.csv',
        'utt/SH_거래내역.csv', 
        'utt/Donus_거래내역.csv'
    ]
    
    print("📥 입력 파일 상태:")
    for file in input_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
            
            # 파일 내용 미리보기
            try:
                df = pd.read_csv(file, encoding='utf-8-sig', nrows=2)
                print(f"   컬럼: {list(df.columns)}")
            except Exception as e:
                print(f"   읽기 오류: {e}")
        else:
            print(f"❌ {file} (없음)")
    
    # 출력 파일 확인
    output_files = [
        '간단_통합_명단.csv',
        '간단_통합_거래내역.csv',
        '통합_명단.csv',
        '통합_명단_report.txt'
    ]
    
    print(f"\n📤 출력 파일 상태:")
    for file in output_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} (없음)")

def run_advanced_test():
    """고급 테스트 전체 실행"""
    print("🎯 고급 통합 시스템 테스트")
    print("=" * 50)
    print(f"📁 현재 디렉토리: {os.getcwd()}")
    print(f"🕐 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 파일 접근 테스트
    test_file_access()
    
    # 2. 고급 명부 통합 테스트
    result = test_member_integration()
    
    # 3. 간단한 통합과 비교
    if result is not None:
        compare_with_simple()
    
    # 4. 데이터 품질 검증
    test_data_quality()
    
    print(f"\n🎉 고급 테스트 완료!")
    print(f"\n📋 다음 단계:")
    print("1. bank_transaction_integrator.py 추가")
    print("2. 거래내역 통합 테스트")
    print("3. 명부와 거래내역 매칭 테스트")

if __name__ == "__main__":
    try:
        run_advanced_test()
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()