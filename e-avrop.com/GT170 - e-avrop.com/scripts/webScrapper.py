from gtOperations.dbManager import DbManager
from gtOperations.operations import Operations as ops 
import requests
import datetime
import pandas
from requests.exceptions import URLRequired
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC, wait
from gtOperations.translator import DataTranslator as translate

class WebScrapper:
    publishStartDate = ""
    publishEndDate = ""
    dataCount = 0
    expiryDate = ""
    url = ""
    header = {
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    __dataObj = []
    __finalDataObj = []

    def __init__(self,publishStartDate,publishEndDate,expiryDate,dataCount):
        self.publishStartDate = publishStartDate 
        self.publishEndDate = publishEndDate 
        self.expiryDate = expiryDate
        self.dataCount = dataCount
        self.url = ""
        self.cookies = ""
        self.dataPamarameter = ""
        self.skipCount = 0
    
    #wait till a selector gets load. This function is necessary while using selenium
    def waitTillElementLoadByCSSSelector(self,selector):
        wait = WebDriverWait(self.driver,0)
        return wait.until(EC.visibility_of(self.driver.find_element(By.CSS_SELECTOR,selector)))
    

    def getData(self):
        try:
            print("Fetching Data Starts...")
            self.driver = webdriver.Chrome('C:\\chromedriver\chromedriver.exe')
            # Setup wait for later
            wait = WebDriverWait(self.driver,0)
            # Store Original Window ID
            originalWindowID = self.driver.current_window_handle
            self.url = 'https://www.e-avrop.com/e-Upphandling/Default.aspx'
            # get is used to navigate and wait till it gets loaded
            self.driver.get(self.url)
            self.waitTillElementLoadByCSSSelector('#mainContent_tenderGridView')
            self.driver.execute_script('document.querySelector("#mainContent_tenderGridView > tbody > tr.headerNeutral > th:nth-child(2) > a").click()')
            pageLen = self.driver.execute_script('return document.querySelector("#mainContent_tenderGridView > tbody > tr.GridViewPager > td > table > tbody > tr > td:nth-last-child(1) > a").innerText')
            incPage = 0
            pageNo = 1
            fetchCount = 0
            responseData = []
            isLoop = True
            while (pageNo != pageLen and isLoop):
                if(incPage!=0):
                    self.driver.execute_script(f'document.querySelector("#mainContent_tenderGridView > tbody > tr.GridViewPager > td").querySelectorAll("tbody > tr > td")[{incPage}].querySelector("a").click()')
                    self.waitTillElementLoadByCSSSelector('#mainContent_tenderGridView')
                trLen = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline").length')
                #fetch Data
                for i in range(0,trLen):
                    fetchCount+=1
                    print(f'Fetching Link No. {fetchCount}')
                    tenderTitle = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(1) > a").innerText')
                    tenderDocLink = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(1) > a").href')
                    publishDate = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(2)").innerText')
                    orgName = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(3)").innerText')
                    cpvValue = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(4)").innerText')
                    deadline = self.driver.execute_script(f'return document.getElementById("mainContent_tenderGridView").querySelectorAll("tr.rowline")[{i}].querySelector("td:nth-child(5)").innerText')
                    if(publishDate!='' and publishDate!='9999-12-31' and deadline != 'Ongoing bidding'):
                        publishDate = ops.convertStringToDate(publishDate) if publishDate!='' else ''
                        if(publishDate>=ops.convertStringToDate(self.publishStartDate) and publishDate<=ops.convertStringToDate(self.publishEndDate)):
                            deadline = deadline.split('\n')[0] if deadline!='' else ''
                            responseData.append({
                                'title': tenderTitle,
                                'org_name':orgName,
                                'deadline': deadline,
                                'tender_doc_link':tenderDocLink,  
                                'cpv_value':cpvValue                  
                            })
                        else:
                            isLoop = False
                            break
                #inc
                incPage = self.driver.execute_script(f'return document.querySelector("#mainContent_tenderGridView > tbody > tr.GridViewPager > td").querySelector("tbody > tr > td > span").parentElement.cellIndex')
                incPage = int(incPage) + 1
                if(incPage!=0):
                    pageLen = self.driver.execute_script('return document.querySelector("#mainContent_tenderGridView > tbody > tr.GridViewPager > td > table > tbody > tr > td:nth-last-child(1) > a").innerText')
                    pageNo = self.driver.execute_script(f'return document.querySelector("#mainContent_tenderGridView > tbody > tr.GridViewPager > td").querySelectorAll("tbody > tr > td")[{incPage}].querySelector("a").innerText')
                print(f'incPage : {incPage} | pageNo : {pageNo} | pageLen : {pageLen}' )
            #end loop
            self.__dataObj = responseData
            print(f"{len(self.__dataObj)} Data Fetched And Moved To Formating..")
            self.__formatData()
        except Exception as e:
            print(e)

    # Format Data To Insert
    def __formatData(self):
        try:
            i=1
            for data in self.__dataObj :
                print(f"Record {i}  is Under Formating out of {len(self.__dataObj)} records")
                title = data['title']
                docLink = data['tender_doc_link'] 
                orgName = data['org_name'] 
                print(f"Tender Title : {str(title)}")
                print(f"Tender Link : {str(docLink)}")
                print(f"Org Name : {str(orgName)}")
                deadline = data['deadline']
                currentDate = str(datetime.datetime.now()).split()[0]
                cpvList = data['cpv_value']
                cpvList = cpvList.split('\\n')
                cpvValue = ''
                for cpv in cpvList:
                    cpvValue += f'{cpv.split(":")[0]},'
                cpvValue = cpvValue[:-1]
                print(f'CPV VALUE : {cpvValue}')
                if(deadline!="" and (ops.convertStringToDate(deadline) < ops.convertStringToDate(currentDate))):
                    self.skipCount += 1
                    print(f"This Record Is Skipped As is Deadline {deadline} is Expired")
                    continue 
                db = DbManager("Masterdb_AMS")
                if(db.checkDuplicateByTenderDocLink(docLink,"e-avrop.com")):
                    self.skipCount += 1 
                    print(f"Skipped This Record As It's Duplicate. Total Skiped Uptill Now : {self.skipCount}")
                    continue
                self.url = docLink
                self.driver.get(self.url)
                self.waitTillElementLoadByCSSSelector('#mainContent_main')
                iFrame = self.driver.execute_script('return document.querySelector("iframe").src')
                self.url = iFrame
                self.driver.get(self.url)
                self.waitTillElementLoadByCSSSelector('form')
                tenderNoticeNo = ''
                tenderNoticeNo = self.driver.execute_script('''
                    if(document.querySelector("#container_mainContent_ContractNotice .notice-card .row:nth-child(1) > .align-self-start:nth-child(1) > .n-segment > span")){
                        return document.querySelector("#container_mainContent_ContractNotice .notice-card .row:nth-child(1) > .align-self-start:nth-child(1) > .n-segment > span").innerText;
                    }else {
                        return "";
                    }
                ''') #tenderNoticeNo end
                
                tenderDescription = self.driver.execute_script('''
                if(document.querySelector("#container_mainContent_ContractNotice .notice-card .row:nth-child(1) > .align-self-start:nth-child(5) > .n-segment > div")){
                    return document.querySelector("#container_mainContent_ContractNotice .notice-card .row:nth-child(1) > .align-self-start:nth-child(5) > .n-segment > div").innerText;
                } else{
                    return ''
                }
                ''') #tenderDescription end
                print(f'Tender Notice No  : {tenderNoticeNo}')
                print(f'Tender Description :  {tenderDescription}')
                isBtn = self.driver.execute_script('''
                    if(document.querySelector("button[aria-label=\'Show announcement\']")){
                        document.querySelector("button[aria-label=\'Show announcement\']").click();
                        return true;
                    }
                    else{
                        return false;
                    }
                ''')
                orgAddress = ''
                orgEmail = ''
                orgUrl = ''
                orgContactPerson = ''
                country = 'Sweden' 
                if(isBtn):
                    self.waitTillElementLoadByCSSSelector("[name = 'reactModal']")
                    if(self.driver.execute_script("return document.querySelectorAll('.notice-body.notice-data > div:not(.section-part) > .notice-field:not(.notice-field.empty)').length") != 0):
                        print("IN 1")
                        orgAddress = self.driver.execute_script("return document.querySelectorAll('.notice-body.notice-data > div:not(.section-part) > .notice-field:not(.notice-field.empty)')[2].innerText.split(\'\\n\')[1]")
                        pincode = self.driver.execute_script("return document.querySelectorAll('.notice-body.notice-data > div:not(.section-part) > .notice-field:not(.notice-field.empty)')[3].innerText.split('\\n')[1]")
                        pincode = f'<br/>Pincode : {pincode}' if(pincode!='') else ''
                        town = self.driver.execute_script("return document.querySelectorAll('.notice-body.notice-data > div:not(.section-part) > .notice-field:not(.notice-field.empty)')[4].innerText.split('\\n')[1]") 
                        town = f'<br/>Town : {town}' if(town!='') else ''
                        orgAddress = orgAddress+f' {pincode} {town}'
                    elif(self.driver.execute_script("return document.querySelectorAll('.ted-notice .mlioccur> .txtmark').length") != 0):
                        print("In")
                        addressDoc = self.driver.execute_script("return document.querySelectorAll('.ted-notice .mlioccur> .txtmark')[0].innerText")
                        addressDoc = str(orgAddress).split('\n')
                        pincode = ''
                        town = ''
                        phone = ''
                        for address in addressDoc:
                            if(address.find('Postadress')):
                                orgAddress = address.split(':')[1] if(address.find(":")!=-1) else ''
                            elif(address.find('Ort')):
                                town = address.split(':')[1] if(address.find(":")!=-1) else ''
                                town = f'<br/>Town : {town}' if(town!='') else ''
                            elif(address.find('Postnummer')):
                                pincode = address.split(':')[1] if(address.find(":")!=-1) else ''
                                pincode = f'<br/>Pincode : {pincode}' if(pincode!='') else ''
                            elif(address.find('Kontaktperson')):
                                orgContactPerson = address.split(':')[1] if(address.find(":")!=-1) else ''
                            elif(address.find('E-post')):
                                orgEmail = address.split(':')[1] if(address.find(":")!=-1) else ''
                            elif(address.find('Telefon')):
                                phone = address.split(':')[1] if(address.find(":")!=-1) else ''
                                phone = f'<br/>Phone : {phone}' if(phone!='') else ''
                            elif(address.find('Allmän adress')):
                                orgUrl = address.split(':')[1] if(address.find(":")!=-1) else ''
                        orgAddress = orgAddress+f' {pincode} {town} {phone}'
                    orgAddress = f'Country : {country}' if(orgAddress=='') else f'{orgAddress} <br/>Country : {country}'
                    print(f'orgAddress : {orgAddress}')
                self.__finalDataObj.append({
                    "file_id": "",
                    "tender_notice_no" : tenderNoticeNo,
                    "tender_title":title,
                    "tender_details":'',
                    "org_country":"SE",
                    "org_name":orgName,
                    "org_address":orgAddress,
                    "org_email":orgEmail,
                    "org_url":orgUrl,
                    "org_contact_person":orgContactPerson,
                    "est_cost":'',
                    "deadline":deadline,
                    "currency":'',
                    "cpv_value":'',
                    "source":"e-avrop.com",
                    "domain_name":"www.e-avrop.com",
                    "tender_doc_link": docLink,
                    "file_name":"",
                    "region_id":"Rg00009",
                    "ext1":"",
                    "document_link_attached":''
                }) 
                i += 1

        except Exception as e:
            print(e)

    def insertRecord(self):
        print("Inserting Record")
        db = DbManager("Masterdb_AMS")
        dbFinal = DbManager("Masterdb_AMSFinal")
        duplicateCount = 0
        skipCount = self.skipCount
        totalData = len(self.__finalDataObj)
        insertCount = 0
        incRec = 0
        for data in self.__finalDataObj :
            incRec+=1
            print(f"Record Count {incRec} of {totalData}")
            if(not(db.checkDuplicateByTenderDocLink(data['tender_doc_link'],"e-avrop.com"))):
                if(not(db.checkDuplicateByTenderNoticeNo(data['tender_notice_no'],data['org_country'],data['deadline']))):
                    print(str(insertCount)+" Record Inserted")
                    nonTranslatedData = {
                    "tender_title" : ops.cutString(data["tender_title"],200),
                    "tender_details": ops.cutString(data["tender_details"],3000),
                    "org_name": data["org_name"],
                    "org_address":data["org_address"],
                    "org_contact_person":data["org_contact_person"],
                    }
                    try:
                        combinedTranslateString = data['tender_title']+str(" <a> ")+data['org_name']+" <a> "+data['org_address']+" <a> "+data["org_contact_person"]
                        combinedTranslateString = translate.gtranslateData(combinedTranslateString)
                        combinedTranslateString = str(combinedTranslateString).upper()
                        combinedTranslateString = str(combinedTranslateString).split("<A>")      
                        data["tender_title"] = combinedTranslateString[0].capitalize().strip()
                        data["org_name"] = combinedTranslateString[1].capitalize().strip()
                        data["org_address"] = combinedTranslateString[2].capitalize().strip()
                        data["org_contact_person"] = combinedTranslateString[3].capitalize().strip()
                    except IndexError as e:
                        data["tender_title"] = translate.gtranslateData(data['tender_title']) if data["tender_title"]!='' else ''
                        data["org_name"] = translate.gtranslateData(data['org_name']) if data["org_name"]!='' else ''
                        data["org_address"] = translate.gtranslateData(data['org_address']) if data["org_address"]!='' else ''
                        data["org_contact_person"] = translate.gtranslateData(data['org_contact_person']) if data["org_contact_person"]!='' else ''
                    if(data["tender_details"]!=""):
                        data["tender_details"] = translate.gtranslateData(nonTranslatedData['tender_details'])
                        data["tender_details"] = ops.removeSpecialCharacters(data["tender_details"])
                    data["tender_title"] = ops.removeSpecialCharacters(data["tender_title"])
                    data["org_name"] = ops.removeSpecialCharacters(data["org_name"])
                    data["org_address"] = ops.removeSpecialCharacters(data["org_address"])
                    data["org_contact_person"] = ops.removeSpecialCharacters(data["org_contact_person"])
                    fileName = ops.getCurrentDateTimeForFileName()
                    data["file_id"] = fileName 
                    data["file_name"] = "Z://GT170"+fileName+".html" 
                    db.createDocHtml(data,nonTranslatedData)
                    isInsert = db.insert(data)
                    isInsertFinal = dbFinal.insert(data)
                    if isInsert and isInsertFinal :
                        insertCount += 1
                else:
                    duplicateCount+=1
                    print(f"Record Skiped Due To Duplicate Count: {duplicateCount}")
            else:
                duplicateCount+=1
                print(f"Record Skiped Due To Duplicate Count: {duplicateCount}")
        print("Total Record : ",totalData)
        print("Skip Count : ",skipCount)
        print("Duplicate Count : ",duplicateCount)
        print("insert Count : ",insertCount)


