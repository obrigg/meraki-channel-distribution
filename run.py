from config import *
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException

def GetAllClients():
    # Fetch {per_page} clients in the past 1 hour (3,600 seconds)
    allClients = []
    per_page = 100
    isLastPage = False
    clients_options = {
    'network_id': NETWORK_ID, 
    'timespan': 3600, 
    'per_page': per_page
    }
    while isLastPage == False:
        newClients = meraki.clients.get_network_clients(clients_options)
        allClients += newClients
        if len(newClients) < per_page:
            isLastPage = True
        else:
            if isDebug:
                print('\nReceived %s clients so far - going for more\n' % len(allClients))
            clients_options['starting_after'] = newClients[per_page - 1]['id']
    return(allClients)

def AnalyzeClient(client):
    if client['status'] and client['ssid'] != None:
        events = GetClientEvents(client)
        channel = GetChannel(client, events)
        if channel == '666':
            print("Error - Not sure which channel client %s (ID: %s) is connected to" % (str(client['description']), client['id']))
            clients_error.append(client)
        elif int(channel) < 15:
            print('Client {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
            clients_2.append(client)
        else:
            print('Client {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
            clients_5.append(client)

def GetClientEvents(client):
    allEvents = []
    per_page = 100
    clientEvents_options = {
        'network_id': NETWORK_ID, 
        'client_id': client['id'], 
        'per_page': per_page,
        'timespan': 3600
        }
    isLastPage = False
    while isLastPage == False:
        clientEvents = meraki.clients.get_network_client_events(clientEvents_options)
        allEvents += clientEvents
        if len(clientEvents) < per_page:
            isLastPage = True
        else:
            if isDebug:
                print(f'Client: %s has %s events so far - more coming' % (str(client['description']), len(allEvents)))
            clientEvents_options['starting_after'] = clientEvents[per_page - 1]['occurredAt']
    if isDebug:
        print(f'Client: %s has a total of %s events' % (str(client['description']), len(allEvents)))
    return(allEvents)

def GetChannel(client, events):
    channel = '666'
    for event in events:
        if 'channel' in event['details'].keys():
            channel = event['details']['channel']
            if isDebug:
                print(f'Channel: {channel}')
    return(channel) 

# Debug mode
isDebug = True
# Initializing Meraki SDK
meraki = MerakiSdkClient(MERAKI_KEY)

clients_2 = []
clients_5 = []
clients_error = []
allClients = GetAllClients()
print('\nReceived a total of %s clients\n' % len(allClients))
for client in allClients:
    if isDebug:
        print(f'Analyzing client:\n{client}')
    AnalyzeClient(client)
    
wirelessClientCount = len(clients_5) + len(clients_2) + len(clients_error)

clients_2_num = len(clients_2)
clients_5_num = len(clients_5)
clients_error_num = len(clients_error)
clients_2_percent = round(len(clients_2)*100/wirelessClientCount)
clients_5_percent = round(len(clients_5)*100/wirelessClientCount)
clients_error_percent = round(len(clients_error)*100/wirelessClientCount)
print(f'''


Summary:
There is a total of {clients_2_num} clients in 2.4GHz = {clients_2_percent} %.
There is a total of {clients_5_num} clients in 5GHz = {clients_5_percent} %.
There is a total of {clients_error_num} channel unknown = {clients_error_percent} %.
''' )