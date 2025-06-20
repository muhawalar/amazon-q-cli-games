import pygame
import sys
import os
import time
import random
import json
import threading
import uuid
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer
from bedrock_client import BedrockClient
from config import *

class Button:
    def __init__(self, x, y, width, height, text, color=LIGHT_BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        
        # Slightly lighter color for hover effect
        hover_offset = 20
        self.hover_color = (
            min(color[0] + hover_offset, 255),
            min(color[1] + hover_offset, 255),
            min(color[2] + hover_offset, 255)
        )
        
        # Bold, modern system font
        self.font = pygame.font.SysFont('Arial', 20, bold=True)
        
        self.is_hovered = False
        self.enabled = True

        
    def draw(self, screen):
        # Define button colors based on state
        if not self.enabled:
            base_color = GRAY
        elif self.is_hovered:
            base_color = self.hover_color
        else:
            base_color = self.color

        # Draw subtle shadow
        shadow_offset = 4
        shadow_rect = pygame.Rect(self.rect.x + shadow_offset, self.rect.y + shadow_offset,
                                self.rect.width, self.rect.height)
        pygame.draw.rect(screen, DARK_GRAY, shadow_rect, border_radius=12)

        # Draw button background
        pygame.draw.rect(screen, base_color, self.rect, border_radius=12)

        # Draw text centered in button
        font = pygame.font.SysFont('Arial', 20, bold=True)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled
        return self.is_hovered
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click and self.enabled

class Character:
    def __init__(self, name, image_path, x, y, width, height):
        self.name = name
        try:
            self.image = pygame.image.load(image_path) if os.path.exists(image_path) else None
            if self.image:
                self.image = pygame.transform.scale(self.image, (width, height))
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            self.image = None
        self.rect = pygame.Rect(x, y, width, height)
        self.speaking = False
        
    def draw(self, screen):
        if self.image:
            # Draw character image
            screen.blit(self.image, self.rect)
        else:
            # Draw a modern placeholder with rounded corners
            placeholder_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(placeholder_surf, GRAY, placeholder_surf.get_rect(), border_radius=15)
            screen.blit(placeholder_surf, self.rect.topleft)
            
            # Draw character name
            font = pygame.font.SysFont("Arial", 20, bold=True)
            text = font.render(self.name, True, WHITE)
            text_rect = text.get_rect(center=self.rect.center)
            screen.blit(text, text_rect)

        # Draw speaking indicator — glowing pulsing circle style
        if self.speaking:
            indicator_radius = 12
            indicator_pos = (self.rect.right - 20, self.rect.top + 20)
            pygame.draw.circle(screen, LIGHT_BLUE, indicator_pos, indicator_radius)
            pygame.draw.circle(screen, WHITE, indicator_pos, indicator_radius, 2)


class SentenceDisplay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.sentence = ""
        self.font = pygame.font.Font(None, 36)
        self.context = ""
        self.small_font = pygame.font.Font(None, 24)
        
    def set_sentence(self, sentence, context=""):
        self.sentence = sentence
        self.context = context
        
    def draw(self, screen):
        # Draw box
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=15)
        pygame.draw.rect(screen, LIGHT_BLUE, self.rect, 2, border_radius=15)
        
        # Draw sentence with improved word wrapping
        words = self.sentence.split(' ')
        line = ""
        y_offset = 20
        max_width = self.rect.width - 40
        
        for word in words:
            test_line = line + word + " "
            test_width = self.font.size(test_line)[0]
            
            if test_width > max_width:
                # If a single word is too long, break it
                if not line and self.font.size(word)[0] > max_width:
                    # Split the long word
                    curr_word = word
                    while curr_word:
                        for i in range(len(curr_word), 0, -1):
                            part = curr_word[:i]
                            if self.font.size(part)[0] <= max_width:
                                text_surface = self.font.render(part, True, WHITE)
                                screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
                                y_offset += 40
                                curr_word = curr_word[i:]
                                break
                else:
                    text_surface = self.font.render(line, True, WHITE)
                    screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
                    y_offset += 40
                    line = word + " "
            else:
                line = test_line
                
        if line:
            text_surface = self.font.render(line, True, WHITE)
            screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
            y_offset += 40
        
        # Draw context if available
        if self.context:
            # Handle long context with wrapping
            context_text = f"Context: {self.context}"
            words = context_text.split(' ')
            line = ""
            max_width = self.rect.width - 40
            
            for word in words:
                test_line = line + word + " "
                test_width = self.small_font.size(test_line)[0]
                
                if test_width > max_width:
                    context_surface = self.small_font.render(line, True, LIGHT_BLUE)
                    screen.blit(context_surface, (self.rect.x + 20, self.rect.y + y_offset))
                    y_offset += 25
                    line = word + " "
                else:
                    line = test_line
                    
            if line:
                context_surface = self.small_font.render(line, True, LIGHT_BLUE)
                screen.blit(context_surface, (self.rect.x + 20, self.rect.y + y_offset))

class FeedbackDisplay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.color = WHITE
        self.correct_pronunciation = ""
        
    def set_feedback(self, text, correct_pronunciation="", success=True):
        self.text = text
        self.correct_pronunciation = correct_pronunciation
        self.color = GREEN if success else RED
        
    def draw(self, screen):
        if not self.text:
            return
            
        # Draw box with rounded corners
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=15)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=15)
        
        # Draw text with improved word wrapping
        words = self.text.split(' ')
        line = ""
        y_offset = 20
        max_width = self.rect.width - 40
        
        for word in words:
            test_line = line + word + " "
            test_width = self.font.size(test_line)[0]
            
            if test_width > max_width:
                # If a single word is too long, break it
                if not line and self.font.size(word)[0] > max_width:
                    # Split the long word
                    curr_word = word
                    while curr_word:
                        for i in range(len(curr_word), 0, -1):
                            part = curr_word[:i]
                            if self.font.size(part)[0] <= max_width:
                                text_surface = self.font.render(part, True, self.color)
                                screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
                                y_offset += 30
                                curr_word = curr_word[i:]
                                break
                else:
                    text_surface = self.font.render(line, True, self.color)
                    screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
                    y_offset += 30
                    line = word + " "
            else:
                line = test_line
                
        if line:
            text_surface = self.font.render(line, True, self.color)
            screen.blit(text_surface, (self.rect.x + 20, self.rect.y + y_offset))
            y_offset += 30
            
        # Draw correct pronunciation if available with wrapping
        if self.correct_pronunciation:
            tip_text = f"Pronunciation tip: {self.correct_pronunciation}"
            words = tip_text.split(' ')
            line = ""
            
            for word in words:
                test_line = line + word + " "
                test_width = self.font.size(test_line)[0]
                
                if test_width > max_width:
                    correct_surface = self.font.render(line, True, WHITE)
                    screen.blit(correct_surface, (self.rect.x + 20, self.rect.y + y_offset))
                    y_offset += 30
                    line = word + " "
                else:
                    line = test_line
                    
            if line:
                correct_surface = self.font.render(line, True, WHITE)
                screen.blit(correct_surface, (self.rect.x + 20, self.rect.y + y_offset))

class StatusDisplay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.status = "Ready"
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.padding = 10

    def set_status(self, status):
        self.status = status

    def draw(self, screen):
        # Draw shadow for modern depth effect
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, (30, 30, 30), shadow_rect, border_radius=12)

        # Draw background with border
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=12)
        pygame.draw.rect(screen, LIGHT_BLUE, self.rect, 2, border_radius=12)

        # Render and center the text
        text_surface = self.font.render(self.status, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class Level:
    def __init__(self, level_num, difficulty, sentences):
        self.level_num = level_num
        self.difficulty = difficulty
        self.sentences = sentences
        self.completed_sentences = set()
        self.score = 0
        self.total_attempts = 0
        self.required_score = 70  # 70% to pass
        self.current_index = 0  # Track current position in sentences
        
    def is_completed(self):
        return self.get_completion_percentage() >= self.required_score
        
    def get_next_sentence(self):
        # Get sentences that haven't been completed yet
        available = [s for s in self.sentences if s["sentence"] not in self.completed_sentences]
        if available:
            return random.choice(available)
        
        # If all sentences are completed, return None to indicate level completion
        if len(self.completed_sentences) >= len(self.sentences):
            return None
            
        # Fallback: return any sentence that hasn't been tried yet
        for i in range(len(self.sentences)):
            idx = (self.current_index + i) % len(self.sentences)
            self.current_index = (idx + 1) % len(self.sentences)
            return self.sentences[idx]
            
        # If we get here, something is wrong with the sentences list
        return None
        
    def mark_sentence_completed(self, sentence, points=1):
        # Only add to completed sentences if not already there
        if sentence not in self.completed_sentences:
            self.completed_sentences.add(sentence)
            # Calculate score based on completed sentences and total sentences
            # Each sentence is worth exactly 20% (for 5 sentences)
            self.score = (len(self.completed_sentences) / len(self.sentences)) * 100
            # Print debug info
            print(f"Completed: {len(self.completed_sentences)}/{len(self.sentences)} sentences")
        self.total_attempts += 1
        
    def get_progress(self):
        return len(self.completed_sentences), len(self.sentences)
        
    def get_completion_percentage(self):
        # Calculate percentage directly from completed sentences
        if not self.sentences:
            return 0
        return min((len(self.completed_sentences) / len(self.sentences)) * 100, 100)  # Cap at 100%

class PronunciationMaster:
    def __init__(self):
        pygame.init()
        try:
            mixer.init()
        except pygame.error:
            print("Warning: Audio mixer could not be initialized")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        
        # Create character
        char_width, char_height = CHARACTER_WIDTH, CHARACTER_HEIGHT
        self.guide = Character("Teacher", "assets/avatar.png", 
                              80, 100, char_width, char_height)
        
        # Create UI elements
        self.sentence_display = SentenceDisplay(char_width + 100, 100, 
                                      WINDOW_WIDTH - char_width - 150, 150)
        
        self.feedback_display = FeedbackDisplay(char_width + 100, 270, 
                                             WINDOW_WIDTH - char_width - 150, 150)
        
        # Create status display
        self.status_display = StatusDisplay(WINDOW_WIDTH // 2 - 100, 450, 200, 40)
        
        # Create buttons
        self.toggle_button = Button(WINDOW_WIDTH // 2 - 200, 500, 180, 40, "Pause Auto Mode")
        self.next_level_button = Button(WINDOW_WIDTH // 2 + 20, 500, 180, 40, "Next Level")
        self.next_level_button.enabled = False
        
        # Start screen buttons
        self.resume_button = Button(WINDOW_WIDTH // 2 - 100, 250, 200, 50, "Resume Latest Level", BLUE)
        self.restart_button = Button(WINDOW_WIDTH // 2 - 100, 320, 200, 50, "Start from Level 1", GREEN)
        self.toggle_dynamic_button = Button(WINDOW_WIDTH // 2 - 100, 390, 200, 50, 
                                          "Dynamic: " + ("ON" if USE_DYNAMIC_SENTENCES else "OFF"), LIGHT_BLUE)
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize Bedrock client
        self.bedrock_client = BedrockClient(
            model_id=MODEL_ID,
            region_name=AWS_REGION,
        )
        
        # Game state
        self.current_level = 0
        self.levels = []
        self.current_sentence = ""
        self.current_context = ""
        self.current_pronunciation_tip = ""
        self.recording = False
        self.playing_audio = False
        self.auto_mode = True
        self.auto_listening = False
        self.generating_sentences = False
        self.game_started = False
        self.has_saved_progress = os.path.exists("pronunciation_progress.json")
        self.used_sentences = set()  # Track all used sentences across levels
        self.use_dynamic_sentences = USE_DYNAMIC_SENTENCES  # Use dynamic sentence generation
        
        # Load levels but don't start yet
        self.preload_levels()
        
    def preload_levels(self):
        """Preload levels without starting the game"""
        # Check if saved progress is available
        self.has_saved_progress = self.load_progress(start_game=False)
        
    def initialize_levels(self, restart=False):
        """Initialize game levels with sentences"""
        # Always create new levels when restarting or if no saved progress
        # This ensures we get fresh sentences from Bedrock each time
        if restart or not self.levels:
            self.levels = []
            # Track all used sentences to avoid repetition across levels
            used_sentences = set()
            
            # Create 10 levels with randomized sentences
            for level_num in range(1, 11):
                # Generate sentences for this level
                level_sentences = self.generate_sentences_for_level(level_num)
                
                # Filter out sentences that have been used in previous levels
                available_sentences = [s for s in level_sentences if s["sentence"] not in used_sentences]
                
                # If we don't have enough unique sentences, generate more
                attempts = 0
                while len(available_sentences) < 5 and attempts < 3:
                    more_sentences = self.generate_sentences_for_level(level_num)
                    for s in more_sentences:
                        if s["sentence"] not in used_sentences:
                            available_sentences.append(s)
                    attempts += 1
                
                # Select 5 sentences for this level
                if available_sentences and len(available_sentences) >= 5:
                    selected = random.sample(available_sentences, 5)
                    
                    # Add these sentences to the used set
                    for s in selected:
                        used_sentences.add(s["sentence"])
                        
                    self.levels.append(Level(level_num, f"{level_num}", selected))
            
            # Start with level 1
            self.current_level = 0
            
            # Save the newly generated levels immediately
            self.save_progress()
            
        # Start the game
        self.game_started = True
        self.next_sentence()
    
    def generate_sentences_for_level(self, level_num):
        """Generate sentences for a specific level"""
        # Level-specific configurations
        level_configs = {
            1: {"difficulty": "easy", "focus": "basic greetings and introductions", 
                "length": "5-7 words", "phonemes": "simple consonants and vowels"},
            2: {"difficulty": "easy", "focus": "daily activities and routines", 
                "length": "6-8 words", "phonemes": "th, r, l sounds"},
            3: {"difficulty": "easy", "focus": "shopping and numbers", 
                "length": "7-9 words", "phonemes": "s, z, sh sounds"},
            4: {"difficulty": "medium", "focus": "work and education", 
                "length": "8-10 words", "phonemes": "ch, j, v sounds"},
            5: {"difficulty": "medium", "focus": "travel and directions", 
                "length": "9-11 words", "phonemes": "w, y, compound sounds"},
            6: {"difficulty": "medium", "focus": "food and dining", 
                "length": "10-12 words", "phonemes": "diphthongs and blends"},
            7: {"difficulty": "medium", "focus": "health and fitness", 
                "length": "10-12 words", "phonemes": "consonant clusters"},
            8: {"difficulty": "hard", "focus": "technology and science", 
                "length": "11-13 words", "phonemes": "complex consonant clusters"},
            9: {"difficulty": "hard", "focus": "business and economics", 
                "length": "12-14 words", "phonemes": "stress patterns and rhythm"},
            10: {"difficulty": "hard", "focus": "arts, culture and philosophy", 
                "length": "13-15 words", "phonemes": "advanced pronunciation patterns"}
        }
        
        # Get config for this level or use default
        config = level_configs.get(level_num, {
            "difficulty": "medium",
            "focus": "general topics",
            "length": "8-12 words",
            "phonemes": "mixed sounds"
        })
        
        difficulty = config["difficulty"]
        focus = config["focus"]
        length = config["length"]
        phonemes = config["phonemes"]
            
        prompt = f"""
        Generate 8 English sentences for pronunciation practice at {difficulty} level.
        Focus on topics related to {focus}.
        Sentences should be {length} in length.
        Include practice for these phonemes: {phonemes}.
        Each sentence should be in a different context.
        Make sure sentences are unique and not similar to common phrases.
        For each sentence, provide a pronunciation tip focusing on 1-2 challenging words or sounds.
        Format your response as a JSON array of objects with 'sentence', 'context', and 'pronunciation_tip' fields.
        """
        
        try:
            print(f"[INFO] Generating sentences for level {level_num} ({difficulty} difficulty)...")
            response = self.bedrock_client.generate_response(prompt)
            import re
        
            # Extract JSON from response
            try:
                # Try direct JSON parsing first
                sentences = json.loads(response)
                print(f"[SUCCESS] Successfully extracted {len(sentences)} sentences")
                return sentences
            except json.JSONDecodeError:
                # If that fails, try to extract JSON with regex
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    try:
                        sentences = json.loads(json_match.group(0))
                        print(f"[SUCCESS] Successfully extracted {len(sentences)} sentences")
                        return sentences
                    except json.JSONDecodeError:
                        print("[ERROR] Failed to parse extracted JSON")
                        print("[ERROR] Response content: " + response[:100] + "..." if len(response) > 100 else response)
                        return [{"sentence": "Please try again later.", 
                                "context": "API error recovery", 
                                "pronunciation_tip": "Focus on clear pronunciation."}]
                else:
                    print("[ERROR] No JSON array found in response")
                    print("[ERROR] Response content: " + response[:100] + "..." if len(response) > 100 else response)
                    return [{"sentence": "Please try again later.", 
                            "context": "API error recovery", 
                            "pronunciation_tip": "Focus on clear pronunciation."}]
        except Exception as e:
            print(f"[ERROR] Error generating sentences: {e}")
            return [{"sentence": "Please try again later.", 
                    "context": "API error recovery", 
                    "pronunciation_tip": "Focus on clear pronunciation."}]

    
    def save_progress(self):
        """Save game progress to file"""
        try:
            # Collect all used sentences across levels
            all_sentences = set()
            for level in self.levels:
                for sentence_data in level.sentences:
                    all_sentences.add(sentence_data["sentence"])
            
            save_data = {
                "current_level": self.current_level,
                "used_sentences": list(all_sentences),
                "levels": []
            }
            
            # Save each level's data
            for level in self.levels:
                level_data = {
                    "level_num": level.level_num,
                    "difficulty": level.difficulty,
                    "score": level.score,
                    "total_attempts": level.total_attempts,
                    "completed_sentences": list(level.completed_sentences),
                    "sentences": level.sentences
                }
                save_data["levels"].append(level_data)
            
            # Save to file
            with open("pronunciation_progress.json", "w") as f:
                json.dump(save_data, f)
                
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def load_progress(self, start_game=True):
        """Load game progress from file"""
        try:
            if os.path.exists("pronunciation_progress.json"):
                with open("pronunciation_progress.json", "r") as f:
                    save_data = json.load(f)
                
                self.current_level = save_data.get("current_level", 0)
                self.levels = []
                
                # Load used sentences
                self.used_sentences = set(save_data.get("used_sentences", []))
                
                # Load each level
                for level_data in save_data.get("levels", []):
                    level = Level(
                        level_data["level_num"],
                        level_data["difficulty"],
                        level_data["sentences"]
                    )
                    level.score = level_data.get("score", 0)
                    level.total_attempts = level_data.get("total_attempts", 0)
                    level.completed_sentences = set(level_data.get("completed_sentences", []))
                    self.levels.append(level)
                
                return True
            return False
        except Exception as e:
            print(f"Error loading progress: {e}")
            return False
    
    def next_sentence(self):
        """Get the next sentence for pronunciation practice"""
        if not self.levels or self.current_level >= len(self.levels):
            self.status_display.set_status("No levels available")
            return False
            
        current = self.levels[self.current_level]
        
        # Check if all sentences are completed
        completed, total = current.get_progress()
        if completed == total:
            # All sentences completed
            self.feedback_display.set_feedback(f"Level {current.level_num} completed! You can move to the next level.", "", True)
            self.next_level_button.enabled = True
            return True
            
        # Get a sentence that hasn't been completed yet
        sentence_data = current.get_next_sentence()
        
        # If no sentence is returned, reset the current index to ensure we cycle through all sentences
        if not sentence_data:
            current.current_index = 0
            sentence_data = current.get_next_sentence()
            
        if not sentence_data:
            return False
            
        self.current_sentence = sentence_data["sentence"]
        self.current_context = sentence_data.get("context", "")
        self.current_pronunciation_tip = sentence_data.get("pronunciation_tip", "")
        
        # Update display
        self.sentence_display.set_sentence(self.current_sentence, self.current_context)
        self.feedback_display.text = ""
        self.feedback_display.correct_pronunciation = ""
        self.guide.speaking = True
        
        # Play audio automatically
        self.play_audio()
        return True
        
    def play_audio(self):
        """Play the current sentence using text-to-speech"""
        if self.playing_audio:
            return
            
        self.playing_audio = True
        self.status_display.set_status("Playing audio...")
        
        def speak_text():
            temp_file = None
            try:
                # Generate unique temp filename
                temp_file = f"temp_audio_{uuid.uuid4().hex}.mp3"
                
                # Generate audio
                tts = gTTS(text=self.current_sentence, lang='en', slow=False)
                
                # Save directly to file
                tts.save(temp_file)
                
                try:
                    # Play the audio
                    mixer.music.load(temp_file)
                    mixer.music.play()
                    
                    # Wait for audio to finish
                    while mixer.music.get_busy():
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Error playing audio: {e}")
                    # Continue without audio playback
                    time.sleep(2)  # Pause briefly to simulate audio playing
                    
                # Start listening after audio finishes
                if self.auto_mode and not self.auto_listening:
                    self.start_listening()
                    
            except Exception as e:
                print(f"Error generating audio: {e}")
            finally:
                # Clean up temp file
                try:
                    if temp_file and os.path.exists(temp_file):
                        try:
                            mixer.music.unload()  # Unload before deleting
                        except:
                            pass  # Ignore if mixer is not initialized
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file: {e}")
                    
                self.playing_audio = False
                if self.auto_mode:
                    self.status_display.set_status("Listening...")
                else:
                    self.status_display.set_status("Ready")
        
        # Start in a separate thread to avoid freezing the UI
        threading.Thread(target=speak_text).start()
    
    def start_listening(self):
        """Start listening for speech in a background thread"""
        if not self.auto_listening and self.auto_mode:
            self.auto_listening = True
            threading.Thread(target=self.listen_for_speech).start()
    
    def listen_for_speech(self):
        """Listen for speech and process it"""
        self.status_display.set_status("Listening...")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise with shorter duration
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                # Set dynamic energy threshold
                self.recognizer.energy_threshold = 4000
                self.recognizer.dynamic_energy_threshold = True
                
                # Listen with shorter timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
            self.status_display.set_status("Processing speech...")
            
            # Use Google's speech recognition
            user_said = self.recognizer.recognize_google(audio).lower()
            expected = self.current_sentence.lower()
            
            # Compare with current sentence
            if user_said == expected:
                # Mark sentence as completed
                current_level = self.levels[self.current_level]
                current_level.mark_sentence_completed(self.current_sentence)
                
                self.feedback_display.set_feedback("Excellent! You said it perfectly.", 
                                                self.current_pronunciation_tip, True)
                
                # Save progress after completing a sentence
                self.save_progress()
                
                # Wait a moment to show feedback, then move to next sentence
                time.sleep(1.5)
                if self.auto_mode:
                    self.next_sentence()
            else:
                # Calculate similarity
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, user_said, expected).ratio()
                
                current_level = self.levels[self.current_level]
                
                if similarity > 0.8:
                    # Mark sentence as completed
                    current_level.mark_sentence_completed(self.current_sentence)
                    
                    self.feedback_display.set_feedback(f"Very good! You said: {user_said}", 
                                                    self.current_pronunciation_tip, True)
                    
                    # Save progress after completing a sentence
                    self.save_progress()
                    
                    # Wait a moment to show feedback, then move to next sentence
                    time.sleep(1.5)
                    if self.auto_mode:
                        self.next_sentence()
                else:
                    # Don't mark as completed, just give feedback and try again
                    if similarity > 0.5:
                        feedback = f"Not bad. You said: {user_said}"
                    else:
                        feedback = f"Try again. You said: {user_said}"
                        
                    self.feedback_display.set_feedback(feedback, self.current_pronunciation_tip, False)
                    
                    # Try again after showing feedback - stay on the same sentence
                    time.sleep(2)
                    if self.auto_mode:
                        self.play_audio()
            
        except sr.WaitTimeoutError:
            self.feedback_display.set_feedback("No speech detected. Please try again.", "", False)
            if self.auto_mode:
                time.sleep(1)
                self.play_audio()
        except sr.UnknownValueError:
            self.feedback_display.set_feedback("Could not understand audio. Please try again.", "", False)
            if self.auto_mode:
                time.sleep(1)
                self.play_audio()
        except sr.RequestError as e:
            self.feedback_display.set_feedback(f"Error with speech recognition service: {e}", "", False)
        except Exception as e:
            self.feedback_display.set_feedback(f"Error: {e}", "", False)
            
        self.auto_listening = False
        self.guide.speaking = False
        
        if self.auto_mode and not self.playing_audio:
            self.status_display.set_status("Ready")
    
    def go_to_next_level(self):
        """Advance to the next level"""
        if self.current_level < len(self.levels) - 1:
            self.current_level += 1
            self.next_level_button.enabled = False
            
            # Reset any stuck state
            current = self.levels[self.current_level]
            if len(current.completed_sentences) == len(current.sentences):
                # If somehow all sentences are already marked as completed, reset them
                current.completed_sentences = set()
                
            # Get a new sentence from the next level
            self.next_sentence()
            
            # Save progress when advancing levels
            self.save_progress()
        else:
            self.feedback_display.set_feedback("Congratulations! You've completed all levels!", "", True)
        
    def toggle_auto_mode(self):
        """Toggle auto mode on/off"""
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.toggle_button.text = "Pause Auto Mode"
            if not self.playing_audio and not self.auto_listening:
                self.play_audio()
        else:
            self.toggle_button.text = "Resume Auto Mode"
            self.status_display.set_status("Auto mode paused")
        
    def draw_start_screen(self):
        """Draw the start screen with resume/restart options"""
        self.screen.fill(BLACK)
        
        # Draw title
        title_font = pygame.font.SysFont('Arial', 48, bold=True)
        title_text = "Pronunciation Master"
        title_surface = title_font.render(title_text, True, WHITE)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Draw subtitle
        subtitle_font = pygame.font.SysFont('Arial', 24)
        subtitle_text = "Improve your pronunciation with 10 levels of practice"
        subtitle_surface = subtitle_font.render(subtitle_text, True, LIGHT_BLUE)
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Set resume button state
        self.resume_button.enabled = self.has_saved_progress
        
        # Draw saved progress info if available
        if self.has_saved_progress and self.levels:
            info_font = pygame.font.SysFont('Arial', 20)
            level_info = f"Saved progress: Level {self.current_level + 1} of 10"
            info_surface = info_font.render(level_info, True, WHITE)
            info_rect = info_surface.get_rect(center=(WINDOW_WIDTH // 2, 200))
            self.screen.blit(info_surface, info_rect)
        
        # Position buttons neatly
        button_spacing = 80
        base_y = 280

        self.resume_button.rect.center = (WINDOW_WIDTH // 2, base_y)
        self.restart_button.rect.center = (WINDOW_WIDTH // 2, base_y + button_spacing)
        self.toggle_dynamic_button.rect.center = (WINDOW_WIDTH // 2, base_y + button_spacing * 2)

        # Draw buttons
        self.resume_button.draw(self.screen)
        self.restart_button.draw(self.screen)
        self.toggle_dynamic_button.draw(self.screen)


    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Save progress before quitting
                    if self.game_started:
                        self.save_progress()
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True
            
            # Show start screen if game not started
            if not self.game_started:
                # Update start screen button hover states
                self.resume_button.check_hover(mouse_pos)
                self.restart_button.check_hover(mouse_pos)
                self.toggle_dynamic_button.check_hover(mouse_pos)
                
                # Handle start screen button clicks
                if self.resume_button.is_clicked(mouse_pos, mouse_click) and self.has_saved_progress:
                    # Resume from saved progress - use existing sentences
                    self.load_progress()
                    self.game_started = True
                    self.next_sentence()
                elif self.restart_button.is_clicked(mouse_pos, mouse_click):
                    # Start new game from level 1 with fresh sentences
                    # Delete any existing progress file to ensure we get new sentences
                    if os.path.exists("pronunciation_progress.json"):
                        try:
                            os.remove("pronunciation_progress.json")
                        except:
                            pass
                    self.initialize_levels(restart=True)
                elif self.toggle_dynamic_button.is_clicked(mouse_pos, mouse_click):
                    # Toggle dynamic sentence generation
                    self.use_dynamic_sentences = not self.use_dynamic_sentences
                    self.toggle_dynamic_button.text = "Dynamic: " + ("ON" if self.use_dynamic_sentences else "OFF")
                    # Update the Bedrock client with the new setting
                    self.bedrock_client.use_dynamic = self.use_dynamic_sentences
                
                # Draw start screen
                self.draw_start_screen()
            else:
                # Game is running - handle game UI
                # Update button hover states
                self.toggle_button.check_hover(mouse_pos)
                self.next_level_button.check_hover(mouse_pos)
                
                # Handle button clicks
                if self.toggle_button.is_clicked(mouse_pos, mouse_click):
                    self.toggle_auto_mode()
                if self.next_level_button.is_clicked(mouse_pos, mouse_click):
                    self.go_to_next_level()
                
                # Draw everything
                self.screen.fill(BLACK)
                self.guide.draw(self.screen)
                self.sentence_display.draw(self.screen)
                self.feedback_display.draw(self.screen)
                self.status_display.draw(self.screen)
                self.toggle_button.draw(self.screen)
                self.next_level_button.draw(self.screen)
                
                # Draw level info and progress
                if self.levels and self.current_level < len(self.levels):
                    current = self.levels[self.current_level]
                    level_font = pygame.font.Font(None, 30)
                    
                    # Level info
                    level_text = f"Level {current.level_num}"
                    level_surface = level_font.render(level_text, True, WHITE)
                    self.screen.blit(level_surface, (50, 20))
                    
                    # Progress
                    completed, total = current.get_progress()
                    progress_text = f"Progress: {completed}/{total} sentences"
                    progress_surface = level_font.render(progress_text, True, WHITE)
                    self.screen.blit(progress_surface, (WINDOW_WIDTH - 250, 20))
                    
                    # Completion percentage
                    completion = current.get_completion_percentage()
                    completion_text = f"Completion: {int(completion)}% ({len(current.completed_sentences)}/{len(current.sentences)})"
                    completion_surface = level_font.render(completion_text, True, 
                                                         GREEN if completion >= 70 else LIGHT_BLUE)
                    self.screen.blit(completion_surface, (WINDOW_WIDTH - 250, 50))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PronunciationMaster()
    game.run()