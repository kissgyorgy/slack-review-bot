#!/usr/bin/env python3

import sys
import slack
import gerrit


def main():
    gerrit_change_list = gerrit.get(gerrit.CHANGES_URL)
    gerrit_changes = [gerrit.Change(c) for c in gerrit_change_list]
    res = slack.post(gerrit_changes)
    return 0 if res.ok else 1


if __name__ == '__main__':
    sys.exit(main())
