import sys

content_to_append = """

@router.get("/suggested-tenders")
def get_suggested_tenders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "BIDDER":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not current_user.vendor_id:
        return []

    # Get bidder's valid, exact-document verifications
    bids = db.query(Bid).filter(Bid.vendor_id == current_user.vendor_id).all()
    bid_ids = [b.id for b in bids]
    
    if not bid_ids:
        verifications = []
    else:
        verifications = db.query(Verification).filter(
            Verification.bid_id.in_(bid_ids),
            Verification.verified == True,
            Verification.document_id.isnot(None)
        ).all()
        
    verified_doc_types = set()
    for v in verifications:
        verified_doc_types.add(v.document_type.upper())

    # Evaluate active tenders
    tenders = db.query(Tender).all()
    suggestions = []
    
    for t in tenders:
        reqs = t.requirements
        if not reqs:
            continue
            
        satisfied = []
        missing = []
        failed = [] # We'll just define failed as mandatory things not satisfied for this mock view
        manual_review = []
        
        mandatory_count = 0
        satisfied_mandatory_count = 0
        
        for r in reqs:
            rtype = r.document_type.upper()
            if r.is_mandatory:
                mandatory_count += 1
                
            if rtype in verified_doc_types:
                satisfied.append(f"{rtype} Verification")
                if r.is_mandatory:
                    satisfied_mandatory_count += 1
            else:
                if r.is_mandatory:
                    missing.append(f"{rtype} Document")
                    
        # Calculate score deterministically
        if mandatory_count == 0:
            score = 100
        else:
            score = int((satisfied_mandatory_count / mandatory_count) * 100)
            
        # Only suggest if match score is somewhat decent (e.g., > 0)
        # For demo purposes, we can suggest all so they can see why it failed.
        suggestions.append({
            "tender_id": t.id,
            "tender_name": t.title,
            "match_score": score,
            "satisfied_requirements": satisfied,
            "missing_requirements": missing,
            "failed_requirements": failed,
            "manual_review_requirements": manual_review,
            "explanation": f"Based on currently verified documents, you match {score}% of the mandatory requirements."
        })
        
    # Sort by highest score first
    suggestions.sort(key=lambda x: x["match_score"], reverse=True)
    return suggestions
"""

with open('app/api/routes/bidder.py', 'a') as f:
    f.write(content_to_append)

print("Appended suggested-tenders to bidder.py")
