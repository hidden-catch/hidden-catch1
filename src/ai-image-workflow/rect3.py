import vertexai
from vertexai.generative_models import GenerativeModel, Part
from PIL import Image
import io
import os
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex_ai/key.json"
PROJECT_ID = "liquid-kite-474906-t7"  # 프로젝트 ID 입력
LOCATION = "us-central1"

def find_game_objects_normalized(image_path):
    # 1. Vertex AI 초기화
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.5-flash")

    # 2. 이미지 로드 및 크기(Width, Height) 확인
    # 파일을 바이트로 읽습니다.
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # PIL을 사용하여 이미지 크기 정보 추출 (좌표 계산용)
    pil_image = Image.open(io.BytesIO(image_bytes))
    img_width, img_height = pil_image.size
    print(f"이미지 크기 확인: {img_width} x {img_height} (px)")

    # Gemini에게 보낼 객체 생성
    image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")

    # 3. [수정됨] 정규화(0.0 ~ 1.0) 좌표를 요청하는 프롬프트
    prompt = """
    You are an expert Game Level Designer for a "Spot the Difference" puzzle game.
    Your task is to analyze the image and identify 5 distinct objects to modify.

    **Selection Criteria:**
    1. Select objects that are clearly visible and distinct from the background.
    2. EXCLUDE objects that are too small, blurry, or have complex/ambiguous boundaries.
    3. Focus on objects where a change (e.g., color change, removal, replacement) would be noticeable.

    **Output Requirements:**
    1. Provide the output STRICTLY in valid JSON format.
    2. Do NOT use Markdown formatting.
    3. The `box_2d` coordinates must be in the format `[ymin, xmin, ymax, xmax]`.
    4. **IMPORTANT:** Values must be **normalized floats between 0.0 and 1.0** (relative to the image size).

    **JSON Example (Follow this pattern):**
    [
        {
            "object_name": "Man's Shirt",
            "box_2d": [0.45, 0.30, 0.60, 0.50],
            "type": "Color Change",
            "modification_idea": "Change the shirt color to bright yellow"
        }
    ]
    """

    # 4. AI 요청
    response = model.generate_content(
        [image_part, prompt],
        generation_config={"response_mime_type": "application/json"}
    )

    # 5. 결과 파싱 및 좌표 변환
    try:
        result_json = json.loads(response.text)
        
        print(f"\n=== AI 분석 결과 ({len(result_json)}개 객체) ===")
        
        final_results = []

        for item in result_json:
            # Gemini가 준 정규화된 좌표 (0.0 ~ 1.0)
            # 순서: [ymin, xmin, ymax, xmax]
            norm_box = item['box_2d'] 
            
            # -------------------------------------------------------
            # [핵심 로직] 정규화 좌표 -> 실제 픽셀 좌표 변환
            # y는 height를 곱하고, x는 width를 곱합니다.
            # -------------------------------------------------------
            ymin, xmin, ymax, xmax = norm_box
            
            pixel_box = {
                "ymin": int(ymin * img_height),
                "xmin": int(xmin * img_width),
                "ymax": int(ymax * img_height),
                "xmax": int(xmax * img_width)
            }
            
            # 결과 저장용 객체 구성
            processed_item = {
                "name": item['object_name'],
                "prompt": item['modification_idea'], # 이미지 생성 모델에 넘길 프롬프트
                "normalized_box": norm_box,          # 0~1 좌표 (DB 저장용)
                "pixel_box": pixel_box               # 실제 픽셀 좌표 (OpenCV/Crop용)
            }
            final_results.append(processed_item)

            # 출력 확인
            print(f"\n[객체] {processed_item['name']}")
            print(f" - 아이디어: {processed_item['prompt']}")
            print(f" - 정규화 좌표: {norm_box}")
            print(f" - 픽셀 좌표: {pixel_box}")

        return final_results

    except Exception as e:
        print(f"에러 발생: {e}")
        print("AI 응답:", response.text)
        return []

#find_game_objects_normalized("test_image.jpg")
