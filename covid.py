import os, shutil, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from datetime import datetime as dt
import time
import pandas as pd
import matplotlib.pyplot as plt
from statistics import mean, median


def set_options():
    options = WebDriverOptions()
    options.add_argument("--window-size=1440,810")
    # options.add_argument("--headless")
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
    plt.figure(figsize=(15,6))
    current_year = dt.now().year
    for year in range(current_year - 1, current_year + 1):
        # define year startpoint and year endpoint
        year_startpoint, year_endpoint = dt(year, 1, 1), dt(year, 12, 31)
        # filter records for year
        dfx = df.loc[lambda i: i["FECHA"] >= year_startpoint].loc[
            lambda i: i["FECHA"] <= year_endpoint
        ]
        # add data series to graph
        plt.plot(dfx["FECHA"], dfx["CUENTA"])
    graph(filename=filename)

def graph(filename):
    #plt.rcParams["figure.figsize"] = (10, 5)

    ax = plt.gca()
    ax.set_facecolor("#F5F1F5")
    ax.spines["bottom"].set_color("#DFD8DF")
    ax.spines["top"].set_color("#DFD8DF")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("#DFD8DF")
    plt.tick_params(axis="both", length=0)
    #plt.axis(axis)
    #plt.xticks(xt[1], xt[0], color="#606060", fontsize=8)
    #plt.yticks(yt, color="#606060", fontsize=8)
    ax.set_ylim(bottom=0)
    #ax.set_aspect(0.2)
    plt.grid(color="#DFD8DF")
    
    plt.savefig(
        os.path.join("C:/pythonCode/Covid/graficos", filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()

def main():
    # download_file()
    df = load_and_prepare_data()
    set_fallecidos_totales(df)
    #for departamento in DEPARTAMENTOS:
    #    set_fallecidos_totales(df, departamento)


WORKING_PATH = "C:\pythonCode\Covid"
DOWNLOAD_PATH = r"C:\Users\gabriel\Downloads"
if sys.argv[1].upper() == "TEST":
    DOWNLOAD_FILE = "fallecidos_sinadef_test.csv"
else:
    DOWNLOAD_FILE = "fallecidos_sinadef.csv"
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

main()
