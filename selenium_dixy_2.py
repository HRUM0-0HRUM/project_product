import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
from datetime import datetime

START_URL = "https://dixy.ru"

options = (
    webdriver.ChromeOptions()
)  # создание объекта, который хранит настройки запуска браузера
options.add_argument(
    "--no-sandbox"
)  # убираем режим песочницы, так как может потребовать доп права, которых у нас нема
options.add_argument(
    "--disable-dev-shm-usage"
)  # используем неразделяемую память: используем обычную папку /tmp
# options.add_argument("--headless")  # запускаем в фоновом режиме

driver = webdriver.Chrome(
    options=options
)  # создаем экземпляр драйвера Chrome (мой представитель в хром)
driver.get(START_URL)  # открываем нужную нам ссылку

wait = WebDriverWait(driver, 15)  # устанавливаем время ожидания загрузки страницы

# 1. Ждём появления ссылки "Каталог" в DOM (не обязательно кликабельной)
# until - метод, принимающий условие. повторно вызывает условие пока не вернет true (каждые 0.5 сек) или время не закончиится
# EC - expected conditions
# presence_of_element_located - функция модуля EC: элемент появился в DOM (может быть невидимым или некликабельным)
# DOM - document object model - дерево объектов на основе HTML
# XPATH - язык запросов для навигации по XML документам (HTML частный случай) - описывает как найти элементы в DOM дереве
# "//a[@aria-label='Ссылка на Каталог Дикси']" - Xpath выражение, селектор
# ищет тег a, у которого атрибут aria-label равен 'Ссылка на Каталог Дикси'
# возвращается объект WebElement
catalog_link = wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//a[@aria-label='Ссылка на Каталог Дикси']")
    )
)
print("Ссылка на каталог найдена")

time.sleep(1)  # пауза для завершения анимаций, загрузку страницы

# открываем меню наведением мыши
# ActionChains строит цепочки действий. будет генерировать команды для driver
# move_to_element перемещает мышь на элемент catalog_link
# perform последовательно с задержками отправляет событие наведения мыши на элемент
try:
    ActionChains(driver).move_to_element(catalog_link).perform()
    print("Выполнено наведение мыши")
except Exception as e:
    print(f"Наведение не сработало: {e}")

time.sleep(2)  # дополнительная задержка для появления меню с категориями

# Собираем ссылки категорий
# driver.page_source - возвращает HTML код текущей страницы

soup = BeautifulSoup(driver.page_source, "html.parser")
category_urls = []
selector = ".catalog-menu a"  # класс catalog-menu, в нем ищем все теги a

links = soup.select(selector)
if links:
    print(f"Найдено {len(links)} ссылок по селектору {selector}")
    for a in links:
        href = a.get("href")
        if href and href != "#" and not href.startswith("javascript"):
            full_url = urljoin(START_URL, href)
            category_urls.append(full_url)
else:
    print("Не удалось найти ссылки категорий по выбранному селектору.")


if category_urls:
    filename = f"categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["index", "url"])  # заголовок
        for idx, url in enumerate(category_urls, start=1):
            writer.writerow([idx, url])
    print(f"Ссылки на категории сохранены в файл: {filename}")
else:
    print("Нет ссылок для сохранения.")

driver.quit()
