import time
import json
from typing import Tuple, Optional, Dict, Union
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
import tenacity
from requests.utils import dict_from_cookiejar

from ..consts import (
    HEADERS_BBS_API, URL_CREATE_VERIFICATION, URL_VERIFY_VERIFICATION,
    URL_FETCH_GAME_TOKEN_QRCODE, URL_QUERY_GAME_TOKEN_QRCODE,
    URL_GET_TOKEN_BY_GAME_TOKEN, URL_GET_COOKIE_TOKEN_BY_GAME_TOKEN,
    URL_LTOKEN_BY_STOKEN, HEADERS_WEBAPI, URL_REGISTRABLE, URL_CREATE_MMT,
    URL_CREATE_MOBILE_CAPTCHA, URL_LOGIN_TICKET_BY_CAPTCHA,
    URL_MULTI_TOKEN_BY_LOGIN_TICKET, HEADERS_API_TAKUMI_PC,
    URL_COOKIE_TOKEN_BY_CAPTCHA, URL_LOGIN_TICKET_BY_PASSWORD,
    HEADERS_PASSPORT_API, URL_COOKIE_TOKEN_BY_STOKEN, URL_STOKEN_V2_BY_V1
)
from ..model import (
    BaseApiStatus, MmtData, GeetestResult, UserAccount,
    QueryGameTokenQrCodeStatus, BBSCookies, GetCookieStatus,
    CreateMobileCaptchaStatus, GeetestResultV4, plugin_env
)
from ..utils import (
    logger, get_async_retry, generate_device_id, generate_ds, generate_fp_locally,
    generate_seed_id
)
from ..config import plugin_config
from .base import ApiResultHandler, is_incorrect_return, IncorrectReturn


async def check_registrable(phone_number: int, keep_client: bool = False, retry: bool = True) -> Tuple[
    BaseApiStatus,
    Optional[bool],
    str,
    Optional[httpx.AsyncClient]
]:
    """
    检查用户是否可以注册

    :param keep_client: httpx.AsyncClient 连接是否需要关闭
    :param phone_number: 手机号
    :param retry: 是否允许重试
    :return: (API返回状态, 用户是否可以注册, 设备ID, httpx.AsyncClient连接对象)
    """
    headers = HEADERS_WEBAPI.copy()
    device_id = generate_device_id()
    headers["x-rpc-device_id"] = device_id

    async def request():
        """
        发送请求的闭包函数
        """
        time_now = round(time.time() * 1000)
        return await client.get(URL_REGISTRABLE.format(mobile=phone_number, t=time_now),
                                headers=headers, timeout=plugin_config.preference.timeout)

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if keep_client:
                    client = httpx.AsyncClient()
                else:
                    async with httpx.AsyncClient() as client:
                        res = await request()
                res = await request()
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), bool(api_result.data["is_registable"]), device_id, client
    except tenacity.RetryError as e:
        if keep_client:
            await client.aclose()
        if is_incorrect_return(e):
            logger.exception(f"检查用户 {phone_number} 是否可以注册 - 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None, device_id, client
        else:
            logger.exception(f"检查用户 {phone_number} 是否可以注册 - 请求失败")
            return BaseApiStatus(network_error=True), None, device_id, None


async def create_mmt(client: Optional[httpx.AsyncClient] = None,
                     use_v4: bool = True,
                     device_id: str = None,
                     retry: bool = True) -> Tuple[
    BaseApiStatus,
    Optional[MmtData],
    str,
    Optional[httpx.AsyncClient]
]:
    """
    发送短信验证前所需的人机验证任务申请

    :param client: httpx.AsyncClient 连接
    :param use_v4: 是否使用极验第四代人机验证
    :param device_id: 设备 ID
    :param retry: 是否允许重试
    :return: (API返回状态, 人机验证任务数据, 设备ID, httpx.AsyncClient连接对象)
    """
    headers = HEADERS_WEBAPI.copy()
    device_id = device_id or generate_device_id()
    headers["x-rpc-device_id"] = device_id
    if use_v4:
        headers.setdefault("x-rpc-source", "accountWebsite")

    async def request():
        """
        发送请求的闭包函数
        """
        time_now = round(time.time() * 1000)
        return await client.get(URL_CREATE_MMT.format(now=time_now, t=time_now),
                                headers=headers, timeout=plugin_config.preference.timeout)

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client:
                    res = await request()
                else:
                    async with httpx.AsyncClient() as client:
                        res = await request()
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), MmtData.model_validate(api_result.data["mmt_data"]), device_id, client
    except tenacity.RetryError as e:
        if client:
            await client.aclose()
        if is_incorrect_return(e):
            logger.exception("获取短信验证-人机验证任务(create_mmt) - 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None, device_id, client
        else:
            logger.exception("获取短信验证-人机验证任务(create_mmt) - 请求失败")
            return BaseApiStatus(network_error=True), None, device_id, None


async def create_mobile_captcha(phone_number: str,
                                mmt_data: MmtData,
                                geetest_result: Union[GeetestResult, GeetestResultV4] = None,
                                client: Optional[httpx.AsyncClient] = None,
                                use_v4: bool = True,
                                device_id: str = None,
                                retry: bool = True
                                ) -> Tuple[CreateMobileCaptchaStatus, Optional[httpx.AsyncClient]]:
    """
    发送短信验证码，可尝试不传入 geetest_result，即不进行人机验证

    :param phone_number: 手机号
    :param mmt_data: 人机验证任务数据
    :param geetest_result: 人机验证结果数据
    :param client: httpx.AsyncClient 连接
    :param use_v4: 是否使用极验第四代人机验证
    :param device_id: 设备ID
    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = device_id or generate_device_id()
    if use_v4 and isinstance(geetest_result, GeetestResultV4):
        content = {
            "action_type": "login",
            "mmt_key": mmt_data.mmt_key,
            "geetest_v4_data": geetest_result.model_dump(exclude_defaults=True),
            "mobile": phone_number,
            "t": str(round(time.time() * 1000))
        }
    elif geetest_result:
        content = {
            "action_type": "login",
            "mmt_key": mmt_data.mmt_key,
            "geetest_challenge": mmt_data.challenge,
            "geetest_validate": geetest_result.validate,
            "geetest_seccode": geetest_result.seccode,
            "mobile": phone_number,
            "t": round(time.time() * 1000)
        }
    else:
        content = {
            "action_type": "login",
            "mmt_key": mmt_data.mmt_key,
            "mobile": phone_number,
            "t": round(time.time() * 1000)
        }

    async def request():
        """
        发送请求的闭包函数
        """
        return await client.post(URL_CREATE_MOBILE_CAPTCHA,
                                 params=content,
                                 headers=headers,
                                 timeout=plugin_config.preference.timeout)

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client and not client.is_closed:
                    res = await request()
                else:
                    async with httpx.AsyncClient() as client:
                        res = await request()
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    return CreateMobileCaptchaStatus(success=True), client
                elif api_result.wrong_captcha:
                    return CreateMobileCaptchaStatus(incorrect_geetest=True), client
                elif api_result.retcode == -217:
                    return CreateMobileCaptchaStatus(not_registered=True), client
                elif api_result.retcode == -103:
                    return CreateMobileCaptchaStatus(invalid_phone_number=True), client
                elif api_result.retcode == -213:
                    return CreateMobileCaptchaStatus(too_many_requests=True), client
                else:
                    return CreateMobileCaptchaStatus(), client
    except tenacity.RetryError as e:
        if client:
            await client.aclose()
        if is_incorrect_return(e):
            logger.exception("发送短信验证码 - 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return CreateMobileCaptchaStatus(incorrect_return=True), client
        else:
            logger.exception("发送短信验证码 - 请求失败")
            return CreateMobileCaptchaStatus(network_error=True), None


async def get_login_ticket_by_captcha(phone_number: str,
                                      captcha: int,
                                      device_id: str = None,
                                      client: Optional[httpx.AsyncClient] = None,
                                      retry: bool = True) -> \
        Tuple[
            GetCookieStatus, Optional[BBSCookies]]:
    """
    通过短信验证码获取 login_ticket

    :param phone_number: 手机号
    :param captcha: 短信验证码
    :param device_id: 设备ID
    :param client: httpx.AsyncClient 连接
    :param retry: 是否允许重试
    """

    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = device_id or generate_device_id()
    params = {
        "mobile": phone_number,
        "mobile_captcha": captcha,
        "source": "user.mihoyo.com",
        "t": round(time.time() * 1000),
    }
    encoded_params = urlencode(params)

    async def request():
        """
        发送请求的闭包函数
        """
        return await client.post(URL_LOGIN_TICKET_BY_CAPTCHA,
                                 headers=headers,
                                 content=encoded_params,
                                 timeout=plugin_config.preference.timeout
                                 )

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client is not None:
                    res = await request()
                else:
                    async with httpx.AsyncClient() as client:
                        res = await request()
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    cookies = BBSCookies.model_validate(dict_from_cookiejar(
                        res.cookies.jar))
                    if not cookies.login_ticket:
                        return GetCookieStatus(missing_login_ticket=True), None
                    else:
                        if client:
                            await client.aclose()
                        return GetCookieStatus(success=True), cookies
                elif api_result.wrong_captcha:
                    logger.info(
                        "通过短信验证码获取 login_ticket - 验证码错误，但你可以再次尝试登录")
                    return GetCookieStatus(incorrect_captcha=True), None
                else:
                    raise IncorrectReturn
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"通过短信验证码获取 login_ticket: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过短信验证码获取 login_ticket: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def get_multi_token_by_login_ticket(cookies: BBSCookies, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
    """
    通过 login_ticket 获取 `stoken 和 ltoken

    :param cookies: 米游社Cookies，需要包含 login_ticket 和 bbs_uid
    :param retry: 是否允许重试
    """
    if not cookies.login_ticket:
        return GetCookieStatus(missing_login_ticket=True), None
    elif not cookies.bbs_uid:
        return GetCookieStatus(missing_bbs_uid=True), None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(
                        URL_MULTI_TOKEN_BY_LOGIN_TICKET.format(cookies.login_ticket, cookies.bbs_uid),
                        headers=HEADERS_API_TAKUMI_PC,
                        timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    logger.warning(f"通过 login_ticket 获取 stoken: 登录失效")
                    return GetCookieStatus(login_expired=True), None
                else:
                    cookies.stoken = list(filter(
                        lambda x: x["name"] == "stoken", api_result.data["list"]))[0]["token"]
                    cookies.ltoken = list(filter(
                        lambda x: x["name"] == "ltoken", api_result.data["list"]))[0]["token"]
                    return GetCookieStatus(success=True), cookies
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"通过 login_ticket 获取 stoken: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过 login_ticket 获取 stoken: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def get_cookie_token_by_captcha(phone_number: str, captcha: int, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
    """
    通过短信验证码获取 cookie_token

    :param phone_number: 手机号
    :param captcha: 验证码
    :param retry: 是否允许重试
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_COOKIE_TOKEN_BY_CAPTCHA,
                                            headers=HEADERS_API_TAKUMI_PC,
                                            json={
                                                "is_bh2": False,
                                                "mobile": phone_number,
                                                "captcha": str(captcha),
                                                "action_type": "login",
                                                "token_type": 6
                                            },
                                            timeout=plugin_config.preference.timeout
                                            )
                api_result = ApiResultHandler(res.json())
                if api_result.wrong_captcha:
                    logger.info(f"登录米哈游账号 - 验证码错误")
                    return GetCookieStatus(incorrect_captcha=True), None
                else:
                    cookies = BBSCookies.model_validate(dict_from_cookiejar(res.cookies.jar))
                    if not cookies.cookie_token:
                        return GetCookieStatus(missing_cookie_token=True), None
                    elif not cookies.bbs_uid:
                        return GetCookieStatus(missing_bbs_uid=True), None
                    else:
                        return GetCookieStatus(success=True), cookies
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"通过短信验证码获取 cookie_token: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过短信验证码获取 cookie_token: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def get_login_ticket_by_password(account: str, password: str, mmt_data: MmtData, geetest_result: GeetestResult,
                                       retry: bool = True) -> Tuple[GetCookieStatus, Optional[BBSCookies]]:
    """
    使用密码登录获取login_ticket

    :param account: 账号
    :param password: 密码
    :param mmt_data: GEETEST验证任务数据
    :param geetest_result: GEETEST验证结果数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = generate_device_id()
    params = {
        "account": account,
        "password": password,
        "is_crypto": False,
        "mmt_key": mmt_data.mmt_key,
        "geetest_challenge": mmt_data.challenge,
        "geetest_validate": geetest_result.validate,
        "geetest_seccode": geetest_result.seccode,
        "source": "user.mihoyo.com",
        "t": round(time.time() * 1000)
    }
    encoded_params = urlencode(params)
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_LOGIN_TICKET_BY_PASSWORD,
                        content=encoded_params,
                        headers=headers,
                        timeout=plugin_config.preference.timeout
                    )
                cookies = BBSCookies.model_validate(dict_from_cookiejar(res.cookies.jar))
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    return GetCookieStatus(success=True), cookies
                elif api_result.wrong_captcha:
                    logger.warning(f"使用密码登录获取login_ticket - 图片验证码失败")
                    return GetCookieStatus(incorrect_captcha=True), None
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"使用密码登录获取login_ticket - 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("使用密码登录获取login_ticket - 请求失败")
            return GetCookieStatus(network_error=True), None


async def get_cookie_token_by_stoken(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
    """
    通过 stoken_v2 获取 cookie_token

    :param cookies: 米游社Cookies，需要包含 stoken_v2 和 mid
    :param device_id: X_RPC_DEVICE_ID
    :param retry: 是否允许重试
    """
    headers = HEADERS_PASSPORT_API.copy()
    headers["x-rpc-device_id"] = device_id if device_id else generate_device_id()
    if not cookies.stoken_v2:
        return GetCookieStatus(missing_stoken_v2=True), None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(
                        URL_COOKIE_TOKEN_BY_STOKEN,
                        cookies=cookies.dict(v2_stoken=True, cookie_type=True),
                        headers=headers,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    cookies.cookie_token = api_result.data["cookie_token"]
                    if not cookies.bbs_uid:
                        cookies.bbs_uid = api_result.data["uid"]
                    return GetCookieStatus(success=True), cookies
                elif api_result.login_expired:
                    logger.warning("通过 stoken 获取 cookie_token: 登录失效")
                    return GetCookieStatus(login_expired=True), None
                else:
                    raise IncorrectReturn

    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("通过 stoken 获取 cookie_token: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken 获取 cookie_token: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def get_stoken_v2_by_v1(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
    """
    通过 stoken_v1 获取 stoken_v2 以及 mid

    :param cookies: 米游社Cookies，需要包含 stoken_v1
    :param device_id: X_RPC_DEVICE_ID
    :param retry: 是否允许重试
    """
    headers = HEADERS_PASSPORT_API.copy()
    headers["x-rpc-device_id"] = device_id or generate_device_id()
    headers.setdefault("x-rpc-aigis", "")
    headers.setdefault("x-rpc-app_id", "bll8iq97cem8")

    if not cookies.stoken_v1:
        return GetCookieStatus(missing_stoken_v1=True), None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    headers.setdefault("DS", generate_ds(salt=plugin_env.salt_config.SALT_PROD))
                    res = await client.post(
                        URL_STOKEN_V2_BY_V1,
                        cookies={"stoken": cookies.stoken_v1, "stuid": cookies.bbs_uid},
                        headers=headers,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    cookies.stoken_v2 = api_result.data["token"]["token"]
                    cookies.mid = api_result.data["user_info"]["mid"]
                    if not cookies.bbs_uid:
                        cookies.bbs_uid = api_result.data["user_info"]["aid"]
                    return GetCookieStatus(success=True), cookies
                elif api_result.login_expired:
                    logger.warning(f"通过 stoken_v1 获取 stoken_v2: 登录失效")
                    return GetCookieStatus(login_expired=True), None
                else:
                    raise IncorrectReturn

    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("通过 stoken_v1 获取 stoken_v2: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken_v1 获取 stoken_v2: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def get_ltoken_by_stoken(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
    """
    通过 stoken_v2 和 mid 获取 ltoken

    :param cookies: 米游社Cookies，需要包含 stoken_v2 和 mid
    :param device_id: X_RPC_DEVICE_ID
    :param retry: 是否允许重试
    """
    headers = HEADERS_PASSPORT_API.copy()
    headers["x-rpc-device_id"] = device_id if device_id else generate_device_id()
    if not cookies.stoken_v2:
        return GetCookieStatus(missing_stoken_v2=True), None
    if not cookies.mid:
        return GetCookieStatus(missing_mid=True), None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(
                        URL_LTOKEN_BY_STOKEN,
                        cookies=cookies.dict(v2_stoken=True, cookie_type=True),
                        headers=headers,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.success:
                    cookies.ltoken = api_result.data["ltoken"]
                    return GetCookieStatus(success=True), cookies
                elif api_result.login_expired:
                    logger.warning("通过 stoken 获取 ltoken: 登录失效")
                    return GetCookieStatus(login_expired=True), None
                else:
                    raise IncorrectReturn

    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("通过 stoken 获取 ltoken: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken 获取 ltoken: 网络请求失败")
            return GetCookieStatus(network_error=True), None


async def create_verification(
        account: UserAccount = None,
        retry: bool = True
) -> Tuple[BaseApiStatus, Optional[MmtData]]:
    """
    创建人机验证任务 - 一般用于米游社讨论区签到
    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_BBS_API.copy()
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                device_id = account.device_id_ios if account else generate_device_id()
                headers["x-rpc-device_id"] = device_id
                headers["x-rpc-device_fp"] = account.device_fp if account and account.device_fp else \
                    generate_fp_locally()
                headers["DS"] = generate_ds()
                async with httpx.AsyncClient() as client:
                    res = await client.get(
                        URL_CREATE_VERIFICATION,
                        headers=headers,
                        cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), MmtData.model_validate(api_result.data)
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("创建人机验证任务(create_verification) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("创建人机验证任务(create_verification) - 请求失败")
            return BaseApiStatus(network_error=True), None


async def verify_verification(
        mmt_data: MmtData,
        geetest_result: GeetestResult,
        account: UserAccount = None,
        retry: bool = True
) -> BaseApiStatus:
    """
    提交人机验证结果 - 一般用于米游社讨论区签到
    :param mmt_data: 极验验证任务数据
    :param geetest_result: 极验验证结果
    :param account: 用户账户数据
    :param retry: 是否允许重试
    """
    headers = HEADERS_BBS_API.copy()
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                content = {
                    "geetest_seccode": geetest_result.seccode,
                    "geetest_challenge": mmt_data.challenge,
                    "geetest_validate": geetest_result.validate,
                }
                device_id = account.device_id_ios if account else generate_device_id()
                headers["x-rpc-device_id"] = device_id
                headers["x-rpc-device_fp"] = account.device_fp if account and account.device_fp else \
                    generate_fp_locally()
                headers["DS"] = generate_ds()
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_VERIFY_VERIFICATION,
                        headers=headers,
                        cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                        json=content,
                        timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.retcode == 0:
                    return BaseApiStatus(success=True)
                else:
                    return BaseApiStatus()
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("验证人机验证结果(verify_verification) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True)
        else:
            logger.exception("验证人机验证结果(verify_verification) - 请求失败")
            return BaseApiStatus(network_error=True)


async def fetch_game_token_qrcode(
        device_id: str,
        app_id: str,
        retry: bool = True
) -> Tuple[BaseApiStatus, Optional[Tuple[str, str]]]:
    """
    获取米游社扫码登录（GameToken）二维码
    :param device_id: 设备ID
    :param app_id: 登录的应用标识符
    :param retry: 是否允许重试
    :return 其中 ``Tuple[str, str]`` 为二维码URL和用于查询二维码扫描状态的 ``token``
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                content = {
                    "app_id": app_id,
                    "device": device_id,
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_FETCH_GAME_TOKEN_QRCODE,
                        json=content,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.retcode == 0:
                    qrcode_url = api_result.data["url"]
                    url = urlparse(qrcode_url)
                    return BaseApiStatus(success=True), (qrcode_url, parse_qs(url.query)["ticket"][0])
                else:
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(), None
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取米游社扫码登录(fetch_game_token_qrcode) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("获取米游社扫码登录(fetch_game_token_qrcode) - 请求失败")
            return BaseApiStatus(network_error=True), None


async def query_game_token_qrcode(
        ticket: str,
        device_id: str,
        app_id: str = "1",
        retry: bool = True
) -> Tuple[QueryGameTokenQrCodeStatus, Optional[Tuple[str, str]]]:
    """
    查询米游社扫码登录（GameToken）二维码扫描状态
    :param ticket: 生成二维码时返回的 URL 参数中 ``ticket`` 字段的值
    :param device_id: 设备ID
    :param app_id: 登录的应用标识符
    :param retry: 是否允许重试
    :return 其中 ``Tuple[str, str]`` 为米游社账号ID和 GameToken
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                content = {
                    "app_id": app_id,
                    "device": device_id,
                    "ticket": ticket
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_QUERY_GAME_TOKEN_QRCODE,
                        json=content,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.retcode == 0:
                    if api_result.data["stat"] == "Init":
                        return QueryGameTokenQrCodeStatus(qrcode_init=True), None
                    elif api_result.data["stat"] == "Scanned":
                        return QueryGameTokenQrCodeStatus(qrcode_scanned=True), None
                    else:
                        payload_raw = api_result.data["payload"]["raw"]
                        parsed_payload: Dict[str, str] = json.loads(payload_raw)
                        return QueryGameTokenQrCodeStatus(success=True), (
                            parsed_payload["uid"],
                            parsed_payload["token"]
                        )
                elif api_result.retcode == -106:
                    return QueryGameTokenQrCodeStatus(qrcode_expired=True), None
                else:
                    return QueryGameTokenQrCodeStatus(), None
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("查询米游社扫码登录(query_game_token_qrcode) - 服务器没有正确返回")
            return QueryGameTokenQrCodeStatus(incorrect_return=True), None
        else:
            logger.exception("查询米游社扫码登录(query_game_token_qrcode) - 请求失败")
            return QueryGameTokenQrCodeStatus(network_error=True), None


async def get_token_by_game_token(
        bbs_uid: str,
        game_token: str,
        retry: bool = True
) -> Tuple[BaseApiStatus, Optional[BBSCookies]]:
    """
    通过 GameToken 获取 STokenV2 和 mid
    :param bbs_uid: 米游社账号 UID
    :param game_token: 有效的 GameToken
    :param retry: 是否允许重试
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                content = {
                    "account_id": int(bbs_uid),
                    "game_token": game_token
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_GET_TOKEN_BY_GAME_TOKEN,
                        headers={"x-rpc-app_id": "bll8iq97cem8"},
                        json=content,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.retcode == 0:
                    stoken_v2 = api_result.data["token"]["token"]
                    mid = api_result.data["user_info"]["mid"]
                    return BaseApiStatus(success=True), BBSCookies(stoken_v2=stoken_v2, mid=mid)
                else:
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(), None
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("通过 GameToken 获取 SToken(get_token_by_game_token) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("通过 GameToken 获取 SToken(get_token_by_game_token) - 请求失败")
            return BaseApiStatus(network_error=True), None


async def get_cookie_token_by_game_token(
        bbs_uid: str,
        game_token: str,
        retry: bool = True
) -> Tuple[BaseApiStatus, Optional[BBSCookies]]:
    """
    通过 GameToken 获取 CookieToken
    :param bbs_uid: 米游社账号 UID
    :param game_token: 有效的 GameToken
    :param retry: 是否允许重试
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                content = {
                    "account_id": int(bbs_uid),
                    "game_token": game_token
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_GET_COOKIE_TOKEN_BY_GAME_TOKEN,
                        headers={"x-rpc-app_id": "bll8iq97cem8"},
                        json=content,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.retcode == 0:
                    cookie_token = api_result.data["token"]["token"]
                    return BaseApiStatus(success=True), BBSCookies(cookie_token=cookie_token)
                else:
                    logger.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(), None
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("通过 GameToken 获取 CookieToken(get_cookie_token_by_game_token) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("通过 GameToken 获取 CookieToken(get_cookie_token_by_game_token) - 请求失败")
            return BaseApiStatus(network_error=True), None
