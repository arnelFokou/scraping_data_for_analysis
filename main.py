from bs4 import BeautifulSoup
import requests
import credentials
import pandas as pd
import re


def extract(url,nb_pages):    
    all_offers = []
    for current_page in range(1,nb_pages):
        current_url = url+f"{current_page}"
        data = requests.get(current_url)
        soup = BeautifulSoup(data.content,"html.parser")
        page_job=  soup.find_all('div',class_="mb-4 relative rounded-lg max-full bg-white flex flex-col cursor-pointer shadow hover:shadow-md")
        print(f"page{current_page}")
        for job_offer in page_job:
            offer={}
            offer['type_job'] = job_offer.find('div',class_="tags absolute top-0 left-0 p-3 flex overflow-hidden w-full").text.strip().split('\n')
            offer['date_published'] = job_offer.find('div',class_="flex items-center gap-2 justify-between mb-4 -mt-2").time.text
            offer['details'] = job_offer.find('div',class_='flex flex-wrap items-center gap-4 mb-4 w-full').text.strip().split('\n')
            offer['description'] = job_offer.find('div',class_='fw-text-highlight line-clamp-3 mb-4').text
            offer['link'] = current_url.split("/fr/")[0]+job_offer.find('div',class_='px-4 pb-4 flex flex-col h-full').h3.a.get('href')
            offer['competences'] = job_offer.find('div',class_="flex items-center").text.split("  ") if job_offer.find('div',class_="flex items-center") else ""
            all_offers.append(offer)
    return all_offers 


def transform(data):
    df = pd.DataFrame(data)
    print(df.head(2))

data = extract(credentials.url,nb_pages=7)
transform(data)