from googleapiclient.discovery import build, HttpError
import asyncio
import aiohttp
import os
import logging
from dotenv import load_dotenv
from fix_url import fix_url

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys from environment variable and split them into a list
api_keys = os.getenv("API_KEYS").split(',')

api_service_name = "youtube"
api_version = "v3"
current_key_index = 0
max_requests_per_key = 1000  # Set a threshold for when to switch keys
request_count = 0

# ------------------------- LOGIC FOR RE-BUILDING FOR NEW API KEY -------------------------
async def build_youtube_service(api_key):
    return build(api_service_name, api_version, developerKey=api_key)

# ------------------------- LOGIC FOR CHANNEL EXTRACTION -------------------------
async def get_channel_details_from_id(channel_id):
    global current_key_index, request_count

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Proactive key rotation
                if request_count >= max_requests_per_key:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0
                    logger.info(f"Switched to new API key: {api_keys[current_key_index]}")

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
                    logger.warning(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0
                    await asyncio.sleep(1)  # Avoid too rapid retries
                else:
                    logger.error(f"API Error: {str(e)}")
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

# ------------------------- LOGIC FOR PLAYLIST_ID EXTRACTION -------------------------
async def get_video_id_from_playlist(upload_playlist_id, pageToken=None):
    global current_key_index, request_count
    video_ids = []
    nextPageToken = pageToken

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if request_count >= max_requests_per_key:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0
                    logger.info(f"Switched to new API key: {api_keys[current_key_index]}")

                youtube = await build_youtube_service(api_keys[current_key_index])
                request_count += 1

                request = youtube.playlistItems().list(
                    part="id,snippet,status,contentDetails",
                    playlistId=upload_playlist_id,
                    maxResults=50,
                    pageToken=nextPageToken
                )
                request.uri = fix_url(str(request.uri))

                response = request.execute()
                items = response.get('items', [])

                video_ids.extend([item['snippet']['resourceId']['videoId'] for item in items])

                nextPageToken = response.get('nextPageToken')
                if not nextPageToken:
                    break

            except HttpError as e:
                if e.resp.status == 403 and 'exceeded' in e.reason:
                    logger.warning(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                    current_key_index = (current_key_index + 1) % len(api_keys)
                else:
                    logger.error(f"API Error: {str(e)}")
                    break

    return {
        'input_playlist_id': upload_playlist_id,
        'video_ids': video_ids,
        'nextPageToken': nextPageToken
    }

# ------------------------- LOGIC FOR VIDEOS EXTRACTION -------------------------
async def get_all_video_details(video_id_strings):
    global current_key_index, request_count
    response_of_all_video_ids = []

    video_id_strings_chunked = await video_id_list_to_string(video_id_strings)

    async with aiohttp.ClientSession() as session:
        for each_chunk in video_id_strings_chunked:
            while True:
                try:
                    if request_count >= max_requests_per_key:
                        current_key_index = (current_key_index + 1) % len(api_keys)
                        request_count = 0
                        logger.info(f"Switched to new API key: {api_keys[current_key_index]}")

                    youtube = await build_youtube_service(api_keys[current_key_index])
                    request_count += 1

                    request = youtube.videos().list(
                        part="contentDetails,id,player,snippet,statistics,status,topicDetails",
                        id=str(each_chunk)
                    )

                    response = request.execute()
                    items = response.get('items', [])
                    response_of_all_video_ids.extend(items)
                    break

                except HttpError as e:
                    if e.resp.status == 403 and 'exceeded' in e.reason:
                        logger.warning(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                        current_key_index = (current_key_index + 1) % len(api_keys)
                    elif e.resp.status == 400 and 'No filter' in e.reason:
                        logger.warning('No filter was selected.. (channel did not give uploadPlaylistId)')
                        logger.info('Skipping this chunk.')
                        break
                    else:
                        logger.error(f"API Error: {str(e)}")
                        break
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    break

    return {"items": response_of_all_video_ids}
        
# ----------- LOGIC LIST TO STRING -----------
async def video_id_list_to_string(video_ids):
    video_id_list = []
    temp_string = ""
    counter = 0

    for video_id in video_ids:
        temp_string += video_id + ","
        counter += 1

        if counter == 50:
            video_id_list.append(temp_string.rstrip(","))
            temp_string = ""
            counter = 0

    if temp_string:
        video_id_list.append(temp_string.rstrip(","))

    return video_id_list
