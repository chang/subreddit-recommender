import os
import os.path as op

import pytest

import subreddit_recommender
from subreddit_recommender.src.util import (base_dir, data_dir,
                                            data_dir_subreddit, env_var,
                                            load_env, parse_client_ids,
                                            parse_env, strip_unwanted_chars,
                                            valid_subreddit_dirname)


@pytest.fixture(scope='module')
def create_temp_env():
    """Creates a temporary test .env file in the base directory."""
    base_path = base_dir()
    env_path = op.join(base_path, '.env')
    has_existing_env = False

    if op.exists(env_path):
        has_existing_env = True
        os.rename(op.join(base_path, '.env'), op.join(base_path, '.env_backup'))

    env_content = [
        '# test comment',
        '',
        'CLIENT_0=test_client_id:test_client_secret',
        'CLIENT_1=test_client_id:test_client_secret',
        'variable=value'
    ]

    with open(env_path, 'w') as file:
        file.write('\n'.join(env_content))

    yield

    # teardown
    if has_existing_env:
        os.rename(op.join(base_path, '.env_backup'), op.join(base_path, '.env'))
    else:
        os.remove(op.join(base_path, '.env'))


@pytest.fixture(scope='module')
def sample_env():
    sample_env = {'CLIENT_0': 'test_client_id:test_client_secret',
                  'CLIENT_1': 'test_client_id:test_client_secret',
                  'variable': 'value'}
    return sample_env


def test_load_env(sample_env, create_temp_env):
    env = load_env()
    for key in sample_env.keys():
        assert sample_env[key] == env[key]


def test_parse_env(sample_env, create_temp_env):
    env = parse_env(op.join(base_dir(), '.env'))
    for key in sample_env.keys():
        assert sample_env[key] == env[key]


def test_env_var(create_temp_env):
    assert 'test_client_id:test_client_secret' == env_var('CLIENT_0')
    assert 'value' == env_var('variable')
    assert None is env_var('does_not_exist')


def test_parse_client_ids(create_temp_env):
    client_ids = parse_client_ids()
    assert 2 == len(client_ids)
    assert ('test_client_id', 'test_client_secret') in client_ids


def test_base_dir():
    assert subreddit_recommender.__file__ == op.join(base_dir(), '__init__.py')


def test_data_dir():
    assert op.join(base_dir(), 'data') == data_dir()
    assert op.join(base_dir(), 'data/raw') == data_dir('raw')
    with pytest.raises(ValueError):
        data_dir(subdir='dir_does_not_exist')


def test_data_dir_subreddit():
    default_reddit_data_dir = 'reddit_raw'
    category, subcategory, subreddit = 'cat', 'morecats', 'allaboutcats'
    path = op.join(data_dir('raw'), default_reddit_data_dir, category, subcategory, subreddit)

    assert path == data_dir_subreddit(category, subcategory, subreddit)
    assert path == data_dir_subreddit((category, subcategory, subreddit))


def test_valid_subreddit_dirname():
    assert 'AskReddit' == valid_subreddit_dirname('/r/AskReddit')
    assert '5050' == valid_subreddit_dirname('/r/50/50')


def test_parse_strip_unwanted_chars():
    assert 'test string' == strip_unwanted_chars('test string')
    assert 'test string' == strip_unwanted_chars('test \nstring\n')
    assert 'test string' == strip_unwanted_chars("test 'string'")
    assert 'test string' == strip_unwanted_chars('"test" string')
