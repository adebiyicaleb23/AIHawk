# ApplyPilot - Automated Job Application System

Adapted from [Auto_Jobs_Applier_AI_Agent](https://github.com/Intusar/Auto_Jobs_Applier_AI_Agent)

An AI-powered job application automation system that:
- Searches for jobs on LinkedIn based on your preferences
- Uses LLMs (OpenAI, Claude, Gemini, Ollama) to answer application questions
- Generates tailored cover letters and resumes
- Auto-applies to jobs with "Easy Apply" on LinkedIn

## Features

- 🤖 **AI-Powered Applications**: Uses LLMs to intelligently answer application questions
- 📄 **Dynamic Resume Generation**: Creates tailored resumes for each application
- 🎯 **Smart Job Matching**: Filters jobs based on your preferences and blacklists
- 🔐 **Secure Configuration**: YAML-based config with API keys stored separately
- 🌐 **Multi-LLM Support**: OpenAI, Anthropic Claude, Google Gemini, Ollama (local), Perplexity
- 📊 **Application Tracking**: Tracks applications, successes, and failures

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Your Profile

Copy the example config files and customize them:

```bash
# The config files should already be in data_folder/
# Edit them with your information:
# - data_folder/secrets.yaml - Add your API keys
# - data_folder/work_preferences.yaml - Set job search preferences
# - data_folder/plain_text_resume.yaml - Add your resume data
```

### 3. Set Up LinkedIn Credentials

Either set environment variables:
```bash
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"
```

Or enter them when prompted during runtime.

### 4. Run ApplyPilot

```bash
# Run with auto-apply (default)
python main.py

# Collect job data only (no applications)
python main.py --collect

# Use a specific PDF resume
python main.py --resume path/to/resume.pdf

# Run in headless mode (for servers/CI)
python main.py --headless
```

## Configuration Files

### `data_folder/secrets.yaml`
```yaml
llm_api_key: "sk-your-openai-api-key"
# ollama_url: "http://localhost:11434"  # For local Ollama
# gemini_api_key: "your-gemini-key"      # For Google Gemini
# claude_api_key: "your-claude-key"      # For Anthropic Claude
```

### `data_folder/work_preferences.yaml`
Configure job search parameters:
- **Work type**: remote, hybrid, onsite
- **Experience levels**: internship, entry, associate, mid_senior_level, director, executive
- **Job types**: full_time, contract, part_time, etc.
- **Date posted**: all_time, month, week, 24_hours
- **Positions**: List of job titles to search for
- **Locations**: List of locations (use "Remote" for remote jobs)
- **Blacklists**: Companies, titles, and locations to exclude

### `data_folder/plain_text_resume.yaml`
Structured resume data including:
- Personal information (name, email, phone, links)
- Self-identification (EEO data)
- Legal authorization (work permits per country)
- Work preferences (remote, relocation, etc.)
- Education, experience, projects
- Certifications, languages, interests

## Project Structure

```
applypilot/
├── main.py                    # Entry point
├── config.py                  # Configuration constants
├── constants.py               # Application constants
├── requirements.txt           # Python dependencies
├── data_folder/               # Configuration files (gitignored)
│   ├── secrets.yaml
│   ├── work_preferences.yaml
│   └── plain_text_resume.yaml
├── src/
│   ├── job.py                 # Job data model
│   ├── job_application.py     # Job application model
│   ├── jobContext.py          # Job context container
│   ├── job_application_profile.py  # Resume profile parser
│   ├── job_application_saver.py    # Application persistence
│   ├── logging.py             # Loguru configuration
│   ├── regex_utils.py         # Blacklist regex generation
│   ├── utils/
│   │   ├── browser_utils.py   # Selenium helpers
│   │   ├── chrome_utils.py    # Chrome configuration
│   │   └── time_utils.py      # Random sleep utilities
│   └── ai_hawk/
│       ├── authenticator.py   # LinkedIn authentication
│       ├── bot_facade.py      # Bot orchestration
│       ├── job_manager.py     # Job search & application logic
│       ├── linkedIn_easy_applier.py  # Form filling
│       └── llm/
│           ├── llm_manager.py # LLM provider abstraction
│           └── prompts.py     # Prompt templates
└── logs/                      # Application logs
```

## Usage Modes

### Interactive Mode (Default)
```bash
python main.py
```
Opens browser window, logs into LinkedIn, and starts applying to jobs.

### Data Collection Only
```bash
python main.py --collect
```
Discovers and saves job data without submitting applications.

### Headless Mode (CI/CD)
```bash
python main.py --headless
```
Runs without visible browser window (for servers).

### Custom Resume
```bash
python main.py --resume /path/to/resume.pdf
```
Uses a specific PDF resume instead of generated one.

## Supported LLM Providers

| Provider | Model Type | Environment Variable |
|----------|------------|---------------------|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `claude` | `ANTHROPIC_API_KEY` |
| Google | `gemini` | `GOOGLE_API_KEY` |
| Ollama | `ollama` | Local (no key needed) |
| Perplexity | `perplexity` | `PERPLEXITY_API_KEY` |

Set `LLM_MODEL_TYPE` and `LLM_MODEL` in environment or config.py.

## Output Files

Applications are saved to `job_applications/` with structure:
```
job_applications/
├── {job_id} - {company} {title}/
│   ├── job_application.json    # Q&A responses
│   ├── job_description.json    # Job details
│   ├── resume.pdf              # Generated resume
│   └── cover_letter.pdf        # Generated cover letter
```

Tracking files in `data_folder/output/`:
- `success.json` - Successful applications
- `failed.json` - Failed applications
- `skipped.json` - Skipped jobs (blacklisted, already applied)
- `data.json` - Discovered jobs

## Safety Features

- **Blacklist filtering**: Excludes companies, titles, locations
- **Duplicate prevention**: Tracks applied jobs and companies
- **Rate limiting**: Random delays between actions
- **Error handling**: Graceful failure recovery
- **Manual login**: You control LinkedIn authentication

## Troubleshooting

### LinkedIn Login Issues
- Ensure you can log in manually first
- Check for 2FA - complete it manually when prompted
- LinkedIn may block automated logins - use persistent Chrome profile

### No Jobs Found
- Check work_preferences.yaml positions/locations
- Verify blacklists aren't too restrictive
- Try broader search terms

### LLM Errors
- Verify API key in secrets.yaml
- Check API quota/limits
- Try different model (e.g., gpt-4o-mini for cost savings)

### Browser Issues
- Update Chrome/Chromium
- Run `playwright install chromium`
- Check ChromeDriver version matches Chrome

## License

AGPL-3.0 - See LICENSE file for details.

## Credits

Based on [Auto_Jobs_Applier_AI_Agent](https://github.com/Intusar/Auto_Jobs_Applier_AI_Agent) by Intusar.