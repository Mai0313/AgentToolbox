import os
from typing import Optional

import autorootcwd
from rich.console import Console
from playwright.sync_api import sync_playwright
from toolbox.src.hsr_utils import HSRUtils
from toolbox.models.payment_models import PaymentModel

console = Console()


class HSR(PaymentModel):
    personal_id: str
    phone_number: str
    email_address: str

    def fill_payment(self):
        pass

    def main(self):
        with sync_playwright() as p:
            hsr_utils = HSRUtils()
            base_url = "https://irs.thsrc.com.tw"
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                java_script_enabled=True,
                accept_downloads=False,
                has_touch=False,
                is_mobile=False,
                locale="en-US",
                permissions=[],
                geolocation=None,
                color_scheme="light",
                timezone_id="Asia/Shanghai",
            )
            page = context.new_page()

            # Page 1
            page.goto(f"{base_url}/IMINT")

            page.select_option('select[name="selectStartStation"]', "5")  # 新竹
            page.select_option('select[name="selectDestinationStation"]', "2")  # 台北

            page.fill('input[name="toTimeInputField"]', "2024/04/05")
            page.select_option('select[name="toTimeTable"]', "23:30")  # 17:00

            page.select_option('select[name="ticketPanel:rows:0:ticketAmount"]', "2")  # 成人票
            page.select_option('select[name="ticketPanel:rows:1:ticketAmount"]', "1")  # 兒童票
            page.select_option('select[name="ticketPanel:rows:2:ticketAmount"]', "0")  # 愛心票
            page.select_option('select[name="ticketPanel:rows:3:ticketAmount"]', "0")  # 敬老票
            page.select_option('select[name="ticketPanel:rows:4:ticketAmount"]', "0")  # 大學生票

            base64_captcha = HSRUtils.get_captcha_image(page=page, base_url=base_url)
            captcha_code = HSRUtils.resolve_captcha(base64_captcha=base64_captcha)
            page.fill('input[name="homeCaptcha:securityCode"]', captcha_code)
            page.click('input[name="SubmitButton"][value="開始查詢"]')

            # Page 2
            # 等待網頁載入
            page.wait_for_load_state("networkidle")
            # 點擊確認車次按鈕
            page.click('input[value="確認車次"]')
            # 等待網頁載入
            page.wait_for_load_state("networkidle")
            # 填寫證件號碼
            page.fill('input[name="dummyId"]', self.personal_id)
            # 填寫手機號碼和電子郵件
            page.fill('input[name="dummyPhone"]', self.phone_number)
            page.fill('input[name="email"]', self.email_address)
            # 勾選同意條款
            page.click('input[name="agree"]')
            # 點擊完成訂位按鈕
            page.click('input[id="isSubmit"]')
            page.wait_for_load_state("networkidle")
            # 獲取訂位號碼代碼
            pnr_code_element = page.query_selector("p.pnr-code span")
            pnr_code = pnr_code_element.inner_text() if pnr_code_element else None

            close_button_selector = (
                'input.uk-modal-close.uk-button.uk-button-primary.btn-confirm[value="關閉"]'
            )
            close_button = page.query_selector(close_button_selector)
            if close_button:
                close_button.click()
                console.log("Warning: The ticket is running out of stock.")

            page.wait_for_load_state("networkidle", timeout=1)
            os.makedirs("logs", exist_ok=True)
            screenshot_path = "./logs/screenshot.png"
            page.screenshot(path=screenshot_path, full_page=True)

            if self.card_number and self.card_expire_date:
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
                page.click("a#btnPressToPay")
                # 等待付款完成或其他後續操作 (目前不知道畫面長啥樣 以後再看)
                page.wait_for_load_state("networkidle")
            browser.close()
            console.log(f"訂位編號: {pnr_code}")
            return pnr_code


if __name__ == "__main__":
    # Need 身分證 電話 email
    # Additional TGo 帳號 (直接用身分證)
    personal_id = "A123456789"
    phone_number = "0977123456"
    email_address = "test@gmail.com"
    card_holder = "Wei"
    card_number = None  # "1234567812345678"
    card_expire_date = None  # "0828"
    HSR(
        personal_id=personal_id,
        phone_number=phone_number,
        email_address=email_address,
        card_holder=card_holder,
        card_number=card_number,
        card_expire_date=card_expire_date,
    ).main()
