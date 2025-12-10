# cs598-uber-eats-health-score-project

## Setup datasets locally

Uber Eats Data

1. `mkdir datasets`
2. `cd datasets/`
3. Download datasets from: `https://www.kaggle.com/datasets/ahmedshahriarsakib/uber-eats-usa-restaurants-menus?resource=download`

USDA Datasets

1. `mkdir datasets/food_data`
2. `cd datasets/food_data`
3. Go to `https://fdc.nal.usda.gov/download-datasets` and download from Latest Downloads: Branded (most recent month) (most recent year) CSV

- ex: Branded April 2025 (CSV)
- necessary files: food.csv, nutrient.csv, food_nutrient

## Install requirements

Python Libraries
`pip3 install -r requirements.txt`

Ollama Setup

1. `brew install ollama`
2. `brew services start ollama`
3. `ollama pull llama3.2:3b-instruct-q8_0`

## Workflows

### Nutrition Score from Uber Eats Menu Descriptions

1. Generate Prompts

```
python3 uber-eats-menu-processing/build-prompts.py --menus <path to restaurant-menus.csv> --restaurants <path to restaurants.csv> --output <path to store output>


e.g. python3 uber-eats-menu-processing//buildPrompts.py --menus datasets/restaurant-menus.csv --restaurants datasets/restaurants.csv --output prompts.csv
```

2. `ollama-helpers/python batch_menu_run.py`
    Examine output in `prompts_with_scores.csv`

### Nutrition Score from Uber Eats Menu Descriptions along with ingredient details from Food Data Central Branded
1. Generate ingredients: `python batch_gen_ingredients.py`
2. TBD
3. TBD
4. TBD
