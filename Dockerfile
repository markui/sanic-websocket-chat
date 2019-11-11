FROM python:3.7-slim-buster
MAINTAINER dexters.xlab@gmail.com

ENV APP_ENV DEV

# Install nginx, supervisor, vim
RUN apt-get -y update
RUN apt-get -y dist-upgrade
RUN apt-get -y install build-essential nginx supervisor vim

COPY . /sanic
WORKDIR /sanic

# Start Installing the Basic Dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

EXPOSE 8000

CMD ["python", "server.py"]




