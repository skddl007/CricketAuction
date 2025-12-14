"""Google Gemini API client with rate limiting and caching."""

import os
import time
from typing import Optional, Dict, Any
from functools import lru_cache
import json
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. LLM features will be disabled.")


class GeminiClient:
    """Gemini API client with rate limiting and caching."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro", cache_dir: str = "cache/llm"):
        """Initialize Gemini client."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        self.request_count = 0
        self.max_requests_per_minute = 60
        
        # Caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.cache_dir / "cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def generate_content(self, prompt: str, use_cache: bool = True, **kwargs) -> str:
        """Generate content using Gemini API with caching and rate limiting."""
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt)
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Rate limiting
        self._rate_limit()
        
        try:
            # Generate content
            response = self.model.generate_content(prompt, **kwargs)
            content = response.text
            
            # Cache result
            if use_cache:
                cache_key = self._get_cache_key(prompt)
                self._cache[cache_key] = content
                self._save_cache()
            
            return content
        except Exception as e:
            print(f"Error generating content: {e}")
            raise
    
    def generate_content_batch(self, prompts: list, use_cache: bool = True, **kwargs) -> list:
        """Generate content for multiple prompts."""
        results = []
        for prompt in prompts:
            try:
                result = self.generate_content(prompt, use_cache=use_cache, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error processing prompt: {e}")
                results.append(None)
        return results
    
    def clear_cache(self):
        """Clear the cache."""
        self._cache = {}
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            cache_file.unlink()
    
    def get_cache_size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)

