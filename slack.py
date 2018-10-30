import re
import json
import asyncio
from urllib.parse import urlencode
import aiohttp
import requests


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


def revoke_token(token):
    return requests.post(SLACK_API_URL + "/auth.revoke", {"token": token})


class _ApiBase:
    def __init__(self, token):
        self._token = token
        self._auth_headers = {"Authorization": "Bearer " + token}

    def _make_json_res(self, res, method, payload):
        json_res = res.json()
        if res.ok and json_res["ok"]:
            return json_res
        else:
            print(
                f"Error {res.status_code} during {method} {res.request.method} request: {res.text}\n"
                f"payload: {payload}"
            )
            return

    def _get(self, method, payload=None):
        print("Request", method, payload)
        res = requests.get(
            f"{SLACK_API_URL}/{method}", payload, headers=self._auth_headers
        )
        return self._make_json_res(res, method, payload)

    def _get_all(self, method, field, payload):
        rv = []
        while True:
            json_res = self._get(method, payload)
            if json_res is None:
                return
            rv.extend(json_res[field])
            next_cursor = json_res.get("response_metadata", {}).get("next_cursor")
            print("Next cursor:", next_cursor or type(next_cursor))
            if not next_cursor:
                return rv
            payload["cursor"] = next_cursor

    def _post(self, method, payload=None):
        print("Posting to", method, payload)
        headers = {
            **self._auth_headers,
            # Slack needs a charset, otherwise it will send a warning in every response...
            "Content-Type": "application/json; charset=utf-8",
        }
        res = requests.post(f"{SLACK_API_URL}/{method}", headers=headers, json=payload)
        return self._make_json_res(res, method, payload)


class Api(_ApiBase):
    def list_all_channels(self):
        payload = {"types": "public_channel,private_channel"}
        return self._get_all("conversations.list", "channels", payload)

    def get_channel_id(self, channel_name):
        name = channel_name.lstrip("#")
        for channel in self.list_all_channels():
            if channel["name"] == name:
                return channel["id"]

    def user_info(self, user_id):
        return self._get("users.info", {"user": user_id})


class MsgType:
    TYPING = "typing"
    USER_TYPING = "user_typing"
    MESSAGE = "message"
    DESKTOP_NOTIFICATION = "desktop_notification"


class MsgSubType:
    MESSAGE_CHANGED = "message_changed"
    MESSAGE_DELETED = "message_deleted"


class RealTimeApi(_ApiBase):
    async def connect(self, message_handler):
        res = self._get("rtm.connect")
        print("Connected to RTM api:", res)

        session = aiohttp.ClientSession()
        ws_connect = session.ws_connect(res["url"])
        async with session, ws_connect as ws:
            await self._wait_messages(ws, message_handler)

    async def _wait_messages(self, ws, message_handler):
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == "close cmd":
                    await ws.close()
                    break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("An unknown error occured in the connection, exiting...")
                break

            message_json = json.loads(msg.data)
            asyncio.ensure_future(message_handler(ws, message_json))


class Channel(_ApiBase):
    def __init__(self, bot_token, channel_id):
        super().__init__(bot_token)
        self._channel_id = channel_id

    def __str__(self):
        return self._channel_id

    def _get(self, method):
        return super()._get(method, {"channel": self._channel_id})

    def _post(self, method, payload):
        payload.update({"channel": self._channel_id})
        return super()._post(method, payload)

    def info(self):
        return self._get("channels.info")

    def delete_message(self, ts):
        return self._post("chat.delete", {"ts": ts})

    def post_message(self, text, attachments):
        # as_user is needed, so direct messages can be deleted.
        # if DMs are sent to the user without as_user: True, they appear as if slackbot sent them
        # and there will be no channel which can be referenced later to delete the sent messages
        return self._post(
            "chat.postMessage",
            {"text": text, "attachments": attachments, "as_user": True},
        )


class App:
    SCOPE = "commands,bot"

    def __init__(self, client_id, client_secret, redirect_uri):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def request_oauth_token(self, code):
        # documentation: https://api.slack.com/methods/oauth.access
        res = requests.post(
            SLACK_API_URL + "/oauth.access",
            {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": self._redirect_uri,
                "code": code,
            },
        )
        # example in slack_messages/oauth.access.json
        return res.json()

    def make_button_url(self, state):
        params = {
            "scope": self.SCOPE,
            "client_id": self._client_id,
            "state": state,
            "redirect_uri": self._redirect_uri,
        }
        encoded_params = urlencode(params, safe=",")
        return f"{SLACK_OAUTH_URL}?{encoded_params}"
