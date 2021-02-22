import time
import threading
import json5

import tgAPI
import wildberriesParser

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
if head_admin not in contacts:
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
            new_update = wildberriesParser.get_televisions()  # Getting new data about TVs
        except:
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

        if changed_tvs:
            # Generating text notice about new prices
            message_text = "На некоторые товары упала цена\n\n"
            for tv_r in changed_tvs:
                tv = tv_r["tv"]  # TV's dict
                old_price = tv_r["prev_price"]  # Old price
                url = tv_r["url"]

                message_text += "Товар: %s\n" % url
                message_text += tv["description"] + "\n"
                message_text += "Старая цена: %s Р\nНовая цена: %s Р\n\n" % (old_price, tv["price"])

            for contact in contacts:  # Sending notice
                try:
                    tgAPI.send_message(access_token, contact, message_text)
                except:
                    print(f"Ошибка при отправке сообщения: user_id: {contact}")

        update_data()  # Updating serial data in file
        time.sleep(refresh_interval)


def fast_send(user_id: str, text: str):
    """
    this function replies text to user's message
    :param user_id: message dict
    :param text: sending text
    """
    tgAPI.send_message(access_token, user_id, text)


def one_message_handler(message: dict):
    """
    this is result of refactoring, this function handles single message of user
    :param message: message dict
    """
    user_id = message["user_id"]
    text = message["text"]
    if text == "id":  # User wants to get self id
        fast_send(user_id, user_id)
    elif text == "contacts":  # User wants to see contact list
        fast_send(user_id, f"Контакты: {', '.join(contacts)}")
    else:  # Command handler
        splitted = text.split()  # Splitting user's string
        if len(splitted) != 2:
            fast_send(user_id, "Неправильное количество аргументов команды")
            return
        command, arg = splitted
        if command == "remove":  # Removing contact arg
            if arg not in contacts:
                fast_send(user_id, f"Пользователь с id {arg} не найден")  # Contact arg not found
                return
            contacts.pop(arg)
            fast_send(user_id, f"Пользователь с id {arg} удален из рассылки")
        elif command == "add":  # Adding new contact arg
            if arg not in contacts:
                contacts.append(arg)
                fast_send(user_id, f"Пользователь с id {arg} добавлен в рассылку")
            else:
                fast_send(user_id, f"Пользователь с id {arg} уже есть в списке рассылки")
        else:  # Command not found
            fast_send(user_id, f"Команда {command} не найдена")


def bot_handler():
    """
    bot handler for messages from users
    """
    while True:
        try:
            new_messages = tgAPI.get_updates(access_token)["result"]
            messages = tgAPI.normalize(new_messages)
            if new_messages:
                tgAPI.get_updates(access_token, int(messages[-1]["message_id"]) + 1)
            for message in messages:
                one_message_handler(message)
        except:
            print("Ошибка при чтении сообщений")  # Error with reading messages
        time.sleep(message_check_interval)


parser_thread = threading.Thread(target=tvs_handler)  # Launching parser in single thread
parser_thread.start()
bot_thread = threading.Thread(target=bot_handler)
bot_thread.start()
