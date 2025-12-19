from bs4 import BeautifulSoup
import requests
import credentials
import pandas as pd
import re
import time

HARD_SKILLS = ["python", "sql", "scala","pandas", "numpy", "scikit-learn","spark", "pyspark","excel", "vba","power bi", "tableau", "looker",
"matplotlib", "seaborn", "plotly","postgresql", "mysql", "sqlite","oracle", "sql server","mongodb", "cassandra","data analysis", "data analytics","data visualization", "data cleaning","data modeling", "etl","data warehouse", "data mart",
"business intelligence", "bi","aws", "azure", "gcp","bigquery", "redshift", "snowflake","databricks"]

SOFT_SKILLS = ["communication","esprit analytique", "analytical thinking","résolution de problèmes", "problem solving","autonomie",
    "rigueur","organisation","curiosité","esprit critique","travail en équipe", "teamwork","adaptabilité","gestion du temps",
    "pédagogie","force de proposition"]

def extract(url,nb_pages):    
    all_offers = []
    for current_page in range(1,8):
        current_url = url+f"{current_page}"

        data = requests.get(current_url)
        soup = BeautifulSoup(data.content,"html.parser")

        list_offers=  soup.find_all('div',class_="mb-4 relative rounded-lg max-full bg-white flex flex-col cursor-pointer shadow hover:shadow-md")
        print(f"page{current_url}")

        for job_offer in list_offers:
            time.sleep(1)        
            offer={}        
            offer['link'] = current_url.split("/fr/")[0]+job_offer.find('div',class_='px-4 pb-4 flex flex-col h-full').h3.a.get('href')
        
            job_more=requests.get(offer['link'])                              
            soup2 = BeautifulSoup(job_more.content,"html.parser")

            offer['details'] = soup2.find('div',class_="px-4 py-3 bg-white text-primary h-full flex flex-col shadow bg-white rounded-lg").find('div',class_='grid').text.strip().split('\n')
            offer['enterprise_name'] = soup2.find('div',class_="text-white w-full").p.text
            offer['localisation'] = offer['details'][-1].strip()
            

            offer['type_job'] = job_offer.find('div',class_="tags absolute top-0 left-0 p-3 flex overflow-hidden w-full").text.strip().split('\n')     
            offer['date_published'] = job_offer.find('div',class_="flex items-center gap-2 justify-between mb-4 -mt-2").time.text     
            offer['description'] = job_offer.find('div',class_='fw-text-highlight line-clamp-3 mb-4').text
            offer['competences'] = job_offer.find('div',class_="flex items-center").text.split("  ") if job_offer.find('div',class_="flex items-center") else ""
         
            all_offers.append(offer)
    return all_offers 

def status_exp(number):
    if number <=3:
        return "Junior"
    elif number >=3 and number<=7:
        return "Confirme"
    else:
        return "Senior"

def max_experience(exp_str):
    # Supprime "ans" et espaces
    exp_str = exp_str.replace("ans", "").strip()
    exp_str = exp_str.replace("an", "").strip()

    # Remplace "à" par "-" pour homogénéiser
    exp_str = exp_str.replace("à", "-")
    
    # Sépare par "-"
    if "-" in exp_str:
        min_exp, max_exp = exp_str.split("-")
        return status_exp(int(max_exp.strip()))
    else:
        return status_exp(int(exp_str) if exp_str else 1)
    
def transform(data):
    data_cleaned=[]
    df = pd.DataFrame(data)
    for _, row in df.iterrows():
        elt = {}
        details = " ".join(row['details'])

        elt['link'] = row['link']

        m = re.search(r"Dès que possible|Immédiat|Sous \d+ mois?|\d{2}/\d{2}/\d{4}?", details)
        elt["disponibilite"] = m.group(0) if m else None

        m = re.search(r"\d+\s*(?:à\s*\d+)?\s*ans?", details)
        elt["experience"] = max_experience(m.group(0)) if m else None

        m = re.search(r"\d{2,3}k\s*-\s*\d{2,3}k", details)
        # int_sal = re.sub(r"\xa0", " ", m.group(0)).split("-")[-1]
        # elt["salaire_annuel"] =  int(int_sal[:-1]+"000") if m else None
        elt["salaire_annuel"] =  re.sub(r"\xa0", " ", m.group(0)) if m else None

        m = re.search(r"Télétravail\s*(?:partiel|total|hybride)?", details)
        elt["teletravail"] = m.group(0) if m else None
        description = row['description']
    
        skills_h = [skill for skill in HARD_SKILLS if skill in description.lower()]
        skills_s = [skill for skill in SOFT_SKILLS if skill in description.lower()]
    
        elt["localisation"] = row['localisation']

        elt['enterprise_name'] = row['enterprise_name'].strip()
        elt["type_job"] = [type_job.strip()  for type_job in row['type_job' ] if len(type_job.strip())>1]
        elt["date_published"] = row["date_published"]
        skills_h.extend(skills_s)
        competences = list(row['competences']) if row['competences'] else []
        competences.extend(skills_h)
        elt["competences"] = list(set(competences))

        data_cleaned.append(elt)
    
    return data_cleaned

def load(data):
    df = pd.DataFrame(data)
    df = df.dropna(subset=['salaire_annuel', 'experience'])
    df.to_csv("data_cleaned.csv")


data_extract = extract(credentials.url,nb_pages=7)
data2 = transform(data=data_extract)
load(data2)