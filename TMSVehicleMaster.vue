<script setup lang="ts">
import { ref } from 'vue';
import TMSVehicleList from './TMSVehicleList.vue';
import TMSVehicleForm from './TMSVehicleForm.vue';
import CommonToast from '@/components/CommonToast.vue';

const vehicleListRef = ref<any>(null);

const onVehicleSaved = () => {
    vehicleListRef.value?.loadData();
};

const onVehicleClosed = (id: string) => {
    vehicleListRef.value?.closeTab(id);
};
</script>

<template>
    <div class="vehicle-master-container flex flex-col h-full bg-surface-50 dark:bg-surface-950">
        <TMSVehicleList ref="vehicleListRef">
            <template #form="{ data, id }">
                <TMSVehicleForm 
                    :initialData="data" 
                    @saved="onVehicleSaved" 
                    @close="onVehicleClosed(id)" 
                />
            </template>
        </TMSVehicleList>
        <CommonToast />
    </div>
</template>

<style scoped>
.vehicle-master-wrapper {
    height: calc(100vh - 4.5rem); 
}
</style>
