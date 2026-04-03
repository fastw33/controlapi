
# app/core/logger.py
from loguru import logger
import sys, os, logging, uuid, time
from typing import Optional, Set
from fastapi import Request, Response

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_DEFAULT_SILENT_PATHS = {"/health", "/", "/robots.txt", "/favicon.ico"}
_env_silent_paths = {
    path.strip()
    for path in os.getenv("LOG_SILENT_PATHS", "").split(",")
    if path.strip()
}
SILENT_PATHS: Set[str] = _DEFAULT_SILENT_PATHS | _env_silent_paths

# ---------- Loguru base ----------
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)
logger.add(
    os.path.join(LOG_DIR, "app_{time:YYYY-MM-DD}.log"),
    rotation=os.getenv("LOG_ROTATION", "1 week"),
    retention=os.getenv("LOG_RETENTION", "4 weeks"),
    compression=os.getenv("LOG_COMPRESSION", "zip"),
    level=os.getenv("LOG_FILE_LEVEL", "INFO"),
    serialize=os.getenv("LOG_JSON", "0") == "1",
)

# ---------- Interceptor para logging estándar ----------
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = "INFO"
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

def setup_std_logging():
    # Redirige logging estándar a Loguru (uvicorn, sqlalchemy, etc.)
    logging.getLogger().handlers = [InterceptHandler()]
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    # Ajusta niveles si quieres menos ruido:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# ---------- Helpers ----------
def get_client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def extract_user_id(request: Request) -> Optional[str]:
    """La app ya no autentica usuarios, así que no se intenta resolver un user id."""
    return None

# ---------- Middlewares ----------
async def request_logger_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    start = time.time()
    path = request.url.path

    try:
        response: Response = await call_next(request)
    except Exception as e:
        # El handler global en errors.py también loguea, aquí agregamos contexto
        logger.exception(f"[{trace_id}] Unhandled error on {request.method} {path}: {e}")
        raise

    ms = (time.time() - start) * 1000
    ip = get_client_ip(request)
    uid = extract_user_id(request) or "-"
    response.headers["X-Trace-Id"] = trace_id

    if path in SILENT_PATHS:
        return response

    logger.info(f"[{trace_id}] {request.method} {path} "
                f"{response.status_code} {ms:.2f}ms ip={ip} user={uid}")
    return response
