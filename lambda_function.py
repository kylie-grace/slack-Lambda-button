import json
import requests
import time

# Read the configuration file
try:
    with open('config.json', 'r') as file:
        CONFIG = json.load(file)
except json.JSONDecodeError as e:
    with open('config.json', 'r') as file:
        print(f"Error decoding JSON: {e}")
        file_content = file.read()
        lines = file_content.split('\n')
        if 0 <= e.docidx < len(lines):
            print(f"Problematic line: {lines[e.docidx]}")
    raise

WEBHOOK_URL = CONFIG["WEBHOOK_URL"]
BUTTON_CONFIG = CONFIG["BUTTON_CONFIG"]

# Dictionary to store the timestamp of the last message sent for each button
LAST_MESSAGE_TIMESTAMP = {}


def post_to_slack(message, webhook_url):
    payload = {'text': message}
    response = requests.post(webhook_url, json=payload)
    return response.text


def lambda_handler(event, context):
    print(event)
    device_info = event.get('deviceInfo', {})
    device_id = device_info.get('deviceId', '').strip()
    click_type = event['deviceEvent']['buttonClicked']['clickType']
    remaining_life = device_info.get('remainingLife', '')
    reported_time = event['deviceEvent']['buttonClicked']['reportedTime']

    print(f"Extracted deviceId: {device_id}, clickType: {click_type}")

    if not device_id:
        print('No deviceId provided.')
        return {'statusCode': 400, 'body': 'No deviceId provided.'}

    last_timestamp = LAST_MESSAGE_TIMESTAMP.get(device_id, 0)
    current_timestamp = time.time()
    if current_timestamp - last_timestamp < 60:
        print('Rate limit applied. Message not sent.')
        return {'statusCode': 429, 'body': 'Rate limit applied.'}

    button_details = BUTTON_CONFIG.get(device_id, {})
    message = button_details.get(click_type, f"Unknown button pressed.")
    location = button_details.get("LOCATION", "Default Location")

    if click_type == "LONG":
        message = f"Testing button {location} {device_id} battery life is {remaining_life} at {reported_time}"

    webhook_url = button_details.get("WEBHOOK_URL") or WEBHOOK_URL

    print(f"Retrieved message: {message}")
    print(f"Using Webhook: {webhook_url}")

    slack_response = post_to_slack(message, webhook_url)
    print(f"Received response from Slack: {slack_response}")

    LAST_MESSAGE_TIMESTAMP[device_id] = current_timestamp

    return {'statusCode': 200, 'body': slack_response}
