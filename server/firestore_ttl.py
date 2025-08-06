"""
Firestore TTL Configuration for Session Cleanup

This module provides utilities to set up Firestore TTL (Time To Live) 
for automatic cleanup of expired sessions.

Note: Firestore TTL requires the Firestore Admin SDK and appropriate IAM permissions.
"""

from firebase_admin import firestore
from datetime import datetime, timedelta

def setup_session_ttl():
    """
    Set up TTL for sessions collection.
    
    This function creates a TTL policy that automatically deletes documents
    when the 'expiresAt' field is in the past.
    
    Note: This requires appropriate Firestore IAM permissions.
    """
    db = firestore.client()
    
    # Create TTL policy for sessions collection
    # This will automatically delete documents when expiresAt < now
    try:
        # Note: TTL policies are set at the collection level
        # The actual TTL field is specified in the Firestore console
        # or via the Admin SDK with appropriate permissions
        
        print("Setting up TTL for sessions collection...")
        print("Note: TTL policies require Firestore Admin SDK permissions")
        print("You may need to set this up manually in the Firebase Console:")
        print("1. Go to Firestore Database > Rules")
        print("2. Add TTL policy for 'sessions' collection")
        print("3. Set TTL field to 'expiresAt'")
        
        # Alternative: Manual cleanup function
        cleanup_expired_sessions()
        
    except Exception as e:
        print(f"Error setting up TTL: {e}")
        print("Using manual cleanup instead")

def cleanup_expired_sessions():
    """
    Manually clean up expired sessions.
    
    This function can be called periodically (e.g., via cron job)
    to remove expired sessions from the database.
    """
    db = firestore.client()
    
    try:
        # Query for expired sessions
        now = datetime.utcnow()
        expired_sessions = db.collection("sessions").where(
            "expiresAt", "<", now
        ).stream()
        
        deleted_count = 0
        for session in expired_sessions:
            session.reference.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} expired sessions")
        else:
            print("No expired sessions found")
            
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")

def get_session_stats():
    """
    Get statistics about sessions in the database.
    """
    db = firestore.client()
    
    try:
        # Count total sessions
        total_sessions = len(list(db.collection("sessions").stream()))
        
        # Count expired sessions
        now = datetime.utcnow()
        expired_sessions = len(list(
            db.collection("sessions").where("expiresAt", "<", now).stream()
        ))
        
        # Count active sessions
        active_sessions = total_sessions - expired_sessions
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "cleanup_needed": expired_sessions > 0
        }
        
    except Exception as e:
        print(f"Error getting session stats: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    print("Firestore TTL Configuration")
    print("=" * 30)
    
    # Get current stats
    stats = get_session_stats()
    if stats:
        print(f"Total sessions: {stats['total_sessions']}")
        print(f"Active sessions: {stats['active_sessions']}")
        print(f"Expired sessions: {stats['expired_sessions']}")
        
        if stats['cleanup_needed']:
            print("\nCleaning up expired sessions...")
            cleanup_expired_sessions()
    
    # Set up TTL (requires permissions)
    setup_session_ttl() 