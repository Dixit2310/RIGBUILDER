from rest_framework import serializers
from .models import PCBuild
from products.serializers import ProductListSerializer

class PCBuildSerializer(serializers.ModelSerializer):
    # Retrieve nested product lists for each slot
    cpu_details = ProductListSerializer(source='cpu', read_only=True)
    motherboard_details = ProductListSerializer(source='motherboard', read_only=True)
    ram_details = ProductListSerializer(source='ram', read_only=True)
    gpu_details = ProductListSerializer(source='gpu', read_only=True)
    ssd_details = ProductListSerializer(source='ssd', read_only=True)
    hdd_details = ProductListSerializer(source='hdd', read_only=True)
    nvme_details = ProductListSerializer(source='nvme', read_only=True)
    psu_details = ProductListSerializer(source='psu', read_only=True)
    cabinet_details = ProductListSerializer(source='cabinet', read_only=True)
    cpu_cooler_details = ProductListSerializer(source='cpu_cooler', read_only=True)
    case_fans_details = ProductListSerializer(source='case_fans', read_only=True)
    
    # Peripheral Details
    monitor_details = ProductListSerializer(source='monitor', read_only=True)
    keyboard_details = ProductListSerializer(source='keyboard', read_only=True)
    mouse_details = ProductListSerializer(source='mouse', read_only=True)
    
    total_power = serializers.IntegerField(source='calculate_total_power', read_only=True)
    total_price = serializers.DecimalField(source='calculate_total_price_usd', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PCBuild
        fields = [
            'id', 'user', 'name', 'build_type', 'target_system', 'system_requirements', 'is_preset', 'is_favorite', 'created_at', 'updated_at',
            'total_power', 'total_price',
            
            # IDs for selection
            'cpu', 'motherboard', 'ram', 'gpu', 'ssd', 'hdd', 'nvme', 'psu', 'cabinet', 'cpu_cooler', 'case_fans',
            'monitor', 'keyboard', 'mouse', 'speakers', 'webcam', 'microphone', 'gaming_chair', 'mouse_pad',
            'thermal_paste', 'os', 'wifi_card', 'rgb_accessories',
            
            # Details for rendering
            'cpu_details', 'motherboard_details', 'ram_details', 'gpu_details', 
            'ssd_details', 'hdd_details', 'nvme_details', 'psu_details', 'cabinet_details',
            'cpu_cooler_details', 'case_fans_details', 'monitor_details', 'keyboard_details', 'mouse_details'
        ]
        read_only_fields = ['user', 'is_preset', 'created_at', 'updated_at']
