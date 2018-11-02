import re
import json
import asyncio
from urllib.parse import urlencode
import aiohttp


class Emoji:
    PLUS_ONE = ":+1:"
    POOP = ":poop:"
    JS = ":js:"
    EXCLAMATION = ":exclamation:"
    WHITE_CHECK_MARK = ":white_check_mark:"
    X = ":x:"


SLACK_API_URL = "https://slack.com/api"
SLACK_OAUTH_URL = "https://slack.com/oauth/authorize"


def escape(text):
    """Escape Slack special characters.
    See: https://api.slack.com/docs/message-formatting#how_to_escape_characters
    """
    rv = text.replace("<", "&lt;")
    rv = rv.replace(">", "&gt;")
    rv = rv.replace("&", "&amp;")
    return rv


def make_link(url, text):
    return f"<{url}|{text}>"


def parse_links(text):
    return re.findall(r"<(.*?)>", text.strip())


def make_attachment(color, author_name, author_link):
    return {"color": color, "author_name": author_name, "author_link": author_link}


class _ApiBase:
    def __init__(self, token):
        self._token = token
        self._headers = {
            "Authorization": "Bearer " + token,
            # Slack needs a charset, otherwise it will send a warning in every response...
            "Content-Type": "application/json; charset=utf-8",
        }
        self._loop = asyncio.get_event_loop()
        self._session = aiohttp.ClientSession(loop=self._loop)

    def __del__(self):
        self._run(self._close_session())

    async def _close_session(self):
        await self._session.close()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    async def _make_json_res(self, res, method, payload):
        json_res = await res.json()
        if 200 <= res.status < 400 and json_res["ok"]:
            return json_res
        else:
            res_body = await res.text()
            print(
                f"Error {res.status} during {method} {res.method} request: {res_body}\n"
                f"payload: {payload}"
            )
            return

    async def _get(self, method, params=None):
        print("Request", method, params)
        url = f"{SLACK_API_URL}/{method}"
        async with self._session.get(url, params=params, headers=self._headers) as res:
            return await self._make_json_res(res, method, params)

    async def _get_all(self, method, field, params):
        rv = []
        while True:
            json_res = await self._get(method, params)
            if json_res is None:
                return
            rv.extend(json_res[field])
            next_cursor = json_res.get("response_metadata", {}).get("next_cursor")
            print("Next cursor:", next_cursor or type(next_cursor))
            if not next_cursor:
                return rv
            params["cursor"] = next_cursor

    async def _post(self, method, payload):
        print("Posting to", method, payload)
        url = f"{SLACK_API_URL}/{method}"
        async with self._session.post(url, headers=self._headers, json=payload) as res:
            return await self._make_json_res(res, method, payload)


class Api(_ApiBase):
    def _get(self, method, params=None):
        return self._run(super()._get(method, params))

    def _get_all(self, method, field, params):
        return self._run(super()._get_all(method, field, params))

    def _post(self, method, payload):
        return self._run(super()._post(method, payload))

    def list_all_channels(self):
        params = {"types": "public_channel,private_channel"}
        return self._get_all("conversations.list", "channels", params)

    def get_channel_id(self, channel_name):
        name = channel_name.lstrip("#")
        for channel in self.list_all_channels():
            if channel["name"] == name:
                return channel["id"]

    def user_info(self, user_id):
        return self._get("users.info", {"user": user_id})

    def revoke_token(self):
        return self._run(self._revoke_token())

    async def _revoke_token(self):
        method = "auth.revoke"
        url = f"{SLACK_API_URL}/{method}"
        # this method doesn't accept JSON body
        async with self._session.post(url, {"token": self._token}) as res:
            return await self._make_json_res(res, method, {"token": "XXXXXXXXXX"})

    def channel_info(self, channel_id):
        return self._get("channels.info", {"channel": channel_id})

    def post_message(self, channel_id, text, attachments):
        # as_user is needed, so direct messages can be deleted.
        # if DMs are sent to the user without as_user: True, they appear
        # as if slackbot sent them and there will be no channel which
        # can be referenced later to delete the sent messages
        return self._post(
            "chat.postMessage",
            {
                "channel": channel_id,
                "text": text,
                "attachments": attachments,
                "as_user": True,
            },
        )

    def delete_message(self, channel_id, ts):
        return self._post("chat.delete", {"channel": channel_id, "ts": ts})


class MsgType:
    TYPING = "typing"
    USER_TYPING = "user_typing"
    MESSAGE = "message"
    DESKTOP_NOTIFICATION = "desktop_notification"
    GOODBYE = "goodbye"


class MsgSubType:
    MESSAGE_CHANGED = "message_changed"
    MESSAGE_DELETED = "message_deleted"


class AsyncApi(_ApiBase):
    async def add_reaction(self, channel, ts, reaction_name):
        payload = {"channel": channel, "timestamp": ts, "name": reaction_name}
        return await self._post("reactions.add", payload)

    async def rtm_connect(self, message_handler):
        res = await self._get("rtm.connect")
        print("Connected to RTM api:", res)

        session = aiohttp.ClientSession()
        ws_connect = session.ws_connect(res["url"])
        async with session, ws_connect as self._ws:
            await self._wait_messages(message_handler)

    async def _wait_messages(self, message_handler):
        async for msg in self._ws:
            print("RTM message:", msg.data)
            if msg.type == aiohttp.WSMsgType.TEXT:
                message_json = json.loads(msg.data)
                if message_json.get("type") == MsgType.GOODBYE:
                    await self.rtm_close()
                    break
                asyncio.ensure_future(message_handler(self, message_json))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("An unknown error occured in the connection, exiting...")
                break

    async def rtm_close(self):
        await self._ws.close()
        self._ws = None

    async def rtm_send_typing_indicator(self, channel):
        # FIXME: should be a real id
        message = {"id": 1, "type": MsgType.TYPING, "channel": channel}
        await self._ws.send_json(message)

    async def rtm_reply_in_thread(self, channel, ts, text):
        # FIXME: should be a real id
        message = {
            "id": 2,
            "type": MsgType.MESSAGE,
            "channel": channel,
            "text": text,
            "thread_ts": ts,
        }
        await self._ws.send_json(message)


class App:
    SCOPE = "commands,bot"

    def __init__(self, client_id, client_secret, redirect_uri):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def request_oauth_token(self, code):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._request_oauth_token(code))

    async def _request_oauth_token(self, code):
        # documentation: https://api.slack.com/methods/oauth.access
        url = SLACK_API_URL + "/oauth.access"
        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "code": code,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as res:
                # example in slack_messages/oauth.access.json
                return await res.json()

    def make_button_url(self, state):
        params = {
            "scope": self.SCOPE,
            "client_id": self._client_id,
            "state": state,
            "redirect_uri": self._redirect_uri,
        }
        encoded_params = urlencode(params, safe=",")
        return f"{SLACK_OAUTH_URL}?{encoded_params}"
