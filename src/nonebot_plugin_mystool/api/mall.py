
async def good_exchange(plan: ExchangePlan) -> Tuple[ExchangeStatus, Optional[ExchangeResult]]:
    """
    执行米游币商品兑换

    :param plan: 兑换计划
    """
    headers = HEADERS_EXCHANGE.copy()
    headers["x-rpc-device_id"] = plan.account.device_id_ios
    headers["x-rpc-device_fp"] = plan.account.device_fp or generate_fp_locally()
    content = {
        "app_id": 1,
        "point_sn": "myb",
        "goods_id": plan.good.goods_id,
        "exchange_num": 1
    }
    if plan.address is not None:
        content.setdefault("address_id", plan.address.id)
    if plan.game_record is not None:
        content.setdefault("uid", plan.game_record.game_role_id)
        # 例: cn_gf01
        content.setdefault("region", plan.game_record.region)
        # 例: hk4e_cn
        content.setdefault("game_biz", plan.good.game_biz)
    start_time = 0
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            res = await client.post(
                URL_EXCHANGE, headers=headers, json=content,
                cookies=plan.account.cookies.dict(cookie_type=True),
                timeout=plugin_config.preference.timeout)
        api_result = ApiResultHandler(res.json())
        if api_result.login_expired:
            logger.info(
                f"米游币商品兑换 - 执行兑换: 用户 {plan.account.display_name} 登录失效 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(login_expired=True), None
        if api_result.success:
            logger.info(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 兑换成功！可以自行确认 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(success=True), ExchangeResult(result=True, return_data=res.json(), plan=plan)
        else:
            logger.info(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 兑换失败，可以自行确认 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(success=True), ExchangeResult(result=False, return_data=res.json(), plan=plan)
    except Exception as e:
        if is_incorrect_return(e):
            logger.error(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 服务器没有正确返回 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(incorrect_return=True), None
        else:
            logger.exception(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 请求失败 - 请求发送时间: {start_time}")
            return ExchangeStatus(network_error=True), None


def good_exchange_sync(plan: ExchangePlan) -> Tuple[ExchangeStatus, Optional[ExchangeResult]]:
    """
    执行米游币商品兑换

    :param plan: 兑换计划
    """
    headers = HEADERS_EXCHANGE.copy()
    headers["x-rpc-device_id"] = plan.account.device_id_ios
    headers["x-rpc-device_fp"] = plan.account.device_fp or generate_fp_locally()
    content = {
        "app_id": 1,
        "point_sn": "myb",
        "goods_id": plan.good.goods_id,
        "exchange_num": 1
    }
    if plan.address is not None:
        content.setdefault("address_id", plan.address.id)
    if plan.game_record is not None:
        content.setdefault("uid", plan.game_record.game_role_id)
        # 例: cn_gf01
        content.setdefault("region", plan.game_record.region)
        # 例: hk4e_cn
        content.setdefault("game_biz", plan.good.game_biz)
    start_time = 0
    try:
        start_time = time.time()
        with httpx.Client() as client:
            res = client.post(
                URL_EXCHANGE, headers=headers, json=content,
                cookies=plan.account.cookies.dict(cookie_type=True),
                timeout=plugin_config.preference.timeout)
        api_result = ApiResultHandler(res.json())
        if api_result.login_expired:
            logger.info(
                f"米游币商品兑换 - 执行兑换: 用户 {plan.account.display_name} 登录失效 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(login_expired=True), None
        if api_result.success:
            logger.info(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 兑换成功！可以自行确认 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(success=True), ExchangeResult(result=True, return_data=res.json(), plan=plan)
        else:
            logger.info(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 兑换失败，可以自行确认 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(success=True), ExchangeResult(result=False, return_data=res.json(), plan=plan)
    except Exception as e:
        if is_incorrect_return(e):
            logger.error(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 服务器没有正确返回 - 请求发送时间: {start_time}")
            logger.debug(f"网络请求返回: {res.text}")
            return ExchangeStatus(incorrect_return=True), None
        else:
            logger.exception(
                f"米游币商品兑换: 用户 {plan.account.display_name} 商品 {plan.good.goods_id} 请求失败 - 请求发送时间: {start_time}")
            return ExchangeStatus(network_error=True), None
