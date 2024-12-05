import socket
from datetime import datetime
import time

# Constants
PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 100

# Metrics tracking
packet_delays = []  # List of per-packet delays
jitter_values = []  # List of jitter values (difference between successive delays)
total_bytes_sent = 0  # Total bytes successfully sent and acknowledged
start_time = None  # Start time for throughput calculation

# Read data
with open('file.mp3', 'rb') as f:
    data = f.read()

# Create a UDP socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # Bind the socket to an OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(2)

    # Start sending data from the 0th sequence
    seq_id = 0
    start_time = time.time()  # Start throughput timer

    while seq_id < len(data):
        # Create messages
        messages = []
        acks = {}
        seq_id_tmp = seq_id

        for i in range(WINDOW_SIZE):
            # Construct messages
            message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp: seq_id_tmp + MESSAGE_SIZE]
            messages.append((seq_id_tmp, message))
            acks[seq_id_tmp] = False
            seq_id_tmp += MESSAGE_SIZE

        # Send messages and track send times
        send_times = {}  # To track when each message is sent
        for sid, message in messages:
            udp_socket.sendto(message, ('localhost', 5001))
            send_times[sid] = time.time()  # Log send time

        # Wait for acknowledgment
        while True:
            try:
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                if 0 <= ack_id < total_packets and not acks[ack_id]:
                acks[ack_id] = True
                delay = time.time() - send_times[ack_id]
                packet_delays.append(delay)

                # Calculate jitter
                if len(packet_delays) > 1:
                    jitter = abs(packet_delays[-1] - packet_delays[-2])
                    jitter_values.append(jitter)
        except socket.timeout:
            # Resend unacknowledged packets in the current window
            for sid, message in messages:
                    if not acks[sid]:
                        udp_socket.sendto(message, ('localhost', 5001))
                        send_times[sid] = time.time()  # Update resend time

        # Slide the window forward
        while window_start < total_packets and acks[window_start]:
            window_start += 1

    # Send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))

# Final Metrics Calculation
end_time = time.time()
total_time = end_time - start_time  # Total time taken for transmission
throughput = total_bytes_sent / total_time if total_time > 0 else 0
average_delay = sum(packet_delays) / len(packet_delays) if packet_delays else 0
average_jitter = sum(jitter_values) / len(jitter_values) if jitter_values else 0

# Performance Metric
performance_metric = (
    0.2 * (throughput / 2000) +
    0.1 / (average_jitter if average_jitter > 0 else 1) +
    0.8 / (average_delay if average_delay > 0 else 1)
)

# Print Metrics
print(f"Throughput: {throughput:.7f} bytes/second")
print(f"Average Packet Delay: {average_delay:.7f} seconds")
print(f"Average Jitter: {average_jitter:.7f} seconds")
print(f"Performance Metric: {performance_metric:.7f}")

#Implement your own sender code and bind it to any port other than 5001. Invoke your sender to send packets to localhost, port 5001 to communicate with the receiver.
#Finally, on sending all the data, sender should send an empty message with the correct sequence id.
#Receiver will then send an ack and fin message for the sender to know it's been acknowledged. (Lines 55 to 59 in receiver.py)
#The sender should then send a message with body '==FINACK' to let the receiver know to exit (see line 31 and 32 in receiver.py)
