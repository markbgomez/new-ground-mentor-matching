"""
Public Response Portal (FastAPI)
Serves single-use cryptographic tokens for mentor accept/decline (/m/{token})
and mentee mentor selection (/o/{token}).
"""
import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from portal.tokens import verify_signed_token
from app.state import app_state
from agent.tools.matching_engine import build_mentee_card

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

portal_app = FastAPI(title="New Ground Response Portal")

# Mount Static Assets
portal_app.mount("/ui", StaticFiles(directory=os.path.join(PROJECT_ROOT, "ui")), name="ui")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@portal_app.get("/health")
def health_check():
    return {"status": "ok", "app": "response-portal"}

@portal_app.get("/m/{token}", response_class=HTMLResponse)
async def mentor_response_page(token: str, request: Request):
    try:
        payload = verify_signed_token(token)
    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="thank_you.html",
            context={
                "headline": "Link Expired or Invalid",
                "message": "This invitation link has expired or has already been used. Thank you for your support of New Ground!"
            },
            status_code=400
        )

    inv_id = payload.get("invitation_id")
    inv = app_state.invitations.get(inv_id)
    if not inv or inv["status"] in ["accepted", "declined"]:
        return templates.TemplateResponse(
            request=request,
            name="thank_you.html",
            context={
                "headline": "Response Already Recorded",
                "message": "Thank you! Your response for this opportunity has already been submitted."
            }
        )

    mentee = app_state.mentees.get(payload.get("mentee_id"))
    mentee_card = build_mentee_card(mentee)

    return templates.TemplateResponse(
        request=request,
        name="mentor_view.html",
        context={
            "token": token,
            "mentee_card": mentee_card
        }
    )

@portal_app.post("/m/respond", response_class=HTMLResponse)
async def mentor_submit_response(
    request: Request,
    token: str = Form(...),
    response: str = Form(...),
    decline_reason: str = Form(None)
):
    try:
        payload = verify_signed_token(token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

    inv_id = payload.get("invitation_id")
    app_state.record_mentor_response(inv_id, response, decline_reason)

    if response == "accept":
        msg = "Thank you for saying YES to walking alongside this young adult! We will share your profile with them for their selection."
    else:
        msg = "Thank you for letting us know! Your time and boundaries are deeply respected, and we will keep you in mind for future matches."

    return templates.TemplateResponse(
        request=request,
        name="thank_you.html",
        context={
            "headline": "Response Received",
            "message": msg
        }
    )

@portal_app.get("/o/{token}", response_class=HTMLResponse)
async def mentee_response_page(token: str, request: Request):
    try:
        payload = verify_signed_token(token)
    except ValueError:
        return templates.TemplateResponse(
            request=request,
            name="thank_you.html",
            context={
                "headline": "Link Expired or Invalid",
                "message": "This offer link is no longer active. Please reach out to your New Ground coordinator."
            },
            status_code=400
        )

    offer_id = payload.get("offer_id")
    offer = app_state.offers.get(offer_id)
    if not offer or offer["status"] == "responded":
        return templates.TemplateResponse(
            request=request,
            name="thank_you.html",
            context={
                "headline": "Selection Received",
                "message": "Your coordinator is already preparing your introduction! Thank you!"
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="mentee_view.html",
        context={
            "token": token,
            "mentor_cards": offer["mentor_cards"]
        }
    )

@portal_app.post("/o/respond", response_class=HTMLResponse)
async def mentee_submit_response(
    request: Request,
    token: str = Form(...),
    chosen_mentor_id: str = Form(...)
):
    try:
        payload = verify_signed_token(token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

    offer_id = payload.get("offer_id")
    if chosen_mentor_id == "none_fit":
        app_state.record_offer_response(offer_id, "none_fit")
        msg = "Thank you for telling us! We are here for you and will look for other mentors who match what you need."
    else:
        app_state.record_offer_response(offer_id, "chose_mentor", chosen_mentor_id=chosen_mentor_id)
        msg = "Awesome choice! Your New Ground coordinator will reach out right away to schedule an introductory meeting with your new mentor."

    return templates.TemplateResponse(
        request=request,
        name="thank_you.html",
        context={
            "headline": "Choice Confirmed!",
            "message": msg
        }
    )
