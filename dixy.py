import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
from datetime import datetime
import requests, re, random
import pandas as pd

START_URL = "https://dixy.ru"


class ProductParser:
    def __init__(self, start_url):
        self.start_url = start_url
        # создание объекта, который хранит настройки запуска браузера
        options = webdriver.ChromeOptions()
        # убираем режим песочницы, так как может потребовать доп права, которых у нас нема
        options.add_argument("--no-sandbox")
        # используем неразделяемую память: используем обычную папку /tmp
        # options.add_argument("--disable-dev-shm-usage") бесполезно пока не используем docker или сервер
        # запускаем в фоновом режиме
        options.add_argument("--headless")
        # типо для смены ip адресов
        options.add_argument("--proxy-server")

        # создаем экземпляр драйвера Chrome (мой представитель в хром)
        self.driver = webdriver.Chrome(options=options)
        self.catalog_link = None
        self.category_urls = []
        self.products_links = []

    def find_catalog(self):
        self.driver.get(self.start_url)  # открываем нужную нам ссылку

        with open('cookies.txt', 'r', encoding='utf-8') as file_cookies:
            for line in file_cookies:
                line = line.strip()
                values = line.split(', ')
                self.driver.add_cookie({"name": values[0], "value": values[1]}) # установка cookies

        self.driver.refresh() # обновление страницы для установки cookies (refresh перезапрашивает еткущий url)
        # не можем установить cookies раньше, чем загрузим нужную страницу

        # устанавливаем время ожидания загрузки страницы
        wait = WebDriverWait(self.driver, 15)

        """
        1. Ждём появления ссылки "Каталог" в DOM (не обязательно кликабельной)
        until - метод, принимающий условие. повторно вызывает условие пока не вернет true (каждые 0.5 сек) или время не закончиится
        EC - expected conditions
        presence_of_element_located - функция модуля EC: элемент появился в DOM (может быть невидимым или некликабельным)
        DOM - document object model - дерево объектов на основе HTML
        XPATH - язык запросов для навигации по XML документам (HTML частный случай) - описывает как найти элементы в DOM дереве
        "//a[@aria-label='Ссылка на Каталог Дикси']" - Xpath выражение, селектор
        ищет тег a, у которого атрибут aria-label равен 'Ссылка на Каталог Дикси'
        возвращается объект WebElement
        """
        try:
            self.catalog_link = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[@aria-label='Ссылка на Каталог Дикси']")
                )
            )
        except TimeoutException:
            print("Ссылка на каталог Дикси не найдена!")

        time.sleep(1)  # пауза для завершения анимаций, загрузку страницы

        """
        открываем меню наведением мыши
        ActionChains строит цепочки действий. будет генерировать команды для driver
        move_to_element перемещает мышь на элемент catalog_link
        perform последовательно с задержками отправляет событие наведения мыши на элемент
        """
        try:
            ActionChains(self.driver).move_to_element(self.catalog_link).perform()
            print("Выполнено наведение мыши")
        except Exception as e:
            print(f"Не удалось перейти по ссылке на каталог Дикси: {e}")

        time.sleep(2)  # дополнительная задержка для появления меню с категориями

        try:
            self.__links_process()
        except Exception as e:
            print(f"Ошибка при обработке ссылок на категории в Дикси: {e}")

        try:
            self.__products_links_gathering()
        except Exception as e:
            print(f"Ошибка при обработке ссылок на продукты в Дикси: {e}")

    def __products_links_gathering(self):
   
        if self.category_urls:
            for url in self.category_urls:
                if url.count("/") == 6:

                    self.driver.get(url)

                    # wait = WebDriverWait(self.driver, 15)

                    soup = BeautifulSoup(self.driver.page_source, "html.parser")

                    selector = "a.card__link"

                    all_links = soup.select(selector)
                    if all_links:
                        self.products_links = [urljoin(START_URL, link.get("href")) for link in all_links if link.get("href") and link.get("href") != "#" and not link.get("href").startswith("javascript")]
                    else:
                        print(f"Не удалось найти товары на странице: {url}!")

                    time.sleep(random.uniform(5, 10))

                    '''
                    try:
                        all_links = wait.until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, "//a[@class='card__link']")
                            )
                        )

                        self.products_links = [urljoin(self.start_url, link.get_attribute("href")) for link in all_links if link.get_attribute("href") and link.get_attribute("href") != "#" and not link.get_attribute("href").startswith("javascript")]
                
                    except TimeoutException:
                        print(
                            f"Не удалось собрать ссылки на продукты в категории: {url}!"
                        )
                    '''
                    

            if self.products_links:
                filename = f"products_dixy.csv"
                with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["index", "url"])  # заголовок
                    for idx, url in enumerate(self.products_links, start=1):
                        writer.writerow([idx, url])

            else:
                raise Exception("Нет ссылок для сохранения ссылок на продукты.")

        else:
            raise Exception("Невозможно собрать ссылки на продукты в Дикси, \
                  так как ссылки на категории отсутствуют!")

        self.driver.quit()

    def __links_process(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        selector = ".catalog-menu a"  # класс catalog-menu, в нем ищем все теги a

        links = soup.select(selector)
        if links:
            self.category_urls = [urljoin(START_URL, link.get("href")) for link in links if link.get("href") and link.get("href") != "#" and not link.get("href").startswith("javascript")]
            # for a in links:
            #     href = a.get("href")
            #     if href and href != "#" and not href.startswith("javascript"):
            #         full_url = urljoin(START_URL, href)
            #         self.category_urls.append(full_url)
        else:
            raise Exception(
                "Не удалось найти ссылки категорий по выбранному селектору в Дикси."
            )


def get_products():
    dixy = ProductParser(START_URL)
    dixy.find_catalog()


if __name__ == "__main__":
    get_products()
