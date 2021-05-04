# tello-h264-to-rtp-packet

A pure python code snippet converting H.264 packets generated by [Tello EDU](https://www.ryzerobotics.com/jp/tello-edu)'s webcam to rtp packets.

This app generates rtp packets by manipulating packets' headers(not decoding/encoding H.264 packets).


## Requirements

 - Python 3.7 or later
 - [Tello EDU](https://www.ryzerobotics.com/jp/tello-edu)


### Tested OS

 - macOS Big Sur 11
 - Windows 10

### To test the rtp packets this app generates

 - [ffplay](https://ffmpeg.org/ffplay.html)

### To send H.264 packets to this app not using Tello

 - [FFmpeg](https://www.ffmpeg.org/)


## How to use

### 1. Run ffplay

```
cd tello-h264-to-rtp-packet
ffplay -protocol_whitelist file,rtp,udp -i video.sdp
```

### 2. Run app

Before you run the command below, please make sure that your PC successfully connects to Tello by Wi-Fi.

```
cd tello-h264-to-rtp-packet
python main.py
```

**NOTE:** Just after you start this app, `ffplay` may output many errors for a while. But after seconds, you should see a video which Tello is capturing by its webcam on `ffplay`'s window.


### Generate video stream by using FFmpeg.

macOS
```
ffmpeg -f avfoundation -list_devices true -i "" # list available devices.
ffmpeg -f avfoundation -framerate 30 -video_size 640x480 -i "0:none" -c:v libx264 -tune zerolatency -f rawvideo udp://127.0.0.1:11111
```

Windows
```
ffmpeg -list_devices true -f dshow -i dummy # list available devices.
ffmpeg -f dshow -framerate 30 -video_size 640x480 -i video="Integrated Camera" -c:v libx264 -tune zerolatency -f rawvideo udp://127.0.0.1:11111
```

In order to test the app by using another tool such as FFmpeg instead of using Tello, you need to set the size of an udp packet from it properly.
To do that, you need to set the proper value to `IN_PACKET_SIZE` defined in `main.py`.

For example:

```
IN_PACKET_SIZE = 1472
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