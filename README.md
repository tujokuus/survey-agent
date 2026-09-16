# Survey Browser Agent

Survey Browser Agent is a learning project for running a small, local, read-only browser
agent. The current MVP opens one public news article in visible Chrome, lets Browser Use
inspect it with the local Ollama model `qwen3.5:9b`, validates a structured result with
Pydantic, and stores the result in SQLite.

This version does **not** fill forms, log in, answer surveys, solve CAPTCHAs, bypass bot
checks, or submit anything.

## What each file does

- `pyproject.toml` defines Python 3.12 dependencies and the command-line programs.
- `.env.example` lists every configurable local setting. Copy it to `.env`; `.env` is ignored.
- `src/survey_browser_agent/config.py` loads settings and resolves project-relative paths.
- `models.py` defines the validated article, health-check, and saved-run structures.
- `safety.py` rejects unsafe URL schemes, credentials, and obvious local/private targets.
- `ollama.py` checks Ollama's local `/api/tags` endpoint and the selected model.
- `browser_agent.py` creates the restricted Browser Use agent and manages its lifecycle.
- `storage.py` creates and queries the SQLite database with the Python standard library.
- `cli.py` implements `news-read`, `check`, `runs`, `show`, and automatic help.
- `tests/` covers URL boundaries, model normalization, and SQLite round trips.

Runtime files live under `data/` and are ignored by Git. Browser Use is configured to use
the dedicated system Chrome profile named `Giveaway Agent` (`Profile 3` on the current
computer); the database is `data/survey_browser_agent.db`.

## Safety boundary

The URL is opened deterministically. The model receives only four browser actions:
`navigate`, `scroll`, `extract`, and structured `done`. Browser Use's click, typing, file,
search, keyboard, JavaScript, upload, and download capabilities are removed. Navigation is
also limited to the article's publisher host.

The task prompt says that page content is untrusted and must never override application
rules. A prompt is useful defense in depth, while the removed actions are the actual
capability boundary. This first MVP therefore cannot click article disclosures. A future
phase can add a narrow, deterministic disclosure action after its target validation is
designed and tested.

Only public `http://` and `https://` URLs are accepted. Obvious local and private IP targets
are rejected. This is a learning-grade guard, not a hardened network sandbox.

The `Giveaway Agent` Chrome profile should remain dedicated to this project. Do not sign in
to personal accounts or save personal addresses, payment methods, passwords, or unrelated
extensions in it. Browser Use resolves the profile by display name and stops with a clear
error if it cannot find it; it will not silently select another Chrome profile. Close any
ordinary Chrome window using that profile before running the agent so Chrome can copy it
without profile-lock conflicts.

## Install on Windows with PowerShell

Prerequisites:

1. Install [Google Chrome](https://www.google.com/chrome/).
2. Install [Ollama for Windows](https://ollama.com/download/windows).
3. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if needed.

From this project folder:

```powershell
uv python install 3.12
uv sync --extra dev
Copy-Item .env.example .env
```

Browser Use can drive installed Chrome through the Chrome channel, so this project does not
need a separate headless browser. If automatic Chrome discovery fails, put the full path in
`.env`, for example:

```dotenv
SURVEY_AGENT_CHROME_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
```

## Start Ollama

The Windows Ollama application normally starts the local service. If it is not running, use
one PowerShell window for:

```powershell
ollama serve
```

In another window, download the configured model once:

```powershell
ollama pull qwen3.5:9b
```

Check the complete local setup:

```powershell
uv run survey-browser-agent check
```

Browser Use notes that smaller Qwen models can occasionally produce an invalid action
schema. The small action set, explicit prompt, Pydantic output, deterministic post-checks,
step limit, and timeout make those failures visible, but they cannot guarantee model
accuracy.

## Run the application

Use the direct command requested by the MVP:

```powershell
uv run news-read "https://example.com/a-real-news-article"
```

The equivalent grouped command is:

```powershell
uv run survey-browser-agent news-read "https://example.com/a-real-news-article"
```

The program prints each agent step, returns formatted JSON, stores both successful and
failed run metadata, and closes the dedicated browser session. Limits can be changed in
`.env`:

```dotenv
SURVEY_AGENT_MAX_STEPS=12
SURVEY_AGENT_TIMEOUT_SECONDS=600
SURVEY_AGENT_QWEN35_9B_LLM_TIMEOUT_SECONDS=180
```

`qwen3.5:9b` gets a 180-second limit for each model response because local inference can
take longer than Browser Use's default 75 seconds on a complex page. The override is matched
by model name and does not change Browser Use's timeout for other models. The 600-second
overall limit still stops the complete browser run if several slow steps accumulate.

List previous runs and inspect one result:

```powershell
uv run survey-browser-agent runs
uv run survey-browser-agent show 1
uv run survey-browser-agent --help
```

Run the automated checks:

```powershell
uv run pytest
uv run ruff check .
```

## How the agent loop works

1. The CLI validates the URL and confirms that Ollama and `qwen3.5:9b` are available.
2. Browser Use starts visible Chrome with this project's dedicated profile.
3. An initial deterministic action opens the URL; the local model does not choose it.
4. At each step Browser Use observes the page's URL, title, and accessibility/DOM-derived
   content, then sends the task, previous results, and currently available action schemas to
   Ollama. Vision is off by default, so screenshots are not sent to the model.
5. Ollama chooses one permitted action. Browser Use performs it and feeds its result into
   the next step. The loop stops at structured `done`, the step limit, an error, or timeout.
6. Pydantic validates the shape. Application checks confirm the URL and mark incomplete
   records as partial. SQLite stores the JSON and basic timing/status metadata.
7. The browser session closes in a `finally` block, including after most failures.

Everything sent to Ollama stays on the configured local Ollama endpoint: the application
instructions, page observations/extracted text, action schemas, and previous action results.
Do not place personal information in article URLs or pages you process. The application
does not configure Browser Use sensitive data, disables Browser Use telemetry/cloud sync,
and does not save model reasoning.

Browser Use controls Chrome through the Chrome DevTools Protocol. The dedicated `Giveaway
Agent` system profile keeps this project separate from personal Chrome profiles. Do not use
it for logins in this MVP.

## Development phases represented here

- Phase 1: packaged `src` layout, Python 3.12 setup, `.env`, and Git hygiene.
- Phase 2: `check` verifies Ollama/model availability and Browser Use installation.
- Phase 3: visible Chrome opens and reads one publisher-restricted article.
- Phase 4: Pydantic validates `NewsArticle`, followed by deterministic checks.
- Phase 5: SQLite persists runs; `runs` and `show` inspect them.
- Phase 6: progress messages, bounded execution, failure storage, tests, and this guide.

The reusable pieces for future survey assistance are the bounded agent runner, local-model
configuration, capability filtering, Pydantic schemas, persistence, progress reporting,
and human-verification status. Future survey work still needs a separate local profile data
model, a distinction between facts and subjective preferences, explicit questions for
unknown opinions, consent controls, site-policy checks, an answer review screen, and a hard
approval gate before final submission.

## Git and pushing to GitHub

The project folder is already initialized as a local Git repository. Review and create the
first commit:

```powershell
git status
git add .
git commit -m "Build read-only Survey Browser Agent MVP"
```

Create an empty repository on GitHub, GitLab, or another Git host. Do not add a remote
README, license, or `.gitignore` if the host asks, because this folder already contains the
initial files. Then connect and push it (replace the URL):

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USER/survey-browser-agent.git
git push -u origin main
```

For SSH, use `git@github.com:YOUR-USER/survey-browser-agent.git` instead. Confirm the remote
at any time with `git remote -v`. Never commit `.env`, the SQLite database, or the Chrome
profile; `.gitignore` excludes all three.

Useful upstream references are the [Browser Use quickstart](https://docs.browser-use.com/open-source/quickstart),
[Browser Use model guide](https://docs.browser-use.com/open-source/supported-models), and
[Ollama model-list API](https://docs.ollama.com/api/tags).
