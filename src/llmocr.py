import sys
import os
import io
import requests
import argparse

from typing import Optional, List
from image_processor import ImageProcessor

class LLMProcessor:
    def __init__(self, api_url, api_password, instruction):
        self.instruction = instruction
        self.max_length = 2048
        self.top_p = 1
        self.top_k = 0
        self.temperature = 0.1
        self.rep_pen = 1
        self.min_p = 0.1
        self.api_url = api_url
        self.api_password = api_password
        self.image_processor = ImageProcessor(max_dimension=896)
        self.system_instruction = "You are a helpful image capable model"
        
    def process_file(self, file_path):
        """Send frames to API for analysis"""
        image, output_path = self.image_processor.process_image(str(file_path))
        user_content = [{"type": "text", "text": self.instruction}]    
        if image:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image}"
                }
            })    
        try:
            messages = [
                {"role": "system", "content": self.system_instruction},
                {
                    "role": "user", 
                    "content": user_content 
                }
            ]
            
            payload = {
                "messages": messages,
                "max_tokens": self.max_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "rep_pen": self.rep_pen,
                "min_p": self.min_p
            }
            
            endpoint = f"{self.api_url}/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.api_password:
                headers["Authorization"] = f"Bearer {self.api_password}"
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                
                if "message" in response_json["choices"][0]:
                    
                    return response_json["choices"][0]["message"]["content"], output_path
                
                else:
                    
                    return response_json["choices"][0].get("text", ""), output_path
            
            return None
            
        except Exception as e:
            raise Exception(f"Error in API call: {str(e)}")        
        
    def save_result(self, result: str, output_path: str) -> bool:
        """Save the processing result to a file"""
        txt_output_path = os.path.splitext(output_path)[0] + ".txt"
        try:
            with open(txt_output_path, "w", encoding="utf-8") as output_file:
                output_file.write(result)
            return True
        except Exception as e:
            print(f"Error saving to {txt_output_path}: {e}")
            return False
        
def run(api_url, api_password, file_list, instruction):
    processor = LLMProcessor(api_url, api_password, instruction)
    try:
        for i, file_path in enumerate(file_list):
            result, output_path = processor.process_file(file_path)
            if result:
                print(f"----\nFile: {output_path}\n----\nResult: {result}\n")
                processor.save_result(result, output_path)
    except Exception as e:
        return None

def main():
    parser = argparse.ArgumentParser(description="LLM OCR")
    parser.add_argument("--files", default="", help="List of files")
    parser.add_argument(
        "--api-url", default="http://localhost:5001", help="URL for the LLM API"
    )
    parser.add_argument(
        "--api-password", default="", help="Password for the LLM API"
    )
    parser.add_argument("--instruction", default="Transcribe any text on the image.", help="Instruction for the model")
    
    args = parser.parse_args()
    if isinstance(args.files, str):
        file_list = args.files.split(" ")
    else:
        return
        
    run(args.api_url, args.api_password, file_list, args.instruction)
    
if __name__ == "__main__":
    main()
