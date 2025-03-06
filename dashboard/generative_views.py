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

def generate_detailed_prompt(user_input: str, purpose: str, post_category: str, platform: str, industry: str, post_type: str, word_count: int) -> str:
    """Expands a short user input into a structured content brief suitable for various platforms and post types."""

    platform_guidelines = {
        "linkedin": "Engaging, professional, and well-structured. Use storytelling and limit hashtags to 3-5.",
        "instagram": "Concise, visually engaging, and fun. Use emojis and line breaks for readability.",
        "whatsapp": "Short, conversational, and direct. Avoid unnecessary formatting and hashtags.",
        "youtube": "For video captions: Use an engaging hook, clear structure, and strong CTAs. Keep sentences short and direct. For community posts: Use casual, engaging text to start discussions, ask questions, or share updates. Avoid excessive hashtags."
    }

    post_type_guidelines = {
        "personal": "Use storytelling, first-person perspective, and an authentic voice.",
        "company": "Maintain a professional, brand-aligned tone. Keep it clear and structured.",
        "product": "Make it exciting and promotional. Highlight key features and a compelling CTA.",
        "event": "Mention location, timinngs, summarize agenda, thank participants, and include relevant highlights."
    }

    script_format_guidelines = """
### **Script Format Guidelines (For Video/Reel Content)**
🎬 **Timestamps**: Indicate scene timing (e.g., [00:05 - 00:10]).  
📹 **Footage/Video**: Describe the visuals (e.g., 'Close-up of product', 'Interview shot').  
🗣️ **Dialog**: Write spoken words in quotes (e.g., "Welcome to our brand!").  
🎥 **B-roll**: Specify supporting visuals (e.g., 'Office workspace', 'Customer testimonial').  
📢 **CTA**: End with a clear call to action (e.g., 'Visit our website', 'Subscribe now').
""" if platform.lower() in ["youtube", "instagram"] and post_category.lower() in ["video_script", "reel_script"] else ""

    platform_notes = platform_guidelines.get(platform.lower(), "General social media best practices apply.")
    post_type_notes = post_type_guidelines.get(post_type.lower(), "Ensure the tone and format match the audience.")

    user_message = f'''
        {user_input}
        - **Purpose**: {purpose}
        - **Type**: {post_category}
        - **Platform**: {platform}
        - **Industry**: {industry}
        - **Post Type**: {post_type}
        - Approximate words: {word_count//3}
        - **Platform Guidelines**: {platform_notes}
        - **Post Type Guidelines**: {post_type_notes}
        {script_format_guidelines}
    '''

    messages = [
        {"role": "system", "content": 
         f"""
You are an expert content strategist crafting high-impact social media posts.

### **Output Format**
1️⃣ **Title/Hook**: A strong opening tailored to {platform} and {post_category}.
2️⃣ **Key Points**: Expand the user's input into structured content.
3️⃣ **Tone & Style**: Adjust based on {platform} and {post_type}.
4️⃣ **Target Audience**: Align messaging appropriately.
5️⃣ **Call-to-Action (CTA)**: Suggest an effective CTA.
6️⃣ **Hashtag & Formatting**: Ensure platform-specific optimization.
{script_format_guidelines if script_format_guidelines else ""}
Follow these guidelines:
- {platform_notes}
- {post_type_notes}
         """},
        {"role": "user", "content": user_message}
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

    detailed_prompt = response.choices[0].message.content.strip() + f" This is for {platform} as a {post_category}."

    return detailed_prompt

def generate_final_post(detailed_prompt: str, platform: str, post_category: str) -> str:
    """Generates a high-quality social media post tailored for the given platform and post type."""

    script_format = (
        "### **Script Format**\n"
        "Ensure the script is formatted properly:\n"
        "⏳ **[Timestamp]** - Scene breakdown\n"
        "🎥 **Footage/Video Description** - What appears on screen\n"
        "🗣 **Dialogue** - Spoken words\n"
        "🎬 **B-Roll** - Suggested supporting visuals\n"
    ) if post_category in ["video_script", "reel_script"] else ""

    messages = [
        {"role": "system", "content":
         f"""
You are an expert content editor and writer specializing in **engaging, professional, and human-like social media posts** for {platform}.

### **Instructions**
- Use the structured prompt to craft a compelling {post_category}.
- Adjust **tone and style** based on platform and post type:
  - **Personal Post (LinkedIn, Twitter/X, Medium, etc.)** → Conversational, engaging, professional.
  - **Company Post (LinkedIn, Website, Press Release)** → Formal, authoritative, brand-aligned.
  - **Product Announcement (LinkedIn, Twitter, Facebook, Instagram, etc.)** → Promotional yet informative.
  - **Industry Thought Leadership (Medium, LinkedIn, Blog)** → Insightful, well-structured, expert tone.
  - **Video Script / Reel Script** → **Use timestamps, footage descriptions, dialogue, and B-roll sections.**

### **Structure**
1️⃣ **Strong Opening Hook** (grabs attention).
2️⃣ **Key Insights / Main Message** (clear, structured, engaging).
3️⃣ **Call to Action (CTA)** (encourage engagement, sign-ups, comments).
4️⃣ **Relevant Hashtags & Mentions** (if applicable).

{script_format}

Ensure the {post_category} feels **authentic, platform-optimized, and valuable**. Add relevant formatting wherever appropriate. Use markdown for formatting.
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

def markdown_to_bold(text):
    # Convert Markdown headings only if they have a space after #
    text = re.sub(r"^(#{1,6})\s+([^\n#]+)$", lambda m: f"**{m.group(2)}**", text, flags=re.MULTILINE)
    
    return text

def generate_social_post(request):
    if request.method == "POST":
        # Get form data
        post_idea = request.POST.get("postIdea", "Exciting Announcement")
        purpose = request.POST.get("purpose", "General Update")
        post_category = request.POST.get("post_category", "General Update")
        platform = request.POST.get("platform", "LinkedIn")
        industry = request.POST.get("industry", "Tech")
        post_type = request.POST.get("postType", "Personal")
        word_count = int(request.POST.get("wordCount", 350))

        word_counts = {"linkedin": 3000, "whatsapp": 5000, "instagram": 2200, "youtube": 10000}
        max_word_count = word_counts.get(platform, 3000)
        word_count = min(word_count, max_word_count)

        start_detailed = time.perf_counter()
        detailed_prompt = generate_detailed_prompt(post_idea, purpose, post_category, platform, industry, post_type, word_count)
        end_detailed = time.perf_counter()
        logger.info(f"Time taken for generate_detailed_prompt: {end_detailed - start_detailed:.4f} seconds")

        start_final = time.perf_counter()
        final_post = generate_final_post(detailed_prompt, platform, post_type)
        end_final = time.perf_counter()
        logger.info(f"Time taken for generate_final_post: {end_final - start_final:.4f} seconds")

        logger.debug(final_post)  # Use debug level for detailed output
        return HttpResponse(markdown_to_bold(final_post), content_type="text/plain")

    return HttpResponse("Invalid Request", status=400)
