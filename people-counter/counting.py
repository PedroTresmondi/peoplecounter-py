import cv2

class CountingLine:
    def __init__(self, start_point, end_point, line_type):
        self.start_point = start_point
        self.end_point = end_point
        self.line_type = line_type  # 'entry' ou 'exit'

    def draw(self, frame):
        color = (0, 0, 255) if self.line_type == 'entry' else (255, 0, 0)
        cv2.line(frame, self.start_point, self.end_point, color, 2)

    def is_crossed(self, prev_cx, prev_cy, cx, cy):
        return ((self.end_point[0] - self.start_point[0]) * (cy - self.start_point[1]) -
                (self.end_point[1] - self.start_point[1]) * (cx - self.start_point[0])) * (
                (self.end_point[0] - self.start_point[0]) * (prev_cy - self.start_point[1]) -
                (self.end_point[1] - self.start_point[1]) * (prev_cx - self.start_point[0])) < 0

class YellowLine:
    def __init__(self, start_point, end_point):
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, frame):
        color = (0, 255, 255)  # Amarelo
        cv2.line(frame, self.start_point, self.end_point, color, 2)

    def contains(self, x, y):
        return (self.start_point[0] <= x <= self.end_point[0] and
                self.start_point[1] <= y <= self.end_point[1])
