from vertexai.preview.vision_models import Image, ImageGenerationModel
from PIL import Image as PILImage, ImageDraw, ImageFilter
import io

def modify_image_with_imagen(original_image_path, detection_results):
    """
    Gemini가 찾은 좌표를 기반으로 마스크를 만들고, Imagen으로 이미지를 수정합니다.
    """
    
    # 1. 원본 이미지 로드 (PIL)
    pil_original = PILImage.open(original_image_path)
    width, height = pil_original.size
    
    # 2. 마스크 이미지 생성 (검은 배경 + 흰색 박스)
    # mode='L'은 흑백 이미지를 의미합니다. 0=검정, 255=흰색
    mask_image = PILImage.new('L', (width, height), 0) 
    draw = ImageDraw.Draw(mask_image)
    
    combined_prompt_list = []
    
    print("=== 마스크 생성 및 프롬프트 병합 중 ===")
    for item in detection_results:
        box = item['pixel_box']
        prompt_idea = item['prompt']
        
        # 마스크 그리기: 해당 좌표 영역을 흰색(255)으로 채움
        # [xmin, ymin, xmax, ymax] 순서
        draw.rectangle(
            [box['xmin'], box['ymin'], box['xmax'], box['ymax']], 
            fill=255
        )
        
        combined_prompt_list.append(prompt_idea)
        print(f" - 영역 추가: {item['name']} ({prompt_idea})")

    # 3. [꿀팁] 마스크 경계 부드럽게 하기 (Soft Masking)
    # 네모난 자국이 덜 남도록 블러 처리를 살짝 합니다.
    mask_image = mask_image.filter(ImageFilter.GaussianBlur(radius=5))
    
    # 4. 통합 프롬프트 생성
    # 예: "Change the car to blue. Remove the bird."
    final_prompt = " ".join(combined_prompt_list)
    print(f"\n🎨 최종 프롬프트: {final_prompt}")

    # 5. Vertex AI Imagen 모델 로드
    # 'imagegeneration@006'은 Imagen 2의 정식 버전 모델명입니다.
    generation_model = ImageGenerationModel.from_pretrained("imagegeneration@006")

    # 6. 이미지를 Vertex AI 포맷으로 변환
    # PIL 이미지를 바이트로 변환 후 Vertex AI Image 객체로 생성
    original_bytes = io.BytesIO()
    pil_original.save(original_bytes, format="PNG")
    vertex_original = Image(original_bytes.getvalue())

    mask_bytes = io.BytesIO()
    mask_image.save(mask_bytes, format="PNG")
    vertex_mask = Image(mask_bytes.getvalue())

    # 7. 이미지 수정 요청 (Inpainting)
    print("Imagen이 이미지를 수정하고 있습니다... (약 5~8초 소요)")
    response = generation_model.edit_image(
        base_image=vertex_original,
        mask=vertex_mask,
        prompt=final_prompt,
        guidance_scale=60,  # 프롬프트를 얼마나 따를지 (높을수록 프롬프트 충실)
        mask_mode="inpainting", # 마스크 안쪽을 수정
    )

    # 8. 결과 저장
    if response.images:
        output_path = "final_diff_game_image.png"
        response.images[0].save(output_path)
        print(f"\n✅ 수정 완료! 파일 저장됨: {output_path}")
        
        # (선택) 마스크가 잘 만들어졌는지 확인용 저장
        mask_image.save("debug_mask.png")
        return output_path
    else:
        print("❌ 이미지 생성 실패")
        return None

