#!/usr/bin/env python3
"""
Mock MediaPipe implementation for testing when MediaPipe is not available
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

class MockLandmarks:
    """Mock landmarks class"""
    def __init__(self):
        pass

class MockResults:
    """Mock MediaPipe results"""
    def __init__(self):
        self.left_hand_landmarks = None
        self.right_hand_landmarks = None
        self.face_landmarks = None
        self.pose_landmarks = None

class MockHolistic:
    """Mock MediaPipe Holistic class"""
    def __init__(self, **kwargs):
        logger.info("Using mock MediaPipe Holistic (MediaPipe not available)")
        
    def process(self, image):
        """Mock process method"""
        return MockResults()
    
    def close(self):
        """Mock close method"""
        pass

class MockDrawingUtils:
    """Mock drawing utilities"""
    @staticmethod
    def draw_landmarks(*args, **kwargs):
        """Mock draw landmarks - does nothing"""
        pass

class MockDrawingStyles:
    """Mock drawing styles"""
    @staticmethod
    def get_default_face_mesh_contours_style():
        return None
    
    @staticmethod
    def get_default_face_mesh_tesselation_style():
        return None
    
    @staticmethod
    def get_default_pose_landmarks_style():
        return None
    
    @staticmethod
    def get_default_pose_connections_style():
        return None
    
    @staticmethod
    def get_default_hand_landmarks_style():
        return None
    
    @staticmethod
    def get_default_hand_connections_style():
        return None

class MockSolutions:
    """Mock solutions module"""
    class holistic:
        Holistic = MockHolistic
        FACEMESH_CONTOURS = []
        FACEMESH_TESSELATION = []
        POSE_CONNECTIONS = []
        HAND_CONNECTIONS = []
    
    drawing_utils = MockDrawingUtils()
    drawing_styles = MockDrawingStyles()

class MockMediaPipe:
    """Mock MediaPipe module"""
    solutions = MockSolutions()
    __version__ = "0.10.7-mock"

# Create mock mediapipe module
import sys
sys.modules['mediapipe'] = MockMediaPipe()

logger.info("Mock MediaPipe module created successfully")