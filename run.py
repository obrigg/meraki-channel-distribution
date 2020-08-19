import time
import os
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track

def SelectNetwork():
    # Fetch and select the organization
    print('\n\nFetching organizations...\n')
    organizations = meraki.organizations.get_organizations()
    ids = []
    table = Table(title="Meraki Organizations")
    table.add_column("Organization #", justify="left", style="cyan", no_wrap=True)
    table.add_column("Org Name", justify="left", style="cyan", no_wrap=True)
    counter = 0
    for organization in organizations:
        ids.append(organization['id'])
        table.add_row(str(counter), organization['name'])
        counter+=1
    console = Console()
    console.print(table)
    selected = input('\nKindly select the organization ID you would like to query: ')
    if int(selected) not in range(0,counter):
        raise Exception ('\tInvalid Organization Number')
    # Fetch and select the network within the organization
    print('\n\nFetching networks...\n')
    networks = meraki.networks.get_organization_networks({'organization_id': organizations[int(selected)]['id']})
    ids = []
    table = Table(title="Available Networks")
    table.add_column("Network #", justify="left", style="green", no_wrap=True)
    table.add_column("Network Name", justify="left", style="green", no_wrap=True)
    counter = 0
    for network in networks:
        ids.append(network['id'])
        table.add_row(str(counter), network['name'])
        counter += 1
    console = Console()
    console.print(table)
    selected = input('\nKindly select the network # you would like to query: ')
    if int(selected) not in range(0,counter):
        raise Exception ('\nInvalid Network #')
    return(networks[int(selected)]['id'])

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
            clients_error.append(client)
            if isDebug:
                print("\t[yellow]Error: Not sure which channel client %s (ID: %s) is connected to[/yellow]" % (str(client['description']), client['id']))
        elif int(channel) < 15:
            client_capabilities = meraki.clients.get_network_client({'network_id': NETWORK_ID, 'client_id': client['id']})['wirelessCapabilities']
            if '5' in client_capabilities:
                clients_5_on_2.append(client)
                if isDebug:
                    print('\tClient {:<40} ( Id: {:<8}) is on channel {:<3} [red]EVENTHOUGH IT IS 5GHz Capable!!![/red]'.format(str(client['description']), client['id'], channel))
            elif isDebug:
                print('\t[yellow]Client {:<40} ( Id: {:<8}) is on channel {:<3}, does not support 5GHz[/yellow]'.format(str(client['description']), client['id'], channel))
            clients_2.append(client)
        else:
            clients_5.append(client)
            if isDebug:
                print('\tClient {:<40} ( Id: {:<8}) is on channel {:<3}'.format(str(client['description']), client['id'], channel))
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
    print('\nReceived a total of %s clients\n' % len(allClients))
    for step in track(range(len(allClients))):
        AnalyzeClient(allClients[step])

    # Summarize the numbers
    wirelessClientCount = len(clients_5) + len(clients_2) + len(clients_error)
    clients_2_num = len(clients_2)
    clients_5_num = len(clients_5)
    clients_error_num = len(clients_error)
    clients_2_percent = round(len(clients_2)*100/wirelessClientCount)
    clients_5_percent = round(len(clients_5)*100/wirelessClientCount)
    clients_error_percent = round(len(clients_error)*100/wirelessClientCount)

    table = Table(title="Wireless Clients Summary")
    table.add_column("Total Clients", justify="center", style="cyan", no_wrap=True)
    table.add_column("5GHz Clients", justify="center", style="cyan", no_wrap=True)
    table.add_column("2.4GHz Clients", justify="center", style="cyan", no_wrap=True)
    table.add_column("Unknown Channel", justify="center", style="cyan", no_wrap=True)
    #
    table.add_row(str(wirelessClientCount), str(clients_5_num), str(clients_2_num), str(clients_error_num))
    table.add_row("---", "---", "---", "---")
    table.add_row("100 % ", str(clients_5_percent) + " % ", str(clients_2_percent) + " % ", str(clients_error_percent) + " % ")
    #
    console = Console()
    console.print(table)

    if len(clients_5_on_2) > 0:
        input('\n\nPress any key to get a list of 5GHz capable clients on 2.4GHz...\n')
        #
        table = Table(title="5GHz capable clients on 2.4GHz")
        table.add_column("SSID", justify="left", style="red", no_wrap=True)
        table.add_column("IP Address", justify="left", no_wrap=True)
        table.add_column("Description", justify="left", style="red", no_wrap=True)
        #
        for client in clients_5_on_2:
            if client['ip'] is None:
                client['ip'] = 'No IP'
            if client['description'] is None:
                client['description'] = 'No description'
            table.add_row(client['ssid'], client['ip'], client['description'])
        #
        console = Console()
        console.print(table)

if clients_error_num > 0:
    input('\n\nPress any key to get a list of the unknown clients... \n')
    #
    table = Table(title="Unknown clients")
    table.add_column("SSID", justify="left", style="yellow", no_wrap=True)
    table.add_column("IP Address", justify="left", style="yellow", no_wrap=True)
    table.add_column("Description", justify="left", style="yellow", no_wrap=True)
    #
    for client in clients_error:
        if client['ip'] is None:
            client['ip'] = 'No IP'
        if client['description'] is None:
            client['description'] = 'No description'
        table.add_row(client['ssid'], client['ip'], client['description'])
    #
    console = Console()
    console.print(table)