"""
CLI tool for managing users and wishlist items
"""
import argparse
from models import init_db, get_session, User, WishlistItem
from datetime import datetime
import json

def add_user(email: str, country: str = "US", state: str = None, zip_code: str = None):
    """Add a new user"""
    client = get_session()

    try:
        # Check if user exists
        existing = client.table('users').select('*').eq('email', email).execute()
        if existing.data:
            user = existing.data[0]
            print(f"User {email} already exists (ID: {user['id']})")
            return user['id']

        # Create new user
        result = User.create(
            client=client,
            email=email,
            location_country=country,
            location_state=state
        )

        if result.data:
            user = result.data[0]
            print(f"✓ User created successfully!")
            print(f"  Email: {user['email']}")
            print(f"  ID: {user['id']}")
            print(f"  Location: {user.get('location_state')}, {user.get('location_country')}")
            return user['id']
        else:
            print("Error: Failed to create user")
            return None

    except Exception as e:
        print(f"Error adding user: {e}")
        return None

def add_wishlist_item(
    user_id: int,
    brand: str,
    item_type: str = None,
    model_name: str = None,
    size: str = None,
    color: str = None,
    min_price: float = None,
    max_price: float = None,
    condition_new: bool = True,
    condition_excellent: bool = True,
    condition_good: bool = True,
    condition_fair: bool = False,
    priority: str = "medium"
):
    """Add a wishlist item for a user"""
    client = get_session()

    try:
        # Check if user exists
        user_check = client.table('users').select('id').eq('id', user_id).execute()
        if not user_check.data:
            print(f"Error: User ID {user_id} not found")
            return None

        # Create wishlist item
        result = WishlistItem.create(
            client=client,
            user_id=user_id,
            brand=brand,
            max_price=max_price,
            item_type=item_type,
            model_name=model_name,
            size=size,
            color=color,
            min_price=min_price,
            condition_new=condition_new,
            condition_excellent=condition_excellent,
            condition_good=condition_good,
            condition_fair=condition_fair,
            priority=priority
        )

        if result.data:
            wishlist = result.data[0]
            print(f"✓ Wishlist item created successfully!")
            print(f"  ID: {wishlist['id']}")
            print(f"  Brand: {wishlist['brand']}")
            if wishlist.get('model_name'):
                print(f"  Model: {wishlist['model_name']}")
            if wishlist.get('item_type'):
                print(f"  Type: {wishlist['item_type']}")
            if wishlist.get('max_price'):
                print(f"  Max Price: ${wishlist['max_price']:,.2f}")
            print(f"  Priority: {wishlist.get('priority', 'medium')}")
            return wishlist['id']
        else:
            print("Error: Failed to create wishlist item")
            return None

    except Exception as e:
        print(f"Error adding wishlist item: {e}")
        return None

def list_users():
    """List all users"""
    client = get_session()

    try:
        result = client.table('users').select('*').execute()
        users = result.data

        if not users:
            print("No users found.")
            return

        print(f"\n{'='*80}")
        print(f"{'ID':<5} {'Email':<30} {'Location':<25} {'Active':<10} {'Created'}")
        print(f"{'='*80}")

        for user in users:
            location = f"{user.get('location_state') or ''}, {user.get('location_country') or ''}"
            active = "Yes" if user.get('active', True) else "No"
            created_str = user.get('created_at', 'N/A')
            if created_str != 'N/A':
                from dateutil import parser
                try:
                    created = parser.parse(created_str).strftime("%Y-%m-%d")
                except:
                    created = created_str[:10] if len(created_str) >= 10 else created_str
            else:
                created = "N/A"

            print(f"{user['id']:<5} {user['email']:<30} {location:<25} {active:<10} {created}")

        print(f"{'='*80}\n")

    except Exception as e:
        print(f"Error listing users: {e}")

def list_wishlists(user_id: int = None):
    """List wishlist items"""
    client = get_session()

    try:
        if user_id:
            result = client.table('wishlist_items').select('*, users(email)').eq('user_id', user_id).execute()
        else:
            result = client.table('wishlist_items').select('*, users(email)').execute()

        items = result.data

        if not items:
            print("No wishlist items found.")
            return

        print(f"\n{'='*100}")
        print(f"{'ID':<5} {'User':<20} {'Brand':<15} {'Model/Type':<25} {'Price Range':<20} {'Active'}")
        print(f"{'='*100}")

        for item in items:
            # Handle user email from joined data
            user_email = "N/A"
            if 'users' in item and item['users']:
                if isinstance(item['users'], dict):
                    user_email = item['users'].get('email', 'N/A')
                elif isinstance(item['users'], list) and len(item['users']) > 0:
                    user_email = item['users'][0].get('email', 'N/A')

            model_type = item.get('model_name') or item.get('item_type') or "Any"

            min_price = item.get('min_price')
            max_price = item.get('max_price')
            if min_price and max_price:
                price_range = f"${min_price:,.0f} - ${max_price:,.0f}"
            elif max_price:
                price_range = f"Up to ${max_price:,.0f}"
            else:
                price_range = "Any"

            active = "Yes" if item.get('active', True) else "No"

            print(f"{item['id']:<5} {user_email:<20} {item['brand']:<15} {model_type:<25} {price_range:<20} {active}")

        print(f"{'='*100}\n")

    except Exception as e:
        print(f"Error listing wishlists: {e}")

def delete_wishlist(wishlist_id: int):
    """Delete a wishlist item"""
    client = get_session()

    try:
        # Check if item exists
        check = client.table('wishlist_items').select('id').eq('id', wishlist_id).execute()
        if not check.data:
            print(f"Error: Wishlist item {wishlist_id} not found")
            return

        # Delete the item
        client.table('wishlist_items').delete().eq('id', wishlist_id).execute()
        print(f"✓ Wishlist item {wishlist_id} deleted successfully")

    except Exception as e:
        print(f"Error deleting wishlist item: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Luxury Scraper Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Init database
    init_parser = subparsers.add_parser('init', help='Initialize database')
    
    # Add user
    user_parser = subparsers.add_parser('add-user', help='Add a new user')
    user_parser.add_argument('email', help='User email address')
    user_parser.add_argument('--country', default='US', help='Country code (default: US)')
    user_parser.add_argument('--state', help='State/Province')
    user_parser.add_argument('--zip', help='Zip/Postal code')
    
    # Add wishlist
    wish_parser = subparsers.add_parser('add-wishlist', help='Add a wishlist item')
    wish_parser.add_argument('user_id', type=int, help='User ID')
    wish_parser.add_argument('brand', help='Brand name (e.g., Chanel)')
    wish_parser.add_argument('--type', dest='item_type', help='Item type (e.g., handbag)')
    wish_parser.add_argument('--model', help='Model name (e.g., Classic Flap)')
    wish_parser.add_argument('--size', help='Size specification')
    wish_parser.add_argument('--color', help='Preferred color')
    wish_parser.add_argument('--min-price', type=float, help='Minimum price')
    wish_parser.add_argument('--max-price', type=float, help='Maximum price')
    wish_parser.add_argument('--priority', choices=['high', 'medium', 'low'], default='medium')
    wish_parser.add_argument('--no-new', action='store_true', help='Exclude new condition')
    wish_parser.add_argument('--no-excellent', action='store_true', help='Exclude excellent condition')
    wish_parser.add_argument('--no-good', action='store_true', help='Exclude good condition')
    wish_parser.add_argument('--fair', action='store_true', help='Include fair condition')
    
    # List users
    list_users_parser = subparsers.add_parser('list-users', help='List all users')
    
    # List wishlists
    list_wish_parser = subparsers.add_parser('list-wishlists', help='List wishlist items')
    list_wish_parser.add_argument('--user-id', type=int, help='Filter by user ID')
    
    # Delete wishlist
    del_parser = subparsers.add_parser('delete-wishlist', help='Delete a wishlist item')
    del_parser.add_argument('wishlist_id', type=int, help='Wishlist item ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'init':
        print("Initializing database...")
        init_db()
        print("✓ Database initialized successfully!")
        
    elif args.command == 'add-user':
        add_user(args.email, args.country, args.state, args.zip)
        
    elif args.command == 'add-wishlist':
        add_wishlist_item(
            user_id=args.user_id,
            brand=args.brand,
            item_type=args.item_type,
            model_name=args.model,
            size=args.size,
            color=args.color,
            min_price=args.min_price,
            max_price=args.max_price,
            condition_new=not args.no_new,
            condition_excellent=not args.no_excellent,
            condition_good=not args.no_good,
            condition_fair=args.fair,
            priority=args.priority
        )
        
    elif args.command == 'list-users':
        list_users()
        
    elif args.command == 'list-wishlists':
        list_wishlists(args.user_id)
        
    elif args.command == 'delete-wishlist':
        delete_wishlist(args.wishlist_id)

if __name__ == "__main__":
    main()
