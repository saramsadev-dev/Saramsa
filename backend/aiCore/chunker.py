import tiktoken

from .utilities import validate_json_structure
from .aiCompletions import generate_completions

def chunk_text(text, model, max_tokens=3000, overlap=100):
    
    encoding = tiktoken.encoding_for_model(model)  
    encoded_text = encoding.encode(text)

    chunks = []
    start = 0
    while start < len(encoded_text):
        end = start + max_tokens
        chunk = encoded_text[start:end]
        chunks.append(encoding.decode(chunk))
        start = end - overlap  # Move the start forward with overlap

    return chunks

async def process_chunks(text, prompt_instruction, type=0):
    
    chunks = chunk_text(text, 'gpt-4')
    results = []
    for chunk in chunks:
        print ("Chunked\n\n")
        response = await generate_completions(prompt_instruction.replace("<feedback_data>", chunk))
        print (response)
        #formatted_result = validate_json_structure(response, type)
        results.append(response)
    return results

# Combine results if needed
#final_output = "\n".join(results)
#print(final_output)
