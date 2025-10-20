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

restaurant_category_stats = {}
restaurant_meta = {}
current_id = None

for _, row in merged_df.iterrows():
    rid = row['restaurant_id']

    if rid != current_id:
        if current_id is not None:
            meta = restaurant_meta
            print(f"Restaurant: {meta['name']}")
            print(f"Price Range: {meta['price_range']}")
            print(f"Zip Code: {meta['zip_code']}")
            print("Menu Categories:")
            for cat_info in restaurant_category_stats.values():
                print(f"  - Category: {cat_info['category_x']}, Items Count: {cat_info['items_count']}, Average Price: ${cat_info['average_price']:.2f}")
            print()
            restaurant_category_stats.clear()
            restaurant_meta.clear()

        current_id = rid
        restaurant_meta['name'] = row['name']
        restaurant_meta['price_range'] = row['price_range']
        restaurant_meta['zip_code'] = row['zip_code']

    restaurant_category_stats[row['category_x']] = {
        'category_x': row['category_x'],     # category_x' is the menu category column from menus.csv after merge
        'items_count': row['items_count'],
        'average_price': row['average_price']
    }

# Print last restaurant data
if current_id is not None:
    meta = restaurant_meta
    print(f"Restaurant: {meta['name']}")
    print(f"Price Range: {meta['price_range']}")
    print(f"Zip Code: {meta['zip_code']}")
    print("Menu Categories:")
    for cat_info in restaurant_category_stats.values():
        print(f"  - Category: {cat_info['category_x']}, Items Count: {cat_info['items_count']}, Average Price: ${cat_info['average_price']:.2f}")