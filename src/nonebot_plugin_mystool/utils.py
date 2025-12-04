
import hashlib
import io
import json
import random
import string
import time
import uuid
from typing import Dict, Union, Optional, Literal

import tenacity
from qrcode import QRCode

from .config import plugin_config

def custom_attempt_times(retry: bool):
    if retry:
        return tenacity.stop_after_attempt(plugin_config.preference.max_retry_times + 1)
    else:
        return tenacity.stop_after_attempt(1)

def get_async_retry(retry: bool):
    return tenacity.AsyncRetrying(
        stop=custom_attempt_times(retry),
        retry=tenacity.retry_if_exception_type(BaseException),
        wait=tenacity.wait_fixed(plugin_config.preference.retry_interval),
    )

def generate_device_id() -> str:
    return str(uuid.uuid4()).upper()

def cookie_str_to_dict(cookie_str: str) -> Dict[str, str]:
    cookie_str = cookie_str.replace(" ", "")
    if not cookie_str.endswith(";"):
        cookie_str += ";"
    
    cookie_dict = {}
    start = 0
    while start < len(cookie_str):
        mid = cookie_str.find("=", start)
        if mid == -1:
            break
        end = cookie_str.find(";", mid)
        if end == -1:
            break
        cookie_dict[cookie_str[start:mid]] = cookie_str[mid + 1:end]
        start = end + 1
    return cookie_dict

def cookie_dict_to_str(cookie_dict: Dict[str, str]) -> str:
    return ";".join([f"{k}={v}" for k, v in cookie_dict.items()]) + ";"

def generate_ds(data: Union[str, dict, list, None] = None, params: Union[str, dict, None] = None,
                platform: Literal["ios", "android"] = "ios", salt: Optional[str] = None):
    if data is None and params is None or \
            salt is not None and salt != plugin_config.salt_config.SALT_PROD:
        if platform == "ios":
            salt = salt or plugin_config.salt_config.SALT_IOS
        else:
            salt = salt or plugin_config.salt_config.SALT_ANDROID
        t = str(int(time.time()))
        a = "".join(random.sample(string.ascii_lowercase + string.digits, 6))
        re = hashlib.md5(f"salt={salt}&t={t}&r={a}".encode()).hexdigest()
        return f"{t},{a},{re}"
    else:
        if params:
            salt = plugin_config.salt_config.SALT_PARAMS if not salt else salt
        else:
            salt = plugin_config.salt_config.SALT_DATA if not salt else salt

        if not data:
            if salt == plugin_config.salt_config.SALT_PROD:
                data = {}
            else:
                data = ""
        if not params:
            params = ""

        if not isinstance(data, str):
            data = json.dumps(data).replace(" ", "")
        if not isinstance(params, str):
            from urllib.parse import urlencode
            params = urlencode(params)

        t = str(int(time.time()))
        r = str(random.randint(100000, 200000))
        c = hashlib.md5(f"salt={salt}&t={t}&r={r}&b={data}&q={params}".encode()).hexdigest()
        return f"{t},{r},{c}"

def generate_seed_id(length: int = 8) -> str:
    max_num = int("FF" * length, 16)
    return hex(random.randint(0, max_num))[2:]

def generate_fp_locally(length: int = 13):
    characters = string.digits + "abcdef"
    return ''.join(random.choices(characters, k=length))

def blur_phone(phone: Union[str, int]) -> str:
    if isinstance(phone, int):
        phone = str(phone)
    return f"☎️{phone[-4:]}" if len(phone) >= 4 else phone

def generate_qr_img(data: str):
    qr_code = QRCode(border=2)
    qr_code.add_data(data)
    qr_code.make()
    image = qr_code.make_image()
    image_bytes = io.BytesIO()
    image.save(image_bytes)
    return image_bytes.getvalue()
