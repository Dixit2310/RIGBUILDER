from decimal import Decimal
from django.db import models
from django.conf import settings
from products.models import Product

class PCBuild(models.Model):
    class BuildType(models.TextChoices):
        CUSTOM = 'CUSTOM', 'Custom Build'
        GAMING = 'GAMING', 'Gaming Build'
        EDITING = 'EDITING', 'Content Creation Build'
        STREAMING = 'STREAMING', 'Streaming Build'
        BUDGET = 'BUDGET', 'Budget Build'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='pc_builds'
    )
    name = models.CharField(max_length=150, default="My Custom PC Build")
    build_type = models.CharField(
        max_length=20, 
        choices=BuildType.choices, 
        default=BuildType.CUSTOM
    )
    
    # Core Components
    cpu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_cpus')
    motherboard = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_motherboards')
    ram = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_rams')
    gpu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_gpus')
    
    # Storage
    ssd = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_ssds')
    hdd = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_hdds')
    nvme = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_nvmes')
    
    # Power and Case
    psu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_psus')
    cabinet = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_cabinets')
    
    # Cooling
    cpu_cooler = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_coolers')
    case_fans = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_case_fans')
    
    # Accessories & Peripherals
    monitor = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_monitors')
    keyboard = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_keyboards')
    mouse = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_mouses')
    speakers = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_speakers')
    webcam = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_webcams')
    microphone = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_microphones')
    gaming_chair = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_chairs')
    mouse_pad = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_mousepads')
    
    # Miscellaneous
    thermal_paste = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_pastes')
    os = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_os')
    wifi_card = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_wifi')
    rgb_accessories = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_rgb')
    
    is_preset = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Custom Use Case Features
    target_system = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        help_text="e.g. Crypto Currency System, Trading System, Deep Learning System"
    )
    system_requirements = models.TextField(
        blank=True, 
        null=True, 
        help_text="Enter required parts or capabilities (e.g. Multi-GPU, 32GB RAM, 850W PSU)"
    )
    custom_required_categories = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated category names explicitly checked by the user"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_required_components_list(self):
        """Returns list of category names that are required for this build's target system"""
        target = (self.target_system or "").strip().lower()
        
        # Default required core components for any PC
        core_required = ["CPU", "Motherboard", "RAM", "Power Supply", "Cabinet"]
        
        if not target:
            # If no target system is specified, return standard set
            return core_required + ["GPU", "SSD", "NVMe SSD", "Operating System"]
            
        if any(x in target for x in ["crypto", "mining", "ethereum", "bitcoin"]):
            # Headless mining rigs don't require monitor, keyboard, OS, etc.
            return core_required + ["GPU", "SSD"]
            
        elif any(x in target for x in ["trading", "stock", "forex", "finance"]):
            # Trading requires display outputs, monitor, keyboard, mouse, OS
            return core_required + ["GPU", "SSD", "Monitor", "Keyboard", "Mouse", "Operating System"]
            
        elif any(x in target for x in ["ai", "deep learning", "machine learning", "neural", "cuda"]):
            # AI requires GPU, NVMe
            return core_required + ["GPU", "NVMe SSD"]
            
        elif any(x in target for x in ["streaming", "podcast", "youtube", "creation", "editing"]):
            # Streaming/Creation requires GPU, SSD/NVMe, Monitor, KB, Mouse, Mic, Webcam, OS
            return core_required + ["GPU", "SSD", "Monitor", "Keyboard", "Mouse", "Microphone", "Webcam", "Operating System"]
            
        elif any(x in target for x in ["office", "work", "school", "general", "basic"]):
            # Basic setup: no discrete GPU required
            return core_required + ["SSD", "Monitor", "Keyboard", "Mouse", "Operating System"]
            
        # Default fallback: return standard components
        return core_required + ["GPU", "SSD", "NVMe SSD", "Operating System"]

    def get_required_components_status(self):
        """Returns a dict with total, configured count, and list of missing required parts"""
        required = self.get_required_components_list()
        
        category_field_map = {
            'CPU': self.cpu,
            'Motherboard': self.motherboard,
            'RAM': self.ram,
            'GPU': self.gpu,
            'SSD': self.ssd,
            'HDD': self.hdd,
            'NVMe SSD': self.nvme,
            'Power Supply': self.psu,
            'Cabinet': self.cabinet,
            'CPU Cooler': self.cpu_cooler,
            'Case Fans': self.case_fans,
            'Monitor': self.monitor,
            'Keyboard': self.keyboard,
            'Mouse': self.mouse,
            'Speakers': self.speakers,
            'Webcam': self.webcam,
            'Microphone': self.microphone,
            'Gaming Chair': self.gaming_chair,
            'Mouse Pad': self.mouse_pad,
            'Thermal Paste': self.thermal_paste,
            'Operating System': self.os,
            'WiFi Card': self.wifi_card,
            'RGB Accessories': self.rgb_accessories
        }
        
        missing = []
        configured_count = 0
        for cat in required:
            field_val = category_field_map.get(cat)
            if field_val:
                configured_count += 1
            else:
                missing.append(cat)
                
        return {
            'required': required,
            'missing': missing,
            'configured_count': configured_count,
            'total_count': len(required),
            'progress_percent': int(configured_count / len(required) * 100) if required else 100
        }

    def calculate_total_power(self):
        """Calculates total TDP required by components"""
        total_watts = 0
        components = [
            self.cpu, self.motherboard, self.ram, self.gpu, 
            self.ssd, self.hdd, self.nvme, self.cpu_cooler, 
            self.case_fans, self.wifi_card, self.rgb_accessories
        ]
        for comp in components:
            if comp:
                total_watts += comp.power_consumption_watts
        return total_watts

    @property
    def has_components(self):
        """Checks if the build has at least one selected component"""
        components = [
            self.cpu, self.motherboard, self.ram, self.gpu, 
            self.ssd, self.hdd, self.nvme, self.psu, self.cabinet, 
            self.cpu_cooler, self.case_fans, self.monitor, self.keyboard, 
            self.mouse, self.speakers, self.webcam, self.microphone, 
            self.gaming_chair, self.mouse_pad, self.thermal_paste, 
            self.os, self.wifi_card, self.rgb_accessories
        ]
        return any(comp is not None for comp in components)

    def calculate_total_price_usd(self):
        """Calculates total price in base USD"""
        total = 0
        components = [
            self.cpu, self.motherboard, self.ram, self.gpu, 
            self.ssd, self.hdd, self.nvme, self.psu, self.cabinet, 
            self.cpu_cooler, self.case_fans, self.monitor, self.keyboard, 
            self.mouse, self.speakers, self.webcam, self.microphone, 
            self.gaming_chair, self.mouse_pad, self.thermal_paste, 
            self.os, self.wifi_card, self.rgb_accessories
        ]
        for comp in components:
            if comp:
                total += comp.final_price_usd
        return round(total, 2)

    def get_price_for_currency_and_country(self, currency, country=None):
        """Calculates converted price details for the entire build for a specific currency/country settings"""
        rate = Decimal(str(currency.exchange_rate_to_usd))
        total_usd = Decimal(str(self.calculate_total_price_usd()))
        total_local = total_usd * rate
        
        if country:
            tax = total_local * Decimal(str(country.default_tax_rate)) / Decimal('100.0')
            shipping = Decimal(str(country.default_shipping_charge)) * rate
        else:
            tax = Decimal('0.00')
            shipping = Decimal('0.00')
            
        grand_total = total_local + tax + shipping

        return {
            'currency_code': currency.code,
            'currency_symbol': currency.symbol,
            'subtotal': round(total_local, 2),
            'tax': round(tax, 2),
            'shipping': round(shipping, 2),
            'grand_total': round(grand_total, 2)
        }

    def get_price_for_country(self, country):
        """Calculates converted price details for the entire build for a specific country"""
        return self.get_price_for_currency_and_country(country.currency, country)

    def __str__(self):
        return f"{self.name} - {self.build_type} (By: {self.user.username if self.user else 'Anonymous'})"

class CompatibilityRule(models.Model):
    class RuleType(models.TextChoices):
        CPU_MOBO = 'CPU_MOBO', 'CPU & Motherboard Socket Matching'
        RAM_MOBO = 'RAM_MOBO', 'RAM & Motherboard DDR Type Matching'
        PSU_WATT = 'PSU_WATT', 'Power Supply Sufficiency'
        CASE_GPU = 'CASE_GPU', 'Cabinet & GPU Length Clearance'
        CASE_COOLER = 'CASE_COOLER', 'Cabinet & CPU Cooler Height Clearance'
        MOBO_CASE = 'MOBO_CASE', 'Motherboard & Cabinet Form Factor Support'
        MOBO_NVME = 'MOBO_NVME', 'Motherboard NVMe Slots Availability'

    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=30, choices=RuleType.choices, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
