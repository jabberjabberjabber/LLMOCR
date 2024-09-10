import argparse
import base64
import requests
import io


def encode_file_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class LLMProcessor:
    def __init__(self, api_url, api_password):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_password}",
        }

    def send_image_to_llm(self, base64_image):
        prompt = f"<|im_start|>user\nRepeat verbatim all text on the image.<|im_end|>\n<|im_start|>assistant\n"
        payload = {
            "prompt": prompt,
            "max_length": 2048,
            "images": [base64_image],
            "temp": 0,
        }
        response = requests.post(f"{self.api_url}/api/v1/generate", json=payload, headers=self.headers)
        if response.status_code == 200:
            return response.json()["results"][0].get("text")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Send an image to LLM API")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--api-url", default="http://localhost:5001", help="URL for the LLM API")
    parser.add_argument("--api-password", default="", help="Password for the LLM API")
    args = parser.parse_args()

    llm_processor = LLMProcessor(args.api_url, args.api_password)

        
    if args.image_path.endswith(".jpg") or args.image_path.endswith(".png"):
        base64_image = encode_file_to_base64(args.image_path)
    
    if base64_image:
        print(f"Processing image.")
        result = llm_processor.send_image_to_llm(base64_image)
        if result:
            print("LLM Response:")
            print(result)
        else:
            print(f"Failed to get a response from the LLM.")
    else:
        print("Failed to process the image.")

if __name__ == "__main__":
    main()