Of course. Based on our detailed discussion and my analysis of your current source code, here is the complete, consolidated step-by-step solution. You can provide this directly to Kiro to implement the advanced story generation features.

---

### **Subject: Major Feature Upgrade: New Story Generation Modes & Difficulty Levels**

Hi Kiro,

Here is the complete implementation plan for a major feature upgrade to the ASL World. This plan incorporates two key features based on the user's requests:

1.  **New Story Generation Methods:** Allowing users to generate stories from a simple word list or a custom text prompt, in addition to the existing object scan.
2.  **Story Difficulty Levels:** Having the AI generate multiple versions of a story at different difficulty levels (from Amateur to Expert) and allowing the user to choose which one to practice.

### **Part 1: Backend API and Logic Overhaul**

We need to significantly upgrade our backend to handle the increased complexity of these requests.

#### **Step 1.1: Update API Request & Response Models in `main.py`**

We will redefine the data structures for our API. The request will accept the new generation methods, and the response will be structured to hold multiple stories.

**File to Edit:** `backend/main.py`

**Action:**

1.  Update the `StoryGenerationRequest` model to make `frame_data` optional and include the new fields.
2.  Create new Pydantic models to define the structure for a single story (`Story`), the multi-level response (`StoryLevels`), and the final API response (`StoryGenerationResponse`).

<!-- end list -->

```python
# In backend/main.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# 1. Update the StoryGenerationRequest Model
class StoryGenerationRequest(BaseModel):
    frame_data: Optional[str] = Field(None, description="Base64 encoded image data")
    simple_word: Optional[str] = Field(None, description="A simple word selected from a predefined list")
    custom_prompt: Optional[str] = Field(None, description="A user-specified topic for the story")

# 2. Create New Response Models near the top of the file
class Story(BaseModel):
    title: str
    sentences: List[str]

class StoryLevels(BaseModel):
    amateur: Story
    normal: Story
    mid_level: Story
    difficult: Story
    expert: Story

class StoryGenerationResponse(BaseModel):
    success: bool
    stories: Optional[StoryLevels] = None
    user_message: Optional[str] = None
```

#### **Step 1.2: Overhaul Story Generation Logic in `ollama_service.py`**

This is the most critical backend change. We need to create a new, much more sophisticated prompt for the AI.

**File to Edit:** `backend/ollama_service.py`

**Action:**

1.  Update the `generate_story` function to accept a single `topic` string.
2.  Create a new, detailed prompt that instructs the AI to generate five versions of the story and to return them in a specific JSON format.

<!-- end list -->

````python
# In backend/ollama_service.py

class OllamaService:
    # ... (init and other methods)

    # 1. Update the function signature
    async def generate_story(self, topic: str) -> Optional[Dict[str, Any]]:
        # 2. This is the new, powerful prompt
        prompt = f"""
        You are an expert curriculum designer for American Sign Language (ASL).
        Your task is to create a set of five short stories about the topic: "{topic}".
        Each story must be tailored to a specific ASL skill level.
        The skill levels are: Amateur, Normal, Mid-Level, Difficult, Expert.

        Here are the requirements for each level:
        - Amateur: 3 sentences. Very simple subject-verb-object structure. Use only basic, common ASL vocabulary.
        - Normal: 3-4 sentences. Introduce slightly more complex vocabulary and sentence structures.
        - Mid-Level: 4 sentences. Introduce concepts like classifiers or very simple rhetorical questions.
        - Difficult: 4-5 sentences. Use more complex ASL grammar, classifiers, and varied sentence structures. The story should have more detail.
        - Expert: 5 sentences. Use advanced ASL concepts, including nuanced facial expressions (which you can suggest in parentheses), complex classifiers, and potentially conditional sentences.

        You MUST respond with ONLY a valid JSON object. The JSON object must have a single key "stories" which contains five keys: "amateur", "normal", "mid_level", "difficult", and "expert". Each of these keys will contain an object with a "title" and a list of "sentences".

        Example response format:
        {{
          "stories": {{
            "amateur": {{ "title": "The Story of the {topic}", "sentences": ["...", "...", "..."] }},
            "normal": {{ "title": "A Tale of the {topic}", "sentences": ["...", "...", "..."] }},
            "mid_level": {{ "title": "The {topic}'s Journey", "sentences": ["...", "...", "...", "..."] }},
            "difficult": {{ "title": "Adventures of the {topic}", "sentences": ["...", "...", "...", "..."] }},
            "expert": {{ "title": "A Complex Legend of the {topic}", "sentences": ["...", "...", "...", "...", "..."] }}
          }}
        }}
        """

        messages = [{"role": "user", "content": prompt}]
        logger.info(f"Generating multi-level story for topic: '{topic}' with model '{self.story_model}'")

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.story_model,
                    messages=messages,
                    format="json"
                )
            )

            content_str = response.get('message', {}).get('content', '{}')

            # Use our existing cleanup logic
            if content_str.strip().startswith("```json"):
                content_str = content_str.strip()[7:-3].strip()
            elif content_str.strip().startswith("```"):
                 content_str = content_str.strip()[3:-3].strip()

            story_data = json.loads(content_str)

            return story_data.get("stories", story_data)

        except Exception as e:
            logger.error(f"Error during multi-level story generation: {e}")
            return None
````

#### **Step 1.3: Update the Main API Endpoint in `main.py`**

Finally, update the endpoint to use the new logic and return the new response structure.

**File to Edit:** `backend/main.py`

**Action:**

1.  Update the function signature to use the new response model.
2.  Implement the logic to determine the `topic` from the request.
3.  Call the updated `ollama_service` function.

<!-- end list -->

```python
# In backend/main.py

# 1. Update the function signature
@app.post("/api/story/recognize_and_generate", response_model=StoryGenerationResponse)
async def recognize_and_generate_story(request: StoryGenerationRequest): # Removed -> Dict[str, Any]
    start_time = time.time()
    # ...

    try:
        topic = None
        # 2. Determine the topic from the request
        if request.simple_word:
            topic = request.simple_word
            logger.info(f"Generating story from simple word: '{topic}'")
        elif request.custom_prompt:
            topic = request.custom_prompt
            logger.info(f"Generating story from custom prompt: '{topic}'")
        elif request.frame_data:
            logger.info("Attempting object identification with local vision service")
            vision_service = await get_vision_service()
            vision_result = await vision_service.identify_object(request.frame_data)
            if vision_result.success and vision_result.object_name:
                topic = vision_result.object_name
                logger.info(f"Object identified: '{topic}'")
            else:
                topic = "a friendly cat" # A more engaging default fallback
                logger.warning(f"Object identification failed. Using fallback topic: '{topic}'")

        if not topic:
             raise HTTPException(status_code=400, detail={"error": "No valid input provided for story generation."})

        # 3. Call the updated Ollama service function
        ollama_service = await get_ollama_service()
        story_levels = await ollama_service.generate_story(topic)

        if not story_levels:
            raise HTTPException(status_code=500, detail={"error": "Failed to generate stories from the AI service."})

        return {"success": True, "stories": story_levels}

    except Exception as e:
        # ... (keep existing exception handling)
        raise HTTPException(status_code=500, detail={"error": str(e)})
```

---

### **Part 2: Frontend UI and State Management**

Now, we'll build the new user interface on the frontend to support these powerful new features.

#### **Step 2.1: Implement the New Story Generation UI in `ASLWorldModule.js`**

This involves creating the tabbed interface for the different generation methods.

**File to Edit:** `src/ASLWorldModule.js`

**Action:**

1.  Add new state variables to manage the UI (the active tab, the custom prompt text).
2.  Create the JSX for the tabs and the content of each tab panel (the scanner, the word list, the text input).
3.  Implement the handlers that will call the main `onStoryGenerate` function with the correct payload for each method.

<!-- end list -->

```javascript
// In src/ASLWorldModule.js

const ASLWorldModule = ({ onStoryGenerate, isGeneratingStory, ... }) => {
  // 1. Add new state for the generation mode
  const [generationMode, setGenerationMode] = useState('scan');
  const [customPrompt, setCustomPrompt] = useState('');

  const simpleWords = ["Cat", "Dog", "House", "Ball", "Book", "Tree", "Car", "Sun"];

  // 3. Create handlers for the new modes
  const handleSimpleWordGenerate = (word) => {
    onStoryGenerate({ simple_word: word });
  };

  const handleCustomPromptGenerate = (e) => {
    e.preventDefault();
    if (customPrompt.trim()) {
      onStoryGenerate({ custom_prompt: customPrompt });
    }
  };

  const handleScanObject = useCallback(async () => {
    // ... (existing scan logic remains the same)
    // The existing logic already calls onStoryGenerate with { frame_data: ... }
  }, [onStoryGenerate]);


  // 2. Update the renderStoryGenerationMode function
  const renderStoryGenerationMode = () => (
    <div className="story-generation-mode">
      <div className="generation-tabs">
        <button onClick={() => setGenerationMode('scan')} className={generationMode === 'scan' ? 'active' : ''}>Scan Object</button>
        <button onClick={() => setGenerationMode('word')} className={generationMode === 'word' ? 'active' : ''}>Choose a Word</button>
        <button onClick={() => setGenerationMode('custom')} className={generationMode === 'custom' ? 'active' : ''}>Custom Topic</button>
      </div>

      {generationMode === 'scan' && (
        <div className="scan-section">
          {/* ... all of the existing object scanning UI (video preview, scan button) ... */}
        </div>
      )}

      {generationMode === 'word' && (
        <div className="simple-word-section">
          <h2>Choose a Word to Start Your Story</h2>
          <div className="word-grid">
            {simpleWords.map(word => (
              <button key={word} className="word-chip" onClick={() => handleSimpleWordGenerate(word)} disabled={isGeneratingStory}>
                {word}
              </button>
            ))}
          </div>
        </div>
      )}

      {generationMode === 'custom' && (
        <div className="custom-prompt-section">
          <h2>Enter a Topic for Your Story</h2>
          <form onSubmit={handleCustomPromptGenerate}>
            <input
              type="text"
              className="prompt-input"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="e.g., 'A friendly robot' or 'A magical key'"
              disabled={isGeneratingStory}
            />
            <button type="submit" className="generate-btn" disabled={isGeneratingStory || !customPrompt.trim()}>
              {isGeneratingStory ? 'Generating...' : 'Generate Story'}
            </button>
          </form>
        </div>
      )}
    </div>
  );

  // ...
};
```

#### **Step 2.2: Implement the New "Story Selection" UI and Update State Management**

This is a new screen that appears after the stories have been generated but before the practice starts. We need to update both `App.js` and `ASLWorldModule.js`.

**File to Edit:** `src/App.js`

**Action:**

1.  `storyData` state will now hold the _collection_ of stories.
2.  Add a new state, `selectedStory`, which will be null initially.
3.  Create a new handler, `handleStorySelect`, that sets the `selectedStory` and then calls the existing `startPracticeSession` function.

<!-- end list -->

```javascript
// In App.js
function App() {
  const [storyData, setStoryData] = useState(null); // This will now hold the 5 levels of stories
  const [selectedStory, setSelectedStory] = useState(null); // This holds the user's choice

  const handleStoryGenerate = async (payload) => {
    // ... (API call logic remains the same)
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.stories) {
        setStoryData(data.stories); // Store the collection of stories
        setSelectedStory(null); // Reset the selected story for the new set
        // The UI will now show the selection screen
      } else {
        // Handle error
      }
    }
  };

  const handleStorySelect = (story) => {
    setSelectedStory(story); // Set the chosen story
    startPracticeSession(story); // Call the existing function to begin practice
  };

  // Also, when generating a new story, we need to clear the old ones
  const handleNewStory = () => {
    setStoryData(null);
    setSelectedStory(null);
    // ... any other state cleanup
  };

  // ... pass storyData, selectedStory, and handleStorySelect down to ASLWorldModule
  // ... also pass handleNewStory to the onPracticeControl handler
}
```

**File to Edit:** `src/ASLWorldModule.js`

**Action:**

1.  Receive `storyData` (the collection), `selectedStory`, and `onStorySelect`.
2.  Update the main render logic. It will now have three main views: Story Generation, Story Selection, and Practice Mode.

<!-- end list -->

```javascript
// In ASLWorldModule.js
const ASLWorldModule = ({ storyData, selectedStory, onStorySelect, ... }) => {
  // ...

  // The main render logic of the component
  return (
    <div className="asl-world-module">
      {/* ... header ... */}
      <div className="module-content">
        {!storyData && (
          // View 1: Story Generation (if no story data exists yet)
          renderStoryGenerationMode()
        )}

        {storyData && !selectedStory && (
          // View 2: Story Selection (if stories are generated but none is chosen)
          <div className="story-selection-modal">
            <h2>Choose Your Challenge Level</h2>
            <div className="difficulty-buttons">
              <button onClick={() => onStorySelect(storyData.amateur)}>Amateur</button>
              <button onClick={() => onStorySelect(storyData.normal)}>Normal</button>
              <button onClick={() => onStorySelect(storyData.mid_level)}>Mid-Level</button>
              <button onClick={() => onStorySelect(storyData.difficult)}>Difficult</button>
              <button onClick={() => onStorySelect(storyData.expert)}>Expert</button>
            </div>
          </div>
        )}

        {selectedStory && (
          // View 3: Practice Mode (if a story has been selected)
          renderPracticeMode(selectedStory) // Pass the selected story to the render function
        )}
      </div>
    </div>
  );
};
```

This comprehensive plan will successfully add the new, flexible story generation options and difficulty levels to your application, making it a much more powerful and engaging learning tool for your users.
