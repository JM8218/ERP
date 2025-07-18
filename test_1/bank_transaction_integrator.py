import pandas as pd
import re
from datetime import datetime

class SimpleBankIntegrator:
    def __init__(self):
        print("💳 은행 거래내역 통합기 초기화")
    
    def process_nh_file(self, file_path):
        """농협 파일 처리"""
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        valid_transactions = []
        for _, row in df.iterrows():
            depositor = str(row.get('입금자', ''))
            amount = str(row.get('입금금액', ''))
            date = str(row.get('거래일자', ''))
            
            # 노이즈 제거
            if any(noise in depositor for noise in ['총', '내부이체', '수수료', 'nan']):
                continue
            
            if len(depositor.strip()) >= 2 and amount and date:
                try:
                    amount_val = float(re.sub(r'[^\d.]', '', amount))
                    if amount_val > 0:
                        valid_transactions.append({
                            'bank': 'NH_농협',
                            'date': date,
                            'amount': amount_val,
                            'depositor': depositor.strip(),
                            'memo': str(row.get('거래내용', ''))
                        })
                except:
                    continue
        
        return valid_transactions
    
    def process_sh_file(self, file_path):
        """신협 파일 처리"""
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        valid_transactions = []
        for _, row in df.iterrows():
            depositor = str(row.get('입금자명', ''))
            amount = str(row.get('금액', ''))
            date = str(row.get('날짜', ''))
            
            # 노이즈 제거
            if any(noise in depositor for noise in ['총', '관리', '수수료', 'nan']):
                continue
            
            if len(depositor.strip()) >= 2 and amount and date:
                try:
                    amount_val = float(re.sub(r'[^\d.]', '', amount))
                    if amount_val > 0:
                        valid_transactions.append({
                            'bank': 'SH_신협',
                            'date': date,
                            'amount': amount_val,
                            'depositor': depositor.strip(),
                            'memo': str(row.get('메모', ''))
                        })
                except:
                    continue
        
        return valid_transactions
    
    def process_donus_file(self, file_path):
        """도너스 파일 처리"""
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        valid_transactions = []
        for _, row in df.iterrows():
            depositor = str(row.get('Donor Name', ''))
            amount = str(row.get('Amount', ''))
            date = str(row.get('Date', ''))
            
            # 노이즈 제거
            if any(noise in depositor for noise in ['Total', 'Fee', 'nan']):
                continue
            
            if len(depositor.strip()) >= 2 and amount and date:
                try:
                    amount_val = float(re.sub(r'[^\d.]', '', amount))
                    if amount_val > 0:
                        valid_transactions.append({
                            'bank': 'Donus_도너스',
                            'date': date,
                            'amount': amount_val,
                            'depositor': depositor.strip(),
                            'memo': str(row.get('Note', ''))
                        })
                except:
                    continue
        
        return valid_transactions
    
    def integrate_all_banks(self):
        """모든 은행 거래내역 통합"""
        print("🏦 은행별 거래내역 통합 시작...")
        
        all_transactions = []
        
        # NH 처리
        try:
            nh_transactions = self.process_nh_file('utt/NH_거래내역.csv')
            all_transactions.extend(nh_transactions)
            print(f"✅ NH 농협: {len(nh_transactions)}건")
        except Exception as e:
            print(f"❌ NH 농협 처리 실패: {e}")
        
        # SH 처리
        try:
            sh_transactions = self.process_sh_file('utt/SH_거래내역.csv')
            all_transactions.extend(sh_transactions)
            print(f"✅ SH 신협: {len(sh_transactions)}건")
        except Exception as e:
            print(f"❌ SH 신협 처리 실패: {e}")
        
        # Donus 처리
        try:
            donus_transactions = self.process_donus_file('utt/Donus_거래내역.csv')
            all_transactions.extend(donus_transactions)
            print(f"✅ Donus 도너스: {len(donus_transactions)}건")
        except Exception as e:
            print(f"❌ Donus 도너스 처리 실패: {e}")
        
        if all_transactions:
            df = pd.DataFrame(all_transactions)
            df.to_csv('통합_거래내역.csv', index=False, encoding='utf-8-sig')
            print(f"💾 통합 거래내역 저장: {len(df)}건")
            return df
        else:
            print("❌ 처리된 거래내역이 없습니다")
            return None

if __name__ == "__main__":
    integrator = SimpleBankIntegrator()
    result = integrator.integrate_all_banks()
    
    if result is not None:
        print(f"\n📊 통합 결과:")
        print(f"- 총 거래: {len(result)}건")
        print(f"- 은행별 분포:")
        bank_counts = result['bank'].value_counts()
        for bank, count in bank_counts.items():
            print(f"  {bank}: {count}건")
        
        print(f"\n💰 금액 통계:")
        print(f"- 총 입금액: {result['amount'].sum():,.0f}원")
        print(f"- 평균 입금액: {result['amount'].mean():,.0f}원")
        
        print(f"\n👥 입금자 현황:")
        unique_depositors = result['depositor'].unique()
        print(f"- 고유 입금자: {len(unique_depositors)}명")
        print(f"- 입금자 목록: {list(unique_depositors)}")