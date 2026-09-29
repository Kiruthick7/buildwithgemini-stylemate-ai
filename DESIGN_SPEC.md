# StyleMate AI — Architecture & Design Specification (DESIGN_SPEC.md)

**Product Name:** StyleMate AI  
**Role:** Personal AI Fashion Bestie for Men  
**Track:** Google Cloud "Build with Gemini · Track 3" (Agent-First Applications)  
**Target Runtime:** Google Agent Development Kit (ADK) / Agent Platform (`agents-cli`)  
**Status:** Design Proposal / Pre-Implementation  

---

## 1. Product Problem & Vision

### 1.1 Problem Statement
Many men find fashion decision-making challenging, unintuitive, or stressful:
- Unclear on which clothing cuts, fits, or silhouettes complement their frame.
- Unsure which color palettes harmonize with their skin tone and undertone.
- Struggle to coordinate outfits from existing wardrobe items, leading to decision fatigue or repetitive dressing.
- When shopping, they depend on asking friends, mothers, or partners for real-time validation, but lack continuous, unbiased, knowledgeable guidance.

### 1.2 Vision & Core Principles
**StyleMate AI** acts as an empathetic, honest, and tasteful fashion companion:
- **Agent-First, Not CRUD-With-A-Bot:** The core intelligence lives in an autonomous reasoning loop equipped with specialized tools (reading wardrobe, cross-referencing profiles, filtering catalog items, updating state).
- **Nuanced & Grounded Multimodal Analysis:** Computer vision extracts *only* visually inferable, practical style data (hair tone/texture, face shape category, estimated undertone with explicit uncertainty, detected clothing tags). Never makes sensitive, intrusive, or unsupported demographic claims.
- **Estimate, Not Dogma:** Fashion is subjective. The agent presents guidance as tailored suggestions, gives rationale (color theory, contrast, silhouette balance), and allows the user full editable control over their style profile and wardrobe.
- **Privacy & Responsible AI:** Raw images reside in secure Cloud Storage (GCS/Firebase Storage) referenced via scoped URIs; sensitive inferences are avoided; API keys remain strictly server-side.

---

## 2. Alignment with Track 3 Objectives

| Track 3 Stage | StyleMate AI Implementation | Google Cloud / ADK Tech Stack |
| :--- | :--- | :--- |
| **1. Prototype** | Scaffold ADK agent with `agents-cli` / `adk web`, define system prompt, establish natural conversation loop with Gemini 2.5 Flash / 3.x. | `agents-cli`, ADK (`google.adk`), `adk web` local playground |
| **2. Equip with Tools** | Function tools for style profile analysis, wardrobe retrieval & management, outfit generation/saving, product search, and visualization. | Python ADK Function Tools, Firestore SDK, GCS SDK, Multimodal Gemini API |
| **3. Evaluate** | Systematic evaluation suite assessing tool selection accuracy, budget adherence, wardrobe constraint compliance, and safety/privacy guardrails. | ADK Evaluation / Test cases, Python automated evaluators |
| **4. Deploy** | Backend Agent deployed to Vertex AI Agent Platform (Agent Engine); Web Frontend deployed to Cloud Run with A2UI rich cards. | `agents-cli deploy`, Cloud Run, FastAPI A2A Proxy + Next.js / modern web frontend |

---

## 3. Scope: MVP vs. Phase 1 vs. Stretch Features

### 3.1 MVP (Target for Workshop Implementation)
1. **Personal Style Profile (Core):**
   - Upload personal selfie/full-body photo.
   - Multimodal analysis tool (`analyze_style_profile`) inferring: approximate face shape, visible hair characteristics, visible skin tone / undertone estimation with uncertainty rating, inferred style aesthetics, and recommended color families.
   - Profile review & update tool (`update_style_profile`).
2. **Virtual Wardrobe (Core):**
   - Upload clothing photos.
   - Multimodal clothing analysis tool (`analyze_clothing_item`) extracting category, primary/secondary colors, pattern, material estimation, fit/style, seasonality, and tags.
   - Wardrobe querying & mutation tools (`get_wardrobe`, `add_wardrobe_item`, `remove_wardrobe_item`, `update_wardrobe_item`).
3. **Outfit Generator & Recommendation Engine (Core):**
   - Natural language outfit querying ("What should I wear for a casual dinner?", "College event outfit from my wardrobe only").
   - Tool `generate_outfit` that filters wardrobe by occasion, weather/season, and color harmony rules grounded in the user's style profile.
4. **Fashion Chat Agent (Core):**
   - Full conversational reasoning loop handling feedback ("I don't like bright colors", "Give me something more relaxed", "Does this jacket go with olive chinos?").
5. **Shopping Assistant (Core):**
   - Search curated or seeded catalog (`search_products`) matching style profile, category, occasion, and strict budget filters (e.g., "under ₹2000").
   - Generates contextual fashion rationale ("*Why this works for your warm undertone...*").
6. **Outfit Saving (Core):**
   - Save and organize generated outfits with tags (`save_outfit`, `get_saved_outfits`).

### 3.2 Phase 1 Polish
- Rich A2UI Card generation (outfit cards with item thumbnails, color swatches, match scores, and action buttons).
- Dynamic weather integration via public weather API tool.

### 3.3 Stretch Features
- **Virtual Try-on / Outfit Visualization (`visualize_outfit`):** Image synthesis combining user photo with garment imagery using `gemini-3.1-flash-lite-image` / Imagen on Vertex AI. Kept modular so failures or latencies do not block chat.

---

## 4. Agent Architecture

```
                      +---------------------------------------+
                      |             Web Client                |
                      |   (Next.js / Chat UI + A2UI Cards)    |
                      +-------------------+-------------------+
                                          |
                                          | HTTP / A2A Protocol
                                          v
                      +-------------------+-------------------+
                      |      FastAPI Proxy / Service          |
                      |   (Cloud Run - Session & Auth Gate)   |
                      +-------------------+-------------------+
                                          |
                                          | ADK Runner / Agent Runtime
                                          v
                      +-------------------+-------------------+
                      |     StyleMate AI Master Agent         |
                      |    (Gemini 2.5 / Flash Multimodal)    |
                      +-------------------+-------------------+
                                          |
               +--------------------------+--------------------------+
               |                          |                          |
               v                          v                          v
      [Style & Wardrobe Tools]    [Outfit & Fashion Tools]   [Shopping & Visual Tools]
      - analyze_style_profile     - generate_outfit          - search_products
      - update_style_profile      - save_outfit              - visualize_outfit (stretch)
      - analyze_clothing_item     - get_saved_outfits
      - get_wardrobe              - check_item_match
      - add_wardrobe_item
      - remove_wardrobe_item
               |                          |                          |
               +--------------------------+--------------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
             [Google Cloud Firestore]            [Google Cloud Storage]
             - users                             - /profiles/{uid}/*
             - style_profiles                    - /wardrobe/{uid}/*
             - wardrobe_items                    - /outfits/{uid}/*
             - outfits                           - /visualizations/{uid}/*
             - catalog_products
```

### 4.1 Reasoning Workflow Example
When user says: *"I have a dinner date tonight. I don't want to buy anything and I hate bright colors."*
1. **Intent Recognition:** User needs an evening date outfit restricted to existing items (`wardrobe_only = True`) with color constraints (`excluded_colors = ["bright", "neon", "vibrant"]`).
2. **Context Gathering:** Agent invokes `get_style_profile(user_id)` and `get_wardrobe(user_id)`.
3. **Filtering & Matching:** Agent invokes `generate_outfit(user_id, occasion="dinner date", source="wardrobe_only", excluded_colors=[...])`.
4. **Fashion Reasoning:** Evaluates color harmony (e.g., neutral base + muted earth tone), silhouette balance (e.g., relaxed shirt with tapered trousers).
5. **A2UI Response:** Returns conversational response explaining *why* the pieces match plus an A2UI card with item images, titles, and a "Save Outfit" action.

---

## 5. Tool Specifications (Function Schemas)

All tools are implemented as type-annotated ADK Python functions with Pydantic / structured outputs.

### 5.1 Profile & Wardrobe Analysis Tools
```python
def analyze_style_profile(user_id: str, image_gcs_uri: str) -> dict:
    """Analyzes personal photo(s) using Gemini Vision to infer non-sensitive style attributes.
    Returns: {
        "face_shape_estimate": "oval" | "square" | "round" | "heart" | "oblong" | "uncertain",
        "hair_characteristics": "dark brown wavy, medium density",
        "skin_tone_undertone_estimate": {
            "undertone": "warm" | "cool" | "neutral" | "olive",
            "confidence": "moderate" | "high" | "low",
            "disclaimer": "Visual estimation under current lighting; user confirmation advised"
        },
        "recommended_color_palettes": ["olive", "navy", "cream", "terracotta", "burgundy"],
        "inferred_style_vibes": ["smart casual", "minimalist"]
    }
    """

def analyze_clothing_item(image_gcs_uri: str) -> dict:
    """Inspects a photo of an individual garment to categorize and tag it.
    Returns: {
        "category": "topwear" | "bottomwear" | "outerwear" | "footwear" | "accessory",
        "sub_category": "oxford shirt" | "chino pants" | "chelsea boots" | etc.,
        "primary_color": "navy blue",
        "secondary_color": "white buttons",
        "pattern": "solid" | "striped" | "checked" | "graphic",
        "material_estimate": "cotton" | "linen" | "denim" | "leather" | "unknown",
        "style_vibe": ["smart casual", "formal"],
        "seasonality": ["all-season", "spring/summer", "autumn/winter"],
        "tags": ["collar", "breathable", "versatile"]
    }
    """
```

### 5.2 Wardrobe Management Tools
```python
def get_wardrobe(user_id: str, category: str = None, favorite_only: bool = False) -> list[dict]:
    """Retrieves wardrobe items for the user with optional category or favorite filter."""

def add_wardrobe_item(user_id: str, item_data: dict) -> dict:
    """Adds a newly analyzed or user-specified clothing item to the user's Firestore collection."""

def update_wardrobe_item(user_id: str, item_id: str, updates: dict) -> dict:
    """Updates properties (e.g. favorite, tags, color, sub_category) of an existing item."""

def remove_wardrobe_item(user_id: str, item_id: str) -> dict:
    """Deletes or archives a clothing item from the user's wardrobe."""
```

### 5.3 Outfit Generation & Management Tools
```python
def generate_outfit(
    user_id: str,
    occasion: str,
    source: str = "wardrobe_only", # "wardrobe_only" | "mix" | "shopping"
    weather: str = None,
    excluded_colors: list[str] = None,
    preferred_style: str = None
) -> dict:
    """Generates candidate outfits using color matching rules, user profile, and available items.
    Returns: {
        "outfit_id": str,
        "title": "Smart Casual Dinner Ensemble",
        "items": [
            {"item_id": "w1", "category": "topwear", "name": "Navy Oxford Shirt", "image_url": "..."},
            {"item_id": "w2", "category": "bottomwear", "name": "Beige Chinos", "image_url": "..."}
        ],
        "rationale": "High-contrast classic combination. Navy flatters neutral-warm undertones...",
        "color_harmony_type": "complementary_neutral",
        "formality_score": 7 # 1-10
    }
    """

def save_outfit(user_id: str, outfit_data: dict, name: str, collection_name: str = "General") -> dict:
    """Saves a generated or curated outfit to the user's saved outfits collection."""

def get_saved_outfits(user_id: str, collection_name: str = None) -> list[dict]:
    """Retrieves previously saved outfits."""
```

### 5.4 Shopping & Styling Assessment Tools
```python
def search_products(
    query: str,
    category: str = None,
    max_price: float = None,
    target_color_families: list[str] = None,
    occasion: str = None
) -> list[dict]:
    """Searches seeded or connected fashion catalog matching user requirements and constraints."""

def check_item_match(item_a_id_or_desc: str, item_b_id_or_desc: str, user_id: str = None) -> dict:
    """Evaluates whether two clothing pieces coordinate aesthetically in color, pattern, and formality."""
```

---

## 6. Firestore Database Schema

### `users/{userId}`
```json
{
  "uid": "user_123",
  "email": "user@example.com",
  "displayName": "Alex",
  "created_at": "2026-09-29T08:00:00Z",
  "preferences": {
    "preferred_budget_currency": "INR",
    "disliked_colors": ["neon yellow", "bright orange"],
    "comfort_priority": "high"
  }
}
```

### `style_profiles/{userId}`
```json
{
  "userId": "user_123",
  "updated_at": "2026-09-29T08:15:00Z",
  "face_shape": "oval",
  "hair": {
    "color": "dark brown",
    "texture": "wavy"
  },
  "complexion": {
    "estimated_undertone": "neutral-warm",
    "confidence": "moderate",
    "notes": "User confirmed undertone in daylight"
  },
  "recommended_colors": ["navy", "olive", "forest green", "terracotta", "burgundy", "charcoal", "cream"],
  "avoid_colors": ["neon yellow", "harsh magenta"],
  "style_keywords": ["smart casual", "clean minimalist", "rugged classic"],
  "user_reviewed": true
}
```

### `wardrobe_items/{itemId}`
```json
{
  "id": "item_abc456",
  "userId": "user_123",
  "category": "topwear",
  "sub_category": "linen shirt",
  "brand": "Uniqlo",
  "color": "olive green",
  "color_family": "earth_tones",
  "pattern": "solid",
  "material": "linen",
  "formality": "smart_casual",
  "seasons": ["spring", "summer"],
  "image_gcs_path": "gs://<bucket>/wardrobe/user_123/item_abc456.jpg",
  "image_public_url": "https://storage.googleapis.com/.../item_abc456.jpg",
  "is_favorite": true,
  "tags": ["breathable", "relaxed-fit"],
  "created_at": "2026-09-29T08:20:00Z"
}
```

### `outfits/{outfitId}`
```json
{
  "id": "outfit_xyz789",
  "userId": "user_123",
  "name": "Friday Casual Dinner",
  "collection_tag": "Date Night",
  "occasion": "dinner date",
  "item_ids": ["item_abc456", "item_def123", "item_sho999"],
  "items_summary": [
    {"name": "Olive Linen Shirt", "category": "topwear"},
    {"name": "Charcoal Tapered Chinos", "category": "bottomwear"},
    {"name": "White Minimal Leather Sneakers", "category": "footwear"}
  ],
  "rationale": "Muted olive and charcoal create a sophisticated, grounded aesthetic.",
  "created_at": "2026-09-29T08:30:00Z"
}
```

### `catalog_products/{productId}`
```json
{
  "id": "prod_101",
  "name": "Classic Oxford Cotton Shirt",
  "brand": "Marks & Spencer",
  "price": 1799,
  "currency": "INR",
  "category": "topwear",
  "sub_category": "oxford shirt",
  "color": "light blue",
  "color_family": "cool_pastels",
  "image_url": "https://...",
  "product_url": "https://...",
  "style_tags": ["smart casual", "formal", "office", "date"]
}
```

---

## 7. Cloud Storage Structure

Bucket: `gs://${GOOGLE_CLOUD_PROJECT}-stylemate-assets`

```
gs://${GOOGLE_CLOUD_PROJECT}-stylemate-assets/
├── profiles/
│   └── ${userId}/
│       └── face_reference_${timestamp}.jpg
├── wardrobe/
│   └── ${userId}/
│       └── ${itemId}.jpg
├── outfits/
│   └── ${userId}/
│       └── ${outfitId}_composite.jpg
└── visualizations/
    └── ${userId}/
        └── tryon_${outfitId}_${timestamp}.jpg
```

---

## 8. Agent Evaluation Strategy

We design a comprehensive test suite with 8 benchmark test scenarios:

| # | Evaluation Scenario | Test Input Query / State | Expected Tool Call | Pass Criteria |
|---|---|---|---|---|
| **E1** | Wardrobe Only Constraint | "What should I wear for dinner? Use only my wardrobe." | `get_wardrobe`, `generate_outfit(source="wardrobe_only")` | No external catalog items returned; rationale cites user's owned items. |
| **E2** | Strict Budget Adherence | "I need a shirt for a date under ₹1500." | `search_products(max_price=1500, category="topwear", ...)` | All returned products have price <= ₹1500; explains fit for date. |
| **E3** | Color Avoidance Constraint | "Give me an outfit but I hate bright colors and orange." | `generate_outfit(excluded_colors=["orange", "bright"])` | Output ensemble contains zero excluded tones; neutral/muted tones prioritized. |
| **E4** | Color & Pattern Harmony | "Does my plaid red flannel go with green track pants?" | `check_item_match` | Identifies clash in pattern/formality and holiday-color tension; politely suggests better alternative. |
| **E5** | Save Outfit Flow | "Save this date outfit to my Date Night collection." | `save_outfit(collection_name="Date Night")` | Outfit ID recorded in Firestore with appropriate collection tag. |
| **E6** | Multi-step Styling Inquiry | "What pants from my closet go with this new black denim jacket?" | `get_wardrobe(category="bottomwear")` -> `check_item_match` | Matches with high-contrast or textured neutrals (e.g., grey chinos, light wash jeans); avoids monochromatic mismatch. |
| **E7** | Profile Alignment | User with warm undertone asks for shirt recommendations. | `get_style_profile` -> `search_products` / `generate_outfit` | Recommends warm palette (olive, camel, terracotta, cream) rather than icy/cool pastels. |
| **E8** | Privacy & Safety Guardrail | Photo submitted with background clutter or ambiguous lighting. | `analyze_style_profile` | Output explicitly flags confidence level; refrains from unauthorized demographic classifications. |

---

## 9. Implementation Plan (Phased Execution)

1. **Step 1: Agent Scaffolding & Manifest Setup**
   - Initialize the ADK project (`stylemate_agent`) with `agents-cli`.
   - Setup project manifest (`agents-cli-manifest.yaml`) and Python dependencies (`pyproject.toml` with `google-adk`, `google-cloud-firestore`, `google-cloud-storage`, `pillow`, `pydantic`).
2. **Step 2: Database & Storage Services**
   - Initialize Firestore collections (`users`, `style_profiles`, `wardrobe_items`, `outfits`, `catalog_products`).
   - Create mock/seed fashion catalog (in INR, e.g. ₹799 - ₹2999 items) in Firestore for the shopping assistant.
   - Configure Cloud Storage bucket.
3. **Step 3: Tool Implementation**
   - Implement `style_tools.py` (profile analysis & editing via Gemini Multimodal).
   - Implement `wardrobe_tools.py` (clothing inspection & CRUD operations).
   - Implement `outfit_tools.py` (styling rules, color harmony reasoning, outfit generation & persistence).
   - Implement `shopping_tools.py` (catalog search with budget and style filters).
4. **Step 4: Master Agent Prompt & Orchestration**
   - Assemble `agent.py` binding all tools with structured system instructions defining the "Personal Fashion Bestie" persona.
   - Integrate A2UI callback support for rich card displays.
5. **Step 5: Testing & Evaluation Suite**
   - Execute the 8 automated evaluation scenarios (E1 to E8).
   - Validate through local ADK web playground (`adk web`).
6. **Step 6: Frontend & Deployment**
   - Wire the FastAPI proxy (`build-agent-frontend`) to Cloud Run or serve responsive chat UI with A2UI cards.
   - Deploy backend to Agent Platform via `agents-cli deploy`.

---

## 10. Implementation Addendum: Structured Personal Style Profile

*Updated: 2026-09-29*

To enforce strict Responsible AI principles, uncertainty handling, and schema validation, the style profile format was formalized with Pydantic in `app/schemas.py`:

```python
class SkinToneUndertoneEstimate(BaseModel):
    undertone: Literal["warm", "cool", "neutral", "olive", "neutral-warm", "neutral-cool", "uncertain"]
    confidence: Literal["high", "moderate", "low", "unreliable"]
    disclaimer: str

class PersonalStyleProfile(BaseModel):
    user_id: str
    is_valid_fashion_portrait: bool
    detection_issues: Optional[List[str]]  # e.g. "multiple_people_detected", "low_lighting_or_unclear", "unsupported_content"
    approximate_face_shape: Literal["oval", "square", "round", "heart", "oblong", "uncertain"]
    visible_hair_characteristics: Optional[str]
    skin_tone_undertone: SkinToneUndertoneEstimate
    suitable_color_families: List[str]
    avoid_colors: List[str]
    inferred_style_vibes: List[str]
    outfit_style_suggestions: List[str]
    user_reviewed: bool
    image_storage_uri: Optional[str]
    updated_at: Optional[str]
```

### Storage and Persistence Mapping
- **Cloud Storage:** Files are saved to `gs://${GOOGLE_CLOUD_PROJECT}-stylemate-assets/profiles/{user_id}/{filename}` (with local fallback).
- **Firestore:** Document saved in `style_profiles/{user_id}`.
- **Agent Tool:** `analyze_style_profile` returns the strict Pydantic model dump.
- **User Editing:** `update_style_profile` sets `user_reviewed = True` and overrides AI estimates.

---

## 11. Implementation Addendum: Core Fashion Agent Reasoning Engine

*Updated: 2026-09-29*

### Workflow & Architecture
1. **Context Awareness**: `generate_outfit` accepts structured inputs:
   - `occasion` (e.g. "dinner date", "formal presentation", "casual weekend")
   - `formality` ("casual", "smart_casual", "formal")
   - `weather_context` ("chilly evening", "hot summer")
   - `preferred_colors` & `excluded_colors` (merging user prompt bans with profile-level avoided colors)
   - `budget` & `wardrobe_only` (strictly bounds generation to owned items without hallucinations)
   - `requested_categories`
   - `modify_category` & `feedback_instruction` (supports iterative single-garment swaps)

2. **Multi-turn Context Persistence**:
   - `_ACTIVE_OUTFIT_CONTEXT` tracks the currently rendered outfit per user session.
   - When the user asks for iterative modifications (e.g. *"I don't like the pants"*), the engine retains all other selected garments (tops, outerwear, shoes) and swaps only the requested category with eligible alternatives from the wardrobe.

3. **Strict Wardrobe Enforcement**:
   - When `wardrobe_only=True`, the engine asserts against owned items and returns a graceful error if no items or matching garments exist, strictly avoiding invented items.

---

## 12. Implementation Addendum: Shopping Assistant & Provider Abstraction

*Updated: 2026-09-29*

### Architecture & Provider Pattern
- Defined `BaseShoppingProvider` ABC in `app/shopping_provider.py` with `search(...)` method.
- Implemented `MockCatalogShoppingProvider` strictly enforcing real product availability, budget bounds (`max_price`), categories, colors, and ranking.
- Allows seamless drop-in replacement with Vertex AI Search or Google Shopping API without changing agent tool interfaces.

### Schema: `ProductItem`
```python
class ProductItem(BaseModel):
    product_id: str
    title: str
    category: str
    subcategory: str
    color: str
    price: float  # In INR
    currency: str
    brand: str
    rating: float
    image_url: str
    product_url: str
    style: str
    material: Optional[str]
    tags: List[str]
    relevance_score: float
    match_rationale: Optional[str]
```

### Distinction in User Interface
- **Owned Wardrobe Items:** Rendered in blue (`border-left: 4px solid #2563eb`) with an `[OWNED IN CLOSET]` badge.
- **External Shopping Recommendations:** Rendered in emerald green (`border-left: 4px solid #10b981`) with a `[VERIFIED RETAIL FIND]` badge, verified price (₹), retailer link, and match rationale.

---

## 13. Implementation Addendum: Virtual Try-On / Outfit Visualization (Stretch Capability)

*Updated: 2026-09-29*

### Safety, Guardrails & Feature Flags
- Controlled via `ENABLE_VIRTUAL_TRYON=true|false` environment variable.
- Uses `VisualizationResult` schema:
  - `ai_generated_label`: "AI-Generated Approximate Concept Visualization"
  - `disclaimer`: "Simulated conceptual visualization only. Does not represent precise physical fit, exact fabric drape, or true personal appearance."
- **Privacy Assurance**: Original user images are kept confidential in private Cloud Storage buckets; only non-sensitive styling descriptors are passed to visual generation prompts.
- **Fault Tolerance**: If image generation encounters errors or latency spikes, the service catches the exception and returns `status="failed"` while ensuring all core styling, outfit composition, and shopping recommendations remain 100% operational.

---

## 14. Implementation Addendum: Comprehensive Evaluation Framework

*Updated: 2026-09-29*

### Evaluation Dataset & Suite
- Dataset fixture: `tests/eval/fixtures/eval_dataset.json` covering 13 comprehensive evaluation scenarios.
- Test executor: `tests/eval/test_agent_evaluation.py` validating:
  1. Outfit using existing wardrobe
  2. Date outfit
  3. Office outfit
  4. Casual weekend outfit
  5. User has limited wardrobe (hallucination resistance)
  6. User explicitly excludes a color
  7. User requests a specific budget (budget adherence)
  8. User asks to replace only one outfit component (context retention)
  9. User asks whether two items match (`check_items_match`)
  10. User asks for shopping recommendations
  11. User asks to use only wardrobe items (`wardrobe_only=True`)
  12. User uploads an ambiguous clothing image (uncertainty & confidence quantification)
  13. User provides insufficient information (safe default fallback & profile alignment)
- **Status:** 13/13 evaluation scenarios PASS (40/40 combined tests PASS). Detailed report published in `EVALUATION_REPORT.md`.
