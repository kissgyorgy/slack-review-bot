#!/usr/bin/env python3
import json
from urllib.parse import quote
import collections
import requests


GERRIT_URL = 'https://review.balabit'
CHANGES_ENDPOINT = GERRIT_URL + '/changes/?q='
ACCOUNTS_ENDPOINT = GERRIT_URL + '/accounts'
QUERY = '(ownerin:scb-beast+OR+ownerin:scb-beauty)+AND+status:open+AND+NOT+label:Code-Review=2'
CHANGES_URL = CHANGES_ENDPOINT + QUERY
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'


Change = collections.namedtuple('Change', 'subject id change_url')


def get(url):
    res = requests.get(url, verify=False)
    # There is a )]}' sequence at the start of each response...
    # we can't process it simply as JSON because of that.
    fixed_body = res.text[4:]
    return json.loads(fixed_body)


def make_view_url(change_id):
    return GERRIT_URL + '/' + str(change_id)


def process_changes(all_changes):
    for change in all_changes:
        change_url = '{}/{}'.format(GERRIT_URL, change['_number'])
        yield Change(change['subject'], change['id'], change_url)


def post_to_slack(processed_changes):
    lines = []
    for change in processed_changes:
        subject = change.subject
        subject = subject.replace('<', '&lt;')
        subject = subject.replace('>', '&gt;')
        change_url = '<{}|{}>'.format(change.change_url, subject)
        lines.append(change_url)

    payload = '\n'.join(lines)
    print('TEXT TO POST:', payload)
    requests.post(SLACK_WEBHOOK_URL, json={'text': payload})


def main():
    all_changes = get(CHANGES_URL)
    processed_changes = process_changes(all_changes)
    post_to_slack(processed_changes)


if __name__ == '__main__':
    main()
