import os
import time
import requests
from pathlib import Path
import json


def image_processing():
    response = requests.get("http://localhost:80")
    assert response.status_code == 200
    assert "text/html" in response.headers['Content-Type']

    test_dir = Path(__file__).parent / "test_dir"
    test_image = test_dir / "test_image.jpg"
    assert test_image.exists(), f"Test image not found: {test_image}"

    colors = [(255, 0, 0), (0, 0, 255)]
    with open(test_image, "rb") as f:
        files = {"file": f}
        data = {
            "confidence": "0.5",
            "model_name": "fire-smoke",
            "colors": json.dumps(colors)
        }
        response = requests.post(
            "http://localhost:80/upload/file/",
            files=files,
            data=data
        )

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    processed = False
    result_url = None
    for _ in range(10):
        time.sleep(3)
        task_response = requests.get(f"http://localhost:80/api/tasks/{task_id}/")
        task_data = task_response.json()

        if task_data["status"] == "SUCCESS":
            processed = True
            result_url = task_data["result"]
            break

    assert processed, "Image processing timed out"

    processed_url = f"http://localhost:80/processed/{result_url}"
    response = requests.get(processed_url)
    assert response.status_code == 200
    assert "image" in response.headers['Content-Type']
