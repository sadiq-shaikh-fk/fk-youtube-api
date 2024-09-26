from quart import Quart, jsonify, request
from all_api_functions import get_channel_details_from_id, get_video_id_from_playlist, get_all_video_details
import asyncio

app = Quart(__name__)

# ------------------------- API CALL TEST ROUTE -------------------------
@app.route('/')
async def index():
    return jsonify({'status': 'Test route works!'})

# ------------------------- API CALL FOR CHANNEL_ID EXTRACTION -------------------------
@app.route('/channel/<string:channel_id>', methods=['GET'])
async def get_channel_details(channel_id):
    try:
        details = await get_channel_details_from_id(channel_id)
        return jsonify(details), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 411

# ------------------------- API CALL FOR PLAYLIST_ITEMS(extract all video id) EXTRACTION -------------------------
@app.route('/playlistItems/<string:playlist_id>', methods=['GET'])
async def get_playlist_details(playlist_id):
    try:
        page_token = request.args.get('pageToken')  # Optional pageToken query parameter
        playlist_data = await get_video_id_from_playlist(playlist_id, pageToken=page_token)
        return jsonify(playlist_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 412

# ------------------------- API CALL FOR VIDEO(details of all video_ids) EXTRACTION -------------------------
@app.route('/videos', methods=['POST'])
async def get_videos_details():
    try:
        data = await request.get_json()
        video_ids = data.get("video_ids", [])

        if not video_ids:
            return jsonify({"error": "No video IDs provided"}), 400

        video_details = await get_all_video_details(video_ids)

        return jsonify(video_details), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 413

# ---------- call the main file ----------
if __name__ == '__main__':
    app.run()