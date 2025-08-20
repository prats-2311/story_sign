#!/usr/bin/env python3
"""
Full Body MediaPipe Tracking (Holistic Model)
This shows the complete skeleton like in StorySign
"""

import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Holistic (full body tracking)
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

print("Successfully imported MediaPipe Holistic for full body tracking.")

# Initialize webcam
cap = None 

try:
    # Open webcam (try 0 if 1 doesn't work)
    cap = cv2.VideoCapture(1)  # Change to 0 if needed
    
    # Configure MediaPipe Holistic model
    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1) as holistic:
        
        print("\nStarting full body tracking...")
        print("Position yourself so your full upper body is visible.")
        print(">>> Press 'q' to quit <<<")

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip image horizontally and convert BGR to RGB
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe Holistic
            results = holistic.process(image)

            # Convert back to BGR for display
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Draw FACE landmarks
            if results.face_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.face_landmarks,
                    mp_holistic.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_contours_style())
            
            # Draw POSE landmarks (body skeleton)
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_holistic.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles
                    .get_default_pose_landmarks_style(),
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_pose_connections_style())
            
            # Draw LEFT HAND landmarks
            if results.left_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.left_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles
                    .get_default_hand_landmarks_style(),
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_hand_connections_style())
            
            # Draw RIGHT HAND landmarks
            if results.right_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.right_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles
                    .get_default_hand_landmarks_style(),
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_hand_connections_style())

            # Show detection status
            status_text = []
            if results.face_landmarks:
                status_text.append("FACE")
            if results.pose_landmarks:
                status_text.append("POSE")
            if results.left_hand_landmarks:
                status_text.append("LEFT_HAND")
            if results.right_hand_landmarks:
                status_text.append("RIGHT_HAND")
            
            # Display status on image
            status = "Detected: " + ", ".join(status_text) if status_text else "No detection"
            cv2.putText(image, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Display the image
            cv2.imshow('Full Body MediaPipe Tracking', image)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

finally:
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("\nFull body tracking closed.")