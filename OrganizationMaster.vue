<script setup lang="ts">
import { ref } from 'vue';
import OrganizationList from './OrganizationList.vue';
import OrganizationForm from './OrganizationForm.vue';

const organizationListRef = ref();

const onRecordSaved = () => {
    organizationListRef.value?.loadOrganizations();
};

const onRecordClosed = (id: string) => {
    organizationListRef.value?.closeTab(id);
};
</script>

<template>
    <div class="organization-master-wrapper h-full">
        <OrganizationList ref="organizationListRef">
            <template #form="{ data, id }">
                <OrganizationForm 
                    :initial-data="data" 
                    @saved="onRecordSaved" 
                    @close="onRecordClosed(id)" 
                />
            </template>
        </OrganizationList>
    </div>
</template>

<style scoped>
.organization-master-wrapper {
    overflow: hidden;
}
</style>
