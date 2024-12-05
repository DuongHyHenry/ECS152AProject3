import socket
import time

#phuong

# total packet size
PACKET_SIZE = 1024  
# bytes reserved for sequence id
SEQ_ID_SIZE = 4     
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE 
# total packets to send
WINDOW_SIZE = 100

# global lists
packet_delays = []  # total per-packet delays
jitters = []
send_times = {}  # Dictionary to store send times for each packet

def get_jitter():
    """calculate jitters based on packet delays."""
    for i in range(len(packet_delays) - 1):
        jitter = abs(packet_delays[i + 1] - packet_delays[i])
        jitters.append(jitter)

def print_metrics(total_bytes, start_time, end_time):
    """print throughput, average packet delay, and average jitter metrics."""
    throughput = (total_bytes) / (end_time - start_time)  # bits per second
    avg_jitter = sum(jitters) / len(jitters) if jitters else 0
    avg_delay = sum(packet_delays) / len(packet_delays) if packet_delays else 0

    metric = 0.2 * (throughput / 2000) + (0.1 / avg_jitter) + (0.8 / avg_delay)

    print(f"Throughput (bps): {round(throughput, 7)}")
    print(f"Avg Packet Delay (s): {round(avg_delay, 7)}")
    print(f"Avg Jitter (s): {round(avg_jitter, 7)}")
    print(f"Metric: {round(metric, 7)}")

def main():
    # Read data
    with open('file.mp3', 'rb') as f:
        data = f.read()

    total_bytes = 0  # Track total data sent

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

        # Bind the socket to a local port
        udp_socket.bind(("localhost", 5002))  
        udp_socket.settimeout(1)  

        # Timing for throughput
        start_time = time.time()  

        # Sliding window variables
        # messages = []
        base_id = 0  # First unacknowledged sequence ID
        seq_id_tmp = 0  # Next sequence ID to send
        acks = {}  # Acknowledgments for each packet
        acked = []

        while base_id < len(data):
            # Fill the window with packets up to the window size
            while seq_id_tmp < base_id + WINDOW_SIZE * MESSAGE_SIZE and seq_id_tmp < len(data):
                # Prepare the packet
                message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp: seq_id_tmp + MESSAGE_SIZE]
                # messages.append((seq_id_tmp, message))                
                udp_socket.sendto(message, ('localhost', 5001))
                print(seq_id_tmp)

                if seq_id_tmp not in send_times: 
                    send_times[seq_id_tmp] = time.time()  # Store the send time for this packet
                total_bytes += len(message)  # Track bytes sent
                acks[seq_id_tmp] = False

                seq_id_tmp += MESSAGE_SIZE

            # Wait for acknowledgment of the packets in the window
            try:
                while True:
                    ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                    ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                    print(ack_id, ack[SEQ_ID_SIZE:], base_id)
                    # Calculate delay for the acknowledged packet
                    if ack_id in send_times:
                        end_send = time.time()  # Timestamp when the acknowledgment is received
                        packet_delay = end_send - send_times[ack_id]
                        packet_delays.append(packet_delay)  # Store the delay

                    if ack_id >= base_id:
                        # print("entered")
                        if ack_id in acks and not acks[ack_id]:
                            acks[ack_id] = True
                            base_id = ack_id + MESSAGE_SIZE

            except socket.timeout:
                #print("timeout")
                print(f"changing seq_id_tmp({seq_id_tmp}) -> base_id ({base_id}) ")
                seq_id_tmp = base_id
                continue

        # Send closing message
        udp_socket.sendto(int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True), ('localhost', 5001))

        end_time = time.time()  # End timing for throughput

    # Calculate and print metrics
    get_jitter()
    print_metrics(total_bytes, start_time, end_time)

if __name__ == "__main__":
    main()
