from quart import Quart, jsonify
from channel_id import get_channel_details_from_id

app = Quart(__name__)

@app.route('/channel/<string:channel_id>', methods=['GET'])
async def get_channel_details(channel_id):
    try:
        details = await get_channel_details_from_id(channel_id)
        return jsonify(details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)