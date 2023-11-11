from decimal import Decimal
import re


def get_amount_by_percent(percent,amount): 
  "this function gets the amount of a percent on a money"
  return Decimal(percent/100) *(amount)





def get_adminHr_actuall_email(email):

  reg = re.compile('emetricshort.\w+')

  actuall_email = reg.split(email)[0]
  return actuall_email