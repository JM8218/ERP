#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

class MemberDatabase:
    """회원 데이터베이스 관리 클래스"""
    
    def __init__(self, db_file='members_database.csv'):
        self.db_file = db_file
        self.members_df = self._load_or_create_db()
        
    def _load_or_create_db(self):
        """기존 DB 로드 또는 새로 생성"""
        if os.path.exists(self.db_file):
            try:
                df = pd.read_csv(self.db_file, encoding='utf-8-sig')
                print(f"✅ 기존 회원 DB 로드: {len(df)}명")
                return df
            except Exception as e:
                print(f"❌ DB 로드 실패: {e}")
        
        # 새 DB 생성
        columns = [
            'member_id',      # 고유 ID
            'name',           # 이름
            'phone',          # 전화번호
            'email',          # 이메일
            'member_type',    # 회원 타입
            'payment_amount', # 납입 예정 금액
            'address',        # 주소
            'join_date',      # 가입일
            'status',         # 상태 (active, inactive)
            'notes',          # 메모
            'created_at',     # 생성일
            'updated_at'      # 수정일
        ]
        
        df = pd.DataFrame(columns=columns)
        print("🆕 새로운 회원 DB 생성")
        return df
    
    def normalize_phone(self, phone):
        """전화번호 정규화"""
        if pd.isna(phone) or not phone:
            return None
        
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
    
    def generate_member_id(self, name, phone):
        """고유 회원 ID 생성"""
        # 이름 + 전화번호 뒷자리로 ID 생성
        phone_suffix = re.sub(r'\D', '', str(phone))[-4:] if phone else '0000'
        member_id = f"{name}_{phone_suffix}"
        
        # 중복 체크 및 번호 추가
        base_id = member_id
        counter = 1
        while self.member_exists(member_id):
            member_id = f"{base_id}_{counter}"
            counter += 1
        
        return member_id
    
    def member_exists(self, member_id=None, name=None, phone=None):
        """회원 존재 여부 확인"""
        if member_id:
            return member_id in self.members_df['member_id'].values
        
        if name and phone:
            phone = self.normalize_phone(phone)
            existing = self.members_df[
                (self.members_df['name'] == name) & 
                (self.members_df['phone'] == phone)
            ]
            return len(existing) > 0
        
        return False
    
    def add_member(self, name, phone, email=None, member_type='supporter', 
                   payment_amount=0, address=None, notes=None):
        """새 회원 추가"""
        
        # 입력 검증
        if not name or len(name.strip()) < 2:
            return False, "이름은 2글자 이상이어야 합니다"
        
        name = name.strip()
        phone = self.normalize_phone(phone)
        
        if not phone:
            return False, "올바른 전화번호를 입력해주세요"
        
        # 중복 체크
        if self.member_exists(name=name, phone=phone):
            return False, f"{name}({phone}) 회원이 이미 존재합니다"
        
        # 회원 ID 생성
        member_id = self.generate_member_id(name, phone)
        
        # 새 회원 데이터
        new_member = {
            'member_id': member_id,
            'name': name,
            'phone': phone,
            'email': email or '',
            'member_type': member_type,
            'payment_amount': float(payment_amount) if payment_amount else 0.0,
            'address': address or '',
            'join_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'active',
            'notes': notes or '',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # DataFrame에 추가
        self.members_df = pd.concat([
            self.members_df, 
            pd.DataFrame([new_member])
        ], ignore_index=True)
        
        # DB 저장
        self.save_db()
        
        return True, f"✅ {name} 회원 추가 완료 (ID: {member_id})"
    
    def update_member(self, member_id, **kwargs):
        """회원 정보 수정"""
        if not self.member_exists(member_id):
            return False, f"회원 ID {member_id}를 찾을 수 없습니다"
        
        # 수정 가능한 필드들
        updatable_fields = [
            'name', 'phone', 'email', 'member_type', 
            'payment_amount', 'address', 'status', 'notes'
        ]
        
        idx = self.members_df[self.members_df['member_id'] == member_id].index[0]
        
        updated_fields = []
        for field, value in kwargs.items():
            if field in updatable_fields:
                if field == 'phone':
                    value = self.normalize_phone(value)
                elif field == 'payment_amount':
                    value = float(value) if value else 0.0
                
                self.members_df.loc[idx, field] = value
                updated_fields.append(field)
        
        if updated_fields:
            self.members_df.loc[idx, 'updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_db()
            return True, f"✅ {member_id} 회원 정보 수정 완료: {', '.join(updated_fields)}"
        else:
            return False, "수정할 내용이 없습니다"
    
    def delete_member(self, member_id):
        """회원 삭제"""
        if not self.member_exists(member_id):
            return False, f"회원 ID {member_id}를 찾을 수 없습니다"
        
        member_info = self.get_member(member_id)
        self.members_df = self.members_df[self.members_df['member_id'] != member_id]
        self.save_db()
        
        return True, f"✅ {member_info['name']} 회원 삭제 완료"
    
    def get_member(self, member_id):
        """회원 정보 조회"""
        member = self.members_df[self.members_df['member_id'] == member_id]
        if len(member) > 0:
            return member.iloc[0].to_dict()
        return None
    
    def search_members(self, name=None, phone=None, member_type=None, status='active'):
        """회원 검색"""
        result = self.members_df.copy()
        
        if status:
            result = result[result['status'] == status]
        
        if name:
            result = result[result['name'].str.contains(name, na=False)]
        
        if phone:
            phone = self.normalize_phone(phone)
            result = result[result['phone'].str.contains(phone, na=False)]
        
        if member_type:
            result = result[result['member_type'] == member_type]
        
        return result
    
    def import_from_csv(self, csv_file, member_type='supporter'):
        """CSV 파일에서 회원 일괄 추가"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            print(f"📥 CSV 파일 로드: {len(df)}행")
            
            # 컬럼명 매핑
            column_mapping = {
                '이름': 'name', '성명': 'name', '회원명': 'name', '후원자명': 'name',
                '전화번호': 'phone', '연락처': 'phone', '휴대폰': 'phone',
                '이메일': 'email', '이메일주소': 'email', 'e-mail': 'email',
                '조합비': 'amount', '후원금': 'amount', '납입금액': 'amount', '후원금액': 'amount',
                '주소': 'address', '거주지': 'address',
                '회원타입': 'member_type', '타입': 'member_type',
                '메모': 'notes', '비고': 'notes'
            }
            
            # 컬럼명 변경
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    name = row.get('name', '')
                    phone = row.get('phone', '')
                    email = row.get('email', '')
                    amount = row.get('amount', 0)
                    address = row.get('address', '')
                    notes = row.get('notes', '')
                    
                    # member_type 결정
                    if 'member_type' in row and row['member_type']:
                        row_member_type = str(row['member_type']).strip()
                        if '조합원' in row_member_type:
                            actual_member_type = 'member'
                        elif '후원자' in row_member_type:
                            actual_member_type = 'supporter'
                        else:
                            actual_member_type = member_type
                    else:
                        actual_member_type = member_type
                    
                    success, message = self.add_member(
                        name=name,
                        phone=phone, 
                        email=email,
                        member_type=actual_member_type,
                        payment_amount=amount,
                        address=address,
                        notes=notes
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"행 {idx+1}: {message}")
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"행 {idx+1}: {str(e)}")
            
            result_message = f"✅ 일괄 추가 완료: 성공 {success_count}건, 실패 {error_count}건"
            
            if errors:
                result_message += f"\n❌ 오류 내역:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    result_message += f"\n... 외 {len(errors)-5}건"
            
            return True, result_message
            
        except Exception as e:
            return False, f"CSV 파일 처리 실패: {str(e)}"
    
    def export_to_csv(self, output_file='exported_members.csv', member_type=None, status='active'):
        """회원 목록을 CSV로 내보내기"""
        export_df = self.members_df.copy()
        
        if status:
            export_df = export_df[export_df['status'] == status]
        
        if member_type:
            export_df = export_df[export_df['member_type'] == member_type]
        
        export_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        return True, f"✅ {len(export_df)}명 회원 정보를 {output_file}로 내보내기 완료"
    
    def get_statistics(self):
        """회원 통계"""
        total = len(self.members_df)
        active = len(self.members_df[self.members_df['status'] == 'active'])
        
        type_stats = self.members_df['member_type'].value_counts().to_dict()
        
        amount_stats = {
            'total_expected': self.members_df['payment_amount'].sum(),
            'avg_amount': self.members_df['payment_amount'].mean(),
            'max_amount': self.members_df['payment_amount'].max(),
            'min_amount': self.members_df['payment_amount'].min()
        }
        
        return {
            '총회원수': total,
            '활성회원수': active,
            '회원타입별': type_stats,
            '납입통계': amount_stats
        }
    
    def save_db(self):
        """데이터베이스 저장"""
        self.members_df.to_csv(self.db_file, index=False, encoding='utf-8-sig')
    
    def backup_db(self):
        """데이터베이스 백업"""
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.db_file}"
        self.members_df.to_csv(backup_file, index=False, encoding='utf-8-sig')
        return backup_file

class MemberManagementCLI:
    """회원 관리 CLI 인터페이스"""
    
    def __init__(self):
        self.db = MemberDatabase()
        
    def show_menu(self):
        """메인 메뉴 출력"""
        print("\n" + "="*50)
        print("🏢 조합원/후원자 관리 시스템")
        print("="*50)
        print("1. 회원 추가")
        print("2. 회원 검색/조회") 
        print("3. 회원 정보 수정")
        print("4. 회원 삭제")
        print("5. CSV 일괄 추가")
        print("6. CSV 내보내기")
        print("7. 회원 통계")
        print("8. 백업 생성")
        print("9. 종료")
        print("="*50)
    
    def add_member_interactive(self):
        """대화형 회원 추가"""
        print("\n📝 새 회원 추가")
        
        name = input("이름: ").strip()
        phone = input("전화번호: ").strip()
        email = input("이메일 (선택): ").strip()
        
        print("회원 타입:")
        print("1. 후원자 (supporter)")
        print("2. 조합원 (member)")
        type_choice = input("선택 (1-2): ").strip()
        
        member_type = 'member' if type_choice == '2' else 'supporter'
        
        try:
            payment_amount = float(input("납입 예정 금액: ") or 0)
        except:
            payment_amount = 0
            
        address = input("주소 (선택): ").strip()
        notes = input("메모 (선택): ").strip()
        
        success, message = self.db.add_member(
            name=name,
            phone=phone,
            email=email or None,
            member_type=member_type,
            payment_amount=payment_amount,
            address=address or None,
            notes=notes or None
        )
        
        print(message)
    
    def search_members_interactive(self):
        """대화형 회원 검색"""
        print("\n🔍 회원 검색")
        
        name = input("이름 검색 (부분 검색 가능, 엔터=전체): ").strip() or None
        phone = input("전화번호 검색 (부분 검색 가능, 엔터=전체): ").strip() or None
        
        print("회원 타입:")
        print("1. 전체")
        print("2. 후원자만")
        print("3. 조합원만")
        type_choice = input("선택 (1-3): ").strip()
        
        member_type = None
        if type_choice == '2':
            member_type = 'supporter'
        elif type_choice == '3':
            member_type = 'member'
        
        results = self.db.search_members(
            name=name,
            phone=phone,
            member_type=member_type
        )
        
        if len(results) == 0:
            print("❌ 검색 결과가 없습니다")
        else:
            print(f"\n✅ 검색 결과: {len(results)}명")
            print("-" * 80)
            for _, member in results.iterrows():
                print(f"ID: {member['member_id']}")
                print(f"이름: {member['name']} | 전화: {member['phone']}")
                print(f"타입: {member['member_type']} | 금액: {member['payment_amount']:,}원")
                print(f"가입일: {member['join_date']} | 상태: {member['status']}")
                if member['notes']:
                    print(f"메모: {member['notes']}")
                print("-" * 80)
    
    def run(self):
        """CLI 실행"""
        while True:
            self.show_menu()
            choice = input("\n선택하세요 (1-9): ").strip()
            
            if choice == '1':
                self.add_member_interactive()
            elif choice == '2':
                self.search_members_interactive()
            elif choice == '3':
                member_id = input("수정할 회원 ID: ").strip()
                # 간단한 수정 인터페이스
                print("수정할 정보를 입력하세요 (엔터=변경하지 않음)")
                # ... 수정 로직 구현
            elif choice == '4':
                member_id = input("삭제할 회원 ID: ").strip()
                confirm = input(f"정말 {member_id}를 삭제하시겠습니까? (y/N): ")
                if confirm.lower() == 'y':
                    success, message = self.db.delete_member(member_id)
                    print(message)
            elif choice == '5':
                csv_file = input("CSV 파일 경로: ").strip()
                print("기본 회원 타입:")
                print("1. 후원자")
                print("2. 조합원")
                type_choice = input("선택 (1-2): ").strip()
                member_type = 'member' if type_choice == '2' else 'supporter'
                
                success, message = self.db.import_from_csv(csv_file, member_type)
                print(message)
            elif choice == '6':
                output_file = input("출력 파일명 (기본: exported_members.csv): ").strip()
                if not output_file:
                    output_file = 'exported_members.csv'
                success, message = self.db.export_to_csv(output_file)
                print(message)
            elif choice == '7':
                stats = self.db.get_statistics()
                print("\n📊 회원 통계")
                print(f"총 회원수: {stats['총회원수']}명")
                print(f"활성 회원수: {stats['활성회원수']}명")
                print("회원 타입별:")
                for member_type, count in stats['회원타입별'].items():
                    print(f"  {member_type}: {count}명")
                print(f"총 예상 납입액: {stats['납입통계']['total_expected']:,.0f}원")
                print(f"평균 납입액: {stats['납입통계']['avg_amount']:,.0f}원")
            elif choice == '8':
                backup_file = self.db.backup_db()
                print(f"✅ 백업 생성: {backup_file}")
            elif choice == '9':
                print("👋 프로그램을 종료합니다")
                break
            else:
                print("❌ 잘못된 선택입니다")

if __name__ == "__main__":
    # CLI 실행
    cli = MemberManagementCLI()
    cli.run()