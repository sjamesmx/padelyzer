import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('/Users/dev4/pdzr/backend/config/firebase-credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
print(list(db.collections())) 