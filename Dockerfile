FROM alpine:edge

RUN mkdir /app
RUN mkdir /app/data
RUN mkdir /app/static_root

WORKDIR /app/data
VOLUME /app/data

CMD ["/app/docker-start.sh"]

ENV PYTHONPATH=/app:/app/web:/app/lib
ENV DJANGO_SETTINGS_MODULE=web.settings

RUN apk update && apk add python3 uwsgi-python3 sqlite

RUN pip3 install pipenv
COPY Pipfile Pipfile.lock /app/
RUN pipenv install --system --deploy

COPY uwsgi.ini /app/
COPY docker-start.sh /app/
COPY secret_key.py /app/
COPY lib/ /app/lib/
COPY web/ /app/web/
COPY gerrit.py /app/
COPY slack.py /app/
COPY bot.py /app/

RUN SECRET_KEY=doesntmatterhere django-admin collectstatic --link --noinput -v 0
