import os
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')
if not API_KEY:
    logging.error("YouTube API key not found in .env file")
    exit(1)

youtube = build('youtube', 'v3', developerKey=API_KEY)

# KoopCast custom URL
CHANNEL_CUSTOM_URL = '@koopcast'

def get_channel_id(custom_url):
    logging.debug(f"Fetching channel ID for custom URL: {custom_url}")
    request = youtube.search().list(
        part='id',
        q=custom_url,
        type='channel'
    )
    response = request.execute()
    if not response['items']:
        logging.error(f"No channel found for custom URL: {custom_url}")
        return None
    channel_id = response['items'][0]['id']['channelId']
    logging.debug(f"Channel ID: {channel_id}")
    return channel_id

def get_playlist_id(channel_id):
    logging.debug(f"Fetching playlist ID for channel: {channel_id}")
    request = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    )
    response = request.execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    logging.debug(f"Playlist ID: {playlist_id}")
    return playlist_id

def get_video_details(playlist_id):
    logging.debug(f"Fetching video details for playlist: {playlist_id}")
    video_details = []
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50
    )
    
    while request:
        response = request.execute()
        for item in response['items']:
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            title = snippet['title']
            published_at = snippet['publishedAt']
            video_details.append({
                'video_id': video_id,
                'title': title,
                'published_at': published_at
            })
        logging.debug(f"Fetched details for {len(video_details)} videos")
        request = youtube.playlistItems().list_next(request, response)
    
    return video_details

def get_transcript(video_id):
    logging.debug(f"Fetching transcript for video: {video_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join([entry['text'] for entry in transcript])
        logging.debug(f"Transcript fetched successfully. Length: {len(text)} characters")
        return text
    except Exception as e:
        logging.error(f"Error getting transcript for video {video_id}: {str(e)}")
        return None

def sanitize_filename(filename):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def save_transcript(video_details, transcript, output_dir, episode_number):
    published_date = datetime.fromisoformat(video_details['published_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
    sanitized_title = sanitize_filename(video_details['title'])
    filename = f"{episode_number:03d}_{published_date}_{sanitized_title}.txt"
    filepath = os.path.join(output_dir, filename)
    logging.debug(f"Saving transcript to {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(transcript)
    logging.debug(f"Transcript saved successfully")

def main():
    output_dir = 'transcripts'
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output directory: {output_dir}")

    channel_id = get_channel_id(CHANNEL_CUSTOM_URL)
    if not channel_id:
        logging.error("Failed to retrieve channel ID. Exiting.")
        return

    playlist_id = get_playlist_id(channel_id)
    video_details = get_video_details(playlist_id)
    logging.info(f"Total videos found: {len(video_details)}")

    # Sort videos by publication date
    video_details.sort(key=lambda x: x['published_at'], reverse=True)

    for i, video in enumerate(video_details, 1):
        logging.info(f"Processing video {i}/{len(video_details)}: {video['video_id']}")
        transcript = get_transcript(video['video_id'])
        if transcript:
            save_transcript(video, transcript, output_dir, len(video_details) - i + 1)
            logging.info(f"Saved transcript for video {video['video_id']}")
        else:
            logging.warning(f"No transcript available for video {video['video_id']}")

    logging.info("Script execution completed")

if __name__ == '__main__':
    main()