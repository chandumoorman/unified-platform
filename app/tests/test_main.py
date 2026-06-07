def register(client, name, email, password="password123"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def login(client, email, password="password123"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register(client):
    r = register(client, "Alice", "alice@test.com")
    assert r.status_code == 201
    assert r.json()["email"] == "alice@test.com"
    assert "password_hash" not in r.json()


def test_duplicate_email(client):
    register(client, "Bob", "bob@test.com")
    r = register(client, "Bob", "bob@test.com")
    assert r.status_code == 400


def test_login(client):
    register(client, "Carol", "carol@test.com")
    r = client.post("/auth/login", json={"email": "carol@test.com", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_wrong_password(client):
    register(client, "Dave", "dave@test.com")
    r = client.post("/auth/login", json={"email": "dave@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_without_token(client):
    assert client.get("/users/me").status_code == 403


# ── Wallet ────────────────────────────────────────────────────────────────────

def test_wallet_created_on_register(client):
    register(client, "Eve", "eve@test.com")
    token = login(client, "eve@test.com")
    r = client.get("/wallet/", headers=auth(token))
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 0.0


def test_add_money(client):
    register(client, "Frank", "frank@test.com")
    token = login(client, "frank@test.com")
    r = client.post("/wallet/add-money", json={"amount": "500"}, headers=auth(token))
    assert r.status_code == 200
    assert float(r.json()["balance"]) == 500.0


def test_transfer(client):
    register(client, "Grace", "grace@test.com")
    register(client, "Heidi", "heidi@test.com")
    token_g = login(client, "grace@test.com")
    token_h = login(client, "heidi@test.com")

    heidi_id = client.get("/users/me", headers=auth(token_h)).json()["id"]
    client.post("/wallet/add-money", json={"amount": "1000"}, headers=auth(token_g))

    r = client.post("/wallet/transfer", json={"receiver_id": heidi_id, "amount": "300"}, headers=auth(token_g))
    assert r.status_code == 201

    balance = client.get("/wallet/", headers=auth(token_g)).json()["balance"]
    assert float(balance) == 700.0


def test_insufficient_balance(client):
    register(client, "Ivan", "ivan@test.com")
    register(client, "Judy", "judy@test.com")
    token_i = login(client, "ivan@test.com")
    judy_id = client.get("/users/me", headers=auth(login(client, "judy@test.com"))).json()["id"]

    r = client.post("/wallet/transfer", json={"receiver_id": judy_id, "amount": "9999"}, headers=auth(token_i))
    assert r.status_code == 400
    assert "Insufficient" in r.json()["detail"]


def test_self_transfer(client):
    register(client, "Karl", "karl@test.com")
    token = login(client, "karl@test.com")
    me = client.get("/users/me", headers=auth(token)).json()["id"]
    client.post("/wallet/add-money", json={"amount": "100"}, headers=auth(token))

    r = client.post("/wallet/transfer", json={"receiver_id": me, "amount": "50"}, headers=auth(token))
    assert r.status_code == 400
