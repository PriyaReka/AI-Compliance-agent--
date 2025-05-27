import google.generativeai as genai
import os

class GeminiComplianceFlagger:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment or passed to constructor.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-pro"

    def flag_risks(self, document_text: str) -> str:
        prompt = (
            "You are a compliance expert. Review the following document for any risks related to "
            "data privacy (GDPR), financial reporting, or ESG. List any compliance risks and suggest corrections.\n\n"
            f"Document:\n{document_text}\n\nCompliance Risks and Suggestions:"
        )
        response = self.model.generate_content(prompt)
        return response.text