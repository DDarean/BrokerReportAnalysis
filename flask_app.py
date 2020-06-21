from flask import Flask, render_template, Markup

import readXML
import alphaVantage

from plotly.offline import plot
from plotly.graph_objs import Scatter, Pie

app = Flask(__name__)

def genIndex():
    # Обработка отчёта
    orders = readXML.read_xml('/home/DDarean/mysite/report/Broker_Report.xml')
    orders, open_orders = readXML.found_orders(orders)
    positions = readXML.preparePositionsDF(orders)

    open_positions = open_orders.groupby('order').agg({'security_name': lambda x: x.iloc[0], \
                                                'quantity': sum, 'volume_rur': sum})
    open_positions['open_price'] = open_positions['volume_rur'] / open_positions['quantity']
    open_positions['current_price'] = open_positions['security_name'].apply(alphaVantage.currentPrice)
    open_positions['trade_result'] = (open_positions['current_price'] - open_positions['open_price'])* \
                                        open_positions['quantity']# для сделок Sell цены наоборот
    open_positions = open_positions.reset_index().drop('order', axis = 1)

    # Данные для таблицы сделок
    tableO = open_positions.to_html(justify = "center", classes = ["table", "table-striped", "table-sm", "table-bordered"])
    # Итоги торговли
    tradeResult = round(positions['volume_rur'].sum(),1)
    commissionTotal = positions['commission'].sum()
    # Готовим данные для графика
    test = positions.sort_values('Close Date')
    test['Close Date'] = test['Close Date'].apply(lambda x: x.date())
    test = test.groupby('Close Date').agg({'volume_rur':sum, 'commission':sum})
    test['trade_result'] = (test['volume_rur'] - test['commission']).cumsum()
    my_plot_div = plot([Scatter(x=test.index, y=test['trade_result'])], output_type='div')

    labels2 = positions['security_name'].unique()
    values2 = [positions.loc[(positions['security_name']==i)]['quantity'].sum() for i in labels2]
    resultPie = plot([Pie(labels=labels2, values=values2, hole=.3)], output_type='div')

    labels = open_positions['security_name'].unique()
    values = [open_positions.loc[(open_positions['security_name']==i)]['quantity'].sum() for i in labels]
    openPie = plot([Pie(labels=labels, values=values, hole=.3)], output_type='div')

    return render_template('index.html',
                       openPos=tableO,
                       result=tradeResult,
                       commission=commissionTotal,
                       div_placeholder=Markup(my_plot_div),
                       resultPie=Markup(resultPie),
                       openPie=Markup(openPie))

def genResult():
    # Обработка отчёта
    orders = readXML.read_xml('/home/DDarean/mysite/report/Broker_Report.xml')
    orders, open_orders = readXML.found_orders(orders)
    positions = readXML.preparePositionsDF(orders)
    # Данные для таблицы сделок
    tableR = positions.to_html(justify = "center", classes = ["table", "table-striped", "table-sm", "table-bordered"])
    return render_template('OrdersTable.html', headrs=tableR)

@app.route("/", methods=["GET", "POST"])
def index():
    return genIndex()

@app.route("/result", methods=["GET", "POST"])
def result():
    return genResult()

@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    return render_template('analysis.html')

@app.route("/about", methods=["GET", "POST"])
def about():
    scheme_url = "/static/Scheme2020.png"
    return render_template('about.html', scheme_img = scheme_url)