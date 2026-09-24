from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, Bid, Document, Verification, Notification
from app.schemas.schemas import ChatRequest, ChatResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/support/chat", tags=["AI Support"])

@router.post("", response_model=ChatResponse)
def ai_support_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "BIDDER":
        return {"reply": "[MOCK AI] I am the Bidder Compliance Assistant. I can only assist bidders with their compliance status."}
        
    query = payload.query.lower().strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    is_documents_needed = (
        "what documents do i need" in query
        or "what documents am i missing" in query
        or "कौन से दस्तावेज" in query
        or "कोणती कागदपत्रे" in query
    )
    is_missing_document = (
        "which document is missing" in query
        or "what document is missing" in query
        or "कौन सा दस्तावेज" in query
        or "कोणते कागदपत्र गहाळ" in query
    )
    is_failed_document = "which documents failed" in query or "failed documents" in query
    is_flagged_document = (
        "why was this document flagged" in query
        or "why is my bid flagged" in query
        or "चिह्नित क्यों" in query
        or "का नोंदवले" in query
    )
    is_fix_request = (
        "how do i fix" in query
        or "how can i fix" in query
        or "कैसे ठीक" in query
        or "कशी सोडवू" in query
    )

    if is_documents_needed or is_missing_document:
        if not current_user.vendor_id:
            return {"reply": "[MOCK AI] You do not have a registered vendor profile yet."}
            
        bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
        if not bids:
            return {"reply": "[MOCK AI] You have not submitted any bids yet, so there are no required documents."}
            
        reply = "[MOCK AI] Here are the required documents for your active bids:\n\n" if is_documents_needed else "[MOCK AI] Missing documents in your active bids:\n\n"
        for bid in bids:
            tender = bid.tender
            if not tender: continue
            
            reqs = tender.requirements
            docs = {doc.document_type.upper() for doc in bid.documents}
            
            missing = [r.document_type.upper() for r in reqs if r.is_mandatory and r.document_type.upper() not in docs]
            if missing:
                reply += f"- **Bid {bid.bid_id}**: {'Required' if is_documents_needed else 'Missing'} {', '.join(missing)}\n"
            else:
                if is_documents_needed:
                    required = [r.document_type.upper() for r in reqs if r.is_mandatory]
                    reply += f"- **Bid {bid.bid_id}**: Required documents are {', '.join(required) or 'not configured'}.\n"
                else:
                    reply += f"- **Bid {bid.bid_id}**: No mandatory document is missing.\n"
        return {"reply": reply}

    if is_failed_document:
        if not current_user.vendor_id:
            return {"reply": "[MOCK AI] You do not have a registered vendor profile yet."}
        bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
        failed = [
            (bid.bid_id, doc.document_type, doc.detail)
            for bid in bids
            for doc in bid.documents
            if doc.document_status.upper() in {"FAILED", "EXPIRED", "WARNING"}
        ]
        if not failed:
            return {"reply": "[MOCK AI] No failed documents were found in your bids."}
        reply = "[MOCK AI] Documents needing attention:\n\n"
        for bid_id, document_type, detail in failed:
            reply += f"- **Bid {bid_id}**: {document_type} (FAILED)"
            if detail:
                reply += f" — {detail}"
            reply += "\n"
        return {"reply": reply}
        
    if "what is my compliance status" in query:
        if not current_user.vendor_id:
            return {"reply": "[MOCK AI] You do not have a registered vendor profile yet."}
            
        bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
        if not bids:
            return {"reply": "[MOCK AI] You have no active bids."}
            
        reply = "[MOCK AI] Your Compliance Status:\n\n"
        for bid in bids:
            score = getattr(bid, 'compliance_score', 0.0) or 0.0
            reply += f"- **Bid {bid.bid_id}**: Status is **{bid.status}**, Risk Level is **{bid.risk_level}**, Compliance Score is **{score:.1f}%**.\n"
        return {"reply": reply}
        
    if is_flagged_document:
        if not current_user.vendor_id:
            return {"reply": "[MOCK AI] You do not have a registered vendor profile yet."}
            
        bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id, Bid.risk_level.in_(["HIGH", "CRITICAL"])).all()
        if not bids:
            return {"reply": "[MOCK AI] Good news! None of your bids are currently flagged with HIGH or CRITICAL risk."}
            
        reply = "[MOCK AI] Your flagged bids:\n\n"
        for bid in bids:
            failed_rules = [
                r for r in bid.rule_results
                if getattr(r, "result", "").upper() not in {"PASS", "NOT_APPLICABLE", "PENDING"}
            ]
            failed_verifs = [v for v in bid.verifications if not getattr(v, "verified", False)]
            
            reply += f"- **Bid {bid.bid_id}** is flagged ({bid.risk_level} Risk).\n"
            if failed_rules:
                reply += "  Failed Rules:\n"
                for r in failed_rules:
                    finding = getattr(r, "finding", None) or f"Rule {getattr(r, 'rule_id', 'unknown')} failed."
                    reply += f"    * {getattr(r, 'document_type', 'Rule')}: {finding}\n"
            if failed_verifs:
                reply += "  Failed Verifications:\n"
                for v in failed_verifs:
                    reply += f"    * {v.document_type} from {v.source}\n"
        return {"reply": reply}

    if is_fix_request:
        if not current_user.vendor_id:
            return {"reply": "[MOCK AI] You do not have a registered vendor profile yet."}
        bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
        if not bids:
            return {"reply": "[MOCK AI] You have no active bids with remediation information."}
        reply = "[MOCK AI] Recommended next steps:\n\n"
        found = False
        for bid in bids:
            failed_rules = [r for r in bid.rule_results if getattr(r, "result", "").upper() == "FAIL"]
            failed_verifs = [v for v in bid.verifications if not getattr(v, "verified", False)]
            if not failed_rules and not failed_verifs:
                continue
            found = True
            reply += f"- **Bid {bid.bid_id}**:\n"
            for rule in failed_rules:
                action = getattr(rule, "recommended_action", None) or getattr(rule, "finding", None)
                if action:
                    reply += f"  * {getattr(rule, 'document_type', 'Compliance')}: {action}\n"
            for verification in failed_verifs:
                detail = (verification.raw_response or {}).get("detail") if verification.raw_response else None
                if detail:
                    reply += f"  * {verification.document_type}: {detail}\n"
        if not found:
            return {"reply": "[MOCK AI] No current remediation issue was found for your bids."}
        return {"reply": reply}

    if any(term in query for term in ("approve my bid", "reject my bid", "approve", "reject", "मंजूर", "नाकार")):
        return {
            "reply": "[MOCK AI] I cannot approve or reject a bid. Compliance results are advisory; an authorized procurement officer makes the final decision."
        }

    if "do i have any alerts" in query:
        alerts = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).order_by(Notification.created_at.desc()).limit(5).all()
        if not alerts:
            return {"reply": "[MOCK AI] You have no unread alerts at this time."}
            
        reply = "[MOCK AI] Your recent unread alerts:\n\n"
        for alert in alerts:
            reply += f"- **{alert.title}**: {alert.message}\n"
        return {"reply": reply}

    return {"reply": "[MOCK AI] I can help you with your compliance status. Try asking: 'What documents am I missing?', 'What is my compliance status?', 'Why is my bid flagged?', or 'Do I have any alerts?'"}
