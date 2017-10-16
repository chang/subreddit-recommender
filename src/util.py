import os
import os.path as op


def load_env(max_levels=5):
    """Finds .env and returns a dictionary with variables.

    Attributes:
        max_levels (int): Maximum number of parent directories to traverse.
    """
    levels = 0
    dir_ = op.dirname(__file__)
    while levels < max_levels:
        files = os.listdir(dir_)
        if '.env' in files:
            vars = parse_env(op.join(dir_, '.env'))
            return vars
        dir_ = op.dirname(dir_)
        levels += 1
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
            client_ids.append(env[key].split(':'))
    return client_ids


def strip_unwanted_chars(s):
    """Strip unwanted characters from a string."""
    unwanted_chars = ['\n', '"', "'"]
    s = s.strip()
    for char in unwanted_chars:
        s = s.replace(char, '')
    return s


def data_dir(subdir='', max_levels=5):
    """Returns the full path of the data directory or a specified subdirectory.

    Assumes the cookiecutter template.
    """
    valid_subdirs = ['', 'processed', 'raw', 'external', 'interim']
    if subdir not in valid_subdirs:
        raise ValueError('subdir must be one of the following: {dirs}'.format(dirs=valid_subdirs))

    levels = 0
    dir_ = op.dirname(__file__)
    while levels < max_levels:
        path = op.abspath(dir_)
        if op.isdir(path) and not op.basename(path) == 'src':
            data_dir = op.join(path, 'data')
            return op.join(data_dir, subdir) if subdir else data_dir
        dir_ = op.dirname(dir_)
    return None


def data_dir_file(file_name, subdir=''):
    """Returns the file path to a specified data subdirectory. Creates subdirectory if does not exist."""
    if not subdir:
        raise ValueError('Must specify a subdirectory.')
    dirname = data_dir(subdir)
    if not op.exists(dirname):
        os.mkdir(dirname)
    return op.join(dirname, file_name)
