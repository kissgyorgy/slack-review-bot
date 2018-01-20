import slack


class BalabitConfigBase:
    GERRIT_URL = 'https://review.balabit'
    ESCAPER = slack.escape
    LINK_MAKER = slack.make_link

    PLUS_ONE = slack.PLUS_ONE
    PLUS_TWO = slack.PLUS_ONE * 2
    MINUS_ONE = slack.POOP
    MINUS_TWO = slack.JS
    MISSING = slack.EXCLAMATION

    VERIFIED = slack.WHITE_CHECK_MARK
    FAILED = slack.X

    PLUS_TWO_COLOR = '#36a64f'
    PLUS_ONE_COLOR = '#DBF32D'
    NO_PLUS_COLOR = '#EC1313'
