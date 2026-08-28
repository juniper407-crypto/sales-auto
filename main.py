import os
import re
import requests
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ['WEBHOOK_URL']

EASYPOS_ID = os.environ.get('EASYPOS_ID')
EASYPOS_PW = os.environ.get('EASYPOS_PW')

BEAVER_ID = os.environ.get('BEAVER_ID')
BEAVER_PW = os.environ.get('BEAVER_PW')

CPLAT_BRAND_CODE = os.environ.get('CPLAT_BRAND_CODE')
CPLAT_ID = os.environ.get('CPLAT_ID')
CPLAT_PW = os.environ.get('CPLAT_PW')

def parse_number(text):
    if not text:
        return 0
    clean_text = re.sub(r'[^0-9]', '', str(text))
    return int(clean_text) if clean_text else 0

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page.set_default_timeout(60000)

        results = []

        # -------------------------------------------------------------
        # 1. 이지포스
        # -------------------------------------------------------------
        try:
            print("[1/3] 이지포스 접속 및 로그인 시도 중...")
            page.goto("https://smart.easypos.net/index.jsp", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            page.fill("input[name='txtUSER_ID']", EASYPOS_ID)
            page.fill("input[name='txtPWD']", EASYPOS_PW)
            page.click("a#btnLogin")
            page.wait_for_timeout(5000)

            page.goto("https://smart.easypos.net/servlet/EasyPos.SvtSls01001", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            rows = page.locator("table tbody tr").all()
            for row in rows:
                cols = row.locator("td").all()
                if len(cols) >= 5:
                    store_name = cols[2].inner_text().strip()
                    if store_name and store_name not in ["합계", "매장명"]:
                        net_sales = parse_number(cols[4].inner_text())
                        results.append(["이지포스", store_name, net_sales, 0, 0, 0, 0, 0])

            print(f"이지포스 완료: {len(results)}개 매장 수집")

        except Exception as e:
            print(f"이지포스 수집 에러: {e}")

        # -------------------------------------------------------------
        # 2. 비버 매장연구소
        # -------------------------------------------------------------
        try:
            print("[2/3] 비버 접속 및 로그인 시도 중...")
            page.goto("https://biz.beaverworksinc.com/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            page.fill("input[type='text']", BEAVER_ID)
            page.fill("input[type='password']", BEAVER_PW)
            page.click("button:has-text('로그인')")
            page.wait_for_timeout(5000)

            page.goto("https://biz.beaverworksinc.com/sales/store-sales", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            if page.locator("button:has-text('오늘')").is_visible():
                page.click("button:has-text('오늘')")
                page.wait_for_timeout(1000)

            rows = page.locator("table tbody tr").all()
            for row in rows:
                cols = row.locator("td").all()
                if len(cols) >= 4:
                    s_name = cols[2].inner_text().strip()
                    if s_name != "합계":
                        r_sales = parse_number(cols[6].inner_text()) if len(cols) > 6 else parse_number(cols[3].inner_text())
                        results.append(["비버", s_name, r_sales, 0, 0, 0, 0, 0])

            print("비버 수집 완료")

        except Exception as e:
            print(f"비버 수집 에러: {e}")

        # -------------------------------------------------------------
        # 3. CPlat 브랜드 인사이트
        # -------------------------------------------------------------
        try:
            print("[3/3] CPlat 접속 및 로그인 시도 중...")
            page.goto("https://brand-insight.cplat.io/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            inputs = page.locator("input")
            inputs.nth(0).fill(CPLAT_BRAND_CODE)
            inputs.nth(1).fill(CPLAT_ID)
            inputs.nth(2).fill(CPLAT_PW)

            page.click("button:has-text('로그인')")
            page.wait_for_timeout(5000)

            page.goto("https://brand-insight.cplat.io/sales/daily", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            sales_text = page.locator("div:has-text('결제금액') + div").first.inner_text()
            results.append(["CPlat", "CPlat 매장", parse_number(sales_text), 0, 0, 0, 0, 0])
            print("CPlat 수집 완료")

        except Exception as e:
            print(f"CPlat 수집 에러: {e}")

        browser.close()

        # 구글 시트 전송
        if results:
            print(f"총 {len(results)}건의 데이터를 구글 시트로 전송 중...")
            res = requests.post(WEBHOOK_URL, json=results)
            print(f"전송 결과: {res.text}")
        else:
            print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    run()
