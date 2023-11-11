from django.test import TestCase
import re

# Create your tests here.

sample = 'hell@.com.emetricshort.hr'

# print(sample.split('.short/w+'))

reg = re.compile('emetricshort.\w+')

real_email = reg.split(sample)[0]
print(real_email)