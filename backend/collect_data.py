import cv2
import os
import time
import uuid

DATASET_DIR = "dataset/images/train"
os.makedirs(DATASET_DIR, exist_ok=True)

def collect_images():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Saving images to {DATASET_DIR}")
    print("Controls:")
    print("  SPACE: Save image")
    print("  q: Quit")

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Data Collection - Press SPACE to Save", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            filename = f"{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(DATASET_DIR, filename)
            cv2.imwrite(filepath, frame)
            count += 1
            print(f"Captured {filename} ({count} total)")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    collect_images()
