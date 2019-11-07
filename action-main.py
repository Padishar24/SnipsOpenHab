#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import toml
import KolfsInselAutomation
from CalDavCalendar import Calendar
from Tools import IntentMsg, getTimeRange, isRadioPlaying
import datetime
import subprocess
from MyMightyGrocery import MyMightyGrocery 
import sys, traceback

USERNAME_INTENTS = "burkhardzeiner"
MQTT_BROKER_ADDRESS = "localhost:1883"
MQTT_USERNAME = None
MQTT_PASSWORD = None

gRadioIsPlaying = False
myMightyGrocery = None
gMyCurrentShop = None

def loginToMightyGrocery(user, pw):
    global myMightyGrocery
    if not myMightyGrocery: # lazy creation
        myMightyGrocery = MyMightyGrocery (user, pw)
        if not myMightyGrocery.login():
            myMightyGrocery = None # close session
    return myMightyGrocery is not None

def add_prefix(intent_name):
    return USERNAME_INTENTS + ":" + intent_name

def replaceUnitsWithAlias(unitStr):
    unitStr = unitStr.replace ("kg", '<sub alias="Kilogramm">kg</sub>')        
    unitStr = unitStr.replace ("Kg", '<sub alias="Kilogramm">Kg</sub>')
    unitStr = unitStr.replace ("g", '<sub alias="Gramm">g</sub>')
    unitStr = unitStr.replace ("G", '<sub alias="Gramm">G</sub>')
    unitStr = unitStr.replace ("l", '<sub alias="Liter">l</sub>')
    unitStr = unitStr.replace ("L", '<sub alias="Liter">L</sub>')
    unitStr = unitStr.replace ("Stck", 'Stück')
    return unitStr

def on_message_intent(client, userdata, msg):
    global myMightyGrocery
    global gMyCurrentShop
        
    intentMsg = IntentMsg(msg)

    required_slot_question = {}
    txt = "Ich verstehe dich nicht."
    shortIntent = intentMsg.intent_id.split(":")[1]
    print ("Short Intent: " + shortIntent)
    print ("   Slots: " + json.dumps(intentMsg.slots))
    handledIntent = True
    if shortIntent in ["LampenAnSchalten", "LampenAusSchalten", "LichtDimmen", "lightDimPercentage"]:
        if shortIntent == "lightDimPercentage":
            if intentMsg.custom_data and 'past_intent' in intentMsg.custom_data.keys():
                intentMsg.slots.update (intentMsg.custom_data['slots'])
                (txt, required_slot_question) = kia.SwitchLights(intentMsg.custom_data['past_intent'], intentMsg.site_id, intentMsg.slots)
        else:
            (txt, required_slot_question) = kia.SwitchLights(intentMsg.intent_id, intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "openWindows":
        (txt, required_slot_question) = kia.GetOpenWindows(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "Rollladen":
        (txt, required_slot_question) = kia.MoveCovers(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "RollladenSetPosition":
        (txt, required_slot_question) = kia.SetCoverPosition(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodBye":
        (txt, required_slot_question) = kia.LeaveHouse(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodNight":
        (txt, required_slot_question) = kia.GoodNight(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodMorning":
        (txt, required_slot_question) = kia.GoodMorning(intentMsg.site_id, intentMsg.slots)

        if txt:
            calendar = Calendar(intentMsg.config)
            
            today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            tomorrow = today + datetime.timedelta(days=1)
            (appointmentsInSpeak, errorMsg) = calendar.getAppointments (today, tomorrow)

            if appointmentsInSpeak:
                txt = "<s>" + txt + "</s><p>Folgende Termine stehen heute an:</p>" + appointmentsInSpeak
            elif errorMsg:
                txt = "<s>" + txt + ("</s><p>%s</p>" % errorMsg)

    elif shortIntent == "getAppointments":
        try:
            (when, until) = getTimeRange(intentMsg.slots["date"])
            if when and until:
                print ("Getting appointments...")
                calendar = Calendar(intentMsg.config)
                (appointmentsInSpeak, errorMsg) = calendar.getAppointments (when, until)
                if appointmentsInSpeak:
                    txt = appointmentsInSpeak
                else:
                    txt = errorMsg
            else:
                txt = "Zeitbereich unklar!"
        except:
            print ('-'*60)
            print ("Exception: " + sys.exc_info()[0])
            traceback.print_exc(file=sys.stdout)
            print ('-'*60)
            txt = "Fehler!"
    elif shortIntent == "getShoppingList":                
        if loginToMightyGrocery(intentMsg.config["secret"]["mightygrocery_email"], intentMsg.config["secret"]["mightygrocery_pw"]):
            try:
                groceryList = intentMsg.slots["shop"]
                lists = myMightyGrocery.getShoppingLists ()
                if groceryList not in lists:
                    raise Exception()

                gMyCurrentShop = groceryList

                items = myMightyGrocery.getShoppingList(groceryList)
                if len(items) > 0:
                    txt = ""
                    for item in items:
                        if item["unit"] in ["Stck", "Stück"]:
                            txt = txt + ("<p>%s</p>" % item["name"])
                        else:
                            txt = txt + ("<p>%s %s %s</p>" % (item["quantity"], replaceUnitsWithAlias(item["unit"]), item["name"]))    
                else:
                    txt = '<say-as interpret-as="interjection">huch.</say-as>. Einkaufsliste %s ist leer' % groceryList
            except:
                txt = "Unbekannte Einkaufsliste"
        else:
            txt = "Verbindung zur Einkaufsliste fehlgeschlagen."
    elif shortIntent == "addToShoppingList" or shortIntent == "addMoreToShoppingList":
        if loginToMightyGrocery(intentMsg.config["secret"]["mightygrocery_email"], intentMsg.config["secret"]["mightygrocery_pw"]):
            list = None
            try:
                list = intentMsg.slots["shop"]
            except:
                list = gMyCurrentShop
            if list:
                item = ""
                unit = None
                quantity = None
                try:
                    item = intentMsg.slots["item"].strip().capitalize()
                except:
                    item = None
                try:
                    unit = intentMsg.slots["unit"]
                except:
                    pass
                try:
                    quantity = intentMsg.slots["quantity"]
                except:
                    pass

                question = ""
                if item:
                    if myMightyGrocery.addItemToList(item, list, quantity, unit):
                        question = '<say-as interpret-as="interjection">alles klar.</say-as>. Noch mehr?'
                    else:
                        question = '<say-as interpret-as="interjection">huch.</say-as>. Das hat nicht geklappt. Möchtest Du etwas anderes auf die Liste setzen?'
                else:
                    question = '<say-as interpret-as="interjection">huch.</say-as>. Da ist etwas schiefgegangen. Möchtest Du etwas anderes auf die Liste setzen?'
                    
                # ask for more
                required_slot_question["item"] = { "response": question, "intend": "addMoreToShoppingList"}
                txt = None
            else:
                # ask for list
                required_slot_question["shop"] = { "response": "Welche Liste möchtest Du bearbeiten?", "intend": "askForShoppingList"}
                txt = None
    else:
        handledIntent = False

    if shortIntent == "stop":
        global gRadioIsPlaying
        gRadioIsPlaying = False # update global state so that alarm is not turned on again after handling this intent
        
    if handledIntent:
        print ("Response: " + json.dumps(required_slot_question))
        if txt == None and len(required_slot_question) > 0:
            slot = next(iter(required_slot_question))
            response = required_slot_question[slot]["response"]
            intend = required_slot_question[slot]["intend"]
            custom_data = {'past_intent': intentMsg.intent_id, 'siteId': intentMsg.site_id, 'slots': intentMsg.slots}
            dialogue(intentMsg.session_id, response, [add_prefix(intend)], custom_data=custom_data)
        else:
            say(intentMsg.session_id, txt)   
  
def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'text': text,
                                                                         'sessionId': session_id}))


def end_session(session_id):
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'sessionId': session_id}))


def dialogue(session_id, text, intent_filter, custom_data=None):
    data = {'text': text,
            'sessionId': session_id,
            'intentFilter': intent_filter}
    if custom_data:
        data['customData'] = json.dumps(custom_data)
    mqtt_client.publish('hermes/dialogueManager/continueSession', json.dumps(data))

def onDialogSessionStarted(client, userdata, msg):
    print ("**** SESSION START DETECTED ****")
    global gRadioIsPlaying
    if not gRadioIsPlaying:
        gRadioIsPlaying = isRadioPlaying()
        if gRadioIsPlaying:
            subprocess.call("mpc stop", shell=True)
            subprocess.call("mpc volume 100", shell=True)
        

def onDialogSessionEnded(client, userdata, msg):
    print ("**** SESSION END DETECTED ****")
    global gRadioIsPlaying
    if gRadioIsPlaying:
        gRadioIsPlaying = False
        subprocess.call("mpc play", shell=True)
        subprocess.call("mpc volume 85", shell=True)

    global myMightyGrocery
    myMightyGrocery = None # close web session


if __name__ == "__main__":
    snips_config = toml.load('/etc/snips.toml')
    if 'mqtt' in snips_config['snips-common'].keys():
        MQTT_BROKER_ADDRESS = snips_config['snips-common']['mqtt']
    if 'mqtt_username' in snips_config['snips-common'].keys():
        MQTT_USERNAME = snips_config['snips-common']['mqtt_username']
    if 'mqtt_password' in snips_config['snips-common'].keys():
        MQTT_PASSWORD = snips_config['snips-common']['mqtt_password']

    mqtt_client = mqtt.Client()
    mqtt_client.message_callback_add('hermes/intent/#', on_message_intent)
    mqtt_client.message_callback_add ('hermes/hotword/toggleOff', onDialogSessionStarted)
    mqtt_client.message_callback_add ('hermes/hotword/toggleOn', onDialogSessionEnded)
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_BROKER_ADDRESS.split(":")[0], int(MQTT_BROKER_ADDRESS.split(":")[1]))
    mqtt_client.subscribe('hermes/intent/#')
    mqtt_client.subscribe ('hermes/hotword/toggleOff')
    mqtt_client.subscribe ('hermes/hotword/toggleOn')
    kia = KolfsInselAutomation.KolfsInselAutomation()
    mqtt_client.loop_forever()