from time import time
from scripts.webScrapper import WebScrapper
import datetime
from datetime import datetime, timedelta
# required Config
dataCount = 0 #if 0 the process donot need dataCount
print("Source : e-avrop.com")
input_var = int(input("\nEnter the days back in interger type : eg(0,1,2,3,4,5...) : \n"))
executionStartTime = time()
publishStartDate = str((datetime.today()- timedelta(input_var)).strftime('%Y-%m-%d'))
publishEndDate = str((datetime.today()).strftime('%Y-%m-%d'))
expiryDate = datetime.today().strftime("%Y-%m-%d")
webScrapObj = WebScrapper(publishStartDate,publishEndDate,expiryDate,dataCount)
webScrapObj.getData()
webScrapObj.insertRecord()
executionTime = time()-executionStartTime
print(f"Time Taken To Execute {int(executionTime/60)}min {int(executionTime%60)}sec")
print("Source : e-avrop.com")
quitTxt = ""
print("Press Q or q to Quit")
while str(quitTxt).lower != str("q").lower:
    quitTxt = str(input("Please Input : "))
exit(0)