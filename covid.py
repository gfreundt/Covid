import os, shutil, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from datetime import datetime as dt
import time
import pandas as pd
import matplotlib.pyplot as plt
from statistics import mean
import tweepy


def set_options():
    options = WebDriverOptions()
    options.add_argument("--window-size=1440,810")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--silent")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return options


def download_file():
    if DOWNLOAD_FILE in os.listdir(DOWNLOAD_PATH):
        os.remove(os.path.join(DOWNLOAD_PATH, DOWNLOAD_FILE))
    url = "https://cloud.minsa.gob.pe/s/nqF2irNbFomCLaa/download"
    driver = webdriver.Chrome(
        os.path.join(WORKING_PATH, "chromedriver.exe"), options=set_options()
    )
    driver.get(url)
    while DOWNLOAD_FILE not in os.listdir(DOWNLOAD_PATH):
        time.sleep(10)
    driver.quit()
    shutil.copyfile(
        os.path.join(DOWNLOAD_PATH, DOWNLOAD_FILE),
        os.path.join(WORKING_PATH, DOWNLOAD_FILE),
    )


def load_and_prepare_data():
    # Read file, convert FECHA column to datetime, clip last NOTAIL records
    df = pd.read_csv(
        os.path.join(WORKING_PATH, DOWNLOAD_FILE), delimiter="|"
    ).sort_values("FECHA")
    df["FECHA"] = df["FECHA"].astype("datetime64[ns]")
    df = df[:-DF_NOTAIL]
    return df


def set_fallecidos_totales(df, departamento=None):
    if departamento:
        df = df.loc[lambda i: i["DEPARTAMENTO DOMICILIO"] == departamento]
        filename = departamento + ".jpg"
    else:
        filename = "peru.jpg"
    # New dataframe with INDEX, FECHA, CUENTA
    df = pd.DataFrame(
        {
            "FECHA": list(pd.unique(df["FECHA"])),
            "CUENTA": list(df["FECHA"].value_counts().sort_index(axis=0)),
        }
    )
    # List of values, cut start of dataframe in DF_NORMAL, replace CUENTA with rolling average of CUENTA
    cuentas = list(df["CUENTA"])
    df = df[DF_NORMAL:]
    df["CUENTA"] = [
        mean(cuentas[i : i + DF_NORMAL]) for i, _ in enumerate(df["CUENTA"])
    ]
    # Break dataset into graph for current and last 3 years
    plt.figure(figsize=(15, 6))
    current_year = dt.now().year
    current_month = dt.now().month
    xaxis_labels, xaxis_ticks = [], []
    for year in range(current_year - 2, current_year + 1):
        # define year startpoint and year endpoint
        year_startpoint, year_endpoint = dt(year, 1, 1), dt(year, 12, 31)
        # filter records for year
        dfx = df.loc[lambda i: i["FECHA"] >= year_startpoint].loc[
            lambda i: i["FECHA"] <= year_endpoint
        ]
        # add data series to graph
        plt.plot(dfx["FECHA"], dfx["CUENTA"])
        # add x-axis labels for the year
        m = min(current_month + 2, 13) if year == current_year else 13
        xaxis_labels += [f"{MESES_3[j-1]}/{str(year)[-2:]}" for j in range(1, m)]
        xaxis_ticks += [dt(year=year, month=i, day=1) for i in range(1, m)]
    # add y-axis labels
    max_y = max(df["CUENTA"])
    if max_y > 100:
        max_y *= 1.2
        jump = 100
    else:
        max_y = 100
        jump = 10
    yaxis_ticks = [i for i in range(0, int(max_y) + 1, jump)]
    yaxis_labels = [f"{i:,}" for i in yaxis_ticks]
    graph(filename, xaxis_labels, xaxis_ticks, yaxis_labels, yaxis_ticks, departamento)


def graph(filename, xaxis_labels, xaxis_ticks, yaxis_labels, yaxis_ticks, departamento):
    ax = plt.gca()
    ax.set_facecolor("#F5F1F5")
    ax.spines["bottom"].set_color("#DFD8DF")
    ax.spines["top"].set_color("#DFD8DF")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("#DFD8DF")
    plt.tick_params(axis="both", length=0)
    plt.xticks(
        ticks=xaxis_ticks, labels=xaxis_labels, rotation=90, color="#606060", fontsize=8
    )
    plt.yticks(ticks=yaxis_ticks, labels=yaxis_labels, color="#606060", fontsize=8)
    ax.set_ylim(bottom=0)
    plt.grid(color="#DFD8DF")

    if not departamento:
        departamento = "PERU"
    plt.title(
        departamento.upper()
        + "\nMuertes SINADEF al "
        + dt.strftime(dt.now(), f"%d - %m - %y"),
        loc="center",
        pad=10,
    )

    plt.savefig(
        os.path.join(GRAPH_PATH, filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()


def tweet():
    env = os.environ
    CONSUMER_KEY = env['TWITTER_CONSUMER_KEY']
    CONSUMER_SECRET = env['TWITTER_CONSUMER_KEY_SECRET']
    ACCESS_TOKEN = env['TWITTER_ACCESS_TOKEN']
    ACCESS_SECRET = env['TWITTER_ACCESS_TOKEN_SECRET']
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth)
    api.update_with_media(
        os.path.join(GRAPH_PATH, "peru.jpg"), status="Muertes SINADEF país."
    )


def main():
    download_file()
    df = load_and_prepare_data()
    set_fallecidos_totales(df)
    for departamento in DEPARTAMENTOS:
        set_fallecidos_totales(df, departamento)
    
    tweet()


WORKING_PATH = "D:\pythonCode\Covid"
GRAPH_PATH = os.path.join(WORKING_PATH, "graficos")
DOWNLOAD_PATH = r"C:\Users\Gabriel\Downloads"
if "NOTEST" in sys.argv:
    DOWNLOAD_FILE = "fallecidos_sinadef.csv"
else:
    DOWNLOAD_FILE = "fallecidos_sinadef_test.csv"
DF_NOTAIL = 3  # Records to be clipped at END of dataset
DF_NORMAL = 7  # Records to be used for rolling averages
DEPARTAMENTOS = [
    "CUSCO",
    "LA LIBERTAD",
    "LIMA",
    "ICA",
    "ANCASH",
    "JUNIN",
    "AMAZONAS",
    "LORETO",
    "PUNO",
    "MADRE DE DIOS",
    "SAN MARTIN",
    "TACNA",
    "AREQUIPA",
    "UCAYALI",
    "CAJAMARCA",
    "HUANUCO",
    "HUANCAVELICA",
    "CALLAO",
    "AYACUCHO",
    "TUMBES",
    "MOQUEGUA",
    "APURIMAC",
    "PASCO",
    "PIURA",
    "LAMBAYEQUE",
]
MESES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SETIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]
MESES_3 = [
    "ENE",
    "FEB",
    "MAR",
    "ABR",
    "MAY",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OCT",
    "NOV",
    "DIC",
]

main()
