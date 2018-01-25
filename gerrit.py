import json
import requests


def get_changes(config):
    # For +1 and -1 information, LABELS option has to be requested. See:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-labels
    # for owner name, DETAILED_ACCOUNTS:
    # https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#detailed-accounts
    changes_api_url = f'{config.GERRIT_URL}/changes/?o=LABELS&o=DETAILED_ACCOUNTS&q={config.QUERY}'
    gerrit_change_list = get(changes_api_url)
    return [Change(config, c) for c in gerrit_change_list]


def get(url):
    res = requests.get(url, verify=False)
    # There is a )]}' sequence at the start of each response...
    # we can't process it simply as JSON because of that.
    fixed_body = res.text[4:]
    return json.loads(fixed_body)


def make_changes_url(config):
    return f'{config.GERRIT_URL}/#/q/{config.QUERY}'


class Change:

    def __init__(self, config, json_change):
        self._config = config
        self._change = json_change

    @property
    def subject(self):
        return self._config.ESCAPER(self._change['subject'])

    @property
    def url(self):
        gerrit_url = self._config.GERRIT_URL
        change_number = self._change['_number']
        return f'{gerrit_url}/{change_number}'

    @property
    def subject_url(self):
        """Return the subject hyperlinked to the Gerrit change_id."""
        return self._config.LINK_MAKER(self.url, self.subject)

    @property
    def author(self):
        # it is the username because it takes less characters, so
        # more valuable information can fit in one line
        return self._change['owner']['username']

    @property
    def code_review(self):
        cr = self._change['labels']['Code-Review']
        if 'approved' in cr:
            return self._config.PLUS_TWO
        elif 'value' not in cr:
            return self._config.MISSING
        elif cr['value'] == 1:
            return self._config.PLUS_ONE
        elif cr['value'] == -1:
            return self._config.MINUS_ONE
        elif cr['value'] == -2:
            return self._config.MINUS_TWO

    @property
    def verified(self):
        ver = self._change['labels']['Verified']
        if not ver:
            return ''
        elif 'approved' in ver:
            return self._config.VERIFIED
        else:
            return self._config.FAILED

    @property
    def color(self):
        if self.code_review == self._config.PLUS_TWO:
            return self._config.PLUS_TWO_COLOR
        elif self.code_review == self._config.PLUS_ONE and self.verified == self._config.VERIFIED:
            return self._config.PLUS_ONE_COLOR
        else:
            return self._config.NO_PLUS_COLOR
