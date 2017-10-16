# -*- coding: utf-8 -*-
import os
import os.path as op
import shutil
import time
from multiprocessing.dummy import Pool as ThreadPool
from timeit import default_timer

import praw

from subreddit_recommender.src.util import (data_dir, data_dir_subreddit,
                                            load_json, parse_client_ids,
                                            valid_subreddit_dirname)

TOP_N_SUBMISSIONS = 20
COMMENT_DEPTH = 4
VERBOSE = 1


def open_reddit_instance(credentials):
    """Returns an authenticated praw.Reddit instance.

    Attributes:
        credentials: tuple of string
            (client_id, client_secret)
    """
    client_id, client_secret = credentials
    user_agent = 'mac:subreddit_recommender_{h}:v1'.format(h=hash(client_id))
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
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


def create_directory_structure(subreddit_dict, raw_data_dirname='reddit_raw', overwrite=False):
    """Create the directory structure for storing reddit data.

    Args:
        subreddit_dict (dict):
        reddit_data_dir (str): Path to reddit data directory.
        overwrite (bool): If True, overwrites all existing data in the directory.
    """
    reddit_data_dir = op.join(data_dir('raw'), raw_data_dirname)
    if overwrite:
        shutil.rmtree(reddit_data_dir)

    flattened_subreddits = flatten_subreddit_dict(subreddit_dict)
    for cat, subcat, subreddit in flattened_subreddits:
        path = data_dir_subreddit(cat, subcat, subreddit)
        try:
            os.makedirs(path)
        except OSError:
            continue

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


def get_subreddit_submissions(subreddit, top_n_submissions, comment_depth, verbose=VERBOSE, worker_id=None):
    """Given a subreddit object, returns a list of submissions.

    Attributes:
        subreddit: praw.models.Subreddit
        top_n_submissions: int
        comment_depth: int

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
            if worker_id is not None:
                msg = 'Worker {id_}: '.format(id_=worker_id) + msg

            print(msg.format(i=i, n=top_n_submissions, title=_decode_utf(subreddit.display_name)))

    return submission_comment_chains


def worker(payload):
    """Performs data downloading"""

    # unzip payload
    subreddit_tuples, worker_id, reddit = payload
    print('Worker #{id_} has entered the game.'.format(id_=worker_id))
    time.sleep(1)

    for sub_id, (cat, subcat, subreddit) in enumerate(subreddit_tuples):
        # download and write description
        t0 = default_timer()
        if cat == 'Defunct':
            continue
        subreddit = valid_subreddit_dirname(subreddit)
        praw_subreddit = reddit.subreddit(subreddit)

        try:
            description = _decode_utf(praw_subreddit.description)
        except Exception:
            description = ''

        # download and write top_n_submissions
        submissions = get_subreddit_submissions(praw_subreddit,
                                                top_n_submissions=TOP_N_SUBMISSIONS,
                                                comment_depth=COMMENT_DEPTH,
                                                worker_id=worker_id,
                                                verbose=0)

        # write to file
        path = data_dir_subreddit(cat, subcat, subreddit)
        with open(op.join(path, 'description'), 'w') as file:
            file.write(description)
        for i, sub in enumerate(submissions):
            with open(op.join(path, 'sub_{i}'.format(i=i)), 'w') as file:
                file.write(_decode_utf(sub))

        msg = 'Worker #{id_}: {sub_id} / {total} complete. Time elapsed: {time}s\n'
        msg += 'Wrote to: {path}\n'
        print(msg.format(id_=worker_id,
                         sub_id=sub_id,
                         total=len(subreddit_tuples),
                         time=round(default_timer() - t0, 2),
                         path=path))


def split_list(arr, n):
    """Split a list into n chunks."""
    return [arr[i::n] for i in range(n)]


def download_reddit_data(subreddit_dict, reddit_data_dir,
                         top_n_submissions=TOP_N_SUBMISSIONS, comment_depth=COMMENT_DEPTH):
    """Downloads all relevant data from subreddits specified in the subreddit dict.

    Downloads to raw data folder. Currently downloads the following data
    - subreddit description
    - subreddit wiki text
    - all comments from top_n_submissions posts

    Args:
        subreddit_dict (dict): Dictionary of subreddits, organized by the hierarchy:
                               Category | Subcategory | List of subreddits
        reddit_data_dir (str): Subdirectory of data/raw to store data.
        top_n_submissions (n): Number of posts to scrape comments from.
    """
    N_THREADS = 10
    flattened_subreddits = flatten_subreddit_dict(subreddit_dict)

    # split subreddit tuples
    split_subreddits = split_list(flattened_subreddits, N_THREADS)

    # make reddit instances
    credentials = parse_client_ids()
    assert len(credentials) >= N_THREADS, 'Need as many credential sets as threads.'
    credentials = credentials[0:N_THREADS]
    reddit_instances = [open_reddit_instance(cred) for cred in credentials]

    # worker ids
    worker_ids = [i for i in range(N_THREADS)]

    # zip payloads
    payloads = [payload for payload in zip(split_subreddits, worker_ids, reddit_instances)]

    pool = ThreadPool(N_THREADS)
    pool.map(worker, payloads)
    print('COMPLETE ' * 100)


def submission_example():
    # authenticate reddit and open subreddit
    client_id, client_secret = parse_client_ids()[0]
    reddit = open_reddit_instance(client_id, client_secret)
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
    reddit_data_dir = op.join(data_dir('raw'), 'reddit_raw')
    subreddit_dict_path = op.join(data_dir('raw'), 'subreddit_list.json')
    subreddit_dict = load_json(subreddit_dict_path)

    create_directory_structure(subreddit_dict, reddit_data_dir, overwrite=False)
    download_reddit_data(subreddit_dict, reddit_data_dir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
