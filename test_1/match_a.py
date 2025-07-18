
import pandas as pd

# 명부와 거래내역 매칭 분석
members_df = pd.read_csv('통합_명단.csv', encoding='utf-8-sig')
transactions_df = pd.read_csv('통합_거래내역.csv', encoding='utf-8-sig')

print('🔗 명부와 거래내역 매칭 분석')
print('=' * 40)

print(f'📋 명부: {len(members_df)}명')
print(f'💳 거래내역: {len(transactions_df)}건')

# 이름 기준 매칭
member_names = set(members_df['name'])
depositor_names = set(transactions_df['depositor'])
matched_names = member_names.intersection(depositor_names)

print(f'\n✅ 매칭 결과:')
print(f'- 매칭된 이름: {len(matched_names)}개')
print(f'- 매칭률: {len(matched_names)/len(member_names)*100:.1f}%')
print(f'- 매칭된 명단: {sorted(list(matched_names))}')

# 각 회원별 납입 현황
print(f'\n💰 개별 납입 현황:')
for member in members_df.itertuples():
    member_name = member.name
    expected_amount = member.amount
    member_transactions = transactions_df[transactions_df['depositor'] == member_name]
    
    if not member_transactions.empty:
        total_paid = member_transactions['amount'].sum()
        count = len(member_transactions)