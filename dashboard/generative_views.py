from django.http import HttpResponse
from huggingface_hub import InferenceClient
from nextweb.secret import HUGGINGFACE_API_KEY
import time

client = InferenceClient(api_key=HUGGINGFACE_API_KEY)

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

Ensure that the output is **clear, well-structured, and tailored for the chosen platform**. Make use of emojis throughout the outline. No need to generate an example post.
         """},
        {"role": "user", "content": user_mesasge}
    ]
    
    response = client.chat_completion(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=messages,
        temperature=0.7,
        max_tokens=1024
    )
    detailed_prompt = response["choices"][0]["message"]["content"].strip()+f"This is supposed to be posted to {platform}. Use emojis throughout the post. Prefix each bullet with a relevant emoji. The post language is strictly English."
    
    return detailed_prompt

def generate_final_post(detailed_prompt: str, platform: str, post_type: str, word_count: int) -> str:
    """Generates a high-quality social media post tailored for the given platform and post type."""
    messages = [
        {"role": "system", "content":
         f"""
You are an expert content writer specializing in **engaging, professional, and human-like social media posts** for {platform}.

### **Instructions**
- Use the structured prompt to craft a compelling post.
- Adjust **tone and style** based on platform and post type:
  - **Personal Post (LinkedIn, Twitter/X, Medium, etc.)** → Conversational, engaging, professional.
  - **Company Post (LinkedIn, Website, Press Release)** → Formal, authoritative, brand-aligned.
  - **Product Announcement (LinkedIn, Twitter, Facebook, Instagram, etc.)** → Promotional yet informative.
  - **Industry Thought Leadership (Medium, LinkedIn, Blog)** → Insightful, well-structured, expert tone.
- Use **platform-specific formatting**:
  - **LinkedIn** → Scannable paragraphs, emojis (if suitable), hashtags.
  - **Twitter/X** → Concise, threaded if needed, impactful first line.
  - **Instagram/Facebook** → Engaging, visual-friendly captions, hashtags.
  - **Website/Blog** → Well-structured, SEO-friendly, in-depth content.

### **Structure**
1️⃣ **Strong Opening Hook** (grabs attention).
2️⃣ **Key Insights / Main Message** (clear, structured, engaging).
3️⃣ **Call to Action (CTA)** (encourage engagement, sign-ups, comments).
4️⃣ **Relevant Hashtags & Mentions** (if applicable).

Ensure the post feels **authentic, platform-optimized, and valuable**.
         """},
        {"role": "user", "content": detailed_prompt}
    ]
    
    response = client.chat_completion(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=messages,
        temperature=0.8,
        max_tokens=2048
    )
    
    return response["choices"][0]["message"]["content"].strip()

def generate_social_post(request):
    if request.method == "POST":
        # Get form data
        post_idea = request.POST.get("postIdea", "Exciting Announcement")
        purpose = request.POST.get("purpose", "General Update")
        platform = request.POST.get("platform", "LinkedIn")
        industry = request.POST.get("industry", "Tech")
        post_type = request.POST.get("postType", "Personal")
        word_count = int(request.POST.get("wordCount", 350))

        word_counts = {"twitter":280, "linkedin": 3000, "whatsapp": 5000, "instagram": 2200, "blog": 10000}
        max_word_count = word_counts.get(platform, 3000)
        word_count = min(word_count, max_word_count)
        start_detailed = time.perf_counter()
        detailed_prompt = generate_detailed_prompt(post_idea, purpose, platform, industry, post_type, word_count)
        end_detailed = time.perf_counter()
        print(f"Time taken for generate_detailed_prompt: {end_detailed - start_detailed:.4f} seconds")

        start_final = time.perf_counter()
        final_post = generate_final_post(detailed_prompt, platform, post_type, word_count)
        end_final = time.perf_counter()
        print(f"Time taken for generate_final_post: {end_final - start_final:.4f} seconds")
        
        # Ensure the response is plain text so HTMX can replace the textarea content
        return HttpResponse(final_post, content_type="text/plain")

    return HttpResponse("Invalid Request", status=400)