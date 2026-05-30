# ✈ Agentic AI Travel Planning Assistant

An intelligent travel planner built with **LangChain ReAct Agent** that autonomously searches flights, hotels, live weather, and attractions to generate optimized day-wise itineraries for Indian travel destinations.

---

## 🏗 Architecture

```
travel_agent/
├── data/                    
│   ├── flights.json         
│   ├── hotels.json          
│   └── places.json          
├── tools/                   
│   ├── flight_tool.py       
│   ├── hotel_tool.py        
│   ├── places_tool.py       
│   ├── weather_tool.py      
│   └── budget_tool.py       
├── agent/
│   ├── travel_agent.py      
│   └── prompts.py           
├── utils/
│   ├── data_loader.py       
│   ├── helpers.py           
│   ├── formatter.py         
│   └── conflict_checker.py
├── ui/
│   └── app.py             
|
├── .env
└── requirements.txt
```

---

## ⚙ Setup

```bash
git clone <repo-url>
cd travel_agent
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your OpenRouter API key to .env
```

**.env:**
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
OPENROUTER_REFERER=http://localhost
OPENROUTER_APP_TITLE=AI Travel Planner
```

Get API key → https://openrouter.ai/keys

---

## 🚀 Run

```bash
streamlit run ui/app.py
```

---

## 🌐 Supported Cities & Routes

**Cities:** Bangalore, Chennai, Delhi, Goa, Hyderabad, Jaipur, Kolkata, Mumbai

**Valid routes (from dataset):**
| From | To |
|------|----|
| Bangalore | Delhi, Goa, Kolkata, Mumbai |
| Chennai | Bangalore, Hyderabad, Mumbai |
| Delhi | Kolkata |
| Goa | Bangalore, Hyderabad, Jaipur, Kolkata, Mumbai |
| Hyderabad | Delhi, Goa, Kolkata, Mumbai |
| Jaipur | Bangalore, Chennai, Delhi, Kolkata, Mumbai |
| Kolkata | Jaipur |
| Mumbai | Goa, Hyderabad |

---

## 🛠 Tools

| Tool | Input | Output |
|------|-------|--------|
| `flight_search_tool` | source, destination, max_price | Cheapest + backup flights |
| `hotel_search_tool` | city, style, max_price, min_stars | Best + backup hotels |
| `places_discovery_tool` | city, category, limit | Top-rated attractions |
| `weather_lookup_tool` | city, date, days | Day-wise forecast |
| `budget_estimation_tool` | flight, hotel, nights, style | Itemized breakdown |

---

## ✨ Features

- **Smart routing** — UI only shows valid city pairs from dataset (no "no data found" loops)
- **Skeleton loader** — animated placeholder while agent thinks
- **Chat re-planning** — "Change hotel to luxury" → agent updates full plan
- **Trip history** — last 5 trips saved, one-click reload
- **Budget chart** — Plotly donut with over/under budget indicator
- **Map view** — Folium map with destination pin
- **PDF export** — full itinerary downloadable
- **Packing checklist** — beach / hill / city presets
- **Agent recovery** — if iteration limit hit, reconstructs output from tool observations

---
