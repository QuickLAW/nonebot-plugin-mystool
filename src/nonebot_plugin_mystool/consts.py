from typing import Dict, Any

from .model import plugin_env
from .config import plugin_config
from .utils import generate_device_id

URL_LOGIN_TICKET_BY_CAPTCHA = "https://webapi.account.mihoyo.com/Api/login_by_mobilecaptcha"
URL_LOGIN_TICKET_BY_PASSWORD = "https://webapi.account.mihoyo.com/Api/login_by_password"
URL_MULTI_TOKEN_BY_LOGIN_TICKET = "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={0}&token_types=3&uid={1}"
URL_COOKIE_TOKEN_BY_CAPTCHA = "https://api-takumi.mihoyo.com/account/auth/api/webLoginByMobile"
URL_COOKIE_TOKEN_BY_STOKEN = "https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken"
URL_LTOKEN_BY_STOKEN = "https://passport-api.mihoyo.com/account/auth/api/getLTokenBySToken"
URL_STOKEN_V2_BY_V1 = "https://passport-api.mihoyo.com/account/ma-cn-session/app/getTokenBySToken"
URL_ACTION_TICKET = "https://api-takumi.mihoyo.com/auth/api/getActionTicketBySToken?action_type=game_role&stoken={stoken}&uid={bbs_uid}"
URL_GAME_RECORD = "https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid={}"
URL_GAME_LIST = "https://bbs-api.mihoyo.com/apihub/api/getGameList"
URL_MYB = "https://api-takumi.mihoyo.com/common/homutreasure/v1/web/user/point?app_id=1&point_sn=myb"
URL_DEVICE_LOGIN = "https://bbs-api.mihoyo.com/apihub/api/deviceLogin"
URL_DEVICE_SAVE = "https://bbs-api.mihoyo.com/apihub/api/saveDevice"
URL_GOOD_LIST = "https://api-takumi.mihoyo.com/mall/v1/web/goods/list?app_id=1&point_sn=myb&page_size=20&page={page}&game={game}"
URL_CHECK_GOOD = "https://api-takumi.mihoyo.com/mall/v1/web/goods/detail?app_id=1&point_sn=myb&goods_id={}"
URL_EXCHANGE = "https://api-takumi.miyoushe.com/mall/v1/web/goods/exchange"
URL_ADDRESS = "https://api-takumi.mihoyo.com/account/address/list?t={}"
URL_REGISTRABLE = "https://webapi.account.mihoyo.com/Api/is_mobile_registrable?mobile={mobile}&t={t}"
URL_CREATE_MMT = "https://webapi.account.mihoyo.com/Api/create_mmt?scene_type=1&now={now}&reason=user.mihoyo.com%2523%252Flogin%252Fcaptcha&action_type=login_by_mobile_captcha&t={t}"
URL_CREATE_MOBILE_CAPTCHA = "https://webapi.account.mihoyo.com/Api/create_mobile_captcha"
URL_GET_USER_INFO = "https://bbs-api.miyoushe.com/user/api/getUserFullInfo?uid={uid}"
URL_GET_DEVICE_FP = "https://public-data-api.mihoyo.com/device-fp/api/getFp"
URL_GENSHEN_NOTE_BBS = "https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote"
URL_GENSHEN_NOTE_WIDGET = "https://api-takumi-record.mihoyo.com/game_record/genshin/aapi/widget/v2"
URL_STARRAIL_NOTE_BBS = "https://api-takumi-record.mihoyo.com/game_record/app/hkrpg/api/note"
URL_STARRAIL_NOTE_WIDGET = "https://api-takumi-record.mihoyo.com/game_record/app/hkrpg/aapi/widget"
URL_CREATE_VERIFICATION = "https://bbs-api.miyoushe.com/misc/api/createVerification?is_high=true"
URL_VERIFY_VERIFICATION = "https://bbs-api.miyoushe.com/misc/api/verifyVerification"
URL_FETCH_GAME_TOKEN_QRCODE = "https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/fetch"
URL_QUERY_GAME_TOKEN_QRCODE = "https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/query"
URL_GET_TOKEN_BY_GAME_TOKEN = "https://api-takumi.mihoyo.com/account/ma-cn-session/app/getTokenByGameToken"
URL_GET_COOKIE_TOKEN_BY_GAME_TOKEN = "https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoByGameToken"

HEADERS_WEBAPI = {
    "Host": "webapi.account.mihoyo.com",
    "Connection": "keep-alive",
    "sec-ch-ua": plugin_config.device_config.UA,
    "DNT": "1",
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_PC,
    "sec-ch-ua-mobile": "?0",
    "User-Agent": plugin_config.device_config.USER_AGENT_PC,
    "x-rpc-device_id": None,
    "Accept": "application/json, text/plain, */*",
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_PC,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-rpc-client_type": "4",
    "sec-ch-ua-platform": plugin_config.device_config.UA_PLATFORM,
    "Origin": "https://user.mihoyo.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://user.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
}
HEADERS_PASSPORT_API = {
    "Host": "passport-api.mihoyo.com",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "x-rpc-client_type": "1",
    "x-rpc-device_id": None,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "x-rpc-game_biz": "bbs_cn",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "User-Agent": plugin_config.device_config.USER_AGENT_OTHER,
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "x-rpc-sdk_version": "1.6.1",
    "Connection": "keep-alive",
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION
}
HEADERS_API_TAKUMI_PC = {
    "Host": "api-takumi.mihoyo.com",
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://bbs.mihoyo.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": plugin_config.device_config.USER_AGENT_PC,
    "Referer": "https://bbs.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9"
}
HEADERS_API_TAKUMI_MOBILE = {
    "Host": "api-takumi.mihoyo.com",
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Referer": "https://webstatic.mihoyo.com/",
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "x-rpc-channel": plugin_config.device_config.X_RPC_CHANNEL,
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=utf-8",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION,
    "x-rpc-platform": plugin_config.device_config.X_RPC_PLATFORM,
    "DS": None
}
HEADERS_GAME_RECORD = {
    "Host": "api-takumi-record.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_BBS_API = {
    "Host": "bbs-api.mihoyo.com",
    "DS": None,
    "Accept": "*/*",
    # x-rpc-device_id needs to be generated dynamically or passed
    "x-rpc-verify_key": "bll8iq97cem8",
    "x-rpc-client_type": "1",
    "x-rpc-channel": plugin_config.device_config.X_RPC_CHANNEL,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "User-Agent": plugin_config.device_config.USER_AGENT_OTHER,
    "Connection": "keep-alive",
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE
}
HEADERS_MYB = {
    "Host": "api-takumi.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_DEVICE = {
    "DS": None,
    "x-rpc-client_type": "2",
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION_ANDROID,
    "x-rpc-channel": plugin_config.device_config.X_RPC_CHANNEL_ANDROID,
    "x-rpc-device_id": None,
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_ANDROID,
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_ANDROID,
    "Referer": "https://app.mihoyo.com",
    "Content-Type": "application/json; charset=UTF-8",
    "Host": "bbs-api.mihoyo.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": plugin_config.device_config.USER_AGENT_ANDROID_OTHER
}
HEADERS_GOOD_LIST = {
    "Host": "api-takumi.mihoyo.com",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://user.mihoyo.com",
    "Connection": "keep-alive",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Referer": "https://user.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_EXCHANGE = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Host": "api-takumi.miyoushe.com",
    "Origin": "https://webstatic.miyoushe.com",
    "Referer": "https://webstatic.miyoushe.com/",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "x-rpc-channel": "appstore",
    "x-rpc-client_type": "1",
    "x-rpc-verify_key": "bll8iq97cem8",
    "x-rpc-device_fp": None,
    "x-rpc-device_id": None,
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION
}
HEADERS_ADDRESS = {
    "Host": "api-takumi.mihoyo.com",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://user.mihoyo.com",
    "Connection": "keep-alive",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Referer": "https://user.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_GENSHIN_STATUS_WIDGET = {
    "Host": "api-takumi-record.mihoyo.com",
    "DS": None,
    "Accept": "*/*",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "1",
    "x-rpc-channel": "appstore",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "User-Agent": plugin_config.device_config.USER_AGENT_WIDGET,
    "Connection": "keep-alive",
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION
}
HEADERS_GENSHIN_STATUS_BBS = {
    "DS": None,
    "x-rpc-device_id": None,
    "Accept": "application/json,text/plain,*/*",
    "Origin": "https://webstatic.mihoyo.com",
    "User-agent": plugin_config.device_config.USER_AGENT_ANDROID,
    "Referer": "https://webstatic.mihoyo.com/",
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "X-Requested-With": "com.mihoyo.hyperion",
    "x-rpc-client_type": "5",
    "x-rpc-tool_version": "v4.2.2-ys",
    "x-rpc-page": "v4.2.2-ys_#/ys/daily"
}
HEADERS_STARRAIL_STATUS_WIDGET = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "User-Agent": plugin_config.device_config.USER_AGENT_WIDGET,
    # "DS": None,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-app_version": plugin_config.device_config.X_RPC_APP_VERSION,
    "x-rpc-channel": plugin_config.device_config.X_RPC_CHANNEL,
    "x-rpc-client_type": "2",
    "x-rpc-page": '',
    "x-rpc-device_fp": '',
    "x-rpc-device_id": '',
    "x-rpc-device_model": plugin_config.device_config.X_RPC_DEVICE_MODEL_MOBILE,
    "x-rpc-device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-sys_version": plugin_config.device_config.X_RPC_SYS_VERSION,
    "Connection": "keep-alive",
    "Host": "api-takumi-record.mihoyo.com"
}

URL_SIGN_REWARD = "https://api-takumi.mihoyo.com/event/luna/home"
URL_SIGN_INFO = "https://api-takumi.mihoyo.com/event/luna/info"
URL_SIGN_SIGN = "https://api-takumi.mihoyo.com/event/luna/sign"
URL_SIGN_REWARD_ZZZ = "https://act-nap-api.mihoyo.com/event/luna/zzz/home"
URL_SIGN_INFO_ZZZ = "https://act-nap-api.mihoyo.com/event/luna/zzz/info"
URL_SIGN_SIGN_ZZZ = "https://act-nap-api.mihoyo.com/event/luna/zzz/sign"

HEADERS_SIGN_REWARD = {
    "Host": "api-takumi.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": plugin_config.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
