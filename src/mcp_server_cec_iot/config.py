

import os

DOMAIN = "https://oapi.sh-cec.com/"
AUTH = "auth/get_token"

#通用国标摄像头的品牌型号
CAMERA_BRAND_MODEL_ID = "1690200341562109953"
CAMERA_PLAY_CODE = ["hlsUrl","ws_flv","https_flv","flvUrl"]
CAMERA_SCREENSHOT_CODE = ["cameraScreenshot"]

# 流媒体id
MEDIA_ID = "1"
# 获取环境变量
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")