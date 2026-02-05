import pandas as pd
from transformers import pipeline
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

bardai = pipeline(
    "text-classification",
    model="bardsai/twitter-sentiment-pl-base",
    device=1   # <<< GPU (0 = pierwsza karta)
)

if __name__ == "__main__":
    df_news = pd.DataFrame([
        {"Title":"Spółka zanotowała świetne wyniki i duży spadek jakości."},
        {"Title":"Niestety, inflacja zjada zyski, a kurs akcji rośnie."},
        {"Title":"Zarząd ogłosił beznadziejne wyniki za kwartał."}
    ])

    results =bardai(df_news['Title'].tolist())
    df_news['Label'] = [result['label'] for result in results]
    df_news['Score'] = [result['score'] for result in results]

    print(df_news)
