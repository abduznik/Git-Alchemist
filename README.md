# Git-Alchemist ⚗️

**Git-Alchemist** is a unified AI-powered CLI tool for automating GitHub repository management. It consolidates multiple technical utilities into a single, intelligent system powered by Google's Gemini and Gemma 3 models.

## 🚀 Features

*   **🧪 Smart Profile Generator:** Intelligently generates or updates your GitHub Profile README.
*   **🏷️ Topic Generator:** Auto-tag your repositories with AI-suggested topics for better discoverability.
*   **📝 Description Refiner:** Automatically generates repository descriptions by analyzing your README content.
*   **🐛 Issue Drafter:** Translates loose ideas into structured, technical GitHub Issue drafts.
*   **🏛️ Architect (Scaffold):** Generates and executes project scaffolding commands in a safe, temporary workspace.
*   **🛠️ Fix & Explain:** Apply AI-powered patches to specific files or get concise technical explanations for complex code.

## 🧠 Model Tiers

Git-Alchemist features a dynamic fallback system to ensure you never hit a quota wall:

*   **Fast Mode (Default):** Utilizes **Gemma 3 (27B)** and **Gemini 3 Flash**. Optimized for speed and high-volume tasks.
*   **Smart Mode (`--smart`):** Utilizes **Gemini 3 Pro** and **Gemini 2.5 Pro**. Optimized for complex architecture and deep code analysis.

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/abduznik/Git-Alchemist.git
    cd Git-Alchemist
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your Environment:**
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## 🛠️ Usage

```bash
# Optimize your repository topics
python -m src.cli topics

# Generate missing descriptions
python -m src.cli describe

# Draft a technical issue
python -m src.cli issue "Add a dark mode toggle to the dashboard"

# Scaffold a new project (Safe Mode)
python -m src.cli scaffold "A FastAPI backend with a React frontend" --smart

# Apply a fix to a file
python -m src.cli fix src/main.py "Convert this function to use async/await"
```

## 🛠️ Requirements

*   Python 3.10+
*   GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
*   A Google Gemini API Key.

## 📜 Migration Note

This tool replaces and consolidates the following legacy scripts:
*   `AI-Gen-Profile`
*   `AI-Gen-Topics`
*   `AI-Gen-Description`
*   `AI-Gen-Issue`
*   `Ai-Pro-Arch`

---
*Created by [abduznik](https://github.com/abduznik)*