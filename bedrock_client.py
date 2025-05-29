import json
import random
import time
import re

class BedrockClient:
    def __init__(self, model_id="anthropic.claude-v2", region_name="us-east-1", use_mock=True):
        self.model_id = model_id
        self.region_name = region_name
        self.use_mock = use_mock
        self.use_dynamic = True  # Default to using dynamic sentence generation
        
    def generate_response(self, prompt):
        """Generate a response using Amazon Bedrock or mock data"""
        if self.use_mock:
            return self._generate_mock_response(prompt)
        else:
            # This would be the actual Bedrock API call
            # For now, we'll just use mock data
            return self._generate_mock_response(prompt)
    
    def _generate_mock_response(self, prompt):
        """Generate a mock response based on the prompt"""
        # Add randomization to ensure we get different sentences each time
        seed = int(time.time())
        random.seed(seed)
        
        # Extract difficulty level from prompt
        difficulty = "medium"  # default
        if "easy" in prompt.lower():
            difficulty = "easy"
        elif "hard" in prompt.lower():
            difficulty = "hard"
            
        # Extract focus area from prompt if available
        focus_match = re.search(r"topics related to ([^.]+)", prompt)
        focus = focus_match.group(1) if focus_match else "general topics"
        
        # Use dynamic or static sentences based on setting
        if self.use_dynamic:
            sentences = self._generate_dynamic_sentences(difficulty, focus)
        else:
            sentences = self._get_static_sentences(difficulty)
            random.shuffle(sentences)
            
        return json.dumps(sentences)
    
    def _generate_dynamic_sentences(self, difficulty, focus):
        """Generate dynamic sentences based on difficulty and focus"""
        # Create sentence templates based on difficulty
        templates = self._get_sentence_templates(difficulty)
        
        # Create contexts based on focus area
        contexts = self._get_contexts(focus)
        
        # Generate 8-10 sentences
        num_sentences = random.randint(8, 10)
        sentences = []
        
        for i in range(num_sentences):
            # Select a random template and context
            template = random.choice(templates)
            context = random.choice(contexts)
            
            # Generate a sentence by filling in the template
            sentence = self._fill_template(template, difficulty)
            
            # Find challenging words for pronunciation tip
            words = sentence.split()
            if len(words) >= 3:
                # Choose 1-2 longer words for pronunciation focus
                challenging_words = [w for w in words if len(w) > 5]
                if not challenging_words:
                    challenging_words = [w for w in words if len(w) > 4]
                if not challenging_words:
                    challenging_words = random.sample(words, min(2, len(words)))
                else:
                    challenging_words = random.sample(challenging_words, min(2, len(challenging_words)))
                
                # Clean up words (remove punctuation)
                challenging_words = [w.strip(".,?!") for w in challenging_words]
                
                # Create pronunciation tip
                if len(challenging_words) == 1:
                    pronunciation_tip = f"Focus on '{challenging_words[0]}'"
                else:
                    pronunciation_tip = f"Practice '{challenging_words[0]}' and '{challenging_words[1]}'"
            else:
                pronunciation_tip = "Focus on clear pronunciation"
            
            # Add to sentences list
            sentences.append({
                "sentence": sentence,
                "context": context,
                "pronunciation_tip": pronunciation_tip
            })
        
        return sentences
    
    def _get_sentence_templates(self, difficulty):
        """Get sentence templates based on difficulty"""
        if difficulty == "easy":
            return [
                "Can you tell me where the {place} is?",
                "I would like to {verb} {object}, please.",
                "Do you know what time the {event} starts?",
                "Could you help me find my {item}?",
                "I need to {verb} before {time_period}.",
                "How was your {time_period}?",
                "The {object} is {adjective} today.",
                "I'd like to order the {food}, please.",
                "Where did you {verb} yesterday?",
                "Can I have a {item}, please?"
            ]
        elif difficulty == "medium":
            return [
                "I'm thinking about {verb_ing} a {object} next {time_period}.",
                "Do you have any recommendations for {place_plural} nearby?",
                "We should consider all {adjective} options carefully.",
                "The {event} went well, but we need to follow up.",
                "Could you explain how this {device} works?",
                "I usually {verb} {adverb} during the {time_period}.",
                "The {service} was {adjective} at that {place}.",
                "I need to {verb} my {document} before it {verb_s}.",
                "The {event} is scheduled for tomorrow {time_period}.",
                "I'm interested in learning more about {topic}."
            ]
        else:  # hard
            return [
                "The {professional} {verb_ed} an {adjective} {object} recently.",
                "We need to {adverb} analyze the {adjective} {topic} results.",
                "The {organization} emphasized {abstract_noun} and {abstract_noun2}.",
                "I'm particularly interested in the {adjective} aspects of {topic}.",
                "The {adjective} approach yielded {adjective2} results in {field}.",
                "The {committee} deliberated on {adjective} amendments to the {document}.",
                "The {field} examination revealed {adjective} patterns in {topic}.",
                "The {professional} successfully {verb_ed} three {object_plural} {adverb}.",
                "According to recent {research}, the {phenomenon} has {verb_ed} significantly.",
                "The {organization} has implemented a {adjective} strategy for {abstract_noun}."
            ]
    
    def _get_contexts(self, focus):
        """Get contexts based on focus area"""
        general_contexts = [
            "Casual conversation", "Daily routine", "At work", 
            "Shopping", "At a restaurant", "Travel planning",
            "Social gathering", "Phone conversation", "Meeting new people",
            "Making plans", "Asking for help", "Giving opinions"
        ]
        
        focus_specific = {
            "basic greetings": ["First meeting", "Introduction", "Social event", "Networking"],
            "daily activities": ["Morning routine", "At work", "Evening activities", "Weekend plans"],
            "shopping": ["At the mall", "Online shopping", "Grocery store", "Retail store"],
            "work": ["Business meeting", "Job interview", "Office conversation", "Work project"],
            "travel": ["Vacation planning", "At the airport", "Hotel check-in", "Tourist information"],
            "food": ["Restaurant order", "Cooking instructions", "Food preferences", "Dining out"],
            "health": ["Doctor's appointment", "Fitness goals", "Wellness discussion", "Medical advice"],
            "technology": ["Tech support", "Device instructions", "Software discussion", "Digital tools"],
            "business": ["Corporate meeting", "Financial discussion", "Business strategy", "Market analysis"],
            "arts": ["Gallery visit", "Performance review", "Creative discussion", "Cultural event"]
        }
        
        # Find matching contexts based on focus
        matching_contexts = []
        for key, contexts in focus_specific.items():
            if key in focus.lower():
                matching_contexts.extend(contexts)
        
        # If no specific matches, use general contexts
        if not matching_contexts:
            return general_contexts
        
        # Combine with some general contexts
        return matching_contexts + random.sample(general_contexts, 4)
    
    def _fill_template(self, template, difficulty):
        """Fill in a template with random words to create a sentence"""
        # Word banks for different parts of speech and categories
        words = {
            "place": ["restaurant", "library", "store", "office", "museum", "park", "hotel", "airport", "station", "hospital", "school", "bank"],
            "place_plural": ["restaurants", "stores", "museums", "hotels", "cafes", "shops", "attractions", "locations", "destinations"],
            "verb": ["buy", "find", "order", "schedule", "book", "visit", "call", "meet", "finish", "start", "check", "review", "discuss"],
            "verb_ing": ["buying", "ordering", "scheduling", "booking", "visiting", "calling", "meeting", "planning", "reviewing", "discussing", "considering"],
            "verb_ed": ["discovered", "published", "announced", "analyzed", "launched", "emphasized", "implemented", "developed", "established", "presented"],
            "verb_s": ["expires", "begins", "ends", "starts", "finishes", "closes", "opens", "changes", "improves"],
            "object": ["book", "ticket", "reservation", "appointment", "meeting", "document", "project", "report", "presentation", "plan", "schedule", "device"],
            "object_plural": ["books", "tickets", "reservations", "appointments", "meetings", "documents", "projects", "reports", "presentations", "plans", "businesses", "strategies"],
            "item": ["bag", "phone", "wallet", "keys", "umbrella", "coat", "glasses", "ticket", "card", "book", "pen", "device"],
            "event": ["meeting", "concert", "movie", "show", "presentation", "conference", "class", "session", "appointment", "interview", "discussion"],
            "time_period": ["morning", "afternoon", "evening", "weekend", "week", "month", "year", "holiday", "vacation", "break", "semester", "quarter"],
            "food": ["salad", "pasta", "chicken", "sandwich", "burger", "pizza", "steak", "fish", "dessert", "appetizer", "special", "soup"],
            "adjective": ["interesting", "important", "useful", "helpful", "valuable", "significant", "relevant", "practical", "effective", "efficient", "innovative", "creative", "comprehensive", "detailed", "thorough", "extraordinary", "remarkable", "impressive", "controversial", "revolutionary"],
            "adjective2": ["unprecedented", "significant", "remarkable", "surprising", "promising", "concerning", "encouraging", "disappointing", "fascinating", "intriguing"],
            "adverb": ["quickly", "carefully", "thoroughly", "efficiently", "effectively", "regularly", "frequently", "occasionally", "rarely", "simultaneously", "subsequently", "consequently"],
            "service": ["service", "staff", "assistance", "support", "help", "guidance", "consultation", "advice"],
            "document": ["license", "passport", "certificate", "registration", "membership", "subscription", "account", "contract", "agreement"],
            "device": ["device", "computer", "phone", "tablet", "system", "application", "software", "tool", "machine", "equipment"],
            "topic": ["technology", "science", "business", "education", "healthcare", "environment", "culture", "politics", "economics", "psychology", "sociology", "philosophy", "history", "literature", "art", "music", "design", "engineering"],
            "professional": ["scientist", "researcher", "professor", "expert", "specialist", "consultant", "analyst", "engineer", "developer", "designer", "entrepreneur", "executive", "archaeologist", "environmentalist", "economist"],
            "organization": ["company", "institution", "organization", "corporation", "foundation", "association", "agency", "department", "committee", "commission", "university", "laboratory"],
            "committee": ["committee", "board", "council", "panel", "commission", "assembly", "authority", "body", "group"],
            "field": ["scientific", "medical", "psychological", "sociological", "economic", "historical", "technological", "environmental", "educational", "cultural", "political", "philosophical"],
            "research": ["studies", "research", "findings", "data", "evidence", "analysis", "surveys", "experiments", "investigations", "observations"],
            "phenomenon": ["trend", "pattern", "effect", "impact", "influence", "correlation", "relationship", "connection", "association", "development", "change", "shift"],
            "abstract_noun": ["sustainability", "efficiency", "productivity", "innovation", "creativity", "diversity", "equality", "integrity", "transparency", "accountability", "reliability", "quality", "performance", "growth", "development"],
            "abstract_noun2": ["conservation", "preservation", "protection", "management", "improvement", "enhancement", "optimization", "transformation", "revolution", "evolution"]
        }
        
        # Replace placeholders in template with random words
        result = template
        for placeholder in re.findall(r"\{([^}]+)\}", template):
            if placeholder in words:
                replacement = random.choice(words[placeholder])
                result = result.replace("{" + placeholder + "}", replacement)
        
        return result
    
    def _get_static_sentences(self, difficulty):
        """Get static (predefined) sentences based on difficulty level"""
        easy_sentences = [
            {
                "sentence": "What time does the movie start?",
                "context": "Entertainment",
                "pronunciation_tip": "Focus on 'what time'"
            },
            {
                "sentence": "Can I have a glass of water please?",
                "context": "Restaurant",
                "pronunciation_tip": "Practice 'glass' and 'water'"
            },
            {
                "sentence": "Could you tell me how to get to the station?",
                "context": "Asking for directions",
                "pronunciation_tip": "Pay attention to 'could you'"
            },
            {
                "sentence": "How was your weekend?",
                "context": "Casual conversation",
                "pronunciation_tip": "Focus on 'weekend'"
            },
            {
                "sentence": "I'd like to order the grilled salmon please.",
                "context": "At a restaurant",
                "pronunciation_tip": "Focus on 'grilled'"
            },
            {
                "sentence": "Could you help me find this in my size?",
                "context": "Shopping",
                "pronunciation_tip": "Focus on 'size'"
            },
            {
                "sentence": "I need to schedule a meeting with the team.",
                "context": "Business conversation",
                "pronunciation_tip": "Focus on 'schedule'"
            },
            {
                "sentence": "The weather is nice today, isn't it?",
                "context": "Small talk",
                "pronunciation_tip": "Practice 'weather' and 'isn't it'"
            },
            {
                "sentence": "Where did you go on your last vacation?",
                "context": "Travel conversation",
                "pronunciation_tip": "Focus on 'vacation'"
            },
            {
                "sentence": "I'd like to pay by credit card, please.",
                "context": "Shopping",
                "pronunciation_tip": "Practice 'credit card'"
            }
        ]
        
        medium_sentences = [
            {
                "sentence": "I'm thinking about taking a vacation next month.",
                "context": "Making plans",
                "pronunciation_tip": "Practice 'thinking' and 'vacation'"
            },
            {
                "sentence": "Do you have any recommendations for restaurants nearby?",
                "context": "Tourist question",
                "pronunciation_tip": "Focus on 'recommendations' and 'restaurants'"
            },
            {
                "sentence": "I usually take public transportation to work every day.",
                "context": "Daily routine",
                "pronunciation_tip": "Practice 'public transportation'"
            },
            {
                "sentence": "We should consider all available options carefully.",
                "context": "Decision making",
                "pronunciation_tip": "Practice 'consider' and 'available'"
            },
            {
                "sentence": "The presentation went well, but we need to follow up.",
                "context": "Work discussion",
                "pronunciation_tip": "Focus on 'presentation' and 'follow up'"
            },
            {
                "sentence": "Could you explain how this device works?",
                "context": "Technology",
                "pronunciation_tip": "Focus on 'explain' and 'device'"
            },
            {
                "sentence": "The customer service was excellent at that hotel.",
                "context": "Travel review",
                "pronunciation_tip": "Practice 'customer service'"
            },
            {
                "sentence": "I need to renew my driver's license before it expires.",
                "context": "Everyday task",
                "pronunciation_tip": "Practice 'renew' and 'expires'"
            },
            {
                "sentence": "The conference call is scheduled for tomorrow afternoon.",
                "context": "Work planning",
                "pronunciation_tip": "Focus on 'conference' and 'scheduled'"
            },
            {
                "sentence": "I'm interested in learning more about your company culture.",
                "context": "Job interview",
                "pronunciation_tip": "Practice 'interested' and 'culture'"
            }
        ]
        
        hard_sentences = [
            {
                "sentence": "The statistics show a significant correlation between variables.",
                "context": "Research presentation",
                "pronunciation_tip": "Focus on 'statistics' and 'correlation'"
            },
            {
                "sentence": "The archaeologist discovered an extraordinary ancient civilization.",
                "context": "Historical discovery",
                "pronunciation_tip": "Focus on 'archaeologist' and 'extraordinary'"
            },
            {
                "sentence": "The pharmaceutical company announced a revolutionary treatment.",
                "context": "News report",
                "pronunciation_tip": "Focus on 'pharmaceutical' and 'revolutionary'"
            },
            {
                "sentence": "The university professor published a controversial research paper.",
                "context": "Academic news",
                "pronunciation_tip": "Focus on 'controversial' and 'research'"
            },
            {
                "sentence": "We need to thoroughly analyze the quarterly financial results.",
                "context": "Business meeting",
                "pronunciation_tip": "Practice 'thoroughly' and 'quarterly'"
            },
            {
                "sentence": "The entrepreneur successfully launched three businesses simultaneously.",
                "context": "Business profile",
                "pronunciation_tip": "Practice 'entrepreneur' and 'simultaneously'"
            },
            {
                "sentence": "The environmentalist emphasized sustainability and conservation.",
                "context": "Environmental talk",
                "pronunciation_tip": "Focus on 'environmentalist' and 'sustainability'"
            },
            {
                "sentence": "I'm particularly interested in the psychological aspects.",
                "context": "Academic discussion",
                "pronunciation_tip": "Practice 'particularly' and 'psychological'"
            },
            {
                "sentence": "The interdisciplinary approach yielded unprecedented results.",
                "context": "Scientific research",
                "pronunciation_tip": "Focus on 'interdisciplinary' and 'unprecedented'"
            },
            {
                "sentence": "The parliamentary committee deliberated on constitutional amendments.",
                "context": "Political news",
                "pronunciation_tip": "Practice 'parliamentary' and 'constitutional'"
            }
        ]
        
        if difficulty == "easy":
            return easy_sentences
        elif difficulty == "medium":
            return medium_sentences
        else:
            return hard_sentences
    
    def _get_mock_sentences(self, difficulty):
        """Legacy method for backward compatibility"""
        if self.use_dynamic:
            return self._generate_dynamic_sentences(difficulty, "general topics")
        else:
            return self._get_static_sentences(difficulty)