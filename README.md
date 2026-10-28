# ✈️ TripSync — AI-Powered Travel Planner

TripSync is a high-performance, AI-driven travel planning application designed to turn complex itineraries into seamless experiences. Built with a focus on speed, privacy, and "Zero-Downtime" reliability.

**Live App:** [https://tripsync.ca](https://tripsync.ca)

## 🌟 Key Features

*   **Smart Deal Optimizer**: Built-in intelligence that automatically analyzes booking timing, currency arbitrage (e.g., BRL/INR savings), and travel day patterns to find the best rates.
*   **Grounded flight data**: Legs resolve to real IATA codes and fares are queried per route, so durations and prices are not invented. AI itinerary *text* still needs a human read — the app says so on every plan.
*   **3-Tier AI Orchestration**: Choose between high-speed Cloud AI, deep Reasoning (Gemma 4 Expert), or complete Privacy (Local AI).
*   **Modern PWA Experience**: Native-feel mobile bottom navigation, frosted-glass aesthetics, and "One-Touch Resume" to pick up where you left off.
*   **Minimalist UI**: Deeply cleaned search interface with collapsible preference panels, designed for speed on mobile devices.
*   **Interactive Planner**: Build detailed itineraries day-by-day with AI refinement.
*   **Fare lookups with honest labels**: cached fares (~48h) and clearly-marked estimates, with tracked deep links so the partner site shows the live price at checkout. Labels never claim "live" for a cached fare.

## 🧠 AI Architecture (The "3 Brains")

TripSync uses a sophisticated multi-tier AI strategy to ensure you always get the best results:

1.  **Cloud AI (Groq)**: Optimized for milliseconds-fast responses.
2.  **Gemma 4 Expert (Google Gemini API)**: A high-intelligence reasoning tier for complex requests. (Avg. response: ~30s)
3.  **Local AI (Ollama/Gemma4)**: Runs on the host machine. In local mode the itinerary request stays on that machine; the page itself still loads from tripsync.ca. Best for private/offline use.

*Note: if a deep request nears the 30s platform limit, the server may fall back to the fast model so you still get a result. Deep mode is best-effort, not guaranteed.*

## 🛠 Tech Stack

*   **Backend**: Python / Flask
*   **Frontend**: Plain HTML5, CSS3 (Glassmorphism), Vanilla JS
*   **Database**: SQLite (Local-first history)
*   **Infrastructure**: Render / GitHub CI/CD

## 🚀 Local Setup

To run TripSync locally:

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/Tripsync-justmeMedia/tripsync.git
    cd tripsync
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**:
    Create a `.env` file with your API keys:
    ```
    GROQ_API_KEY=your_key
    GEMINI_API_KEY=your_key
    ```

4.  **Run the server**:
    ```bash
    python3 server.py
    ```

## 📄 License
© 2026 TripSync by Just Me Media. All Rights Reserved.
