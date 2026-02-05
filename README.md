# Git-Alchemist ⚗️

**Git-Alchemist ⚗️** is a unified AI-powered CLI tool for automating GitHub repository management. It consolidates multiple technical utilities into a single, intelligent system powered by Google's Gemini 3 and Gemma 3 models.

### 🌐 [Visit the Official Site](https://abduznik.github.io/Git-Alchemist/)

---

## Features

*   **Smart Profile Generator:** Intelligently generates or updates your GitHub Profile README.
*   **Topic Generator:** Auto-tag your repositories with AI-suggested topics for better discoverability.
*   **Description Refiner:** Automatically generates repository descriptions by analyzing your README content.
*   **Issue Drafter:** Translates loose ideas into structured, technical GitHub Issue drafts.
*   **Architect (Scaffold):** Generates and executes project scaffolding commands in a safe, temporary workspace.
*   **Fix & Explain:** Apply AI-powered patches to specific files or get concise technical explanations for complex code.
*   **Gold Score Audit:** Measure your repository's professional quality and health.
*   **The Sage:** Contextual codebase chat to answer deep technical questions about your code.
*   **Alchemist Helper:** Interactive assistant to help you navigate the tool and your project.
*   **Commit Alchemist:** Automated semantic commit message suggestions from staged changes.
*   **Forge:** Automated PR creation from local changes.

## Model Tiers

Git-Alchemist features a dynamic fallback system to ensure you never hit a quota wall:

*   **Fast Mode (Default):** Utilizes **Gemma 3 (27B)** and **Gemini 3 Flash**. Optimized for speed and high-volume tasks.
*   **Smart Mode (`--smart`):** Utilizes **Gemini 3 Pro** and **Gemini 2.5 Pro**. Optimized for complex architecture and deep code analysis.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/abduznik/Git-Alchemist.git
    cd Git-Alchemist
    ```

2.  **Install as a Global Library:**
    ```bash
    pip install git-alchemist
    ```

3.  **Set up your Environment:**
    Create a `.env` file in the directory or export it in your shell:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## Usage

Once installed, you can run the `alchemist` command from **any directory**:

```bash
# Audit a repository
alchemist audit

# Optimize repository topics
alchemist topics

# Generate semantic commit messages
alchemist commit

# Ask the Sage a question
alchemist sage "How does the audit scoring work?"

# Start the interactive helper
alchemist helper

# Scaffold a new project (Safe Mode)
alchemist scaffold "A FastAPI backend with a React frontend" --smart
```

## Requirements

*   Python 3.10+
*   GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
*   A Google Gemini API Key.

## Migration Note

This tool replaces and consolidates the following legacy scripts:
*   `AI-Gen-Profile`
*   `AI-Gen-Topics`
*   `AI-Gen-Description`
*   `AI-Gen-Issue`
*   `Ai-Pro-Arch`

---
*Created by [abduznik](https://github.com/abduznik)*
