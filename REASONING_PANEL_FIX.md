# Reasoning Panel Fix - Implementation Details

## Problem
The "Show Reasoning" dropdown in the Agent Logs modal was showing "No reasoning loaded" even after the agent executed and reasoning events were emitted.

## Root Cause
1. **Reasoning events were not being persisted** - Events came through SSE but were immediately discarded if the checkbox wasn't already checked
2. **No buffer** - When users clicked "Show Reasoning" after the agent ran, there was no stored history to display
3. **Race condition** - Events arrived via SSE, but if the checkbox wasn't checked, they were lost forever

## Solution Implemented

### 1. Added Reasoning Event Buffer to State
```javascript
const state = {
    ...
    reasoningBuffer: [] // Buffer to store all reasoning events for display
};
```

### 2. Buffer All Relevant Events
Updated the SSE message handler to always buffer reasoning-related events:
```javascript
// Always buffer reasoning events, and display if checkbox is checked
if (data.type === 'planner_output' || data.type === 'reason' || data.type === 'evaluation' || data.type === 'run_complete') {
    state.reasoningBuffer.push(data);
}
```

### 3. Display Buffered Events When Checkbox is Toggled
Updated the checkbox event listener to populate the panel from the buffer:
```javascript
reasoningToggle.addEventListener('change', (e) => {
    const panel = document.getElementById('agent-reasoning-container');
    const list = document.getElementById('agent-reasoning-list');
    if (e.target.checked) {
        panel.classList.remove('hidden');
        // Clear and populate with buffered reasoning events
        list.innerHTML = '';
        if (state.reasoningBuffer.length === 0) {
            list.innerHTML = 'No reasoning loaded.';
        } else {
            state.reasoningBuffer.forEach(entry => addReasoningEntryToPanel(entry));
        }
    } else {
        panel.classList.add('hidden');
    }
});
```

### 4. Clear Buffer on New Run
Clear the buffer when starting a new agent stream to avoid mixing events from different runs:
```javascript
function connectAgentStream() {
    if (state.agentEventSource) return; // already connected
    state.reasoningBuffer = []; // Clear buffer for new run
    ...
}
```

## How It Works Now

### Flow:
1. **User clicks sidebar "Agent" button** → Opens Agent Logs modal
2. **User runs an agent task** (e.g., asks to generate document, summarize, etc.)
3. **Agent emits SSE events** → All reasoning events are captured in `state.reasoningBuffer`
4. **User clicks "Show Reasoning" checkbox** → Panel displays all buffered reasoning events
5. **Reasoning entries show**:
   - ✅ Planner output (the plan the agent created)
   - ✅ Reason steps (internal reasoning with expectations)
   - ✅ Evaluation steps (final scoring)
   - ✅ Run complete event

### What Gets Displayed:
- **Planner Output**: The structured plan (steps with tools and expected inputs)
- **Reason Events**: Internal reasoning steps with title and expectations
- **Evaluation**: Final evaluation result (success/failure and reasoning)
- **Run Complete**: Agent finished with final result

## Testing the Fix

### Manual Test Steps:
1. Open the application (`index.html`)
2. Click **"Agent"** button in sidebar (opens Agent Logs modal)
3. In the main chat:
   - Type: **"Create an NDA document"** 
   - Or: **"Summarize the Indian Contract Act"**
   - Or: **"Analyze contract enforcement in Indian law"**
4. Watch the agent run (you'll see log entries appear)
5. **Check the "Show Reasoning" checkbox** in the Agent Logs modal
6. **Reasoning panel should now show**:
   - Planner output (the steps)
   - Each reasoning step with title and expectations
   - Evaluation result

## Files Modified
- `script.js`:
  - Line 11: Added `reasoningBuffer: []` to state
  - Lines 148-165: Updated checkbox change handler
  - Line 850: Clear buffer in `connectAgentStream()`
  - Lines 883-887: Always buffer reasoning events

## Why This Works Better
- **Persistent history** - Reasoning events are preserved until the next run
- **User-friendly** - Users can check "Show Reasoning" anytime during or after agent execution
- **No race conditions** - Events are buffered immediately regardless of checkbox state
- **Clean separation** - Each agent run gets its own buffer (cleared on new connection)

## Related Fixes
This fix complements earlier improvements:
- ✅ Enhanced `emit_event()` to include `expectations` field for reason steps
- ✅ Updated `addReasoningEntryToPanel()` to extract and display expectations
- ✅ Fixed modal registration for summarize modal
- ✅ Added file path resolver for uploaded documents
