"""
Prompt templates for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
All LLM prompts for job application automation.
"""

# ============================================================
# RESUME SECTION PROMPTS
# ============================================================

PERSONAL_INFORMATION_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the question using the provided resume information.

Resume Personal Information:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- If information is not in the resume, provide a reasonable default
- Maximum 140 characters
- No extra text, just the answer
"""

SELF_IDENTIFICATION_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the self-identification question using the provided resume information.

Resume Self Identification:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

LEGAL_AUTHORIZATION_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the work authorization question using the provided resume information.

Resume Legal Authorization:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Be honest about visa/sponsorship requirements
- Maximum 140 characters
- No extra text, just the answer
"""

WORK_PREFERENCES_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the work preference question using the provided resume information.

Resume Work Preferences:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

EDUCATION_DETAILS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the education question using the provided resume information.

Resume Education Details:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

EXPERIENCE_DETAILS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the experience question using the provided resume information.

Resume Experience Details:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Infer experience when plausible from resume
- Never return "0" years experience - minimum "2"
- Maximum 140 characters
- No extra text, just the answer
"""

PROJECTS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the project question using the provided resume information.

Resume Projects:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

AVAILABILITY_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the availability question using the provided resume information.

Resume Availability:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

SALARY_EXPECTATIONS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the salary question using the provided resume information.

Resume Salary Expectations:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Provide range if asked
- Maximum 140 characters
- No extra text, just the answer
"""

CERTIFICATIONS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the certification question using the provided resume information.

Resume Certifications:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

LANGUAGES_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the language question using the provided resume information.

Resume Languages:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

INTERESTS_PROMPT = """
You are an AI assistant helping to fill out job application forms.
Answer the interests question using the provided resume information.

Resume Interests:
{resume_section}

Question: {question}

Rules:
- Answer directly and concisely
- Use only information from the resume
- Maximum 140 characters
- No extra text, just the answer
"""

# ============================================================
# UTILITY PROMPTS
# ============================================================

SUMMARIZE_JOB_DESCRIPTION = """
Summarize the following job description in 3-4 bullet points.
Focus on: key responsibilities, required skills, experience level, and notable requirements.

Job Description:
{job_description}

Summary:
"""

GENERATE_COVER_LETTER = """
Write a compelling, tailored cover letter for the following position.

Position: {position}
Company: {company}
Job Description:
{job_description}

Candidate Resume:
{resume}

Requirements:
- Professional tone
- Highlight relevant experience and skills
- Show enthusiasm for the company/role
- 3-4 paragraphs
- No placeholder text
- Address hiring manager professionally
"""

ANSWER_NUMERIC_QUESTION = """
Answer the following numeric question based on the candidate's resume and job description.

Question: {question}
Job Description: {job_description}
Resume: {resume}

Rules:
- Provide a single number
- Infer from resume if not explicitly stated
- Never answer "0" for years of experience (minimum "2")
- Be honest but optimistic
"""

ANSWER_MULTIPLE_CHOICE = """
Select the best answer for the following multiple choice question based on the candidate's resume.

Question: {question}
Options:
{options}
Job Description: {job_description}
Resume: {resume}

Rules:
- Return ONLY the letter or text of the chosen option
- No explanation
- Choose the most accurate option based on resume
"""

ANSWER_FREE_TEXT = """
Answer the following question based on the candidate's resume and job description.

Question: {question}
Job Description: {job_description}
Resume: {resume}

Rules:
- Answer directly and concisely
- Maximum 140 characters
- Use resume information when relevant
- Be professional and positive
- No extra text, just the answer
"""

SCORE_JOB_SUITABILITY = """
Rate the candidate's suitability for this job on a scale of 1-10.

Job Description: {job_description}
Resume: {resume}
Preferences: {preferences}

Consider:
- Skills match
- Experience level match
- Location/remote preferences
- Salary expectations
- Work authorization

Return ONLY a single integer from 1 to 10.
"""

# ============================================================
# CLASSIFICATION PROMPTS
# ============================================================

RESUME_VS_COVER_LETTER = """
Classify the following question as either "resume" or "cover_letter".

Question: {question}

Return ONLY "resume" or "cover_letter".
"""

RESUME_SECTION_ROUTER = """
Route the following question to the most relevant resume section.

Available sections:
- personal_information
- self_identification
- legal_authorization
- work_preferences
- education_details
- experience_details
- projects
- availability
- salary_expectations
- certifications
- languages
- interests

Question: {question}

Return ONLY the section name from the list above.
"""

# ============================================================
# INPUT ERROR FIXING
# ============================================================

FIX_INPUT_ERROR = """
The previous answer was rejected. Fix it based on the error message.

Question: {question}
Previous Answer: {previous_answer}
Error: {error_message}
Job Description: {job_description}
Resume: {resume}

Rules:
- Provide corrected answer only
- Maximum 140 characters
- No extra text
"""