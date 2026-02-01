# News-Sentiment-GPW
Repository for statistical arbitration methods course on MIMUW


# Project requirements:

- tytuł
- streszczenie (może być na kolejne zajęcia, czyli 20/01)
- pytanie/pytania badawcze, na które chcecie znaleźć odpowiedź
- Url repozytorium kodu (może być na 20/01)
- Url aplikacji (może być na 20/01)
- diagram architektury aplikacji (może być na 20/01) -> jak to ma wyglądać? 
Chodzi o rysunek, na którym pokażecie 
jak zbudowane jest wasze rozwiązanie i jakie wykorzystuje technologie, serwisy 
(te oczywiście mogą, ale nie muszą pochodzić od IBM). 
- Dobre przykład znajdziecie np tu: https://cloud.ibm.com/docs/ContinuousDelivery?topic=ContinuousDelivery-tutorial-cd-vsi
![img.png](img.png)

## UV
To sync libraries use uv manager Download from: https://docs.astral.sh/uv/#__tabbed_1_2
In project directory type: 
```$ uv sync``` to get all dependencies

## PIP 
To sync dependencies with pip type: 
```$ pip install -r requirements.txt```

## HOW TO LAUNCH WEBSITE?
in project root type:

```streamlit run src/main.py```

or this if you use UV

```uv run streamlit run src/main.py```
