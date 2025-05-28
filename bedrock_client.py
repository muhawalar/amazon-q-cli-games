import boto3
import json
import os
import random

class BedrockClient:
    def __init__(self, model_id="anthropic.claude-3-sonnet-20240229-v1:0", region_name=None, use_mock=False):
        """Initialize the Bedrock client"""
        self.model_id = model_id
        self.use_mock = use_mock
        
        if not self.use_mock:
            region = region_name or os.environ.get('AWS_REGION', 'us-east-1')
            try:
                self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
            except Exception as e:
                print(f"Failed to initialize Bedrock client: {e}")
                print("Falling back to mock responses")
                self.use_mock = True
    
    def generate_response(self, prompt, max_tokens=500):
        """Generate a response from the AI model"""
        if self.use_mock:
            return self._generate_mock_response(prompt)
            
        try:
            # Format request based on model
            if "anthropic.claude" in self.model_id:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": prompt}]
                        }
                    ]
                }
            else:
                raise ValueError(f"Unsupported model: {self.model_id}")
            
            # Make API call
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            print(f"Error generating response: {e}")
            print("Falling back to mock response")
            return self._generate_mock_response(prompt)
            
    def _generate_mock_response(self, prompt):
        """Generate mock sentences for pronunciation practice"""
        if "pronunciation" in prompt.lower():
            # Return mock sentences based on difficulty
            difficulty_terms = ["easy", "medium", "hard", "advanced"]
            difficulty = next((d for d in difficulty_terms if d in prompt.lower()), "medium")
            
            sentences = self._get_mock_sentences(difficulty)
            return json.dumps(random.sample(sentences, min(5, len(sentences))))
        
        return "Mock response: Unable to process this request."
        
    def _get_mock_sentences(self, difficulty):
        """Get mock sentences based on difficulty level"""
        if difficulty == "easy":
            return [
                {"sentence": "I need to schedule a meeting with the team.", 
                 "context": "Business conversation", 
                 "pronunciation_tip": "Focus on 'schedule'"},
                {"sentence": "Could you tell me how to get to the station?", 
                 "context": "Asking for directions", 
                 "pronunciation_tip": "Pay attention to 'could you'"},
                {"sentence": "I'd like to order the grilled salmon please.", 
                 "context": "At a restaurant", 
                 "pronunciation_tip": "Focus on 'grilled'"},
                {"sentence": "The weather is nice today, isn't it?", 
                 "context": "Small talk", 
                 "pronunciation_tip": "Practice 'weather' and 'isn't it'"},
                {"sentence": "Could you help me find this in my size?", 
                 "context": "Shopping", 
                 "pronunciation_tip": "Focus on 'size'"},
                {"sentence": "What time does the movie start?", 
                 "context": "Entertainment", 
                 "pronunciation_tip": "Focus on 'what time'"}
            ]
        elif difficulty == "medium":
            return [
                {"sentence": "I'm thinking about taking a vacation next month.", 
                 "context": "Making plans", 
                 "pronunciation_tip": "Practice 'thinking' and 'vacation'"},
                {"sentence": "Do you have any recommendations for restaurants nearby?", 
                 "context": "Tourist question", 
                 "pronunciation_tip": "Focus on 'recommendations' and 'restaurants'"},
                {"sentence": "I need to renew my driver's license before it expires.", 
                 "context": "Everyday task", 
                 "pronunciation_tip": "Practice 'renew' and 'expires'"},
                {"sentence": "The presentation went well, but we need to follow up.", 
                 "context": "Work discussion", 
                 "pronunciation_tip": "Focus on 'presentation' and 'follow up'"},
                {"sentence": "I usually take public transportation to work every day.", 
                 "context": "Daily routine", 
                 "pronunciation_tip": "Practice 'public transportation'"},
                {"sentence": "Could you explain how this device works?", 
                 "context": "Technology", 
                 "pronunciation_tip": "Focus on 'explain' and 'device'"}
            ]
        else:  # hard or advanced
            return [
                {"sentence": "The pharmaceutical company announced a revolutionary treatment.", 
                 "context": "News report", 
                 "pronunciation_tip": "Focus on 'pharmaceutical' and 'revolutionary'"},
                {"sentence": "I'm particularly interested in the psychological aspects.", 
                 "context": "Academic discussion", 
                 "pronunciation_tip": "Practice 'particularly' and 'psychological'"},
                {"sentence": "The statistics show a significant correlation between variables.", 
                 "context": "Research presentation", 
                 "pronunciation_tip": "Focus on 'statistics' and 'correlation'"},
                {"sentence": "The entrepreneur successfully launched three businesses simultaneously.", 
                 "context": "Business profile", 
                 "pronunciation_tip": "Practice 'entrepreneur' and 'simultaneously'"},
                {"sentence": "The environmentalist emphasized sustainability and conservation.", 
                 "context": "Environmental talk", 
                 "pronunciation_tip": "Focus on 'environmentalist' and 'sustainability'"},
                {"sentence": "The archaeologist discovered an extraordinary ancient civilization.", 
                 "context": "Historical discovery", 
                 "pronunciation_tip": "Focus on 'archaeologist' and 'extraordinary'"}
            ]