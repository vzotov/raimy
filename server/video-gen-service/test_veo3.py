#!/usr/bin/env python3
"""
Simple test script for Veo 3 video generation API
Run with: python test_veo3.py

Install: pip install google-genai
"""

import os
import time
from google import genai


def main():
    # Get API key from environment or input
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        api_key = input("Enter your Google API Key: ")

    client = genai.Client(api_key=api_key)

    prompt = """Showing how to properly mince onions. Close-up shots of hands using a sharp knife 
    to finely chop onions on a wooden cutting board. Well-lit kitchen setting with clear focus on 
    the chopping technique."""

    print("=" * 60)
    print("Veo 3 Video Generation Test")
    print("=" * 60)
    print(f"\nPrompt: {prompt}")
    print("\nGenerating video...\n")

    # Generate video
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt
    )

    print(f"Operation: {operation.name}")

    # Poll the operation status until the video is ready
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    print("\nVideo generation completed!")

    # Download the generated video
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save("veo3_output.mp4")

    print(f"Video saved to: veo3_output.mp4")
    print(f"Video URI: {generated_video.video.uri}")


if __name__ == "__main__":
    main()
