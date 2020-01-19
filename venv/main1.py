from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz


# If modifying these scopes, delete the file token.pickle.

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
          "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENTIONS = ["rd", "th", "st", "nd"]
NO_EVENTS = ["No events fam","You got nothing that day","Negative no events dawwwwwg","Let me look up  oops you have nothing that day"]

# text given to python and we wanna taht it says tro us
######  PYTHON SAYING TEXT TO THE USER FROM SPEAKERS ######

def speak(text):
    engine = pyttsx3.init() # starts it on
    voices = engine.getProperty("voices")
    engine.setProperty('voice',voices[1].id)
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()
#############################################################################
############# USER SAYING TEXT TO THE MACHINE ###############################

# GET THE audio FROM USER CONVERT IT INTO TEXT AND THEN DO SOMETHING WITH THAT TEXT FORM
def get_audio():
    r = sr.Recognizer()# object of class spech recognition class
    with sr.Microphone() as source:# gets input sets microphone as source
        audio = r.listen(source)# we listen what yser says
        said = ""

        try:
            said = r.recognize_google(audio)# this will  convert whatever user says
            print(said)
        except Exception as e:# when we dont understand what user said so to prvent error
            print("Exception: " + str(e))

    return said


def authenticate_google():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service


def get_events(day, service):
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())

    # so the day that user wants us to tell event has entire day so we need
    # to give time to the google api from the start time of that dya to end time to tell
    # the event that we have on that day
    utc = pytz.UTC
    date = date.astimezone(utc)#gives us utc time zone
   # this two lines down here will conver the dates into some utc format
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        s = random.choice(NO_EVENTS)

        speak(s)
    else:
        speak(f"You have {len(events)} events on this day.")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0])# getting start time with string manupulation
            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else:
                # if its more than 12 then we dont wanna say 13 we wanna say 1

                start_time = str(int(start_time.split(":")[0]) - 12)
                start_time = start_time + "pm"

            speak(event["summary"] + " at " + start_time)

# from a string of text we will retrieve the date
#GIVES US THE DATE
def get_date(text):
    text = text.lower()
    # so we need to know the current day in order to find the event day4
    today = datetime.date.today()# thiss will give the today's dtae aight

    #Breaking up the text in order to get the date

    if text.count("today") > 0:# of text contains today just give us today's date
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split(): # splits the words in spaces
        if word in MONTHS:
            # returns the index of a substring inside the string (if found).
            month = MONTHS.index(word) + 1# get the number of month eg febru =2 etc
        elif word in DAYS:
            day_of_week = DAYS.index(word)# similarly we will get the number of the day in week wednesday = 3rd day of the week
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENTIONS:
                # word= "21st"
                # ext = st
                # found = 5 because it will find that substring in that string anf
                # gives its starting position
                found = word.find(ext)
                if found > 0: # that means user said something like 21st 22nd 23rd  etc.
                    try:
                        day = int(word[:found])# give me everything before extension which is certainly a date
                    except:
                        pass

    if month < today.month and month != -1:# this means user is asking for the next year
    # because suppose we are in august and user says  "March 23"
    # we will not say that oh march is past sorry we will say that okay march of 2021 u mean cuz we already in august 2020
        year = year + 1
    # this check is when use says " plans on 17th ??"
    # supposing current , today date is  = 18
    # so that means user is basically asking for the 17th of the next month
    # IMPORTANT: notice that user does'nt say the month with the date##########
    if month == -1 and day != -1:
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    # this check is when use says "What do i  have on Tuesday"
    # we need to figure the current date(day), month , year
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday() # ranges from 0= monday to 6 =sunday
        # day_of_week we found from the word
        dif = day_of_week - current_day_of_week

        # if the difference is less than zero that means we are talking about the
        # day in the next week cuz
        # lets say today is tuesday and user says Monday
        # so that means we will have a difference of negative  monday = 1 and tuesday = 2
        # diff 1 - 2 = -1
        # so thats how we know that wehn we have diff < 0 we are talking about next week

        if dif < 0:
            dif += 7# go to next week
            # lets say im saying in what do i have on next wednesday that doesnt mean in next week menas next to next week
            if text.count("next") >= 1:
                dif += 7# go to next to next week

        return today + datetime.timedelta(dif)# correct day

    if day != -1:# FIXED FROM VIDEO
        return datetime.date(month=month, day=day, year=year)


SERVICE = authenticate_google()
print("Start")
text = get_audio()
DONT = ["What are you saying man I don't get it","Pardon me!!","Say it again!!","What!!!","Nah I did'nt get it ","Oh no What are you even speaking homie","Speak again okay"]

WAAKE = "hello hello hello"
while True:
    print("Listening...")
    text = get_audio() # if we said hello hello
    if text.count(WAAKE) > 0:
        speak("Hello!!!!!! , I am ready to help  you.")
        text = get_audio()
    CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy"]
    for phrase in CALENDAR_STRS:
        if phrase in text.lower():
            date = get_date(text)
            if date:
                get_events(date, SERVICE)
            else:
                say = random.choice(DONT)
                speak(say)