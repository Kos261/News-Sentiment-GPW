import streamlit as st
from textblob import TextBlob


def ui(df):
    st.header("News Sentiment Analysis")
    # with st.expander("Analyze text"):
    #     text = st.text_area("Your text: ")
    #     if text:
    #         blob = TextBlob(text)
    #         text, result = classify(model, text)
    #         label, score = result['label'], str(round(result['score'], 2))
    #
    #         pol = round(blob.sentiment.polarity, 2)
    #         sub = round(blob.sentiment.subjectivity, 2)
    #         st.write(text)
    #         st.write(f'Label: {label}, Score: {score}')
    #         st.write(f'Polarity: {pol}, Subjectivity: {sub}')

    st.dataframe(df)



if __name__ == "__main__":
    ui()