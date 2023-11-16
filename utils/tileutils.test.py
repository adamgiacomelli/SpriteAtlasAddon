import unittest
from helpers import AutoImageSize

# Mock Action class to simulate the action.frame_range attribute
class MockAction:
    def __init__(self, frame_range):
        self.frame_range = frame_range

class TestAutoImageSize(unittest.TestCase):
     def test_auto_image_size(self):
        # Test cases with mock actions
        test_cases = [
            ((64, 64, [{'action': MockAction((0, 9))}], 1, 1), (640, 64)),
            ((32, 48, [{'action': MockAction((0, 4))}], 4, 1), (160, 192)),
            ((50, 50, [{'action': MockAction((0, -1))}], 3, 1), (0, 150)),
            ((100, 100, [{'action': MockAction((0, 2))}], 0, 1), (300, 0)),
            ((256, 256, [{'action': MockAction((0, 40))}], 4, 4), (2816, 1024))
        ]

        for inputs, expected in test_cases:
            frame_width, frame_height, animations, rotations, step = inputs
            self.assertEqual(AutoImageSize(frame_width, frame_height, animations, rotations, step), expected)

if __name__ == '__main__':
    unittest.main()
