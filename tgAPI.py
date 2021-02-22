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
    response = urlopen(f"{API_URL}{access_token}/{method}?" + urlencode(data)).read()  # Loading method
    return json5.loads(response)  # Converting to JSON5 format


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


# Demonstration of working the module
if __name__ == "__main__":
    config_path = "config.json5"
    config = json5.load(open(config_path, "r"))
    token = config["access_token"]
    interval = float(config["messages_check_interval"])
    while True:
        response = get_updates(token)
        updates = response["result"] if response["ok"] else []
        if len(updates) == 0:
            continue
        t_offset = updates[-1]["update_id"]
        get_updates(token, int(t_offset) + 1)  # Marking as read all messages
        message = updates[0]
        if "message" in message and "text" in message["message"]:
            user_id = message["message"]["from"]["id"]
            t_text = message["message"]["text"]
            result = send_message(token, user_id, "Ваше сообщение: " + t_text)
            if result["ok"]:
                print("SENDING SUCCESS")
            else:
                print(f"PROBLEM:\n{result}")
            break
        time.sleep(interval)
