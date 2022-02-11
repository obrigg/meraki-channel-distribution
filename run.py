import meraki
from datetime import datetime, timedelta
from rich import print as pp
from rich.console import Console
from rich.table import Table
from rich.progress import track

def return_name(dictionary: dict) -> str:
    return dictionary['name']

def SelectNetwork():
    # Fetch and select the organization
    print('\n\nFetching organizations...\n')
    organizations = dashboard.organizations.getOrganizations()
    organizations.sort(key=return_name)
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
    networks.sort(key=return_name)
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


if __name__ == '__main__':
    # Initializing Meraki SDK
    dashboard = meraki.DashboardAPI(output_log=False, suppress_logging=True)
    NETWORK_ID = SelectNetwork()

    print("Fetching association events...")
    start_time = (datetime.now() - timedelta(days=2)).isoformat() # Fetching association events for the last 2 days
    is_done = False
    association_events = []
    while is_done == False:
        events = dashboard.networks.getNetworkEvents(NETWORK_ID, productType="wireless", 
            includedEventTypes=["association"], perPage=1000, startingAfter=start_time)
        association_events += events['events']
        if len(events['events']) < 1000:
            is_done = True
        else:
            start_time = events['pageEndAt']
    results = {}
    """
    results format:
    {client_id1: {'name': 'client1', '2.4GHz': True, '5GHz': True, 'SSID': 'SSID1' ,5GHz_capable: True},
     client_id2: {'name': 'client2', '2.4GHz': False, '5GHz': True, 'SSID': 'SSID1' ,5GHz_capable: True},
        ...}
    """
    # Analyzing the association events, to understand which clients are connected to 2.4GHz channels and which to 5GHz channels.
    for step in track(range(len(association_events)), description='Analyzing association events...'):
        event = association_events[step]
        # Client in 2.4GHz
        if int(event['eventData']['channel']) < 13:
            if event['clientId'] in results.keys():
                results[event['clientId']]['2.4GHz'] = True
            else:
                results[event['clientId']] = {'2.4GHz': True, '5GHz': False, 'SSID': event['ssidName']}
                results[event['clientId']]['name'] = event['clientDescription']
        # Client in 5GHz
        elif int(event['eventData']['channel']) > 13:
            if event['clientId'] in results.keys():
                results[event['clientId']]['5GHz'] = True
            else:
                results[event['clientId']] = {'2.4GHz': False, '5GHz': True, 'SSID': event['ssidName']}
                results[event['clientId']]['name'] = event['clientDescription']
        # Client unknown
        else:
            print(f"Error processing client {event['clientId']}, unknown channel")

    # Adding client capabilities
    client_list = list(results.keys())
    for step in track(range(len(client_list)), description='Adding client capabilities...'):
        client = client_list[step]
        try:
            client_details = dashboard.networks.getNetworkClient(NETWORK_ID, clientId=client)
            client_capabilities = client_details['wirelessCapabilities']
        except:
            client_capabilities = "Unknown"
            results[client]['name'] = "Unknown"
            print(f"Error processing client {client}, client details not found")
        if '5' in client_capabilities:
            results[client]['5GHz_capable'] = True
        else:
            results[client]['5GHz_capable'] = False

    # Summarize the numbers
    wirelessClientCount = len(results)
    clients_2_only = [client for client in results if results[client]['5GHz'] == False and results[client]['2.4GHz'] == True and results[client]['5GHz_capable'] == False]
    clients_5_only = [client for client in results if results[client]['5GHz'] == True and results[client]['2.4GHz'] == False]
    clients_error = [client for client in results if results[client]['5GHz'] == False and results[client]['2.4GHz'] == False]
    clients_5_on_2 = [client for client in results if results[client]['2.4GHz'] == True and (results[client]['5GHz_capable'] == True or results[client]['5GHz'] == True)]
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
            table.add_column("Client ID", justify="left", style="red", no_wrap=True)
            table.add_column("SSID", justify="left", style="red", no_wrap=True)
            table.add_column("Description", justify="left", style="red", no_wrap=True)
            #
            for client in clients_5_on_2:
                table.add_row(client, results[client]['SSID'], results[client].get('name', 'Unknown'))
            #
            console = Console()
            console.print(table)
