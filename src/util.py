import json
import os
import os.path as op


def load_env():
    """Load the .env in the base directory as a dictionary."""
    env_path = op.join(base_dir(), '.env')
    if op.exists(env_path):
        vars = parse_env(env_path)
        return vars
    return None


def parse_env(path):
    """Parse and load variables in an .env into a dictionary."""
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
    """Grab an environment variable without case sensitivity, by key."""
    env = load_env()
    for key, value in env.items():
        if var.lower() in key.lower():
            return env[key]


def parse_client_ids():
    """Parse .env and return a list of client ids and client keys.

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
    """Return the base directory for the project. Assumes the DS cookiecutter template."""
    path = os.path.dirname(os.path.abspath(__file__))
    return _base_dir(path=path, frame=0)


def _base_dir(path, frame):
    MAX_FRAMES = 5
    if frame > MAX_FRAMES:
        raise ValueError('Max frames reached.')
    elif _is_base_dir(path):
        return path
    else:
        frame += 1
        return _base_dir(path=os.path.dirname(path), frame=frame)


def _is_base_dir(path):
    files = os.listdir(path)
    has_src = 'src' in files
    has_data = 'data' in files
    return has_src and has_data


def data_dir(subdir=''):
    """Return the full path of the data directory or a specified subdirectory.

    Assumes the cookiecutter template.
    """
    valid_subdirs = ['', 'processed', 'raw', 'external', 'interim']
    if subdir not in valid_subdirs:
        raise ValueError('subdir must be one of the following: {dirs}'.format(dirs=valid_subdirs))

    data_dir = op.join(base_dir(), 'data')
    return op.join(data_dir, subdir) if subdir else data_dir


def data_dir_file(file_name, subdir=''):
    """Return the file path to a specified data subdirectory. Creates subdirectory if does not exist."""
    if not subdir:
        raise ValueError('Must specify a subdirectory.')
    dirname = data_dir(subdir)
    if not op.exists(dirname):
        os.mkdir(dirname)
    return op.join(dirname, file_name)


def data_dir_subreddit(*args, raw_data_dirname='reddit_raw'):
    """Return the subreddit data directory.

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
    """Load a .json by filename or path. Assumes the file is in data/raw."""
    if not op.exists(filename):
        filename = op.join(data_dir(subdir), filename)
    with open(filename, 'r') as file:
        subreddit_dict = json.load(file)
    return subreddit_dict


def valid_subreddit_dirname(s):
    """Convert a subreddit name to a valid directory name.
    (necessary since some subreddits have forward slashes in their names)
    """
    return s.replace('/r/', '').replace('/', '')
