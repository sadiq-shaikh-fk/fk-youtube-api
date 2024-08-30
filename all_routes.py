from quart import Quart, jsonify, request
from all_api_functions import get_channel_details_from_id, get_video_id_from_playlist, get_all_video_details

app = Quart(__name__)

# ------------------------- API CALL TEST ROUTE -------------------------
@app.route('/test', methods = ['GET'])
async def test_route():
    return jsonify({'status':'Test route works!'})

# ------------------------- API CALL FOR CHANNEL_ID EXTRACTION -------------------------
@app.route('/channel/<string:channel_id>', methods=['GET'])
async def get_channel_details(channel_id):
    try:
        details = await get_channel_details_from_id(channel_id)
        return jsonify(details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 411

# ------------------------- API CALL FOR PLAYLIST_ITEMS(all video id) EXTRACTION -------------------------
@app.route('/playlistItems/<string:playlist_id>', methods=['GET'])
async def get_playlist_details(playlist_id):
    all_video_ids = []
    pageToken = None  # Initialize pageToken

    while True:
        playlist_item_resp = await get_video_id_from_playlist(playlist_id, pageToken)

        input_playlist_id = playlist_item_resp['input_playlist_id']
        video_ids = playlist_item_resp['video_ids']
        nextPageToken = playlist_item_resp.get('nextPageToken')  # Safely get nextPageToken
        
        if video_ids:
            all_video_ids.extend(video_ids)  # Append all video IDs

        if not nextPageToken:  # Break the loop if there's no nextPageToken
            break
        
        pageToken = nextPageToken  # Update pageToken with the nextPageToken for the next iteration

    try:
        all_video_ids_dict = { 
        'input_playlist_id':input_playlist_id, 
        'video_ids': all_video_ids
        }
        return jsonify(all_video_ids_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 412

@app.route('/videos', methods=['POST'])
async def get_video_details():
    try:
        data = await request.json
        all_video_ids = data.get('video_ids', [])    
    
        details = await get_all_video_details(all_video_ids)
        return jsonify(details), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 413  

# ---------- call the main file ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)