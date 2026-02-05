import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from datetime import datetime, timedelta
import torch
import pytz 
from io import BytesIO
import warnings
import re

# Ignorowanie ostrzeżeń SSL/Excel
warnings.filterwarnings("ignore")

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="GPW SENTIX AI", layout="wide", initial_sidebar_state="collapsed")

hide_ui_css = """
<style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    footer {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .block-container {
        padding-top: 1rem;
    }
</style>
"""

st.markdown(hide_ui_css, unsafe_allow_html=True)
# --- MAPOWANIE SPÓŁEK ---
# --- MAPOWANIE SPÓŁEK (PEŁNY WIG20) ---
COMPANIES = {
    "PKO BP": {"yahoo": "PKO.WA", "bankier": "PKOBP"},
    "ORLEN": {"yahoo": "PKN.WA", "bankier": "PKNORLEN"},
    "KGHM": {"yahoo": "KGH.WA", "bankier": "KGHM"},
    "PEKAO": {"yahoo": "PEO.WA", "bankier": "PEKAO"},
    "PZU": {"yahoo": "PZU.WA", "bankier": "PZU"},
    "DINO": {"yahoo": "DNP.WA", "bankier": "DINOPL"},
    "ALLEGRO": {"yahoo": "ALE.WA", "bankier": "ALLEGRO"},
    "LPP": {"yahoo": "LPP.WA", "bankier": "LPP"},
    "CD PROJEKT": {"yahoo": "CDR.WA", "bankier": "CDPROJEKT"},
    "SANTANDER": {"yahoo": "SPL.WA", "bankier": "SANPL"},
    "MBANK": {"yahoo": "MBK.WA", "bankier": "MBANK"},
    "ALIOR": {"yahoo": "ALR.WA", "bankier": "ALIOR"},
    "KĘTY": {"yahoo": "KTY.WA", "bankier": "KETY"},
    "ŻABKA": {"yahoo": "ZAB.WA", "bankier": "ZABKA"},
    "BUDIMEX": {"yahoo": "BDX.WA", "bankier": "BUDIMEX"},
    "PGE": {"yahoo": "PGE.WA", "bankier": "PGE"},
    "KRUK": {"yahoo": "KRU.WA", "bankier": "KRUK"},
    "ORANGE PL": {"yahoo": "OPL.WA", "bankier": "ORANGEPL"},
    "CCC": {"yahoo": "CCC.WA", "bankier": "CCC"},
    "PEPCO": {"yahoo": "PCO.WA", "bankier": "PEPCO"}
}

# --- 1. MODEL AI (SZYBKI DISTILBERT) ---
@st.cache_resource
def load_model():
    # Model "student" jest lżejszy i szybszy, a nadal świetnie radzi sobie z polskim
    model_name = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    device = 0 if torch.cuda.is_available() else -1
    # Używamy zwykłej klasyfikacji tekstu (dużo szybsza niż zero-shot)
    return pipeline("text-classification", model=model_name, device=device)

# --- 2. POBIERANIE DANYCH RYNKOWYCH ---
def get_market_data(ticker_yahoo):
    try:
        stock = yf.Ticker(ticker_yahoo)
        hist = stock.history(period="2y", auto_adjust=False)
        
        if hist.empty:
            return None, None, None, None

        hist.index = hist.index.tz_localize(None)
        current_price = hist['Close'].iloc[-1]
        
        def get_price_at_date(target_date):
            past_data = hist[hist.index <= target_date]
            if not past_data.empty:
                return past_data['Close'].iloc[-1]
            return None

        # Obliczanie zwrotów
        year_end_date = datetime(hist.index[-1].year - 1, 12, 31)
        price_ytd = get_price_at_date(year_end_date)
        ret_ytd = ((current_price / price_ytd) - 1) * 100 if price_ytd else 0.0

        date_1m = hist.index[-1] - timedelta(days=30)
        price_1m = get_price_at_date(date_1m)
        ret_1m = ((current_price / price_1m) - 1) * 100 if price_1m else 0.0

        date_1r = hist.index[-1] - timedelta(days=365)
        price_1r = get_price_at_date(date_1r)
        ret_1r = ((current_price / price_1r) - 1) * 100 if price_1r else 0.0

        return round(current_price, 2), [round(ret_1m, 2), round(ret_1r, 2), round(ret_ytd, 2)], hist, None

    except Exception as e:
        st.error(f"Błąd Yahoo Finance: {e}")
        return None, [0, 0, 0], None, None

# --- 3. SCRAPING NEWSÓW ---
def get_news(ticker_bankier):
    url = f"https://www.bankier.pl/gielda/notowania/akcje/{ticker_bankier}/wiadomosci"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    news_list = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.select_one('#boxNews') or soup.select_one('#col-main') or soup.body
            
            if main_content:
                all_links = main_content.find_all('a', href=True)
                seen_titles = set()
                
                # Licznik do pomijania pierwszego newsa
                found_count = 0
                
                for link in all_links:
                    href = link['href']
                    raw_text = link.get_text(strip=True)
                    
                    is_news = '/wiadomosc/' in href or '/gielda/wiadomosci/' in href
                    
                    if is_news and len(raw_text) > 10 and raw_text not in seen_titles:
                        # 1. POMIJANIE PIERWSZEGO
                        found_count += 1
                        if found_count == 1: continue

                        # 2. PARSOWANIE DATY I TYTUŁU
                        # Domyślne wartości
                        date = "Dzisiaj"
                        title = raw_text

                        # Szukamy wzorca: YYYY-MM-DD GG:MM Tytuł
                        # Np.: "2026-02-03 13:06PKO BP..."
                        match = re.search(r'(\d{4}-\d{2}-\d{2})\s*\d{2}:\d{2}\s*(.*)', raw_text)
                        
                        if match:
                            date = match.group(1)  # Wyciągamy samą datę (2026-02-03)
                            title = match.group(2) # Wyciągamy tytuł bez daty i godziny
                        
                        full_link = "https://www.bankier.pl" + href if href.startswith("/") else href
                        
                        # (Opcjonalnie) Jeśli regex nie zadziałał, próbujemy szukać w tagach HTML jako fallback
                        if date == "Dzisiaj":
                            parent = link.find_parent()
                            if parent:
                                time_tag = parent.find('time') or parent.find('span', class_='date')
                                if not time_tag:
                                     grandparent = parent.find_parent()
                                     if grandparent:
                                         time_tag = grandparent.find('time') or grandparent.find('span', class_='date')
                                if time_tag:
                                    t_text = time_tag.get_text(strip=True)
                                    if len(t_text) >= 10 and t_text[4] == '-':
                                        date = t_text[:10]

                        news_list.append({"Title": title, "Date": date, "Link": full_link})
                        seen_titles.add(raw_text) # Dodajemy pełny tekst do unikania duplikatów
                        
                        if len(news_list) >= 10: break
    except Exception:
        pass
    return pd.DataFrame(news_list)

# --- 4. SENTYMENT SII (NOWY MODUŁ) ---
@st.cache_data(ttl=3600) 
def get_sii_sentiment():
    """
    Pobiera dane z Excela SII bazując na logice z web_scrap_mood_index.
    Zwraca ostatnią wartość z 6. kolumny (indeks 5).
    """
    base_url = "https://www.sii.org.pl"
    page_url = base_url + "/3438/analizy/nastroje-inwestorow.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(page_url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            link_tag = soup.select_one("a[href$='.xlsx']")

            if link_tag:
                relative_link = link_tag['href']
                if relative_link.startswith("http"):
                    excel_url = relative_link
                else:
                    excel_url = base_url + relative_link
                
                r_file = requests.get(excel_url, headers=headers, verify=False, timeout=15)

                if r_file.status_code == 200:
                    # Wczytujemy kolumny A:G
                    df = pd.read_excel(BytesIO(r_file.content), header=2, usecols="A:G")
                    
                    n = df.shape[0]
                    df = df.rename(columns={"Unnamed: 0": "Data"})
                    
                    if n > 4:
                        df = df.drop([n-1, n-2, n-3, n-4])
                    
                    df['Data'] = pd.to_datetime(df['Data'])
                    
                    latest_row = df.iloc[-1]
                    date_val = latest_row.iloc[0]
                    
                    # Kolumna F (Indeks 5) - Indeks Nastrojów
                    raw_value = latest_row.iloc[5]
                    
                    if isinstance(date_val, pd.Timestamp):
                        date_str = date_val.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_val)

                    # Normalizacja (ułamek vs procent)
                    sentiment_index = raw_value
                    if isinstance(sentiment_index, (int, float)) and abs(sentiment_index) < 1.5 and sentiment_index != 0:
                        sentiment_index = sentiment_index * 100
                    
                    return round(sentiment_index, 1), f"Odczyt z dn. {date_str}"
            
            return 0, "Brak pliku Excel"
        else:
            return 0, "Błąd pobierania SII"
            
    except Exception as e:
        return 0, f"Błąd SII: {str(e)}"

# --- 5. ANALIZA SENTYMENTU (DOSTOSOWANA DO SZYBKIEGO MODELU) ---
def analyze_market(news_df, current_price):
    if news_df.empty: 
        return 50, current_price, 0, news_df
    
    classifier = load_model()
    
    # Lista tytułów do analizy
    titles = news_df['Title'].tolist()
    
    # Nowy model nie potrzebuje candidate_labels
    results = classifier(titles)
    
    # Jeśli results to pojedynczy słownik, zamień na listę
    if isinstance(results, dict): results = [results]

    sentiment_labels = []
    score_sum_for_gauge = 0
    company_rating_sum = 0
    
    for res in results:
        # Ten model zwraca etykiety: "positive", "negative", "neutral"
        label = res['label']
        
        if label == "positive":
            label_short = "LABEL_2" # Kod dla koloru zielonego w Twoim UI
            score_sum_for_gauge += 1
            company_rating_sum += 1.0
        elif label == "negative":
            label_short = "LABEL_0" # Kod dla czerwonego
            score_sum_for_gauge -= 1
            # 0 pkt do oceny
        else:
            label_short = "LABEL_1" # Kod dla szarego
            company_rating_sum += 0.5
            
        sentiment_labels.append(label_short)

    news_df['Sentiment_Label'] = sentiment_labels

    # Skalowanie (Gauge 0-100)
    # Zakładamy max 10 newsów. Mnożnik 8 daje zakres +/- 80 pkt wokół 50.
    normalized_score = 50 + (score_sum_for_gauge * 8)
    normalized_score = max(5, min(95, normalized_score))
    
    # Cena Docelowa
    impact = (normalized_score - 50) / 200
    target_price = current_price * (1 + impact)
    
    # Ocena (0-10)
    company_rating = round(company_rating_sum, 1)
    
    return normalized_score, round(target_price, 2), company_rating, news_df

# --- 6. ZAAWANSOWANY WSKAŹNIK HYBRYDOWY ---
# --- 6. ZAAWANSOWANY WSKAŹNIK HYBRYDOWY ---
def calculate_advanced_score(news_df, returns_1m, returns_1y, sii_val, current_price):
    """
    Oblicza Wskaźnik Hybrydowy (0-10) oraz Cenę Docelową.
    """
    # ... (kod obliczania newsów, ceny i rynku bez zmian - skopiuj go ze starej funkcji) ...
    
    # --- 1. NEWS SCORE (Waga 50%) ---
    ai_raw_score = 0
    limit = min(10, len(news_df))
    if limit > 0:
        impactful_news = news_df.iloc[:limit]
        for label in impactful_news['Sentiment_Label']:
            if label == 'LABEL_2': ai_raw_score += 1
            elif label == 'LABEL_0': ai_raw_score -= 1
    max_poss_score = max(1, limit) 
    score_news = ((ai_raw_score + max_poss_score) / (2 * max_poss_score)) * 10
    
    # --- 2. PRICE SCORE (Waga 30%) ---
    score_1m = max(0, min(10, 5 + (returns_1m * 0.2)))
    score_1y = max(0, min(10, 5 + (returns_1y * 0.05)))
    score_price = (score_1m * 0.6) + (score_1y * 0.4)
    
    # --- 3. MARKET SCORE (Waga 20%) ---
    score_market = max(0, min(10, 5 + (sii_val / 20)))
    
    # --- FINALNA OCENA (0-10) ---
    final_score = (score_news * 0.50) + (score_price * 0.30) + (score_market * 0.20)
    
    # --- CENA DOCELOWA ---
    # Logika: Neutralnie (5.0) = 0% zmiany. 
    # Każdy 1 pkt różnicy od 5.0 to 3% zmiany ceny.
    # Max potencjał (przy ocenie 10) = +15%. Min (przy 0) = -15%.
    impact_per_point = 0.03 # 3%
    price_change_pct = (final_score - 5.0) * impact_per_point
    target_price = current_price * (1 + price_change_pct)
    
    return round(final_score, 1), round(target_price, 2)

# --- STYLIZACJA CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .returns-box {
        background: linear-gradient(180deg, #1c202a 0%, #1e3a8a 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #3b82f6;
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        display: flex; align-items: center; justify-content: space-between; font-family: sans-serif;
    }
    .kpi-card {
        background-color: #1c202a; border: 1px solid #2d3446; border-radius: 12px;
        padding: 10px; text-align: center; height: 160px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .kpi-label { font-size: 11px; color: #8b949e; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; font-weight: 600; }
    .kpi-value-big { font-size: 24px; font-weight: bold; color: white; }
    .kpi-sub { font-size: 13px; color: #6b7280; margin-top: 5px; }
    .block-container { padding-top: 2rem; }
    .streamlit-expanderHeader { background-color: #1c202a; color: #8b949e; border-radius: 8px; }
            
    /* CIEMNY MOTYW: Selectbox - TOTALNE WYMUSZENIE SZAROŚCI */
    
    /* 1. Belka główna (zamknięta) */
    div[data-baseweb="select"] > div {
        background-color: #1c202a !important;
        color: white !important;
        border: 1px solid #2d3446 !important;
        border-radius: 8px !important;
    }
    
    /* 2. Ikona strzałki */
    div[data-baseweb="select"] svg {
        fill: #8b949e !important;
    }

    /* 3. WNĘTRZE LISTY ROZWIJANEJ (To naprawia białe tło) */
    /* Kontener listy */
    ul[data-baseweb="menu"] {
        background-color: #1c202a !important;
        border: 1px solid #2d3446 !important;
    }
    
    /* Puste miejsca w kontenerze popovera */
    div[data-baseweb="popover"] > div {
        background-color: #1c202a !important;
    }

    /* 4. OPCJE NA LIŚCIE */
    li[data-baseweb="option"] {
        background-color: #1c202a !important; /* Każda opcja ma szare tło */
        color: white !important;              /* Biały tekst */
    }

    /* 5. OPCJA NAJECHANA (HOVER) I WYBRANA */
    li[data-baseweb="option"]:hover,
    li[data-baseweb="option"][aria-selected="true"] {
        background-color: #2d3446 !important; /* Jaśniejszy szary dla kontrastu */
        color: #4ade80 !important;            /* Zielony tekst */
    }
    
    /* CIEMNY MOTYW: Expander - TOTALNA NAPRAWA */
    
    /* Kontener główny (zamknięty i otwarty) */
    details {
        background-color: #1c202a !important;
        border: 1px solid #2d3446 !important;
        border-radius: 8px !important;
        color: #8b949e !important;
    }

    /* Nagłówek (klikana belka) - wymuszenie koloru w każdym możliwym stanie */
    summary, 
    summary:hover, 
    summary:focus, 
    summary:active,
    details[open] > summary,
    details:focus-within > summary {
        background-color: #1c202a !important;
        color: #8b949e !important;
        border-radius: 8px !important;
        transition: none !important; /* Wyłącza błyskanie przy zmianie */
    }

    /* Naprawa koloru strzałki */
    summary svg {
        fill: #8b949e !important;
        color: #8b949e !important;
    }

    /* Treść w środku po rozwinięciu */
    details > div {
        background-color: #0e1117 !important;
        color: white !important;
        border-top: 1px solid #2d3446;
    }
    
    /* Ukrycie domyślnego obramowania focusu przeglądarki */
    summary:focus-visible {
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- WYKRESY ---
def create_price_chart_real(hist_data):
    fig = go.Figure()
    one_year_ago = datetime.now() - timedelta(days=365)
    plot_data = hist_data[hist_data.index >= one_year_ago]
    
    # 1. Obliczamy zakresy
    min_y = plot_data['Close'].min() * 0.95
    max_y = plot_data['Close'].max() * 1.05  # Dajemy 5% luzu u góry
    
    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['Close'], fill='tozeroy', mode='lines', line=dict(color='#3b82f6', width=2), fillcolor='rgba(59, 130, 246, 0.1)'))
    
    fig.update_layout(
        title="WYKRES CENY (1R)", 
        title_font_color="#8b949e", 
        title_font_size=12, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=0, r=0, t=30, b=0), 
        xaxis=dict(showgrid=False, tickfont=dict(color='#8b949e')), 
        # 2. Ustawiamy zakres osi Y
        yaxis=dict(
            range=[min_y, max_y],
            showgrid=True, 
            gridcolor='#2d3446', 
            tickfont=dict(color='#8b949e')
        ), 
        height=250
    )
    return fig
    fig = go.Figure()
    one_year_ago = datetime.now() - timedelta(days=365)
    plot_data = hist_data[hist_data.index >= one_year_ago]
    fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['Close'], fill='tozeroy', mode='lines', line=dict(color='#3b82f6', width=2), fillcolor='rgba(59, 130, 246, 0.1)'))
    fig.update_layout(title="WYKRES CENY (1R)", title_font_color="#8b949e", title_font_size=12, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, tickfont=dict(color='#8b949e')), yaxis=dict(showgrid=True, gridcolor='#2d3446', tickfont=dict(color='#8b949e')), height=250)
    return fig

def create_pro_sentiment_gauge(value, source_text=""):
    """
    Tworzy wykres Gauge w stylu nowoczesnym (Vivid/Dark Mode). Skala: -70 do +70.
    """
    # NOWOCZESNA PALETA KOLORÓW (VIVID)
    c_ext_bear = "#FF004D"  # Neonowy Czerwony
    c_bear     = "#FF6B6B"  # Jasny Czerwony
    c_neutral  = "#4B5563"  # Chłodny Szary
    c_bull     = "#4ADE80"  # Jasny Zielony
    c_ext_bull = "#00E054"  # Neonowy Zielony
    
    # Logika etykiet
    if value < -45:
        label_text = "SKRAJNY PESYMIZM"
        label_color = c_ext_bear
    elif value < -15:
        label_text = "PESYMIZM"
        label_color = c_bear
    elif value > 45:
        label_text = "SKRAJNY OPTYMIZM"
        label_color = c_ext_bull
    elif value > 15:
        label_text = "OPTYMIZM"
        label_color = c_bull
    else:
        label_text = "NEUTRALNIE"
        label_color = "#9ca3af"

    fig = go.Figure(go.Indicator(
        mode = "gauge",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'shape': "angular",
            'axis': {
                'range': [-70, 70], 
                'visible': True, 
                'tickvals': [-70, -45, -15, 15, 45, 70],
                'ticktext': ['-70', '-45', '-15', '15', '45', '70'],
                'tickfont': {'size': 10, 'color': '#6b7280'},
                'tickwidth': 0,
            },
            'bar': {'color': "rgba(0,0,0,0)", 'thickness': 0},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [-70, -45], 'color': c_ext_bear},
                {'range': [-45, -15], 'color': c_bear},
                {'range': [-15, 15],  'color': c_neutral},
                {'range': [15, 45],   'color': c_bull},
                {'range': [45, 70],   'color': c_ext_bull}
            ],
            'threshold': {'line': {'color': "white", 'width': 5}, 'thickness': 0.8, 'value': value}
        }
    ))

    annotations = [
        dict(x=0.5, y=1.15, text="INDEKS NASTROJÓW INWESTORÓW (SII)", showarrow=False, font=dict(color="#9ca3af", size=10)), 
        dict(x=0.5, y=0.25, text=f"{value:+.1f}%", showarrow=False, font=dict(color="white", size=36, weight="bold")),
        dict(x=0.5, y=0.10, text=label_text, showarrow=False, font=dict(color=label_color, size=14, weight="bold")),
        dict(x=0.5, y=-0.1, text=source_text, showarrow=False, font=dict(color="#4b5563", size=9))
    ]
    
    fig.update_layout(
        annotations=annotations, height=280, margin=dict(l=25, r=25, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)', font={'family': "Arial, sans-serif"}
    )
    return fig

# --- GŁÓWNA LOGIKA APLIKACJI ---

# Zmieniamy proporcje na [1.2, 1.8], żeby logo było wyraźniejsze
col_title, col_select = st.columns([1.2, 1.8])

with col_title:
    # Zamiast st.title używamy st.image
    # use_container_width=True sprawi, że logo dopasuje się do szerokości kolumny
    try:
        st.image("src/logo.png", use_container_width=True)
    except:
        # Zapasowo wyświetli tekst, jeśli zapomnisz wrzucić pliku
        st.title("GPW SENTIX AI")

with col_select:
    # Opcjonalnie: Dodajemy margines, żeby wyrównać listę do środka logo w pionie
    st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
    
    selected_name = st.selectbox("Wybierz spółkę", list(COMPANIES.keys()), label_visibility="collapsed")
    ticker_yahoo = COMPANIES[selected_name]["yahoo"]
    ticker_bankier = COMPANIES[selected_name]["bankier"]

with st.spinner(f'Pobieranie danych dla {selected_name}...'):
    # 1. Dane Rynkowe
    price, returns, hist_data, _ = get_market_data(ticker_yahoo)
    # 2. Newsy i AI
    df_raw = get_news(ticker_bankier)
    # 3. Sentyment SII
    sii_val, sii_desc = get_sii_sentiment()
    
    if price is not None:
        # Analiza AI (pobieramy tylko newsy i sentyment, ignorujemy starą cenę docelową z tej funkcji)
        sentiment_score, _, _, df_news = analyze_market(df_raw, price)
        
        # --- NOWE OBLICZENIE OCENY I CENY DOCELOWEJ ---
        company_rating, target_price = calculate_advanced_score(df_news, returns[0], returns[1], sii_val, price)
        
        # Obliczenie potencjału procentowego do nowej ceny docelowej
        upside_pct = ((target_price - price) / price) * 100
    else:
        st.error("Nie udało się pobrać danych rynkowych.")
        st.stop()

# Layout
left_col, right_col = st.columns([1, 1.8])

with left_col:
    # Panel Cenowy
    c_1m = "#4ade80" if returns[0] >= 0 else "#ef4444"
    c_1r = "#4ade80" if returns[1] >= 0 else "#ef4444"
    c_ytd = "#4ade80" if returns[2] >= 0 else "#ef4444"

    st.markdown(f"""
    <div class="returns-box">
        <div style="text-align: left; width: 45%;">
            <div style="font-size: 11px; color: #93c5fd; margin-bottom: 5px; text-transform: uppercase;">Kurs Aktualny</div>
            <div style="font-size: 32px; font-weight: bold; color: white;">{price} PLN</div>
        </div>
        <div style="width: 1px; height: 50px; background-color: #3b82f6; opacity: 0.4;"></div>
        <div style="text-align: right; width: 45%;">
            <div style="font-size: 11px; color: #93c5fd; margin-bottom: 5px; text-transform: uppercase;">Zwroty (1M/1R/YTD)</div>
            <div style="font-size: 14px; font-weight: bold;">
                <span style="color:{c_1m}">{returns[0]:+}%</span> | <span style="color:{c_1r}">{returns[1]:+}%</span> | <span style="color:{c_ytd}">{returns[2]:+}%</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    
    # Wykres Ceny
    st.plotly_chart(create_price_chart_real(hist_data), use_container_width=True, config={'displayModeBar': False})
    
    # NOWY Sentyment SII (Zastępuje stary gauge)
    st.plotly_chart(create_pro_sentiment_gauge(sii_val, sii_desc), use_container_width=True, config={'displayModeBar': False})

with right_col:
    kpi1, kpi2, kpi3 = st.columns(3)
    
    # Logika: Tekst, Kolor i Strzałka w zależności od wyniku
    if sentiment_score > 60:
        rec_text = "KUPUJ"
        rec_col = "#4ade80"  # Zielony
        rec_arrow = "↗"      # Strzałka wzrostowa
    elif sentiment_score < 40:
        rec_text = "SPRZEDAJ"
        rec_col = "#ef4444"  # Czerwony
        rec_arrow = "↘"      # Strzałka spadkowa (możesz też użyć "↓")
    else:
        rec_text = "TRZYMAJ"
        rec_col = "#9ca3af"  # Szary
        rec_arrow = "→"      # Strzałka pozioma

    with kpi1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Rekomendacja</div>
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span style="font-size: 32px; color: {rec_col}; line-height: 1;">{rec_arrow}</span>
                    <span class="kpi-value-big" style="color: {rec_col};">{rec_text}</span>
                </div>
                <div class="kpi-sub">Analiza AI</div>
            </div>""", unsafe_allow_html=True)

    # --- Reszta kodu bez zmian (kpi2, kpi3...) ---
    with kpi2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Cena Docelowa (AI)</div><div class="kpi-value-big">{target_price} PLN</div><div class="kpi-sub">Potencjał: <span style="color: {'#4ade80' if upside_pct>0 else '#ef4444'}; font-weight: bold;">{upside_pct:+.2f}%</span></div></div>""", unsafe_allow_html=True)
    with kpi3:
        # Dynamiczny kolor paska w zależności od oceny
        if company_rating < 4: score_color = "#ef4444"   # Czerwony
        elif company_rating < 6: score_color = "#9ca3af" # Szary
        else: score_color = "#4ade80"                    # Zielony

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Ocena Spółki (0-10)</div>
                <div style="position: relative; width: 100px; height: 50px; margin-top: 10px;">
                    <svg viewBox="0 0 100 50" width="100" height="50">
                        <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#2d3446" stroke-width="8" stroke-linecap="round"/>
                        <path d="M 10 50 A 40 40 0 0 1 75 20" fill="none" stroke="{score_color}" stroke-width="8" stroke-linecap="round" 
                              stroke-dasharray="{company_rating * 10}, 100" />
                    </svg>
                    <div style="position: absolute; top: 25px; left: 0; width: 100%; text-align: center; font-size: 20px; font-weight: bold; color: {score_color};">
                        {company_rating}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"#### Najnowsze wiadomości: {selected_name}")
    
    if not df_news.empty:
        def display_news_row(row, idx):
            label = row.get('Sentiment_Label', 'LABEL_1')
            if label == 'LABEL_2': icon, color = "+", "#4ade80"
            elif label == 'LABEL_0': icon, color = "−", "#ef4444"
            else: icon, color = "•", "#9ca3af"

            st.markdown(f"""
                <div style="padding: 10px 0; border-bottom: 1px solid #2d3446; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex-grow: 1;">
                        <span style="color: #3b82f6; font-weight: bold; margin-right: 5px;">{idx+1}.</span> 
                        <a href="{row['Link']}" target="_blank" style="color: white; text-decoration: none; font-size: 15px;">{row['Title']}</a>
                        <span style="color: #6b7280; font-size: 12px; margin-left: 10px;">{row['Date']}</span>
                    </div>
                    <div style="color: {color}; font-weight: bold; font-size: 20px; margin-left: 15px; width: 20px; text-align: center;">{icon}</div>
                </div>""", unsafe_allow_html=True)

        for idx, row in df_news.iloc[:3].iterrows():
             display_news_row(row, idx)
        
        if len(df_news) > 3:
            with st.expander("Zobacz starsze wiadomości"):
                for idx, row in df_news.iloc[3:10].iterrows():
                     display_news_row(row, idx)
    else:
        st.info("Brak newsów.")