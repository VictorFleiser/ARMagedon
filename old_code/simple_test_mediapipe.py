import cv2
import mediapipe as mp
import numpy as np
import math

# Initialize MediaPipe solutions
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

def calculate_distance(point1, point2):
    """Calculates the Euclidean distance between two points."""
    return math.sqrt((point2.x - point1.x)**2 + (point2.y - point1.y)**2)

def is_hand_closed(hand_landmarks):
    """
    Checks if a hand is closed by calculating the distance between fingertips and the palm.
    A smaller total distance indicates a closed hand.
    """
    if not hand_landmarks:
        return False

    # Landmarks for fingertips
    fingertips = [
        hand_landmarks.landmark[mp_holistic.HandLandmark.THUMB_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.INDEX_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.MIDDLE_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.RING_FINGER_TIP],
        hand_landmarks.landmark[mp_holistic.HandLandmark.PINKY_TIP],
    ]

    # Landmark for the base of the palm
    palm_base = hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST]

    total_distance = sum(calculate_distance(tip, palm_base) for tip in fingertips)
    
    # This threshold may need adjustment for different hand sizes and camera distances
    return total_distance < 0.7 

def get_eye_aspect_ratio(eye_landmarks, frame_dimensions):
    """
    Calculates the Eye Aspect Ratio (EAR) to determine if an eye is closed.
    """
    if not eye_landmarks:
        return 0.0

    def get_coords(landmark_index):
        point = eye_landmarks[landmark_index]
        return int(point.x * frame_dimensions[1]), int(point.y * frame_dimensions[0])

    # Vertical landmarks
    p2_p6 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    p3_p5 = calculate_distance(eye_landmarks[2], eye_landmarks[4])

    # Horizontal landmarks
    p1_p4 = calculate_distance(eye_landmarks[0], eye_landmarks[3])

    if p1_p4 == 0:
        return 0.0
        
    ear = (p2_p6 + p3_p5) / (2.0 * p1_p4)
    return ear

# Start webcam capture
cap = cv2.VideoCapture(0)

with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Flip the frame horizontally for a later selfie-view display
        # and convert the BGR image to RGB.
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = holistic.process(frame)

        # Draw the annotations on the image.
        frame.flags.writeable = True
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        image_height, image_width, _ = frame.shape

        # --- Hand Tracking ---
        # Left Hand
        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            left_hand_wrist = results.left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST]
            left_hand_x = int(left_hand_wrist.x * image_width)
            left_hand_y = int(left_hand_wrist.y * image_height)
            cv2.putText(frame, f'Left Hand: ({left_hand_x}, {left_hand_y})', (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if is_hand_closed(results.left_hand_landmarks):
                cv2.putText(frame, 'Left Hand: Closed', (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Right Hand
        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            right_hand_wrist = results.right_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST]
            right_hand_x = int(right_hand_wrist.x * image_width)
            right_hand_y = int(right_hand_wrist.y * image_height)
            cv2.putText(frame, f'Right Hand: ({right_hand_x}, {right_hand_y})', (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if is_hand_closed(results.right_hand_landmarks):
                cv2.putText(frame, 'Right Hand: Closed', (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # --- Head Tracking (using face landmarks) ---
        if results.face_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS,
                mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1),
                mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1))
            
            nose = results.face_landmarks.landmark[1] # Using the nose tip as the head position
            head_x = int(nose.x * image_width)
            head_y = int(nose.y * image_height)
            cv2.putText(frame, f'Head: ({head_x}, {head_y})', (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # --- Eye Blink Detection ---
            face_landmarks = results.face_landmarks.landmark
            
            # Indices for left and right eye landmarks in MediaPipe Face Mesh
            # These are specific to the 468 landmark model
            left_eye_indices = [33, 160, 158, 133, 153, 144]
            right_eye_indices = [362, 385, 387, 263, 373, 380]
            
            left_eye_landmarks = [face_landmarks[i] for i in left_eye_indices]
            right_eye_landmarks = [face_landmarks[i] for i in right_eye_indices]
            
            left_ear = get_eye_aspect_ratio(left_eye_landmarks, (image_height, image_width))
            right_ear = get_eye_aspect_ratio(right_eye_landmarks, (image_height, image_width))
            
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Threshold for eye closure, may need adjustment
            EYE_AR_THRESH = 0.2
            if avg_ear < EYE_AR_THRESH:
                 cv2.putText(frame, "Eyes Closed", (10, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


        cv2.imshow('Bullet Hell Controller Test', frame)

        if cv2.waitKey(5) & 0xFF == 27: # Press 'ESC' to exit
            break

cap.release()
cv2.destroyAllWindows()