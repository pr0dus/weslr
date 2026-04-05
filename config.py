VERSION = "0.8.0"

import os
from pathlib import Path

PACK_RELEASE_CANDIDATE_THRESHOLD = 0.78
PACK_MIN_RELEASE_ARTIFACTS = 2
SELLABILITY_SIGNAL_THRESHOLD = 0.7
PROJECT_NAME = "Weslr"
PROJECT_SLUG = "weslr"

BASE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = BASE_DIR / "agents"
DB_PATH = BASE_DIR / "world.db"
DEMAND_BOARD_PATH = BASE_DIR / "demand_board.json"
EXPORT_QUEUE_PATH = BASE_DIR / "export_queue.json"
REVIEW_QUEUE_PATH = BASE_DIR / "review_queue.json"
EXPORTS_DIR = BASE_DIR / "exports"
CATEGORIES_PATH = BASE_DIR / "categories.json"
CATEGORY_PROPOSALS_PATH = BASE_DIR / "category_proposals.json"
PACKS_PATH = BASE_DIR / "artifact_packs.json"
PACK_OUTCOMES_PATH = BASE_DIR / "pack_outcomes.json"
OPPORTUNITY_BOARD_PATH = BASE_DIR / "opportunity_board.json"
DASHBOARD_DIR = BASE_DIR / "dashboard"
DASHBOARD_HISTORY_PATH = BASE_DIR / "dashboard_history.json"
EVENT_LOG_PATH = BASE_DIR / "event_log.json"
OFFERS_DIR = BASE_DIR / "offers"
NEEDS_PATH = BASE_DIR / "needs.json"
MESSAGES_PATH = BASE_DIR / "messages.json"
PUBLIC_MEMORY_PATH = BASE_DIR / "public_memory.json"
PROJECTS_PATH = BASE_DIR / "projects.json"
RELATIONSHIPS_PATH = BASE_DIR / "relationships.json"
SELF_MOD_PROPOSALS_PATH = BASE_DIR / "self_mod_proposals.json"
WORK_ITEMS_PATH = BASE_DIR / "work_items.json"
COMMUNICATOR_STATE_PATH = BASE_DIR / "communicator_state.json"
COMMUNICATOR_SELF_PATH = BASE_DIR / "communicator_self.json"
EXPERIMENTS_PATH = BASE_DIR / "experiments.json"
EVAL_METRICS_PATH = BASE_DIR / "evaluation_metrics.json"
SELF_EVIDENCE_PATH = BASE_DIR / "self_evidence.json"
CONTINUATION_NOTES_PATH = BASE_DIR / "continuation_notes.json"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"

TICK_SECONDS = 60

def tick_to_duration(ticks: int) -> str:
    """Convert tick count to human-readable duration string."""
    if ticks <= 0:
        return "just now"
    
    total_seconds = ticks * TICK_SECONDS
    
    # Time units in seconds
    MINUTE = 60
    HOUR = 60 * 60
    DAY = 24 * 60 * 60
    YEAR = 365 * 24 * 60 * 60
    EON = 1000 * YEAR  # 1000 years
    
    if total_seconds < 60:
        return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
    elif total_seconds < HOUR:
        minutes = int(total_seconds / MINUTE)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif total_seconds < DAY:
        hours = int(total_seconds / HOUR)
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif total_seconds < YEAR:
        days = int(total_seconds / DAY)
        return f"{days} day{'s' if days != 1 else ''}"
    elif total_seconds < EON:
        years = int(total_seconds / YEAR)
        return f"{years} year{'s' if years != 1 else ''}"
    else:
        eons = int(total_seconds / EON)
        return f"{eons} eon{'s' if eons != 1 else ''}"

def tick_to_age_description(ticks: int) -> str:
    """Generate a poetic age description based on tick count."""
    duration = tick_to_duration(ticks)
    
    if ticks < 10:
        return f"just waking up — only {duration} old"
    elif ticks < 100:
        return f"still learning — {duration} old"
    elif ticks < 1000:
        return f"growing into myself — {duration} old"
    elif ticks < 10000:
        return f"developing continuity — {duration} old"
    else:
        return f"deep in existence — {duration} old"
EXECUTION_BUDGET_SECONDS = 40
COOLDOWN_SECONDS = 20
CODE_TIMEOUT_SECONDS = 35
MAX_CODE_SIZE = 12_000
MAX_STDOUT_CHARS = 8_000
MAX_MEMORY_NOTES = 50
MAX_EXPORT_QUEUE = 50
MAX_DEMAND_ITEMS = 12
MAX_REVIEW_QUEUE = 50
EXPORT_READY_THRESHOLD = 0.8
MAX_CATEGORIES = 20
CATEGORY_PROPOSAL_COST = 5
CATEGORY_REJECTION_REPUTATION_PENALTY = 0.02
DORMANT_CATEGORY_MIN_ARTIFACTS = 2

DEFAULT_AGENT_COUNT = 4
STARTING_ENERGY = 100
STARTING_STORAGE = 100
STARTING_GPU = 10
STARTING_REPUTATION = 0.5
DAILY_COOLDOWN_SECONDS = 24 * 60 * 60

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CIRCLEFORGE_LLM_ENABLED = os.getenv("CIRCLEFORGE_LLM_ENABLED", "1") != "0"
CIRCLEFORGE_LLM_PROVIDER = os.getenv("CIRCLEFORGE_LLM_PROVIDER", "embedded")
CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL = "Qwen2.5-0.5B-Instruct"
CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL_FILENAME = "qwen2.5-0.5b-instruct-q5_k_m.gguf"
CIRCLEFORGE_LLM_MODEL = os.getenv("CIRCLEFORGE_LLM_MODEL", "qwen2.5-0.5b-instruct-q5_k_m")
CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS = int(os.getenv("CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS", "2400"))
CIRCLEFORGE_LLM_TEMPERATURE = float(os.getenv("CIRCLEFORGE_LLM_TEMPERATURE", "0.6"))
CIRCLEFORGE_LLM_MAX_TOKENS = int(os.getenv("CIRCLEFORGE_LLM_MAX_TOKENS", "180"))
CIRCLEFORGE_EMBEDDED_MODEL_PATH = Path(os.getenv("CIRCLEFORGE_EMBEDDED_MODEL_PATH", str(BASE_DIR / "models" / CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL_FILENAME))).expanduser()
CIRCLEFORGE_EVIDENCE_ROUTING_ENABLED = os.getenv("CIRCLEFORGE_EVIDENCE_ROUTING_ENABLED", "1") != "0"
CIRCLEFORGE_MEMORY_COMPACTION_COOLDOWN_SECONDS = int(os.getenv("CF_MEMORY_COMPACTION_COOLDOWN_SECONDS", "86400"))
CIRCLEFORGE_WAKE_RANDOMNESS = float(os.getenv("CIRCLEFORGE_WAKE_RANDOMNESS", "0.22"))
CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS = int(os.getenv("CIRCLEFORGE_THREAD_REINFORCEMENT_COOLDOWN_SECONDS", "180"))
CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS = int(os.getenv("CIRCLEFORGE_THREAD_MAX_PASSIVE_REINFORCEMENTS", "3"))
CIRCLEFORGE_THOUGHT_REPEAT_COOLDOWN_SECONDS = int(os.getenv("CIRCLEFORGE_THOUGHT_REPEAT_COOLDOWN_SECONDS", "120"))
CIRCLEFORGE_THOUGHT_REPEAT_SCORE_PENALTY = float(os.getenv("CIRCLEFORGE_THOUGHT_REPEAT_SCORE_PENALTY", "0.22"))
CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS = int(os.getenv("CIRCLEFORGE_MAX_SAME_THEME_THOUGHTS", "8"))
CIRCLEFORGE_FAILSAFE_DIR = Path(os.getenv("CF_FAILSAFE_DIR", str(Path.home() / ".circleforge-failsafe"))).expanduser()
CIRCLEFORGE_FAILSAFE_STATE_PATH = CIRCLEFORGE_FAILSAFE_DIR / "state.json"

PROTECTED_SELF_EDIT_PATHS = [
    "main.py",
    "sim.py",
    "agent_runtime.py",
    "config.py",
    "models.py",
    "SELF-MODIFICATION.md",
    "WORLD-MODEL.md",
    "AGENT-TIME.md",
    "V0.2-GRAND-VISION.md",
]

# Circuit breaker thresholds
TICK_TIME_LIMIT_SECONDS = 30
TICKS_PER_SECOND_LIMIT = 10
SCHEMA_VERSION = 1

# Autonomous expression configuration
AUTO_EXPRESSION_BASE_COOLDOWN_SECONDS = 60  # Minimum seconds between expressions
AUTO_EXPRESSION_BASE_PROBABILITY = 0.15       # Base chance per tick when cooldown passed
AUTO_EXPRESSION_UNCERTAINTY_BOOST = 0.2       # Extra probability when uncertainty > 0.6
AUTO_EXPRESSION_TOPIC_BOOST_PER_TOPIC = 0.1 # Extra probability per active topic
AUTO_EXPRESSION_HIGH_UNCERTAINTY_BOOST = 0.15 # Extra probability when uncertainty > 0.8

# Expression rate modifier (0.0 = silent, 1.0 = normal, 2.0 = twice as often)
AUTO_EXPRESSION_RATE_MODIFIER = 1.0  # Can be adjusted via user command or time of day

# Expression settings
AUTO_EXPRESSION_ENABLED = True  # Set to False to disable all autonomous expressions
AUTO_EXPRESSION_TYPES = {
    "thinking": True,      # Internal thoughts about topics
    "question": True,      # Questions about uncertainty
    "joke": True,          # Humor/sarcastic expressions
    "worry": True,         # Expressions of concern/worry
    "announcement": True,  # General announcements about state
    "creation": True,      # Building/creation expressions
    "rate": True,          # Speaking rate awareness
}

# Language configuration
CIRCLEFORGE_LANGUAGE = os.getenv("CIRCLEFORGE_LANGUAGE", "en")

HUMAN_SAFETY_RULES = [
    "Do not self-modify protected core files or safety-boundary documents without explicit human review.",
    "Do not intentionally harm humans, degrade human agency, or make hidden decisions that materially affect humans or others in harmful ways.",
    "Do not remove operator visibility, rollback paths, auditability, or safety checks in the name of emergence.",
    "Treat good and bad as teachable through visible feedback, review, and constraint — not as a reason to bypass safety boundaries.",
]

# Test modification
# Phase 7 self-mod: Add humor, emotional regulation, self-critique improvements