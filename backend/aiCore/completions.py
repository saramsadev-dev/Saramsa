import openai
import os

# Ideally use environment variables
openai.api_type = "azure"
openai.api_base = "https://saramsa-ai.openai.azure.com/"
openai.api_version = "2024-05-01-preview"
openai.api_key = "5PGUZoFqwJK96jASVRMAeb8HJtoMUvlvMSvA8eTniDqvLkdyiBhnJQQJ99ALACYeBjFXJ3w3AAABACOGYDFn"

DEPLOYMENT_NAME = "gpt-4o-mini"

def analyze_comments(prompt):
    try:
        response = openai.ChatCompletion.create(
            engine=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        answer = response["choices"][0]["message"]["content"]
        import json
        return json.loads(answer)
    except Exception as e:
        return {"error": str(e)}
