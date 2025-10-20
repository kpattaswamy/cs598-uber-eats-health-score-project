import pandas as pd

menus = pd.read_csv("datasets/restaurant-menus.csv")
restaurants = pd.read_csv("datasets/restaurants.csv")

menus['price_float'] = menus['price'].str.replace(' USD', '', regex=False).astype(float)

category_stats = menus.groupby(['restaurant_id', 'category']).agg(
    items_count=('name', 'count'),
    average_price=('price_float', 'mean')
).reset_index()

merged_df = pd.merge(
    category_stats,
    restaurants,
    left_on='restaurant_id',
    right_on='id',
    how='left'
)

output_rows = []
for restaurant_id, group in merged_df.groupby('restaurant_id'):
    meta = group.iloc[0]
    categories = []
    for _, row in group.iterrows():
        categories.append(
            f"{row['category_x']} ({row['items_count']} items, avg price ${row['average_price']:.2f})"
        )
    cat_str = "; ".join(categories)
    sentence = (
        f"Restaurant: {meta['name']}, Price Range: {meta['price_range']}, "
        f"Zip Code: {meta['zip_code']}. Menu Categories: {cat_str}."
    )
    output_rows.append({'restaurant_id': restaurant_id, 'summary': sentence})

# Save to CSV
output_df = pd.DataFrame(output_rows)
output_df.to_csv("prompts.csv", index=False)

