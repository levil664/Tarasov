import pandas as pd
import pdfkit
from jinja2 import Environment, FileSystemLoader


def get_stats(filename, vacancy_name, area_name):
    """
    Метод обрабатывающий полученную базу данных исходя из названия полученной вакансии и города, формирует pdf с полученными результатами

    Attributes:
        filename: Название файла
        vacancy_name: Название вакансии
        area_name: Название города
    """

    title_1 = ['Год',
              'Динамика уровня зарплат по годам для выбранной профессии и региона',
              'Динамика количества вакансий по годам для выбранной профессии и региона']

    title_2 = ['Город', 'Зарплата по городу', 'Доля вакансий по городам']

    # Формируем статистику по полученным данным
    result = pd.read_csv(filename, encoding='utf-8-sig')\
            .dropna()\
            .assign(area_name=lambda x: x['area_name'].astype('category'))\
            .assign(year=lambda x: x.apply(lambda y: y['published_at'].split('T')[0].split('-')[0], axis=1))
    len_result = len(result)
    p = len_result // 100
    salary_by_area = result.groupby('area_name')['salary'].agg(['count', 'mean']).query(f'count > {p}')['mean']\
                            .sort_values(ascending=False).round(2).head(10).to_dict()
    distribution_by_area = result.groupby('area_name').count()['salary']
    distribution_by_area = distribution_by_area[distribution_by_area > p] / len_result
    distribution_by_area = distribution_by_area.round(3).head(10).to_dict()
    selected_salary_stat = result[result.name.apply(lambda x: vacancy_name.lower() in x.lower())][result.area_name.apply(lambda x: area_name.lower() == x.lower())][['year', 'salary']].groupby('year').mean().round().to_dict()['salary']
    selected_count_stat = result[result.name.apply(lambda x: vacancy_name.lower() in x.lower())][result.area_name.apply(lambda x: area_name.lower() == x.lower())].groupby('year').count().to_dict()['salary']

    # Готовим статистику к выгрузке в виде пдф
    dictionary_area = dict()
    for area in salary_by_area:
        dictionary_area[area] = dict()
        dictionary_area[area][title_2[0]] = area
        dictionary_area[area][title_2[1]] = salary_by_area[area]
        dictionary_area[area][title_2[2]] = distribution_by_area[area]

    # Готовим статистику к выгрузке в виде пдф
    dictionary_year = dict()
    for year in selected_salary_stat:
        dictionary_year[year] = dict()
        dictionary_year[year][title_1[0]] = year
        dictionary_year[year][title_1[1]] = selected_salary_stat[year]
        dictionary_year[year][title_1[2]] = selected_count_stat[year]

    # Выгружаем статистику в виде пдф
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("3.4.3_template.html")
    pdf_template = template.render({'title_1': title_1, 'dictionary_area': dictionary_area, 'dictionary_year': dictionary_year, 'title_2': title_2})
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdfkit.from_string(pdf_template, '3.4.3.pdf', configuration=config)

filename = input()
vacancy_name = input()
area_name = input()

get_stats(filename, vacancy_name, area_name)