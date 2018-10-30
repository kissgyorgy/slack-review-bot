import pytest
import slack


@pytest.mark.parametrize(
    "url, expected",
    (
        ("", []),
        ("No links at all", []),
        ("<One bracket only", []),
        ("Right side>", []),
        ("<https://google.com>", ["https://google.com"]),
        ("<http://google.com>", ["http://google.com"]),
        ("<http://google.com> Some text here", ["http://google.com"]),
        ("Naked domain: <google.com>", ["google.com"]),
        ("Multiple <google.com> <facebook.com>", ["google.com", "facebook.com"]),
    ),
)
def test_parse_links(url, expected):
    assert slack.parse_links(url) == expected
