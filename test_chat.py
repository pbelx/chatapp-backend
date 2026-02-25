"""
Quick integration test for the chat app.
Usage: python test_chat.py
"""
import asyncio
import json
import httpx
import websockets

BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

ALICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjODA3MWIwOS05ZjJlLTQzNzQtYTExNy1kNGY1YmUyOGVmNzkiLCJleHAiOjE3NzIwMTcwOTh9.TyoJsSCOTiQfNTEspyZ4w_0hlGz-JIN61JOh6kWt0jc"
BOB_TOKEN   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNzdmYWJiZC1hZDU2LTQyMGItOTc1OS03N2E2NTQ4MjI5MDQiLCJleHAiOjE3NzIwMTcxMzV9.BiZttvX3iJ24HvH2rAPh7L3Mhw4vtd3kAH0q2N4UOEM"

ALICE_ID = "c8071b09-9f2e-4374-a117-d4f5be28ef79"
BOB_ID   = "177fabbd-ad56-420b-9759-77a654822904"

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def ok(label, response):
    status = "✓" if response.status_code < 300 else "✗"
    print(f"{status} [{response.status_code}] {label}")
    if response.status_code >= 300:
        print(f"  {response.text}")
    return response

# ── REST Tests ────────────────────────────────────────────────────────────────

def test_rest():
    print("\n── REST ─────────────────────────────────────────")
    with httpx.Client(base_url=BASE) as c:

        # /me
        ok("Alice /me", c.get("/api/v1/users/me", headers=auth(ALICE_TOKEN)))
        ok("Bob   /me", c.get("/api/v1/users/me", headers=auth(BOB_TOKEN)))

        # Alice → Bob
        r = ok("Alice sends DM to Bob", c.post(
            "/api/v1/messages/dm",
            json={"recipient_id": BOB_ID, "content": "Hey Bob, this is Alice!"},
            headers=auth(ALICE_TOKEN),
        ))
        if r.status_code == 201:
            print(f"  message id: {r.json()['id']}")

        # Bob → Alice
        ok("Bob sends DM to Alice", c.post(
            "/api/v1/messages/dm",
            json={"recipient_id": ALICE_ID, "content": "Hey Alice, got your message!"},
            headers=auth(BOB_TOKEN),
        ))

        # DM history (Alice's view)
        r = ok("Alice fetches DM history with Bob", c.get(
            f"/api/v1/messages/dm/{BOB_ID}",
            headers=auth(ALICE_TOKEN),
        ))
        if r.status_code == 200:
            msgs = r.json()
            print(f"  {len(msgs)} message(s) in history")
            for m in msgs:
                who = "Alice" if m["sender_id"] == ALICE_ID else "Bob"
                print(f"    [{who}] {m['content']}")

        # Conversations list
        r = ok("Alice lists conversations", c.get(
            "/api/v1/messages/conversations",
            headers=auth(ALICE_TOKEN),
        ))
        if r.status_code == 200:
            for conv in r.json():
                print(f"  conversation with {conv['username']}: \"{conv['last_message']}\"")

# ── WebSocket Test ────────────────────────────────────────────────────────────

async def test_websocket():
    print("\n── WebSocket ────────────────────────────────────")

    bob_received = asyncio.Event()
    bob_msg = {}

    async def bob_listener():
        async with websockets.connect(f"{WS_BASE}/ws/chat?token={BOB_TOKEN}") as ws:
            print("✓ Bob connected to WebSocket")
            bob_received.clear()
            data = await asyncio.wait_for(ws.recv(), timeout=5)
            bob_msg.update(json.loads(data))
            bob_received.set()

    async def alice_sender():
        async with websockets.connect(f"{WS_BASE}/ws/chat?token={ALICE_TOKEN}") as ws:
            print("✓ Alice connected to WebSocket")
            await asyncio.sleep(0.2)  # let Bob connect first
            payload = {"recipient_id": BOB_ID, "content": "Real-time hello from Alice!"}
            await ws.send(json.dumps(payload))
            print(f"✓ Alice sent: \"{payload['content']}\"")
            # also receive echo
            echo = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            print(f"✓ Alice got echo: \"{echo['content']}\"")

    bob_task   = asyncio.create_task(bob_listener())
    alice_task = asyncio.create_task(alice_sender())

    await asyncio.gather(bob_task, alice_task)

    if bob_received.is_set():
        print(f"✓ Bob received: \"{bob_msg.get('content')}\" from {bob_msg.get('sender_username')}")
    else:
        print("✗ Bob did not receive message in time")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_rest()
    asyncio.run(test_websocket())
    print("\nDone.")
