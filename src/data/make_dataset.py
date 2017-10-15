# -*- coding: utf-8 -*-
import praw
from subreddit_recommender.utils import load_env


def get_subreddit_list():
    pass


def open_reddit():
    env = load_env()
    reddit = praw.Reddit(
        client_id=env['CLIENT_ID'],
        client_secret=env['CLIENT_SECRET'],
        user_agent=env['USER_AGENT']
    )
    subreddit = reddit.subreddit('redditdev')
    print(subreddit.display_name)  # Output: redditdev
    print(subreddit.title)         # Output: reddit Development
    print(subreddit.description)   # Output: A subreddit for discussion of ...


def main():
    pass


if __name__ == '__main__':
    pass
