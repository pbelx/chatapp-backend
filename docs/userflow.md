# User Flow

## 1. Registration

```
User visits app
    │
    ▼
POST /api/v1/auth/register
{ username, email, password }
    │
    ├── username or email already taken → 400 Bad Request
    │
    └── success → 201 Created { id, username, email, ... }
```

---

## 2. Login

```
User submits credentials
    │
    ▼
POST /api/v1/auth/login
{ username, password }
    │
    ├── invalid credentials → 401 Unauthorized
    │
    └── success → 200 OK { access_token, token_type: "bearer" }
                              │
                              └── store token client-side
```

---

## 3. Authenticated Requests (REST)

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

### View own profile
```
GET /api/v1/users/me
    │
    ├── missing/invalid token → 401
    └── success → { id, username, email, is_active, created_at }
```

### Send a direct message
```
POST /api/v1/messages/dm
{ recipient_id, content }
    │
    ├── recipient not found → 404
    └── success → 201 { id, sender_id, recipient_id, content, created_at }
                         │
                         └── recipient receives message via WebSocket (if online)
```

### Fetch DM history with a user
```
GET /api/v1/messages/dm/{user_id}?limit=50&offset=0
    │
    └── success → [ ...messages ordered by newest first ]
```

### List conversations
```
GET /api/v1/messages/conversations
    │
    └── success → [ { user_id, username, last_message, last_at }, ... ]
```

---

## 4. Real-time Messaging (WebSocket)

```
Client connects
    │
    ▼
ws://host/ws/chat?token=<access_token>
    │
    ├── invalid/missing token → connection closed (code 4001)
    │
    └── connected
            │
            ▼
    Client sends JSON:
    { "recipient_id": "<uuid>", "content": "Hello!" }
            │
            ├── missing fields → { "error": "..." } (connection stays open)
            │
            └── success:
                    ├── message saved to DB
                    ├── delivered to recipient (if online)
                    └── echoed back to sender

    Received message shape:
    {
      "id": "<uuid>",
      "sender_id": "<uuid>",
      "sender_username": "alice",
      "recipient_id": "<uuid>",
      "content": "Hello!",
      "created_at": "2026-02-25T12:00:00+00:00"
    }
```

---

## 5. Full Example Flow (Alice → Bob)

```
1. Alice registers        POST /auth/register
2. Bob registers          POST /auth/register
3. Alice logs in          POST /auth/login  →  alice_token
4. Bob logs in            POST /auth/login  →  bob_token

5. Bob connects WS        ws/chat?token=bob_token
6. Alice connects WS      ws/chat?token=alice_token

7. Alice sends via WS     { recipient_id: bob_id, content: "Hey Bob!" }
        │
        ├── Bob receives message instantly (WebSocket)
        └── Alice receives echo (WebSocket)

8. Bob replies via WS     { recipient_id: alice_id, content: "Hey Alice!" }

9. Alice fetches history  GET /messages/dm/{bob_id}
10. Alice lists convos    GET /messages/conversations
```

---

## 6. Error Reference

| Code | Meaning |
|------|---------|
| 400 | Username or email already taken |
| 401 | Invalid credentials / expired token |
| 404 | Recipient user not found |
| 4001 | WebSocket closed — invalid token |
