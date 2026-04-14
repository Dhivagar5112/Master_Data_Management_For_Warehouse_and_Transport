<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import Fluid from 'primevue/fluid';
import Toast from 'primevue/toast';
import CommonHeading from '@/components/CommonHeading.vue';
import CommonField from '@/components/CommonField.vue';
import FormFooter from '@/components/FormFooter.vue';
import CommonCommentModal from '@/components/CommonCommentModal.vue';
import CommonDocumentModal from '@/components/CommonDocumentModal.vue';
import CommonEmailModal from '@/components/CommonEmailModal.vue';
import CommonExceptionModal from '@/components/CommonExceptionModal.vue';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { commentService } from '@/core/api/comment.service';
import { documentService } from '@/core/api/document.service';
import { usePermissions } from '@/composables/usePermissions';

const props = defineProps({
    countryName: { type: String, default: undefined }
});

const emit = defineEmits(['saved', 'close']);
const toast = useToast();
const { canWrite } = usePermissions('MDM Country');

const savedCountryName = ref(props.countryName);
const isLoading = ref(false);
const commentCount = ref(0);
const documentCount = ref(0);

const showCommentModal = ref(false);
const showDocumentModal = ref(false);
const showEmailModal = ref(false);
const showExceptionModal = ref(false);

const form = ref<any>({
    name: '',
    code: '',
    description: '',
    is_active: 1
});

const syncFromBackend = (doc: any) => {
    Object.assign(form.value, doc);
    form.value.is_active = !!(form.value.is_active === 1 || form.value.is_active === true);
};

const loadCountry = async () => {
    if (!savedCountryName.value) return;
    try {
        isLoading.value = true;
        const doc = await masterDataService.getResource('MDM Country', savedCountryName.value);
        if (doc) {
            syncFromBackend(doc);
        }
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load country details', life: 3000 });
    } finally {
        isLoading.value = false;
    }
};

const fetchCounts = async () => {
    if (!savedCountryName.value) return;
    try {
        const [cCount, dCount] = await Promise.all([
            commentService.getCommentCount('MDM Country', savedCountryName.value),
            documentService.getDocumentCount('MDM Country', savedCountryName.value)
        ]);
        commentCount.value = cCount;
        documentCount.value = dCount;
    } catch (e) {
        console.error('Error fetching counts:', e);
    }
};

const onSave = async () => {
    if (!form.value.code || !form.value.description) {
        toast.add({ severity: 'error', summary: 'Validation Error', detail: 'Country Code and Name are required', life: 3000 });
        return false;
    }

    try {
        isLoading.value = true;
        const payload = { ...form.value };
        payload.is_active = payload.is_active ? 1 : 0;
        
        let result: any;
        if (savedCountryName.value) {
            result = await masterDataService.updateResource('MDM Country', savedCountryName.value, payload);
            toast.add({ severity: 'success', summary: 'Success', detail: 'Country updated', life: 3000 });
        } else {
            result = await masterDataService.createResource('MDM Country', payload);
            toast.add({ severity: 'success', summary: 'Success', detail: 'Country created', life: 3000 });
        }
        
        if (result && result.name) {
            savedCountryName.value = result.name;
            syncFromBackend(result);
            await fetchCounts();
        }
        
        emit('saved', form.value);
        return true;
    } catch (error: any) {
        if (error.response?.status === 409 || error.response?.status === 417) {
            toast.add({ severity: 'error', summary: 'Version Conflict', detail: 'This record has been modified by another user. Please reload and try again.', life: 5000 });
        } else {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message || 'Save failed', life: 3000 });
        }
        return false;
    } finally {
        isLoading.value = false;
    }
};

const onSaveAndClose = async () => {
    const success = await onSave();
    if (success) {
        emit('close');
    }
};

const handleActionClick = (id: string) => {
    if (id === 'comment') showCommentModal.value = true;
    else if (id === 'document') showDocumentModal.value = true;
    else if (id === 'email') showEmailModal.value = true;
    else if (id === 'exception') showExceptionModal.value = true;
};

const footerLeftActions = computed(() => [
    { id: 'comment', label: 'Comment', icon: 'pi pi-comments', count: commentCount.value },
    { id: 'document', label: 'Document', icon: 'pi pi-copy', count: documentCount.value },
    { id: 'email', label: 'Email', icon: 'pi pi-envelope' },
    { id: 'exception', label: 'Exception', icon: 'pi pi-exclamation-triangle' },
]);

const footerActions = computed(() => [
    { 
        label: 'Documents', 
        severity: 'secondary' as const,
        outlined: true,
        items: [
            { label: 'View All', icon: 'pi pi-eye', command: () => { showDocumentModal.value = true; } },
            { label: 'Upload New', icon: 'pi pi-upload', command: () => { showDocumentModal.value = true; } }
        ] 
    },
    { 
        label: 'More', 
        severity: 'secondary' as const,
        outlined: true,
        items: [
            { label: 'Print', icon: 'pi pi-print' },
            { label: 'Export PDF', icon: 'pi pi-file-pdf' },
            { label: 'Share', icon: 'pi pi-share-alt' }
        ] 
    },
    { label: 'Save & Close', severity: 'primary' as const, command: onSaveAndClose, disabled: !canWrite.value, loading: isLoading.value },
    { label: 'Save', severity: 'primary' as const, command: onSave, disabled: !canWrite.value, loading: isLoading.value, icon: 'pi pi-save' }
] as any[]);

onMounted(async () => {
    if (savedCountryName.value) {
        await loadCountry();
        await fetchCounts();
    }
});

defineExpose({ onSave, isLoading });
</script>

<template>
    <div class="country-form-container flex flex-col h-full bg-surface-50 dark:bg-surface-950 overflow-hidden font-poppins">
        <!-- Content Area -->
        <div class="flex-1 overflow-y-auto p-6">
            <Fluid>
                <div class="max-w-[1200px] mx-auto space-y-6">
                    <!-- Basic Info Section -->
                    <div class="card p-6 bg-surface-0 dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl shadow-sm space-y-4">
                        <CommonHeading text="Country Details" level="2" icon="pi pi-info-circle" />
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <CommonField label="Country Code" v-model="form.code" required placeholder="e.g. IN, US" />
                            <CommonField label="Country Name" v-model="form.description" required placeholder="e.g. India, United States" />
                            <CommonField type="checkbox-card" label="Is Active" v-model="form.is_active" />
                        </div>
                    </div>
                </div>
            </Fluid>
        </div>

        <FormFooter 
            :leftActions="footerLeftActions"
            :actions="footerActions"
            @action-click="handleActionClick"
        />

        <CommonCommentModal v-model:visible="showCommentModal" doctype="MDM Country" :docname="savedCountryName || ''" />
        <CommonDocumentModal v-model:visible="showDocumentModal" doctype="MDM Country" :docname="savedCountryName || ''" />
        <CommonEmailModal v-model:visible="showEmailModal" doctype="MDM Country" :docname="savedCountryName || ''" />
        <CommonExceptionModal v-model:visible="showExceptionModal" doctype="MDM Country" :docname="savedCountryName || ''" />
        <Toast />
    </div>
</template>

<style scoped>
.country-form-container {
    height: 100%;
}
</style>
