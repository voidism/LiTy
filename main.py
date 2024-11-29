import os
import argparse
from dictate import Dictation
import yt_dlp


def download_youtube_video(url, output_path, video_title):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/{video_title}',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'writeautomaticsub': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download(url, save_data_dir):
    global sentences, progress, current_sentence, current_video_id
    video_title = url.split('=')[-1]  # Fallback to video ID

    current_video_id = video_title

    audio_path = os.path.join(save_data_dir, f"{video_title}.mp3")
    subtitle_path = os.path.join(save_data_dir, f"{video_title}.en.vtt")

    # if the segmented audio files already exist, skip downloading
    if os.path.exists(audio_path) and os.path.exists(subtitle_path):
        print(f"Audio file {audio_path} already exists, skipping download")
        return audio_path, subtitle_path
    # if the audio is not downloaded, download it

    if not os.path.exists(audio_path):
        try:
            download_youtube_video(url, save_data_dir, video_title)
        except Exception as e:
            raise Exception("Error downloading video", e)

    if not os.path.exists(audio_path):
        raise Exception("Error downloading video")

    if not os.path.exists(subtitle_path):
        raise Exception("Error downloading subtitles")

    return audio_path, subtitle_path



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("link", type=str, help="the link of the YouTube video with subtitles.")
    parser.add_argument("--log_dir", type=str, default='logs', required=False, help="the folder to save the log file.")
    parser.add_argument("--data_dir", type=str, default='data', required=False, help="the folder to save the downloaded data.")
    parser.add_argument("--pause_time", type=float, default=2.5, required=False, help="the pause time in seconds between each audio replay.")
    parser.add_argument("--char_per_sent", type=int, default=100, required=False, help="number of maximum characters should be included in a sentence.")
    parser.add_argument("--openai_key", type=str, default=None, required=False, help="the OpenAI API key. (optional. if not provided, the explanation function will be disabled.)")
    parser.add_argument("--lang", type=str, default='en', required=False, help="the language of the GPT-4o explanation. supported languages are English (`en`), Chinese (`zh`), Spanish (`es`) and French (`fr`).")
    args = parser.parse_args()
    # start downloading and segmenting the video
    audio_path, subtitle_path = download(args.link, args.data_dir)
    print(open('logo').read())
    dic = Dictation(audio_path, subtitle_path, args.log_dir, args.pause_time, args.char_per_sent, args.openai_key, args.lang)
    dic.run()
