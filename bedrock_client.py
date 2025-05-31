import json
import boto3
import time

class BedrockClient:
    def __init__(self, model_id="anthropic.claude-3-haiku-20240307-v1:0", region_name="us-east-1"):
        self.model_id = model_id
        self.region_name = region_name
        self.use_dynamic = True
        
        # Initialize Bedrock client
        try:
            # Try to import credentials from aws_credentials.py
            try:
                import aws_credentials
                # Use hardcoded credentials
                boto3.setup_default_session(
                    aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=aws_credentials.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region_name
                )
                if hasattr(aws_credentials, 'AWS_SESSION_TOKEN') and aws_credentials.AWS_SESSION_TOKEN:
                    boto3.setup_default_session(
                        aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=aws_credentials.AWS_SECRET_ACCESS_KEY,
                        aws_session_token=aws_credentials.AWS_SESSION_TOKEN,
                        region_name=self.region_name
                    )
                print("[INFO] Using credentials from aws_credentials.py")
            except ImportError:
                print("[INFO] No aws_credentials.py found, using default credentials")
            
            # Create the Bedrock client
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            print("[SUCCESS] Successfully initialized Bedrock client")
        except Exception as e:
            print(f"[ERROR] Error initializing Bedrock client: {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            print("[ERROR] Please check your AWS credentials and network connection")
            raise
        
    def generate_response(self, prompt):
        """Generate a response using Amazon Bedrock"""
        print("[INFO] Sending request to Bedrock API...")
        response = self._call_bedrock_api(prompt)
        print("[INFO] Received response from Bedrock API")
        return response
                
    def _call_bedrock_api(self, prompt):
        """Call the Amazon Bedrock API with the given prompt"""
        try:
            print(f"[INFO] Using model: {self.model_id}")
            # For Claude 3 models, use the invoke_model API with messages format
            if "claude-3" in self.model_id.lower():
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "top_p": 0.9
                }
                
                # Invoke the model
                print("[INFO] Invoking Bedrock model...")
                start_time = time.time()
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                end_time = time.time()
                print(f"[INFO] Model response received in {end_time - start_time:.2f} seconds")
                
                # Parse the response
                print("[INFO] Parsing response...")
                response_body = json.loads(response.get('body').read())
                
                # Extract content from Claude 3 response
                if 'content' in response_body:
                    for content_item in response_body['content']:
                        if content_item.get('type') == 'text':
                            return content_item.get('text', '')
                return ""
                
            # For other models, use the standard invoke_model API
            else:
                if "claude-v2" in self.model_id.lower():
                    # Anthropic Claude v2 format
                    request_body = {
                        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                        "max_tokens_to_sample": 2000,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                elif "amazon" in self.model_id.lower():
                    # Amazon Titan format
                    request_body = {
                        "inputText": prompt,
                        "textGenerationConfig": {
                            "maxTokenCount": 2000,
                            "temperature": 0.7,
                            "topP": 0.9,
                        }
                    }
                else:
                    # Default format for other models
                    request_body = {
                        "prompt": prompt,
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                
                # Invoke the model
                print("[INFO] Invoking Bedrock model...")
                start_time = time.time()
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                end_time = time.time()
                print(f"[INFO] Model response received in {end_time - start_time:.2f} seconds")
                
                # Parse the response based on the model
                print("[INFO] Parsing response...")
                response_body = json.loads(response.get('body').read())
                
                if "claude-v2" in self.model_id.lower():
                    return response_body.get('completion', '')
                elif "amazon" in self.model_id.lower():
                    return response_body.get('results', [{}])[0].get('outputText', '')
                else:
                    # Default response parsing
                    return response_body.get('generated_text', '')
                
        except Exception as e:
            print(f"[ERROR] Bedrock API call failed: {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            print("[ERROR] Please check your AWS credentials and network connection")
            raise
            
    def _get_mock_sentences(self, difficulty):
        """Generate default sentences when API calls fail"""
        print(f"[ERROR] Failed to get sentences from Bedrock API for difficulty: {difficulty}")
        print("[INFO] Returning default sentences instead")
        
        # Return a minimal set of default sentences
        return [
            {
                "sentence": "This is a default sentence for practice.",
                "context": "API fallback",
                "pronunciation_tip": "Please try again later when the API is available."
            }
        ]