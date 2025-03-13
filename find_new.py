#!/usr/bin/env python3

from multiprocessing import Process
import os
import json
import re
import sqlite3
import requests
import math
from datetime import datetime
from datetime import timedelta
from lxml import etree

# Make this table in your database
# CREATE TABLE jobs (
# id INTEGER PRIMARY KEY AUTOINCREMENT,
# title TEXT,
# desc TEXT,
# company TEXT,
# joblink TEXT,
# date_found DATETIME,
# ignore BOOL,
# raw_data TEXT, 
# applied BOOL DEFAULT 0, 
# listing TEXT);
# CREATE UNIQUE INDEX job_link_idx ON jobs(joblink);

def adapt_datetime_iso(val):
    return val.isoformat()

def convert_datetime(val):
    return datetime.fromisoformat(val)

sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter('datetime', convert_datetime)
dir_path = os.path.dirname(os.path.realpath(__file__))
con = sqlite3.connect(dir_path + '/jobs.sqlite3')
cur = con.cursor()

headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept':'*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'content-type': 'application/json',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
        }

new_job_meta = {}

def add_job(company,title,link,raw_data,thedate=None,description=None):

    if thedate == None:
        thedate = datetime.today()
    if description == None:
        description = ""

    # print(company + " : " + title)

    # print("\t" + description)
    # print("\t" + link)
    # print("\t" + str(thedate))

    # doesn't work on most sites
    # listing_res = requests.get(link,headers=headers)


    res = cur.execute("""INSERT OR IGNORE INTO jobs 
                      (
                      'company',
                      'title',
                      'joblink',
                      'desc',
                      'date_found',
                      'raw_data'
                      ) VALUES (?,?,?,?,?,?)
                      RETURNING *
                      """, 
                      (
                          company, 
                          title, 
                          link,
                          description,
                          thedate,
                          raw_data
                        )
                    )
    # import pdb; pdb.set_trace()
    row = res.fetchall()
    con.commit()
    if len(row) > 0:
        if company not in new_job_meta: 
            new_job_meta[company] = 0
        new_job_meta[company] = new_job_meta[company] + 1
        return 1

    return 0


def truncate():
    cur.execute("""DELETE FROM jobs""")
    con.commit()

def parse_date(datestr):
        the_new_date = None
        if datestr == "Posted Today":
            the_new_date = datetime.today()
        elif datestr == "Posted Yesterday":
            the_new_date = datetime.today() - timedelta(1)
        elif re.match(r"Posted ([0-9]+)\+? Days Ago",datestr):
            deltaval = re.match(r".* ([0-9]+)\+? .*",datestr)
            deltaval = int(deltaval[1])
            the_new_date = datetime.today() - timedelta(deltaval)
        else:
            print("Unsure how to find date for " + job["postedOn"])

        return the_new_date

def _find_better_workday(company,url,req_data,job_url):
    req_data['size'] = 100
    req_data['sortBy'] = 'Most recent'
    response = requests.post(url,data=json.dumps(req_data),headers=headers)
    data = response.json()

    print(company + "\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    #import pdb;pdb.set_trace()

    new_postings = 0

    for job in data["refineSearch"]["data"]["jobs"]:
        new_postings = new_postings + add_job(
                company=company,
                title=job["title"], 
                link=job_url + job["jobId"],
                description=job["descriptionTeaser"],
                thedate=datetime.strptime(job["postedDate"],"%Y-%m-%dT%H:%M:%S.000+0000"),
                raw_data=json.dumps(job)
        )

    print(str(len(data["refineSearch"]["data"]["jobs"])) + " postings (" + str(new_postings) + " new)")


def find_trane():
    url = 'https://careers.tranetechnologies.com/widgets'
    req_data = {"lang":"en_global","deviceType":"desktop","country":"global","pageName":"search-results","ddoKey":"refineSearch","sortBy":"Most recent","subsearch":"","from":0,"jobs":True,"counts":True,"all_fields":["category","country","state","city","type","jobCompany","phLocSlider","remoteType"],"size":100,"clearAll":False,"jdsource":"facets","isSliderEnable":True,"pageId":"page25","siteType":"external","keywords":"","global":True,"selected_fields":{"state":["Minnesota"]},"sort":{"order":"desc","field":"postedDate"},"locationData":{"sliderRadius":200,"aboveMaxRadius":True,"LocationUnit":"kilometers"},"s":"1"}

    _find_better_workday("Trane",url,req_data, "https://careers.tranetechnologies.com/global/en/job/")


def find_philips():
    url = 'https://www.careers.philips.com/professional/widgets'
    req_data = {"lang":"en_global","deviceType":"desktop","country":"global","pageName":"search-results","ddoKey":"refineSearch","sortBy":"Most recent","subsearch":"","from":1,"jobs":True,"counts":True,"all_fields":["category","type","country","state","city"],"size":100,"clearAll":False,"jdsource":"facets","isSliderEnable":False,"pageId":"page69","siteType":"professional","keywords":"","global":True,"selected_fields":{"state":["Minnesota"]},"sort":{"order":"desc","field":"postedDate"},"locationData":{}}

    _find_better_workday("Philips",url,req_data, "https://www.careers.philips.com/professional/global/en/job/")

def find_ecolab():
    url = 'https://jobs.ecolab.com/widgets'
    req_data = {"lang":"en_global","deviceType":"desktop","country":"global","pageName":"search-results","ddoKey":"refineSearch","sortBy":"","subsearch":"","from":0,"jobs":True,"counts":True,"all_fields":["category","phLocSlider"],"size":100,"clearAll":False,"jdsource":"facets","isSliderEnable":True,"pageId":"page11","siteType":"external","keywords":"","global":True,"selected_fields":{"state":["Minnesota"],"category":["Information Technology","Research, Development & Engineering","Supply Chain"]},"locationData":{"sliderRadius":51,"aboveMaxRadius":True,"LocationUnit":"miles"},"s":"1"}

    _find_better_workday("Ecolab",url,req_data, "https://jobs.ecolab.com/global/en/job/")

def find_honeywell():
    url = 'https://careers.honeywell.com/widgets' 
    req_data = {"lang":"en_us","deviceType":"desktop","country":"us","pageName":"search-results","ddoKey":"refineSearch","sortBy":"Most recent","subsearch":"","from":0,"jobs":True,"counts":True,"all_fields":["country","state","city","category","WorkType","experienceLevel","phLocSlider"],"size":100,"clearAll":False,"jdsource":"facets","isSliderEnable":True,"pageId":"page13","siteType":"external","keywords":"","global":True,"selected_fields":{"state":["Minnesota"],"category":["Information Technology","Integrated Supply Chain & Procurement","Business Management"]},"sort":{"order":"desc","field":"postedDate"},"locationData":{"sliderRadius":150,"aboveMaxRadius":True,"LocationUnit":"miles"},"s":"1"}

    _find_better_workday("Honeywell",url,req_data, "https://careers.honeywell.com/us/en/job/")

def find_lol():
    url = 'https://careers.landolakesinc.com/widgets'
    req_data = {"lang":"en_us","deviceType":"desktop","country":"us","pageName":"it","ddoKey":"refineSearch","sortBy":"","subsearch":"","from":0,"jobs":True,"counts":True,"all_fields":["category","city","state","isRemoteField","type","division","country","workHours"],"pageType":"category","size":10,"rk":"","ak":"","clearAll":False,"jdsource":"facets","isSliderEnable":False,"pageId":"page22-ds","siteType":"external","location":"","keywords":"","global":True,"selected_fields":{"state":["Minnesota"],"category":["Supply Chain, Operations & Sourcing","Manufacturing & Quality Assurance","IT"]},"locationData":{}}

    _find_better_workday("Land'O Lakes",url,req_data, "https://careers.landolakesinc.com/us/en/job/")


def _find_workdayjob(company,url,req_data,job_url):

    response = requests.post(url,data=json.dumps(req_data),headers=headers)

    data = response.json()

    print(company + "\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    postings_found = 0
    new_postings = 0

    #import pdb;pdb.set_trace()
    num_reqs = math.floor(data['total'] / req_data['limit'])

    while True:

        for job in data["jobPostings"]:

            if "title" not in job:
                continue

            postings_found = postings_found + 1


            if "postedOn" in job:
                the_new_date = parse_date(job["postedOn"])
            else:
                the_new_date = datetime.today()

            new_postings = new_postings + add_job(
                    company=company,
                    title=job["title"],
                    link= job_url + job["externalPath"],
                    description="",
                    thedate=the_new_date,
                    raw_data=json.dumps(job)
                    )

        #import pdb; pdb.set_trace()
        if num_reqs > 0:
            req_data["offset"] = req_data["offset"] + req_data["limit"]
            #print("New offset is " + str(req_data["offset"]))
            num_reqs = num_reqs - 1

            response = requests.post(url,data=json.dumps(req_data),headers=headers)

            data = response.json()
        else:
            break

    print(str(postings_found) + " postings (" + str(new_postings) + " new)")

def find_3m():

    url = 'https://3m.wd1.myworkdayjobs.com/wday/cxs/3m/Search/jobs'
    req_data = {"appliedFacets":{"Location_Country":["bc33aa3152ec42d4995f4791a106ed09"],"Location_Region_State_Province":["02f3984b69ba450080e456fe733f6741"],"jobFamilyGroup":["e937e224196b1066cb468414c1519e8e","e937e224196b1066cb4688a8038b9ec2","e937e224196b1066cb46855288e09e9c","e937e224196b1066cb46873369939eb0","e937e224196b1066cb468623979c9ea2","e937e224196b1066cb468878e95c9ebe","e937e224196b1066cb4684c49de69e96","5ddf75e181aa101455314b07eb170000","e937e224196b1066cb46883ee4019ebc","e937e224196b1066cb46833eb3219e82"],"startDate":["29d7affdc34a10001f8fca3a631900f8","29d7affdc34a10001f8fca311c1900f7"]},"limit":20,"offset":0,"searchText":""}
    job_url="https://3m.wd1.myworkdayjobs.com/en-US/Search"

    _find_workdayjob("3M", url, req_data, job_url)


def find_medtronic():
    url = 'https://medtronic.wd1.myworkdayjobs.com/wday/cxs/medtronic/MedtronicCareers/jobs'
    req_data = { "appliedFacets": { "jobFamilyGroup": [ "2fe8588f35e84eb98ef535f4d738f243", "9f511399cde0412cb986049830df9cbd", "d5575fc80af44949aae34f0770ad3fcf", "4e8537909ca04133879bbd846eef97bf", "1aff29bdfacf4fc2becd9b28aba27c75", "a1fac31977894774aedd9a134ec054ad" ], "locationRegionStateProvince": [ "02f3984b69ba450080e456fe733f6741" ], "timeType": [ "7685fe50c6cf4872af78b98cd2b0fda1" ], "workerSubType": [ "a30d7e666c984cd592d4a0d4e941e4eb" ] } ,"limit":20,"offset":0}


    job_url = 'https://medtronic.wd1.myworkdayjobs.com/en-US/MedtronicCareers'
    _find_workdayjob("Medtronic", url, req_data, job_url)

def find_graco():
    url = 'https://graco.wd5.myworkdayjobs.com/wday/cxs/graco/Graco_Careers/jobs' 
    req_data = {"appliedFacets":{"locationRegionStateProvince":["02f3984b69ba450080e456fe733f6741"],"jobFamilyGroup":["761e42d70d2410bd5752a1269c7df904","761e42d70d2410bd5752bcb9fbb5f90e","761e42d70d2410bd5752a8c3e41df908","761e42d70d2410bd575278bfceadf8f2","761e42d70d2410bd575288024945f8f8"]},"limit":20,"offset":0,"searchText":""}
    job_url="https://graco.wd5.myworkdayjobs.com/en-US/Graco_Careers" 

    _find_workdayjob("Graco", url, req_data, job_url)


def find_solventum():
    url = 'https://healthcare.wd1.myworkdayjobs.com/wday/cxs/healthcare/Search/jobs' 
    req_data = {"appliedFacets":{"jobFamilyGroup":["bf1df20936a9100075842f5998f50000","bf1df20936a910007583d34ab47e0000","bf1df20936a910007584348470760000","bf1df20936a910007583d9fc5ca60000","bf1df20936a9100075843da4c8f90001","bf1df20936a910007583ad61fcde0000","bf1df20936a910007583b1ae459a0000","bf1df20936a910007583d2a278490000","bf1df20936a910007584479dd79b0000","bf1df20936a910007583a5c5261a0000","bf1df20936a9100075843d0a14640001"],"Location_Country":["bc33aa3152ec42d4995f4791a106ed09"],"Location_Region_State_Province":["02f3984b69ba450080e456fe733f6741"]},"limit":20,"offset":0,"searchText":""}
    job_url = "https://healthcare.wd1.myworkdayjobs.com/en-US/Search" 

    _find_workdayjob("Solventum", url, req_data, job_url)


def find_digikey():
    url = 'https://digikey.wd5.myworkdayjobs.com/wday/cxs/digikey/Digi-Key/jobs' 
    req_data = {"appliedFacets":{"locations":["593f581c9b370108b999a54f2c001702"]},"limit":20,"offset":0,"searchText":""}
    job_url = "https://digikey.wd5.myworkdayjobs.com/en-US/Digi-Key/job/"

    _find_workdayjob("Digikey", url, req_data, job_url)




def find_boston():
    url = 'https://bostonscientific.eightfold.ai/api/pcsx/search?domain=bostonscientific.com&query=&location=MN&start=0&sort_by=timestamp&filter_include_remote=1&filter_seniority=Manager&filter_seniority=Senior'
    response = requests.get(url)

    print("Boston\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    data = response.json()
    total_jobs = 0
    new_jobs = 0

    for job in data["data"]["positions"]:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="Boston",
                title=job["name"],
                link="https://bostonscientific.eightfold.ai" + job["positionUrl"],
                description="Department: " + job["department"] + " \n Location: " + job["standardizedLocations"][0] + " \n Work type: " + job["workLocationOption"],
                thedate=datetime.fromtimestamp(job['postedTs']),
                raw_data=json.dumps(job)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_maurices():
    url = 'https://careers.maurices.com/widgets'
    raw_data = '{"lang":"en_us","deviceType":"desktop","country":"us","pageName":"search-results","ddoKey":"eagerLoadRefineSearch","sortBy":"Most recent","subsearch":"","from":0,"jobs":true,"counts":true,"all_fields":["category","country","state","city","type","remote","phLocSlider"],"size":10,"clearAll":false,"jdsource":"facets","isSliderEnable":true,"pageId":"page19","siteType":"external","keywords":"","global":true,"selected_fields":{"category":["Technology","Sourcing & Production"]},"sort":{"order":"desc","field":"postedDate"},"locationData":{"place_id":"ChIJ_zcueH5SrlIRcgxY63a__ZA","sliderRadius":25,"aboveMaxRadius":false,"LocationUnit":"miles","placeVal":"Duluth, MN, USA"},"s":"1"}'
    job_url = 'https://careers.maurices.com/us/en/job/'

    response = requests.post(url,data=raw_data,headers=headers)

    print("Maurices\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    data = response.json()

    total_jobs = 0
    new_jobs = 0
    for job in data["eagerLoadRefineSearch"]["data"]["jobs"]:
        total_jobs = total_jobs + 1
        new_jobs = new_jobs + add_job(
                company="Maurices",
                title=job["title"],
                link= job_url + job["jobId"],
                description= job["descriptionTeaser"],
                thedate=datetime.strptime(job["postedDate"],"%Y-%m-%dT%H:%M:%S.000+0000"),
                raw_data=json.dumps(job)
                )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")





def find_gm():
    url = 'https://careers.generalmills.com/api/jobs?page=1&locations=Minneapolis,Minnesota,United%20States&categories=Brand%20Management%7CDigital%20%26%20Technology%7CGlobal%20Security%7CGlobal%20Shared%20Services%7CInternational%7CLogistics%7CMarketing%20Insights%7CStrategy%20and%20Growth&sortBy=relevance&descending=false&internal=false&deviceId=undefined&domain=generalmills.jibeapply.com&limit=100'
    response = requests.get(url,headers=headers)
    data = response.json()

    print("GM\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    for job in data["jobs"]:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="General Mills",
                title=job["data"]["title"],
                link="https://careers.generalmills.com/careers/jobs/" + job["data"]["slug"],
                description=job["data"]["description"],
                thedate=datetime.strptime(job["data"]["posted_date"],"%Y-%m-%dT%H:%M:%S+0000"),
                raw_data=json.dumps(job)
                )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_suncountry():

    url = 'https://recruiting2.ultipro.com/SUN1000SUNCO/JobBoard/5882c1c5-18e3-8740-5e61-37d8f7574d64/JobBoardView/LoadSearchResults' 
    req_data = {"opportunitySearch":{"Top":50,"Skip":0,"QueryString":"","OrderBy":[{"Value":"postedDateDesc","PropertyName":"PostedDate","Ascending":False}],"Filters":[{"t":"TermsSearchFilterDto","fieldName":37,"extra":None,"values":[]},{"t":"TermsSearchFilterDto","fieldName":4,"extra":None,"values":["f1e32b78-d7b5-5431-b34e-29c120ef4593","f8eb60ce-417f-55a5-a5da-9c69e6032983","0ea39e13-427f-5198-9751-436c219c643f","fd29af9e-c067-5436-9745-ae4e418ad7b2","2408e1a3-8c52-5be9-b915-d7e594f15cc8"]},{"t":"TermsSearchFilterDto","fieldName":5,"extra":None,"values":["cda63779-c205-4dac-a8c7-0f40e41f1e6d"]},{"t":"TermsSearchFilterDto","fieldName":6,"extra":None,"values":["1"]}]},"matchCriteria":{"PreferredJobs":[],"Educations":[],"LicenseAndCertifications":[],"Skills":[],"hasNoLicenses":False,"SkippedSkills":[]}}
    response = requests.post(url,data=json.dumps(req_data),headers=headers)

    print("Sun Country\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    data = response.json()
    total_jobs = 0
    new_jobs = 0
    for job in data["opportunities"]:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="SunCountry",
                title=job["Title"],
                link="https://recruiting2.ultipro.com/SUN1000SUNCO/JobBoard/5882c1c5-18e3-8740-5e61-37d8f7574d64/OpportunityDetail?opportunityId=" + job["Id"],
                description=job["BriefDescription"],
                thedate=datetime.strptime(job["PostedDate"],"%Y-%m-%dT%H:%M:%S.%fZ"),
                raw_data=json.dumps(job)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_minne():
    url = 'https://minneanalytics.org/jm-ajax/get_listings/'
    req_data = 'lang=&search_keywords=&search_location=&filter_job_type%5B%5D=full-time&filter_job_type%5B%5D=&per_page=10&orderby=featured&featured_first=false&order=DESC&page=1&remote_position=&show_pagination=false&form_data=search_keywords%3D%26search_location%3D%26filter_job_type%255B%255D%3Dfull-time%26filter_job_type%255B%255D%3D'
    response = requests.post(url,req_data,headers=headers)
    data = response.json()

    print("MINNE\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return


    total_jobs = 0
    new_jobs = 0
    results = f"{data['html']}"
    tree = etree.HTML(results)
    for e in tree.xpath('//li[contains(@class,"job_listing")]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="MinneAnalytics: " + e.xpath('.//div[@class="company"]/strong')[0].text,
                title=e.xpath('.//h3')[0].text,
                link=e.xpath('.//a')[0].get('href'),
                raw_data=etree.tostring(e,pretty_print=True),
                thedate=datetime.strptime(e.xpath('.//time[@datetime]')[0].get('datetime'),'%Y-%m-%d')
                )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_pearsonvue():
    url = 'https://pearson.jobs/jobs/ajax/joblisting/?location=Minnesota&r=25&num_items=20'
    response = requests.get(url)
    data = response.content

    total_jobs = 0
    new_jobs = 0
    results = data
    # print(results)
    tree = etree.HTML(results)
    for e in tree.xpath('//li[contains(@class,"direct_joblisting")]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="PearsonVue",
                title=e.xpath('.//span[@class="resultHeader"]')[0].text,
                link="https://pearson.jobs" + e.xpath('.//a')[0].get('href'),
                raw_data=etree.tostring(e,pretty_print=True)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_cargill():
    url = 'https://careers.cargill.com/en/search-jobs/results?ActiveFacetID=6252001-5037779-5038045&CurrentPage=1&RecordsPerPage=15&TotalContentResults=&Distance=50&RadiusUnitType=0&Keywords=&Location=&ShowRadius=False&IsPagination=False&CustomFacetName=&FacetTerm=6252001-5037779&FacetType=3&FacetFilters%5B0%5D.ID=6252001-5037779-5037649&FacetFilters%5B0%5D.FacetType=4&FacetFilters%5B0%5D.Count=7&FacetFilters%5B0%5D.Display=Minneapolis%2C+Minnesota%2C+United+States&FacetFilters%5B0%5D.IsApplied=true&FacetFilters%5B0%5D.FieldName=&FacetFilters%5B1%5D.ID=6252001-5037779&FacetFilters%5B1%5D.FacetType=3&FacetFilters%5B1%5D.Count=9&FacetFilters%5B1%5D.Display=Minnesota%2C+United+States&FacetFilters%5B1%5D.IsApplied=true&FacetFilters%5B1%5D.FieldName=&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=3&OrganizationIds=23251&PostalCode=&ResultsType=0&fc=&fl=&fcf=&afc=&afl=&afcf=&TotalContentPages=NaN'
    response = requests.get(url)
    data = response.json()

    print("Cargill\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    results = f"{data['results']}"
    tree = etree.HTML(results)
    # import pdb; pdb.set_trace()
    for e in tree.xpath('//a[@data-job-id]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="Cargill",
                title=e[0].text,
                link='https://careers.cargill.com/' + e.get('href'),
                raw_data=etree.tostring(e,pretty_print=True)
        )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_chrobinson():
    # Need a cookie!
    url = 'https://www.chrobinson.com/api/Sitecore/CoveoApi/GetCoveoConfig' 
    response = requests.post(url)
    data = response.json()

    api_key = data['CoveoAPIKey']

    url = 'https://chrobinsonproduction1v9rxz121.org.coveo.com/rest/search/v2?organizationId=chrobinsonproduction1v9rxz121'
    raw_data = '{"locale":"en-US","debug":false,"tab":"default","referrer":"https://www.chrobinson.com/en-us/about-us/careers/","timezone":"Europe/Paris","visitorId":"52f05f09-0e22-42ad-afd6-7eced34e7996","actionsHistory":[{"name":"Query","time":"\\"2024-12-08T23:06:48.953Z\\""},{"name":"Query","time":"\\"2024-12-08T23:05:31.227Z\\""},{"name":"Query","time":"\\"2024-12-08T23:04:24.191Z\\""},{"name":"Query","time":"\\"2024-12-08T23:03:16.276Z\\""}],"fieldsToInclude":["author","language","urihash","objecttype","collection","source","permanentid","date","filetype","parents","ec_price","ec_name","ec_description","ec_brand","ec_category","ec_item_group_id","ec_shortdesc","ec_thumbnails","ec_images","ec_promo_price","ec_in_stock","ec_rating","careers_job_requisitionid","careers_job_familygroup","careers_job_timetype","careers_job_business_unit","careers_job_title","careers_job_additional_jp_locations","careers_job_primarylocation","careers_job_remotetype","careers_job_primaryloc_displayname","careers_job_add_jploc_displayname"],"pipeline":"Career QP Production CD","q":"","enableQuerySyntax":false,"searchHub":"Career Jobs Prod Search CD","sortCriteria":"date descending","analytics":{"clientId":"52f05f09-0e22-42ad-afd6-7eced34e7996","clientTimestamp":"2024-12-08T23:06:48.978Z","documentReferrer":"https://www.chrobinson.com/en-us/about-us/careers/","originContext":"Search","actionCause":"facetDeselect","customData":{"coveoHeadlessVersion":"2.80.5","facetId":"careers_job_region","facetField":"careers_job_region","facetTitle":"Country","facetValue":"Mexico","coveoAtomicVersion":"2.79.0"},"documentLocation":"https://www.chrobinson.com/en-us/about-us/careers/search/#f-careers_job_region=Canada,Mexico,United%20States%20of%20America","capture":false},"queryCorrection":{"enabled":false,"options":{"automaticallyCorrect":"whenNoResults"}},"enableDidYouMean":true,"facets":[{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"Minnesota","state":"selected"},{"value":"Illinois","state":"idle"},{"value":"Missouri","state":"idle"},{"value":"Nuevo Le\xf3n","state":"idle"},{"value":"Ohio","state":"idle"},{"value":"Texas","state":"idle"},{"value":"Tennessee","state":"idle"},{"value":"Georgia","state":"idle"},{"value":"Arizona","state":"idle"},{"value":"California","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_state","field":"careers_job_state"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"In Office","state":"idle"},{"value":"Hybrid","state":"idle"},{"value":"Remote","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_remotetype","field":"careers_job_remotetype"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"Eden Prairie","state":"idle"},{"value":"Remote","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_city","field":"careers_job_city"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"Full time","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_timetype","field":"careers_job_timetype"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"C.H Robinson","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_brand","field":"careers_job_brand"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"Operations","state":"selected"},{"value":"Technology","state":"selected"},{"value":"Supply Chain","state":"selected"},{"value":"Reporting, Analysis & Data Science","state":"selected"},{"value":"Sales & Account Management Group","state":"idle"},{"value":"Finance","state":"idle"},{"value":"Human Resources","state":"idle"}],"freezeCurrentValues":false,"isFieldExpanded":false,"preventAutoSelect":false,"facetId":"careers_job_familygroup","field":"careers_job_familygroup"},{"filterFacetCount":true,"injectionDepth":1000,"numberOfValues":10,"sortCriteria":"occurrences","resultsMustMatch":"atLeastOneValue","type":"specific","currentValues":[{"value":"United States of America","state":"selected"},{"value":"Mexico","state":"idle"},{"value":"Canada","state":"selected"}],"freezeCurrentValues":true,"isFieldExpanded":false,"preventAutoSelect":true,"facetId":"careers_job_region","field":"careers_job_region"}],"numberOfResults":100,"firstResult":0,"facetOptions":{"freezeFacetOrder":true}}'
    #'
    custom_headers = headers.copy()
    custom_headers['Authorization'] = "Bearer " + api_key
    response = requests.post(url,data=raw_data,headers=custom_headers)
    data = response.json()

    print("CH Robinson\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    for job in data['results']:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="CH Robinson",
                title=job['title'],
                link=job['uri'],
                description=job['excerpt'],
                thedate=datetime.fromtimestamp(job['raw']['date']/1000),
                raw_data=json.dumps(job)
                )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")


def find_sherwin_williams():
    url = "https://ejhp.fa.us6.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields&finder=findReqs;siteNumber=CX_2,facetsList=LOCATIONS%3BWORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS,limit=25,lastSelectedFacet=LOCATIONS,locationId=300000063061424,selectedFlexFieldsFacets=%22AttributeChar6%7CFull-time%20regular%22,selectedLocationsFacet=300000063029024%3B300000063061424,sortBy=POSTING_DATES_DESC"
    response = requests.get(url)
    data = response.json()

    print("Sherwin Williams\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return


    total_jobs = 0
    new_jobs = 0
    for job in data['items'][0]['requisitionList']:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="Sherwin Williams",
                title=job['Title'],
                link= "https://ejhp.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2/job/" + job['Id'],
                description = job['ShortDescriptionStr'],
                thedate = datetime.strptime(job['PostedDate'],"%Y-%m-%d"),
                raw_data = json.dumps(job)
            )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_toro():
    url = 'https://jobs.thetorocompany.com/search-jobs/results?ActiveFacetID=Full+time&CurrentPage=1&RecordsPerPage=15&Distance=50&RadiusUnitType=0&Keywords=&Location=&ShowRadius=False&IsPagination=False&CustomFacetName=&FacetTerm=&FacetType=0&FacetFilters%5B0%5D.ID=8680048&FacetFilters%5B0%5D.FacetType=1&FacetFilters%5B0%5D.Count=7&FacetFilters%5B0%5D.Display=Administrative&FacetFilters%5B0%5D.IsApplied=true&FacetFilters%5B0%5D.FieldName=&FacetFilters%5B1%5D.ID=8419760&FacetFilters%5B1%5D.FacetType=1&FacetFilters%5B1%5D.Count=1&FacetFilters%5B1%5D.Display=Engineering+Management&FacetFilters%5B1%5D.IsApplied=true&FacetFilters%5B1%5D.FieldName=&FacetFilters%5B2%5D.ID=8419648&FacetFilters%5B2%5D.FacetType=1&FacetFilters%5B2%5D.Count=2&FacetFilters%5B2%5D.Display=Procurement&FacetFilters%5B2%5D.IsApplied=true&FacetFilters%5B2%5D.FieldName=&FacetFilters%5B3%5D.ID=6252001-5037779&FacetFilters%5B3%5D.FacetType=3&FacetFilters%5B3%5D.Count=9&FacetFilters%5B3%5D.Display=Minnesota%2C+United+States&FacetFilters%5B3%5D.IsApplied=true&FacetFilters%5B3%5D.FieldName=&FacetFilters%5B4%5D.ID=6252001-5037779-5018739&FacetFilters%5B4%5D.FacetType=4&FacetFilters%5B4%5D.Count=9&FacetFilters%5B4%5D.Display=Bloomington%2C+Minnesota%2C+United+States&FacetFilters%5B4%5D.IsApplied=true&FacetFilters%5B4%5D.FieldName=&FacetFilters%5B5%5D.ID=Full+time&FacetFilters%5B5%5D.FacetType=5&FacetFilters%5B5%5D.Count=8&FacetFilters%5B5%5D.Display=Full+time&FacetFilters%5B5%5D.IsApplied=true&FacetFilters%5B5%5D.FieldName=job_type&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=1&SortDirection=0&SearchType=5&PostalCode=&ResultsType=0&fc=&fl=&fcf=&afc=&afl=&afcf=' 
    response = requests.get(url)
    data = response.json()

    print("Toro\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    results = f"{data['results']}"
    # print(results)
    tree = etree.HTML(results)
    for e in tree.xpath('//li/a[@data-job-id]/..'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company="Toro",
                title=e.xpath('.//span[@class="job-title"]')[0].text,
                link="https://jobs.thetorocompany.com/" + e.xpath('.//a[@data-job-id]')[0].get('href'),
                raw_data=etree.tostring(e,pretty_print=True)
                )

    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")
    

def find_chs():
    url = 'https://jobs.chsinc.com/search-jobs/results?ActiveFacetID=8847520&CurrentPage=1&RecordsPerPage=100&TotalContentResults=&Distance=50&RadiusUnitType=0&Keywords=&Location=&ShowRadius=False&IsPagination=False&CustomFacetName=&FacetTerm=&FacetType=0&FacetFilters%5B0%5D.ID=8347600&FacetFilters%5B0%5D.FacetType=1&FacetFilters%5B0%5D.Count=3&FacetFilters%5B0%5D.Display=Environmental%2C+Health+%26+Safety&FacetFilters%5B0%5D.IsApplied=true&FacetFilters%5B0%5D.FieldName=&FacetFilters%5B1%5D.ID=8168544&FacetFilters%5B1%5D.FacetType=1&FacetFilters%5B1%5D.Count=3&FacetFilters%5B1%5D.Display=Information+Technology&FacetFilters%5B1%5D.IsApplied=true&FacetFilters%5B1%5D.FieldName=&FacetFilters%5B2%5D.ID=8168592&FacetFilters%5B2%5D.FacetType=1&FacetFilters%5B2%5D.Count=9&FacetFilters%5B2%5D.Display=Production+%26+Operations&FacetFilters%5B2%5D.IsApplied=true&FacetFilters%5B2%5D.FieldName=&FacetFilters%5B3%5D.ID=8174896&FacetFilters%5B3%5D.FacetType=1&FacetFilters%5B3%5D.Count=1&FacetFilters%5B3%5D.Display=Quality+Management&FacetFilters%5B3%5D.IsApplied=true&FacetFilters%5B3%5D.FieldName=&FacetFilters%5B4%5D.ID=8168752&FacetFilters%5B4%5D.FacetType=1&FacetFilters%5B4%5D.Count=1&FacetFilters%5B4%5D.Display=Supply+Chain+%26+Procurement&FacetFilters%5B4%5D.IsApplied=true&FacetFilters%5B4%5D.FieldName=&FacetFilters%5B5%5D.ID=8168608&FacetFilters%5B5%5D.FacetType=1&FacetFilters%5B5%5D.Count=1&FacetFilters%5B5%5D.Display=Trading&FacetFilters%5B5%5D.IsApplied=true&FacetFilters%5B5%5D.FieldName=&FacetFilters%5B6%5D.ID=8847520&FacetFilters%5B6%5D.FacetType=1&FacetFilters%5B6%5D.Count=1&FacetFilters%5B6%5D.Display=Union&FacetFilters%5B6%5D.IsApplied=true&FacetFilters%5B6%5D.FieldName=&FacetFilters%5B7%5D.ID=6252001-5037779&FacetFilters%5B7%5D.FacetType=3&FacetFilters%5B7%5D.Count=18&FacetFilters%5B7%5D.Display=Minnesota%2C+United+States&FacetFilters%5B7%5D.IsApplied=true&FacetFilters%5B7%5D.FieldName=&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=1&SortDirection=1&SearchType=5&PostalCode=&ResultsType=0&fc=&fl=&fcf=&afc=&afl=&afcf=&TotalContentPages=NaN' 
    response = requests.get(url)
    data = response.json()


    print("CHS\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0

    results = f"{data['results']}"
    tree = etree.HTML(results)
    for e in tree.xpath('//li/a[@data-job-id]/..'):
        add_job(
                company="CHS",
                title=e.xpath('.//h2[@class="search-list-heading"]')[0].text,
                link='https://jobs.chsinc.com' + e.xpath('.//a[@data-job-id]')[0].get('href'),
                thedate = datetime.strptime(e.xpath('.//span[@class="job-date-posted"]')[0].text,'%m/%d/%Y'),
                raw_data=etree.tostring(e,pretty_print=True)
        )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_target():
    url = 'https://corporate.target.com/api/jobsearch'
    data = 'lat=44.98526&lon=-93.26984&maxdistance=40.225&currentPage=1&q=&hierarchy=Corporate%7C%7CSupply%20Chain&remotetype=&jobcategories=Administrative%20Support%7C%7CBusiness%20Operations%7C%7CGlobal%20Supply%20Chain%20%26%20Logistics%7C%7CMarketing%20%26%20Digital%7C%7CMerchandising%20%26%20Global%20Sourcing%7C%7CService%20Centers%20%26%20Business%20Enablement%7C%7CSupply%20Chain%20Leadership%7C%7CTarget%20Tech&workersubtype=Regular&scheduletype=Full-time&basepayfrequency=&organization=&locationname=&jobaddress=&profiles=&city=&state=&country=&internshipType=&jobfamily=&subFamilies=&culture=en-us&filtercondition=&compgrade='

    response = requests.post(url,data=data,headers=headers)

    print("Target\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)

    data = response.json()
    total_jobs = 0
    new_jobs = 0

    for job in data['results']:
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company = "Target",
                title = job['document']['title'],
                link = 'https://corporate.target.com' + job['document']['url'],
                thedate = datetime.strptime(job['document']['dateposted'],"%Y-%m-%dT%H:%M:%SZ"),
                raw_data = json.dumps(job)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_lomn():
    url = "https://www.governmentjobs.com/careers/home/index?agency=lmnc&sort=PostingDate&isDescendingSort=true&_=1733906745284"
    custom_headers = headers.copy()
    custom_headers['X-Requested-With'] = "XMLHttpRequest"
    response = requests.get(url,headers=custom_headers)

    print("LOMN\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    tree = etree.HTML(response.content)
    for e in tree.xpath('//li[@data-job-id]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company = "League of MN Cities",
                title = e.xpath('.//a[@class="item-details-link"]')[0].text,
                link = "https://www.governmentjobs.com/" + e.xpath('.//a[@class="item-details-link"]')[0].get('href'),
                description = e.xpath('.//ul[@class="list-meta"]')[0].text + "\n\n" + e.xpath('.//div[@class="list-entry"]')[0].text,
                raw_data=etree.tostring(e,pretty_print=True)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")


def find_northern_tool():
    url = "https://careers.northerntool.com/search/jobs/?q=&cfm3[]=Customer%20Contact%20Centers&cfm3[]=Corporate&branch=search-corporate-headquarters-jobs"
    custom_headers = headers.copy()
    response = requests.get(url,headers=custom_headers)


    print("Northern Tool\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    total_jobs = 0
    new_jobs = 0
    tree = etree.HTML(response.content)
    for e in tree.xpath('//div[@class="jobs-section__item padded-v-small"]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company = "Northern Tool",
                title = e.xpath('.//h2/a')[0].text,
                link = e.xpath('.//a')[0].get('href'),
                thedate=datetime.strptime(e.xpath('.//time')[0].get('datetime'),"%Y-%m-%d"),
                description = re.sub(r'\n ',' ',re.sub(r'^ +','',re.sub(r' +',' ',' '.join(e.xpath('.//div[@class="large-4 columns"]/descendant-or-self::*/text()'))))),
                raw_data=etree.tostring(e,pretty_print=True)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")

def find_wagner():
    url = "https://careers.wagner-group.com/go/All-Jobs/3844501/?q=&q2=&alertId=&facility=&title=&location=MN&department="
    custom_headers = headers.copy()
    response = requests.get(url,headers=custom_headers)

    print("Wagner\t",end="")
    if response.ok:
        pass
    else:
        print(response.status_code)
        return

    tree = etree.HTML(response.content)
    total_jobs = 0
    new_jobs = 0
    for e in tree.xpath('//tr[@class="data-row"]'):
        total_jobs = total_jobs + 1

        new_jobs = new_jobs + add_job(
                company = "Wagner",
                title = e.xpath('.//td[@headers="hdrTitle"]/span/a')[0].text,
                link = "https://careers.wagner-group.com/" + e.xpath('.//td[@headers="hdrTitle"]/span/a')[0].get('href'),
                description = e.xpath('.//td[@headers="hdrTitle"]/span/a')[0].text,
                raw_data=etree.tostring(e,pretty_print=True)
                )
    print(str(total_jobs) + " postings (" + str(new_jobs) + " new)")


# Send new_jobs to Slack
def send_slack_notification():

    # import pdb; pdb.set_trace()
    companies = ', '.join(new_job_meta.keys())

    url = 'https://hooks.slack.com/services/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'

    tot = 0
    for count in new_job_meta:
        tot = tot + new_job_meta[count]

    if tot == 0:
        return;

    cols = {
            'id':0,
            'title':1,
            'desc':2,
            'company': 3,
            'joblink':4,
            'thedate':5,
            'applied':6,
            'raw_data':7
            }

    req_data = {
                "blocks": [
                    {
                        "type":"header",
                        "text": {
                            "type": "plain_text",
                            "text": ("JobBot! I found " + str(tot) + " new posting at " + companies + "!")[:150]
                        }
                    },
                    {
                        "type":"divider"
                    },
                    {
                        "type":"section",
                        "text":{
                            "type":"mrkdwn",
                            "text": ("https://convenienturl.com/jobbot/")[:200]
                            },
                    }
                ]
            }
    response = requests.post(url,data=json.dumps(req_data),headers=headers)


#    for job in new_jobs:
#
#        req_data = {
#                    "blocks": [
#                        {
#                            "type":"header",
#                            "text": {
#                                "type": "plain_text",
#                                "text": ("JobBot! " + job[cols['company']] + " | " + job[cols['title']])[:150]
#                            }
#                        },
#                        {
#                            "type":"divider"
#                        },
#                        {
#                            "type":"section",
#                            "text":{
#                                "type":"mrkdwn",
#                                "text": ("<" + job[cols['joblink']] + "|" + job[cols['title']] + "> \n\n" + job[cols['desc']])[:200]
#                                },
#                            "accessory": {
#                                    "action_id": "job-" + str(job[cols['id']]),
#                                    "type": "static_select",
#                                    "placeholder": {
#                                        "type": "plain_text",
#                                        "text": "Select an item"
#                                    },
#                                    "options": [
#                                        {
#                                        "text": {
#                                            "type": "plain_text",
#                                            "text": "Dismiss Job"
#                                        },
#                                        "value": "1"
#                                        },
#                                        {
#                                        "text": {
#                                            "type": "plain_text",
#                                            "text": "Keep Job For Later"
#                                        },
#                                        "value": "0"
#                                        }
#                                    ]
#                                }
#                        }
#                    ]
#                }
#        response = requests.post(url,data=json.dumps(req_data),headers=headers)

def find_jobs():

    proc = []

    # # workdayjob
    # for fn in (find_3m, find_medtronic, find_graco, find_solventum, find_digikey ): 
    #     p = Process(target=fn)
    #     p.start()
    #     proc.append(p)

    # # better workday
    # for fn in ( find_trane, find_philips, find_ecolab, find_honeywell, find_lol):
    #     p = Process(target=fn)
    #     p.start()
    #     proc.append(p)


    # # Friendly JSON
    # for fn in ( find_boston, find_maurices):
    #     p = Process(target=fn)
    #     p.start()
    #     proc.append(p)


    # # Their own thing
    # for fn in ( find_gm, find_suncountry, find_sherwin_williams, find_minne, find_pearsonvue, find_cargill, find_chrobinson, find_lomn, find_northern_tool, find_wagner):
    #     p = Process(target=fn)
    #     p.start()
    #     proc.append(p)


    # # Very similar, but different - returns JSON inside of HTML
    # for fn in ( find_chs, find_toro ):
    #     p = Process(target=fn)
    #     p.start()
    #     proc.append(p)

    for p in proc:
        p.join()

    # find_target()

    # TODO:
    # State of MN
    # City of Oakdale etc. 
    # Delta
    # Chewy

    # Optum 
    # https://www.northerntool.com/categories/hand-tools
    # https://bellinternationallabs.com/


find_jobs()

tot = 0
for count in new_job_meta:
    tot = int(tot) + int(new_job_meta[count])

send_slack_notification()
print("Found " + str(tot) + " new jobs")
