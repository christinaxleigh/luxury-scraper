"""
Script to add test user and wishlist items
Run this on Railway or locally with Supabase credentials set
"""
from models import get_session, User, WishlistItem

def add_test_data():
    client = get_session()

    # Add user
    print("Adding user...")
    user_result = User.create(
        client=client,
        email='christinasubs@gmail.com',
        location_country='US',
        location_state='CA'
    )

    if user_result.data:
        user = user_result.data[0]
        user_id = user['id']
        print(f"✓ User created with ID: {user_id}")

        # Add wishlist items
        wishlists = [
            {
                'brand': 'Hermès',
                'item_type': 'bag',
                'model_name': 'Kelly 25 Epsom Sellier',
                'max_price': 16000,
                'priority': 'high'
            },
            {
                'brand': 'Chanel',
                'item_type': 'bag',
                'model_name': 'Classic Flap Medium Gold Caviar',
                'max_price': 7000,
                'priority': 'high'
            },
            {
                'brand': 'The Row',
                'item_type': 'bag',
                'model_name': 'Margaux 15',
                'max_price': 4000,
                'priority': 'medium'
            }
        ]

        for wishlist in wishlists:
            result = WishlistItem.create(
                client=client,
                user_id=user_id,
                **wishlist
            )
            if result.data:
                item = result.data[0]
                print(f"✓ Added wishlist: {item['brand']} {item['model_name']} (ID: {item['id']})")

        print("\n✅ All test data added successfully!")
    else:
        print("❌ Failed to create user")

if __name__ == "__main__":
    add_test_data()
