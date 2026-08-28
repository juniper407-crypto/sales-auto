import os
import requests
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ['WEBHOOK_URL']

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        results = []

        # 1. 이지포스 수집 (테스트 데이터)
        try:
            results.append(["이지포스", "명동점", 30900, 285900, 1420000, 1380000, 5800000, 5600000])
            results.append(["이지포스", "판교점", 14000, 150000, 890000, 850000, 3600000, 3400000])
        except Exception as e:
            print(f"이지포스 오류: {e}")

        # 2. 비버 매장연구소 수집 (테스트 데이터)
        try:
            results.append(["비버", "대치점", 138500, 420000, 2100000, 1950000, 8200000, 7800000])
        except Exception as e:
            print(f"비버 오류: {e}")

        # 3. CPlat 브랜드인사이트 수집 (테스트 데이터)
        try:
            results.append(["CPlat", "OO점", 31000, 1622800, 9500000, 9100000, 38000000, 36500000])
        except Exception as e:
            print(f"CPlat 오류: {e}")

        browser.close()

        # 구글 시트로 전송
        print("구글 시트로 데이터 전송 중...")
        res = requests.post(WEBHOOK_URL, json=results)
        print(f"전송 결과: {res.text}")

if __name__ == "__main__":
    run()
