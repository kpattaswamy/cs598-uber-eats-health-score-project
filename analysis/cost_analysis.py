import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

os.makedirs('analysis/figures', exist_ok=True)

print("Loading datasets...")

scores_df = pd.read_csv('scored-datasets/uber_eats_menu_with_scores.csv')
ingredients_scores_df = pd.read_csv('scored-datasets/uber_eats_menu_with_ingredients_scores.csv')

print("Loading restaurant menus (this may take a moment)...")
menus_df = pd.read_csv('datasets/restaurant-menus.csv')

print("Calculating price ranges per restaurant...")
menus_df['price_float'] = menus_df['price'].str.replace(' USD', '', regex=False)
menus_df['price_float'] = pd.to_numeric(menus_df['price_float'], errors='coerce')

restaurant_prices = menus_df.groupby('restaurant_id')['price_float'].agg(['min', 'max', 'mean']).reset_index()
restaurant_prices.columns = ['restaurant_id', 'min_price', 'max_price', 'avg_price']

restaurant_prices = restaurant_prices.dropna(subset=['avg_price'])

print(f"Found prices for {len(restaurant_prices)} restaurants")

print("Merging price data with health scores...")
dataset1 = scores_df.merge(restaurant_prices, on='restaurant_id', how='inner')
dataset1 = dataset1.dropna(subset=['nutrition_score', 'avg_price'])

dataset2 = ingredients_scores_df.merge(restaurant_prices, on='restaurant_id', how='inner')
dataset2 = dataset2.dropna(subset=['healthiness_score', 'avg_price'])

print(f"Dataset 1 (pure-LLM): {len(dataset1)} restaurants")
print(f"Dataset 2 (ingredients-based LLM): {len(dataset2)} restaurants")

print("\n=== Statistical Analysis ===")

corr1, pval1 = stats.pearsonr(dataset1['avg_price'], dataset1['nutrition_score'])
print(f"\nDataset 1 - Pure-LLM Scoring vs Price:")
print(f"  Correlation coefficient: {corr1:.4f}")
print(f"  P-value: {pval1:.4e}")

corr2, pval2 = stats.pearsonr(dataset2['avg_price'], dataset2['healthiness_score'])
print(f"\nDataset 2 - Ingredients-based LLM Scoring vs Price:")
print(f"  Correlation coefficient: {corr2:.4f}")
print(f"  P-value: {pval2:.4e}")

print("\n=== Creating Visualizations ===")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ax1 = axes[0]
scatter1 = ax1.scatter(dataset1['avg_price'], dataset1['nutrition_score'], 
                      alpha=0.6, s=50, c=dataset1['nutrition_score'], 
                      cmap='viridis', edgecolors='black', linewidth=0.5)

z1 = np.polyfit(dataset1['avg_price'], dataset1['nutrition_score'], 1)
p1 = np.poly1d(z1)
ax1.plot(dataset1['avg_price'], p1(dataset1['avg_price']), 
         "r--", alpha=0.8, linewidth=2, label=f'Trend (r={corr1:.3f})')

ax1.set_xlabel('Average Price per Restaurant ($)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Nutrition Score', fontsize=12, fontweight='bold')
ax1.set_title('Pure-LLM Based Scoring Approach', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter1, ax=ax1, label='Nutrition Score')

ax2 = axes[1]
scatter2 = ax2.scatter(dataset2['avg_price'], dataset2['healthiness_score'], 
                      alpha=0.6, s=50, c=dataset2['healthiness_score'], 
                      cmap='plasma', edgecolors='black', linewidth=0.5)

z2 = np.polyfit(dataset2['avg_price'], dataset2['healthiness_score'], 1)
p2 = np.poly1d(z2)
ax2.plot(dataset2['avg_price'], p2(dataset2['avg_price']), 
         "r--", alpha=0.8, linewidth=2, label=f'Trend (r={corr2:.3f})')

ax2.set_xlabel('Average Price per Restaurant ($)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Nutrition Score', fontsize=12, fontweight='bold')
ax2.set_title('Ingredients-Based LLM Scoring Approach', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.colorbar(scatter2, ax=ax2, label='Nutrition Score')

plt.tight_layout()
plt.savefig('analysis/figures/correlation_analysis.png', bbox_inches='tight')
print("Saved: analysis/figures/correlation_analysis.png")

print("\n=== Saving Results ===")
summary_stats = {
    'metric': [
        'Pure-LLM - Correlation (nutrition_score)',
        'Pure-LLM - P-value',
        'Pure-LLM - Min Price',
        'Pure-LLM - Max Price',
        'Pure-LLM - Avg Price',
        'Ingredients-based LLM - Correlation (healthiness_score)',
        'Ingredients-based LLM - P-value',
        'Ingredients-based LLM - Min Price',
        'Ingredients-based LLM - Max Price',
        'Ingredients-based LLM - Avg Price',
    ],
    'value': [
        corr1,
        pval1,
        dataset1['min_price'].min(),
        dataset1['max_price'].max(),
        dataset1['avg_price'].mean(),
        corr2,
        pval2,
        dataset2['min_price'].min(),
        dataset2['max_price'].max(),
        dataset2['avg_price'].mean(),
    ]
}

summary_df = pd.DataFrame(summary_stats)
summary_df.to_csv('analysis/cost_analysis_results.csv', index=False)
print("Saved: analysis/cost_analysis_results.csv")

print("\n=== Analysis Complete ===")
print(f"All results saved to analysis/ directory")
