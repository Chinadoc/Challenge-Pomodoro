import os
import base64
import json
from dotenv import load_dotenv
import openai
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import sys

def print_error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def test_openai_connection():
    """Test the OpenAI API connection with a simple request"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
            max_tokens=5
        )
        print("✅ OpenAI API connection successful!")
        print("Response:", response)
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        if hasattr(e, 'response'):
            try:
                print("Error details:", e.response.json())
            except:
                print("Could not parse error details")
        return False

def test_dalle():
    """Test DALL-E image generation with a simple prompt"""
    try:
        print("\nTesting DALL-E image generation...")
        response = openai.Image.create(
            prompt="A simple red circle on a white background",
            n=1,
            size="256x256"
        )
        print("✅ DALL-E API call successful!")
        print("Response keys:", response.keys())
        if 'data' in response and len(response['data']) > 0:
            print("Image URL:", response['data'][0].get('url', 'No URL in response'))
        return True
    except Exception as e:
        print(f"❌ DALL-E API call failed: {str(e)}")
        if hasattr(e, 'response'):
            try:
                print("Error details:", e.response.json())
            except:
                print("Could not parse error details")
        return False

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Set the API key for the openai module
    if api_key:
        openai.api_key = api_key
        print(f"Using OpenAI API key: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Test the API connection
    if not test_openai_connection():
        print("\n⚠️  OpenAI API connection test failed. Please check your API key and internet connection.")
        if not test_dalle():
            return
    else:
        # Only test DALL-E if the basic API connection works
        test_dalle()
    
    output_dir = os.path.join(os.path.dirname(__file__), "assets", "achievements")
    os.makedirs(output_dir, exist_ok=True)
    
    # List of achievement prompts with custom icons
    achievement_prompts = [
        "A minimalist flat icon of a bird with the sun rising in the background, representing 'Early Bird' achievement, flat color vector style, 64x64 PNG, pastel colors, clean lines",
        "A minimalist flat icon of a runner crossing a finish line, representing 'Marathoner' achievement, flat color vector style, 64x64 PNG, vibrant colors, clean lines",
        "A minimalist flat icon of a medal with a weekend calendar, representing 'Weekend Warrior' achievement, flat color vector style, 64x64 PNG, bold colors, clean lines",
        "A minimalist flat icon of an owl on a moon, representing 'Night Owl' achievement, flat color vector style, 64x64 PNG, dark theme, clean lines",
        "A minimalist flat icon of a 7-day calendar with checkmarks, representing 'Perfect Week' achievement, flat color vector style, 64x64 PNG, clean design",
        "A minimalist flat icon of a brain with a lock symbol, representing 'Focused Mind' achievement, flat color vector style, 64x64 PNG, simple and clean",
        "A minimalist flat icon of a lightning bolt with a clock, representing 'Quick Draw' achievement, flat color vector style, 64x64 PNG, electric colors",
        "A minimalist flat icon of a scale balancing work and break, representing 'Balanced' achievement, flat color vector style, 64x64 PNG, clean design",
        "A minimalist flat icon of a sun with an alarm clock, representing 'Early Riser' achievement, flat color vector style, 64x64 PNG, warm colors",
        "A minimalist flat icon of a lightning bolt with the number 4, representing 'Power Hour' achievement, flat color vector style, 64x64 PNG, energetic colors"
    ]
    
    # Achievement names corresponding to each prompt
    achievement_names = [
        "Early Bird",
        "Marathoner",
        "Weekend Warrior",
        "Night Owl",
        "Perfect Week",
        "Focused Mind",
        "Quick Draw",
        "Balanced",
        "Early Riser",
        "Power Hour"
    ]
    
    for i in range(len(achievement_prompts)):
        filename = f"{achievement_names[i].replace(' ', '_').lower()}.png"
        filepath = os.path.join(output_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"{filename} exists, skipping.")
            continue
            
        print(f"Generating icon {filename} with prompt: {achievement_prompts[i]}")
        
        try:
            # Try to generate the image using DALL-E
            try:
                response = openai.Image.create(
                    prompt=achievement_prompts[i],
                    n=1,
                    size="256x256",
                    response_format="b64_json"
                )
                
                if not response.get('data') or not response['data'][0].get('b64_json'):
                    raise ValueError("No image data in API response")
                
                # Decode and save the image
                img_data = base64.b64decode(response['data'][0]['b64_json'])
                img = Image.open(io.BytesIO(img_data))
                img = img.convert("RGBA")
                img = img.resize((64, 64), Image.LANCZOS)
                img.save(filepath, "PNG")
                print(f"✅ Generated {filename} using DALL-E")
                
            except Exception as e:
                print(f"⚠️  DALL-E generation failed, falling back to placeholder: {str(e)}")
                # Create a simple placeholder image
                img = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                
                # Add a border
                draw.rectangle([0, 0, 63, 63], outline="#888888", width=2)
                
                # Add text
                try:
                    # Try to use a nice font, fallback to default
                    try:
                        font = ImageFont.truetype("Arial", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    # Add achievement number
                    text = str(i)
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    x = (64 - text_width) // 2
                    y = (64 - text_height) // 2
                    draw.text((x, y), text, fill="#000000", font=font)
                except Exception as e:
                    print(f"⚠️  Couldn't add text to placeholder: {str(e)}")
                
                img.save(filepath, "PNG")
                print(f"✅ Created placeholder for {filename}")
                
        except Exception as e:
            print(f"❌ Fatal error with {filename}: {str(e)}")
            if hasattr(e, 'response'):
                try:
                    if hasattr(e.response, 'json'):
                        print(f"Error details: {e.response.json()}")
                    elif hasattr(e.response, 'text'):
                        print(f"Error response: {e.response.text}")
                except:
                    pass

if __name__ == "__main__":
    main()
    print("\nNote: If you're seeing API errors, please check:")
    print("1. Your OpenAI API key is valid and has available credits")
    print("2. Your account has access to the DALL-E API")
    print("3. You're not hitting any rate limits")
    print("4. The API endpoint is accessible from your location")
