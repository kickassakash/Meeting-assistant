import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class MeetingAgent:
    """Gemini-powered agent for meeting summarization, action item extraction, and Q&A"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
    
    def process_meeting(self, meeting_notes: str) -> Dict[str, Any]:
        """Process a meeting to generate summary, action items, and tags"""
        if not meeting_notes:
            return {
                "summary": "",
                "action_items": [],
                "tags": []
            }
        
        summary = self._summarize_meeting(meeting_notes)
        action_items = self._extract_action_items(meeting_notes)
        tags = self._generate_tags(meeting_notes, summary)
        
        return {
            "summary": summary,
            "action_items": action_items,
            "tags": tags
        }
    
    def _summarize_meeting(self, notes: str) -> str:
        """Summarize meeting notes"""
        try:
            prompt = f"""Summarize the following meeting notes concisely in 2-3 paragraphs while maintaining key points:

{notes}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text or ""
        except Exception as e:
            print(f"Error summarizing meeting: {e}")
            return ""
    
    def _extract_action_items(self, notes: str) -> List[Dict[str, Any]]:
        """Extract action items from meeting notes"""
        try:
            system_prompt = """You are a helpful assistant that extracts action items from meeting notes.
Extract action items and return them as a JSON array.
Each action item should have: description, owner (if mentioned), due_date (if mentioned in ISO format).
Only extract information that is explicitly mentioned in the notes. Do not invent owners or dates.
Return ONLY a JSON array, nothing else."""
            
            prompt = f"""{system_prompt}

Meeting notes:
{notes}

Extract action items as JSON array:"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if not response.text:
                return []
            
            content = response.text.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
            
            action_items = json.loads(content)
            return action_items if isinstance(action_items, list) else []
        except Exception as e:
            print(f"Error extracting action items: {e}")
            return []
    
    def _generate_tags(self, notes: str, summary: str) -> List[str]:
        """Generate relevant tags for the meeting"""
        try:
            prompt = f"""Generate 3-5 concise tags that capture the main topics discussed in this meeting.
Return tags as a comma-separated list.

Summary: {summary[:300]}

Notes: {notes[:500]}

Tags:"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if not response.text:
                return []
            
            tags_text = response.text.strip()
            tags = [tag.strip() for tag in tags_text.split(",")]
            return tags[:5]
        except Exception as e:
            print(f"Error generating tags: {e}")
            return []
    
    def answer_question(self, question: str, relevant_meetings: List[Dict[str, Any]]) -> str:
        """Answer a question based on relevant meeting context"""
        if not question or not relevant_meetings:
            return "I don't have enough information to answer that question."
        
        try:
            context = "\n\n".join([
                f"Meeting {i+1} - {m.get('title', 'N/A')} (ID: {m.get('meeting_id', 'N/A')}):\n{m.get('notes', '')}"
                for i, m in enumerate(relevant_meetings)
            ])
            
            prompt = f"""You are a helpful assistant that answers questions about past meetings.
Use only the information provided in the meeting notes to answer questions.
If the information is not available in the notes, say so clearly.

Question: {question}

Relevant Meeting Notes:
{context}

Answer:"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text or "I couldn't generate an answer."
        except Exception as e:
            print(f"Error answering question: {e}")
            return f"Error processing your question: {str(e)}"


meeting_agent = MeetingAgent()
