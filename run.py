import time
import os
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from pprint import pprint

def SelectNetwork():
    # Fetch and select the organization
    print('\n\nFetching organizations...\n')
    organizations = meraki.organizations.get_organizations()
    ids = []
    print('{:<30} {:<20}'.format('ID: ', 'Name: '))
    print(50*"-")
    for organization in organizations:
        print('{:<30} {:<20}'.format(organization['id'],organization['name']))
        ids.append(organization['id'])
    selected = input('\nKindly select the organization ID you would like to query: ')
    if selected not in ids:
        raise Exception ('\nInvalid Organization ID')
    # Fetch and select the network within the organization
    print('\n\nFetching networks...\n')
    networks = meraki.networks.get_organization_networks({'organization_id': selected})
    ids = []
    print('{:<30} {:<20}'.format('ID: ', 'Name: '))
    print(50*"-")
    for network in networks:
        print('{:<30} {:<20}'.format(network['id'],network['name']))
        ids.append(network['id'])
    selected = input('\nKindly select the network ID you would like to query: ')
    if selected not in ids:
        raise Exception ('\nInvalid Network ID')
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
            print("\tError: Not sure which channel client %s (ID: %s) is connected to" % (str(client['description']), client['id']))
            clients_error.append(client)
        elif int(channel) < 15:
            client_capabilities = meraki.clients.get_network_client({'network_id': NETWORK_ID, 'client_id': client['id']})['wirelessCapabilities']
            if '5' in client_capabilities:
                print('\tClient {:<40} ( Id: {:<8}) is on channel {:<3} EVENTHOUGH IT IS 5GHz Capable!!!'.format(str(client['description']), client['id'], channel))
                clients_5_on_2.append(client)
            else:
                print('\tClient {:<40} ( Id: {:<8}) is on channel {:<3}, does not support 5GHz'.format(str(client['description']), client['id'], channel))
            clients_2.append(client)
        else:
            print('\tClient {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
            clients_5.append(client)
    elif isDebug:
        print(f'\tClient %s is not a wireless client. Skipping...\n' % str(client['description']))

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
                print(f'\tClient: %s has %s events so far. Fetching more...' % (str(client['description']), len(allEvents)))
            clientEvents_options['starting_after'] = clientEvents[per_page - 1]['occurredAt']
    if isDebug:
        print(f'\tClient: %s has a total of %s events' % (str(client['description']), len(allEvents)))
    return(allEvents)

def GetChannel(client, events):
    # The dashboard API does not have a direct query to the channel a client is
    # associated with. The workaround is to analyze the client events and search
    # for their last association event, where the channel association is mentioned.
    # The achilles heel of the process is that clients associated for more than
    # the searched time span will not return an associated channel.
    # Increasing the time span will increase the running time of the code, while
    # decreasing it will increase the number of unknown clients.
    channel = '666'
    for event in events:
        if 'channel' in event['details'].keys():
            channel = event['details']['channel']
            #if isDebug:
                #print(f'Channel: {channel}')
    return(channel)

if __name__ == '__main__':
    # Debug mode
    isDebug = False
    # Initializing Meraki SDK
    meraki = MerakiSdkClient(os.environ.get('MERAKI_KEY'))
    NETWORK_ID = SelectNetwork()

    clients_2 = []
    clients_5 = []
    clients_5_on_2 = []
    clients_error = []
    allClients = GetAllClients()
    counter = 0
    print('\nReceived a total of %s clients\n' % len(allClients))
    for client in allClients:
        counter += 1
        if isDebug:
            print(f'\tAnalyzing client %s of %s:\n{client}' % (counter, len(allClients)))
            print('Status: 5G - %s, 2.4G - %s, unknown - %s' % (len(clients_5), len(clients_2), len(clients_error)))
        AnalyzeClient(client)

    # Summarize the numbers
    wirelessClientCount = len(clients_5) + len(clients_2) + len(clients_error)
    clients_2_num = len(clients_2)
    clients_5_num = len(clients_5)
    clients_error_num = len(clients_error)
    clients_2_percent = round(len(clients_2)*100/wirelessClientCount)
    clients_5_percent = round(len(clients_5)*100/wirelessClientCount)
    clients_error_percent = round(len(clients_error)*100/wirelessClientCount)

    print(f'''

    Summary:
    Out of a total of {len(allClients)} clients, {wirelessClientCount} are wireless clients:
    There are {clients_2_num} clients in 2.4GHz = {clients_2_percent} %.
    There are {clients_5_num} clients in 5GHz = {clients_5_percent} %.
    There are {clients_error_num} channel unknown = {clients_error_percent} %.

    ''' )

    input('Press any key to get a list of 5GHz capable clients on 2.4GHz... ')
    print("\n5GHz capable clients on 2.4GHz:")
    print('{:<20} {:<18} {:<25}'.format('SSID', 'IP Address', 'Description'))
    for client in clients_5_on_2:
        if client['ip'] is None:
            client['ip'] = 'No IP'
        if client['description'] is None:
            client['description'] = 'No description'
        print('{:<20} {:<18} {:<25}'.format(client['ssid'], client['ip'], client['description']))

    input('Press any key to get a list of the unknown clients... ')
    print("\n\nUnknown clients:")
    print('{:<20} {:<18} {:<25}'.format('SSID', 'IP Address', 'Description'))
    for client in clients_error:
        if client['ip'] is None:
            client['ip'] = 'No IP'
        if client['description'] is None:
            client['description'] = 'No description'
        print('{:<25} {:<18} {:<20}'.format(client['ssid'], client['ip'], client['description']))
