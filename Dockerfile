FROM alpine:edge

RUN mkdir /app
WORKDIR /app
VOLUME /app

RUN apk update && apk add python3 uwsgi-python3 sqlite
RUN pip3 install flask croniter requests

CMD ["uwsgi", "--ini", "uwsgi.ini"]
