def upload_file(file_path: str, destination_path: str) -> str:
    """
    Sube un archivo a Firebase Storage y retorna la URL pública.
    """
    try:
        db, _ = get_firebase_client()
        bucket = storage.bucket()
        blob = bucket.blob(destination_path)
        
        # Subir archivo
        blob.upload_from_filename(file_path)
        
        # Hacer el blob público
        blob.make_public()
        
        # Retornar URL pública
        return blob.public_url
    except Exception as e:
        logger.error(f"Error al subir archivo a Firebase Storage: {str(e)}")
        raise

def delete_file(file_path: str):
    """
    Elimina un archivo de Firebase Storage.
    """
    try:
        db, _ = get_firebase_client()
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        blob.delete()
    except Exception as e:
        logger.error(f"Error al eliminar archivo de Firebase Storage: {str(e)}")
        raise 