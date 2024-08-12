from googleapiclient.discovery import build, HttpError
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variable and split them into a list
api_keys = os.getenv("API_KEYS").split(',')

api_service_name = "youtube"
api_version = "v3"
current_key_index = 0

async def build_youtube_service(api_key):
    return build(api_service_name, api_version, developerKey=api_key)

youtube = build_youtube_service(api_keys[current_key_index])


async def get_channel_details_from_id(channel_id):
    global current_key_index, youtube

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                youtube = await build_youtube_service(api_keys[current_key_index])
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
                    await asyncio.sleep(1)  # Avoid too rapid retries
                else:
                    return {"error": f"API Error: {str(e)}"}

    channel_details_clean = response.get('items', [{}])[0]

    # Extract madeForKids and set to None if it's not provided
    made_for_kids = channel_details_clean.get("status", {}).get("madeForKids", None)

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
        'channel_made_for_kids': made_for_kids,  # Return None if madeForKids is not present
        'channel_trailer_video_url': channel_details_clean.get("brandingSettings", {}).get("channel", {}).get("unsubscribedTrailer", ""),
        'channel_keywords': channel_details_clean.get("brandingSettings", {}).get("channel", {}).get("keywords", ""),
        'channel_image_banner_url': channel_details_clean.get("brandingSettings", {}).get("image", {}).get("bannerExternalUrl", "")
    }


# def get_channel_details_from_id(channel_id):
#     global current_key_index, youtube
    
#     while True:
#         request = youtube.channels().list(
#             part="brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails",
#             id = channel_id,
#             fields="items(id,snippet(title,description,publishedAt,thumbnails(high),localized,country),statistics(viewCount,subscriberCount,videoCount),status(privacyStatus,madeForKids),brandingSettings(image,channel),contentDetails(relatedPlaylists(uploads)))"
#         )

#         try:
#             response = request.execute() # 1 credit used
#             break

#         except HttpError as e:
        
#             if e.resp.status == 403 and 'exceeded' in e.reason:
#                 print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
#                 #socketio.emit('quota_exceed', {'status': f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key..."}, namespace='/status')
#                 current_key_index = (current_key_index + 1) % len(api_keys)
#                 youtube = build_youtube_service(api_keys[current_key_index])
#                 time.sleep(1)  # Avoid too rapid retries
#             else:
#                 print(f'API URL invalid or other error: {e}')
#                 #socketio.emit('error_msg', {'status': f'API URL invalid or other error: {e}'}, namespace='/status')
#                 return [None] * 16

#     channel_details_str = str(response)
#     channel_details_str1 = channel_details_str.replace("[","")
#     channel_details_str2 = channel_details_str1.replace("]","")
#     channel_details_clean = ast.literal_eval(channel_details_str2)

#     # checking if channel link is invaid or changed it will not generate response hence, need to handing it
#     if len(channel_details_clean) == 0:
#         return [None] * 16
#     else:
#         try:
#             channel_link = str("www.youtube.com/channel/" + channel_details_clean["items"]["id"])
#         except:
#             channel_link = None
#     # ------------------------------------------------------------------------------------------------
#         try:
#             channel_id = channel_details_clean["items"]["id"]
#         except:
#             channel_id = None
#     # ------------------------------------------------------------------------------------------------
#         try:
#             channel_title = channel_details_clean["items"]["snippet"]["title"]
#         except:
#             channel_title = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_desc = channel_details_clean["items"]["snippet"]["description"]
#         except:
#             channel_desc = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_publishedAt = channel_details_clean["items"]["snippet"]["publishedAt"]
#         except:
#             channel_publishedAt = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_thumbnail_high_url = channel_details_clean["items"]["snippet"]["thumbnails"]["high"]["url"]
#         except:
#             channel_thumbnail_high_url = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_country = channel_details_clean["items"]["snippet"]["country"]
#         except:
#             channel_country = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_upload_playlist_id = channel_details_clean["items"]["contentDetails"]["relatedPlaylists"]["uploads"]
#         except:
#             channel_upload_playlist_id = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_view_count = channel_details_clean["items"]["statistics"]["viewCount"]
#         except:
#             channel_view_count = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_subscriber_count = channel_details_clean["items"]["statistics"]["subscriberCount"]
#         except:
#             channel_subscriber_count = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_video_count = channel_details_clean["items"]["statistics"]["videoCount"]
#         except:
#             channel_video_count = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_privacy_status = channel_details_clean["items"]["status"]["privacyStatus"]
#         except:
#             channel_privacy_status = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_made_for_kids = channel_details_clean["items"]["status"]["madeForKids"]
#         except:
#             channel_made_for_kids = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_trailer_video_url = channel_details_clean["items"]["brandingSettings"]["channel"]["unsubscribedTrailer"]
#         except:
#             channel_trailer_video_url = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_keywords = channel_details_clean["items"]["brandingSettings"]["channel"]["keywords"]
#         except:
#             channel_keywords = None
# # ------------------------------------------------------------------------------------------------
#         try:
#             channel_image_banner_url = channel_details_clean["items"]["brandingSettings"]["image"]["bannerExternalUrl"]
#         except:
#             channel_image_banner_url = None

#         return [
#             channel_link, channel_id, channel_title, channel_desc, channel_publishedAt, 
#             channel_country, channel_thumbnail_high_url, channel_made_for_kids, 
#             channel_view_count, channel_subscriber_count, channel_video_count, 
#             channel_privacy_status, channel_image_banner_url, channel_upload_playlist_id, 
#             channel_trailer_video_url, channel_keywords
#         ]