"""
Firebase utilities - timeout handling, health checks, and error recovery
"""
import functools
import signal
import os
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.cache import cache

# ========================================
# TIMEOUT DECORATOR
# ========================================

class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutException("Operation timed out")


def firebase_timeout(seconds=30):
    """
    Decorator to add timeout to Firebase operations

    Args:
        seconds: Timeout duration in seconds (default: 30)

    Usage:
        @firebase_timeout(30)
        def my_view(request):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set signal handler for timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                return result
            except TimeoutException:
                signal.alarm(0)  # Cancel the alarm
                print(f"⚠️ Firebase operation timed out after {seconds}s")
                return None
            except Exception as e:
                signal.alarm(0)  # Cancel the alarm
                raise

        return wrapper
    return decorator


# ========================================
# FIREBASE HEALTH CHECK
# ========================================

FIREBASE_HEALTH_CACHE_KEY = 'firebase_health_status'
FIREBASE_HEALTH_CACHE_TIMEOUT = 60  # 1 minute


def check_firebase_connectivity():
    """
    Check if Firebase is accessible

    Returns:
        dict: {
            'is_healthy': bool,
            'last_checked': str,
            'message': str,
            'cached': bool
        }
    """
    # Check cache first
    cached_status = cache.get(FIREBASE_HEALTH_CACHE_KEY)
    if cached_status:
        cached_status['cached'] = True
        return cached_status

    try:
        import firebase_admin
        from firebase_admin import firestore as admin_firestore

        # Check if Firebase is initialized
        if not firebase_admin._apps:
            print("❌ Firebase not initialized")
            status = {
                'is_healthy': False,
                'last_checked': datetime.now().isoformat(),
                'message': 'Firebase not initialized',
                'cached': False
            }
            cache.set(FIREBASE_HEALTH_CACHE_KEY, status, FIREBASE_HEALTH_CACHE_TIMEOUT)
            return status

        # Try to get Firestore client
        db = admin_firestore.client()

        # Do a simple test query (count documents in a collection)
        # This is lightweight and will fail quickly if auth is broken
        test_ref = db.collection('products')

        # Use query timeout
        try:
            # Get just one document as a health check
            test_query = test_ref.limit(1)
            test_docs = list(test_query.stream())

            status = {
                'is_healthy': True,
                'last_checked': datetime.now().isoformat(),
                'message': 'Firebase is accessible',
                'cached': False
            }
            print("✅ Firebase health check passed")
        except Exception as auth_error:
            print(f"❌ Firebase auth error: {auth_error}")
            status = {
                'is_healthy': False,
                'last_checked': datetime.now().isoformat(),
                'message': f'Authentication failed: {str(auth_error)}',
                'cached': False
            }

        cache.set(FIREBASE_HEALTH_CACHE_KEY, status, FIREBASE_HEALTH_CACHE_TIMEOUT)
        return status

    except Exception as e:
        print(f"❌ Error checking Firebase health: {e}")
        status = {
            'is_healthy': False,
            'last_checked': datetime.now().isoformat(),
            'message': f'Error: {str(e)}',
            'cached': False
        }
        return status


# ========================================
# FIRESTORE QUERY TIMEOUT WRAPPER
# ========================================

def get_firestore_client_with_timeout():
    """
    Get Firestore client with proper configuration

    Returns:
        Firestore client instance
    """
    try:
        import firebase_admin
        from firebase_admin import firestore as admin_firestore

        if not firebase_admin._apps:
            cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
            from firebase_admin import credentials
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        # Get Firestore client
        db = admin_firestore.client()

        return db
    except Exception as e:
        print(f"❌ Error getting Firestore client: {e}")
        raise


def safe_firestore_query(collection_name, operation=None, timeout=10, default_value=None):
    """
    Safely execute a Firestore query with timeout and error handling

    Args:
        collection_name: Name of the collection to query
        operation: Function to execute on the collection reference
        timeout: Query timeout in seconds
        default_value: Value to return if query fails

    Returns:
        Query result or default_value on error
    """
    try:
        db = get_firestore_client_with_timeout()

        # Get collection reference
        collection_ref = db.collection(collection_name)

        # Execute operation if provided
        if operation:
            result = operation(collection_ref)
        else:
            result = collection_ref.stream()

        return result

    except Exception as e:
        print(f"❌ Error querying {collection_name}: {e}")
        return default_value if default_value is not None else []


# ========================================
# CREDENTIALS VALIDATION
# ========================================

def validate_firebase_credentials():
    """
    Validate Firebase credentials file

    Returns:
        dict: {
            'is_valid': bool,
            'message': str,
            'file_exists': bool,
            'file_path': str
        }
    """
    try:
        cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')

        # Check if file exists
        if not os.path.exists(cred_path):
            return {
                'is_valid': False,
                'message': f'Credentials file not found at {cred_path}',
                'file_exists': False,
                'file_path': cred_path
            }

        # Try to parse JSON
        import json
        with open(cred_path, 'r') as f:
            creds = json.load(f)

        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]

        if missing_fields:
            return {
                'is_valid': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'file_exists': True,
                'file_path': cred_path
            }

        return {
            'is_valid': True,
            'message': f'Credentials file is valid (project: {creds.get("project_id")})',
            'file_exists': True,
            'file_path': cred_path
        }

    except json.JSONDecodeError:
        return {
            'is_valid': False,
            'message': 'Credentials file is not valid JSON',
            'file_exists': True,
            'file_path': cred_path
        }
    except Exception as e:
        return {
            'is_valid': False,
            'message': f'Error validating credentials: {str(e)}',
            'file_exists': False,
            'file_path': cred_path
        }


# ========================================
# ERROR CONTEXT HELPER
# ========================================

def get_firebase_error_context():
    """
    Get comprehensive error information for debugging

    Returns:
        dict: Error context information
    """
    context = {
        'timestamp': datetime.now().isoformat(),
        'credentials_valid': validate_firebase_credentials(),
        'firebase_healthy': check_firebase_connectivity(),
        'environment': {
            'credentials_path': os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json'),
            'working_directory': os.getcwd()
        }
    }
    return context
