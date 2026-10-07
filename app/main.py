"""
Coordinator Application (FastAPI + IAP)
Project 1.27 New Ground Mentoring
"""
import os
import yaml
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.state import app_state

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

app = FastAPI(title="New Ground Match Agent Coordinator")

# Mount Static assets
app.mount("/ui", StaticFiles(directory=os.path.join(PROJECT_ROOT, "ui")), name="ui")

# Template engine
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Import and include portal routes for seamless local dev & testing
from portal.main import (
    mentor_response_page,
    mentor_submit_response,
    mentee_response_page,
    mentee_submit_response
)

app.add_api_route("/m/{token}", mentor_response_page, methods=["GET"], response_class=HTMLResponse)
app.add_api_route("/m/respond", mentor_submit_response, methods=["POST"], response_class=HTMLResponse)
app.add_api_route("/o/{token}", mentee_response_page, methods=["GET"], response_class=HTMLResponse)
app.add_api_route("/o/respond", mentee_submit_response, methods=["POST"], response_class=HTMLResponse)


# Load allowed coordinators
ACCESS_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "access.yaml")
ALLOWED_COORDINATORS = ["mgomez@project127.org", "adudrey@project127.org", "akuykendall@project127.org"]
if os.path.exists(ACCESS_CONFIG_PATH):
    with open(ACCESS_CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
        ALLOWED_COORDINATORS = cfg.get("coordinators", ALLOWED_COORDINATORS)

def get_current_user(request: Request) -> str:
    """Extracts and verifies authenticated IAP user, or falls back to demo default in local mode."""
    iap_header = request.headers.get("X-Goog-Authenticated-User-Email", "")
    if iap_header:
        user_email = iap_header.replace("accounts.google.com:", "").strip()
        if user_email not in ALLOWED_COORDINATORS:
            raise HTTPException(status_code=403, detail="Forbidden: User not authorized in config/access.yaml")
        return user_email
    return "mgomez@project127.org"

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "coordinator-app", "mentors": len(app_state.mentors), "mentees": len(app_state.mentees)}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    pipeline = {
        "intake": [m for m in app_state.mentees.values() if m.get("status") in ["intake", "needs_review"]],
        "proposed": [m for m in app_state.mentees.values() if m.get("status") == "proposed"],
        "mentor_review": [m for m in app_state.mentees.values() if m.get("status") == "mentor_review"],
        "ready_to_offer": [m for m in app_state.mentees.values() if m.get("status") == "ready_to_offer"],
        "offer_sent": [m for m in app_state.mentees.values() if m.get("status") == "offer_sent"],
        "mentee_selected": [m for m in app_state.mentees.values() if m.get("status") == "mentee_selected"],
        "matched": [m for m in app_state.mentees.values() if m.get("status") == "matched"],
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "pipeline": pipeline,
            "mentees": list(app_state.mentees.values()),
            "mentors_count": len(app_state.mentors),
            "outbox_count": len(app_state.outbox),
            "user": user
        }
    )

@app.get("/mentors", response_class=HTMLResponse)
async def view_mentors(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="mentors.html",
        context={
            "mentors": list(app_state.mentors.values()),
            "mentors_count": len(app_state.mentors),
            "outbox_count": len(app_state.outbox),
            "user": user
        }
    )

@app.get("/match/{mentee_id}")
async def trigger_match(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    proposal = app_state.run_matching(mentee_id, user)
    return RedirectResponse(f"/proposal/{mentee_id}", status_code=303)

@app.get("/proposal/{mentee_id}", response_class=HTMLResponse)
async def view_proposal(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    mentee = app_state.mentees.get(mentee_id)
    props = [p for p in app_state.proposals.values() if p["mentee_id"] == mentee_id]
    if not props:
        return RedirectResponse("/", status_code=303)
    proposal = props[-1]
    return templates.TemplateResponse(
        request=request,
        name="proposal.html",
        context={
            "mentee": mentee,
            "proposal": proposal,
            "user": user
        }
    )

@app.post("/select-3", response_class=HTMLResponse)
async def select_3(request: Request, proposal_id: str = Form(...), mentor_ids: list[str] = Form(...), user: str = Depends(get_current_user)):
    if len(mentor_ids) != 3:
        raise HTTPException(status_code=400, detail="Must select exactly 3 mentors.")
    selection = app_state.select_3_mentors(proposal_id, mentor_ids, user)
    return templates.TemplateResponse(
        request=request,
        name="drafts.html",
        context={
            "selection": selection,
            "user": user
        }
    )

@app.post("/approve-send-invites")
async def approve_send_invites(selection_id: str = Form(...), user: str = Depends(get_current_user)):
    app_state.approve_and_send_invitations(selection_id, user)
    selection = app_state.selections[selection_id]
    return RedirectResponse(f"/tracker/{selection['mentee_id']}", status_code=303)

@app.get("/tracker/{mentee_id}", response_class=HTMLResponse)
async def view_tracker(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    mentee = app_state.mentees.get(mentee_id)
    invs = [inv for inv in app_state.invitations.values() if inv["mentee_id"] == mentee_id]
    accepted_count = sum(1 for inv in invs if inv["status"] == "accepted")
    has_declines = any(inv["status"] == "declined" for inv in invs)

    # Candidate #4 backfill if available
    backfill_mentor = None
    props = [p for p in app_state.proposals.values() if p["mentee_id"] == mentee_id]
    if props and len(props[-1]["top_5"]) >= 4:
        cand_4 = props[-1]["top_5"][3]
        if cand_4["mentor_id"] not in [i["mentor_id"] for i in invs]:
            backfill_mentor = cand_4["mentor_obj"]

    return templates.TemplateResponse(
        request=request,
        name="tracker.html",
        context={
            "mentee": mentee,
            "invitations": invs,
            "accepted_count": accepted_count,
            "has_declines": has_declines,
            "backfill_mentor": backfill_mentor,
            "user": user
        }
    )

@app.get("/prepare-offer/{mentee_id}", response_class=HTMLResponse)
async def prepare_offer_view(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    offer = app_state.prepare_mentee_offer(mentee_id, user)
    mentee = app_state.mentees.get(mentee_id)
    return templates.TemplateResponse(
        request=request,
        name="offer_review.html",
        context={
            "mentee": mentee,
            "offer": offer,
            "user": user
        }
    )

@app.post("/approve-send-offer")
async def approve_send_offer(offer_id: str = Form(...), user: str = Depends(get_current_user)):
    app_state.approve_and_send_offer(offer_id, user)
    return RedirectResponse("/", status_code=303)

@app.get("/portal-preview/{mentee_id}")
async def portal_preview(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    offers = [o for o in app_state.offers.values() if o.get("mentee_id") == mentee_id]
    if not offers:
        mentee = app_state.mentees.get(mentee_id)
        name = f"{mentee['first_name']} {mentee['last_initial']}." if mentee else mentee_id
        raise HTTPException(
            status_code=404,
            detail=f"No active offer found for mentee {name}. Please prepare and send an offer first from the Coordinator Pipeline."
        )
    latest_offer = offers[-1]
    return RedirectResponse(latest_offer["portal_url"], status_code=303)


@app.get("/confirm-match/{mentee_id}", response_class=HTMLResponse)
async def confirm_match_view(mentee_id: str, request: Request, user: str = Depends(get_current_user)):
    mentee = app_state.mentees.get(mentee_id)
    chosen_mentor_id = mentee.get("selected_mentor_id")
    chosen_mentor = app_state.mentors.get(chosen_mentor_id)
    return templates.TemplateResponse(
        request=request,
        name="confirm_match.html",
        context={
            "mentee": mentee,
            "chosen_mentor": chosen_mentor,
            "user": user
        }
    )

@app.post("/confirm-match-action")
async def confirm_match_action(mentee_id: str = Form(...), mentor_id: str = Form(...), user: str = Depends(get_current_user)):
    app_state.confirm_match(mentee_id, mentor_id, user)
    return RedirectResponse("/", status_code=303)

@app.get("/outbox", response_class=HTMLResponse)
async def view_outbox(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="outbox.html",
        context={
            "outbox": app_state.outbox,
            "user": user
        }
    )

@app.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "actions": app_state.coordinator_actions,
            "user": user
        }
    )

