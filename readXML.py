import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import copy


def read_xml(xml_path):
    """

    :rtype: DataFrame
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # список извлекаемых столбцов
    attrib_list = ['security_name',
                   'request_no',
                   'conclusion_time',
                   'buy_qnty',
                   'sell_qnty',
                   'price',
                   'volume_rur',
                   'broker_commission']
    # создаем список индексов DataFrame
    index_list = copy.deepcopy(attrib_list)
    index_list[index_list.index('buy_qnty')] = 'quantity'
    index_list[index_list.index('broker_commission')] = 'commission'
    index_list.remove('sell_qnty')
    # формируем список всех отправленных заявок на покупку/продажу
    orders_list = []
    for i in root:  # ищем раздел spot_main_deals_conclusion
        if i.tag == "spot_main_deals_conclusion":
            for order in i:  # извлекаем информацию
                temp_list = []
                for attribute in attrib_list:
                    if attribute in order.attrib.keys():  # проверяем что запрашиваемый аттрибут есть в файле
                        if attribute == 'sell_qnty':  # если происходит продажа добавляем минус перед количеством акций
                            temp_list.append('-' + order.attrib[attribute])
                        else:  # для всех случаев кроме sell, принимаем значение как есть
                            temp_list.append(order.attrib[attribute])
                orders_list.append(temp_list)
    df = pd.DataFrame(orders_list, columns=index_list)
    # Изменяем формат данных в столбцах
    df['security_name'] = df['security_name'].apply(str.strip)  # удаляем пробелы в названиях инструментов
    df['conclusion_time'] = df['conclusion_time'].apply(pd.to_datetime)
    df['quantity'] = df['quantity'].astype('float').astype('int')
    df['commission'] = df['commission'].astype('float')
    df['price'] = df['price'].astype('float')
    df['volume_rur'] = df['volume_rur'].astype('float')
    df.loc[(df['quantity'] < 0), 'volume_rur'] = -df['volume_rur']  # ставим знак минус у объёма в случае sell
    # Группировка по номеру заявки (одна строка - одна сделка) + сортировка по имени и времени
    df = df.groupby('request_no').agg(
        {'security_name': min, 'conclusion_time': min, 'quantity': sum, 'price': np.mean,
         'volume_rur': sum, 'commission': sum})
    df = df.sort_values(by=['security_name', 'conclusion_time']).reset_index()
    df = df.drop('request_no', axis=1)
    return df


def found_orders(orders):
    order_number = 0
    poz = 0  # глобальное отслеживание позиции
    open_list = []
    for instrument in orders['security_name'].unique():
        orders.loc[(orders['security_name'] == instrument), 'cumsum'] = \
            orders.loc[(orders['security_name'] == instrument)]['quantity'].cumsum()  # считаем кумулятивную сумму по инструменту
        rangeLen = orders.loc[(orders['security_name'] == instrument)].shape[0]  # определяем число ордеров для одного инструмента
        for i in range(0, rangeLen):  # идем по всем ордерам
            if orders.loc[poz]['cumsum'] != 0:
                orders.loc[poz, 'order'] = order_number
                if i == rangeLen - 1:  # если это последний ордер и сумма больше нуля, то позиция не закрыта, добавляем в список открытых
                    open_list.append(order_number)
                    orders.loc[poz, 'cumsum'] = 0  # обнуляем сумму, чтобы учитывать следующие сделки
                    order_number += 1
            else:
                orders.loc[poz, 'order'] = order_number
                order_number += 1
            poz += 1
    orders['order'] = orders['order'].astype('int')
    open_pos = pd.DataFrame(columns=orders.columns) #датафрейм для открытых сделок
    for i in open_list:
        dt = orders[orders['order'] == i]
        open_pos = open_pos.append(dt) # сохраняем открытую сделку перед удалением из основной таблицы
        indexDrop = orders[ orders['order'] == i ].index  # ищем индексы открытых позиций
        orders.drop(indexDrop , inplace=True)  # удаляем открытые позиции из основной таблицы
    return orders, open_pos


def preparePositionsDF(orders):
    orders['Open Price'] = orders.groupby('order')['price'].head(1)
    orders['Close Price'] = orders.groupby('order')['price'].tail(1)
    orders['Open Date'] = orders.groupby('order')['conclusion_time'].head(1)
    orders['Close Date'] = orders.groupby('order')['conclusion_time'].tail(1)
    # Позиции
    positions = orders.groupby('order').agg(
        {'security_name': lambda x: x.iloc[0], 'quantity': lambda x: x.iloc[0],
         'volume_rur': lambda x: -(x.sum()), 'Open Price': min, 'Close Price': min,
         'commission': sum, 'Open Date': min, 'Close Date': min})
    # Определяем тип позиции
    positions.loc[(positions['quantity'] > 0), 'Order Type'] = 'Buy'
    positions.loc[(positions['quantity'] < 0), 'Order Type'] = 'Sell'
    positions = positions.reset_index()
    positions = positions.drop('order', axis=1)
    return positions