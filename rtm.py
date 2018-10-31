import asyncio
from pprint import pprint
import functools
import django
from constance import config
import gerrit
import slack
from slack import MsgType, MsgSubType
from slackbot.models import Crontab, ReviewRequest


async def process_message(ws, msg, *, loop):
    if "ok" in msg:
        return

    msgtype = msg["type"]

    if msgtype == MsgType.DESKTOP_NOTIFICATION:
        await handle_restart(msg)
        return

    if msgtype != MsgType.MESSAGE or msg.get("subtype"):
        return

    text = get_text(msg)

    queries = parse_gerrit_queries(text)
    if queries:
        print(f"Found review links, adding them to queue: {queries}")
        await send_typing_indicator(ws, msg["channel"])
        await reply_in_thread(ws, msg)
        await loop.run_in_executor(None, save_review_requests, msg, queries)
        await loop.run_in_executor(None, update_review_requests, ws, msg)


async def handle_restart(msg):
    content = msg["content"]
    if all(w in content for w in ("restart", "@Review")):
        await ws.close()


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


async def send_typing_indicator(ws, channel):
    message = {"id": 1, "type": MsgType.TYPING, "channel": channel}
    await ws.send_json(message)


async def reply_in_thread(ws, msg):
    message = {
        "id": 2,
        "type": MsgType.MESSAGE,
        "channel": msg["channel"],
        "text": "Köszi, betettem a listába.",
        "thread_ts": msg["ts"],
    }
    await ws.send_json(message)


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


def update_review_requests(ws, msg):
    pass


def main():
    django.setup()
    rtm_api = slack.RealTimeApi(config.BOT_ACCESS_TOKEN)

    loop = asyncio.get_event_loop()
    message_handler = functools.partial(process_message, loop=loop)

    # run_until_complete instead of run_forever, because
    # uwsgi can restart it if it crashes
    loop.run_until_complete(rtm_api.connect(message_handler))


if __name__ == "__main__":
    main()
