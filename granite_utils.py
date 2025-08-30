import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import streamlit as st

@st.cache_resource
def load_granite_model():
    """
    Load IBM Granite model for text processing
    Returns a Hugging Face pipeline for text generation
    """
    try:
        # Get HF token from environment variables
        hf_token = os.getenv("HF_TOKEN")
        
        # IBM Granite model identifier
        model_name = "ibm-granite/granite-3.3-2b-instruct"
        
        # Load tokenizer and model with authentication
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=hf_token,
            trust_remote_code=True
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            token=hf_token,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        # Create text generation pipeline
        granite_pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        
        return granite_pipe
    
    except Exception as e:
        st.error(f"Error loading Granite model: {str(e)}")
        # Fallback to a lighter model if Granite fails
        try:
            return pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7
            )
        except:
            return None

def process_text_with_granite(text, tone="neutral", language="English", style="neutral", granite_pipe=None):
    """
    Process input text using IBM Granite model to enhance it for audiobook narration
    
    Args:
        text (str): Input text to process
        tone (str): Desired tone (formal, casual, emotional)
        language (str): Target language
        style (str): Voice style (neutral, narration, animated)
        granite_pipe: Pre-loaded Granite pipeline
    
    Returns:
        str: Enhanced text suitable for TTS conversion
    """
    if not granite_pipe:
        # If model loading failed, return original text with basic formatting
        return format_text_for_narration(text, tone, style)
    
    try:
        # Create a prompt for text enhancement based on parameters
        prompt = create_enhancement_prompt(text, tone, language, style)
        
        # Generate enhanced text using Granite
        result = granite_pipe(
            prompt,
            max_new_tokens=min(len(text.split()) * 2, 512),
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        
        # Extract the generated text
        enhanced_text = result[0]['generated_text']
        
        # Clean up the output (remove the prompt part)
        if prompt in enhanced_text:
            enhanced_text = enhanced_text.replace(prompt, "").strip()
        
        # Apply additional formatting for better TTS
        enhanced_text = format_text_for_narration(enhanced_text, tone, style)
        
        return enhanced_text if enhanced_text.strip() else text
    
    except Exception as e:
        st.warning(f"Text enhancement failed, using original text: {str(e)}")
        return format_text_for_narration(text, tone, style)

def create_enhancement_prompt(text, tone, language, style):
    """
    Create a prompt for the Granite model to enhance text for audiobook narration
    """
    tone_descriptions = {
        "formal": "professional and authoritative",
        "casual": "friendly and conversational", 
        "emotional": "expressive and emotionally engaging"
    }
    
    style_descriptions = {
        "neutral": "clear and balanced",
        "narration": "storytelling with appropriate pacing",
        "animated": "dynamic and expressive"
    }
    
    tone_desc = tone_descriptions.get(tone, "clear and engaging")
    style_desc = style_descriptions.get(style, "clear and balanced")
    
    prompt = f"""Enhance the following text for audiobook narration in {language}. 
Make it {tone_desc} in tone and {style_desc} in style. 
Add appropriate pauses, emphasis, and flow for better audio delivery.
Preserve the original meaning while making it more suitable for spoken word.

Original text: {text[:500]}...

Enhanced text:"""
    
    return prompt

def format_text_for_narration(text, tone="neutral", style="neutral"):
    """
    Apply basic formatting to text for better TTS output
    """
    # Add pauses for better pacing
    text = text.replace(". ", ". ... ")
    text = text.replace("! ", "! ... ")
    text = text.replace("? ", "? ... ")
    text = text.replace(", ", ", . ")
    
    # Add emphasis based on tone
    if tone == "emotional":
        # Add more dramatic pauses
        text = text.replace("...", "......")
    elif tone == "formal":
        # Ensure proper punctuation
        text = text.replace("...", ".")
    
    # Style-specific adjustments
    if style == "narration":
        # Add narrative markers
        text = "Once upon a time... " + text if not text.lower().startswith(("once", "there", "in")) else text
    elif style == "animated":
        # Add more expressive punctuation
        text = text.replace(".", "!")
    
    return text.strip()
