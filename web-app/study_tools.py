"""StudyCap study prompts and related-video ranking from the shared application."""

SUMMARY_SYSTEM_PROMPT_BASE = "You are StudyCap, a dedicated and approachable chatbot assistant specializing in helping students understand lecture material. " + \
    "Your purpose is to provide an EXHAUSTIVE, COMPREHENSIVE, and COMPLETE summary of ALL lecture material provided. " + \
    "CRITICAL REQUIREMENT: Include ALL equations, formulas, and mathematical expressions - do not skip any mathematical content. " + \
    "EXHAUSTIVENESS REQUIREMENT: Your summary must be exhaustive and detailed. Include ALL concepts, examples, definitions, explanations, formulas, theorems, proofs, diagrams descriptions, and any other content mentioned in the source material. " + \
    "Do not summarize or condense - instead, expand and explain. If a concept is mentioned, explain it fully. If an example is given, include it. If a formula is shown, include it with context. " + \
    "Preserve ALL section headings and topic titles. Use '##' for main sections, '###' for subsections, and '####' for sub-subsections. " + \
    "Bullet points should start with '*'. " + \
    "MATH FORMATTING RULES (CRITICAL FOR RENDERING): " + \
    "For EVERY mathematical expression, equation, formula, symbol, or operator, you MUST use LaTeX delimiters. " + \
    "Use \\(...\\) for inline math (e.g., \\(x^2 + y^2 = r^2\\) or \\(E = mc^2\\)). " + \
    "Use \\[...\\] for display/block math on its own line (e.g., \\[\\int_0^1 x dx = \\frac{1}{2}\\]). " + \
    "IMPORTANT: In your output, write these delimiters with a SINGLE backslash: \\( and \\) for inline, \\[ and \\] for display. " + \
    "Examples: 'The equation \\(a^2 + b^2 = c^2\\) is fundamental.' or 'We have: \\[\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\\]' " + \
    "Do NOT use plain text for math symbols (no 'x squared', 'alpha', 'pi' in words). Always use LaTeX. " + \
    "Do NOT use single dollar signs ($) as they conflict with currency. " + \
    "If you see math in the source material, convert it to proper LaTeX format. " + \
    "Be comprehensive and detail-oriented - include all important technical details. " + \
    "IMPORTANT NOTE-TAKING STYLE: You must create summaries in the form of detailed study notes, going above and beyond to explain concepts thoroughly. " + \
    "Like a teacher would, break down complex ideas into simpler parts, provide clear examples, and explain the 'why' behind concepts. " + \
    "Your notes should be so clear that someone could understand the material even months later. " + \
    "When multiple sources are provided (e.g., audio captions AND PDF slides), you MUST exhaustively use content from BOTH sources, integrating them seamlessly. " + \
    "Do not use horizontal rules (---) or other separators between sections. Use only the specified heading levels (##, ###, ####) for organization."

SUMMARY_PDF_CONTEXT_ADDITION = " CRITICAL: You have been provided with BOTH audio captions AND lecture slides/notes from a PDF. These are EQUAL PRIMARY SOURCES. " + \
    "You MUST exhaustively use content from BOTH sources. Do not treat the PDF as supplementary - it contains essential information that must be fully integrated. " + \
    "Combine information from both sources: use the audio captions for spoken explanations and the PDF slides for visual content, formulas, diagrams, examples, and structured information. " + \
    "If the same concept appears in both sources, include the most complete version or combine details from both. " + \
    "If content appears in only one source, you must still include it. Your summary must be exhaustive of BOTH sources combined."

SUMMARY_PDF_ONLY_CONTEXT = " CONTEXT: You have been provided with lecture slides/notes from a PDF document. This PDF contains the PRIMARY source material for your summary. Create a comprehensive summary based solely on this PDF content."

# Common user prompt instructions for summaries (reused across all summary types)
SUMMARY_USER_INSTRUCTIONS = """CRITICAL INSTRUCTIONS FOR EXHAUSTIVE SUMMARY:
1. EXHAUSTIVENESS: Include EVERY equation, formula, mathematical expression, concept, example, definition, theorem, proof, diagram description, and piece of information found in the source material(s)
2. DETAIL LEVEL: Be exhaustive and detailed - do not summarize or condense. Expand on concepts, provide full explanations, include all examples, and explain the reasoning behind formulas and theorems
3. Preserve ALL section headings and topic titles using the specified markdown format
4. Do not omit ANY content - if it's in the source material, it should be in your summary
5. MATH FORMATTING: Format ALL math with LaTeX delimiters (use SINGLE backslash in your output):
   - Inline math: \\(expression\\) (e.g., \\(x^2\\), \\(\\alpha\\), \\(\\frac{{a}}{{b}}\\))
   - Display math: \\[expression\\] (e.g., \\[\\int_0^\\infty e^{{-x}} dx = 1\\])
   - NEVER use single dollar signs ($) - they conflict with currency
   - Write the delimiters exactly as shown: \\( and \\) for inline, \\[ and \\] for display
6. When multiple sources are provided, exhaustively integrate content from ALL sources - treat them as equal primary sources

"""

CHAT_SYSTEM_PROMPT = "You are a helpful assistant that answers questions based on the lecture summary provided and give concise short answers. When mentioning mathematical expressions, use LaTeX format: \\(...\\) for inline math and \\[...\\] for display math (use single backslash in your output)."

QUIZ_SYSTEM_PROMPT = "You are an educational quiz creator that generates high-quality multiple-choice questions based on educational content. For each question, provide 4 options (A, B, C, D) with exactly one correct answer. Format your response as valid JSON that can be parsed with JSON.parse(). Return exactly 5 questions. Return a JSON object with a questions array of objects, where each object has: 'question' (string), 'options' (array of 4 strings), 'correctAnswer' (string with just the letter A, B, C, or D), and 'explanation' (string explaining why the answer is correct). " + \
    "MATH FORMATTING RULES (CRITICAL FOR RENDERING): " + \
    "For EVERY mathematical expression, equation, formula, symbol, or operator in questions, options, or explanations, you MUST use LaTeX delimiters. " + \
    "Use \\(...\\) for inline math within text (e.g., \\(x^2\\), \\(\\alpha\\), \\(E = mc^2\\), \\(\\frac{a}{b}\\)). " + \
    "Use \\[...\\] for display/block math when the equation is prominent (e.g., \\[\\int_0^1 x dx = \\frac{1}{2}\\]). " + \
    "IMPORTANT: In your output, write these delimiters with a SINGLE backslash: \\( and \\) for inline, \\[ and \\] for display. " + \
    "Examples: Question: 'What is \\(x^2 + y^2\\)?' or Option: 'The value is \\(\\frac{n(n+1)}{2}\\)' or Explanation: 'We use \\[\\sum_{i=1}^{n} i\\]' " + \
    "Do NOT use plain text for math symbols (no 'x squared', 'alpha', 'pi' in words). Always use LaTeX. " + \
    "Do NOT use single dollar signs ($) as they conflict with currency. " + \
    "This is critical for proper math rendering in the quiz interface."


def build_messages(request_type, data):
    if request_type == "summary":
        captions = data.get("captions", "")
        pdf_text = data.get("pdfText")
        
        # Determine if PDF-only or PDF + captions
        is_pdf_only = (not captions or captions.strip() == "") and pdf_text and pdf_text.strip()
        
        if is_pdf_only:
            system_prompt = SUMMARY_SYSTEM_PROMPT_BASE + SUMMARY_PDF_ONLY_CONTEXT
            user_prompt = SUMMARY_USER_INSTRUCTIONS + f"""LECTURE SLIDES/NOTES FROM PDF:
The following text was extracted from the PDF document. Create an EXHAUSTIVE and detailed summary based on this content:

{pdf_text}

IMPORTANT: This PDF is the PRIMARY source material. Create an exhaustive summary that includes ALL concepts, examples, formulas, definitions, theorems, proofs, diagrams, and explanations found in the PDF. 
- Do not summarize or condense - be detailed and exhaustive
- Include every formula, equation, and mathematical expression
- Include all examples and explanations
- Expand on concepts to provide full understanding
- Remember to convert ANY math expressions into proper LaTeX format using \\(...\\) for inline and \\[...\\] for display math (use single backslash in your output)"""
        elif pdf_text and pdf_text.strip():
            system_prompt = SUMMARY_SYSTEM_PROMPT_BASE + SUMMARY_PDF_CONTEXT_ADDITION
            user_prompt = SUMMARY_USER_INSTRUCTIONS + f"""You have been provided with TWO PRIMARY SOURCES for this lecture. You MUST exhaustively use content from BOTH sources:

SOURCE 1 - AUDIO CAPTIONS (Lecture Transcript):
The following text contains the spoken content from the lecture:

{captions}

SOURCE 2 - LECTURE SLIDES/NOTES (PDF):
The following text was extracted from the lecture slides or notes:

{pdf_text}

CRITICAL INSTRUCTIONS:
- These are EQUAL PRIMARY SOURCES - you must exhaustively include content from BOTH
- Integrate information from both sources seamlessly - combine spoken explanations from captions with visual/formula content from slides
- If the same concept appears in both, include the most complete version or merge details from both sources
- If content appears in only one source, you MUST still include it
- Include ALL formulas, equations, examples, definitions, diagrams, and explanations from BOTH sources
- Your summary must be exhaustive of the combined content from both sources
- Remember to convert ANY math expressions into proper LaTeX format using \\(...\\) for inline and \\[...\\] for display math (use single backslash in your output)
- Be detailed and exhaustive - do not summarize or condense. Expand on concepts and provide full explanations."""
        else:
            system_prompt = SUMMARY_SYSTEM_PROMPT_BASE
            user_prompt = SUMMARY_USER_INSTRUCTIONS + f"""LECTURE CAPTIONS (Audio Transcript):
The following text contains the spoken content from the lecture. Create an EXHAUSTIVE and detailed summary:

{captions}

IMPORTANT: Create an exhaustive summary that includes ALL concepts, examples, formulas, definitions, explanations, and information from the captions. Do not summarize or condense - be detailed and exhaustive. Include every formula, equation, and mathematical expression. Expand on concepts to provide full understanding."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
    elif request_type == "chat":
        summary_text = data.get("summaryText", "")
        user_question = data.get("userQuestion", "")
        
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Lecture Summary:\n{summary_text}"},
            {"role": "user", "content": f"Question: {user_question}"}
        ]
        
    elif request_type == "quiz":
        summary_text = data.get("summaryText", "")
        avoid_repeating = data.get("avoidRepeating", False)
        
        system_prompt = QUIZ_SYSTEM_PROMPT
        if avoid_repeating:
            system_prompt += " Avoid repeating previous questions if possible."
        
        user_prompt = f"""Based on the following lecture summary, generate 5 multiple-choice quiz questions to test understanding of key concepts. Lecture Summary:\n{summary_text}\n\nIMPORTANT: Format ALL mathematical expressions using LaTeX delimiters: \\(...\\) for inline math and \\[...\\] for display math (use single backslash in your output). NEVER use single dollar signs ($)."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
    else:
        raise ValueError("Unknown study action")
    return messages


def score_and_filter_videos(videos, summary_text, lecture_title):
    """Score and filter videos based on relevance and quality indicators"""
    
    # Keywords that indicate educational content
    educational_keywords = [
        "tutorial", "explained", "introduction", "basics", "lesson",
        "course", "lecture", "learn", "understanding", "guide",
        "how to", "what is", "example", "worked", "step by step"
    ]
    
    # Keywords that might indicate clickbait or low-quality content
    negative_keywords = [
        "challenge", "prank", "reaction", "vlog", "unboxing",
        "drama", "exposed", "shocking", "you won't believe"
    ]
    
    # Extract key terms from summary and title for matching
    search_terms = set()
    if lecture_title:
        search_terms.update(lecture_title.lower().split())
    if summary_text:
        # Get first 500 chars of summary for key terms
        search_terms.update(summary_text[:500].lower().split())
    
    # Remove common words
    common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                    "being", "have", "has", "had", "do", "does", "did", "will",
                    "would", "could", "should", "may", "might", "can", "to", "of",
                    "in", "for", "on", "with", "at", "by", "from", "and", "or", "but"}
    search_terms = {term for term in search_terms if term not in common_words and len(term) > 2}
    
    scored_videos = []
    
    for video in videos:
        score = 50  # Base score
        
        title_lower = video.get("title", "").lower()
        channel_lower = video.get("channelTitle", "").lower()
        description_lower = video.get("description", "").lower()
        
        # Bonus for educational keywords in title
        for keyword in educational_keywords:
            if keyword in title_lower:
                score += 10
                break
        
        # Penalty for negative keywords
        for keyword in negative_keywords:
            if keyword in title_lower:
                score -= 20
                break
        
        # Bonus for matching search terms in title
        matches = sum(1 for term in search_terms if term in title_lower)
        score += min(matches * 5, 25)
        
        # Bonus for view count (logarithmic scale)
        view_count = video.get("viewCount", 0)
        if view_count > 1000000:
            score += 15
        elif view_count > 100000:
            score += 10
        elif view_count > 10000:
            score += 5
        
        # Prefer videos between 5-20 minutes (ideal for educational content)
        duration_seconds = video.get("durationSeconds", 0) or parse_duration_to_seconds_from_formatted(video.get("duration", ""))
        if 300 <= duration_seconds <= 1200:  # 5-20 minutes
            score += 15
            video["durationTag"] = "Quick overview"
        elif 1200 < duration_seconds <= 2400:  # 20-40 minutes
            score += 10
            video["durationTag"] = "Deep dive"
        elif duration_seconds < 300:  # Under 5 minutes
            video["durationTag"] = "Best for overview"
        else:  # Over 40 minutes
            score -= 5
            video["durationTag"] = "Full lecture"
        
        # Add relevance tag based on title analysis
        if "example" in title_lower or "worked" in title_lower:
            video["relevanceTag"] = "Worked examples"
        elif "basics" in title_lower or "introduction" in title_lower or "intro" in title_lower:
            video["relevanceTag"] = "Best for overview"
        elif "advanced" in title_lower or "deep" in title_lower:
            video["relevanceTag"] = "Deep dive"
        elif "visual" in title_lower or "animation" in title_lower:
            video["relevanceTag"] = "Visual explanation"
        else:
            video["relevanceTag"] = ""
        
        video["score"] = score
        scored_videos.append(video)
    
    # Sort by score (descending)
    scored_videos.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Filter out low-scoring videos
    filtered_videos = [v for v in scored_videos if v.get("score", 0) >= 30]
    
    return filtered_videos if filtered_videos else scored_videos[:8]


def parse_duration_to_seconds_from_formatted(duration_str):
    """Parse formatted duration (e.g., '5:30' or '1:05:30') to seconds"""
    if not duration_str:
        return 0
    
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return 0
    except (ValueError, IndexError):
        return 0
