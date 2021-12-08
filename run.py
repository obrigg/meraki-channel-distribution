import time
import os
import meraki
from rich import print as pp
from rich.console import Console
from rich.table import Table
from rich.progress import track

def SelectNetwork():
    # Fetch and select the organization
    print('\n\nFetching organizations...\n')
    organizations = dashboard.organizations.getOrganizations()
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
    isOrgDone = False
    while isOrgDone == False:
        selected = input('\nKindly select the organization ID you would like to query: ')
        try:
            if int(selected) in range(0,counter):
                isOrgDone = True
            else:
                print('\t[bold red]Invalid Organization Number\n')
        except:
            print('\t[bold red]Invalid Organization Number\n')
    # Fetch and select the network within the organization
    print('\n\nFetching networks...\n')
    networks = dashboard.organizations.getOrganizationNetworks(organizations[int(selected)]['id'])
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
    isNetDone = False
    while isNetDone == False:
        selected = input('\nKindly select the Network you would like to query: ')
        try:
            if int(selected) in range(0,counter):
                isNetDone = True
            else:
                print('\t[bold red]Invalid Organization Number\n')
        except:
            print('\t[bold red]Invalid Organization Number\n')
    return(networks[int(selected)]['id'])


    if client['status'] and client['ssid'] != None:
        events = GetClientEvents(client)
        channel = GetChannel(client, events)
        if channel == '666':
            clients_error.append(client)
            if isDebug:
                print("\t[yellow]Error: Not sure which channel client %s (ID: %s) is connected to[/yellow]" % (str(client['description']), client['id']))
        elif int(channel) < 15:
            client_capabilities = dashboard.client.getNetworkClient(NETWORK_ID, client['id'])
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
    # Initializing Meraki SDK
    dashboard = meraki.DashboardAPI(output_log=False, suppress_logging=True)
    NETWORK_ID = SelectNetwork()

    print("Fetching association events...")
    association_events = dashboard.networks.getNetworkEvents(NETWORK_ID, includedEventTypes=["association"], perPage=1000, total_pages=50)
    results = {}
    """
    results format:
    {client_id1: {'name': 'client1', '2.4GHz': True, '5GHz': True, 'SSID': 'SSID1' ,5GHz_capable: True},
     client_id2: {'name': 'client2', '2.4GHz': False, '5GHz': True, 'SSID': 'SSID1' ,5GHz_capable: True},
        ...}
    """
    # Analyzing the association events, to understand which clients are connected to 2.4GHz channels and which to 5GHz channels.
    for step in track(range(len(association_events['events'])), description='Analyzing association events...'):
        event = association_events['events'][step]
        # Client in 2.4GHz
        if int(event['eventData']['channel']) < 13:
            if event['clientId'] in results.keys():
                results[event['clientId']]['2.4GHz'] = True
            else:
                results[event['clientId']] = {'2.4GHz': True, '5GHz': False, 'SSID': event['ssidName']}
        # Client in 5GHz
        elif int(event['eventData']['channel']) > 13:
            if event['clientId'] in results.keys():
                results[event['clientId']]['5GHz'] = True
            else:
                results[event['clientId']] = {'2.4GHz': False, '5GHz': True, 'SSID': event['ssidName']}
        # Client unknown
        else:
            print(f"Error processing client {event['clientId']}")

    # Adding client capabilities
    client_list = list(results.keys())
    for step in track(range(len(client_list)), description='Adding client capabilities...'):
        client = client_list[step]
        try:
            client_details = dashboard.networks.getNetworkClient(NETWORK_ID, clientId=client)
            client_capabilities = client_details['wirelessCapabilities']
            results[client]['name'] = client_details['description']
        except:
            client_capabilities = "Unknown"
            results[client]['name'] = "Unknown"
            print(f"Error processing client {client}")
        if '5' in client_capabilities:
            results[client]['5GHz_capable'] = True
        elif '2.4' in client_capabilities:
            results[client]['2.4GHz_capable'] = True
            results[client]['5GHz_capable'] = False
        else:
            results[client]['5GHz_capable'] = False
            results[client]['2.4GHz_capable'] = False

    # Summarize the numbers
    wirelessClientCount = len(results)
    clients_2_only = [client for client in results if results[client]['2.4GHz'] == True and results[client]['5GHz'] == False]
    clients_5_only = [client for client in results if results[client]['5GHz'] == True and results[client]['2.4GHz'] == False]
    clients_error = [client for client in results if results[client]['5GHz'] == False and results[client]['2.4GHz'] == False]
    clients_5_on_2 = [client for client in results if results[client]['2.4GHz'] == True and results[client]['5GHz_capable'] == True]
    #
    if wirelessClientCount > 0:
        clients_2_percent = round(len(clients_2_only)*100/wirelessClientCount)
        clients_5_percent = round(len(clients_5_only)*100/wirelessClientCount)
        clients_5_on_2_percent = round(len(clients_5_on_2)*100/wirelessClientCount)
        clients_error_percent = round(len(clients_error)*100/wirelessClientCount)
        #
        table = Table(title="Wireless Clients Summary")
        table.add_column("Total Clients", justify="center", style="cyan", no_wrap=True)
        table.add_column("5GHz Only Clients", justify="center", style="cyan", no_wrap=True)
        table.add_column("2.4GHz Only Clients", justify="center", style="cyan", no_wrap=True)
        table.add_column("2.4GHz + 5GHz Clients", justify="center", style="cyan", no_wrap=True)
        table.add_column("Unknown", justify="center", style="cyan", no_wrap=True)
        #
        table.add_row(str(wirelessClientCount), str(len(clients_5_only)), str(len(clients_2_only)), str(len(clients_5_on_2)), str(len(clients_error)))
        table.add_row("---", "---", "---", "---")
        table.add_row("100 % ", str(clients_5_percent) + " % ", str(clients_2_percent) + " % ", str(clients_5_on_2_percent) + " % ", str(clients_error_percent) + " % ")
        #
        console = Console()
        console.print(table)

        if len(clients_5_on_2) > 0:
            input('\n\nPress any key to get a list of 5GHz capable clients on 2.4GHz...\n')
            #
            table = Table(title="5GHz capable clients on 2.4GHz")
            table.add_column("SSID", justify="left", style="red", no_wrap=True)
            table.add_column("Description", justify="left", style="red", no_wrap=True)
            #
            for client in clients_5_on_2:
                if results[client]['name'] is None:
                    results[client]['name'] = 'No name'
                table.add_row(results[client]['SSID'], results[client]['name'])
            #
            console = Console()
            console.print(table)
