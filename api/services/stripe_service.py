import os
import time
import logging
from typing import Dict, Any, Optional
import stripe

from core.config import get_env

logger = logging.getLogger(__name__)

_PRICES_CACHE: Dict[str, Any] = {}
_CACHE_TTL_SECONDS = 600


def _is_placeholder_key(val: str) -> bool:
    return not val or "your_" in val or "price_your" in val or "sk_test_your" in val


def get_stripe_client():
    secret_key = get_env("STRIPE_SECRET_KEY")
    if _is_placeholder_key(secret_key):
        return None
    stripe.api_key = secret_key
    return stripe


def _resolve_price_id(client, identifier: str) -> str:
    if identifier and identifier.startswith("prod_"):
        prices = client.Price.list(product=identifier, active=True, limit=1)
        if prices.data:
            return prices.data[0].id
    return identifier


def get_bundle_prices() -> Dict[str, Any]:
    global _PRICES_CACHE
    now = time.time()

    if _PRICES_CACHE and (now - _PRICES_CACHE.get("_timestamp", 0) < _CACHE_TTL_SECONDS):
        return _PRICES_CACHE["data"]

    client = get_stripe_client()
    price_five_id = get_env("STRIPE_PRICE_FIVE")
    price_ten_id = get_env("STRIPE_PRICE_TEN")

    if not client or _is_placeholder_key(price_five_id) or _is_placeholder_key(price_ten_id):
        raise ValueError("Stripe credentials or price IDs are not configured in the environment file.")

    try:
        price_five_id = _resolve_price_id(client, price_five_id)
        price_ten_id = _resolve_price_id(client, price_ten_id)
        price_five = client.Price.retrieve(price_five_id)
        price_ten = client.Price.retrieve(price_ten_id)

        amount_five = (price_five.unit_amount or 0) / 100
        amount_ten = (price_ten.unit_amount or 0) / 100
        currency = (price_five.currency or "sar").upper()

        data = {
            "five": {
                "price_id": price_five_id,
                "amount": amount_five,
                "currency": currency,
                "formatted": f"{currency} {amount_five:,.0f}",
                "perClassFormatted": f"{currency} {amount_five / 5:,.0f} PER CLASS"
            },
            "ten": {
                "price_id": price_ten_id,
                "amount": amount_ten,
                "currency": currency,
                "formatted": f"{currency} {amount_ten:,.0f}",
                "perClassFormatted": f"{currency} {amount_ten / 10:,.0f} PER CLASS"
            }
        }

        _PRICES_CACHE = {"_timestamp": now, "data": data}
        return data

    except Exception as e:
        logger.error(f"Error retrieving prices from Stripe: {str(e)}.")
        if _PRICES_CACHE and "data" in _PRICES_CACHE:
            return _PRICES_CACHE["data"]
        raise RuntimeError(f"Unable to retrieve prices from Stripe: {str(e)}.")


def create_checkout_session(bundle: str) -> str:
    bundle_key = (bundle or "").lower().strip()
    if bundle_key not in {"five", "ten"}:
        raise ValueError(f"Invalid bundle: '{bundle}'. Allowed options: 'five' or 'ten'.")

    client = get_stripe_client()
    price_id = get_env(f"STRIPE_PRICE_{bundle_key.upper()}")

    if not client or _is_placeholder_key(price_id):
        raise ValueError("Stripe credentials or price IDs are not configured in the environment file.")

    domain = get_env("DOMAIN", "http://localhost:8000").rstrip("/")
    price_id = _resolve_price_id(client, price_id)

    try:
        session = client.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            success_url=f"{domain}/?status=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/?status=cancelled",
            metadata={
                "bundle": bundle_key,
                "classes": 5 if bundle_key == "five" else 10
            }
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}.")
        raise RuntimeError(f"Payment gateway error: {e.user_message or str(e)}.")
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {str(e)}.")
        raise
