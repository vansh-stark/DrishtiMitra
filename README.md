# DrishtiMitra 👓

### AI-Based Assistive Navigation System for Visually Impaired Persons

DrishtiMitra is an AI-powered assistive navigation system designed to help visually impaired users understand their surrounding environment through real-time computer vision, object detection, depth estimation, hand gesture recognition, and voice interaction.

The system combines **YOLOv8, MiDaS, MediaPipe, OpenCV, and speech technologies** to provide real-time environmental awareness and interaction through an accessible interface.

---

## 📌 Project Overview

DrishtiMitra is designed as a computer-vision-based assistive system that analyzes the user's surroundings using a camera and provides meaningful information through audio and visual feedback.

The system can detect objects in the environment, estimate their relative depth, recognize hand gestures, and interact with the user through voice-based commands.

The project aims to demonstrate how modern AI and computer vision techniques can be integrated into an assistive technology system for real-world accessibility applications.

---

## ✨ Key Features

- 🎯 **Real-Time Object Detection**  
  Detects objects in the user's surroundings using YOLOv8.

- 📏 **Depth Estimation**  
  Uses the MiDaS depth-estimation model to estimate the relative distance of objects.

- 👋 **Hand Gesture Recognition**  
  Uses MediaPipe Hand Landmarker for recognizing hand-based interactions.

- 🗣️ **Voice Interaction**  
  Supports speech recognition and text-to-speech for hands-free interaction.

- 🔊 **Audio Feedback**  
  Provides information about detected objects and the surrounding environment through voice output.

- 📷 **Live Camera Processing**  
  Processes the camera feed in real time using OpenCV.

- 🤖 **Custom Object Detection Model**  
  Includes a custom-trained YOLOv8 model specifically integrated into DrishtiMitra.

- 🌐 **Web-Based Interface**  
  Provides an accessible browser-based interface powered by Flask.

- ⚡ **Local AI Processing**  
  The core computer-vision pipeline runs locally, reducing dependence on external AI APIs.

---

## ⚙️ How It Works

DrishtiMitra follows a real-time computer vision pipeline:

```text
                ┌─────────────────┐
                │   Camera Feed   │
                └────────┬────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   OpenCV Processing │
              └──────────┬──────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐
   │    YOLOv8       │       │     MiDaS       │
   │ Object Detection│       │ Depth Estimation│
   └────────┬────────┘       └────────┬────────┘
            │                         │
            └────────────┬────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Environment Analysis│
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
     ┌─────────────────┐   ┌─────────────────┐
     │ MediaPipe       │   │ Voice Processing│
     │ Hand Detection  │   │ Speech / TTS    │
     └────────┬────────┘   └────────┬────────┘
              │                     │
              └──────────┬──────────┘
                         ▼
                ┌─────────────────┐
                │ User Feedback   │
                │ Audio / Web UI  │
                └─────────────────┘
```

---

## 🧠 AI & Machine Learning Components

DrishtiMitra integrates multiple AI and computer vision models:

| Component | Technology | Purpose |
|---|---|---|
| Object Detection | YOLOv8 | Real-time detection of objects |
| Custom Object Detection | Custom YOLOv8 Model | Detection using the project's trained model |
| Depth Estimation | MiDaS | Relative depth estimation from camera frames |
| Hand Tracking | MediaPipe | Hand landmark and gesture detection |
| Computer Vision | OpenCV | Image processing and camera handling |
| Speech Recognition | SpeechRecognition | Converts user speech into commands |
| Text-to-Speech | pyttsx3 | Provides spoken feedback to the user |
| Deep Learning | PyTorch | Model inference and AI computation |

### Models Included

The repository contains the models required for running the application:

- `drishtimitra_best.pt` — Custom-trained YOLOv8 model
- `yolov8n.pt` — YOLOv8 Nano model
- `yolov8m.pt` — YOLOv8 Medium model used for training
- `hand_landmarker.task` — MediaPipe hand landmark model

> **Note:** The complete training dataset is not included in this repository because of its size. See the [Dataset](#-dataset) section for details.

---

## 📁 Project Structure

```text
DrishtiMitra/
│
├── backend/
│   ├── models/
│   │   ├── drishtimitra_best.pt
│   │   ├── yolov8m.pt
│   │   └── yolov8n.pt
│   │
│   ├── custom_dataset/
│   │   └── dataset.yaml
│   │
│   ├── hand_landmarker.task
│   ├── main.py
│   └── train.py
│
├── glasses.png
├── index.html
├── style.css
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vansh-stark/DrishtiMitra.git
cd DrishtiMitra
```

---

## 📊 Dataset

DrishtiMitra uses the **COCO (Common Objects in Context) dataset**, a publicly available large-scale dataset widely used for object detection and computer vision research.

For this project, a subset of the COCO dataset was prepared and converted into the **YOLO format** for training the custom YOLOv8 object-detection model.

### Dataset Details

- **Source:** COCO Dataset
- **Format:** YOLO
- **Images used:** 10,000
- **Annotation files:** 10,000
- **Object classes:** 70
- **Training framework:** Ultralytics YOLOv8

The prepared dataset configuration is available at:

```text
backend/custom_dataset/dataset.yaml
```

---

## 🏋️ Model Training

The custom object-detection model was trained using **Ultralytics YOLOv8** with the prepared COCO dataset.

The training pipeline is implemented in:

```text
backend/train.py
```

---

## 🛠️ Tech Stack

### Artificial Intelligence & Computer Vision
- **YOLOv8** — Real-time object detection
- **MiDaS** — Monocular depth estimation
- **MediaPipe** — Hand landmark detection
- **PyTorch** — Deep learning framework
- **OpenCV** — Computer vision and image processing

### Speech & Interaction
- **SpeechRecognition** — Speech-to-text interaction
- **pyttsx3** — Text-to-speech feedback

### Backend
- **Python**
- **Flask**

### Frontend
- **HTML5**
- **CSS3**
- **JavaScript**

### Dataset & Model Training
- **COCO Dataset**
- **Ultralytics YOLOv8**
- **Roboflow**
- **FiftyOne**

---

## 🔮 Future Scope

DrishtiMitra can be further developed into a more comprehensive assistive navigation platform.

Potential improvements include:

- 🧭 **Navigation Assistance** — Integration with GPS and digital maps for route guidance.
- 🚧 **Obstacle & Path Analysis** — Improved detection of obstacles and navigable paths.
- 📍 **Real-Time Distance Estimation** — More accurate estimation of object distance using depth and sensor fusion.
- 🧠 **Advanced Scene Understanding** — Integration of vision-language models for richer environmental descriptions.
- 📱 **Mobile Application** — Development of a dedicated Android/iOS application.
- 🥽 **Wearable Integration** — Integration with smart glasses or other wearable devices.
- ☁️ **Edge/Cloud Hybrid Processing** — Optimizing computationally intensive AI tasks for different hardware platforms.
- 🔊 **Personalized Audio Guidance** — Context-aware and user-configurable voice feedback.

---

## 🚧 Project Status

DrishtiMitra is currently a functional prototype demonstrating the integration of AI-based computer vision, depth estimation, hand tracking, and voice interaction for assistive applications.

Further development is planned to improve robustness, navigation capabilities, hardware integration, and real-world usability.

---

## ⚠️ Disclaimer

DrishtiMitra is an academic and research-oriented prototype developed to explore AI-based assistive technology.

It is **not a certified medical or safety device** and should not be relied upon as the sole means of navigation or personal safety.

---

## 👨‍💻 Author

**Vansh Bansal**

B.Tech Computer Science Engineering  
Jaypee Institute of Information Technology

### Connect with me

- GitHub: [@vansh-stark](https://github.com/vansh-stark)
- LinkedIn: [Vansh Bansal](https://www.linkedin.com/bansalvansh0911)
- Email: [Contact Me](mailto:bansal_vansh@outlook.com)

---

## ⭐ Support

If you find this project interesting, consider giving the repository a ⭐ on GitHub.