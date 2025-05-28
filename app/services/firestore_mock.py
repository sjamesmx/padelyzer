from unittest.mock import MagicMock, patch
from google.cloud import firestore

class MockDocumentSnapshot:
    def __init__(self, data=None):
        self._data = data or {}
        self.exists = True

    def to_dict(self):
        return self._data

class MockFirestoreClient:
    def __init__(self):
        self._collections = {}

    def collection(self, collection_path):
        if collection_path not in self._collections:
            self._collections[collection_path] = MockCollectionReference()
        return self._collections[collection_path]

class MockCollectionReference:
    def __init__(self):
        self._documents = {}

    def document(self, document_path):
        if document_path not in self._documents:
            self._documents[document_path] = MockDocumentReference()
        return self._documents[document_path]

class MockDocumentReference:
    def __init__(self):
        self._data = {}

    def get(self):
        return MockDocumentSnapshot(self._data)

    def set(self, data):
        self._data = data
        return self

def get_mock_firestore_client():
    return MockFirestoreClient()

def patch_firestore():
    return patch('google.cloud.firestore.Client', return_value=get_mock_firestore_client()) 