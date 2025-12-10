import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional
import numpy as np
import time

FOOD_CSV_PATH = 'datasets/food_data/food.csv'
NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'

FUZZY_MATCH_THRESHOLD = 75
DRI_CALORIES = 2000.0
DRI_SODIUM = 2000.0
DRI_PROTEIN = 85.0
IDEAL_CALORIES_PER_MEAL = DRI_CALORIES / 3.0
IDEAL_SODIUM_PER_MEAL = DRI_SODIUM / 3.0
IDEAL_PROTEIN_PER_MEAL = DRI_PROTEIN / 3.0

food_df: Optional[pd.DataFrame] = None
merged_df: Optional[pd.DataFrame] = None
nutrition_lookup: Dict[str, Dict[str, float]] = {}

def load_and_preprocess_data():
    global food_df, merged_df
    try:
        print("Loading food csv")
        food_data = pd.read_csv(FOOD_CSV_PATH)
        nutrient_data = pd.read_csv(NUTRIENT_CSV_PATH)
        food_nutrient_data = pd.read_csv(FOOD_NUTRIENT_CSV_PATH)
        food_data.columns = food_data.columns.str.lower().str.strip()
        nutrient_data.columns = nutrient_data.columns.str.lower().str.strip()
        food_nutrient_data.columns = food_nutrient_data.columns.str.lower().str.strip()

        food_df = food_data[['fdc_id', 'description']].copy()
        food_df['description'] = food_df['description'].fillna('').astype(str)

        nutrient_data = nutrient_data[['id', 'name', 'unit_name']]
        nutrient_data.rename(columns={'id': 'nutrient_id'}, inplace=True)

        food_nutrient_data = food_nutrient_data[['fdc_id', 'nutrient_id', 'amount']]

        merged_df = food_nutrient_data.merge(nutrient_data, on='nutrient_id', how='left')
        return True
    except Exception as e:
        return False

def get_nutrition_info(ingredient_name: str) -> Dict[str, Any]:
    if merged_df is None or food_df is None:
        return {}

    choices_list = food_df['description'].tolist()
    best_match = process.extractOne(
        query=ingredient_name,
        choices=choices_list,
        scorer=fuzz.ratio
    )

    if not best_match or best_match[1] < FUZZY_MATCH_THRESHOLD:
        return {}

    food_desc, score = best_match
    fdc_id = food_df.loc[food_df['description'] == food_desc, 'fdc_id'].iloc[0]
    nutrients = merged_df[merged_df['fdc_id'] == fdc_id]
    cal = nutrients[nutrients['name'] == 'Energy']['amount'].mean()
    sod = nutrients[nutrients['name'] == 'Sodium, Na']['amount'].mean()
    prot = nutrients[nutrients['name'] == 'Protein']['amount'].mean()

    return {
        'calories': float(cal) if pd.notna(cal) else 0.0,
        'sodium': float(sod) if pd.notna(sod) else 0.0,
        'protein': float(prot) if pd.notna(prot) else 0.0
    }

def create_nutrition_lookup_table(input_df: pd.DataFrame):
    global nutrition_lookup

    start_time = time.time()

    all_ingredients = input_df['ingredients'].str.split(',').explode().str.strip().dropna().unique()
    for idx, ingredient in enumerate(all_ingredients):
        if ingredient not in nutrition_lookup:
            nutrition_lookup[ingredient] = get_nutrition_info(ingredient)

        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(all_ingredients)} unique ingredients...")

    end_time = time.time()

def process_restaurants(input_file='restaurants_with_ingredients.csv', output_file='restaurant_averages_v2.csv'):

    main_start_time = time.time()

    if not load_and_preprocess_data():
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Input file not found.")
        return

    create_nutrition_lookup_table(df)

    item_stats = []

    for idx, row in df.iterrows():
        ingredients_str = str(row['ingredients'])
        ingredients = [x.strip() for x in ingredients_str.split(',') if x.strip()]

        i_cals, i_sods, i_prots = [], [], []

        for ing in ingredients:
            info = nutrition_lookup.get(ing, {})
            if info:
                i_cals.append(info['calories'])
                i_sods.append(info['sodium'])
                i_prots.append(info['protein'])

        avg_cal = sum(i_cals) / len(i_cals) if i_cals else None
        avg_sod = sum(i_sods) / len(i_sods) if i_sods else None
        avg_prot = sum(i_prots) / len(i_prots) if i_prots else None

        item_stats.append({
            'restaurant_id': row['restaurant_id'],
            'item_calories': avg_cal,
            'item_sodium': avg_sod,
            'item_protein': avg_prot
        })

        if (idx + 1) % 500 == 0:
            print(f"  Processed {idx + 1} items...")

    items_df = pd.DataFrame(item_stats)

    final_df = items_df.groupby('restaurant_id').mean().reset_index()

    final_df.rename(columns={
        'item_calories': 'average_calories',
        'item_sodium': 'average_sodium',
        'item_protein': 'average_protein'
    }, inplace=True)

    def calculate_deviation_ratio(ideal, avg_series):
        diff = np.abs(avg_series - ideal)

        ratio_raw = np.where(
            (avg_series.values > 0) & np.isfinite(avg_series.values),
            1.0 - (diff / ideal),
            0.0
        )
        return np.maximum(0.0, ratio_raw)

    final_df['ratio_cal'] = calculate_deviation_ratio(IDEAL_CALORIES_PER_MEAL, final_df['average_calories'])
    final_df['ratio_sod'] = calculate_deviation_ratio(IDEAL_SODIUM_PER_MEAL, final_df['average_sodium'])

    ratio_prot_raw = np.where(
        (final_df['average_protein'].values > 0) & np.isfinite(final_df['average_protein'].values),
        final_df['average_protein'] / IDEAL_PROTEIN_PER_MEAL,
        0.0
    )
    final_df['ratio_prot'] = np.minimum(1.0, ratio_prot_raw)
    final_df['avg_ratios'] = final_df[['ratio_cal', 'ratio_sod', 'ratio_prot']].mean(axis=1)
    final_df['healthiness_score'] = (final_df['avg_ratios'] * 100).round(2)
    final_df.drop(columns=['ratio_cal', 'ratio_sod', 'ratio_prot', 'avg_ratios'], inplace=True)
    final_df.to_csv(output_file, index=False)

    print("\nFinal Restaurant Averages and Healthiness Scores:")
    print(final_df.head(10))

if __name__ == '__main__':
    process_restaurants()
