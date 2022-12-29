import csv, requests, json, time


template = {
        'page': 0,
        'per_page': 100,
        'specialization': 1,
        'date_from': '2022-12-19T00:00:00+0300',
        'date_to':  '2022-12-19T06:00:00+0300'
    }
dates_from = ['2022-12-26T00:00:00+0300', '2022-12-26T06:00:00+0300', '2022-12-26T12:00:00+0300', '2022-12-26T18:00:00+0300']
dates_to = ['2022-12-26T06:00:00+0300', '2022-12-26T12:00:00+0300', '2022-12-26T18:00:00+0300', '2022-12-26T23:59:59+0300']


def get_vacancies(template):
    """
    Метод получающий из API HH (https://api.hh.ru/) все IT-вакансии за любой прошедший будний день текущего месяца

    Attributes:
        template (dict): шаблон выгрузки
    """
    api_url = 'https://api.hh.ru'
    request = requests.get(f'{api_url}/vacancies', template)
    if request.status_code != 200:
        for i in range(100):
            time.sleep(0.3)
            request = requests.get(f'{api_url}/vacancies', template)
            if request.status_code == 200:
                break
            else:
                if 'captha' in request.content.decode():
                    print(request.content.decode())
                    input()
    data = request.content.decode()
    request.close()
    return data


with open('26-12-2022.csv', 'w',encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    title = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
    writer.writerow(title)

    for i in range(4):
        template['date_to'], template['date_from'] = dates_to[i], dates_from[i]
        for page in range(20):
            template['page'] = page
            jsn = json.loads(get_vacancies(template))
            for dict in jsn['items']:
                row = [dict['name']]
                if dict['salary'] == None:
                    row.extend([None, None, None])
                else:
                    row.extend([dict['salary']['from'], dict['salary']['to'], dict['salary']['currency']])
                if dict['area'] == None:
                    row.append(None)
                else:
                    row.append(dict['area']['name'])
                row.append(dict['published_at'])
                writer.writerow(row)
            time.sleep(0.25)