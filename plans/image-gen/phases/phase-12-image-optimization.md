# Phase 12: Image Optimization for Web

## Checklist

- [x] Add Pillow-based optimization to `GCSStorage.upload_image()`
- [x] Add `quality` parameter (default 72)
- [x] Log before/after sizes
- [x] Verify Pillow is in agent-service dependencies
- [ ] End-to-end test: generate recipe, check image sizes < 100KB
- [ ] Verify images look acceptable in frontend

## Additional: "Generate images" intent

- [x] Add `generate_images` intent to recipe creator agent
- [x] Skip steps that already have `image_url` in ImageGenAgent
- [x] Handle `generate_images` event in main.py
- [x] Support `regenerate_step_numbers` for regenerating specific steps by number
