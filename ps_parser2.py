import csv
import random
from time import sleep
import datetime
from pycbrf import ExchangeRates
from bs4 import BeautifulSoup
import requests
from multiprocessing.dummy import Pool as ThreadPool



headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}

proxies = [None]


def parsing():
    global proxies
    with open('proxies.txt', 'r', encoding='utf-8') as file:
        proxies = [{'https': proxy.removesuffix('\n')} for proxy in file.readlines()]

    with open('proxies.txt', 'w', encoding='utf-8') as file:
        for i in proxies[1:]:
            file.write(i['https'] + '\n')

        file.write(proxies[0]['https'])

    if proxies == 'None':
        proxies = [None]
    else:
        proxies = [proxies[0]]

    print(proxies)

    sheet_headers = ['Название', 'Описание', 'Цена', 'Цена без скидки', 'Цена закупки', 'Подкаталог',
                     'PlayStation Plus', 'Русский язык', 'Фото', 'Background', 'Платформа:', 'Выпуск:', 'Издатель:',
                     'Жанр:']
    data = requests.get('https://store.playstation.com/en-tr/pages/deals', proxies=random.choice(proxies),
                        headers=headers).text
    soup2 = BeautifulSoup(data, 'html.parser')
    link2 = soup2.find_all('a', class_='psw-content-link')[-6].get('href')
    main_links = [f'https://store.playstation.com{link2.removesuffix("1")}',
                  'https://store.playstation.com/en-tr/category/4cbf39e2-5749-4970-ba81-93a489e4570c/',
                  'https://store.playstation.com/en-tr/category/44d8bb20-653e-431e-8ad0-c0a365f68d2f/']

    try_rub = 0
    today = str(datetime.datetime.now())[:10]
    for rate in list(filter(lambda el: el.code == 'TRY', ExchangeRates(today).rates)):
        try_rub = round(float(rate.rate) * 1.08, 4)

    csvfile = open('data/ps.csv', 'w', newline='', encoding='UTF-8')
    writer = csv.DictWriter(csvfile, fieldnames=sheet_headers, delimiter='\t')
    writer.writeheader()

    count = 0
    game_cards = {}
    for numb, main_link in enumerate(main_links):

        try:
            data = requests.get(main_link, proxies=random.choice(proxies), headers=headers).text
        except Exception as e:
            with open('proxies.txt', 'r', encoding='utf-8') as file:
                proxies = [{'https': proxy.removesuffix('\n')} for proxy in file.readlines()]

            with open('proxies.txt', 'w', encoding='utf-8') as file:
                for i in proxies[1:]:
                    file.write(i['https'] + '\n')

                file.write(proxies[0]['https'])

            if proxies == 'None':
                proxies = [None]
            else:
                proxies = [proxies[0]]

            data = requests.get(main_link, proxies=random.choice(proxies), headers=headers).text

        soup = BeautifulSoup(data, 'html.parser')
        pages = int(soup.find_all('span', class_='psw-fill-x')[-4].text)
        pages = get_paged_links(main_link, pages)
        results = get_requested_links(pages)

        elements = []
        for data in results:
            soup = BeautifulSoup(data.text, 'html.parser')
            elements += soup.find_all('li', class_='psw-l-w-1/8@desktop')

        prices = []
        full_prices = []
        photos = []
        buy_prices = []
        rem_elements = []
        pspluses = []
        for element in elements:
            price = element.find('span', class_='psw-m-r-3')
            if not price:
                rem_elements.append(element)
            else:
                price = price.text.split()[0].replace(',', '.')
                if price != 'Unavailable' and price != 'Free' and price != 'Included' and price != 'Game' and price != 'Early':
                    try:
                        full_price = element.find('s', class_='psw-c-t-2').text.split()[0].replace(',', '.')
                    except:
                        full_price = price

                    while price.count('.') > 1:
                        price = price.replace('.', '', 1)

                    while full_price.count('.') > 1:
                        full_price = full_price.replace('.', '', 1)

                    price = float(price) * try_rub
                    full_price = float(full_price) * try_rub
                    buy_price = int(round(float(price) * 1.05 + 100))

                    if 0 < price < 300:
                        price = round(price + 300) + 100
                    elif 299 < price < 600:
                        price = round((price + 200) * 1.3) + 100
                    elif 599 < price < 1000:
                        price = round((price + 150) * 1.5) + 100
                    else:
                        price = round(price * 1.57)

                    price += 250

                    if price < 750:
                        price = 750

                    if 0 < full_price < 300:
                        full_price = round(full_price + 300) + 100
                    elif 299 < full_price < 600:
                        full_price = round((full_price + 200) * 1.3) + 100
                    elif 599 < full_price < 1000:
                        full_price = round((full_price + 150) * 1.5) + 100
                    else:
                        full_price = round(full_price * 1.57)

                    full_price += 250

                    if full_price < 750:
                        full_price = 750

                    try:
                        pspluses.append('Да' if element.findChild('span', {
                            'data-qa': 'ems-sdk-grid#productTile4#service-upsell#descriptorText'}).text == 'Extra' else 'Нет')
                    except:
                        pspluses.append('Нет')

                    photo = element.findChild('img').get('src').split('?')[0]

                    prices.append(price)
                    full_prices.append(full_price)
                    buy_prices.append(buy_price)
                    photos.append(photo)
                else:
                    rem_elements.append(element)

        for i in rem_elements:
            elements.remove(i)

        element_links = ['https://store.playstation.com' + x.find('a').get('href').replace('en-tr', 'ru-ua') for x in
                         elements]
        results = get_requested_links(element_links)

        for photo, price, full_price, buy_price, psplus, data in zip(photos, prices, full_prices, buy_prices, pspluses,
                                                                     results):
            soup = BeautifulSoup(data.text, 'html.parser')
            try:
                title = soup.find('h1').text.replace('на PS4™', '').replace('на PS5™', '').replace('для PS4™',
                                                                                                   '').replace(
                    'для PS5™', '').replace('PS4 & PS5', '').replace('(PlayStation®5)', '').replace('(PlayStation®4)',
                                                                                                    '').replace(
                    '(PS4™)', '').replace('(PS5™)', '').replace('PS5™', '').replace('PS4™', '')
                boss_title = soup.find('h1').text
                description = soup.find('div', class_='psw-l-w-1/2@desktop').find('p').get_text('\n')
            except Exception as e:
                continue

            game_cards[boss_title] = {}
            game_cards[boss_title]['Название'] = title
            game_cards[boss_title]['Цена'] = price
            game_cards[boss_title]['Цена без скидки'] = full_price
            game_cards[boss_title]['Цена закупки'] = buy_price
            game_cards[boss_title][
                'Подкаталог'] = 'Предложения' if numb == 0 else 'PS5 Игры' if numb == 1 else 'PS4 Игры'
            game_cards[boss_title]['Описание'] = description
            game_cards[boss_title]['PlayStation Plus'] = psplus
            game_cards[boss_title]['Фото'] = photo
            game_cards[boss_title]['Background'] = soup.find('img').get('src').split('?')[0]
            chars = zip(soup.find_all('dt'), soup.find_all('dd'))
            voice = lang = False
            for name, value in chars:
                if name.text == 'Голос:':
                    voice = True if 'Русский,' in value.text else False
                elif name.text == 'Языки отображения:':
                    lang = True if 'Русский,' in value.text else False
                elif name.text not in sheet_headers:
                    sheet_headers.append(name.text)
                    game_cards[boss_title][name.text] = value.text
                else:
                    game_cards[boss_title][name.text] = value.text

            game_cards[boss_title][
                'Русский язык'] = 'Полная локализация' if voice else 'Только субтитры' if lang else 'Нет'
            count += 1

        for i in game_cards.keys():
            writer.writerow(game_cards[i])
        game_cards.clear()

    csvfile.close()
    print(count)
    # parsing_e(proxies)


def get_paged_links(link, pages):
    links = []
    for page in range(1, pages + 1, +1):
        links.append(link + str(page))
    return links


def get_requested_links(links):
    global proxies
    pool = ThreadPool()
    print('enter')
    results = []
    # results = pool.map(lambda link: requests.get(link, proxies=proxy, headers=headers), links)
    while links:
        try:
            results.extend(
                pool.map(lambda link: requests.get(link, proxies=random.choice(proxies), headers=headers), links[:100]))
        except Exception as e:
            with open('proxies.txt', 'r', encoding='utf-8') as file:
                proxies = [{'https': proxy.removesuffix('\n')} for proxy in file.readlines()]

            with open('proxies.txt', 'w', encoding='utf-8') as file:
                for i in proxies[1:]:
                    file.write(i['https'] + '\n')

                file.write(proxies[0]['https'])

            if proxies == 'None':
                proxies = [None]
            else:
                proxies = [proxies[0]]

            sleep(10)

            results.extend(
                pool.map(lambda link: requests.get(link, proxies=random.choice(proxies), headers=headers), links[:100]))
        links = links[100:]
        print(len(links))
        sleep(10)
    return results

parsing()
