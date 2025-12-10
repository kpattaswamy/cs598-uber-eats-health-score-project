import pandas as pd
import ollama
import re

# --- CONFIGURATION ---
INPUT_FILE = 'prompts-truncated.csv'     
OUTPUT_FILE = 'prompts_with_scores.csv'
INPUT_COL = 'summary'          # The column containing the menu text
OUTPUT_COL = 'nutrition_score' # The new column for the score
MODEL = 'tinyllama'            
# ---------------------

def extract_score(text):
    """
    Tries to find a number between 0-100 in the response text.
    Returns the first valid number found, or None if it fails.
    """
    # Look for one or more digits
    matches = re.findall(r'\d+', text)
    if matches:
        # Take the last number found (often the most conclusive one if it lists criteria)
        # or just the first one. Let's try the first distinct number that is <= 100
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

    # Check if summary column exists
    if INPUT_COL not in df.columns:
        print(f"Error: Column '{INPUT_COL}' not found. Available columns: {list(df.columns)}")
        return

    scores = []
    explanations = [] # Optional: Capture the raw text just in case the parsing fails

    print(f"Starting analysis with {MODEL}. This may take a while depending on row count...")
    
    total = len(df)
    for index, row in df.iterrows():
        menu_summary = str(row[INPUT_COL])
        
        # Construct a strict prompt for TinyLlama
        prompt = (
            f"You are a strict nutrition expert. "
            f"Evaluate the healthiness of this restaurant based on its menu categories and items. "
            f"Assign a health score from 0 (very unhealthy) to 100 (very healthy). "
            f"IMPORTANT: Respond with ONLY the numeric score. Do not write any other words.\n\n"
            f"Restaurant Menu: {menu_summary}"
        )

        if index % 5 == 0:
            print(f"Processing row {index+1}/{total}...")

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content']
            score = extract_score(raw_text)
            
            # If extracting failed, store -1 or keep empty
            final_score = score if score is not None else -1
            
            scores.append(final_score)
            explanations.append(raw_text) # Storing raw text is helpful for debugging
            
        except Exception as e:
            print(f"Error on row {index}: {e}")
            scores.append(-1)
            explanations.append("Error")

    # Add results to dataframe
    df[OUTPUT_COL] = scores
    df['raw_response'] = explanations # Useful to see why a score might be -1

    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Processed {total} rows.")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_csv()