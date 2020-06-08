from config import *
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException

def GetClients(options):
    clients = meraki.clients.get_network_clients(clients_options)
    return(clients)

def AnalyzeClients(clients):
    for client in clients:
        if client['status'] and client['ssid'] != None:
            channel = AnalyzeEvents(client)
            if channel == '666':
                print("Error - Not sure which channel client %s (ID: %s) is connected to" % (client['description'], client['id']))
                clients_error.append(client)
            elif int(channel) < 15:
                print('Client {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
                clients_2.append(client)
            else:
                print('Client {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
                clients_5.append(client)

def AnalyzeEvents(client):
    per_page = 100
    clientEvents_options = {
        'network_id': NETWORK_ID, 
        'client_id': client['id'], 
        'per_page': per_page,
        'timespan': 3600
        }
    isLastPage = False
    channel = '666'
    while isLastPage == False:
        clientEvents = meraki.clients.get_network_client_events(clientEvents_options)
        if len(clientEvents) < per_page:
            isLastPage = True
        else:
            clientEvents_options['starting_after'] = clientEvents[per_page - 1]['occurredAt']
        channel = GetChannel(client, clientEvents)
    return(channel)

def GetChannel(client, events):
    for event in events:
        if 'channel' in event['details'].keys():
            return(event['details']['channel'])
    return('666') 

# Initializing Meraki SDK
meraki = MerakiSdkClient(MERAKI_KEY)

# Fetch {per_page} clients in the past 1 hour (3,600 seconds)
per_page = 100
isLastPage = False
clients_2 = []
clients_5 = []
clients_error = []

clients_options = {
    'network_id': NETWORK_ID, 
    'timespan': 3600, 
    'per_page': per_page
    }

while isLastPage == False:
    clients = GetClients(clients_options)
    print('\nReceived %s clients\n' % len(clients))
    if len(clients) < per_page:
        isLastPage = True
    else:
        clients_options['starting_after'] = clients[per_page - 1]['id']
    AnalyzeClients(clients)
    
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