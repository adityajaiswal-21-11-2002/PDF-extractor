# Import all models so SQLAlchemy can resolve relationship("User") etc.
from app.models import user  # noqa: F401
from app.models import document  # noqa: F401
from app.models import job  # noqa: F401
from app.models import agent_output  # noqa: F401
from app.models import email_record  # noqa: F401
from app.models import execution_log  # noqa: F401
