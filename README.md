# Meraki Wireless Clients Distribution

### The Challenge

The year is 2020. And yet some of our wireless clients are still connected to the wireless network on the 2.4GHz spectrum which cannot provide them the performance they are looking for.
The Meraki dashboard is amazing, but (at the moment) is does not allow us to have a single view of all clients connected via 2.4GHz (vs. 5GHz).

### The Solution

This script will use the Meraki API to query all wireless clients on a given Meraki network, and return the client distribution between 2.4GHz and 5GHz.
In addition, it will mark 5GHz-capable clients that are connected to 2.4GHz for some reason.

### How to run the script

You'll need to store the Meraki dashboard API key as an environment variable:
`export MERAKI_KEY = <YOUR MERAKI API KEY>`
and install the Meraki SDK via `pip install -r requirements.txt`

Now you're ready. Good luck!
`python run.py`

### Troubleshooting
The is a isDebug variable in the script, changing it to `True` should shed more light on what's happening for troubleshooting purposes.
The script will search for clients that were connected during the last hour (or still are connected). You can change the search span by changing the `timespan` attribute.
The way the script is searching for the associated channel is searching through the logs of the past 5 hours for an association message. If the client did not re-associate with an AP during the last 5 hours - it will not find its channel.
You can change the log search span by changing the `starting_after` attribute.

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
