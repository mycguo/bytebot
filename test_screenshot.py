#!/usr/bin/env python3
"""Test script to debug screenshot display issue."""

import asyncio
import httpx
import base64
from PIL import Image
import io

async def test_screenshot_flow():
    """Test the full screenshot flow like the UI does."""
    
    print("Testing screenshot API flow...")
    
    # Step 1: Call computer control service directly
    data = {"action": "screenshot"}
    computer_base_url = "http://localhost:9995"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            print(f"Making POST request to: {computer_base_url}/computer-use")
            print(f"Request data: {data}")
            
            response = await client.post(f"{computer_base_url}/computer-use", json=data)
            print(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"Response keys: {list(result.keys())}")
            print(f"Response contains 'data': {'data' in result}")
            print(f"Response contains 'image': {'image' in result}")
            
            if "data" in result:
                image_data = result["data"]
                print(f"Image data length: {len(image_data)}")
                
                # Try to decode and display
                try:
                    decoded_data = base64.b64decode(image_data)
                    print(f"Decoded data length: {len(decoded_data)}")
                    
                    image = Image.open(io.BytesIO(decoded_data))
                    print(f"PIL Image size: {image.size}, mode: {image.mode}")
                    
                    # Save for testing
                    image.save("/tmp/test_screenshot.png")
                    print("Screenshot saved to /tmp/test_screenshot.png")
                    
                except Exception as e:
                    print(f"Error processing image: {e}")
            else:
                print("No 'data' key in response")
                print(f"Full response: {result}")
                
    except Exception as e:
        print(f"Error in screenshot test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_screenshot_flow())