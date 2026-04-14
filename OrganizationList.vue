<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { uiScreenService } from '@/core/api/uiScreen.service';
import Button from 'primevue/button';
import CommonTable from '@/components/CommonTable.vue';

const commonTableRef = ref();

const organizationList = ref<any[]>([]);
const selectedOrganizations = ref<any[]>([]);
const isLoading = ref(false);
const activeFilters = ref<any[]>([]);

const columns = ref<any[]>([]);
const gridPageSize = ref(10);

const applyScreenConfig = () => {
    const config = uiScreenService.getScreenConfig('Organization Master');
    if (config && config.grid_fields && config.grid_fields.length > 0) {
        console.log('[OrganizationList] Applying screen config:', config);
        
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
                dataType: f.field_name.startsWith('is_') ? 'boolean' : 'text'
            }));
        }
        
        if (config.grid_page_size) {
            gridPageSize.value = config.grid_page_size;
        }
    } else {
        // Fallback columns when no config is available
        columns.value = [
       
            { field: 'code', header: 'Code', sortable: true },
            { field: 'full_name', header: 'Full Name', sortable: true },
            { field: 'oad_related_port_code', header: 'Related Port', sortable: true, width: '150px' },
            { field: 'oad_city', header: 'City', sortable: true, width: '120px' },
            { field: 'oad_state', header: 'State', sortable: true, width: '120px' },
            { field: 'oad_country_code', header: 'Country', sortable: true, width: '120px' },
            { field: 'is_forwarder', header: 'Is Forwarder', sortable: true, dataType: 'boolean', width: '120px' },
            { field: 'is_consignee', header: 'Is Consignee', sortable: true, dataType: 'boolean', width: '120px' },
            { field: 'is_consignor', header: 'Is Consignor', sortable: true, dataType: 'boolean', width: '120px' },
            { field: 'is_transporter', header: 'Is Transporter', sortable: true, dataType: 'boolean', width: '120px' },
            { field: 'is_active', header: 'Is Active', sortable: true, dataType: 'boolean', width: '100px' }
        ];
    }
};


const emit = defineEmits(['createNew', 'editOrganization']);

const loadOrganizations = async () => {
    try {
        isLoading.value = true;
        
        // Get configured fields for API fetching
        const config = uiScreenService.getScreenConfig('Organization Master');
        let fields = ['*'];
        if (config && config.grid_fields && config.grid_fields.length > 0) {
            fields = config.grid_fields
                .filter((f: any) => f.is_visible)
                .map((f: any) => f.field_name);
        } else {
            // Use fallback field list
            fields = [
                'name', 'code', 'full_name', 'oad_related_port_code', 'oad_city', 'oad_state', 
                'oad_post_code', 'is_forwarder', 'is_consignee', 'is_consignor', 'is_transporter', 
                'is_warehouse_provider', 'is_transport_client', 'is_active', 'is_shipping_line', 
                'is_air_line', 'oad_country_code'
            ];
        }
        
        // Ensure name is always included
        if (!fields.includes('name')) fields.push('name');
        
        const data = await masterDataService.getOrganizationDetailsList(activeFilters.value, fields);
        console.log('[OrganizationList] Organizations loaded:', data);
        if (Array.isArray(data)) {
            organizationList.value = data.filter((org: any) => org.full_name || org.code);
        } else {
            organizationList.value = [];
        }
    } catch (error) {
        console.error('Error loading organizations:', error);
    } finally {
        isLoading.value = false;
    }
};

const onAdvancedFilter = (filters: Array<{ fieldname: string; value: any; operator: string; logical_operator: string }>) => {
    // Convert emitted filter objects to Frappe filter array format: [field, operator, value]
    activeFilters.value = filters.map((f) => {
        let value = f.value;
        if (f.operator === 'like' || f.operator === 'not like') {
            value = `%${value}%`;
        }
        return ['MDM Org Header', f.fieldname, f.operator, value];
    });
    loadOrganizations();
};

const onClearFilter = () => {
    activeFilters.value = [];
    loadOrganizations();
};

const onAddNew = () => {
    commonTableRef.value?.openNewTab('New Organization');
};

const onRowSelect = (event: any) => {
    commonTableRef.value?.openTab(event.data);
};

defineExpose({
    loadOrganizations,
    closeTab: (id: string) => commonTableRef.value?.closeTab(id)
});

onMounted(() => {
    applyScreenConfig();
    loadOrganizations();
});
</script>

<template>
    <div class="organization-list-container flex flex-col h-full bg-surface-50 dark:bg-surface-950 p-1 font-poppins">
        <CommonTable 
            ref="commonTableRef"
            :data="organizationList" 
            :columns="columns" 
            title="Organization Master"
            :rows="gridPageSize"
            :loading="isLoading"
            dataKey="name"
            v-model:selection="selectedOrganizations"
            :show-add-action="true"
            @add-new="onAddNew"
            @row-click="onRowSelect"
            @refresh="loadOrganizations"
             filter-doctype="MDM Org Header"
            @apply-advanced-filter="onAdvancedFilter"
            @clear-filter="onClearFilter"
        >
            <template #title-actions>
            </template>

            <!-- Custom Slot for Code column (now titled "Full Name") -->
            

            <template #form="{ data, id }">
                <slot name="form" :data="data" :id="id"></slot>
            </template>
        </CommonTable>
    </div>
</template>
