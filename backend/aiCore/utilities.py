import re, json

def flatten_feedback(data):
    feedback_texts = [entry["Feedback"] for entry in data]
    return feedback_texts

def fix_json_string(faulty_json):
    # Step 1: Replace \\n (escaped newlines) with actual newlines
    cleaned_json = faulty_json.replace(r'\\n', '\n')
    
    # Step 2: Replace the escaped quotes \\" with actual quotes
    cleaned_json = cleaned_json.replace(r'\\"', '"')

    # Step 3: Ensure the string is well-formed (this is where you can add custom checks for specific problems)
    # Clean additional escape characters if necessary
    cleaned_json = re.sub(r'\\\\"', '"', cleaned_json)
    
    # Step 1: Replace escaped newlines and quotes
    cleaned_json = cleaned_json.replace(r'\\n', '\n')  # Unescape newlines
    cleaned_json = cleaned_json.replace(r'\\"', '"')   # Unescape quotes
    cleaned_json = cleaned_json.replace(r'json', '')   # Unescape quotes
    
    # Step 2: Remove unwanted stray characters (can be customized based on known stray values)
    # Remove characters that are not part of the expected structure
    cleaned_json = re.sub(r'[^a-zA-Z0-9\s\[\]\{\}\:,\.\-\"\\n]', '', cleaned_json)  # Removing non-alphanumeric, non-structural characters
    
    # Step 3: Fix any extra or missing braces, or stray symbols
    # Ensure the string has valid JSON syntax by fixing stray issues
    cleaned_json = re.sub(r'[\n\r]+', ' ', cleaned_json)  # Convert newlines or unwanted line breaks to space
    cleaned_json = cleaned_json.strip()
    
    
    # Optional: Ensure the string has opening and closing braces for a valid JSON structure
    if not cleaned_json.startswith("{"):
        cleaned_json = "{"+ cleaned_json
    if not cleaned_json.endswith("}"):
        cleaned_json = cleaned_json + "}"
    #print (cleaned_json)
    
    return cleaned_json

# Function to validate the structure of the JSON after parsing
import json

def validate_json_structure(cleaned_json, type):
    try:
        parsed_json = json.loads(cleaned_json)
        
        # Define the expected merged schema structure
        expected_structure = {
            "sentiment_summary": {
                "positive": str,
                "negative": str,
                "neutral": str
            },
            "feature_asba": [
                {
                    "feature": str,
                    "sentiment": {
                        "positive": str,
                        "negative": str,
                        "neutral": str
                    },
                    "keywords": list,
                    "explanations": list
                }
            ],
            "emoji_analysis": {
                "top_emojis": list,
                "overall_sentiment": str
            },
            "positive_keywords": list,
            "negative_keywords": list,
            "action_items": {
                "feature_requests": list,
                "bugs": list,
                "change_requests": list
            }
        }

        # Validate root-level fields
        required_root_fields_sentiment = [
            "sentiment_summary", "feature_asba", "emoji_analysis", 
            "positive_keywords", "negative_keywords"
        ]
        required_root_fields_deepAnalysis = [
            "negative_summary", "action_items"
        ]
        if type == 0: 
            required_root_fields = required_root_fields_sentiment
        else:
            required_root_fields = required_root_fields_deepAnalysis

        if not all(field in parsed_json for field in required_root_fields):
            print("Missing required root-level fields.")
            return None

        # Validate sentiment_summary structure
        sentiment_summary = parsed_json["sentiment_summary"]
        if not all(isinstance(sentiment_summary.get(k), str) 
                  for k in ["positive", "negative", "neutral"]):
            print("Invalid sentiment_summary structure.")
            return None

        # Validate feature_asba structure
        for feature in parsed_json["feature_asba"]:
            if not all(k in feature for k in ["feature", "sentiment", "keywords", "explanations"]):
                print(f"Missing keys in feature entry: {feature.get('feature', 'unknown')}")
                return None
            if not all(isinstance(feature["sentiment"].get(k), str) 
                      for k in ["positive", "negative", "neutral"]):
                print(f"Invalid sentiment structure for feature: {feature['feature']}")
                return None

        # Validate emoji_analysis
        emoji_analysis = parsed_json["emoji_analysis"]
        if not (isinstance(emoji_analysis["top_emojis"], list) and 
                isinstance(emoji_analysis["overall_sentiment"], str)):
            print("Invalid emoji_analysis structure.")
            return None

        # Validate action_items
        action_items = parsed_json["action_items"]
        required_action_categories = ["feature_requests", "bugs", "change_requests"]
        if not all(k in action_items and isinstance(action_items[k], list) 
                  for k in required_action_categories):
            print("Invalid action_items structure.")
            return None

        # If all checks pass
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None