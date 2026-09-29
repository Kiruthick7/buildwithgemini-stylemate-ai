# StyleMate AI — Live Hackathon / Demo Presentation Script

**Track 3: Agent-First Architecture Demo**  
**Web Application URL:** `http://localhost:8000/stylemate`  
**Agent Engine:** Google ADK / Agents CLI  

---

## 🎬 14-Step Presentation Story

| Step | Action / User Message | Visible AI Reasoning / Tool Actions | Expected Output & Key Talking Points |
| :---: |---|---|---|
| **Step 1** | User clicks **"1. Profile"** or uploads portrait. | `Analyzing portrait photo with Gemini Vision`<br>`Extracting non-sensitive facial balance and undertone`<br>`✓ Style profile created` | Demonstrates multimodal analysis that extracts styling attributes without inferring sensitive biometric traits. Left panel updates with neutral-warm palette. |
| **Step 2** | StyleMate creates Personal Style Profile. | `✓ Style profile loaded` | Profile populated with oval face structure, neutral-warm undertone, flattering earth tones & neutrals, and avoidance rules. |
| **Step 3** | User clicks **"3. Wardrobe"** or uploads garment photo. | `Classifying garments with Gemini Multimodal Vision`<br>`Cataloging colors, fabrics, and formality tiers` | Gemini Vision classifies clothing (category, color, formality, fabric). |
| **Step 4** | StyleMate builds Virtual Wardrobe. | `✓ Wardrobe populated` | Right panel shows owned closet items with clear `[OWNED IN CLOSET]` blue badges. |
| **Step 5** | User asks: *"I have a dinner date tonight. What should I wear?"* | `Analyzing your style`<br>`✓ Style profile loaded`<br>`✓ Wardrobe loaded`<br>`✓ Finding compatible colors`<br>`✓ Creating outfit` | Demonstrates agent-first reasoning: rather than listing items, the agent calls `get_wardrobe` and `get_style_profile` to coordinate an outfit. |
| **Step 6** | Agent retrieves profile & wardrobe. | Tool status visible in pulsing AI Reasoning banner. | Transparent tool invocation without exposing private chain-of-thought tokens. |
| **Step 7** | Agent generates outfit options. | `generate_outfit` tool result rendered. | Recommends coordinated outfit (navy oxford shirt + beige chinos + white sneakers) with concise fashion rationale. |
| **Step 8** | User says: *"I don't like the pants. Change them."* | `Retaining active shirt and shoes context`<br>`Querying wardrobe for alternative bottomwear`<br>`Replacing only pants while preserving rest` | Highlights multi-turn memory: agent preserves shirt, jacket, and shoes from Step 7 and swaps only the bottomwear. |
| **Step 9** | Agent modifies only the pants. | `generate_outfit(modify_category="bottomwear")` | Bottomwear changes to charcoal jeans, preserving the original topwear. |
| **Step 10** | User asks: *"I don't own a good shirt for this. Find me one under ₹1500."* | `Checking user skin undertone compatibility`<br>`Calling search_products tool abstraction`<br>`Filtering verified retail catalog under ₹1500`<br>`Ranking by style relevance` | Initiates the shopping assistant capability. |
| **Step 11** | Agent uses shopping tool. | `search_products(query="black shirt", max_price=1500)` | Strictly enforces budget ceiling: returns verified retail finds (e.g. CottonCraft Black Oxford at ₹1,299). Right panel displays green `[VERIFIED RETAIL FIND]` cards. |
| **Step 12** | User saves the outfit. | User clicks **"💾 Save Outfit"**. | Stores outfit into saved collections. Saved count increments and appears in the ⭐ Saved tab. |
| **Step 13** | User selects **"🎨 Visualize on Me"**. | User clicks button on outfit recommendation card. | Opens the lookbook visualization preview modal. |
| **Step 14** | Show generated visualization. | Lookbook modal displays conceptual preview image. | Clearly displays: `AI-Generated Approximate Concept Visualization` + responsible AI disclaimer ensuring no unsupported fit/sizing claims. |

---

## 🚀 Quick Execution for Demo

To present the demo live:
1. Open Chrome to `http://localhost:8000/stylemate`.
2. Use the **DEMO STEPS** pill buttons in the top navigation bar to advance through the story step-by-step with synchronized AI tool reasoning indicators.
