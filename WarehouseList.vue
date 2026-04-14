<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { uiScreenService } from '@/core/api/uiScreen.service';
import CommonTable from '@/components/CommonTable.vue';
import CommonButton from '@/components/CommonButton.vue';

const commonTableRef = ref();
const route = useRoute();


const warehouseList = ref<any[]>([]);
const selectedWarehouses = ref<any[]>([]);
const isLoading = ref(false);
const activeFilters = ref<any[]>([]);

const columns = ref<any[]>([]);
const gridPageSize = ref(10);

const applyScreenConfig = () => {
    const config = uiScreenService.getScreenConfig('WMS Warehouse');
    if (config && config.grid_fields && config.grid_fields.length > 0) {
        console.log('[WarehouseList] Applying screen config:', config);
        
        // Filter and sort columns based on configuration
        const visibleFields = config.grid_fields
            .filter((f: any) => f.is_visible)
            .sort((a: any, b: any) => (a.display_order || 0) - (b.display_order || 0));

        if (visibleFields.length > 0) {
            columns.value = visibleFields.map((f: any) => ({
                field: f.field_name,
                header: f.field_label || f.field_name,
                sortable: true,
                width: f.column_width,
                dataType: (f.field_name === 'is_active' || f.field_name === 'is_bonded_warehouse') ? 'boolean' : 'text'
            }));
        }
        
        if (config.grid_page_size) {
            gridPageSize.value = config.grid_page_size;
        }
    } else {
        // Fallback columns when no config is available
        columns.value = [
            { field: 'warehouse_code', header: 'Code', sortable: true },
            { field: 'warehouse_name', header: 'Warehouse Name', sortable: true },
            { field: 'warehouse_type', header: 'Type', sortable: true },
            { field: 'branch_name', header: 'Branch', sortable: true },
            { field: 'organization_name', header: 'Organization', sortable: true },
            { field: 'country_code', header: 'Country', sortable: true },
            { field: 'is_active', header: 'IsActive', sortable: true, dataType: 'boolean' }
        ];
    }
};


const emit = defineEmits(['createNew', 'editWarehouse']);

const loadWarehouses = async () => {
    try {
        isLoading.value = true;
        
        // Get configured fields for API fetching
        const config = uiScreenService.getScreenConfig('WMS Warehouse');
        let fields = ['*'];
        if (config && config.grid_fields && config.grid_fields.length > 0) {
            fields = config.grid_fields
                .filter((f: any) => f.is_visible)
                .map((f: any) => f.field_name);
            
            // Ensure mandatory fields or ID is included if needed for row selection
            if (!fields.includes('name')) fields.push('name');
        }
        const data = await masterDataService.getWarehouses(activeFilters.value, fields);
        console.log('[WarehouseList] Warehouses loaded with fields:', fields, data);
        warehouseList.value = data;

        // Check for deep link after data is loaded
        await handleDeepLink();
    } catch (error) {
        console.error('Error loading warehouses:', error);
    } finally {
        isLoading.value = false;
    }
};

const handleDeepLink = async () => {
    const id = route.query.id as string;
    if (id && warehouseList.value.length > 0) {
        console.log('[WarehouseList] Deep link detected for id:', id);
        // Find the record by name (ID) or warehouse_code
        const record = warehouseList.value.find(w => w.name === id || w.warehouse_code === id);
        if (record) {
            commonTableRef.value?.openTab(record, record.warehouse_name || record.warehouse_code);
        } else {
            // If not found in current list, try fetching it directly
            try {
                const doc = await masterDataService.getWarehouse(id);
                if (doc) {
                    commonTableRef.value?.openTab(doc, doc.warehouse_name || doc.warehouse_code);
                }
            } catch (e) {
                console.warn('[WarehouseList] Failed to fetch deep linked record:', e);
            }
        }
    }
};

watch(() => route.query.id, (newId) => {
    if (newId) handleDeepLink();
});

const onAdvancedFilter = (filters: Array<{ fieldname: string; value: any; operator: string; logical_operator: string }>) => {
    activeFilters.value = filters.map((f) => {
        let value = f.value;
        if (f.operator === 'like' || f.operator === 'not like') value = `%${value}%`;
        return ['WMS Warehouse', f.fieldname, f.operator, value];
    });
    loadWarehouses();
};

const onClearFilter = () => {
    activeFilters.value = [];
    loadWarehouses();
};

const onAddNew = () => {
    commonTableRef.value?.openNewTab('New Warehouse');
};

const onRowSelect = (event: any) => {
    commonTableRef.value?.openTab(event.data, event.data.warehouse_name || event.data.warehouse_code);
};

defineExpose({
    loadWarehouses,
    closeTab: (id: string) => commonTableRef.value?.closeTab(id)
});

onMounted(() => {
    applyScreenConfig();
    loadWarehouses();
});
</script>

<template>
    <div class="warehouse-list-container flex flex-col h-full bg-surface-50 dark:bg-surface-950 p-1 font-poppins">
        <CommonTable 
            ref="commonTableRef"
            :data="warehouseList" 
            :columns="columns" 
            title="WAREHOUSE MASTER"
            :rows="gridPageSize"
            :loading="isLoading"
            dataKey="name"
            v-model:selection="selectedWarehouses"
            show-add-action
            filter-doctype="WMS Warehouse"
            @add-new="onAddNew"
            @row-click="onRowSelect"
            @refresh="loadWarehouses"
            @apply-advanced-filter="onAdvancedFilter"
            @clear-filter="onClearFilter"
        >

            <template #form="{ data, id }">
                <slot name="form" :data="data" :id="id"></slot>
            </template>
        </CommonTable>
    </div>
</template>


