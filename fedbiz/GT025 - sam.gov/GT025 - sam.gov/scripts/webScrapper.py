from gtOperations.dbManager import DbManager
from gtOperations.translator import DataTranslator
from gtOperations.operations import Operations as ops
import requests
import pandas

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
        self.url = f"https://sam.gov/api/prod/sgs/v1/search/?api_key=null&random=1623147022153&index=opp&page=0&sort=-modifiedDate&size=100&mode=search&responseType=json&is_active=true&publish_date.to={self.publishEndDate}+05:30&publish_date.from={self.publishStartDate}+05:30"
    
    #get Respose Of Data From Website
    def getResponse(self):
        try:
            response = requests.get(self.url, headers=self.header)
            if response.status_code == 200:
                return response
        except Exception as e:
            print(e)
        print('Error status code', response.status_code, response.text)

    # fetches the Data From Website
    def getData(self):
        try:
            print("Please Wait Will We Are Fetching Data...")
            responseData = self.getResponse()
            responseData = responseData.json()
            count = int(responseData['page']['totalPages'])
            if(count==0):
                ops.alertMessage("No Records Avaliable.",True)
            self.__dataObj = responseData['_embedded']['results']
            for i in range(1,count):
                self.url = f"https://sam.gov/api/prod/sgs/v1/search/?api_key=null&random=1623162365527&index=opp&page={i}&sort=-modifiedDate&size={self.dataCount}&mode=search&responseType=json&is_active=true&publish_date.to={self.publishEndDate}+05:30&publish_date.from={self.publishStartDate}+05:30"
                requestData = self.getResponse()
                responseJsonData = requestData.json()
                self.__dataObj.extend(responseJsonData['_embedded']['results'])                
            print(f"{len(self.__dataObj)} Data Fetched And Moved To Formating..")
            self.__formatData()
        except Exception as e:
            ops.alertMessage(e,True)
    # Format Data To Insert
    def __formatData(self):
        try:
            i=1
            self.skipCount = 0
            for data in self.__dataObj :
                print(f"Record {i}  is Under Formating out of {len(self.__dataObj)} records")
                print(f"Tender Title : {data['title']}")
                print(f"Tender No : {data.get('solicitationNumber','')}")
                i+=1
                isAward = data.get("type","")
                if(isAward!="" and isAward['code']=="a"):
                    self.skipCount += 1
                    print("**This Tender is an award so we have skipped it.**\n")
                    continue
                content = data['descriptions']
                if(len(content) == 0):
                    content = ""
                else :
                    content = content[len(content)-1]['content']
                    if(content.find('This Is Only a Test') != -1 ):
                        self.skipCount += 1
                        print("**This Tender is Just For Testing so we have skipped it.**\n")
                        continue
                #fetching main data 
                self.url = f"https://sam.gov/api/prod/opps/v2/opportunities/{data['_id']}?random=1623230991202"
                requestData = self.getResponse()
                #main data fetched in responseJsonData
                responseJsonData = requestData.json()
                solicitation = responseJsonData['data'].get("solicitation","")
                deadline = ""
                deadline = solicitation.get("deadlines","") if(solicitation!="") else ""
                deadline = deadline.get("response","") if(deadline!="") else ""
                if(deadline!=""):
                    deadline = str(deadline).split("T")[0] if (deadline != "") else ""
                    year = deadline
                    if(str(year) != "" ):
                        year = str(year).split("-")[0]
                        deadline = deadline if(int(year) >= 2021) else ""
                attachedDocStringLink = f"<a href='https://sam.gov/api/prod/opps/v3/opportunities/{data['_id']}/resources/download/zip?api_key=null&token='>Download Attachment</a>"
                contactObj = responseJsonData['data'].get('pointOfContact',"")
                contactNo = ""
                orgEmail = ""
                orgContactPerson =""
                if(len(contactObj)>0):
                    for contact in contactObj :
                        contactNo += str(contact.get('phone',""))+"," 
                        orgEmail +=str(contact.get('email',""))+","
                        orgContactPerson+=str(contact.get('fullName',""))+","
                
                contactNo = contactNo[:-1]
                orgEmail = orgEmail[:-1]
                orgContactPerson = orgContactPerson[:-1]

                orgId = responseJsonData['data']['organizationId']
                #geting data for address
                self.url = f"https://sam.gov/api/prod/federalorganizations/v1/organizations/{orgId}?random=1623233179351&sort=name"
                orgInfo = self.getResponse().json()
                orgName = orgInfo['_embedded'][0]['org']['l1Name']
                orgAddressObj = orgInfo['_embedded'][0]['org'].get('orgAddresses',"")
                orgAddress=""
                if(orgAddressObj!=""):
                    for address in orgAddressObj:
                        orgAddress += str(address['street_address'])+","+str(address['street_address_2'])+","+str(address['city'])+","+str(address['state'])+"-"+str(address['zipcode'])+"<br/>"
                if(orgContactPerson!=""):
                    orgAddress+="Contact Person : <br/>"+orgContactPerson+"<br/>"
                if(contactNo!=""):
                    orgAddress+=contactNo

                orgName = ops.removeSpecialCharacters(orgName)
                orgAddress = ops.removeSpecialCharacters(orgAddress)
                tenderDetails = responseJsonData['description'][0]['body'] if len(responseJsonData['description'])>0 else ""
                tenderDetails = ops.removeSpecialCharacters(tenderDetails)
                tenderDetails = ops.removeHtmlTags(tenderDetails)
                self.__finalDataObj.append({
                    "file_id": "",
                    "tender_notice_no" : data.get('solicitationNumber',''),
                    "tender_title":data['title'],
                    "tender_details":tenderDetails,
                    "org_country":"US",
                    "org_name":orgName,
                    "org_address":orgAddress,
                    "org_email":orgEmail,
                    "org_url":"",
                    "org_contact_person":"",
                    "est_cost":"",
                    "deadline":deadline,
                    "currency":"",
                    "cpv_value":"",
                    "source":"FedBiz",
                    "domain_name":"sam.gov",
                    "tender_doc_link": f"https://sam.gov/opp/{data['_id']}/view" ,
                    "file_name":"",
                    "region_id":"Rg00005",
                    "ext1":"",
                    "document_link_attached":attachedDocStringLink
                })               
            print(pandas.DataFrame(self.__finalDataObj))
            print(len(self.__dataObj),"*********************")
        except Exception as e:
            ops.alertMessage(e,True)

    def insertRecord(self):
        print("Inserting Record")
        db = DbManager("Masterdb_AMS")
        dbFinal = DbManager("Masterdb_AMSFinal")
        duplicateCount = 0
        skipCount = self.skipCount
        totalData = len(self.__finalDataObj)
        insertCount = 0
        for data in self.__finalDataObj :
            if(not(db.checkDuplicateByTenderNoticeNo(data['tender_notice_no'],data['org_country'],data['deadline'],data["source"]))):
                print(str(insertCount)+" Record Inserted")
                fileName = ops.getCurrentDateTimeForFileName()
                data["file_id"] = fileName 
                data["file_name"] = "Z://GT025"+fileName+".html" 
                db.createDocHtml(data)
                isInsert = db.insert(data)
                isInsertFinal = dbFinal.insert(data)
                if isInsert and isInsertFinal :
                    insertCount += 1
            else:
                duplicateCount += 1
            ops.holdProcess(0.5)        
        print("Total Record : ",totalData)
        print("Skip Count : ",skipCount)
        print("Duplicate Count : ",duplicateCount)
        print("insert Count : ",insertCount)