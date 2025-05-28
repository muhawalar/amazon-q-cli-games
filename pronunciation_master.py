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
        self.hover_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.is_hovered = False
        self.enabled = True
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered and self.enabled else self.color
        if not self.enabled:
            color = GRAY
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, WHITE)
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
            screen.blit(self.image, self.rect)
        else:
            # Draw placeholder if image not found
            pygame.draw.rect(screen, GRAY, self.rect)
            font = pygame.font.Font(None, 30)
            text = font.render(self.name, True, WHITE)
            text_rect = text.get_rect(center=self.rect.center)
            screen.blit(text, text_rect)
            
        # Draw speaking indicator
        if self.speaking:
            pygame.draw.circle(screen, LIGHT_BLUE, 
                              (self.rect.right - 20, self.rect.top + 20), 10)

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
        pygame.draw.rect(screen, DARK_GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Draw sentence with word wrapping
        words = self.sentence.split(' ')
        line = ""
        y_offset = 20
        
        for word in words:
            test_line = line + word + " "
            test_width = self.font.size(test_line)[0]
            
            if test_width > self.rect.width - 40:
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
            context_surface = self.small_font.render(f"Context: {self.context}", True, LIGHT_BLUE)
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
            
        # Draw box
        pygame.draw.rect(screen, DARK_GRAY, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Draw text with word wrapping
        words = self.text.split(' ')
        line = ""
        y_offset = 20
        
        for word in words:
            test_line = line + word + " "
            test_width = self.font.size(test_line)[0]
            
            if test_width > self.rect.width - 40:
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
            
        # Draw correct pronunciation if available
        if self.correct_pronunciation:
            correct_text = f"Pronunciation tip: {self.correct_pronunciation}"
            correct_surface = self.font.render(correct_text, True, WHITE)
            screen.blit(correct_surface, (self.rect.x + 20, self.rect.y + y_offset))

class StatusDisplay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.status = "Ready"
        self.font = pygame.font.Font(None, 24)
        
    def set_status(self, status):
        self.status = status
        
    def draw(self, screen):
        pygame.draw.rect(screen, DARK_GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
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
        self.points_per_sentence = 20  # Each sentence is worth 20%
        self.required_score = 70  # 70% to pass
        
    def is_completed(self):
        return self.get_completion_percentage() >= self.required_score
        
    def get_next_sentence(self):
        available = [s for s in self.sentences if s["sentence"] not in self.completed_sentences]
        if not available:
            return None
        return random.choice(available)
        
    def mark_sentence_completed(self, sentence, points=1):
        self.completed_sentences.add(sentence)
        self.score += self.points_per_sentence * points
        self.total_attempts += 1
        
    def get_progress(self):
        return len(self.completed_sentences), len(self.sentences)
        
    def get_completion_percentage(self):
        return min(self.score, 100)  # Cap at 100%

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
        self.guide = Character("Teacher", "../assets/guide.png", 
                              50, 100, char_width, char_height)
        
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
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize Bedrock client
        self.bedrock_client = BedrockClient(
            model_id=MODEL_ID,
            region_name=AWS_REGION,
            use_mock=USE_MOCK
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
        
        # Initialize levels
        self.initialize_levels()
        
    def initialize_levels(self):
        """Initialize game levels with sentences"""
        # Load saved progress if available
        self.load_progress()
        
        # If no saved progress, create new levels
        if not self.levels:
            self.levels = []
            # Create 10 levels with randomized sentences
            for level_num in range(1, 11):
                # Generate sentences for this level
                level_sentences = self.generate_sentences_for_level(level_num)
                
                # Always select exactly 5 sentences for each level (for 20% per sentence)
                if level_sentences and len(level_sentences) >= 5:
                    selected = random.sample(level_sentences, 5)
                    self.levels.append(Level(level_num, f"Level {level_num}", selected))
                
            # Start with level 1
            self.current_level = 0
            
        self.next_sentence()
    
    def generate_sentences_for_level(self, level_num):
        """Generate sentences for a specific level"""
        difficulty = "easy"
        if level_num >= 8:
            difficulty = "hard"
        elif level_num >= 4:
            difficulty = "medium"
            
        prompt = f"""
        Generate 5 English sentences for pronunciation practice at {difficulty} level.
        Each sentence should be in a different context.
        For each sentence, provide a pronunciation tip focusing on 1-2 challenging words or sounds.
        Format your response as a JSON array of objects with 'sentence', 'context', and 'pronunciation_tip' fields.
        """
        
        try:
            response = self.bedrock_client.generate_response(prompt)
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\\[.*\\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                # Use mock sentences from the client
                return self.bedrock_client._get_mock_sentences(difficulty)
        except Exception as e:
            print(f"Error generating sentences: {e}")
            # Use mock sentences from the client
            return self.bedrock_client._get_mock_sentences(difficulty)
    
    def save_progress(self):
        """Save game progress to file"""
        try:
            save_data = {
                "current_level": self.current_level,
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
    
    def load_progress(self):
        """Load game progress from file"""
        try:
            if os.path.exists("pronunciation_progress.json"):
                with open("pronunciation_progress.json", "r") as f:
                    save_data = json.load(f)
                
                self.current_level = save_data.get("current_level", 0)
                self.levels = []
                
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
        sentence_data = current.get_next_sentence()
        
        if not sentence_data:
            # All sentences in this level have been used
            if current.is_completed():
                self.feedback_display.set_feedback(f"Level {current.level_num} completed! You can move to the next level.", "", True)
                self.next_level_button.enabled = True
            else:
                self.feedback_display.set_feedback(f"You need more practice to complete this level. Try again!", "", False)
                # Reset completed sentences to try again
                current.completed_sentences = set()
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
                # Mark sentence as completed with full points
                current_level = self.levels[self.current_level]
                current_level.mark_sentence_completed(self.current_sentence, 1.0)
                
                self.feedback_display.set_feedback(f"Excellent! You said it perfectly.", 
                                                self.current_pronunciation_tip, True)
                
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
                    # Mark sentence as completed with partial points
                    current_level.mark_sentence_completed(self.current_sentence, 0.8)
                    
                    self.feedback_display.set_feedback(f"Very good! You said: {user_said}", 
                                                    self.current_pronunciation_tip, True)
                    
                    # Wait a moment to show feedback, then move to next sentence
                    time.sleep(1.5)
                    if self.auto_mode:
                        self.next_sentence()
                elif similarity > 0.5:
                    # Don't mark as completed, just give feedback
                    self.feedback_display.set_feedback(f"Not bad. You said: {user_said}", 
                                                    self.current_pronunciation_tip, False)
                    
                    # Try again after showing feedback
                    time.sleep(2)
                    if self.auto_mode:
                        self.play_audio()
                else:
                    # Don't mark as completed, just give feedback
                    self.feedback_display.set_feedback(f"Try again. You said: {user_said}", 
                                                    self.current_pronunciation_tip, False)
                    
                    # Try again after showing feedback
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
        
    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Save progress before quitting
                    self.save_progress()
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click = True
            
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
                level_text = f"Level {current.level_num} - {current.difficulty}"
                level_surface = level_font.render(level_text, True, WHITE)
                self.screen.blit(level_surface, (50, 20))
                
                # Progress
                completed, total = current.get_progress()
                progress_text = f"Progress: {completed}/{total} sentences"
                progress_surface = level_font.render(progress_text, True, WHITE)
                self.screen.blit(progress_surface, (WINDOW_WIDTH - 250, 20))
                
                # Completion percentage
                completion = current.get_completion_percentage()
                completion_text = f"Completion: {int(completion)}%"
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