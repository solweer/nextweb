import markdown
from bs4 import BeautifulSoup

# Unicode conversion functions
def to_unicode_bold(text):
    return "".join(chr(0x1D5D4 + ord(c) - ord("A")) if "A" <= c <= "Z" else
                   chr(0x1D5EE + ord(c) - ord("a")) if "a" <= c <= "z" else c for c in text)

def to_unicode_italic(text):
    return "".join(chr(0x1D609 + ord(c) - ord("A")) if "A" <= c <= "Z" else
                   chr(0x1D623 + ord(c) - ord("a")) if "a" <= c <= "z" else c for c in text)

def html_to_unicode_text(html):
    """Convert HTML to Unicode plaintext while preserving bold/italic formatting."""
    soup = BeautifulSoup(html, "html.parser")

    # Convert bold and italic text to Unicode equivalents
    for b in soup.find_all(["b", "strong"]):
        b.string = to_unicode_bold(b.get_text())

    for i in soup.find_all(["i", "em"]):
        i.string = to_unicode_italic(i.get_text())

    return soup.get_text()

# Updated text with Markdown formatting
md_content = """
# 9 Months of Growth and Innovation at PrismScale 🚀

🎉 **Milestone Achievement:** I'm thrilled to announce that I've been a part of the incredible team at PrismScale for 9 months now! It's been a journey filled with challenges, learning, and growth, and I couldn't be more grateful.     

👩‍💻 **Personal Growth:** From day one, I've been immersed in cutting-edge technology and the dynamic world of Gen AI. This role has not only honed my technical skills but also expanded my understanding of product development and innovation. I've learned so much from my talented colleagues and the supportive environment we share.

🤝 **Team Collaboration:** One of the highlights of my time at PrismScale has been the incredible teamwork. The collaborative spirit here is truly inspiring. Every project is a collective effort, and the support and encouragement from my team have been invaluable.

🌟 **Future Goals:** Looking ahead, I'm excited about the upcoming projects and the continued growth of our Gen AI solutions. I'm also setting personal goals to deepen my expertise in AI ethics and continue contributing to meaningful, impactful work.

🔗 **Connect with Me:** Share your own milestones or connect with me to learn more about our journey at PrismScale! 🤝

#PrismScale #ProductDeveloper #GenAI #Milestone #Growth #Innovation #TechStartup #ProfessionalJourney 🚀👩‍💻🤝🌟🔗
"""

# Convert Markdown to HTML
html_content = markdown.markdown(md_content)

# Convert HTML to Unicode plaintext
unicode_text = html_to_unicode_text(html_content)

print(unicode_text)
