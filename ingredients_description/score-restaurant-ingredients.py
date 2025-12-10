# import pandas as pd
# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process
# from typing import List, Dict, Any, Optional
# import numpy as np # Import for NaN handling

# # --- CONFIGURATION ---
# FOOD_CSV_PATH = 'datasets/food_data/food.csv'
# NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
# FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'

# FUZZY_MATCH_THRESHOLD = 75

# # Daily Recommended Intakes (DRI)
# # Source: Assumptions provided by the user
# DRI_CALORIES = 2000.0   # kcal/day
# DRI_SODIUM = 2000.0     # mg/day
# DRI_PROTEIN = 85.0      # g/day

# # Ideal amount for one meal (1/3 of daily)
# IDEAL_CALORIES_PER_MEAL = DRI_CALORIES / 3.0
# IDEAL_SODIUM_PER_MEAL = DRI_SODIUM / 3.0
# IDEAL_PROTEIN_PER_MEAL = DRI_PROTEIN / 3.0

# # Global variables for dataframes
# food_df: Optional[pd.DataFrame] = None
# merged_df: Optional[pd.DataFrame] = None

# def load_and_preprocess_data():
#     """Loads and prepares the food database."""
#     global food_df, merged_df
#     try:
#         print("Loading food database...")
#         food_data = pd.read_csv(FOOD_CSV_PATH)
#         nutrient_data = pd.read_csv(NUTRIENT_CSV_PATH)
#         food_nutrient_data = pd.read_csv(FOOD_NUTRIENT_CSV_PATH)

#         # Normalize columns
#         food_data.columns = food_data.columns.str.lower().str.strip()
#         nutrient_data.columns = nutrient_data.columns.str.lower().str.strip()
#         food_nutrient_data.columns = food_nutrient_data.columns.str.lower().str.strip()

#         # Prepare main tables
#         food_df = food_data[['fdc_id', 'description']]
#         food_df['description'] = food_df['description'].fillna('').astype(str)
        
#         nutrient_data = nutrient_data[['id', 'name', 'unit_name']]
#         nutrient_data.rename(columns={'id': 'nutrient_id'}, inplace=True)
        
#         food_nutrient_data = food_nutrient_data[['fdc_id', 'nutrient_id', 'amount']]

#         merged_df = food_nutrient_data.merge(nutrient_data, on='nutrient_id', how='left')
#         print("Data loaded successfully.")
#         return True
#     except Exception as e:
#         print(f"Error loading data: {e}")
#         return False

# def get_nutrition_info(ingredient_name: str) -> Dict[str, Any]:
#     """Finds nutrition info for a single ingredient string."""
#     if merged_df is None or food_df is None:
#         return {}

#     # Convert the series to a list first using .tolist()
#     choices_list = food_df['description'].tolist()

#     best_match = process.extractOne(
#         query=ingredient_name,
#         choices=choices_list,
#         scorer=fuzz.ratio
#     )

#     # Check if match exists and meets threshold
#     if not best_match or best_match[1] < FUZZY_MATCH_THRESHOLD:
#         return {}

#     food_desc, score = best_match

#     # Retrieve the FDC ID
#     fdc_id = food_df[food_df['description'] == food_desc]['fdc_id'].iloc[0]

#     # Get nutrients
#     nutrients = merged_df[merged_df['fdc_id'] == fdc_id]

#     # Extract specific values (default to 0.0 if missing)
#     cal = nutrients[nutrients['name'] == 'Energy']['amount'].mean()
#     sod = nutrients[nutrients['name'] == 'Sodium, Na']['amount'].mean()
#     prot = nutrients[nutrients['name'] == 'Protein']['amount'].mean()

#     return {
#         'calories': float(cal) if pd.notna(cal) else 0.0,
#         'sodium': float(sod) if pd.notna(sod) else 0.0,
#         'protein': float(prot) if pd.notna(prot) else 0.0
#     }

# def process_restaurants(input_file='restaurants_with_ingredients.csv', output_file='restaurant_averages.csv'):
#     if not load_and_preprocess_data():
#         return

#     print(f"Reading {input_file}...")
#     try:
#         df = pd.read_csv(input_file)
#     except FileNotFoundError:
#         print("Input file not found.")
#         return

#     # Store item-level averages here
#     item_stats = []

#     print("Processing menu items...")
#     for idx, row in df.iterrows():
#         ingredients_str = str(row['ingredients'])
#         ingredients = [x.strip() for x in ingredients_str.split(',') if x.strip()]

#         # Lists to hold values for the ingredients in THIS item
#         i_cals, i_sods, i_prots = [], [], []

#         for ing in ingredients:
#             info = get_nutrition_info(ing)
#             if info:
#                 i_cals.append(info['calories'])
#                 i_sods.append(info['sodium'])
#                 i_prots.append(info['protein'])
        
#         # Calculate average for the menu item
#         avg_cal = sum(i_cals) / len(i_cals) if i_cals else None
#         avg_sod = sum(i_sods) / len(i_sods) if i_sods else None
#         avg_prot = sum(i_prots) / len(i_prots) if i_prots else None

#         item_stats.append({
#             'restaurant_id': row['restaurant_id'],
#             'item_calories': avg_cal,
#             'item_sodium': avg_sod,
#             'item_protein': avg_prot
#         })

#         if (idx + 1) % 100 == 0:
#             print(f"Processed {idx + 1} items...")

#     # Create a temporary dataframe with item-level stats
#     items_df = pd.DataFrame(item_stats)

#     print("Aggregating by Restaurant ID...")
#     # Group by restaurant_id and take the mean across all menu items
#     final_df = items_df.groupby('restaurant_id').mean().reset_index()

#     # Rename columns
#     final_df.rename(columns={
#         'item_calories': 'average_calories',
#         'item_sodium': 'average_sodium',
#         'item_protein': 'average_protein'
#     }, inplace=True)
    
#     # --- HEALTHINESS SCORE CALCULATION ---
#     print("Calculating Healthiness Score...")
    
#     # To prevent Division by Zero, we use numpy's isfinite check
#     # We will compute the ratio components. If the average is NaN or 0, the ratio will be NaN.
    
#     # 1. Calculate Ratios (Ideal / Average)
#     final_df['ratio_cal'] = np.where(
#         (final_df['average_calories'].values > 0) & np.isfinite(final_df['average_calories'].values),
#         IDEAL_CALORIES_PER_MEAL / final_df['average_calories'],
#         np.nan # Use NaN if division is impossible
#     )
    
#     final_df['ratio_sod'] = np.where(
#         (final_df['average_sodium'].values > 0) & np.isfinite(final_df['average_sodium'].values),
#         IDEAL_SODIUM_PER_MEAL / final_df['average_sodium'],
#         np.nan
#     )
    
#     final_df['ratio_prot'] = np.where(
#         (final_df['average_protein'].values > 0) & np.isfinite(final_df['average_protein'].values),
#         IDEAL_PROTEIN_PER_MEAL / final_df['average_protein'],
#         np.nan
#     )
    
#     # 2. Calculate the average of the three ratios
#     # .mean(axis=1) safely ignores NaNs in the row when calculating the mean
#     final_df['avg_ratios'] = final_df[['ratio_cal', 'ratio_sod', 'ratio_prot']].mean(axis=1)
    
#     # 3. Calculate Final Score (Average Ratio * 100)
#     # The score is capped at 200 for presentation purposes, but theoretically can be higher
#     final_df['healthiness_score'] = (final_df['avg_ratios'] * 100).round(2)
    
#     # Clean up intermediate columns
#     final_df.drop(columns=['ratio_cal', 'ratio_sod', 'ratio_prot', 'avg_ratios'], inplace=True)

#     # Save to CSV
#     final_df.to_csv(output_file, index=False)
#     print(f"Done! Aggregated data saved to '{output_file}'.")
#     print("\n--- Final Restaurant Averages and Scores (First 5 Rows) ---")
#     print(final_df.head())

# if __name__ == '__main__':
#     process_restaurants()

import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional
import numpy as np

# --- CONFIGURATION ---
FOOD_CSV_PATH = 'datasets/food_data/food.csv'
NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'

FUZZY_MATCH_THRESHOLD = 75

# Daily Recommended Intakes (DRI) based on user's input
DRI_CALORIES = 2000.0   # kcal/day
DRI_SODIUM = 2000.0     # mg/day
DRI_PROTEIN = 85.0      # g/day

# Ideal amount for one meal (1/3 of daily)
IDEAL_CALORIES_PER_MEAL = DRI_CALORIES / 3.0
IDEAL_SODIUM_PER_MEAL = DRI_SODIUM / 3.0
IDEAL_PROTEIN_PER_MEAL = DRI_PROTEIN / 3.0

# Global variables for dataframes
food_df: Optional[pd.DataFrame] = None
merged_df: Optional[pd.DataFrame] = None

def load_and_preprocess_data():
    """Loads and prepares the food database."""
    global food_df, merged_df
    try:
        print("Loading food database...")
        food_data = pd.read_csv(FOOD_CSV_PATH)
        nutrient_data = pd.read_csv(NUTRIENT_CSV_PATH)
        food_nutrient_data = pd.read_csv(FOOD_NUTRIENT_CSV_PATH)

        # Normalize columns
        food_data.columns = food_data.columns.str.lower().str.strip()
        nutrient_data.columns = nutrient_data.columns.str.lower().str.strip()
        food_nutrient_data.columns = food_nutrient_data.columns.str.lower().str.strip()

        # Prepare main tables
        food_df = food_data[['fdc_id', 'description']]
        food_df['description'] = food_df['description'].fillna('').astype(str)

        nutrient_data = nutrient_data[['id', 'name', 'unit_name']]
        nutrient_data.rename(columns={'id': 'nutrient_id'}, inplace=True)

        food_nutrient_data = food_nutrient_data[['fdc_id', 'nutrient_id', 'amount']]

        merged_df = food_nutrient_data.merge(nutrient_data, on='nutrient_id', how='left')
        print("Data loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def get_nutrition_info(ingredient_name: str) -> Dict[str, Any]:
    """Finds nutrition info for a single ingredient string using fuzzy matching."""
    if merged_df is None or food_df is None:
        return {}

    # Convert the series to a list first using .tolist() to ensure (match, score) unpacking
    choices_list = food_df['description'].tolist()

    best_match = process.extractOne(
        query=ingredient_name,
        choices=choices_list,
        scorer=fuzz.ratio
    )

    # Check if match exists and meets threshold
    if not best_match or best_match[1] < FUZZY_MATCH_THRESHOLD:
        return {}

    food_desc, score = best_match

    # Retrieve the FDC ID
    # Use loc for safer access
    fdc_id = food_df.loc[food_df['description'] == food_desc, 'fdc_id'].iloc[0]

    # Get nutrients
    nutrients = merged_df[merged_df['fdc_id'] == fdc_id]

    # Extract specific values (using .mean() handles multiple entries per nutrient ID if they exist)
    cal = nutrients[nutrients['name'] == 'Energy']['amount'].mean()
    sod = nutrients[nutrients['name'] == 'Sodium, Na']['amount'].mean()
    prot = nutrients[nutrients['name'] == 'Protein']['amount'].mean()

    return {
        'calories': float(cal) if pd.notna(cal) else 0.0,
        'sodium': float(sod) if pd.notna(sod) else 0.0,
        'protein': float(prot) if pd.notna(prot) else 0.0
    }

def process_restaurants(input_file='restaurants_with_ingredients.csv', output_file='restaurant_averages_v2.csv'):
    if not load_and_preprocess_data():
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Input file not found.")
        return

    item_stats = []

    print("Processing menu items (calculating item-level nutrient averages)...")
    for idx, row in df.iterrows():
        ingredients_str = str(row['ingredients'])
        ingredients = [x.strip() for x in ingredients_str.split(',') if x.strip()]

        i_cals, i_sods, i_prots = [], [], []

        for ing in ingredients:
            info = get_nutrition_info(ing)
            if info:
                i_cals.append(info['calories'])
                i_sods.append(info['sodium'])
                i_prots.append(info['protein'])

        # Calculate average for the menu item (None/NaN if no ingredients found)
        avg_cal = sum(i_cals) / len(i_cals) if i_cals else None
        avg_sod = sum(i_sods) / len(i_sods) if i_sods else None
        avg_prot = sum(i_prots) / len(i_prots) if i_prots else None

        item_stats.append({
            'restaurant_id': row['restaurant_id'],
            'item_calories': avg_cal,
            'item_sodium': avg_sod,
            'item_protein': avg_prot
        })

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1} items...")

    # Create a temporary dataframe with item-level stats
    items_df = pd.DataFrame(item_stats)

    print("Aggregating by Restaurant ID (calculating restaurant-level averages)...")
    # Group by restaurant_id and take the mean across all menu items
    final_df = items_df.groupby('restaurant_id').mean().reset_index()

    # Rename columns
    final_df.rename(columns={
        'item_calories': 'average_calories',
        'item_sodium': 'average_sodium',
        'item_protein': 'average_protein'
    }, inplace=True)

    # --- HEALTHINESS SCORE CALCULATION V2: Distance from Ideal ---
    print("Calculating Healthiness Score V2 (0-100)...")

    # Helper for calculating the penalty ratio for Calorie/Sodium (Deviation from Ideal)
    def calculate_deviation_ratio(ideal, avg_series):
        # 1 - |Avg Nutrient - Ideal Nutrient| / Ideal Nutrient
        diff = np.abs(avg_series - ideal)

        # Calculate raw ratio, safely handling division by zero/NaN
        ratio_raw = np.where(
            (avg_series.values > 0) & np.isfinite(avg_series.values),
            1.0 - (diff / ideal),
            0.0 # Assign 0.0 if data is missing or zero
        )
        # Ensure the final score is not negative (e.g., if calories are massive, ratio can be < 0)
        return np.maximum(0.0, ratio_raw)

    # 1. Calorie Ratio (Deviation)
    final_df['ratio_cal'] = calculate_deviation_ratio(IDEAL_CALORIES_PER_MEAL, final_df['average_calories'])

    # 2. Sodium Ratio (Deviation)
    final_df['ratio_sod'] = calculate_deviation_ratio(IDEAL_SODIUM_PER_MEAL, final_df['average_sodium'])

    # 3. Protein Ratio (Meet/Exceed Ideal - Capped at 1.0)
    # min(1, Avg Prot / Ideal Prot)
    ratio_prot_raw = np.where(
        (final_df['average_protein'].values > 0) & np.isfinite(final_df['average_protein'].values),
        final_df['average_protein'] / IDEAL_PROTEIN_PER_MEAL,
        0.0
    )
    final_df['ratio_prot'] = np.minimum(1.0, ratio_prot_raw)

    # 4. Calculate the average of the three ratios (This is the final score ratio)
    final_df['avg_ratios'] = final_df[['ratio_cal', 'ratio_sod', 'ratio_prot']].mean(axis=1)

    # 5. Calculate Final Score (Average Ratio * 100)
    final_df['healthiness_score'] = (final_df['avg_ratios'] * 100).round(2)

    # Clean up intermediate columns
    final_df.drop(columns=['ratio_cal', 'ratio_sod', 'ratio_prot', 'avg_ratios'], inplace=True)

    # Save to CSV
    final_df.to_csv(output_file, index=False)
    print(f"\nSuccess! Aggregated data saved to '{output_file}'.")
    print("\n--- Final Restaurant Averages and Healthiness Scores (Score V2) ---")
    print(final_df.head(10))

if __name__ == '__main__':
    process_restaurants()
