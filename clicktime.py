# -*- coding: utf-8 -*-
# @Author: boyac
# @Date:   2017-04-18 21:41:10
# @Last Modified by:   Boya Chiou
# @Last Modified time: 2017-04-20 10:11:26

import httplib
import base64
import copy
import json
import datetime
import requests

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


    def create_expensesht(self, company_id=None, user_id=None, title=None, description=None, tracking_id=None, date=None):
        """
        http://app.clicktime.com/API/1.3/help#POST_CreateExpenseSheet
        """
        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))

        data = {"Title": title,
                "Description": description,
                "TrackingID": tracking_id,
                "ExpenseSheetDate": date.strftime("%Y%m%d"),
                "HasForeignCurrency": True
                }
        
        data = json.dumps(data)
        data, status, reason = self._post("Companies/%s/Users/%s/ExpenseSheets" % (self.CompanyID, self.UserID), data=data)
        data = self._parse(data, None)
        return data


    def create_expenseitem(self, company_id=None, user_id=None, ExpenseSheetID=None, amount=0, date=None):
        """
        http://app.clicktime.com/API/1.3/help#POST_CreateExpenseItem
        """
        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))
       
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
                            date=None):
        """
        http://app.clicktime.com/API/1.3/help#POST_CreateExpenseItem
        """
        if date == None:
            date = datetime.datetime.today()
        elif type(date) == str:
            date = datetime.datetime.strptime(date, ("%Y%m%d"))
       
        data = {"Amount": Amount,
                "Amount_Currency":"USD", #Foreign_Currency is not allowed
                "BillToJob":True, #Not Supported
                "Comment":"",
                "Description": Description,
                "ExpenseDate": ExpenseDate,
                "ExpenseItemID":"", #Shouldn't from my submission
                #"ExpenseReceiptID":null,
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



if __name__ == "__main__":
    """
    Example implementation using the ClickTime class
    """
    ct = ClickTime(login_id, login_pw)
    ct.CompanyID
    ct.UserID
    
    TFB_201704 = "<ExpenseSheetID>" 
    ExpenseTypeID = "<ExpenseTypeID>"
    PaymentTypeID = "<PaymentTypeID>"
    
    # BC_201704_TFB   
    ct.create_expenseitem( company_id=ct.CompanyID, 
                            user_id=ct.UserID, 
                            ExpenseSheetID=TFB_201704,
                            Amount=170,
                            Description="Taxi to work",
                            ExpenseDate="20170418",
                            ExpenseTypeID=Taxi_kc,
                            JobID=TFB,
                            PaymentTypeID=VISA_kc,  
                            )
