# Project Plan: Meeting Notes to Action Items Assistant
# Yiyang Tong
## 1. Project Title
**Meeting Notes → Action Items Assistant**

## 2. Target User, Workflow, and Business Value
- **Target User**: Product Managers, student project team members, and small startup teams (I am also a target user as a student/product intern).
- **Workflow**:  
  After a meeting, the user pastes their raw meeting notes (text, Zoom summary, or bullet points) into a web application. The system automatically extracts and generates a structured list of action items, including task description, assignee, deadline, and priority. The user can then quickly review, edit, and export the action items as Markdown or CSV.
- **Business Value**:  
  This workflow saves significant time (typically 15–30 minutes of manual cleanup reduced to under 2 minutes), reduces the risk of missing important tasks, and improves team accountability and execution speed. It is especially valuable for students and small teams where meeting outcomes need to be turned into concrete next steps quickly.

## 3. Problem Statement and GenAI Fit
**Problem Statement**:  
Meeting notes are often messy natural language with implied information, multiple speakers, vague deadlines, and unclear ownership. Manually converting them into clear action items is time-consuming and error-prone, frequently leading to missed tasks or unclear responsibility.

**GenAI Fit**:  
Large language models excel at understanding context, extracting entities (people, dates, tasks), reasoning about implied intentions, and producing structured output. Simple non-GenAI tools (such as regular expressions or basic keyword extraction) perform poorly on varied note styles and implicit information, while GenAI can dramatically improve efficiency and accuracy.

## 4. Planned System Design and Baseline
**System Design**:
- **User Interface**: A simple web app built with Streamlit. Users paste notes, click “Generate”, review/edit results in a table, and export them.
- **Core Technology**:
  - **Prompt Engineering**: Few-shot examples, Chain-of-Thought reasoning, and structured JSON output to ensure consistent format (task, assignee, deadline, priority, confidence score).
  - **RAG (Retrieval-Augmented Generation)**: A small knowledge base containing team/project conventions, standard action item formats, and priority definitions to improve consistency and reduce hallucinations.
  - Additional features: Confidence scoring and governance rules (e.g., flag low-confidence items for human review).
- **User Experience**: Clean input box, generate button, editable results table, and export options.

**Baseline**:  
A simple zero-shot prompt (no few-shot examples, no RAG, no structured output) or fully manual process. This will be used for comparison to measure improvement.

**Course Concepts Integration**:
- **Prompt Engineering** (Weeks 2-3): Few-shot prompting and Chain-of-Thought will be used to improve extraction quality.
- **RAG** (Week 4): A small retrieval knowledge base will be implemented to standardize outputs and reduce errors.
- **Evaluation Design**: A clear rubric and baseline comparison will be applied.

## 5. Evaluation Plan
**Success Criteria**:
- Action item completeness ≥ 85%
- Accuracy (correct assignee, task, deadline) ≥ 80%
- Hallucination rate (fabricated items) ≤ 5%
- User-perceived usefulness (clear and actionable output)

**Measurement**:
- **Rubric**: Completeness, accuracy, format correctness, hallucination rate, and confidence level.
- **Test Set**: 10–15 real or simulated meeting notes covering normal, vague, long, and multi-speaker cases.
- **Method**: Human evaluation + LLM-as-a-Judge scoring based on the rubric.
- **Comparison**: Run both the baseline (simple prompt) and the improved system on the same test set, then analyze the differences and remaining areas needing human review.

## 6. Example Inputs and Failure Cases
**Example Inputs** (3–5 planned):
1. Clean weekly team meeting notes with clear speakers and dates.
2. Vague notes such as “We should finish this before next week.”
3. Long, messy notes mixing multiple topics.

**Anticipated Failure / Edge Cases**:
- Extremely chaotic notes with heavy abbreviations or missing context.
- Implicit action items that the model might over-interpret or miss.
- Conflicting dates or multiple people with similar names.
- Notes containing no actual action items, where the model might hallucinate tasks.

## 7. Risks and Governance
- **Potential Failures**: Hallucination of non-existent tasks, incorrect assignee assignment, or wrong deadline inference.
- **When the System Should Not Be Trusted**: When confidence scores are low, notes are too vague, or the content involves sensitive decisions.
- **Controls and Governance**:
  - Every action item will display a confidence score.
  - Low-confidence items will be automatically flagged with “Please review manually.”
  - Users must manually confirm or edit outputs before exporting.
  - No user data will be stored (processed in-session only) to protect privacy.
- **Other Concerns**: API cost (using free tiers such as Gemini where possible) and data privacy.

## 8. Plan for the Week 6 Check-in
By Week 6, I plan to have:
- A working Streamlit application that accepts pasted notes and generates structured JSON action items.
- Basic prompt with few-shot examples + a simple RAG knowledge base implemented.
- Evaluation results on at least 8–10 test cases, including a comparison table against the baseline.
- Initial prompt iteration observations showing what improved and what still requires human judgment.

## 9. (Optional) Pair Request
I plan to complete this project individually. The scope is narrow and focused, making it suitable for a single-person deep evaluation.