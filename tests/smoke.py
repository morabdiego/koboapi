import os
from dotenv import load_dotenv
from koboapi import Kobo
from pprint import pprint

load_dotenv()
API_KEY = os.getenv("KOBO_KEY")

client = Kobo(token=API_KEY)
survey_uid = client.list_uid()['EUT_TEST_1']
asset = client.get_asset(survey_uid)
questions = client.get_questions(asset)
choices = client.get_choices(asset)
data = client.get_data(survey_uid)

pprint(questions)
print("----------------------------------------------------\n")
pprint(choices)
print("----------------------------------------------------\n")
pprint(data)
print("----------------------------------------------------\n")
print("----------------------------------------------------\n")
