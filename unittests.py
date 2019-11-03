from Tools import IntentMsg, getTimeRange, read_configuration_file
import json
import sys, traceback
import os
from pytz import timezone

sys.path.append('../')
from KolfsInselOpenHAB.CalDavCalendar import Calendar

from datetime import datetime

def ReadUnitTestData(file):
    with open(os.getcwd() + '\\UnitTestsData\\' + file + '.json') as json_file:
        return IntentMsg (None, False, json.load(json_file))
    return None

def GetTimeRangeUnitTest(intentMsg, f, t):
    (when, until) = getTimeRange (intentMsg.slots["date"])
    if len(f) == 3 and len(t) == 3:
        if when != datetime (year=f[0], month=f[1], day=f[2]).replace(tzinfo=timezone('Europe/Amsterdam')) or \
            until != datetime (year=t[0], month=t[1], day=t[2]).replace(tzinfo=timezone('Europe/Amsterdam')):
                return (False, "DateTime Failure")
    else:
        if when != datetime (year=f[0], month=f[1], day=f[2], hour=f[3], minute=f[4], second=f[5]).replace(tzinfo=timezone('Europe/Amsterdam')) or \
            until != datetime (year=t[0], month=t[1], day=t[2], hour=t[3], minute=t[4], second=t[5]).replace(tzinfo=timezone('Europe/Amsterdam')):
                return (False, "DateTime Failure")
    
    return (True, "")

def WelcheTermineHabeIchMorgenUnitTest():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchMorgen'), (2019, 11, 2), (2019, 11, 3))

def WelcheTermineInDieserWocher():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchInDieserWoche'), (2019, 10, 28), (2019, 11, 4))
     
def WelcheTermineInDiesemMonat():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchDiesenMonat'), (2019, 11, 1), (2019, 12, 1))
    
def WelcheTermineInDiesemViertelJahr():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchInDiesemViertelJahr'), (2019, 11, 30), (2020, 3, 3))

def WelcheTermineHabeIchJetzt():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchJetzt'), (2019, 11, 2, 6, 0, 33), (2019, 11, 2, 6, 0, 34))
    
def WelcheTermineHabeIchInDenNächstenZweiWochen():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTerminHabeIchIndenNaechstenZweiWochen'), (2019, 11, 4), (2019, 11, 18))
    
def WelcheTermineHabeIchÜbermorgen():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchÜbermorgen'), (2019, 11, 4), (2019, 11, 5))
    
def WelcheTermineHabeIchInDerNaechstenStunde():
    return GetTimeRangeUnitTest (ReadUnitTestData('WelcheTermineHabeIchInDerNaechstenStunde'), (2019, 11, 2, 7, 0, 0), (2019, 11, 2, 8, 0, 0))

def UnitTest_Calendar():
    tests = [
        "WelcheTermineHabeIchMorgen", 
        "WelcheTermineHabeIchInDieserWoche",
        "WelcheTermineHabeIchDiesenMonat",
        "WelcheTermineHabeIchInDiesemViertelJahr",
        "WelcheTermineHabeIchJetzt",
        "WelcheTerminHabeIchIndenNaechstenZweiWochen",
        "WelcheTermineHabeIchÜbermorgen",
        "WelcheTermineHabeIchInDerNaechstenStunde"
    ]
    
    config = {}
    config["secret"] = {}
    config['secret']['caldav_url'] = 'https://owncloud.bzeiner.de/remote.php/dav/calendars/bzeiner/'
    config['secret']['caldav_user'] = 'bzeiner'
    config['secret']['caldav_password'] = 'DoeMr7y5'
    config['secret']['caldav_ssl_verify'] = 'True'
    
    calendar = Calendar(config)
            
    errorMsg = ""
    result = True
    for test in tests:
        intentMsg = ReadUnitTestData(test)
        intentMsg.config = config
        (when, until) = getTimeRange(intentMsg.slots["date"])
        
        if when and until:
            txt = calendar.getAppointments (when, until)
            if len(txt) > 100:
                print ("    Calendar Test %s:   %s" % (test, ("Answer with %d characters" % len(txt))))
            else:
                print ("    Calendar Test %s:   %s" % (test, txt))
        else:
            result = False
            errorMsg += "%s: Zeiten unklar!" % test
    return (result, errorMsg)
        

UnitTests = [
            #  ("Welche Termine habe ich morgen?", WelcheTermineHabeIchMorgenUnitTest), 
            #  ("Welche Termine habe ich in dieser Woche?", WelcheTermineInDieserWocher),
            #  ("Welche Termine habe ich in diesem Monat?", WelcheTermineInDiesemMonat),
            #  ("Welche Termine habe ich in diesem viertel Jahr?", WelcheTermineInDiesemViertelJahr),
            #  ("Welche Termine habe ich jetzt?", WelcheTermineHabeIchJetzt),
            #  ("Welche Termine habe ich in den nächsten zwei Wochen?", WelcheTermineHabeIchInDenNächstenZweiWochen),
            #  ("Welche Termine habe ich übermorgen?", WelcheTermineHabeIchÜbermorgen),
            #  ("Welche Termine habe ich in der nächsten Stunde?", WelcheTermineHabeIchInDerNaechstenStunde),
            #  ("CalDavCalendar", UnitTest_Calendar)
             ]


if __name__ == "__main__":
    for (Name, Func) in UnitTests:
        try:
            (passed, reason) = Func()
            if passed:
                print ("Unit Test '%s' passed" % Name)
            else:
                print ("Unit Test '%s' failed: %s" % (Name, reason))
        except:
            e = sys.exc_info()[0]
            print ('-'*60)
            traceback.print_exc(file=sys.stdout)
            print ('-'*60)
            print ("Unit Test '%s' failed with exception: %s" % (Name, e))


