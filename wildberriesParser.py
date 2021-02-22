from selenium import webdriver
from selenium.webdriver.chrome.options import Options

wildberries_url = "https://www.wildberries.ru/catalog/elektronika/" \
    "tv-audio-foto-video-tehnika/televizory/televizory?page="  # URL of wildberries page

options = Options()  # Options for Chrome driver (without browser window, js, images and css-events)
options.add_argument("--no-sandbox")
options.add_experimental_option(
    "prefs",
    {
        "profile.default_content_setting_values": {
            "images": 2,
            "webdriver_enable_native_events": 2
        }
    }
)


def get_page_count(wd: webdriver.Chrome) -> int:
    """
    This function returns count of pages of our category
    :param wd: instance of webdriver class
    :return: count of pages of the category
    """
    pages_class_name = "pageToInsert"  # Page's container class name
    wd.get(wildberries_url + "1")  # Getting first page
    pages_element = wd.find_elements_by_class_name(pages_class_name)  # Page's container
    if len(pages_element) == 0:  # Container not found
        return -1
    return len(pages_element[0].find_elements_by_tag_name("a"))  # Each number of page has <a> tag name


def get_televisions() -> list:
    """
    This function returns list of found televisions in format:
        [{
            "url": url of the product page,
            "price": price of product,
            "description": description of the product
        }, ...]
    :return: list of televisions
    """
    # Initializing variables
    result_list = []  # result of function
    product_container_class_name = "ref_goods_n_p,j-open-full-product-card"
    price_class_name = "lower-price"
    description_class_name = "dtlist-inner-brand-name"

    # Initializing webdriver
    wd = webdriver.Chrome(chrome_options=options)
    print("Webdriver started")
    pages_count = get_page_count(wd)  # Getting page count
    print(f"Pages count: {pages_count}")

    # Loading pages
    for i in range(1, pages_count + 1):
        wd.get(wildberries_url + str(i))  # Pages are numbered from 0
        product_list = wd.find_elements_by_class_name(product_container_class_name)
        print(f"Page {i}: products count: %i" % len(product_list))
        for ind, product_raw in enumerate(product_list):
            product = {
                "url": product_raw.get_property("href"),  # Getting url of page of the product
            }
            price_raw = product_raw.find_elements_by_class_name(price_class_name)[0].text  # Getting raw price
            product["price"] = price_raw[:-1].replace(" ", "")  # Removing last symbol and spaces
            # Getting product description
            product["description"] = product_raw.find_elements_by_class_name(description_class_name)[0].text
            result_list.append(product)

    print("Closing webdriver")
    wd.quit()  # Closing webdriver
    return result_list


# Demonstration of working the module
if __name__ == "__main__":
    tvs = get_televisions()
    print(*tvs, sep="\n")
