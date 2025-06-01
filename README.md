# Real-time Detection Service

## Overview

This service provides real-time detection of images, videos, and live camera streams using YOLO (You Only Look Once)
object detection models. Built with FastAPI for backend processing and a lightweight HTML/JS frontend, it offers:

- 🖼️ Image processing with annotated results
- 🎥 Video analysis with detection overlays
- 📹 Live camera stream processing
- 📊 Customizable detection parameters
- 📈 Logging and result storage

The system is containerized using Docker for easy deployment and scales with Celery for distributed task processing.

## Key Features

- **Multi-format support**: Process images (JPG/PNG) and videos (MP4)
- **Real-time detection**: Analyze live camera streams with WebSocket support
- **Model management**: Use built-in YOLO models or upload custom weights
- **Adjustable parameters**: Configure confidence thresholds and class colors
- **Distributed processing**: Celery workers handle heavy computation tasks
- **Logging**: Detectors log some info

## Technology Stack

### Backend

- **Python 3.11**
- **FastAPI** (REST API framework)
- **Celery** (distributed task queue)
- **Redis** (message broker and result store)
- **Ultralytics YOLO** (object detection models)
- **OpenCV** (image/video processing)

### Frontend

- Vanilla JavaScript
- HTML5/CSS3

### Infrastructure

- Docker
- Docker Compose
- Nginx (reverse proxy and static file serving)

## Project Structure

project/
├── docker-compose.yml # Container orchestration
├── backend/ # API and processing logic
│ ├── main.py # FastAPI application
│ ├── task.py # Celery task definitions
│ ├── config.py # Application settings
│ ├── anydetector.py # Detection condition handlers
│ ├── Dockerfile # Backend container setup
│ └── file_utils.py # Media processing utilities
├── frontend/ # User interface
│ ├── app.js # Frontend logic
│ ├── index.html # Main interface
│ └── style.css # Styling
├── nginx/ # Web server configuration
│ └── default.conf
├── shared_volume/ # Persistent storage
│ ├── logs # Detection logs
│ ├── models # Custom model weights
│ ├── processed # Processed results
│ └── uploads # User uploads
├── tests/ # Test suite
│ ├── test_dir/ # Test media samples
│ ├── test_api.py # API endpoint tests
│ └── test_utils.py # Utility function tests
└── README.md # Project documentation

## Getting Started

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

### Installation & Launch

1. **Clone the repository**
   ```bash
   git clone https://github.com/YurySalyatov/fastApiYOLOService.git
   ```
2. **Build and launch service**
    ```bash
   docker-compose up --build
    ```
3. **Access service**
   open `https://localhost:80`
4. **Verify services are running**
    ```bash
    docker-compose ps
    ```

## Usage Guide

### Web Interface

Follow these steps to process media files through the web interface:

1. **Access the Web Interface**  
   Open your browser and navigate to:  
   `https://localhost`  
   *(Replace localhost with your server IP if accessing remotely)*

2. **Upload Media File**  
   Click "Choose File" and select:
    - Image file (JPG, PNG)
    - Video file (MP4)

3. **Configure Detection Parameters**  
   Adjust settings as needed:
    - **Model Selection**:
        - Default models (pre-configured)
        - Custom model (upload your own .pt weights)
    - **Confidence Threshold** (0-1):
        - Lower value = more detections (may include false positives)
        - Higher value = fewer but more accurate detections
    - **Class Colors**:
        - Click color picker to assign colors to detection classes
        - Colors help distinguish different objects in results

4. **Start Processing**  
   Click the "Process" button to begin analysis.  
   Status indicators will show:
    - Processing animation during detection
    - Real-time progress for videos
    - Estimated time remaining for large files

5. **Retrieve Results**  
   When processing completes:
    - Processed images appear side-by-side with originals
    - Videos show "Download" button
    - Click "Download" to save annotated results
    - View detection logs in `shared_volume/logs/`

## API Reference

### Endpoints Overview

| Endpoint                        | Method    | Description                            | Content-Type          |
|---------------------------------|-----------|----------------------------------------|-----------------------|
| `/upload/file/`                 | POST      | Upload images or videos for processing | `multipart/form-data` |
| `/api/tasks/{task_id}`          | GET       | Check processing task status           | `application/json`    |
| `/api/models`                   | GET       | List available detection models        | `application/json`    |
| `/camera_upload/process_frame/` | POST      | Process single camera frame            | `multipart/form-data` |
| `/api/ws/video_feed`            | WebSocket | Live video processing stream           | -                     |

---

### 1. Upload Media File

**Endpoint**: `POST /upload/file/`  
**Description**: Submit images (JPG/PNG) or videos (MP4) for fire/smoke detection processing.  
**Parameters**:

| Name             | Type   | Description                                         | Required |
|------------------|--------|-----------------------------------------------------|----------|
| `file`           | File   | Media file to process (*.jpeg, *.png, *.jpg, *.mp4) | Yes      |
| `confidence`     | Float  | Detection confidence threshold (0.0-1.0)            | Yes      |
| `model_name`     | String | Model identifier (e.g., "yolo12s")                  | Yes      |
| `colors`         | JSON   | Array of custom colors [[R,G,B], ...]               | No       |
| `custom_weights` | File   | Custom model weights (.pt file)                     | No       |

**Example Request**:

```bash
curl -X POST http://localhost/upload/file/ \
  -F "file=@fire-smoke.jpg" \
  -F "confidence=0.5" \
  -F "model_name=fire-smoke" \
  -F "colors=[[255,0,0],[0,255,0]]"
```

**Example Response**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Check Task Status

**Endpoint**: `GET /api/tasks/{task_id}`  
**Description**: Retrieve the current status and processing results for a specific task. This endpoint allows you to
monitor the progress of media processing operations initiated through the `/upload/file/` endpoint.

#### Path Parameters

| Parameter | Type | Description                              | Example                                |
|-----------|------|------------------------------------------|----------------------------------------|
| `task_id` | UUID | Unique identifier of the processing task | `550e8400-e29b-41d4-a716-446655440000` |

#### Response Statuses

| Status    | Meaning    | Description                          |
|-----------|------------|--------------------------------------|
| `PENDING` | In Queue   | Task is waiting for available worker |
| `STARTED` | Processing | Task is currently being processed    |
| `SUCCESS` | Completed  | Processing finished successfully     |
| `FAILURE` | Failed     | Processing encountered an error      |

**Example Request**

```bash
curl http://localhost/api/tasks/550e8400-e29b-41d4-a716-446655440000
```

**Response Examples**

***Success Case:***

```json
{
  "status": "SUCCESS",
  "result": "processed_fire.jpg"
}
```

***In Progress:***

```json
{
  "status": "STARTED",
  "result": "None"
}
```

***Failed Case:***

```json
{
  "status": "FAILURE",
  "result": "None"
}
```

#### Response Fields

| Field  | Type   | Description         | Present When |
|--------|--------|---------------------|--------------|
| status | String | Current task status | Always       |
| result | String | Processed filename  | SUCCESS      |

### 3. List Available Models

**Endpoint**: `GET /api/models`  
**Description**: Retrieve detailed information about all available object detection models. This endpoint provides
metadata including class definitions and default color mappings for each model, which is essential for configuring
processing parameters.

#### Request

- **Method**: GET
- **Authentication**: None required
- **Query Parameters**: None

#### Example Request

```bash
curl http://localhost/api/models
```

**Response**

```json
[
  {
    "name": "fire-smoke",
    "classes": {
      "0": "fire",
      "1": "smoke"
    },
    "colors": "[[255,0,0],[0,255,0]]"
  },
  {
    "name": "couriers",
    "classes": {
      "0": "human-courier",
      "1": "robot-courier",
      "2": "courier-package"
    },
    "colors": "[[220,20,60],[0,191,255],[255,215,0]]"
  },
  ...
]
```

#### One Object Response Fields

| Field   | Type   | Description                       | Example                   |
|---------|--------|-----------------------------------|---------------------------|
| name    | String | Unique model identifier           | "fire-smoke"              |
| classes | String | Dictionary of class IDs and names | {"0": "fire", "1": smoke} |
| colors  | String | Default RGB colors for each class | [[255,0,0], [0,255,0]]    |

### 4. Process Camera Frame

**Endpoint**: `POST /camera_upload/process_frame/`  
**Description**: Process individual frames from live camera streams or image sequences. This endpoint is optimized for
real-time processing with low latency, making it suitable for security systems, IoT devices, and live monitoring
applications.

#### Request Parameters

| Name         | Type       | Description                              | Required | Format                  |
|--------------|------------|------------------------------------------|----------|-------------------------|
| `frame`      | File       | Image frame to process                   | Yes      | JPEG/PNG (max 10MB)     |
| `confidence` | Float      | Detection confidence threshold (0.0-1.0) | Yes      | 0.7                     |
| `model_name` | String     | Identifier of detection model            | Yes      | "yolo12s"               |
| `colors`     | JSON Array | Custom colors for classes [[R,G,B], ...] | No       | `[[255,0,0],[0,255,0]]` |

#### Example Request

```bash
curl -X POST http://localhost/camera_upload/process_frame/ \
  -F "frame=@camera_frame.jpg" \
  -F "confidence=0.5" \
  -F "model_name=fire-smoke" \
  -F "colors=[[255,0,0],[0,255,0]]"
```

