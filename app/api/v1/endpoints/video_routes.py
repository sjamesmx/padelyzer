from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from app.api.v1.schemas.video_schema import VideoUploadRequest, VideoUploadResponse, VideoStatus
from app.services.video_service import upload_video, get_video_blueprint
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from app.services.firebase import get_firebase_client
from datetime import datetime
import logging
import tempfile
import os
from typing import Optional

router = APIRouter(prefix="/video", tags=["video"])
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video_endpoint(
    file: UploadFile = File(...),
    video_type: str = Form(...),
    description: Optional[str] = Form(None),
    player_position: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Uploads a video to Firebase Storage and initiates analysis.
    - Validates the video file
    - Uploads to Firebase Storage
    - Generates a unique blueprint
    - Creates a video analysis record
    - Returns the video details
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a video"
            )

        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a name"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Upload to Firebase Storage
            db, _ = get_firebase_client()
            video_path = f"videos/{current_user.id}/{file.filename}"
            upload_result = upload_video(temp_path, current_user.id, file.filename)
            
            # Generate blueprint
            blueprint = get_video_blueprint(upload_result['url'])
            
            # Check if analysis already exists
            analyses_ref = db.collection('video_analyses')
            query = analyses_ref.where('blueprint', '==', blueprint).limit(1)
            results = query.get()
            
            if results:
                # Return existing analysis
                analysis_doc = results[0]
                analysis_data = analysis_doc.to_dict()
                return VideoUploadResponse(
                    video_id=analysis_doc.id,
                    url=upload_result['url'],
                    status=VideoStatus(analysis_data['status']),
                    created_at=analysis_data['created_at'],
                    message="Video already analyzed"
                )
            
            # Create analysis document
            analysis_data = {
                'video_url': upload_result['url'],
                'video_path': video_path,
                'user_id': current_user.id,
                'video_type': video_type,
                'description': description,
                'player_position': player_position,
                'created_at': datetime.utcnow(),
                'status': VideoStatus.PENDING,
                'blueprint': blueprint
            }
            analysis_ref = analyses_ref.document()
            analysis_ref.set(analysis_data)
            
            return VideoUploadResponse(
                video_id=analysis_ref.id,
                url=upload_result['url'],
                status=VideoStatus.PENDING,
                created_at=analysis_data['created_at'],
                message="Video uploaded successfully"
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video: {str(e)}"
        ) 