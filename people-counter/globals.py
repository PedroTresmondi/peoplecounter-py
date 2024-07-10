import cv2

paused = False
drawing = False
ix, iy, fx, fy = -1, -1, -1, -1
drawing_entry = True
drawing_mode = 'line'
entry_lines = []
yellow_lines = []
heatmap_data = []
last_frame = None
cnt_up = 0
cnt_down = 0
cnt_inside_yellow = 0
total_unique_ids = 0
unique_ids_in_yellow_area = set()
persons = []
max_p_age = 5
pid = 1
font = cv2.FONT_HERSHEY_SIMPLEX
