import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "https://dixy.ru"
SEARCH_TERM = "хлеб"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def find_category():
    resp = requests.get(START_URL, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Сохраняем HTML для отладки
    with open("dixy_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("💾 HTML сохранён в dixy_page.html")
    
    # 🔥 Ищем h2 с классом catalog__title
    titles = soup.find_all("div", class_="catalog__list")
    print(f"🔍 Найдено заголовков: {len(titles)}")
    
    # for title in titles:
    #     text = title.get_text(strip=True).lower()
    #     print(f"   • '{text}'")
        
    #     if SEARCH_TERM in text:
    #         # Ищем родительский <a>
    #         link = title.find_parent("a")
    #         full_url = urljoin(START_URL, link["href"])
    #         return full_url, text
    
    return titles

if __name__ == "__main__":
    result = find_category()
    print(result)