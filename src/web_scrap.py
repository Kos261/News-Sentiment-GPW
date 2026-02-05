from bs4 import BeautifulSoup
import requests
from io import StringIO, BytesIO
import pandas as pd
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_bankier_company_news(ticker, pages=1):
    """
    Pobiera newsy dla konkretnej spółki z Bankier.pl.
    URL: https://www.bankier.pl/gielda/notowania/akcje/{TICKER}/wiadomosci
    """
    base_url = f"https://www.bankier.pl/gielda/notowania/akcje/{ticker}/wiadomosci"
    news_data = []

    print(f"Scraping news for: {ticker}...")

    for page in range(1, pages + 1):
        url = f"{base_url}?page={page}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Szukamy listy artykułów w sekcji wiadomości spółki
            # Struktura na Bankierze dla podstrony spółki może się różnić od głównej
            articles = soup.select("div.section-content .news-entry")

            if not articles:
                print(f"-> Brak artykułów na stronie {page} dla {ticker}")
                break

            for entry in articles:
                title_tag = entry.select_one("span.entry-title a")
                date_tag = entry.select_one("time")

                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = "https://www.bankier.pl" + title_tag['href']
                    date = date_tag['datetime'] if date_tag else "Brak daty"
                    
                    # Uproszczenie daty do YYYY-MM-DD
                    if len(date) >= 10:
                        date = date[:10]

                    news_data.append({
                        "Title": title,
                        "Date": date,
                        "Link": link
                    })
            
            time.sleep(0.5) # Krótka pauza żeby nie blokowali

        except Exception as e:
            print(f"Błąd pobierania dla {ticker}: {e}")

    return pd.DataFrame(news_data)

# --- Pozostałe funkcje bez zmian (dla kompatybilności) ---
def web_scrap_bankier_news(base_url="https://www.bankier.pl/wiadomosc/", pages=3):
    news_data = []
    for page in range(1, pages + 1):
        url = f"{base_url}?page={page}"
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select("span.entry-title")
            for tag in articles:
                link_tag = tag.find("a")
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    news_data.append({"Title": title})
            time.sleep(1)
        except Exception:
            pass
    return pd.DataFrame(news_data)

def get_GPW(url):
    # (Twoja funkcja get_GPW - bez zmian)
    pass