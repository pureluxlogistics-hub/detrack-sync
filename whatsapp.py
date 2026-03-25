from flask import Flask, request
import requests
import json

app = Flask(__name__)

WHATSAPP_TOKEN = 'your_whatsapp_token_here'
VERIFY_TOKEN = 'purelux123'

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print('Received:', json.dumps(data, indent=2))
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
