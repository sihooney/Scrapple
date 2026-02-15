"""
Camera Index Finder
====================
Run this script to find available camera indices on your system.
Use this to identify the OBS Virtual Camera index.

Usage:
    python camera_test.py
"""

import cv2
import sys


def find_cameras(max_index=10):
    """Test camera indices 0 through max_index and report which ones work."""
    print("=" * 60)
    print("  CAMERA INDEX FINDER")
    print("=" * 60)
    print(f"\nTesting camera indices 0-{max_index}...\n")
    
    available = []
    
    for i in range(max_index + 1):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Try to read a frame to confirm it's working
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                # Try to get camera name (may not work on all systems)
                backend = cap.getBackendName()
                print(f"  [OK] Index {i}: {w}x{h} ({backend})")
                available.append(i)
            else:
                print(f"  [--] Index {i}: Opens but no frames (may be in use)")
            cap.release()
        else:
            print(f"  [  ] Index {i}: Not available")
    
    print("\n" + "=" * 60)
    print(f"  AVAILABLE CAMERAS: {available if available else 'None found'}")
    print("=" * 60)
    
    if available:
        print("\nTo use a camera in Scrapple, update your .env file:")
        print(f"  CV_LIVE_FEED_CAMERA={available[0]}")
        if len(available) > 1:
            print(f"  CV_CAMERA_FEED_INDEX={available[1]}")
        print("\nTip: OBS Virtual Camera usually appears as 'OBS Virtual Camera'")
        print("     and is typically at index 0, 1, or after your physical cameras.")
    
    return available


def preview_camera(index):
    """Preview a specific camera index."""
    print(f"\nPreviewing camera index {index}... (Press 'q' to quit)")
    
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"ERROR: Could not open camera {index}")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No frame received")
            break
        
        # Add index label to frame
        cv2.putText(frame, f"Camera Index: {index}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow(f"Camera {index} Preview", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Find all cameras
    cameras = find_cameras()
    
    # If a specific index is provided, preview it
    if len(sys.argv) > 1:
        try:
            index = int(sys.argv[1])
            preview_camera(index)
        except ValueError:
            print(f"Invalid index: {sys.argv[1]}")
    elif cameras:
        print(f"\nTo preview a camera, run: python camera_test.py <index>")
        print(f"Example: python camera_test.py {cameras[0]}")
