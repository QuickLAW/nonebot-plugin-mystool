
import inspect
import time
from abc import abstractmethod
from datetime import datetime
from typing import Optional, Union, Dict, Any, TypeVar, Tuple, List, Set, Literal, NamedTuple

import pytz
from httpx import Cookies
from pydantic import BaseModel, Field, field_validator, no_type_check
from uuid import UUID, uuid4

from .utils import blur_phone, generate_device_id
from ._version import __version__

class BaseModelWithSetter(BaseModel):
    @no_type_check
    def __setattr__(self, name, value):
        try:
            super().__setattr__(name, value)
        except ValueError as e:
            setters = inspect.getmembers(
                self.__class__,
                predicate=lambda x: isinstance(x, property) and x.fset is not None
            )
            for setter_name, func in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    break
            else:
                raise e

class BaseModelWithUpdate(BaseModel):
    _T = TypeVar("_T", bound=BaseModel)

    @abstractmethod
    def update(self, obj: Union[_T, Dict[str, Any]]) -> _T:
        if isinstance(obj, type(self)):
            obj = obj.model_dump()
        items = filter(lambda x: x[0] in self.model_fields, obj.items())
        for k, v in items:
            setattr(self, k, v)
        return self

class Good(BaseModelWithUpdate):
    type: int
    next_time: Optional[int] = None
    status: Optional[str] = None
    sale_start_time: Optional[int] = None
    time_by_detail: Optional[int] = None
    next_num: Optional[int] = None
    account_exchange_num: int
    account_cycle_limit: int
    account_cycle_type: str
    game_biz: Optional[str] = None
    game: Optional[str] = None
    unlimit: Optional[bool] = None
    name: Optional[str] = None
    goods_name: Optional[str] = None
    goods_id: str
    price: int
    icon: str

    def update(self, obj: Union["Good", Dict[str, Any]]) -> "Good":
        return super().update(obj)

    @property
    def time(self):
        if self.next_time == 0:
            return None
        sale_start_time = int(self.sale_start_time) if self.sale_start_time else 0
        if sale_start_time and time.time() < sale_start_time < self.next_time:
            return sale_start_time
        else:
            return self.next_time

    def get_time_text(self, timezone: Optional[str] = None):
        if self.time_end:
            return "已结束"
        elif self.time == 0:
            return None
        elif self.time_limited:
            if timezone:
                tz_info = pytz.timezone(timezone)
                date_time = datetime.fromtimestamp(self.time, tz_info)
            else:
                date_time = datetime.fromtimestamp(self.time)
            return date_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "任何时间"

    @property
    def stoke_text(self):
        if self.time_end:
            return "无"
        elif self.time_limited:
            return str(self.num)
        else:
            return "不限"

    @property
    def time_limited(self):
        return not self.unlimit

    @property
    def time_end(self):
        return self.next_time == 0

    @property
    def num(self):
        if self.type != 1 and self.next_num == 0:
            return None
        else:
            return self.next_num

    @property
    def limit(self):
        return (self.account_exchange_num,
                self.account_cycle_limit, self.account_cycle_type)

    @property
    def is_virtual(self):
        return self.type == 2

    @property
    def general_name(self):
        return self.name or self.goods_name

class GameRecord(BaseModel):
    region_name: str
    game_id: int
    level: int
    region: str
    game_role_id: str
    nickname: str

class GameInfo(BaseModel):
    id: int
    app_icon: str
    op_name: str
    en_name: str
    icon: str
    name: str

class Address(BaseModel):
    connect_areacode: str
    connect_mobile: str
    province_name: str
    city_name: str
    county_name: str
    addr_ext: str
    connect_name: str
    id: str

    @property
    def phone(self) -> str:
        return self.connect_areacode + " " + self.connect_mobile

class MmtData(BaseModel):
    challenge: Optional[str] = None
    gt: Optional[str] = None
    mmt_key: Optional[str] = None
    new_captcha: Optional[bool] = None
    risk_type: Optional[str] = None
    success: Optional[int] = None
    use_v4: Optional[bool] = None

class Award(BaseModel):
    name: str
    icon: str
    cnt: int

class GameSignInfo(BaseModel):
    is_sign: bool
    total_sign_day: int
    sign_cnt_missed: int

class MissionData(BaseModel):
    points: int
    name: str
    mission_key: str
    threshold: int

class MissionState(BaseModel):
    current_myb: int
    state_dict: Dict[str, Tuple[MissionData, int]]

class GenshinNote(BaseModel):
    current_resin: Optional[int] = None
    finished_task_num: Optional[int] = None
    current_expedition_num: Optional[int] = None
    max_expedition_num: Optional[int] = None
    current_home_coin: Optional[int] = None
    max_home_coin: Optional[int] = None
    transformer: Optional[Dict[str, Any]] = None
    resin_recovery_time: Optional[int] = None

    @property
    def transformer_text(self):
        try:
            if not self.transformer['obtained']:
                return '未获得'
            elif self.transformer['recovery_time']['reached']:
                return '已准备就绪'
            else:
                return f"{self.transformer['recovery_time']['Day']} 天" \
                       f"{self.transformer['recovery_time']['Hour']} 小时 " \
                       f"{self.transformer['recovery_time']['Minute']} 分钟"
        except KeyError:
            return None

    @property
    def resin_recovery_text(self):
        try:
            if not self.resin_recovery_time:
                return ':未获得时间数据'
            elif self.resin_recovery_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.resin_recovery_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None

class StarRailNote(BaseModel):
    current_stamina: Optional[int] = None
    max_stamina: Optional[int] = None
    stamina_recover_time: Optional[int] = None
    current_train_score: Optional[int] = None
    max_train_score: Optional[int] = None
    current_rogue_score: Optional[int] = None
    max_rogue_score: Optional[int] = None
    accepted_expedition_num: Optional[int] = None
    total_expedition_num: Optional[int] = None
    has_signed: Optional[bool] = None

    @property
    def stamina_recover_text(self):
        try:
            if not self.stamina_recover_time:
                return ':未获得时间数据'
            elif self.stamina_recover_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.stamina_recover_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None

class GenshinNoteNotice(GenshinNote):
    current_resin: bool = False
    current_resin_full: bool = False
    current_home_coin: bool = False
    transformer: bool = False

class StarRailNoteNotice(StarRailNote):
    current_stamina: bool = False
    current_stamina_full: bool = False
    current_train_score: bool = False
    current_rogue_score: bool = False

class BaseApiStatus(BaseModel):
    success: bool = False
    network_error: bool = False
    incorrect_return: bool = False
    login_expired: bool = False
    need_verify: bool = False
    invalid_ds: bool = False

    def __bool__(self):
        return self.success

    @property
    def error_type(self):
        for key, field in self.model_fields.items():
            if field and key != "success":
                return key
        return None

class CreateMobileCaptchaStatus(BaseApiStatus):
    incorrect_geetest: bool = False
    not_registered: bool = False
    invalid_phone_number: bool = False
    too_many_requests: bool = False

class GetCookieStatus(BaseApiStatus):
    incorrect_captcha: bool = False
    missing_login_ticket: bool = False
    missing_bbs_uid: bool = False
    missing_cookie_token: bool = False
    missing_stoken: bool = False
    missing_stoken_v1: bool = False
    missing_stoken_v2: bool = False
    missing_mid: bool = False

class GetGoodDetailStatus(BaseApiStatus):
    good_not_existed: bool = False

class ExchangeStatus(BaseApiStatus):
    missing_stoken: bool = False
    missing_mid: bool = False
    missing_address: bool = False
    missing_game_uid: bool = False
    unsupported_game: bool = False
    failed_getting_game_record: bool = False
    init_required: bool = False
    account_not_found: bool = False

class MissionStatus(BaseApiStatus):
    failed_getting_post: bool = False
    already_signed: bool = False

class GetFpStatus(BaseApiStatus):
    invalid_arguments: bool = False

class BoardStatus(BaseApiStatus):
    game_record_failed: bool = False
    game_list_failed: bool = False

class GenshinNoteStatus(BoardStatus):
    no_genshin_account: bool = False

class StarRailNoteStatus(BoardStatus):
    no_starrail_account: bool = False

class QueryGameTokenQrCodeStatus(BaseApiStatus):
    qrcode_expired: bool = False
    qrcode_init: bool = False
    qrcode_scanned: bool = False

GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)

class GeetestResultV4(BaseModel):
    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str

class CommandUsage(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None

# --- Data Models ---

class BBSCookies(BaseModelWithSetter, BaseModelWithUpdate):
    stuid: Optional[str] = None
    ltuid: Optional[str] = None
    account_id: Optional[str] = None
    login_uid: Optional[str] = None
    stoken_v1: Optional[str] = None
    stoken_v2: Optional[str] = None
    cookie_token: Optional[str] = None
    login_ticket: Optional[str] = None
    ltoken: Optional[str] = None
    mid: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        stoken = data.get("stoken")
        if stoken:
            self.stoken = stoken

    def is_correct(self) -> bool:
        if self.bbs_uid and self.stoken and self.cookie_token:
            return True
        else:
            return False

    @property
    def bbs_uid(self):
        uid = None
        for value in [self.stuid, self.ltuid, self.account_id, self.login_uid]:
            if value:
                uid = value
                break
        return uid or None

    @bbs_uid.setter
    def bbs_uid(self, value: str):
        self.stuid = value
        self.ltuid = value
        self.account_id = value
        self.login_uid = value

    @property
    def stoken(self):
        if self.stoken_v1:
            return self.stoken_v1
        elif self.stoken_v2:
            return self.stoken_v2
        else:
            return None

    @stoken.setter
    def stoken(self, value):
        if value.startswith("v2_"):
            self.stoken_v2 = value
        else:
            self.stoken_v1 = value

    def update(self, cookies: Union[Dict[str, str], Cookies, "BBSCookies"]):
        if not isinstance(cookies, BBSCookies):
            self.stoken = cookies.get("stoken") or self.stoken
            self.bbs_uid = cookies.get("bbs_uid") or self.bbs_uid
            cookies.pop("stoken", None)
            cookies.pop("bbs_uid", None)
        return super().update(cookies)

    def dict(self, *,
             include: Optional[Union[Set[str], Mapping[str, Any]]] = None,
             exclude: Optional[Union[Set[str], Mapping[str, Any]]] = None,
             by_alias: bool = False,
             exclude_unset: bool = False, exclude_defaults: bool = False,
             exclude_none: bool = False, v2_stoken: bool = False,
             cookie_type: bool = False) -> Dict[str, Any]:
        self.bbs_uid = self.bbs_uid
        cookies_dict = super().model_dump(include=include, exclude=exclude, by_alias=by_alias,
                                          exclude_unset=exclude_unset, exclude_defaults=exclude_defaults,
                                          exclude_none=exclude_none)
        if v2_stoken and self.stoken_v2:
            cookies_dict["stoken"] = self.stoken_v2
        else:
            cookies_dict["stoken"] = self.stoken_v1

        if cookie_type:
            cookies_dict.pop("stoken_v1", None)
            cookies_dict.pop("stoken_v2", None)
            empty_key = set()
            for key, value in cookies_dict.items():
                if not value:
                    empty_key.add(key)
            for key in empty_key:
                cookies_dict.pop(key)

        return cookies_dict

class UserAccount(BaseModelWithSetter):
    phone_number: Optional[str] = None
    cookies: BBSCookies
    address: Optional[Address] = None
    device_id_ios: str
    device_id_android: str
    device_fp: Optional[str] = None
    enable_mission: bool = True
    enable_game_sign: bool = True
    enable_resin: bool = True
    platform: Literal["ios", "android"] = "ios"
    game_sign_games: List[str] = [
        "GenshinImpact",
        "HonkaiImpact3",
        "HoukaiGakuen2",
        "TearsOfThemis",
        "StarRail",
        "ZenlessZoneZero"
    ]
    mission_games: List[str] = ["BBSMission"]
    user_stamina_threshold: int = 240
    user_resin_threshold: int = 200

    def __init__(self, **data: Any):
        if not data.get("device_id_ios") or not data.get("device_id_android"):
            if not data.get("device_id_ios"):
                data.setdefault("device_id_ios", generate_device_id())
            if not data.get("device_id_android"):
                data.setdefault("device_id_android", generate_device_id())
        super().__init__(**data)

    @property
    def bbs_uid(self):
        return self.cookies.bbs_uid

    @bbs_uid.setter
    def bbs_uid(self, value: str):
        self.cookies.bbs_uid = value

    @property
    def display_name(self):
        return f"{self.bbs_uid}({blur_phone(self.phone_number)})" if self.phone_number else self.bbs_uid

class ExchangePlan(BaseModel):
    good: Good
    address: Optional[Address] = None
    account: UserAccount
    game_record: Optional[GameRecord] = None

    def __hash__(self):
        return hash(
            (
                self.good.goods_id,
                self.good.time,
                self.address.id if self.address else None,
                self.account.bbs_uid,
                self.game_record.game_role_id if self.game_record else None
            )
        )

    class CustomDict(dict):
        _hash: int
        def __hash__(self):
            return self._hash

    def dict(self, **kwargs) -> Dict[str, Any]:
        normal_dict = super().model_dump(**kwargs)
        hashable_dict = ExchangePlan.CustomDict(normal_dict)
        hashable_dict._hash = hash(self)
        return hashable_dict

class ExchangeResult(BaseModel):
    result: bool
    return_data: dict
    plan: ExchangePlan

def uuid4_validate(v):
    try:
        UUID(v, version=4)
    except Exception:
        return False
    else:
        return True

class UserData(BaseModelWithSetter):
    enable_notice: bool = True
    geetest_url: Optional[str] = None
    geetest_params: Optional[Dict[str, Any]] = None
    uuid: Optional[str] = None
    qq_guild: Optional[Dict[str, int]] = {}
    qq_guilds: Optional[Dict[str, List[int]]] = Field(default={}, exclude=True)
    exchange_plans: Union[Set[ExchangePlan], List[ExchangePlan]] = set()
    accounts: Dict[str, UserAccount] = {}

    @field_validator("uuid")
    def uuid_validator(cls, v):
        if v is None and not uuid4_validate(v):
            raise ValueError("UUID格式错误，不是合法的UUIDv4")
        return v

    def __init__(self, **data: Any):
        super().__init__(**data)
        exchange_plans = self.exchange_plans
        self.exchange_plans = set()
        for plan in exchange_plans:
            plan = ExchangePlan.model_validate(plan)
            self.exchange_plans.add(plan)

        if self.uuid is None:
            self.uuid = str(uuid4())
        
        if not self.qq_guild and self.qq_guilds:
            self.qq_guild = {k: v[0] for k, v in filter(lambda x: x[1], self.qq_guilds.items())}

    def __hash__(self):
        return hash(self.uuid)

class PluginData(BaseModel):
    version: str = __version__
    user_bind: Optional[Dict[str, str]] = {}
    users: Dict[str, UserData] = {}
