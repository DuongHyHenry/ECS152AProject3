import socket
import time

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 100  # Initial window size for slow start

# Congestion control variables

def main():
    with open('file.mp3', 'rb') as f:
        data = f.read()

    ssthresh = 1000  # Slow start threshold
    cwnd = 1         # Congestion window starts at 1 (slow start)
    
    packet_delays = []
    jitters = []
    ack_count = 0     # Counter for duplicate ACKs
    ack_queue = []    # Queue to track received ACKs for duplicate detection
    send_times = {}   # For tracking send times to calculate RTT

    total_bytes = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind(("localhost", 5002))
        udp_socket.settimeout(1)

        start_time = time.time()

        acks = {}  # Acknowledgments for each packet
        base_id = 0      # First unacknowledged sequence ID
        seq_id_tmp = 0    # Next sequence ID to send
        while base_id < len(data):
            print(f"Base ID: {base_id}, Sending packets with seq_id_tmp: {seq_id_tmp}")
            
            # Send packets in the sliding window
            while seq_id_tmp < base_id + cwnd * MESSAGE_SIZE and seq_id_tmp < len(data):
                message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp: seq_id_tmp + MESSAGE_SIZE]
                print(f"Sending packet with seq_id {seq_id_tmp} of size {len(message)}")
                udp_socket.sendto(message, ('localhost', 5001))

                if seq_id_tmp not in send_times:
                    send_times[seq_id_tmp] = time.time()
                    print(f"Recording send time for seq_id {seq_id_tmp}: {send_times[seq_id_tmp]}")

                total_bytes += len(message)
                acks[seq_id_tmp] = False
                print(f"Packet with seq_id {seq_id_tmp} added to send_times")

                seq_id_tmp += MESSAGE_SIZE

            try:
                # Listen for ACKs
                print(f"Waiting for ACKs...")
                while True:
                    ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                    ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                    print(f"Received ACK for seq_id {ack_id}")

                    if ack_id in send_times:
                        end_send = time.time()
                        packet_delay = end_send - send_times[ack_id]
                        packet_delays.append(packet_delay)
                        print(f"Calculated delay for seq_id {ack_id}: {packet_delay} seconds")

                    if ack_id >= base_id:
                        print(f"Acknowledged seq_id {ack_id} is >= base_id {base_id}")
                        if ack_id in acks and not acks[ack_id]:
                            acks[ack_id] = True
                            base_id = ack_id + MESSAGE_SIZE
                            print(f"Updated base_id to {base_id}")

                        # Fast retransmit on receiving 3 duplicate ACKs
                        ack_count = ack_queue.count(ack_id)
                        if ack_count == 3:
                            print(f"Duplicate ACKs for seq_id {ack_id} received. Fast Retransmit!")
                            seq_id_tmp = ack_id

                    # Update sliding window after each ACK
                    ack_queue.append(ack_id)
                    if len(ack_queue) > 3:
                        ack_queue.pop(0)

            except socket.timeout:
                print(f"Timeout occurred. Reducing cwnd and adjusting ssthresh.")
                ssthresh = max(cwnd // 2, 2)
                cwnd = 1
                seq_id_tmp = base_id  # Resend from the base ID
                print(f"cwnd set to {cwnd}, ssthresh set to {ssthresh}")

            # Update congestion window size
            if cwnd < ssthresh:
                cwnd *= 2  # Slow start
                print(f"cwnd in slow start. New cwnd = {cwnd}")
            else:
                cwnd += 1  # Congestion avoidance
                print(f"cwnd in congestion avoidance. New cwnd = {cwnd}")

        # Send closing message
        print(f"Sending FIN message to receiver.")
        udp_socket.sendto(int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True), ('localhost', 5001))

        end_time = time.time()
        print(f"Finished sending all packets. Total time: {end_time - start_time} seconds.")

    for i in range(len(packet_delays) - 1):
        jitter = abs(packet_delays[i + 1] - packet_delays[i])
        jitters.append(jitter)
        
    #calculate metrics
    throughput = (total_bytes) / (end_time - start_time)  # bits per second
    avg_jitter = sum(jitters) / len(jitters) if jitters else 0
    avg_delay = sum(packet_delays) / len(packet_delays) if packet_delays else 0

    metric = 0.2 * (throughput / 2000) + (0.1 / avg_jitter) + (0.8 / avg_delay)

    print(f"Throughput (bps): {round(throughput, 7)}")
    print(f"Avg Packet Delay (s): {round(avg_delay, 7)}")
    print(f"Avg Jitter (s): {round(avg_jitter, 7)}")
    print(f"Metric: {round(metric, 7)}")

if __name__ == "__main__":
    main()
