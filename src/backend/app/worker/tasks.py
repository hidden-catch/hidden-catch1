import os
import sys
import time
from datetime import datetime

from app.worker.celery_app import celery_app

# AI workflow 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ai-image-workflow"))

@celery_app.task(bind=True)
def process_uploaded_image(self, slot_id: int):
    """
    업로드된 이미지를 AI로 분석하고 수정된 이미지를 생성하는 태스크
    
    파이프라인:
    1. DB에서 슬롯 정보 조회
    2. S3에서 원본 이미지 다운로드
    3. Gemini로 객체 탐지
    4. Imagen으로 이미지 수정
    5. 수정된 이미지를 S3에 업로드
    6. DB에 결과 저장
    """
    from app.db.session import SessionLocal
    from app.models.upload_slot import GameUploadSlot
    from app.services.s3_service import S3Service
    from main import process_image_pipeline

    db = SessionLocal()
    s3_service = S3Service()
    
    # 임시 파일 경로
    temp_dir = "/tmp"
    original_local_path = None
    modified_local_path = None
    
    try:
        # 1. DB에서 슬롯 정보 가져오기
        slot = db.query(GameUploadSlot).filter(
            GameUploadSlot.id == slot_id
        ).first()
        
        if not slot:
            raise ValueError(f"Slot {slot_id} not found")
        
        if not slot.s3_object_key or not slot.s3_object_key.get('original'):
            raise ValueError(f"Slot {slot_id} has no original S3 object key")
        
        original_s3_key = slot.s3_object_key['original']
        print(f"\n📦 처리 시작: Slot ID {slot_id}, Original S3 Key: {original_s3_key}")
        
        # 2. 상태를 'processing'으로 업데이트
        slot.analysis_status = "processing"
        db.commit()
        
        # 3. S3에서 원본 이미지 다운로드
        original_filename = original_s3_key.split("/")[-1]
        original_local_path = os.path.join(temp_dir, f"original_{slot_id}_{original_filename}")
        
        s3_service.download_image(original_s3_key, original_local_path)
        
        # 4. AI 처리 파이프라인 실행 (Gemini 탐지 + Imagen 수정)
        detected_objects, modified_image_path = process_image_pipeline(original_local_path)
        
        if not detected_objects:
            raise ValueError("No objects detected by AI")
        
        if not modified_image_path or not os.path.exists(modified_image_path):
            raise ValueError("Modified image was not created")
        
        # 5. 수정된 이미지를 S3에 업로드
        # S3 키: uploads/modified/{game_id}/slot_{slot_number}_modified.png
        modified_s3_key = f"uploads/modified/{slot.game_id}/slot_{slot.slot_number}_modified.png"
        s3_service.upload_image(modified_image_path, modified_s3_key)
        
        # 6. DB에 결과 저장 (s3_object_key에 original과 modified 모두 저장)
        slot.s3_object_key = {
            "original": original_s3_key,
            "modified": modified_s3_key
        }
        slot.detected_objects = detected_objects
        slot.analysis_status = "completed"
        slot.last_analyzed_at = datetime.utcnow()
        db.commit()
        
        print(f"\n✅ 처리 완료!")
        print(f"   - 탐지된 객체: {len(detected_objects)}개")
        print(f"   - 원본 이미지 S3: {original_s3_key}")
        print(f"   - 수정 이미지 S3: {modified_s3_key}")
        
        return {
            "slot_id": slot_id,
            "status": "success",
            "objects_count": len(detected_objects),
            "s3_keys": slot.s3_object_key,
        }
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
        
        # 에러 발생 시 상태 업데이트
        if slot:
            slot.analysis_status = "failed"
            slot.analysis_error = str(e)[:500]  # 최대 500자
            db.commit()
        
        raise
        
    finally:
        # 7. 임시 파일 정리
        if original_local_path and os.path.exists(original_local_path):
            os.remove(original_local_path)
            print(f"🗑️  임시 파일 삭제: {original_local_path}")
        
        if modified_local_path and os.path.exists(modified_local_path):
            os.remove(modified_local_path)
            print(f"🗑️  임시 파일 삭제: {modified_local_path}")
        
        # final_diff_game_image.png도 정리 (ai-image-workflow에서 생성)
        if os.path.exists("final_diff_game_image.png"):
            os.remove("final_diff_game_image.png")
        
        db.close()

