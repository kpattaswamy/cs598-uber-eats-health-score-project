# cs598-uber-eats-health-score-project

## Setup datasets locally

1. `mkdir datasets`
2. `cd datasets/`
3. Download datasets from: `https://www.kaggle.com/datasets/ahmedshahriarsakib/uber-eats-usa-restaurants-menus?resource=download`

## Install requirements

`pip3 install -r requirements.txt`

## Usage

### Generate prompts to feed the LLM
```
python3 build-prompts.py --menus <path to restaurant-menus.csv> --restaurants <path to restaurants.csv> --output <path to store output>


e.g. python3 build-prompts.py --menus datasets/restaurant-menus.csv --restaurants datasets/restaurants.csv --output prompts.csv
```

The output csv schema contains two columns: `restaurant_id`, `summary`. Wrap the `summary` in a prompt asking a question to the LLM in order to fetch the healthiness score rated by the LLM. The `restaurant_id` can then be used to stitch together the healthiness score with the dataset.
