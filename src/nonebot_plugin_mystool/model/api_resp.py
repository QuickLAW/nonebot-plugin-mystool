from typing import Optional, Dict, Any, Tuple, Type
from pydantic import BaseModel

class BaseApiStatus(BaseModel):
    """
    API返回结果基类
    """
    success: bool = False
    """成功"""
    network_error: bool = False
    """连接失败"""
    incorrect_return: bool = False
    """服务器返回数据不正确"""
    login_expired: bool = False
    """登录失效"""
    need_verify: bool = False
    """需要进行人机验证"""
    invalid_ds: bool = False
    """Headers DS无效"""

    def __bool__(self):
        return self.success

    @property
    def error_type(self):
        """
        返回错误类型
        """
        for key, field in self.model_fields.items():
            if field and key != "success":
                return key
        return None


class ApiResultHandler(BaseModel):
    """
    API返回的数据处理器
    """
    content: Dict[str, Any]
    """API返回的JSON对象序列化以后的Dict对象"""
    data: Optional[Dict[str, Any]] = None
    """API返回的数据体"""
    message: Optional[str] = None
    """API返回的消息内容"""
    retcode: Optional[int] = None
    """API返回的状态码"""

    def __init__(self, content: Dict[str, Any]):
        super().__init__(content=content)

        self.data = self.content.get("data")

        for key in ["retcode", "status"]:
            if self.retcode is None:
                self.retcode = self.content.get(key)
                if self.retcode is None:
                    self.retcode = self.data.get(key) if self.data else None

        self.message: Optional[str] = None
        for key in ["message", "msg"]:
            if not self.message:
                self.message = self.content.get(key)
                if not self.message:
                    self.message = self.data.get(key) if self.data else None

    @property
    def success(self):
        """
        是否成功
        """
        return self.retcode == 1 or self.message in ["成功", "OK"]

    @property
    def wrong_captcha(self):
        """
        是否返回验证码错误
        """
        return self.retcode in [-201, -302] or self.message in ["验证码错误", "Captcha not match Err"]

    @property
    def login_expired(self):
        """
        是否返回登录失效
        """
        return self.retcode in [-100, 10001] or self.message in ["登录失效，请重新登录"]

    @property
    def invalid_ds(self):
        """
        Headers里的DS是否无效
        """
        return self.message in ["invalid request"]

# Specific Status Classes

class CreateMobileCaptchaStatus(BaseApiStatus):
    """发送短信验证码 返回结果"""
    incorrect_geetest: bool = False
    not_registered: bool = False
    invalid_phone_number: bool = False
    too_many_requests: bool = False

class GetCookieStatus(BaseApiStatus):
    """获取Cookie 返回结果"""
    incorrect_captcha: bool = False
    missing_login_ticket: bool = False
    missing_bbs_uid: bool = False
    missing_cookie_token: bool = False
    missing_stoken: bool = False
    missing_stoken_v1: bool = False
    missing_stoken_v2: bool = False
    missing_mid: bool = False

class GetGoodDetailStatus(BaseApiStatus):
    """获取商品详细信息 返回结果"""
    good_not_existed: bool = False

class ExchangeStatus(BaseApiStatus):
    """兑换操作 返回结果"""
    missing_stoken: bool = False
    missing_mid: bool = False
    missing_address: bool = False
    missing_game_uid: bool = False
    unsupported_game: bool = False
    failed_getting_game_record: bool = False
    init_required: bool = False
    account_not_found: bool = False

class MissionStatus(BaseApiStatus):
    """米游币任务 返回结果"""
    failed_getting_post: bool = False
    already_signed: bool = False

class GetFpStatus(BaseApiStatus):
    """获取DeviceFp 返回结果"""
    invalid_arguments: bool = False

class BoardStatus(BaseApiStatus):
    """实时便笺 返回结果"""
    game_record_failed: bool = False
    game_list_failed: bool = False

class GenshinNoteStatus(BoardStatus):
    """原神实时便笺 返回结果"""
    no_genshin_account: bool = False

class StarRailNoteStatus(BoardStatus):
    """星铁实时便笺 返回结果"""
    no_starrail_account: bool = False

class QueryGameTokenQrCodeStatus(BaseApiStatus):
    """查询二维码状态 返回结果"""
    qrcode_expired: bool = False
    qrcode_init: bool = False
    qrcode_scanned: bool = False
