from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import (JSONFormatter, PrettyPrintFormatter, 
                                               TextFormatter, WebVTTFormatter, SRTFormatter)
import requests

app = Flask(__name__)

def get_video_id(youtube_url):
    parsed_url = urlparse(youtube_url)
    
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path[1:]
    elif 'youtube.com' in parsed_url.netloc:
        if 'shorts' in parsed_url.path:
            return parsed_url.path.split('/')[-1]
        else:
            return parse_qs(parsed_url.query)['v'][0]
    return None

def get_video_title(video_id):
    try:
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        return response.json()['title']
    except:
        return video_id

def sanitize_filename(title):
    invalid_chars = '<>:"/\\|?*'
    filename = ''.join(char for char in title if char not in invalid_chars)
    return filename[:50]

def get_transcript(url, formatter_name):
    try:
        video_id = get_video_id(url)
        if not video_id:
            return "Could not extract video ID from URL", 400

        video_title = get_video_title(video_id)
        safe_title = sanitize_filename(video_title)

        # Get transcript without specifying language
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        formatters = {
            'JSON': (JSONFormatter(), 'json'),
            'Pretty Print': (PrettyPrintFormatter(), 'txt'),
            'Text': (TextFormatter(), 'txt'),
            'WebVTT': (WebVTTFormatter(), 'vtt'),
            'SRT': (SRTFormatter(), 'srt')
        }

        formatter, ext = formatters.get(formatter_name, (TextFormatter(), 'txt'))  # Default to Text if not found
        formatted_transcript = formatter.format_transcript(transcript)

        return formatted_transcript

    except Exception as e:
        return f"Error occurred: {str(e)}", 500

@app.route('/get_transcript', methods=['GET','POST'])
def get_transcript_route():
    url_data = request.get_json()
    youtube_url = url_data.get("url")
    output_format = request.args.get('format', 'Text')  # Default format is Text

    if not youtube_url:
        return "YouTube URL is required", 400

    transcript = get_transcript(youtube_url, output_format)
    
    if isinstance(transcript, tuple):  # If the response is an error tuple
        return transcript

    return transcript, 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)
