import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from textblob import TextBlob
import cleantext
import nltk

def main():
    print("Hello from news-sentiment-gpw!")
    dic = {"A":1, "B":2, "C":3, "D":4, "E":5}
    df = pd.DataFrame(dic.items())
    print(df.head())

def ui():
    st.header("News Sentiment Analysis")
    with st.expander("Analyze text"):
        text = st.text_area("Your text: ")
        if text:
            blob = TextBlob(text)
            st.write('Polarity: ', round(blob.sentiment.polarity, 2))
            st.write('Subjectivity: ', round(blob.sentiment.subjectivity, 2))



if __name__ == "__main__":
    # main()
    ui()