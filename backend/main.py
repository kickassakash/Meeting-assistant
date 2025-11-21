from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Meeting, ActionItem, init_db, get_db
from backend.keyword_indexer import keyword_indexer
from agent.meeting_agent import meeting_agent

app = FastAPI(title="Meeting & Task Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


class MeetingCreate(BaseModel):
    title: str
    datetime: datetime
    participants: str
    raw_notes: str


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    datetime: Optional[datetime] = None
    participants: Optional[str] = None
    raw_notes: Optional[str] = None


class MeetingResponse(BaseModel):
    id: int
    title: str
    datetime: datetime
    participants: str
    raw_notes: str
    ai_summary: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ActionItemResponse(BaseModel):
    id: int
    meeting_id: int
    description: str
    owner: Optional[str]
    due_date: Optional[datetime]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActionItemUpdate(BaseModel):
    status: str


class AskAIRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {"message": "Meeting & Task Assistant API", "status": "running"}


@app.post("/meetings/", response_model=MeetingResponse)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    """Create a new meeting"""
    db_meeting = Meeting(
        title=meeting.title,
        datetime=meeting.datetime,
        participants=meeting.participants,
        raw_notes=meeting.raw_notes
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    
    keyword_indexer.index_meeting(db_meeting.id, db_meeting.raw_notes)
    
    return db_meeting


@app.get("/meetings/", response_model=List[MeetingResponse])
def get_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all meetings"""
    meetings = db.query(Meeting).order_by(Meeting.datetime.desc()).offset(skip).limit(limit).all()
    return meetings


@app.get("/meetings/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Get a specific meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.put("/meetings/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate, db: Session = Depends(get_db)):
    """Update a meeting"""
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    update_data = meeting_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_meeting, key, value)
    
    db.commit()
    db.refresh(db_meeting)
    
    keyword_indexer.remove_meeting(meeting_id)
    keyword_indexer.index_meeting(meeting_id, db_meeting.raw_notes)
    
    return db_meeting


@app.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Delete a meeting"""
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    keyword_indexer.remove_meeting(meeting_id)
    db.delete(db_meeting)
    db.commit()
    
    return {"message": "Meeting deleted successfully"}


@app.post("/meetings/{meeting_id}/process")
def process_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Process a meeting with AI to generate summary, action items, and tags"""
    db_meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    try:
        result = meeting_agent.process_meeting(db_meeting.raw_notes)
        
        db_meeting.ai_summary = result["summary"]
        db_meeting.tags = ", ".join(result["tags"])
        
        db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).delete()
        
        for item_data in result["action_items"]:
            action_item = ActionItem(
                meeting_id=meeting_id,
                description=item_data.get("description", ""),
                owner=item_data.get("owner"),
                due_date=datetime.fromisoformat(item_data["due_date"]) if item_data.get("due_date") else None,
                status="pending"
            )
            db.add(action_item)
        
        db.commit()
        db.refresh(db_meeting)
        
        return {
            "message": "Meeting processed successfully",
            "summary": db_meeting.ai_summary,
            "tags": db_meeting.tags,
            "action_items_count": len(result["action_items"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing meeting: {str(e)}")


@app.get("/action-items/", response_model=List[ActionItemResponse])
def get_all_action_items(db: Session = Depends(get_db)):
    """Get all action items across all meetings"""
    action_items = db.query(ActionItem).order_by(ActionItem.created_at.desc()).all()
    return action_items


@app.get("/meetings/{meeting_id}/action-items/", response_model=List[ActionItemResponse])
def get_meeting_action_items(meeting_id: int, db: Session = Depends(get_db)):
    """Get action items for a specific meeting"""
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    return action_items


@app.patch("/action-items/{action_item_id}", response_model=ActionItemResponse)
def update_action_item(action_item_id: int, update: ActionItemUpdate, db: Session = Depends(get_db)):
    """Update an action item status"""
    action_item = db.query(ActionItem).filter(ActionItem.id == action_item_id).first()
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    action_item.status = update.status
    db.commit()
    db.refresh(action_item)
    
    return action_item


@app.post("/ask-ai/")
def ask_ai(request: AskAIRequest, db: Session = Depends(get_db)):
    """Ask AI a question about past meetings"""
    try:
        relevant_notes = keyword_indexer.get_relevant_notes(request.question, limit=5)
        
        if not relevant_notes:
            return {
                "question": request.question,
                "answer": "I couldn't find any relevant meetings to answer your question.",
                "relevant_meetings": []
            }
        
        relevant_meetings = []
        for note_data in relevant_notes:
            meeting = db.query(Meeting).filter(Meeting.id == note_data["meeting_id"]).first()
            if meeting:
                relevant_meetings.append({
                    "meeting_id": meeting.id,
                    "title": meeting.title,
                    "notes": meeting.raw_notes
                })
        
        answer = meeting_agent.answer_question(request.question, relevant_meetings)
        
        return {
            "question": request.question,
            "answer": answer,
            "relevant_meetings": [{"id": m["meeting_id"], "title": m["title"]} for m in relevant_meetings]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Load existing meetings into keyword indexer on startup"""
    db = next(get_db())
    meetings = db.query(Meeting).all()
    for meeting in meetings:
        keyword_indexer.index_meeting(meeting.id, meeting.raw_notes)
    db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
