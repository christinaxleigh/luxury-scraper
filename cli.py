"""
CLI tool for managing users and wishlist items
"""
import argparse
from models import init_db, get_session, User, WishlistItem
from datetime import datetime
import json

def add_user(email: str, country: str = "US", state: str = None, zip_code: str = None):
    """Add a new user"""
    session = get_session()
    
    try:
        # Check if user exists
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            print(f"User {email} already exists (ID: {existing.id})")
            return existing.id
        
        # Create new user
        user = User(
            email=email,
            location_country=country,
            location_state=state,
            location_zip=zip_code
        )
        session.add(user)
        session.commit()
        
        print(f"✓ User created successfully!")
        print(f"  Email: {user.email}")
        print(f"  ID: {user.id}")
        print(f"  Location: {user.location_state}, {user.location_country}")
        
        return user.id
        
    except Exception as e:
        session.rollback()
        print(f"Error adding user: {e}")
        return None
    finally:
        session.close()

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
    session = get_session()
    
    try:
        # Check if user exists
        user = session.query(User).get(user_id)
        if not user:
            print(f"Error: User ID {user_id} not found")
            return None
        
        # Create wishlist item
        wishlist = WishlistItem(
            user_id=user_id,
            brand=brand,
            item_type=item_type,
            model_name=model_name,
            size=size,
            color=color,
            min_price=min_price,
            max_price=max_price,
            condition_new=condition_new,
            condition_excellent=condition_excellent,
            condition_good=condition_good,
            condition_fair=condition_fair,
            priority=priority
        )
        session.add(wishlist)
        session.commit()
        
        print(f"✓ Wishlist item created successfully!")
        print(f"  ID: {wishlist.id}")
        print(f"  Brand: {wishlist.brand}")
        if wishlist.model_name:
            print(f"  Model: {wishlist.model_name}")
        if wishlist.item_type:
            print(f"  Type: {wishlist.item_type}")
        if wishlist.max_price:
            print(f"  Max Price: ${wishlist.max_price:,.2f}")
        print(f"  Priority: {wishlist.priority}")
        
        return wishlist.id
        
    except Exception as e:
        session.rollback()
        print(f"Error adding wishlist item: {e}")
        return None
    finally:
        session.close()

def list_users():
    """List all users"""
    session = get_session()
    
    try:
        users = session.query(User).all()
        
        if not users:
            print("No users found.")
            return
        
        print(f"\n{'='*80}")
        print(f"{'ID':<5} {'Email':<30} {'Location':<25} {'Active':<10} {'Created'}")
        print(f"{'='*80}")
        
        for user in users:
            location = f"{user.location_state or ''}, {user.location_country or ''}"
            active = "Yes" if user.active else "No"
            created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
            
            print(f"{user.id:<5} {user.email:<30} {location:<25} {active:<10} {created}")
        
        print(f"{'='*80}\n")
        
    finally:
        session.close()

def list_wishlists(user_id: int = None):
    """List wishlist items"""
    session = get_session()
    
    try:
        query = session.query(WishlistItem)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        items = query.all()
        
        if not items:
            print("No wishlist items found.")
            return
        
        print(f"\n{'='*100}")
        print(f"{'ID':<5} {'User':<20} {'Brand':<15} {'Model/Type':<25} {'Price Range':<20} {'Active'}")
        print(f"{'='*100}")
        
        for item in items:
            user_email = item.user.email if item.user else "N/A"
            model_type = item.model_name or item.item_type or "Any"
            
            if item.min_price and item.max_price:
                price_range = f"${item.min_price:,.0f} - ${item.max_price:,.0f}"
            elif item.max_price:
                price_range = f"Up to ${item.max_price:,.0f}"
            else:
                price_range = "Any"
            
            active = "Yes" if item.active else "No"
            
            print(f"{item.id:<5} {user_email:<20} {item.brand:<15} {model_type:<25} {price_range:<20} {active}")
        
        print(f"{'='*100}\n")
        
    finally:
        session.close()

def delete_wishlist(wishlist_id: int):
    """Delete a wishlist item"""
    session = get_session()
    
    try:
        item = session.query(WishlistItem).get(wishlist_id)
        if not item:
            print(f"Error: Wishlist item {wishlist_id} not found")
            return
        
        session.delete(item)
        session.commit()
        print(f"✓ Wishlist item {wishlist_id} deleted successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error deleting wishlist item: {e}")
    finally:
        session.close()

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
