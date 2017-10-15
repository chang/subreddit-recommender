# -*- coding: utf-8 -*-
import json
import os
import os.path as op
import shutil

import praw
from subreddit_recommender.src.util import data_dir, env_var, load_env

# path defaults, can be overridden by setting variables of the same name in .env
REDDIT_DATA_DIR = op.join(data_dir('raw'), 'REDDIT_RAW')
SUBREDDIT_DICT_PATH = op.join(data_dir('processed'), 'subreddit_list.json')
VERBOSE = 1


def load_subreddit_dict(path=SUBREDDIT_DICT_PATH):
    """"""
    with open(path, 'r') as file:
        subreddit_dict = json.load(file)
    return subreddit_dict


def open_reddit_instance():
    """Returns a praw.Reddit instance authenticated with environment variables."""
    env = load_env()
    reddit = praw.Reddit(
        client_id=env['CLIENT_ID'],
        client_secret=env['CLIENT_SECRET'],
        user_agent=env['USER_AGENT']
    )
    return reddit


def flatten_subreddit_dict(subreddit_dict):
    """Flattens 2 nested dictionaries into a list of tuples."""
    subreddits = []
    for cat in subreddit_dict.keys():
        for subcat in subreddit_dict[cat].keys():
            for subreddit in subreddit_dict[cat][subcat]:
                subreddits.append((cat, subcat, subreddit))
    return subreddits


def make_dirname(s):
    """Converts a subreddit name to a valid directory name.
    (necessary since some subreddits have forward slashes in their names)
    """
    return s.replace('/r/', '').replace('/', '')


def _mkdir(path):
    """Makes directory if path doesn't exist."""
    if not op.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            raise ValueError('Problematic path: {path}'.format(path=path))


def create_directory_structure(subreddit_dict, reddit_dirname=REDDIT_DATA_DIR, overwrite=False):
    """Create the directory structure for storing reddit data.

    Args:
        subreddit_dict (dict):
        reddit_dirname (str): Path to reddit data directory.
        overwrite (bool): If True, overwrites all existing data in the directory.
    """
    if overwrite:
        shutil.rmtree(reddit_dirname)
    _mkdir(reddit_dirname)

    flattened_subreddits = flatten_subreddit_dict(subreddit_dict)
    for cat, subcat, subreddit in flattened_subreddits:
        cat, subcat, subreddit = map(make_dirname, (cat, subcat, subreddit))

        _mkdir(op.join(reddit_dirname, cat))
        _mkdir(op.join(reddit_dirname, cat, subcat))
        _mkdir(op.join(reddit_dirname, cat, subcat, subreddit))

    print('{n} directories for subreddits created.'.format(n=len(flattened_subreddits)))


def _decode_utf(s):
    """Coverts utf-8 to ascii, removing non ascii chars"""
    return s.encode('utf-8').decode('ascii', 'ignore')


def wikipage_text(subreddit, verbose=0):
    """Extracts text from a subreddit's wiki"""
    content = "".encode('utf-8')
    for page in subreddit.wiki:
        try:
            content += subreddit.wiki[page].content_md.encode('utf-8')
        except AttributeError:
            if verbose:
                print('Skipping wiki page {page}'.format(page=page))
            continue
    return content


def traverse_comment_forest(comment_forest, depth=3, max_comments=100, verbose=VERBOSE):
    """Traverses a comment chain, saving each top level comment and a specified number of replies.

    Returns:
        comment_and_replies: list(str)
            List of [flattened_comment_chain, flattened_comment_chain, ...],
            where flattened_comment_chain is of type
    """
    is_comment_forest = isinstance(comment_forest, praw.models.comment_forest.CommentForest)
    assert is_comment_forest, 'Input should be a CommentForest object.'

    comments_and_replies = []
    comment_forest.replace_more(limit=3, threshold=1)  # TODO: Find a logical # of replaces and a logical threshold
    for comment in comment_forest:
        content = [comment.body] + [reply.body for reply in comment.replies[0:depth]]
        comments_and_replies.append('\n'.join(content))
    return comments_and_replies


def get_subreddit_submissions(subreddit, top_n_submissions, comment_depth, verbose=VERBOSE):
    """Given a subreddit object, returns a list of submissions.

    Return is a list of length top_n_submissions, with each string being the submission's
    title and comment chain.
    """
    assert isinstance(subreddit, praw.models.Subreddit), 'Input should be a Subreddit object.'
    top_submissions = subreddit.top(limit=top_n_submissions)
    submission_comment_chains = []

    for i, submission in enumerate(top_submissions):
        submission.comment_sort = 'top'
        comment_forest = submission.comments
        content = [submission.title] + traverse_comment_forest(comment_forest, comment_depth)
        submission_comment_chains.append('\n'.join(content))

        if verbose > 0:
            msg = '{i} of {n} submissions extracted for {title}'
            print(msg.format(i=i, n=top_n_submissions, title=_decode_utf(subreddit.display_name)))

    return submission_comment_chains


def download_reddit_data(reddit, subreddit_dict, reddit_dirname=REDDIT_DATA_DIR, top_n_submissions=10, comment_depth=4):
    """Downloads all relevant data from subreddits specified in the subreddit dict.

    Downloads to raw data folder. Currently downloads the following data
    - subreddit description
    - subreddit wiki text
    - all comments from top_n_submissions posts

    Args:
        reddit (praw.Reddit): An authenticated praw.Reddit instance.
        subreddit_dict (dict): Dictionary of subreddits, organized by the hierarchy:
                               Category | Subcategory | List of subreddits
        reddit_dirname (str): Subdirectory of data/raw to store data.
        top_n_submissions (n): Number of posts to scrape comments from.
    """
    flattened_subreddits = flatten_subreddit_dict(subreddit_dict)
    for sub_id, (cat, subcat, subreddit) in enumerate(flattened_subreddits):
        cat, subcat, subreddit = map(make_dirname, (cat, subcat, subreddit))
        if cat == 'Defunct':
            continue

        dirname = op.join(reddit_dirname, cat, subcat, subreddit)
        praw_subreddit = reddit.subreddit(subreddit)

        # download description
        try:
            description = _decode_utf(praw_subreddit.description)
        except Exception:  # TODO: Use the more specific prawcore.excpetions.NotFound
            description = ''

        with open(op.join(dirname, 'description'), 'w') as file:
            file.write(description)

        # download top n submission comment chains
        submissions = get_subreddit_submissions(reddit.subreddit(subreddit), top_n_submissions, comment_depth)
        for i, sub in enumerate(submissions):
            with open(op.join(dirname, 'sub_{}'.format(i)), 'w') as file:
                file.write(_decode_utf(sub))

        print('{i} of {n} subreddits complete'.format(i=sub_id, n=len(flattened_subreddits)))
        print('Wrote: {path}'.format(path=dirname))


def submission_example():
    # authenticate reddit and open subreddit
    reddit = open_reddit_instance()
    subreddit = reddit.subreddit('gravityfalls')

    # grab submissions (posts)
    top_ten_submissions = subreddit.top(limit=10)

    # grab top level comments as a list
    submission = [s for s in top_ten_submissions][0]
    submission.comment_sort = 'top'
    comments = submission.comments.list()

    # print comment text
    for comment in comments:
        print('*' * 80)
        print(comment.body)

    # print comments and replies
    comment_chain = traverse_comment_forest(comments)
    for chain in comment_chain:
        print(chain)


def main():
    reddit_data_dir = env_var('REDDIT_DATA_DIR') or REDDIT_DATA_DIR
    subreddit_dict_path = env_var('SUBREDDIT_DICT_PATH') or SUBREDDIT_DICT_PATH

    subreddit_dict = load_subreddit_dict(subreddit_dict_path)
    # create_directory_structure(subreddit_dict, reddit_data_dir)

    reddit = open_reddit_instance()
    download_reddit_data(reddit, subreddit_dict, reddit_data_dir)


if __name__ == '__main__':
    reddit = open_reddit_instance()
    try:
        main()
    except KeyboardInterrupt:
        pass
