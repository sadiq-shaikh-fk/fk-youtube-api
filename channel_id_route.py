from channel_id import get_channel_details_from_id
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/channel/<string:channel_id>', methods = ['GET'])
def get_channel_details(channel_id):
    details = get_channel_details_from_id(channel_id)
    return jsonify(details)

if __name__ == '__main__':
    app.run(debug=True)