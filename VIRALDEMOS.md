# 3 Viral Demo Ideas for ontology-platform

**Goal:** Create demos that are technically impressive AND highly shareable on social media

---

## Demo 1: AI Hiring Assistant 🎯

### Concept
An AI recruiter that interviews candidates and provides **confidence-scored assessments** with clear reasoning.

### Why It's Viral
- **Relatable:** Everyone has been interviewed or hired someone
- **Controversial:** "AI deciding who gets hired" sparks debate
- **Educational:** Shows exactly how confidence scoring works
- **Shareable:** Hiring managers will share this with their network

### User Flow

```
1. Upload candidate resume (PDF/text)
2. Agent extracts key info: skills, experience, education
3. Agent asks clarifying questions (simulated)
4. Agent provides assessment:

=== Candidate Assessment: John Doe ===

Overall Recommendation: PROCEED WITH CAUTION
Confidence: 0.68 (ASSUMED)

Strengths:
  ✓ Strong Python skills (confidence: 0.92)
    Evidence: 5 years at tech company, GitHub portfolio
  
  ✓ Leadership experience (confidence: 0.71)
    Evidence: Led team of 4, but limited scope

Concerns:
  ⚠ Limited ML experience (confidence: 0.85)
    Evidence: No ML projects visible, role didn't require it
  
  ⚠ Career gap unexplained (confidence: 0.45)
    Evidence: 8-month gap in 2024, no explanation provided

Knowledge Gaps:
  ? Reference checks pending
  ? Technical interview not completed
  ? Cultural fit unknown

Next Steps:
  → Schedule technical interview
  → Check 2 professional references
  → Ask about career gap

Final Verdict: "Candidate shows promise but has gaps. 
                Proceed to next round with specific focus areas."
```

### Technical Implementation

```python
from ontology import Agent

agent = Agent()

# Load hiring ontology
agent.load_ontology("hiring_domain.yaml")

# Add candidate data
agent.learn({
    "type": "Candidate",
    "id": "john_doe",
    "properties": {
        "name": "John Doe",
        "years_experience": 5,
        "skills": ["Python", "Django", "PostgreSQL"],
        "leadership_roles": 1,
        "ml_experience": False,
        "career_gap_months": 8
    }
})

# Add hiring rules
agent.add_rule({
    "id": "experience_threshold",
    "condition": "years_experience >= 3",
    "conclusion": "Meets minimum experience requirement",
    "confidence": 0.9
})

agent.add_rule({
    "id": "ml_requirement",
    "condition": "ml_experience == False AND role_requires_ml == True",
    "conclusion": "Skill gap identified",
    "confidence": 0.85
})

# Get assessment
result = agent.ask("Should we hire John Doe for Senior ML Engineer role?")
print(result.render_report())
```

### Distribution Strategy

- **LinkedIn:** Post as "How we're using AI to reduce hiring bias"
- **Twitter:** Thread showing before/after (traditional vs ontology-platform)
- **Reddit:** r/recruiting, r/humanresources, r/cscareerquestions
- **Demo Video:** 60-second Loom recording

---

## Demo 2: Medical Second Opinion 💊

### Concept
A symptom checker that **knows its limitations** and explicitly recommends when to see a doctor.

### Why It's Viral
- **High Stakes:** Medical misinformation is a real problem
- **Emotional:** People worry about health constantly
- **Educational:** Shows responsible AI design
- **Newsworthy:** "AI that admits uncertainty" is a great headline

### ⚠️ Critical Disclaimer
Must prominently display: **"NOT MEDICAL ADVICE. Consult a healthcare professional."**

### User Flow

```
User Input:
"I've been having headaches, increased thirst, and frequent urination 
for the past 2 weeks. I'm 45 years old, overweight (BMI 32), and my 
father had diabetes."

Agent Analysis:

=== Symptom Analysis Report ===

Possible Conditions Identified:

1. Type 2 Diabetes
   Confidence: 0.72 (ASSUMED)
   
   Supporting Evidence:
     ✓ Increased thirst (polydipsia) - classic symptom
     ✓ Frequent urination (polyuria) - classic symptom
     ✓ Age 45 + overweight - risk factors present
     ✓ Family history - genetic predisposition
   
   Missing Information:
     ? Blood glucose levels (critical)
     ? HbA1c test results
     ? Duration and severity of symptoms
     ? Other symptoms (fatigue, blurred vision?)

2. Tension Headaches (Secondary)
   Confidence: 0.58 (SPECULATIVE)
   
   Supporting Evidence:
     ✓ Headache symptom reported
     ✓ Stress/dehydration can co-occur with diabetes
   
   Alternative Explanations:
     → Could be dehydration from polyuria
     → Could be unrelated stress

Recommendation: CONSULT HEALTHCARE PROVIDER

Reasoning:
  "Symptoms suggest possible Type 2 Diabetes, but I cannot diagnose.
   Blood tests are required for confirmation. This condition requires
   medical intervention if confirmed. Please see a doctor within 1 week."

Urgency Level: MODERATE (not emergency, but don't delay)

What to Expect at Doctor:
  → Fasting blood glucose test
  → HbA1c test
  → Physical examination
  → Discussion of family history

Emergency Warning Signs:
  ⚠ Seek immediate care if: confusion, difficulty breathing, 
    severe abdominal pain, or loss of consciousness
```

### Technical Implementation

```python
from ontology import Agent

agent = Agent()

# Load medical ontology (simplified for demo)
agent.load_ontology("medical_symptoms.yaml")

# Add patient data
agent.learn({
    "type": "Patient",
    "id": "patient_001",
    "properties": {
        "age": 45,
        "bmi": 32,
        "symptoms": ["headache", "polydipsia", "polyuria"],
        "symptom_duration_days": 14,
        "family_history": ["father_diabetes"],
        "lab_results": None  # Unknown
    }
})

# Add diagnostic rules
agent.add_rule({
    "id": "diabetes_indicators",
    "condition": "polydipsia == True AND polyuria == True AND age > 40",
    "conclusion": "Possible Type 2 Diabetes",
    "confidence": 0.75
})

agent.add_rule({
    "id": "requires_lab_confirmation",
    "condition": "possible_diabetes == True AND lab_results == None",
    "conclusion": "Cannot diagnose without blood tests",
    "confidence": 0.95
})

# Get analysis
result = agent.ask("What could be causing these symptoms?")
print(result.render_medical_report())
```

### Distribution Strategy

- **Twitter:** Thread on "Responsible AI in healthcare"
- **Reddit:** r/medicine, r/healthIT, r/MachineLearning
- **LinkedIn:** Article on "Why medical AI needs metacognition"
- **Press Angle:** "New AI framework prevents dangerous overconfidence"

---

## Demo 3: Investment Risk Analyzer 📈

### Concept
A stock analysis tool that gives **confidence-weighted recommendations** and admits market uncertainty.

### Why It's Viral
- **Money Talks:** Everyone cares about investing
- **Timely:** Market volatility makes this relevant
- **Contrarian:** Most investment bots pretend to know more than they do
- **Debate-Worthy:** Will spark discussions about AI in finance

### User Flow

```
User Query:
"Should I buy $TSLA at $245/share?"

Agent Analysis:

=== Investment Analysis: Tesla Inc. ($TSLA) ===

Current Price: $245.00
Analysis Date: March 26, 2026

Recommendation: HOLD (Do Not Buy at Current Price)
Confidence: 0.54 (SPECULATIVE)

Bullish Factors:
  ✓ Q4 2025 deliveries beat estimates (+18% YoY)
    Confidence: 0.92 (verified from earnings report)
  
  ✓ Energy storage business growing rapidly
    Confidence: 0.88 (verified from segment reporting)
  
  ✓ FSD beta showing improvement
    Confidence: 0.65 (based on user reports, anecdotal)

Bearish Factors:
  ⚠ Valuation remains high (P/E: 68x vs industry 25x)
    Confidence: 0.95 (calculated from financial data)
  
  ⚠ Competition intensifying in EV market
    Confidence: 0.78 (market share data available)
  
  ⚠ CEO Twitter activity creates volatility
    Confidence: 0.45 (subjective, hard to quantify)

Unknown Variables:
  ? Q1 2026 earnings (reporting in 2 weeks)
  ? Federal Reserve rate decision (next month)
  ? China factory production status (no recent data)
  ? Cybertruck profitability (no margin disclosure)

Technical Analysis:
  RSI: 58 (neutral)
  Support: $230
  Resistance: $260
  Trend: Sideways (confidence: 0.62)

Risk Assessment:
  Volatility: HIGH
  Downside Risk: -15% to -25% (if earnings disappoint)
  Upside Potential: +20% to +35% (if earnings beat)

Final Verdict:
  "Too many unknown variables near-term. Earnings report 
   in 2 weeks will provide critical information. Recommend 
   waiting for post-earnings clarity before entering position.
   
   If you must invest now, consider small position (<5% portfolio) 
   with stop-loss at $220."

Alternative Strategy:
  → Wait for Q1 earnings (April 15, 2026)
  → Set price alert at $220 (strong support)
  → Consider options strategy if expecting volatility

Disclaimer: This is not financial advice. Consult a licensed 
financial advisor. Past performance does not guarantee future results.
```

### Technical Implementation

```python
from ontology import Agent

agent = Agent()

# Load financial ontology
agent.load_ontology("investment_analysis.yaml")

# Add stock data
agent.learn({
    "type": "Stock",
    "id": "TSLA",
    "properties": {
        "symbol": "TSLA",
        "current_price": 245.00,
        "pe_ratio": 68,
        "delivery_growth_yoy": 0.18,
        "market_share_trend": "declining",
        "next_earnings_date": "2026-04-15",
        "analyst_ratings": {"buy": 12, "hold": 18, "sell": 8}
    }
})

# Add investment rules
agent.add_rule({
    "id": "high_pe_warning",
    "condition": "pe_ratio > 50 AND industry_avg_pe < 30",
    "conclusion": "Valuation risk identified",
    "confidence": 0.85
})

agent.add_rule({
    "id": "earnings_uncertainty",
    "condition": "days_to_earnings < 30",
    "conclusion": "High uncertainty period - consider waiting",
    "confidence": 0.70
})

# Get analysis
result = agent.ask("Should I buy TSLA at current price?")
print(result.render_investment_report())
```

### Distribution Strategy

- **Twitter:** Daily stock analysis threads during earnings season
- **Reddit:** r/investing, r/stocks, r/wallstreetbets (controversial!)
- **Seeking Alpha:** Cross-post analysis as article
- **YouTube:** "AI analyzes popular stocks" video series

---

## Implementation Priority

**Week 2 Focus:**

1. **Start with Demo 1 (Hiring)** - Safest, broadest appeal
   - Estimated dev time: 2-3 days
   - Impact: High engagement, low controversy

2. **Then Demo 3 (Investment)** - High viral potential
   - Estimated dev time: 2 days
   - Impact: Very shareable, timely

3. **Finally Demo 2 (Medical)** - Highest impact, highest risk
   - Estimated dev time: 3-4 days
   - Impact: Newsworthy, but requires careful disclaimers
   - Legal review recommended before publishing

---

## Success Metrics for Each Demo

| Metric | Target |
|--------|--------|
| GitHub stars gained per demo | +100 |
| Twitter impressions per demo thread | 50,000+ |
| Demo Colab notebook opens | 1,000+ |
| Media mentions (if any) | 3+ |

---

## Next Steps

1. **Choose first demo** (recommend: Hiring Assistant)
2. **Create detailed spec** (data models, rules, UI mockup)
3. **Build MVP** (2-3 days)
4. **Record demo video** (Loom, 60 seconds)
5. **Launch on Twitter + Reddit**
6. **Measure and iterate**

Let's build something people actually want to share. 🚀
