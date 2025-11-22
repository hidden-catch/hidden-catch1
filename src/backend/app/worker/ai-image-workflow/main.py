import os
from rect3 import find_game_objects_normalized
from inpainting import modify_image_with_imagen


def process_image_pipeline(original_image_path: str) -> tuple[list[dict], str | None]:
    """
    이미지 처리 파이프라인: 객체 탐지 -> 이미지 수정
    
    Args:
        original_image_path: 원본 이미지 로컬 경로
        
    Returns:
        (탐지된 객체 리스트, 생성된 이미지 경로)
    """
    print(f"\n🚀 AI 이미지 처리 시작: {original_image_path}")
    
    # 1단계: 객체 탐지 (Gemini)
    print("\n[1단계] Gemini로 객체 탐지 중...")
    detected_objects = find_game_objects_normalized(original_image_path)
    
    if not detected_objects:
        print("❌ 탐지된 객체가 없습니다.")
        return [], None
    
    print(f"✅ {len(detected_objects)}개 객체 탐지 완료")
    
    # 2단계: 이미지 수정 (Imagen)
    print("\n[2단계] Imagen으로 이미지 수정 중...")
    modified_image_path = modify_image_with_imagen(original_image_path, detected_objects)
    
    if not modified_image_path:
        print("❌ 이미지 수정 실패")
        return detected_objects, None
    
    print(f"✅ 이미지 수정 완료: {modified_image_path}")
    
    return detected_objects, modified_image_path


def main():
    """테스트용 메인 함수"""
    results, modified_path = process_image_pipeline("test_image.jpg")
    print(f"\n=== 최종 결과 ===")
    print(f"탐지 객체 수: {len(results)}")
    print(f"수정된 이미지: {modified_path}")


if __name__ == '__main__':
    main()


