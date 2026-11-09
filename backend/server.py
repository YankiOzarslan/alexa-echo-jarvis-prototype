import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from . import brain, config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("JarvisServer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Telegram Bot if token is present in .env
    token = config.get_telegram_token()
    tg_task = None
    if token and token != "your_telegram_bot_token_here":
        from . import telegram_bot
        logger.info("🚀 Launching Telegram Jarvis Bot in background...")
        tg_task = asyncio.create_task(telegram_bot.run_telegram_bot())
    else:
        logger.info("ℹ️ TELEGRAM_BOT_TOKEN is empty in .env. Telegram uplink dormant.")
    yield
    # Shutdown
    if tg_task:
        tg_task.cancel()

app = FastAPI(title="Echo Dot & Mobile Jarvis Backend", version="1.0.0", lifespan=lifespan)

def build_alexa_response(speech_text: str, reprompt_text: str = "I am listening, Sir.", should_end_session: bool = False) -> dict:
    """Builds standard Alexa response format with automatic SSML language support."""
    has_ssml = "<lang" in speech_text or "<speak>" in speech_text or "<phoneme" in speech_text or "<emphasis" in speech_text or "<voice" in speech_text or "<prosody" in speech_text
    
    if has_ssml:
        clean_ssml = speech_text.strip()
        if not clean_ssml.startswith("<speak>"):
            clean_ssml = f"<speak>{clean_ssml}</speak>"
        output_speech = {
            "type": "SSML",
            "ssml": clean_ssml
        }
    else:
        output_speech = {
            "type": "PlainText",
            "text": speech_text
        }

    response = {
        "version": "1.0",
        "sessionAttributes": {},
        "response": {
            "outputSpeech": output_speech,
            "shouldEndSession": should_end_session
        }
    }
    if not should_end_session and reprompt_text:
        reprompt_has_ssml = "<lang" in reprompt_text or "<speak>" in reprompt_text
        if reprompt_has_ssml:
            r_ssml = reprompt_text.strip()
            if not r_ssml.startswith("<speak>"):
                r_ssml = f"<speak>{r_ssml}</speak>"
            response["response"]["reprompt"] = {
                "outputSpeech": {"type": "SSML", "ssml": r_ssml}
            }
        else:
            response["response"]["reprompt"] = {
                "outputSpeech": {"type": "PlainText", "text": reprompt_text}
            }
    return response

@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "J.A.R.V.I.S.",
        "ai_provider": config.get_ai_provider(),
        "endpoint": "/alexa"
    }

@app.post("/test")
async def test_jarvis(request: Request):
    """Direct test endpoint for testing Jarvis without Alexa."""
    data = await request.json()
    query = data.get("query", "Hello Jarvis")
    logger.info(f"[TEST QUERY]: {query}")
    answer = await brain.process_user_query(query)
    logger.info(f"[TEST ANSWER]: {answer}")
    return {"query": query, "response": answer}

@app.post("/")
@app.post("/alexa")
async def alexa_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    req_obj = body.get("request", {})
    req_type = req_obj.get("type", "")
    logger.info(f"Received Alexa Request Type: {req_type}")

    # 1. User says "Alexa, open Jarvis"
    if req_type == "LaunchRequest":
        brain.memory.clear()
        welcome = "Jarvis online and at your service, Sir. What are your orders?"
        logger.info(f"[LAUNCH] -> {welcome}")
        return build_alexa_response(
            speech_text=welcome,
            reprompt_text="Still here, Sir. Is there anything else?",
            should_end_session=False
        )

    # 2. User speaks a query or command
    elif req_type == "IntentRequest":
        intent = req_obj.get("intent", {})
        intent_name = intent.get("name", "")
        logger.info(f"Intent name: {intent_name}")

        # Stop / Cancel intents
        if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"]:
            farewell = "Understood, Sir. Systems standing by. Have a pleasant day."
            brain.memory.clear()
            logger.info(f"[STOP] -> {farewell}")
            return build_alexa_response(speech_text=farewell, should_end_session=True)

        if intent_name == "AMAZON.HelpIntent":
            help_text = "I am Jarvis, your personal AI assistant. You can ask me any question, request system diagnostics, or have me control your Mac."
            return build_alexa_response(speech_text=help_text, should_end_session=False)

        # Iconic Daddy's Home Protocol Intent
        if intent_name == "DaddysHomeIntent":
            from . import tools
            await tools.protocol_daddys_home()
            response_text = "Welcome home, Sir. Initializing protocol Back in Black. Volume raised to eighty percent and sound systems engaged."
            return build_alexa_response(
                speech_text=response_text,
                reprompt_text="Ready for further orders, Sir.",
                should_end_session=False
            )

        # Extract user speech
        query_text = ""
        slots = intent.get("slots", {})
        if "query" in slots and "value" in slots["query"]:
            query_text = slots["query"]["value"].strip()
        
        # If fallback intent or empty speech
        if intent_name == "AMAZON.FallbackIntent" or not query_text:
            logger.info(f"[FALLBACK / UNMATCHED] Intent: {intent_name}, Slot value: '{query_text}'")
            
            # Check if Sir is currently in a German tutoring / practice session
            from . import german_tutor
            if brain.is_in_german_session() or german_tutor.is_in_german_session():
                logger.info("🇩🇪 [GERMAN SESSION REPETITION]: User spoke foreign/German phonetics. Evaluating attempt.")
                tutor_reply = await german_tutor.handle_fallback_attempt()
                return build_alexa_response(
                    speech_text=tutor_reply,
                    reprompt_text="I am listening, Sir. Shall we continue our German lesson?",
                    should_end_session=False
                )

            return build_alexa_response(
                speech_text="I didn't quite catch that, Sir. What would you like me to do?",
                reprompt_text="I am standing by, Sir. Please state your order.",
                should_end_session=False
            )

        logger.info(f"[USER SPOKE]: {query_text}")

        # Check for quit, close, and dismissal keywords in speech
        lower_q = query_text.lower()
        quit_keywords = [
            "close", "close jarvis", "quit", "quit jarvis", "stop", "bye", "goodbye",
            "shut down", "power off", "turn off", "exit", "sleep", "cancel", "never mind",
            "dismiss", "dismissed", "that's all", "that is all", "that will be all",
            "nothing else", "no thank you", "kapat", "tamam kapat", "dur", "görüşürüz"
        ]
        if any(w in lower_q for w in quit_keywords) or lower_q in ["no", "nope", "nothing", "none", "hayır", "yok"]:
            farewell = "Powering down, Sir. Have a pleasant day."
            brain.memory.clear()
            from . import german_tutor
            german_tutor.set_german_session(False)
            logger.info(f"[QUIT COMMAND]: '{query_text}' -> Closing Alexa session.")
            return build_alexa_response(speech_text=farewell, should_end_session=True)

        # Query LLM Brain with error safety
        try:
            response_text = await brain.process_user_query(query_text)
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            response_text = f"An error occurred while processing your request, Sir: {str(e)}"

        if not response_text or not response_text.strip():
            response_text = "I apologize, Sir. I was unable to formulate a response to that."

        logger.info(f"[JARVIS REPLIED]: {response_text}")

        return build_alexa_response(
            speech_text=response_text,
            reprompt_text="Is there anything else I can do for you, Sir?",
            should_end_session=False
        )

    # 3. Session ended by Alexa or timeout
    elif req_type == "SessionEndedRequest":
        reason = req_obj.get("reason", "Unknown")
        logger.info(f"Session ended reason: {reason}")
        brain.memory.clear()
        from . import german_tutor
        german_tutor.set_german_session(False)
        return build_alexa_response(speech_text="", should_end_session=True)

    # Fallback
    return build_alexa_response(
        speech_text="I didn't quite catch that, Sir. Could you please repeat?",
        should_end_session=False
    )
