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

        results = []

        # -------------------------------------------------------------
        # 1. 이지포스 (전체 매장 한 번에 수집)
        # -------------------------------------------------------------
        try:
            print("[1/3] 이지포스 수집 시작...")
            page.goto("https://smart.easypos.net/index.jsp")
            page.wait_for_load_state("networkidle")

            page.fill("input[name='txtUSER_ID']", EASYPOS_ID)
            page.fill("input[name='txtPWD']", EASYPOS_PW)
            page.click("a#btnLogin")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            page.goto("https://smart.easypos.net/servlet/EasyPos.SvtSls01001")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

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
            print(f"이지포스 수집 중 오류: {e}")

        # -------------------------------------------------------------
        # 2. 비버 매장연구소 (매장 드롭다운 자동 순회)
        # -------------------------------------------------------------
        try:
            print("[2/3] 비버 매장연구소 수집 시작...")
            page.goto("https://biz.beaverworksinc.com/login")
            page.wait_for_load_state("networkidle")

            page.fill("input[type='text']", BEAVER_ID)
            page.fill("input[type='password']", BEAVER_PW)
            page.click("button:has-text('로그인')")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            page.goto("https://biz.beaverworksinc.com/sales/store-sales")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            # 오늘 날짜 필터 선택
            if page.locator("button:has-text('오늘')").is_visible():
                page.click("button:has-text('오늘')")
                page.wait_for_timeout(1000)

            # 매장 선택 드롭다운 클릭하여 전체 매장 목록 파악
            store_select = page.locator("div:has-text('매장 :')").last
            if store_select.is_visible():
                store_select.click()
                page.wait_for_timeout(1000)
                
                # 드롭다운 옵션(매장들) 가져오기
                options = page.locator("ul[role='listbox'] li, div[role='option']").all()
                store_count = len(options)

                for i in range(store_count):
                    # 드롭다운 다시 열기 (첫 번째가 아니면)
                    if i > 0:
                        store_select.click()
                        page.wait_for_timeout(500)
                    
                    current_option = page.locator("ul[role='listbox'] li, div[role='option']").nth(i)
                    store_name = current_option.inner_text().strip()
                    current_option.click()
                    
                    # 조회하기 버튼 클릭
                    page.click("button:has-text('조회하기')")
                    page.wait_for_timeout(1500)

                    # 실매출 카드 또는 하단 테이블에서 매출 가져오기
                    sales_element = page.locator("div:has-text('실매출') + div").first
                    sales_val = parse_number(sales_element.inner_text()) if sales_element.is_visible() else 0
                    
                    results.append(["비버", store_name, sales_val, 0, 0, 0, 0, 0])
                    print(f"비버 수집: {store_name} -> {sales_val}원")
            else:
                # 단일 매장 계정인 경우 테이블에서 바로 수집
                rows = page.locator("table tbody tr").all()
                for row in rows:
                    cols = row.locator("td").all()
                    if len(cols) >= 4:
                        s_name = cols[2].inner_text().strip()
                        if s_name != "합계":
                            r_sales = parse_number(cols[6].inner_text()) if len(cols) > 6 else parse_number(cols[3].inner_text())
                            results.append(["비버", s_name, r_sales, 0, 0, 0, 0, 0])

        except Exception as e:
            print(f"비버 수집 중 오류: {e}")

        # -------------------------------------------------------------
        # 3. CPlat 브랜드 인사이트 (우측 상단 매장 셀렉터 순회)
        # -------------------------------------------------------------
        try:
            print("[3/3] CPlat 수집 시작...")
            page.goto("https://brand-insight.cplat.io/login")
            page.wait_for_load_state("networkidle")

            inputs = page.locator("input")
            inputs.nth(0).fill(CPLAT_BRAND_CODE)
            inputs.nth(1).fill(CPLAT_ID)
            inputs.nth(2).fill(CPLAT_PW)

            page.click("button:has-text('로그인')")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            page.goto("https://brand-insight.cplat.io/sales/daily")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            # 우측 상단 매장 선택 드롭다운 클릭
            store_dropdown = page.locator("header button, div[role='combobox']").filter(has_text="오크베리").first
            
            if store_dropdown.is_visible():
                store_dropdown.click()
                page.wait_for_timeout(1000)

                # 팝업된 매장 목록 추출
                store_items = page.locator("div[role='menu'] button, ul li").all()
                store_names = [item.inner_text().strip() for item in store_items if item.inner_text().strip()]
                
                # 메뉴 닫기
                page.keyboard.press("Escape")

                for s_name in store_names:
                    # 매장 선택
                    store_dropdown.click()
                    page.wait_for_timeout(500)
                    page.locator(f"button:has-text('{s_name}'), li:has-text('{s_name}')").first.click()
                    page.wait_for_timeout(1500)

                    # 결제금액 카드 수집
                    sales_text = page.locator("div:has-text('결제금액') + div, span:has-text('결제금액') + span").first.inner_text()
                    sales_val = parse_number(sales_text)
                    
                    results.append(["CPlat", s_name, sales_val, 0, 0, 0, 0, 0])
                    print(f"CPlat 수집: {s_name} -> {sales_val}원")
            else:
                # 매장 1개인 경우 바로 수집
                sales_text = page.locator("div:has-text('결제금액') + div").first.inner_text()
                results.append(["CPlat", "CPlat 매장", parse_number(sales_text), 0, 0, 0, 0, 0])

        except Exception as e:
            print(f"CPlat 수집 중 오류: {e}")

        browser.close()

        # 구글 시트 전송
        if results:
            print(f"\n총 {len(results)}개 매장 데이터 구글 시트로 전송 중...")
            res = requests.post(WEBHOOK_URL, json=results)
            print(f"전송 결과: {res.text}")

if __name__ == "__main__":
    run()
