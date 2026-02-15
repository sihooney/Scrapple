import cv2
from ultralytics import YOLO

def main():
    model = YOLO(r'runs\detect\train\weights\best.pt')
    
    cap = cv2.VideoCapture('dataset/test_video.mov')
    
    if not cap.isOpened():
        print("ERROR: Could not open test_video.mov. Check the file path or format.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"Video loaded! Resolution: {width}x{height} at {fps} FPS")
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('test_result.avi', fourcc, fps, (width, height))
    
    frame_count = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print(f"Finished processing! Total frames: {frame_count}")
            break
            
        results = model(frame, conf=0.15, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                
        out.write(frame)
        frame_count += 1
        
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")
            
    cap.release()
    out.release()

if __name__ == '__main__':
    main()