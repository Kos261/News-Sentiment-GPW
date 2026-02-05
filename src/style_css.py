style_css = """
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
"""