import re
from collections import defaultdict
from typing import List, Dict, Set, Any


class KeywordIndexer:
    """Simple keyword-based indexer for meeting notes using hashmap"""
    
    def __init__(self):
        self.index: Dict[str, Set[int]] = defaultdict(set)
        self.meeting_notes: Dict[int, str] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, removing punctuation and converting to lowercase"""
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return [w for w in words if len(w) > 2]
    
    def index_meeting(self, meeting_id: int, notes: str):
        """Index a meeting's notes by creating a hashmap of words to meeting IDs"""
        self.meeting_notes[meeting_id] = notes
        words = self._tokenize(notes)
        
        for word in words:
            self.index[word].add(meeting_id)
    
    def remove_meeting(self, meeting_id: int):
        """Remove a meeting from the index"""
        if meeting_id in self.meeting_notes:
            notes = self.meeting_notes[meeting_id]
            words = self._tokenize(notes)
            
            for word in words:
                self.index[word].discard(meeting_id)
            
            del self.meeting_notes[meeting_id]
    
    def search_keywords(self, query: str) -> List[int]:
        """Search for meetings containing keywords from the query"""
        keywords = self._tokenize(query)
        
        if not keywords:
            return []
        
        meeting_ids = set()
        for keyword in keywords:
            if keyword in self.index:
                meeting_ids.update(self.index[keyword])
        
        return list(meeting_ids)
    
    def get_relevant_notes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant meeting notes based on keyword search with ranking"""
        keywords = self._tokenize(query)
        
        if not keywords:
            return []
        
        meeting_scores = defaultdict(int)
        
        for keyword in keywords:
            if keyword in self.index:
                for meeting_id in self.index[keyword]:
                    meeting_scores[meeting_id] += 1
        
        sorted_meetings = sorted(
            meeting_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {"meeting_id": mid, "score": score, "notes": self.meeting_notes.get(mid, "")}
            for mid, score in sorted_meetings
        ]


keyword_indexer = KeywordIndexer()
