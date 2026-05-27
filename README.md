# ✈️ TripSync — AI-Powered Travel Planner

TripSync is a high-performance, AI-driven travel planning application designed to turn complex itineraries into seamless experiences. Built with a focus on speed, privacy, and "Zero-Downtime" reliability.

**Live App:** [https://tripsync-ilao.onrender.com](https://tripsync-ilao.onrender.com)

## 🌟 Key Features

*   **Smart Deal Optimizer**: Built-in intelligence that automatically analyzes booking timing, currency arbitrage (e.g., BRL/INR savings), and travel day patterns to find the best rates.
*   **Precision Flight Engine**: Eliminates AI "hallucinations" by requiring origin data for accurate intercontinental flight pricing and durations.
*   **3-Tier AI Orchestration**: Choose between high-speed Cloud AI, deep Reasoning (Gemma 4 Expert), or complete Privacy (Local AI).
*   **Modern PWA Experience**: Native-feel mobile bottom navigation, frosted-glass aesthetics, and "One-Touch Resume" to pick up where you left off.
*   **Minimalist UI**: Deeply cleaned search interface with collapsible preference panels, designed for speed on mobile devices.
*   **Interactive Planner**: Build detailed itineraries day-by-day with AI refinement.
*   **Real-Time Price Matching**: Integrated booking links with live availability from partners like Booking.com, Google Flights, and Skyscanner.

## 🧠 AI Architecture (The "3 Brains")

TripSync uses a sophisticated multi-tier AI strategy to ensure you always get the best results:

1.  **Cloud AI (Groq)**: Optimized for milliseconds-fast responses.
2.  **Gemma 4 Expert (Google Gemini API)**: A high-intelligence reasoning tier for complex requests. (Avg. response: ~30s)
3.  **Local AI (Ollama/Gemma4)**: Runs directly on your hardware. No data ever leaves your device. Perfect for privacy-conscious travelers.

*Note: Expert mode uses a "Silent Fallback" strategy. If the request nears the 30s platform limit, it seamlessly switches to Cloud AI to ensure you always get a result.*

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
