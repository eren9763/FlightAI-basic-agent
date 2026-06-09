# FlightAI Basic Agent

A Gradio chatbot for the fictional airline **FlightAI**. The assistant answers customer questions using OpenAI tool calling, looks up flight prices and dates from a local SQLite database, generates destination brochure images, and speaks replies with text-to-speech.

## Features

- Chat interface powered by OpenAI (`gpt-4.1-mini`)
- Tool calls for ticket price and flight date lookups
- Image generation for destination brochures
- Voice responses via OpenAI TTS

## Requirements

- Python 3.10+
- OpenAI API key
- Google API key (for Gemini client configuration in the project)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Usage

```bash
python project.py
```

The Gradio UI opens in your browser. Ask about destinations such as London, Paris, Berlin, or Tokyo to try the flight lookup tools.

## Project Files

| File | Description |
|------|-------------|
| `project.py` | Main application: Gradio UI, chat logic, tools, image and audio generation |
| `data.db` | SQLite database with sample flights from Istanbul |

## Sample Data

`data.db` includes example routes from Istanbul to London, Paris, Berlin, and Tokyo with dates and prices.

## Author

Eren Koybasi ([@eren9763](https://github.com/eren9763))
