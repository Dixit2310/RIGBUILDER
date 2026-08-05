from django.core.management.base import BaseCommand
from products.models import Currency, Country, Brand, Category, Product
from builder.models import PCBuild

class Command(BaseCommand):
    help = "Seeds database with initial currencies, countries, brands, categories, and compatible components."

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing data to allow fresh seed with INR prices...")
        PCBuild.objects.filter(is_preset=True).delete()
        Product.objects.all().delete()

        self.stdout.write("Seeding/updating currencies...")
        inr, _ = Currency.objects.get_or_create(code="INR", defaults={'name': "Indian Rupee", 'symbol': "₹"})
        inr.exchange_rate_to_usd = 1.0000
        inr.save()
        
        usd, _ = Currency.objects.get_or_create(code="USD", defaults={'name': "US Dollar", 'symbol': "$"})
        usd.exchange_rate_to_usd = 0.0120
        usd.save()

        eur, _ = Currency.objects.get_or_create(code="EUR", defaults={'name': "Euro", 'symbol': "€"})
        eur.exchange_rate_to_usd = 0.0110
        eur.save()

        gbp, _ = Currency.objects.get_or_create(code="GBP", defaults={'name': "British Pound", 'symbol': "£"})
        gbp.exchange_rate_to_usd = 0.0094
        gbp.save()

        aed, _ = Currency.objects.get_or_create(code="AED", defaults={'name': "UAE Dirham", 'symbol': "AED"})
        aed.exchange_rate_to_usd = 0.0440
        aed.save()

        cad, _ = Currency.objects.get_or_create(code="CAD", defaults={'name': "Canadian Dollar", 'symbol': "C$"})
        cad.exchange_rate_to_usd = 0.0163
        cad.save()

        jpy, _ = Currency.objects.get_or_create(code="JPY", defaults={'name': "Japanese Yen", 'symbol': "¥"})
        jpy.exchange_rate_to_usd = 1.8667
        jpy.save()

        self.stdout.write("Seeding/updating countries...")
        india, _ = Country.objects.get_or_create(code="IN", defaults={'name': "India", 'currency': inr, 'flag_emoji': "🇮🇳"})
        india.default_tax_rate = 18.00
        india.default_shipping_charge = 50.00
        india.save()

        usa, _ = Country.objects.get_or_create(code="US", defaults={'name': "United States", 'currency': usd, 'flag_emoji': "🇺🇸"})
        usa.default_tax_rate = 8.50
        usa.default_shipping_charge = 1250.00
        usa.save()

        uk, _ = Country.objects.get_or_create(code="GB", defaults={'name': "United Kingdom", 'currency': gbp, 'flag_emoji': "🇬🇧"})
        uk.default_tax_rate = 20.00
        uk.default_shipping_charge = 1660.00
        uk.save()

        germany, _ = Country.objects.get_or_create(code="DE", defaults={'name': "Germany", 'currency': eur, 'flag_emoji': "🇩🇪"})
        germany.default_tax_rate = 19.00
        germany.default_shipping_charge = 2080.00
        germany.save()

        uae, _ = Country.objects.get_or_create(code="AE", defaults={'name': "United Arab Emirates", 'currency': aed, 'flag_emoji': "🇦🇪"})
        uae.default_tax_rate = 5.00
        uae.default_shipping_charge = 2500.00
        uae.save()

        self.stdout.write("Seeding brands...")
        intel, _ = Brand.objects.get_or_create(name="Intel", website_url="https://intel.com")
        amd, _ = Brand.objects.get_or_create(name="AMD", website_url="https://amd.com")
        nvidia, _ = Brand.objects.get_or_create(name="NVIDIA", website_url="https://nvidia.com")
        asus, _ = Brand.objects.get_or_create(name="ASUS", website_url="https://asus.com")
        msi, _ = Brand.objects.get_or_create(name="MSI", website_url="https://msi.com")
        corsair, _ = Brand.objects.get_or_create(name="Corsair", website_url="https://corsair.com")
        samsung, _ = Brand.objects.get_or_create(name="Samsung", website_url="https://samsung.com")
        nzxt, _ = Brand.objects.get_or_create(name="NZXT", website_url="https://nzxt.com")
        logitech, _ = Brand.objects.get_or_create(name="Logitech", website_url="https://logitech.com")
        seagate, _ = Brand.objects.get_or_create(name="Seagate", website_url="https://seagate.com")
        thermalright, _ = Brand.objects.get_or_create(name="Thermalright", website_url="https://thermalright.com")
        microsoft, _ = Brand.objects.get_or_create(name="Microsoft", website_url="https://microsoft.com")

        self.stdout.write("Seeding categories...")
        cpu_cat, _ = Category.objects.get_or_create(name="CPU", is_pc_component=True)
        mobo_cat, _ = Category.objects.get_or_create(name="Motherboard", is_pc_component=True)
        ram_cat, _ = Category.objects.get_or_create(name="RAM", is_pc_component=True)
        gpu_cat, _ = Category.objects.get_or_create(name="GPU", is_pc_component=True)
        nvme_cat, _ = Category.objects.get_or_create(name="NVMe SSD", is_pc_component=True)
        ssd_cat, _ = Category.objects.get_or_create(name="SSD", is_pc_component=True)
        hdd_cat, _ = Category.objects.get_or_create(name="HDD", is_pc_component=True)
        psu_cat, _ = Category.objects.get_or_create(name="Power Supply", is_pc_component=True)
        cab_cat, _ = Category.objects.get_or_create(name="Cabinet", is_pc_component=True)
        cooler_cat, _ = Category.objects.get_or_create(name="CPU Cooler", is_pc_component=True)
        fans_cat, _ = Category.objects.get_or_create(name="Case Fans", is_pc_component=True)
        monitor_cat, _ = Category.objects.get_or_create(name="Monitor", is_pc_component=False)
        keyboard_cat, _ = Category.objects.get_or_create(name="Keyboard", is_pc_component=False)
        mouse_cat, _ = Category.objects.get_or_create(name="Mouse", is_pc_component=False)
        os_cat, _ = Category.objects.get_or_create(name="Operating System", is_pc_component=False)

        self.stdout.write("Seeding products with real local images and INR prices...")
        
        # =========================================================================
        # --- CPUs (6 products) ---
        # =========================================================================
        i9_cpu, _ = Product.objects.get_or_create(
            name="Core i9-14900K",
            brand=intel,
            category=cpu_cat,
            defaults={
                'description': "Intel 14th Gen 24-Core desktop processor with integrated graphics.",
                'original_price_usd': 50000.00,
                'discount_percentage': 5.00,
                'power_consumption_watts': 150,
                'socket': "LGA1700",
                'image': 'products/intel_i9.jpg'
            }
        )

        r7_cpu, _ = Product.objects.get_or_create(
            name="Ryzen 7 7800X3D",
            brand=amd,
            category=cpu_cat,
            defaults={
                'description': "AMD Zen 4 8-Core processor with 3D V-Cache, optimized for high FPS gaming.",
                'original_price_usd': 35000.00,
                'discount_percentage': 0.00,
                'power_consumption_watts': 120,
                'socket': "AM5",
                'image': 'products/ryzen_7.jpg'
            }
        )

        r5_cpu, _ = Product.objects.get_or_create(
            name="Ryzen 5 5600X",
            brand=amd,
            category=cpu_cat,
            defaults={
                'description': "Classic AMD Zen 3 6-Core processor, ideal for budget-friendly builds.",
                'original_price_usd': 12000.00,
                'discount_percentage': 10.00,
                'power_consumption_watts': 65,
                'socket': "AM4",
                'image': 'products/ryzen_5.jpg'
            }
        )

        r9_cpu, _ = Product.objects.get_or_create(
            name="Ryzen 9 7950X",
            brand=amd,
            category=cpu_cat,
            defaults={
                'description': "Extreme 16-Core Zen 4 AMD desktop processor for heavy workloads.",
                'original_price_usd': 52000.00,
                'discount_percentage': 0.00,
                'power_consumption_watts': 170,
                'socket': "AM5",
                'image': 'products/ryzen_9.jpg'
            }
        )

        i7_cpu, _ = Product.objects.get_or_create(
            name="Core i7-14700K",
            brand=intel,
            category=cpu_cat,
            defaults={
                'description': "Powerful 20-Core 14th Gen Intel processor with hybrid architecture.",
                'original_price_usd': 36000.00,
                'discount_percentage': 8.00,
                'power_consumption_watts': 125,
                'socket': "LGA1700",
                'image': 'products/intel_i7.jpg'
            }
        )

        i5_cpu, _ = Product.objects.get_or_create(
            name="Core i5-12400F",
            brand=intel,
            category=cpu_cat,
            defaults={
                'description': "Value 6-Core LGA1700 desktop CPU without integrated graphics.",
                'original_price_usd': 10000.00,
                'discount_percentage': 0.00,
                'power_consumption_watts': 65,
                'socket': "LGA1700",
                'image': 'products/intel_i5.jpg'
            }
        )

        # =========================================================================
        # --- Motherboards (6 products) ---
        # =========================================================================
        z790_mobo, _ = Product.objects.get_or_create(
            name="ROG Maximus Z790 Hero",
            brand=asus,
            category=mobo_cat,
            defaults={
                'description': "Premium ATX motherboard supporting LGA1700 CPUs with DDR5 memory support.",
                'original_price_usd': 60000.00,
                'power_consumption_watts': 60,
                'socket': "LGA1700",
                'ram_type': "DDR5",
                'ram_speed': 6000,
                'form_factor': "ATX",
                'nvme_slots_count': 3,
                'pcie_version': "Gen5",
                'image': 'products/asus_z790.jpg'
            }
        )

        b650_mobo, _ = Product.objects.get_or_create(
            name="MAG B650 Tomahawk WiFi",
            brand=msi,
            category=mobo_cat,
            defaults={
                'description': "Mid-range AM5 ATX motherboard with built-in Wi-Fi 6E.",
                'original_price_usd': 22000.00,
                'power_consumption_watts': 45,
                'socket': "AM5",
                'ram_type': "DDR5",
                'ram_speed': 5600,
                'form_factor': "ATX",
                'nvme_slots_count': 2,
                'pcie_version': "Gen4",
                'image': 'products/msi_b650.jpg'
            }
        )

        b550_mobo, _ = Product.objects.get_or_create(
            name="B550-A PRO",
            brand=msi,
            category=mobo_cat,
            defaults={
                'description': "Reliable ATX motherboard for socket AM4, supporting DDR4 memory.",
                'original_price_usd': 10000.00,
                'power_consumption_watts': 35,
                'socket': "AM4",
                'ram_type': "DDR4",
                'ram_speed': 3200,
                'form_factor': "ATX",
                'nvme_slots_count': 2,
                'pcie_version': "Gen4",
                'image': 'products/msi_b550.jpg'
            }
        )

        b760_mobo, _ = Product.objects.get_or_create(
            name="Prime B760M-A D4",
            brand=asus,
            category=mobo_cat,
            defaults={
                'description': "Compact Micro-ATX LGA1700 motherboard with DDR4 memory support.",
                'original_price_usd': 11000.00,
                'power_consumption_watts': 30,
                'socket': "LGA1700",
                'ram_type': "DDR4",
                'ram_speed': 3200,
                'form_factor': "Micro-ATX",
                'nvme_slots_count': 2,
                'pcie_version': "Gen4",
                'image': 'products/asus_b760.jpg'
            }
        )

        z790_max_mobo, _ = Product.objects.get_or_create(
            name="PRO Z790-A MAX WIFI",
            brand=msi,
            category=mobo_cat,
            defaults={
                'description': "High performance DDR5 Z790 ATX motherboard with Wi-Fi 7.",
                'original_price_usd': 24000.00,
                'power_consumption_watts': 50,
                'socket': "LGA1700",
                'ram_type': "DDR5",
                'ram_speed': 6400,
                'form_factor': "ATX",
                'nvme_slots_count': 4,
                'pcie_version': "Gen5",
                'image': 'products/msi_z790_max.jpg'
            }
        )

        strix_b650_mobo, _ = Product.objects.get_or_create(
            name="ROG Strix B650-A Gaming WiFi",
            brand=asus,
            category=mobo_cat,
            defaults={
                'description': "Premium silver-themed AM5 ATX gaming motherboard.",
                'original_price_usd': 23000.00,
                'power_consumption_watts': 40,
                'socket': "AM5",
                'ram_type': "DDR5",
                'ram_speed': 6000,
                'form_factor': "ATX",
                'nvme_slots_count': 3,
                'pcie_version': "Gen4",
                'image': 'products/asus_strix_b650.jpg'
            }
        )

        # =========================================================================
        # --- RAM (6 products) ---
        # =========================================================================
        corsair_ram, _ = Product.objects.get_or_create(
            name="Vengeance 32GB DDR5 6000MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "High performance DDR5 RAM dual kit (2x16GB) with heatspreader.",
                'original_price_usd': 10000.00,
                'power_consumption_watts': 8,
                'ram_type': "DDR5",
                'ram_speed': 6000,
                'image': 'products/corsair_d5_32.jpg'
            }
        )

        corsair_ddr4_ram, _ = Product.objects.get_or_create(
            name="Vengeance LPX 16GB DDR4 3200MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "Compact DDR4 memory kit (2x8GB) with high compatibility.",
                'original_price_usd': 3500.00,
                'power_consumption_watts': 5,
                'ram_type': "DDR4",
                'ram_speed': 3200,
                'image': 'products/corsair_d4_16.jpg'
            }
        )

        corsair_dom_ram, _ = Product.objects.get_or_create(
            name="Dominator Platinum RGB 64GB DDR5 5600MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "Luxury high-capacity DDR5 RAM dual kit (2x32GB) with Capellix LEDs.",
                'original_price_usd': 20000.00,
                'power_consumption_watts': 10,
                'ram_type': "DDR5",
                'ram_speed': 5600,
                'image': 'products/corsair_dom_64.jpg'
            }
        )

        corsair_rgb_ram, _ = Product.objects.get_or_create(
            name="Vengeance RGB 32GB DDR5 6200MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "Dynamic multi-zone RGB DDR5 memory kit (2x16GB).",
                'original_price_usd': 12000.00,
                'power_consumption_watts': 9,
                'ram_type': "DDR5",
                'ram_speed': 6200,
                'image': 'products/corsair_rgb_32.jpg'
            }
        )

        corsair_ddr4_32_ram, _ = Product.objects.get_or_create(
            name="Vengeance LPX 32GB DDR4 3600MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "High performance DDR4 dual channel memory kit (2x16GB).",
                'original_price_usd': 7500.00,
                'power_consumption_watts': 6,
                'ram_type': "DDR4",
                'ram_speed': 3600,
                'image': 'products/corsair_d4_32.jpg'
            }
        )

        corsair_rgb_pro_ram, _ = Product.objects.get_or_create(
            name="Vengeance RGB PRO 16GB DDR4 3200MHz",
            brand=corsair,
            category=ram_cat,
            defaults={
                'description': "Vibrant RGB lighting DDR4 gaming RAM kit (2x8GB).",
                'original_price_usd': 5000.00,
                'power_consumption_watts': 7,
                'ram_type': "DDR4",
                'ram_speed': 3200,
                'image': 'products/corsair_rgb_pro_16.jpg'
            }
        )

        # =========================================================================
        # --- GPUs (6 products) ---
        # =========================================================================
        rtx4090, _ = Product.objects.get_or_create(
            name="GeForce RTX 4090 Gaming X Trio",
            brand=msi,
            category=gpu_cat,
            defaults={
                'description': "Enthusiast graphic card with 24GB GDDR6X, Ada Lovelace architecture.",
                'original_price_usd': 160000.00,
                'discount_percentage': 3.00,
                'power_consumption_watts': 450,
                'gpu_length': 337,
                'pcie_version': "Gen5",
                'rgb_support': True,
                'image': 'products/msi_rtx4090.jpg'
            }
        )

        rtx4070ti, _ = Product.objects.get_or_create(
            name="GeForce RTX 4070 Ti Super",
            brand=asus,
            category=gpu_cat,
            defaults={
                'description': "High-end gaming graphics card with 16GB VRAM.",
                'original_price_usd': 80000.00,
                'power_consumption_watts': 285,
                'gpu_length': 305,
                'pcie_version': "Gen4",
                'rgb_support': True,
                'image': 'products/asus_rtx4070ti.jpg'
            }
        )

        rtx4060, _ = Product.objects.get_or_create(
            name="GeForce RTX 4060 Ti Gaming X 8GB",
            brand=msi,
            category=gpu_cat,
            defaults={
                'description': "Efficient mid-range gaming graphics card with DLSS 3 support.",
                'original_price_usd': 38000.00,
                'power_consumption_watts': 160,
                'gpu_length': 240,
                'pcie_version': "Gen4",
                'rgb_support': True,
                'image': 'products/msi_rtx4060.jpg'
            }
        )

        rtx4080s, _ = Product.objects.get_or_create(
            name="ROG Strix GeForce RTX 4080 Super",
            brand=asus,
            category=gpu_cat,
            defaults={
                'description': "Premium massive cooling graphics card with 16GB GDDR6X.",
                'original_price_usd': 105000.00,
                'power_consumption_watts': 320,
                'gpu_length': 357,
                'pcie_version': "Gen4",
                'rgb_support': True,
                'image': 'products/asus_rtx4080s.jpg'
            }
        )

        rtx4060_2x, _ = Product.objects.get_or_create(
            name="GeForce RTX 4060 Ventus 2X",
            brand=msi,
            category=gpu_cat,
            defaults={
                'description': "Compact dual fan RTX 4060, perfect for small form factor builds.",
                'original_price_usd': 29000.00,
                'power_consumption_watts': 115,
                'gpu_length': 199,
                'pcie_version': "Gen4",
                'rgb_support': False,
                'image': 'products/msi_rtx4060_2x.jpg'
            }
        )

        rtx4070s, _ = Product.objects.get_or_create(
            name="GeForce RTX 4070 Super Dual",
            brand=asus,
            category=gpu_cat,
            defaults={
                'description': "Excellent performance-to-value gaming GPU with 12GB VRAM.",
                'original_price_usd': 60000.00,
                'power_consumption_watts': 220,
                'gpu_length': 267,
                'pcie_version': "Gen4",
                'rgb_support': False,
                'image': 'products/asus_rtx4070s.jpg'
            }
        )

        # =========================================================================
        # --- NVMe SSDs (6 products) ---
        # =========================================================================
        samsung_ssd, _ = Product.objects.get_or_create(
            name="990 PRO 2TB NVMe M.2",
            brand=samsung,
            category=nvme_cat,
            defaults={
                'description': "Lightning-fast PCIe Gen4 NVMe M.2 solid state drive.",
                'original_price_usd': 16000.00,
                'power_consumption_watts': 6,
                'is_nvme': True,
                'pcie_version': "Gen4",
                'image': 'products/samsung_990_2tb.jpg'
            }
        )

        samsung_980_ssd, _ = Product.objects.get_or_create(
            name="980 PRO 1TB NVMe M.2",
            brand=samsung,
            category=nvme_cat,
            defaults={
                'description': "Highly popular Gen4 SSD with outstanding reliability and cache.",
                'original_price_usd': 9500.00,
                'power_consumption_watts': 5,
                'is_nvme': True,
                'pcie_version': "Gen4",
                'image': 'products/samsung_980_1tb.jpg'
            }
        )

        samsung_990_4tb, _ = Product.objects.get_or_create(
            name="990 PRO 4TB NVMe M.2",
            brand=samsung,
            category=nvme_cat,
            defaults={
                'description': "Ultimate high-capacity desktop NVMe SSD with heatspreader compatibility.",
                'original_price_usd': 30000.00,
                'power_consumption_watts': 6,
                'is_nvme': True,
                'pcie_version': "Gen4",
                'image': 'products/samsung_990_4tb.jpg'
            }
        )

        seagate_firecuda_ssd, _ = Product.objects.get_or_create(
            name="FireCuda 530 2TB NVMe M.2",
            brand=seagate,
            category=nvme_cat,
            defaults={
                'description': "Extreme endurance gaming SSD with high speeds and PS5 support.",
                'original_price_usd': 15000.00,
                'power_consumption_watts': 7,
                'is_nvme': True,
                'pcie_version': "Gen4",
                'image': 'products/seagate_firecuda_2tb.jpg'
            }
        )

        samsung_970_ssd, _ = Product.objects.get_or_create(
            name="970 EVO Plus 1TB NVMe M.2",
            brand=samsung,
            category=nvme_cat,
            defaults={
                'description': "Reliable PCIe Gen3 NVMe SSD, great for secondary storage slots.",
                'original_price_usd': 7500.00,
                'power_consumption_watts': 5,
                'is_nvme': True,
                'pcie_version': "Gen3",
                'image': 'products/samsung_970_1tb.jpg'
            }
        )

        seagate_cuda_510, _ = Product.objects.get_or_create(
            name="BarraCuda 510 500GB NVMe M.2",
            brand=seagate,
            category=nvme_cat,
            defaults={
                'description': "Budget-friendly PCIe Gen3 boot drive SSD.",
                'original_price_usd': 4000.00,
                'power_consumption_watts': 4,
                'is_nvme': True,
                'pcie_version': "Gen3",
                'image': 'products/seagate_cuda_500gb.jpg'
            }
        )

        # =========================================================================
        # --- SATA SSDs (6 products) ---
        # =========================================================================
        samsung_sata_ssd, _ = Product.objects.get_or_create(
            name="870 EVO 1TB SATA III",
            brand=samsung,
            category=ssd_cat,
            defaults={
                'description': "Industry standard reliable SATA III 2.5 inch internal solid state drive.",
                'original_price_usd': 8500.00,
                'power_consumption_watts': 4,
                'is_nvme': False,
                'image': 'products/samsung_870_1tb.jpg'
            }
        )

        samsung_qvo_2tb, _ = Product.objects.get_or_create(
            name="870 QVO 2TB SATA III",
            brand=samsung,
            category=ssd_cat,
            defaults={
                'description': "High capacity QLC SATA III SSD for bulk files and media loading.",
                'original_price_usd': 13000.00,
                'power_consumption_watts': 4,
                'is_nvme': False,
                'image': 'products/samsung_qvo_2tb.jpg'
            }
        )

        samsung_qvo_4tb, _ = Product.objects.get_or_create(
            name="870 QVO 4TB SATA III",
            brand=samsung,
            category=ssd_cat,
            defaults={
                'description': "Massive storage size SATA III SSD, replacing noisy HDDs.",
                'original_price_usd': 25000.00,
                'power_consumption_watts': 5,
                'is_nvme': False,
                'image': 'products/samsung_qvo_4tb.jpg'
            }
        )

        seagate_cuda_ssd, _ = Product.objects.get_or_create(
            name="BarraCuda 120 1TB SATA III",
            brand=seagate,
            category=ssd_cat,
            defaults={
                'description': "Reliable 2.5 inch solid state drive with Seagate durability.",
                'original_price_usd': 7500.00,
                'power_consumption_watts': 4,
                'is_nvme': False,
                'image': 'products/seagate_cuda_1tb.jpg'
            }
        )

        samsung_sata_500gb, _ = Product.objects.get_or_create(
            name="870 EVO 500GB SATA III",
            brand=samsung,
            category=ssd_cat,
            defaults={
                'description': "Excellent reliable SATA III solid state drive for office PCs.",
                'original_price_usd': 5000.00,
                'power_consumption_watts': 3,
                'is_nvme': False,
                'image': 'products/samsung_870_500gb.jpg'
            }
        )

        samsung_evo_4tb, _ = Product.objects.get_or_create(
            name="870 EVO 4TB SATA III",
            brand=samsung,
            category=ssd_cat,
            defaults={
                'description': "Top performance SATA III solid state drive for heavy caching.",
                'original_price_usd': 28000.00,
                'power_consumption_watts': 5,
                'is_nvme': False,
                'image': 'products/samsung_evo_4tb.jpg'
            }
        )

        # =========================================================================
        # --- HDDs (6 products) ---
        # =========================================================================
        seagate_hdd, _ = Product.objects.get_or_create(
            name="BarraCuda 2TB 7200 RPM",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "Cost-efficient bulk internal hard disk drive.",
                'original_price_usd': 5500.00,
                'power_consumption_watts': 8,
                'image': 'products/seagate_2tb.jpg'
            }
        )

        seagate_iron_4tb, _ = Product.objects.get_or_create(
            name="IronWolf Pro 4TB NAS HDD",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "High performance NAS internal hard disk drive with AgileArray firmware.",
                'original_price_usd': 11000.00,
                'power_consumption_watts': 7,
                'image': 'products/seagate_nas_4tb.jpg'
            }
        )

        seagate_cuda_4tb, _ = Product.objects.get_or_create(
            name="BarraCuda 4TB 5400 RPM",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "Quiet low power internal hard disk drive for backups.",
                'original_price_usd': 8500.00,
                'power_consumption_watts': 6,
                'image': 'products/seagate_4tb.jpg'
            }
        )

        seagate_iron_8tb, _ = Product.objects.get_or_create(
            name="IronWolf 8TB NAS HDD",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "High-reliability NAS hard disk drive, built for multi-user arrays.",
                'original_price_usd': 18000.00,
                'power_consumption_watts': 8,
                'image': 'products/seagate_nas_8tb.jpg'
            }
        )

        seagate_cuda_pro_10tb, _ = Product.objects.get_or_create(
            name="BarraCuda Pro 10TB 7200 RPM",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "Enthusiast class massive capacity desktop internal hard disk drive.",
                'original_price_usd': 28000.00,
                'power_consumption_watts': 9,
                'image': 'products/seagate_pro_10tb.jpg'
            }
        )

        seagate_cuda_1tb, _ = Product.objects.get_or_create(
            name="BarraCuda 1TB 7200 RPM",
            brand=seagate,
            category=hdd_cat,
            defaults={
                'description': "Entry level SATA internal hard drive for general file storage.",
                'original_price_usd': 4000.00,
                'power_consumption_watts': 6,
                'image': 'products/seagate_1tb.jpg'
            }
        )

        # =========================================================================
        # --- PSUs (6 products) ---
        # =========================================================================
        corsair_psu, _ = Product.objects.get_or_create(
            name="RM850x 850W Gold Modular",
            brand=corsair,
            category=psu_cat,
            defaults={
                'description': "80 Plus Gold certified fully modular quiet power supply.",
                'original_price_usd': 12000.00,
                'psu_wattage_rating': 850,
                'image': 'products/corsair_850w.jpg'
            }
        )

        corsair_psu_650, _ = Product.objects.get_or_create(
            name="CX650M 650W Bronze Semi-Modular",
            brand=corsair,
            category=psu_cat,
            defaults={
                'description': "Reliable 80 Plus Bronze certified power supply for budget builds.",
                'original_price_usd': 6500.00,
                'psu_wattage_rating': 650,
                'image': 'products/corsair_650w.jpg'
            }
        )

        corsair_rm1000x, _ = Product.objects.get_or_create(
            name="RM1000x 1000W Gold Modular",
            brand=corsair,
            category=psu_cat,
            defaults={
                'description': "Heavy duty 1000W fully modular power supply for multi-GPU setups.",
                'original_price_usd': 18000.00,
                'psu_wattage_rating': 1000,
                'image': 'products/corsair_1000w.jpg'
            }
        )

        nzxt_c1200, _ = Product.objects.get_or_create(
            name="C1200 1200W Gold PCIe 5.0 ATX 3.0",
            brand=nzxt,
            category=psu_cat,
            defaults={
                'description': "Next-gen power supply with native 12VHPWR connector.",
                'original_price_usd': 21000.00,
                'psu_wattage_rating': 1200,
                'image': 'products/nzxt_1200w.jpg'
            }
        )

        corsair_sf750, _ = Product.objects.get_or_create(
            name="SF750 750W Platinum SFX",
            brand=corsair,
            category=psu_cat,
            defaults={
                'description': "High performance SFX power supply for compact SFF cases.",
                'original_price_usd': 16000.00,
                'psu_wattage_rating': 750,
                'image': 'products/corsair_750w.jpg'
            }
        )

        nzxt_c750, _ = Product.objects.get_or_create(
            name="C750 Gold Modular 750W",
            brand=nzxt,
            category=psu_cat,
            defaults={
                'description': "Efficient fully modular Gold power supply with Zero-RPM Fan mode.",
                'original_price_usd': 11000.00,
                'psu_wattage_rating': 750,
                'image': 'products/nzxt_750w.jpg'
            }
        )

        # =========================================================================
        # --- Cabinets (6 products) ---
        # =========================================================================
        nzxt_case, _ = Product.objects.get_or_create(
            name="H9 Flow Mid-Tower",
            brand=nzxt,
            category=cab_cat,
            defaults={
                'description': "Dual-chamber ATX mid-tower PC cabinet with high airflow mesh panel.",
                'original_price_usd': 15000.00,
                'form_factor': "ATX",
                'gpu_length_limit': 435,
                'max_cooler_height': 165,
                'image': 'products/nzxt_h9.jpg'
            }
        )

        corsair_case, _ = Product.objects.get_or_create(
            name="4000D Airflow Tempered Glass",
            brand=corsair,
            category=cab_cat,
            defaults={
                'description': "High airflow ATX mid-tower case with simple cable routing system.",
                'original_price_usd': 8500.00,
                'form_factor': "ATX",
                'gpu_length_limit': 360,
                'max_cooler_height': 170,
                'image': 'products/corsair_4000d.jpg'
            }
        )

        nzxt_h5_case, _ = Product.objects.get_or_create(
            name="H5 Flow Compact Mid-Tower",
            brand=nzxt,
            category=cab_cat,
            defaults={
                'description': "Compact ATX mid-tower case with dedicated GPU air duct cooling.",
                'original_price_usd': 9000.00,
                'form_factor': "ATX",
                'gpu_length_limit': 365,
                'max_cooler_height': 165,
                'image': 'products/nzxt_h5.jpg'
            }
        )

        nzxt_h1_case, _ = Product.objects.get_or_create(
            name="H1 V2 Mini-ITX vertical case",
            brand=nzxt,
            category=cab_cat,
            defaults={
                'description': "Vertical Mini-ITX case with built-in AIO liquid cooler and 750W PSU.",
                'original_price_usd': 19000.00,
                'form_factor': "Mini-ITX",
                'gpu_length_limit': 324,
                'max_cooler_height': 140,
                'image': 'products/nzxt_h1.jpg'
            }
        )

        corsair_5000d, _ = Product.objects.get_or_create(
            name="iCUE 5000D RGB Airflow",
            brand=corsair,
            category=cab_cat,
            defaults={
                'description': "Premium ATX mid-tower PC case with three pre-installed SP RGB fans.",
                'original_price_usd': 19000.00,
                'form_factor': "ATX",
                'gpu_length_limit': 400,
                'max_cooler_height': 170,
                'image': 'products/corsair_5000d.jpg'
            }
        )

        corsair_2000d, _ = Product.objects.get_or_create(
            name="2000D RGB Airflow Mini-ITX",
            brand=corsair,
            category=cab_cat,
            defaults={
                'description': "Mini-ITX case with high airflow panels and triple fan bracket.",
                'original_price_usd': 14000.00,
                'form_factor': "Mini-ITX",
                'gpu_length_limit': 365,
                'max_cooler_height': 165,
                'image': 'products/corsair_2000d.jpg'
            }
        )

        # =========================================================================
        # --- CPU Coolers (6 products) ---
        # =========================================================================
        corsair_cooler, _ = Product.objects.get_or_create(
            name="iCUE H150i Elite Liquid Cooler",
            brand=corsair,
            category=cooler_cat,
            defaults={
                'description': "360mm AIO liquid processor cooler with RGB fans.",
                'original_price_usd': 18000.00,
                'power_consumption_watts': 15,
                'cooler_socket_support': "LGA1700,AM5,AM4",
                'cooler_height': 52,
                'image': 'products/corsair_h150i.jpg'
            }
        )

        tr_cooler, _ = Product.objects.get_or_create(
            name="Peerless Assassin 120 SE Air Cooler",
            brand=thermalright,
            category=cooler_cat,
            defaults={
                'description': "Highly rated dual-tower CPU air cooler with 6 heat pipes.",
                'original_price_usd': 3500.00,
                'power_consumption_watts': 5,
                'cooler_socket_support': "LGA1700,AM5,AM4",
                'cooler_height': 155,
                'image': 'products/tr_peerless.jpg'
            }
        )

        nzxt_kraken_elite, _ = Product.objects.get_or_create(
            name="Kraken Elite 360 RGB AIO",
            brand=nzxt,
            category=cooler_cat,
            defaults={
                'description': "360mm premium liquid cooler with customizable LCD display screen.",
                'original_price_usd': 27000.00,
                'power_consumption_watts': 15,
                'cooler_socket_support': "LGA1700,AM5,AM4",
                'cooler_height': 53,
                'image': 'products/nzxt_kraken_elite.jpg'
            }
        )

        tr_assassin_x, _ = Product.objects.get_or_create(
            name="Assassin X 120 Refined SE",
            brand=thermalright,
            category=cooler_cat,
            defaults={
                'description': "Single-tower quiet CPU air cooler, perfect for budget configurations.",
                'original_price_usd': 1900.00,
                'power_consumption_watts': 4,
                'cooler_socket_support': "LGA1700,AM5,AM4",
                'cooler_height': 148,
                'image': 'products/tr_assassin_x.jpg'
            }
        )

        nzxt_kraken_240, _ = Product.objects.get_or_create(
            name="Kraken 240 Black AIO",
            brand=nzxt,
            category=cooler_cat,
            defaults={
                'description': "240mm AIO liquid cooler with standard square screen display.",
                'original_price_usd': 13000.00,
                'power_consumption_watts': 12,
                'cooler_socket_support': "LGA1700,AM5,AM4",
                'cooler_height': 50,
                'image': 'products/nzxt_kraken_240.jpg'
            }
        )

        corsair_a500, _ = Product.objects.get_or_create(
            name="A500 Dual Fan Air Cooler",
            brand=corsair,
            category=cooler_cat,
            defaults={
                'description': "Quad heatpipe CPU air cooler with slide-and-lock fan mounting system.",
                'original_price_usd': 9500.00,
                'power_consumption_watts': 6,
                'cooler_socket_support': "LGA1700,AM4,LGA1200",
                'cooler_height': 169,
                'image': 'products/corsair_a500.jpg'
            }
        )

        # =========================================================================
        # --- Case Fans (6 products) ---
        # =========================================================================
        corsair_fans, _ = Product.objects.get_or_create(
            name="SP120 RGB Elite 120mm 3-Pack",
            brand=corsair,
            category=fans_cat,
            defaults={
                'description': "Three 120mm RGB LED PWM case fans with Lighting Node CORE controller.",
                'original_price_usd': 5500.00,
                'power_consumption_watts': 6,
                'image': 'products/corsair_sp120.jpg'
            }
        )

        corsair_ll120, _ = Product.objects.get_or_create(
            name="LL120 RGB 120mm Dual Loop 3-Pack",
            brand=corsair,
            category=fans_cat,
            defaults={
                'description': "Premium dual loop light ring RGB case fans with command center.",
                'original_price_usd': 8500.00,
                'power_consumption_watts': 8,
                'image': 'products/corsair_ll120.jpg'
            }
        )

        nzxt_f120_fans, _ = Product.objects.get_or_create(
            name="F120 RGB Core 120mm 3-Pack",
            brand=nzxt,
            category=fans_cat,
            defaults={
                'description': "Flow and static pressure custom RGB fans for NZXT cases.",
                'original_price_usd': 7500.00,
                'power_consumption_watts': 7,
                'image': 'products/nzxt_f120.jpg'
            }
        )

        corsair_qx120, _ = Product.objects.get_or_create(
            name="iCUE LINK QX120 RGB Starter Kit",
            brand=corsair,
            category=fans_cat,
            defaults={
                'description': "Daisy-chain smart link active RGB fans with System Hub controller.",
                'original_price_usd': 13000.00,
                'power_consumption_watts': 9,
                'image': 'products/corsair_qx120.jpg'
            }
        )

        tr_c12_fans, _ = Product.objects.get_or_create(
            name="Thermalright TL-C12C 120mm 3-Pack",
            brand=thermalright,
            category=fans_cat,
            defaults={
                'description': "High quality quiet cooling fans with hydraulic bearings.",
                'original_price_usd': 1300.00,
                'power_consumption_watts': 4,
                'image': 'products/tr_c12.jpg'
            }
        )

        nzxt_f140_fans, _ = Product.objects.get_or_create(
            name="F140 RGB Duo 140mm 2-Pack",
            brand=nzxt,
            category=fans_cat,
            defaults={
                'description': "Double-sided 140mm RGB fans kit with RGB controller.",
                'original_price_usd': 6500.00,
                'power_consumption_watts': 6,
                'image': 'products/nzxt_f140.jpg'
            }
        )

        # =========================================================================
        # --- Monitors (6 products) ---
        # =========================================================================
        asus_monitor, _ = Product.objects.get_or_create(
            name="TUF Gaming VG27AQ 27\" 1440p",
            brand=asus,
            category=monitor_cat,
            defaults={
                'description': "IPS 165Hz gaming monitor with G-SYNC compatibility.",
                'original_price_usd': 24000.00,
                'image': 'products/asus_tuf_monitor.jpg'
            }
        )

        asus_pg42uq, _ = Product.objects.get_or_create(
            name="ROG Swift OLED PG42UQ 42\" 4K",
            brand=asus,
            category=monitor_cat,
            defaults={
                'description': "Anti-glare 138Hz OLED gaming monitor with HDMI 2.1 inputs.",
                'original_price_usd': 120000.00,
                'image': 'products/asus_pg42uq.jpg'
            }
        )

        msi_mag274, _ = Product.objects.get_or_create(
            name="Optix MAG274QRF-QD 27\" 1440p",
            brand=msi,
            category=monitor_cat,
            defaults={
                'description': "Quantum Dot IPS 165Hz high-gamut fast response gaming monitor.",
                'original_price_usd': 32000.00,
                'image': 'products/msi_mag274.jpg'
            }
        )

        asus_xg27aqmr, _ = Product.objects.get_or_create(
            name="ROG Strix XG27AQMR 27\" 270Hz",
            brand=asus,
            category=monitor_cat,
            defaults={
                'description': "Super fast 270Hz IPS gaming monitor for esports competitors.",
                'original_price_usd': 44000.00,
                'image': 'products/asus_xg27aqmr.jpg'
            }
        )

        msi_g241v, _ = Product.objects.get_or_create(
            name="Optix G241V E2 24\" IPS 75Hz",
            brand=msi,
            category=monitor_cat,
            defaults={
                'description': "Essential IPS monitor, great for setup testing or secondary screen.",
                'original_price_usd': 10000.00,
                'image': 'products/msi_g241v.jpg'
            }
        )

        asus_mb16ac, _ = Product.objects.get_or_create(
            name="ZenScreen MB16AC 15.6\" Portable",
            brand=asus,
            category=monitor_cat,
            defaults={
                'description': "Sleek portable USB-C monitor, ideal for coding on-the-go.",
                'original_price_usd': 18000.00,
                'image': 'products/asus_mb16ac.jpg'
            }
        )

        # =========================================================================
        # --- Keyboards (6 products) ---
        # =========================================================================
        logi_keyboard, _ = Product.objects.get_or_create(
            name="G213 Prodigy RGB Gaming Keyboard",
            brand=logitech,
            category=keyboard_cat,
            defaults={
                'description': "Durable spill-resistant membrane keyboard with gaming key matrix.",
                'original_price_usd': 4500.00,
                'image': 'products/logi_g213.jpg'
            }
        )

        corsair_k70, _ = Product.objects.get_or_create(
            name="K70 RGB PRO Mechanical Keyboard",
            brand=corsair,
            category=keyboard_cat,
            defaults={
                'description': "Premium Cherry MX Red switch gaming keyboard with aluminum frame.",
                'original_price_usd': 16000.00,
                'image': 'products/corsair_k70.jpg'
            }
        )

        logi_g915, _ = Product.objects.get_or_create(
            name="G915 TKL Wireless Mechanical Keyboard",
            brand=logitech,
            category=keyboard_cat,
            defaults={
                'description': "Low-profile LIGHTSPEED wireless keyboard with RGB keys.",
                'original_price_usd': 19000.00,
                'image': 'products/logi_g915.jpg'
            }
        )

        asus_scope_ii, _ = Product.objects.get_or_create(
            name="ROG Strix Scope II 96 Wireless",
            brand=asus,
            category=keyboard_cat,
            defaults={
                'description': "96% hot-swappable gaming mechanical keyboard with foam dampening.",
                'original_price_usd': 14000.00,
                'image': 'products/asus_scope_ii.jpg'
            }
        )

        logi_mx_keys, _ = Product.objects.get_or_create(
            name="MX Keys S Wireless Office Keyboard",
            brand=logitech,
            category=keyboard_cat,
            defaults={
                'description': "Premium productivity wireless typing keyboard with smart backlighting.",
                'original_price_usd': 11000.00,
                'image': 'products/logi_mx_keys.jpg'
            }
        )

        corsair_k55, _ = Product.objects.get_or_create(
            name="K55 RGB PRO Macro Key Keyboard",
            brand=corsair,
            category=keyboard_cat,
            defaults={
                'description': "Customizable zone RGB membrane keyboard with dedicated macro keys.",
                'original_price_usd': 4500.00,
                'image': 'products/corsair_k55.jpg'
            }
        )

        # =========================================================================
        # --- Mice (6 products) ---
        # =========================================================================
        logi_mouse, _ = Product.objects.get_or_create(
            name="G502 HERO High Performance Mouse",
            brand=logitech,
            category=mouse_cat,
            defaults={
                'description': "Ergonomic gaming mouse with 25K HERO sensor and adjustable weights.",
                'original_price_usd': 3900.00,
                'image': 'products/logi_g502.jpg'
            }
        )

        logi_superlight, _ = Product.objects.get_or_create(
            name="G PRO X SUPERLIGHT 2 wireless",
            brand=logitech,
            category=mouse_cat,
            defaults={
                'description': "Pro-grade ultra lightweight esports wireless mouse (60g).",
                'original_price_usd': 15000.00,
                'image': 'products/logi_superlight.jpg'
            }
        )

        corsair_dark_core, _ = Product.objects.get_or_create(
            name="Dark Core RGB Pro SE Wireless",
            brand=corsair,
            category=mouse_cat,
            defaults={
                'description': "Ergonomic gaming mouse with Qi wireless charging support.",
                'original_price_usd': 8500.00,
                'image': 'products/corsair_dark_core.jpg'
            }
        )

        asus_harpe, _ = Product.objects.get_or_create(
            name="ROG Harpe Ace Aim Lab Edition",
            brand=asus,
            category=mouse_cat,
            defaults={
                'description': "Esports-tuned lightweight wireless mouse co-developed with Aim Lab.",
                'original_price_usd': 13000.00,
                'image': 'products/asus_harpe.jpg'
            }
        )

        logi_g305, _ = Product.objects.get_or_create(
            name="G305 LIGHTSPEED Wireless Mouse",
            brand=logitech,
            category=mouse_cat,
            defaults={
                'description': "Reliable wireless mouse with HERO sensor and long battery life.",
                'original_price_usd': 3900.00,
                'image': 'products/logi_g305.jpg'
            }
        )

        corsair_harpoon, _ = Product.objects.get_or_create(
            name="Harpoon RGB Wireless Mouse",
            brand=corsair,
            category=mouse_cat,
            defaults={
                'description': "Comfortable contoured lightweight budget wireless gaming mouse.",
                'original_price_usd': 4500.00,
                'image': 'products/corsair_harpoon.jpg'
            }
        )

        # =========================================================================
        # --- Operating Systems (6 products) ---
        # =========================================================================
        win_os, _ = Product.objects.get_or_create(
            name="Windows 11 Home Retail",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "Standard edition retail license code for Windows 11.",
                'original_price_usd': 11000.00,
                'image': 'products/win11_home.jpg'
            }
        )

        win11_pro, _ = Product.objects.get_or_create(
            name="Windows 11 Pro Retail",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "Professional edition retail license code with advanced security features.",
                'original_price_usd': 19000.00,
                'image': 'products/win11_pro.jpg'
            }
        )

        win10_home, _ = Product.objects.get_or_create(
            name="Windows 10 Home Retail",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "Standard retail license code for Windows 10 OS.",
                'original_price_usd': 10000.00,
                'image': 'products/win10_home.jpg'
            }
        )

        win10_pro, _ = Product.objects.get_or_create(
            name="Windows 10 Pro Retail",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "Professional retail license code for Windows 10 OS.",
                'original_price_usd': 18000.00,
                'image': 'products/win10_pro.jpg'
            }
        )

        win11_home_oem, _ = Product.objects.get_or_create(
            name="Windows 11 Home OEM",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "OEM license version of Windows 11 Home, tied to motherboard.",
                'original_price_usd': 9000.00,
                'image': 'products/win11_home_oem.jpg'
            }
        )

        win11_pro_oem, _ = Product.objects.get_or_create(
            name="Windows 11 Pro OEM",
            brand=microsoft,
            category=os_cat,
            defaults={
                'description': "OEM license version of Windows 11 Professional.",
                'original_price_usd': 14000.00,
                'image': 'products/win11_pro_oem.jpg'
            }
        )

        # Seeding presets
        self.stdout.write("Seeding presets...")
        PCBuild.objects.get_or_create(
            name="Intel Ultimate Gaming Rig",
            is_preset=True,
            defaults={
                'cpu': i9_cpu,
                'motherboard': z790_mobo,
                'ram': corsair_ram,
                'gpu': rtx4090,
                'nvme': samsung_ssd,
                'psu': corsair_psu,
                'cabinet': nzxt_case,
                'cpu_cooler': corsair_cooler,
                'build_type': PCBuild.BuildType.GAMING
            }
        )

        PCBuild.objects.get_or_create(
            name="AMD Gamer's Dream",
            is_preset=True,
            defaults={
                'cpu': r7_cpu,
                'motherboard': b650_mobo,
                'ram': corsair_ram,
                'gpu': rtx4070ti,
                'nvme': samsung_ssd,
                'psu': corsair_psu,
                'cabinet': nzxt_case,
                'cpu_cooler': corsair_cooler,
                'build_type': PCBuild.BuildType.GAMING
            }
        )

        PCBuild.objects.get_or_create(
            name="Budget Performance Rig",
            is_preset=True,
            defaults={
                'cpu': r5_cpu,
                'motherboard': b550_mobo,
                'ram': corsair_ddr4_ram,
                'gpu': rtx4060,
                'ssd': samsung_sata_ssd,
                'hdd': seagate_hdd,
                'psu': corsair_psu_650,
                'cabinet': corsair_case,
                'cpu_cooler': tr_cooler,
                'case_fans': corsair_fans,
                'monitor': asus_monitor,
                'keyboard': logi_keyboard,
                'mouse': logi_mouse,
                'os': win_os,
                'build_type': PCBuild.BuildType.BUDGET
            }
        )

        # Seed Inventory objects for all products
        self.stdout.write("Seeding inventories...")
        from orders.models import Inventory
        for product in Product.objects.all():
            Inventory.objects.get_or_create(
                product=product,
                defaults={'total_stock': product.stock}
            )

        self.stdout.write("Database seeded successfully with INR base prices!")
