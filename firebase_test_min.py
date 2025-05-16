import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials path from environment variable
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
if not cred_path:
    raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is not set")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()
print(list(db.collections())) 