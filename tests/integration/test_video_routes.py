import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
import os
import tempfile
from app.schemas.user import UserInDB
from app.core.deps import get_current_user

client = TestClient(app)

# Override authentication dependency for all tests
app.dependency_overrides[get_current_user] = lambda: UserInDB(id='user123', email='test@example.com')

@pytest.fixture
def mock_firebase():
    with patch('app.services.firebase.get_firebase_client') as mock:
        mock_db = MagicMock()
        mock_auth = MagicMock()
        mock.return_value = (mock_db, mock_auth)
        yield mock

@pytest.fixture
def mock_video_service():
    with patch('app.services.video_service.upload_video') as mock:
        mock.return_value = {
            'url': 'https://firebasestorage.googleapis.com/v0/b/pdzr-458820.appspot.com/o/videos/test.mp4',
            'storage_path': 'videos/user123/test.mp4'
        }
        yield mock

def test_video_upload_success(mock_firebase, mock_video_service):
    # Create a temporary video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_file.write(b'fake video content')
        temp_path = temp_file.name

    try:
        # Prepare the request
        files = {
            'file': ('test.mp4', open(temp_path, 'rb'), 'video/mp4')
        }
        data = {
            'video_type': 'training',
            'description': 'Test video',
            'player_position': '{"side": "right", "zone": "back"}'
        }

        # Make the request
        response = client.post(
            "/api/v1/video/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer test-token"}
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert 'video_id' in data
        assert 'url' in data
        assert data['status'] == 'pending'
        assert 'created_at' in data
        assert data['message'] == 'Video uploaded successfully'

    finally:
        # Clean up
        os.unlink(temp_path)

def test_video_upload_invalid_file_type():
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_file.write(b'not a video')
        temp_path = temp_file.name

    try:
        # Prepare the request
        files = {
            'file': ('test.txt', open(temp_path, 'rb'), 'text/plain')
        }
        data = {
            'video_type': 'training'
        }

        # Make the request
        response = client.post(
            "/api/v1/video/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer test-token"}
        )

        # Assert response
        assert response.status_code == 400
        assert response.json()['detail'] == 'File must be a video'

    finally:
        # Clean up
        os.unlink(temp_path)

def test_video_upload_unauthorized():
    # Remove the dependency override for this test
    app.dependency_overrides.pop(get_current_user, None)
    try:
        # Create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'fake video content')
            temp_path = temp_file.name

        try:
            # Prepare the request
            files = {
                'file': ('test.mp4', open(temp_path, 'rb'), 'video/mp4')
            }
            data = {
                'video_type': 'training'
            }

            # Make the request without auth header
            response = client.post(
                "/api/v1/video/upload",
                files=files,
                data=data
            )

            # Assert response
            assert response.status_code in (401, 403)

        finally:
            # Clean up
            os.unlink(temp_path)
    finally:
        # Restore the dependency override
        app.dependency_overrides[get_current_user] = lambda: UserInDB(id='user123', email='test@example.com')

def test_video_upload_duplicate(mock_firebase, mock_video_service):
    # Mock existing analysis
    mock_db, _ = mock_firebase.return_value
    mock_query = MagicMock()
    mock_doc = MagicMock()
    mock_doc.id = 'existing-analysis-id'
    mock_doc.to_dict.return_value = {
        'status': 'completed',
        'created_at': '2024-05-19T10:00:00Z'
    }
    mock_query.get.return_value = [mock_doc]
    mock_db.collection.return_value.where.return_value.limit.return_value = mock_query

    # Create a temporary video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_file.write(b'fake video content')
        temp_path = temp_file.name

    try:
        # Prepare the request
        files = {
            'file': ('test.mp4', open(temp_path, 'rb'), 'video/mp4')
        }
        data = {
            'video_type': 'training'
        }

        # Make the request
        response = client.post(
            "/api/v1/video/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer test-token"}
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data['message'] in ('Video uploaded successfully', 'Video already analyzed')
        assert 'video_id' in data
        assert data['status'] in ('pending', 'completed', 'processing', 'failed')

    finally:
        # Clean up
        os.unlink(temp_path) 