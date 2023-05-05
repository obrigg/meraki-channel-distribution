# Meraki Wireless Clients Distribution
[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/obrigg/meraki-channel-distribution)
### The Challenge

The year is 2020. And yet some of our wireless clients are still connected to the wireless network on the 2.4GHz spectrum which cannot provide them the performance they are looking for.
The Meraki dashboard is amazing, but (at the moment) is does not allow us to have a single view of all clients connected via 2.4GHz (vs. 5GHz).

### The Solution

This script will use the Meraki API to query all wireless clients on a given Meraki network, and return the client distribution between 2.4GHz and 5GHz.
In addition, it will mark 5GHz-capable clients that are connected to 2.4GHz for some reason.

### How to run the script:

#### Generate your Meraki API Key

1. Access the [Meraki dashboard](dashboard.meraki.com).
2. For access to the API, first enable the API for your organization under Organization > Settings > Dashboard API access.
<p align="center"><img src="img/org_settings.png"></p>
3. After enabling the API, go to "my profile" on the upper right side of the dashboard to generate an API key. This API key will be associated with the Dashboard Administrator account which generates it, and will inherit the same permissions as that account.  You can generate, revoke, and regenerate your API key on your profile.
<p align="center"><img src="img/my_profile.png"></p>
<p align="center"><img src="img/api_access.png"></p>
**Always keep your API key safe as it provides authentication to all of your organizations with the API enabled. If your API key is shared, you can regenerate your API key at any time. This will revoke the existing API key.**

#### Storing the Meraki API Key as an environment variable
Once the API key is obtained, you'll need to store the Meraki dashboard API key as an environment variable:
`export MERAKI_DASHBOARD_API_KEY = <YOUR MERAKI API KEY>`
and install the Meraki SDK via `pip install -r requirements.txt`

Now you're ready. Good luck!
`python run.py`

### Troubleshooting
The is a `isDebug` variable in the script, changing it to `True` should shed more light on what's happening for troubleshooting purposes.
The script will search for clients that were connected during the last hour (or still are connected). You can change the search span by changing the `timespan` attribute.

The dashboard API does not have a direct query to the channel a client is associated with (at least today). The workaround is to analyze the client events and search for their last association event, where the channel association is mentioned.
The achilles heel of the process is that clients associated for more than the searched time span will not return an associated channel.

You can change the log search span by changing the `starting_after` attribute. Increasing the time span will increase the running time of the code, while decreasing it will increase the number of unknown clients.

----
### Licensing info
Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
