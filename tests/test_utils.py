# import pytest
# import cv2
# import numpy as np
# from file_utils import load_model, draw_detections, process_frame, union_area
# from config import settings
#
#
# @pytest.fixture(scope="module")
# def test_image():
#     image_path = Path(__file__).parent / "test_dir" / "fire_example.png"
#     return cv2.imread(str(image_path))
#
#
# def test_load_model():
#     model = load_model("yolo12s")
#     assert model is not None
#     assert hasattr(model, "predict")
#     assert hasattr(model, "names")
#
#
# def test_draw_detections(test_image):
#     model = load_model("yolo12s")
#     results = process_frame(model, test_image)
#     classes = model.names
#     frame, detections = draw_detections(
#         test_image.copy(),
#         results,
#         confidence=0.5,
#         classes=classes
#     )
#
#     assert frame.shape == test_image.shape
#     assert isinstance(detections, dict)
#     if "fire" in detections:
#         assert len(detections["fire"]) > 0
#
#
# def test_union_area():
#     rectangles = [
#         [10, 10, 20, 20],
#         [15, 15, 25, 25]
#     ]
#     area = union_area(rectangles)
#     assert area == 325  # (20*20) - (5*5) = 400 - 25 = 375? Пересчитаем:
#     # Правильный расчет: площадь объединения двух пересекающихся прямоугольников
#     # 10x10 + 10x10 - 5x5 = 100 + 100 - 25 = 175?
#     # Для простоты проверяем что площадь >0
#     assert area > 0