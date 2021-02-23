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
common_products_data = serial_data["common_products"]  # Serialized data about common products
admin_products_data = serial_data["admin_products"]  # Serialized data about admin products
contacts = serial_data["contacts"]  # Serialized data about contacts for sending
message_check_interval = float(config["messages_check_interval"])  # Interval (seconds) between updating bot messages
refresh_interval = float(config["refresh_interval"])  # Interval (seconds) between updating wildberries TVs
access_token = config["access_token"]  # Access token of telegram bot
head_admin = config["head_admin"]  # Head admin telegram id
if head_admin not in contacts:
    contacts.append(head_admin)  # Adding head admin to sending notices
common_product_urls = serial_data["common_product_urls"]  # Products for all contacts
admin_product_urls = serial_data["admin_product_urls"]  # Products for admin only


def update_data():
    """
    updating serial_data.json5 (info about available tvs and contacts for sending)
    """
    json5.dump(serial_data, open(serial_data_path, "w"))  # Writing current data in JSON5-file


def one_category_product_handler(url: str, products_data: dict) -> str:
    """
    this handler working with only 1 category (url) and creating message string for
    notices about decreased prices
    :param url: url of wildberries request
    :param products_data: dict of data about this products
    :return: string for notice message
    """
    try:
        new_update = wildberriesParser.get_products(url)  # New data about products
    except:
        error_message = f"При обновлении информации о товарах {url} произошла ошибка"
        print(error_message)
        tgAPI.send_message(access_token, head_admin, error_message)  # Notice head admin about update error
        return ""
    notice = ""
    for product in new_update:
        product_url = product["url"]
        if product_url not in products_data:  # Adding new product to data dict
            products_data[product_url] = {
                "description": product["description"],
                "price": product["price"]
            }
            continue
        old_price = products_data[product_url]["price"]
        new_price = product["price"]
        description = product["description"]
        if int(new_price) < int(old_price):  # Price decreased
            notice += f"{product_url}\n{description}\nСтарая цена: {old_price}\nНовая цена{new_price}\n\n"
            products_data[product_url]["price"] = new_price  # Updating product price in data dict
    return notice


def send(user_id, text):  # trying to send message
    error_message = f"Не удалось уведомить пользователя {user_id}"
    try:
        tgAPI.send_message(access_token, user_id, text)
    except:
        print(error_message)
        if user_id != head_admin:
            tgAPI.send_message(access_token, head_admin, error_message)


def product_handler():
    """
    tvs (televisions) handler calls in single Thread and finding changing prices of wildberries products (tvs)
    """
    while True:
        message_header = "Цена на некоторые продукты снизилась\n\n"
        message = ""
        for product in common_product_urls:
            message += one_category_product_handler(product, common_products_data)
        if message:
            for contact in contacts:  # Sending notices to all contacts
                send(contact, message_header + message)

        message = ""
        for product in admin_product_urls:
            message += one_category_product_handler(product, admin_products_data)
        if message:
            send(head_admin, message_header + message)

        update_data()  # Updating serial data in file
        time.sleep(refresh_interval)


def add_to_list(element: str, data_list: list) -> bool:
    if element in data_list:
        return False
    data_list.append(element)
    return True


def remove_from_list(element: str, data_list: list) -> bool:
    if element not in data_list:
        return False
    data_list.remove(element)
    return True


def add_contact(contact: str) -> str:
    return [
        f"Пользователь {contact} уже есть в списке контактов",  # Fail
        f"Пользователь {contact} успешно добавлен"  # Success
    ][add_to_list(contact, contacts)]


def remove_contact(contact: str) -> str:
    return [
        f"Пользователь с id {contact} отсутствует в списке",  # Fail
        f"Пользователь с id {contact} добавлен в список"  # Success
    ][remove_from_list(contact, contacts)]


def add_admin_url(url: str) -> str:
    return [
        "Каталог уже есть в списке",  # Fail
        "Каталог успешно добавлен"  # Success
    ][add_to_list(url, admin_product_urls)]


def remove_admin_url(url: str) -> str:
    return [
        "Каталога нет в списке",  # Fail
        "Каталог успешно удален"  # Success
    ][remove_from_list(url, admin_product_urls)]


def add_common_url(url: str) -> str:
    return [
        "Каталог уже есть в списке",  # Fail
        "Каталог успешно добавлен"  # Success
    ][add_to_list(url, common_product_urls)]


def remove_common_url(url: str) -> str:
    return [
        "Каталога нет в списке",  # Fail
        "Каталог успешно удален"  # Success
    ][remove_from_list(url, common_product_urls)]


def one_message_handler(message: dict):
    """
    this is result of refactoring, this function handles single message of user
    :param message: message dict
    """
    help_message = """
Команды для всех:

help - помощь
id - узнать свой id


Команды для администратора
    
common - показать каталоги для всех пользователей
admin - показать каталоги администратора
add_common <url> - добавить каталог <url> в общую рассылку
remove_common <url> - удалить каталог <url> из общей рассылки
add_admin <url> - добавить каталог <url> для рассылки для администратора
remove_admin <url> - удалить <url> из рассылки для администратора
add_contact <id> - добавить контакт <id> в общую рассылку
remove_contact <id> - удалить контакт <id> из общей рассылки  
"""
    unexpected_command_message = "Недоступная вам команда или неверное количество аргументов"

    user_id = message["user_id"]
    commands_for_all = ["id", "help"]
    text = message["text"]
    splitted = text.split()
    functional = [
        {  # 0 arguments
            "id": lambda: f"Ваш id: {user_id}",  # User wants to get self id
            "help": lambda: help_message,  # Help instruction
            "common": lambda: "Каталоги для всех пользователей:\n" + "\n".join(common_product_urls),  # common
            "admin": lambda: "Каталоги администратора:\n" + "\n".join(admin_product_urls),  # admin urls
            "contacts": lambda: "Пользователи в рассылке: \n" + "\n".join(contacts)
        },
        {  # 1 argument
            "add_common": add_common_url,  # Add new common url
            "remove_common": remove_common_url,  # Remove common url
            "add_admin": add_admin_url,  #
            "remove_admin": remove_admin_url,
            "add_contact": add_contact,
            "remove_contact": remove_contact
        }
    ]
    arguments_count = len(splitted) - 1  # Arguments count of user's command
    command, args = splitted[0], splitted[1:]
    # Too many parameters or
    # undefined command or
    # non-admin user try to use admin-only command
    if arguments_count >= len(functional) or \
            command not in functional[arguments_count] or \
            (user_id != head_admin and command not in commands_for_all):
        send(user_id, unexpected_command_message)
        return
    send(user_id, functional[arguments_count][command](*args))


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


parser_thread = threading.Thread(target=product_handler)  # Launching parser in single thread
parser_thread.start()
bot_thread = threading.Thread(target=bot_handler)  # Launching bot handler in single thread
bot_thread.start()
