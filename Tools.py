import io
import configparser
import calendar
from datetime import date, datetime, timedelta, timezone
from pytz import timezone
import json

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file = CONFIG_INI):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

def getTimeRange (slotData):
    kind = slotData["kind"]
    when = None
    until = None
    if kind == "TimeInterval":        
        try:
            when = datetime.strptime(slotData["from"][:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
            until = datetime.strptime(slotData["to"][:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
        except ValueError as e:
            raise e
    elif kind == "InstantTime":
        try:
            when = datetime.strptime(slotData["value"][:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
        except ValueError as e:
            raise e
        delta = None
        if slotData["grain"] == "Year":
            delta = timedelta(days=(366 if calendar.isleap(when.year) else 365))
        elif slotData["grain"] == "Quarter":
            end = None
            if (when.month + 3) > 12:
                end = date(year=when.year + 1, month=(when.month + 3) - 12, day=1)
            else:
                end = date(year=when.year, month=when.month + 3, day=1)
            end += timedelta (days = when.day)
            delta = (end - when.date()) + timedelta (days=1)
        elif slotData["grain"] == "Month":
            end = date(year=when.year, month=when.month, day=calendar.monthrange(when.year, when.month)[1])
            delta = (end - when.date()) + timedelta (days=1)
        elif slotData["grain"] == "Week":
            delta = timedelta(days=7)
        elif slotData["grain"] == "Day":
            delta = timedelta(days=1)
        elif slotData["grain"] == "Hour":
            delta = timedelta(hours=1)
        elif slotData["grain"] == "Minute":
            delta = timedelta(minutes=1)
        elif slotData["grain"] == "Second":
            delta = timedelta(seconds=1)
        until = when + delta

    # TODO if slotData["grain"] == "“Approximate":
    return (when, until)

class IntentMsg:
    def __init__(self, msg, debug=False, data=None):
        if not data:
            self._data = json.loads(msg.payload.decode("utf-8"))
        else:
            self._data = data
        self.intent_id = self._data['intent']['intentName']
        
        try:
            self.session_id = self._data['sessionId']
        except:
            self.session_id = 1

        try:
            self.site_id = self._data['siteId']
        except:
            self.site_id = "default"

        try:
            self.custom_data = json.loads(self._data['customData'])
        except:
            self.custom_data = {}

        try:
            self.slots = self.get_slots ()
        except:
            self.slots = {}

        self.config = {"secret": {}, "global": {}}
        config = read_configuration_file()
        try:
            self.config["global"] = config["global"]
        except:
            pass
        try:
            self.config["secret"] = config["secret"]
        except:
            pass    
        
        if debug:
            print (json.dumps(self._data))
            print (json.dumps(slots))

    def get_slots(self):
        data = self._data
        slot_dict = {}
        try:
            for slot in data['slots']:
                if slot['value']['kind'] in ["InstantTime", "TimeInterval", "Duration"]:
                    slot_dict[slot['slotName']] = slot['value']
                else:
                    slot_dict[slot['slotName']] = slot['value']['value']
        except (KeyError, TypeError, ValueError) as e:
            print("Error: ", e)
            slot_dict = {}
        return slot_dict
