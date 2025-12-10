import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def compare_restaurant_scores(file_path_1, file_path_2, score_column_file1='nutrition_score', score_column_file2='healthiness_score'):
    try:
        df1 = pd.read_csv(file_path_1)
        df2 = pd.read_csv(file_path_2)

        if score_column_file1 not in df1.columns or score_column_file2 not in df2.columns:
            print("Missing score column in csv file")
            print(f"Columns in CSV 1: {df1.columns.tolist()}")
            print(f"Columns in CSV 2: {df2.columns.tolist()}")
            return

        plt.figure(figsize=(10, 6))
        sns.kdeplot(df1[score_column_file1], label='uber_eats_menu_with_scores', fill=True, alpha=0.5, linewidth=2)
        sns.kdeplot(df2[score_column_file2], label='uber_eats_menu_with_ingredients_scores', fill=True, alpha=0.5, linewidth=2)

        title = f'Comparison of scores between the datasets'
        plt.title(title, fontsize=16)
        plt.xlabel("Score (1-100)", fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)

        output_filename = 'restaurant_score_comparison.png'
        plt.savefig(output_filename)
        plt.close() 

    except FileNotFoundError:
        print("Error: One of the CSV files was not found")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
compare_restaurant_scores('scored-datasets/uber_eats_menu_with_scores.csv', 'scored-datasets/uber_eats_menu_with_ingredients_scores.csv')