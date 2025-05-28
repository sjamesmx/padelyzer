import pytest
import os
from app.services import firebase
import firebase_admin
from firebase_admin import firestore
from app.core.config.firebase import initialize_firebase, get_firebase_clients

@pytest.mark.skip("Prueba solo para entorno real, no en CI")
def test_initialize_firebase():
    """Test que Firebase se inicialice correctamente."""
    # Limpiar cualquier app de Firebase existente
    for app in list(firebase_admin._apps.values()):
        firebase_admin.delete_app(app)
    
    # Inicializar Firebase
    client = initialize_firebase()
    
    # Verificar que Firebase esté inicializado
    assert len(firebase_admin._apps) > 0
    assert client is not None
    assert hasattr(client, 'collection')  # Verificar que es un cliente de Firestore

@pytest.mark.skip("Prueba solo para entorno real, no en CI")
def test_firestore_operations():
    """Test de operaciones básicas de Firestore."""
    # Obtener cliente de Firestore
    clients = get_firebase_clients()
    db = clients['db']
    
    # Probar creación de colección y operaciones de documento
    test_collection = db.collection('test_collection')
    test_doc = test_collection.document('test_doc')
    
    # Escribir datos
    test_data = {'test_field': 'test_value'}
    test_doc.set(test_data)
    
    # Leer datos
    doc = test_doc.get()
    assert doc.exists
    assert doc.to_dict() == test_data
    
    # Limpiar
    test_doc.delete()

def test_initialize_firebase_with_emulator(monkeypatch, mocker):
    """Test de inicialización de Firebase con emulador."""
    # Configurar el entorno
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    mocker.patch("firebase_admin._apps", {})
    
    # Mock de logger
    mock_logger = mocker.patch("app.config.firebase.logger")
    
    # Inicializar Firebase con emulador
    mock_firestore = mocker.patch("firebase_admin.firestore.client")
    mock_initialize_app = mocker.patch("firebase_admin.initialize_app")
    
    # Ejecutar la función
    initialize_firebase()
    
    # Verificaciones
    mock_initialize_app.assert_called_once()
    mock_logger.info.assert_any_call(mocker.ANY)  # Verificar que se logueó algo
    
    # Verificar que se llamó a firestore.client()
    mock_firestore.assert_called_once()

def test_initialize_firebase_with_credentials(monkeypatch, mocker):
    """Test de inicialización de Firebase con credenciales."""
    # Configurar el entorno
    monkeypatch.delenv("FIRESTORE_EMULATOR_HOST", raising=False)
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY_ID", "test-key-id")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "test-key")
    monkeypatch.setenv("FIREBASE_CLIENT_EMAIL", "test@example.com")
    
    # Mock para aplicaciones existentes
    mocker.patch("firebase_admin._apps", {})
    
    # Mock para Certificate y initialize_app
    mock_cert = mocker.patch("firebase_admin.credentials.Certificate")
    mock_initialize_app = mocker.patch("firebase_admin.initialize_app")
    mock_firestore = mocker.patch("firebase_admin.firestore.client")
    
    # Ejecutar la función
    initialize_firebase()
    
    # Verificar que se llamaron las funciones correctas
    mock_cert.assert_called_once()
    mock_initialize_app.assert_called_once()
    mock_firestore.assert_called_once()

def test_get_firebase_client(mocker):
    """Test que get_firebase_client retorna un cliente de Firestore."""
    # Mock para initialize_firebase
    mock_initialize = mocker.patch("app.config.firebase.initialize_firebase")
    mock_client = mocker.Mock()
    mock_initialize.return_value = mock_client
    
    # Mock para verificar si Firebase ya está inicializado
    mocker.patch("firebase_admin._apps", {"[DEFAULT]": mocker.Mock()})
    
    # Ejecutar la función
    client = firebase.get_firebase_client()
    
    # Verificar que se retornó el cliente correcto
    assert client is not None

def test_get_firebase_client_exception(mocker):
    """Test que get_firebase_client maneja excepciones correctamente."""
    # Mock para initialize_firebase que lanza una excepción
    mock_initialize = mocker.patch(
        "app.config.firebase.initialize_firebase",
        side_effect=Exception("Error de prueba")
    )
    
    # Mock para logger.error
    mock_logger = mocker.patch("app.services.firebase.logger")
    
    # Ejecutar la función y verificar que se lanza la excepción
    with pytest.raises(Exception):
        firebase.get_firebase_client()
    
    # Verificar que se logueó el error
    mock_logger.error.assert_called_once()