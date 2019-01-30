FROM alpine:edge

RUN mkdir /app
RUN mkdir /app/data
RUN mkdir /app/static_root

WORKDIR /app/data
VOLUME /app/data

CMD ["/app/docker-start.sh"]

ENV PYTHONPATH=/app:/app/web:/app/lib
ENV DJANGO_SETTINGS_MODULE=web.settings

RUN apk add --update curl python3 uwsgi-python3 sqlite ca-certificates

# Poetry simply won't work without these symlinks
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry config settings.virtualenvs.create false
RUN poetry install --no-dev

COPY uwsgi.ini /app/
COPY docker-start.sh /app/
COPY secret_key.py /app/
COPY lib/ /app/lib/
COPY web/ /app/web/
COPY gerrit.py /app/
COPY slack.py /app/
COPY bot.py /app/
COPY rtm.py /app/

RUN SECRET_KEY=doesntmatterhere django-admin collectstatic --link --noinput -v 0
