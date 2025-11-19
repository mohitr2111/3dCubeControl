# 3D Object Manipulation with Hand Gestures

Control 3D objects in real-time using hand gestures! This project combines MediaPipe hand tracking with OpenGL 3D rendering to create an interactive experience where you can manipulate a 3D cube using only your hand movements.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.12-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.30-orange.svg)
![PyGame](https://img.shields.io/badge/PyGame-2.6-yellow.svg)
![PyOpenGL](https://img.shields.io/badge/PyOpenGL-3.1-red.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

## ✨ Features

- **Real-time Hand Tracking**: Advanced hand detection using MediaPipe's latest Tasks API
- **3D Object Manipulation**: Control a beautifully rendered 3D cube with lighting and shadows
- **Intuitive Gestures**:
  - Open hand movement → Rotate the cube
  - Pinch gesture → Zoom in/out
  - Hand movement → Multi-axis rotation control
- **Smooth Animations**: Optimized rendering with gesture smoothing
- **Live Feedback**: On-screen HUD showing rotation, zoom, and FPS
- **Automatic Model Download**: MediaPipe model downloads automatically on first run

## 🎮 How to Use

### Hand Gestures

- **Open Hand + Move Left/Right**: Rotate cube on Y-axis (horizontal rotation)
- **Open Hand + Move Up/Down**: Rotate cube on X-axis (vertical rotation)
- **Pinch (Thumb + Index)**: Zoom in/out by moving fingers together/apart
- **Close Hand**: Pause manipulation (cube enters idle rotation)

### Keyboard Controls

- **R**: Reset view to default position
- **Q** or **ESC**: Quit application

## 🖼️ How It Works

1. **Webcam captures your hand** in real-time
2. **MediaPipe detects 21 hand landmarks** with high accuracy
3. **Gesture recognition** interprets hand position and finger states
4. **OpenGL renders** the 3D scene with your manipulations
5. **Smooth transitions** for natural interaction

## 🔧 Requirements

- **Python 3.10+** (tested with Python 3.13)
- **Webcam** (built-in or external)
- **Operating System**: macOS, Linux, or Windows

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone <repo-url>
cd 3d-object-manipulation
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Ensure your webcam is connected and accessible before running the application.

### 4. Run the Application

```bash
python3 main.py
```

**Note**: The file is named `main.py` in the repository, but you can rename it to `hand_gesture_3d.py` if preferred.

### 5. About the Hand Tracking Model

#### What is `hand_landmarker.task`?

The `hand_landmarker.task` file is a **pre-trained machine learning model** (7.5MB) that enables MediaPipe to detect and track 21 hand landmarks in real-time. This model is essential for the application to work.

#### Why it's not in the repository?

The model file is **excluded from Git** because:

- It's a large binary file (7.5MB) that would bloat the repository
- It's automatically downloaded by the application on first run
- Users always get the latest official version from Google's servers

#### Automatic Download (Recommended)

The model **downloads automatically** the first time you run the application:

```bash
python3 main.py
# Output: "Downloading hand landmark model..."
# Output: "Model downloaded!"
```

#### Manual Download (Optional)

If you prefer to download the model manually or need offline setup:

```bash
# Download the model file directly
curl -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

# Or using wget
wget -O hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

**Model Details:**

- **File**: `hand_landmarker.task`
- **Size**: ~7.5 MB
- **Type**: MediaPipe Hand Landmarker (float16)
- **Detects**: 21 hand landmarks per hand
- **Source**: [Google MediaPipe Models](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)

## 📦 Dependencies

- **opencv-python** - Webcam capture and image processing
- **mediapipe** - Hand landmark detection and tracking (new Tasks API)
- **numpy** - Mathematical operations for 3D transformations
- **pygame** - Window management and event handling
- **PyOpenGL** - 3D graphics rendering

See `requirements.txt` for exact versions.

## 🛠️ Troubleshooting

### Camera Not Working

- Ensure your webcam is connected and not in use by another application
- Grant camera permissions:
  - **macOS**: System Preferences → Security & Privacy → Privacy → Camera
  - **Windows**: Settings → Privacy → Camera
  - Enable access for Terminal/Python

### Hand Not Detected

- Ensure good lighting conditions
- Keep your hand clearly visible and centered in the camera view
- Try adjusting detection confidence in code (lines 98-100)
- Keep hand at comfortable distance from camera

### Performance Issues

- Close other applications using the webcam
- Reduce video resolution if needed (modify `Config.WEBCAM_WIDTH/HEIGHT`)
- Ensure you have a compatible GPU for OpenGL rendering

### Module Import Errors

- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.10+)

### OpenGL Issues

- **macOS**: Should work out of the box
- **Linux**: May need to install: `sudo apt-get install python3-opengl`
- **Windows**: Ensure graphics drivers are up to date

## 🎨 Customization

You can customize various aspects by modifying `hand_gesture_3d.py`:

### Adjust Sensitivity

```python
# Lines 34-44 - Configuration
class Config:
    ROTATION_SENSITIVITY = 0.3  # Increase for faster rotation
    ZOOM_SENSITIVITY = 0.015     # Increase for faster zoom
    SMOOTHING_FACTOR = 0.4       # Lower for more responsive (less smooth)
    ZOOM_MIN = -15.0             # Maximum zoom out
    ZOOM_MAX = -2.0              # Maximum zoom in
```

### Change Cube Colors

```python
# Lines 335-342 - Cube face colors
faces = [
    ([0, 0, 1], [0.9, 0.2, 0.2], ...),  # Red face
    ([0, 0, -1], [0.2, 0.9, 0.2], ...),  # Green face
    # Modify RGB values [R, G, B] where each is 0.0-1.0
]
```

### Modify Detection Confidence

```python
# Lines 94-100 - Hand detection settings
options = vision.HandLandmarkerOptions(
    # ...
    min_hand_detection_confidence=0.5,  # Increase for stricter detection
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5         # Increase for smoother tracking
)
```

## 📊 Technical Details

- **Hand Tracking**: MediaPipe Tasks API (new, optimized version)
- **21 Landmarks**: Tracks all finger joints and palm points
- **Gesture Recognition**: Custom algorithm detecting open hand and pinch
- **Smoothing Algorithm**: Moving average with configurable window
- **3D Rendering**: OpenGL with Phong lighting model
- **Frame Rate**: Typically 30-60 FPS depending on hardware

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](#) file for details.

## 🙏 Acknowledgments

- [MediaPipe](https://google.github.io/mediapipe/) by Google for advanced hand tracking
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [PyGame](https://www.pygame.org/) for window management
- [PyOpenGL](http://pyopengl.sourceforge.net/) for 3D graphics

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features or gestures
- Submit pull requests
- Improve documentation

## 🔮 Future Enhancements

Potential improvements:

- Multiple hand support for two-handed manipulation
- Different 3D objects (sphere, pyramid, custom models)
- Gesture recording and playback
- VR/AR integration
- Multi-object scene manipulation

## 📧 Contact

For questions, feedback, or collaborations, please open an issue on the repository.

---

**Control reality with your hands! 🖐️✨**
