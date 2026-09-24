# LLM API backend

The production content-generation path uses an API backend instead of automating the consumer Gemini web UI. Drive-native leasing, checkpoints, repository validation, and Git publication are unchanged.

## Current backend

The tracked project configuration selects:

```toml
[llm]
backend = "gemini_api"
gemini_api_model = "gemini-3.8-flash"
gemini_api_location = "global"
gemini_api_thinking_level = "high"
gemini_api_timeout_seconds = 1200
gemini_api_max_attempts = 3
gemini_api_retry_backoff_seconds = 5
```

`gemini_browser` remains available as a legacy fallback. It still uses the configured Gem URL, Gem editor URL, dedicated Chrome profile, and browser-session recovery logic.

## Authentication

`gemini_api` supports two authentication modes. If `GOOGLE_API_KEY` or `GEMINI_API_KEY` is present, the Gemini Developer API is used. Otherwise the package uses the configured desktop OAuth client with Vertex AI and stores a separate refreshable token at `gemini_api_token_file` outside Git.

The Vertex route requires the Google Cloud `aiplatform.googleapis.com` service to be enabled for the OAuth client's project. API use can consume Google Cloud quota and incur normal provider charges when billing is enabled.
