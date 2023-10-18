from selenium                                import webdriver
from selenium.webdriver.common.by            import By
from selenium.webdriver.common.keys          import Keys
from selenium.webdriver.support.ui           import WebDriverWait
from selenium.webdriver.support              import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service       import Service as ChromeService
from webdriver_manager.chrome                import ChromeDriverManager
import json
import time
import requests
import re



"""
    Функция чтения json-файла

    :param     filename: Название файла
    :type      filename: str.
    
    :returns: dict или list
"""
def json_load(filename):
    with open(filename, "r", encoding="utf8") as read_file:
        result = json.load(read_file)
    return result

"""
    Функция записи в json-файл

    :param     filename: Название файла
    :type      filename: str.
    :param     data: Записываемые данные
    :type      data: list or dict.
  
"""
def json_dump(filename, data):
    with open(filename, "w", encoding="utf8") as write_file:
        json.dump(data, write_file, ensure_ascii=False)




"""
    Функция отправки сообщения в телеграм 

    :param     text: Отправляемый текст сообщения
    :type      text: str.
    :param tg_token: Токен телеграм-бота из BotFather
    :type  tg_token: str.
    :param  user_id: ID пользователя бота
    :type   user_id: int.

"""
def send_msg(text, tg_token, user_id):
    url_req = (
        "https://api.telegram.org/bot"
        + tg_token
        + "/sendMessage"
        + "?chat_id="
        + str(user_id)
        + "&text="
        + text
    )
    requests.get(url_req)



def get_driver_cookies(driver):

    cookies_list = browser.get_cookies()
    cookies_dict = {}
    for cookie in cookies_list:
        cookies_dict[cookie["name"]] = cookie["value"]
    return [cookies_list, cookies_dict]

try:
    config         = json_load(r"./json/config.json")
except:
    print('Заполните корректно файл с настройками')




url       = "https://lis-skins.ru/market/csgo/?sort_by=price_asc&price_to={}&page={}"
max_price = config['max_price']
max_page  = config['max_page']
min_sale  = config['min_sale']
token     = config['tg_token']
user_id   = config['user_id']

try:
    cookies   = json_load(r"./json/cookies.json")

except:
    print('Заполните корректно файл с куки')



try:
    config = json_load("config.json")
except:
    print("Необходимо проверить конфигурационный файл и перезапустить приложение")
    time.sleep(20)


error_count = True
browser     = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
browser.get("https://lis-skins.ru/market/csgo/")

for cookie in cookies:
    browser.add_cookie(cookie)


#  блок проверки защиты от ддоса
while True:
    try:

        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "skins-obj"))
        )
        break
    except Exception as e:
        print(e)
        if error_count:
            send_msg("CloudFlare error", token, user_id)
            error_count = False
        continue


total_price = 0

# блок парсинга сведений о скинах и автоматической покупки 
while True:
    for page in range(1, max_page + 1):
        prices = {}
        browser.get(url.format(max_price, page))

        try:

            element = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.ID, "skins-obj"))
            )
            no_weapon = browser.find_elements(By.CLASS_NAME, "no-skins")
            if len(no_weapon) > 0:
                continue
            prices_list = browser.find_elements(By.CLASS_NAME, "price")
            hrefs = browser.find_elements(By.CLASS_NAME, "name")

            for item_price in prices_list:
                price = float(item_price.text.split(".cls")[0].replace(" ", ""))
                href = hrefs[prices_list.index(item_price)].get_attribute("href")

                prices[href] = price

            for href in prices.keys():
                try:
                    while True:
                        browser.get(href)

                        element = WebDriverWait(browser, 5).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "skin-min-price")
                            )
                        )
                        sale = re.findall(
                            "\d+",
                            browser.find_element(By.CLASS_NAME, "min-price-sale").text,
                        )[0]
                        
                        # блок покупки товара с подходящей скидкой
                        if int(sale) >= min_sale:
                            total_price += prices[href]
                            buy = browser.find_element(
                                By.CLASS_NAME, "buy-now.buy-now-button"
                            ).click()

                            try:
                                element = WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located(
                                        (
                                            By.CLASS_NAME,
                                            "buy-now-popup-button.buy-now-popup-bottom-button",
                                        )
                                    )
                                )
                                buy = browser.find_element(
                                    By.CLASS_NAME,
                                    "buy-now-popup-button.buy-now-popup-bottom-button",
                                ).click()
                                element = WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located(
                                        (
                                            By.CLASS_NAME,
                                            "buy-now-popup-payment-info-status",
                                        )
                                    )
                                )
                            except:
                                continue
                            time.sleep(3)
                            total_price += prices[href]

                        else:
                            break


                except Exception as e:
                    continue
                time.sleep(1)
        except Exception as e:
            continue

