import librosa
import numpy as np
import json
import random
import yt_dlp
import os

OUTPUT_JSON = "beatmap.json"
AUDIO_PATH = "song.mp3"
NUM_LANES = 3
AMP_THRESHOLD = 0.05  # check metric - sensitivity of what counts as a beat
MIN_SPACING = 0.3  # min seconds between each tile
DEFAULT_THRESHOLD = 0.05
DEFAULT_SPACING = 0.3


def download_audio_from_youtube(url, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "temp_audio.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for ext in ["mp3", "m4a", "webm"]:
        temp_file = f"temp_audio.{ext}"
        if os.path.exists(temp_file):
            os.rename(temp_file, output_path)
            break


def generate_beatmap_from_youtube(youtube_url):
    # download audio
    download_audio_from_youtube(youtube_url, AUDIO_PATH)

    # load audio file
    y, sr = librosa.load(AUDIO_PATH)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"Loaded {AUDIO_PATH} - Duration: {duration:.2f}s")

    # get beat times and tempo
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    print(f"Detected BPM: {float(tempo):.2f} - Total beats: {len(beat_times)}")

    # measure loudness (rms) over time
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    amp_at_beats = np.interp(beat_times, rms_times, rms)

    # filter beats by amplitude and min spacing
    filtered = []
    last_time = -float('inf')

    for t, amp in zip(beat_times, amp_at_beats):
        if amp > AMP_THRESHOLD and (t - last_time) > MIN_SPACING:
            lane = random.randint(0, NUM_LANES - 1)
            filtered.append({
                "time": round(t, 3),
                "lane": lane
            })
            last_time = t

    print(f"Filtered beats: {len(filtered)}")

    # output dict
    output_data = {
        "metadata": {
            "bpm": float(tempo),
            "duration": duration,
            "num_lanes": NUM_LANES
        },
        "tiles": filtered
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Beatmap saved to {OUTPUT_JSON}")

    return output_data
