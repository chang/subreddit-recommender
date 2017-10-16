import json
import time

import requests
from bs4 import BeautifulSoup

from subreddit_recommender.src.util import data_dir_file, env_var


class TooManyRequestsError(Exception):
    """Exception to raise when 'too many requests' is encountered."""
    pass


def get_categorized_subreddit_list(sleep_time=2):
    try:
        _get_categorized_subreddit_list()
    except TooManyRequestsError:
        print('Rate limit reached.')
        time.sleep(sleep_time)
        get_categorized_subreddit_list(sleep_time + 2)


def _get_categorized_subreddit_list():
    SUBREDDIT_LIST_URL = 'https://www.reddit.com/r/ListOfSubreddits/wiki/listofsubreddits'
    headers = {'User-Agent': env_var('USER_AGENT')}
    req = requests.get(SUBREDDIT_LIST_URL, headers=headers)
    content = req.content.decode('utf-8')

    # createa BS object and check for too many requests response
    soup = BeautifulSoup(str(content), 'html.parser')
    if 'too many requests' in soup.title.get_text().lower():
        raise TooManyRequestsError('Rate limit reached.')

    # write to file for inspection
    pretty_file_path = data_dir_file('pretty_subreddits.html', subdir='processed')
    pretty_text = soup.prettify(encoding='utf-8')
    with open(pretty_file_path, 'wb') as file:
        file.write(pretty_text)

    # extract and write tags
    tag_types = ['h1', 'h2', 'a']
    tags = soup.find_all(tag_types)

    subreddit_dict = subreddits_to_dict(tags)
    subreddit_json = json.dumps(subreddit_dict, indent=4, sort_keys=True)

    with open(data_dir_file('subreddit_list.json', subdir='processed'), 'w') as file:
        file.write(subreddit_json)


def subreddits_to_dict(tags):
    """Organize subreddit list into the predefined hierarchy"""
    subreddit_dict = {}
    category = None
    subcategory = None
    subreddit = None
    content_reached = False  # flag indicating if the subreddit list has been reached

    for i, tag in enumerate(tags):
        # check if subreddit list has been reached
        if tag.get_text() == 'General Content' and tag.name == 'h1':
            content_reached = True

        if content_reached:
            tag_text = tag.get_text()

            if '.com' in tag_text:
                continue

            if tag.name == 'h1':
                category = tag_text
                subreddit_dict[category] = {}
            elif tag.name == 'h2':
                subcategory = tag_text
                subreddit_dict[category][subcategory] = []
            elif tag.name == 'a' and '/r/' in tag.text:
                subreddit = tag_text
                try:
                    subreddit_dict[category][subcategory].append(subreddit)
                except KeyError:
                    # when a new category appears but no new subcategory
                    subcategory = category
                    subreddit_dict[category][subcategory] = []
                    subreddit_dict[category][subcategory].append(subreddit)

    return subreddit_dict


if __name__ == '__main__':
    get_categorized_subreddit_list()
