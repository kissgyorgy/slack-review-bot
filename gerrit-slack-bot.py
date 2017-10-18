#!/usr/bin/env python3

import slack
import gerrit


def main():
    gerrit_change_list = gerrit.get(gerrit.CHANGES_URL)
    gerrit_changes = [gerrit.Change(c) for c in gerrit_change_list]
    slack.post(gerrit_changes)


if __name__ == '__main__':
    main()
