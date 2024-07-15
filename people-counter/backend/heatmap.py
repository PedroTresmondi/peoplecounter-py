import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import cv2
import time
from supabase import create_client, Client
import config

# Supabase
url = config.SUPABASE_URL
key = config.SUPABASE_KEY
supabase: Client = create_client(url, key)

if not os.path.exists('heatmaps'):
    os.makedirs('heatmaps')

def upload_to_supabase(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = file.read()
        # Adicionando timestamp ao nome do arquivo
        timestamp = int(time.time())
        file_name = f'heatmaps/heatmap_{timestamp}.png'
        response = supabase.storage.from_('heatmap').upload(file_name, data)
        print(f"Upload successful: {response}")
        return response
    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        if hasattr(e, 'response'):
            print(f"Supabase error response: {e.response.text}")
        return None

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
    # Adicionando timestamp ao salvar o arquivo
    timestamp = int(time.time())
    file_path = f'heatmaps/heatmap_{timestamp}.png'
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    upload_to_supabase(file_path)
