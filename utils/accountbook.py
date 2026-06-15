import time

import pandas as pd
import os
import datetime
import re



payments_dict = {
    # "temptemptemp":"현금",
    # "temptemptemp":"은행",
    r"^(\d{8})\d{12}_카드이용내역부가세용.xls$":"국민카드",
    r"^개인사업자용\+카드\+이용내역_(\d{8}).xlsx$":"삼성카드",
    # "":"카드"
}

category_dict = {
    "주유소": "🚖 교통/차량$자차",
    "주차": "🚖 교통/차량$자차",
    "단지 관리단": "🚖 교통/차량$자차",
    "도로": "🚖 교통/차량$자차",
    "칼텍스": "🚖 교통/차량$자차",
    "오일뱅크": "🚖 교통/차량$자차",
    "SK에너지": "🚖 교통/차량$자차",
    "티머니": "🚖 교통/차량$대중교통",
    "택시": "🚖 교통/차량$택시",
    "주식회사더스윙": "🚖 교통/차량$대중교통",
    "학원": "📙 교육$학원비",
    "의원": "🧘🏼 건강$병원",
    "병원": "🧘🏼 건강$병원",
    "치과": "🧘🏼 건강$병원",
    "이비인후과": "🧘🏼 건강$병원",
    "내과": "🧘🏼 건강$병원",
    "외과": "🧘🏼 건강$병원",
    "부인과": "🧘🏼 건강$병원",
    "보험": "🧘🏼 건강$병원",
    "약국": "🧘🏼 건강$약국",
    "아크로짐": "🧘🏼 건강$운동",
    "카페": "🍜 식비$간식",
    "커피": "🍜 식비$간식",
    "메머드익스": "🍜 식비$간식",
    "스타벅스": "🍜 식비$간식",
    "투썸": "🍜 식비$간식",
    "페이타랩": "🍜 식비$간식",
    "베이커리": "🍜 식비$간식",
    "배달": "🍜 식비$외식",
    "쿠팡이츠": "🍜 식비$외식",
    "배민": "🍜 식비$외식",
    "지에스": "🛒 마트/편의점",
    "이마트24": "🛒 마트/편의점",
    "씨유": "🛒 마트/편의점",
    "세븐일레븐": "🛒 마트/편의점",
    "아성다이소": "🪑 생활용품",
    "쿠팡": "🪑 생활용품",
    "이마트": "🪑 생활용품",
    "홈플러스": "🪑 생활용품",
    "이케아": "🪑 생활용품",
    "텔링크": "구독료",
    "피클플러스": "구독료",
    "올리브영": "🧥 패션/미용$헤어/뷰티",
    "에이블리": "🧥 패션/미용$의류",
    "무신사": "🧥 패션/미용$의류"

}

df = pd.DataFrame({
    "기간":[],
    "자산":[],
    "분류":[],
    "소분류":[],
    "내용":[],
    "KRW":[],
    "수입/지출":[],
    "추가입력":[],
    "금액":[],
    "화폐":[],
    "자산":[]
})
pd.set_option('display.max_columns', None)

print(os.listdir("C:\\Users\\sygwak.BRANVISOFT\\Downloads"))
#2025-09-01 ~ 09-30 (1).xlsx
file_list = os.listdir("C:\\Users\\sygwak.BRANVISOFT\\Downloads")

for file_name in file_list:
    recent_file = datetime.datetime.min
    target = ""
    payment = ""

    for k, v in payments_dict.items():
        n = re.search(k, file_name)
        if n:
            try:
                start_date = datetime.datetime.strptime(n.group(1), "%Y%m%d")
                if recent_file < start_date:
                    recent_file = start_date
                    target = "C:\\Users\\sygwak.BRANVISOFT\\Downloads\\" + file_name
                payment = v
            except ValueError:
                continue

    if target == "":
        continue
    print("===================\n⚙️대상 파일⚙️ 👉 ",target, "\n===================")
    if payment == "삼성카드":
        pf = pd.read_excel(target)
    elif payment == "국민카드":
        pf = pd.read_excel(target, header=13, usecols="B:O")
        first_empty_idx = pf.index[pf.isna().all(axis=1)].min()
        pf.dropna(axis=1, how="all", inplace=True)

        if pd.notna(first_empty_idx):
            pf = pf.loc[:first_empty_idx-1]  # 빈 행 직전까지만 남김
    print(pf)
    for idx, row in pf.iterrows():
        category = next((v for k, v in category_dict.items() if k in row["가맹점명"]), "미분류").split('$')
        big_c = category[0]
        small_c = category[1] if len(category) > 1 else pd.NA
        if payment == "삼성카드":
            df.loc[len(df)] = {
                "기간": datetime.datetime.strptime(str(row["접수일자"]), "%Y%M%d") ,
                "자산":payment,
                "분류":big_c,
                "소분류":small_c,
                "내용":row["가맹점명"],
                "KRW":int(row["매출금액(원)"]),
                "수입/지출":'지출',
                "추가입력":pd.NA,
                "금액":int(row["매출금액(원)"]),
                "화폐":'KRW',
                "자산":int(row["매출금액(원)"])
            }
        elif payment == "국민카드":
            df.loc[len(df)] = {
                    "기간":row["이용일"],
                    "자산":payment,
                    "분류":big_c,
                    "소분류":small_c,
                    "내용":row["가맹점명"],
                    "KRW":int(row["매출금액"]),
                    "수입/지출":'지출',
                    "추가입력":pd.NA,
                    "금액":int(row["매출금액"]),
                    "화폐":'KRW',
                    "자산":int(row["매출금액"])
            }

############################
# 쿠팡 // 네이버페이 / 카카오페이 충전결제내역 조회
############################
coupang = "C:\\Users\\sygwak.BRANVISOFT\\Downloads"

for file_name in file_list:
    if(re.match(r"^coupang-orders-\d{13}.csv",file_name)):
        coupang += "\\" + file_name
        break

coupang_df = pd.read_csv(coupang)
coupang_payment_df = df[df["내용"] == "쿠팡"]

# 매칭 키 만들기
coupang_payment_df = coupang_payment_df.copy()
coupang_payment_df["key"] = coupang_payment_df["기간"].astype(int).astype(str) + "_" + coupang_payment_df["금액"].astype(str)
coupang_df["key"] = coupang_df["주문일"].astype(int).astype(str) + "_" + coupang_df["상품가격(원)"].astype(str)

# merge
merged = coupang_payment_df.merge(coupang_df[["key", "상품명"]], on="key", how="left")

# 상품명으로 내용 교체
df.loc[merged.index, "내용"] = merged["상품명"]

print(df)
############################
# 송금 관련은 알아서 수기입력
############################
## 기간 자산 분류 소분류 내용 KRW 수입/지출 추가입력 금액 화폐 자산
## 삼성카드는?
## 개인사업자용+카드+이용내역_YYYYMMdd.xlsx
## 매출상품명	카드종류명	할부개월수	매출일자	접수일자	매출금액(원)	부가세(원)	카드번호	이용자	가맹점명	가맹점번호	사업자등록번호	승인번호
## 접수일자 -> 기간
## 이름 필터링으로 자산 필드 추가
## 국민카드는? ( B14 부터 컬럼명 시작됨)
## YYYYMMdd{12자리수}카드이용내역부가세용.xls
## 순번	이용일		카드번호	취소여부	매출구분	매출금액			가맹점명			사업자번호	과세유형
##
##
## + 우리카드 + 현금 이용내역 + 쿠팡 구매 내역 + 네이버 페이 결제 내역 + 카카오페이 결제내역을 합치면 내 한달 사용량을 알 수 있음.