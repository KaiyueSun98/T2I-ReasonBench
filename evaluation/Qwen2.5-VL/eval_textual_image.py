from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import os
import csv
import json
import re
import argparse

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

def ask_qw(messages, processor, model):
    # Preparation for inference
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    # Inference: Generation of the output
    generated_ids = model.generate(**inputs, max_new_tokens=1000)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    
    return output_text



def eval(args):
    model_name = args.model_name
    image_folder = args.image_folder
    output_path = args.output_path
    
    prompt_json = args.prompt_json
    qs_json = args.qs_json
    
    # default: Load the model on the available device(s)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained( 
        "Qwen/Qwen2.5-VL-72B-Instruct", 
        torch_dtype="auto", 
        device_map="auto"
    )

    # We recommend enabling flash_attention_2 for better acceleration and memory saving, especially in multi-image and video scenarios.
    # model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    #     "Qwen/Qwen2.5-VL-7B-Instruct",
    #     torch_dtype=torch.bfloat16,
    #     attn_implementation="flash_attention_2",
    #     device_map="auto",
    # )

    # default processor
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-72B-Instruct")

    # The default range for the number of visual tokens per image in the model is 4-16384.
    # You can set min_pixels and max_pixels according to your needs, such as a token range of 256-1280, to balance performance and cost.
    # min_pixels = 256*28*28
    # max_pixels = 1280*28*28
    # processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)
    

    with open(prompt_json, 'r') as file: 
        prompts = json.load(file)
    
    with open(qs_json, 'r') as file:
        qs = json.load(file)
        
   
    os.makedirs(output_path, exist_ok=True)
    csv_path = os.path.join(output_path,f"{model_name}.csv")
    
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='') as csvreader: 
            reader = csv.reader(csvreader)
            lines = list(reader)  # Read all lines into a list
            line_count = len(lines)  # Count the number of lines
    else:
        line_count = 0
    

    with open(csv_path, 'a', newline='') as csvfile:
        # Create a CSV writer
        csv_writer = csv.writer(csvfile)
        if line_count == 0:
            # Write the header row
            csv_writer.writerow(["id","prompt","answer_1", "answer_2", "score_acc", "answer_3", "score_qual", "score_a_avg", "score_q_avg"])    
            
        all_images = [f for f in os.listdir(image_folder) if f[0].isdigit() and (f[-4:]==".png" or f[-4:]==".jpg")]
        all_images = sorted(all_images)
        print(len(all_images))
        
        evaluated = max(line_count - 1,0)
        
        for i in range(evaluated,len(all_images)):
            image_name = all_images[i]
            num = int(image_name[0:4])-1
            prompt = prompts[num]['prompt']
            
            print(image_name, prompt)
            assert qs[num]["id"] == int(image_name[0:4]), f"Image {image_name} does not match the expected id {i+1}."
            
            qs_reason_question_criteria = qs[num]["reason_evaluation"]
            qs_quality_question_criteria = qs[num]["quality_evaluation"]
            
        
            image_path = os.path.join(image_folder, image_name)
                
            q1 = "Describe this image."   
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image_path,
                        },
                        {"type": "text", "text": q1},
                    ],
                }
            ]
            
            out1 = ask_qw(messages, processor, model)[0]
            print(out1)

    
            # print(prompt)
            q2 = f"""\
Based on the image and your previous description, answer the following questions: q1, q2, ...
For each question, assign a score of 1, 0.5 or 0 according to the corresponding scoring criteria: c1, c2, ...
Here are the questions and criteria: {qs_reason_question_criteria}
Carefully consider the image and each question before responding, then provide your answer in json format:
{{"reason": [your detailed reasoning], "score": [s1,s2, ...]"}}"""
            
            
            new_messages_acc = messages + [
                {
                    "role": "assistant",
                    "content": out1,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", 
                        "text": q2},
                    ],
                }
            ]
            # print(new_messages_acc)
            
            out2 = ask_qw(new_messages_acc, processor, model)[0]
            print(out2)
            json_data_2 = extract_json(out2)
            score_acc = json_data_2['score'] # a list
            # print(score_acc)
            
            
            
            
            
            q3 = f"""\
Based on the image and your previous description, answer the following questions: q1, q2, ...
For each question, assign a score of 1, 0.5 or 0 according to the corresponding scoring criteria: c1, c2, ...
Here are the questions and criteria: {qs_quality_question_criteria}
Carefully consider the image and each question before responding, then provide your answer in json format:
{{"reason": [your detailed reasoning], "score": [s1,s2, ...]"}}"""


            new_messages_quality = messages + [
                {
                    "role": "assistant",
                    "content": out1,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", 
                        "text": q3},
                    ],
                }
            ]
            # print(new_messages)
            
            out3 = ask_qw(new_messages_quality, processor, model)[0]
            print(out3)
            json_data_3 = extract_json(out3)
            score_quality = json_data_3['score'] # a list
            # print(score_quality)
            
            try:
                score_acc_avg = sum(score_acc)/len(score_acc)
                score_quality_avg = sum(score_quality)/len(score_quality)
            except:
                score_acc  = [float(x) for x in score_acc]
                score_quality = [float(x) for x in score_quality]
                score_acc_avg = sum(score_acc)/len(score_acc)
                score_quality_avg = sum(score_quality)/len(score_quality)
                
            
            print(score_acc_avg, score_quality_avg)
            
            csv_writer.writerow([image_name,prompt,out1,out2,score_acc,out3,score_quality,score_acc_avg, score_quality_avg])
            csvfile.flush()
        
        return csv_path

def model_score(csv_path):
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        lines = list(reader)
        accuracy = 0
        quality = 0
        cnt = 0
        for line in lines[1:]:
            try:
                acc_tmp = float(line[-2]) 
                qual_tmp = float(line[-1]) 
                accuracy+=acc_tmp
                quality+=qual_tmp
                cnt+=1
            except:
                continue
            
        accuracy = round(accuracy/cnt * 100, 2)
        quality = round(quality/cnt * 100, 2)
        print("number of images evaluated: ", cnt, "reasoning accuracy score: ",accuracy, "image quality score: ",quality)
        
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["reasoning accuracy score: ",accuracy, "image quality score", quality]) 
                   
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--prompt_json",
        type=str,
        default = "prompts/textual_image_design.json",
        help="path to the prompt",
    )
    parser.add_argument(
        "--qs_json",
        type=str,
        default = "deepseek_evaluation_qs/evaluation_textual_image.json",
        help="path to the evaluation question-criterion pairs",
    )
    
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="name of the T2I model to be evaluated",
    )
    parser.add_argument(
        "--image_folder",
        type=str,
        required=True,
        help="path to images",
    )
    parser.add_argument(
        "--output_path", 
        type=str, 
        default="csv_result/textual_image", 
        help="path to store the image scores")
    
    args = parser.parse_args()
    
    csv_path = eval(args)
    model_score(csv_path)