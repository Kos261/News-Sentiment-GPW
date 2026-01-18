import pandas as pd
from transformers import pipeline

model = pipeline("text-classification", model="bardsai/twitter-sentiment-pl-base")

if __name__ == "__main__":
    df_news = pd.DataFrame([
    {"Title":"Spółka zanotowała świetne wyniki i duży spadek jakości."},
    {"Title":"Niestety, inflacja zjada zyski, a kurs akcji rośnie."},
    {"Title":"Zarząd ogłosił beznadziejne wyniki za kwartał."}
    ])

    results = model(df_news['Title'].tolist())
    df_news['Label'] = [result['label'] for result in results]
    df_news['Score'] = [result['score'] for result in results]

    print(df_news)