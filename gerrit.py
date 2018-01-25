import json
import requests
import slack


def get_changes(gerrit_url, query):
    # For +1 and -1 information, LABELS option has to be requested. See:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-labels
    # for owner name, DETAILED_ACCOUNTS:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-accounts
    changes_api_url = f'{gerrit_url}/changes/?o=LABELS&o=DETAILED_ACCOUNTS&q={query}'
    gerrit_change_list = get(changes_api_url)
    return [Change(gerrit_url, c) for c in gerrit_change_list]


def get(api_url):
    res = requests.get(api_url, verify=False)
    # There is a )]}' sequence at the start of each response...
    # we can't process it simply as JSON because of that.
    fixed_body = res.text[4:]
    return json.loads(fixed_body)


def make_changes_url(gerrit_url, query):
    return f'{gerrit_url}/#/q/{query}'


class Change:
    PLUS_ONE = slack.Emoji.PLUS_ONE
    PLUS_TWO = slack.Emoji.PLUS_ONE * 2
    MINUS_ONE = slack.Emoji.POOP
    MINUS_TWO = slack.Emoji.JS
    MISSING = slack.Emoji.EXCLAMATION

    VERIFIED = slack.Emoji.WHITE_CHECK_MARK
    FAILED = slack.Emoji.X

    PLUS_TWO_COLOR = '#36a64f'
    PLUS_ONE_COLOR = '#DBF32D'
    NO_PLUS_COLOR = '#EC1313'

    def __init__(self, gerrit_url, json_change):
        self._gerrit_url = gerrit_url
        self._change = json_change

    @property
    def subject(self):
        return slack.escape(self._change['subject'])

    @property
    def url(self):
        change_number = self._change['_number']
        return f'{self._gerrit_url}/{change_number}'

    @property
    def subject_url(self):
        """Return the subject hyperlinked to the Gerrit change_id."""
        return slack.make_link(self.url, self.subject)

    @property
    def author(self):
        # it is the username because it takes less characters, so
        # more valuable information can fit in one line
        return self._change['owner']['username']

    @property
    def code_review(self):
        cr = self._change['labels']['Code-Review']
        if 'approved' in cr:
            return self.PLUS_TWO
        elif 'value' not in cr:
            return self.MISSING
        elif cr['value'] == 1:
            return self.PLUS_ONE
        elif cr['value'] == -1:
            return self.MINUS_ONE
        elif cr['value'] == -2:
            return self.MINUS_TWO

    @property
    def verified(self):
        ver = self._change['labels']['Verified']
        if not ver:
            return ''
        elif 'approved' in ver:
            return self.VERIFIED
        else:
            return self.FAILED

    @property
    def color(self):
        if self.code_review == self.PLUS_TWO:
            return self.PLUS_TWO_COLOR
        elif self.code_review == self.PLUS_ONE and self.verified == self.VERIFIED:
            return self.PLUS_ONE_COLOR
        else:
            return self.NO_PLUS_COLOR
