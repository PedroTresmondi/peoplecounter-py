import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import cv2

def save_heatmap(heatmap_data, last_frame, frame_width, frame_height):
    if len(heatmap_data) == 0:
        print("Nenhum dado para gerar o mapa de calor")
        return

    heatmap_array = np.zeros((frame_height, frame_width))

    radius = 15

    for coord in heatmap_data:
        x, y = coord[0], coord[1]
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if 0 <= y + i < frame_height and 0 <= x + j < frame_width and i ** 2 + j ** 2 <= radius ** 2:
                    heatmap_array[y + i, x + j] += 1

    plt.figure(figsize=(frame_width / 100, frame_height / 100))
    sns.heatmap(heatmap_array, cmap='RdYlGn_r', cbar=True, alpha=0.5, zorder=2)
    plt.imshow(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB), aspect='auto', zorder=1)
    plt.axis('off')
    plt.savefig('heatmap.png', bbox_inches='tight', pad_inches=0)
    plt.close()
