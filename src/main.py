from model import model
from web_scrap import web_scrap_multiple_pages, get_GPW, web_scrap
from ui import ui

def main():
    df_news = web_scrap_multiple_pages(pages=10)

    results = model(df_news['Title'].tolist())
    df_news['Label'] = [result['label'] for result in results]
    df_news['Score'] = [result['score'] for result in results]
    print(df_news)

    df_GPW = get_GPW(url="https://www.bankier.pl/gielda/notowania/akcje")
    print("Giełda Papierów Wartościowych")
    print(df_GPW.head(5))

    ui(df_news)



if __name__ == "__main__":
    main()
