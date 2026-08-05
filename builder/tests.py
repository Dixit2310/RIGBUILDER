from django.test import TestCase
from django.core.files.base import ContentFile
from products.models import Brand, Category, Product
from builder.models import PCBuild
from builder.compatibility import CompatibilityChecker

class CompatibilityCheckerTestCase(TestCase):
    def setUp(self):
        # Setup Brands
        self.intel = Brand.objects.create(name="Intel")
        self.amd = Brand.objects.create(name="AMD")
        self.nvidia = Brand.objects.create(name="NVIDIA")
        self.msi = Brand.objects.create(name="MSI")
        self.nzxt = Brand.objects.create(name="NZXT")
        self.corsair = Brand.objects.create(name="Corsair")
        self.samsung = Brand.objects.create(name="Samsung")

        # Setup Categories
        self.cpu_cat = Category.objects.create(name="CPU", is_pc_component=True)
        self.mobo_cat = Category.objects.create(name="Motherboard", is_pc_component=True)
        self.ram_cat = Category.objects.create(name="RAM", is_pc_component=True)
        self.gpu_cat = Category.objects.create(name="GPU", is_pc_component=True)
        self.nvme_cat = Category.objects.create(name="NVMe SSD", is_pc_component=True)
        self.psu_cat = Category.objects.create(name="Power Supply", is_pc_component=True)
        self.cab_cat = Category.objects.create(name="Cabinet", is_pc_component=True)
        self.cooler_cat = Category.objects.create(name="CPU Cooler", is_pc_component=True)

        # Mock image data
        self.dummy_image = ContentFile(b"fake image data", name="dummy.png")

        # Create compatible products for base testing
        self.cpu_i9 = Product.objects.create(
            name="Core i9-14900K",
            brand=self.intel,
            category=self.cpu_cat,
            original_price_usd=580.00,
            power_consumption_watts=150,
            socket="LGA1700",
            image=self.dummy_image
        )

        self.mobo_z790 = Product.objects.create(
            name="Z790 Motherboard",
            brand=self.msi,
            category=self.mobo_cat,
            original_price_usd=300.00,
            power_consumption_watts=60,
            socket="LGA1700",
            ram_type="DDR5",
            ram_speed=6000,
            form_factor="ATX",
            nvme_slots_count=3,
            pcie_version="Gen5",
            image=self.dummy_image
        )

        self.mobo_b650 = Product.objects.create(
            name="B650 Motherboard",
            brand=self.msi,
            category=self.mobo_cat,
            original_price_usd=200.00,
            power_consumption_watts=45,
            socket="AM5",
            ram_type="DDR5",
            ram_speed=5600,
            form_factor="ATX",
            nvme_slots_count=2,
            pcie_version="Gen4",
            image=self.dummy_image
        )

        self.ram_ddr5 = Product.objects.create(
            name="DDR5 32GB 6000MHz",
            brand=self.corsair,
            category=self.ram_cat,
            original_price_usd=110.00,
            power_consumption_watts=8,
            ram_type="DDR5",
            image=self.dummy_image
        )

        self.gpu_rtx4070 = Product.objects.create(
            name="RTX 4070 Super",
            brand=self.msi,
            category=self.gpu_cat,
            original_price_usd=600.00,
            power_consumption_watts=220,
            gpu_length=240,
            pcie_version="Gen5",
            image=self.dummy_image
        )

        self.nvme_samsung = Product.objects.create(
            name="990 PRO 1TB",
            brand=self.samsung,
            category=self.nvme_cat,
            original_price_usd=90.00,
            power_consumption_watts=6,
            is_nvme=True,
            image=self.dummy_image
        )

        self.psu_850w = Product.objects.create(
            name="850W Gold PSU",
            brand=self.corsair,
            category=self.psu_cat,
            original_price_usd=130.00,
            psu_wattage_rating=850,
            image=self.dummy_image
        )

        self.cabinet_atx = Product.objects.create(
            name="ATX Mid Tower Case",
            brand=self.nzxt,
            category=self.cab_cat,
            original_price_usd=100.00,
            form_factor="ATX",
            gpu_length_limit=360,
            max_cooler_height=165,
            image=self.dummy_image
        )

        self.cooler_360 = Product.objects.create(
            name="360mm AIO Cooler",
            brand=self.corsair,
            category=self.cooler_cat,
            original_price_usd=150.00,
            power_consumption_watts=15,
            cooler_socket_support="LGA1700,AM5,AM4",
            cooler_height=52,
            image=self.dummy_image
        )

    def test_fully_compatible_build(self):
        """Test a build where all selected parts are compatible"""
        build = PCBuild.objects.create(
            name="Perfect Build",
            cpu=self.cpu_i9,
            motherboard=self.mobo_z790,
            ram=self.ram_ddr5,
            gpu=self.gpu_rtx4070,
            nvme=self.nvme_samsung,
            psu=self.psu_850w,
            cabinet=self.cabinet_atx,
            cpu_cooler=self.cooler_360
        )
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertTrue(result['is_compatible'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(len(result['warnings']), 0)

    def test_cpu_motherboard_socket_mismatch(self):
        """Test error when CPU socket does not match Motherboard socket"""
        cpu_am5 = Product.objects.create(
            name="Ryzen 7 7800X3D",
            brand=self.amd,
            category=self.cpu_cat,
            original_price_usd=370.00,
            socket="AM5",
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Mismatch Socket Build",
            cpu=cpu_am5,
            motherboard=self.mobo_z790 # LGA1700
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("Incompatible Socket" in err for err in result['errors']))
        # Should suggest motherboards supporting AM5
        self.assertTrue(any(sug['field'] == 'motherboard' for sug in result['suggestions']))

    def test_ram_motherboard_ddr_mismatch(self):
        """Test error when RAM DDR type does not match Motherboard RAM type"""
        ram_ddr4 = Product.objects.create(
            name="DDR4 16GB 3200MHz",
            brand=self.corsair,
            category=self.ram_cat,
            original_price_usd=40.00,
            ram_type="DDR4",
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Mismatch RAM Build",
            motherboard=self.mobo_z790, # DDR5
            ram=ram_ddr4
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("Incompatible RAM" in err for err in result['errors']))
        self.assertTrue(any(sug['field'] == 'ram' for sug in result['suggestions']))

    def test_motherboard_cabinet_form_factor_mismatch(self):
        """Test size mismatch when Motherboard form factor is larger than Cabinet limit"""
        cabinet_itx = Product.objects.create(
            name="Mini-ITX Case",
            brand=self.nzxt,
            category=self.cab_cat,
            original_price_usd=90.00,
            form_factor="Mini-ITX",
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Oversized Mobo Build",
            motherboard=self.mobo_z790, # ATX (Hierarchy ATX > Mini-ITX)
            cabinet=cabinet_itx
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("Incompatible Size" in err for err in result['errors']))
        self.assertTrue(any(sug['field'] == 'cabinet' for sug in result['suggestions']))

    def test_cpu_cooler_cabinet_height_clearance(self):
        """Test error when CPU cooler height exceeds Cabinet clearance limit"""
        cooler_tall = Product.objects.create(
            name="Very Tall Air Cooler",
            brand=self.msi,
            category=self.cooler_cat,
            original_price_usd=60.00,
            cooler_height=175,
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Tall Cooler Build",
            cabinet=self.cabinet_atx, # max height = 165
            cpu_cooler=cooler_tall
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("Cooler Height Clearance" in err for err in result['errors']))

    def test_gpu_cabinet_length_clearance(self):
        """Test error when GPU length exceeds Cabinet limit"""
        gpu_long = Product.objects.create(
            name="Gigantic RTX 4090",
            brand=self.msi,
            category=self.gpu_cat,
            original_price_usd=1600.00,
            gpu_length=380,
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Long GPU Build",
            cabinet=self.cabinet_atx, # limit = 360
            gpu=gpu_long
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("GPU Length Clearance" in err for err in result['errors']))
        self.assertTrue(any(sug['field'] == 'gpu' for sug in result['suggestions']))

    def test_power_supply_sufficiency(self):
        """Test warning when PSU wattage rating is below recommended load + margin"""
        gpu_power_hungry = Product.objects.create(
            name="Power Hungry GPU",
            brand=self.nvidia,
            category=self.gpu_cat,
            original_price_usd=800.00,
            power_consumption_watts=450, # very high load
            image=self.dummy_image
        )
        
        psu_small = Product.objects.create(
            name="500W PSU",
            brand=self.corsair,
            category=self.psu_cat,
            original_price_usd=50.00,
            psu_wattage_rating=500,
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="High Power Build",
            cpu=self.cpu_i9, # 150W
            motherboard=self.mobo_z790, # 60W
            gpu=gpu_power_hungry, # 450W
            psu=psu_small # Total load = 660W. Recommended = 660 * 1.2 = 792W > 500W
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        # Warning, but still technically compatible
        self.assertTrue(result['is_compatible'])
        self.assertTrue(any("Low Wattage" in warn for warn in result['warnings']))
        self.assertTrue(any(sug['field'] == 'psu' for sug in result['suggestions']))

    def test_cooler_bracket_support_warning(self):
        """Test warning when CPU Cooler does not include socket support brackets"""
        cooler_no_lga = Product.objects.create(
            name="AM4/AM5 Only Cooler",
            brand=self.msi,
            category=self.cooler_cat,
            original_price_usd=40.00,
            cooler_socket_support="AM5, AM4", # LGA1700 missing
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="No Bracket Build",
            cpu=self.cpu_i9, # socket = LGA1700
            cpu_cooler=cooler_no_lga
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertTrue(result['is_compatible'])
        self.assertTrue(any("Cooler Bracket" in warn for warn in result['warnings']))

    def test_motherboard_nvme_slot_mismatch(self):
        """Test error when Motherboard has 0 NVMe slots but NVMe SSD is selected"""
        mobo_no_nvme = Product.objects.create(
            name="Old/Budget Motherboard",
            brand=self.msi,
            category=self.mobo_cat,
            original_price_usd=60.00,
            nvme_slots_count=0,
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="No NVMe Slots Build",
            motherboard=mobo_no_nvme,
            nvme=self.nvme_samsung
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertFalse(result['is_compatible'])
        self.assertTrue(any("Motherboard does not have NVMe M.2 slots" in err for err in result['errors']))

    def test_pcie_version_mismatch_warning(self):
        """Test warning when GPU and Motherboard PCIe versions differ"""
        gpu_gen3 = Product.objects.create(
            name="Legacy GPU Gen3",
            brand=self.nvidia,
            category=self.gpu_cat,
            original_price_usd=100.00,
            pcie_version="Gen3",
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="PCIe Mismatch Build",
            motherboard=self.mobo_z790, # PCIe Gen5
            gpu=gpu_gen3
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertTrue(result['is_compatible'])
        self.assertTrue(any("PCIe Version Mismatch" in warn for warn in result['warnings']))

    def test_ram_speed_downclock_warning(self):
        """Test warning when RAM speed exceeds Motherboard maximum supported RAM speed"""
        ram_fast = Product.objects.create(
            name="Super Fast RAM 7200MHz",
            brand=self.corsair,
            category=self.ram_cat,
            original_price_usd=200.00,
            ram_type="DDR5",
            ram_speed=7200,
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Fast RAM Build",
            motherboard=self.mobo_z790, # supports up to 6000MHz
            ram=ram_fast
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertTrue(result['is_compatible'])
        self.assertTrue(any("RAM Speed Downclock" in warn for warn in result['warnings']))

    def test_ssd_pcie_version_mismatch_warning(self):
        """Test warning when NVMe SSD PCIe speed exceeds Motherboard PCIe slot version speed capability"""
        ssd_gen5 = Product.objects.create(
            name="Gen5 SSD",
            brand=self.samsung,
            category=self.nvme_cat,
            original_price_usd=250.00,
            pcie_version="Gen5",
            image=self.dummy_image
        )
        
        build = PCBuild.objects.create(
            name="Gen5 SSD Gen4 Mobo Build",
            motherboard=self.mobo_b650, # PCIe Gen4
            nvme=ssd_gen5
        )
        
        checker = CompatibilityChecker(build)
        result = checker.check()

        self.assertTrue(result['is_compatible'])
        self.assertTrue(any("SSD Speed Capped" in warn for warn in result['warnings']))


class BuilderViewsTestCase(TestCase):
    def setUp(self):
        from products.models import Currency
        Currency.objects.create(code="USD", name="US Dollar", symbol="$", exchange_rate_to_usd=1.0000)
        self.intel = Brand.objects.create(name="Intel")
        self.cpu_cat = Category.objects.create(name="CPU", is_pc_component=True)
        self.dummy_image = ContentFile(b"fake image data", name="dummy.png")
        self.cpu = Product.objects.create(
            name="Core i9-14900K",
            brand=self.intel,
            category=self.cpu_cat,
            original_price_usd=580.00,
            image=self.dummy_image
        )
        self.build = PCBuild.objects.create(
            name="Test PC Build",
            cpu=self.cpu
        )
        from django.test import Client
        self.client = Client()
        session = self.client.session
        session['active_build_id'] = self.build.id
        session.save()

    def test_clear_build_view(self):
        from django.urls import reverse
        self.assertEqual(self.build.cpu, self.cpu)
        self.assertTrue(self.build.has_components)
        response = self.client.get(reverse('clear_build'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('builder'))
        self.build.refresh_from_db()
        self.assertIsNone(self.build.cpu)
        self.assertFalse(self.build.has_components)

