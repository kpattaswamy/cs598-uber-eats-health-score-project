import pandas as pd
import argparse

def gen_prompts(menus_path, restaurants_path, output_path):
    menus = pd.read_csv(menus_path)
    restaurants = pd.read_csv(restaurants_path)

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
        categories = [
            f"{row['category_x']} ({row['items_count']} items, avg price ${row['average_price']:.2f})"
            for _, row in group.iterrows()
        ]
        cat_str = "; ".join(categories)
        sentence = (
            f"Restaurant: {meta['name']}, Price Range: {meta['price_range']}, "
            f"Zip Code: {meta['zip_code']}. Menu Categories: {cat_str}."
        )
        output_rows.append({'restaurant_id': restaurant_id, 'summary': sentence})

    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_path, index=False)

def main():
    parser = argparse.ArgumentParser(description="Generate restaurant menu category summaries.")
    parser.add_argument('--menus', required=True, help="Path to restaurant menus CSV file")
    parser.add_argument('--restaurants', required=True, help="Path to restaurants CSV file")
    parser.add_argument('--output', required=True, help="Path to output CSV file")

    args = parser.parse_args()

    gen_prompts(args.menus, args.restaurants, args.output)

if __name__ == "__main__":
    main()
