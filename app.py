from flask import Flask, render_template, request, Response
from ultralytics import YOLO
import cv2
import os
import csv
from datetime import datetime

app = Flask(__name__)

model = YOLO("runs/detect/train-2/weights/best.pt")

UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== CSV =====
CSV_FILE = "detections.csv"

# tạo file nếu chưa có
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "type", "class", "confidence", "x1", "y1", "x2", "y2"])

file_path = None
file_type = None


@app.route("/", methods=["GET", "POST"])
def index():
    global file_path, file_type

    if request.method == "POST":

        if "file" not in request.files:
            return "No file part"

        file = request.files.get("file")

        if file is None or file.filename == "":
            return "No selected file"

        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # ===== IMAGE =====
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_type = "image"

            img = cv2.imread(file_path)
            if img is None:
                return "Error reading image"

            img = cv2.resize(img, (480, 320))

            results = model(img, conf=0.25, imgsz=320)

            # 🔥 LƯU CSV (IMAGE)
            with open(CSV_FILE, mode="a", newline="") as f:
                writer = csv.writer(f)

                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    writer.writerow([
                        datetime.now(),
                        "image",
                        label,
                        round(conf, 2),
                        x1, y1, x2, y2
                    ])

            annotated = results[0].plot()

            result_path = os.path.join(UPLOAD_FOLDER, "result.jpg")
            cv2.imwrite(result_path, annotated)

            return render_template(
                "index.html",
                image_result="result.jpg",
                video=False
            )

        # ===== VIDEO =====
        elif filename.lower().endswith(('.mp4', '.avi', '.mov')):
            file_type = "video"
            return render_template("index.html", video=True)

        else:
            return "File không hỗ trợ"

    return render_template("index.html", image_result=None, video=False)


# 🎥 STREAM VIDEO
def generate_frames():
    global file_path

    cap = cv2.VideoCapture(file_path)
    frame_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1

        # skip frame cho mượt
        if frame_count % 2 != 0:
            continue

        frame = cv2.resize(frame, (480, 320))

        results = model(frame, conf=0.25, imgsz=320)

        # 🔥 LƯU CSV (VIDEO - giảm ghi cho đỡ nặng)
        if frame_count % 10 == 0:
            with open(CSV_FILE, mode="a", newline="") as f:
                writer = csv.writer(f)

                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    writer.writerow([
                        datetime.now(),
                        "video",
                        label,
                        round(conf, 2),
                        x1, y1, x2, y2
                    ])

        annotated = results[0].plot()

        count = len(results[0].boxes)

        cv2.putText(
            annotated,
            f"Objects: {count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        _, buffer = cv2.imencode(
            '.jpg',
            annotated,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)