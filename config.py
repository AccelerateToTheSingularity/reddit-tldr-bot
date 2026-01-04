"""
Centralized configuration for Reddit TLDR Bot.
"""

# Subreddit configuration
SUBREDDIT = "accelerate"

# TLDR Settings
WORD_THRESHOLD = 270  # Minimum words to trigger TLDR
MAX_TLDR_PER_RUN = 1  # Only 1 TLDR per run (~3 min between TLDRs)
MAX_TLDR_PER_DAY = 40  # Daily cap for TLDRs
MAX_AGE_HOURS = 24  # Only process posts/comments from last 24 hours
COMMENT_MILESTONES = [20, 50, 100]  # Comment thresholds for summaries

# Reply/Conversation Settings
MAX_REPLIES_PER_RUN = 1  # Limit conversational replies per execution (runs are ~3 min apart)
MAX_REPLIES_PER_DAY = 30  # Daily cap for conversational replies
MAX_REPLY_WORDS = 75  # Target max words for conversational replies (keep it tight)
MIN_REPLY_WORDS = 10  # Minimum words for replies (can be very short if appropriate)

# Rate limiting
SAME_USER_COOLDOWN_HOURS = 1  # Don't reply to same user within this window
SAME_USER_REPLIES_BEFORE_COOLDOWN = 2  # Allow this many replies to a user before cooldown kicks in
MOD_CACHE_REFRESH_DAYS = 3  # Refresh moderator list from Reddit every N days

# Summon detection patterns (case-insensitive)
# These patterns will trigger the bot to respond
SUMMON_PATTERNS = [
    # Direct name mentions
    r"\b(hey|hi|hello|yo|sup)\s+(optimist\s*prime)\b",
    r"\boptimist\s*prime\b",
    
    # Bot summons
    r"\b(hey|hi|hello|yo|sup)\s+(bot|ai\s*bot|mod\s*bot|tldr\s*bot)\b",
    r"\b(summon|summoning|calling|paging)\s+(the\s+)?(bot|ai|optimist|optimist\s*prime)\b",
    
    # Mod bot references
    r"\bmod\s*bot\b",
    
    # Direct username mention (Reddit style)
    r"u/Optimist[\-_]?Prime\b",
    
    # Questions directed at the bot
    r"\b(can|could|would|will)\s+(the\s+)?(bot|ai|optimist\s*prime)\b",
    
    # Explicit requests
    r"\b(ask|tell|get)\s+(the\s+)?(bot|ai|optimist)\b",
]

# Patterns that indicate hostile/bad-faith comments to avoid
HOSTILE_PATTERNS = [
    r"\b(stupid|dumb|useless|trash|garbage)\s+(bot|ai)\b",
    r"\bfuck\s*(off|you|this)\b",
    r"\bshut\s*(up|the\s*fuck)\b",
    r"\bkill\s+yourself\b",
    r"\bgo\s+away\b",
    r"\bnobody\s+(asked|cares)\b",
]

# Bot identification patterns (to avoid responding to other bots)
BOT_INDICATORS = [
    r"bot\b",
    r"Bot\b", 
    r"auto[\-_]?mod",
    r"AutoModerator",
]
