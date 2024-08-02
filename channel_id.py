from googleapiclient.discovery import build, HttpError
import time
import ast

# List of API keys
api_keys = [
    "AIzaSyBIwH-0I1RknoVDzU3Lv9DumnR5X4Kzk5Q",   # 1 Fame Keeda Website
    "AIzaSyDploAX5ItaTrZXv46o7ZwYwFTTNtBRZv0",   # 2 Fame Space
    "AIzaSyAYF4raqM5IqoRl47JFn5q5jXmOQSHzAw4",   # 3 Youtube Scapper 500
    "AIzaSyCKIr0PTua6oshKqW0hHkKr2_8UCO9clRA",   # 4 My Maps Project
    "AIzaSyCZMOL8NXA-6yumpXbBJszRc9wL4RJhMGM",   # 5 FK Metabase
    "AIzaSyDOB1YlqGVRU4r4cRnMeDP5_KsnLIu8H_Y",   # 6 My Project 76789
    "AIzaSyChSeWpt_Fyv57sYtA0EWcwh7GYEle1Ttk",   # 7 YTStats1234
    "AIzaSyC9YY6W5CK2bMFD4Bg05lsSdRkc1c7jYlA",   # 8 inf active status
    "AIzaSyAE1EGgnf7D7z8JvjbmJpl-AOTl8ItRtq8",   # 9 Apollo 
    "AIzaSyBjorP-CAlBNTxGDUkhzOeVtNUPcfN8J3I",   # 10 language teaching assistant
    "AIzaSyCq6qGF0jacKcbDxPokPEQJ31cPzbGHba8",   # 11 Booking App
    "AIzaSyDdRA5R3fzUTDqbAFe7I8xAwDBLCph63Js",   # 12 drive image link
    "AIzaSyD0XlKMiGnlNxC02XmNZvh8SxDiJGU6FuM",   # 13 unknown project1
    "AIzaSyAN4Hvy_6hzR3bCf8WDHpBjsvh66nueXrs",   # 14 unknown project2
    "AIzaSyDeIlfCzB5S7AO_ZslcdPlw-blYNOH0_po"    # 15 unknown project3
]

api_service_name = "youtube"
api_version = "v3"
current_key_index = 0

def build_youtube_service(api_key):
    return build(api_service_name, api_version, developerKey=api_key)

youtube = build_youtube_service(api_keys[current_key_index])


def get_channel_details_from_id(channel_id):
    global current_key_index, youtube

    while True:
        request = youtube.channels().list(
            part="brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails",
            id=channel_id,
            fields="items(id,snippet(title,description,publishedAt,thumbnails(high),localized,country),statistics(viewCount,subscriberCount,videoCount),status(privacyStatus,madeForKids),brandingSettings(image,channel),contentDetails(relatedPlaylists(uploads)))"
        )

        try:
            response = request.execute()
            break

        except HttpError as e:
            if e.resp.status == 403 and 'exceeded' in e.reason:
                print(f"Quota exceeded for key: {api_keys[current_key_index]}. Trying next key...")
                current_key_index = (current_key_index + 1) % len(api_keys)
                youtube = build_youtube_service(api_keys[current_key_index])
                time.sleep(1)  # Avoid too rapid retries
            else:
                print(f'API URL invalid or other error: {e}')
                return {}

    channel_details_str = str(response)
    channel_details_str1 = channel_details_str.replace("[", "")
    channel_details_str2 = channel_details_str1.replace("]", "")
    channel_details_clean = ast.literal_eval(channel_details_str2)

    if len(channel_details_clean) == 0:
        return {}

    channel_data = {
        'channel_link': None,
        'channel_id': None,
        'channel_title': None,
        'channel_desc': None,
        'channel_publishedAt': None,
        'channel_thumbnail_high_url': None,
        'channel_country': None,
        'channel_upload_playlist_id': None,
        'channel_view_count': None,
        'channel_subscriber_count': None,
        'channel_video_count': None,
        'channel_privacy_status': None,
        'channel_image_banner_url': None,
        'channel_trailer_video_url': None,
        'channel_keywords': None
    }

    try:
        channel_data['channel_link'] = f"www.youtube.com/channel/{channel_details_clean['items']['id']}"
    except:
        pass

    try:
        channel_data['channel_id'] = channel_details_clean["items"]["id"]
    except:
        pass

    try:
        channel_data['channel_title'] = channel_details_clean["items"]["snippet"]["title"]
    except:
        pass

    try:
        channel_data['channel_desc'] = channel_details_clean["items"]["snippet"]["description"]
    except:
        pass

    try:
        channel_data['channel_publishedAt'] = channel_details_clean["items"]["snippet"]["publishedAt"]
    except:
        pass

    try:
        channel_data['channel_thumbnail_high_url'] = channel_details_clean["items"]["snippet"]["thumbnails"]["high"]["url"]
    except:
        pass

    try:
        channel_data['channel_country'] = channel_details_clean["items"]["snippet"]["country"]
    except:
        pass

    try:
        channel_data['channel_upload_playlist_id'] = channel_details_clean["items"]["contentDetails"]["relatedPlaylists"]["uploads"]
    except:
        pass

    try:
        channel_data['channel_view_count'] = channel_details_clean["items"]["statistics"]["viewCount"]
    except:
        pass

    try:
        channel_data['channel_subscriber_count'] = channel_details_clean["items"]["statistics"]["subscriberCount"]
    except:
        pass

    try:
        channel_data['channel_video_count'] = channel_details_clean["items"]["statistics"]["videoCount"]
    except:
        pass

    try:
        channel_data['channel_privacy_status'] = channel_details_clean["items"]["status"]["privacyStatus"]
    except:
        pass

    try:
        channel_data['channel_made_for_kids'] = channel_details_clean["items"]["status"]["madeForKids"]
    except:
        pass

    try:
        channel_data['channel_trailer_video_url'] = channel_details_clean["items"]["brandingSettings"]["channel"]["unsubscribedTrailer"]
    except:
        pass

    try:
        channel_data['channel_keywords'] = channel_details_clean["items"]["brandingSettings"]["channel"]["keywords"]
    except:
        pass

    try:
        channel_data['channel_image_banner_url'] = channel_details_clean["items"]["brandingSettings"]["image"]["bannerExternalUrl"]
    except:
        pass

    return channel_data


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