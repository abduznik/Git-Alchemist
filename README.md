# Git-Alchemist ⚗️

**Git-Alchemist** is a unified AI-powered CLI tool for automating GitHub repository management. It consolidates multiple utilities into a single, intelligent system powered by Google's Gemini 2.0 (via `google-genai`).

## Features

*   **🧪 Smart Profile Generator:** Automatically generates or updates your GitHub Profile README based on your public repositories. Detects existing profiles and intelligently inserts new projects.
*   *(Coming Soon)* **🏷️ Topic Generator:** Auto-tag your repositories with AI-suggested topics.
*   *(Coming Soon)* **📝 Description Refiner:** Rewrite repository descriptions for clarity and impact.
*   *(Coming Soon)* **🐛 Issue Drafter:** Generate structured issue templates from loose notes.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/abduznik/Git-Alchemist.git
    cd Git-Alchemist
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up your Environment:
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## Usage

Run the tool via Python:

```bash
# Generate/Update your profile
python -m src.cli profile

# Force a full regeneration
python -m src.cli profile --force
```

## Requirements

*   Python 3.10+
*   GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
*   A Google Gemini API Key.

## Migration Note

This tool replaces the following legacy scripts:
*   `AI-Gen-Profile`
*   `AI-Gen-Topics`
*   `AI-Gen-Description`
*   `AI-Gen-Issue`

These repositories are now archived.
