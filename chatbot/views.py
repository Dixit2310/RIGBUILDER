import json
import re
import os
import requests
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie

from products.models import Product, Category, Brand, Currency, Country
from orders.models import Order
from .models import ChatbotSettings, LocalFAQ, ConversationLog

def parse_budget(message):
    match = re.search(r'(?:[\$₹£€]|under|budget|of)\s*([\d,]+)', message, re.IGNORECASE)
    if not match:
        match = re.search(r'\b(\d{4,6})\b', message)
    if match:
        num_str = match.group(1).replace(',', '')
        try:
            return int(num_str)
        except ValueError:
            return None
    return None

def get_budget_pc_build(budget_inr):
    allocations = {
        'CPU': 0.20,
        'Motherboard': 0.12,
        'GPU': 0.35,
        'RAM': 0.08,
        'NVMe SSD': 0.08,
        'Power Supply': 0.08,
        'Cabinet': 0.06,
        'CPU Cooler': 0.03
    }
    
    selected_parts = {}
    total_cost = Decimal('0.00')
    total_tdp = 0
    
    for cat_name, alloc in allocations.items():
        cat_budget = Decimal(str(budget_inr)) * Decimal(str(alloc))
        
        part = Product.objects.filter(
            Q(category__name__iexact=cat_name) | Q(category__name__icontains=cat_name),
            original_price_usd__lte=cat_budget,
            stock__gt=0
        ).order_by('-original_price_usd').first()
        
        if not part:
            part = Product.objects.filter(
                Q(category__name__iexact=cat_name) | Q(category__name__icontains=cat_name),
                stock__gt=0
            ).order_by('original_price_usd').first()
            
        if part:
            selected_parts[cat_name] = part
            total_cost += part.original_price_usd
            total_tdp += getattr(part, 'power_consumption_watts', 65)
            
    return selected_parts, total_cost, total_tdp

def get_local_reply(request, message):
    msg_lower = message.lower()
    
    budget = parse_budget(message)
    if budget and any(kw in msg_lower for kw in ['build', 'pc', 'recommend', 'gaming', 'computer', 'setup', 'system', 'workstation', 'editing', 'streaming']):
        selected_currency_id = request.session.get('currency_id')
        currency = None
        if selected_currency_id:
            currency = Currency.objects.filter(id=selected_currency_id).first()
        if not currency:
            currency = Currency.objects.filter(code='USD').first() or Currency.objects.first()
            
        is_usd = budget < 5000
        rate = currency.exchange_rate_to_usd
        
        if is_usd:
            budget_inr = Decimal(str(budget)) / rate
        else:
            budget_inr = Decimal(str(budget))
            
        parts, total_base, total_tdp = get_budget_pc_build(budget_inr)
        
        if not parts:
            return "I couldn't find any matching components in the stock database. Please check back later!"
            
        symbol = currency.symbol
        rate_to_show = Decimal(str(rate))
        
        table_md = "| Category | Component | Price |\n| :--- | :--- | :--- |\n"
        for cat, p in parts.items():
            price_converted = p.original_price_usd * rate_to_show
            table_md += f"| {cat} | [{p.brand.name} {p.name}](/products/{p.slug}/) | {symbol}{price_converted:,.2f} |\n"
            
        total_converted = total_base * rate_to_show
        table_md += f"| **Total** | **Estimated Cost** | **{symbol}{total_converted:,.2f}** |\n"
        
        fps_info = ""
        if budget_inr < 60000:
            fps_info = (
                "🎮 **Expected Performance (1080p High):**\n"
                "- **GTA V**: 90+ FPS\n"
                "- **Cyberpunk 2077**: 45+ FPS (Medium)\n"
                "- **Counter-Strike 2**: 180+ FPS"
            )
        elif budget_inr < 120000:
            fps_info = (
                "🎮 **Expected Performance (1440p High):**\n"
                "- **GTA V**: 140+ FPS\n"
                "- **Cyberpunk 2077**: 75+ FPS (High)\n"
                "- **Counter-Strike 2**: 260+ FPS"
            )
        else:
            fps_info = (
                "🎮 **Expected Performance (4K Ultra):**\n"
                "- **GTA V**: 180+ FPS\n"
                "- **Cyberpunk 2077**: 110+ FPS (Ultra/DLSS)\n"
                "- **Counter-Strike 2**: 360+ FPS"
            )
            
        psu_suggestion = max(total_tdp + 100, 550)
        psu_margin = int(psu_suggestion * 1.2)
        
        reply = (
            f"Here is a recommended PC build matching your budget of **{symbol}{budget:,.2f}**:\n\n"
            f"{table_md}\n"
            f"⚡ **Power Metrics & TDP:**\n"
            f"- Estimated TDP: **{total_tdp}W**\n"
            f"- Recommended PSU Wattage: **{psu_margin}W**\n\n"
            f"{fps_info}"
        )
        return reply

    order_keywords = ['my order', 'order status', 'track order', 'recent order', 'invoice', 'orders']
    if any(kw in msg_lower for kw in order_keywords):
        if request.user.is_authenticated:
            orders = Order.objects.filter(user=request.user).order_by('-created_at')[:3]
            if orders.exists():
                selected_currency_id = request.session.get('currency_id')
                currency = None
                if selected_currency_id:
                    currency = Currency.objects.filter(id=selected_currency_id).first()
                if not currency:
                    currency = Currency.objects.filter(code='USD').first() or Currency.objects.first()
                rate = currency.exchange_rate_to_usd
                
                reply = "Here are your recent orders:\n\n"
                for o in orders:
                    total_converted = o.grand_total_usd * rate
                    reply += (
                        f"### **Order #{o.order_number}**\n"
                        f"- **Status**: **{o.status}**\n"
                        f"- **Grand Total**: **{currency.symbol}{total_converted:,.2f}**\n"
                        f"- **Placed**: **{o.created_at.strftime('%Y-%m-%d')}**\n"
                        f"- [Download Invoice PDF](/orders/download-invoice/{o.id}/)\n\n"
                    )
                return reply
            else:
                return "You haven't placed any orders yet. Start building your rig in the workspace!"
        else:
            return "Please [Login First...](/accounts/login/) to view and track your orders."

    faqs = LocalFAQ.objects.filter(is_active=True)
    faq_match = None
    max_overlap = 0
    words = [w.strip("?,.!") for w in msg_lower.split() if len(w) > 3]
    
    for faq in faqs:
        overlap = sum(1 for w in words if w in faq.question.lower() or w in faq.answer.lower())
        if overlap > max_overlap:
            max_overlap = overlap
            faq_match = faq
            
    if faq_match and max_overlap >= 3:
        return faq_match.answer

    try:
        from core.models import FAQ
        site_faqs = FAQ.objects.filter(is_active=True)
        for s_faq in site_faqs:
            overlap = sum(1 for w in words if w in s_faq.question.lower() or w in s_faq.answer.lower())
            if overlap > max_overlap:
                max_overlap = overlap
                faq_match = s_faq
        if faq_match and max_overlap >= 3:
            return faq_match.answer
    except:
        pass

    return None

def call_openrouter_api(messages, personality_prompt):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:8000/",
        "X-Title": "RIGBUILDER"
    }
    
    full_messages = [{"role": "system", "content": personality_prompt}] + messages
    
    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": full_messages,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
    except Exception as e:
        pass
    return None

def call_free_ai(messages, personality_prompt):
    url = "https://text.pollinations.ai/"
    full_messages = [{"role": "system", "content": personality_prompt}] + messages
    
    payload = {
        "messages": full_messages,
        "model": "openai",
        "jsonMode": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200 and response.text:
            return response.text.strip()
    except Exception as e:
        pass
    return None

def call_gemini_api(messages, personality_prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
        
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": personality_prompt}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        pass
    return None

@ensure_csrf_cookie
def chatbot_api_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
        
    settings = ChatbotSettings.objects.first()
    if not settings:
        settings = ChatbotSettings.objects.create()
        
    if not settings.is_enabled:
        return JsonResponse({'error': 'Chatbot is disabled by administrator'}, status=403)
        
    chat_count = request.session.get('chatbot_message_count', 0)
    if chat_count >= settings.max_messages_per_session:
        return JsonResponse({'reply': 'You have reached the maximum message limit for this session to prevent spam. Please try again later.'})
        
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        
    if not user_message:
        return JsonResponse({'error': 'Empty message not allowed'}, status=400)
        
    cleaned_input = re.sub(r'<[^>]*>', '', user_message)
    request.session['chatbot_message_count'] = chat_count + 1
    
    history = request.session.get('chatbot_history', [])
    history.append({"role": "user", "content": cleaned_input})
    if len(history) > 12:
        history = history[-12:]
        
    # 0. Intercept Explicit Database Search Trigger
    clean_msg = cleaned_input.strip("?.! ").lower()
    db_q = None
    if "gaming cpu" in clean_msg or "show gaming cpus" in clean_msg or "show gaming cpu" in clean_msg:
        db_q = Q(category__name__icontains='processor') | Q(category__name__icontains='cpu')
    elif "rtx gpu" in clean_msg or "show rtx gpus" in clean_msg or "show rtx gpu" in clean_msg:
        db_q = Q(name__icontains='rtx')
    elif "ddr5 ram" in clean_msg or "show ddr5 ram" in clean_msg:
        db_q = Q(name__icontains='ddr5') | Q(description__icontains='ddr5')
    elif "ssd" in clean_msg or "show ssds" in clean_msg or "show ssd" in clean_msg:
        db_q = Q(name__icontains='ssd') | Q(name__icontains='nvme') | Q(category__name__icontains='storage') | Q(category__name__icontains='ssd')
    elif "motherboard" in clean_msg or "show motherboards" in clean_msg or "show motherboard" in clean_msg:
        db_q = Q(category__name__icontains='motherboard')

    if db_q:
        matched_products = Product.objects.filter(db_q).distinct()[:5]
        if matched_products.exists():
            selected_currency_id = request.session.get('currency_id')
            currency = None
            if selected_currency_id:
                currency = Currency.objects.filter(id=selected_currency_id).first()
            if not currency:
                currency = Currency.objects.filter(code='USD').first() or Currency.objects.first()
                
            reply_md = "I found these matching products in our database:\n\n"
            reply_md += "| Product | Price | Stock Status | Link |\n| :--- | :--- | :--- | :--- |\n"
            for p in matched_products:
                price_info = p.get_price_for_currency_and_country(currency)
                symbol = price_info['currency_symbol']
                price = price_info['final_price']
                stock_status = f"**In Stock ({p.stock})**" if p.stock > 0 else "~~Out of Stock~~"
                reply_md += f"| **{p.brand.name} {p.name}** | {symbol}{price:,.2f} | {stock_status} | [View Product](/products/{p.slug}/) |\n"
            
            ConversationLog.objects.create(
                session_id=request.session.session_key or "unregistered_session",
                user=request.user if request.user.is_authenticated else None,
                message=cleaned_input,
                reply=reply_md
            )
            history.append({"role": "assistant", "content": reply_md})
            request.session['chatbot_history'] = history
            return JsonResponse({'reply': reply_md})

    # 1. Attempt Heuristics Check (Budget / Order / Local FAQs)
    local_reply = get_local_reply(request, cleaned_input)
    
    if local_reply:
        bot_reply = local_reply
    else:
        # Build context products & orders
        db_context_products = search_database_context(cleaned_input)
        product_context = ""
        if db_context_products:
            selected_currency_id = request.session.get('currency_id')
            currency = None
            if selected_currency_id:
                currency = Currency.objects.filter(id=selected_currency_id).first()
            if not currency:
                currency = Currency.objects.filter(code='USD').first() or Currency.objects.first()
                
            product_context = "Actual matched database products (in stock):\n"
            for p in db_context_products:
                price_info = p.get_price_for_currency_and_country(currency)
                product_context += f"- [{p.brand.name} {p.name}](https://127.0.0.1:8000/products/{p.slug}/): Price {price_info['currency_symbol']}{price_info['final_price']:.2f}, Stock: {p.stock}.\n"
                
        order_context = ""
        if request.user.is_authenticated:
            orders = Order.objects.filter(user=request.user).order_by('-created_at')[:3]
            if orders.exists():
                order_context = "User's order history:\n"
                for o in orders:
                    order_context += f"- Order #{o.order_number}: Status: {o.status}, Total: {o.grand_total_usd} USD, Invoice Download: /orders/download-invoice/{o.id}/\n"
                    
        additions = ""
        if product_context:
            additions += f"\n\n{product_context}\nIMPORTANT: Present the matched products above with their exact prices and links. Use markdown formatting."
        if order_context:
            additions += f"\n\n{order_context}"
            
        website_context = (
            "\n\n### WEBSITE & PROJECT OVERVIEW\n"
            "You are representing the website **RIGBUILDER** (http://127.0.0.1:8000/). Here are its key sections and features:\n"
            "1. **Live Custom PC Builder** (Access: `[Custom PC Builder](/builder/)`): Users can manually configure a desktop rig category by category. It automatically validates socket constraints, Motherboard vs Cabinet form factors, and calculates PSU power limits with a 20% safety margin. Users can add the entire rig to the shopping cart in one click.\n"
            "2. **AI Build Recommendation** (Access: `[AI Rig Advisor](/builder/ai-recommend/)`): Generates a complete compatible setup in one click based on a target budget and task focus slider, and hosts this AI Chat window.\n"
            "3. **E-commerce Product Catalog** (Access: `[Product Catalog](/products/)`): Displays all hardware items, sorted by Categories (CPUs, Motherboards, GPUs, RAM, NVMe SSDs, Cases, PSUs) and Brands (Intel, AMD, NVIDIA, ASUS, MSI, Corsair, G.Skill, Crucial). Clickable product page URLs follow the `/products/<slug>/` format, for example: `[AMD Ryzen 5 7600X](/products/amd-ryzen-5-7600x/)`.\n"
            "4. **User Accounts & Profiles** (Access: `[User Profile](/accounts/profile/)`): Allows users to log in, register (`[Sign Up](/accounts/register/)`), manage saved shipping addresses, and view their wishlist.\n"
            "5. **Order Management & Invoices** (Access: `[Order History](/orders/history/)`): Users can track shipping statuses (Pending, Shipped, Delivered) and download professional Invoice PDFs directly from their orders list.\n"
            "6. **Blogs & FAQs** (Access: `[Tech Blogs](/blogs/)`, `[FAQ Help Desk](/faq/)`, `[Contact Support](/contact/)`): Contains helpful tech articles, hardware frequently asked questions, and direct support contact forms.\n\n"
            "When users ask about how to build a PC, order products, register, check compatibility, download invoices, or use different features of this website, refer them to these specific features, explain the live checks, and suggest they visit the corresponding relative URL."
        )

        system_prompt = (
            f"{settings.ai_personality}\n\n"
            f"{website_context}\n\n"
            "Strict Instructions for Easy Understanding & Proper Formatting:\n"
            "1. **DO NOT SHOW RAW PATHS**: Under no circumstances should you output raw relative path strings (like `/accounts/login/`, `/builder/`, `/products/`) in plain text to the user. You MUST always format every single link as a Markdown link with readable anchor text, for example: use `[Login](/accounts/login/)` instead of writing raw `/accounts/login/`.\n"
            "2. **Simple Explanations**: Explain technical terms (like socket types, TDP, dual-channel, NVMe SSDs) in plain, simple language so beginner builders can easily understand.\n"
            "3. **Highly Organized Layout**: Always structure component lists, specifications, or pricing options in clean Markdown tables. Use headers, bold text, and bullet points to break down details.\n"
            "4. **Short & Clear Paragraphs**: Write short, conversational paragraphs (maximum 2-3 sentences each) to keep the chat highly readable.\n"
            "5. **No Raw HTML / XML**: Only output clean Markdown. Do not include raw HTML tag markers like <div> or <br>.\n"
            "6. **Clear Call to Action**: Guide the user on what page to visit next on the website using proper markdown links (e.g. `[Live PC Builder](/builder/)` to assemble a parts list, or `[Login](/accounts/login/)` to log in)."
            f"{additions}"
        )
        
        # 1. Attempt Official OpenRouter API call
        openrouter_reply = call_openrouter_api(history, system_prompt)
        
        if openrouter_reply:
            bot_reply = openrouter_reply
        else:
            # 2. Attempt Official Gemini API call
            gemini_reply = call_gemini_api(history, system_prompt)
            if gemini_reply:
                bot_reply = gemini_reply
            else:
                # 3. Fall back to keyless Free AI Service
                free_prompt = (
                    "You are RIGBUILDER AI, a friendly and expert sales assistant representing RIGBUILDER. "
                    f"{system_prompt}"
                )
                free_reply = call_free_ai(history, free_prompt)
                if free_reply:
                    bot_reply = free_reply
                else:
                    bot_reply = "Sorry, I'm currently unavailable. Please try again later."
            
    history.append({"role": "assistant", "content": bot_reply})
    request.session['chatbot_history'] = history
    
    ConversationLog.objects.create(
        session_id=request.session.session_key or "unregistered_session",
        user=request.user if request.user.is_authenticated else None,
        message=cleaned_input,
        reply=bot_reply
    )
    
    return JsonResponse({'reply': bot_reply})

def search_database_context(query):
    words = [w.strip("?,.!") for w in query.lower().split() if len(w.strip()) > 2]
    stop_words = ['do', 'you', 'have', 'search', 'for', 'find', 'show', 'me', 'recommend', 'buy', 'get', 'a', 'an', 'the', 'please', 'any', 'is', 'there']
    query_words = [w for w in words if w not in stop_words]
    
    if not query_words:
        return []
        
    q_obj = Q()
    for qw in query_words:
        q_obj |= Q(name__icontains=qw) | Q(brand__name__icontains=qw) | Q(category__name__icontains=qw)
        
    return list(Product.objects.filter(q_obj).distinct()[:4])
