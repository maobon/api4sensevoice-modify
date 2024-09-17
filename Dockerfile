
FROM registry.cn-hangzhou.aliyuncs.com/maobon/miniconda3

WORKDIR /app

COPY . .

RUN conda create --name api4sensevoice-main python=3.10 -y

RUN /bin/bash -c "source activate api4sensevoice-main"

RUN conda install -c conda-forge ffmpeg==6.1.1 -y

RUN pip install -r requirements.txt

EXPOSE 8888

ENTRYPOINT [ "python", "server_wss.py"]