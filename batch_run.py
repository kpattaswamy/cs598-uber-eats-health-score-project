import pandas as pd
import ollama
import re
import time
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = 'prompts-truncated.csv'       # Use 'prompts_test.csv' for testing!
OUTPUT_FILE = 'prompts_with_scores.csv'
INPUT_COL = 'summary'
OUTPUT_COL = 'nutrition_score'
# MODEL = 'tinyllama'
MODEL = 'llama3.2:3b-instruct-q8_0'
# ---------------------

def extract_score(text):
    """
    Extract score from response. Expects only a number (0-100).
    Strips whitespace and converts to integer.
    """
    # Strip whitespace and try to convert directly
    text = text.strip()
    
    # Try direct conversion first (if response is just "35")
    try:
        val = int(text)
        if 0 <= val <= 100:
            return val
    except ValueError:
        pass
    
    # Fallback: extract first valid number (0-100) from the text
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
        
        # --- UPDATED PROMPT (Strict: only return the number) ---
        prompt = (
            f"You are a nutrition expert. Evaluate the menu items for this restaurant to assign a holistic health score "
            f"from 0 (extremely unhealthy) to 100 (extremely healthy).\n\n"
            f"Instructions:\n"
            f"1. IGNORE price. Focus on nutrient balance (veggies vs. sugar/fryer).\n"
            f"2. A score of 50 is average.\n"
            f"3. CRITICAL: Your response must contain ONLY the numeric score (0-100) with no other text, explanation, or formatting.\n"
            f"Menu Data: {menu_summary}"
        )
        # ------------------------------------------------

        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Processing row {index+1}/{total}...", end="", flush=True)

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content']
            score = extract_score(raw_text)
            
            # If we still can't find a score, use -1 to indicate error
            final_score = score if score is not None else -1
            scores.append(final_score)
            
            elapsed = time.time() - start_time
            print(f" Done in {elapsed:.2f}s (score: {final_score})")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f" Error after {elapsed:.2f}s: {e}")
            scores.append(-1)

    df[OUTPUT_COL] = scores
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_csv()