# 使用官方Python轻量级镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到容器中（确保Dockerfile放置在SRC目录下）
COPY . .

# 暴露服务端口
EXPOSE 8080

# 启动命令（允许通过docker run传递命令行参数）
CMD ["python", "-m", "mcp_server_cec_iot.server"]