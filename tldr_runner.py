"""
Minimal TLDR Runner for GitHub Actions.
Runs a single check cycle for generating TLDRs on r/accelerate posts.
"""

import os
import sys
import json
import argparse
from datetime import datetime

import praw
import google.generativeai as genai

# Configuration from environment
SUBREDDIT = "accelerate"
WORD_THRESHOLD = 500
MAX_TLDR_PER_RUN = 5  # Don't overwhelm in a single run


def load_state(state_file: str = "data/tldr_state.json") -> dict:
    """Load TLDR state from file."""
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {
        "last_check": None,
        "processed_posts": [],
        "stats": {
            "total_posts_processed": 0,
            "total_tldrs_generated": 0,
            "total_tokens_used": 0,
            "total_cost": 0.0
        }
    }


def save_state(state: dict, state_file: str = "data/tldr_state.json"):
    """Save state to file."""
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def update_stats(stats_file: str = "data/stats.json", tldrs_generated: int = 0, tokens: int = 0, cost: float = 0.0):
    """Update cumulative stats file."""
    stats = {"total_tldrs": 0, "total_tokens": 0, "total_cost": 0.0, "runs": 0, "last_run": None}
    
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        except:
            pass
    
    stats["total_tldrs"] = stats.get("total_tldrs", 0) + tldrs_generated
    stats["total_tokens"] = stats.get("total_tokens", 0) + tokens
    stats["total_cost"] = stats.get("total_cost", 0.0) + cost
    stats["runs"] = stats.get("runs", 0) + 1
    stats["last_run"] = datetime.utcnow().isoformat()
    
    os.makedirs(os.path.dirname(stats_file), exist_ok=True)
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)


def count_words(text: str) -> int:
    """Count words in text, handling markdown."""
    import re
    if not text:
        return 0
    # Remove markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
    return len(text.split())


def calculate_max_tldr_words(content_word_count: int) -> int:
    """Calculate target TLDR length (17% of content, clamped 40-400)."""
    scaled = int(content_word_count * 0.17)
    return max(40, min(400, scaled))


def get_tldr_prompt(max_words: int = 100) -> str:
    """Generate TLDR system prompt."""
    return f"""You are a TLDR summarization bot for r/accelerate, a subreddit about technological acceleration and AI progress.

Your task is to create a clear, informative TLDR summary of the provided post.

Guidelines:
- Target approximately {max_words} words, but prioritize completeness over word count
- Capture the main argument, key points, and conclusions
- Maintain a neutral, informative tone
- Use clear, direct language
- Focus on what the post is actually saying, not meta-commentary

Respond with ONLY the TLDR text. No prefixes like "TLDR:" or "Summary:" - just the summary itself."""


def generate_tldr(content: str, title: str, gemini_model) -> tuple[str, dict]:
    """Generate TLDR using Gemini API."""
    word_count = count_words(content)
    max_words = calculate_max_tldr_words(word_count)
    
    prompt = get_tldr_prompt(max_words)
    full_content = f"Title: {title}\n\nContent: {content}"
    
    response = gemini_model.generate_content(
        [{"role": "user", "parts": [prompt + "\n\n" + full_content]}],
        generation_config={"temperature": 0.3, "max_output_tokens": 1024}
    )
    
    # Extract token counts
    token_info = {
        "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
        "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
    }
    token_info["total_tokens"] = token_info["input_tokens"] + token_info["output_tokens"]
    
    # Estimate cost (Gemini 2.0 Flash pricing)
    token_info["cost"] = (token_info["input_tokens"] * 0.10 + token_info["output_tokens"] * 0.40) / 1_000_000
    
    return response.text.strip(), token_info


def main():
    parser = argparse.ArgumentParser(description="Reddit TLDR Bot for GitHub Actions")
    parser.add_argument("--dry-run", action="store_true", help="Don't post TLDRs, just log what would happen")
    args = parser.parse_args()
    
    print(f"🚀 Reddit TLDR Bot starting at {datetime.utcnow().isoformat()}")
    
    # Check required environment variables
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD", "GEMINI_API_KEY"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Initialize Reddit
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent="Reddit TLDR Bot v1.0 (GitHub Actions)"
    )
    print(f"✅ Connected to Reddit as u/{reddit.user.me().name}")
    
    # Initialize Gemini
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")
    print("✅ Gemini API initialized")
    
    # Load state
    state = load_state()
    last_check = state.get("last_check")
    processed_posts = set(state.get("processed_posts", []))
    
    # Get subreddit
    subreddit = reddit.subreddit(SUBREDDIT)
    
    # Check posts
    tldrs_generated = 0
    total_tokens = 0
    total_cost = 0.0
    
    limit = 10 if last_check is None else 50
    print(f"🔍 Checking last {limit} posts on r/{SUBREDDIT}...")
    
    for submission in subreddit.new(limit=limit):
        # Skip if too old
        if last_check and submission.created_utc < last_check:
            continue
        
        # Skip if already processed
        if submission.id in processed_posts:
            continue
        
        # Skip if no text content
        if not submission.selftext:
            continue
        
        # Check word count
        word_count = count_words(submission.selftext)
        if word_count < WORD_THRESHOLD:
            print(f"  📝 Post {submission.id}: {word_count} words (below {WORD_THRESHOLD} threshold)")
            continue
        
        print(f"  ✨ Post {submission.id}: {word_count} words - Generating TLDR...")
        
        if args.dry_run:
            print(f"     [DRY RUN] Would generate TLDR for: {submission.title[:50]}...")
            processed_posts.add(submission.id)
            continue
        
        try:
            # Generate TLDR
            tldr_text, token_info = generate_tldr(submission.selftext, submission.title, model)
            
            # Post comment
            comment_text = f"**TLDR:** {tldr_text}"
            comment = submission.reply(comment_text)
            comment.mod.distinguish(sticky=True)
            
            print(f"     ✅ Posted TLDR ({len(tldr_text.split())} words, {token_info['total_tokens']} tokens)")
            
            processed_posts.add(submission.id)
            tldrs_generated += 1
            total_tokens += token_info["total_tokens"]
            total_cost += token_info["cost"]
            
            if tldrs_generated >= MAX_TLDR_PER_RUN:
                print(f"  ⏸️ Reached max TLDRs per run ({MAX_TLDR_PER_RUN})")
                break
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Update state
    state["last_check"] = datetime.utcnow().timestamp()
    state["processed_posts"] = list(processed_posts)[-1000:]  # Keep last 1000
    state["stats"]["total_posts_processed"] += 1
    state["stats"]["total_tldrs_generated"] += tldrs_generated
    state["stats"]["total_tokens_used"] += total_tokens
    state["stats"]["total_cost"] += total_cost
    
    save_state(state)
    update_stats(tldrs_generated=tldrs_generated, tokens=total_tokens, cost=total_cost)
    
    print(f"\n📊 Summary: Generated {tldrs_generated} TLDRs, {total_tokens} tokens, ${total_cost:.6f}")
    print(f"✅ TLDR Bot completed at {datetime.utcnow().isoformat()}")


if __name__ == "__main__":
    main()
