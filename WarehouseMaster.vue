<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useToastMessage } from '@/composables/useToastMessage';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import WarehouseList from './WarehouseList.vue';
import WarehouseForm from './WarehouseForm.vue';

const { showSuccess, showError } = useToastMessage();
const isLoading = ref(false);
const warehouseListRef = ref();

// Dropdown Lists
const warehouseTypes = ref<any[]>([]);
const areaTypes = ref<any[]>([]);
const branchList = ref<any[]>([]);
const organizationList = ref<any[]>([]);
const clientOrganizationList = ref<any[]>([]);
const transporterOrganizationList = ref<any[]>([]);
const dockOrganizationList = ref<any[]>([]);
const locationList = ref<any[]>([]);

onMounted(async () => {
    try {
        isLoading.value = true;
        
        const safePromise = <T>(p: Promise<T>, fallback: T): Promise<T> => p.catch(e => {
            console.error('Dropdown load failed:', e);
            return fallback;
        });

        const [wTypes, aTypes, branches, orgs, clientOrgs, transporterOrgs, dockOrgs, locs] = await Promise.all([
            safePromise(masterDataService.getWarehouseTypes(), []),
            safePromise(masterDataService.getAreaTypes(), []),
            safePromise(masterDataService.getBranches(), []),
            safePromise(masterDataService.getWarehouseProviderOrganizations(), []),
            safePromise(masterDataService.getClientOrganizations(), []),
            safePromise(masterDataService.getTransporterOrganizations(), []),
            safePromise(masterDataService.getDockOrganizations(), []),
            safePromise(masterDataService.getLocations(), [])
        ]);

        warehouseTypes.value = wTypes.map(t => ({ label: t.type_value, value: t.name })); 
        areaTypes.value = aTypes.map(t => ({ label: t.type_value, value: t.name }));
        branchList.value = branches.map(b => ({ 
            label: `${b.code} - ${b.branch_name}`, 
            value: b.code, 
            ...b 
        }));
        organizationList.value = orgs.map(o => ({ 
            label: `${o.code} - ${o.full_name}`, 
            value: o.name, 
            ...o 
        }));
        clientOrganizationList.value = clientOrgs.map(o => ({
            label: `${o.code} - ${o.full_name}`,
            value: o.name,
            ...o
        }));
        transporterOrganizationList.value = transporterOrgs.map(o => ({
             label: `${o.code} - ${o.full_name}`,
             value: o.name,
             ...o
        }));
        dockOrganizationList.value = dockOrgs.map(o => ({
             label: `${o.code} - ${o.full_name}`,
             value: o.name,
             ...o
        }));
        locationList.value = locs.map(l => ({
            label: l.location_code,
            value: l.location_code, 
            ...l
        }));


    } catch (error) {
        console.error('Error loading data:', error);
        showError('Error', 'Failed to load master data');
    } finally {
        isLoading.value = false;
    }
});

const onRecordSaved = () => {
    warehouseListRef.value?.loadWarehouses();
};

const onRecordClosed = (tabId: string) => {
    warehouseListRef.value?.closeTab(tabId);
};
</script>

<template>
    <div class="warehouse-master-container flex flex-col h-full bg-surface-50 dark:bg-surface-950">
        <WarehouseList ref="warehouseListRef">
            <template #form="{ data, id }">
                <WarehouseForm
                    :initial-data="data"
                    :warehouse-types="warehouseTypes"
                    :area-types="areaTypes"
                    :branch-list="branchList"
                    :organization-list="organizationList"
                    :client-organization-list="clientOrganizationList"
                    :transporter-organization-list="transporterOrganizationList"
                    :dock-organization-list="dockOrganizationList"
                    :location-list="locationList"
                    @saved="onRecordSaved"
                    @close="onRecordClosed(id)"
                />
            </template>
        </WarehouseList>
    </div>
</template>
