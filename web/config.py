from nnx.config.node import Node


class SlackBotSetting(Node):
    timespec = SimpleProperty(str)
    channel = SimpleProperty(str)
    gerrit_query = SimpleProperty(str)
    slack_webhook_url = SimpleProperty(str)
