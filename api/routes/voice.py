from fastapi import APIRouter
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceIntent(BaseModel):
    raw_text:      str    # text from Web Speech API
    language:      str = "en"


class CleanedIntent(BaseModel):
    cleaned_intent: str
    original_text:  str


def clean_intent(raw_text: str) -> str:
    """
    Cleans browser-transcribed text into
    a clear developer intent.
    """
    fillers = ["um", "uh", "like", "you know", "basically", "so", "please"]
    text    = raw_text.strip()

    for filler in fillers:
        text = text.replace(f" {filler} ", " ")

    return text.strip().capitalize()


@router.post("/process", response_model=CleanedIntent)
async def process_voice_text(intent: VoiceIntent):
    """
    Receives text already transcribed by Web Speech API.
    Cleans and normalizes it.
    Frontend then sends cleaned_intent to /agent/run.
    """
    cleaned = clean_intent(intent.raw_text)

    logger.info(
        "voice_processed",
        original=intent.raw_text,
        cleaned=cleaned
    )

    return CleanedIntent(
        cleaned_intent=intent.original_text,
        original_text=intent.raw_text
    )
