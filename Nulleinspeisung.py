#!/usr/bin/env python3

"""
Nulleinspeisung Control Script for Hoymiles Wechselrichter with OpenDTU and Shelly3EM Pro
Originally forked from: https://github.com/Selbstbau-PV/Selbstbau-PV-Hoymiles-nulleinspeisung-mit-OpenDTU-und-Shelly3EM

This script is a modified version, tailored for specific use-cases and enhancements.
All original work and its credits belong to the authors of the referenced repository.
"""

import requests, time, sys
from requests.auth import HTTPBasicAuth

# User Configuration: Replace with your specific details
serial = "<SERIAL_NUMBER>"  # Serial number of Hoymiles Wechselrichter
maximum_wr = <MAX_OUTPUT>  # Maximum output of the Wechselrichter (Watts)
minimum_wr = <MIN_OUTPUT>  # Minimum output of the Wechselrichter (Watts)

# OpenDTU Configuration: Replace with your OpenDTU details
dtu_ip = '<OPEN_DTU_IP>'
dtu_user = '<OPEN_DTU_USERNAME>'
dtu_password = '<OPEN_DTU_PASSWORD>'

# Shelly Device Configuration: Replace with your Shelly 3EM Pro IP
shelly_ip = '<SHELLY_IP>'

while True:
    time.sleep(1)  # Sleep for 1 second

    try:
        # Retrieve data from OpenDTU REST API and parse it into JSON format
        dtu_response = requests.get(f'http://{dtu_ip}/api/livedata/status/inverters').json()

        # Extract specific data from the JSON response
        reachable = dtu_response['inverters'][0]['reachable']  # Is DTU reachable?
        producing = int(dtu_response['inverters'][0]['producing'])  # Is the Wechselrichter producing?
        old_limit = int(dtu_response['inverters'][0]['limit_absolute'])  # Old limit
        power_dc = dtu_response['inverters'][0]['AC']['0']['Power DC']['v']  # DC power from panels
        power_ac = dtu_response['inverters'][0]['AC']['0']['Power']['v']  # AC power output to grid (Watts)
    except:
        print('Error retrieving data from OpenDTU')

    try:
        # Retrieve data from Shelly 3EM REST API
        shelly_response = requests.get(f'http://{shelly_ip}/rpc/Shelly.GetStatus')

        if shelly_response.status_code == 200:
            shelly_data = shelly_response.json()
            total_act_power = shelly_data['em:0']['total_act_power']  # Total active power
        else:
            print(f"Shelly request failed with status code: {shelly_response.status_code}")

        grid_consumption = total_act_power - 100  # Total grid consumption (all phases)
    except:
        print('Error retrieving data from Shelly Pro3EM')

    # Calculate and display power values
    print(f'\nGrid Consumption: {round(grid_consumption, 1)} W, Production: {round(power_ac, 1)} W, Total Consumption: {round(grid_consumption + power_ac, 1)} W')

    if reachable:
        # Calculate new limit in Watts
        new_limit = grid_consumption + old_limit - 5

        # Check and adjust the new limit against maximum and minimum thresholds
        if new_limit > maximum_wr:
            new_limit = maximum_wr
            print(f'Setpoint to maximum: {maximum_wr} W')
        elif new_limit < minimum_wr:
            new_limit = minimum_wr
            print(f'Setpoint to minimum: {minimum_wr} W')
        else:
            print(f'Calculated Setpoint: {round(grid_consumption, 1)} W + {round(old_limit, 1)} W - 5 W = {round(new_limit, 1)} W')

        # Update the inverter limit if it has changed
        if new_limit != old_limit:
            print(f'Setting inverter limit from {round(old_limit, 1)} W to {round(new_limit, 1)} W... ', end='')
            try:
                # Send the new limit to the inverter
                dtu_limit_response = requests.post(
                    url=f'http://{dtu_ip}/api/limit/config',
                    data=f'data={{"serial":"{serial}", "limit_type":0, "limit_value":{new_limit}}}',
                    auth=HTTPBasicAuth(dtu_user, dtu_password),
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                print(f'Configuration sent ({dtu_limit_response.json()["type"]})')
            except:
                print('Error sending configuration')

    sys.stdout.flush()  # Flush cached messages to stdout
    time.sleep(5)  # Sleep for 5 seconds
