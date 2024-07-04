from datetime import time
import numpy as np
import cv2
import torch
import Person
import time
import tkinter as tk

class CountingLine:
    def __init__(self, start_point, end_point, line_type):
        self.start_point = start_point
        self.end_point = end_point
        self.line_type = line_type  # 'entry' or 'exit'

    def draw(self, frame):
        color = (0, 0, 255) if self.line_type == 'entry' else (255, 0, 0)
        cv2.line(frame, self.start_point, self.end_point, color, 2)

    def is_crossed(self, prev_cx, prev_cy, cx, cy):
        return ((self.end_point[0] - self.start_point[0]) * (cy - self.start_point[1]) -
                (self.end_point[1] - self.start_point[1]) * (cx - self.start_point[0])) * (
                       (self.end_point[0] - self.start_point[0]) * (prev_cy - self.start_point[1]) -
                       (self.end_point[1] - self.start_point[1]) * (prev_cx - self.start_point[0])) < 0

class CountingArea:
    def __init__(self, start_point, end_point, area_type):
        self.start_point = start_point
        self.end_point = end_point
        self.area_type = area_type  # 'entry' or 'exit'

    def draw(self, frame):
        color = (0, 0, 255) if self.area_type == 'entry' else (255, 0, 0)
        cv2.rectangle(frame, self.start_point, self.end_point, color, 2)

    def contains(self, x, y):
        return (self.start_point[0] < x < self.end_point[0] and
                self.start_point[1] < y < self.end_point[1])

cnt_up = 0
cnt_down = 0

# Variáveis para desenhar as linhas e áreas
drawing = False  # Verdadeiro se o mouse estiver pressionado
paused = False  # Estado de pausa do vídeo
entry_lines = []  # Lista para armazenar as linhas de entrada
exit_lines = []  # Lista para armazenar as linhas de saída
entry_areas = []  # Lista para armazenar as áreas de entrada
exit_areas = []  # Lista para armazenar as áreas de saída
ix, iy = -1, -1  # Coordenadas iniciais da linha/área
fx, fy = -1, -1  # Coordenadas finais da linha/área
drawing_entry = True  # Flag para desenhar linhas/áreas de entrada
drawing_mode = 'line'  # 'line' ou 'area'
frame_skip = 3  # Processar a cada 3 frames para melhorar a detecção
frame_count = 0

# Função de callback do mouse
def draw_shape(event, x, y, flags, param):
    global ix, iy, fx, fy, drawing, drawing_mode, entry_lines, exit_lines, entry_areas, exit_areas, drawing_entry

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        print(f"Mouse down: ({ix}, {iy})")

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            fx, fy = x, y
            print(f"Mouse move: ({fx}, {fy})")

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = x, y
        print(f"Mouse up: ({fx}, {fy})")
        if drawing_mode == 'line':
            line_type = 'entry' if drawing_entry else 'exit'
            if line_type == 'entry':
                entry_lines.append(CountingLine((ix, iy), (fx, fy), line_type))  # Adicionar a linha de entrada à lista
            else:
                exit_lines.append(CountingLine((ix, iy), (fx, fy), line_type))  # Adicionar a linha de saída à lista
        elif drawing_mode == 'area':
            area_type = 'entry' if drawing_entry else 'exit'
            if area_type == 'entry':
                entry_areas.append(CountingArea((ix, iy), (fx, fy), area_type))  # Adicionar a área de entrada à lista
            else:
                exit_areas.append(CountingArea((ix, iy), (fx, fy), area_type))  # Adicionar a área de saída à lista

# Funções para os botões
def pause_video():
    global paused
    paused = not paused

def set_entry_shape():
    global drawing_entry
    drawing_entry = True

def set_exit_shape():
    global drawing_entry
    drawing_entry = False

def set_drawing_mode_line():
    global drawing_mode
    drawing_mode = 'line'

def set_drawing_mode_area():
    global drawing_mode
    drawing_mode = 'area'

# Configuração da interface gráfica
root = tk.Tk()
root.title("Contador de Pessoas")

frame = tk.Frame(root)
frame.pack()

pause_button = tk.Button(frame, text="Pausar/Resumir", command=pause_video)
pause_button.pack(side=tk.LEFT)

entry_button = tk.Button(frame, text="Desenhar Entrada", command=set_entry_shape)
entry_button.pack(side=tk.LEFT)

exit_button = tk.Button(frame, text="Desenhar Saída", command=set_exit_shape)
exit_button.pack(side=tk.LEFT)

line_button = tk.Button(frame, text="Modo Linha", command=set_drawing_mode_line)
line_button.pack(side=tk.LEFT)

area_button = tk.Button(frame, text="Modo Área", command=set_drawing_mode_area)
area_button.pack(side=tk.LEFT)

root.update()

# Entrada de vídeo
cap = cv2.VideoCapture("video6.mp4")
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output1.mkv', fourcc, 20.0, (640, 480))

# Reduzir a resolução do vídeo para melhorar a performance
scale_percent = 90  # Reduzir a 90% da resolução original
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * scale_percent / 100)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * scale_percent / 100)
dim = (width, height)

# Variáveis
persons = []  # Adicionando a lista persons
max_p_age = 5  # Definindo a idade máxima
pid = 1  # Inicializando o id
font = cv2.FONT_HERSHEY_SIMPLEX  # Definindo a fonte
smooth_buffer = {}  # Buffer de suavização

# Carregar o modelo YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

cv2.namedWindow('Frame')
cv2.setMouseCallback('Frame', draw_shape)  # Adicionando o callback do mouse

while cap.isOpened():
    root.update()

    if not paused:
        ret, frame = cap.read()
        if not ret:
            print('EOF')
            print('Entrada:', cnt_up)
            print('Saída:', cnt_down)
            break

        # Reduzir a resolução do frame
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

        frame_count += 1
        if frame_count % frame_skip == 0:
            # Detecção com YOLOv5
            results = model(frame)
            detections = results.pred[0].cpu().numpy()

            # Atualizar o buffer de suavização
            for detection in detections:
                x1, y1, x2, y2, conf, cls = detection
                if conf > 0.5 and int(cls) == 0:  # Filtrar apenas pessoas
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    id = f"{cx}-{cy}"

                    if id not in smooth_buffer:
                        smooth_buffer[id] = [(cx, cy)]
                    else:
                        smooth_buffer[id].append((cx, cy))
                        if len(smooth_buffer[id]) > 5:  # Manter um buffer de 5 frames
                            smooth_buffer[id].pop(0)

            for key, positions in smooth_buffer.items():
                avg_x = int(np.mean([pos[0] for pos in positions]))
                avg_y = int(np.mean([pos[1] for pos in positions]))
                new = True

                for i in persons:
                    if abs(avg_x - i.getX()) <= 30 and abs(avg_y - i.getY()) <= 30:
                        new = False
                        prev_cx, prev_cy = i.getX(), i.getY()
                        i.updateCoords(avg_x, avg_y)

                        # Verificar se cruzou as linhas de entrada
                        for line in entry_lines:
                            if line.is_crossed(prev_cx, prev_cy, avg_x, avg_y):
                                if prev_cy < avg_y:  # Cruzando para baixo
                                    if not i.counted_entry and not i.counted_exit:
                                        cnt_up += 1
                                        i.counted_entry = True
                                        i.last_crossed_entry = time.time()
                                        print("ID:", i.getId(), 'crossed entry line at', time.strftime("%c"))
                                        break

                        # Verificar se cruzou as linhas de saída
                        for line in exit_lines:
                            if line.is_crossed(prev_cx, prev_cy, avg_x, avg_y):
                                if prev_cy > avg_y:  # Cruzando para cima
                                    if not i.counted_exit and not i.counted_entry:
                                        cnt_down += 1
                                        i.counted_exit = True
                                        i.last_crossed_exit = time.time()
                                        print("ID:", i.getId(), 'crossed exit line at', time.strftime("%c"))
                                        break

                        # Verificar se está dentro das áreas de entrada
                        for area in entry_areas:
                            if area.contains(avg_x, avg_y) and not i.counted_entry and not i.counted_exit:
                                cnt_up += 1
                                i.counted_entry = True
                                print("ID:", i.getId(), 'entered area at', time.strftime("%c"))
                                break

                        # Verificar se está dentro das áreas de saída
                        for area in exit_areas:
                            if area.contains(avg_x, avg_y) and not i.counted_exit and not i.counted_entry:
                                cnt_down += 1
                                i.counted_exit = True
                                print("ID:", i.getId(), 'exited area at', time.strftime("%c"))
                                break

                        break

                    if i.timedOut():
                        index = persons.index(i)
                        persons.pop(index)
                        del i

                if new == True:
                    p = Person.MyPerson(pid, avg_x, avg_y, max_p_age)
                    persons.append(p)
                    pid += 1

                    # Verificar se está dentro das áreas de entrada
                    for area in entry_areas:
                        if area.contains(avg_x, avg_y) and not p.counted_entry and not p.counted_exit:
                            cnt_up += 1
                            p.counted_entry = True
                            print("ID:", p.getId(), 'entered area at', time.strftime("%c"))
                            break

                    # Verificar se está dentro das áreas de saída
                    for area in exit_areas:
                        if area.contains(avg_x, avg_y) and not p.counted_exit and not p.counted_entry:
                            cnt_down += 1
                            p.counted_exit = True
                            print("ID:", p.getId(), 'exited area at', time.strftime("%c"))
                            break

                cv2.circle(frame, (avg_x, avg_y), 5, (0, 0, 255), -1)
                img = cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        for i in persons:
            cv2.putText(frame, str(i.getId()), (i.getX(), i.getY()), font, 0.3, i.getRGB(), 1, cv2.LINE_AA)

    str_up = 'Entrada: ' + str(cnt_up)
    str_down = 'Saida: ' + str(cnt_down)

    cv2.putText(frame, str_up, (10, 40), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, str_up, (10, 40), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, str_down, (10, 90), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, str_down, (10, 90), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, 'Desenhar linhas e areas de entrada/saida usando botoes', (10, 440), font, 0.5, (255, 0, 255), 1, cv2.LINE_AA)

    # Desenhar linhas de entrada
    for line in entry_lines:
        line.draw(frame)

    # Desenhar linhas de saída
    for line in exit_lines:
        line.draw(frame)

    # Desenhar áreas de entrada
    for area in entry_areas:
        area.draw(frame)

    # Desenhar áreas de saída
    for area in exit_areas:
        area.draw(frame)

    out.write(frame)
    cv2.imshow('Frame', frame)

    k = cv2.waitKey(1) & 0xff  # Reduzir o tempo de espera para 1 ms
    if k == 27:  # Tecla 'ESC' para sair
        break

cap.release()
cv2.destroyAllWindows()
root.destroy()
