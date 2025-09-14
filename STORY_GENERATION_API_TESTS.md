# Test Commands for Fixed Story Generation API

## Test the exact endpoint the frontend calls:

```bash
# Test story generation (non-versioned - what frontend uses)
curl -X POST https://story-sign.onrender.com/api/asl-world/story/recognize_and_generate \
  -H "Content-Type: application/json" \
  -d '{"frame_data": "data:image/jpeg;base64,test-image-data"}'

# Test story generation (versioned)
curl -X POST https://story-sign.onrender.com/api/v1/asl-world/story/recognize_and_generate \
  -H "Content-Type: application/json" \
  -d '{"frame_data": "data:image/jpeg;base64,test-image-data"}'
```

## Expected Response:

```json
{
  "success": true,
  "recognized_objects": ["book", "table", "lamp", "chair"],
  "story": {
    "id": 2,
    "title": "My Scanned Objects Story",
    "content": "I used my camera to scan the objects around me...",
    "sentences": [
      "I see a book on the table.",
      "The table is brown and sturdy.",
      "The lamp gives bright light.",
      "I sit on the comfortable chair."
    ],
    "vocabulary": ["book", "table", "lamp", "chair", "see", "brown", "light", "sit"]
  },
  "message": "Objects recognized and story generated from your scan (demo mode)"
}
```

## Frontend Integration:

After deployment, the frontend call:
```javascript
fetch(`${API_BASE_URL}/api/asl-world/story/recognize_and_generate`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ frame_data: imageData })
})
```

Should now work without 404 errors!
