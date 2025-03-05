from django.http import HttpResponse
from huggingface_hub import InferenceClient
from together import Together
from nextweb.secret import TOGETHER_API_KEY
import time
import re 
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = Together(api_key=TOGETHER_API_KEY)

def to_unicode_bold(text):
    return "".join(
        chr(0x1D7CE + ord(c) - ord("0")) if "0" <= c <= "9" else
        chr(0x1D5D4 + ord(c) - ord("A")) if "A" <= c <= "Z" else
        chr(0x1D5EE + ord(c) - ord("a")) if "a" <= c <= "z" else c
        for c in text
    )

def generate_detailed_prompt(user_input: str, purpose: str, platform: str, industry: str, post_type: str, word_count:int) -> str:
    """Expands a short user input into a structured content brief suitable for various platforms and post types."""

    user_mesasge = f'''
        {user_input}
        - **Purpose**: {purpose}
        - **Platform**: {platform}
        - **Industry**: {industry}
        - **Post Type**: {post_type} (e.g., personal, company announcement, product update, thought leadership)
        - Approximate words: {word_count//3}
        '''
    
    messages = [
        {"role": "system", "content":
         f"""
You are an expert content strategist specializing in crafting high-impact social media content for various platforms.

### **Output Format**
Generate a structured post brief covering:
1️⃣ **Title/Hook**: A strong opening that suits the platform and post type.
2️⃣ **Key Points**: Expand on the user's input with critical details.
3️⃣ **Tone & Style**: Adjust tone (formal, conversational, promotional, informative) based on post type and platform.
4️⃣ **Target Audience**: Align messaging with the right audience.
5️⃣ **CTA (Call-to-Action)**: Suggest an appropriate CTA (engagement, product interest, discussion, etc.).
6️⃣ **Hashtag & Formatting Guidelines**: Relevant hashtags for visibility and platform-specific formatting.

Ensure that the output is **clear, well-structured, and tailored for {platform}**. Make use of emojis throughout the outline. No need to generate an example post.
         """},
        {"role": "user", "content": user_mesasge}
    ]
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=messages,
        temperature=0.8,
        max_tokens=None,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
    )
    detailed_prompt = response.choices[0].message.content.strip()+f"This is supposed to be posted to {platform}. Use emojis throughout the post. Prefix each point with a relevant emoji. The post language is strictly English."
    
    return detailed_prompt

def generate_final_post(detailed_prompt: str, platform: str, post_type: str, word_count: int) -> str:
    """Generates a high-quality social media post tailored for the given platform and post type."""
    messages = [
        {"role": "system", "content":
         f"""
You are an expert content editor and writer specializing in **engaging, professional, and human-like social media posts** for {platform}.

### **Instructions**
- Use the structured prompt to craft a compelling post.
- Adjust **tone and style** based on platform and post type:
  - **Personal Post (LinkedIn, Twitter/X, Medium, etc.)** → Conversational, engaging, professional.
  - **Company Post (LinkedIn, Website, Press Release)** → Formal, authoritative, brand-aligned.
  - **Product Announcement (LinkedIn, Twitter, Facebook, Instagram, etc.)** → Promotional yet informative.
  - **Industry Thought Leadership (Medium, LinkedIn, Blog)** → Insightful, well-structured, expert tone.

### **Structure**
1️⃣ **Strong Opening Hook** (grabs attention).
2️⃣ **Key Insights / Main Message** (clear, structured, engaging).
3️⃣ **Call to Action (CTA)** (encourage engagement, sign-ups, comments).
4️⃣ **Relevant Hashtags & Mentions** (if applicable).

Ensure the post feels **authentic, platform-optimized, and valuable**. Add relevant formatting wherever approriate.
         """},
        {"role": "user", "content": detailed_prompt}
    ]
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=messages,
        temperature=0.8,
        max_tokens=None,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
    )
    return response.choices[0].message.content.strip()

def markdown_to_unicode(text):
    # Convert Markdown headings only if they have a space after #
    text = re.sub(r"^(#{1,6})\s+([^\n#]+)$", lambda m: to_unicode_bold(m.group(2)), text, flags=re.MULTILINE)

    # Convert bold (**text** or __text__) to Unicode bold
    text = re.sub(r"\*\*(.*?)\*\*|__(.*?)__", lambda m: to_unicode_bold(m.group(1) or m.group(2)), text)

    return text

def generate_social_post(request):
    if request.method == "POST":
        # Get form data
        post_idea = request.POST.get("postIdea", "Exciting Announcement")
        purpose = request.POST.get("purpose", "General Update")
        platform = request.POST.get("platform", "LinkedIn")
        industry = request.POST.get("industry", "Tech")
        post_type = request.POST.get("postType", "Personal")
        word_count = int(request.POST.get("wordCount", 350))

        word_counts = {"twitter": 280, "linkedin": 3000, "whatsapp": 5000, "instagram": 2200, "blog": 10000}
        max_word_count = word_counts.get(platform, 3000)
        word_count = min(word_count, max_word_count)

        start_detailed = time.perf_counter()
        detailed_prompt = generate_detailed_prompt(post_idea, purpose, platform, industry, post_type, word_count)
        end_detailed = time.perf_counter()
        logger.info(f"Time taken for generate_detailed_prompt: {end_detailed - start_detailed:.4f} seconds")

        start_final = time.perf_counter()
        final_post = generate_final_post(detailed_prompt, platform, post_type, word_count)
        end_final = time.perf_counter()
        logger.info(f"Time taken for generate_final_post: {end_final - start_final:.4f} seconds")

        logger.debug(final_post)  # Use debug level for detailed output
        return HttpResponse(markdown_to_unicode(final_post), content_type="text/plain")

    return HttpResponse("Invalid Request", status=400)
