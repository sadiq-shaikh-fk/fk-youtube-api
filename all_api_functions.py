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

# ------------------------- LOGIC FOR PLAYLIST_ID EXTRACTION -------------------------
async def get_video_id_from_playlist(playlist_id, pageToken=None):
    global current_key_index, request_count

    async with aiohttp.ClientSession() as session:
        while True:
                # Proactive key rotation
                if request_count >= max_requests_per_key:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0

                youtube = await build_youtube_service(api_keys[current_key_index])
                request_count += 1

                request = youtube.playlistItems().list(
                    part="id,snippet,status,contentDetails",
                    playlistId = playlist_id,
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
        'input_playlist_id': playlist_id,
        'video_ids': video_ids,
        'nextPageToken': nextPageToken
    }

# ------------------------- LOGIC FOR VIDEOS EXTRACTION -------------------------
async def get_all_video_details(video_id_strings):
    global current_key_index, request_count
    response_of_all_video_ids = []
    response_of_all_video_ids_final = []

    # making chunks of 50 string from srting all video_id
    video_id_strings_chunked = await video_id_list_to_string(video_id_strings)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Proactive key rotation
                if request_count >= max_requests_per_key:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    request_count = 0

                youtube = await build_youtube_service(api_keys[current_key_index])
                request_count += 1

                for each_chunk in video_id_strings_chunked:
                    request = youtube.videos().list(
                    part="contentDetails,id,player,snippet,statistics,status,topicDetails",
                    id = str(each_chunk)
                    #fields = "items(id,snippet(title,description,publishedAt,thumbnails(high),localized,country),statistics(viewCount,subscriberCount,videoCount),status(privacyStatus,madeForKids),brandingSettings(image,channel),contentDetails(relatedPlaylists(uploads)))"
                    )
                    try:
                        # request execution
                        response = request.execute() # 1 credit used
                        items = response.get('items', [{}])
                        response_of_all_video_ids.append(items)
                        
                        for each_response in response_of_all_video_ids:
                            for item in each_response:
                                try:
                                    response_of_all_video_ids_final.append(item)
                                except Exception as e:
                                    print(f'except occured{e}')
                        break

                    except HttpError as e:
                        if e.resp.status == 403 and 'exceeded' in e.reason:
                            print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                            current_key_index = (current_key_index + 1) % len(api_keys)
                            #await asyncio.sleep(1)  # Avoid too rapid retries
                            
                            print(f"error - API Error: {str(e)}")
                        elif e.resp.status == 400 and 'No filter' in e.reason:
                            print('no filter was selected.. (channel did not gave uploadPlaylistId)')
                            print()
                            #return [None] * 5

                        else:
                            print('API URL invalid or other error:', e)
                            print('------------------------------------------------------------------------------------------------')
                            #return [None] * 5
                    except Exception as e:
                        print('Some error - ', e)
            
            except Exception as e:
                print('Some error at query Building', e)

            return {
                    "items" : response_of_all_video_ids_final
                    }
        
# ----------- LOGIC LIST TO STRING -----------
async def video_id_list_to_string(video_ids_lst):
    video_id_strings = []
    total_video_ids = len(video_ids_lst)          # storing the total videos count to create chunks

    for i in range(0, total_video_ids, 50):
        chunk = video_ids_lst[i:i+50]             # Get the current chunk of 50 (or fewer if at the end)
        video_id_str = ','.join(chunk)            # Convert the chunk to a comma-separated string without spaces        
        video_id_strings.append(video_id_str)     # Append the string to the new list
    return video_id_strings


# ---------------------------------------- OLD CODE ---------------------------------------- 
# async def get_video_details(video_id, pageToken=None):
#     global current_key_index, youtube

#     async with aiohttp.ClientSession() as session:
#         while True:
#             youtube = await build_youtube_service(api_keys[current_key_index])
#             request = youtube.videos().list(
#             part="id,snippet,status,contentDetails",
#             id = video_id
#             )
#             # request.uri = fix_url(str(request.uri))     # Build the URL from the request
#             try:
#                 # request execution
#                 response = request.execute() # 1 credit used
#                 break

#             except HttpError as e:
#                 if e.resp.status == 403 and 'exceeded' in e.reason:
#                     print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
#                     current_key_index = (current_key_index + 1) % len(api_keys)
#                     await asyncio.sleep(1)  # Avoid too rapid retries
#                 else:
#                     return {"error": f"API Error: {str(e)}"}
    
#     video_details_clean = response.get('items', [{}])

#     return{
#         'vide_title' : video_details_clean.get("snippet", {}).get("title", ""),
#         'input_video_id' : video_id
#     }