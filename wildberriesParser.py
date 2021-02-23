from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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


def get_page_count(wd: webdriver.Chrome, url: str) -> int:
    """
    This function returns count of pages of our category
    :param wd: instance of webdriver class
    :param url: url of products page
    :return: count of pages of the category
    """
    wd.get(url + "1")  # Getting first page

    pages_class_name = "pageToInsert"  # Page's container class name
    pages_element = wd.find_elements_by_class_name(pages_class_name)  # Page's container
    pages_count = len(pages_element[0].find_elements_by_tag_name("a"))  # Each number of page has <a> tag name
    return pages_count if pages_count > 0 else 1  # If count of <a> elements = 0 it means that exists 1 page only


def get_products(url: str) -> list:
    """
    :param url: url of products page
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

    # Adding page (GET) parameter to url
    if "page=" not in url:  # Url has not page parameter
        if "?" not in url:  # Url has not GET parameters
            url += "?page="
        else:
            url += "&page="  # Url has other GET parameters

    # Initializing webdriver
    wd = webdriver.Chrome(chrome_options=options)
    print("Webdriver started")
    pages_count = get_page_count(wd, url)  # Getting page count
    print(f"Pages count: {pages_count}")

    # Loading pages
    for i in range(1, pages_count + 1):
        wd.get(url + str(i))  # Pages are numbered from 0
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
    tvs_url = "https://www.wildberries.ru/catalog/0/search.aspx?search=%D0%B2%D0%B8%D0%B4%D0%B5%D0%BE%D0%BA%D0%B0%D1%80%D1%82%D1%8B&xsearch=true"
    tvs = get_products(tvs_url)
    print(*tvs, sep="\n")
