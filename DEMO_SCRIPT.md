# AABLAS-LexiGPT: Teacher Demo Script

## Overview (2-3 minutes)
**What is AABLAS?** An **Agentic Legal Co-Pilot**—an offline-first system that combines AI reasoning (planner → executor → evaluator), document search (RAG), and legal document generation, all running locally on your machine.

**Key differentiator:** Unlike ChatGPT or traditional legal tools (LegalZoom, LawGeex), AABLAS doesn't just answer questions—it actively *plans and executes multi-step workflows* to solve complex legal problems.

---

## Pre-Demo Setup (5 minutes before)

### 1. Start Ollama (if not already running)
```bash
# Open a terminal and run Ollama
ollama serve
# In another terminal: ollama pull llama3 (if not already pulled)
```

### 2. Start the Flask Backend
```bash
cd "c:\Users\Yugandhar Paulbudhe\Desktop\AABLAS - Copy"
.\.venv\Scripts\activate
python app.py
# Should see: "Flask backend running on http://localhost:5000"
```

### 3. Open the Frontend
- Open `index.html` in your browser (double-click or use a local server)
- Should see the chat interface with sidebar buttons

### 4. Prepare Test Files
- Have a sample PDF or text file ready to upload (e.g., a contract, legal document)
- Or use the pre-existing PDFs in `data/pdfs/` (e.g., "Indian Contract Act, 1872.pdf")

---

## Demo Flow (10-15 minutes)

### **Demo 1: Basic Chat + RAG (2 minutes)**

**Narrative:** "Let's start with a simple legal question."

1. **In the chat input, type:**
   ```
   What is an NDA and what are its key clauses?
   ```
   
2. **Show the response:**
   - The system retrieves relevant legal documents from the knowledge base
   - Answer includes inline citations (e.g., "[1] Legal document X, [2] Legal document Y")
   - **Point out:** This isn't a generic ChatGPT answer—it's *grounded in our local legal corpus*

3. **Follow-up question:**
   ```
   What happens if someone breaches an NDA?
   ```
   - Show that the system maintains conversation context
   - Citations help verify the answer

---

### **Demo 2: Document Generation (3 minutes)**

**Narrative:** "Now let's create a legal document. Instead of hiring a lawyer or paying LegalZoom fees, AABLAS can generate templates on the fly."

1. **Click the "Generate" button in the sidebar** (document icon)

2. **In the modal, select:**
   - **Template:** "NDA" or "Employment Offer"
   - **Document Type:** "DOCX" or "PDF"
   - **Fill in sample fields:**
     - For NDA: Party A Name, Party B Name, Effective Date, Confidentiality Duration
     - For Employment: Employee Name, Job Title, Annual Salary, Start Date

3. **Click "Generate"**
   - Wait for the agent to run (watch the Agent Logs modal pop up)
   - Show the **"Show reasoning"** dropdown to reveal the agent's plan:
     - Step 1: Validate inputs
     - Step 2: Populate template
     - Step 3: Generate DOCX/PDF
   - **Point out:** The agent is transparent about what it's doing

4. **Download the generated document**
   - Click the download link in the chat
   - Open it in Word/PDF reader to show it's a real, formatted document
   - **Emphasize:** Generated locally, no cloud service, instant

---

### **Demo 3: File Summarization (3 minutes)**

**Narrative:** "Let's say you have a long legal document—a contract, act, or policy. AABLAS can summarize it in seconds."

1. **Method A: Upload a file, then ask to summarize in chat**
   - **Click "Upload Documents"** button (sidebar)
   - **Select a PDF** from `data/pdfs/` (e.g., "Indian Contract Act, 1872.pdf")
   - **In chat, type:**
     ```
     Summarize the contents of that file
     ```
   - **Show the agent logs:**
     - The agent recognizes the intent (summarization)
     - It reads the file
     - It calls the summarize tool
     - Returns a structured summary with key sections

2. **Method B: Use the Summarize button**
   - **Click "Summarize"** button (sidebar)
   - **Fill in:**
     - Request: "Summarize this legal document, highlighting key clauses and obligations"
     - File Path: "Indian Contract Act, 1872.pdf" (or just the filename)
   - **Click "Generate"**
   - **Show the result:** Concise, structured summary

---

### **Demo 4: RAG Synthesis (Multi-step analysis) (3 minutes)**

**Narrative:** "AABLAS isn't just answering questions—it can synthesize answers from multiple documents and cite sources."

1. **In chat, type:**
   ```
   Analyze contract enforcement procedures according to Indian law and highlight common pitfalls
   ```

2. **Watch the agent logs:**
   - **Planner step:** Agent creates a plan:
     - Step 1: Search for contract enforcement procedures
     - Step 2: Search for common pitfalls in Indian law
     - Step 3: Synthesize and cite sources
   - **Executor steps:** Agent runs RAG search, retrieves relevant sections
   - **Evaluator step:** Agent scores the response

3. **Show the response:**
   - Contains inline citations `[1] [2] [3]`
   - Each citation maps to a source document
   - **Point out:** This is verifiable, grounded reasoning—not hallucination

---

### **Demo 5: Observable Reasoning (1-2 minutes)**

**Narrative:** "One key differentiator is transparency. Users can see exactly how the agent solved the problem."

1. **In the chat, look at the agent response**
2. **Click "Show reasoning"**
3. **Expand reasoning steps:**
   - See the agent's thought process for each step
   - See expectations (what the agent was trying to achieve)
   - See the actual output
   - **Emphasize:** This transparency builds trust and allows users to verify or override decisions

---

## Demo 6 (Optional): Offline Advantage (1 minute)

**Narrative:** "Everything runs locally. No cloud calls, no data sent to OpenAI or other services."

1. **Show the system.**
   - All chat history is stored in `data/chat_history.json` (local file)
   - All embeddings are in `vector_data/` (local Chroma DB)
   - Model runs via Ollama (local)

2. **Emphasize:**
   - **Privacy:** Sensitive legal documents never leave your machine
   - **Speed:** No network latency, instant responses
   - **Cost:** No per-token API fees (unlike ChatGPT)
   - **Compliance:** HIPAA/GDPR-friendly (no third-party data processors)

---

## Key Points to Emphasize

| Feature | Why It Matters | Competitive Advantage |
|---------|---------------|----------------------|
| **Agentic Planning** | Multi-step reasoning for complex tasks | ChatGPT/Gemini are stateless; LegalZoom is rigid templates |
| **Observable Steps** | Users verify reasoning; builds trust | Black-box LLMs = "magic answer" problem |
| **RAG Grounding** | Answers cite actual documents | Reduces hallucinations; verifiable |
| **Multi-Domain** | One tool for summaries, analysis, generation | Traditional tools: separate products for each task |
| **Offline** | Privacy, speed, no subscription costs | Cloud tools charge per API call |
| **Extensible** | Add new tools = new agent capabilities | Competitors' features are baked in |

---

## Talking Points for Questions

### Q: "How is this different from ChatGPT?"
**A:** ChatGPT answers questions one at a time. AABLAS *plans* multi-step workflows. For example, if you ask AABLAS to "analyze a contract and summarize risks," it:
1. Plans the steps (read file → extract key terms → search for risks → synthesize)
2. Executes each step, using different tools
3. Shows you the plan and reasoning at each step

ChatGPT just gives you an answer; you don't know how it decided what to include.

### Q: "Why is offline important?"
**A:** Three reasons:
1. **Privacy:** Sensitive contracts stay on your machine (no cloud)
2. **Speed:** No network latency; instant responses
3. **Cost:** No per-token fees like OpenAI (traditional licensing model)

### Q: "Can it handle complex legal documents?"
**A:** Yes, via RAG. We ingest PDFs, acts, and documents into a vector DB. When you ask a question, the system searches for relevant sections and synthesizes answers with citations.

### Q: "Is it accurate?"
**A:** Like all AI, it can hallucinate. But AABLAS reduces that risk by:
- Grounding answers in actual documents (RAG)
- Showing its reasoning (users can verify)
- Using smaller, local models (more conservative)
- Allowing humans to review and override

### Q: "Can I customize it?"
**A:** Yes, fully extensible:
- Add new document templates (modify `services/docgen_services.py`)
- Add new tools to the agent (modify `services/agent_services.py` TOOL_MAP)
- Ingest your own documents into the vector DB (upload PDFs via the UI)
- Change the model (any Ollama-compatible model)

---

## Troubleshooting During Demo

| Issue | Solution |
|-------|----------|
| Chat input not responding | Check Flask backend is running (`python app.py`); check browser console for errors |
| Agent logs modal not opening | Refresh the page; check browser console |
| Documents not uploading | Ensure `data/pdfs/` exists; check file permissions; check browser console |
| Ollama connection error | Ensure `ollama serve` is running; check `OLLAMA_HOST` in `config.py` |
| Slow response | Ollama models are slower than cloud APIs (expected); give it 10-30 seconds |
| RAG not finding documents | Chroma DB may need re-initialization; run `python rag/chroma_init.py` |

---

## Timing Breakdown

- **Intro & Setup:** 2-3 min
- **Demo 1 (Chat + RAG):** 2 min
- **Demo 2 (Document Generation):** 3 min
- **Demo 3 (Summarization):** 3 min
- **Demo 4 (RAG Synthesis):** 3 min
- **Demo 5 (Reasoning):** 1-2 min
- **Demo 6 (Offline):** 1 min
- **Buffer for questions:** 3-5 min
- **Total:** ~18-22 minutes

---

## Slides / Talking Points (Optional)

If you want to create a slide deck alongside this demo:

1. **Title Slide:** AABLAS-LexiGPT
2. **Problem Statement:** Existing legal tools are either chatbots (no reasoning) or rigid templates (no intelligence)
3. **Solution:** Agentic architecture with multi-domain tasks, observable reasoning, offline privacy
4. **Demo:** [Run live demos as above]
5. **Competitive Comparison Table:** [From COMPETITIVE_ADVANTAGES.md]
6. **Tech Stack:** Flask, Ollama, ChromaDB, ReportLab/python-docx (local PDF/DOCX generation)
7. **Future Work:** 
   - Custom reasoning steps
   - Integration with external APIs (optional, for cloud backups)
   - Batch processing (analyze 100 contracts at once)
   - Web UI improvements

---

## Files to Showcase (if asked for code)

1. **Agent Pipeline:** `services/agent_services.py` (planner, executor, evaluator)
2. **RAG Retriever:** `rag/retriever.py` (search and citation)
3. **Document Generation:** `services/docgen_services.py` (template rendering)
4. **Frontend Intent Detection:** `routes/ollama_routes.py` (keyword detection → agent routing)
5. **Frontend UI:** `script.js` (modal handling, chat flow, SSE streaming)

---

## Closing Statement

> "AABLAS demonstrates that legal AI doesn't have to be a trade-off between power (cloud APIs) and privacy (offline). By combining local reasoning, document retrieval, and transparent agent planning, we've built a system that's fast, private, trustworthy, and extensible. Whether you're a solo lawyer, a legal firm, or a compliance officer, AABLAS gives you an agentic co-pilot that thinks through problems the way you do—and shows you how it got there."
