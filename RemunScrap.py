from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import date
from config import *
import re
import os



#Configuration
payload = { "LDAPUsername": username, "LDAPPassword": password}

loginURL = "https://careeraxis.ntu.edu.sg/students/login"
formURL = "https://careeraxis.ntu.edu.sg/providers/ldap/login/1"
ogURL = "https://careeraxis.ntu.edu.sg"
internURL = "/students/jobs/typeofwork/2210/internship"
headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}


    
def init():
    print("Initialising...")
    with requests.session() as session:
        
        sessionSpider(session)
        webSpider(session)


#Main Spider function
def webSpider(curSession):
    print("Called webSpider...")

    links = linkSpider(curSession)
    details = detailSpider(curSession, links)
    fileSpider(details)
    
    print("End Session...")



#Starts new session and login
def sessionSpider(session):
    print("session started...")

    #Get Dynamic Session Verification Code
    a = session.get(loginURL)
    loginsource = BeautifulSoup(a.text, "html.parser")

    #Insert Dynamic Verification Code into payload
    payload["__RequestVerificationToken"] = loginsource.find("input", attrs={'name':'__RequestVerificationToken'})['value']

    #Login
    session.post(formURL,payload)
    



    
#---Parse all links from url, returns a list of links
def linkSpider(session):
    print("Called linkspider...")

    #Get total page no. from scrap URL
    scrapPageSource = BeautifulSoup(session.get(ogURL+internURL).text,"lxml")
    #css selector to parse out total page, starts from 1
    totalPage = int(scrapPageSource.select(".pull-right > strong")[1].text) + 1

    #list of all links
    links = []

    #collect all available links from page 1 - totalpage
    for i in range(1 , totalPage):
        pageurl = ogURL + internURL + "?page={0}".format(i)
        pageSource = BeautifulSoup(session.get(pageurl).text)
        print("Page{0} -- ".format(i) , len(pageSource.select(".col-sm-8.list-group-item-heading h4 a")))
        links.extend(pageSource.select(".col-sm-8.list-group-item-heading h4 a"))

    '''print(links)
    print("\n\n")
    print("No. of Links -- ", len(links))'''

    return links
    



#Parse--- all details from list of links (given by linkSpider)
#Returns a list of tuples (Job, Company, Salary, Start Date, Company Website)

def detailSpider(session, links):
    print("Called detailSpider...")

    detailList = []

    #Go through all collected intern detail page links
    for detailUrl in links:

        pageSource = BeautifulSoup(session.get(ogURL+detailUrl["href"]).text, "lxml")
        #Parse through link to get
        #Job Name, Organization, Remuneration, Commencement Data, Website

        jobName = pageSource.select(".under-nav h3")[0].text
        orgName = pageSource.select(".under-nav h4 span")[0].text
        pay = salarySpider(pageSource)
        commences = pageSource.select(".col-md-4 .panel-body p")[3].text

        if(len(pageSource.select(".col-md-4 .panel-body p a"))!=0): 
            orgWebsite = ogURL + pageSource.select(".col-md-4 .panel-body p a")[0]['href']
        else:
            orgWebsite = "none"
        print("Extracting...")
        detailList.append((jobName, orgName, pay,commences, orgWebsite))
    
    return detailList




#Create File from Tuple List Data set
def fileSpider(details):
    print("Converting file...")
    columnNames = ["Job", "Company", "Salary", "Start Date", "Website"]
    df = pd.DataFrame(details, columns = columnNames)
    filetypes = { "excel":".xlsx", "csv":".csv"}
    filename = "/" + str(date.today()) + " Report" +filetypes["excel"]
    dirPath = os.getcwd()
    folderPath = "/Reports"
    df.to_excel(dirPath + folderPath + filename ,index=False)
    print("{0} file saved as {1} in folder path {2}".format( filetypes["excel"],filename, dirPath+folderPath))




#Takes in session Page Source, extracts Salary
#Based on RegEx
#Cleans up Salary data format
#Returns cleaned Salary format
def salarySpider(pageSource):
    pay = pageSource.select(".col-md-4 .panel-body p")[2].text
    regex = r"(\d(,)?\d*[.\d\d]*)([-/.(\s)(to)(per)(month)(hr)(hour)(day)(SGD)$(USD)(RMB)(monthly)]*)(\d(,)?\d*)*"
    
   
    match = re.search(regex, pay)
#no digit -> returns original format
#have digit but comes in a range -> returns original format
    if (match == None) or (match.group(4) != None):
        return pay
    else:
#Single Salary with comma -> remove comma
        if (match.group(2) == ","):
            return match.group(1).replace(",","")
#Single Salary
        else:
            return match.group(1)



#If input string contains integers 0-9
def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))
    

    

init()




    
