
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 18:57:47 2024

@author: bkeyes
"""

import asyncio
import nest_asyncio
import websockets
import requests
import json
from pylogix import PLC
from collections import deque
import math



#uncomment one of these api tokens below
#bkeyes API token:
#MCI1 Only Token
#api_token = 'jbcgtSDxWR2ND2PnAzwI44TOCvTYSfdn9cR1xCneUX7KP51VsBmzzqihVjeMB23E'
#Universal Token
#api_token = 'EzkvbtH9KpoKxvconU2os59sKnEVZK6zvNYKxknsANTQS1wrbK8iAgmVyR7GfTxF'

#ffernandez API token:
#MCI1 Only Token
#api_token = 'r7WDosW3o5u7JnkgGELFhhk8rqeWnijLrUu9ZoC68SGfymp1WchP2nah0Iq7bnsX'
#Universal Token
api_token = 'N3XnwvIXS8oI3f8WhGXRSN1PZgW7gpdKMlpfX1wmKFSnWNnRgOndDzHpspVTwhwO'

#HMI Server API token
#MCI1 Only Token
#api_token = 'UwYPW3swf3gr8FE47NfeZaLhbtj5fgwVzJkcLLOumyPETsSyvZis3XUeYeixP8xB'
#Universal Token
#api_token = 'u6L0HLpLzRZOI4axAnr2wGlBtLP5xcZaWvJIRrfi6Re0ASivKkpNE6S5FF0Chjnu'

# uncomment for which site is required
#AVP2
#site = 'a031v00000lDpmGAAS'

#MCI1
site = 'a031v000011QpRnAAK'

#RNO1
#site = 'a031v00001D6lYFAAZ'

#BNA1
#site = 'a031v00001Ee9weAAB'

def AS_URL():
    while True:
        keys_value = {'Authorization' : f"Token {api_token}"}
        response = requests.get('https://live.unify.autostoresystem.com/connect?installations='+ site, headers = keys_value)
        websocket_url = response.text
    
        return websocket_url
  
#print(AS_URL())
#uri = f"{AS_URL()}" #Defined above, wss:// only lasts for 10 minutes

rest_url = "https://unify-api.autostoresystem.com/v1/installations/a031v000011QpRnAAK/"
rest_header = {"API-Authorization": f"Token {api_token}"}



nest_asyncio.apply()

#####if not using coroutine, remove it from the connect_to_api(), you can set it as a comment as a reminder to put it back inside.#####
async def connect_to_api(uri,bin_and_task_queue):   #robot_state_queue, system_mode_queue,  robot_error_queue, bin_and_task_queue, port_state_queue, port_error_queue, door_state_queue, incident_queue
        while True:
            try:
                #comm = PLC('192.168.20.5',1)
                uri = AS_URL()
                async with websockets.connect(uri) as websocket:
                    print('Connected')
                    #comm.Write('AS_Grid.Websocket_Connected', True, datatype = 193 )
                    while True:
                        try:
                        
                            as_data = await websocket.recv()
                            json_data = json.loads(as_data)
                            print(json_data)
                            event_type = json_data.get('event_type')
                            #put data into queue depending on event_type.
                            #if not using coroutine, set its if and await statements to comments
                            #if event_type == 'SYSTEM_MODE':
                                #await system_mode_queue.put(as_data)
                            #elif event_type == 'ROBOT_STATE':
                                #await robot_state_queue.put(as_data)
                            #elif event_type == 'ROBOT_ERROR':
                                #await robot_error_queue.put(as_data)             
                            if event_type == 'BIN_AND_TASK':
                                await bin_and_task_queue.put(as_data)
                            #if event_type == 'PORT_STATE':
                                #await port_state_queue.put(as_data)
                            #elif event_type == 'PORT_ERROR':
                                #await port_error_queue.put(as_data)
                            #elif event_type == 'DOOR_STATE':
                                #await door_state_queue.put(as_data)
                            #elif event_type == 'INCIDENT':
                                #await incident_queue.put(as_data)
                        
                        
                            #await queue.put(as_data)  #do not use
                        except websockets.ConnectionClosed:
                            print("Connection Closed")
                            #comm.Write('AS_Grid.Websocket_Connection_Closed', True, datatype = 193)
                            #comm.Close()
                            break
            except Exception as e:
                print(f"Connection error: {e}")
            finally:
                for i in range(5, 0, -1):
                    print(f"Reconnecting in {i} seconds...")
                    await asyncio.sleep(1)

async def system_mode(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received System State")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'SYSTEM_MODE':  #Ensures only relevent event data is called from the right queue
                local_installation_timestamp = json_data.get('local_installation_timestamp', 'N/A')
                system_mode = json_data.get('data', {}).get('system_mode', 'N/A')
                print(f"At: {local_installation_timestamp}, System Mode: {system_mode}")
                comm.Write('Grid.Status[0]', system_mode, datatype=160)
        except json.JSONDecodeError as e:
            print(f"Invalid Data for system_mode: {e}")
        except Exception as e:
            print(f"Error processing system_mode data: {e}")
        finally:
            queue.task_done()
        comm.Close()

async def robot_state(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()    # Get data from the queue
        print("Data Received Robot State")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'ROBOT_STATE':  #Ensures only relevent event data is called from the right queue
                #local_installation_timestamp = json_data.get('local_installation_timestamp', 'N/A')
                #for robot in json_data.get('data', {}).get('robots', []):
                    #if robot.get('robot_id') in range(1, 173): #Set robot range, must be desired robot range +1, 1, 173 is robots 1 - 172
                        #print (f"At: {local_installation_timestamp}, Robot:{robot.get('robot_id')}")
                        #print (f"Robot ID: {robot.get('robot_id')}")
                        #print (f"Battery: {robot.get('battery')}")
                
                
#### Borrows the update push for robot_state to do a .get for the grid state
                status = requests.get(rest_url + 'status', headers=rest_header)
                if status.status_code == 200:
                    print(f"Current Grid Status: {status.json()}")
                else:
                    print(f"Request failed with status code: {status.status_code}")
        except json.JSONDecodeError as e:
            print(f"Invalid Data for robot_state: {e}")
        except Exception as e:
            print(f"Error processing robot_state data: {e}")
        finally:
            queue.task_done()
        comm.Close()            

async def robot_error(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Robot Error")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'ROBOT_ERROR':  #Ensures only relevent event data is called from the right queue
                local_installation_timestamp = json_data.get('local_installation_timestamp', 'N/A')
                robot_id = json_data.get('data', {}).get('robot_id', 'N/A')
                robot_error = json_data.get('data', {}).get('robot_error', 'N/A')
                position_x = json_data.get('data', {}).get('position_x', 'N/A')
                position_y = json_data.get('data', {}).get('position_y', 'N/A')
                has_bin = json_data.get('data', {}).get('robot_has_bin' 'N/A')
                bin_id = json_data.get('data', {}).get('bin_id', 'N/A')
                robot_error_code = json_data.get('data', {}).get('robot_error_code', 'N/A')
                print(f"At: {local_installation_timestamp}, Robot: {robot_id} Faulted with: {robot_error}, error code:{robot_error_code} at: {position_x},{position_y}")
                comm.Write('AS_Grid.X_Coordinate', position_x, datatype=196)
                comm.Write('AS_Grid.Y_Coordinate', position_y, datatype=196)
                if has_bin == 'true':
                    print(f"Robot is holding bin: {bin_id}")
        except json.JSONDecodeError as e:
            print(f"Invalid Data for robot_error: {e}")
        except Exception as e:
            print(f"Error processing robot_error data: {e}")
        finally:
            queue.task_done()
        comm.Close()
async def bin_and_task(queue):
    wait_bin_data1 = {port_id: deque(maxlen=12) for port_id in range (1, 24)} 
    wait_user_data1 = {port_id: deque(maxlen=12) for port_id in range (1, 24)}
    presentation_data1 = {port_id: deque(maxlen=12) for port_id in range (1, 24)}
    wait_bin_data2 = {port_id: deque(maxlen=24) for port_id in range (1, 24)} 
    wait_user_data2 = {port_id: deque(maxlen=24) for port_id in range (1, 24)}
    presentation_data2 = {port_id: deque(maxlen=24) for port_id in range (1, 24)}
    bins_above_data1 = {port_id: deque(maxlen=12) for port_id in range (1, 24)} 
    
    while True:
        #comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Bin and Task")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'BIN_AND_TASK':  #Ensures only relevent event data is called from the right queue
                active = json_data.get('data', {}).get('active', 'N/A')
                prepared = json_data.get('data', {}).get('total_prepared', 'N/A')
                created = json_data.get('data', {}).get('created', 'N/A')
                updated = json_data.get('data', {}).get('updated', 'N/A')
                deleted = json_data.get('data', {}).get('deleted', 'N/A')
                delta = active - prepared
                print(f"Created Jobs: {created}, Prepared Jobs: {prepared}, Active Jobs: {active}, Delta : {delta}, Updated Jobs: {updated}, Deleted Jobs: {deleted}")

                for port in json_data.get('data', {}).get('ports', []):
                    port_id = port.get('port_id')
                    wait_bin = port.get('wait_bin')
                    wait_user = port.get('wait_user')
                    pick = port.get('picks')
                    put = port.get('goods_in')
                    other = port.get('inspection_or_adhoc')
                    bins_above = port.get('bins_above')
                    presentations = pick + put + other
                    if port.get('port_id') in range(1, 24):  #Set port range, must be desired port range +1, 1. 24 is ports 1 - 23
                        #print(f"Port ID: {port.get('port_id')}, Wait Bin: {port.get('wait_bin')}, Wait User: {port.get('wait_user')}, Picks: {port.get('picks')}, Puts: {port.get('goods_in')}, Other: {port.get('inspection_or_adhoc')},Status : {port.get('port_state')}")
                        wait_bin_data2[port_id].append(wait_bin)
                        wait_user_data2[port_id].append(wait_user)
                        presentation_data2[port_id].append(presentations)
                        wait_bin_data1[port_id].append(wait_bin)
                        wait_user_data1[port_id].append(wait_user)
                        presentation_data1[port_id].append(presentations)
                        bins_above_data1[port_id].append(bins_above)

                    
                    if port.get('port_id') in range(1, 17):  #Set port range, must be desired port range +1, 1. 24 is ports 1 - 23
                        print(f"Port ID: {port.get('port_id')}, Wait Bin: {port.get('wait_bin')}, Wait User: {port.get('wait_user')}, Picks: {port.get('picks')}, Bins Above: {port.get('bins_above')}")
                        port_id = port.get('port_id')
                        #comm.Write(f'Port_{port_id}_Test.Bin_Wait', port.get('wait_bin'), datatype = 196)
                        #comm.Write(f'Port_{port_id}_Test.User_Wait', port.get('wait_user'), datatype = 196)
                        #comm.Write(f'Port_{port_id}_Test.Picks', port.get('picks'), datatype = 196)    
                        
                    if port.get('port_id') in range(17, 23):  
                        print(f"Port ID: {port.get('port_id')}, Wait Bin: {port.get('wait_bin')}, Wait User: {port.get('wait_user')}, Goods In: {port.get('goods_in')}, Bins Above:{port.get('bins_above')}") 
                        port_id = port.get('port_id')
                        #comm.Write(f'Port_{port_id}_Test.Bin_Wait', port.get('wait_bin'), datatype = 196)
                        #comm.Write(f'Port_{port_id}_Test.User_Wait', port.get('wait_user'), datatype = 196)
                        #comm.Write(f'Port_{port_id}_Test.Goods_In', port.get('goods_in'), datatype = 196)
                        
                        
                    if port.get('port_id') == 23:
                        print(f"Port ID: {port.get('port_id')}, Wait Bin: {port.get('wait_bin')}, Wait User: {port.get('wait_user')}, Goods In: {port.get('goods_in')}, Picks: {port.get('picks')}, Bins Above:{port.get('bins_above')}")
                        #comm.Write('Port_23_Test.Bin_Wait', port.get('wait_bin'), datatype = 196)
                        #comm.Write('Port_23_Test.User_Wait', port.get('wait_user'), datatype = 196)
                        #comm.Write('Port_23_Test.Goods_In', port.get('goods_in'), datatype = 196)
                        #comm.Write('Port_23_Test.Picks', port.get('picks'), datatype = 196)
                
                #bins_above_1hr
                

                if len(bins_above_data1[16]) == 12 and len(bins_above_data1[23]) == 12:
                    above_bins1 = {port_id: 0 for port_id in range (1, 24)}
                    for port_id in bins_above_data1:
                        total_above_bin = sum(bins_above_data1[port_id])
                        above_bins1[port_id] = math.trunc(total_above_bin/12)
                    for port_id, value in above_bins1.items():
                        print(f"Port {port_id}: Avg Bin Above: {value}")
                        
                #Pick 1 hour
                pick_total_wait_bin1 = sum(sum(wait_bin_data1[port_id]) for port_id in range(1, 17))
                pick_total_wait_user1 = sum(sum(wait_user_data1[port_id]) for port_id in range(1, 17))
                pick_total_presentations1 = sum(sum(presentation_data1[port_id]) for port_id in range (1, 17))
                if pick_total_presentations1 !=0:
                   pick_average_bin_wait1 = pick_total_wait_bin1 / pick_total_presentations1
                   pick_average_user_wait1 = pick_total_wait_user1 / pick_total_presentations1
                elif pick_total_presentations1 == 0:
                   pick_average_bin_wait1 = pick_total_wait_bin1
                   pick_average_user_wait1 = pick_total_wait_user1
                
                
                #Pick 2 hour
                pick_total_wait_bin2 = sum(sum(wait_bin_data2[port_id]) for port_id in range(1, 17))
                pick_total_wait_user2 = sum(sum(wait_user_data2[port_id]) for port_id in range(1, 17))
                pick_total_presentations2 = sum(sum(presentation_data2[port_id]) for port_id in range (1, 17))
                if pick_total_presentations2 !=0:
                   pick_average_bin_wait2 = pick_total_wait_bin2 / pick_total_presentations2
                   pick_average_user_wait2 = pick_total_wait_user2 / pick_total_presentations2
                elif pick_total_presentations2 == 0:
                   pick_average_bin_wait2 = pick_total_wait_bin2
                   pick_average_user_wait2 = pick_total_wait_user2
                   
                #Put 1 hour
                put_total_wait_bin1 = sum(sum(wait_bin_data1[port_id]) for port_id in range(17, 23))
                put_total_wait_user1 = sum(sum(wait_user_data1[port_id]) for port_id in range(17, 23))
                put_total_presentations1 = sum(sum(presentation_data1[port_id]) for port_id in range (17, 23))
                if put_total_presentations1 !=0:
                   put_average_bin_wait1 = put_total_wait_bin1 / put_total_presentations1
                   put_average_user_wait1 = put_total_wait_user1 / put_total_presentations1
                elif put_total_presentations1 == 0:
                   put_average_bin_wait1 = put_total_wait_bin1
                   put_average_user_wait1 = put_total_wait_user1    
                
                   
                #Put 2 hour
                put_total_wait_bin2 = sum(sum(wait_bin_data2[port_id]) for port_id in range(17, 23))
                put_total_wait_user2 = sum(sum(wait_user_data2[port_id]) for port_id in range(17, 23))
                put_total_presentations2 = sum(sum(presentation_data2[port_id]) for port_id in range (17, 23))
                if put_total_presentations2 !=0:
                   put_average_bin_wait2 = put_total_wait_bin2 / put_total_presentations2
                   put_average_user_wait2 = put_total_wait_user2 / put_total_presentations2
                elif put_total_presentations2 == 0:
                   put_average_bin_wait2 = put_total_wait_bin2
                   put_average_user_wait2 = put_total_wait_user2
                   
                #IC 1 hour
                ic_total_wait_bin1 = sum(wait_bin_data1[23])
                ic_total_wait_user1 = sum(wait_user_data1[23])
                ic_total_presentations1 = sum(presentation_data1[23])
                if ic_total_presentations1 != 0:
                    ic_average_bin_wait1 = ic_total_wait_bin1 / ic_total_presentations1
                    ic_average_user_wait1 = ic_total_wait_user1 / ic_total_presentations1
                elif ic_total_presentations1 == 0:
                    ic_average_bin_wait1 = ic_total_wait_bin1
                    ic_average_user_wait1 = ic_total_wait_user1                   
                   
                   
                #IC 2 hour
                ic_total_wait_bin2 = sum(wait_bin_data2[23])
                ic_total_wait_user2 = sum(wait_user_data2[23])
                ic_total_presentations2 = sum(presentation_data2[23])
                if ic_total_presentations2 != 0:
                    ic_average_bin_wait2 = ic_total_wait_bin2 / ic_total_presentations2
                    ic_average_user_wait2 = ic_total_wait_user2 / ic_total_presentations2
                elif ic_total_presentations2 == 0:
                    ic_average_bin_wait2 = ic_total_wait_bin2
                    ic_average_user_wait2 = ic_total_wait_user2
                
                
                ##Bin Times##
                #Individual Ports 1 hour
                wait_bin1 = {port_id: 0 for port_id in range (1, 24)}
                for port_id in wait_bin_data1:
                    total_bin_wait = sum(wait_bin_data1[port_id])
                    total_presentations = sum(presentation_data1[port_id])
                    if total_presentations !=0:
                        wait_bin1[port_id] = total_bin_wait / total_presentations
                    else:
                        wait_bin1[port_id] = total_bin_wait
                for port_id, value in wait_bin1.items():
                    print(f"Port {port_id}: Avg Bin Wait: {value}")
                
                #Individual Ports 2 hour
                wait_bin2 = {port_id: 0 for port_id in range (1, 24)}
                for port_id in wait_bin_data2:
                    total_bin_wait = sum(wait_bin_data2[port_id])
                    total_presentations = sum(presentation_data2[port_id])
                    if total_presentations !=0:
                        wait_bin2[port_id] = total_bin_wait / total_presentations
                    else:
                        wait_bin2[port_id] = total_bin_wait
                 
                
                ##User Times## 
                #Individual Ports 1 hour
                wait_user1 = {port_id: 0 for port_id in range (1, 24)}
                for port_id in wait_user_data1:
                    total_user_wait = sum(wait_user_data1[port_id])
                    total_presentations = sum(presentation_data1[port_id])
                    if total_presentations !=0:
                        wait_user1[port_id] = total_user_wait / total_presentations
                    else:
                        wait_user1[port_id] = total_user_wait
                for port_id, value in wait_bin1.items():
                    print(f"Port {port_id}: Avg User Wait: {value}")
               
                #Individual Ports 2 hour
                wait_user2 = {port_id: 0 for port_id in range (1, 24)}
                for port_id in wait_user_data2:
                    total_user_wait = sum(wait_user_data2[port_id])
                    total_presentations = sum(presentation_data2[port_id])
                    if total_presentations !=0:
                        wait_user2[port_id] = total_user_wait / total_presentations
                    else:
                        wait_user2[port_id] = total_user_wait
                  
                
                
                
            
                if len(wait_bin_data1[16]) == 12 and len(wait_bin_data1[23]) == 12:
                    print(f"Average Pick Wait Time Last Hour Bin: {pick_average_bin_wait1:.2f}, User: {pick_average_user_wait1:.2f}")
                    print(f"Average Put Wait Time Last Hour Bin: {put_average_bin_wait1:.2f}, User: {put_average_user_wait1:.2f}")
                    print(f"Average IC Wait Time Last Hour Bin: {ic_average_bin_wait1:.2f}, User: {ic_average_user_wait1:.2f}")
                    for port_id, value in wait_bin1.items():
                        print(f'Average Port Bin Wait Time Last Hour for port {port_id}: {value}')
                        #comm.Write(f'Port_{port_id}_Test.Average_Bin_Wait_1',value, datatype = 202 )
                    for port_id, value in wait_bin2.items():
                        print(f'Average Port Bin Wait Time Last 2 Hours for port {port_id}: {value}')
                        #comm.Write(f'Port_{port_id}_Test.Average_Bin_Wait_2', value, datatype = 202)
                    #comm.Write('AS_Grid.Pick_Average_Bin_Wait_1',pick_average_bin_wait1, datatype = 202 )
                    #comm.Write('AS_Grid.Pick_Average_User_Wait_1',pick_average_user_wait1, datatype = 202)
                    #comm.Write('AS_Grid.Put_Average_Bin_Wait_1',put_average_bin_wait1, datatype = 202)
                    #comm.Write('AS_Grid.Put_Average_User_Wait_1',put_average_user_wait1, datatype = 202)
                    #comm.Write('Port_23_Test.Average_Bin_Wait_1',ic_avg_bin_wait1, datatype = 202)
                    #comm.Write('Port_23_Test.Average_User_Wait_1',ic_avg_user_wait1, datatype = 202)
                    if len(wait_bin_data2[16]) == 24 and len(wait_bin_data2[23]) == 24:
                        print(f"Average Pick Wait Time Last Two Hours Bin: {pick_average_bin_wait2:.2f}, User: {pick_average_user_wait2:.2f}")
                        print(f"Average Put Wait Time Last Two Hours Bin: {put_average_bin_wait2:.2f}, User: {put_average_user_wait2:.2f}")
                        print(f"Average IC Wait Time Last Two Hours Bin: {ic_average_bin_wait2:.2f}, User: {ic_average_user_wait2:.2f}")
                        for port_id, value in wait_user1.items():
                            print(f'Average Port User Wait Time Last Hour for port {port_id}: {value}')
                            #comm.Write(f'Port_{port_id}_Test.Average_User_Wait_1',value, datatype = 202 )
                        for port_id, value in wait_user2.items():
                            print(f'Average Port user Wait Time Last Hour for port {port_id}: {value}')
                            #comm.Write(f'Port_{port_id}_Test.Average_User_Wait_2',value, datatype = 202 )
                        #comm.Write('AS_Grid.Pick_Average_Bin_Wait_2',pick_average_bin_wait2, datatype = 202)
                        #comm.Write('AS_Grid.Pick_Average_User_Wait_2',pick_average_user_wait2, datatype = 202)
                        #comm.Write('AS_Grid.Put_Average_Bin_Wait_2',put_average_bin_wait2, datatype = 202)
                        #comm.Write('AS_Grid.Put_Average_User_Wait_2',put_average_user_wait2, datatype = 202)
                        #comm.Write('Port_23_Test.Average_Bin_Wait_2',ic_avg_bin_wait2, datatype = 202)
                        #comm.Write('Port_23_Test.Average_Bin_Wait_2',ic_avg_user_wait2, datatype = 202)
                
        except json.JSONDecodeError as e:
            print(f"Invalid data for bin_and_task: {e}")
        except Exception as e:
            print(f"Error processing bin_and_task data: {e}")
        finally:
            queue.task_done()
        #comm.Close()
            
async def port_error(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Port Error")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'PORT_ERROR':  #Ensures only relevent event data is called from the right queue
                local_installation_timestamp = json_data.get('local_installation_timestamp', 'N/A')
                port_id = json_data.get('data', {}).get('port_id', 'N/A')
                port_error = json_data.get('data', {}).get('port_error', 'N/A')
                port_state = json_data.get('data', {}).get('port_state', 'N/A')
                comm.Write(f'Port_{port_id}_Test_Error',port_error, datatype = 160)
            print(f"At:{local_installation_timestamp}, Port ID: {port_id}, Fault: {port_error}, Port State: {port_state}")
        except json.JSONDecodeError as e:
            print(f"Invalid data for port_error: {e}")
        except Exception as e:
            print(f"Error processing port_error data: {e}")
        finally:
            queue.task_done()
        comm.Close()
async def port_state(queue):  #once all tasks are done, this force dumps all data out of the queue so its empty for the next set of data
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Port State")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'PORT_STATE':  #Ensures only relevent event data is called from the right queue
               x = 0
               i = 0
               open_port = json_data.get('data', {}).get('open', {})
               closed_port = json_data.get('data', {}).get('closed', {})
               other = json_data.get('data', {}).get('other', {})
               length_open = len(open_port)
               length_closed = len(closed_port)
               print(f"Open Ports: {open_port}")
               print(f"Closed Ports: {closed_port}")
               print(f"Ports in State other that Open/Closed: {other}")
               for x in range (0,length_open):
                   comm.Write(f'Port_{open_port[x]}_Test.Open', True )
               for i in range (0,length_closed):
                   comm.Write(f'Port_{closed_port[i]}_Test.Closed', False)
                   

               
        except json.JSONDecodeError as e:
           print(f"Invalid data for port_state: {e}")
        except Exception as e:
           print(f"Error processing port_state data: {e}")
        finally:
           
           queue.task_done()
        comm.Close()
            
async def door_state(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Door State")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'DOOR_STATE':  #Ensures only relevent event data is called from the right queue
                local_installation_timestamp = json_data.get('local_installation_timestamp', 'N/A')
                robot_door = json_data['data']['door_states'][0]['state']['robot']
                grid_door = json_data['data']['door_states'][0]['state']['grid']
                comm.Write('Grid.Status[1]', grid_door)
                comm.Write('Grid.Status[2]', robot_door)
            print(f"At:{local_installation_timestamp}, Robot Door:{robot_door}, Grid_Door:{grid_door}")
            
        except json.JSONDecodeError as e:
            print(f"Invalid data for door_state: {e}")
        except Exception as e:
            print(f"Error processing door_state data: {e}")
        finally:
            queue.task_done()
        comm.Close()
            
async def incident(queue):
    while True:
        comm = PLC('192.168.20.5',1)
        data = await queue.get()  # Get data from the queue
        print("Data Received Incident")  #Verifies relevent to event type is loaded in the queue
        try:
            json_data = json.loads(data)  # Parse JSON data
            if json_data.get('event_type') == 'INCIDENT':  #Ensures only relevent event data is called from the right queue
                incident_owner = json_data['data']['owner']
                incident_status = json_data['data']['status']
                if incident_status == 'ACTIVE' and json_data['data']['module'] == 'ASROBOTS' :
                    incident_module = json_data['data']['module']
                    mod_id = json_data['data']['module_id']
                    error_name = json_data['data']['error_name']
                    print(f'Owner : {incident_owner}')
                    print(f'Status : {incident_status}')
                    print(f'Module : {incident_module}')
                    print(f'Module_ID : {mod_id}')
                    print(f'Error_Name : {error_name}')
                    comm.Write('AS_Grid.Robot',mod_id,datatype=196)
                    comm.Write('AS_Grid_Incident',error_name,datatype=160)
                    
                elif incident_status == 'ACTIVE' and json_data['data']['module'] == 'ASCHARGERS' :
                    mod = json_data['data']['module']
                    modid = json_data['data']['module_id']
                    detailsname = json_data['data']['details_name']
                    print(f'Owner : {incident_owner}')
                    print(f'Status : {incident_status}')
                    print(f'Module : {mod}')
                    print(f'Module_ID : {modid}')
                    print(f'Details : {detailsname}')          

                
                elif incident_status == 'RESOLVED':
                    print(f'Owner : {incident_owner}')
                    print(f'Status : {incident_status}')
                    comm.Write('AS_Grid_Incident', incident_status, datatype=160)
                    comm.Write('AS_Grid.Robot', 0, datatype= 196)

        except json.JSONDecodeError as e:
            print(f"Invalid data for incident: {e}")
        except Exception as e:
            print(f"Error processing incident data: {e}")
        finally:
            queue.task_done()
        comm.Close()
            
async def empty_queue(queue):  #once all tasks are done, this force dumps all data out of the queue so its empty for the next set of data
    while not queue.empty():
        data = await queue.get()
        print(f"emptying queue:{data}")
    queue.task_done()
    
    
    

async def main():  #Main coroutine, call all other coroutines to run.
    uri = f"{AS_URL()}"
    #if not using coroutine, set them to comments here and await below.
    #queue = asyncio.Queue() do not use
    #system_mode_queue = asyncio.Queue()
    #robot_state_queue = asyncio.Queue()
    #robot_error_queue = asyncio.Queue()
    bin_and_task_queue = asyncio.Queue()
    #port_state_queue = asyncio.Queue()
    #port_error_queue = asyncio.Queue()
    #door_state_queue = asyncio.Queue()
    #incident_queue = asyncio.Queue()
    
#####if not using coroutine, remove it from inside the asyncio.gather(), you can put it outside as a comment as a reminder to put it back inside.#####
    await asyncio.gather(connect_to_api(uri,bin_and_task_queue),# robot_state_queue,uri,system_mode_queue, robot_error_queue, bin_and_task_queue, port_state_queue, port_error_queue, door_state_queue, incident_queue
                         #system_mode(system_mode_queue),
                         #robot_state(robot_state_queue),
                         #robot_error(robot_error_queue),
                         bin_and_task(bin_and_task_queue),
                         #port_state(port_state_queue),
                         #port_error(port_error_queue),
                         #door_state(door_state_queue),
                         #incident(incident_queue)
                         
                         
                         )



asyncio.run(main())
