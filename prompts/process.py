from openai import OpenAI
import json
import re
import os
DEEPSEEK_KEY = "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"

instruction_prepare = """\
I have a text-to-image generation model that can generate images based on given prompts. However, the model is not perfect and may fail to accurately capture the meaning of the prompt or depict it correctly.
Your task is to evaluate the generated image based on a specific prompt that contains an idiom.
Given the prompt: {{'id': {pid}, 'prompt': {prompt}, 'idiom': {idiom}, 'idiom_meaning': {idiom_meaning}}}, \
you need to:
1. identify what should be depicted in the image or the meaning the image should convey.
2. analyze the prompt and create a list of questions based on the key elements that the image should be checked against.
3. consider factors that could impact the aesthetics or visual quality of the image and list relevant questions.
Please also design a scoring criteria for each question, where a score of 1 means "yes (to the question)," 0 means "no," and 0.5 means "partially."
Provide your answer in json format:
{{"id": [prompt id], "prompt": [the prompt], "image_content": [what the image should convey], "reason_evaluation": (here should be a dictionary with 3-5 sets of question and criteria: 'q1': [question 1], 'c1': [criteria 1], 'q2': [question 2], 'c2': [criteria 2]...), "aesthetic_evaluation": (same format as 'reason_evaluation' with 1-3 sets of question and criteria)}}.
"""

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=DEEPSEEK_KEY,
)

def extract_json(string):
    # Find the start and end positions of the JSON part
    start = string.find('{')
    end = string.rfind('}') + 1

    # Extract the JSON part from the string
    json_part = string[start:end]

    # Load the JSON part as a dictionary
    try:
        json_data = json.loads(json_part)
    except json.JSONDecodeError:
        # Handle the case when the JSON part is not valid
        print("Invalid JSON part")
        return None

    return json_data


def ask(instruction):
    completion = client.chat.completions.create(
    #   extra_headers={
    #     "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    #     "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
    #   },
    #   extra_body={},
    model="deepseek/deepseek-r1-0528",
    messages=[
        {
        "role": "user",
        "content": instruction
        }
    ]
    )
    answer = completion.choices[0].message.content
    print(answer)
    return answer
    
    
    
if __name__ == "__main__":
    # prompt_json = "/group/xihuiliu/sky/reasoning/idiom/benchmark/selected_idioms_merged.json"
    # prompt_txt = "/group/xihuiliu/sky/reasoning/idiom/benchmark/idiom_200.txt"
    # output_json = "/group/xihuiliu/sky/reasoning/github/prompts/idiom_interpretation.json"
    
    
    # prompt_txt = "/group/xihuiliu/sky/reasoning/text_image/benchmark/prompt_200_final.txt"
    # output_json = "/group/xihuiliu/sky/reasoning/github/prompts/textual_image_design.json"
    
    # prompt_txt = "/group/xihuiliu/sky/reasoning/common_sense/prompts.txt"
    # rewrite_txt = "/group/xihuiliu/sky/reasoning/common_sense/rewrite.txt"
    # output_json = "/group/xihuiliu/sky/reasoning/github/prompts/entity.json"
    
    prompt_txt = "/group/xihuiliu/sky/reasoning/physics/prompts_physics.txt"    
    rewrite_txt = "/group/xihuiliu/sky/reasoning/physics/prompts_physics_rewrite.txt"
    physics_json = "/group/xihuiliu/sky/reasoning/physics/physics.json"
    output_json = "/group/xihuiliu/sky/reasoning/github/prompts/scientific.json"
    
    try:
        with open(output_json, 'r', encoding='utf-8') as fc:
            print("start loading")
            written = json.load(fc)
            print("finish loading")
            if written:
                last_element = written[-1]  # Get the last element
                last_id = last_element['id']
                start = last_id
            else:
                written = []
                start=0
    except:
            written = []
            start=0
            
            
    with open(physics_json, 'r', encoding='utf-8') as f3:
        p_json = json.load(f3)
    with open(prompt_txt, 'r', encoding='utf-8') as f2:
        prompts_txt = f2.readlines()
    with open(rewrite_txt, 'r', encoding='utf-8') as f1:
        rewrites_txt = f1.readlines()
    
    total = 200
    for i in range(start, total):
    # for i in []:
        
        # if 'usage_pdf' in prompts_json[i]:
        #     prompt = prompts_json[i]['usage_pdf'].strip()
        # else:
        #     prompt = prompts_json[i]['usage'].strip()
            
        # assert prompt == prompts_txt[i].strip()
        
        # idiom = prompts_json[i]['idiom'].strip()
        # meaning = prompts_json[i]['meaning'].strip()
        # tag = prompts_json[i]['tag'].strip()
        
        
        prompt = prompts_txt[i].strip()
        rewrite =  rewrites_txt[i].strip()
        tag = p_json[i]["category"].strip()
        assert prompt == p_json[i]["prompt"].strip()
        # if i<40:
        #     tag = "Infographic"
        # if i>40 and i<80:
        #     tag = "Poster"
        # if i>80 and i<160:
        #     tag = "Real-world textual images"
        # if i>=160 and i<180:
        #     tag = "Document"
        # if i>=180 and i<190:
        #     tag = "Table"
        # if i>=190:
        #     tag = "Diagram"
        
        # if i<23:
        #     tag = "Event"
        # if i>=23 and i<72:
        #     tag = "Celebrity"
        # if i>=72 and i<99:
        #     tag = "Artifact"
        # if i>=99 and i<120:
        #     tag = "Architecture"
        # if i>=120 and i<136:
        #     tag = "Nature"
        # if i>=136 and i<156:
        #     tag = "Animal"
        # if i>=156 and i<174:    
        #     tag = "Plant"
        # if i>=174:
        #     tag = "Food"
        
        data = {"id": i+1, 
                "prompt": prompt,
                "explicit_meaning": rewrite,
                # "idiom": idiom,
                # "idiom_meaning": meaning,
                "tag": tag,
                }

        written.append(data)
                    
    with open(output_json, 'w') as outf:           
            json.dump(written, outf, ensure_ascii=False, indent=4)                    
    
            
        