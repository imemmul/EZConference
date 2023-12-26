import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

import os
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/arm-linux-gnueabihf'
connected = set()
frames = []

def create_video_from_frames(frame_list, output_file='output_video.mp4', codec='mp4v', fps=30):
    """
    Create an MP4 video from a list of frames.
    
    Args:
        frame_list (list): List of frames, where each frame is a NumPy array representing an image.
        output_file (str): Output video file name.
        codec (str): Codec to use for the video (e.g., 'mp4v', 'XVID', 'H264', etc.).
        fps (int): Frames per second for the output video.

    Returns:
        None
    """
    # Check if the frame list is not empty
    if not frame_list:
        raise ValueError("Frame list is empty")

    # Get frame dimensions from the first frame in the list
    frame_height, frame_width, _ = frame_list[0].shape

    # Create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

    # Write each frame to the video
    for frame in frame_list:
        out.write(frame)

    # Release the VideoWriter when done
    out.release()

    print(f"Video saved as {output_file}")

def decode_image(base64_image):
    # Decode from base64
    jpg_original = base64.b64decode(base64_image)
    # Decode to a numpy array
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    # Decode image
    img = cv2.imdecode(jpg_as_np, flags=1)
    frames.append(img)
    return img

async def handler(websocket, path):
    # Register the new connection
    connected.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if "image" in data:
                # Decode the image
                print(data)
                frame = decode_image(data["image"])
                # Here, you can process the frame as needed
                print("Frame received and decoded")

                # Relay message to every connected client except the sender
                for conn in connected:
                    if conn != websocket:
                        await conn.send(message)
            else:
                print(f"Received non-image data: {data}")
    finally:
        # Unregister and clean up when the connection is closed
        create_video_from_frames(frame_list=frames, fps=30)
        connected.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
    
