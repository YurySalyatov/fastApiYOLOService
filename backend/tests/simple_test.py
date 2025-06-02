# import os
# import time
#
# import cv2
# from app.anydetector import get_detector
# from app.file_utils import return_process_image, DEFAULT_COLORS
# from ultralytics import YOLO
#
#
# def test_frames_detected():
#     # print("test1")
#     fire_detector = get_detector('fire-smoke')
#     frames_dir = 'test_dir/frames'
#     frames = []
#     # print(os.getcwd())
#     model = YOLO("../../shared_volume/models/fire-smoke.pt")
#     for filename in os.listdir(frames_dir):
#         frame = cv2.imread(os.path.join(frames_dir, filename))
#         _, boxex = return_process_image(model, model.names, DEFAULT_COLORS[:2], frame, 0.5)
#         print(boxex)
#         frames.append(boxex)
#         if len(frames) >= 10:
#             print(frames)
#             fire_detector.detect_frames(frames, time.time())
#             frames = []
#     fire_detector.detect_frames(frames, time.time())
#
#
# # frames_detected()