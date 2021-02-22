import time
import threading
import json5

import tgAPI
import parser

# Initializing
config_path = "config.json5"
serial_data_path = "serial_data.json5"
config = json5.load(open(config_path, "r"))
serial_data = json5.load(open(serial_data_path, "r"))
tvs = serial_data["tvs"]  # Serialized data about televisions
contacts = serial_data["contacts"]  # Serialized data about contacts for sending
message_check_interval = float(config["messages_check_interval"])  # Interval (seconds) between updating bot messages
refresh_interval = float(config["refresh_interval"])  # Interval (seconds) between updating wildberries TVs
access_token = config["access_token"]
head_admin = config["head_admin"]
contacts.append(head_admin)  # Adding head admin to sending notices


def update_data():
    """
    updating serial_data.json5 (info about available tvs and contacts for sending)
    """
    json5.dump(serial_data, open(serial_data_path, "w"))  # Writing current data in JSON5-file


def tvs_handler():
    """
    tvs (televisions) handler calls in single Thread and finding changing prices of wildberries products (tvs)
    """
    while True:
        new_update = []
        try:
            new_update = parser.get_televisions()  # Getting new data about TVs
        except Exception:
            error_message = "При обновлении товаров произошла ошибка"
            print(error_message)
            tgAPI.send_message(access_token, head_admin, error_message)

        changed_tvs = []
        for tv in new_update:
            url = tv["url"]  # TV's page url
            if url not in tvs:  # Adding new TV
                tvs[url] = {
                    "description": tv["description"],
                    "price": tv["price"]
                }
                continue
            if int(tv["price"]) < int(tvs[url]["price"]):  # Price for this tv decreased
                changed_tvs.append({
                    "prev_price": tvs[url]["price"],
                    "url": url,
                    "tv": tv
                })
                tvs[url]["price"] = tv["price"]  # Update price in serial data

        # Generating text notice about new prices
        message_text = "На некоторые товары упала цена\n\n"
        for tv_r in changed_tvs:
            tv = tv_r["tv"]  # TV's dict
            old_price = tv_r["prev_price"]  # Old price
            url = tv_r["url"]

            message_text += "Товар: %s\n" % url
            message_text += tv["description"] + "\n\n"
            message_text += "Старая цена: %s Р\nНовая цена: %s Р" % (old_price, tv["price"])

        for contact in contacts:  # Sending notice
            tgAPI.send_message(access_token, contact, message_text)

        update_data()  # Updating serial data in file
        time.sleep(refresh_interval)


def bot_handler():
    """
    TODO
    :return:
    """


parser_thread = threading.Thread(target=tvs_handler)  # Launching parser in single thread
parser_thread.start()
