import cv2

# Contadores globais
cnt_up = 0
cnt_down = 0
cnt_inside_yellow = 0
total_unique_ids = set()

# Variáveis de controle de estado
paused = False
drawing = False
drawing_entry = True
drawing_mode = 'line'

# Listas globais
persons = []
entry_lines = []
yellow_lines = []
heatmap_data = []

# Outras variáveis globais
pid = 1
max_p_age = 5
ix, iy, fx, fy = -1, -1, -1, -1
frame_width, frame_height = 0, 0
areaTH = 0
font = cv2.FONT_HERSHEY_SIMPLEX
cap = None
out = None
last_frame = None
root = None
heatmap_movement_threshold = 10  # Ajuste conforme necessário
