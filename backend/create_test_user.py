"""
Script to create a test user for development.
This is needed for book uploads since they require an owner_id.
"""

from app.database import SessionLocal, Base, engine
from app.models import User
from sqlalchemy.exc import IntegrityError

def create_test_user():
    """Create a test user for development."""
    
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.id == 1).first()
        if existing_user:
            print("Test user already exists!")
            return
        
        # Create test user
        test_user = User(
            id=1,
            email="test@chaptr.dev",
            username="testuser",
            hashed_password="placeholder_hash",  # We'll implement proper auth later
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"Created test user: {test_user.username} (ID: {test_user.id})")
        
    except IntegrityError as e:
        db.rollback()
        print(f"User already exists or integrity error: {e}")
    except Exception as e:
        db.rollback()
        print(f"Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 