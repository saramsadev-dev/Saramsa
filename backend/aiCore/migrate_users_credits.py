"""
Migration script to add credit fields to existing users in Cosmos DB.

This script adds the following fields to all existing users:
- balance: Current credit balance
- total_earned: Lifetime credits earned
- total_spent: Lifetime credits spent

Usage:
    python manage.py shell
    >>> from aiCore.migrate_users_credits import migrate_users_credits
    >>> migrate_users_credits()
"""

from aiCore.cosmos_service import cosmos_service
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def migrate_users_credits(dry_run=False):
    """
    Add credit fields to all existing users.
    
    Args:
        dry_run: If True, only print what would be done without making changes
    
    Returns:
        dict: Migration statistics
    """
    try:
        # Get all users
        container = cosmos_service.get_container('users')
        query = "SELECT * FROM c WHERE c.type = 'user'"
        users = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        stats = {
            'total_users': len(users),
            'users_updated': 0,
            'users_skipped': 0,
            'errors': []
        }
        
        initial_credits = settings.INITIAL_USER_CREDITS
        
        for user in users:
            user_id = user.get('id')
            username = user.get('username', 'unknown')
            
            # Check if user already has credit fields
            if 'balance' in user and 'total_earned' in user and 'total_spent' in user:
                logger.info(f"User {username} ({user_id}) already has credit fields, skipping")
                stats['users_skipped'] += 1
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would add credits to user {username} ({user_id})")
                stats['users_updated'] += 1
                continue
            
            try:
                # Add credit fields
                user['balance'] = initial_credits
                user['total_earned'] = initial_credits
                user['total_spent'] = 0
                
                # Save updated user
                cosmos_service.save_user(user)
                logger.info(f"Added {initial_credits} credits to user {username} ({user_id})")
                stats['users_updated'] += 1
                
            except Exception as e:
                error_msg = f"Error updating user {username} ({user_id}): {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Total users found: {stats['total_users']}")
        print(f"Users updated: {stats['users_updated']}")
        print(f"Users skipped (already have credits): {stats['users_skipped']}")
        print(f"Errors: {len(stats['errors'])}")
        
        if stats['errors']:
            print("\nErrors encountered:")
            for error in stats['errors']:
                print(f"  - {error}")
        
        if dry_run:
            print("\n[DRY RUN MODE] No changes were made to the database.")
        else:
            print(f"\nSuccessfully migrated {stats['users_updated']} users.")
        
        print("="*60 + "\n")
        
        return stats
        
    except Exception as e:
        logger.exception(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    # Run migration
    print("Starting credit migration for existing users...")
    print("Running in DRY RUN mode first...\n")
    
    # First do a dry run
    migrate_users_credits(dry_run=True)
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with the actual migration? (yes/no): ")
    if response.lower() == 'yes':
        migrate_users_credits(dry_run=False)
    else:
        print("Migration cancelled.")
