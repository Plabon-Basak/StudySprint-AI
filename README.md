# StudySprint AI

StudySprint AI is an AI-powered revision coach that turns study notes into a short quiz and a personalized, day-by-day revision plan.

Instead of stopping at quiz scores, StudySprint AI identifies weak topics from incorrect answers and helps students decide what to revise next, based on their exam date and available study time.

## Features

- **AI-generated quiz:** Generate five multiple-choice questions from pasted study notes, each with four answer options.
- **Automatic grading:** Submit answers and see your score and the correct answers.
- **Explanations:** Review explanations for the quiz questions.
- **Weak-topic identification:** Identify topics that need more attention based on incorrect answers.
- **Personalized revision schedule:** Generate a day-by-day revision plan that prioritizes weak topics and considers the exam date and daily study-time budget.
- **Single-session workflow:** Complete a study session without creating an account or setting up a database.

## Tech Stack

- Python
- Streamlit
- Google Gemini API (`google-genai`)
- `python-dotenv` for environment configuration
- Pytest for automated testing

## Prerequisites

- Python installed on your computer
- A Google AI Studio API key with access to a supported Gemini model
- Git (optional, for cloning the repository)

## Installation and Setup

### 1. Get the project

If you have already downloaded or cloned this repository, open PowerShell in the project directory.

Otherwise, clone your repository and enter its directory:

```powershell
git clone https://github.com/Plabon-Basak/StudySprint-AI.git
cd "StudySprint AI"
```

Replace `https://github.com/Plabon-Basak/StudySprint-AI.git` with your actual repository URL.

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the project's Python executable directly using the commands in the following sections.

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure the Gemini API

Create your local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and set your own API key and preferred model:

```dotenv
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-3.8-flash
```

Replace the placeholder with your own Google AI Studio API key. Use a Gemini model available to your API account.

**Security:** Keep `.env` private. Never commit your API key, share it publicly, or include it in screenshots. The repository's `.gitignore` should exclude the real `.env` file.

## Run the Application

With the virtual environment activated, run:

```powershell
streamlit run app.py
```

Alternatively, without activating the environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will display a local URL in the terminal, usually `http://localhost:8501`. Open that address in your browser.

## How to Use StudySprint AI

1. Paste your study notes into the application.
2. Enter your exam date.
3. Specify how many hours you can study per day.
4. Generate a quiz containing five multiple-choice questions.
5. Answer all questions and submit your responses.
6. Review your score, correct answers, explanations, and weak topics.
7. Follow the personalized day-by-day revision schedule.

The schedule turns quiz results into concrete revision tasks, helping you focus on the topics that need the most attention before your exam.

## Run the Tests

Run the automated test suite from the project root:

```powershell
python -m pytest -q
```

On the development environment used for this project, the suite has passed with **87 tests passing**. Test results may change if the code or dependencies change.

The tests cover application behavior, quiz logic, input validation, AI client behavior, and revision scheduling. AI-related tests use test doubles where appropriate and do not require live API requests for every test.

## Project Structure

```text
StudySprint-AI/
├── app.py
├── ai_client.py
├── quiz_logic.py
├── schedule.py
├── validators.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── devpost/
│   ├── checklist.md
│   ├── prd.md
│   ├── scope.md
│   └── spec.md
└── tests/
    ├── test_ai_client.py
    ├── test_app.py
    ├── test_quiz_logic.py
    ├── test_schedule.py
    └── test_validators.py
```

## Current Scope

StudySprint AI is designed as a focused, single-session prototype. It does not currently require user accounts, a database, file uploads, or long-term progress tracking.

Deployment is optional in the approved prototype scope. Check the project's current hosting status before relying on a public demo URL.

## Future Improvements

Potential future extensions include:

- Uploading study materials from files
- Saving progress between study sessions
- Supporting larger question banks and repeated quizzes

These are future possibilities, not claims about current functionality.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Run Locally

### Requirements

- Python 3.11 or later
- A Google Gemini API key

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/Plabon-Basak/StudySprint-AI.git
   cd StudySprint-AI
   ```

2. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Gemini API key:

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=your_supported_gemini_model
   ```

   Replace the placeholder values with your own credentials and a model supported by your Google AI Studio project. Never commit your actual API key.

5. Start the application:

   ```bash
   streamlit run app.py
   ```

## Testing

Run the automated tests with:

```bash
pytest -q
```

## Deployment

StudySprint AI is deployed on Streamlit Community Cloud:

https://studysprint-ai-plabonbasak.streamlit.app/

## Acknowledgments

StudySprint AI uses Google's Gemini API to generate practice questions and support personalized study planning. Streamlit provides the web application interface.


