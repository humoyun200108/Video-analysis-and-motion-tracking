import torch
import cv2
import numpy as np
import os
from moviepy.editor import VideoFileClip, ImageSequenceClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter

def load_yolo_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # YOLOv5 modelini yuklash
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.to(device).eval()
    return model, device

def detect_objects(image, model, device):
    # Tasvirni RGB formatga o'zgartirish
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = model(img)
    detections = results.xyxy[0]  # Detections in xyxy format
    return detections

def process_image(image_path, output_path):
    model, device = load_yolo_model()
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Tasvirni yuklashda muammo: {image_path}")

    detections = detect_objects(image, model, device)

    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection[:6]
        x1, y1, x2, y2 = map(int, [x1.item(), y1.item(), x2.item(), y2.item()])
        label = model.names[int(cls.item())]
        confidence = conf.item()
        color = (0, 255, 0)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, f"{label} {confidence:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    success = cv2.imwrite(output_path, image)
    if not success:
        raise ValueError(f"Tasvirni saqlashda muammo: {output_path}")

def process_video(video_path, output_path, task_id=None, progress_dict=None):
    try:
        model, device = load_yolo_model()
        clip = VideoFileClip(video_path)
        total_frames = int(clip.fps * clip.duration)

        frames = []
        for i, frame in enumerate(clip.iter_frames()):
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            detections = detect_objects(frame_rgb, model, device)

            for detection in detections:
                x1, y1, x2, y2, conf, cls = detection[:6]
                x1, y1, x2, y2 = map(int, [x1.item(), y1.item(), x2.item(), y2.item()])
                label = model.names[int(cls.item())]
                confidence = conf.item()
                color = (0, 255, 0)
                cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame_rgb, f"{label} {confidence:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
            frames.append(frame_bgr)

        # Videoni yozish
        fps = clip.fps
        size = frames[0].shape[:2][::-1]  # (width, height)

        writer = FFMPEG_VideoWriter(output_path, size=size, fps=fps, codec='libx264')

        for i, frame in enumerate(frames):
            writer.write_frame(frame)
            # Progressni yangilash (0% - 100%)
            if task_id and progress_dict is not None:
                percent = int(((i + 1) / total_frames) * 100)
                progress_dict[task_id] = percent

        writer.close()

        # Progressni 100% ga o'rnatamiz
        if task_id and progress_dict is not None:
            progress_dict[task_id] = 100

    except Exception as e:
        if task_id and progress_dict is not None:
            progress_dict[task_id] = 'error'
        print(f"Xatolik: {e}")
