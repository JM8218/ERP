#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class PaymentMatchingSystem:
    """조합원/후원자 납입 매칭 시스템"""
    
    def __init__(self):
        print("💰 납입 매칭 시스템 초기화")
        self.member_data = None
        self.supporter_data = None
        self.transaction_data = None
        
    def load_extracted_data(self):
        """추출된 데이터 로드"""
        print("\n📥 추출된 데이터 로드 중...")
        
        # 조합원 데이터 로드
        if os.path.exists('extracted_members.csv'):
            self.member_data = pd.read_csv('extracted_members.csv', encoding='utf-8-sig')
            print(f"  ✅ 조합원 데이터: {len(self.member_data)}명")
        else:
            print("  ❌ extracted_members.csv 파일 없음")
        
        # 후원자 데이터 로드
        if os.path.exists('extracted_supporters.csv'):
            self.supporter_data = pd.read_csv('extracted_supporters.csv', encoding='utf-8-sig')
            print(f"  ✅ 후원자 데이터: {len(self.supporter_data)}명")
        else:
            print("  ❌ extracted_supporters.csv 파일 없음")
        
        # 거래내역 데이터 로드
        if os.path.exists('통합_거래내역.csv'):
            self.transaction_data = pd.read_csv('통합_거래내역.csv', encoding='utf-8-sig')
            print(f"  ✅ 거래내역 데이터: {len(self.transaction_data)}건")
        else:
            print("  ❌ 통합_거래내역.csv 파일 없음")
        
        return all([
            self.member_data is not None,
            self.supporter_data is not None, 
            self.transaction_data is not None
        ])
    
    def normalize_name_for_matching(self, name):
        """매칭을 위한 이름 정규화"""
        if pd.isna(name) or not name:
            return ''
        
        name = str(name).strip()
        # 공백 제거
        name = re.sub(r'\s+', '', name)
        return name
    
    def find_transactions_by_name(self, name):
        """이름으로 거래내역 찾기"""
        if self.transaction_data is None or not name:
            return pd.DataFrame()
        
        normalized_name = self.normalize_name_for_matching(name)
        
        # 정확 매칭
        exact_matches = self.transaction_data[
            self.transaction_data['depositor'].apply(self.normalize_name_for_matching) == normalized_name
        ]
        
        if not exact_matches.empty:
            return exact_matches
        
        # 부분 매칭 (이름이 포함된 경우)
        partial_matches = self.transaction_data[
            self.transaction_data['depositor'].apply(self.normalize_name_for_matching).str.contains(normalized_name, na=False)
        ]
        
        return partial_matches
    
    def calculate_monthly_payments(self, transactions, start_date=None):
        """월별 납입액 계산"""
        if transactions.empty:
            return {}
        
        # 날짜 변환
        transactions = transactions.copy()
        if 'date' in transactions.columns:
            transactions['date'] = pd.to_datetime(transactions['date'], errors='coerce')
            transactions = transactions.dropna(subset=['date'])
        
        # 월별 그룹화
        transactions['year_month'] = transactions['date'].dt.strftime('%Y-%m')
        monthly_payments = transactions.groupby('year_month')['amount'].sum().to_dict()
        
        return monthly_payments
    
    def process_member_payments(self):
        """조합원 납입 현황 처리"""
        print("\n🏢 조합원 납입 현황 처리 중...")
        
        if self.member_data is None:
            print("  ❌ 조합원 데이터가 없습니다")
            return None
        
        # 새 컬럼 추가
        result_data = self.member_data.copy()
        result_data['월별입금액'] = ''
        result_data['총입금액'] = 0
        result_data['최근납입일'] = ''
        result_data['납입현황'] = '미확인'
        result_data['매칭거래수'] = 0
        
        print(f"  총 {len(result_data)}명 처리 중...")
        
        for idx, member in result_data.iterrows():
            name = member['이름']
            
            # 해당 조합원의 거래내역 찾기
            member_transactions = self.find_transactions_by_name(name)
            
            if not member_transactions.empty:
                # 월별 납입액 계산
                monthly_payments = self.calculate_monthly_payments(member_transactions)
                
                # 총 입금액
                total_amount = member_transactions['amount'].sum()
                
                # 최근 납입일
                latest_date = member_transactions['date'].max()
                if pd.notna(latest_date):
                    latest_date = latest_date.strftime('%Y-%m-%d')
                else:
                    latest_date = ''
                
                # 월별 입금액을 문자열로 변환
                monthly_str = ', '.join([f"{month}: {amount:,.0f}원" for month, amount in monthly_payments.items()])
                
                # 납입 현황 판단
                if total_amount > 0:
                    status = f"납입 완료 ({len(member_transactions)}건)"
                else:
                    status = "입금 없음"
                
                # 데이터 업데이트
                result_data.loc[idx, '월별입금액'] = monthly_str
                result_data.loc[idx, '총입금액'] = total_amount
                result_data.loc[idx, '최근납입일'] = latest_date
                result_data.loc[idx, '납입현황'] = status
                result_data.loc[idx, '매칭거래수'] = len(member_transactions)
                
                print(f"    ✅ {name}: {len(member_transactions)}건, 총 {total_amount:,.0f}원")
            else:
                result_data.loc[idx, '납입현황'] = '거래내역 없음'
                print(f"    ❌ {name}: 거래내역 없음")
        
        return result_data
    
    def process_supporter_payments(self):
        """후원자 납입 현황 처리"""
        print("\n💝 후원자 납입 현황 처리 중...")
        
        if self.supporter_data is None:
            print("  ❌ 후원자 데이터가 없습니다")
            return None
        
        # 새 컬럼 추가
        result_data = self.supporter_data.copy()
        result_data['실제월납입액'] = ''
        result_data['약정대비차액'] = ''
        result_data['총입금액'] = 0
        result_data['최근납입일'] = ''
        result_data['납입현황'] = '미확인'
        result_data['매칭거래수'] = 0
        
        print(f"  총 {len(result_data)}명 처리 중...")
        
        for idx, supporter in result_data.iterrows():
            name = supporter['이름']
            supporter_type = supporter['유형']
            agreed_amount = supporter['월납입약정금액']
            
            # 약정 금액을 숫자로 변환
            agreed_amount_num = 0
            if pd.notna(agreed_amount) and str(agreed_amount).strip():
                try:
                    agreed_amount_num = float(str(agreed_amount).replace(',', '').replace('원', ''))
                except:
                    agreed_amount_num = 0
            
            # 해당 후원자의 거래내역 찾기
            supporter_transactions = self.find_transactions_by_name(name)
            
            if not supporter_transactions.empty:
                # 월별 납입액 계산
                monthly_payments = self.calculate_monthly_payments(supporter_transactions)
                
                # 총 입금액
                total_amount = supporter_transactions['amount'].sum()
                
                # 최근 납입일
                latest_date = supporter_transactions['date'].max()
                if pd.notna(latest_date):
                    latest_date = latest_date.strftime('%Y-%m-%d')
                else:
                    latest_date = ''
                
                # 정기후원자의 경우 약정 금액과 비교
                if supporter_type == '정기후원' and agreed_amount_num > 0:
                    # 월평균 입금액 계산
                    if monthly_payments:
                        avg_monthly = sum(monthly_payments.values()) / len(monthly_payments)
                        difference = avg_monthly - agreed_amount_num
                        
                        monthly_str = f"평균 {avg_monthly:,.0f}원/월 (약정: {agreed_amount_num:,.0f}원)"
                        difference_str = f"{difference:+,.0f}원"
                        
                        if abs(difference) <= agreed_amount_num * 0.1:  # 10% 오차 범위
                            status = "약정액 정상 납입"
                        elif difference > 0:
                            status = "약정액 초과 납입"
                        else:
                            status = "약정액 미달 납입"
                    else:
                        monthly_str = "입금 없음"
                        difference_str = f"{-agreed_amount_num:,.0f}원"
                        status = "납입 없음"
                else:
                    # 일시후원 또는 약정금액 없는 경우
                    monthly_str = ', '.join([f"{month}: {amount:,.0f}원" for month, amount in monthly_payments.items()])
                    difference_str = f"총 {total_amount:,.0f}원"
                    status = f"후원 완료 ({len(supporter_transactions)}건)"
                
                # 데이터 업데이트
                result_data.loc[idx, '실제월납입액'] = monthly_str
                result_data.loc[idx, '약정대비차액'] = difference_str
                result_data.loc[idx, '총입금액'] = total_amount
                result_data.loc[idx, '최근납입일'] = latest_date
                result_data.loc[idx, '납입현황'] = status
                result_data.loc[idx, '매칭거래수'] = len(supporter_transactions)
                
                print(f"    ✅ {name} ({supporter_type}): {len(supporter_transactions)}건, {status}")
            else:
                result_data.loc[idx, '납입현황'] = '거래내역 없음'
                if agreed_amount_num > 0:
                    result_data.loc[idx, '약정대비차액'] = f"{-agreed_amount_num:,.0f}원"
                print(f"    ❌ {name}: 거래내역 없음")
        
        return result_data
    
    def generate_matching_report(self, member_result, supporter_result):
        """매칭 결과 리포트 생성"""
        print("\n📊 매칭 결과 리포트 생성 중...")
        
        report_lines = []
        report_lines.append("=== 납입 매칭 결과 리포트 ===\n")
        report_lines.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 조합원 리포트
        if member_result is not None:
            report_lines.append("🏢 조합원 납입 현황\n")
            report_lines.append(f"총 조합원: {len(member_result)}명\n")
            
            # 납입 현황별 통계
            status_counts = member_result['납입현황'].value_counts()
            for status, count in status_counts.items():
                report_lines.append(f"  {status}: {count}명\n")
            
            # 총 납입액 통계
            total_payments = member_result['총입금액'].sum()
            avg_payments = member_result[member_result['총입금액'] > 0]['총입금액'].mean()
            
            report_lines.append(f"총 납입액: {total_payments:,.0f}원\n")
            report_lines.append(f"평균 납입액: {avg_payments:,.0f}원\n")
            
            # 미납자 목록
            unpaid_members = member_result[member_result['총입금액'] == 0]
            if not unpaid_members.empty:
                report_lines.append(f"\n미납 조합원 ({len(unpaid_members)}명):\n")
                for _, member in unpaid_members.iterrows():
                    report_lines.append(f"  - {member['이름']} ({member['연락처']})\n")
        
        # 후원자 리포트
        if supporter_result is not None:
            report_lines.append(f"\n💝 후원자 납입 현황\n")
            report_lines.append(f"총 후원자: {len(supporter_result)}명\n")
            
            # 유형별 통계
            type_counts = supporter_result['유형'].value_counts()
            for supporter_type, count in type_counts.items():
                report_lines.append(f"  {supporter_type}: {count}명\n")
            
            # 납입 현황별 통계
            status_counts = supporter_result['납입현황'].value_counts()
            for status, count in status_counts.items():
                report_lines.append(f"  {status}: {count}명\n")
            
            # 총 후원액 통계
            total_support = supporter_result['총입금액'].sum()
            report_lines.append(f"총 후원액: {total_support:,.0f}원\n")
            
            # 정기후원자 약정 준수율
            regular_supporters = supporter_result[supporter_result['유형'] == '정기후원']
            if not regular_supporters.empty:
                normal_payments = len(regular_supporters[regular_supporters['납입현황'].str.contains('정상', na=False)])
                compliance_rate = normal_payments / len(regular_supporters) * 100
                report_lines.append(f"정기후원자 약정 준수율: {compliance_rate:.1f}% ({normal_payments}/{len(regular_supporters)}명)\n")
        
        # 파일로 저장
        report_content = ''.join(report_lines)
        with open('payment_matching_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("📄 리포트 저장: payment_matching_report.txt")
        return report_content
    
    def save_results(self, member_result, supporter_result):
        """결과 저장"""
        print("\n💾 매칭 결과 저장 중...")
        
        if member_result is not None:
            member_result.to_csv('조합원_납입현황.csv', index=False, encoding='utf-8-sig')
            print("  ✅ 조합원_납입현황.csv 저장")
        
        if supporter_result is not None:
            supporter_result.to_csv('후원자_납입현황.csv', index=False, encoding='utf-8-sig')
            print("  ✅ 후원자_납입현황.csv 저장")
    
    def run_matching_process(self):
        """전체 매칭 프로세스 실행"""
        print("🚀 납입 매칭 시스템 시작")
        print("=" * 50)
        
        # 데이터 로드
        if not self.load_extracted_data():
            print("❌ 필요한 데이터 파일이 없습니다")
            return
        
        # 조합원 납입 처리
        member_result = self.process_member_payments()
        
        # 후원자 납입 처리
        supporter_result = self.process_supporter_payments()
        
        # 결과 저장
        self.save_results(member_result, supporter_result)
        
        # 리포트 생성
        self.generate_matching_report(member_result, supporter_result)
        
        print(f"\n🎉 납입 매칭 완료!")
        print(f"생성된 파일:")
        print(f"  - 조합원_납입현황.csv")
        print(f"  - 후원자_납입현황.csv") 
        print(f"  - payment_matching_report.txt")
        
        # 요약 출력
        if member_result is not None:
            paid_members = len(member_result[member_result['총입금액'] > 0])
            print(f"\n📊 조합원 요약: {paid_members}/{len(member_result)}명 납입")
        
        if supporter_result is not None:
            paid_supporters = len(supporter_result[supporter_result['총입금액'] > 0])
            print(f"📊 후원자 요약: {paid_supporters}/{len(supporter_result)}명 후원")

def main():
    """메인 실행 함수"""
    matcher = PaymentMatchingSystem()
    matcher.run_matching_process()

if __name__ == "__main__":
    main()