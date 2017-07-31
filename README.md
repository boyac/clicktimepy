### Introduction

This library is a Python interface to the clicktime.com REST API.  Currently it
only supports a small number of functions, but more will be added.



### Expense Submission
Author: Boya Chiou
/ Last Modified: 2017-07-31

* Step 1: 
Save receipt images in a form of 'sequence_amount_description_date.jpg', e.g. '01_170_taxi to work_20170701.jpg'
Python rsplit function will slice strings according to delimiters and indexes.

* Step 2: 
Execute script and choose option 1 in command window to create a new sheet and automate images uploading.
This execution will return an Output.txt, prepared for Expense items submission.
You will need to change "ThisMonthRate" for your exchange rate.

* Step 3: 
Execute script and choose option 2 to upload the Output.txt.
Process Completed!

