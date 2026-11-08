import pytest
import os
import sys
import hmac
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure task1-usage-metering root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure test settings
os.environ["ENVIRONMENT"] = "testing"
os.environ["WEBHOOK_SECRET"] = "callzo_test_secret_change_me"
os.environ["API_KEY"] = "test_admin_api_key_123"

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.account import Account
from app.models.usage_cap import UsageCap

# In-memory SQLite for instantaneous, isolated test runs
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed baseline test accounts
    acc1 = Account(
        id="acc_test_01",
        name="Test Account 01",
        email="test01@example.com",
        country="US",
        plan="pro",
        status="active"
    )
    cap1 = UsageCap(
        account_id="acc_test_01",
        monthly_minutes_cap=100,
        monthly_cost_cents_cap=5000,
        is_hard_cap=True
    )
    session.add(acc1)
    session.add(cap1)
    session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test_admin_api_key_123"}


@pytest.fixture
def make_signature():
    def _sign(payload_bytes: bytes, secret: str = "callzo_test_secret_change_me") -> str:
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return _sign
