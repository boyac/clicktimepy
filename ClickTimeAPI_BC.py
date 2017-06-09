# -*- coding: utf-8 -*-
# @Author: boyac
# @Date:   2017-04-18 21:41:10
# @Last Modified by:   Boya Chiou
# @Last Modified time: 2017-06-08 20:15:57

import httplib
import base64
import copy
import json
import datetime
import requests
import os
import sys

# ASCII Art with Pyfiglet
# import sys
from colorama import init
init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected
from termcolor import cprint 
from pyfiglet import figlet_format


class ClickTime(object):
    """
    The ClickTime class is the interface to the ClickTime service.
    
    >>> ct = ClickTime("username", "password")
    >>> ct.CompanyID
    "xxxxxxxx"
    >>> ct.UserID
    "xxxxxxxx"
    """
    
    SERVER = "app.clicktime.com"
    URL_BASE = "/api/1.3"

    def __init__(self, username, password):
        auth = base64.encodestring("%s:%s" % (username, password))[:-1] # remove the extra newline
        self.__headers = {"Authorization" : "Basic %s" % auth}
        self.__session = self.session()
        if self.__session == None:
            raise StandardError("Failure to establish session information")
        if not self.__session.has_key("CompanyID"):
            raise StandardError("Session information lacks CompanyID")
        for k, v in self.__session.items():
            setattr(self, str(k), str(v))


    def _get(self, url, headers=None):
        """
        Internal helper method for GET requests.
        """
        if headers:
            headers.update(self.__headers)
        else:
            headers = copy.copy(self.__headers)
        connection = httplib.HTTPSConnection(ClickTime.SERVER)
        connection.request("GET", "%s/%s" % (ClickTime.URL_BASE, url), headers=headers)
        resp = connection.getresponse()
        data = resp.read()
        connection.close()
        return data, resp.status, resp.reason
    

    def _post(self, url, headers=None, data=None):
        """
        Internal helper method for POST requests.
        """
        if headers:
            headers.update(self.__headers)
        else:
            headers = copy.copy(self.__headers)
        headers["content-type"] = "application/json; charset=utf-8"
        connection = httplib.HTTPSConnection(ClickTime.SERVER)
        connection.request("POST", "%s/%s" % (ClickTime.URL_BASE, url), headers=headers, body=data)
        resp = connection.getresponse()
        data = resp.read()
        connection.close()
        return data, resp.status, resp.reason
        

    def _parse(self, json_str, default=None):
        try:
            return json.loads(json_str)
        except ValueError:
            logging.error("Error parsing JSON '%s'", json_str)
            return default
        

    def session(self):
        """
        http://app.clicktime.com/api/1.3/help#GET_Session
        """
        data, status, reason = self._get("Session")
        data = self._parse(data, None)
        return data
    

    def company(self, company_id=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_Company
        """
        if company_id == None:
            company_id = self.CompanyID
        data, status, reason = self._get("Companies/%s" % (company_id))
        data = self._parse(data, None)
        return data


    def user(self, company_id=None, user_id=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_User
        """
        if company_id == None:
            company_id = self.CompanyID
        if user_id == None:
            user_id = self.UserID
        data, status, reason = self._get("Companies/%s/Users/%s" % (company_id, user_id))
        data = self._parse(data, None)
        return data
        

    def clients(self, client_id=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_ClientsForUser
        
        Per the documentations, only supports listing clients for the requesting user.
        
        If provided with the optional client_id argument the result will either be an empty list
        or a list of length one containing only the requested client.
        """
        data, status, reason = self._get("Companies/%s/Users/%s/Clients" % (self.CompanyID, self.UserID))
        data = self._parse(data, [])
        if client_id != None:
            for client in data:
                if client["ClientID"] == client_id:
                    return [client]
            return []
        return data
    

    def jobs(self, job_number=None, with_child_ids=True):
        """
        http://app.clicktime.com/api/1.3/help#GET_JobsForUser
        
        Per the documentations, only supports listing clients for the requesting user.
        
        If provided with the optional job_number argument the result will either be an empty list
        or a list of length one containing only the requested job.
        """
        url = "Companies/%s/Users/%s/Jobs" % (self.CompanyID, self.UserID)
        if with_child_ids == True:
            url += "?withChildIDs=true"
        data, status, reason = self._get(url)
        data = self._parse(data, [])
        if job_number != None:
            for job in data:
                if job["Number"] == job_number:
                    return [job]
            return []
        return data
    

    def tasks(self, task_number=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_TasksForUser
        
        Per the documentations, only supports listing clients for the requesting user.
        
        If provided with the optional task_number argument the result will either be an empty list
        or a list of length one containing only the requested task.
        """
        data, status, reason = self._get("Companies/%s/Users/%s/Tasks" % (self.CompanyID, self.UserID))
        data = self._parse(data, [])
        if task_number != None:
            for task in data:
                if task["Code"] == task_number:
                    return [task]
            return []
        return data
    

    def timeentires(self, startdate=None, enddate=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_TimeEntries
        """
        url = "Companies/%s/Users/%s/Jobs" % (self.CompanyID, self.UserID)
        if startdate != None:
            if type(startdate) == str:
                startdate = datetime.datetime.strptime(startdate, ("%Y%m%d"))
        if enddate != None:
            if type(enddate) == str:
                enddate = datetime.datetime.strptime(enddate, ("%Y%m%d"))
          
        if startdate != None and enddate == None:
            url += "?date=%s" % startdate.strftime("%Y%m%d")
        elif startdate != None and enddate != None:
            if (enddate - startdate) > datetime.timedelta(days=7):
                raise ValueError("You can only request up to 7 days of timeentires")
            url += "?startdate=%s&enddate=%s" % (startdate.strftime("%Y%m%d"), enddate.strftime("%Y%m%d"))
        elif startdate == None and enddate != None:       
            raise ValueError("If enddate is provided you must provide startdate") 

        data, status, reason = self._get(url)
        data = self._parse(data, None)
        return data
    

    def create_timeentry(self, job_id, task_id, hours, date=None, comment=None, break_time=None):
        """
        http://app.clicktime.com/api/1.3/help#POST_CreateTimeEntry
        """
        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))

        data = {"JobID": job_id,
                "TaskID": task_id,
                "Date": date.strftime("%Y%m%d"),
                "Hours": float(hours),
                "Comment": "" # The comment field is always required, even if blank
                }
        if comment != None:
            data["Comment"] = comment
        if break_time != None:
            data["BreakTime"] = break_time
        # TODO add support for ISOStartTime and ISOEndTime
        
        data = json.dumps(data)
        data, status, reason = self._post("Companies/%s/Users/%s/TimeEntries" % (self.CompanyID, self.UserID), data=data)
        data = self._parse(data, None)
        return data


    def expensesht(self, company_id=None, user_id=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_ExpenseSheets
        """
        if company_id == None:
            company_id = self.CompanyID
        if user_id == None:
            user_id = self.UserID
        data, status, reason = self._get("Companies/%s/Users/%s/ExpenseSheets" % (company_id, user_id))
        data = self._parse(data, None)
        return data


    def expense_item(self, company_id=None, user_id=None, expensesht_id=None):
        """
        http://app.clicktime.com/api/1.3/help#GET_ExpenseItems
        """
        if company_id == None:
            company_id = self.CompanyID
        if user_id == None:
            user_id = self.UserID
        data, status, reason = self._get("Companies/%s/Users/%s/ExpenseSheets/%s/ExpenseItems" % (company_id, user_id, expensesht_id))
        data = self._parse(data, None)
        return data


    def create_expensesht(self, company_id=None, user_id=None, Title=None, Description=None, TrackingID=None, date=None):
        """
        http://app.clicktime.com/API/1.3/help#POST_CreateExpenseSheet
        """
        self.MyExpenseID = []

        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))

        data = {"Title": Title,
                "Description": Description,
                "TrackingID": TrackingID,
                "ExpenseSheetDate": date.strftime("%Y%m%d"),
                "HasForeignCurrency": True
                }
        
        data = json.dumps(data)
        data, status, reason = self._post("Companies/%s/Users/%s/ExpenseSheets" % (self.CompanyID, self.UserID), data=data)
        data = self._parse(data, None)

        self.MyExpenseID.append((Title, data))
        print self.MyExpenseID
        # return data
        
        # Output results to a txt file
        with open('MyExpenseID.txt', 'w') as f:
            f.write(str(self.MyExpenseID))

        
    def create_expenseitem(self, 
                            company_id=None, 
                            user_id=None, 
                            ExpenseSheetID=None,
                            Amount=0,
                            Description=None,
                            ExpenseDate=None,
                            ExpenseItemID=None,
                            ExpenseTypeID=None,
                            JobID=None,
                            PaymentTypeID=None,  
                            Amount_Currency=None,
                            Rate=None, 
                            date=None,
                            ExpenseReceiptURLs=None,
                            ExpenseReceiptID=None,
                            BillToJob=True):
        """
        http://app.clicktime.com/API/1.3/help#POST_CreateExpenseItem
        """
        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))
       
        data = {"Amount": Amount,
                "Amount_Currency":"USD", #Foreign_Currency is not allowed
                "BillToJob":BillToJob, #Not Supported
                "Comment":"",
                "Description": Description,
                "ExpenseDate": ExpenseDate,
                "ExpenseItemID":"", #Shouldn't from my submission
                "ExpenseReceiptID":ExpenseReceiptID,
                "ExpenseReceiptURLs":[],
                "ExpenseSheetID": ExpenseSheetID,
                "ExpenseTypeID": ExpenseTypeID, #taxi="2e0taDJGrNCM",
                #"HasForeignCurrency":True, #Not supported
                "JobID": JobID, #Project_Name
                "PaymentTypeID": PaymentTypeID, #VISA
                #"Quantity":0.00,
                #"Rate":0.0000
                }
        
        data = json.dumps(data)
        data, status, reason = self._post("Companies/%s/Users/%s/ExpenseSheets/%s/ExpenseItems" % (self.CompanyID, self.UserID, ExpenseSheetID), data=data)
        data = self._parse(data, None)
        return data


    def upload_receipt(self, company_id=None, user_id=None, image_path=None):
        """
        http://app.clicktime.com/api/1.3/help#POST_Receipt
        """   
        self.MyInvoice = []

        for f in os.listdir(image_path):
            i = os.path.join(image_path, f)
            with open(i, "rb") as f:
                image = f.read()
                encoded = image.encode("base64")
            
                data = {#"ImageData": "[base64 encoded string]",
                        "ImageData": "{0}".format(encoded),
                        "fileType": "image/png"
                        }   
                        
                data = json.dumps(data)
                data, status, reason = self._post("Companies/%s/Users/%s/Receipts" % (self.CompanyID, self.UserID), data=data)
                data = self._parse(data, None)
                self.MyInvoice.append((i, data))
            
        print self.MyInvoice
        
        # Output results to a txt file
        with open('MyInvoice.txt', 'w') as f:
            for i in self.MyInvoice:
                f.write(str(i)+'\n')


# /* ---------- POSTING ITEMS ----------*/
class MyFunc(object):
    """docstring for MyFunc"""
    def __init__(self):
        super(MyFunc, self).__init__()
        pass


    def MyLogin(self, arg1, arg2):
        ct = ClickTime("{0}".format(arg1), "{0}".format(arg2))


    def MyTFB(self, Amount=None, TWD2USD=None, Description = "N/A", ExpenseDate=None, sheet_name=None, image_name=None, SheetID=None, ReceiptID=None, BillToJob=True):
        ct.create_expenseitem(  company_id=ct.CompanyID, 
                                user_id=ct.UserID, 

                                #ExpenseSheetID=ct.MyExpenseID[sheet_name],
                                #ExpenseReceiptID=ct.MyInvoice['test_pic.jpg']['POST_ReceiptResult'][-14:-2],
                                ExpenseSheetID = SheetID,
                                ExpenseReceiptID = ReceiptID,

                                JobID=ref['job_TFB'],
                                ExpenseTypeID=ref['exp_Taxi'],
                                PaymentTypeID=ref['pym_VISA'], 
                                    
                                # Changes each time                            
                                Amount=Amount*TWD2USD,  # Must have
                                Description=Description, # Must have
                                ExpenseDate=ExpenseDate, # Must have

                                #NT Reimbusement
                                BillToJob=BillToJob
                                )


    def MyNT(self, Amount=None, TWD2USD=None, Description = "N/A", ExpenseDate=None, sheet_name=None, image_name=None, SheetID=None, ReceiptID=None, BillToJob=False):
        ct.create_expenseitem(  company_id=ct.CompanyID, 
                                user_id=ct.UserID, 

                                #ExpenseSheetID=ct.MyExpenseID[sheet_name],
                                #ExpenseReceiptID=ct.MyInvoice['test_pic.jpg']['POST_ReceiptResult'][-14:-2],
                                ExpenseSheetID = SheetID,
                                ExpenseReceiptID = ReceiptID,

                                JobID=ref['job_TBB'],
                                ExpenseTypeID=ref['exp_Taxi'],
                                PaymentTypeID=ref['pym_VISA'], 
                                    
                                # Changes each time                            
                                Amount=Amount*TWD2USD,  # Must have
                                Description=Description, # Must have
                                ExpenseDate=ExpenseDate, # Must have

                                #NT Reimbusement
                                BillToJob=BillToJob
                                )


    def screen1(self):
        self.MyLogin(arg1, arg2)

        arg3 = raw_input('Enter New ExpenseSheet Name: ') # EXPENSESHEET_TITLE
        arg4 = raw_input('Enter Receipt Folder Path: ') # RECEIPT_FOLDER_PATH

        # STEP 1: CREATE EXPENSE SHEET
        ct.create_expensesht(company_id=ct.CompanyID, user_id=ct.UserID, Title="{0}".format(arg3), Description=None, TrackingID=None, date=None)

        # STEP 2: UPLOAD RECEIPT
        folder_path = "{0}".format(arg4)
        ct.upload_receipt(company_id=ct.CompanyID, user_id=ct.UserID, image_path=folder_path)

        # STEP 3: COMPOSE POST ITEMS TEMPLATE
        MyTemplate = []
        with open("MyInvoice.txt","r") as f:
            for i in f:
                with open("MyExpenseID.txt", "r") as d:
                    for j in d:
                        lst = i.split(',')
                        expr = lst[0]
                        sequence = expr.rsplit('_', 3)[0]
                        amount = expr.rsplit('_', 3)[1]
                        descr = expr.rsplit('_', 3)[2]
                        date = expr.rsplit('_', 3)[3].rsplit('.', 1)[0]

                        ItemTemp = """self.MyTFB(Amount={0}, TWD2USD=ThisMonthRate, Description = "{1}", ExpenseDate="{2}", SheetID="{3}", ReceiptID="{4}")""".format(amount, descr, date, j[-15:-3], i[-18:-6])
                        MyTemplate.append(ItemTemp)
                        print ItemTemp

        # Output results to a txt file
        with open('Output.txt', 'w') as f:
            for i in MyTemplate:
                f.write(str(i)+'\n')

        print "\nYour ExpenseSheet and Receipt IDs Are Generated Successfully!\n"

        text = "KAMAKURA"
        cprint(figlet_format(text, font='standard'),
                   'yellow', 'on_red', attrs=['bold'])

        continue_1 = raw_input('Do You Want to Continue?(Y/N)')
        if continue_1 == 'Y' or continue_1 == 'y':
            arg0 = raw_input("For Genrating IDs, Please Enter '1'; For Posting Items, Please Enter '2': ")
            if arg0 == '2':
                self.screen2()


    def screen2(self):
            self.MyLogin(arg1, arg2)

            arg5 = raw_input('Upload Customized Output.txt to Execute: ') # Txt Name, MyTBB.txt or MyTBB_NT
           
            # EXECUTE POST FUNCTIONS
            with open('{0}'.format(arg5)) as data:
                for i in data:
                    eval(i)
                    print "Process Completed!"
                    #print i

            text = "KAMAKURA"
            cprint(figlet_format(text, font='standard'),
                   'yellow', 'on_red', attrs=['bold'])


    def take_off(self):
        arg0 = raw_input("For Genrating IDs, Please Enter '1'; For Posting Items, Please Enter '2': ")
        if arg0 == '1':
            self.screen1()
        elif arg0 =='2':
            self.screen2()



if __name__ == "__main__":
    """
    Example implementation using the ClickTime class
    """
    # General Keys:
    # Users can add frequently used items
    ref = { "job_TFB": "24i7bM8VCT1I",
            "job_TBB": "2dAUSqDElHgM",
            "exp_Taxi" : "2bUBVIgz_DDc",
            "exp_Phone": "2Bl7N9atBKRI",
            "exp_OtherExpense": "20eqwJSfhUNc", #LUNCHES
            "exp_Software": "2fppGGLEr-00",
            "pym_VISA" : "2muJ90RaS5yI"
           }


    """
    Example implementation using the ClickTime class
    """
    arg1 = raw_input('Enter Your Username: ') # USERNAME
    arg2 = raw_input('Enter Your Password: ') # PASSWORD
    
    # ACCESS TO MAIN CLASS OF CLICKTIME 
    ct = ClickTime(arg1, arg2)
    
    # ACCESS TO MyFunc OF AUTOMATION
    mf = MyFunc()

    # ACCESS TO LOGIN CREDENTIAL KEEP LOGIN
    # USING IN SCREEN1, SCREEN2 AND POST EXPENSE ITEMS
    mf.MyLogin(arg1, arg2)

    # EXECUTION
    mf.take_off()