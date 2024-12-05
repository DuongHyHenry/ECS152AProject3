import socket
import time

# Constants
# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# total packets to send
#WINDOW_SIZE = 1

def main():

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
        udp_socket.bind(("0.0.0.0", 5002))
        udp_socket.settimeout(2)
    
        # Start sending data from the 0th sequence
        seq_id = 0
        start_time = time.time()  # Start throughput timer
    
        while seq_id < len(data):
            # Create messages
            #messages = []
            #acks = {}
            seq_id_tmp = seq_id

            # Construct messages
            message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp: seq_id_tmp + MESSAGE_SIZE]
            #messages.append((seq_id_tmp, message))
            #acks[seq_id_tmp] = False
            acks = False
            seq_id_tmp += MESSAGE_SIZE
    
            # Send messages and track send times
            #send_times = {}  # To track when each message is sent
            udp_socket.sendto(message, ('localhost', 5001))
            send_times = time.time()  # Log send time
    
            # Wait for acknowledgment
            while True:
                try:
                    ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                    ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                    print(ack_id, ack[SEQ_ID_SIZE:])  # Preserve the print statement for each acknowledgment
    
                    # Mark all sequence IDs up to the ack_id as acknowledged
                    #for sid in list(acks.keys()):
                        #if sid <= ack_id:
                            #acks[sid] = True
                    acks = True
    
                    # Measure delay for this packet
                    #if ack_id in send_times:
                    delay = time.time() - send_times
                    packet_delays.append(delay)
    
                        # Calculate jitter (difference from the previous delay)
                        if len(packet_delays) > 1:
                            jitter = abs(packet_delays[-1] - packet_delays[-2])
                            jitter_values.append(jitter)
    
                    # All acks received, move on
                    if acks:
                        break
                except socket.timeout:
                    # Resend unacknowledged messages
                    if not acks:
                        udp_socket.sendto(message, ('localhost', 5001))
                        send_times = time.time()  # Update resend time
    
            # Update the sequence ID and total bytes sent
            seq_id += MESSAGE_SIZE
            total_bytes_sent += MESSAGE_SIZE
    
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

if __name__ == "__main__":
    main()
