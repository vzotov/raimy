# Video Generation Service

Prototype for integrating video generation into Raimy using Google's Veo 3 API.

## Concept

When Raimy suggests cooking techniques (e.g., "how to mince onions", "proper knife sharpening", "folding egg whites"), the system will:

1. **Search existing videos** - Use vector search to find if we already have a video for this technique in our storage
2. **Generate new video** - If the technique is new or not in our database, generate a fresh video using Veo 3
3. **Cache & serve** - Store the generated video for future use and serve it to the user

## Benefits

- Visual learning for cooking techniques
- Reduce API costs by reusing generated videos
- Enhance user experience with dynamic, contextual video content
- Build a growing library of cooking technique videos over time

## Current Status

**Prototype phase** - Basic Veo 3 API integration

## Setup

```bash
pip install google-genai
```

Set your Google API key:
```bash
export GOOGLE_API_KEY="your-api-key"
```

## Usage

Run the test script:
```bash
python test_veo3.py
```

This will generate a video based on the prompt and save it as `veo3_output.mp4`.

## Future Integration

### Architecture

```
User Query → Raimy Agent
    ↓
Identifies cooking technique
    ↓
Vector Search (existing videos)
    ↓
Found? → Serve from storage
    ↓
Not found? → Generate with Veo 3
    ↓
Store in database + vector index
    ↓
Serve to user
```

### Requirements

- [ ] Vector database setup for video embeddings
- [ ] Video storage solution (S3, GCS, or local)
- [ ] API service endpoints for video generation
- [ ] Integration with Raimy agent workflow
- [ ] Caching strategy to minimize API costs
- [ ] Video metadata schema (technique name, duration, cost, etc.)

## Pricing

Veo 3: $0.75 per second of generated video

Example: 8-second video = $6.00

## Notes

- Videos are generated asynchronously (takes 1-3 minutes)
- Veo 3 is currently in paid preview
- Requires billing enabled on Google Cloud project
- Currently US-only availability