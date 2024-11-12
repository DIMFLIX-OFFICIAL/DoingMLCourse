import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

class Article:
    def __init__(self, title, publication_date, content):
        self.title = title
        self.publication_date = publication_date
        self.content = content

    def __str__(self):
        return f"Title: {self.title}\nPublication Date: {self.publication_date}\nFull Content: {self.content[:100]}...\n"

class Company:
    def __init__(self, name):
        self.name = name
        self.articles = []

    def add_article(self, article):
        self.articles.append(article)

    def __str__(self):
        return f"Company: {self.name}, Articles: {len(self.articles)}"

class HabrScraper:
    BASE_URL = "https://habr.com/"

    def __init__(self, companies):
        self.companies = [Company(name) for name in companies]

    def get_full_article_content(self, article_url):
        response = requests.get(article_url)
        if response.status_code == 200:
            soup = bs(response.text, 'html.parser')
            article_body = soup.find(class_='tm-article-body')
            return article_body.get_text(strip=True) if article_body else "Content not found."
        return "Failed to retrieve article."

    def get_data_article(self, company_link, title_text):
        modified_link = "/".join(company_link.split("/")[:-2] + ['articles/'])
        url = self.BASE_URL + modified_link
        response = requests.get(url)
        if response.status_code == 200:
            soup = bs(response.text, 'html.parser')
            all_articles = soup.find_all(class_="tm-title__link")
            for article in all_articles:
                title = article.get_text(strip=True)
                article_url = self.BASE_URL + article['href']
                publication_date_tag = article.find_previous('time')
                publication_date = publication_date_tag.get('datetime', '').strip() if publication_date_tag else "Not available"
                full_content = self.get_full_article_content(article_url)
                self.companies[0].add_article(Article(title, publication_date, full_content))
                print(Article(title, publication_date, full_content))
        else:
            print(f"Error fetching articles from {url}: {response.status_code}")

    def get_company_data(self):
        for company in self.companies:
            url = f'https://habr.com/ru/search/?q={company.name}&target_type=companies&order=relevance'
            response = requests.get(url)
            if response.status_code == 200:
                soup = bs(response.text, 'html.parser')
                titles = soup.find_all(class_='tm-company-snippet__title')
                descriptions = soup.find_all(class_='tm-company-snippet__description')
                links = soup.find_all(class_='tm-company-snippet__info')
                for title, description, link in zip(titles, descriptions, links):
                    title_text = title.get_text(strip=True)
                    description_text = description.get_text(strip=True)
                    link_tag = link.find('a')
                    link_href = link_tag['href'] if link_tag and 'href' in link_tag.attrs else 'No link'
                    company.add_article(Article(title_text, "", description_text))
                    self.get_data_article(link_href, title_text)
            else:
                print(f"Error fetching data for {company.name}: {response.status_code}")

    def save_to_csv(self, filename='all_company_data.csv'):
        articles_data = []
        for company in self.companies:
            for article in company.articles:
                articles_data.append([company.name, "", "", article.title, article.publication_date, article.content])
        df = pd.DataFrame(articles_data, columns=["Company Name", "Description", "Link", "Article Title", "Publication Date", "Full Content"])
        df.to_csv(filename, index=False, encoding='utf-8')

if __name__ == "__main__":
    companies = ['СберМаркет', 'Московская биржа', 'Samsung Electronics', 'Нетология', 'Цифровое образование']
    scraper = HabrScraper(companies)
    scraper.get_company_data()
    scraper.save_to_csv()
