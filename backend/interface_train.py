from ultralytics import YOLO

def main():
    model = YOLO('yolo11n.pt')
    
    model.train(
        data='dataset/data.yaml',
        epochs=50,
        imgsz=320,
        patience=10
    )

if __name__ == '__main__':
    main()