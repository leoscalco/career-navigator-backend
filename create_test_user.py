#!/usr/bin/env python3
"""
Script to create a test user with email and password for login testing.
Usage: poetry run python create_test_user.py
"""
import sys
from career_navigator.infrastructure.database.session import get_db
from career_navigator.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from career_navigator.domain.models.user import User as DomainUser
from career_navigator.domain.models.user_group import UserGroup
from career_navigator.domain.services.auth_service import AuthService

def create_test_user(email: str, password: str, username: str = None):
    """Create a test user with email and password."""
    db = next(get_db())
    repository = SQLAlchemyUserRepository(db)
    
    # Check if user already exists
    existing_user = repository.get_by_email(email)
    if existing_user:
        print(f"❌ User with email {email} already exists!")
        print(f"   User ID: {existing_user.id}")
        print(f"   Username: {existing_user.username}")
        print(f"   Has password: {bool(existing_user.password_hash)}")
        
        # Update password if user exists but has no password
        if not existing_user.password_hash:
            print(f"\n🔄 Updating password for existing user...")
            password_hash = AuthService.get_password_hash(password)
            updated_user = DomainUser(
                id=existing_user.id,
                email=existing_user.email,
                username=existing_user.username,
                password_hash=password_hash,
                is_active=True,
                is_verified=False,
                user_group=existing_user.user_group,
            )
            repository.update(updated_user)
            print(f"✅ Password updated successfully!")
            print(f"   You can now login with:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            return
        
        response = input(f"\n❓ User exists. Update password? (y/n): ")
        if response.lower() == 'y':
            password_hash = AuthService.get_password_hash(password)
            updated_user = DomainUser(
                id=existing_user.id,
                email=existing_user.email,
                username=existing_user.username,
                password_hash=password_hash,
                is_active=True,
                is_verified=False,
                user_group=existing_user.user_group,
            )
            repository.update(updated_user)
            print(f"✅ Password updated successfully!")
        else:
            print("❌ Cancelled.")
        return
    
    # Generate username if not provided
    if not username:
        username = email.split("@")[0]
    
    # Check username uniqueness
    all_users = repository.get_all()
    existing_usernames = {u.username for u in all_users if u.username}
    base_username = username
    counter = 1
    while username in existing_usernames:
        username = f"{base_username}_{counter}"
        counter += 1
    
    # Hash password
    password_hash = AuthService.get_password_hash(password)
    
    # Create user
    new_user = DomainUser(
        email=email,
        username=username,
        password_hash=password_hash,
        user_group=UserGroup.INEXPERIENCED_NO_GOAL,
        is_active=True,
        is_verified=False,
    )
    
    created_user = repository.create(new_user)
    
    print(f"\n✅ Test user created successfully!")
    print(f"   User ID: {created_user.id}")
    print(f"   Email: {created_user.email}")
    print(f"   Username: {created_user.username}")
    print(f"\n📝 Login credentials:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n💡 You can now login at: http://localhost:5173")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        username = sys.argv[3] if len(sys.argv) > 3 else None
        create_test_user(email, password, username)
    else:
        print("🔐 Create Test User for Login")
        print("=" * 50)
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()
        username = input("Enter username (optional, press Enter to use email prefix): ").strip() or None
        
        if not email or not password:
            print("❌ Email and password are required!")
            sys.exit(1)
        
        create_test_user(email, password, username)

