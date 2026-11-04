# Job Autopilot (ApplyPilot Automation)

Autonomous job discovery, fit scoring, resume tailoring, and application generation powered by [ApplyPilot](https://github.com/Pickle-Pixel/ApplyPilot) and Google Gemini AI.

## 🚀 Repository Structure

- `.github/workflows/run-applypilot.yml`: GitHub Actions automated workflow (runs on a daily schedule or manual click).
- `profile.json`: Your master professional profile and career facts used by ApplyPilot for scoring and tailoring.
- `searches.yaml`: Search queries and target criteria (roles, locations, filters).
- `resume.txt`: Plain-text structured resume used by LLMs to tailor applications without hallucinations.
- `resume.pdf`: Original master PDF resume.

## ⚙️ Setup Instructions for GitHub Actions

### 1. Add your Gemini API Key Secret
1. Go to your GitHub repository: [adebiyicaleb23/job-autopilot](https://github.com/adebiyicaleb23/job-autopilot)
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Set:
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: *(Your Google Gemini API Key from Google AI Studio)*
5. Click **Add secret**

### 2. Run the Workflow Manually
1. Go to the **Actions** tab in your GitHub repository
2. Click **Run ApplyPilot** in the left sidebar
3. Click **Run workflow** (select branch `main`)
4. Once completed, download your tailored resumes and cover letters from the **Artifacts** section at the bottom of the run page!

## 💻 Local Usage

You can also run ApplyPilot directly on your computer:

```bash
# Set your environment variable
$env:APPLYPILOT_DIR="C:\Users\USER\Desktop\applypilot"

# Run doctor to verify all components
python -m applypilot doctor

# Discover new jobs and tailor resumes
python -m applypilot run
```

