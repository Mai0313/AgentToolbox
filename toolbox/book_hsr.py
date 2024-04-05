import os
from typing import Optional
import datetime

import autorootcwd
from rich.console import Console
from playwright.sync_api import TimeoutError, sync_playwright
from toolbox.src.hsr_core import HSRUtils
from toolbox.models.payment_models import PaymentModel
from playwright.sync_api._generated import Page

console = Console()


class HSR(PaymentModel):
    personal_id: str
    phone_number: str
    email_address: str
    ticket_type: str
    ticket_numbers: str
    location_from: str
    location_to: str
    departure_date: str
    departure_time: str

    def fill_payment(self, page: Page) -> None:
        page.wait_for_load_state("networkidle", timeout=1)
        # 選擇付款方式
        page.click('input[name="payCon:paymentMethod"][value="radio42"]')
        # 點擊立即付款按鈕
        page.click('input[name="payCon:SubmitButton"][value="立即付款"]')
        # 等待跳轉
        page.wait_for_load_state("networkidle")
        # 輸入信用卡資訊
        page.fill('input[name="txtPAN1"]', self.card_number[0:4])
        page.fill('input[name="txtPAN2"]', self.card_number[4:8])
        page.fill('input[name="txtPAN3"]', self.card_number[8:12])
        page.fill('input[name="txtPAN4"]', self.card_number[12:16])
        # 選擇信用卡有效期限
        page.select_option('select[name="ddlExpMonth"]', self.card_expire_date[0:2])
        page.select_option('select[name="ddlExpYear"]', self.card_expire_date[2:4])
        # 點擊立即付款按鈕
        page.click("a#btnPressToPay", timeout=1)
        # 等待付款完成或其他後續操作 (目前不知道畫面長啥樣 以後再看)
        page.wait_for_load_state("networkidle")

    def screenshot(cls, page: Page) -> None:
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        log_path = f"./logs/log_{now}"
        os.makedirs(log_path, exist_ok=True)
        existed_log = len(os.listdir(log_path)) + 1
        screenshot_path = f"{log_path}/screenshot_step{existed_log}.png"
        page.screenshot(path=screenshot_path, full_page=True)

    def main(self):
        hsr_utils = HSRUtils()
        location_id = hsr_utils.location_id
        ticket_type = hsr_utils.ticket_type

        with sync_playwright() as p:
            base_url = "https://irs.thsrc.com.tw"
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                java_script_enabled=True,
                accept_downloads=False,
                has_touch=False,
                is_mobile=False,
                locale="zh-TW",
                permissions=[],
                geolocation=None,
                color_scheme="light",
                timezone_id="Asia/Shanghai",
            )
            page = context.new_page()
            page.goto(f"{base_url}/IMINT")

            # Page 1
            page.wait_for_load_state("networkidle")  # 等待網頁載入
            page.select_option(
                'select[name="selectStartStation"]', f"{location_id.get(self.location_from)}"
            )  # 出發地
            page.select_option(
                'select[name="selectDestinationStation"]', f"{location_id.get(self.location_to)}"
            )  # 目的地
            page.fill('input[name="toTimeInputField"]', f"{self.departure_date}")  # 2024/04/08
            page.select_option('select[name="toTimeTable"]', f"{self.departure_time}")  # 14:00
            page.select_option(
                f'select[name="ticketPanel:rows:{ticket_type.get(self.ticket_type)}:ticketAmount"]',
                f"{self.ticket_numbers}",
            )  # 票種
            base64_captcha = hsr_utils.get_captcha_image(page=page, base_url=base_url)
            captcha_code = hsr_utils.resolve_captcha(base64_captcha=base64_captcha)
            page.fill('input[name="homeCaptcha:securityCode"]', captcha_code)
            self.screenshot(page=page)
            page.click('input[name="SubmitButton"][value="開始查詢"]', timeout=1)

            # Page 2
            page.wait_for_load_state("networkidle")  # 等待網頁載入
            # hsr_utils.skip_cookie(page=page)  # 跳過詢問cookie
            page.click('input[value="確認車次"]')  # 點擊確認車次按鈕
            self.screenshot(page=page)

            # Page 3
            page.wait_for_load_state("networkidle")  # 等待網頁載入
            page.fill('input[name="dummyId"]', self.personal_id)  # 填寫證件號碼
            page.fill('input[name="dummyPhone"]', self.phone_number)  # 填寫手機號碼
            page.fill('input[name="email"]', self.email_address)  # 填寫電子郵件
            page.click('input[name="agree"]')  # 勾選同意條款
            page.click('input[id="isSubmit"]')  # 點擊完成訂位按鈕
            self.screenshot(page=page)

            # Page 4
            page.wait_for_load_state("networkidle")
            pnr_code_element = page.query_selector("p.pnr-code > span")  # 獲取訂位號碼代碼
            pnr_code = pnr_code_element.inner_text() if pnr_code_element else None
            console.log(f"訂位編號: {pnr_code}")
            # hsr_utils.skip_alert(page=page)
            self.screenshot(page=page)

            # if self.card_number and self.card_expire_date:
            #     self.fill_payment(page=page)
            return pnr_code


if __name__ == "__main__":
    personal_id = "A123456789"
    phone_number = "0977123456"
    email_address = "test@gmail.com"
    ticket_type = "成人票"
    ticket_numbers = "1"
    location_from = "新竹"
    location_to = "南港"
    departure_date = "2024/04/08"
    departure_time = "14:00"
    HSR(
        personal_id=personal_id,
        phone_number=phone_number,
        email_address=email_address,
        ticket_type=ticket_type,
        ticket_numbers=ticket_numbers,
        location_from=location_from,
        location_to=location_to,
        departure_date=departure_date,
        departure_time=departure_time,
    ).main()
