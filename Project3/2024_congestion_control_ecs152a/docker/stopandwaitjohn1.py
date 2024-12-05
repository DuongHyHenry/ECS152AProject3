import socket
import time

# Constants
PACKET_SIZE = 1024  # Total packet size
SEQ_ID_SIZE = 4     # Bytes reserved for sequence ID
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE  # Bytes available for message
WINDOW_SIZE = 1     # Stop-and-Wait uses a single packet window

# Metrics
packet_delays = []  # Per-packet delays
jitters = []        # Packet delay variations

def get_jitter():
    """Calculate jitters based on packet delays."""
    for i in range(len(packet_delays) - 1):
        jitter = abs(packet_delays[i + 1] - packet_delays[i])
        jitters.append(jitter)

def print_metrics(total_data_sent, start_time, end_time):
    """Print throughput, average packet delay, and average jitter metrics."""
    throughput = (total_data_sent) / (end_time - start_time)  # bytes per second
    avg_jitter = sum(jitters) / len(jitters) if jitters else 0
    avg_delay = sum(packet_delays) / len(packet_delays) if packet_delays else 0

    metric = 0.2 * (throughput / 2000) + 0.1 / avg_jitter + 0.8 / avg_delay

    print(f"Throughput (bps): {round(throughput, 7)}")
    print(f"Avg Packet Delay (s): {round(avg_delay, 7)}")
    print(f"Avg Jitter (s): {round(avg_jitter, 7)}")
    print(f"Metric: {round(metric, 7)}")

def main():
    # Read file data
    with open('file.mp3', 'rb') as f:
        data = f.read()

    total_data_sent = 0  # Track total data sent

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind(("localhost", 5000))  # Bind to a local port
        udp_socket.settimeout(1)  # Set timeout for retransmissions

        start_time = time.time()  # Start timing for throughput

        # Initialize sequence ID
        seq_id = 0
        acks = {}  # Dictionary to track acknowledged sequence IDs
        while seq_id < len(data):
            # Prepare the packet
            message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + \
                      data[seq_id: min(seq_id + MESSAGE_SIZE, len(data))]
            udp_socket.sendto(message, ('localhost', 5001))
            total_data_sent += len(message)  # Track bytes sent

            # Measure delay for each packet
            start_send = time.time()
            while True:
                try:
                    # Wait for ACK
                    ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                    end_send = time.time()
                    packet_delays.append(end_send - start_send)

                    # Extract ACK ID
                    ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                    print(f"Received ACK for Sequence ID: {ack_id}")

                    # Mark all sequence IDs up to ack_id as acknowledged
                    for sid in list(acks.keys()):
                        if sid <= ack_id:
                            acks[sid] = True

                    if ack_id == seq_id:  # Valid acknowledgment received
                        break
                except socket.timeout:
                    # Retransmit if ACK not received
                    print(f"Timeout occurred for Sequence ID: {seq_id}")
                    udp_socket.sendto(message, ('localhost', 5001))

            # Move to the next sequence ID
            seq_id += MESSAGE_SIZE

        # Send closing message
        udp_socket.sendto(int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True), ('localhost', 5001))

        end_time = time.time()  # End timing for throughput

    # Calculate and print metrics
    get_jitter()
    print_metrics(total_data_sent, start_time, end_time)

if __name__ == "__main__":
    main()

