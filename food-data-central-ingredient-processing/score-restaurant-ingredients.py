import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional
import numpy as np

FOOD_CSV_PATH = 'datasets/food_data/food.csv'
NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'

FUZZY_MATCH_THRESHOLD = 75
DRI_CALORIES = 2000.0
DRI_SODIUM = 2000.0
DRI_PROTEIN = 85.0
MAX_INGREDIENTS_PER_ITEM = 4

IDEAL_CALORIES_PER_MEAL = DRI_CALORIES / 3.0
IDEAL_SODIUM_PER_MEAL = DRI_SODIUM / 3.0
IDEAL_PROTEIN_PER_MEAL = DRI_PROTEIN / 3.0

food_df: Optional[pd.DataFrame] = None
merged_df: Optional[pd.DataFrame] = None
nutrition_lookup: Dict[str, Dict[str, float]] = {}

def load_and_preprocess_data():
    global food_df, merged_df
    try:
        print("Loading food csv...")
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
        print(f"Error loading data: {e}")
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


    if MAX_INGREDIENTS_PER_ITEM and MAX_INGREDIENTS_PER_ITEM > 0:
        def limit_ingredients(ingredients_str):
            if pd.isna(ingredients_str):
                return []
            return [x.strip() for x in str(ingredients_str).split(',') if x.strip()][:MAX_INGREDIENTS_PER_ITEM]

        all_ingredients = input_df['ingredients'].apply(limit_ingredients).explode().dropna().unique()
    else:
        all_ingredients = input_df['ingredients'].str.split(',').explode().str.strip().dropna().unique()

    for idx, ingredient in enumerate(all_ingredients):
        if ingredient not in nutrition_lookup:
            nutrition_lookup[ingredient] = get_nutrition_info(ingredient)

        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(all_ingredients)} unique ingredients...")

    successful_matches = len([k for k, v in nutrition_lookup.items() if v])

def process_restaurants(input_file='restaurants_with_ingredients.csv', output_file='restaurant_averages_with_scores.csv'):

    if not load_and_preprocess_data():
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Input file not found.")
        return

    create_nutrition_lookup_table(df)

    if MAX_INGREDIENTS_PER_ITEM and MAX_INGREDIENTS_PER_ITEM > 0:
        def split_and_limit(ingredients_str):
            if pd.isna(ingredients_str):
                return []
            return [x.strip() for x in str(ingredients_str).split(',') if x.strip()][:MAX_INGREDIENTS_PER_ITEM]

        ingredients_exploded_df = df.set_index(['restaurant_id', df.index]).ingredients.apply(split_and_limit).explode().reset_index()
    else:
        ingredients_exploded_df = df.set_index(['restaurant_id', df.index]).ingredients.str.split(',').explode().reset_index()

    ingredients_exploded_df.rename(columns={'level_1': 'menu_item_index', 'ingredients': 'ingredient_name'}, inplace=True)
    ingredients_exploded_df['ingredient_name'] = ingredients_exploded_df['ingredient_name'].str.strip()
    lookup_df = pd.DataFrame.from_dict(nutrition_lookup, orient='index').reset_index()
    lookup_df.rename(columns={'index': 'ingredient_name'}, inplace=True)

    merged_ingredients_df = ingredients_exploded_df.merge(lookup_df, on='ingredient_name', how='left')

    item_averages_df = merged_ingredients_df.groupby(['restaurant_id', 'menu_item_index']).mean(numeric_only=True).reset_index()

    final_df = item_averages_df.groupby('restaurant_id').mean(numeric_only=True).reset_index()

    final_df.rename(columns={
        'item_calories': 'average_calories',
        'item_sodium': 'average_sodium',
        'item_protein': 'average_protein'
    }, inplace=True)


    print("Calculating Healthiness Score V2 (0-100)...")

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

    final_df.drop(columns=['menu_item_index', 'ratio_cal', 'ratio_sod', 'ratio_prot', 'avg_ratios'], inplace=True, errors='ignore')

    final_df.to_csv(output_file, index=False)


    print("\nFinal Restaurant Averages and Healthiness Scores:")
    print(final_df.head(10))

if __name__ == '__main__':
    process_restaurants()
