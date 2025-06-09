FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制requirements文件并安装依赖
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# 复制项目文件到容器中
COPY *.py /app/

# 创建数据目录
RUN mkdir -p /data

# 设置环境变量默认值
ENV YUQUE_BASE_URL="https://www.yuque.com"
ENV YUQUE_TOKEN=""
ENV YUQUE_SESSION=""
ENV SAVE_PATH="/data"
ENV MONITOR_INTERVAL_MINUTES="10"

# 创建启动脚本
RUN echo '#!/bin/sh\n\
\n\
# 检查必要的环境变量\n\
if [ -z "$YUQUE_TOKEN" ] || [ -z "$YUQUE_SESSION" ]; then\n\
  echo "错误: 请设置 YUQUE_TOKEN 和 YUQUE_SESSION 环境变量"\n\
  echo "使用方法: docker run -e YUQUE_TOKEN=your_token -e YUQUE_SESSION=your_session ..."\n\
  exit 1\n\
fi\n\
\n\
echo "语雀同步工具启动中..."\n\
echo "保存路径: $SAVE_PATH"\n\
echo "同步间隔: ${MONITOR_INTERVAL_MINUTES}分钟"\n\
echo "语雀地址: $YUQUE_BASE_URL"\n\
\n\
# 主循环，按设定间隔同步\n\
while true; do\n\
  python /app/main.py download\n\
  echo "下载完成，等待${MONITOR_INTERVAL_MINUTES}分钟后再次同步..."\n\
  sleep $((MONITOR_INTERVAL_MINUTES * 60))\n\
done' > /app/start.sh && chmod +x /app/start.sh

# 设置容器启动命令
CMD ["/app/start.sh"] 