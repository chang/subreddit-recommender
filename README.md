## Subreddit Recommender

[![Build Status](https://travis-ci.org/ericchang00/subreddit_recommender.svg?branch=master)](https://travis-ci.org/ericchang00/subreddit_recommender)

Using natural language processing and deep feature embeddings to recommend subreddits.

#### Project Organization
------------

    ├── README.md
    ├── data
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── models             <- Trained and serialized models.
    │
    ├── src
    │   ├── __init__.py
    │   │
    │   ├── data           <- Scripts to download and generate data.
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling.
    │   │
    │   └── models         <- Scripts to train models.
    │
    ├── tests
    │
    ├── requirements.txt
    │
    └── tox.ini            


--------

#### Installation

Create a virtual environment and install the dependencies.

```bash
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Create a file called `.env` in the root of the project directory with your reddit API keys in the format below. Downloading the data is quite slow, so it will multithread with as many keys as you have available.

```bash
CLIENT_0=api_key:api_id
CLIENT_1=api_key:api_id
```

Run the data extraction scripts.

```bash
python src/data/make_subreddit_list.py
python src/data/download_reddit_data.py
```
