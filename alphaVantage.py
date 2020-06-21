import requests
import pandas as pd
import json
import time


def receiveJSON(symbol, interval):
    APIkey = '8MNWMDBEFN4O6DG9'
    params = {'function': 'TIME_SERIES_' + interval, 'symbol': symbol, 'apikey': APIkey,
              'outputsize': 'full'}

    # Запрос AV, преобразование выдачи
    r = requests.get("https://www.alphavantage.co/query", params)
    a = r.json()
    return a


def requestAV(symbol, interval):
    # Параметры запроса
    a = receiveJSON(symbol, interval)
    if interval == 'Daily':
        data = a['Time Series (' + interval + ')']
    else:
        data = a[interval + ' Time Series']
    # Словарь в DataFrame, переименовываем столбцы
    df = pd.DataFrame.from_dict(data, orient='index').rename(
        columns={"1. open": "Open", "2. high": "High", "3. low": "Low",
                 "4. close": "Close", "5. volume": "Volume"})
    # Переворачиваем таблицу
    df = pd.DataFrame(df.iloc[::-1])
    # Меняем индекс
    df = df.reset_index().rename(columns={"index": "Date"})
    df['Date'] = df['Date'].apply(pd.to_datetime)
    df = df.set_index('Date')
    return df


def saveJSON(symbol, interval, path):
    a = receiveJSON(symbol, interval)
    # Сохранить исходный JSON
    name = symbol
    name = name + '.json'
    path = path + name
    with open(path, 'w') as sf:
        json.dump(a, sf)
    print(name, 'saved')


def requestSAR(symbol, interval):
    APIkey = '8MNWMDBEFN4O6DG9'
    params = {'function': 'SAR', 'symbol': symbol, 'apikey': APIkey,
              'interval': interval.lower(), 'acceleration': '0.02'}
    r = requests.get("https://www.alphavantage.co/query", params)
    a = r.json()
    data = a
    df = pd.DataFrame.from_dict(data)
    return df


def SARstatus(symbol):
    intervals = ['Daily', 'Weekly', 'Monthly']
    SAR = []
    prices = []
    result = []
    for interval in intervals:
        temp = requestSAR(symbol, interval)
        SAR.append(float(temp.iloc[7]['Technical Analysis: SAR']['SAR']))
        temp = requestAV(symbol, interval)
        prices.append(float(temp.iloc[-1]['Close']))
        time.sleep(30)
    for i in range(0, len(SAR)):
        if SAR[i] > prices[i]:
            result.append("SELL")
        else:
            result.append("BUY")
    return SAR, prices, result


def currentPrice(instrument):
    instrument_dict = {'AGRO-гдр': 'AGRO.MOS', 'АЛРОСА ао': 'ALRS.MOS', 'Аэрофлот': 'AFLT.MOS', 'БСП ао': 'BSPB.MOS', \
                       'Башнефт ап': 'BANEP.MOS', 'ГАЗПРОМ ао': 'GAZP.MOS', 'ЛУКОЙЛ': 'LKOH.MOS', \
                       'МТС-ао': 'MTSS.MOS', 'Магнит ао': 'MGNT.MOS', 'Мечел ао': 'MTLR.MOS', \
                       'МосБиржа': 'MOEX.MOS', 'Мостотрест': 'MSTT.MOS', 'НЛМК ао': 'NLMK.MOS', \
                       'Ростел -ао': 'RTKM.MOS', 'Сбербанк': 'SBER.MOS', 'СевСт-ао': 'CHMF.MOS', \
                       'Система ао': 'AFKS.MOS'}

    return (float(requestAV(instrument_dict[instrument], 'Daily')['Close'][0]))