# https://api.slack.com/docs/messages/builder?msg=%7B%22attachments%22%3A%5B%7B%22fallback%22%3A%22Required%20plain-text%20summary%20of%20the%20attachment.%22%2C%22color%22%3A%22%2336a64f%22%2C%22author_name%22%3A%22Bobby%20Tables%3A%20tests%2Fjenkins%2Fdsl%3A%20setup%20for%20parametric%20jobs%22%2C%22author_link%22%3A%22http%3A%2F%2Fflickr.com%2Fbobby%2F%22%2C%22author_icon%22%3A%22https%3A%2F%2Fintra.balabit%2Fwhoiswho%2Fimages%2Fgyorgykiss_250.jpg%22%2C%22mrkdwn_in%22%3A%5B%22fields%22%5D%2C%22fields%22%3A%5B%7B%22title%22%3A%22Code-Review%22%2C%22value%22%3A%22%2B1%22%2C%22short%22%3Atrue%7D%2C%7B%22title%22%3A%22Verified%22%2C%22value%22%3A%22%E2%9C%93%22%2C%22short%22%3Atrue%7D%5D%7D%5D%7D
# {
#     'attachments': [
#         {
#             'fallback': 'Required plain-text summary of the attachment.',
#             'color': '#36a64f',
#             'author_name': 'Bobby Tables: tests/jenkins/dsl: setup for parametric jobs',
#             'author_link': 'http://flickr.com/bobby/',
#             'author_icon': 'https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg',
#             'mrkdwn_in': ['fields'],
#             'fields': [
#                 {
#                     'title': 'Code-Review',
#                     'value': '+1',
#                     'short': true
#                 },
#                 {
#                     'title': 'Verified',
#                     'value': '✓',
#                     'short': true
#                 }
#             ]
#         }
#     ]
# }

message1 = {
    "channel": "@walkman",
    "attachments": [
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Nyírő Gergő: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "Code-Review", "value": "+1", "short": True},
                {"title": "Verified", "value": "✓", "short": True},
            ],
        },
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Kiss György: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "ID", "value": "12312", "short": True},
                {"title": "Code-Review", "value": "-1", "short": True},
                {"title": "Verified", "value": "✓", "short": True},
            ],
        },
    ],
}

message2 = {
    "channel": "@walkman",
    "attachments": [
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Nyírő Gergő: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "Code-Review: -2", "short": True},
                {"title": "Verified: ✓", "short": True},
            ],
        },
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Kiss György: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "Code-Review: -1", "short": True},
                {"title": "Verified: ✓", "short": True},
            ],
        },
    ],
}


message_emoji = {
    "channel": "@walkman",
    "attachments": [
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Nyírő Gergő: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "Code-Review: :+1::+1:        Verified: :x:", "short": False}
            ],
        },
        {
            "fallback": "tests/jenkins/dsl: setup for parametric jobs",
            "color": "#36a64f",
            "author_name": "Kiss György: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {
                    "title": "Code-Review: :exclamation:        Verified: :white_check_mark:",
                    "short": False,
                }
            ],
        },
    ],
}


message_emoji2 = {
    "channel": "@walkman",
    "text": "10 patch vár review-ra:",
    "attachments": [
        {
            "color": "#36a64f",
            "author_name": "Nyírő Gergő: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {"title": "Code-Review: :+1::+1:        Verified: :x:", "short": False}
            ],
        },
        {
            "color": "#36a64f",
            "author_name": "Kiss György: tests/jenkins/dsl: setup for parametric jobs",
            "author_link": "http://flickr.com/bobby/",
            "author_icon": "https://intra.balabit/whoiswho/images/gyorgykiss_250.jpg",
            "mrkdwn_in": ["fields"],
            "fields": [
                {
                    "title": "Code-Review: :exclamation:        Verified: :white_check_mark:",
                    "short": False,
                }
            ],
        },
    ],
}


message_table = {
    "channel": "@walkman",
    "fallback": "tests/jenkins/dsl: setup for parametric jobs",
    "color": "#36a64f",
    "text": """```
Name | Subject | Code-Review | Verified
---------------------------------------
Kiss György | tests/jenkins/dsl: setup for parametric jobs
```""",
}
