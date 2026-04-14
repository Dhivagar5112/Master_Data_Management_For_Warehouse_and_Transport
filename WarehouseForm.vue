<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useToastMessage } from '@/composables/useToastMessage';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { commentService } from '@/core/api/comment.service';
import Fluid from 'primevue/fluid';
import EditableGrid from '@/components/EditableGrid.vue';
import CommonHeading from '@/components/CommonHeading.vue';
import FormFooter from '@/components/FormFooter.vue';
import CommonCommentModal from '@/components/CommonCommentModal.vue';
import CommonDocumentModal from '@/components/CommonDocumentModal.vue';
import CommonEmailModal from '@/components/CommonEmailModal.vue';
import CommonExceptionModal from '@/components/CommonExceptionModal.vue';
import { usePermissions } from '@/composables/usePermissions';
import { documentService } from '@/core/api/document.service';
import { extractErrorMessage } from '@/core/utils/errorUtils';

const props = defineProps({
    initialData: { type: Object, default: () => ({}) },
    warehouseTypes: { type: Array, default: () => [] },
    areaTypes: { type: Array, default: () => [] },
    branchList: { type: Array, default: () => [] },
    organizationList: { type: Array, default: () => [] },
    clientOrganizationList: { type: Array, default: () => [] },
    transporterOrganizationList: { type: Array, default: () => [] },
    dockOrganizationList: { type: Array, default: () => [] },
    locationList: { type: Array, default: () => [] },
});

const emit = defineEmits(['saved', 'close']);

const { canWrite } = usePermissions('WMS Warehouse');
const { showSuccess, showError, showWarning } = useToastMessage();

const activeTab = ref('General');
const isLoading = ref(false);
const showCommentModal = ref(false);
const showDocumentModal = ref(false);
const showEmailModal = ref(false);
const showExceptionModal = ref(false);
const commentCount = ref(0);
const documentCount = ref(0);

const form = ref<any>({
    warehouse_code: '', 
    warehouse_name: '',
    warehouse_type: '',
    branch_code: '',
    branch_name: '',
    region: '',
    country_code: '',
    is_active: 1,
    is_bonded_warehouse: 0,
    organization: '',
    organization_address: '',
    organization_phone: '',
    valid_from: null,
    valid_to: null,
    // Config fields
    enable_gatepass: 0,
    is_gatepass_mandatory: 0,
    enable_damage_captured: 0,
    enable_direct_invoice: 0,
    enable_otp_configuration: 0,
    enable_inward_tracking: 0,
    enable_outward_tracking: 0,
    enable_package: 0,
    enable_docket_configuration: 0,
    enable_so_consolidation: 0,
    enable_double_scanning: 0,
    enable_auto_package_id: 0,
    manifest_creation_restriction: 0,
    manifest_accrual_restriction: 0,
    release_capture_bulkoption: 0,
    enable_shuttle_method: 0,
    default_putaway_location: '',
    areas: [],
    client_configs: [],
    vendor_configs: [],
    dock_configs: []
});

// Initialize form with defaults or initial data
const initializeForm = async () => {
    if (props.initialData && (props.initialData.name || props.initialData.id) && props.initialData.name !== 'new' && props.initialData.id !== 'new') {
        // Edit Mode
        const tabId = props.initialData.name || props.initialData.id;
        
        // Use passed data initially and convert dates immediately
        const initialForm = { ...form.value, ...props.initialData };
        if (initialForm.valid_from) initialForm.valid_from = new Date(initialForm.valid_from);
        if (initialForm.valid_to) initialForm.valid_to = new Date(initialForm.valid_to);
        form.value = initialForm;

        try {
            isLoading.value = true;
            const fullDoc = await masterDataService.getWarehouse(tabId);
            if (fullDoc) {
                 const doc = { ...fullDoc };
                 doc.is_active = !!doc.is_active;
                 doc.is_bonded_warehouse = !!doc.is_bonded_warehouse;
                 if (doc.valid_from) doc.valid_from = new Date(doc.valid_from);
                 if (doc.valid_to) doc.valid_to = new Date(doc.valid_to);
                 
                 // Ensure child tables exist
                 if (!doc.areas) doc.areas = [];
                 if (!doc.client_configs) doc.client_configs = [];
                 if (!doc.vendor_configs) doc.vendor_configs = [];
                 if (!doc.dock_configs) doc.dock_configs = [];

                 // Convert 0/1 to boolean for Checkboxes in Warehouse Config
                 const fieldsToConvert = [
                    'enable_gatepass', 'is_gatepass_mandatory', 'enable_damage_captured', 
                    'enable_direct_invoice', 'enable_otp_configuration', 'enable_inward_tracking',
                    'enable_outward_tracking', 'enable_package', 'enable_docket_configuration',
                    'enable_so_consolidation', 'enable_double_scanning', 'enable_auto_package_id',
                    'manifest_creation_restriction', 'manifest_accrual_restriction', 'release_capture_bulkoption',
                    'enable_shuttle_method'
                 ];
                 fieldsToConvert.forEach(field => {
                     doc[field] = !!doc[field];
                 });

                 // Update form value once at the end to minimize re-renders
                 form.value = { ...form.value, ...doc };

                 // Fetch counts
                 fetchCommentCount();
                 fetchDocumentCount();
            }
        } catch (error) {
            console.error('Error fetching full warehouse details', error);
        } finally {
            isLoading.value = false;
        }

    } else {
        // Create Mode - form.value is already default
    }
};

onMounted(() => {
    initializeForm();
});

// Watch for initialData changes if the component is reused (though in tabs it should be mounted once per tab)
watch(() => props.initialData, (newVal) => {
    if (newVal && (newVal.name || newVal.id)) {
        initializeForm();
    }
}, { deep: true });

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
            { label: 'View All', icon: 'pi pi-eye' },
            { label: 'Upload New', icon: 'pi pi-upload' }
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
    {
        label: 'Save & Close',
        severity: 'primary' as const,
        loading: isLoading.value,
        disabled: !canWrite.value,
        command: onSaveAndClose,
    },
    { 
        label: 'Save', 
        severity: 'primary' as const,
        icon: 'pi pi-save', 
        loading: isLoading.value, 
        disabled: !canWrite.value, 
        command: onSave,
    }
] as any[]);

const menuItems = [
    { label: 'General', icon: 'pi pi-id-card' },
    { label: 'Area', icon: 'pi pi-map' },
    { label: 'Warehouse Config', icon: 'pi pi-cog' },
    { label: 'Client Config', icon: 'pi pi-users' },
    { label: 'Vendor Config', icon: 'pi pi-briefcase' },
    { label: 'Dock Config', icon: 'pi pi-sign-in' }
];

const onBranchChange = (event?: any) => {
    // If event is passed from CommonField, it might contain the value directly
    const branchCode = event?.value || form.value.branch_code;
    const selectedBranch = props.branchList.find((b: any) => b.value === branchCode) as any;
    
    if (selectedBranch) {
        form.value.branch_name = selectedBranch.branch_name;
        form.value.region = selectedBranch.region;
        form.value.country_code = selectedBranch.country;
    } else {
        form.value.branch_name = '';
        form.value.region = '';
        form.value.country_code = '';
    }
};

const minToDate = computed(() => {
    if (!form.value.valid_from) return null;
    const d = new Date(form.value.valid_from);
    d.setDate(d.getDate() + 1);
    return d;
});

const onOrganizationChange = async (event?: any) => {
    const orgValue = event?.value || form.value.organization;
    if (!orgValue) {
        form.value.organization_address = '';
        form.value.organization_phone = '';
        return;
    }
    
    try {
        isLoading.value = true;
        const orgDetails = await masterDataService.getOrganizationDetails(orgValue);
        
        if (orgDetails) {
            form.value.organization_address = orgDetails.organization_address || '';
            form.value.organization_phone = orgDetails.organization_phone || '';
        }
    } catch (error) {
        console.error('Error fetching org details:', error);
        showError('Error', 'Failed to load organization details');
    } finally {
        isLoading.value = false;
    }
};

const validateForm = () => {
    const requiredFields = [
        { field: 'warehouse_code', label: 'Warehouse Code' },
        { field: 'warehouse_name', label: 'Warehouse Name' },
        { field: 'warehouse_type', label: 'Warehouse Type' },
        { field: 'branch_code', label: 'Branch Code' },
        { field: 'organization', label: 'Organization' },
        { field: 'valid_from', label: 'From Date' },
        { field: 'valid_to', label: 'To Date' }
    ];

    for (const f of requiredFields) {
        if (!form.value[f.field]) {
            showWarning('Validation Error', `${f.label} is required`);
            return false;
        }
    }

    // Child Table Validations
    if (form.value.areas) {
        for (let i = 0; i < form.value.areas.length; i++) {
            const area = form.value.areas[i];
            if (!area.area_name || !area.area_type) {
                showWarning('Area Tab Error', `Area Name and Type are required in row ${i + 1}`);
                return false;
            }
        }
    }

    if (form.value.client_configs) {
        for (let i = 0; i < form.value.client_configs.length; i++) {
            const config = form.value.client_configs[i];
            if (!config.organization_code) {
                showWarning('Client Config Error', `Organization Code is required in row ${i + 1}`);
                return false;
            }
        }
    }

    if (form.value.vendor_configs) {
        for (let i = 0; i < form.value.vendor_configs.length; i++) {
            const config = form.value.vendor_configs[i];
            if (!config.organization_code) {
                showWarning('Vendor Config Error', `Organization Code is required in row ${i + 1}`);
                return false;
            }
        }
    }

    if (form.value.dock_configs) {
        for (let i = 0; i < form.value.dock_configs.length; i++) {
            const config = form.value.dock_configs[i];
            if (!config.dock_name || !config.organization_code) {
                showWarning('Dock Config Error', `Dock Name and Organization Code are required in row ${i + 1}`);
                return false;
            }
        }
    }

    if (form.value.valid_from && form.value.valid_to) {
        const from = new Date(form.value.valid_from);
        const to = new Date(form.value.valid_to);
        if (to <= from) {
            showWarning('Validation Error', 'To Date must be after From Date');
            return false;
        }
    }

    return true;
};

const formatDateForAPI = (date: Date | string | null): string | null => {
    if (!date) return null;
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

const onSave = async () => {
    if (!canWrite.value) {
        showError('Permission Denied', 'You do not have write permission for this DocType');
        return false;
    }
    
    if (!validateForm()) return false;

    try {
        isLoading.value = true;
        
        // Prepare payload with formatted dates
        const payload = { ...form.value };
        if (payload.valid_from) payload.valid_from = formatDateForAPI(payload.valid_from);
        if (payload.valid_to) payload.valid_to = formatDateForAPI(payload.valid_to);

        // Convert booleans back to 0/1 for API
        const fieldsToConvert = [
            'is_active', 'is_bonded_warehouse',
            'enable_gatepass', 'is_gatepass_mandatory', 'enable_damage_captured', 
            'enable_direct_invoice', 'enable_otp_configuration', 'enable_inward_tracking',
            'enable_outward_tracking', 'enable_package', 'enable_docket_configuration',
            'enable_so_consolidation', 'enable_double_scanning', 'enable_auto_package_id',
            'manifest_creation_restriction', 'manifest_accrual_restriction', 'release_capture_bulkoption',
            'enable_shuttle_method'
        ];
        fieldsToConvert.forEach(field => {
            payload[field] = payload[field] ? 1 : 0;
        });

        let result: any = null;
        if (form.value.name && form.value.name !== 'new') {
            result = await masterDataService.updateWarehouse(form.value.name, payload);
            showSuccess('Successful', 'Warehouse Updated Successfully');
        } else {
            result = await masterDataService.createWarehouse(payload);
            showSuccess('Successful', 'Warehouse Created Successfully');
        }

        if (result) {
            syncFromBackend(result);
        }
        emit('saved', form.value);
        return true;
    } catch (error: any) {
        console.error('Save error:', error);
        const msg = extractErrorMessage(error);
        if (msg.toLowerCase().includes('modified by another user') || error.response?.status === 409) {
            showError('Version Conflict', 'This record has been modified by another user. Please reload and try again.');
        } else {
             showError('Error', msg);
        }
        return false;
    } finally {
        isLoading.value = false;
    }
};

const syncFromBackend = (doc: any) => {
    Object.assign(form.value, doc);
    
    // Restore booleans for checkboxes
    form.value.is_active = !!form.value.is_active;
    form.value.is_bonded_warehouse = !!form.value.is_bonded_warehouse;
    
    // Convert 0/1 to boolean for Warehouse Config
    const configFields = [
        'enable_gatepass', 'is_gatepass_mandatory', 'enable_damage_captured', 
        'enable_direct_invoice', 'enable_otp_configuration', 'enable_inward_tracking',
        'enable_outward_tracking', 'enable_package', 'enable_docket_configuration',
        'enable_so_consolidation', 'enable_double_scanning', 'enable_auto_package_id',
        'manifest_creation_restriction', 'manifest_accrual_restriction', 'release_capture_bulkoption',
        'enable_shuttle_method'
    ];
    configFields.forEach(field => {
        form.value[field] = !!form.value[field];
    });

    // Restore date objects
    if (form.value.valid_from) form.value.valid_from = new Date(form.value.valid_from);
    if (form.value.valid_to) form.value.valid_to = new Date(form.value.valid_to);
};

const onSaveAndClose = async () => {
    const success = await onSave();
    if (success) {
        emit('close');
    }
};

const onClientConfigOrgChange = (row: any) => {
    const org = props.clientOrganizationList.find((o: any) => o.value === row.organization_code) as any;
    if (org) {
        row.organization_name = org.full_name;
    } else {
        row.organization_name = '';
    }
};

const onVendorConfigOrgChange = (row: any) => {
    const org = props.transporterOrganizationList.find((o: any) => o.value === row.organization_code) as any;
    if (org) {
        row.organization_name = org.full_name;
    } else {
        row.organization_name = '';
    }
};

const onDockConfigOrgChange = (row: any) => {
    const org = props.dockOrganizationList.find((o: any) => o.value === row.organization_code) as any;
    if (org) {
        row.organization_name = org.full_name;
    } else {
        row.organization_name = '';
    }
};

const handleActionClick = (actionId: string) => {
    if (actionId === 'comment') showCommentModal.value = true;
    else if (actionId === 'document') showDocumentModal.value = true;
    else if (actionId === 'email') showEmailModal.value = true;
    else if (actionId === 'exception') showExceptionModal.value = true;
};

const fetchDocumentCount = async () => {
    if (form.value.name) {
        try {
            documentCount.value = await documentService.getDocumentCount('WMS Warehouse', form.value.name);
        } catch (error) {
            console.error('Error fetching document count:', error);
        }
    } else {
        documentCount.value = 0;
    }
};

const fetchCommentCount = async () => {
    if (form.value.name) {
        try {
            commentCount.value = await commentService.getCommentCount('WMS Warehouse', form.value.name);
        } catch (error) {
            console.error('Error fetching comment count:', error);
        }
    } else {
        commentCount.value = 0;
    }
};

watch(showDocumentModal, (newVal) => { if (!newVal) fetchDocumentCount(); });
watch(showCommentModal, (newVal) => { if (!newVal) fetchCommentCount(); });

// Editable Grid Configs
const areaColumns = computed(() => [
    { field: 'idx', header: 'S.No', readonly: true, width: '2rem' },
    { field: 'area_name', header: 'Area Name', required: true },
    { field: 'area_type', header: 'Area Type', type: 'select' as const, options: props.areaTypes, placeholder: 'Select Type', required: true }
]);

const clientConfigColumns = computed(() => [
    { field: 'idx', header: 'S.No', readonly: true, width: '4rem' },
    { field: 'organization_code', header: 'Organization Code', type: 'select' as const, options: props.clientOrganizationList, placeholder: 'Search...', onChange: (row: any) => onClientConfigOrgChange(row), required: true },
    { field: 'organization_name', header: 'Organization Name', readonly: true },
    { field: 'sku_scan_quantity', header: 'SKU Scan Qty', type: 'number' as const },
    { field: 'is_edi_client', header: 'Is EDI', type: 'checkbox' as const }
]);

const vendorConfigColumns = computed(() => [
    { field: 'idx', header: 'S.No', readonly: true, width: '4rem' },
    { field: 'organization_code', header: 'Organization Code', type: 'select' as const, options: props.transporterOrganizationList, placeholder: 'Select Org', onChange: (row: any) => onVendorConfigOrgChange(row), required: true },
    { field: 'organization_name', header: 'Organization Name', readonly: true }
]);

const dockOrderOptions = Array.from({ length: 100 }, (_, i) => ({ label: String(i + 1), value: String(i + 1) }));
const dockPurposeOptions = [
    { label: 'ALL-All', value: 'ALL-All' },
    { label: 'LOD-Load', value: 'LOD-Load' },
    { label: 'ULD-Unload', value: 'ULD-Unload' }
];

const dockConfigColumns = computed(() => [
    { field: 'idx', header: 'S.No', readonly: true, width: '4rem' },
    { field: 'dock_name', header: 'Dock Name', required: true },
    { field: 'dock_order', header: 'Dock Order', type: 'select' as const, options: dockOrderOptions },
    { field: 'purpose', header: 'Purpose', type: 'select' as const, options: dockPurposeOptions },
    { field: 'organization_code', header: 'Organization Code', type: 'select' as const, options: props.dockOrganizationList, placeholder: 'Select Org', onChange: (row: any) => onDockConfigOrgChange(row), required: true },
    { field: 'organization_name', header: 'Organization Name', readonly: true }
]);

</script>

<template>
    <div class="flex flex-col h-full bg-surface-50 dark:bg-surface-950 overflow-hidden font-poppins">
        <!-- Horizontal Tabs -->
        <div class="px-1 bg-surface-0 dark:bg-surface-900">
             <CommonTabs :items="menuItems" v-model="activeTab" />
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-2 md:p-2 bg-surface-50 dark:bg-surface-950">
            <div v-if="activeTab === 'General'" key="general" class="card p-2 md:p-6 space-y-4 border border-primary bg-white dark:bg-surface-900 rounded-xl shadow-sm w-full">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <CommonField label="Warehouse Code" v-model="form.warehouse_code" id="w_code" required />
                        <CommonField label="Warehouse Name" v-model="form.warehouse_name" id="w_name" required />
                        <CommonField type="select" label="Warehouse Type" v-model="form.warehouse_type" id="w_type" :options="props.warehouseTypes" placeholder="Select Warehouse Type" required/>
                        <CommonField type="select" label="Branch Code" v-model="form.branch_code" id="b_code" :options="props.branchList" placeholder="Select Branch" @change="onBranchChange" required/>
                        <CommonField label="Branch Name" v-model="form.branch_name" id="b_name" readonly />
                        <CommonField label="Region" v-model="form.region" id="region" readonly />
                        <CommonField label="Country Code" v-model="form.country_code" id="country" readonly />
                    </div>

                    <!-- Organization Section -->
                    <div class="space-y-4 pt-4">
                        <CommonHeading text="Organization" level="2" icon="pi-user" />
                        <div class="card p-6 border border-surface-200 dark:border-surface-700 bg-surface-0 dark:bg-surface-900 rounded-lg">
                            <div class="grid grid-cols-1 md:grid-cols-1 gap-6 max-w-lg">
                                <CommonField type="select" v-model="form.organization" :options="props.organizationList" placeholder="Search Organization..." @change="onOrganizationChange" required/>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-surface-600 dark:text-surface-400 mt-2">
                                    <div class="text-md italic">
                                        {{ form.organization_address }}
                                    </div>
                                    <div class="flex md:justify-end items-center gap-2 text-md font-semibold">
                                        <i class="pi pi-phone"></i>
                                        <span>{{ form.organization_phone }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Agreement Date Section -->
                    <div class="space-y-4 pt-4">
                        <CommonHeading text="Agreement Date" level="2" icon="pi-calendar" />
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <CommonField type="date" label="From" v-model="form.valid_from" required/>
                            <CommonField type="date" label="To" v-model="form.valid_to" required :minDate="minToDate" />
                        </div>
                    </div>
                    
                    <div class="flex flex-col md:flex-row gap-8 mt-6 px-1">
                        <CommonField type="checkbox" label="Is Active" v-model="form.is_active" id="is_active" />
                        <CommonField type="checkbox" label="Is Bonded Warehouse" v-model="form.is_bonded_warehouse" id="is_bonded" />
                    </div>
                </div>

                <div v-else-if="activeTab === 'Warehouse Config'" key="config" class="card p-8 bg-white dark:bg-surface-900 rounded-xl shadow-sm border border-surface-200 w-full">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="space-y-4">
                            <CommonField type="checkbox-card" label="Enable Gatepass" v-model="form.enable_gatepass" id="c_gatepass" />
                            <CommonField type="checkbox-card" label="Enable Damage Captured" v-model="form.enable_damage_captured" id="c_damage" />
                            <CommonField type="checkbox-card" label="Enable OTP Configuration" v-model="form.enable_otp_configuration" id="c_otp" />
                            <CommonField type="checkbox-card" label="Enable Outward Tracking" v-model="form.enable_outward_tracking" id="c_outward" />
                            <CommonField type="checkbox-card" label="Enable Docket Configuration" v-model="form.enable_docket_configuration" id="c_docket" />
                            <CommonField type="checkbox-card" label="Enable Double Scanning for Warehouse" v-model="form.enable_double_scanning" id="c_double_scan" />
                            <CommonField type="checkbox-card" label="Manifest Creation Restriction for Warehouse" v-model="form.manifest_creation_restriction" id="c_manifest_create" />
                            <CommonField type="checkbox-card" label="Release Capture Bulkoption" v-model="form.release_capture_bulkoption" id="c_release_bulk" />
                        </div>

                        <div class="space-y-4">
                            <CommonField type="checkbox-card" label="Is Gatepass Mandatory" v-model="form.is_gatepass_mandatory" id="c_gate_man" />
                            <CommonField type="checkbox-card" label="Enable Direct Invoice" v-model="form.enable_direct_invoice" id="c_inv" />
                            <CommonField type="checkbox-card" label="Enable Inward Tracking" v-model="form.enable_inward_tracking" id="c_inward" />
                            <CommonField type="checkbox-card" label="Enable Package" v-model="form.enable_package" id="c_package" />
                            <CommonField type="checkbox-card" label="Enable SO Consolidation" v-model="form.enable_so_consolidation" id="c_so_consol" />
                            <CommonField type="checkbox-card" label="Enable Auto Package ID Generation" v-model="form.enable_auto_package_id" id="c_auto_package" />
                            <CommonField type="checkbox-card" label="Manifest Accrual Restriction for Warehouse" v-model="form.manifest_accrual_restriction" id="c_manifest_accrual" />
                            <CommonField type="checkbox-card" label="Enable Shuttle Method" v-model="form.enable_shuttle_method" id="c_shuttle" />
                        </div>
                    </div>
                    
                    <div class="mt-8 max-w-lg">
                         <CommonField type="select" label="Default Putaway Location" v-model="form.default_putaway_location" :options="props.locationList" placeholder="Select Location" />
                    </div>
                </div>

                <div v-else-if="activeTab === 'Area'" key="area" class="p-0 w-full">
                    <EditableGrid 
                        v-model="form.areas" 
                        :columns="areaColumns" 
                        :newRowTemplate="{ area_name: '', area_type: '' }"
                        showCopy
                    />
                </div>

                <div v-else-if="activeTab === 'Client Config'" key="client" class="p-0 w-full">
                    <EditableGrid 
                        v-model="form.client_configs" 
                        :columns="clientConfigColumns" 
                        :newRowTemplate="{ organization_code: '', organization_name: '', sku_scan_quantity: 0, is_edi_client: 0 }"
                        showCopy
                    />
                </div>

                <div v-else-if="activeTab === 'Vendor Config'" key="vendor" class="p-0 w-full">
                    <EditableGrid 
                        v-model="form.vendor_configs" 
                        :columns="vendorConfigColumns" 
                        :newRowTemplate="{ organization_code: '', organization_name: '' }"
                        showCopy
                    />
                </div>

                <div v-else-if="activeTab === 'Dock Config'" key="dock" class="p-0 w-full">
                    <EditableGrid 
                        v-model="form.dock_configs" 
                        :columns="dockConfigColumns" 
                        :newRowTemplate="{ dock_name: '', dock_order: '', purpose: '', organization_code: '', organization_name: '' }"
                        showCopy
                    />
                </div>
            <!-- Removed w-full wrap -->
        </div>

        <FormFooter 
            :leftActions="footerLeftActions"
            :actions="footerActions"
            @action-click="handleActionClick"
        />

        <CommonCommentModal 
            v-model:visible="showCommentModal"
            doctype="WMS Warehouse"
            :docname="form.name || form.warehouse_code || ''"
        />

        <CommonDocumentModal
            v-model:visible="showDocumentModal"
            doctype="WMS Warehouse"
            :docname="form.name || form.warehouse_code || ''"
        />

        <CommonEmailModal
            v-model:visible="showEmailModal"
            doctype="WMS Warehouse"
            :docname="form.name || form.warehouse_code || ''"
        />

        <CommonExceptionModal
            v-model:visible="showExceptionModal"
            doctype="WMS Warehouse"
            :docname="form.name || form.warehouse_code || ''"
        />
    </div>
</template>
