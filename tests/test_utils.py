from subreddit_recommender.src.util import strip_unwanted_chars


def test_parse_strip_unwanted_chars():
    assert 'test string' == strip_unwanted_chars('test string')
    assert 'test string' == strip_unwanted_chars('test \nstring\n')
    assert 'test string' == strip_unwanted_chars("test 'string'")
    assert 'test string' == strip_unwanted_chars('"test" string')
