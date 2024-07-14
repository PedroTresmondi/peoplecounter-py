import numpy as np
import cv2
import time
import tkinter as tk
import torch
import yolov5
import Person
import utils
import globals
from counting import CountingLine, YellowLine
import heatmap
import gui

# Inicializar o modelo YOLOv5
device = 'cuda' if torch.cuda.is_available() else 'cpu'
yolo = yolov5.load('yolov5n.pt', device=torch.cuda.current_device())

# Classes de interesse (pessoas)
classes_of_interest = [0]

# Função de callback do mouse
def draw_shape(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        globals.drawing = True
        globals.ix, globals.iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if globals.drawing:
            globals.fx, globals.fy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        globals.drawing = False
        globals.fx, globals.fy = x, y
        if globals.drawing_mode == 'line':
            line_type = 'entry' if globals.drawing_entry else 'exit'
            globals.entry_lines.append(CountingLine((globals.ix, globals.iy), (globals.fx, globals.fy), line_type))
        elif globals.drawing_mode == 'yellow_line':
            globals.yellow_lines.append(YellowLine((globals.ix, globals.iy), (globals.fx, globals.fy)))

# Função para processar os frames
def process_frame(frame):
    globals.cnt_inside_yellow = 0

    try:
        results = yolo(frame)
        boxes = results.xyxy[0].cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2, conf, cls = box
            if cls in classes_of_interest and (x2 - x1) * (y2 - y1) > globals.areaTH:
                x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                cx = int(x + w / 2)
                cy = int(y + h / 2)

                new = True
                for i in globals.persons:
                    if abs(cx - i.getX()) <= w and abs(cy - i.getY()) <= h:
                        new = False
                        prev_cx, prev_cy = i.getX(), i.getY()
                        i.updateCoords(cx, cy)

                        # Verificar cruzamento de linhas
                        for line in globals.entry_lines:
                            if line.line_type == 'entry' and not i.counted_entry and line.is_crossed(prev_cx, prev_cy, cx, cy):
                                globals.cnt_up += 1
                                i.counted_entry = True
                            elif line.line_type == 'exit' and not i.counted_exit and line.is_crossed(prev_cx, prev_cy, cx, cy):
                                globals.cnt_down += 1
                                i.counted_exit = True

                        # Verificar se a pessoa está na área amarela
                        for yellow_line in globals.yellow_lines:
                            if yellow_line.contains(cx, cy):
                                globals.cnt_inside_yellow += 1
                                globals.total_unique_ids.add(i.getId())

                        # Atualizar os dados para o heatmap
                        globals.heatmap_data.append([cx, cy])
                        break

                    if i.timedOut():
                        index = globals.persons.index(i)
                        globals.persons.pop(index)
                        del i

                if new:
                    p = Person.MyPerson(globals.pid, cx, cy, globals.max_p_age)
                    globals.persons.append(p)
                    globals.pid += 1

                    globals.heatmap_data.append([cx, cy])

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        for i in globals.persons:
            cv2.putText(frame, str(i.getId()), (i.getX(), i.getY()), globals.font, 0.3, i.getRGB(), 1, cv2.LINE_AA)

    except Exception as e:
        print(f'Error: {e}')

    return frame

# Função principal de loop de vídeo
def video_loop():
    while globals.cap.isOpened():
        if not globals.paused:
            ret, frame = globals.cap.read()
            if not ret:
                print('EOF')
                print('Entrada:', globals.cnt_up)
                print('Saída:', globals.cnt_down)
                print('Dentro da área amarela:', globals.cnt_inside_yellow)
                print('Total de IDs únicos na área amarela:', len(globals.total_unique_ids))
                break

            frame = cv2.resize(frame, (globals.frame_width, globals.frame_height))
            frame = process_frame(frame)

            str_up = 'Entrada: ' + str(globals.cnt_up)
            str_down = 'Saida: ' + str(globals.cnt_down)
            str_inside_yellow = 'Dentro da área amarela: ' + str(globals.cnt_inside_yellow)
            str_total_unique_ids = 'Total de IDs únicos: ' + str(len(globals.total_unique_ids))

            cv2.putText(frame, str_up, (10, 40), globals.font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str_up, (10, 40), globals.font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, str_down, (10, 90), globals.font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str_down, (10, 90), globals.font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str_inside_yellow, (10, 140), globals.font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str_inside_yellow, (10, 140), globals.font, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, str_total_unique_ids, (10, 190), globals.font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str_total_unique_ids, (10, 190), globals.font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, 'Desenhar linhas e áreas de entrada/saída usando botões', (10, 440), globals.font, 0.5,
                        (255, 0, 255), 1, cv2.LINE_AA)

            for line in globals.entry_lines:
                line.draw(frame)

            for line in globals.yellow_lines:
                line.draw(frame)

            globals.out.write(frame)
            cv2.imshow('Contador de Pessoas', frame)

            globals.last_frame = frame.copy()  # Atualizar last_frame aqui

            k = cv2.waitKey(1) & 0xff
            if k == 27:
                break

        globals.root.update_idletasks()
        globals.root.update()

    heatmap.save_heatmap(globals.heatmap_data, globals.last_frame, globals.frame_width, globals.frame_height)
    globals.cap.release()
    cv2.destroyAllWindows()
    globals.root.destroy()

# Configuração inicial
globals.root = tk.Tk()
globals.root.title("Contador de Pessoas")

frame = tk.Frame(globals.root)
frame.pack()

pause_button = tk.Button(frame, text="Pausar/Resumir", command=gui.pause_video)
pause_button.pack(side=tk.LEFT)

entry_button = tk.Button(frame, text="Desenhar Linha de Entrada", command=gui.set_entry_shape)
entry_button.pack(side=tk.LEFT)

exit_button = tk.Button(frame, text="Desenhar Linha de Saída", command=gui.set_exit_shape)
exit_button.pack(side=tk.LEFT)

line_button = tk.Button(frame, text="Modo Linha", command=gui.set_drawing_mode_line)
line_button.pack(side=tk.LEFT)

yellow_line_button = tk.Button(frame, text="Modo Linha Amarela", command=gui.set_drawing_mode_yellow_line)
yellow_line_button.pack(side=tk.LEFT)

globals.root.update()

# URL da live do YouTube
youtube_url = "https://www.youtube.com/watch?v=DjdUEyjx8GM"
stream_url = utils.get_stream_url(youtube_url)

globals.cap = cv2.VideoCapture(stream_url)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
globals.out = cv2.VideoWriter('output1.mkv', fourcc, 20.0, (640, 480))

globals.frame_width = int(globals.cap.get(cv2.CAP_PROP_FRAME_WIDTH) // 2)
globals.frame_height = int(globals.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) // 2)
globals.areaTH = globals.frame_width * globals.frame_height / 1500
print('Area Threshold', globals.areaTH)

globals.fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

cv2.namedWindow('Contador de Pessoas')
cv2.setMouseCallback('Contador de Pessoas', draw_shape)

video_loop()
