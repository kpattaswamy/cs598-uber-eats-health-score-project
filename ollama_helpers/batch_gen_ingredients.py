import pandas as pd
import ollama

MENU_FILE = 'datasets/restaurant-menus.csv'
RESTAURANT_FILE = 'datasets/restaurants.csv'
OUTPUT_FILE = 'restaurants_with_ingredients.csv'
INPUT_COL = 'description'
OUTPUT_COL = 'ingredients'
MODEL = 'llama3.2:3b-instruct-q8_0'


STATE = "DC"

def process_data():
    print(f"Reading {MENU_FILE} and {RESTAURANT_FILE}...")
    try:
        restaurant_menus_df = pd.read_csv(MENU_FILE)
        restaurants = pd.read_csv(RESTAURANT_FILE)
        
        restaurants['state'] = restaurants['full_address'].str.split(', ').str[-2]
        restaurants = restaurants[restaurants['state'] == STATE].copy()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    df = pd.merge(
        restaurant_menus_df,
        restaurants,
        left_on='restaurant_id',
        right_on='id',
        how='left',
        suffixes=('_menu', '_rest')
    )

    df.dropna(subset=['id'], inplace=True)

    
    if INPUT_COL not in df.columns:
        print(f"Error: Column '{INPUT_COL}' not found in the merged data.")
        return

    ingredients_list = []
    
    print(f"Starting ingredient generation with {MODEL}...")

    total = len(df)
    for index, row in df.iterrows():
        item_description = str(row[INPUT_COL])
        
        prompt = (
            f"You are a food scientist. Analyze the following menu item description and generate a single, "
            f"comma-separated list of the most likely ingredients. Focus on primary components (proteins, vegetables, grains, main sauces/spices).\n"
            f"DO NOT include any explanation, introduction, or extra text. Your entire response MUST be ONLY the comma-separated list of ingredients.\n\n"
            f"Menu Item Description: {item_description}"
        )

        print(f"Processing row {index+1}/{total}...")

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content'].strip()
            ingredients_list.append(raw_text)
            
        except Exception as e:
            print(f"Error on row {index}: {e}")
            ingredients_list.append("ERROR") 

    df[OUTPUT_COL] = ingredients_list
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_data()