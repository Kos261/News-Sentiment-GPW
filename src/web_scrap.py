from bs4 import BeautifulSoup
import requests
from io import StringIO
import pandas as pd
import time


headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

def web_scrap(url):
    news_data = []
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("#boxRelatedArticle a.title")

        for article in articles:
            article = article.get_text(strip=True)
            news_data.append({"Title": article})

        return pd.DataFrame(news_data)

    except requests.exceptions.RequestException as e:
        print("ERROR", e)



def web_scrap_multiple_pages(base_url="https://www.bankier.pl/wiadomosc/",pages=3):
    news_data = []

    for page in range(1, pages + 1):
        url = f"{base_url}?page={page}"
        print(f"Scanning page: {url}")

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select("span.entry-title")

            if not articles:
                print("-> Can't find any title (maybe different layout?).")
                continue

            for tag in articles:
                link_tag = tag.find("a")

                if link_tag:
                    title = link_tag.get_text(strip=True)
                    news_data.append({"Title": title})

            # To reset IP
            time.sleep(1)

        except Exception as e:
            print(f"ERROR on page {page}", e)

    return pd.DataFrame(news_data)



def get_GPW(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dfs = pd.read_html(StringIO(response.text), decimal=',', thousands=' ')
        df = dfs[0]
        # df = df[['Walor', 'Kurs', 'Zmiana', 'Obrót']]
        return df

    except requests.exceptions.RequestException as e:
        print("ERROR", e)


if __name__ == "__main__":
    df_news = web_scrap(url="https://www.bankier.pl/wiadomosci/ostatnie")
    print(df_news)

    df_news2 = web_scrap_multiple_pages(pages=10)
    print(df_news2)


    df = get_GPW(url = "https://www.bankier.pl/gielda/notowania/akcje")
    print(df.head())

