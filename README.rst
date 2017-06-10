============
Introduction
============
This library is a Python interface to the clicktime.com REST API.  Currently it
only supports a small number of functions, but more will be added.


============
Expense Submission
Author: Boya Chiou
============ 

Step 1: 
Save receiptimages in a form of 'amount_description_date.jpg', e.g. '170_taxi to work_20170701.jpg'

Step 2: 
Execute script and choose option 1 to create a new sheet and automate images uploading.
This execution will return an Output.txt, prepared for Expense items submission.
You will need to change "ThisMonthRate" for your exchange rate.

Step 3: 
Execute script and choose option 2 to upload the Output.txt.
Process Completed!

* Note: 
Please be aware, the default setting is for Projct TFB, Transportation, and VISA payment items.
You may be able to customized them in the script or via ClickTime's page.
