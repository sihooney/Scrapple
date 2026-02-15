# Backend Tools

This directory contains utility scripts for dataset collection and model training. These scripts are **not used in the current demo** but are available for development and training workflows.

## Scripts

### `collect_data.py`

**Purpose**: Captures images from your webcam for building custom YOLO training datasets.

**What it does**:
- Opens your system's default webcam
- Displays a live video feed
- Allows you to capture individual frames with the SPACE key
- Saves captured images to `backend/dataset/images/train/` with unique UUIDs
- Exits with the 'q' key

**Dependencies**:
- `opencv-python` (cv2)

**Usage**:
```bash
# From the backend directory
python tools/collect_data.py
```

**Controls**:
- **SPACE**: Capture current frame and save to dataset
- **q**: Quit the capture session

---

### `interface_train.py`

**Purpose**: Trains a YOLOv11 Nano model using the collected dataset.

**What it does**:
- Loads the YOLOv11 Nano pre-trained weights (`yolo11n.pt`)
- Trains the model for 50 epochs using your custom dataset
- Uses `dataset/data.yaml` configuration for dataset paths and classes
- Generates trained model checkpoints

**Dependencies**:
- `ultralytics` (YOLOv11)

**Usage**:
```bash
# From the backend directory
python tools/interface_train.py
```

**Requirements**:
- `dataset/data.yaml` must be configured with proper paths and class definitions
- Training images should be in `dataset/images/train/`

---

## Dataset Structure

For training scripts to work properly, your dataset should follow this structure:

```
backend/dataset/
├── data.yaml           (Configuration file with class names and paths)
├── images/
│   ├── train/          (Training images collected via collect_data.py)
│   └── val/            (Optional: validation images)
└── labels/             (YOLO format labels for training images)
```

## Large Binary Files

⚠️ **Note**: The `backend/dataset/test_video.mov` file is a large binary video file used for testing. Do not commit to version control without proper `.gitignore` configuration.

---

## Future Improvements

- Add command-line arguments for customizing dataset paths
- Implement model evaluation and validation metrics
- Add data augmentation options
- Create separate validation/test dataset splits
