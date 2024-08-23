from googleapiclient.discovery import build, HttpError
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from fix_url import fix_url

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variable and split them into a list
api_keys = os.getenv("API_KEYS").split(',')

api_service_name = "youtube"
api_version = "v3"
current_key_index = 0
max_requests_per_key = 1000  # Set a threshold for when to switch keys
request_count = 0

async def build_youtube_service(api_key):
    return build(api_service_name, api_version, developerKey=api_key)

async def get_channel_details_from_id(channel_id):
    global current_key_index, request_count

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Proactive key rotation
                if request_count >= max_requests_per_key:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0

                youtube = await build_youtube_service(api_keys[current_key_index])
                request_count += 1

                request = youtube.channels().list(
                    part="brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails",
                    id=channel_id,
                    fields="items(id,snippet(title,description,publishedAt,thumbnails(high),localized,country),statistics(viewCount,subscriberCount,videoCount),status(privacyStatus,madeForKids),brandingSettings(image,channel),contentDetails(relatedPlaylists(uploads)))"
                )

                response = request.execute()
                break

            except HttpError as e:
                if e.resp.status == 403 and 'exceeded' in e.reason:
                    print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0
                    await asyncio.sleep(1)  # Avoid too rapid retries
                else:
                    return {"error": f"API Error: {str(e)}"}

    channel_details_clean = response.get('items', [{}])[0]

    return {
        'channel_link': f"www.youtube.com/channel/{channel_details_clean.get('id', '')}",
        'yt_channel_id': channel_details_clean.get("id", ""),
        'channel_title': channel_details_clean.get("snippet", {}).get("title", ""),
        'channel_desc': channel_details_clean.get("snippet", {}).get("description", ""),
        'channel_custom_url': channel_details_clean.get("snippet", {}).get('customUrl', ""),
        'channel_publishedAt': channel_details_clean.get("snippet", {}).get("publishedAt", ""),
        'channel_thumbnail_high_url': channel_details_clean.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", ""),
        'channel_country': channel_details_clean.get("snippet", {}).get("country", ""),
        'channel_upload_playlist_id': channel_details_clean.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", ""),
        'channel_view_count': channel_details_clean.get("statistics", {}).get("viewCount", ""),
        'channel_subscriber_count': channel_details_clean.get("statistics", {}).get("subscriberCount", ""),
        'channel_video_count': channel_details_clean.get("statistics", {}).get("videoCount", ""),
        'channel_privacy_status': channel_details_clean.get("status", {}).get("privacyStatus", ""),
        'channel_made_for_kids': channel_details_clean.get("status", {}).get("madeForKids", None),
        'channel_trailer_video_url': channel_details_clean.get("brandingSettings", {}).get("channel", {}).get("unsubscribedTrailer", ""),
        'channel_keywords': channel_details_clean.get("brandingSettings", {}).get("channel", {}).get("keywords", ""),
        'channel_image_banner_url': channel_details_clean.get("brandingSettings", {}).get("image", {}).get("bannerExternalUrl", ""),
        'input_channel_id' : channel_id
    }

async def get_video_id_from_playlist(upload_playlist_id, pageToken=None):
    global current_key_index, youtube

    async with aiohttp.ClientSession() as session:
        while True:
            youtube = await build_youtube_service(api_keys[current_key_index])
            request = youtube.playlistItems().list(
            part="id,snippet,status,contentDetails",
            playlistId = upload_playlist_id,
            maxResults = 50,
            pageToken=pageToken
            )
            request.uri = fix_url(str(request.uri))     # Build the URL from the request
            try:
                # request execution
                response = request.execute() # 1 credit used
                break

            except HttpError as e:
                if e.resp.status == 403 and 'exceeded' in e.reason:
                    print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    await asyncio.sleep(1)  # Avoid too rapid retries
                else:
                    return {"error": f"API Error: {str(e)}"}
    
    playlist_item_details_clean = response.get('items', [{}])
    video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_item_details_clean]

    nextPageToken = response.get('nextPageToken')  # Get nextPageToken if it exists, otherwise None
    return {
        'input_playlist_id': upload_playlist_id,
        'video_ids': video_ids,
        'nextPageToken': nextPageToken
    }
