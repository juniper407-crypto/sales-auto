import os
import requests
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ['WEBHOOK_URL']

# 환경 변수에서 계정 정보 불러오기
EASYPOS_ID = os.environ.get('EASYPOS_ID')
EASYPOS_PW = os.environ.get('EASYPOS_PW')

BEAVER_ID = os.environ.get('BEAVER_ID')
BEAVER_PW = os.environ.get('BEAVER_PW')

CPLAT_BRAND_CODE = os.environ.get('CPLAT_BRAND_CODE')
CPLAT_ID = os.environ.get('CPLAT_ID')
CPLAT_PW = os.environ.get('CPLAT_PW')

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        results = []

        # 1. 이지포스 (https://smart.easypos.net/index.jsp)
        try:
            print("이지포스 접속 및 로그인 시도 중...")
            page.goto("https://smart.easypos.net/index.jsp")
            page.wait_for_load_state("networkidle")

            page.fill("input[name='txtUSER_ID']", EASYPOS_ID)
            page.fill("input[name='txtPWD']", EASYPOS_PW)
            page.click("a#btnLogin")
            page.wait_for_load_state("networkidle")
            print("이지포스 로그인 완료")

            # TODO: 매출 수집 로직 추가 위치
            results.append(["이지포스", "명동점", 30900, 285900, 1420000, 1380000, 5800000, 5600000])
            results.append(["이지포스", "판교점", 14000, 150000, 890000, 850000, 3600000, 3400000])

        except Exception as e:
            print(f"이지포스 수집 에러: {e}")

        # 2. 비버 매장연구소 (https://biz.beaverworksinc.com/login)
        try:
            print("비버 접속 및 로그인 시도 중...")
            page.goto("https://biz.beaverworksinc.com/login")
            page.wait_for_load_state("networkidle")

            page.fill("input[type='text']", BEAVER_ID)
            page.fill("input[type='password']", BEAVER_PW)
            page.click("button:has-text('로그인')")
            page.wait_for_load_state("networkidle")
            print("비버 로그인 완료")

            # TODO: 매출 수집 로직 추가 위치
            results.append(["비버", "대치점", 138500, 420000, 2100000, 1950000, 8200000, 7800000])

        except Exception as e:
            print(f"비버 수집 에러: {e}")

        # 3. CPlat 브랜드 인사이트 (https://brand-insight.cplat.io/login)
        try:
            print("CPlat 접속 및 로그인 시도 중...")
            page.goto("https://brand-insight.cplat.io/login")
            page.wait_for_load_state("networkidle")

            # 브랜드코드, 아이디, 비밀번호 3가지 입력
            inputs = page.locator("input")
            inputs.nth(0).fill(CPLAT_BRAND_CODE)
            inputs.nth(1).fill(CPLAT_ID)
            inputs.nth(2).fill(CPLAT_PW)

            page.click("button:has-text('로그인')")
            page.wait_for_load_state("networkidle")
            print("CPlat 로그인 완료")

            # TODO: 매출 수집 로직 추가 위치
            results.append(["CPlat", "신논현역점", 100000, 90000, 500000, 480000, 2100000, 2000000])

        except Exception as e:
            print(f"CPlat 수집 에러: {e}")

        browser.close()

        # 구글 시트(Apps Script) 전송
        print("구글 시트로 데이터 전송 중...")
        res = requests.post(WEBHOOK_URL, json=results)
        print(f"전송 결과: {res.text}")

if __name__ == "__main__":
    run()
