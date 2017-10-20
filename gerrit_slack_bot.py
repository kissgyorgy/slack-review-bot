#!/usr/bin/env python3

import sys
import slack
import gerrit


def get_changes_and_submit_to_slack():
    gerrit_change_list = gerrit.get(gerrit.CHANGES_URL)
    gerrit_changes = [gerrit.Change(c) for c in gerrit_change_list]
    return slack.post(gerrit_changes) if gerrit_changes else None


def main():
    res = get_changes_and_submit_to_slack()
    if res is None or not res.ok:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
