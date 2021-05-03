# tello-h264-to-rtp-packet

A pure python code snippet converting H.264 packets from [Tello EDU](https://www.ryzerobotics.com/jp/tello-edu) to rtp packets.

This app generates rtp packets by manipulating packets' headers(not decoding/encoding h264 packets).


## System requirements

 - Python 3.7 or later
 - [Tello EDU](https://www.ryzerobotics.com/jp/tello-edu)

 
 The author tested the app on `mac OS Big Sur 11`.


### To test the rtp packets this app generates

 - [ffplay](https://ffmpeg.org/ffplay.html)

### To send H.264 packets to this app not using Tello

 - [FFmpeg](https://www.ffmpeg.org/)


## How to use

Run this app:

```
cd tello-h264-to-rtp-packet
python main.py
```

View video by using ffplay:

```
cd tello-h264-to-rtp-packet
ffplay -protocol_whitelist file,rtp,udp -i video.sdp
```

Generating video streaming by using FFmpeg(on mac OS).

```
ffmpeg -f avfoundation -list_devices true -i "" # list available devices.
ffmpeg -f avfoundation -framerate 30 -video_size 640x480 -i "0:none" -c:v libx264 -tune zerolatency -f rawvideo udp://127.0.0.1:11111
```

## Reference

### RTP/H.264

 - [Kurento Blog - RTP (I): Intro to RTP and SDP](https://www.kurento.org/blog/rtp-i-intro-rtp-and-sdp)
 - [ProgrammerSought - H264 basic and rtp packet unpacking (transfer)](https://www.programmersought.com/article/2518934242/)
 - [Yumi Chan's Blog - Introduction to H.264: (1) NAL Unit](https://yumichan.net/video-processing/video-compression/introduction-to-h264-nal-unit/)
 - [RFC 3550 - RTP: A Transport Protocol for Real-Time Applications](https://tools.ietf.org/html/rfc3550)
 - [RFC 6184 - RTP Payload Format for H.264 Video](https://tools.ietf.org/html/rfc6184)

### FFmpeg/ffplay

 - [Kurento Blog - RTP (II): Streaming with FFmpeg](https://www.kurento.org/blog/rtp-ii-streaming-ffmpeg)
 - [FFmpeg StreamingGuide](https://fftrac-bg.ffmpeg.org/wiki/StreamingGuide)
 - [avfoundation - ffmpeg](http://underpop.online.fr/f/ffmpeg/help/avfoundation.htm.gz)

### Tello

 - [SDK 2.0 User Guide](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)