from openai import OpenAI
import json
import os

DEEPSEEK_API_KEY = "Your API KEY"  
API_BASE = "Your API BASE"

instruction_prepare = """I have a text-to-image generation model that can generate images based on given prompts. However, the model is not perfect and may fail to accurately reflect the prompt or depict the details correctly.
Given a prompt which is a design intention for a text-rich image like infographic or poster, your task is to evaluate whether the generated image correctly fulfill the design intention.
Here is the prompt: {{'id': {pid}, 'prompt': {prompt}}}, \
you need to:
1. identify what should be depicted in the image and its functional purposes.
2. analyze the design intention and create a list of questions based on the key elements that the image should be checked against, including presence of required text elements.
3. consider factors that could impact the aesthetics or visual quality of the image and list relevant questions.
Please also design a scoring criteria for each question, where a score of 1 means "yes (to the question)," 0 means "no," and 0.5 means "partially."
Provide your answer in json format:
{{"id": [prompt id], "prompt": [the prompt], "image_content": [what the image should convey], "reason_evaluation": (here should be a dictionary with 3-5 sets of question and criteria: 'q1': [question 1], 'c1': [criteria 1], 'q2': [question 2], 'c2': [criteria 2]...), "quality_evaluation": (same format as 'reason_evaluation' with 1-3 sets of question and criteria)}}.
"""

client = OpenAI(
  base_url=API_BASE,
  api_key=DEEPSEEK_API_KEY,
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
    prompt_json = "../prompt/textual_image_design.json"
    output_json = "./evaluation_textual_image.json"
  
    
    try:
        with open(output_json, 'r', encoding='utf-8') as fc:
            print("start loading")
            question_criterion = json.load(fc)
            print("finish loading")
            if question_criterion:
                last_element = question_criterion[-1]  # Get the last element
                last_id = last_element['id']
                start = last_id
            else:
                question_criterion = []
                start=0
    except:
            question_criterion = []
            start=0
            
            
    with open(prompt_json, 'r', encoding='utf-8') as f1:
        prompts_json = json.load(f1)
    
    total = 200
    for i in range(start, total):
        
        pid = prompts_json[i]['id']
        prompt = prompts_json[i]['prompt'].strip()
        
        instruction = instruction_prepare.format(pid=pid, prompt=prompt)
        
        # print(instruction)
        
        try:
            answer = ask(instruction)
            data = extract_json(answer)
        except:
            answer = ask(instruction)
            data = extract_json(answer)
            
        question_criterion.append(data)
        
        if i%20 == 0:
            with open(output_json, 'w') as outf:           
                json.dump(question_criterion, outf, ensure_ascii=False, indent=4)
                    
    with open(output_json, 'w') as outf:           
            json.dump(question_criterion, outf, ensure_ascii=False, indent=4)                    
    
            
        