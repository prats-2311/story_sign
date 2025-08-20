# Pythong env variable and packages list
# conda create -n mediapipe_env python=3.11
# conda activate mediapipe_env
# pip install jupyter notebook mediapipe opencv-python
# cd path/to/your/project && jupyter notebook
# Cell 1: Imports and Initial Setup
# This cell imports all the necessary libraries.
# - cv2 (OpenCV) is for capturing the webcam feed.
# - mediapipe is for the hand tracking AI model.
# - time is used for small delays if needed.

import cv2
import mediapipe as mp
import time

# Initialize the core MediaPipe components.
# mp_hands provides the main Hand tracking solution.
# mp_drawing provides the utilities to draw the skeleton on the image.
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

print("Successfully imported all libraries and initialized MediaPipe components.")

# Cell 2: Live Hand Tracking Demonstration
# This cell contains the main loop to capture video, process it, and display the results.
# It will open a new window to show your webcam feed.

# Initialize a variable for the webcam capture.
cap = None 

try:
    # Open a connection to the webcam.
    # Index 1 worked for you before, but 0 is also a common default.
    # If 1 doesn't work, try changing this to 0.
    cap = cv2.VideoCapture(1) 
    
    # Configure and initialize the MediaPipe Hands model.
    # - model_complexity=0 is the fastest model, good for real-time.
    # - min_detection_confidence is how sure the model needs to be that a hand is present.
    # - min_tracking_confidence is how sure the model needs to be to continue tracking the hand.
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5) as hands:
        
        print("\nStarting webcam feed...")
        print("Place your hand in front of the camera.")
        print(">>> To close the video window, make it the active window and press the 'q' key. <<<")

        # Start a loop that runs as long as the webcam is open.
        while cap.isOpened():
            # Read a single frame from the webcam.
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame. Check webcam connection.")
                continue

            # --- Image Processing ---
            # 1. Flip the image horizontally for a natural "mirror" view.
            # 2. Convert the image color from BGR (OpenCV's default) to RGB, which MediaPipe requires.
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            
            # Process the image with the MediaPipe Hands model to find landmarks.
            results = hands.process(image)

            # Convert the image color back from RGB to BGR to display it correctly with OpenCV.
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # --- Drawing the Skeleton ---
            # Check if any hands were detected in the frame.
            if results.multi_hand_landmarks:
                # Loop through each detected hand.
                for hand_landmarks in results.multi_hand_landmarks:
                    # Use the drawing utility to draw the landmarks (dots) and connections (lines).
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=hand_landmarks,
                        connections=mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2, circle_radius=2),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(20, 180, 90), thickness=2, circle_radius=2)
                    )

            # Display the final, annotated image in a window named "Live Hand Tracking".
            cv2.imshow('Live Hand Tracking', image)
            
            # Wait for 5 milliseconds, and check if the 'q' key was pressed.
            # This is the standard way to handle quitting an OpenCV window.
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
finally:
    # This block ensures that all resources are properly released when the loop ends.
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("\nWebcam feed closed and all windows destroyed.")

