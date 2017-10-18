import os
import json
import requests
import slack


GERRIT_URL = 'https://review.balabit'
# For +1 and -1 information, LABELS option has to be requested. See:
# https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-labels
# for owner name, DETAILS_ACCOUNT:
# https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-accounts
CHANGES_ENDPOINT = GERRIT_URL + '/changes/?o=LABELS&o=DETAILED_ACCOUNTS&q='
ACCOUNTS_ENDPOINT = GERRIT_URL + '/accounts'
CHANGES_URL = CHANGES_ENDPOINT + os.environ['QUERY']


class Change:
    PLUS_ONE = slack.PLUS_ONE
    PLUS_TWO = slack.PLUS_ONE + slack.PLUS_ONE
    MINUS_ONE = slack.POOP
    MINUS_TWO = slack.JS
    MISSING = slack.EXCLAMATION

    VERIFIED = slack.WHITE_CHECK_MARK
    FAILED = slack.X

    GREEN = '#36a64f'
    YELLOW = '#DBF32D'
    RED = '#EC1313'

    def __init__(self, json_change):
        self._change = json_change

    @property
    def subject(self):
        return slack.escape(self._change['subject'])

    @property
    def url(self):
        return '{}/{}'.format(GERRIT_URL, self._change['_number'])

    @property
    def subject_url(self):
        """Return the subject hyperlinked to the Gerrit change_id."""
        return '<{}|{}>'.format(self.url, self.subject)

    @property
    def author(self):
        return self._change['owner']['name']

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
        verified = "approved" in self._change['labels']["Verified"]
        return self.VERIFIED if verified else self.FAILED

    @property
    def color(self):
        if self.code_review == self.PLUS_TWO:
            return self.GREEN
        elif self.code_review == self.PLUS_ONE and self.verified == self.VERIFIED:
            return self.YELLOW
        return self.RED


def get(url):
    res = requests.get(url, verify=False)
    # There is a )]}' sequence at the start of each response...
    # we can't process it simply as JSON because of that.
    fixed_body = res.text[4:]
    return json.loads(fixed_body)
