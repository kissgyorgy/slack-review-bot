import enum
import json
import requests


class CodeReview(enum.Enum):
    PLUS_ONE = 1
    PLUS_TWO = 2
    MISSING = 0
    MINUS_ONE = -1
    MINUS_TWO = -2


class Verified(enum.Enum):
    VERIFIED = True
    FAILED = False
    MISSING = None


class Change:
    def __init__(self, gerrit_url, json_change):
        self._gerrit_url = gerrit_url
        self._change = json_change

    @property
    def url(self):
        change_number = self._change['_number']
        return f'{self._gerrit_url}/#/c/{change_number}'

    @property
    def username(self):
        # it is the username because it takes less characters, so
        # more valuable information can fit in one line
        return self._change['owner']['username']

    @property
    def subject(self):
        return self._change['subject']

    @property
    def code_review(self):
        cr = self._change['labels']['Code-Review']
        if 'approved' in cr:
            return CodeReview.PLUS_TWO
        elif 'value' not in cr:
            return CodeReview.MISSING
        elif cr['value'] == 1:
            return CodeReview.PLUS_ONE
        elif cr['value'] == -1:
            return CodeReview.MINUS_ONE
        elif cr['value'] == -2:
            return CodeReview.MINUS_TWO

    @property
    def verified(self):
        ver = self._change['labels']['Verified']
        if not ver:
            return Verified.MISSING
        elif 'approved' in ver:
            return Verified.VERIFIED
        else:
            return Verified.FAILED


def get(api_url):
    res = requests.get(api_url, verify=False)
    # There is a )]}' sequence at the start of each response...
    # we can't process it simply as JSON because of that.
    fixed_body = res.text[4:]
    return json.loads(fixed_body)


def get_changes(gerrit_url, query):
    # For +1 and -1 information, LABELS option has to be requested. See:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-labels
    # for owner name, DETAILED_ACCOUNTS:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-accounts
    changes_api_url = f'{gerrit_url}/changes/?o=LABELS&o=DETAILED_ACCOUNTS&q={query}'
    gerrit_change_list = get(changes_api_url)
    return [Change(gerrit_url, c) for c in gerrit_change_list]


def make_changes_url(gerrit_url, query):
    return f'{gerrit_url}/#/q/{query}'
