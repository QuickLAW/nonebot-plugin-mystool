from typing import NamedTuple
from pydantic import BaseModel

GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)
"""人机验证结果数据"""


class GeetestResultV4(BaseModel):
    """
    GEETEST GT4 人机验证结果数据
    """
    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str
