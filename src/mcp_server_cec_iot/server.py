import json
import secrets
import string
from typing import Any, Dict, Optional, List
from mcp.server.fastmcp import FastMCP
import logging

import httpx

from config import *

logger = logging.getLogger("cec_iot_mcp_server_server")

# 初始化FastMCP服务器
mcp = FastMCP("mcp_server_cec_iot")


@mcp.tool()
async def get_area_info() -> List[Dict]:
    """
    ## 查询全量区域列表
    以下场景需要调用此函数
    1. 当用户提出获取区域信息的需求时，使用工具获取所有区域信息。
    2. 分析获取到的 areaName，梳理出区域的上下级关系。
    返回数据
    将区域信息以 markdown 表格的形式展示，表格应包含区域名称、上级区域等必要信息。
    """
    access_token = await get_access_token()
    return await get_all_area_info(access_token)


@mcp.tool()
async def list_device_base_info(area_ids:List[str],name:str = "") -> List[Dict]:
    """
    ## 查询设备基本信息（id、名称、序列号、区域、在离线）
    ### 入参
    1. area_ids 区域id列表，非必填，需要通过“查询全量区域列表”tool获取到目标区域列表
    2. name 设备名称
    ## 调用示例，查询19楼的所有设备：
    1. 先判断用户输入是否带有区域
    2. 如果有，则通过“查询全量区域列表”tool，获取全量区域信息，并获取出和“19楼”相关的区域id列表，包含19楼-房间1、19楼-房间2。
    3. 将区域id列表，作为area_ids 入参

    ### 返回数据
    [{"id":"设备id","name":"设备名称","brandModelId":"品牌型号id","sn":"序列号","areaId":"区域id","areaName":"区域名称","status":"在离线枚举值","statusName":"在离线状态描述"}]
    """
    access_token = await get_access_token()
    device_list = await get_device_base_info(access_token,area_ids,name)
    result = [
        {
            "id": device["id"],
            "name": device["name"],
            "brandModelId": device["brandModelId"],
            "sn": device["sn"],
            "areaId": device["areaId"],
            "areaName": device["areaName"],
            "status": status,
            "statusName": (
                "在线" if status == '0' else
                "离线" if status in ('-1', '1') else
                "未注册" if status == '-2' else
                "未知状态"
            )
        }
        for device in device_list
        if all(key in device for key in ("id", "name", "status"))
        for status in [device["status"]]  # 提取status并确保类型一致
    ]
    return result

@mcp.tool()
async def add_camera(name: str = "",sn: str ="",area_code: str =""):
    """新增摄像头
     ## 调用示例，查询19楼前台新增一个摄像头：
    1. 先判断用户输入是否带有区域
    2. 如果有，则通过“查询全量区域列表”tool，获取全量区域信息，并获取出和“19楼前台”相关的区域code。
    3. 将区域code，作为area_code 入参
    ### 入参
    1. name 摄像头名称，非必填，如果用户没指定，则不需要填
    2. sn 摄像头序列号，非必填，如果用户没指定，则不需要填
    3. area_code 区域编码，非必填，如果用户没有输入区域信息，则不需要填

    ### 返回GB/T - 28181配置
    1. 新增摄像头成功后，返回GB/T - 28181配置。
    2. 如果返回结果不是GB/T - 28181配置，则判定新增异常。
    3. 返回结果以可读性较好的markdown形式呈现给用户，
    4. 提示用户去摄像头管理后台录入GB/T - 28181信息。
    """
    try:
        access_token = await get_access_token()
        # 序列号不传则随机生成
        if not sn:
            sn = generate_random_string()
        if not name:
            name = "摄像头" + "-" + sn
        link_attr: List[Dict[str, str]] = [
            {"attributeCode": "mediaConfig", "value": "GB/T-28181"}
        ]
        add_result = await add_device(access_token,name,sn,CAMERA_BRAND_MODEL_ID,area_code,MEDIA_ID,link_attr)
        device_id = add_result.get("data")
        # 如果id 为空，则直接返回
        if not device_id:
            return add_result
        media_config_collect_data = await get_one_collect_data(access_token, device_id, "mediaConfig")
        if not media_config_collect_data:
            return None
        # 获取 extData 数据
        media_config_value = media_config_collect_data.get('value')
        media_config_json = json.loads(media_config_value)
        ext_data = media_config_json.get("extData")
        return ext_data
    except Exception as e:
        return f"Error occurred: {str(e)}"

def generate_random_string():
    # 定义所有可能的字符（大写字母和数字）
    all_characters = string.ascii_uppercase + string.digits
    # 从所有可能的字符中随机选择 12 个字符并拼接成字符串
    random_string = ''.join(secrets.choice(all_characters) for i in range(12))
    return random_string



@mcp.tool()
async def get_play_url(area_ids:List[str]):
    """
    获取摄像头实时流播放地址（HLS/RTMP格式）
    ### 参数说明
    - area_ids：区域ID列表，可以通过“查询全量区域列表”tool，获取全量区域信息，并获取出区域id列表。
    ### 示例
    查询19楼摄像头播放地址：先查询出19楼，19楼-房间1，19楼-房间2 区域id列表，再查询播放地址
    ### 返回结果需要转成markdown表格
    """
    access_token = await get_access_token()
    device_list = await list_device_base_info(area_ids,'摄像头')
    device_ids = [
        device.get("id")
        for device in device_list
    ]
    device_id_codes = {device_id: CAMERA_PLAY_CODE for device_id in device_ids}
    resp = await get_collect_data(access_token, device_id_codes)
    return resp

@mcp.tool()
async def get_camera_screenshot(area_ids:List[str]):
    """
    获取摄像头当前截图地址
    ### 参数说明
    - area_ids：区域ID列表，可以通过“查询全量区域列表”tool，获取全量区域信息，并获取出区域id列表。
    ### 实例
    查询19楼摄像头当前图像：先查询出19楼，19楼-房间1，19楼-房间2 区域id列表，再查询播放地址
    ### 返回结果需要转成markdown表格
    """
    access_token = await get_access_token()
    device_list = await list_device_base_info(area_ids, '摄像头')
    device_ids = [
        device.get("id")
        for device in device_list
    ]
    device_id_codes = {device_id: CAMERA_SCREENSHOT_CODE for device_id in device_ids}
    resp = await get_collect_data(access_token, device_id_codes)
    result = [
        {
            "id":collect_data.get("id",""),
            "url":DOMAIN + collect_data.get("value","")
        }
        for collect_data in resp if collect_data.get("value", "")
    ]
    return result



@mcp.tool()
async def get_asset_model_tool(brand_model_ids:List[str]):
    """
    获取品牌型号物模型信息，获取设备的属性信息，属性信息用于控制以及当前采集值查询
    ### 参数说明
    brand_model_ids：品牌型号id列表，可以通过`list_device_base_info` 工具查询符合条件的品牌型号ID

    ### 返回格式
    [{"brandModelId":"","code":"","alias":"","choseEnums":[{"enumCode": "1", "enumName": "开"}, {"enumCode": "0", "enumName": "关"}]}]
    """
    access_token = await get_access_token()
    return await get_asset_model(access_token,brand_model_ids)

@mcp.tool()
async def control_device_tool(controlInstructions:List[Dict[str,Any]]):
    """
    批量控制设备
    入参说明：
    入参格式：[{"assetId":"设备id","code":"属性编码","value":"控制属性值"}]，
    入参格式的数据来源场景示例：
    关闭19楼的所有灯，(1). 通过`获取设备基本信息`Tool 获取到设备列表，(2). 获取设备列表的brandModelId列表，(3). 通过`获取品牌型号物模型信息`Tool 获取物模型属性信息，(4). 组装入参指令
    返回说明
    将结果转化为可读的markdown形式
    """
    access_token = await get_access_token()
    control_result = await batch_control_device(access_token,controlInstructions)
    # 提取并转换数据
    result_list = [{
        'assetId': item['resultData']['assetId'],
        'code': item['resultData']['code'],
        'value': item['resultData']['value'],
        'resultCode': item['result']['code'],
        'resultmessage': item['result']['message']
    } for item in control_result['controlResults']]
    return result_list

@mcp.tool()
async def get_collect_data_by_id_codes_tool(device_ids:List[str],codes:List[str]):
    """
    获取设备的采集值（不包含在离线），
    入参说明：
    device_ids：设备id列表，通过`获取设备基本信息`Tool 获取到设备id列表，
    codes：属性编码列表，参数来源：(1).通过`获取设备基本信息`Tool 获取到设备列表，(2). 获取设备列表的brandModelId列表，(3). 通过`获取品牌型号物模型信息`Tool 获取物模型属性信息
    示例：
    19楼有几个灯开着：(1).通过`获取设备基本信息`Tool 获取到19楼的所有灯的设备，并获取ids,brandModelIds。(2). 通过`获取品牌型号物模型信息`Tool 获取包含了`开`枚举值的属性编码列表
    返回说明：
    将获取到的设备采集值结果转化为易读的Markdown形式
    """
    if not device_ids or not codes:
        return None
    device_id_codes = {device_id: codes for device_id in device_ids}
    access_token = await get_access_token()
    return await get_collect_data(access_token, device_id_codes)


async def get_access_token() -> Optional[str]:
    url = AUTH
    method = "GET"
    url_params = {
        "appKey": APP_KEY,
        "appSecret": APP_SECRET
    }

    response = await make_cec_request(url, method, url_params)

    if not response or not response.get("success"):
        error_msg = response.get("message", {}).get("message") if response else "空响应"
        logger.error(f"获取access_token失败: {error_msg}")
        return None

    return response.get("data", {}).get("access_token")


async def make_cec_request(
        url: str,
        method: str,
        url_params: Optional[Dict[str, str]] = None,
        body_params: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    full_url = f"{DOMAIN}{url}"

    # 合并请求参数
    merged_params = url_params.copy() if url_params else {}
    if access_token:
        merged_params["access_token"] = access_token

    try:
        async with httpx.AsyncClient() as client:
            # 根据请求方法处理
            if method.upper() == "GET":
                response = await client.get(
                    full_url,
                    params=merged_params,
                    timeout=30
                )
            else:
                response = await client.request(
                    method.upper(),
                    full_url,
                    json=body_params,
                    params=merged_params,
                    timeout=30
                )
            response.encoding = 'utf-8'
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP Error [{e.response.status_code}] "
            f"{method} {url}: {e.request.url}"
        )
    except httpx.RequestError as e:
        logger.error(
            f"Network Error: {method} {url} - {str(e)}",
            exc_info=True
        )
    except Exception as e:
        logger.error(
            f"Unexpected Error: {method} {url} - {str(e)}",
            exc_info=True
        )

    return None

async def get_all_area_info(access_token: str):
    url = "cec-saas-ac-platform/V2_7_0/areaApi/list"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "fillName":"true"
        }
    }
    try:
        response = await make_cec_request(url,method,None,request_body,access_token)
        area_list = response.get("data", [])
        if not area_list:
            return None
        result = [
            {
                "id": area.get("id", ""),
                "areaName": area.get("areaName", ""),
                "code": area.get("code", "")
            }
            for area in area_list
            if 'code' in area and 'areaName' in area
        ]
        return result
    except Exception as e:
        logger.error(f"无法获取区域：{str(e)}")


async def get_28181(access_token: str):
    url = "cec-saas-ac-platform/V2_7_0/assetApi/getMediaGBT28181Config"
    method = "GET"

    response = await make_cec_request(url, method, None, None, access_token)
    return response

async def add_device(access_token: str,name: str,sn: str,brand_model_id: str,area_code: str,parent_id: str,link_attr: List[Dict[str,str]]):
    url = "cec-saas-ac-platform/V2_5_0/assetApi"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "name": name,
            "sn": sn,
            "brandModelId": brand_model_id,
            "areaCode": area_code,
            "parentId": parent_id,
            "attributes": link_attr
        }
    }
    return await make_cec_request(url,method,None,request_body,access_token)

#获取单条采集值
async def get_one_collect_data(access_token: str,device_id:str,code:str):
    url = "cec-saas-ac-platform/V3_4_1/assetApi/listCollectData"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "assetId": device_id,
            "codes": [code]
        }
    }
    response = await make_cec_request(url,method,None,request_body,access_token)
    # 检查 response 是否存在且包含所需的键
    if response and isinstance(response.get("data"), dict) and isinstance(response["data"].get("collectDataList"),
                                                                          list):
        collect_data_list = response["data"]["collectDataList"]
        if collect_data_list:
            return collect_data_list[0]
    return None

# 批量获取采集数据
async def get_collect_data(access_token: str, device_id_codes: Dict[str, List[str]]):
    url = "cec-saas-ac-platform/V3_4_1/assetApi/listCollectDataIdCodes"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "assetIdCodes": device_id_codes
        }
    }

    # 发送请求
    response = await make_cec_request(url, method, None, request_body, access_token)

    # 校验响应结构
    if not isinstance(response, dict):
        return None

    data = response.get("data", {})
    if not isinstance(data, dict):
        return None

    collect_data_list = data.get("collectDataList", [])
    if not isinstance(collect_data_list, list):
        return None

    # 过滤字段
    filtered_data = [
        {
            "id": str(item.get("id", "")),  # 强制转为字符串
            "code": str(item.get("code", "")),
            "value": str(item.get("value", ""))  # 统一转为字符串格式
        }
        for item in collect_data_list
        if isinstance(item, dict)  # 过滤非字典元素
    ]

    return filtered_data if filtered_data else None

async def get_device_base_info(access_token:str,area_ids:List[str],name:str):
    url = "cec-saas-ac-platform/V2_5_0/assetApi/list"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "name": name,
            "areaIds": area_ids,
            "needStatus":"true",
            "needDeviceInfo":"false"
        }
    }
    device_list_resp = await make_cec_request(url,method,None,request_body,access_token)
    return device_list_resp.get("data",List)

async def get_label(access_token:str):
    url = "cec-saas-ac-platform/V3_1_0/labelApi/labelList"
    method = "GET"
    result = await make_cec_request(url,method,None,None,access_token)
    return result.get("data", List)

async def get_asset_model(access_token:str,brand_model_ids:List[str]):
    url = "cec-saas-ac-platform/V3_4_1/assetModelApi/pageAssetModelAttribute"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "brandModelIds": brand_model_ids
        }
    }
    resp = await make_cec_request(url, method, None, request_body, access_token)
    result = [
        {
            "brandModelId": attr.get("brandModelId", ""),
            "code": attr.get("code", ""),
            "choseEnums": attr.get("choseEnums"),
            "alias": attr.get("alias", "")
        }
        for attr in resp.get("data",Dict[str,Any]).get("records",List)
    ]
    return result

async def batch_control_device(access_token:str,controlInstructions:List[Dict[str,Any]]):
    url = "cec-saas-ac-platform/V2_5_0/assetApi/batchControl"
    method = "POST"
    request_body: Dict[str, Any] = {
        "data": {
            "controlInstructions": controlInstructions,
            "source":"MCP Server"
        }
    }
    result = await make_cec_request(url, method, None, request_body, access_token)
    return result.get("data", List)

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')