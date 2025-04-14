

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
#APP_KEY = '67fcc47ee4b0ab0ae18029c1'
#APP_SECRET = 'xShqoM-xR2n5uo0v5WKajRJQ4mLXEvtBQcbyclXxTM62F5QacpUqqRYcLSxZLJDU'
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")