FROM python:3.13.5

WORKDIR /quant_app

# 接收构建参数
ARG HOST_IP=127.0.0.1
ARG HOST_PORT=7897 # 默认端口（可选）

# 设置环境变量和代理配置（curl wget等）
ENV HTTP_PROXY="http://${HOST_IP}:${HOST_PORT}" \
    HTTPS_PROXY="http://${HOST_IP}:${HOST_PORT}" \
    NO_PROXY="localhost, 127.0.0.1"

# 给apt配置代理
RUN mkdir -p /etc/apt/apt.conf.d && \
    echo "Acquire::http::Proxy \"http://${HOST_IP}:${HOST_PORT}\";" > /etc/apt/apt.conf.d/90proxy && \
    echo "Acquire::https::Proxy \"http://${HOST_IP}:${HOST_PORT}\";" >> /etc/apt/apt.conf.d/90proxy

RUN apt-get update && \
    apt-get install -y \ 
        default-mysql-client \
        netcat-openbsd \  
        iputils-ping      

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# CMD ["bash", "-c", "mysql -u root -proot -e "SHOW DATABASES;""]

