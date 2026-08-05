from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from products.models import Product, Category, Country, Currency
from .models import PCBuild
from .compatibility import CompatibilityChecker
from .utils import calculate_performance_scores, estimate_fps, calculate_bottleneck, estimate_temperatures, estimate_build_time

def builder_view(request):
    """Main custom PC builder interface view"""
    # Fetch or create the active build slot in the session
    build_id = request.session.get('active_build_id')
    build = None
    if build_id:
        try:
            build = PCBuild.objects.get(id=build_id)
        except PCBuild.DoesNotExist:
            pass
            
    if not build:
        # Create a new blank build
        build = PCBuild.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name="My PC Build"
        )
        request.session['active_build_id'] = build.id

    # Check if we should keep the target system or clear it (e.g. on page reload / direct visit)
    if not request.session.get('keep_target_system', False):
        if build.target_system or build.system_requirements:
            build.target_system = None
            build.system_requirements = None
            build.save()
    else:
        # Reset the flag so that a subsequent direct reload/visit will clear it
        request.session['keep_target_system'] = False

    # List of all categories to show as build slots
    categories = Category.objects.all().order_by('is_pc_component', 'name')
    
    # Check compatibility
    checker = CompatibilityChecker(build)
    compat_results = checker.check()
    
    # Calculate scores & estimations
    scores = calculate_performance_scores(build)
    fps_estimates = estimate_fps(build)
    bottleneck_details = calculate_bottleneck(build)
    temps = estimate_temperatures(build)
    build_time = estimate_build_time(build)
    
    # Localized prices
    selected_currency_id = request.session.get('currency_id')
    selected_country_id = request.session.get('country_id')
    
    currency = None
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
        except Currency.DoesNotExist:
            pass
            
    country = None
    if selected_country_id:
        try:
            country = Country.objects.get(id=selected_country_id)
        except Country.DoesNotExist:
            pass
            
    if not currency:
        if country:
            currency = country.currency
        else:
            currency = Currency.objects.filter(code='INR').first() or Currency.objects.first()
            
    price_details = build.get_price_for_currency_and_country(currency, country)

    return render(request, 'builder/workspace.html', {
        'build': build,
        'categories': categories,
        'compat_results': compat_results,
        'scores': scores,
        'fps_estimates': fps_estimates,
        'bottleneck': bottleneck_details,
        'temperatures': temps,
        'build_time': build_time,
        'price_details': price_details,
    })

def add_to_build_view(request, product_id):
    """View to place a selected product into its corresponding slot in the active build"""
    product = get_object_or_404(Product, id=product_id)
    build_id = request.session.get('active_build_id')
    
    if not build_id:
        return redirect('builder')
        
    build = get_object_or_404(PCBuild, id=build_id)
    category_name = product.category.name.upper()
    
    # Map category to the exact field on PCBuild
    category_map = {
        'CPU': 'cpu', 'MOTHERBOARD': 'motherboard', 'RAM': 'ram', 'GPU': 'gpu',
        'SSD': 'ssd', 'HDD': 'hdd', 'NVME SSD': 'nvme', 'POWER SUPPLY': 'psu',
        'CABINET': 'cabinet', 'CPU COOLER': 'cpu_cooler', 'CASE FANS': 'case_fans',
        'MONITOR': 'monitor', 'KEYBOARD': 'keyboard', 'MOUSE': 'mouse',
        'SPEAKERS': 'speakers', 'WEBCAM': 'webcam', 'MICROPHONE': 'microphone',
        'GAMING CHAIR': 'gaming_chair', 'MOUSE PAD': 'mouse_pad', 'THERMAL PASTE': 'thermal_paste',
        'OPERATING SYSTEM': 'os', 'WIFI CARD': 'wifi_card', 'RGB ACCESSORIES': 'rgb_accessories'
    }
    
    field_name = category_map.get(category_name)
    if field_name:
        setattr(build, field_name, product)
        build.save()
        request.session['keep_target_system'] = True
        messages.success(request, f"Added {product.name} to your build slot!")
    else:
        messages.error(request, "Unrecognized category type.")
        
    return redirect('builder')

def remove_from_build_view(request, slot_name):
    """View to remove/clear a product from a specific build slot"""
    build_id = request.session.get('active_build_id')
    if not build_id:
        return redirect('builder')
        
    build = get_object_or_404(PCBuild, id=build_id)
    
    # Safety check on fields
    valid_slots = [
        'cpu', 'motherboard', 'ram', 'gpu', 'ssd', 'hdd', 'nvme', 'psu', 'cabinet',
        'cpu_cooler', 'case_fans', 'monitor', 'keyboard', 'mouse', 'speakers', 'webcam',
        'microphone', 'gaming_chair', 'mouse_pad', 'thermal_paste', 'os', 'wifi_card', 'rgb_accessories'
    ]
    
    if slot_name in valid_slots:
        setattr(build, slot_name, None)
        build.save()
        request.session['keep_target_system'] = True
        messages.success(request, f"Cleared slot {slot_name.upper()}!")
    else:
        messages.error(request, "Invalid slot name specified.")
        
    return redirect('builder')

@login_required
def save_build_view(request):
    """View to rename and persist the active build to the user's account"""
    build_id = request.session.get('active_build_id')
    if not build_id:
        return redirect('builder')
        
    build = get_object_or_404(PCBuild, id=build_id)
    build.user = request.user
    
    if request.method == 'POST':
        name = request.POST.get('build_name', '').strip()
        target_system = request.POST.get('target_system', '').strip()
        system_requirements = request.POST.get('system_requirements', '').strip()
        
        if name:
            build.name = name
        if target_system:
            build.target_system = target_system
        if system_requirements:
            build.system_requirements = system_requirements
            
        build.save()
        messages.success(request, f"PC Configuration '{build.name}' saved successfully to your profile!")
        
        # Automatically add the saved configuration to the cart
        from orders.views import get_or_create_cart
        from orders.models import CartItem
        cart = get_or_create_cart(request)
        item, created = CartItem.objects.get_or_create(cart=cart, pc_build=build)
        if not created:
            item.quantity += 1
        item.save()
        messages.success(request, f"Added configuration '{build.name}' to your cart.")
        
        # Create a new blank build slot for subsequent configs
        new_build = PCBuild.objects.create(user=request.user, name="My PC Build")
        request.session['active_build_id'] = new_build.id
        return redirect('cart')
        
    categories = Category.objects.all().order_by('is_pc_component', 'name')
    return render(request, 'builder/save_build.html', {'build': build, 'categories': categories})

def presets_list_view(request):
    """View showing pre-configured gaming, editing, budget preset builds"""
    presets = PCBuild.objects.filter(is_preset=True)
    return render(request, 'builder/presets.html', {'presets': presets})

def load_preset_view(request, preset_id):
    """Copies all slots of a preset build to a new custom build slot for editing"""
    preset = get_object_or_404(PCBuild, id=preset_id, is_preset=True)
    
    # Copy all component fields
    new_build = PCBuild.objects.create(
        user=request.user if request.user.is_authenticated else None,
        name=f"Custom: {preset.name}",
        cpu=preset.cpu,
        motherboard=preset.motherboard,
        ram=preset.ram,
        gpu=preset.gpu,
        ssd=preset.ssd,
        hdd=preset.hdd,
        nvme=preset.nvme,
        psu=preset.psu,
        cabinet=preset.cabinet,
        cpu_cooler=preset.cpu_cooler,
        case_fans=preset.case_fans,
        monitor=preset.monitor,
        keyboard=preset.keyboard,
        mouse=preset.mouse,
        speakers=preset.speakers,
        webcam=preset.webcam,
        microphone=preset.microphone,
        gaming_chair=preset.gaming_chair,
        mouse_pad=preset.mouse_pad,
        thermal_paste=preset.thermal_paste,
        os=preset.os,
        wifi_card=preset.wifi_card,
        rgb_accessories=preset.rgb_accessories
    )
    
    request.session['active_build_id'] = new_build.id
    messages.success(request, f"Loaded preset config '{preset.name}' into your builder workspace!")
    return redirect('builder')
def auto_populate_build_parts(build):
    """Automatically populates empty required slots of the build with compatible products based on target system type"""
    from django.db.models import Q
    target = (build.target_system or "").strip().lower()
    required = build.get_required_components_list()
    
    # 1. Choose CPU if empty
    if "CPU" in required and not build.cpu:
        cpus = Product.objects.filter(category__name__iexact='CPU')
        if any(x in target for x in ["ai", "deep learning", "machine learning", "neural"]):
            build.cpu = cpus.order_by('-original_price_usd').first()
        elif any(x in target for x in ["crypto", "mining"]):
            build.cpu = cpus.order_by('original_price_usd').first()
        else:
            count = cpus.count()
            if count > 0:
                build.cpu = cpus.order_by('original_price_usd')[count // 2]
        build.save()

    # 2. Choose Motherboard if empty (requires CPU to match socket)
    if "Motherboard" in required and not build.motherboard:
        mobos = Product.objects.filter(category__name__iexact='Motherboard')
        if build.cpu and build.cpu.socket:
            mobos = mobos.filter(socket__iexact=build.cpu.socket)
        
        if any(x in target for x in ["ai", "deep learning"]):
            build.motherboard = mobos.order_by('-original_price_usd').first()
        elif any(x in target for x in ["crypto", "mining"]):
            build.motherboard = mobos.order_by('original_price_usd').first()
        else:
            count = mobos.count()
            if count > 0:
                build.motherboard = mobos.order_by('original_price_usd')[count // 2]
        build.save()

    # 3. Choose RAM if empty (requires Motherboard to match ram_type)
    if "RAM" in required and not build.ram:
        rams = Product.objects.filter(category__name__iexact='RAM')
        if build.motherboard and build.motherboard.ram_type:
            rams = rams.filter(ram_type__iexact=build.motherboard.ram_type)
            
        if any(x in target for x in ["ai", "deep learning"]):
            build.ram = rams.filter(name__icontains='32gb').first() or rams.order_by('-original_price_usd').first()
        elif any(x in target for x in ["crypto", "mining"]):
            build.ram = rams.order_by('original_price_usd').first()
        else:
            count = rams.count()
            if count > 0:
                build.ram = rams.order_by('original_price_usd')[count // 2]
        build.save()

    # 4. Choose GPU if empty
    if "GPU" in required and not build.gpu:
        gpus = Product.objects.filter(category__name__iexact='GPU')
        if any(x in target for x in ["ai", "deep learning", "machine learning"]):
            nvidia_gpus = gpus.filter(Q(brand__name__icontains='nvidia') | Q(name__icontains='rtx'))
            build.gpu = nvidia_gpus.order_by('-original_price_usd').first() or gpus.order_by('-original_price_usd').first()
        elif any(x in target for x in ["crypto", "mining"]):
            build.gpu = gpus.order_by('-original_price_usd').first()
        elif any(x in target for x in ["office", "work", "basic"]):
            build.gpu = gpus.order_by('original_price_usd').first()
        else:
            count = gpus.count()
            if count > 0:
                build.gpu = gpus.order_by('original_price_usd')[count // 2]
        build.save()

    # 5. Choose Storage (SSD / NVMe SSD) if empty
    if "NVMe SSD" in required and not build.nvme:
        nvmes = Product.objects.filter(category__name__iexact='NVMe SSD')
        if any(x in target for x in ["ai", "deep learning"]):
            build.nvme = nvmes.order_by('-original_price_usd').first()
        else:
            build.nvme = nvmes.order_by('original_price_usd').first()
        build.save()

    if "SSD" in required and not build.ssd and not build.nvme:
        ssds = Product.objects.filter(category__name__iexact='SSD')
        build.ssd = ssds.order_by('original_price_usd').first()
        build.save()

    # 6. Choose Power Supply if empty (requires checking TDP)
    if "Power Supply" in required and not build.psu:
        psus = Product.objects.filter(category__name__iexact='Power Supply')
        total_tdp = build.calculate_total_power()
        needed_watts = int(total_tdp * 1.2) + 100
        if needed_watts < 550:
            needed_watts = 550
            
        compatible_psus = psus.filter(psu_wattage_rating__gte=needed_watts)
        if any(x in target for x in ["crypto", "mining"]):
            build.psu = compatible_psus.filter(psu_wattage_rating__gte=750).order_by('original_price_usd').first() or psus.order_by('-psu_wattage_rating').first()
        else:
            build.psu = compatible_psus.order_by('original_price_usd').first() or psus.order_by('original_price_usd').first()
        build.save()

    # 7. Choose Cabinet if empty (requires form factor compatibility)
    if "Cabinet" in required and not build.cabinet:
        cabinets = Product.objects.filter(category__name__iexact='Cabinet')
        if build.motherboard and build.motherboard.form_factor:
            ff_hierarchy = {'mini-itx': 1, 'mitx': 1, 'matx': 2, 'micro-atx': 2, 'atx': 3, 'eatx': 4}
            mobo_val = ff_hierarchy.get(build.motherboard.form_factor.lower(), 3)
            if mobo_val == 4:
                cabinets = cabinets.filter(form_factor__iexact='EATX')
            elif mobo_val == 3:
                cabinets = cabinets.filter(Q(form_factor__iexact='ATX') | Q(form_factor__iexact='EATX'))
                
        build.cabinet = cabinets.order_by('original_price_usd').first() or Product.objects.filter(category__name__iexact='Cabinet').first()
        build.save()

    # 8. Peripherals if empty
    if "Monitor" in required and not build.monitor:
        build.monitor = Product.objects.filter(category__name__iexact='Monitor').first()
        build.save()
    if "Keyboard" in required and not build.keyboard:
        build.keyboard = Product.objects.filter(category__name__iexact='Keyboard').first()
        build.save()
    if "Mouse" in required and not build.mouse:
        build.mouse = Product.objects.filter(category__name__iexact='Mouse').first()
        build.save()
    if "Microphone" in required and not build.microphone:
        build.microphone = Product.objects.filter(category__name__iexact='Microphone').first()
        build.save()
    if "Webcam" in required and not build.webcam:
        build.webcam = Product.objects.filter(category__name__iexact='Webcam').first()
        build.save()
    if "Operating System" in required and not build.os:
        build.os = Product.objects.filter(category__name__iexact='Operating System').first()
        build.save()

def update_target_system_view(request):
    """Updates target system classification and requirements on the active build slot"""
    build_id = request.session.get('active_build_id')
    if not build_id:
        return redirect('builder')
        
    build = get_object_or_404(PCBuild, id=build_id)
    
    if request.method == 'POST':
        build.target_system = request.POST.get('target_system', '').strip()
        build.system_requirements = request.POST.get('system_requirements', '').strip()
        build.save()
        
        # Auto-choose compatible products for empty required slots
        auto_populate_build_parts(build)
        
        request.session['keep_target_system'] = True
        messages.success(request, "Target system requirements updated and required parts auto-configured!")
        
    return redirect('builder')

def ai_recommendation_view(request):
    """Deterministic, DB-driven AI Recommendation Engine"""
    selected_currency_id = request.session.get('currency_id')
    rate = 1.0
    if selected_currency_id:
        try:
            currency = Currency.objects.get(id=selected_currency_id)
            rate = float(currency.exchange_rate_to_usd)
        except (Currency.DoesNotExist, ValueError):
            pass
    else:
        selected_country_id = request.session.get('country_id')
        if selected_country_id:
            try:
                country = Country.objects.get(id=selected_country_id)
                rate = float(country.currency.exchange_rate_to_usd)
            except (Country.DoesNotExist, ValueError):
                pass

    # Calculate slider limits in local currency based on standard USD range [400, 4000]
    min_local = round(400.0 / 0.0120 * rate, -2)
    max_local = round(4000.0 / 0.0120 * rate, -2)
    step_local = round(100.0 / 0.0120 * rate, -2) if rate > 0.1 else 50.0
    default_local = round(1000.0 / 0.0120 * rate, -2)

    if request.method == 'POST':
        try:
            budget_str = request.POST.get('budget', str(default_local))
            # Convert user budget input from local currency back to base currency (INR)
            budget = float(budget_str) / rate
        except (ValueError, ZeroDivisionError):
            messages.error(request, "Please enter a valid numeric budget.")
            return redirect('ai_recommend')
            
        focus = request.POST.get('focus', 'gaming').lower()
        
        # Allocations based on focus
        if focus == 'gaming':
            cpu_pct, gpu_pct, mobo_pct, ram_pct, psu_pct, cab_pct, ssd_pct = 0.25, 0.40, 0.10, 0.08, 0.07, 0.05, 0.05
        elif focus == 'productivity':
            cpu_pct, gpu_pct, mobo_pct, ram_pct, psu_pct, cab_pct, ssd_pct = 0.38, 0.22, 0.12, 0.12, 0.06, 0.05, 0.05
        elif focus == 'streaming':
            cpu_pct, gpu_pct, mobo_pct, ram_pct, psu_pct, cab_pct, ssd_pct = 0.30, 0.32, 0.10, 0.10, 0.07, 0.05, 0.06
        else: # general / office
            cpu_pct, gpu_pct, mobo_pct, ram_pct, psu_pct, cab_pct, ssd_pct = 0.35, 0.10, 0.15, 0.15, 0.08, 0.08, 0.09

        # Filter products under maximum item allocations in USD
        # Find parts sequentially enforcing compatibility: CPU -> Motherboard -> RAM -> GPU -> SSD/NVMe -> PSU -> Cabinet -> CPU Cooler
        cpu = Product.objects.filter(category__name__iexact='CPU', original_price_usd__lte=budget*cpu_pct).order_by('-original_price_usd').first()
        if not cpu:
            cpu = Product.objects.filter(category__name__iexact='CPU').order_by('original_price_usd').first()
            
        mobo = None
        if cpu:
            mobo = Product.objects.filter(
                category__name__iexact='Motherboard', 
                socket__iexact=cpu.socket,
                original_price_usd__lte=budget*mobo_pct
            ).order_by('-original_price_usd').first()
            
        if not mobo and cpu:
            # Fall back to any motherboard that matches the CPU socket to guarantee compatibility
            mobo = Product.objects.filter(category__name__iexact='Motherboard', socket__iexact=cpu.socket).order_by('original_price_usd').first()
        if not mobo:
            mobo = Product.objects.filter(category__name__iexact='Motherboard').order_by('original_price_usd').first()

        ram = None
        if mobo:
            ram = Product.objects.filter(
                category__name__iexact='RAM',
                ram_type__iexact=mobo.ram_type,
                original_price_usd__lte=budget*ram_pct
            ).order_by('-original_price_usd').first()
            if not ram:
                # Fall back to any RAM matching motherboard's DDR type to guarantee compatibility
                ram = Product.objects.filter(category__name__iexact='RAM', ram_type__iexact=mobo.ram_type).order_by('original_price_usd').first()
        if not ram:
            ram = Product.objects.filter(category__name__iexact='RAM').order_by('original_price_usd').first()

        # GPU
        gpu = Product.objects.filter(category__name__iexact='GPU', original_price_usd__lte=budget*gpu_pct).order_by('-original_price_usd').first()
        if not gpu and focus != 'general':
            gpu = Product.objects.filter(category__name__iexact='GPU').order_by('original_price_usd').first()

        # Storage (SSD or NVMe SSD depending on Motherboard slots)
        ssd = None
        nvme_ssd = None
        
        # Check motherboard NVMe support
        has_nvme_support = mobo and (mobo.nvme_slots_count is None or mobo.nvme_slots_count > 0)
        
        if has_nvme_support:
            nvme_ssd = Product.objects.filter(category__name__iexact='NVMe SSD', original_price_usd__lte=budget*ssd_pct).order_by('-original_price_usd').first()
            if not nvme_ssd:
                nvme_ssd = Product.objects.filter(category__name__iexact='NVMe SSD').order_by('original_price_usd').first()
        else:
            ssd = Product.objects.filter(category__name__iexact='SSD', original_price_usd__lte=budget*ssd_pct).order_by('-original_price_usd').first()
            if not ssd:
                ssd = Product.objects.filter(category__name__iexact='SSD').order_by('original_price_usd').first()

        # PSU - Wattage check based on CPU & GPU power consumption
        total_power = (cpu.power_consumption_watts if cpu else 100) + (gpu.power_consumption_watts if gpu else 0) + 100
        recommended_psu = int(total_power * 1.2)
        
        psu = Product.objects.filter(
            category__name__iexact='Power Supply', 
            psu_wattage_rating__gte=recommended_psu,
            original_price_usd__lte=budget*psu_pct
        ).order_by('-original_price_usd').first()
        
        if not psu:
            # Fall back to any PSU that satisfies the wattage to guarantee compatibility
            psu = Product.objects.filter(category__name__iexact='Power Supply', psu_wattage_rating__gte=recommended_psu).order_by('original_price_usd').first()
        if not psu:
            psu = Product.objects.filter(category__name__iexact='Power Supply').order_by('original_price_usd').first()

        # Cabinet - Form factor check and GPU clearance check
        ff_hierarchy = {'mini-itx': 1, 'mitx': 1, 'matx': 2, 'micro-atx': 2, 'atx': 3, 'eatx': 4}
        mobo_val = ff_hierarchy.get((mobo.form_factor or "").lower(), 3) if mobo else 3
        
        cabinet = None
        # Get all cabinets
        cabinets = Product.objects.filter(category__name__iexact='Cabinet')
        compatible_cabinets = []
        for cab in cabinets:
            cab_val = ff_hierarchy.get((cab.form_factor or "").lower(), 3)
            # Must support motherboard form factor
            if cab_val < mobo_val:
                continue
            # Must support GPU length
            if gpu and gpu.gpu_length and cab.gpu_length_limit and gpu.gpu_length > cab.gpu_length_limit:
                continue
            compatible_cabinets.append(cab)
            
        # Select compatible cabinet under budget
        cab_under_budget = [c for c in compatible_cabinets if c.original_price_usd <= budget * cab_pct]
        if cab_under_budget:
            cabinet = sorted(cab_under_budget, key=lambda x: x.original_price_usd, reverse=True)[0]
        elif compatible_cabinets:
            cabinet = sorted(compatible_cabinets, key=lambda x: x.original_price_usd)[0]
            
        if not cabinet:
            cabinet = Product.objects.filter(category__name__iexact='Cabinet').order_by('original_price_usd').first()

        # CPU Cooler - Socket support and cooler height clearance check
        cpu_cooler = None
        coolers = Product.objects.filter(category__name__iexact='CPU Cooler')
        compatible_coolers = []
        for c in coolers:
            # Socket matching
            if cpu and cpu.socket and c.cooler_socket_support:
                supported_sockets = [s.strip().lower() for s in c.cooler_socket_support.split(',')]
                if cpu.socket.lower() not in supported_sockets:
                    continue
            # Cabinet clearance check
            if cabinet and cabinet.max_cooler_height and c.cooler_height and c.cooler_height > cabinet.max_cooler_height:
                continue
            compatible_coolers.append(c)
            
        # Select compatible cooler under budget
        cooler_under_budget = [c for c in compatible_coolers if c.original_price_usd <= budget * 0.05]
        if cooler_under_budget:
            cpu_cooler = sorted(cooler_under_budget, key=lambda x: x.original_price_usd, reverse=True)[0]
        elif compatible_coolers:
            cpu_cooler = sorted(compatible_coolers, key=lambda x: x.original_price_usd)[0]
            
        if not cpu_cooler:
            cpu_cooler = Product.objects.filter(category__name__iexact='CPU Cooler').order_by('original_price_usd').first()

        # Save to active build
        with transaction.atomic():
            new_build = PCBuild.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=f"AI Recommend: {focus.capitalize()} ${int(budget)}",
                cpu=cpu,
                motherboard=mobo,
                ram=ram,
                gpu=gpu,
                ssd=ssd,
                nvme=nvme_ssd,
                psu=psu,
                cabinet=cabinet,
                cpu_cooler=cpu_cooler
            )
            request.session['active_build_id'] = new_build.id
            
        messages.success(request, f"Generated a compatible {focus.capitalize()} build matching your ${budget} budget!")
        return redirect('builder')

    return render(request, 'builder/ai_recommend.html', {
        'slider_min': int(min_local),
        'slider_max': int(max_local),
        'slider_step': int(step_local) if step_local > 0.0 else 1,
        'slider_val': int(default_local)
    })


def clear_build_view(request):
    """View to clear all components from all slots of the active build"""
    build_id = request.session.get('active_build_id')
    if not build_id:
        return redirect('builder')
        
    build = get_object_or_404(PCBuild, id=build_id)
    
    valid_slots = [
        'cpu', 'motherboard', 'ram', 'gpu', 'ssd', 'hdd', 'nvme', 'psu', 'cabinet',
        'cpu_cooler', 'case_fans', 'monitor', 'keyboard', 'mouse', 'speakers', 'webcam',
        'microphone', 'gaming_chair', 'mouse_pad', 'thermal_paste', 'os', 'wifi_card', 'rgb_accessories'
    ]
    
    for slot in valid_slots:
        setattr(build, slot, None)
    build.save()
    
    messages.success(request, "Cleared all components from your workspace!")
    return redirect('builder')

