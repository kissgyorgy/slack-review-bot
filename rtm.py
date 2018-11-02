import time
import asyncio
from pprint import pprint
import functools
import django
from constance import config
import gerrit
import slack
from slack import MsgType, MsgSubType
from slackbot.models import Crontab, ReviewRequest


async def process_message(api, rtm, msg, loop):
    if "ok" in msg:
        return

    msgtype = msg["type"]

    if msgtype == MsgType.DESKTOP_NOTIFICATION:
        await handle_restart(rtm, msg)
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


async def handle_restart(rtm, msg):
    content = msg["content"]
    if all(w in content for w in ("restart", "@Review")):
        await rtm.close()


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


async def rtm_connect(api, loop):
    async with api.rtm_connect() as rtm:
        if not await rtm.got_hello():
            _count_down(10)
            return

        async for msg in rtm.wait_messages():
            loop.create_task(process_message(api, rtm, msg, loop))


def _count_down(from_sec):
    print(
        "Something happened during connecting to RTM API, got no hello message.\n"
        "Quitting in ... ",
        end="",
    )
    for sec in range(from_sec, 0, -1):
        print(f"{sec}..", end="", flush=True)
        time.sleep(1)
    print("0.", flush=True)


def main():
    django.setup()
    api = slack.AsyncApi(config.BOT_ACCESS_TOKEN)
    loop = asyncio.get_event_loop()
    # run_until_complete instead of run_forever, because
    # uwsgi can restart it if it crashes
    loop.run_until_complete(rtm_connect(api, loop))


if __name__ == "__main__":
    main()
