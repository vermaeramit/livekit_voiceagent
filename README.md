# LiveKit + Sarvam Voice Agent

A real-time voice assistant built on [LiveKit Agents](https://docs.livekit.io/agents/) with Sarvam AI for STT, LLM, and TTS. Supports English (India), Hindi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Marathi, Punjabi, and Odia with auto language detection.

Based on the [Sarvam x LiveKit guide](https://docs.sarvam.ai/api-reference-docs/integration/integration-guides/build-voice-agent-with-live-kit).

## Components

| Stage | Model        |
| ----- | ------------ |
| STT   | `saaras:v3`  |
| LLM   | `sarvam-30b` |
| TTS   | `bulbul:v3`  |

## Setup

Requires Python 3.9+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
```

Copy the env template and fill in your keys:

```bash
copy .env.example .env        # Windows
```

- **LiveKit** keys: https://cloud.livekit.io → Settings → Keys
- **Sarvam** key: https://dashboard.sarvam.ai

## Run

Download required model files (e.g. Silero VAD) once:

```bash
python agent.py download-files
```

Talk to the agent directly in your terminal:

```bash
python agent.py console
```

Run as a worker that connects to your LiveKit Cloud project:

```bash
python agent.py dev
```

Then join a room from the [LiveKit Agents Playground](https://agents-playground.livekit.io/) to talk to it.

## Run fully self-hosted (Docker)

Runs both a self-hosted LiveKit server and the agent — no LiveKit Cloud needed.

```bash
copy .env.example .env        # fill in SARVAM_API_KEY (LiveKit vars are set in compose)
docker compose up --build
```

This starts:
- `livekit` — the media server, reachable at `ws://localhost:7880`
- `agent` — the worker, which registers with the server and waits for a room

Keys live in two files that **must stay in sync**: [livekit.yaml](livekit.yaml) (`keys:`) and
[docker-compose.yml](docker-compose.yml) (`LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`). Change the
dev secret before exposing the server.

### Talk to it in the browser

`docker compose up` also starts a `token` service on **http://localhost:3000** — a static
page ([web/index.html](web/index.html)) using the LiveKit JS SDK, plus a token endpoint
([token_server.py](token_server.py)). Token signing needs the API secret, so it must live
server-side, not in the browser.

1. Open **http://localhost:3000**
2. Click **Connect & talk**, allow microphone access
3. Speak — the browser joins room `playground`, the agent is auto-dispatched into it and replies

Watch it handle the call: `docker compose logs -f agent`.

> Browsers only allow microphone capture on `http://localhost` or HTTPS. From another
> machine you'd need to serve it over HTTPS (or use an SSH tunnel to localhost).

### Alternative: LiveKit CLI

```bash
lk token create --api-key devkey --api-secret <secret> \
  --join --room playground --identity user --valid-for 24h
```

### Networking note

WebRTC media flows over UDP `7882`. Locally this just works. On a cloud VM you must open
TCP `7880`/`7881` and UDP `7882`, and set `use_external_ip: true` in [livekit.yaml](livekit.yaml)
(plus advertise the node's public IP), or clients won't get audio.
