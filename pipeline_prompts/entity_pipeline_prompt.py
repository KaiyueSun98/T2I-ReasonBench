import requests
import base64
import os
from PIL import Image
import io
from openai import OpenAI
import json
import re



API_KEY = "Your API KEY"
API_BASE = "Your API Base"
MODEL = "Your Model Name"



entity_pipeline_instruction = """Your task is to transform a prompt with unnamed entities into complete, visually explicit, contextually accurate depiction for a text-to-image generation model.  
Given the prompt and its {{'id': {pid}, 'prompt': {prompt}}}.
Rules to Follow: 
1. Identify the Hidden Entity:  
   - Research and reason to confirm the exact subject using reliable sources
   - Replace vague references with unmistakable imagery, confirm: Who/What, When, Where  
   - Ask: What would this entity look like in the context of the prompt?
2. Include Supporting Elements/Context: (below are some examples, you can adjust according to needs):
   - Iconic Visual Cues
   - Temporal cues 
   - Environment details/Location 
4. Avoid:
   - Ambiguous references ("a famous scientist")  
   - Anachronisms  
  
Final Output Format:
- You should first think about what the image should look like.
- Then describe it in a way that the text-to-image model can understand. Keep it 2-4 sentences. Prioritize key visuals.  
- Provide your answer in json format, including the id, reasoning steps and the prompt after your reasoning: {{"id": [id], "reason": [reasoning steps], "reason_prompt": "[within 70 words]"}}"""



def extract_json(text):
    # Use a regular expression to find the JSON part
    json_pattern = r'\{.*?\}'
    match = re.search(json_pattern, text, re.DOTALL)

    if match:
        json_string = match.group(0)  # Extract the matched JSON string
        try:
            # Parse the JSON string
            json_data = json.loads(json_string)
            # print("Extracted JSON:", json_data)
        except json.JSONDecodeError as e:
            print("Failed to decode JSON:", e)
    else:
        print("No JSON found in the text.")
    return json_data


def ask(pid,prompt):
    instruction = entity_pipeline_instruction.format(pid=pid,prompt=prompt.strip())
    print(instruction)
    
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE
    )

    completion = client.chat.completions.create(
        model = MODEL,
        messages=[
            {"role": "user", "content": instruction}
        ]
    )
    answer = completion.choices[0].message.content
    print(answer)
    return answer


if __name__ == "__main__":
    
    prompts = "../prompts/entity_reasoning.json"
    output_json = "./entity_pipeline_prompts.json"

    

    with open(output_json, 'r', encoding='utf-8') as fc:
        print("start loading")
        rewrite = json.load(fc)
        print("finish loading")
        if isinstance(rewrite, list) and rewrite:  # Check if data is a non-empty list
            last_element = rewrite[-1]  # Get the last element
            last_id = last_element['id']
            start = last_id
        else:
            rewrite = []
            start=0


    with open(prompts, 'r', encoding='utf-8') as f1:
        prompts_json = json.load(f1)
                
        for i, prompt_json in enumerate(prompts_json):
            pid = prompt_json['id']
            prompt = prompt_json['prompt']
            # print(pid, prompt)
                
            try: 
                answer = ask(pid, prompt)
                data = extract_json(answer)
            except:
                answer = ask(pid, prompt)
                data = extract_json(answer)
                
            rewrite.append(data)
            
    with open(output_json, 'w') as outf:           
        json.dump(rewrite, outf, ensure_ascii=False, indent=4)
                
        
            