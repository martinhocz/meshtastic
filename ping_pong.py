import time
import sys
from datetime import datetime
from pubsub import pub
from meshtastic.serial_interface import SerialInterface
from meshtastic import portnums_pb2

serial_port = '/dev/cu.usbserial-0001'  # Meshtastic serial port

# Define ID Channel, where you want to send asnwers
channel_id = 1  # Replace with number of your channel id

def get_current_time():
    # Get actual time
    now = datetime.now()
    # Format to DD/MM/YYYY HH:MM:SS
    formatted_time = now.strftime('%d/%m/%Y %H:%M:%S')
    return formatted_time


def get_node_info(serial_port):
    print("Initializing SerialInterface to get node info...")
    local = SerialInterface(serial_port)
    node_info = local.nodes
    local.close()
    print("Node info retrieved.")
    return node_info

def parse_node_info(node_info):
    print("Parsing node info...")
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown')
            },
            'rssi': node.get('rssi', 'Unknown'),
            'snr': node.get('snr', 'Unknown')
        })
        for key, value in node.items():
            print(f"  {key}: {value}")
        print("-----------------------------------------------------")
    print("Node info parsed.")
    return nodes

def on_receive(packet, interface, node_list, node_info):
    try:
        if packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            
            print(f"{shortname}: {message}")

            # Check, if message is "ping"
            if message.lower() == 'ping':
                pong_message = f"pong - [{get_current_time()}]"
                print(f"Zasílám 'pong' zpět uživateli {shortname} (ID: {fromnum})")
                #Answer to channel
                interface.sendText(pong_message, channelIndex = channel_id)
                #Answer via DM
                #interface.sendText(pong_message, destinationId=fromnum)

            # Check, if message is "info"
            if message.lower() == 'info':
                print(f"Zpráva od uzlu {shortname} (ID: {fromnum}):")
                node_info = next((node for node in node_list if node['num'] == fromnum), None)
                if node_info:
                    rssi_value = node_info.get('rssi', 'N/A')
                    snr_value = node_info.get('snr', 'N/A')
                    response_message = f"RSSI : {rssi_value} SNR : {snr_value}"
                    interface.sendText(response_message, destinationId=fromnum)


            if message.lower() == 'infotest':
                print(f"Žádost o info od uzlu {shortname} (ID: {fromnum}):")
                # Get actual info about node
                node_list = parse_node_info(node_info)  # Parse info

                # Find node via ID
                node_info = next((node for node in node_list if node['num'] == fromnum), None)
                if node_info:
                    # Answer with info
                    response_message = (f"Informace o uzlu {shortname} (ID: {fromnum}): "
                                        f"RSSI: {node_info.get('rssi', 'N/A')}, "
                                        f"SNR: {node_info.get('snr', 'N/A')}, "
                                        f"Last Heard: {node_info.get('lastHeard', 'N/A')}, "
                                        f"Battery Level: {node_info.get('batteryLevel', 'N/A')}, "
                                        f"Position: {node_info.get('position', 'N/A')}")
                    interface.sendText(response_message, destinationId=fromnum)

    except KeyError:
        pass  # Ignore KeyError silently
    except UnicodeDecodeError:
        pass  # Ignore UnicodeDecodeError silently

def main():
    print(f"Using serial port: {serial_port}")

    # Retrieve and parse node information
    node_info = get_node_info(serial_port)
    node_list = parse_node_info(node_info)

    # Print node list for debugging
    print("Node List:")
    for node in node_list:
        print(node)

    # Subscribe the callback function to message reception
    def on_receive_wrapper(packet, interface):
        on_receive(packet, interface, node_list, node_info)

    pub.subscribe(on_receive_wrapper, "meshtastic.receive")
    print("Subscribed to meshtastic.receive")

    # Set up the SerialInterface for message listening
    local = SerialInterface(serial_port)
    print("SerialInterface setup for listening.")

    # Keep the script running to listen for messages
    try:
        while True:
            sys.stdout.flush()
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("Script terminated by user")
        local.close()

if __name__ == "__main__":
    main()

