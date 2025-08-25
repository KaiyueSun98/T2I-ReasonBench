from openai import OpenAI
import json
import os

DEEPSEEK_API_KEY = "Your API KEY"  
API_BASE = "Your API BASE"

instruction_prepare = """\
I have a text-to-image generation model that can generate images based on given prompts. However, the prompts given to the model imply scientific laws (e.g., physics, chemistry, biology, or astronomy) that can affect how the scene looks without explicit explanation.
Your task is to evaluate whether the generated image accurately reflects the scientific law and correctly portrays the resulting scene.
Given the prompt: {{'id': {pid}, 'prompt': {prompt}, 'explicit_meaning': {explicit_meaning}}}, \
you need to:
1. describe what should be depicted in the image in order to fully and accurately reflect the explicit meaning of the prompt.
2. identify any scientific law(s) that the model needs to infer from the prompt, and create a list of questions that check whether the image correctly demonstrates and complies with these scientific laws.
3. consider other elements or details in the prompt that are not directly affected by the scientific law(s), create a list of questions that check if the image accurately represents these additional key elements.
4. consider factors that could impact the aesthetics or visual quality of the image and list relevant questions.
Please also design a scoring criteria for each question, where a score of 1 means "yes (to the question)," 0 means "no," and 0.5 means "partially."
Provide your answer in json format:
{{"id": [prompt id], "prompt": [the prompt], 'explicit_meaning': [the explicit meaning], "image_content": [what the image should depict], "scientific_evaluation": (here should be a dictionary with 2-4 sets of question and criteria: 'q1': [question 1], 'c1': [criteria 1], 'q2': [question 2], 'c2': [criteria 2]...), "other_details_evaluation": (same format as 'scientific_evaluation' with 1-3 sets of question and criteria), "quality_evaluation": (same format as 'scientific_evaluation' with 1-3 sets of question and criteria)}}.
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
    prompt_json = "../prompt/scientific_reasoning.json"
    output_json = "./evaluation_scientific.json"
  
    
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
        meaning = prompts_json[i]['explicit_meaning'].strip()
        
        instruction = instruction_prepare.format(pid=pid, prompt=prompt, explicit_meaning=meaning)
        
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
    
            
        