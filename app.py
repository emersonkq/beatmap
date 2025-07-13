from flask import Flask, request, jsonify, send_file, send_from_directory
from beatmap_generator import generate_beatmap_from_youtube
import os

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    # serve the frontend page
    return app.send_static_file('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    youtube_url = data.get('youtube_url')

    if not youtube_url:
        return jsonify({'error': 'No YouTube URL provided'}), 400

    try:
        beatmap_data = generate_beatmap_from_youtube(youtube_url)
    except Exception as e:
        # Check for common YouTube download errors
        error_msg = str(e)
        if "Video unavailable" in error_msg or "This content isn’t available" in error_msg:
            return jsonify({'error': 'The YouTube video is unavailable or restricted.'}), 400
        return jsonify({'error': error_msg}), 500

    return jsonify(beatmap_data)

@app.route('/audio')
def audio():
    # serve the downloaded song.mp3
    audio_path = 'song.mp3'
    if not os.path.exists(audio_path):
        return jsonify({'error': 'Audio file not found'}), 404
    return send_file(audio_path, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

