import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MockFirestore:
    def __init__(self):
        self.data = {}
        
    def collection(self, collection_name: str):
        if collection_name not in self.data:
            self.data[collection_name] = {}
        return MockCollection(self.data[collection_name])

class MockCollection:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        
    def document(self, doc_id: Optional[str] = None) -> 'MockDocument':
        if doc_id is None:
            # Generar un ID único
            doc_id = f"doc_{len(self.data)}"
        return MockDocument(self.data, doc_id)
        
    def where(self, field: str, operator: str, value: Any) -> 'MockQuery':
        return MockQuery(self.data, field, operator, value)
        
    def get(self) -> list:
        results = []
        for doc_id, doc_data in self.data.items():
            results.append(MockDocumentSnapshot(doc_data, doc_id))
        return results

class MockDocument:
    def __init__(self, collection_data: Dict[str, Any], doc_id: str):
        self.collection_data = collection_data
        self.id = doc_id
        
    def set(self, data: Dict[str, Any]) -> None:
        self.collection_data[self.id] = data
        
    def update(self, data: Dict[str, Any]) -> None:
        if self.id in self.collection_data:
            self.collection_data[self.id].update(data)
        else:
            self.collection_data[self.id] = data
            
    def get(self) -> 'MockDocumentSnapshot':
        return MockDocumentSnapshot(self.collection_data.get(self.id, {}), self.id)

class MockDocumentSnapshot:
    def __init__(self, data: Dict[str, Any], doc_id: str = None):
        self.data = data
        self.id = doc_id
        
    def to_dict(self) -> Dict[str, Any]:
        return self.data
        
    def get(self, field: str) -> Any:
        return self.data.get(field)

class MockQuery:
    def __init__(self, data: Dict[str, Any], field: str, operator: str, value: Any):
        self.data = data
        self.field = field
        self.operator = operator
        self.value = value
        
    def get(self) -> list:
        results = []
        for doc_id, doc_data in self.data.items():
            if self.operator == '==' and doc_data.get(self.field) == self.value:
                results.append(MockDocumentSnapshot(doc_data, doc_id))
        return results

_mock_firestore = MockFirestore()

def initialize_firebase():
    """Mock de inicialización de Firebase."""
    logger.info("Mock de Firebase inicializado")
    return True

def client():
    """Retorna el cliente mock de Firestore."""
    return _mock_firestore 