import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

def scraper ():
    index_url ="https://www.conservapedia.com/Special:AllPages"
    index_page = requests.get(index_url)
    index_soup = BeautifulSoup(index_page.text, "html.parser")
    #print(index_soup)
    link_sec = index_soup.find(class_="mw-allpages-chunk")
    link_list = link_sec.find_all("a")
    #print(link_list)
    f = csv.writer(open("conservapedia.csv", "w"))
    f.writerow(["page_title", "page_link", "page_contents"])
    site_dict = {}
    for link in link_list:
        page_title = link.contents[0]
        page_link = "https://www.conservapedia.com"+link.get("href")
        site_dict[page_title] = page_link
    #print(site_dict)
    for k,v in site_dict.items():
        page = requests.get(v)
        page_soup = BeautifulSoup(page.text, "html.parser")
        page_body = page_soup.find(id="content")
        page_content = page_body.find("div", class_="mw-content-ltr")
        text = page_content.get_text()
        f.writerow([k,v,text])
    f.close()
    return

scraper()





from bs4 import BeautifulSoup 
#importing BeautifulSoup
import csv
import requests 
#importing requests

source = requests.get('https://bulletins.psu.edu/undergraduate/colleges/behrend/digital-media-arts-technology-ba/#programrequirementstext') 

soup = BeautifulSoup(source.text, 'lxml') 
course_list = []

for td in soup.find_all('td', class_='codecol')[:42]: 
    coursecode = td.a.text
    course_list.append(coursecode.split())
    print(coursecode)

for td in soup.find_all("tr")[8:63]:
    coursename = td.text
    print(coursename)
    
for td in soup.find_all('td', class_='hourscol')[:42]: 
    coursehours = td.text
    course_list.append(coursehours.split())
    print(coursehours)



myFile = open('digit.csv', 'w')
with myFile:
	writer = csv.writer(myFile)
	writer.writerows([['course','code', 'title','credits']])
	writer.writerows(course_list)
myFile.close()






from bs4 import BeautifulSoup 
import csv
import requests 

    source = requests.get('https://bulletins.psu.edu/undergraduate/colleges/behrend/digital-media-arts-technology-ba/#programrequirementstext') 

    soup = BeautifulSoup(source.text, 'lxml') 
    course_list = []


    for td in soup.find_all("td")[12:162]:
        courseinfo = td.text
        course_list.append(courseinfo.split())
        print(courseinfo) 

        
myFile = open('digit.csv', 'w')
with myFile:
	writer = csv.writer(myFile)
	writer.writerows([['course_code', 'course_name','course_credits']])
	writer.writerows(coursename)
myFile.close()


