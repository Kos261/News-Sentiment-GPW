import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="GPW.NEXUS", layout="wide", initial_sidebar_state="collapsed")

# --- LISTA SPÓŁEK ---
WIG20_TICKERS = [
    "PKOBP", "PKNORLEN", "KGHM", "PEKAO", "PZU", 
    "LPP", "SANPL", "ALLEGRO", "DINOPL", "CDPROJEKT", 
    "MBANK", "ALIOR", "KETY", "ZABKA", "BUDIMEX", 
    "PGE", "KRUK", "ORANGEPL", "CCC", "PEPCO"
]

# --- STYLIZACJA CSS ---
st.markdown("""
    <style>
    /* Ogólne ustawienia aplikacji */
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    
    /* LEWA STRONA: Box zwrotów i ceny */
    .returns-box {
        background: linear-gradient(180deg, #1c202a 0%, #1e3a8a 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #3b82f6;
        font-family: 'Source Sans Pro', sans-serif;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* PRAWA STRONA: Styl dla 3 identycznych ramek KPI */
    .kpi-card {
        background-color: #1c202a;
        border: 1px solid #2d3446;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        height: 160px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .kpi-label {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    .kpi-value-big {
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    
    .kpi-sub {
        font-size: 13px;
        color: #6b7280;
        margin-top: 5px;
    }

    /* Usunięcie marginesu górnego */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Stylizacja nagłówka expandera */
    .streamlit-expanderHeader {
        background-color: #1c202a;
        color: #8b949e;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE ---

def get_simulated_prices(ticker):
    random.seed(ticker)
    base_price = random.uniform(10000, 18000) if ticker == "LPP" else random.uniform(20, 400)
    current_price = base_price * random.uniform(0.95, 1.05)
    target_price = current_price * random.uniform(1.05, 1.30) 
    upside_pct = ((target_price - current_price) / current_price) * 100
    return round(current_price, 2), round(target_price, 2), round(upside_pct, 2)

def create_price_chart(current_price):
    dates = pd.date_range(start="2023-01-01", periods=100)
    prices = np.linspace(current_price * 0.8, current_price, 100) + np.random.randn(100) * (current_price * 0.02)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        fill='tozeroy', 
        mode='lines',
        line=dict(color='#3b82f6', width=2),
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    fig.update_layout(
        title="WYKRES CENY (1R)",
        title_font_color="#8b949e",
        title_font_size=12,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False, tickfont=dict(color='#8b949e')),
        yaxis=dict(showgrid=True, gridcolor='#2d3446', tickfont=dict(color='#8b949e')),
        height=250
    )
    return fig

def create_pro_sentiment_gauge(value):
    """
    Tworzy nowoczesny, minimalistyczny wykres sentymentu (bez zbędnych opisów na łuku).
    """
    # Kolory dopasowane do Dark Mode
    color_bearish = "#ef4444"  # Czerwony
    color_neutral = "#374151"  # Ciemnoszary
    color_bullish = "#22c55e"  # Zielony
    color_needle = "#ffffff"   # Biała wskazówka
    
    # Etykieta tekstowa na podstawie wartości
    if value < 33:
        label_text = "NEGATYWNY"
        label_color = color_bearish
    elif value < 66:
        label_text = "NEUTRALNY"
        label_color = "#9ca3af" # Jasnoszary
    else:
        label_text = "POZYTYWNY"
        label_color = color_bullish

    fig = go.Figure(go.Indicator(
        mode = "gauge",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'shape': "angular", # Kształt półkola
            'axis': {'range': [0, 100], 'visible': False}, # Ukrywamy oś z liczbami
            'bar': {'color': "rgba(0,0,0,0)", 'thickness': 0}, # Ukrywamy pasek postępu
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            # Definicja stref kolorystycznych
            'steps': [
                {'range': [0, 33.3], 'color': color_bearish},
                {'range': [33.3, 66.6], 'color': color_neutral},
                {'range': [66.6, 100], 'color': color_bullish}
            ],
            # Styl wskazówki
            'threshold': {
                'line': {'color': color_needle, 'width': 4}, 
                'thickness': 0.75, 
                'value': value
            }
        }
    ))

    # Adnotacje tekstowe (Tylko tytuł, wartość i główny status)
    annotations = [
        # Główny tytuł
        dict(x=0.5, y=1.2, text="SENTYMENT RYNKU", showarrow=False, font=dict(color="#8b949e", size=12)),
        
        # Wartość liczbowa w środku
        dict(x=0.5, y=0.25, text=f"{value}", showarrow=False, font=dict(color="white", size=30, weight="bold")),
        
        # Opis słowny pod liczbą (np. POZYTYWNY)
        dict(x=0.5, y=0.10, text=label_text, showarrow=False, font=dict(color=label_color, size=14, weight="bold"))
    ]
    
    # Dodanie "Pivot Point" (kropki w środku wskazówki)
    # fig.add_shape(
    #     type="circle",
    #     xref="paper", yref="paper",
    #     x0=0.47, y0=0.22, x1=0.53, y1=0.28, # Wyśrodkowana kropka
    #     fillcolor="#1c202a", 
    #     line=dict(color=color_needle, width=2)
    # )
    
    fig.update_layout(
        annotations=annotations,
        height=260, 
        margin=dict(l=30, r=30, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)', 
        font={'family': "Arial, sans-serif"}
    )
    return fig

# --- UKŁAD STRONY ---

# 1. Nagłówek i Wybór Spółki
col_title, col_select = st.columns([1, 2])
with col_title:
    st.title("GPW.NEXUS")
with col_select:
    selected_ticker = st.selectbox("Wybierz spółkę z WIG20", WIG20_TICKERS, label_visibility="collapsed")

# Pobranie danych
cur_price, tar_price, upside = get_simulated_prices(selected_ticker)
random.seed(selected_ticker)
sentiment_val = random.randint(25, 95) 

# 2. Główny podział
left_col, right_col = st.columns([1, 1.8])

# --- LEWA KOLUMNA ---
with left_col:
    # A. Panel Kursu i Zwrotów (HTML bez wcięć)
    html_left_panel = f"""
<div class="returns-box">
<div style="text-align: left; width: 45%;">
<div style="font-size: 11px; color: #93c5fd; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;">Kurs Aktualny</div>
<div style="font-size: 32px; font-weight: bold; color: white;">{cur_price} PLN</div>
</div>
<div style="width: 1px; height: 50px; background-color: #3b82f6; opacity: 0.4;"></div>
<div style="text-align: right; width: 45%;">
<div style="font-size: 11px; color: #93c5fd; margin-bottom: 5px; text-transform: uppercase;">Zwroty (1M/1R/YTD)</div>
<div style="font-size: 14px; font-weight: bold;">
<span style="color:#4ade80">+5.4%</span> | 
<span style="color:#ef4444">-2.1%</span> | 
<span style="color:#4ade80">+8.9%</span>
</div>
</div>
</div>"""
    
    st.markdown(html_left_panel, unsafe_allow_html=True)
    
    # B. Wykres Ceny
    st.plotly_chart(create_price_chart(cur_price), use_container_width=True, config={'displayModeBar': False})
    
    # C. Sentyment (Zmodernizowany - Czysty)
    st.plotly_chart(create_pro_sentiment_gauge(sentiment_val), use_container_width=True, config={'displayModeBar': False})

# --- PRAWA KOLUMNA ---
with right_col:
    # KPI - 3 Identyczne Ramki
    kpi1, kpi2, kpi3 = st.columns(3)
    
    # Ramka 1: Rekomendacja
    with kpi1:
        st.markdown("""
            <div class="kpi-card">
                <div class="kpi-label">Rekomendacja</div>
                <div style="font-size: 38px; color: #4ade80; line-height: 1;">↗</div>
                <div class="kpi-value-big" style="color: #4ade80;">KUPUJ</div>
                <div class="kpi-sub">Silna rekomendacja</div>
            </div>
        """, unsafe_allow_html=True)

    # Ramka 2: Cena Docelowa
    with kpi2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Cena Docelowa</div>
                <div class="kpi-value-big">{tar_price} PLN</div>
                <div class="kpi-sub">
                    Potencjał: <span style="color: #4ade80; font-weight: bold;">+{upside}%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Ramka 3: Ocena (SVG)
    with kpi3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Ocena Spółki</div>
                <div style="position: relative; width: 100px; height: 50px; margin-top: 10px;">
                    <svg viewBox="0 0 100 50" width="100" height="50">
                        <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#2d3446" stroke-width="8" stroke-linecap="round"/>
                        <path d="M 10 50 A 40 40 0 0 1 75 20" fill="none" stroke="#4ade80" stroke-width="8" stroke-linecap="round" />
                    </svg>
                    <div style="position: absolute; top: 25px; left: 0; width: 100%; text-align: center; font-size: 20px; font-weight: bold; color: #4ade80;">
                        8/10
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- NEWSY ---
    st.markdown(f"#### Wydarzenia Rynkowe: {selected_ticker}")
    
    titles_pool = [
        "Znakomite wyniki kwartalne spółki", "Obawy o inflację wpływają na sektor",
        "Nowa strategia dywidendowa zatwierdzona", "Prezes ogłasza rezygnację z końcem roku",
        "Rekomendacja 'Przeważaj' od dużego banku", "Fuzja z zagranicznym podmiotem wstrzymana",
        "Rekordowa produkcja w zakładach", "Zmiany w prawie energetycznym a zyski",
        "Analiza techniczna: przełamanie oporu", "Inwestycje w nowe technologie"
    ]
    
    all_news = []
    for i in range(10):
        title = random.choice(titles_pool)
        date = (datetime.now() - timedelta(days=i*2)).strftime('%Y-%m-%d')
        msg_type = random.choice(["positive", "negative", "neutral"])
        
        color = "#4ade80" if msg_type == "positive" else ("#ef4444" if msg_type == "negative" else "#9ca3af")
        icon = "+" if msg_type == "positive" else ("−" if msg_type == "negative" else "•")
        
        all_news.append({"id": i+1, "title": title, "date": date, "color": color, "icon": icon})

    def display_news_item(item):
        col_txt, col_icon = st.columns([5, 0.5])
        with col_txt:
            st.markdown(f"""
                <div style="font-size: 16px;">
                    <span style="color: #3b82f6; font-weight: bold;">{item['id']}.</span> 
                    {item['title']} <span style="color: #6b7280; font-size: 12px;">({item['date']})</span>
                </div>
            """, unsafe_allow_html=True)
        with col_icon:
            st.markdown(f"<div style='color: {item['color']}; font-size: 20px; font-weight: bold; text-align: right;'>{item['icon']}</div>", unsafe_allow_html=True)
        st.divider()

    for i in range(3):
        display_news_item(all_news[i])

    with st.expander("Zobacz starsze wiadomości"):
        for i in range(3, len(all_news)):
             display_news_item(all_news[i])