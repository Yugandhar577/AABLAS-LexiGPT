# LexiGPT Research Paper - Flowchart Specifications
## Flowcharts, Diagrams & Visual Assets
**Date:** December 3, 2025  
**Purpose:** Define all flowcharts needed for research paper with placement recommendations

---

## Table of Contents
1. [System Architecture Diagrams](#system-architecture-diagrams)
2. [Process Flow Diagrams](#process-flow-diagrams)
3. [User Journey Diagrams](#user-journey-diagrams)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Algorithm Flow Diagrams](#algorithm-flow-diagrams)
6. [Comparison Charts](#comparison-charts)

---

## 1. System Architecture Diagrams

### 1.1 High-Level System Architecture
**Position in Paper:** Introduction / System Overview (Page 3-4)  
**Description:** Bird's eye view of all components and how they interact  
**Elements:**
```
┌─────────────────────────────────────────────────────────────┐
│                    LEXIGPT SYSTEM ARCHITECTURE              │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   Frontend Layer     │
                    │  (HTML/CSS/JS)       │
                    │  - Chat Interface    │
                    │  - Document Upload   │
                    │  - CoT Display       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │   API Layer         │
                    │  (Flask 3.1.2)      │
                    │  - Chat Endpoint    │
                    │  - Auth Endpoint    │
                    │  - Docgen Endpoint  │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐          ┌────▼────┐         ┌─────▼─────┐
    │ Agentic │          │  RAG    │         │ Document  │
    │ Loop    │          │Pipeline │         │ Generator │
    │         │          │         │         │           │
    │- Plan   │          │- Query  │         │- Templates│
    │- Execute│          │- Retrieve          │- Output   │
    │- Eval   │          │- Rank   │         │- Formats  │
    └────┬────┘          └────┬────┘         └─────┬─────┘
         │                    │                     │
         └────────────────────┼─────────────────────┘
                              │
         ┌────────────────────▼─────────────────────┐
         │      LLM Engine (Llama 3 via Ollama)    │
         │  - Legal Reasoning                      │
         │  - Multi-step Planning                  │
         │  - Response Generation                  │
         └────────────────────┬─────────────────────┘
                              │
         ┌────────────────────▼─────────────────────┐
         │      Data Layer                         │
         │  - Chromadb (Vector Store)              │
         │  - SQLite (Sessions)                    │
         │  - JSON (Metadata)                      │
         └─────────────────────────────────────────┘
```

**Recommended Format:** Architecture diagram with color-coded layers  
**Tools:** Draw.io, Miro, or ASCII art with styling

---

### 1.2 Microservices Architecture
**Position in Paper:** Architecture Details Section (Page 5-6)  
**Description:** Individual services and their responsibilities  
**Components:**
```
┌──────────────────────────────────────────────────────┐
│           MICROSERVICES LAYOUT                       │
└──────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  FRONTEND SERVICE                                   │
│  ├─ Chat Module                                    │
│  ├─ Document Upload Module                         │
│  ├─ Profile Manager                                │
│  └─ CoT Renderer                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  BACKEND SERVICE (Flask)                            │
│  ├─ Chat Service                                    │
│  ├─ Auth Service                                    │
│  ├─ Document Service                                │
│  ├─ Agent Service                                   │
│  └─ RAG Service                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  AI/ML SERVICE                                      │
│  ├─ LLM Interface (Ollama)                          │
│  ├─ Clause Analyzer                                │
│  ├─ NER Module                                      │
│  └─ Risk Scorer                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  DATA SERVICE                                       │
│  ├─ Vector Store (Chromadb)                        │
│  ├─ Session Manager                                │
│  ├─ Chat History Store                             │
│  └─ Knowledge Base                                  │
└─────────────────────────────────────────────────────┘
```

**Recommended Format:** Service boxes with internal modules  
**Tools:** Draw.io boxes and connectors

---

## 2. Process Flow Diagrams

### 2.1 Chat Processing Pipeline
**Position in Paper:** Methodology Section (Page 7-8)  
**Description:** Step-by-step flow of how a user query is processed  
**Flow:**
```
START: User Query
  │
  ├─► Input Validation
  │   ├─ Check for empty input
  │   ├─ Sanitize special characters
  │   └─ Log incoming query
  │
  ├─► Query Enhancement
  │   ├─ Expand abbreviations
  │   ├─ Extract entities
  │   └─ Identify query type (Q&A, doc analysis, etc.)
  │
  ├─► Context Retrieval (RAG)
  │   ├─ Semantic search on knowledge base
  │   ├─ Retrieve top-K documents
  │   ├─ Rank by relevance
  │   └─ Assemble context window
  │
  ├─► Agentic Reasoning
  │   ├─ Plan next steps
  │   ├─ Determine if tool calling needed
  │   ├─ Call tools (if needed)
  │   │   ├─ Document Analysis
  │   │   ├─ Clause Detection
  │   │   └─ Scheme Matching
  │   └─ Evaluate interim results
  │
  ├─► LLM Generation
  │   ├─ Format prompt with context
  │   ├─ Send to Llama 3 (via Ollama)
  │   ├─ Stream response chunks
  │   └─ Track tokens used
  │
  ├─► Post-Processing
  │   ├─ Parse response structure
  │   ├─ Extract CoT reasoning
  │   ├─ Identify sources
  │   └─ Compute confidence score
  │
  ├─► Display & Storage
  │   ├─ Render markdown in UI
  │   ├─ Show CoT tabs
  │   ├─ Display source citations
  │   └─ Save to chat history
  │
  └─► END: Response to User
```

**Recommended Format:** Diamond decision nodes with action boxes  
**Tools:** Draw.io flowchart shapes or Lucidchart

---

### 2.2 Document Generation Pipeline
**Position in Paper:** Document Generation Section (Page 12-13)  
**Description:** How documents are generated from user parameters  
**Flow:**
```
START: User Requests Document
  │
  ├─► Select Template
  │   ├─ Choose document type (Contract, NDA, etc.)
  │   ├─ Load template structure
  │   └─ Validate template availability
  │
  ├─► Collect Parameters
  │   ├─ Party names
  │   ├─ Dates & durations
  │   ├─ Terms & conditions
  │   └─ Special clauses
  │
  ├─► Validate Parameters
  │   ├─ Check required fields
  │   ├─ Verify date formats
  │   ├─ Cross-check legal validity
  │   └─ Flag potential issues
  │
  ├─► AI Enhancement (Optional)
  │   ├─ Auto-expand clauses
  │   ├─ Add protective language
  │   ├─ Suggest missing sections
  │   └─ Ensure legal compliance
  │
  ├─► Generate Document
  │   ├─ Parse template variables
  │   ├─ Substitute parameters
  │   ├─ Apply formatting
  │   └─ Insert page numbers & TOC
  │
  ├─► Format Output
  │   ├─ PDF (via ReportLab)
  │   │   ├─ Apply styling
  │   │   ├─ Embed fonts
  │   │   └─ Create navigation
  │   │
  │   ├─ DOCX (via python-docx)
  │   │   ├─ Preserve formatting
  │   │   ├─ Add bookmarks
  │   │   └─ Enable editing
  │   │
  │   └─ PPTX (via python-pptx)
  │       ├─ Create slides
  │       ├─ Add speaker notes
  │       └─ Format for presentation
  │
  ├─► Quality Check
  │   ├─ Validate document integrity
  │   ├─ Check for formatting errors
  │   ├─ Verify all clauses present
  │   └─ Ensure legal compliance
  │
  ├─► Deliver to User
  │   ├─ Generate download link
  │   ├─ Show file preview
  │   ├─ Log generation event
  │   └─ Store for audit trail
  │
  └─► END: Document Ready
```

**Recommended Format:** Sequential flow with branching for formats  
**Tools:** Draw.io with color-coded format sections

---

### 2.3 Agent Workflow Loop
**Position in Paper:** Agentic AI Section (Page 9-10)  
**Description:** The planning-execution-evaluation loop  
**Flow:**
```
┌─────────────────────────────────────────────┐
│         AGENT WORKFLOW LOOP                 │
└─────────────────────────────────────────────┘

START: Complex Legal Query
  │
  ├──► PLAN PHASE
  │    ├─ Decompose query into subtasks
  │    ├─ Identify required tools:
  │    │  ├─ RAG Search
  │    │  ├─ Clause Analysis
  │    │  ├─ Risk Detection
  │    │  ├─ Scheme Matching
  │    │  └─ Document Generation
  │    ├─ Sequence operations
  │    └─ Set success criteria
  │
  ├──► EXECUTE PHASE
  │    ├─ Execute Plan Step 1
  │    │  └─ Call appropriate tool
  │    │
  │    ├─ Execute Plan Step 2
  │    │  └─ Use results from Step 1
  │    │
  │    ├─ Execute Plan Step N
  │    │  └─ Iterative refinement
  │    │
  │    └─ Collect all outputs
  │
  ├──► EVALUATE PHASE
  │    ├─ Check against success criteria
  │    │  ├─ Is response complete? ──NO──┐
  │    │  ├─ Is answer accurate? ───NO──┐│
  │    │  └─ Is confidence high? ───NO──││
  │    │                                 ││
  │    ├─YES: Continue              ┌────┘│
  │    │                            │     │
  │    ├─ Compile reasoning steps   │     │
  │    ├─ Extract sources           │     │
  │    ├─ Calculate confidence      │     │
  │    └─ Format for display        │     │
  │                                 │     │
  │    ◄─ Refine: Try alternative ──┴─────┘
  │    tool or approach
  │
  └──► END: Return structured response
       with CoT, sources, confidence
```

**Recommended Format:** Loop diagram with decision points  
**Tools:** Draw.io with arrow feedback loops

---

## 3. User Journey Diagrams

### 3.1 User Journey - First Time User (Onboarding)
**Position in Paper:** User Interface Section (Page 14-15)  
**Description:** First-time user experience flow  
**Journey:**
```
┌─────────────────────────────────────────────┐
│     FIRST-TIME USER JOURNEY                 │
└─────────────────────────────────────────────┘

Landing Page
  │
  ├─ Sign Up / Register
  │  ├─ Enter username
  │  ├─ Set password
  │  ├─ Confirm email
  │  └─ Account created ✓
  │
  ├─ First Login
  │  ├─ See "How can I help?" screen
  │  ├─ Notice upload button
  │  ├─ See keyboard shortcuts hint
  │  └─ Browse recent chats (empty)
  │
  ├─ Try Chat Feature
  │  ├─ Type legal query
  │  ├─ See typing indicator
  │  ├─ Receive response with CoT
  │  ├─ Click on sources tab
  │  └─ Understand answer better
  │
  ├─ Try Document Generation
  │  ├─ Click "Generate Docs" button
  │  ├─ Select Contract template
  │  ├─ Fill in parameters
  │  ├─ Click Generate
  │  ├─ Download PDF
  │  └─ Success! ✓
  │
  ├─ Set Up Profile
  │  ├─ Click user avatar
  │  ├─ Upload profile picture
  │  ├─ Add bio information
  │  ├─ Click Save Changes
  │  └─ Profile complete ✓
  │
  ├─ Explore Features
  │  ├─ Try search (Cmd+K)
  │  ├─ Try keyboard shortcuts
  │  ├─ Try message copy button
  │  ├─ Try drag-drop upload
  │  └─ Get comfortable with UI
  │
  └─ Start Using System
     ├─ Regular queries
     ├─ Document generation
     ├─ Chat history review
     └─ Productivity increase ✓
```

**Recommended Format:** Step-by-step user actions with outcomes  
**Tools:** Draw.io or Figma user journey template

---

### 3.2 User Journey - Document Analysis Scenario
**Position in Paper:** Use Cases / Scenarios Section (Page 16-17)  
**Description:** Real-world scenario: User uploads contract for analysis  
**Journey:**
```
User: Freelancer reviewing client contract
  │
  ├─ PROBLEM: Don't understand contract clauses
  │
  ├─ ACTION 1: Upload Contract
  │  ├─ Drag-drop contract PDF into chat
  │  └─ See confirmation with file info
  │
  ├─ ACTION 2: Ask for Analysis
  │  ├─ Type: "Analyze this contract for risks"
  │  ├─ System processes document
  │  ├─ Shows: "⠋ Thinking..."
  │  └─ Returns analysis
  │
  ├─ RESULT 1: Risk Detection
  │  ├─ Display: Risky clauses highlighted
  │  ├─ Explanation: Simplified language
  │  ├─ Warning: "Non-compete clause may be too broad"
  │  └─ Action: "Click sources to see similar cases"
  │
  ├─ ACTION 3: Explore Sources
  │  ├─ Click "Sources" tab in CoT
  │  ├─ See related court cases
  │  ├─ Read precedents
  │  └─ Build confidence in understanding
  │
  ├─ ACTION 4: Generate Safe Version
  │  ├─ Ask: "Generate a safer version"
  │  ├─ System modifies clauses
  │  ├─ Suggests protective language
  │  └─ Offers document download
  │
  ├─ RESULT 2: Document Ready
  │  ├─ Download modified contract (PDF)
  │  ├─ Review changes highlighted
  │  ├─ Export as Word for editing
  │  └─ Ready to negotiate
  │
  └─ OUTCOME: User confident & informed ✓
```

**Recommended Format:** Timeline with decisions and outcomes  
**Tools:** Draw.io or Lucidchart scenario flow

---

## 4. Data Flow Diagrams

### 4.1 Chat Message Data Flow
**Position in Paper:** Data Management Section (Page 11-12)  
**Description:** How data flows through the system for a chat message  
**Flow:**
```
┌──────────────────────────────────────────────────────┐
│     CHAT MESSAGE DATA FLOW (DFD)                     │
└──────────────────────────────────────────────────────┘

User Input
  │ (via browser)
  ▼
┌─────────────────────────────┐
│  Frontend Validation        │
│ - Check length              │
│ - Sanitize input            │
│ - Format for transmission   │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ /api/chat Endpoint (Flask)  │
│ - Authenticate user         │
│ - Extract parameters        │
│ - Log request               │
└──────────┬──────────────────┘
           │
      ┌────┴──────────────────┐
      │                       │
      ▼                       ▼
  ┌─────────────┐     ┌──────────────────┐
  │RAG Pipeline │     │Session Manager   │
  │             │     │                  │
  │1.Search VDB │     │- Load chat hist. │
  │2.Rank docs  │     │- Build context   │
  │3.Assemble   │     │- Store new msg.  │
  │  context    │     │                  │
  └──────┬──────┘     └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
           ┌─────────────────────┐
           │ Prompt Construction │
           │                     │
           │ System Prompt       │
           │ + Context Docs      │
           │ + Chat History      │
           │ + User Query        │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │LLM (Llama 3/Ollama) │
           │                     │
           │ Process & Generate  │
           │ Response Chunks     │
           └──────────┬──────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
      ▼               ▼               ▼
  Response      CoT Steps        Source List
  Tokens        Reasoning        Citations
      │               │               │
      └───────────────┼───────────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │ Post-Processing     │
           │                     │
           │ Parse CoT           │
           │ Extract sources     │
           │ Score confidence    │
           │ Format markdown     │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │ Storage Layer       │
           │                     │
           │ Save to SQLite      │
           │ (chat_history)      │
           │                     │
           │ Update Chromadb     │
           │ (embed response)    │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │ Streaming to UI     │
           │                     │
           │ Send SSE chunks     │
           │ (real-time display) │
           │                     │
           │ Render markdown     │
           │ Show CoT tabs       │
           │ Display sources     │
           └─────────────────────┘
```

**Recommended Format:** DFD with numbered data flows  
**Tools:** Draw.io DFD template or Lucidchart

---

### 4.2 Knowledge Base Search Data Flow
**Position in Paper:** RAG Pipeline Section (Page 10-11)  
**Description:** How semantic search retrieves relevant legal documents  
**Flow:**
```
Query: "What about non-compete clauses?"
  │
  ▼
┌──────────────────────────┐
│ Query Embedding          │
│ (Convert to vector)      │
│ Dimension: 384           │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Chromadb Vector Store    │
│                          │
│ Similarity Search        │
│ cos(query, docs) > 0.7   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Retrieved Candidates     │
│ • Doc A: Score 0.92      │
│ • Doc B: Score 0.88      │
│ • Doc C: Score 0.82      │
│ • Doc D: Score 0.79      │
│ • Doc E: Score 0.72      │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Relevance Ranking        │
│                          │
│ Rank by:                 │
│ 1. Similarity score      │
│ 2. Document recency      │
│ 3. Citation count        │
│ 4. User preferences      │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Top-K Selection          │
│ (k=5)                    │
│                          │
│ Final Ranked List:       │
│ 1. Case A (non-compete)  │
│ 2. Act B (restraint)     │
│ 3. Rule C (enforcement)  │
│ 4. Brief D (analysis)    │
│ 5. Case E (precedent)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Context Assembly         │
│                          │
│ Create prompt segment:   │
│ "Relevant documents:"    │
│ [Combined text window]   │
│ (max tokens: 2000)       │
└──────────┬───────────────┘
           │
           ▼
Ready for LLM Prompt
```

**Recommended Format:** Sequential process with scoring details  
**Tools:** Draw.io or Miro flowchart

---

## 5. Algorithm Flow Diagrams

### 5.1 Clause Risk Detection Algorithm
**Position in Paper:** Risk Detection Algorithm Section (Page 13)  
**Description:** How the system identifies risky contract clauses  
**Algorithm:**
```
┌──────────────────────────────────────┐
│  CLAUSE RISK DETECTION ALGORITHM     │
└──────────────────────────────────────┘

INPUT: Contract Document
  │
  ├─► Tokenization
  │   ├─ Split into sentences
  │   ├─ Identify clause boundaries
  │   ├─ Extract clause headers
  │   └─ Parse clause bodies
  │
  ├─► Named Entity Recognition (NER)
  │   ├─ Extract: Parties, Dates, Amounts
  │   ├─ Identify: Rights, Obligations, Penalties
  │   ├─ Classify: Risk keywords (e.g., "unlimited", "indemnity")
  │   └─ Tag entity types
  │
  ├─► Risk Pattern Matching
  │   For each clause:
  │   ├─ Check against 50+ risk patterns
  │   ├─ Pattern examples:
  │   │  • "non-compete" + "indefinite" = HIGH RISK
  │   │  • "indemnify" + "all losses" = HIGH RISK
  │   │  • "termination" + "no notice" = MEDIUM RISK
  │   │  • "confidentiality" + "5 years" = LOW RISK
  │   └─ Score: 0-100
  │
  ├─► Semantic Similarity Search
  │   ├─ Compare clause to precedents
  │   ├─ Find similar cases in knowledge base
  │   ├─ Check outcome: Favorable? Unfavorable?
  │   └─ Adjust risk score based on precedent
  │
  ├─► Contextual Analysis
  │   ├─ Consider jurisdiction
  │   ├─ Check industry standards
  │   ├─ Compare to peer contracts
  │   └─ Flag deviations
  │
  ├─► Risk Aggregation
  │   ├─ Per-clause risk: Average(pattern_score, precedent_score)
  │   ├─ Contract risk: Weighted average of clause risks
  │   ├─ Critical risks: Count clauses with score > 75
  │   └─ Overall flag: Green/Yellow/Red
  │
  ├─► Explanation Generation
  │   ├─ "Why is this risky?"
  │   ├─ "What's the legal precedent?"
  │   ├─ "How can it be fixed?"
  │   └─ "What's the likely impact?"
  │
  └─► OUTPUT: Risk Report
      ├─ Clause-level risks
      ├─ Contract-level assessment
      ├─ Remedial suggestions
      └─ Source precedents
```

**Recommended Format:** Algorithm flowchart with decision points  
**Tools:** Draw.io or pseudocode visualization

---

### 5.2 Scheme Recommendation Algorithm
**Position in Paper:** Benefit Discovery Section (Page 12)  
**Description:** How the system matches users to applicable benefits/schemes  
**Algorithm:**
```
┌──────────────────────────────────────┐
│  SCHEME RECOMMENDATION ALGORITHM     │
└──────────────────────────────────────┘

INPUT: User Profile + Query Context
  │
  ├─► User Profile Extraction
  │   ├─ Employment status: Freelancer / Employee / Business owner
  │   ├─ Age: 18-30 / 30-60 / 60+
  │   ├─ Location: State / Union territory
  │   ├─ Income level: Low / Medium / High
  │   ├─ Business type (if applicable)
  │   └─ Current issues: Labor / Tax / Property / Family
  │
  ├─► Query Intent Classification
  │   ├─ Query about: Benefits / Rights / Legal Status
  │   ├─ Problem domain: Employment / Finance / Family / Property
  │   ├─ Urgency level: Immediate / Medium / Long-term
  │   └─ Action needed: Information / Document / Action
  │
  ├─► Scheme Database Query
  │   ├─ Access 300+ schemes in knowledge base
  │   ├─ Filter by:
  │   │  • Eligibility criteria (match user profile)
  │   │  • Relevance category (match query intent)
  │   │  • Geographic applicability
  │   │  • Active status
  │   └─ Initial candidates: List of potential schemes
  │
  ├─► Semantic Matching
  │   ├─ Embed user context as vector
  │   ├─ Search scheme descriptions in VDB
  │   ├─ Calculate similarity scores
  │   ├─ Rank schemes by relevance
  │   └─ Threshold: Score > 0.75
  │
  ├─► Eligibility Verification
  │   For each top scheme:
  │   ├─ Check mandatory criteria
  │   │  • Age requirements
  │   │  • Income limits
  │   │  • Employment status
  │   │  • Residential requirements
  │   ├─ Mark: Eligible / Partially Eligible / Ineligible
  │   └─ Note: Missing documents or conditions
  │
  ├─► Benefit Calculation
  │   ├─ Estimate benefits:
  │   │  • Cash amount
  │   │  • Duration
  │   │  • Coverage scope
  │   ├─ Compare schemes:
  │   │  • Best benefit: highest amount
  │   │  • Easiest access: lowest requirements
  │   │  • Fastest approval: shortest timeline
  │   └─ Rank final candidates
  │
  ├─► Confidence Scoring
  │   ├─ Match confidence: 0-100%
  │   ├─ Factors:
  │   │  • Profile match with eligibility criteria
  │   │  • Semantic similarity to query
  │   │  • Recency of scheme data
  │   │  • Verification status
  │   └─ Flag: High/Medium/Low confidence
  │
  ├─► Recommendation Explanation
  │   ├─ "You may be eligible for:"
  │   ├─ Scheme name + brief description
  │   ├─ Why you qualify
  │   ├─ Benefits you'd receive
  │   ├─ How to apply
  │   ├─ Supporting documents needed
  │   ├─ Link to official resources
  │   └─ Source: Government website / Legal precedent
  │
  └─► OUTPUT: Ranked Scheme List
      ├─ Top 3-5 matches
      ├─ Eligibility status for each
      ├─ Expected benefits
      ├─ Application instructions
      └─ Confidence scores
```

**Recommended Format:** Algorithm with decision tree nodes  
**Tools:** Draw.io or Miro

---

## 6. Comparison Charts

### 6.1 Feature Comparison: LexiGPT vs Traditional Legal Services
**Position in Paper:** Introduction / Motivation (Page 2-3)  
**Description:** Show advantages of AI legal assistant  
**Comparison Table:**
```
┌────────────────────┬──────────────────┬──────────────────┐
│ Aspect             │ Traditional      │ LexiGPT          │
├────────────────────┼──────────────────┼──────────────────┤
│ Availability       │ 9-5 Office hrs   │ 24/7 Online      │
│ Cost per Query     │ $200-500         │ $0 (self-hosted) │
│ Response Time      │ 2-7 days         │ <1 second        │
│ Document Draft     │ 1-3 weeks        │ 2 minutes        │
│ Explanation Level  │ Complex jargon   │ Simple language  │
│ Access Barrier     │ High (cost)      │ Low (free)       │
│ Scalability        │ Limited          │ Unlimited        │
│ Multi-language     │ Limited          │ LLM-capable      │
│ Learning Curve     │ Requires lawyer  │ Intuitive UI     │
│ Privacy            │ Depends on firm  │ On-device        │
│ Personalization    │ Limited          │ Full history     │
│ Sources/Precedent  │ Verbal notes     │ Linked & cited   │
├────────────────────┼──────────────────┼──────────────────┤
│ Winner             │ Complex cases    │ Routine queries  │
│                    │ Litigation       │ Document gen     │
│                    │ Court rep.       │ Legal education  │
└────────────────────┴──────────────────┴──────────────────┘

Visualization: Bar chart showing cost, speed, accessibility
Tools: Excel chart or Draw.io table with icons
```

**Recommended Format:** Comparison matrix with icons  
**Tools:** Draw.io or Figma

---

### 6.2 AI Model Comparison Table
**Position in Paper:** Technology Choices Section (Page 8)  
**Description:** Why Llama 3 was chosen  
**Comparison:**
```
┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Model           │ Llama 3  │ Mistral  │ GPT-4    │ Local    │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Model Size      │ 8-70B    │ 7-8B     │ Large    │ Local    │
│ Cost            │ $0*      │ $0*      │ $$$      │ $0*      │
│ Speed           │ Fast     │ V.Fast   │ Depends  │ Fast     │
│ Legal Domain    │ ✓✓✓      │ ✓✓       │ ✓✓✓      │ Training │
│ Privacy         │ ✓✓✓      │ ✓✓✓      │ ✗        │ ✓✓✓      │
│ Custom Training │ ✓        │ ✓        │ Limited  │ ✓✓✓      │
│ Reasoning       │ ✓✓✓      │ ✓✓       │ ✓✓✓      │ Varies   │
│ Token Limit     │ 8K/128K  │ 32K     │ 128K     │ Varies   │
│ Deployment      │ Easy     │ Easy     │ API-only │ Easy     │
│ Support         │ Good     │ Good     │ Excellent│ Community│
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Best For        │ Legal AI │ Small    │ Premium  │ On-device│
│                 │ on device│ models   │ service  │          │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘

*With Ollama (local) - No API costs
```

**Recommended Format:** Comparison table with checkmarks and ratings  
**Tools:** Draw.io or Figma

---

### 6.3 Feature Implementation Timeline
**Position in Paper:** Implementation Section (Page 15)  
**Description:** Gantt chart showing development phases  
**Timeline:**
```
┌─────────────────────────────────────────────────────────┐
│       IMPLEMENTATION TIMELINE (GANTT CHART)              │
└─────────────────────────────────────────────────────────┘

Phase 1: Foundation (Week 1-2)
├─ Backend Setup             ████████
├─ Flask API Structure       ████████
├─ Database Setup            ████████
└─ Frontend Scaffold         ████████

Phase 2: Core Features (Week 3-4)
├─ Chat Endpoint             ████████████
├─ RAG Pipeline              ████████████
├─ Authentication            ████████████
├─ Document Upload           ████████████
└─ Chat UI                   ████████████

Phase 3: AI Integration (Week 5)
├─ Ollama Setup              ████████
├─ Llama 3 Integration       ████████
├─ Agentic Loop              ████████
├─ CoT Rendering             ████████
└─ Agent Logs                ████████

Phase 4: Polish & Features (Week 6)
├─ Document Generation       ████████████
├─ PDF Viewer                ████████████
├─ Profile Editor            ████████████
├─ Message Search            ████████████
├─ Export Features           ████████████
└─ UI Polish (18 features)   ████████████

Testing & Deployment (Week 7)
├─ Unit Testing              ████████
├─ Integration Testing       ████████
├─ User Testing              ████████
└─ Documentation             ████████

Legend:
████████ = Completed
████░░░░ = In Progress
░░░░░░░░ = Not Started
```

**Recommended Format:** Horizontal Gantt chart  
**Tools:** Excel, Project Libre, or Draw.io with timeline

---

## 7. UI/UX Flow Diagrams

### 7.1 Chat Interface Navigation Flow
**Position in Paper:** User Interface Section (Page 14)  
**Description:** How users navigate through the chat interface  
**Flow:**
```
┌───────────────────────────────────────┐
│    CHAT INTERFACE NAVIGATION          │
└───────────────────────────────────────┘

Landing Screen
  │
  ├─► Sign In / Sign Up
  │   └─ → Dashboard
  │
  └─ Dashboard (Main Chat View)
     │
     ├─► Sidebar Menu
     │   ├─ New Consultation
     │   ├─ Search History
     │   ├─ Recent Chats (list)
     │   ├─ Settings ──┐
     │   ├─ Agent Logs │
     │   ├─ DocGen ────┤───► Modals/Views
     │   └─ Profile ───┘
     │
     ├─► Chat Area
     │   ├─ Initial State / Chat History
     │   ├─ Messages with:
     │   │  ├─ Copy button (hover)
     │   │  ├─ Retry button (hover)
     │   │  ├─ Timestamp (hover)
     │   │  ├─ CoT tabs (expandable)
     │   │  └─ Markdown rendering
     │   │
     │   ├─ Input Area
     │   │  ├─ File upload button
     │   │  ├─ Prompt input field
     │   │  ├─ Send button
     │   │  └─ Drag-drop zone
     │   │
     │   └─ Keyboard Shortcuts Help
     │
     ├─► Settings View
     │   ├─ Appearance (theme toggle)
     │   ├─ Streaming toggle
     │   ├─ Chat Export
     │   │  ├─ Export as JSON
     │   │  └─ Export as PDF
     │   ├─ Session Management
     │   │  └─ Logout all devices
     │   └─ Back to Chat
     │
     ├─► Agent Modal
     │   ├─ Agent Logs (terminal view)
     │   ├─ Controls: Start, Stop, Clear
     │   ├─ Filters: All Actions
     │   ├─ Pause Autoscroll checkbox
     │   └─ Close
     │
     ├─► DocGen Modal
     │   ├─ Document Type selector
     │   ├─ Format selector
     │   ├─ Parameters textarea
     │   ├─ Generate button
     │   ├─ Result display
     │   └─ Download link
     │
     ├─► Profile Modal
     │   ├─ Avatar upload
     │   ├─ Display name field
     │   ├─ Bio textarea
     │   ├─ Save button
     │   └─ Close
     │
     ├─► PDF Viewer Modal
     │   ├─ Canvas display
     │   ├─ Navigation: Prev/Next
     │   ├─ Page counter
     │   └─ Close
     │
     └─► Theme Toggle
         ├─ Dark Mode
         └─ Light Mode
```

**Recommended Format:** State diagram or wireflow  
**Tools:** Figma, Draw.io, or Balsamiq Mockups

---

### 7.2 Modal Windows Layout
**Position in Paper:** UI Components Section (Page 15-16)  
**Description:** Visual mockups of all 7 modals  
**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│                    MODAL LAYOUTS                        │
└─────────────────────────────────────────────────────────┘

[1] Auth Modal              [2] Profile Modal
┌──────────────────┐        ┌──────────────────┐
│ ✕ Welcome Back   │        │ ✕ Account        │
│ Sign In / Up     │        │ Settings         │
│ ┌──────────────┐ │        │ ┌──────────────┐ │
│ │ Username...  │ │        │ │ [Avatar]     │ │
│ ├──────────────┤ │        │ ├──────────────┤ │
│ │ Password...  │ │        │ │ Display Name │ │
│ ├──────────────┤ │        │ │              │ │
│ │   [Sign In]  │ │        │ │ Bio...       │ │
│ └──────────────┘ │        │ │              │ │
│ New? Sign Up     │        │ │   [Save]     │ │
└──────────────────┘        └──────────────────┘

[3] Agent Logs             [4] Document Generator
┌──────────────────┐       ┌──────────────────┐
│ ✕ Agent Logs     │       │ ✕ DocGen         │
│ [▶] [⏹] [🗑️]    │       │ Type: [Contract▼]│
│ ┌──────────────┐ │       │ Format:[PDF▼]    │
│ │ system...    │ │       │ ┌──────────────┐ │
│ │ tool_call... │ │       │ │ Parameters...│ │
│ │ result...    │ │       │ │              │ │
│ │ agent_step..│ │       │ │ [Generate]   │ │
│ └──────────────┘ │       │ └──────────────┘ │
└──────────────────┘       └──────────────────┘

[5] PDF Viewer             [6] Message Search
┌──────────────────┐       ┌──────────────────┐
│ ✕ Document       │       │ ✕ Search         │
│ [◄] Page 1/5 [►]│       │ Find in chat:    │
│ ┌──────────────┐ │       │ ┌──────────────┐ │
│ │              │ │       │ │ Search term..│ │
│ │  [PDF page]  │ │       │ │ Highlighted  │ │
│ │              │ │       │ │ results      │ │
│ │              │ │       │ │ • Match 1    │ │
│ └──────────────┘ │       │ │ • Match 2    │ │
└──────────────────┘       │ • Match 3   │ │
                           └──────────────┘
```

**Recommended Format:** Wireframe mockups  
**Tools:** Figma, Balsamiq Mockups, or Adobe XD

---

## Recommended Paper Structure with Flowcharts

### Suggested Placement by Section:

```
PAPER STRUCTURE WITH FLOWCHART PLACEMENT

1. INTRODUCTION (Page 1-2)
   └─ Flowchart 6.1: Feature Comparison Chart

2. MOTIVATION & PROBLEM STATEMENT (Page 2-3)
   └─ Chart: Cost & Time Comparison

3. RELATED WORK (Page 3-4)
   └─ Timeline: Technology Evolution

4. PROPOSED SYSTEM (Page 4-7)
   ├─ 1.1 High-Level Architecture
   ├─ 1.2 Microservices Architecture
   └─ 2.1 Chat Processing Pipeline

5. METHODOLOGY (Page 7-13)
   ├─ 2.2 Document Generation Pipeline
   ├─ 2.3 Agent Workflow Loop
   ├─ 5.1 Clause Risk Detection Algorithm
   ├─ 5.2 Scheme Recommendation Algorithm
   ├─ 4.1 Chat Message Data Flow
   └─ 4.2 Knowledge Base Search Data Flow

6. IMPLEMENTATION (Page 13-16)
   ├─ Feature Implementation Timeline (6.3)
   ├─ Technology Choices Comparison (6.2)
   ├─ 7.1 Chat Interface Navigation
   ├─ 7.2 Modal Windows Layout
   └─ Code snippets/screenshots

7. USER JOURNEY & USE CASES (Page 16-18)
   ├─ 3.1 First-Time User Journey
   └─ 3.2 Document Analysis Scenario

8. RESULTS & EVALUATION (Page 18-20)
   ├─ Performance metrics table
   ├─ Feature completion matrix
   └─ User feedback summary

9. FUTURE WORK (Page 20-21)
   └─ Roadmap with timeline

10. CONCLUSION (Page 21-22)
    └─ Key achievements summary
```

---

## Flowchart Specifications Summary

| # | Name | Type | Position | Complexity |
|---|------|------|----------|------------|
| 1.1 | High-Level Architecture | Architecture | Page 4 | Medium |
| 1.2 | Microservices Layout | Architecture | Page 5 | Medium |
| 2.1 | Chat Processing Pipeline | Process | Page 8 | High |
| 2.2 | Document Generation | Process | Page 12 | High |
| 2.3 | Agent Workflow Loop | Process | Page 10 | High |
| 3.1 | First-Time User Journey | User Journey | Page 16 | Medium |
| 3.2 | Document Analysis Scenario | User Journey | Page 17 | Medium |
| 4.1 | Chat Message Data Flow | DFD | Page 11 | High |
| 4.2 | Knowledge Base Search | Data Flow | Page 11 | Medium |
| 5.1 | Clause Risk Detection | Algorithm | Page 13 | High |
| 5.2 | Scheme Recommendation | Algorithm | Page 12 | High |
| 6.1 | Feature Comparison | Comparison | Page 2 | Low |
| 6.2 | AI Model Comparison | Comparison | Page 8 | Low |
| 6.3 | Implementation Timeline | Gantt Chart | Page 15 | Low |
| 7.1 | Chat UI Navigation | UI Flow | Page 14 | Medium |
| 7.2 | Modal Windows | UI Mockup | Page 15 | Low |

---

## Design Recommendations

### Color Coding by Category:
- **Architecture:** Blue
- **Process Flow:** Green
- **Data Flow:** Orange
- **User Journey:** Purple
- **Algorithm:** Red
- **Comparison:** Gray
- **UI/UX:** Cyan

### Typography:
- **Headers:** 14pt bold
- **Labels:** 11pt regular
- **Notes:** 10pt italic

### Dimensions:
- **Page width:** 6.5 inches (standard)
- **Flowchart max height:** 4.5 inches
- **Min font size:** 9pt (for readability in print)

---

## Tools Recommended for Creation

1. **Draw.io** (Free, web-based)
   - Best for: All flowcharts, DFDs, architecture diagrams
   - Export: SVG, PNG, PDF

2. **Figma** (Free/Paid)
   - Best for: UI/UX flows, mockups, prototypes
   - Export: High-quality PNG/SVG

3. **Lucidchart** (Paid)
   - Best for: Professional diagrams, complex flows
   - Export: Multiple formats

4. **Miro** (Free/Paid)
   - Best for: Collaborative diagramming, mind maps
   - Export: PNG, PDF

5. **GraphViz** (Free, CLI)
   - Best for: Programmatic diagram generation
   - Export: SVG, PNG, PDF

---

## Export Recommendations

### For Research Paper:
- **Format:** SVG or high-res PNG (300 DPI)
- **Size:** Embeddable in LaTeX/Word
- **Style:** Professional, monochrome-friendly
- **Labels:** Clear, readable fonts

### For Presentation:
- **Format:** PNG (72 DPI) or PDF vector
- **Size:** 1920x1080 or 16:9 aspect
- **Style:** Colorful, modern design
- **Animation:** Consider slide transitions

### For Online Sharing:
- **Format:** PNG with alt text
- **Size:** Optimized for web (< 500KB)
- **Style:** Accessible color schemes
- **Captions:** Include descriptive titles

---

## Final Recommendation

**Priority Flowcharts (Start with these):**
1. 1.1 High-Level Architecture
2. 2.1 Chat Processing Pipeline
3. 2.3 Agent Workflow Loop
4. 5.1 Clause Risk Detection
5. 3.1 User Journey
6. 6.1 Feature Comparison

**Create these after completing priority set:**
7. 2.2 Document Generation
8. 5.2 Scheme Recommendation
9. 4.1 Chat Data Flow
10. 7.1 UI Navigation

**Nice-to-have (if time permits):**
11. 1.2 Microservices
12. 4.2 Search Data Flow
13. 7.2 Modal Mockups
14. Timeline Gantt Chart

---

*Document Generated: December 3, 2025*  
*For: LexiGPT Research Paper*  
*Total Flowcharts: 16 core diagrams*  
*Estimated Creation Time: 15-20 hours*
