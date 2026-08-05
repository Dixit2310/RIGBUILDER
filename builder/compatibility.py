from products.models import Product

class CompatibilityChecker:
    def __init__(self, build):
        self.build = build
        self.errors = []
        self.warnings = []
        self.suggestions = []
        self.is_compatible = True

    def check(self):
        # 1. CPU & Motherboard Socket Check
        if self.build.cpu and self.build.motherboard:
            cpu_socket = self.build.cpu.socket
            mobo_socket = self.build.motherboard.socket
            if cpu_socket and mobo_socket and cpu_socket.lower() != mobo_socket.lower():
                self.errors.append(
                    f"Incompatible Socket: CPU has socket '{cpu_socket}' but Motherboard has socket '{mobo_socket}'."
                )
                self.is_compatible = False
                # Suggest compatible Motherboards
                matching_mobos = Product.objects.filter(category__name__iexact='Motherboard', socket__iexact=cpu_socket)[:3]
                if matching_mobos.exists():
                    self.suggestions.append({
                        'field': 'motherboard',
                        'message': f"Replace Motherboard with one supporting {cpu_socket}",
                        'items': [{'id': p.id, 'name': p.name, 'brand': p.brand.name, 'price': float(p.original_price_usd)} for p in matching_mobos]
                    })

        # 2. RAM & Motherboard RAM Type Check (DDR4/DDR5)
        if self.build.ram and self.build.motherboard:
            ram_type = self.build.ram.ram_type
            mobo_ram_type = self.build.motherboard.ram_type
            if ram_type and mobo_ram_type and ram_type.lower() != mobo_ram_type.lower():
                self.errors.append(
                    f"Incompatible RAM: RAM is '{ram_type}' but Motherboard only supports '{mobo_ram_type}'."
                )
                self.is_compatible = False
                # Suggest compatible RAM
                matching_ram = Product.objects.filter(category__name__iexact='RAM', ram_type__iexact=mobo_ram_type)[:3]
                if matching_ram.exists():
                    self.suggestions.append({
                        'field': 'ram',
                        'message': f"Replace RAM with {mobo_ram_type} memory",
                        'items': [{'id': p.id, 'name': p.name, 'brand': p.brand.name, 'price': float(p.original_price_usd)} for p in matching_ram]
                    })

        # 3. Cabinet & Motherboard Form Factor Check
        # Cabinet form_factor contains comma-separated values or single value (e.g. ATX supports ATX, mATX, Mini-ITX)
        if self.build.motherboard and self.build.cabinet:
            mobo_ff = self.build.motherboard.form_factor
            cab_ff = self.build.cabinet.form_factor
            if mobo_ff and cab_ff:
                # Typically a cabinet form factor is its max supported (ATX supports ATX/mATX/ITX, mATX supports mATX/ITX)
                ff_hierarchy = {'mini-itx': 1, 'mitx': 1, 'matx': 2, 'micro-atx': 2, 'atx': 3, 'eatx': 4}
                mobo_val = ff_hierarchy.get(mobo_ff.lower(), 3)
                cab_val = ff_hierarchy.get(cab_ff.lower(), 3)
                if mobo_val > cab_val:
                    self.errors.append(
                        f"Incompatible Size: Motherboard is '{mobo_ff}' but Cabinet only supports up to '{cab_ff}'."
                    )
                    self.is_compatible = False
                    # Suggest compatible Cabinets
                    matching_cabinets = Product.objects.filter(category__name__iexact='Cabinet', form_factor__iexact=mobo_ff)[:3]
                    if matching_cabinets.exists():
                        self.suggestions.append({
                            'field': 'cabinet',
                            'message': f"Replace Cabinet with one supporting {mobo_ff} motherboards",
                            'items': [{'id': p.id, 'name': p.name, 'brand': p.brand.name, 'price': float(p.original_price_usd)} for p in matching_cabinets]
                        })

        # 4. CPU Cooler & Cabinet Clearance Check
        if self.build.cpu_cooler and self.build.cabinet:
            cooler_height = self.build.cpu_cooler.cooler_height
            cab_limit = self.build.cabinet.max_cooler_height
            if cooler_height and cab_limit and cooler_height > cab_limit:
                self.errors.append(
                    f"Cooler Height Clearance: Cooler height is {cooler_height}mm but Cabinet maximum cooler clearance is {cab_limit}mm."
                )
                self.is_compatible = False

        # 5. Cabinet & GPU Length Check
        if self.build.gpu and self.build.cabinet:
            gpu_len = self.build.gpu.gpu_length
            cab_gpu_limit = self.build.cabinet.gpu_length_limit
            if gpu_len and cab_gpu_limit and gpu_len > cab_gpu_limit:
                self.errors.append(
                    f"GPU Length Clearance: GPU length is {gpu_len}mm but Cabinet only supports GPUs up to {cab_gpu_limit}mm."
                )
                self.is_compatible = False
                # Suggest compatible GPUs
                matching_gpus = Product.objects.filter(category__name__iexact='GPU', gpu_length__lte=cab_gpu_limit).order_by('-original_price_usd')[:3]
                if matching_gpus.exists():
                    self.suggestions.append({
                        'field': 'gpu',
                        'message': f"Replace GPU with one shorter than {cab_gpu_limit}mm",
                        'items': [{'id': p.id, 'name': p.name, 'brand': p.brand.name, 'price': float(p.original_price_usd)} for p in matching_gpus]
                    })

        # 6. Power Supply Wattage Sufficiency Check
        if self.build.psu:
            total_power_needed = self.build.calculate_total_power()
            recommended_psu = int(total_power_needed * 1.2) # 20% safety margin
            psu_rating = self.build.psu.psu_wattage_rating
            if psu_rating and psu_rating < recommended_psu:
                self.warnings.append(
                    f"Low Wattage: Selected Power Supply is {psu_rating}W, but the recommended wattage with a 20% safety buffer is {recommended_psu}W (Est. Load: {total_power_needed}W)."
                )
                # Suggest higher wattage PSUs
                matching_psus = Product.objects.filter(category__name__iexact='Power Supply', psu_wattage_rating__gte=recommended_psu).order_by('original_price_usd')[:3]
                if matching_psus.exists():
                    self.suggestions.append({
                        'field': 'psu',
                        'message': f"Upgrade Power Supply to at least {recommended_psu}W",
                        'items': [{'id': p.id, 'name': p.name, 'brand': p.brand.name, 'price': float(p.original_price_usd)} for p in matching_psus]
                    })

        # 7. CPU Cooler Socket Check
        if self.build.cpu and self.build.cpu_cooler:
            cpu_socket = self.build.cpu.socket
            cooler_sockets = self.build.cpu_cooler.cooler_socket_support
            if cpu_socket and cooler_sockets:
                supported_sockets = [s.strip().lower() for s in cooler_sockets.split(',')]
                if cpu_socket.lower() not in supported_sockets:
                    self.warnings.append(
                        f"Cooler Bracket: CPU Cooler may not include brackets for '{cpu_socket}' out of the box. Double check socket support."
                    )

        # 8. Motherboard NVMe Slot Check
        if self.build.nvme and self.build.motherboard:
            slots = self.build.motherboard.nvme_slots_count
            if slots is not None and slots == 0:
                self.errors.append(
                    "Motherboard does not have NVMe M.2 slots. Choose a SATA SSD or change motherboard."
                )
                self.is_compatible = False

        # 9. PCIe Version Check (Warning only)
        if self.build.gpu and self.build.motherboard:
            gpu_pcie = self.build.gpu.pcie_version
            mobo_pcie = self.build.motherboard.pcie_version
            if gpu_pcie and mobo_pcie and gpu_pcie.lower() != mobo_pcie.lower():
                self.warnings.append(
                    f"PCIe Version Mismatch: GPU supports '{gpu_pcie}' and Motherboard supports '{mobo_pcie}'. They are backwards compatible but performance may be capped by the slower interface."
                )

        # 10. RAM Speed & Motherboard RAM Speed Support Warning
        if self.build.ram and self.build.motherboard:
            ram_speed = self.build.ram.ram_speed
            mobo_max_speed = self.build.motherboard.ram_speed
            if ram_speed and mobo_max_speed and ram_speed > mobo_max_speed:
                self.warnings.append(
                    f"RAM Speed Downclock: Selected RAM runs at {ram_speed}MHz but Motherboard only natively supports up to {mobo_max_speed}MHz. The RAM will downclock to {mobo_max_speed}MHz unless manually overclocked via XMP/EXPO."
                )

        # 11. NVMe SSD PCIe Version & Motherboard PCIe Slot Warning
        if self.build.nvme and self.build.motherboard:
            ssd_pcie = self.build.nvme.pcie_version
            mobo_pcie = self.build.motherboard.pcie_version
            if ssd_pcie and mobo_pcie:
                # Compare PCIe Generations (e.g. Gen5 > Gen4 > Gen3)
                pcie_levels = {'gen5': 5, 'gen4': 4, 'gen3': 3, 'gen2': 2}
                ssd_val = pcie_levels.get(ssd_pcie.lower(), 4)
                mobo_val = pcie_levels.get(mobo_pcie.lower(), 4)
                if ssd_val > mobo_val:
                    self.warnings.append(
                        f"SSD Speed Capped: Selected NVMe SSD supports fast '{ssd_pcie}' speeds, but Motherboard M.2 slots only support '{mobo_pcie}'. The SSD is backwards compatible but its performance will be capped at '{mobo_pcie}' bandwidth."
                    )

        return {
            'is_compatible': self.is_compatible,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'custom_audit': self.check_custom_requirements()
        }

    def check_custom_requirements(self):
        audit_results = []
        target = (self.build.target_system or "").strip().lower()
        reqs = (self.build.system_requirements or "").strip().lower()
        
        if not target and not reqs:
            return audit_results
            
        import re
        
        # 1. Crypto / Mining System rules
        if any(x in target for x in ["crypto", "mining", "ethereum", "bitcoin"]) or any(x in reqs for x in ["crypto", "mining", "hash"]):
            # GPU requirement
            if not self.build.gpu:
                audit_results.append({
                    'status': 'error',
                    'message': "Crypto mining systems require a high-performance GPU to compute hashes."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"GPU Selected: {self.build.gpu.brand.name} {self.build.gpu.name} (Capable of crypto hash operations)."
                })
            
            # PSU requirement
            psu_watts = self.build.psu.psu_wattage_rating if (self.build.psu and self.build.psu.psu_wattage_rating) else 0
            if psu_watts < 750:
                audit_results.append({
                    'status': 'warning',
                    'message': "Mining operations run 24/7 at high load; a 750W+ gold-rated PSU is recommended."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"PSU Capacity: {psu_watts}W is sufficient for single-GPU mining load."
                })

        # 2. Trading System rules
        if any(x in target for x in ["trading", "stock", "forex", "finance"]) or any(x in reqs for x in ["trading", "stock", "chart"]):
            # Display requirement
            if not self.build.monitor:
                audit_results.append({
                    'status': 'warning',
                    'message': "Multi-monitor setups are standard for trading desks. Consider adding a display."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"Display configured: {self.build.monitor.brand.name} {self.build.monitor.name}."
                })
            
            # RAM requirement
            ram_size_gb = 0
            if self.build.ram:
                ram_name = self.build.ram.name.lower()
                match = re.search(r'(\d+)\s*gb', ram_name)
                if match:
                    ram_size_gb = int(match.group(1))
            
            if ram_size_gb < 16:
                audit_results.append({
                    'status': 'warning',
                    'message': "Day trading terminals benefit from at least 16GB RAM for running multiple charting platforms & feeds."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"Memory: {ram_size_gb}GB RAM is optimal for multitasking."
                })

        # 3. AI / Machine Learning rules
        if any(x in target for x in ["ai", "deep learning", "machine learning", "neural", "cuda"]) or any(x in reqs for x in ["ai", "deep learning", "cuda", "tensorflow", "pytorch"]):
            if not self.build.gpu:
                audit_results.append({
                    'status': 'error',
                    'message': "AI training/inference relies heavily on parallel hardware. A dedicated GPU is required."
                })
            elif "nvidia" not in self.build.gpu.brand.name.lower() and "nvidia" not in self.build.gpu.name.lower() and "rtx" not in self.build.gpu.name.lower():
                audit_results.append({
                    'status': 'warning',
                    'message': "NVIDIA GPUs with CUDA/Tensor cores are standard for AI workloads. AMD/Intel GPUs may have limited framework compatibility."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"NVIDIA RTX GPU '{self.build.gpu.brand.name} {self.build.gpu.name}' selected with tensor/CUDA core capabilities."
                })

        # 4. Check for explicitly typed specs in requirements notes (e.g. "32GB RAM", "1000W PSU", "SSD")
        # Check RAM size requirement explicitly typed (e.g. "32gb ram" or "64gb ram")
        ram_req_match = re.search(r'(\d+)\s*gb\s*ram', reqs)
        if ram_req_match:
            required_ram = int(ram_req_match.group(1))
            ram_size_gb = 0
            if self.build.ram:
                ram_name = self.build.ram.name.lower()
                m = re.search(r'(\d+)\s*gb', ram_name)
                if m:
                    ram_size_gb = int(m.group(1))
            
            if ram_size_gb < required_ram:
                audit_results.append({
                    'status': 'error',
                    'message': f"Requirement mismatch: Specified '{required_ram}GB RAM' in requirements, but selected RAM only provides '{ram_size_gb}GB'."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"Requirement met: Selected RAM has {ram_size_gb}GB, meeting your {required_ram}GB requirement."
                })

        # Check PSU wattage requirement explicitly typed (e.g. "850w psu" or "850w")
        psu_req_match = re.search(r'(\d+)\s*w\s*(psu|power)?', reqs)
        if psu_req_match:
            required_psu = int(psu_req_match.group(1))
            psu_watts = self.build.psu.psu_wattage_rating if (self.build.psu and self.build.psu.psu_wattage_rating) else 0
            if psu_watts < required_psu:
                audit_results.append({
                    'status': 'error',
                    'message': f"Requirement mismatch: Specified '{required_psu}W PSU' in requirements, but selected PSU is '{psu_watts}W'."
                })
            else:
                audit_results.append({
                    'status': 'success',
                    'message': f"Requirement met: Selected PSU is {psu_watts}W, meeting your {required_psu}W requirement."
                })

        return audit_results
