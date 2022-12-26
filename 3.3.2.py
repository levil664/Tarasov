import csv


filename = 'vacancies_dif_currencies.csv'
complite = dict()


with open('complite.csv', encoding='utf-8') as file:
    reader = csv.reader(file)
    complite_title = next(reader)
    for line in reader:
        complite[tuple(line[0].split('-'))] = {element: i for element, i in zip(complite_title, line)}


with open(filename, encoding='utf-8-sig') as complite_file, open('result.csv', 'w', encoding='utf-8-sig', newline='') as result_file:
    writer = csv.writer(result_file)
    reader = csv.reader(complite_file)
    title = next(reader)
    new_title = title[::]
    new_title[new_title.index('salary_from')] = 'salary'
    new_title.remove('salary_to').remove('salary_currency')
    writer.writerow(new_title)

    for row in reader:
        dict = {element: i for element, i in zip(title, row)}
        year, month = dict['published_at'].split('-')[:2]
        currency_value = complite[year, month]
        new_row = []
        salary = ''
        if (dict['salary_from'] != '' or dict['salary_to'] != '') and (dict['salary_currency'] == "RUR"
            or (dict['salary_currency'] in currency_value and currency_value[dict['salary_currency']] != '')):
            salary, count = 0, 0
            if dict['salary_from'] != '':
                salary += float(dict['salary_from'])
                count += 1
            if dict['salary_to'] != '':
                salary += float(dict['salary_to'])
                count += 1
            currency = dict['salary_currency']
            if currency != 'RUR':
                salary *= float(currency_value[currency])
            salary //= count

        for element in new_title:
            if element == 'salary':
                new_row.append(salary)
            else:
                new_row.append(dict[element])

        writer.writerow(new_row)