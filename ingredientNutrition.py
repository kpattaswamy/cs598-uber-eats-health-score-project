import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import List, Dict, Any, Optional

FOOD_CSV_PATH = 'datasets/food_data/food.csv'
NUTRIENT_CSV_PATH = 'datasets/food_data/nutrient.csv'
FOOD_NUTRIENT_CSV_PATH = 'datasets/food_data/food_nutrient.csv'

FUZZY_MATCH_THRESHOLD = 75 # TODO: Adjust threshold as needed

food_df: Optional[pd.DataFrame] = None
merged_df: Optional[pd.DataFrame] = None

def load_and_preprocess_data():
    """
    Loads, cleans, and merges the necessary CSV data into global DataFrames.
    Returns True if successful, False otherwise.
    """
    global food_df, merged_df
    try:
        print("Loading data...")
        food_data = pd.read_csv(FOOD_CSV_PATH)
        nutrient_data = pd.read_csv(NUTRIENT_CSV_PATH)
        food_nutrient_data = pd.read_csv(FOOD_NUTRIENT_CSV_PATH)

        food_data.columns = food_data.columns.str.lower().str.strip()
        nutrient_data.columns = nutrient_data.columns.str.lower().str.strip()
        food_nutrient_data.columns = food_nutrient_data.columns.str.lower().str.strip()

        food_df = food_data[['fdc_id', 'description']]
        
        food_df['description'] = food_df['description'].fillna('').astype(str)
        
        nutrient_data = nutrient_data[['id', 'name', 'unit_name']]
        nutrient_data.rename(columns={'id': 'nutrient_id'}, inplace=True)
        
        food_nutrient_data = food_nutrient_data[['fdc_id', 'nutrient_id', 'amount']]

        merged_df = food_nutrient_data.merge(nutrient_data, on='nutrient_id', how='left')
        print("Data loaded and preprocessed successfully.")
        return True
    
    except FileNotFoundError as e:
        print(f"\n--- ERROR: FILE NOT FOUND ---")
        print(f"The required CSV file was not found: {e.filename}")
        print(f"Please ensure '{e.filename}' is in the correct directory.")
        print(f"-----------------------------\n")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return False


def get_nutrition_info_function(ingredient_name: str) -> Dict[str, Any]:
    """
    Performs a fuzzy search on food descriptions and outputs nutrition information 
    for the best match.

    Args:
        ingredient_name: The name of the ingredient to search for.

    Returns:
        A dictionary containing the search results, match details, and nutrition facts.
    """
    if merged_df is None or food_df is None:
        return {
            "error": "Data not initialized.",
            "message": "Please call load_and_preprocess_data() and ensure all CSV files are present and correct."
        }

    food_descriptions = food_df['description'].tolist()
    
    best_match_result: Optional[tuple] = process.extractOne(
        query=ingredient_name, 
        choices=food_descriptions, 
        scorer=fuzz.ratio
    )

    if not best_match_result:
        return {
            "search_query": ingredient_name,
            "error": "No food data found to search against."
        }
        
    food_description, similarity_score = best_match_result

    if similarity_score < FUZZY_MATCH_THRESHOLD:
        return {
            "search_query": ingredient_name,
            "error": "No close match found.",
            "message": f"Best match '{food_description}' only had a similarity score of {similarity_score}, which is below the threshold of {FUZZY_MATCH_THRESHOLD}."
        }

    # Find the fdc_id for the matched description
    fdc_id = food_df[food_df['description'] == food_description]['fdc_id'].iloc[0]

    nutrition_data = merged_df[merged_df['fdc_id'] == fdc_id]

    if nutrition_data.empty:
        return {
            "search_query": ingredient_name,
            "matched_food": food_description,
            "fdc_id": int(fdc_id),
            "match_score": similarity_score,
            "error": "No nutrition data available for this food item."
        }

    nutrition_list = []
    for _, row in nutrition_data.iterrows():
        amount = row['amount']
        
        nutrition_list.append({
            "nutrient_name": row['name'],
            "amount": float(amount) if pd.notna(amount) and amount is not None else 0.0,
            "unit": row['unit_name']
        })

    nutrition_list.sort(key=lambda x: x['nutrient_name'])

    return {
        "search_query": ingredient_name,
        "matched_food": food_description,
        "fdc_id": int(fdc_id),
        "match_score": similarity_score,
        "nutrition_facts": nutrition_list
    }

''' 
# Example usage 
if __name__ == '__main__':
    if load_and_preprocess_data():
        
        search_term_1 = "aple"
        print(f"\n--- Searching for: '{search_term_1}' ---")
        result_1 = get_nutrition_info_function(search_term_1)
        print(result_1)

        search_term_2 = "chocolate milk" 
        print(f"\n--- Searching for: '{search_term_2}' ---")
        result_2 = get_nutrition_info_function(search_term_2)
        print(result_2)
        
        # A term that shouldn't meet the threshold
        search_term_3 = "asdnasdioejqoiwejqw"
        print(f"\n--- Searching for: '{search_term_3}' ---")
        result_3 = get_nutrition_info_function(search_term_3)
        print(result_3)
'''