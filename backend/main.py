import os
import cv2
import torch
import pyttsx3
import threading
import time
import numpy as np
import mediapipe as mp
import pyaudio
import speech_recognition as sr
import wave
from ultralytics import YOLO
from flask import Flask, Response, jsonify, send_from_directory, request

app = Flask(__name__, static_folder='../')




ai_state = {
    "objects": [],
    "scene_descriptions": [],
    "touch_event": None,
    "fps": 0,
    "object_count": 0,
    "haptic_motors": [],
    "terminal_messages": [],
    "is_recording": False
}

guidance_state = {
    "active": False,
    "target": ""
}


audio_state = {
    "mic_index": None,
    "speaker_index": None,
    "manual_trigger": False
}

def get_audio_devices():
    p = pyaudio.PyAudio()
    devices = {"mics": [], "speakers": []}
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices["mics"].append({"id": i, "name": info["name"]})
        if info["maxOutputChannels"] > 0:
            devices["speakers"].append({"id": i, "name": info["name"]})
    
    if audio_state["mic_index"] is None:
        try:
            audio_state["mic_index"] = p.get_default_input_device_info()["index"]
        except Exception:
            pass
    if audio_state["speaker_index"] is None:
        try:
            audio_state["speaker_index"] = p.get_default_output_device_info()["index"]
        except Exception:
            pass
            
    p.terminate()
    return devices

get_audio_devices()

import queue

tts_queue = queue.Queue()

def tts_worker():
    import pythoncom
    while True:
        text = tts_queue.get()
        if text is None:
            break
            
        print("Speaking:", text)
        filename = "temp_speech.wav"
        try:
            pythoncom.CoInitialize()
            engine = pyttsx3.init()
            engine.save_to_file(text, filename)
            engine.runAndWait()
            del engine
            pythoncom.CoUninitialize()
            
            if os.path.exists(filename):
                wf = wave.open(filename, 'rb')
                p = pyaudio.PyAudio()
                
                out_idx = audio_state["speaker_index"]
                if out_idx is not None:
                    out_idx = int(out_idx)
                    
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True,
                                output_device_index=out_idx)
                data = wf.readframes(1024)
                while len(data) > 0:
                    stream.write(data)
                    data = wf.readframes(1024)
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                try:
                    wf.close()
                    os.remove(filename)
                except:
                    pass
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            tts_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

def speak(text):
    tts_queue.put(text)

camera_index = 1
yolo_model_base = YOLO("models/yolov8n.pt")
yolo_model_custom = YOLO("models/drishtimitra_best.pt")

print("Loading MiDaS depth model...")
midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
midas.to(device)
midas.eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.small_transform

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import urllib.request

model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print("Downloading MediaPipe Hand Landmarker model...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", model_path)

base_options = mp_python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
hand_detector = vision.HandLandmarker.create_from_options(options)



def get_horizontal_position(x_center, frame_width):
    third = frame_width / 3
    if x_center < third:
        return "left"
    elif x_center < 2 * third:
        return "center"
    else:
        return "right"

def get_depth_estimate(depth_map, x1, y1, x2, y2):
    object_depth = np.median(depth_map[y1:y2, x1:x2])
    if object_depth == 0:
        return 0
    estimated_distance_meters = 1000.0 / object_depth
    return round(estimated_distance_meters, 1)

def check_touch_interaction(hand_landmarks_list, objects, frame_width, frame_height):
    if not hand_landmarks_list or not objects:
        return None
    for hand_landmarks in hand_landmarks_list:
        index_tip = hand_landmarks[8]
        tip_x = int(index_tip.x * frame_width)
        tip_y = int(index_tip.y * frame_height)
        for obj in objects:
            x1, y1, x2, y2, cls_name = obj
            if x1 <= tip_x <= x2 and y1 <= tip_y <= y2:
                return cls_name
    return None

def process_command_logic(command):
    command = command.lower()
    response = "Command not recognized."
    
    if command.startswith("what is in my hand"):
        if ai_state["touch_event"]:
            response = ai_state["touch_event"]
        else:
            response = "You are not touching anything."
            
    elif command.startswith("describe surroundings"):
        if ai_state["scene_descriptions"]:
            response = "I see: " + ", ".join(ai_state["scene_descriptions"])
        else:
            response = "I don't see any recognized objects right now."

    elif command.startswith("where is") or command.startswith("find"):
        target = command.replace("where is", "").replace("find", "").strip()
        found = False
        for desc in ai_state["scene_descriptions"]:
            if target in desc.lower():
                response = f"{target.capitalize()} detected: {desc}"
                found = True
                break
        if not found:
            response = f"{target.capitalize()} not found in current view."
            
    elif command.startswith("assist me find") or command.startswith("help me find") or command.startswith("guide me to"):
        target = command.replace("assist me find", "").replace("help me find", "").replace("guide me to", "").strip()
        guidance_state["active"] = True
        guidance_state["target"] = target
        ai_state["guidance_reached"] = False
        response = f"Guidance mode activated for {target}. Please raise your hand into the camera view."
        
    return response

def audio_listener_thread():
    recognizer = sr.Recognizer()
    while True:
        try:
            mic_idx = audio_state["mic_index"]
            if mic_idx is None:
                time.sleep(1)
                continue
                
            mic_idx = int(mic_idx)
            with sr.Microphone(device_index=mic_idx) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                ai_state["is_recording"] = audio_state["manual_trigger"]
                
                try:

                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    continue
                
                ai_state["is_recording"] = False
                
            try:
                transcript = recognizer.recognize_google(audio).lower()
                print("Heard:", transcript)
                
                if audio_state["manual_trigger"]:
                    audio_state["manual_trigger"] = False
                    ai_state["terminal_messages"].append(f"> {transcript}")
                    response = process_command_logic(transcript)
                    ai_state["terminal_messages"].append(response)
                    speak(response)
                    
                elif "vision" in transcript:
                    idx = transcript.find("vision")
                    cmd = transcript[idx+6:].strip()
                    if len(cmd) > 2:
                        ai_state["terminal_messages"].append(f"> {cmd}")
                        response = process_command_logic(cmd)
                        ai_state["terminal_messages"].append(response)
                        speak(response)
                    else:
                        audio_state["manual_trigger"] = True
                        
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print("Speech recognition service error:", e)
                
        except Exception as e:
            print("Audio listener error:", e)
            time.sleep(2)


listener_thread = threading.Thread(target=audio_listener_thread, daemon=True)
listener_thread.start()



def generate_frames():
    global camera_index
    cap = cv2.VideoCapture(camera_index)
    
    last_spoken_time = 0
    last_touch_spoken = 0
    prev_time = 0
    frame_count = 0
    cached_depth_map = None
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = time.time()
        fps = int(1 / (current_time - prev_time)) if prev_time > 0 else 0
        prev_time = current_time
        
        frame_height, frame_width = frame.shape[:2]
        
        results_base = yolo_model_base(frame, verbose=False)
        results_custom = yolo_model_custom(frame, verbose=False)
        all_results = results_base + results_custom
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        if frame_count % 5 == 0 or cached_depth_map is None:
            input_batch = transform(img_rgb).to(device)
            with torch.no_grad():
                prediction = midas(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img_rgb.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            cached_depth_map = prediction.cpu().numpy()
        
        depth_map = cached_depth_map
        frame_count += 1
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection_result = hand_detector.detect(mp_image)
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                tip_x = int(hand_landmarks[8].x * frame_width)
                tip_y = int(hand_landmarks[8].y * frame_height)
                cv2.circle(frame, (tip_x, tip_y), 10, (0, 0, 255), -1)
        
        detected_objects = []
        scene_descriptions = []
        api_objects = []
        
        for result in all_results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                cls_id = int(box.cls[0].item())
                cls_name = result.names[cls_id]
                
                if conf < 0.5:
                    continue
                
                detected_objects.append((x1, y1, x2, y2, cls_name))
                
                x_center = (x1 + x2) / 2
                position = get_horizontal_position(x_center, frame_width)
                distance = get_depth_estimate(depth_map, x1, y1, x2, y2)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{cls_name} {distance:.1f}m", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                scene_descriptions.append(f"{cls_name} on {position} at {distance:.1f} meters")
                api_objects.append(f"{cls_name} - {position.capitalize()}")
        
        touched_object = check_touch_interaction(detection_result.hand_landmarks, detected_objects, frame_width, frame_height)
        current_time = time.time()
        
        ai_state["objects"] = api_objects
        ai_state["scene_descriptions"] = scene_descriptions
        ai_state["fps"] = fps
        ai_state["object_count"] = len(detected_objects)
        
        haptic_motors = []
        if guidance_state["active"]:
            target_obj = None
            for obj in detected_objects:
                if guidance_state["target"] in obj[4].lower():
                    target_obj = obj
                    break
            
            if target_obj and detection_result.hand_landmarks:
                x1, y1, x2, y2, cls_name = target_obj
                obj_cx = (x1 + x2) / 2
                obj_cy = (y1 + y2) / 2
                
                hand_landmarks = detection_result.hand_landmarks[0]
                tip_x = hand_landmarks[8].x * frame_width
                tip_y = hand_landmarks[8].y * frame_height
                
                if x1 <= tip_x <= x2 and y1 <= tip_y <= y2:
                    haptic_motors = ["motor-tl", "motor-bl", "motor-tr", "motor-br", "blink"]
                    ai_state["guidance_reached"] = True
                    guidance_state["active"] = False
                    msg = "Object reached"
                    ai_state["terminal_messages"].append(f"System: {msg}")
                    speak(msg)
                else:
                    if obj_cx > tip_x + 50:
                        haptic_motors.extend(["motor-tr", "motor-br"])
                    elif obj_cx < tip_x - 50:
                        haptic_motors.extend(["motor-tl", "motor-bl"])
                    
                    if obj_cy > tip_y + 50:
                        haptic_motors.extend(["motor-bl", "motor-br"])
                    elif obj_cy < tip_y - 50:
                        haptic_motors.extend(["motor-tl", "motor-tr"])

        ai_state["haptic_motors"] = list(set(haptic_motors))
        
        if touched_object:
            msg = f"Your hand is on a {touched_object}"
            ai_state["touch_event"] = msg
        else:
            ai_state["touch_event"] = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()


@app.route('/')
def index():
    return send_from_directory('../', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('../', 'style.css')

@app.route('/glasses.png')
def glasses_img():
    return send_from_directory('../', 'glasses.png')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    return jsonify(ai_state)

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    command = data.get('command', '').lower()
    
    ai_state["terminal_messages"].append(f"> {command}")
    response = process_command_logic(command)
    ai_state["terminal_messages"].append(response)
    speak(response)
    
    return jsonify({"response": response})

@app.route('/api/devices')
def api_devices():
    return jsonify(get_audio_devices())

@app.route('/api/set_device', methods=['POST'])
def api_set_device():
    data = request.json
    if "mic_index" in data:
        audio_state["mic_index"] = int(data["mic_index"])
    if "speaker_index" in data:
        audio_state["speaker_index"] = int(data["speaker_index"])
    return jsonify({"success": True})

@app.route('/api/start_voice', methods=['POST'])
def api_start_voice():
    audio_state["manual_trigger"] = True
    return jsonify({"success": True})

@app.route('/api/clear_messages', methods=['POST'])
def api_clear_messages():
    ai_state["terminal_messages"] = []
    return jsonify({"success": True})

@app.route('/api/camera', methods=['POST'])
def switch_camera():
    global camera_index
    data = request.json
    idx = data.get('index', 1)
    camera_index = int(idx)
    return jsonify({"success": True})

if __name__ == "__main__":
    print("Starting Web Server on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
