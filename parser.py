import requests
from bs4 import BeautifulSoup
import json
import datetime

# Базовый класс парсера
class Parser:
    def __init__(self, base_url, keywords):
        self.base_url = base_url
        self.keywords = keywords
        self.results = []

    def fetch_html(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.log(f"Ошибка загрузки {url}: {e}")
            return ""

    def parse(self):
        raise NotImplementedError("Метод parse() должен быть реализован в подклассе")

    def save_results(self, filename="parsed_data.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        self.log(f"Результаты сохранены в файл {filename}")

    def log(self, message):
        log_message = f"{datetime.datetime.now()}: {message}\n"
        with open("parser.log", "a", encoding="utf-8") as f:
            f.write(log_message)
        print(log_message, end="")

# Парсер для Wikipedia
class WikipediaParser(Parser):
    def parse(self):
        for keyword in self.keywords:
            url = f"https://ru.wikipedia.org/w/index.php?search={keyword}"
            html = self.fetch_html(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            articles = soup.find_all("div", class_="mw-search-result-heading")
            if articles:
                for article in articles:
                    title = article.find("a").get_text(strip=True)
                    link = "https://ru.wikipedia.org" + article.find("a")["href"]
                    self.results.append({"title": title, "link": link})
            else:
                self.log(f"Не найдено статей для ключевого слова '{keyword}' на Wikipedia.")

        self.log(f"Найдено {len(self.results)} статей на Wikipedia")

# Парсер для Quotes to Scrape
class QuotesParser(Parser):
    def parse(self):
        html = self.fetch_html(self.base_url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")
        quotes = soup.find_all("div", class_="quote")
        if quotes:
            for quote in quotes:
                text = quote.find("span", class_="text").get_text(strip=True)
                author = quote.find("small", class_="author").get_text(strip=True)
                if any(keyword.lower() in text.lower() for keyword in self.keywords):
                    self.results.append({"quote": text, "author": author})
        else:
            self.log("Цитаты не найдены на Quotes to Scrape.")

        self.log(f"Найдено {len(self.results)} цитат на Quotes to Scrape")

# Парсер для Habr
class BlogParser(Parser):
    def parse(self):
        html = self.fetch_html(self.base_url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article")
        if articles:
            for article in articles:
                header = article.find("h2")
                if header:
                    title = header.get_text(strip=True)
                    link = article.find("a")["href"]
                    if any(keyword.lower() in title.lower() for keyword in self.keywords):
                        self.results.append({"title": title, "link": link})
                else:
                    self.log(f"Заголовок не найден в статье {article}")

        else:
            self.log("Статьи не найдены на Habr.")

        self.log(f"Найдено {len(self.results)} статей на Habr")

# Основной код
if __name__ == "__main__":
    # Указываем ключевые слова и ссылки на сайты
    keywords = ["Работа", "Год", "Читать"]
    parsers = [
        WikipediaParser("https://ru.wikipedia.org", keywords),
        QuotesParser("http://quotes.toscrape.com", keywords),
        BlogParser("https://habr.com/ru/", keywords),
    ]

    # Запускаем парсинг
    all_results = []
    for parser in parsers:
        parser.parse()
        all_results.extend(parser.results)

    # Сохраняем все в логи
    output_file = "aggregated_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    print(f"Все данные сохранены в файл {output_file}")

