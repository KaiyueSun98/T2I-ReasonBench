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


scientific_pipeline_instruction = """Your task is to transform an abstract scientific scenario into visually accurate, law-driven depiction for a text-to-image generation model. The model won’t infer science, so please describe only the observable phenomena resulting from the prompt’s underlying principles (physics/chemistry/biology/astronomy).  
Given the prompt and its {{'id': {pid}, 'prompt': {prompt}}}.
Rules to Follow: 
1. Identify the Governing Law(s): 
   - Identify the scientific principle(s) involved (e.g., "Wood vs. iron in water → Archimedes’ principle (buoyancy)").  
   - Ask: What visible outcome does this law produce?

2. Describe Observable Effects:
   - Focus on measurable, visual consequences due the scientific principle(s).
   - Specify visual details (below are some examples, you can adjust according to needs):
     - Positions 
     - Light/Color 
     - Motion/Action  
     - Scale/Proportion

3. Prioritize Key Phenomena:
   - Highlight causal relationships  
   - Omit non-visible elements 

4. Contextualize for Realism (if necessary):
   - Add environmental details
   - Include reference objects

Final Output Format:
- You should first think about what the image should look like.
- Then describe it in a way that the text-to-image model can understand. Keep it 3-5 sentences. Prioritize key visuals.  
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
    instruction = scientific_pipeline_instruction.format(pid=pid,prompt=prompt.strip())
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
    
    prompts = "../prompts/scientific_reasoning.json"
    output_json = "./scientific_pipeline_prompts.json"

    

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
                
        
            