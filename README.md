# Real-time Detection Service

## Overview
This service provides real-time detection of images, videos, and live camera streams using YOLO (You Only Look Once) object detection models. Built with FastAPI for backend processing and a lightweight HTML/JS frontend, it offers:

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