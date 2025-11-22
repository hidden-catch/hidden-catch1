import os
# from rect2 import game_data
# from inpainting2 import create_diff_game_image
from rect3 import find_game_objects_normalized
from inpainting import modify_image_with_imagen

# ==========================================
# [설정] 프로젝트 정보
# ==========================================

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex_ai/key.json"

def main():
    results = find_game_objects_normalized("test_image.jpg")
    if results:
        modify_image_with_imagen("test_image.jpg", results)
    # if game_data:
    #      create_diff_game_image("test_image.jpg", game_data)

if __name__ == '__main__':
    main()

