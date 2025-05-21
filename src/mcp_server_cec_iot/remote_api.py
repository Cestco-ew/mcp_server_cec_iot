import logging
from typing import Dict, Any, List, Optional

import httpx

from config import DOMAIN, AUTH


logger = logging.getLogger("cec_iot_mcp_server_server_remote_api")

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




async def get_access_token(app_key: str,app_secret:str) -> Optional[str]:
    url = AUTH
    method = "GET"
    url_params = {
        "appKey": app_key,
        "appSecret": app_secret
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
