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

    gerrit_urls = parse_gerrit_urls(text)
    if gerrit_urls:
        print(f"Found review links, adding them to queue: {gerrit_urls}")
        # with loop.create_task, it would raise an AssertionError:
        #   File "/usr/lib/python3.6/asyncio/coroutines.py", line 276, in _format_coroutine
        # assert iscoroutine(coro)
        # AssertionError
        # https://bugs.python.org/issue34071
        filtered_urls, duplicate_requests = await loop.run_in_executor(
            None, filter_duplicate_requests, gerrit_urls
        )
        loop.create_task(add_reaction(api, rtm, duplicate_requests, msg, loop))
        await loop.run_in_executor(None, save_review_requests, msg, filtered_urls)


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


def parse_gerrit_urls(text):
    return [url for url in slack.parse_links(text) if url.startswith(config.GERRIT_URL)]


def filter_duplicate_requests(gerrit_urls):
    duplicate_requests = list(ReviewRequest.objects.filter(gerrit_url__in=gerrit_urls))
    existing_urls = {rr.gerrit_url for rr in duplicate_requests}
    filtered_urls = [url for url in gerrit_urls if url not in existing_urls]
    return filtered_urls, duplicate_requests


async def add_reaction(api, rtm, duplicate_requests, msg, loop):
    channel_id, ts = msg["channel"], msg["ts"]

    if duplicate_requests:
        loop.create_task(api.add_reaction(channel_id, ts, "no_entry_sign"))
        # the first will always be a duplicate, we don't have to be very detailed
        permalink = await api.get_permalink(channel_id, duplicate_requests[0].ts)
        if permalink is not None:
            message = f"Vót má: {permalink}"
        else:
            message = f"Már benne van a queue-ban"
        loop.create_task(rtm.reply_in_thread(channel_id, ts, message))
    else:
        loop.create_task(api.add_reaction(channel_id, ts, "review"))


def save_review_requests(msg, gerrit_urls):
    objs = []
    channel_id = msg["channel"]
    crontab = Crontab.objects.filter(channel_id=channel_id).first()
    for url in gerrit_urls:
        rr = ReviewRequest(
            crontab=crontab,
            ts=msg["ts"],
            slack_user_id=msg["user"],
            channel_id=channel_id,
            gerrit_url=url,
            gerrit_query=gerrit.parse_query(url),
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
