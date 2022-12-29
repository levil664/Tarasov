import decimal
import requests
import csv
import xml.etree.ElementTree as ET


currencies = ['USD', 'EUR', 'KZT', 'UAH', 'BYR']
min_date = 2003, 1, 24, 21, 30, 49
max_date = 2022, 7, 19, 11, 10, 32


def get_curency_from_bank(min_date, max_date):
    """
    Метод, который собирает курсы валют с помощью API сайта ЦБ РФ

    Attributes:
        min_date: крайняя минимальная дата
        max_date: крайняя максимальная дата
    """
    for year in range(min_date[0], max_date[0] + 1):
        for month in range(1, 13):
            if year == max_date[0] and month > max_date[1]:
                 break
            if year == min_date[0] and month < min_date[1]:
                continue
            request = requests.get(f'http://www.cbr.ru/scripts/XML_daily.asp?date_req=01/{month:02}/{year}')
            with open(f'curency/01-{month}-{year}.xml','w') as request_file:
                request_file.write(request.text)

def do_split(i, sep, delete_empty = False, func = lambda x: x):
    """
    Вспомогательный метод помогающий разбить время
    """
    results = []
    temp = ''
    for element in i:
        if element in sep:
            if (delete_empty and temp != '') or not delete_empty:
                results.append(func(temp))
            temp = ''
        else:
            temp += element
    results.append(func(temp))
    return results

def complite_curency_from_bank(currencies, min_date, max_date):
    """
    Метод формирующий dataframe

    Attributes:
        currencies: массив валют (RUR, USD...)
        min_date: крайняя минимальная дата
        max_date: крайняя максимальная дата
    """
    with open('complite.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date'] + currencies)
        for year in range(min_date[0], max_date[0] + 1):
            for month in range(1, 13):
                if year == max_date[0] and month > max_date[1]:
                    break
                if year == min_date[0] and month < min_date[1]:
                    continue
                tree = ET.parse(f'curency/01-{month}-{year}.xml')
                row = [f'{year}-{month:02}']
                for curr in currencies:
                    value = tree.find(f"Valute[CharCode='{curr}']/Value")
                    if value != None:
                        row.append(decimal.Decimal(value.text.replace(',', '.')) / int(
                            tree.find(f"Valute[CharCode='{curr}']/Nominal").text))
                    else:
                        row.append('')
                writer.writerow(row)

def get_min_max_date(filename, lower_limit=5000):
    """
    Метод определения максимальной и минимальной выборки
    """
    res_dict = dict()
    min_date = 2023, 12, 31, 23, 59, 59
    max_date = 2000, 12, 31, 23, 59, 59
    with open(filename, encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        title = next(reader)
        for row in reader:
            if row[3] not in res_dict:
                res_dict[row[3]] = 0
            res_dict[row[3]] += 1
            date = tuple(do_split(row[5], '-T:+', True, int)[:-1])
            if date < min_date:
                min_date = date
            if date > max_date:
                max_date = date

    return list(filter(lambda x: res_dict[x] > lower_limit, res_dict)), min_date, max_date

get_curency_from_bank(min_date, max_date)
complite_curency_from_bank(currencies, min_date, max_date)