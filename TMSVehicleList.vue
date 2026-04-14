<script setup lang="ts">
import { ref, onMounted } from 'vue';
import CommonTable from '@/components/CommonTable.vue';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { uiScreenService } from '@/core/api/uiScreen.service';

const emit = defineEmits(['createNew', 'editVehicle']);

const items = ref<any[]>([]);
const isLoading = ref(false);
const columns = ref<any[]>([]);
const gridPageSize = ref(20);

const vehicleTypeOptions = ref<any[]>([]);
const orgOptions = ref<any[]>([]);

const fetchFilterOptions = async () => {
    try {
        const [types, orgs] = await Promise.all([
            masterDataService.getResourceList('Vehicle Type', ['name', 'vehicle_type_name']),
            masterDataService.getResourceList('MDM Org Header', ['name', 'full_name'])
        ]);
        vehicleTypeOptions.value = types.map((t: any) => ({ label: t.vehicle_type_name, value: t.name }));
        orgOptions.value = orgs.map((o: any) => ({ label: o.full_name, value: o.name }));
    } catch (e) {
        console.error("Filter Options Fetch Error:", e);
    }
};

const applyScreenConfig = () => {
    // 1. Define Full Schema for Filters & Possible Columns
    const baseSchema: any[] = [
        { field: 'vehicle_number', header: 'Vehicle No', sortable: true, style: { width: '150px' } },
        { 
            field: 'vehicle_type', 
            header: 'Type', 
            sortable: true, 
            style: { width: '150px' },
            filterType: 'select',
            filterOptions: vehicleTypeOptions.value
        },
        { 
            field: 'organization', 
            header: 'Organization', 
            sortable: true, 
            style: { width: '180px' },
            filterType: 'select',
            filterOptions: orgOptions.value
        },
        { field: 'branch', header: 'Branch', sortable: true, style: { width: '150px' } },
        { field: 'carrier', header: 'Carrier', sortable: true, style: { width: '180px' } },
        { 
            field: 'owner_type', 
            header: 'Owner Type', 
            sortable: true, 
            style: { width: '120px' },
            filterType: 'select',
            filterOptions: [
                { label: 'Owned', value: 'Owned' },
                { label: 'Attached', value: 'Attached' },
                { label: 'Leased', value: 'Leased' }
            ]
        },
        { 
            field: 'vehicle_status', 
            header: 'Status', 
            sortable: true, 
            style: { width: '120px' },
            filterType: 'select',
            filterOptions: [
                { label: 'Available', value: 'Available' },
                { label: 'In Trip', value: 'In Trip' },
                { label: 'Maintenance', value: 'Maintenance' },
                { label: 'Breakdown', value: 'Breakdown' }
            ]
        },
        { field: 'fuel_level', header: 'Fuel Level (%)', sortable: true, dataType: 'numeric', style: { width: '120px' } },
        { field: 'current_odometer', header: 'Odometer', sortable: true, dataType: 'numeric', style: { width: '120px' } },
        { field: 'engine_hours', header: 'Engine Hours', sortable: true, dataType: 'numeric', style: { width: '120px' } },
        { field: 'capacity_weight', header: 'Cap (Weight)', sortable: true, dataType: 'numeric', style: { width: '120px' } },
        { field: 'capacity_volume', header: 'Cap (Vol)', sortable: true, dataType: 'numeric', style: { width: '120px' } },
        { field: 'is_active', header: 'Active', sortable: true, dataType: 'boolean', style: { width: '100px' } },
        { field: 'data_source', header: 'Data Source', sortable: true, style: { width: '120px' } }
    ];

    const config = uiScreenService.getScreenConfig('TMS Vehicle Master');
    
    if (config?.grid_fields?.length > 0) {
        // Merge configuration with base schema
        columns.value = baseSchema.map((base: any) => {
            const cfg = config.grid_fields.find((f: any) => f.field_name === base.field);
            if (cfg) {
                return {
                    ...base,
                    header: cfg.field_label || base.header,
                    style: { ...base.style, width: cfg.column_width || base.style.width },
                    hidden: !cfg.is_visible,
                    display_order: cfg.display_order || 99
                };
            }
            // If not in config specifically, hide it from grid but keep for filter
            return { ...base, hidden: true, display_order: 100 };
        }).sort((a: any, b: any) => a.display_order - b.display_order);

        if (config.grid_page_size) gridPageSize.value = config.grid_page_size;
    } else {
        // Fallback or No Config: Everything in baseSchema is available, but we can default some to hidden
        columns.value = baseSchema.map((col) => ({
            ...col,
            // Default visibility if no config: 
            hidden: !['vehicle_number', 'vehicle_type', 'organization', 'branch', 'vehicle_status', 'is_active', 'data_source'].includes(col.field)
        }));
    }
};

const loadData = async () => {
    isLoading.value = true;
    try {
        const fields = columns.value.map(c => c.field);
        if (!fields.includes('name')) fields.push('name');
        if (!fields.includes('data_source')) fields.push('data_source');

        const data = await masterDataService.getResourceList('TMS Vehicle Master', fields);
        
        // Map legacy "FRAPPE" data source to "FLEETA" for display consistency
        items.value = data.map((v: any) => ({
            ...v,
            data_source: v.data_source === 'FRAPPE' ? 'FLEETA' : (v.data_source || 'FLEETA')
        }));
    } catch (error) {
        console.error('Failed to load vehicles:', error);
    } finally {
        isLoading.value = false;
    }
};

const commonTableRef = ref<any>(null);

const onAddNew = () => {
    commonTableRef.value?.openNewTab('New Vehicle');
};

const onRowClick = (event: any) => {
    const displayName = event.data.vehicle_number || event.data.name;
    commonTableRef.value?.openTab(event.data, displayName);
};

const activateListTab = () => {
    commonTableRef.value?.activateListTab();
};

const closeTab = (id: string) => {
    commonTableRef.value?.closeTab(id);
};

defineExpose({ activateListTab, closeTab, loadData });

onMounted(async () => {
    await uiScreenService.fetchConfigsIfNeeded();
    await fetchFilterOptions();
    applyScreenConfig();
    await loadData();
});
</script>

<template>
    <div class="vehicle-list-container flex flex-col h-full bg-surface-50 dark:bg-surface-950 p-1 font-poppins">
        <CommonTable 
            ref="commonTableRef"
            :data="items" 
            :columns="columns" 
            title="Vehicle Master"
            :rows="gridPageSize"
            :loading="isLoading"
            dataKey="name"
            show-add-action
            @add-new="onAddNew"
            @row-click="onRowClick"
        >
            <template #form="slotProps">
                <slot name="form" v-bind="slotProps"></slot>
            </template>
        </CommonTable>
    </div>
</template>

<style scoped>
.vehicle-list-container {
    height: 100%;
    width: 100%;
}
</style>