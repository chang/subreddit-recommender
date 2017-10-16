import json
import os
import os.path as op

import subreddit_recommender


def load_env():
    """Loads the .env in the base directory as a dictionary."""
    env_path = op.join(base_dir(), '.env')
    if op.exists(env_path):
        vars = parse_env(env_path)
        return vars
    return None


def parse_env(path):
    """Parses and loads variables in an .env into a dictionary."""
    variables = {}
    with open(path, 'r') as file:
        lines = file.readlines()
        lines = [strip_unwanted_chars(l) for l in lines if not l.startswith('#')]
        for line in lines:
            try:
                var, value = line.split('=')
                value = strip_unwanted_chars(value)
                variables[var] = value
            except ValueError:  # skip empty lines in .env
                continue
    return variables


def env_var(var):
    """Grabs an environment variable without case sensitivity, by key"""
    env = load_env()
    for key, value in env.items():
        if var.lower() in key.lower():
            return env[key]


def parse_client_ids():
    """Parses .env and returns a list of client ids and client keys.

    Returns:
        client_ids: list(tuple)
            List of (client_id, client_secret)
    """
    client_ids = []
    env = load_env()
    for key in env.keys():
        if key.startswith('CLIENT'):
            client_id = tuple(env[key].split(':'))
            client_ids.append(client_id)
    return client_ids


def strip_unwanted_chars(s):
    """Strip unwanted characters from a string."""
    unwanted_chars = ['\n', '"', "'"]
    s = s.strip()
    for char in unwanted_chars:
        s = s.replace(char, '')
    return s


def base_dir():
    head, tail = op.split(subreddit_recommender.__file__)
    return head


def data_dir(subdir='', max_levels=5):
    """Returns the full path of the data directory or a specified subdirectory.

    Assumes the cookiecutter template.
    """
    valid_subdirs = ['', 'processed', 'raw', 'external', 'interim']
    if subdir not in valid_subdirs:
        raise ValueError('subdir must be one of the following: {dirs}'.format(dirs=valid_subdirs))

    data_dir = op.join(base_dir(), 'data')
    return op.join(data_dir, subdir) if subdir else data_dir


def data_dir_file(file_name, subdir=''):
    """Returns the file path to a specified data subdirectory. Creates subdirectory if does not exist."""
    if not subdir:
        raise ValueError('Must specify a subdirectory.')
    dirname = data_dir(subdir)
    if not op.exists(dirname):
        os.mkdir(dirname)
    return op.join(dirname, file_name)


def data_dir_subreddit(*args, raw_data_dirname='reddit_raw'):
    """Returns the subreddit data directory.

    Input should be a tuple of the form (category, subcategory, subreddit),
    or as separate arguments.
    """
    args_correct_length = len(args) == 3 or len(args) == 1
    single_arg_correct_length = len(args[0]) == 3 if len(args) == 1 else True
    if not (args_correct_length and single_arg_correct_length):
        raise ValueError('Input should be a tuple of the form (category, subcategory, subreddit), or *args')

    if len(args) == 1:
        args = args[0]
    category, subcategory, subreddit = args

    reddit_data_dir = op.join(data_dir('raw'), raw_data_dirname)
    elems = [reddit_data_dir] + [valid_subreddit_dirname(e) for e in args]
    return op.join(*elems)


def load_json(filename, subdir='raw'):
    """Loads a .json by filename or path. Assumes the file is in data/raw."""
    if not op.exists(filename):
        filename = op.join(data_dir(subdir), filename)
    with open(filename, 'r') as file:
        subreddit_dict = json.load(file)
    return subreddit_dict


def valid_subreddit_dirname(s):
    """Converts a subreddit name to a valid directory name.
    (necessary since some subreddits have forward slashes in their names)
    """
    return s.replace('/r/', '').replace('/', '')
