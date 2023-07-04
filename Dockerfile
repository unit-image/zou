FROM python:3.7-slim-buster

EXPOSE 5000

# install pg_dump & ffmpeg
RUN apt-get update && apt-get install postgresql-client --yes && apt-get install ffmpeg --yes && apt-get install netcat --yes

# Install external dependencies
# We do it separatly to leverage docker build cache
WORKDIR /opt/zou

# Install zou
COPY . .
RUN pip install -r requirements.txt
RUN mkdir /tmp/zou
VOLUME /tmp/zou

ENTRYPOINT ["bash", "./entrypoint.sh"]
