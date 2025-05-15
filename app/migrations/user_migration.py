from datetime import datetime
from firebase_admin import firestore
from app.core.config import settings
from app.services.firebase import get_firebase_client

def migrate_users():
    """
    Migración de la colección de usuarios para añadir nuevos campos:
    - last_login
    - preferences
    - stats
    - achievements
    - blocked_users
    """
    db = get_firebase_client()
    users_ref = db.collection('users')
    users = users_ref.stream()
    
    batch = db.batch()
    count = 0
    
    for user in users:
        user_data = user.to_dict()
        
        # Preparar datos de actualización
        update_data = {
            'last_login': user_data.get('last_login', datetime.now()),
            'preferences': {
                'notifications': user_data.get('preferences', {}).get('notifications', True),
                'email_notifications': user_data.get('preferences', {}).get('email_notifications', True),
                'language': user_data.get('preferences', {}).get('language', 'es'),
                'timezone': user_data.get('preferences', {}).get('timezone', 'UTC')
            },
            'stats': {
                'matches_played': user_data.get('stats', {}).get('matches_played', 0),
                'matches_won': user_data.get('stats', {}).get('matches_won', 0),
                'total_points': user_data.get('stats', {}).get('total_points', 0)
            },
            'achievements': user_data.get('achievements', []),
            'blocked_users': user_data.get('blocked_users', [])
        }
        
        # Actualizar documento
        user_ref = users_ref.document(user.id)
        batch.update(user_ref, update_data)
        count += 1
        
        # Ejecutar batch cada 500 documentos
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()
            print(f"Migrated {count} users...")
    
    # Ejecutar batch final
    if count % 500 != 0:
        batch.commit()
    
    print(f"Migration completed. Total users migrated: {count}")

if __name__ == "__main__":
    migrate_users() 