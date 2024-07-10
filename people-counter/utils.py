import yt_dlp as youtube_dl

def get_stream_url(youtube_url):
    ydl_opts = {
        'format': 'best',
        'quiet': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        return info_dict['url']
