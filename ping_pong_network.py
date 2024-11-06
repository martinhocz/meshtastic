import time
import sys
from datetime import datetime
from pubsub import pub
from meshtastic.tcp_interface import TCPInterface
from meshtastic import portnums_pb2

meshtastic_ip = '192.168.15.10'  # Meshtastic IP address
meshtastic_port = 4403  # Default Meshtastic port for TCP communication

debug = True # Debug info

channel_id = 1  # Replace with your channel ID

def get_current_time():
    """Get the current time formatted as DD/MM/YYYY HH:MM:SS"""
    now = datetime.now()
    return now.strftime('%d/%m/%Y %H:%M:%S')

def get_node_info(interface):
    """Retrieve node information directly from the active interface."""
    print("Getting node info from Meshtastic device...")
    node_info = interface.nodes
    print("Node info retrieved.")
    return node_info

def parse_node_info(node_info):
    """Parse and format the node information for easier handling."""
    print("Parsing node info...")
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown')
            },
            'batteryLevel': node.get('batteryLevel', 'Unknown'),
            'snr': node.get('snr', 'Unknown')
        })
        """Debug info - all info from nodes"""
        if(debug):
            for key, value in node.items():
                print(f"  {key}: {value}")
            print("-----------------------------------------------------")

    print("Node info parsed.")
    return nodes

def on_receive(packet, interface, node_list, node_info):
    """Process received messages and respond based on message content."""
    try:
        if packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            
            print(f"{shortname}: {message}")

            if message.lower() == 'ping':
                pong_message = f"pong - [{get_current_time()}]"
                print(f"Sending 'pong' back to user {shortname} (ID: {fromnum})")
                interface.sendText(pong_message, destinationId=fromnum)

            elif message.lower() == 'info':
                print(f"Info request from node {shortname} (ID: {fromnum})")
                node_info = next((node for node in node_list if node['num'] == fromnum), None)
                if node_info:
                    rssi_value = node_info.get('rssi', 'N/A')
                    snr_value = node_info.get('snr', 'N/A')
                    response_message = f"RSSI : {rssi_value} SNR : {snr_value}"
                    interface.sendText(response_message, destinationId=fromnum)

            elif message.lower() == 'infotest':
                print(f"Info test request from node {shortname} (ID: {fromnum})")
                node_list = parse_node_info(node_info)
                node_info = next((node for node in node_list if node['num'] == fromnum), None)
                if node_info:
                    response_message = (f"Node info for {shortname} (ID: {fromnum}): "
                                        f"RSSI: {node_info.get('rssi', 'N/A')}, "
                                        f"SNR: {node_info.get('snr', 'N/A')}")
                    interface.sendText(response_message, destinationId=fromnum)


    except KeyError:
        pass  # Ignore missing keys
    except UnicodeDecodeError:
        pass  # Ignore decoding errors

def reconnect():
    """Attempt to reconnect to the Meshtastic device."""
    print("Attempting to reconnect...")
    while True:
        try:
            interface = TCPInterface(meshtastic_ip, meshtastic_port)
            print("Reconnected successfully.")
            return interface
        except OSError as e:
            print(f"Reconnect failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def main():
    """Main function to initialize and maintain Meshtastic device connection."""
    print(f"Connecting to Meshtastic device at IP: {meshtastic_ip}, Port: {meshtastic_port}")
    local = reconnect() 
    node_info = get_node_info(local)
    node_list = parse_node_info(node_info)

    def on_receive_wrapper(packet, interface):
        """Wrapper to pass node_list and node_info to the on_receive callback."""
        on_receive(packet, interface, node_list, node_info)

    pub.subscribe(on_receive_wrapper, "meshtastic.receive")
    print("Subscribed to meshtastic.receive")

    try:
        while True:
            try:
                sys.stdout.flush()
                time.sleep(1)
            except (BrokenPipeError, OSError) as e:
                print(f"Connection error occurred: {e}. Attempting to reconnect...")
                pub.unsubscribe(on_receive_wrapper, "meshtastic.receive")
                local.close()

                local = reconnect()
                pub.subscribe(on_receive_wrapper, "meshtastic.receive")
    except KeyboardInterrupt:
        print("Script terminated by user")
        local.close()

if __name__ == "__main__":
    main()
