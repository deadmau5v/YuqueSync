FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装redis客户端
RUN apt-get update && apt-get install -y redis-tools

# 复制项目文件到容器中
COPY *.py /app/
COPY config.yaml /app/

# 安装Python依赖
RUN pip install redis pyyaml aiohttp asyncio requests

# 创建数据目录
RUN mkdir -p /data

# 创建启动脚本
RUN echo '#!/bin/sh\n\
\n\
# 更新Redis配置\n\
if [ ! -z "$REDIS_HOST" ]; then\n\
  sed -i "s/host: \\"localhost\\"/host: \\"$REDIS_HOST\\"/g" /app/config.yaml\n\
fi\n\
\n\
if [ ! -z "$REDIS_PORT" ]; then\n\
  sed -i "s/port: 16379/port: $REDIS_PORT/g" /app/config.yaml\n\
fi\n\
\n\
if [ ! -z "$REDIS_DB" ]; then\n\
  sed -i "s/db: 1/db: $REDIS_DB/g" /app/config.yaml\n\
fi\n\
\n\
# 主循环，每10分钟同步一次\n\
while true; do\n\
  python /app/main.py download\n\
  echo "下载完成，等待10分钟后再次同步..."\n\
  sleep 600\n\
done' > /app/start.sh && chmod +x /app/start.sh

# 设置容器启动命令
CMD ["/app/start.sh"] 