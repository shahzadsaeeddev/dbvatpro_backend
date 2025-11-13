FROM python:3.10-bullseye

RUN apt-get update -y  && apt-get install -y default-jdk redis-tools iputils-ping

COPY . /neksio

WORKDIR /neksio

RUN python3 -m  venv /opt/venv

RUN pip install pip  --upgrade
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN java --version


RUN apt-get update && apt-get install -y postgresql-client tesseract-ocr libgl1-mesa-glx libglib2.0-0

RUN   /opt/venv/bin/pip3 install -r requirements.txt


RUN chmod +x /neksio/api/csr/file
RUN chmod +x /neksio/entrypoint.sh

CMD ["/neksio/entrypoint.sh"]