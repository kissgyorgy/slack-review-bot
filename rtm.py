import asyncio
from pprint import pprint
import functools
import django
from constance import config
import gerrit
import slack
from slack import MsgType, MsgSubType
from slackbot.models import Crontab, ReviewRequest


async def process_message(api, msg, *, loop):
    if "ok" in msg:
        return

    msgtype = msg["type"]

    if msgtype == MsgType.DESKTOP_NOTIFICATION:
        await handle_restart(api, msg)
        return

    if msgtype != MsgType.MESSAGE or msg.get("subtype"):
        return

    # Don't react to bot's own messages :D
    if msg["user"] == config.BOT_USER_ID:
        return

    text = get_text(msg)

    queries = parse_gerrit_queries(text)
    if queries:
        print(f"Found review links, adding them to queue: {queries}")
        loop.create_task(api.add_reaction(msg["channel"], msg["ts"], "review"))
        # with loop.create_task, it would raise an AssertionError:
        #   File "/usr/lib/python3.6/asyncio/coroutines.py", line 276, in _format_coroutine
        # assert iscoroutine(coro)
        # AssertionError
        # https://bugs.python.org/issue34071
        await loop.run_in_executor(None, save_review_requests, msg, queries)


async def handle_restart(api, msg):
    content = msg["content"]
    if all(w in content for w in ("restart", "@Review")):
        await api.rtm_close()


def get_text(msg):
    subtype = msg.get("subtype")
    if subtype == MsgSubType.MESSAGE_CHANGED:
        return msg["message"]["text"]
    else:
        return msg["text"]


def parse_gerrit_queries(text):
    rv = []
    for link in slack.parse_links(text):
        if link.startswith(config.GERRIT_URL):
            query = (link, gerrit.parse_query(link))
            rv.append(query)
    return rv


def save_review_requests(msg, queries):
    objs = []
    channel_id = msg["channel"]
    crontab = Crontab.objects.filter(channel_id=channel_id).first()
    for gerrit_url, gerrit_query in queries:
        rr = ReviewRequest(
            crontab=crontab,
            ts=msg["ts"],
            slack_user_id=msg["user"],
            channel_id=channel_id,
            gerrit_url=gerrit_url,
            gerrit_query=gerrit_query,
        )
        objs.append(rr)

    ReviewRequest.objects.bulk_create(objs)
    print(f"Saved {len(objs)} review requests.")


def main():
    django.setup()
    api = slack.AsyncApi(config.BOT_ACCESS_TOKEN)

    loop = asyncio.get_event_loop()
    message_handler = functools.partial(process_message, loop=loop)

    # run_until_complete instead of run_forever, because
    # uwsgi can restart it if it crashes
    loop.run_until_complete(api.rtm_connect(message_handler))


if __name__ == "__main__":
    main()
