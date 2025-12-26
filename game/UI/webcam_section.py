import pygame
import cv2
import mediapipe as mp
import numpy as np
import time
import math

# --- Mediapipe setup ---
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# --- Webcam setup ---
cap = cv2.VideoCapture(0)

# Semaphore Definitions
# Right hand, Left hand
SEMAPHORE_LETTERS = {
    ('Low Right', 'Down'): 'A',
    ('Down', 'Low Right'): 'A',
    ('Right', 'Down'): 'B',
    ('Down', 'Right',): 'B',
    ('High Right', 'Down'): 'C',
    ('Down', 'High Right'): 'C',
    ('Up', 'Down'): 'D',
    ('Down', 'Up'): 'D',
    ('Down', 'High Left'): 'E',
    ('High Left', 'Down'): 'E',
    ('Down', 'Left'): 'F',
    ('Left', 'Down'): 'F',
    ('Down', 'Low Left'): 'G',
    ('Low Left', 'Down'): 'G',
    ('Right', 'Low Right'): 'H',
    ('Low Right', 'Right'): 'H',
    ('High Right', 'Low Right'): 'I',
    ('Low Right', 'High Right'): 'I',
    ('Up', 'Right'): 'J',
    ('Right', 'Up'): 'J',
    ('Low Right', 'Up'): 'K',
    ('Up', 'Low Right'): 'K',
    ('Low Right', 'High Left'): 'L',
    ('High Left', 'Low Right'): 'L',
    ('Low Right', 'Left'): 'M',
    ('Left', 'Low Right'): 'M',
    ('Low Right', 'Low Left'): 'N',
    ('Low Left', 'Low Right'): 'N',
    ('High Right', 'Right'): 'O',
    ('Right', 'High Right'): 'O',
    ('Right', 'Up'): 'P',
    ('Up', 'Right'): 'P',
    ('Right', 'High Left'): 'Q',
    ('High Left', 'Right'): 'Q',
    ('Right', 'Left'): 'R',
    ('Left', 'Right'): 'R',
    ('Right', 'Low Left'): 'S',
    ('Low Left', 'Right'): 'S',
    ('High Right', 'Up'): 'T',
    ('Up', 'High Right'): 'T',
    ('High Right', 'High Left'): 'U',
    ('High Left', 'High Right'): 'U',
    ('Up', 'Low Left'): 'V',
    ('Low Left', 'Up'): 'V',
    ('Left', 'High Left'): 'W',
    ('High Left', 'Left'): 'W',
    ('Low Left', 'High Left'): 'X',
    ('High Left', 'Low Left'): 'X',
    ('High Right', 'Left'): 'Y',
    ('Left', 'High Right'): 'Y',
    ('Low Left', 'Left'): 'Z',
    ('Left', 'Low Left'): 'Z',
    ('Down', 'Down'): 'SPACE', # Bomb
    # UNUSED COMBINATIONS :
    ('Low Left', 'High Right'): 'CANCEL',
    ('High Right', 'Low Left'): 'CANCEL',
    ('High Left', 'Up'): 'NUMERIC',
    ('Up', 'High Left'): 'NUMERIC',
    ('Left', 'Up'): 'unused_1',
    ('Up', 'Left'): 'unused_1',
    ('Up', 'Up'): 'unused_2',
    ('High Right', 'High Right'): 'unused_3',
    ('Right', 'Right'): 'unused_4',
    ('Low Right', 'Low Right'): 'unused_5',
    ('Low Left', 'Low Left'): 'unused_6',
    ('Left', 'Left'): 'unused_7',
    ('High Left', 'High Left'): 'unused_8',
}

# Helper Functions
def calculate_angle(point1, point2):
    """Calculates angle between two points (origin: point1) in degrees"""
    if not (isinstance(point1, (tuple, list)) and isinstance(point2, (tuple, list))):
        return 0
    angle = math.degrees(math.atan2(point2[1] - point1[1], point2[0] - point1[0]))
    return angle

def get_palm_top_coords(hand_landmarks, image_width, image_height):
    """Calculates the center of palm"""
    mcp_ids = [
        mp_holistic.HandLandmark.INDEX_FINGER_MCP, mp_holistic.HandLandmark.MIDDLE_FINGER_MCP,
        mp_holistic.HandLandmark.RING_FINGER_MCP, mp_holistic.HandLandmark.PINKY_MCP,
    ]
    xs = [hand_landmarks.landmark[lm_id].x * image_width for lm_id in mcp_ids]
    ys = [hand_landmarks.landmark[lm_id].y * image_height for lm_id in mcp_ids]
    if not xs: return None
    return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))

def get_hand_position(angle):
    if -22.5 <= angle <= 22.5: return 'Right'
    elif 22.5 < angle <= 67.5: return 'Low Right'
    elif 67.5 < angle <= 112.5: return 'Down'
    elif 112.5 < angle <= 157.5: return 'Low Left'
    elif 157.5 < angle <= 180 or -180 <= angle <= -157.5: return 'Left'
    elif -157.5 < angle <= -112.5: return 'High Left'
    elif -112.5 < angle <= -67.5: return 'Up'
    elif -67.5 < angle < -22.5: return 'High Right'
    return None

def get_position_angle(position):
    """Get the angle (degrees) for a hand position"""
    position_angles = {'Right': 0, 'Low Right': 45, 'Down': 90, 'Low Left': 135,
                       'Left': 180, 'High Left': -135, 'Up': -90, 'High Right': -45}
    return position_angles.get(position, 0)

def draw_guide_lines(frame, body_center, detected_letter, image_width, image_height):
    """Draws purple guide lines showing optimal hand positions.
    Also draw semi-transparent angles from center"""
    if not body_center or not detected_letter: return
    
    target_positions = next(((rh, lh) for (rh, lh), letter in SEMAPHORE_LETTERS.items() if letter == detected_letter), None)
    if not target_positions: return

    line_length = min(image_width, image_height) // 4
    
    for hand, target_pos in zip(["R", "L"], target_positions):
        angle_deg = get_position_angle(target_pos)
        angle_rad = math.radians(angle_deg)
        end_x = int(body_center[0] + line_length * math.cos(angle_rad))
        end_y = int(body_center[1] + line_length * math.sin(angle_rad))
        cv2.line(frame, body_center, (end_x, end_y), (255, 0, 255), 3)
        cv2.putText(frame, f'{hand}:{target_pos}', (end_x + 5, end_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

def draw_additional_guidelines(frame, body_center):
    for angle in range(-180, 180, 45):
        line_length = 1000
        angle_rad = math.radians(angle + 22.5)
        end_x = int(body_center[0] + line_length * math.cos(angle_rad))
        end_y = int(body_center[1] + line_length * math.sin(angle_rad))
        cv2.line(frame, body_center, (end_x, end_y), (255, 255, 255), 2)

class WebcamPanel:
    def __init__(self, rect, webcam_logger):
        self.rect = rect
        self.holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.webcam_logger = webcam_logger

        # for logging purposes
        self.valid_landmarks_flag = False
        self.last_detected_semaphore = "None"

    def update(self):
        ret, frame = cap.read()
        if not ret:
            return None, "NONE"
        
        frame = cv2.flip(frame, 1)
        image_height, image_width, _ = frame.shape
        
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_image.flags.writeable = False
        results = self.holistic.process(rgb_image)
        rgb_image.flags.writeable = True
        
        body_center = None
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Body Center Calculation
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
            
            if left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5 and nose.visibility > 0.5:
                shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
                shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
                
                # Average the Y of the shoulder midpoint and the nose
                body_center_x = shoulder_mid_x * image_width
                body_center_y = ((shoulder_mid_y + nose.y) / 2) * image_height
                
                body_center = (int(body_center_x), int(body_center_y))
                cv2.circle(frame, body_center, 7, (255, 0, 0), -1) # Blue circle

                draw_additional_guidelines(frame, body_center)

        # Hand position detection
        physical_right_hand_pos = None # User's right hand (screen left)
        physical_left_hand_pos = None  # User's left hand (screen right)

        # Right hand (Screen Left)
        right_hand_coords = None
        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            right_hand_coords = get_palm_top_coords(results.left_hand_landmarks, image_width, image_height)
        elif results.pose_landmarks:
            wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            if wrist.visibility > 0.5:
                right_hand_coords = (int(wrist.x * image_width), int(wrist.y * image_height))
        
        if right_hand_coords and body_center:
            angle = calculate_angle(body_center, right_hand_coords)
            physical_right_hand_pos = get_hand_position(angle)
            cv2.line(frame, body_center, right_hand_coords, (200, 200, 0), 2)
            if physical_right_hand_pos:
                cv2.putText(frame, f'Right Hand (Screen): {physical_right_hand_pos}', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 0), 2)

        # Left hand (Screen Right)
        left_hand_coords = None
        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            left_hand_coords = get_palm_top_coords(results.right_hand_landmarks, image_width, image_height)
        elif results.pose_landmarks:
            wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
            if wrist.visibility > 0.5:
                left_hand_coords = (int(wrist.x * image_width), int(wrist.y * image_height))
        
        if left_hand_coords and body_center:
            angle = calculate_angle(body_center, left_hand_coords)
            physical_left_hand_pos = get_hand_position(angle)
            cv2.line(frame, body_center, left_hand_coords, (0, 255, 0), 2)
            if physical_left_hand_pos:
                 cv2.putText(frame, f'Left Hand (Screen): {physical_left_hand_pos}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
        # Logging
        if self.valid_landmarks_flag :
            if not (left_hand_coords and right_hand_coords and body_center):
                self.webcam_logger.invalid_detection({
                    'right_hand': right_hand_coords,
                    'left_hand': left_hand_coords,
                    'body_center': body_center
                })
                self.valid_landmarks_flag = False
        else :
            if left_hand_coords and right_hand_coords and body_center:
                self.webcam_logger.valid_detection({
                    'right_hand': right_hand_coords,
                    'left_hand': left_hand_coords,
                    'body_center': body_center
                })
                self.valid_landmarks_flag = True

        # Semaphore Interpretation
        detected_semaphore = "NONE"
        if physical_right_hand_pos and physical_left_hand_pos:
            key = (physical_right_hand_pos, physical_left_hand_pos)
            detected_semaphore = SEMAPHORE_LETTERS.get(key, "NONE")
            if detected_semaphore != "NONE":
                 draw_guide_lines(frame, body_center, detected_semaphore, image_width, image_height)
        
        # Logging
        if detected_semaphore != self.last_detected_semaphore:
            self.last_detected_semaphore = detected_semaphore
            self.webcam_logger.semaphore_detected(detected_semaphore, {
                'right_hand': right_hand_coords,
                'left_hand': left_hand_coords,
                'body_center': body_center
            })
        return frame, detected_semaphore

    def draw(self, surface, frame):
        if frame is None:
            return
            
        x, y, w, h = self.rect
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (w, h))
        
        frame_surface = pygame.surfarray.make_surface(np.rot90(frame))
        frame_surface = pygame.transform.flip(frame_surface, True, False)
        
        surface.blit(frame_surface, (x, y))

    def __del__(self):
        self.holistic.close()