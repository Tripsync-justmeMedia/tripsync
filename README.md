# ✈️ TripSync — AI-Powered Travel Planner

TripSync is a high-performance, AI-driven travel planning application designed to turn complex itineraries into seamless experiences. Built with a focus on speed, privacy, and "Zero-Downtime" reliability.

**Live App:** [https://tripsync-ilao.onrender.com](https://tripsync-ilao.onrender.com)

## 🌟 Key Features

*   **3-Tier AI Orchestration**: Choose between high-speed Cloud AI, deep Reasoning (Gemma 4 Expert), or complete Privacy (Local AI).
*   **Interactive Planner**: Don't just get a list—edit your activities, refine with AI instructions, and build the perfect trip day-by-day.
*   **Real-Time Price Matching**: Integrated flight and hotel booking links with live availability from partners like Booking.com and Google Flights.
*   **Viral Sharing**: One-click sharing to WhatsApp, X (Twitter), and Facebook.
*   **PWA Ready**: Install TripSync as a native app on iOS and Android for offline access and better performance.

## 🧠 AI Architecture (The "3 Brains")

TripSync uses a sophisticated multi-tier AI strategy to ensure you always get the best results:

1.  **Cloud AI (Groq)**: Optimized for milliseconds-fast responses.
2.  **Gemma 4 Expert (Google Gemini API)**: A high-intelligence reasoning tier for complex, "off-the-beaten-path" requests.
3.  **Local AI (Ollama/Gemma4)**: Runs directly on your hardware. No data ever leaves your device. Perfect for privacy-conscious travelers.

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
