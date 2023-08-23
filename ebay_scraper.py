import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import datetime as dt
from email.message import EmailMessage
import smtplib
import ssl
from dotenv import load_dotenv

load_dotenv(r"C:\Users\T2040\Desktop\All\.env")

url = 'https://www.ebay.co.uk/sch/i.html?_from=R40&_nkw=+&_sacat=33596&_udlo=200&LH_Sold=1&LH_Complete=1&LH_ItemCondition=3000&_ipg=240'

def get_data(url):
    response = requests.get(url)
    t = response.text 
    soup = BeautifulSoup(t, features='html.parser')
    return soup

def get_product_list(soup):
    results = soup.find_all('div', {'class' :"s-item__wrapper clearfix"})
    product_list = []
    yesterday = (pd.to_datetime('today').normalize() - dt.timedelta(days=1))
    for n in range(1, len(results)):
        item = soup.find_all('div', {'class' :"s-item__wrapper clearfix"})[n]
        product = {
            # 'product_title' : item.find('h3', class_ = 's-item__title s-item__title--has-tags').text, --old
            'product_title' :item.find('div', class_ = 's-item__title').text,
            'product_url' : item.find('a', {'class' :'s-item__link'}).get("href"),
            'sold_date' : item.find('div', {'class' :'s-item__title--tagblock'}).find('span', {'class':'POSITIVE'}).text.replace('Sold', '').strip(),
            'item_price' : item.find('span', {'class':'s-item__price'}).find('span').text.replace('£','')
        }
        if pd.to_datetime(product['sold_date']) > yesterday:
            continue
        elif pd.to_datetime(product['sold_date']) < yesterday:
            break
        else:
            product_list.append(product)
    return product_list

def get_part_numbers(product_list):

    # parts_df = pd.DataFrame(columns=['part_number', 'product_title', 'product_url', 'sold_date', 'item_price'])
    parts_df = pd.read_csv('parts_df.csv')
    accepted_labels = ['Manufacturer Part Number:', 'Reference OE/OEM Number:', 'Other Part Number:', 'Manufacturer number:', \
        'Other Part Codes:', 'MPN:', 'Manufacturer number:', 'Reference number (s) OE:', 'Reference number (s) OEM:', \
            'Herstellernummer:', 'Vergleichsnummern:', 'OE/OEM Referenznummer(n):', ]     
    split_chars = '|'.join([',', ' ', '/'])
    replace_chars = '|'.join(['\.','-', "'", '\(', '\)'])
    for item in product_list:
        part_numbers = []
        url = item['product_url']
        soup = get_data(url)
        try:
            labels = soup.find('div', {'class':'ux-layout-section__item ux-layout-section__item--table-view'}).find_all('div', {'class':'ux-labels-values__labels'})
            values = soup.find('div', {'class':'ux-layout-section__item ux-layout-section__item--table-view'}).find_all('div', {'class':'ux-labels-values__values-content'})
        except:
            url=soup.find('div', {'class':'nodestar-item-card-details__image-table'}).find('a').get('href')
            soup = get_data(url)
            labels = soup.find('div', {'class':'ux-layout-section__item ux-layout-section__item--table-view'}).find_all('div', {'class':'ux-labels-values__labels'})
            values = soup.find('div', {'class':'ux-layout-section__item ux-layout-section__item--table-view'}).find_all('div', {'class':'ux-labels-values__values-content'})

        for n in range(len(labels)):
            if labels[n].text in accepted_labels:
                value_numbers = re.split(split_chars, values[n].text)
            else:
                continue
            for number in value_numbers:
                number = number.strip().lower()
                number = re.sub(replace_chars, '', number)
                if len(number) > 6 and bool(re.search(r'\d', number)):
                    part_numbers.append(number)
        part_numbers = list(set(part_numbers)) #removing duplicate part numbers
        item_df = pd.DataFrame(part_numbers, columns = ['part_number'])
        item_df['product_title'] = item['product_title']
        item_df['product_url'] = item['product_url']
        item_df['sold_date'] = item['sold_date']
        item_df['item_price'] = item['item_price']
        parts_df = pd.concat([parts_df, item_df], ignore_index=True)
    parts_df.to_csv('parts_df.csv', index=False)
    print('Saved to CSV')
    return

def send_email(subject, body):
    email_sender = 'pitono.pastas@gmail.com'
    email_password = os.getenv('email_password')
    email_receiver = 'ramaskaleksas@gmail.com'

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

try:
    soup = get_data(url)
    product_list = get_product_list(soup)
    get_part_numbers(product_list)
except Exception as error:
    str_error = str(error)
    send_email(str_error, str_error)
