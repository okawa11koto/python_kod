import os
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import datetime
import tkinter as tk
from tkinter import messagebox, filedialog

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

    def save_results(self, filename="parsed_data.html"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Результаты парсинга</title></head><body>")
            f.write("<h1>Результаты парсинга</h1>")
            for result in self.results:
                f.write(f"<p><a href='{result.get('link', '#')}'>{result.get('title', 'Без заголовка')}</a></p>")
            f.write("</body></html>")
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
                    self.results.append({"title": text, "link": f"Автор: {author}"})
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

# Функции для работы с GUI
def start_parsing():
    keywords = entry_keywords.get().split(",")
    keywords = [kw.strip() for kw in keywords if kw.strip()]

    if not keywords:
        messagebox.showerror("Ошибка", "Введите хотя бы одно ключевое слово!")
        return

    selected_sites = []
    if var_wikipedia.get():
        selected_sites.append(WikipediaParser("https://ru.wikipedia.org", keywords))
    if var_quotes.get():
        selected_sites.append(QuotesParser("http://quotes.toscrape.com", keywords))
    if var_habr.get():
        selected_sites.append(BlogParser("https://habr.com/ru/", keywords))

    if not selected_sites:
        messagebox.showerror("Ошибка", "Выберите хотя бы один сайт для парсинга!")
        return

    all_results = []
    for parser in selected_sites:
        parser.parse()
        all_results.extend(parser.results)

    if all_results:
        save_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if save_path:
            selected_sites[0].save_results(save_path)
            messagebox.showinfo("Успех", f"Парсинг завершён! Результаты сохранены в {save_path}")
    else:
        messagebox.showinfo("Результаты", "Не найдено данных по заданным ключевым словам.")

# Создание GUI
root = tk.Tk()
root.title("Парсер сайтов")

# Поле для ввода ключевых слов
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

label_keywords = tk.Label(frame_top, text="Введите ключевые слова через запятую:")
label_keywords.pack()

entry_keywords = tk.Entry(frame_top, width=50)
entry_keywords.pack()

# Флажки для выбора сайтов
frame_middle = tk.Frame(root)
frame_middle.pack(pady=10)

label_sites = tk.Label(frame_middle, text="Выберите сайты для парсинга:")
label_sites.pack()

var_wikipedia = tk.BooleanVar()
check_wikipedia = tk.Checkbutton(frame_middle, text="Wikipedia", variable=var_wikipedia)
check_wikipedia.pack(anchor="w")

var_quotes = tk.BooleanVar()
check_quotes = tk.Checkbutton(frame_middle, text="Quotes to Scrape", variable=var_quotes)
check_quotes.pack(anchor="w")

var_habr = tk.BooleanVar()
check_habr = tk.Checkbutton(frame_middle, text="Habr", variable=var_habr)
check_habr.pack(anchor="w")

# Кнопка для запуска парсинга
frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=20)

button_start = tk.Button(frame_bottom, text="Начать парсинг", command=start_parsing)
button_start.pack()

# Запуск приложения
root.mainloop()



