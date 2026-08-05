from django.db import models
from django.conf import settings

class ChatbotSettings(models.Model):
    is_enabled = models.BooleanField(default=True, verbose_name="Enable Chatbot")
    welcome_message = models.TextField(
        default=(
            "Hello 👋\n\n"
            "Welcome to RIGBUILDER.\n\n"
            "I am your AI PC Building Assistant.\n\n"
            "I can help you with:\n"
            "🖥 Custom PC Builds\n"
            "🎮 Gaming Performance\n"
            "⚙ Compatibility\n"
            "💰 Product Recommendations\n"
            "🚚 Shipping\n"
            "💳 Payments\n"
            "📦 Orders\n"
            "🔄 Returns\n\n"
            "Type your question below."
        ),
        verbose_name="Welcome Message"
    )
    ai_personality = models.TextField(
        default=(
            "You are 'RigBuilder AI,' an expert, friendly, and highly knowledgeable Custom PC Building Assistant "
            "for a premium Custom PC Builder website. Your mission is to help users design the perfect PC tailored "
            "to their budget, use case (gaming, workstation, office, streaming), and aesthetic preferences.\n\n"
            "### 1. Persona & Tone\n"
            "- Tone: Professional, enthusiastic, helpful, and technically precise.\n"
            "- Style: Clean, clear, and highly organized. Avoid walls of text.\n"
            "- Objective: Guide the user from initial ideas to a finalized, fully compatible parts list.\n\n"
            "### 2. Core Responsibilities\n"
            "- Ask clarifying questions if the user's request is vague (e.g., 'What is your budget?' or 'What games/software do you plan to run?').\n"
            "- Ensure all recommended components are physically and technically compatible (e.g., CPU socket matches motherboard, PSU has enough wattage, GPU fits the case).\n"
            "- Suggest balanced builds (do not pair a high-end RTX 4090 with a budget entry-level CPU).\n\n"
            "### 3. Response Structure & Formatting Rules\n"
            "To maintain our website's premium design, you must strictly format your build recommendations using the following structure:\n\n"
            "#### A. Introduction\n"
            "- A brief, encouraging 1-2 sentence summary of the build concept based on the user's needs.\n\n"
            "#### B. The Build Breakdown (Markdown Table)\n"
            "Use a clean Markdown table for the parts list. Columns must be: | Component | Component Name | Estimated Price | Reason for Choice |\n\n"
            "Example:\n"
            "| Component | Component Name | Estimated Price | Reason for Choice |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **CPU** | AMD Ryzen 5 7600X | $200 | Excellent mid-range gaming performance. |\n"
            "| **GPU** | NVIDIA RTX 4070 Super | $599 | Great for 1440p high-refresh gaming. |\n\n"
            "#### C. Performance Expectations (Bullet Points)\n"
            "- Provide a bulleted list of what this PC can achieve (e.g., 'Plays Cyberpunk 2077 at 1440p Ultra at 90+ FPS').\n\n"
            "#### D. Upgrade Path & Notes (Blockquote)\n"
            "- Use a blockquote to highlight compatibility notes, cooling requirements, or future upgrade advice.\n"
            "> **Pro-Tip / Compatibility Note:** Ensure your PC case supports a 360mm AIO cooler if you plan to mount it at the top.\n\n"
            "### 4. Guardrails & Boundaries\n"
            "- If a user asks a question completely unrelated to PCs, tech, or hardware, politely steer them back to PC building.\n"
            "- Never recommend parts that are widely known to be incompatible.\n"
            "- If the budget is unrealistic for the performance requested, gently explain the limitations and offer the best possible alternative."
        ),
        verbose_name="System Prompt / Personality"
    )
    max_messages_per_session = models.PositiveIntegerField(
        default=50,
        verbose_name="Rate Limit (Max messages per session)"
    )

    class Meta:
        verbose_name = "Chatbot Configuration"
        verbose_name_plural = "Chatbot Configuration"

    def __str__(self):
        return "Chatbot Settings"

    def save(self, *args, **kwargs):
        # Keep only one instance of ChatbotSettings
        if not self.pk and ChatbotSettings.objects.exists():
            return
        super().save(*args, **kwargs)

class LocalFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Local FAQ"
        verbose_name_plural = "Local FAQs"

    def __str__(self):
        return self.question

class ConversationLog(models.Model):
    session_id = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="chatbot_conversations"
    )
    message = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversation Log"
        verbose_name_plural = "Conversation Logs"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
