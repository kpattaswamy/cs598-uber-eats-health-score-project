import pandas as pd
import ollama
import re
import time
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = 'prompts-30.csv'       # Use 'prompts_test.csv' for testing!
OUTPUT_FILE = 'prompts_with_scores.csv'
INPUT_COL = 'summary'
OUTPUT_COL = 'nutrition_score'
# MODEL = 'tinyllama'
MODEL = 'llama3.2:3b-instruct-q8_0'
# ---------------------

def extract_score(text):
    """
    Extract score from response. More robust extraction that handles various formats.
    """
    if not text:
        return None
    
    # Strip whitespace and newlines
    text = text.strip()
    
    # Strategy 1: Direct conversion (if response is just "35" or "35\n")
    try:
        val = int(text)
        if 0 <= val <= 100:
            return val
    except ValueError:
        pass
    
    # Strategy 2: Look for number at the start of the line (common pattern)
    first_line = text.split('\n')[0].strip()
    match = re.match(r'^\s*(\d+)\s*$', first_line)
    if match:
        val = int(match.group(1))
        if 0 <= val <= 100:
            return val
    
    # Strategy 3: Look for "score: X" or "score is X" pattern (case insensitive)
    score_patterns = [
        r'score\s*:?\s*(\d+)',
        r'score\s+is\s+(\d+)',
        r'health\s+score\s*:?\s*(\d+)',
        r'rating\s*:?\s*(\d+)',
    ]
    for pattern in score_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 0 <= val <= 100:
                return val
    
    # Strategy 4: Extract all numbers and find the first valid one (0-100)
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
        
        # --- SIMPLIFIED PROMPT (Optimized for speed) ---
        prompt = (
            f"Rate restaurant healthiness 0-100. Ignore price. Consider: vegetables, whole grains, lean proteins vs fried/sugary/processed foods. "
            f"0-20=very unhealthy, 21-40=unhealthy, 41-60=average, 61-80=healthy, 81-100=very healthy. "
            f"Respond with ONLY a number 0-100.\n\n"
            f"{menu_summary}\n\n"
            f"Score:"
        )
        # ------------------------------------------------

        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Processing row {index+1}/{total}...", end="", flush=True)

        try:
            response = ollama.chat(model=MODEL, messages=[
                {
                    'role': 'system',
                    'content': 'Respond with ONLY a number 0-100. No text.'
                },
                {'role': 'user', 'content': prompt},
            ])
            
            raw_text = response['message']['content']
            score = extract_score(raw_text)
            
            # If we still can't find a score, use -1 to indicate error
            final_score = score if score is not None else -1
            scores.append(final_score)
            
            elapsed = time.time() - start_time
            if final_score == -1:
                # Log the raw response when extraction fails for debugging
                print(f" Done in {elapsed:.2f}s (score: {final_score}) [Failed to extract - raw response: '{raw_text[:100]}...']")
            else:
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