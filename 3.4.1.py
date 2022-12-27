import pandas as pd
import csv


complite = dict()


with open('complite.csv', encoding='utf-8') as file:
    reader = csv.reader(file)
    compile_head = next(reader)
    for line in reader:
        complite[tuple(line[0].split('-'))] = {element: i for element, i in zip(compile_head, line)}


def get_salary(salary_from, salary_to, salary_currency, published_at):
    year, month = published_at.split('T')[0].split('-')[:2]
    if (salary_to == 0 and salary_from == 0) or (year, month) not in complite or salary_currency == '':
        return None
    dictionary = complite[year, month]
    if salary_currency not in dictionary or dictionary[salary_currency] == '':
        return None
    salary, count = 0, 0
    if salary_from != 0:
        salary += salary_from
        count += 1
    if salary_to != 0:
        salary += salary_to
        count += 1
    if salary_currency != 'RUR':
        salary *= float(dictionary[salary_currency])
    return salary // count

result = pd.read_csv('vacancies_dif_currencies.csv', encoding='utf-8-sig').fillna(0)
result['salary'] = result.apply(lambda row: get_salary(row['salary_from'], row['salary_to'], row['salary_currency'], row['published_at']), axis=1)
with open('3.4.1_full.csv', 'w', encoding='utf-8-sig', newline='') as file:
    result[['name', 'salary', 'area_name', 'published_at']].to_csv(file, index=False)