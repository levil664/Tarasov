import pandas as pd
from jinja2 import Environment, FileSystemLoader
import pdfkit


def get_statistics(filename, vacancy_name):
    """
    Метод обрабатывающий полученную базу данных исходя из названия полученной вакансии, формирует pdf с полученными результатами

    Attributes:
        filename: Название файла
        vacancy_name: Название вакансии
    """
    result = pd.read_csv(filename, encoding='utf-8-sig')\
            .dropna()\
            .assign(salary=lambda x: x['salary'].astype('int64'),
                    area_name=lambda x: x['area_name'].astype('category'))\
            .assign(year=lambda x: x.apply(lambda y: y['published_at'].split('T')[0].split('-')[0], axis=1))
    salary_statistic = result[['year', 'salary']].groupby('year').mean().round().to_dict()['salary']
    selected_salary_statistic = result[result.name.apply(lambda x: vacancy_name.lower() in x.lower())][['year', 'salary']].groupby('year').mean().round().to_dict()['salary']
    count_statistic = result.groupby('year').count().to_dict()['salary']
    selected_count_statistic = result[result.name.apply(lambda x: vacancy_name.lower() in x.lower())].groupby('year').count().to_dict()['salary']
    header = ['Года',
              'Динамика уровня зарплат по годам',
              'Динамика уровня зарплат по годам для выбранной профессии',
              'Динамика количества вакансий по годам',
              'Динамика количества вакансий по годам для выбранной профессии']
    dictionary = dict()
    for year in salary_statistic:
        dictionary[year] = dict()
        dictionary[year][header[0]] = year
        dictionary[year][header[1]] = salary_statistic[year]
        dictionary[year][header[2]] = selected_salary_statistic[year]
        dictionary[year][header[3]] = count_statistic[year]
        dictionary[year][header[4]] = selected_count_statistic[year]

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("3.4.2_template.html").render({'header': header, 'dictionary': dictionary})
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdfkit.from_string(template, '3.4.2.pdf', configuration=config)


filename = input()
vacancy_name = input()

get_statistics(filename, vacancy_name)
