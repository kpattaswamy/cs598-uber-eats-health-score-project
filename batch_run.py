import pandas as pd
import ollama
import re

# --- CONFIGURATION ---
INPUT_FILE = 'prompts.csv'       # Use 'prompts_test.csv' for testing!
OUTPUT_FILE = 'prompts_with_scores.csv'
INPUT_COL = 'summary'
OUTPUT_COL = 'nutrition_score'
# MODEL = 'tinyllama'
MODEL = 'llama3.2'
# ---------------------

def extract_score(text):
    """
    Robust extraction:
    1. Looks specifically for "SCORE: <number>" (case insensitive).
    2. If that fails, looks for the LAST number in the text (0-100).
    """
    # STRATEGY 1: Look for the specific label we asked for
    # Matches "SCORE: 85", "Score: 85", "Score:85", etc.
    match = re.search(r'SCORE:\s*(\d+)', text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if 0 <= val <= 100:
            return val

    # STRATEGY 2: Fallback - use the LAST number found
    # (Models often explain first, then give the score at the end)
    matches = re.findall(r'\d+', text)
    if matches:
        # Filter for valid 0-100 numbers first
        valid_scores = [int(m) for m in matches if 0 <= int(m) <= 100]
        if valid_scores:
            # Return the last one found (most likely the conclusion)
            return valid_scores[-1]
            
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
        
        # --- UPDATED PROMPT (Added strict formatting) ---
        prompt = (
            f"You are a nutrition expert. Evaluate the menu items for this restaurant to assign a holistic health score "
            f"from 0 (extremely unhealthy) to 100 (extremely healthy).\n\n"
            f"Instructions:\n"
            f"1. IGNORE price. Focus on nutrient balance (veggies vs. sugar/fryer).\n"
            f"2. A score of 50 is average.\n"
            f"3. IMPORTANT: You must end your response with exactly 'SCORE: ' followed by the number.\n"
            f"   Example: '...therefore the healthy options are limited. SCORE: 45'\n\n"
            f"Menu Data: {menu_summary}"
        )
        # ------------------------------------------------

        if index % 10 == 0:
             print(f"Processing row {index+1}/{total}...")

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content']
            score = extract_score(raw_text)
            
            # If we still can't find a score, use -1 to indicate error
            final_score = score if score is not None else -1
            scores.append(final_score)
            
        except Exception as e:
            print(f"Error on row {index}: {e}")
            scores.append(-1)

    df[OUTPUT_COL] = scores
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_csv()