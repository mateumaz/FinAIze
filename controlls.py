import numpy as np
import os
from functions_v2 import File
from matplotlib.figure import Figure
import mplcursors
import datetime
import calendar
from collections import OrderedDict

# Pomysł - zrobić klase do wykresu, kóra będzie zawierała różne przydatne metody

def show_window(app, page_name):
        frame = app.windows[page_name]
        frame.tkraise()

def look_for_models():
    path = os.path.dirname(__file__)
    models = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.keras'):   #'.h5'
                #file_path = os.path.join(root, file)
                models.append(file)
    return models


def get_bar_plot(Data: File, checkboxes: list, per='last'):
    x, y = [], []
    summary = Data.summary
    if per=='last':
        month_per = summary['Okres'].iloc[-1]
    else:
        month_per = per

    j = 0
    for i in range(len(summary)):
        if month_per == summary.loc[i, 'Okres']:
            if checkboxes[j].get() == 1:
                x.append(summary.loc[i,'Kategoria'])
                y.append(summary.loc[i,'Suma'])
            j += 1

    figure = Figure()
    ax = figure.add_subplot(111)
    bars = ax.bar(x, y)
    ax.set_xlabel('Category')
    ax.set_ylabel('Amount')
    start_date, end_date = last_month(month_per)
    ax.set_title(f'{start_date} : {end_date}')

    cursor = mplcursors.cursor(bars)
    @cursor.connect("add")
    def on_add(sel):
        bar = sel.artist
        sel.annotation.set_text(f'{bar.datavalues[sel.index]:.2f}')
        sel.annotation.get_bbox_patch().set(fc="white")

    return figure, bars, cursor


def get_combined_bar_plot(Data: File, checkboxes: list):
    summary = Data.summary
    months = np.unique(summary['Okres'])
    months_str = []
    for month in months:
        m_str = ''
        for x in month:
            m_str = m_str + str(x) + "-"
        months_str.append(m_str)

    categories = list(OrderedDict.fromkeys(summary['Kategoria']))
    j = 0
    for i in range(len(checkboxes)):
        if checkboxes[i].get() == 0:
            del categories[j]
            j -= 1
        j += 1

    y = []
    for j in range(len(categories)):
        ys = []
        for i in range(len(summary)):
            if summary['Kategoria'].iloc[i] == categories[j]:
                ys.append(summary['Suma'].iloc[i])
        y.append(ys)

    figure = Figure()
    ax = figure.add_subplot(111)
    bars = []
    bottom = np.zeros(len(months))
    for i in range(len(y)):
        bar = ax.bar(months_str, y[i], bottom=bottom, label=categories[i])
        bars.append(bar)
        bottom += np.array(y[i])

    ax.set_xlabel('Month')
    ax.set_ylabel('Amount')
    ax.set_title('Finances over several months')
    ax.set_xticks(months_str)
    ax.set_xticklabels(months_str)
    ax.legend()

    cursor = mplcursors.cursor(bars, hover=True)
    @cursor.connect("add")
    def on_add(sel):
        bar = sel.artist
        sel.annotation.set_text(f'{bar.datavalues[sel.index]:.2f}')
        sel.annotation.get_bbox_patch().set(fc="white")
    
    return figure, bars, cursor



def last_month(period) -> datetime.date:
    M, Y = period
    start_month = datetime.date(Y,M,1)
    _, num_days = calendar.monthrange(Y, M)
    end_month = datetime.date(Y,M,num_days)
    return(start_month, end_month)

     