import time
from config import *
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from pprint import pprint

def SelectNetwork():
    # Fetch and select the organization
    print('Fetching organizations...')
    organizations = meraki.organizations.get_organizations()
    ids = []
    print('{:<30} {:<20}'.format('ID: ', 'Name: '))
    for organization in organizations:
        print('{:<30} {:<20}'.format(organization['id'],organization['name']))
        ids.append(organization['id'])
    selected = input('Kindly select the organization ID you would like to query: ')
    if selected not in ids:
        raise Exception ('Invalid Organization ID')
    # Fetch and select the network within the organization
    print('Fetching networks...')
    networks = meraki.networks.get_organization_networks({'organization_id': selected})
    ids = []
    print('{:<30} {:<20}'.format('ID: ', 'Name: '))
    for network in networks:
        print('{:<30} {:<20}'.format(network['id'],network['name']))
        ids.append(network['id'])
    selected = input('Kindly select the network ID you would like to query: ')
    if selected not in ids:
        raise Exception ('Invalid Network ID')
    return(selected)

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
                print('Received %s clients so far. Fetching more...' % len(allClients))
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
    elif isDebug:
        print(f'Client %s is not a wireless client. Skipping...\n' % str(client['description']))

def GetClientEvents(client):
    allEvents = []
    per_page = 100
    clientEvents_options = {
        'network_id': NETWORK_ID,
        'client_id': client['id'],
        'per_page': per_page,
        'starting_after': time.time() - 60*60*5 # Fetching logs 5 hours back.
        }
    isLastPage = False
    while isLastPage == False:
        try:
            clientEvents = meraki.clients.get_network_client_events(clientEvents_options)
            allEvents += clientEvents
        except ValueError as e:
            print(f'Error: {e}')
        if len(clientEvents) < per_page:
            isLastPage = True
        else:
            if isDebug:
                print(f'Client: %s has %s events so far. Fetching more...' % (str(client['description']), len(allEvents)))
            clientEvents_options['starting_after'] = clientEvents[per_page - 1]['occurredAt']
    if isDebug:
        print(f'Client: %s has a total of %s events' % (str(client['description']), len(allEvents)))
    return(allEvents)

def GetChannel(client, events):
    channel = '666'
    for event in events:
        if 'channel' in event['details'].keys():
            channel = event['details']['channel']
            #if isDebug:
                #print(f'Channel: {channel}')
    return(channel)

# Debug mode
isDebug = False
# Initializing Meraki SDK
meraki = MerakiSdkClient(MERAKI_KEY)
NETWORK_ID = SelectNetwork()

clients_2 = []
clients_5 = []
clients_error = []
allClients = GetAllClients()
counter = 0
print('\nReceived a total of %s clients\n' % len(allClients))
for client in allClients:
    counter += 1
    if isDebug:
        print(f'Analyzing client %s of %s:\n{client}' % (counter, len(allClients)))
        print('Status: 5G - %s, 2.4G - %s, unknown - %s' % (len(clients_5), len(clients_2), len(clients_error)))
    AnalyzeClient(client)


wirelessClientCount = len(clients_5) + len(clients_2) + len(clients_error)

clients_2_num = len(clients_2)
clients_5_num = len(clients_5)
clients_error_num = len(clients_error)
clients_2_percent = round(len(clients_2)*100/wirelessClientCount)
clients_5_percent = round(len(clients_5)*100/wirelessClientCount)
clients_error_percent = round(len(clients_error)*100/wirelessClientCount)

print("Unknown clients:")
print('{:<20} {:<18} {:<20}'.format('description', 'ip', 'ssid'))
for client_error in clients_error:
    print('{:<20} {:<18} {:<20}'.format(client_error['description'], client_error['ip'], client_error['ssid']))

print(f'''

Summary:
There is a total of {clients_2_num} clients in 2.4GHz = {clients_2_percent} %.
There is a total of {clients_5_num} clients in 5GHz = {clients_5_percent} %.
There is a total of {clients_error_num} channel unknown = {clients_error_percent} %.
''' )
