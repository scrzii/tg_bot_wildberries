import time
import json5
from urllib.request import urlopen
from urllib.parse import urlencode

API_URL = "https://api.telegram.org/bot"


def request_api(method: str, access_token: str, **data) -> dict:
    """
    returns request for method "method"
    :param method: method name ("getUpdates" for example)
    :param access_token: access_token of your bot
    :param data: method data ("chat_id", "user_id", etc)
    :return: JSON5-object
    """
    url = f"{API_URL}{access_token}/{method}?" + urlencode(data)
    req_response = urlopen(url).read()  # Loading method
    return json5.loads(req_response)  # Converting to JSON5 format


def get_updates(access_token: str, offset: int=0) -> dict:
    """
    returns updates (messages/callbacks)
    :param access_token: access token of your bot
    :param offset: messages offset
    :return: JSON5-object with result
    """
    return request_api(
        "getUpdates",
        access_token,
        offset=offset
    )


def send_message(access_token: str, chat_id: str, text: str) -> dict:
    """
    sends message with your text to char chat_id and returns sending result (JSON)
    :param access_token: access token of your bot
    :param chat_id: chat id for sending
    :param text: message text
    :return: JSON-object (result of sending)
    """
    return request_api(
        "sendMessage",
        access_token,
        text=text,
        chat_id=chat_id
    )


def normalize(messages: list) -> list:
    """
    this function normalizes message list to format:
    [{
        "user_id": user id,
        "message_id": message id
        "text": message text (non-text messages will be ignored)
    }, ...]
    :param messages: your message list
    :return: normalized message list
    """
    result_list = []
    for message in messages:
        if "message" not in message or "text" not in message["message"]:  # If message is
            # not correct text message it will be ignored
            continue
        result_list.append({
            "user_id": message["message"]["from"]["id"],
            "message_id": message["update_id"],
            "text": message["message"]["text"]
        })
    return result_list


# Demonstration of working the module
if __name__ == "__main__":
    config_path = "config.json5"
    config = json5.load(open(config_path, "r"))
    token = config["access_token"]  # Access token
    interval = float(config["messages_check_interval"])  # Checking interval from config

    while True:
        response = get_updates(token)  # Getting messages/callbacks from chats
        updates = response["result"] if response["ok"] else []  # updates is messages only
        if len(updates) == 0:
            continue

        t_offset = updates[-1]["update_id"]  # Last message offset
        get_updates(token, int(t_offset) + 1)  # Marking as read all messages
        t_message = updates[0]  # Tracking 1st message only

        if "message" in t_message and "text" in t_message["message"]:
            user_id = t_message["message"]["from"]["id"]
            t_text = t_message["message"]["text"]
            result = send_message(token, user_id, "Ваше сообщение: " + t_text)
            if result["ok"]:
                print("SENDING SUCCESS")
            else:
                print(f"PROBLEM:\n{result}")
            break

        time.sleep(interval)  # Waiting next update
