import asyncio
import json
import redis.asyncio as redis
from app.core.config import get_settings
from app.notifications import send_email, send_sms

settings = get_settings()

CHANNELS = [
    "order.created",
    "order.cancelled",
    "payment.success",
    "payment.failed",
    "inventory.low_stock",
]


def handle_order_created(payload: dict):
    order_id = payload.get("order_id", "unknown")
    user_id = payload.get("user_id", "unknown")
    total = payload.get("total_amount", 0)
    print(f"[NOTIFY] order.created → order={order_id} user={user_id} total=₹{total}")
    send_email(
        to_email=settings.ADMIN_EMAIL,
        subject=f"New Order #{order_id}",
        body=f"<p>Order <b>{order_id}</b> placed by user {user_id}. Total: ₹{total}</p>",
    )


def handle_order_cancelled(payload: dict):
    order_id = payload.get("order_id", "unknown")
    print(f"[NOTIFY] order.cancelled → order={order_id}")
    send_email(
        to_email=settings.ADMIN_EMAIL,
        subject=f"Order Cancelled #{order_id}",
        body=f"<p>Order <b>{order_id}</b> was cancelled.</p>",
    )


def handle_payment_success(payload: dict):
    order_id = payload.get("order_id", "unknown")
    amount = payload.get("amount", 0)
    print(f"[NOTIFY] payment.success → order={order_id} amount=₹{amount}")
    send_email(
        to_email=settings.ADMIN_EMAIL,
        subject=f"Payment Received for Order #{order_id}",
        body=f"<p>Payment of ₹{amount} received for order <b>{order_id}</b>.</p>",
    )


def handle_payment_failed(payload: dict):
    order_id = payload.get("order_id", "unknown")
    print(f"[NOTIFY] payment.failed → order={order_id}")
    send_email(
        to_email=settings.ADMIN_EMAIL,
        subject=f"Payment Failed for Order #{order_id}",
        body=f"<p>Payment failed for order <b>{order_id}</b>. User may retry.</p>",
    )


def handle_inventory_low_stock(payload: dict):
    product_id = payload.get("product_id", "unknown")
    quantity = payload.get("quantity", 0)
    print(f"[NOTIFY] inventory.low_stock → product={product_id} qty={quantity}")
    send_email(
        to_email=settings.ADMIN_EMAIL,
        subject=f"Low Stock Alert: Product {product_id}",
        body=f"<p>Product <b>{product_id}</b> has only {quantity} units left.</p>",
    )


HANDLERS = {
    "order.created": handle_order_created,
    "order.cancelled": handle_order_cancelled,
    "payment.success": handle_payment_success,
    "payment.failed": handle_payment_failed,
    "inventory.low_stock": handle_inventory_low_stock,
}


async def start_consumer():
    print(f"[NOTIFY] Connecting to Redis: {settings.REDIS_URL}")
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(*CHANNELS)
    print(f"[NOTIFY] Subscribed to: {CHANNELS}")

    async for message in pubsub.listen():
        await asyncio.sleep(0)
        if message["type"] != "message":
            continue
        channel = message["channel"]
        try:
            payload = json.loads(message["data"])
        except json.JSONDecodeError:
            print(f"[NOTIFY] Bad JSON on channel {channel}: {message['data']}")
            continue
        handler = HANDLERS.get(channel)
        if handler:
            try:
                handler(payload)
            except Exception as e:
                print(f"[NOTIFY] Handler error on {channel}: {e}")
        else:
            print(f"[NOTIFY] No handler for channel: {channel}")