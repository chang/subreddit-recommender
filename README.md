### Subreddit Recommender

[![Build Status](https://travis-ci.org/ericchang00/subreddit_recommender.svg?branch=master)](https://travis-ci.org/ericchang00/subreddit_recommender)

Using NLP to recommend subreddits.

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
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py
    │   │
    │   ├── data           <- Scripts to download and generate data.
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling.
    │   │   └── build_features.py
    │   │
    │   └── models         <- Scripts to train models.
    │
    ├── requirements.txt
    │
    └── tox.ini            


--------
