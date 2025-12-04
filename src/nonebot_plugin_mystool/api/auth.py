
import time
from typing import Tuple, Optional, Union, Dict
from urllib.parse import urlencode, urlparse, parse_qs

import httpx
import tenacity
from requests.utils import dict_from_cookiejar

from ..consts import (
    HEADERS_WEBAPI, HEADERS_API_TAKUMI_PC, HEADERS_PASSPORT_API, HEADERS_BBS_API,
    URL_REGISTRABLE, URL_CREATE_MMT, URL_CREATE_MOBILE_CAPTCHA,
    URL_LOGIN_TICKET_BY_CAPTCHA, URL_MULTI_TOKEN_BY_LOGIN_TICKET,
    URL_COOKIE_TOKEN_BY_CAPTCHA, URL_LOGIN_TICKET_BY_PASSWORD,
    URL_COOKIE_TOKEN_BY_STOKEN, URL_STOKEN_V2_BY_V1, URL_LTOKEN_BY_STOKEN,
    URL_FETCH_GAME_TOKEN_QRCODE, URL_QUERY_GAME_TOKEN_QRCODE,
    URL_GET_TOKEN_BY_GAME_TOKEN, URL_GET_COOKIE_TOKEN_BY_GAME_TOKEN
)
from ..schema import (
    BaseApiStatus, MmtData, GeetestResult, CreateMobileCaptchaStatus,
    GetCookieStatus, BBSCookies, GeetestResultV4, QueryGameTokenQrCodeStatus
)
from ..utils import (
    logger, generate_device_id, get_async_retry, generate_ds, IncorrectReturn
)
from ..config import plugin_config
from .base import ApiResultHandler, is_incorrect_return

async def check_registrable(phone_number: int, keep_client: bool = False, retry: bool = True) -> Tuple[
    BaseApiStatus, Optional[bool], str, Optional[httpx.AsyncClient]
]:
    headers = HEADERS_WEBAPI.copy()
    device_id = generate_device_id()
    headers["x-rpc-device_id"] = device_id

    async def request(client):
        time_now = round(time.time() * 1000)
        return await client.get(URL_REGISTRABLE.format(mobile=phone_number, t=time_now),
                                headers=headers, timeout=plugin_config.preference.timeout)

    client = None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if keep_client:
                    client = httpx.AsyncClient()
                else:
                    async with httpx.AsyncClient() as client_ctx:
                        client = client_ctx # This logic in original was slightly different but intention is clear
                        # Actually original: if keep_client: client = httpx.AsyncClient() else: async with ...
                        # The original code had a bug/weirdness where it assigned client inside async with but then called request() outside?
                        # No, inside async with it called request().
                        pass
                
                # Let's rewrite properly
                if keep_client:
                    if not client: client = httpx.AsyncClient()
                    res = await request(client)
                else:
                    async with httpx.AsyncClient() as c:
                        res = await request(c)
                
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), bool(api_result.data["is_registable"]), device_id, client
    except tenacity.RetryError as e:
        if client and keep_client:
            await client.aclose()
        if is_incorrect_return(e):
            logger.exception(f"检查用户 {phone_number} 是否可以注册 - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None, device_id, client
        else:
            logger.exception(f"检查用户 {phone_number} 是否可以注册 - 请求失败")
            return BaseApiStatus(network_error=True), None, device_id, None

async def create_mmt(client: Optional[httpx.AsyncClient] = None,
                     use_v4: bool = True,
                     device_id: str = None,
                     retry: bool = True) -> Tuple[
    BaseApiStatus, Optional[MmtData], str, Optional[httpx.AsyncClient]
]:
    headers = HEADERS_WEBAPI.copy()
    device_id = device_id or generate_device_id()
    headers["x-rpc-device_id"] = device_id
    if use_v4:
        headers.setdefault("x-rpc-source", "accountWebsite")

    async def request(c):
        time_now = round(time.time() * 1000)
        return await c.get(URL_CREATE_MMT.format(now=time_now, t=time_now),
                                headers=headers, timeout=plugin_config.preference.timeout)

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client:
                    res = await request(client)
                else:
                    async with httpx.AsyncClient() as c:
                        res = await request(c)
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), MmtData.model_validate(api_result.data["mmt_data"]), device_id, client
    except tenacity.RetryError as e:
        if client and not client.is_closed:
            await client.aclose()
        if is_incorrect_return(e):
            logger.exception("获取短信验证-人机验证任务(create_mmt) - 服务器没有正确返回")
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

    async def request(c):
        return await c.post(URL_CREATE_MOBILE_CAPTCHA,
                                 params=content,
                                 headers=headers,
                                 timeout=plugin_config.preference.timeout)

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client and not client.is_closed:
                    res = await request(client)
                else:
                    async with httpx.AsyncClient() as c:
                        res = await request(c)
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
            return CreateMobileCaptchaStatus(incorrect_return=True), client
        else:
            logger.exception("发送短信验证码 - 请求失败")
            return CreateMobileCaptchaStatus(network_error=True), None

async def get_login_ticket_by_captcha(phone_number: str,
                                      captcha: int,
                                      device_id: str = None,
                                      client: Optional[httpx.AsyncClient] = None,
                                      retry: bool = True) -> \
        Tuple[GetCookieStatus, Optional[BBSCookies]]:
    headers = HEADERS_WEBAPI.copy()
    headers["x-rpc-device_id"] = device_id or generate_device_id()
    params = {
        "mobile": phone_number,
        "mobile_captcha": captcha,
        "source": "user.mihoyo.com",
        "t": round(time.time() * 1000),
    }
    encoded_params = urlencode(params)

    async def request(c):
        return await c.post(URL_LOGIN_TICKET_BY_CAPTCHA,
                                 headers=headers,
                                 content=encoded_params,
                                 timeout=plugin_config.preference.timeout
                                 )

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                if client is not None:
                    res = await request(client)
                else:
                    async with httpx.AsyncClient() as c:
                        res = await request(c)
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
                    logger.info("通过短信验证码获取 login_ticket - 验证码错误，但你可以再次尝试登录")
                    return GetCookieStatus(incorrect_captcha=True), None
                else:
                    raise IncorrectReturn
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"通过短信验证码获取 login_ticket: 服务器没有正确返回")
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过短信验证码获取 login_ticket: 请求失败")
            return GetCookieStatus(network_error=True), None

async def get_multi_token_by_login_ticket(cookies: BBSCookies, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过 login_ticket 获取 stoken: 网络请求失败")
            return GetCookieStatus(network_error=True), None

async def get_cookie_token_by_captcha(phone_number: str, captcha: int, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception(f"通过短信验证码获取 cookie_token: 网络请求失败")
            return GetCookieStatus(network_error=True), None

async def get_login_ticket_by_password(account: str, password: str, mmt_data: MmtData, geetest_result: GeetestResult,
                                       retry: bool = True) -> Tuple[GetCookieStatus, Optional[BBSCookies]]:
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("使用密码登录获取login_ticket - 请求失败")
            return GetCookieStatus(network_error=True), None

async def get_cookie_token_by_stoken(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken 获取 cookie_token: 网络请求失败")
            return GetCookieStatus(network_error=True), None

async def get_stoken_v2_by_v1(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
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
                    headers.setdefault("DS", generate_ds(salt=plugin_config.salt_config.SALT_PROD))
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken_v1 获取 stoken_v2: 网络请求失败")
            return GetCookieStatus(network_error=True), None

async def get_ltoken_by_stoken(cookies: BBSCookies, device_id: str = None, retry: bool = True) -> Tuple[
    GetCookieStatus,
    Optional[BBSCookies]
]:
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
            return GetCookieStatus(incorrect_return=True), None
        else:
            logger.exception("通过 stoken 获取 ltoken: 网络请求失败")
            return GetCookieStatus(network_error=True), None

async def fetch_game_token_qrcode(
        device_id: str,
        app_id: str,
        retry: bool = True
) -> Tuple[BaseApiStatus, Optional[Tuple[str, str]]]:
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
                        import json
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
