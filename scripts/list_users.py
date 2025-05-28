from app.core.config.firebase import get_firebase_clients


def buscar_usuario(email):
    clients = get_firebase_clients()
    db = clients['db']
    query = db.collection('users').where('email', '==', email).stream()
    encontrados = False
    for doc in query:
        print(f"ID: {doc.id}")
        print(doc.to_dict())
        encontrados = True
    if not encontrados:
        print("No se encontró el usuario en la colección 'users'.")

if __name__ == "__main__":
    buscar_usuario("usuario_test_20240625_03@ejemplo.com") 