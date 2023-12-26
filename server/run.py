import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

connected = set()

def decode_image(base64_image):
    # Decode from base64
    jpg_original = base64.b64decode(base64_image)
    # Decode to a numpy array
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    # Decode image
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

async def handler(websocket, path):
    # Register the new connection
    connected.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if "image" in data:
                # Decode the image
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
        connected.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
