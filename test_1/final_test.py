#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import os
from difflib import SequenceMatcher
from datetime import datetime

class FinalBankMatcher:
    """완전 새로운 은행 거래내역 매칭 시스템"""
    
    def __init__(self):
        print("🏦 새로운 은행 거래내역 매칭 시스템 초기화")
        self.master_members = None
        self.all_transactions = []
        self.matching_results = []
    
    def load_master_members(self, members_file, supporters_file):
        """마스터 회원 리스트 로드"""
        print("\n👥 마스터 회원 리스트 생성 중...")
        
        # 조합원 데이터
        members_df = pd.read_csv(members_file, encoding='utf-8-sig')
        print(f"  조합원: {len(members_df)}명")
        
        # 후원자 데이터
        supporters_df = pd.read_csv(supporters_file, encoding='utf-8-sig')
        print(f"  후원자: {len(supporters_df)}명")
        
        # 조합원 표준화
        members_std = []
        for _, row in members_df.iterrows():
            members_std.append({
                '이름': str(row['이름']).strip(),
                '연락처': str(row.get('연락처', '')).strip(),
                '이메일': str(row.get('이메일', '')).strip(),
                '회원구분': '조합원',
                '기업명': str(row.get('기업/단체명', '')).strip(),
                '예상금액': '',
                '가입일': str(row.get('가입일', '')).strip(),
                '원본소스': 'members'
            })
        
        # 후원자 표준화
        supporters_std = []
        for _, row in supporters_df.iterrows():
            supporters_std.append({
                '이름': str(row['이름']).strip(),
                '연락처': str(row.get('연락처', '')).strip(),
                '이메일': str(row.get('이메일', '')).strip(),
                '회원구분': '후원자',
                '기업명': '',
                '예상금액': str(row.get('월납입약정금액', '')).strip(),
                '가입일': str(row.get('최초약정일', '')).strip(),
                '원본소스': 'supporters'
            })
        
        # 통합 및 중복 제거
        all_members = members_std + supporters_std
        unique_members = []
        seen = set()
        
        for member in all_members:
            key = (member['이름'], member['연락처'])
            if key not in seen:
                seen.add(key)
                unique_members.append(member)
            else:
                # 중복인 경우 겸용으로 처리
                for existing in unique_members:
                    if (existing['이름'], existing['연락처']) == key:
                        if existing['회원구분'] != member['회원구분']:
                            existing['회원구분'] = '겸용'
                        break
        
        # 마스터 ID 부여
        for i, member in enumerate(unique_members):
            member['마스터ID'] = f'M{i+1:04d}'
        
        self.master_members = pd.DataFrame(unique_members)
        
        # 기업명 통계
        company_members = self.master_members[
            (self.master_members['기업명'] != '') & 
            (self.master_members['기업명'] != 'nan')
        ]
        
        print(f"  ✅ 마스터 리스트 생성 완료: {len(self.master_members)}명")
        print(f"     조합원 전용: {len(self.master_members[self.master_members['회원구분']=='조합원'])}명")
        print(f"     후원자 전용: {len(self.master_members[self.master_members['회원구분']=='후원자'])}명")
        print(f"     겸용: {len(self.master_members[self.master_members['회원구분']=='겸용'])}명")
        print(f"     기업명 보유: {len(company_members)}명")
        
        return self.master_members
    
    def load_bank_transactions(self):
        """은행 거래내역 로드"""
        print("\n🏦 은행 거래내역 로드 중...")
        
        bank_configs = [
            {
                'name': 'SH은행',
                'file': 'utt/SH_거래내역.xlsx',
                'header_row': 7,
                'columns': {'date': '거래일시', 'depositor': '내용', 'amount': '입금'}
            },
            {
                'name': 'NH농협',
                'file': 'utt/NH_거래내역.xls',
                'header_row': 9,
                'columns': {'date': '거래일자', 'depositor': '거래내용', 'amount': '입금금액(원)'}
            },
            {
                'name': 'DONUS',
                'file': 'utt/Donus_거래내역.xlsx',
                'header_row': 0,
                'columns': {'date': '납입일', 'depositor': '이름', 'amount': '납입액'}
            }
        ]
        
        for config in bank_configs:
            self._process_bank_file(config)
        
        print(f"  ✅ 총 {len(self.all_transactions)}건의 거래 로드 완료")
        return self.all_transactions
    
    def _process_bank_file(self, config):
        """개별 은행 파일 처리"""
        print(f"  처리 중: {config['name']}")
        
        try:
            # 파일 읽기
            if config['file'].endswith('.xls'):
                df = pd.read_excel(config['file'], header=config['header_row'], engine='xlrd')
            else:
                df = pd.read_excel(config['file'], header=config['header_row'])
            
            print(f"    📊 원본: {len(df)}건")
            
            # 거래 추출
            for _, row in df.iterrows():
                try:
                    # 날짜 처리
                    date_val = row[config['columns']['date']]
                    if pd.isna(date_val):
                        continue
                    
                    if isinstance(date_val, str):
                        date_str = date_val.split()[0]  # 시간 부분 제거
                    else:
                        date_str = str(date_val).split()[0]
                    
                    # 입금자명 처리
                    depositor_raw = str(row.get(config['columns']['depositor'], '')).strip()
                    if config['name'] == 'SH은행':
                        depositor = self._extract_name_from_sh(depositor_raw)
                    elif config['name'] == 'NH농협':
                        depositor = ''  # NH농협은 시스템 거래가 대부분
                    else:
                        depositor = depositor_raw
                    
                    # 금액 처리
                    amount_val = row.get(config['columns']['amount'], 0)
                    if pd.isna(amount_val) or amount_val <= 0:
                        continue
                    
                    amount = float(amount_val)
                    
                    # 거래 저장
                    self.all_transactions.append({
                        '거래일': date_str,
                        '입금자명': depositor,
                        '금액': amount,
                        '은행': config['name'],
                        '원본내용': depositor_raw
                    })
                    
                except Exception as e:
                    continue
            
            valid_count = len([t for t in self.all_transactions if t['은행'] == config['name']])
            print(f"    ✅ 유효 거래: {valid_count}건")
            
        except Exception as e:
            print(f"    ❌ 처리 실패: {e}")
    
    def _extract_name_from_sh(self, content):
        """SH은행 거래내용에서 이름 추출"""
        if not content or content == 'nan':
            return ''
        
        # 시스템 거래 제외
        if any(keyword in content for keyword in ['내부이체', '결산이자', '이자지급']):
            return ''
        
        # 한글 이름 추출 (2-4글자)
        match = re.search(r'[가-힣]{2,4}', content)
        if match:
            return match.group()
        
        # 기업명인 경우 그대로 반환
        return content
    
    def normalize_company_name(self, name):
        """기업명 정규화"""
        if not name or name == 'nan':
            return ''
        
        # 기본 정리
        normalized = str(name).strip().lower()
        
        # 법인 형태 통일
        normalized = re.sub(r'\(주\)', '주식회사', normalized)
        normalized = re.sub(r'\(유\)', '유한회사', normalized)
        
        # 영문 변환
        replacements = {
            'pal': '피에이엘',
            'nawa': '나와'
        }
        
        for eng, kor in replacements.items():
            normalized = normalized.replace(eng, kor)
        
        # 공백 제거
        normalized = re.sub(r'\s+', '', normalized)
        
        return normalized
    
    def calculate_company_similarity(self, name1, name2):
        """기업명 유사도 계산"""
        if not name1 or not name2:
            return 0
        
        # 정규화
        norm1 = self.normalize_company_name(name1)
        norm2 = self.normalize_company_name(name2)
        
        if norm1 == norm2:
            return 0.95
        
        # 키워드 추출 (3글자 이상)
        keywords1 = [norm1[i:i+j] for i in range(len(norm1)) for j in range(3, 6) if i+j <= len(norm1)]
        keywords2 = [norm2[i:i+j] for i in range(len(norm2)) for j in range(3, 6) if i+j <= len(norm2)]
        
        # 공통 키워드
        common = set(keywords1) & set(keywords2)
        if common and len(max(common, key=len)) >= 3:
            return 0.85
        
        # 부분 매칭
        if norm1 in norm2 or norm2 in norm1:
            return 0.8
        
        return 0
    
    def calculate_name_similarity(self, name1, name2):
        """이름 유사도 계산"""
        if not name1 or not name2:
            return 0
        
        if name1 == name2:
            return 1.0
        
        # 괄호 제거
        clean1 = name1.split('(')[0].strip()
        clean2 = name2.split('(')[0].strip()
        
        if clean1 == clean2:
            return 0.95
        
        # 문자열 유사도
        return SequenceMatcher(None, clean1, clean2).ratio()
    
    def match_transactions(self):
        """거래내역 매칭"""
        print("\n🔍 거래내역 매칭 중...")
        
        for transaction in self.all_transactions:
            depositor = transaction['입금자명']
            amount = transaction['금액']
            bank = transaction['은행']
            
            best_match = None
            best_score = 0
            match_type = ''
            
            # NH농협 금액 매칭 (입금자명이 없는 경우)
            if bank == 'NH농협' and not depositor:
                for _, member in self.master_members.iterrows():
                    expected = str(member['예상금액']).strip()
                    if expected and expected != 'nan' and str(int(amount)) == expected:
                        if best_score < 0.7:
                            best_match = member
                            best_score = 0.7
                            match_type = f'NH금액매칭({int(amount)}원)'
                            break
            
            # 이름 및 기업명 매칭
            else:
                for _, member in self.master_members.iterrows():
                    member_name = member['이름']
                    member_company = member['기업명']
                    
                    # 1. 이름 정확 매칭
                    if depositor == member_name:
                        best_match = member
                        best_score = 1.0
                        match_type = '이름정확매칭'
                        break
                    
                    # 2. 기업명 매칭
                    if member_company and member_company != 'nan':
                        company_sim = self.calculate_company_similarity(depositor, member_company)
                        if company_sim > best_score:
                            best_match = member
                            best_score = company_sim
                            if company_sim >= 0.95:
                                match_type = f'기업명정규화매칭({member_company}→{member_name})'
                            elif company_sim >= 0.85:
                                match_type = f'기업명키워드매칭({member_company}→{member_name})'
                            else:
                                match_type = f'기업명부분매칭({member_company}→{member_name})'
                    
                    # 3. 이름 유사 매칭
                    name_sim = self.calculate_name_similarity(depositor, member_name)
                    if name_sim >= 0.7 and name_sim > best_score:
                        best_match = member
                        best_score = name_sim
                        match_type = f'이름유사매칭({name_sim:.2f})'
            
            # 결과 저장
            result = {
                '거래일': transaction['거래일'],
                '입금자명': depositor,
                '금액': int(amount),
                '은행': bank,
                '매칭상태': '매칭성공' if best_match is not None else '미매칭',
                '매칭방식': match_type,
                '매칭점수': best_score,
                '매칭회원ID': best_match['마스터ID'] if best_match is not None else '',
                '매칭회원명': best_match['이름'] if best_match is not None else '',
                '회원구분': best_match['회원구분'] if best_match is not None else '',
                '매칭기업명': best_match['기업명'] if best_match is not None else '',
                '원본내용': transaction['원본내용']
            }
            
            self.matching_results.append(result)
        
        # 통계 출력
        total = len(self.matching_results)
        matched = len([r for r in self.matching_results if r['매칭상태'] == '매칭성공'])
        
        print(f"  ✅ 매칭 완료:")
        print(f"    총 거래: {total}건")
        print(f"    매칭 성공: {matched}건 ({matched/total*100:.1f}%)")
        print(f"    미매칭: {total-matched}건 ({(total-matched)/total*100:.1f}%)")
        
        return self.matching_results
    
    def analyze_results(self):
        """결과 분석"""
        print("\n📊 결과 분석:")
        
        # 매칭 방식별 통계
        matched_results = [r for r in self.matching_results if r['매칭상태'] == '매칭성공']
        if matched_results:
            methods = {}
            for result in matched_results:
                method = result['매칭방식'].split('(')[0]
                methods[method] = methods.get(method, 0) + 1
            
            print("  매칭 방식별 현황:")
            for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
                print(f"    {method}: {count}건")
        
        # 신규 인원 식별
        unmatched_results = [r for r in self.matching_results if r['매칭상태'] == '미매칭']
        new_people = []
        system_transactions = []
        
        for result in unmatched_results:
            depositor = result['입금자명']
            bank = result['은행']
            original = result['원본내용']
            
            # 시스템 거래 분류
            if bank == 'NH농협' or not depositor:
                if any(keyword in original for keyword in 
                       ['CMS공동', 'PC', '폰', '타행이체', '예금이자', '스마트당행']):
                    system_transactions.append(result)
                    continue
            
            if bank == 'SH은행':
                if any(keyword in original for keyword in 
                       ['내부이체', '결산이자', '이자지급']):
                    system_transactions.append(result)
                    continue
            
            # 신규 인원 후보
            if depositor and re.match(r'^[가-힣]{2,4}', depositor):
                new_people.append(result)
        
        # 신규 인원 알림
        if new_people:
            unique_names = {}
            for person in new_people:
                name = person['입금자명'].split('(')[0].strip()
                if name not in unique_names:
                    unique_names[name] = []
                unique_names[name].append(person)
            
            print(f"\n🆕 신규 인원 후보: {len(unique_names)}명")
            for name, transactions in unique_names.items():
                total_amount = sum(t['금액'] for t in transactions)
                banks = list(set(t['은행'] for t in transactions))
                print(f"    • {name}: {len(transactions)}건, {total_amount:,}원 ({', '.join(banks)})")
        
        # 시스템 거래 통계
        if system_transactions:
            print(f"\n🔧 시스템 거래: {len(system_transactions)}건 (매칭 대상 아님)")
            by_bank = {}
            for trans in system_transactions:
                bank = trans['은행']
                by_bank[bank] = by_bank.get(bank, 0) + 1
            
            for bank, count in by_bank.items():
                print(f"    {bank}: {count}건")
    
    def save_results(self, output_dir='final_matching_results'):
        """결과 저장"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 전체 결과
        results_df = pd.DataFrame(self.matching_results)
        results_df.to_csv(f'{output_dir}/all_results.csv', index=False, encoding='utf-8-sig')
        
        # 매칭 성공
        matched_df = results_df[results_df['매칭상태'] == '매칭성공']
        matched_df.to_csv(f'{output_dir}/matched_results.csv', index=False, encoding='utf-8-sig')
        
        # 실제 미매칭 (시스템 거래 제외)
        unmatched_df = results_df[results_df['매칭상태'] == '미매칭']
        real_unmatched = []
        
        for _, row in unmatched_df.iterrows():
            original = row['원본내용']
            bank = row['은행']
            
            # 시스템 거래 제외
            if bank == 'NH농협':
                if any(keyword in original for keyword in 
                       ['CMS공동', 'PC', '폰', '타행이체', '예금이자', '스마트당행']):
                    continue
            
            if bank == 'SH은행':
                if any(keyword in original for keyword in 
                       ['내부이체', '결산이자', '이자지급']):
                    continue
            
            real_unmatched.append(row)
        
        if real_unmatched:
            real_unmatched_df = pd.DataFrame(real_unmatched)
            real_unmatched_df.to_csv(f'{output_dir}/unmatched_real.csv', index=False, encoding='utf-8-sig')
        
        # 마스터 회원 리스트
        self.master_members.to_csv(f'{output_dir}/master_members.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n💾 결과 저장 완료: {output_dir}/")

def main():
    """메인 함수"""
    matcher = FinalBankMatcher()
    
    # 1. 마스터 회원 리스트 로드
    matcher.load_master_members('extracted_members_with_company.csv', 'extracted_supporters.csv')
    
    # 2. 은행 거래내역 로드
    matcher.load_bank_transactions()
    
    # 3. 매칭 수행
    matcher.match_transactions()
    
    # 4. 결과 분석
    matcher.analyze_results()
    
    # 5. 결과 저장
    matcher.save_results()

if __name__ == "__main__":
    main()