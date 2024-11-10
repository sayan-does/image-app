from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch
from diffusers import (
    StableDiffusionUpscalePipeline,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionPipeline
)
import shutil
import os
import io

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
device = "cuda" if torch.cuda.is_available() else "cpu"

# Upscaling model
upscaler = StableDiffusionUpscalePipeline.from_pretrained(
    "stabilityai/stable-diffusion-x4-upscaler",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)
upscaler.to(device)

# Image-to-Image model
img2img = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)
img2img.to(device)

# Text-to-Image model
txt2img = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)
txt2img.to(device)

# Theme prompts matching frontend options
THEME_PROMPTS = {
    "default": "high quality, detailed image",
    "historic": "vintage photograph, historical style, aged, antique appearance, sepia tones",
    "funky": "psychedelic, vibrant colors, funky style, retro pop art, creative and bold",
    "abstract": "abstract art style, non-representational, geometric shapes, modern art",
    "pixelart": "pixel art style, 8-bit graphics, retro gaming aesthetic",
    "modern": "contemporary art style, minimalist, clean lines, modern aesthetic",
    "anime": "anime style, detailed, vibrant, manga-inspired",
    "watercolor": "watercolor painting style, artistic, soft edges, flowing colors",
    "sketch": "pencil sketch style, detailed drawing, hand-drawn appearance",
    "oil_painting": "oil painting style, artistic, detailed, textured brushstrokes"
}


def process_image(image_path: str, operation: str, prompt: str = "", theme: str = "default"):
    """Process the image based on the selected operation and parameters."""
    try:
        # Get theme prompt
        theme_prompt = THEME_PROMPTS.get(theme, THEME_PROMPTS["default"])

        if operation == "generate":
            # Generate new image based on prompt and theme
            final_prompt = f"{prompt}, {theme_prompt}"
            generated_image = txt2img(
                prompt=final_prompt,
                num_inference_steps=50,
                guidance_scale=7.5
            ).images[0]
            return generated_image

        # Load and preprocess image for other operations
        image = Image.open(image_path)

        if operation == "upscale":
            # Upscale the image while maintaining theme
            final_prompt = f"high quality, detailed image, {theme_prompt}"
            upscaled_image = upscaler(
                image=image,
                prompt=final_prompt,
                num_inference_steps=20
            ).images[0]
            return upscaled_image

        elif operation == "modify":
            # Modify image based on theme and prompt
            final_prompt = f"{prompt}, {theme_prompt}"
            modified_image = img2img(
                image=image,
                prompt=final_prompt,
                strength=0.75,  # Adjust strength based on theme
                guidance_scale=7.5,
                num_inference_steps=50
            ).images[0]
            return modified_image

        else:
            raise ValueError(f"Unsupported operation: {operation}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_image(
    file: UploadFile = None,
    prompt: str = Form(...),
    theme: str = Form(...),
    option: str = Form(...)
):
    try:
        # For generate option, we don't need an input file
        if option == "generate":
            processed_image = process_image(
                image_path="",
                operation=option,
                prompt=prompt,
                theme=theme
            )

            # Save generated image
            output_filename = f"generated_image_{theme}.png"
            output_path = f"temp/{output_filename}"
            os.makedirs("temp", exist_ok=True)
            processed_image.save(output_path)

            # Read the generated image into bytes
            with open(output_path, "rb") as img_file:
                image_bytes = img_file.read()

            # Clean up
            os.remove(output_path)

            return {
                "message": "Image generated successfully",
                "image": image_bytes,
                "filename": output_filename
            }

        # For other options, we need an input file
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)

        # Save uploaded file
        file_location = f"temp/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the image
        processed_image = process_image(
            image_path=file_location,
            operation=option,
            prompt=prompt,
            theme=theme
        )

        # Save processed image
        output_filename = f"processed_{theme}_{file.filename}"
        output_path = f"temp/{output_filename}"
        processed_image.save(output_path)

        # Read the processed image into bytes
        with open(output_path, "rb") as img_file:
            image_bytes = img_file.read()

        # Clean up temporary files
        os.remove(file_location)
        os.remove(output_path)

        return {
            "message": "Image processed successfully",
            "image": image_bytes,
            "filename": output_filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
