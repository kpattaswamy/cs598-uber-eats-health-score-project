import pandas as pd
import ollama
import re

# --- CONFIGURATION ---
INPUT_FILE = 'prompts-truncated.csv'       # Switch this to 'prompts_test.csv' if testing
OUTPUT_FILE = 'prompts_with_scores.csv'
INPUT_COL = 'summary'
OUTPUT_COL = 'nutrition_score'
MODEL = 'tinyllama'
# ---------------------

def extract_score(text):
    """
    Finds the first integer between 0 and 100 in the text.
    """
    matches = re.findall(r'\d+', text)
    if matches:
        for match in matches:
            val = int(match)
            if 0 <= val <= 100:
                return val
    return None

def process_csv():
    print(f"Reading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    if INPUT_COL not in df.columns:
        print(f"Error: Column '{INPUT_COL}' not found.")
        return

    scores = []
    
    print(f"Starting analysis with {MODEL}...")

    total = len(df)
    for index, row in df.iterrows():
        menu_summary = str(row[INPUT_COL])
        
        # --- UPDATED PROMPT ---
        prompt = (
            f"You are a nutrition expert. Evaluate the menu items for this restaurant to assign a holistic health score "
            f"from 0 (extremely unhealthy) to 100 (extremely healthy). "
            f"A score of 50 represents an average restaurant with mixed options.\n\n"
            f"Instructions:\n"
            f"1. IGNORE all price information. Focus ONLY on the food categories and items.\n"
            f"2. Consider the balance of nutrients (vegetables vs. fried foods vs. sugar).\n"
            f"3. Respond with ONLY the numeric score (e.g., 65).\n\n"
            f"Menu Data: {menu_summary}"
        )
        # ----------------------

        # Progress log every 1 row (since you are testing small batches now)
        if index % 1 == 0:
             print(f"Processing row {index+1}/{total}...")

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content']
            score = extract_score(raw_text)
            
            # Default to None if no number found, or you could use 50 as a neutral fallback
            final_score = score if score is not None else -1
            scores.append(final_score)
            
        except Exception as e:
            print(f"Error on row {index}: {e}")
            scores.append(-1)

    # Assign the new column
    df[OUTPUT_COL] = scores

    # Save to CSV (The 'raw_response' column is gone)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_csv()