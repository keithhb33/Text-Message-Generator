import openai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
import moviepy.editor as mpe
from elevenlabs import generate, save, play
import os
import glob

# Function to get text from OpenAI GPT
def get_chatgpt_response(prompt, api_key):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an actor in a movie texting another character. You should act crazy in this conversation for the purpose of the show. Imagine it as a text conversation. Give each person a real first-name prefixed with 'M-' for male or 'F-' for female. Don't use perfect capitalization and punctuation or emojis, it should be casual texting style, but don't overdo it and don't use 'u' for 'you' in the chats. Make sure each conversation/story has a conclusion/ending without a cliffhanger illustrated within the text messages. Format the text like 'NAME: DIALOGUE' and don't include anything other than dialogue."},
            {"role": "user", "content": prompt},
        ]
    )
    answer = response['choices'][0]['message']['content']
    print(answer)
    return answer.replace("*", "").replace(" ur ", " your ")

# Function to create an iMessage style conversation bubble with rounded corners and tail
def draw_text_bubble(draw, text, font, bubble_color, text_color, max_width, tail_position="left"):
    padding = 20
    corner_radius = 25  # Radius for the rounded corners
    tail_width = 10
    tail_height = 15

    # Wrap the text
    wrapped_text = textwrap.fill(text, width=30)
    
    # Calculate text size
    text_size = draw.textsize(wrapped_text, font=font)
    
    # Create bubble with tail
    bubble_width = text_size[0] + 2 * padding + tail_width
    bubble_height = text_size[1] + 2 * padding

    bubble = Image.new('RGBA', (bubble_width, bubble_height + tail_height), (255, 255, 255, 0))
    bubble_draw = ImageDraw.Draw(bubble)

    # Draw rounded rectangle
    bubble_draw.rounded_rectangle(
        [(tail_width if tail_position == "left" else 0, 0), (bubble_width - (0 if tail_position == "left" else tail_width), bubble_height)], 
        radius=corner_radius, 
        fill=bubble_color
    )

    # Draw the tail
    if tail_position == "left":
        bubble_draw.polygon([(0, bubble_height // 2), (tail_width, bubble_height // 2 - tail_height // 2), (tail_width, bubble_height // 2 + tail_height // 2)], fill=bubble_color)
    else:
        bubble_draw.polygon([(bubble_width, bubble_height // 2), (bubble_width - tail_width, bubble_height // 2 - tail_height // 2), (bubble_width - tail_width, bubble_height // 2 + tail_height // 2)], fill=bubble_color)

    # Draw the text on the bubble
    bubble_draw.text((padding + (tail_width if tail_position == "left" else 0), padding), wrapped_text, font=font, fill=text_color)

    return bubble, bubble_height + tail_height, bubble_width  # Return the bubble, its height, and width

# Function to save the current image, crop, and reset for new image
def save_and_reset(image, draw, index, current_y):
    # Crop the image 50 pixels below the last message
    cropped_height = current_y - 15
    cropped_image = image.crop((0, 0, image.width, cropped_height))
    
    edited_image_path = f"src/edited_text_template_{index}.jpg"
    cropped_image.save(edited_image_path)
    print(f"iMessage conversation template part {index} has been created. Saved as {edited_image_path}")
    
    # Reset for new image
    new_image = Image.open(template_path)
    new_draw = ImageDraw.Draw(new_image)
    return new_image, new_draw

def read_prompt_from_config(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        prompt = data.get('prompt', '')
        return prompt
    
def delete_files(pattern):
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)
        except OSError as e:
            print(f"Error deleting file {file}: {e}")

# Main function
def main():
    
    # Delete existing images and audio files
    delete_files("src/edited_text_template_*.jpg")
    delete_files("audio_*.mp3")
    delete_files("final_video.mp4")
    
    api_key = "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"  # Replace with your OpenAI API key
    elevenlabs_api_key = "sk_5bd4124076fd938e910e70af0fdef495fa04b3a35b61ef47"  # Replace with your ElevenLabs API key
    prompt = r"""
    Create a two-way conversation between two people. Come up with a long and complex and creative scenario based on the following information. Be graphic for the story. Tell a story with the dialogue. Only include dialogue.\n
    """
    prompt += read_prompt_from_config("story_config.json")
    
    # Get the response from ChatGPT
    chatgpt_response = get_chatgpt_response(prompt, api_key)
    
    # Split the conversation into individual messages
    messages = chatgpt_response.split('\n')
    messages = [msg.strip() for msg in messages if msg.strip()]
    
    # Load the image template
    global template_path  # Declare as global for use in save_and_reset function
    template_path = "src/text_template.jpg"
    image = Image.open(template_path)
    draw = ImageDraw.Draw(image)
    
    # Define font and text properties
    font_path = "C:/Windows/Fonts/Arial.ttf"  # Adjust the path to your font file if needed
    font = ImageFont.truetype(font_path, 24)
    bubble_color_1 = (240, 240, 240)  # Light gray bubble for one speaker
    bubble_color_2 = (0, 122, 255)  # Blue bubble for the other speaker
    text_color_1 = (0, 0, 0)  # Black text for one speaker
    text_color_2 = (255, 255, 255)  # White text for the other speaker
    name_font = ImageFont.truetype(font_path, 15)  # Smaller font for the name
    profile_font = ImageFont.truetype(font_path, 45)  # Font for the profile letter
    profile_color = (255, 255, 255)  # Letter font color
    name_color = (0, 0, 0)  # Gray color for the name
    
    # Starting positions for the conversation
    position_left = (7, 150)  # Adjusted starting position for the left side (20 pixels more to the left, 50 pixels higher)
    position_right_offset = 5  # Offset from the right edge (20 pixels more to the right)
    vertical_space = 20
    bottom_padding = 100
    
    # Extract and center the name underneath the profile picture
    names = []
    if messages:
        names.append(messages[0].split(':')[0])
    if len(messages) > 1:
        names.append(messages[1].split(':')[0])

    if names:
        name_text = names[0].split('-')[1]  # Extract the name without the gender prefix
        profile_letter = name_text[0].upper()  # Get the first letter of the name
        name_width = draw.textsize(name_text, font=name_font)[0]
        draw.text(((image.width - name_width) // 2 + 1, 87), name_text, font=name_font, fill=name_color)
        # Draw the profile letter
        draw.text(((image.width - 50) // 2 + 11, 23), profile_letter, font=profile_font, fill=profile_color)

    current_y = position_left[1]
    image_index = 1
    image_files = []
    audio_files = []
    image_audio_map = []
    
    for i, message in enumerate(messages):
        if ':' in message:
            prefix_name, text = message.split(':', 1)
            text = text.strip()
            gender, name = prefix_name.split('-')
            
            # Determine the voice based on the gender prefix
            if gender == "M":
                voice_id = "Liam"
            else:
                voice_id = "Laura"
            
            # Create text bubble
            if i % 2 == 0:
                bubble, bubble_height, bubble_width = draw_text_bubble(draw, text, font, bubble_color_1, text_color_1, image.width - 100, tail_position="left")
                position_left_x = position_left[0]
            else:
                bubble, bubble_height, bubble_width = draw_text_bubble(draw, text, font, bubble_color_2, text_color_2, image.width - 100, tail_position="right")
                position_left_x = image.width - bubble_width - position_right_offset

            # Check if the bubble will fit in the current image
            if current_y + bubble_height + vertical_space > image.height - bottom_padding:
                image, draw = save_and_reset(image, draw, image_index, current_y)
                image_files.append(f"src/edited_text_template_{image_index}.jpg")
                image_audio_map.append(audio_files)
                audio_files = []
                if names:
                    name_text = names[0].split('-')[1]  # Extract the name without the gender prefix
                    profile_letter = name_text[0].upper()  # Get the first letter of the name
                    name_width = draw.textsize(name_text, font=name_font)[0]
                    draw.text(((image.width - name_width) // 2 + 1, 87), name_text, font=name_font, fill=name_color)
                    # Draw the profile letter
                    draw.text(((image.width - 50) // 2 + 11.85, 23), profile_letter, font=profile_font, fill=profile_color)
                current_y = position_left[1]
                image_index += 1

            # Paste the bubble in the current image
            image.paste(bubble, (position_left_x, current_y), bubble)
            
            current_y += bubble_height + vertical_space

            # Generate audio for the text
            audio = generate(
                text=text,
                api_key=elevenlabs_api_key,
                voice=voice_id
            )
            audio_file = f"audio_{i}.mp3"
            save(audio, audio_file)
            audio_files.append(audio_file)
    
    # Save and crop the final image
    save_and_reset(image, draw, image_index, current_y)
    image_files.append(f"src/edited_text_template_{image_index}.jpg")
    image_audio_map.append(audio_files)

    # Create video from images
    clips = []
    for img, audio_group in zip(image_files, image_audio_map):
        combined_duration = sum(mpe.AudioFileClip(audio).duration for audio in audio_group)
        img_clip = mpe.ImageClip(img).set_duration(combined_duration)
        clips.append(img_clip)
    
    video = mpe.concatenate_videoclips(clips, method="compose")
    audio_concat = mpe.concatenate_audioclips([mpe.AudioFileClip(audio) for audio_group in image_audio_map for audio in audio_group])
    final_video = video.set_audio(audio_concat)
    final_video.write_videofile("final_video.mp4", fps=24)

if __name__ == "__main__":
    main()
