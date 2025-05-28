# Pronunciation Master

A pronunciation practice game with multiple levels, randomized sentences, and progress tracking.

## Features

- **10 Difficulty Levels**: Progress through increasingly challenging pronunciation exercises
- **Randomized Sentences**: Each level has unique, randomly selected sentences
- **Progress Tracking**: Your progress is saved automatically between sessions
- **Auto Mode**: The game automatically listens for your pronunciation and advances when correct
- **Pronunciation Tips**: Each sentence includes specific pronunciation tips
- **Real-Life Contexts**: Sentences are grouped by everyday situations

## Requirements

- Python 3.6+
- PyGame
- SpeechRecognition
- PyAudio
- gTTS (Google Text-to-Speech)
- Boto3 (optional, for Amazon Bedrock integration)

## Setup

1. Install the required Python packages:
   ```
   pip install pygame speechrecognition pyaudio gtts boto3
   ```

2. Make sure your microphone is properly connected and configured

3. If you want to use Amazon Bedrock for generating sentences:
   - Configure your AWS credentials with `aws configure`
   - Set `USE_MOCK = False` in `config.py`

## Running the Game

To start the game, run:
```
python pronunciation_master.py
```

## How to Play

1. The game displays a sentence in a real-life context
2. Listen to the pronunciation (played automatically)
3. Repeat the sentence into your microphone
4. Get feedback on your pronunciation
5. Progress through levels as you improve

## Game Controls

- **Pause/Resume Auto Mode**: Toggle automatic listening and progression
- **Next Level**: Advance to the next level when you've completed enough sentences

## Progress System

- Each level has 5 sentences
- Each correctly pronounced sentence contributes 20% to level completion
- You need 70% completion to advance to the next level
- Your progress is automatically saved when you quit or advance levels