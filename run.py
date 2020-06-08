from config import *
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException

def GetClients(options):
    clients = meraki.clients.get_network_clients(clients_options)
    return(clients)

def AnalyzeClients(clients):
    for client in clients:
        if client['status'] and client['ssid'] != None:
            channel = CheckChannel(client)
            if channel == '666':
                print("Error - Not sure which channel client %s (ID: %s) is connected to" % (client['description'], client['id']))
                clients_error.append(client)
            elif int(channel) < 15:
                clients_2.append(client)
            else:
                clients_5.append(client)

def CheckChannel(client):
    clientEvents_options = {
        'network_id': NETWORK_ID, 
        'client_id': client['id'], 
        'per_page': 20
        }
    clientEvents = meraki.clients.get_network_client_events(clientEvents_options)
    
    for event in clientEvents:
        if 'channel' in event['details'].keys():
            #print('Client %s (Id: %s) is on channel %s' % (client['description'], client['id'], event['details']['channel']))
            print('Client {:<40} ( Id: {:<8}) is on channel {:<3}'.format(client['description'], client['id'], event['details']['channel']))
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
    AnalyzeClients(clients)

wirelessClientCount = len(clients_5) + len(clients_2) + len(clients_error)
print('''


Summary:
There is a total of %s clients in 2.4GHz = %s %.
There is a total of %s clients in 5GHz = %s %.
There is a total of %s channel unknown = %s %.
''' % (len(clients_2), round(len(clients_2)*100/wirelessClientCount), len(clients_5), 
    round(len(clients_5)*100/wirelessClientCount), len(clients_error), round(len(clients_error)*100/wirelessClientCount)))