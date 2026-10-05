import logging
import os
import re
import sys
from typing import List, Union

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS

from core.config import get_env
from core.responses import success, created, error, internal_error
from services.stripe_service import get_bundle_prices, create_checkout_session
from services.email_service import send_lead_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reps-api")


def get_allowed_origins() -> List[Union[str, re.Pattern]]:
    origins: List[Union[str, re.Pattern]] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5000",
        "http://localhost:3000",
        "https://reps-fitness.com",
        "https://www.reps-fitness.com",
        re.compile(r"^https://.*\.vercel\.app$")
    ]
    cors_env = get_env("CORS_ORIGIN", "")
    if cors_env:
        for item in cors_env.split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
    return origins


def create_app() -> Flask:
    app = Flask(__name__)

    allowed_origins = get_allowed_origins()
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "reps-api"}), 200

    @app.route("/api/prices", methods=["GET"])
    def list_prices():
        try:
            prices = get_bundle_prices()
            return success(data=prices, message="Prices retrieved successfully.")
        except Exception as e:
            logger.error(f"Error fetching prices: {str(e)}.")
            return error(str(e), status_code=500)

    @app.route("/api/create-checkout-session", methods=["POST"])
    def create_session():
        payload = request.get_json(silent=True)
        if payload is None or not isinstance(payload, dict):
            return error("Request body must be valid JSON.", status_code=400)

        bundle = payload.get("bundle")
        if not bundle:
            return error("The 'bundle' field is required ('five' or 'ten').", status_code=400)

        try:
            checkout_url = create_checkout_session(bundle)
            return created(data={"url": checkout_url}, message="Checkout session created successfully.")
        except ValueError as e:
            return error(str(e), status_code=400)
        except RuntimeError as e:
            return error(str(e), status_code=502)
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}.")
            return internal_error("Failed to initialize Stripe checkout.")

    @app.route("/api/send-email", methods=["POST"])
    def send_email():
        payload = request.get_json(silent=True)
        if payload is None or not isinstance(payload, dict):
            return error("Request body must be valid JSON.", status_code=400)

        email_address = payload.get("email")
        if not email_address or not isinstance(email_address, str) or not email_address.strip():
            return error("O campo 'email' é obrigatório.", status_code=400)

        try:
            result = send_lead_email(email_address.strip())
            return success(data=result, message="E-mail enviado com sucesso.")
        except ValueError as e:
            return error(str(e), status_code=400)
        except RuntimeError as e:
            return error(str(e), status_code=502)
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}.")
            return internal_error("Falha ao processar o envio de e-mail.")

    @app.errorhandler(404)
    def handle_not_found(e):
        return error("Endpoint not found.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error("HTTP method not allowed for this route.", status_code=405)

    @app.errorhandler(500)
    def handle_internal_error(e):
        return internal_error()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(get_env("PORT", "5000"))
    debug = get_env("FLASK_ENV", "development").lower() == "development"
    logger.info(f"Starting REPS API on port {port} (debug={debug})...")
    app.run(host="0.0.0.0", port=port, debug=debug)
