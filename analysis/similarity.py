import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def compare_restaurant_scores(file_path_1, file_path_2, score_column='restaurant_score'):
    """
    Reads two CSV files, compares the distribution of a specified score column,
    and saves a KDE plot to a file named 'restaurant_score_comparison.png'.

    Args:
        file_path_1 (str): Path to the first CSV file.
        file_path_2 (str): Path to the second CSV file.
        score_column (str): The name of the column containing the scores (default is 'restaurant_score').
    """
    try:
        df1 = pd.read_csv(file_path_1)
        df2 = pd.read_csv(file_path_2)

        if score_column not in df1.columns or score_column not in df2.columns:
            print(f"Error: The column '{score_column}' was not found in one or both CSV files.")
            print(f"Columns in CSV 1: {df1.columns.tolist()}")
            print(f"Columns in CSV 2: {df2.columns.tolist()}")
            return

        plt.figure(figsize=(10, 6))

        sns.kdeplot(df1[score_column], label='Dataset 1 Scores', fill=True, alpha=0.5, linewidth=2)

        sns.kdeplot(df2[score_column], label='Dataset 2 Scores', fill=True, alpha=0.5, linewidth=2)

        title = f'Comparison of {score_column.replace("_", " ").title()} Distributions'
        plt.title(title, fontsize=16)
        plt.xlabel(score_column.replace("_", " ").title(), fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)

        output_filename = 'restaurant_score_comparison.png'
        plt.savefig(output_filename)
        plt.close() 
        print(f"Comparison plot saved successfully to '{output_filename}'")
        print("Similarity can be visually assessed by how much the two distribution curves overlap.")

    except FileNotFoundError:
        print("Error: One of the CSV files was not found. Please check the file paths.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")