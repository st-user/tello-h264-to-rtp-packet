import asyncio
import random
import datetime
import logging


logging.basicConfig(level=logging.INFO)



#
# copy from https://github.com/aiortc/aiortc/blob/main/src/aiortc/codecs/h264.py and omit type hints.
#
def _split_bitstream(buf):
    # TODO: write in a more pytonic way,
    # translate from: https://github.com/aizvorski/h264bitstream/blob/master/h264_nal.c#L134
    i = 0
    while True:
        while (buf[i] != 0 or buf[i + 1] != 0 or buf[i + 2] != 0x01) and (
            buf[i] != 0 or buf[i + 1] != 0 or buf[i + 2] != 0 or buf[i + 3] != 0x01
        ):
            i += 1  # skip leading zero
            if i + 4 >= len(buf):
                return
        if buf[i] != 0 or buf[i + 1] != 0 or buf[i + 2] != 0x01:
            i += 1
        i += 3
        nal_start = i
        while (buf[i] != 0 or buf[i + 1] != 0 or buf[i + 2] != 0) and (
            buf[i] != 0 or buf[i + 1] != 0 or buf[i + 2] != 0x01
        ):
            i += 1
            # FIXME: the next line fails when reading a nal that ends
            # exactly at the end of the data
            if i + 3 >= len(buf):
                nal_end = len(buf)
                yield buf[nal_start:nal_end]
                return  # did not find nal end, stream ended first
        nal_end = i
        yield buf[nal_start:nal_end]



# S | E | R | TYPE = 1 | 0 | 0 | 0 0001
# S | E | R | TYPE = 1 | 0 | 0 | 0 0101
OUT_FU_HEADER_START = bytes([ 0x81 ])
OUT_FU_HEADER_START_IDR = bytes([ 0x85 ])

# S | E | R | TYPE = 0 | 0 | 0 | 0 0001
# S | E | R | TYPE = 0 | 0 | 0 | 0 0101
OUT_FU_HEADER_MIDDLE = bytes([ 0x1 ])
OUT_FU_HEADER_MIDDLE_IDR = bytes([ 0x5 ])

# S | E | R | TYPE = 0 | 1 | 0 | 0 0001
# S | E | R | TYPE = 0 | 1 | 0 | 0 0101
OUT_FU_HEADER_END = bytes([ 0x41 ])
OUT_FU_HEADER_END_IDR = bytes([ 0x45 ])


## Tello EDU
IN_PACKET_SIZE = 1460

## 
#
# In order to test the app by using another tool such as ffmpeg instead of using Tello,
# we need to set the size of an udp packet from it properly.
#
# EXAMPLE:
#
# - list available devices for '-i' option
# ============================================
# ffmpeg -f avfoundation -list_devices true -i ""
# ============================================
#
# - Generate video streaming.
# ============================================
# ffmpeg -f avfoundation -framerate 30 -video_size 640x480 -i "0:none" -c:v libx264 -tune zerolatency -f rawvideo udp://127.0.0.1:11111
# ============================================
# 
##
#IN_PACKET_SIZE = 1472


RAW_PAYLOAD_SIZE = 1440


def splite_bytes(_data, size):
    for i in range(0, len(_data), size):
        yield _data[i:i + size]


def timestamp():
    return int(datetime.datetime.now().timestamp() * 1000)


def create_rtp_packet_header(
    sequence_number, timestamp, ssrc,
    version = 2, padding = 0, extension = 0, csrc_count = 0, marker = 1,
    payload_type = 96
):
    v_p_x_cc = 0
    v_p_x_cc += (version << 6)
    v_p_x_cc += (padding << 5)
    v_p_x_cc += (extension << 4)
    v_p_x_cc += csrc_count
 
    logging.debug(f'V|P|X|CC : {v_p_x_cc}')

    m_pt = 0
    m_pt += (marker << 7)
    m_pt += payload_type

    logging.debug(f'M|PT : {m_pt}')

    sn_1 = sequence_number >> 8
    sn_2 = sequence_number & 0xFF

    logging.debug(f'Sequence Number : {sn_1}-{sn_2}')

    t_1 = timestamp >> 24
    t_2 = (timestamp >> 16) & 0xFF
    t_3 = (timestamp >> 8) & 0xFF
    t_4 = timestamp & 0xFF

    logging.debug(f'Timestamp : {t_1}-{t_2}-{t_3}-{t_4}')

    ssrc_1 = ssrc >> 24
    ssrc_2 = (ssrc >> 16) & 0xFF
    ssrc_3 = (ssrc >> 8) & 0xFF
    ssrc_4 = ssrc & 0xFF

    logging.debug(f'SSRC : {ssrc_1}-{ssrc_2}-{ssrc_3}-{ssrc_4}')

    data = bytes([
        v_p_x_cc, m_pt, sn_1, sn_2,
        t_1, t_2, t_3, t_4,
        ssrc_1, ssrc_2, ssrc_3, ssrc_4
    ])

    return data


class ReceiveTelloWebcamDataProtocol:

    """
        An UDP server protocol receiving h264 packets from Tello
        and converting them to rtp packets.
    """

    def __init__(self, packet_queue):
        self.packet_queue = packet_queue
        self.data_holder = bytes(0)
        self.ssrc = random.randint(0, 0xFFFFFF)
        self.sequence_number = 0
        self.timestamp = 0
        self.timestamp_start_clock = timestamp()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):

        if len(data) != IN_PACKET_SIZE:
            
            _data = self.data_holder + data
            self.data_holder = bytes(0)

            nal_units = list(_split_bitstream(_data))
            logging.debug(f'NALU count {len(nal_units)}')
           
            for nal_unit in nal_units:
             
                """

                F | NRI | TYPE

                e.g.

                0 | 11 | 0 0101  =  0x65 (IDR)
                0 | 11 | 0 0111  =  0x67 (SPS)
                0 | 11 | 0 1000  =  0x68 (PPS)

                """
                orig_f = nal_unit[0] >> 7
                orig_nri = nal_unit[0] >> 5 & 0x3
                orig_nalu_type = nal_unit[0] & 0x1f

                if orig_nalu_type != 1 and orig_nalu_type != 5:
                    logging.debug(f'Maybe SPS or PPS NALU type {orig_nalu_type}, {len(nal_unit)}')
                    logging.debug(nal_unit)

                if len(nal_unit) == 1:
                    logging.info(f'Payload does not exist.')
                    logging.info(nal_unit)

                payloads = list(splite_bytes(nal_unit[1:], RAW_PAYLOAD_SIZE))

                is_idr = orig_nalu_type == 5
                if is_idr:
                    logging.debug(f'IDR', payloads)

                current_timestamp = timestamp() - self.timestamp_start_clock
                packets = []    

                if len(payloads) == 1:
                    self.sequence_number += 1

                    packet = create_rtp_packet_header(
                        sequence_number=self.sequence_number,
                        timestamp=current_timestamp, 
                        ssrc=self.ssrc
                    )
                    out_header_int = orig_f << 7
                    out_header_int += (orig_nri << 5)
                    out_header_int += orig_nalu_type
                    out_header = bytes([ out_header_int ])

                    packet += out_header
                    packet += payloads[0]

                    packets.append(packet)

                else:

                    for i, payload in enumerate(payloads):
                        self.sequence_number += 1

                        is_end = i == len(payloads) - 1

                        marker = 1 if is_end else 0
                        packet = create_rtp_packet_header(
                            sequence_number=self.sequence_number,
                            timestamp=current_timestamp, 
                            ssrc=self.ssrc,
                            marker=marker
                        )
                        out_fu_indicator_int = orig_f << 7
                        out_fu_indicator_int += (orig_nri << 5)
                        out_fu_indicator_int += 28 #FU-A

                        out_fu_indicator = bytes([ out_fu_indicator_int ])
                        packet += out_fu_indicator

                        if i == 0:
                            if is_idr:
                                packet += OUT_FU_HEADER_START_IDR
                            else:
                                packet += OUT_FU_HEADER_START

                        elif is_end:
                            if is_idr:
                                packet += OUT_FU_HEADER_END_IDR
                            else:
                                packet += OUT_FU_HEADER_END

                        else:
                            if is_idr:
                                packet += OUT_FU_HEADER_MIDDLE_IDR
                            else:
                                packet += OUT_FU_HEADER_MIDDLE
                        
                        packet += payload
                        packets.append(packet)

                asyncio.ensure_future(self.put_into_queue(packets))

        else:

            self.data_holder += data
    

    async def put_into_queue(self, packets):
        for packet in packets:
            await self.packet_queue.put(packet)


class SendTelloCommandProtocol:

    """
        An UDP Client protocol starting video streaming.
        In order to start video streaming from Tello,
        we need to send 'streamon' command.
    """

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto('command'.encode())
        self.transport.sendto('streamon'.encode())
        logging.debug('SendTelloCommandProtocol connection_made')
    
    def datagram_received(self, data, addr):
        logging.debug(f'SendTelloCommandProtocol data_received: {data.decode()}')
    
    def error_received(self, exc):
        logging.warn('SendTelloCommandProtocol error_received')

    def connection_lost(self, exc):
        logging.debug('SendTelloCommandProtocol connection_lost')


class SendRtpPacketProtocol:

    """
        An UDP Client protocol sending rtp packets to a remote peer(e.g. ffplay).
    """

    def __init__(self, packet_queue):
        self.packet_queue = packet_queue
    
    def connection_made(self, transport):
        logging.debug('SendRtpPacketProtocol connection_made')
        self.transport = transport
        asyncio.ensure_future(self.send_packet())

    def datagram_received(self, data, addr):
        logging.debug(f'SendRtpPacketProtocol data_received: {data.decode()}')
    
    def error_received(self, exc):
        logging.warn('SendRtpPacketProtocol error_received')

    def connection_lost(self, exc):
        logging.debug('SendRtpPacketProtocol connection_lost')

    async def send_packet(self):
        while True:
            packet = await self.packet_queue.get()
            self.transport.sendto(packet)


async def main():

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    receive_protocol = ReceiveTelloWebcamDataProtocol(queue)
    command_protocol = SendTelloCommandProtocol()
    rtp_protocol = SendRtpPacketProtocol(queue)

    await loop.create_datagram_endpoint(
        lambda: receive_protocol,
        local_addr=('0.0.0.0', 11111)
    )

    await loop.create_datagram_endpoint(
        lambda: command_protocol,
        remote_addr=('192.168.10.1', 8889)
    )
    
    await loop.create_datagram_endpoint(
        lambda: rtp_protocol,
        remote_addr=('127.0.0.1', 6004)
    )

    await asyncio.sleep(3600)


if __name__ == '__main__':
    asyncio.run(main())