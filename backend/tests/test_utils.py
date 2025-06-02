import pytest
import cv2
import numpy as np
from pathlib import Path
from file_utils import load_model, draw_detections, process_frame, union_area, DEFAULT_COLORS

@pytest.fixture(scope="module")
def test_image():
    image_path = Path(__file__).parent / "test_dir" / "fire_example.png"
    return cv2.imread(str(image_path))


def test_load_model():
    model = load_model("yolo12s")
    assert model is not None
    assert hasattr(model, "predict")
    assert hasattr(model, "names")


def test_draw_detections(test_image):
    model = load_model("fire-smoke")
    results = process_frame(model, test_image)
    classes = model.names
    colors = DEFAULT_COLORS[:len(classes)]
    frame, detections = draw_detections(
        test_image.copy(),
        results,
        confidence=0.5,
        classes=classes
    )

    assert frame.shape == test_image.shape
    assert isinstance(detections, dict)
    if "fire" in detections:
        assert len(detections["fire"]) > 0


def test_union_area():
    rectangles = [
        [10, 10, 20, 20],
        [15, 15, 25, 25]
    ]
    area = union_area(rectangles)
    assert area > 0