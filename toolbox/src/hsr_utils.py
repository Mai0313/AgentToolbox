import base64
from urllib.parse import urljoin

import orjson
import ddddocr
from pydantic import BaseModel, computed_field
import requests
from rich.console import Console
from playwright.sync_api._generated import Page

console = Console()


class HSRConfig(BaseModel):
    location_id: dict[str, int]
    ticket_type: dict[str, int]


class HSRUtils(BaseModel):
    @staticmethod
    def resolve_captcha(base64_captcha: str) -> str:
        ocr = ddddocr.DdddOcr(show_ad=False)
        captcha_code = ocr.classification(base64_captcha)
        console.log(f"Captcha Result: {captcha_code}")
        return captcha_code

    @staticmethod
    def get_captcha_image(page: Page, base_url: str) -> str:
        captcha_selector = "img#BookingS1Form_homeCaptcha_passCode"
        captcha_element = page.wait_for_selector(captcha_selector)
        captcha_element = captcha_element.get_attribute("src")
        captcha_url = urljoin(base_url, captcha_element)
        console.log(f"Captcha URL: {captcha_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        }
        response = requests.get(url=captcha_url, headers=headers)
        base64_captcha = base64.b64encode(response.content).decode("utf-8")
        return base64_captcha

    @computed_field
    @property
    def hsr_config(self) -> HSRConfig:
        hsr_config_path = "./configs/hsr_location.json"
        with open(hsr_config_path) as f:
            hsr_config = orjson.loads(f.read())
        hsr_config = HSRConfig(**hsr_config)
        return hsr_config

    @computed_field
    @property
    def location_id(self) -> dict[str, int]:
        return self.hsr_config.location_id

    @computed_field
    @property
    def ticket_type(self) -> dict[str, int]:
        return self.hsr_config.ticket_type


if __name__ == "__main__":
    hsr_utils = HSRUtils()
    console.print(hsr_utils.location_id)
    console.print(hsr_utils.ticket_type)
