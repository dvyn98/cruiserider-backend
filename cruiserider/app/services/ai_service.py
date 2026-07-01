"""
AI Blog Service - Generates SEO articles from YouTube video content using Claude AI

PIPELINE:
  YouTube Video → Extract Description/Title → Claude AI → SEO Article → Save to DB

Future enhancement: Extract actual transcript using YouTube Transcript API
  pip install youtube-transcript-api
  from youtube_transcript_api import YouTubeTranscriptApi
"""

import anthropic
import re
from typing import Optional, Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def generate_article_from_video(
    video_title: str,
    video_description: str,
    car_brand: Optional[str] = None,
    car_model: Optional[str] = None,
    video_url: Optional[str] = None,
) -> Optional[Dict]:
    """
    Uses Claude AI to generate a full SEO-optimised article
    based on a YouTube video's title and description.
    
    Returns dict with: title, slug, content, excerpt, meta_description, tags
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("⚠️  ANTHROPIC_API_KEY not set in .env")
        return None

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    car_context = ""
    if car_brand and car_model:
        car_context = f"The video is specifically about the {car_brand} {car_model}."

    prompt = f"""You are an expert automotive journalist writing for an Indian car review website called CruiseRider.

VIDEO TITLE: {video_title}
VIDEO DESCRIPTION: {video_description}
{car_context}
{"VIDEO LINK: " + video_url if video_url else ""}

Write a comprehensive, SEO-optimised automotive article based on this YouTube video content. 

REQUIREMENTS:
1. Write for Indian car buyers - mention Indian prices in lakhs (₹), Indian road conditions, fuel types relevant to India
2. Article should be 600-1000 words
3. Use proper HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <strong>
4. Include these sections naturally: Introduction, Key Highlights, Performance & Drive, Features, Verdict
5. Make it engaging and conversational - like Priyanshu's style (enthusiastic, honest, relatable)
6. Mention the YouTube video review for more details

Return ONLY a JSON object with this exact structure (no markdown, no extra text):
{{
  "title": "SEO article title (60 chars max)",
  "slug": "url-friendly-slug-with-hyphens",
  "excerpt": "2-3 sentence summary for article cards (150 chars)",
  "content": "Full HTML article content here",
  "meta_description": "SEO meta description 150-160 chars",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "read_time_minutes": 5
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        
        raw_text = message.content[0].text.strip()
        
        # Clean up any stray markdown fences
        raw_text = re.sub(r"```json|```", "", raw_text).strip()
        
        import json
        return json.loads(raw_text)

    except Exception as e:
        logger.error(f"❌ AI article generation failed: {e}")
        return None


def generate_article_from_transcript(
    transcript: str,
    video_title: str,
    car_brand: Optional[str] = None,
    car_model: Optional[str] = None,
) -> Optional[Dict]:
    """
    Future: Generate article from actual video transcript.
    Use youtube-transcript-api to extract transcript first.
    
    from youtube_transcript_api import YouTubeTranscriptApi
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'en'])
    text = " ".join([t['text'] for t in transcript])
    """
    if not settings.ANTHROPIC_API_KEY:
        return None

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    # Truncate transcript to ~3000 words to stay within context
    truncated = transcript[:12000] if len(transcript) > 12000 else transcript

    prompt = f"""You are an expert automotive journalist for CruiseRider, an Indian car review platform.

VIDEO TITLE: {video_title}
CAR: {car_brand or 'Unknown'} {car_model or ''}

VIDEO TRANSCRIPT:
{truncated}

Based on this actual video transcript, write a comprehensive SEO article. 
Extract key insights, opinions, pros/cons, and verdict from the transcript.
Write in English even if transcript is in Hindi/Hinglish.

Return ONLY JSON (same format as before):
{{
  "title": "SEO title",
  "slug": "url-slug",
  "excerpt": "Summary",
  "content": "<h2>...</h2><p>...</p>",
  "meta_description": "SEO description",
  "tags": ["tag1"],
  "read_time_minutes": 6
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        raw_text = re.sub(r"```json|```", "", raw_text).strip()
        import json
        return json.loads(raw_text)
    except Exception as e:
        logger.error(f"❌ Transcript article generation failed: {e}")
        return None
