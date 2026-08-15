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
from selenium.common.exceptions import NoSuchElementException
import inspect

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
        self.products_data = []
        self.path_to_proxy_txt = './proxy.txt'

    def find_catalog(self):
        try:
            self.driver.get(self.start_url)  # selenium запускает реальный браузер в котором открывает сайт дикси
        except Exception as e:
            raise(f"Что-то пошло не так при попытке загрузить сайт Дикси!")
            
        with open('cookies.txt', 'r', encoding='utf-8') as file_cookies:
            for line in file_cookies:
                line = line.strip() # strip удаляет любые пробельные символы c начала и конца строки
                values = line.split(', ')
                self.driver.add_cookie({"name": values[0], "value": values[1]}) # установка cookies

        self.driver.refresh() # обновление страницы для установки cookies (refresh перезапрашивает еткущий url)
        # не можем установить cookies раньше, чем загрузим нужную страницу
        # устанавливаем время ожидания загрузки страницы
        wait = WebDriverWait(self.driver, random.uniform(15.0, 17.0))

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
            raise(f"Ссылка на каталог Дикси не найдена!")

        time.sleep(random.uniform(1.0, 5.0))  # пауза для завершения анимаций, загрузку страницы

        """
        открываем меню наведением мыши
        ActionChains строит цепочки действий. будет генерировать команды для driver
        move_to_element перемещает мышь на элемент catalog_link
        perform последовательно с задержками отправляет событие наведения мыши на элемент
        """

        try:
            ActionChains(self.driver).move_to_element(self.catalog_link).perform()
        except Exception as e:
            raise(f"Не удалось перейти по ссылке на каталог Дикси: {e}.")

        time.sleep(random.uniform(1.0, 5.0))  # дополнительная задержка для появления меню с категориями

        self.__links_process()

        time.sleep(random.uniform(1.0, 5.0))

        self.__products_links_gathering()

        time.sleep(random.uniform(1.0, 5.0))

        self.__get_products_data()

        self.driver.quit()

    def __choose_random_ip(self):
        with open(self.path_to_proxy_txt, 'r') as f:
            proxies = [line.strip() for line in f]

        ip = random.choice(proxies) if proxies else None
        
    
    def __links_process(self):
            # на момент выполнения этого метода мы уже перешли в каталог дикси

            # wait = WebDriverWait(self.driver, random.uniform(15.0, 17.0))
            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.catalog__list a")))

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            main_tag = soup.find('div', class_='catalog-menu')
            if main_tag is None:
                # RunTimeError - ошибка времени выполнения, то есть ошибка во время выполнения программы
                # используется, так как данная ошибка не подходит под другие более конкретные категории ошибок и исключений
                raise RuntimeError(f"Каталог не найден. Поиск осуществлялся через тег div с классом catalog__list!")
            
            try:
                catalog_links = main_tag.find_all('a', class_='link')
            except NoSuchElementException:
                raise RuntimeError(f"Внутри каталога не найдены теги a для поиска ссылок на категории товаров!")
            
            self.category_urls = [urljoin(START_URL, a.get('href')) for a in catalog_links if a.get('href')]

    
    def __products_links_gathering(self):
        # здесь, используя ссылки на категории, мы собираем ссылки на продукты
        if not self.category_urls:
            raise RuntimeError(f"Невозможно собрать ссылки на продукты в Дикси, так как ссылки на категории отсутствуют! ")

        filename = f"categories_dixy{datetime.now().strftime('%Y-%m-%d %H:%M:%s')}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["index", "url"])  # заголовок
            for idx, url in enumerate(self.category_urls, start=1):
                writer.writerow([idx, url])

        for url in self.category_urls:
            if url.count('/') == 6:
                self.driver.get(url)
                safe_url = re.sub(r'[^a-zA-Z0-9.]', '_', url)

                wait = WebDriverWait(self.driver, random.uniform(15.0, 17.0))
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".listing__cards")))  # или другой контейнер
                    all_links = self.driver.find_elements(By.XPATH, "//a[@class='card__link']")
                except Exception as e:
                    raise RuntimeError(f"Чето пошло не так при попытке найти ссылки на товары в категории {url}. Ошибка: {e}.")

                self.products_links.extend([urljoin(START_URL, link.get_attribute("href")) for link in all_links if link.get_attribute("href")])

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

        if not self.products_links:
            raise RuntimeError(f"Нет ссылок на продукты для сохранения ни в одной из категорий.")
        
        filename = f"products_dixy{datetime.now().strftime('%Y-%m-%d')}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["index", "url"])  # заголовок
            for idx, url in enumerate(self.products_links, start=1):
                writer.writerow([idx, url])


    def __get_products_data(self):
        characteristics = {'название', 'цена_без_скидки', 'скидка_по_карте', 'размер_скидки'}
        temp_products_data = []

        for link in self.products_links:
            product = {}
                
            self.driver.get(link)
            wait = WebDriverWait(self.driver, random.uniform(15.0, 17.0))
            try:
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[@class='card__link']")))
            except TimeoutException:
                raise RuntimeError(f"Чето пошло не так при попытке найти ссылки на товары в категории {link}.")
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            # название товара
            name = soup.find('h1', class_='detail-card__title open')
            if name:
                name = name.get_text(strip=True)   # очищает от пробелов и переносов
            else:
                name = None
            product['название'] = name

            # цена товара
            price = soup.find('div', class_='card__price-num')
            if price:
                first_part = price.get_text(strip=True)
                second_part = price.find("span").get_text(strip=True)
                price = int(first_part + second_part)
            else:
                price = None
            product['цена_без_скидки'] = price

            # есть ли на товар скидка по карте и какая
            discount = soup.find('div', class_='badge violet violet-title')
            if discount:
                persentage = discount.find("span").get_text(strip=True)
                persentage = re.search(r'(\d+)%', persentage)
                discount = True
            else:
                discount = False
                persentage = None
            product['скидка_по_карте'] = discount
            product['размер_скидки'] = persentage

            # получение всех остальных характеристик
            parent = soup.find("div", class_="detail-data__holder list list-top")
            lines = parent.find_all("div", class_="list__line")

            for line in lines:
                # Получаем все span внутри этой строки
                spans = line.find_all("span")
                label = spans[0].get_text(strip=True)   # первый span
                value = spans[1].get_text(strip=True)   # второй span
                product[label] = value
                characteristics.add(label)

            temp_products_data.append(product)
            
        characteristics = list(characteristics)
        for row in temp_products_data:
            full_row = {key: "" for key in characteristics}   # все колонки с пустыми строками
            full_row.update(row)                      # заполняем тем, что есть
            self.products_data.append(full_row)

        with open("products.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=characteristics)
            writer.writeheader()
            writer.writerows(self.products_data)


def get_products():
    dixy = ProductParser(START_URL)
    dixy.find_catalog()


if __name__ == "__main__":
    get_products()
