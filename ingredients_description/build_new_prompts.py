import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional

# --- CONFIGURATION ---
FOOD_CSV_PATH = 'datasets/food_data/food.csv'
NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'
FUZZY_MATCH_THRESHOLD = 75

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
    """Finds nutrition info for a single ingredient string."""
    if merged_df is None or food_df is None:
        return {}

    # FIX: Convert the series to a list first using .tolist()
    # This ensures extractOne returns only (match, score)
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
    fdc_id = food_df[food_df['description'] == food_desc]['fdc_id'].iloc[0]

    # Get nutrients
    nutrients = merged_df[merged_df['fdc_id'] == fdc_id]

    # Extract specific values (default to 0.0 if missing)
    cal = nutrients[nutrients['name'] == 'Energy']['amount'].mean()
    sod = nutrients[nutrients['name'] == 'Sodium, Na']['amount'].mean()
    prot = nutrients[nutrients['name'] == 'Protein']['amount'].mean()

    return {
        'calories': float(cal) if pd.notna(cal) else 0.0,
        'sodium': float(sod) if pd.notna(sod) else 0.0,
        'protein': float(prot) if pd.notna(prot) else 0.0
    }

def process_restaurants(input_file='restaurants_with_ingredients.csv', output_file='restaurant_averages.csv'):
    if not load_and_preprocess_data():
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Input file not found.")
        return

    # Store item-level averages here
    item_stats = []

    print("Processing menu items...")
    for idx, row in df.iterrows():
        ingredients_str = str(row['ingredients'])
        ingredients = [x.strip() for x in ingredients_str.split(',') if x.strip()]

        # Lists to hold values for the ingredients in THIS item
        i_cals, i_sods, i_prots = [], [], []

        for ing in ingredients:
            info = get_nutrition_info(ing)
            if info:
                i_cals.append(info['calories'])
                i_sods.append(info['sodium'])
                i_prots.append(info['protein'])
        
        # Calculate average for the menu item
        # (If a menu item has no valid ingredients, we treat it as None/NaN to avoid skewing the restaurant average with 0s)
        avg_cal = sum(i_cals) / len(i_cals) if i_cals else None
        avg_sod = sum(i_sods) / len(i_sods) if i_sods else None
        avg_prot = sum(i_prots) / len(i_prots) if i_prots else None

        item_stats.append({
            'restaurant_id': row['restaurant_id'],
            'item_calories': avg_cal,
            'item_sodium': avg_sod,
            'item_protein': avg_prot
        })

        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1} items...")

    # Create a temporary dataframe with item-level stats
    items_df = pd.DataFrame(item_stats)

    print("Aggregating by Restaurant ID...")
    # Group by restaurant_id and take the mean across all menu items for that restaurant
    final_df = items_df.groupby('restaurant_id').mean().reset_index()

    # Rename columns for clarity
    final_df.rename(columns={
        'item_calories': 'average_calories',
        'item_sodium': 'average_sodium',
        'item_protein': 'average_protein'
    }, inplace=True)

    # Save to CSV
    final_df.to_csv(output_file, index=False)
    print(f"Done! Aggregated data saved to '{output_file}'.")
    print(final_df.head())

if __name__ == '__main__':
    process_restaurants()
