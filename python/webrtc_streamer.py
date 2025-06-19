import asyncio
import json
import logging
import re
import threading
import queue
from typing import Dict, Tuple, List, Optional, Union, Callable, Any
import cv2
import numpy as np
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration
from av import VideoFrame

# Default logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webrtc-streamer")

class FrameProvider:
    """Abstract class defining the interface for frame providers"""
    
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the next frame as a numpy array in BGR format"""
        raise NotImplementedError("Subclasses must implement get_frame()")

class QueueFrameProvider(FrameProvider):
    """Frame provider that gets frames from a queue"""
    
    def __init__(self, max_queue_size: int = 1):
        """Initialize the queue frame provider
        
        Args:
            max_queue_size: Maximum number of frames to keep in the queue
        """
        self.frame_queue = queue.Queue(maxsize=max_queue_size)
        self.last_frame = None
        self.active = True
    
    def set_frame(self, frame: np.ndarray) -> bool:
        """Add a frame to the queue
        
        Args:
            frame: OpenCV frame (numpy array in BGR format)
            
        Returns:
            True if the frame was added, False if the queue was full
        """
        if not self.active:
            return False
            
        try:
            # If queue is full, remove oldest frame
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
                    
            self.frame_queue.put_nowait(frame.copy())
            return True
        except Exception as e:
            logger.warning(f"Error adding frame to queue: {e}")
            return False
    
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the next frame from the queue"""
        if not self.active:
            return None
            
        try:
            # Non-blocking get with timeout
            frame = self.frame_queue.get_nowait()
            self.last_frame = frame
            return frame
        except queue.Empty:
            # Return the last frame if we have one
            return self.last_frame
        except Exception as e:
            logger.warning(f"Error getting frame from queue: {e}")
            return self.last_frame

class CustomVideoTrack(VideoStreamTrack):
    """VideoStreamTrack that gets frames from a FrameProvider"""
    
    def __init__(self, frame_provider: FrameProvider, width: int = 1280, height: int = 720, fps: int = 30):
        super().__init__()
        self.frame_provider = frame_provider
        self.width = width
        self.height = height
        self.fps = fps
    
    async def recv(self):
        """Get a frame from the provider and convert it to a VideoFrame"""
        # Get proper timestamp for the frame
        pts, time_base = await self.next_timestamp()
        
        # Get frame from provider
        frame = await self.frame_provider.get_frame()
        
        if frame is None:
            # If no frame available, sleep a bit and try again
            await asyncio.sleep(1/self.fps)
            return await self.recv()
        
        # Always resize the frame to match requested dimensions
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        
        # Convert BGR to RGB for the video frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create a VideoFrame from the numpy array
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame

class WebRTCStreamer:
    """High-quality WebRTC streaming server that can be used as a library"""
    
    def __init__(self, 
                 host: str = "0.0.0.0", 
                 port: int = 8080, 
                 cors_origin: str = "*",
                 default_width: int = 1280,
                 default_height: int = 720,
                 default_fps: int = 30,
                 default_bitrate: int = 10000,
                 max_bitrate: int = 50000):
        """Initialize the WebRTC streamer
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            cors_origin: CORS origin to allow (use "*" for any origin)
            default_width: Default video width if not specified by client
            default_height: Default video height if not specified by client
            default_fps: Default frame rate if not specified by client
            default_bitrate: Default bitrate in kbps if not specified by client
            max_bitrate: Maximum allowed bitrate in kbps
        """
        self.host = host
        self.port = port
        self.cors_origin = cors_origin
        self.default_width = default_width
        self.default_height = default_height
        self.default_fps = default_fps
        self.default_bitrate = default_bitrate
        self.max_bitrate = max_bitrate
        
        self.app = None
        self.runner = None
        self.site = None
        self.frame_provider = QueueFrameProvider()
        self.peer_connections = set()
        self.server_task = None
        self.server_thread = None
        self.loop = None
        self.is_running = False

        # Store streams by name
        self.streams = {}
        
        # Default landing page HTML
        self.index_html = """
        <html>
        <head>
            <title>WebRTC Video Stream</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                .stream-container { margin-top: 20px; }
                .stream { margin-bottom: 30px; }
                video { width: 100%; background: #000; border-radius: 4px; }
                .stream-info { margin-top: 10px; color: #666; }
                button { padding: 8px 16px; background: #3498db; color: white; border: none; 
                         border-radius: 4px; cursor: pointer; margin-right: 10px; }
                button:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <h1>WebRTC Video Streams</h1>
            <p>Available streams:</p>
            <div class="stream-container" id="streams">
                <!-- Streams will be added here -->
            </div>
            
            <script>
                // Simple function to create a stream element
                function createStreamElement(streamName, width, height, bitrate) {
                    const streamDiv = document.createElement('div');
                    streamDiv.className = 'stream';
                    streamDiv.innerHTML = `
                        <h3>${streamName}</h3>
                        <video id="video-${streamName}" autoplay playsinline></video>
                        <div class="stream-info">
                            Resolution: ${width}x${height}, Bitrate: ${bitrate}kbps
                        </div>
                        <div class="stream-controls">
                            <button onclick="connectToStream('${streamName}')">Connect</button>
                            <button onclick="disconnectFromStream('${streamName}')">Disconnect</button>
                        </div>
                    `;
                    return streamDiv;
                }
                
                // Function to connect to a stream
                async function connectToStream(streamName) {
                    const videoElement = document.getElementById(`video-${streamName}`);
                    if (!videoElement) return;
                    
                    const pc = new RTCPeerConnection();
                    
                    pc.ontrack = (event) => {
                        if (event.track.kind === 'video') {
                            videoElement.srcObject = event.streams[0];
                        }
                    };
                    
                    try {
                        // Create an offer
                        const offer = await pc.createOffer({
                            offerToReceiveVideo: true,
                            offerToReceiveAudio: false
                        });
                        
                        await pc.setLocalDescription(offer);
                        
                        // Send the offer to the server
                        const response = await fetch(`/offer?stream=${streamName}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                sdp: pc.localDescription.sdp,
                                type: pc.localDescription.type,
                                resolution: {
                                    width: 1280,  // Default HD
                                    height: 720,
                                    bitrate: 5000  // 5Mbps
                                }
                            })
                        });
                        
                        const answer = await response.json();
                        await pc.setRemoteDescription(new RTCSessionDescription(answer));
                        
                        // Store PC in the element
                        videoElement.pc = pc;
                        
                    } catch (e) {
                        console.error('Connection failed:', e);
                        alert(`Failed to connect to stream: ${e.message}`);
                    }
                }
                
                // Function to disconnect from a stream
                function disconnectFromStream(streamName) {
                    const videoElement = document.getElementById(`video-${streamName}`);
                    if (!videoElement || !videoElement.pc) return;
                    
                    videoElement.pc.close();
                    videoElement.srcObject = null;
                    delete videoElement.pc;
                }
                
                // Fetch available streams
                async function fetchStreams() {
                    try {
                        const response = await fetch('/server-info');
                        const data = await response.json();
                        
                        const streamsContainer = document.getElementById('streams');
                        streamsContainer.innerHTML = '';
                        
                        if (data.streams && data.streams.length > 0) {
                            data.streams.forEach(stream => {
                                const streamElement = createStreamElement(
                                    stream.name, 
                                    stream.width, 
                                    stream.height, 
                                    stream.bitrate
                                );
                                streamsContainer.appendChild(streamElement);
                            });
                        } else {
                            streamsContainer.innerHTML = '<p>No streams available</p>';
                        }
                    } catch (e) {
                        console.error('Failed to fetch streams:', e);
                    }
                }
                
                // Load streams on page load
                window.addEventListener('load', fetchStreams);
                
                // Refresh streams every 10 seconds
                setInterval(fetchStreams, 10000);
            </script>
        </body>
        </html>
        """
    
    def add_stream(self, name: str, width: int = None, height: int = None, fps: int = None, bitrate: int = None) -> QueueFrameProvider:
        """Add a new stream to the server
        
        Args:
            name: Name of the stream
            width: Width of the video (defaults to instance default)
            height: Height of the video (defaults to instance default)
            fps: Frame rate of the video (defaults to instance default)
            bitrate: Bitrate of the video in kbps (defaults to instance default)
            
        Returns:
            The QueueFrameProvider for this stream that can be used to set frames
        """
        frame_provider = QueueFrameProvider()
        
        self.streams[name] = {
            'name': name,
            'width': width or self.default_width,
            'height': height or self.default_height,
            'fps': fps or self.default_fps,
            'bitrate': bitrate or self.default_bitrate,
            'frame_provider': frame_provider
        }
        
        logger.info(f"Added stream '{name}' ({self.streams[name]['width']}x{self.streams[name]['height']}@{self.streams[name]['fps']}fps, {self.streams[name]['bitrate']}kbps)")
        
        return frame_provider
    
    def remove_stream(self, name: str) -> bool:
        """Remove a stream from the server
        
        Args:
            name: Name of the stream to remove
            
        Returns:
            True if the stream was removed, False if it didn't exist
        """
        if name in self.streams:
            # Deactivate the frame provider
            self.streams[name]['frame_provider'].active = False
            del self.streams[name]
            logger.info(f"Removed stream '{name}'")
            return True
        return False
    
    async def _index_handler(self, request):
        """Handler for the landing page"""
        return web.Response(content_type="text/html", text=self.index_html)
    
    async def _server_info_handler(self, request):
        """Handler for the server info endpoint"""
        streams_info = []
        
        for name, stream in self.streams.items():
            streams_info.append({
                'name': name,
                'width': stream['width'],
                'height': stream['height'],
                'fps': stream['fps'],
                'bitrate': stream['bitrate']
            })
        
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                'streams': streams_info,
                'maxBitrate': self.max_bitrate,
                'bitratePresets': [
                    {"name": "Low", "value": 1000},
                    {"name": "Medium", "value": 2500},
                    {"name": "High", "value": 5000},
                    {"name": "Very High", "value": 10000},
                    {"name": "Ultra", "value": 20000},
                    {"name": "Maximum", "value": 30000},
                    {"name": "Extreme", "value": 50000}
                ]
            })
        )
    
    def _extract_resolution_from_sdp(self, sdp: str) -> Tuple[int, int, int, int]:
        """Extract resolution and bitrate from SDP
        
        Args:
            sdp: Session Description Protocol string
            
        Returns:
            Tuple of (width, height, bitrate, fps)
        """
        # Default values
        width, height = self.default_width, self.default_height
        bitrate = self.default_bitrate
        fps = self.default_fps
        
        # Try to extract resolution from imageattr
        resolution_match = re.search(r'a=imageattr:\d+ recv \[x=\[1:(\d+)\],y=\[1:(\d+)\]\]', sdp)
        if resolution_match:
            width = int(resolution_match.group(1))
            height = int(resolution_match.group(2))
            logger.info(f"Found resolution in SDP imageattr: {width}x{height}")
        
        # Try to extract frame rate
        framerate_match = re.search(r'a=framerate:(\d+(?:\.\d+)?)', sdp)
        if framerate_match:
            fps = int(float(framerate_match.group(1)))
            logger.info(f"Found framerate in SDP: {fps}fps")
        
        # Try to extract bitrate constraint
        bitrate_match = re.search(r'b=AS:(\d+)', sdp)
        if bitrate_match:
            bitrate = int(bitrate_match.group(1))
            logger.info(f"Found bitrate in SDP: {bitrate}kbps")
        
        return width, height, bitrate, fps
    
    async def _offer_handler(self, request):
        """Handler for the offer endpoint"""
        params = await request.json()
        logger.info("Received SDP offer")
        
        # Get stream name from query parameters
        stream_name = request.query.get('stream', 'default')
        
        # Check if the stream exists
        if stream_name not in self.streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return web.Response(
                status=404,
                content_type="application/json",
                text=json.dumps({"error": f"Stream '{stream_name}' not found"})
            )
        
        # Get stream configuration
        stream = self.streams[stream_name]
        
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        
        # Extract video settings from SDP
        width, height, bitrate, fps = self._extract_resolution_from_sdp(offer.sdp)
        
        # Also check if resolution is explicitly provided in the request JSON
        if "resolution" in params:
            explicit_width = params["resolution"].get("width")
            explicit_height = params["resolution"].get("height")
            explicit_bitrate = params["resolution"].get("bitrate")
            explicit_fps = params["resolution"].get("frameRate")
            
            if explicit_width and explicit_height:
                logger.info(f"Using explicit resolution from request: {explicit_width}x{explicit_height}")
                width = explicit_width
                height = explicit_height
                
            if explicit_bitrate:
                bitrate = explicit_bitrate
                
            if explicit_fps:
                fps = explicit_fps
        
        logger.info(f"Client requested video: {width}x{height}@{fps}fps, {bitrate}kbps")
        
        # Limit to reasonable values for dimensions, but allow very high bitrates
        width = max(160, min(width, 1920))
        height = max(120, min(height, 1080))
        fps = max(5, min(fps, 60))
        bitrate = max(500, min(bitrate, self.max_bitrate))
        
        # Create peer connection
        pc = RTCPeerConnection()
        self.peer_connections.add(pc)
        logger.info(f"Created PeerConnection: {pc}")
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state is {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.peer_connections.discard(pc)
        
        # Attach the custom video track with the requested resolution
        video_track = CustomVideoTrack(
            stream['frame_provider'],
            width=width,
            height=height,
            fps=fps
        )
        pc.addTrack(video_track)
        
        # Handle the SDP negotiation
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        
        # Modify SDP answer to include bitrate constraint
        answer.sdp = answer.sdp.replace(
            "a=mid:0\r\n",
            f"a=mid:0\r\nb=AS:{bitrate}\r\n"
        )
        
        # Add H.264 specific parameters for higher quality when possible
        if "H264" in answer.sdp:
            logger.info(f"Using H.264 codec with optimized parameters for high bitrate: {bitrate}kbps")
            # Find the H.264 fmtp line and add quality parameters
            h264_pattern = r'(a=fmtp:\d+ .*)'
            match = re.search(h264_pattern, answer.sdp)
            if match:
                original_fmtp = match.group(1)
                # Add high profile and level parameters
                enhanced_fmtp = original_fmtp
                if "profile-level-id" not in enhanced_fmtp:
                    enhanced_fmtp += ";profile-level-id=640029"  # High profile, Level 4.2
                if "packetization-mode" not in enhanced_fmtp:
                    enhanced_fmtp += ";packetization-mode=1"  # Single NAL unit mode
                # Add quality vs. bitrate optimization
                enhanced_fmtp += f";x-google-max-bitrate={bitrate}"
                enhanced_fmtp += f";x-google-min-bitrate={int(bitrate * 0.7)}"
                enhanced_fmtp += f";x-google-start-bitrate={int(bitrate * 0.85)}"
                
                answer.sdp = answer.sdp.replace(original_fmtp, enhanced_fmtp)
        
        await pc.setLocalDescription(answer)
        
        logger.info(f"Sending SDP answer with video: {width}x{height}@{fps}fps, {bitrate}kbps")
        return web.Response(
            content_type="application/json",
            text=json.dumps({
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type,
                "actualResolution": {
                    "width": width,
                    "height": height,
                    "bitrate": bitrate,
                    "fps": fps
                }
            })
        )
    
    async def _start_server(self):
        """Start the aiohttp server in the event loop"""
        # Create the aiohttp application
        self.app = web.Application()
        
        # Set up routes
        self.app.router.add_get("/", self._index_handler)
        self.app.router.add_get("/server-info", self._server_info_handler)
        self.app.router.add_post("/offer", self._offer_handler)
        
        # Set up CORS
        cors = cors_setup(self.app, defaults={
            self.cors_origin: ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "OPTIONS"]
            )
        })
        
        # Apply CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        # Start the server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"Server running at http://{self.host}:{self.port}")
        
        # Keep the server running
        while self.is_running:
            await asyncio.sleep(1)
    
    async def _stop_server(self):
        """Stop the aiohttp server"""
        # Close all peer connections
        coros = [pc.close() for pc in self.peer_connections]
        if coros:
            await asyncio.gather(*coros)
        self.peer_connections.clear()
        
        # Close all frame providers
        for stream in self.streams.values():
            stream['frame_provider'].active = False
        
        # Close the site and runner
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("Server stopped")
    
    def _run_server(self):
        """Run the server in a separate thread with its own event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.server_task = self.loop.create_task(self._start_server())
            self.loop.run_until_complete(self.server_task)
        except asyncio.CancelledError:
            pass
        finally:
            remaining_tasks = asyncio.all_tasks(self.loop)
            if remaining_tasks:
                self.loop.run_until_complete(asyncio.gather(*remaining_tasks))
            self.loop.close()
    
    def start(self):
        """Start the WebRTC streaming server"""
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        # If no streams added, create a default one
        if not self.streams:
            logger.info("No streams added, creating default stream")
            self.add_stream('default')
        
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"WebRTCStreamer started on {self.host}:{self.port}")
        return True
    
    def stop(self):
        """Stop the WebRTC streaming server"""
        if not self.is_running:
            logger.warning("Server is not running")
            return
        
        self.is_running = False
        
        if self.loop and self.server_task:
            asyncio.run_coroutine_threadsafe(self._stop_server(), self.loop)
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
            if self.server_thread.is_alive():
                logger.warning("Server thread did not terminate properly")
        
        logger.info("WebRTCStreamer stopped")
        return True
    
    def set_frame(self, frame, stream_name='default'):
        """Set a frame for a specific stream
        
        Args:
            frame: OpenCV frame (numpy array in BGR format)
            stream_name: Name of the stream to set the frame for
            
        Returns:
            True if the frame was set, False otherwise
        """
        if not self.is_running:
            logger.warning("Cannot set frame, server is not running")
            return False
        
        if stream_name not in self.streams:
            logger.warning(f"Stream '{stream_name}' not found")
            return False
        
        return self.streams[stream_name]['frame_provider'].set_frame(frame)

# Simple example usage
if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="WebRTC Streamer Example")
    parser.add_argument("--host", default="0.0.0.0", help="Host for the HTTP server (default: 0.0.0.0)")
    parser.add_argument("--port", default=8080, type=int, help="Port for the HTTP server (default: 8080)")
    parser.add_argument("--camera", default=0, type=int, help="Camera index to use (default: 0)")
    parser.add_argument("--width", default=1280, type=int, help="Video width (default: 1280)")
    parser.add_argument("--height", default=720, type=int, help="Video height (default: 720)")
    parser.add_argument("--fps", default=30, type=int, help="Frame rate (default: 30)")
    parser.add_argument("--bitrate", default=5000, type=int, help="Bitrate in kbps (default: 5000)")
    args = parser.parse_args()
    
    # Create the streamer
    streamer = WebRTCStreamer(
        host=args.host,
        port=args.port,
        default_width=args.width,
        default_height=args.height,
        default_fps=args.fps,
        default_bitrate=args.bitrate
    )
    
    # Add a stream
    streamer.add_stream('webcam', args.width, args.height, args.fps, args.bitrate)
    
    # Start the server
    streamer.start()
    
    # Open the camera
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        logger.error("Could not open camera")
        streamer.stop()
        exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)
    
    # Main loop
    try:
        logger.info("Capturing frames from camera. Press Ctrl+C to stop.")
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Set the frame for the stream
            streamer.set_frame(frame, 'webcam')
            
            # Optional: Show the frame
            cv2.imshow('WebRTC Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        logger.info("Stopping...")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        streamer.stop()