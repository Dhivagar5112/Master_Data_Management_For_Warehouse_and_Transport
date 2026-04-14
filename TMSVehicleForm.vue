<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import Fluid from 'primevue/fluid';
import Toast from 'primevue/toast';
import InputSwitch from 'primevue/inputswitch';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

// Components
import CommonHeading from '@/components/CommonHeading.vue';
import CommonField from '@/components/CommonField.vue';
import CommonTabs from '@/components/CommonTabs.vue';
import FormFooter from '@/components/FormFooter.vue';
import CommonCommentModal from '@/components/CommonCommentModal.vue';
import CommonDocumentModal from '@/components/CommonDocumentModal.vue';
import CommonEmailModal from '@/components/CommonEmailModal.vue';
import CommonExceptionModal from '@/components/CommonExceptionModal.vue';
import CommonPreview from '@/components/CommonPreview.vue';

// Services
// import { apiClient } from '@/core/api/apiClient';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import { transportService } from '@/domains/transport/services/transport.service';
import { commentService } from '@/core/api/comment.service';
import { documentService } from '@/core/api/document.service';
import { usePermissions } from '@/composables/usePermissions';
import { extractErrorMessages, extractErrorMessage } from '@/core/utils/errorUtils';
import { rehydrateDates, formatDate } from '@/core/utils/validation.utils';

const props = defineProps({
    initialData: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['saved', 'close']);
const toast = useToast();
const { canWrite } = usePermissions('TMS Vehicle Master');

const API_BASE_URL = import.meta.env.VITE_FRAPPE_API_URL || '';

const savedVehicleName = ref(props.initialData?.name && props.initialData.name !== 'new' ? props.initialData.name : null);
const isLoading = ref(false);
const activeTab = ref('General');

// UI State
const previewVisible = ref(false);
const previewUrl = ref<string | null>(null);
const previewFileName = ref<string>('');
const showCommentModal = ref(false);
const showDocumentModal = ref(false);
const showEmailModal = ref(false);
const showExceptionModal = ref(false);

// Options
const vehicleTypeOptions = ref<any[]>([]);
const carrierOptions = ref<any[]>([]);
const orgOptions = ref<any[]>([]);
const branchOptions = ref<any[]>([]); 
const driverOptions = ref<any[]>([]);
const allDriversRaw = ref<any[]>([]); 
const webfleetVehicleOptions = ref<any[]>([]);
const commentCount = ref(0);
const documentCount = ref(0);

const ownerTypeOptions = [
    { label: 'Owned', value: 'Owned' },
    { label: 'Leased', value: 'Leased' },
    { label: 'Third-party', value: 'Third-party' }
];
const vehicleStatusOptions = [
    { label: 'Available', value: 'Available' },
    { label: 'Busy', value: 'Busy' },
    { label: 'Not Available', value: 'Not Available' },
    { label: 'Damaged', value: 'Damaged' }
];
const ignitionOptions = [
    { label: 'On', value: 'On' },
    { label: 'Off', value: 'Off' }
];
const docTypeOptions = [
    { label: 'License Disk', value: 'License Disk' },
    { label: 'Roadworthy Certificate', value: 'Roadworthy Certificate' },
    { label: 'Insurance Policy', value: 'Insurance Policy' },
    { label: 'Permit', value: 'Permit' },
    { label: 'Pollution Certificate', value: 'Pollution Certificate' },
    { label: 'Fitness Certificate', value: 'Fitness Certificate' }
];

const initialForm = {
    vehicle_number: '',
    vehicle_type: '',
    webfleet_object_no: '',
    carrier: '',
    organization: '',
    branch: '', 
    owner_type: 'Owned',
    is_active: 1,
    gps_device_id: '',
    ignition_status: 'Off',
    fuel_level: 0,
    vehicle_status: 'Available',
    current_driver: '',
    capacity_weight: 0,
    capacity_volume: 0,
    current_odometer: 0,
    engine_hours: 0,
    registration_validity_date: null,
    insurance_validity_date: null,
    fitness_certificate_validity: null,
    photo_front: null,
    photo_back: null,
    photo_left: null,
    photo_right: null,
    compliance_documents: [], 
    notes: '',
    data_source: 'FLEETA'
};

const form = ref<any>({ ...initialForm });

const notesRemaining = computed(() => {
    const len = form.value.notes?.length || 0;
    return 250 - len;
});

const menuItems = computed(() => [
    { label: 'General' },
    { label: 'Specifications' },
    { label: 'Asset Photos' },
    { label: 'Compliance' },
    { label: 'Additional' }
]);

/* ===============================
   Logic: Driver Filtering
================================= */
const updateDriverOptions = () => {
    driverOptions.value = allDriversRaw.value
        .filter((d: any) => {
            const isUnassigned = !d.assigned_vehicle;
            const isAssignedToThisVehicle = d.assigned_vehicle === savedVehicleName.value;
            return isUnassigned || isAssignedToThisVehicle;
        })
        .map((d: any) => {
            const fullName = `${d.first_name || d.driver_name || ''} ${d.last_name || ''}`.trim();
            return { 
                label: fullName || d.driver_code || d.name, 
                value: d.name 
            };
        });
};

/* ===============================
   Logic: File Upload & Preview
================================= */
const onFileSelect = async (event: any, fieldName: string, item?: any) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
        isLoading.value = true;
        
        // 1. Validate if we have a context for upload (needed for backend attachment tracking)
        const docType = 'TMS Vehicle Master';
        const docName = savedVehicleName.value || 'new';

        const result = await documentService.uploadDocument(file, docType, docName);
        
        if (result?.file_url) {
            if (item) item[fieldName] = result.file_url;
            else form.value[fieldName] = result.file_url;
            toast.add({ severity: 'success', summary: 'Success', detail: 'File uploaded successfully', life: 2000 });
        } else {
            throw new Error('Upload failed: No file URL returned');
        }
    } catch (error: any) {
        console.error("Upload Error:", error);
        const msg = extractErrorMessage(error) || 'Permission denied or server error';
        toast.add({ severity: 'error', summary: 'Upload Failed', detail: msg, life: 5000 });
    } finally {
        isLoading.value = false;
        event.target.value = '';
    }
};

const openPreview = (url: string | null, name: string = 'Preview') => {
    if (!url) return;
    previewUrl.value = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    previewFileName.value = name;
    previewVisible.value = true;
};

const getImageUrl = (url: string | null) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    const baseUrl = API_BASE_URL || window.location.origin;
    return `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;
};

/* ===============================
   Logic: Formatting & Dates
================================= */




/* ===============================
   Actions: Save & Load
================================= */
const syncFromBackend = (doc: any) => {
    form.value = { ...form.value, ...rehydrateDates({ ...doc }) };
    form.value.is_active = doc.is_active === 1 || doc.is_active === true ? 1 : 0;
    
    // Ensure we keep track of the modified timestamp to bypass Frappe's stale record validation
    if (doc.modified) {
        form.value.modified = doc.modified;
    }
    
    
    const numericFields = ['fuel_level', 'capacity_weight', 'capacity_volume', 'current_odometer', 'engine_hours'];
    numericFields.forEach(field => {
        if (form.value[field] !== undefined && form.value[field] !== null) {
            const val = parseFloat(form.value[field]);
            form.value[field] = isNaN(val) ? 0 : val;
        }
    });

    updateDriverOptions();
};

const loadVehicle = async () => {
    if (!savedVehicleName.value) return;
    try {
        isLoading.value = true;
        const doc = await masterDataService.getResource('TMS Vehicle Master', savedVehicleName.value);
        syncFromBackend(doc);
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load details', life: 3000 });
    } finally {
        isLoading.value = false;
    }
};

const onSave = async () => {
    const f = form.value;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 1. Mandatory Fields
    const missing = [];
    if (!f.vehicle_number?.toString().trim()) missing.push('Vehicle Number');
    if (!f.vehicle_type) missing.push('Vehicle Type');
    if (!f.organization) missing.push('Organization');
    if (!f.branch) missing.push('Branch');
    
    // Compliance Mandatory Dates
    if (!f.registration_validity_date) missing.push('Registration Validity');
    if (!f.insurance_validity_date) missing.push('Insurance Validity');
    if (!f.fitness_certificate_validity) missing.push('Roadworthy Certificate');

    if (missing.length > 0) {
        toast.add({ severity: 'error', summary: 'Missing Requirements', detail: `The following are mandatory: ${missing.join(', ')}`, life: 5000 });
        return false;
    }

    // 2. Date Validations 
    const regVal = new Date(f.registration_validity_date);
    const insVal = new Date(f.insurance_validity_date);
    const fitVal = new Date(f.fitness_certificate_validity);

    if (regVal < today) {
        toast.add({ severity: 'error', summary: 'Invalid Date', detail: 'Registration Validity cannot be in the past', life: 4000 });
        return false;
    }

    if (insVal < today) {
        toast.add({ severity: 'error', summary: 'Invalid Date', detail: 'Insurance Validity Date has already expired', life: 4000 });
        return false;
    }

    if (insVal > regVal) {
        toast.add({ 
            severity: 'error', 
            summary: 'Invalid Insurance Date', 
            detail: `Insurance Validity (${f.insurance_validity_date}) cannot exceed Registration Validity (${f.registration_validity_date})`, 
            life: 6000 
        });
        return false;
    }

    if (fitVal < today) {
        toast.add({ severity: 'error', summary: 'Invalid Date', detail: 'Road worthy Certificate has already expired', life: 4000 });
        return false;
    }

    if (fitVal < today) {
        toast.add({ severity: 'error', summary: 'Invalid Date', detail: 'Road worthy Certificate has already expired', life: 4000 });
        return false;
    }

    if (fitVal > regVal) {
        toast.add({ 
            severity: 'error', 
            summary: 'Invalid Roadworthy Date', 
            detail: `Road worthy Certificate (${f.fitness_certificate_validity}) cannot exceed Registration Validity (${f.registration_validity_date})`, 
            life: 6000 
        });
        return false;
    }

    // 3. Document Repository Validations
    if (f.compliance_documents?.length > 0) {
        for (const doc of f.compliance_documents) {
            // Basic date logic
            if (doc.issue_date && doc.expiry_date) {
                const issue = new Date(doc.issue_date);
                const expiry = new Date(doc.expiry_date);
                if (expiry <= issue) {
                    toast.add({ severity: 'error', summary: 'Invalid Doc Dates', detail: `Expiry date for ${doc.document_number} must be AFTER the issue date`, life: 4000 });
                    return false;
                }
                if (expiry < today) {
                    toast.add({ severity: 'error', summary: 'Expired Document', detail: `Document ${doc.document_number} (${doc.document_type || doc.document_number}) has already expired`, life: 4000 });
                    return false;
                }
            }

            if (doc.expiry_date) {
                const expiry = new Date(doc.expiry_date);
                if (expiry < today) {
                    toast.add({ severity: 'error', summary: 'Expired Document', detail: `Document ${doc.document_number} (${doc.document_type || doc.document_number}) has already expired`, life: 4000 });
                    return false;
                }
            }

            // Cross-field validation (Bug 1 & 2)
            if (doc.expiry_date) {
                const childExpiry = new Date(doc.expiry_date);
                
                // Bug 1: Insurance Policy expiry cannot be LATER than master insurance validity
                if (doc.document_type === "Insurance Policy" && f.insurance_validity_date) {
                    const masterInsurance = new Date(f.insurance_validity_date);
                    if (childExpiry > masterInsurance) {
                        toast.add({ 
                            severity: 'error', 
                            summary: 'Insurance Date Conflict', 
                            detail: `Insurance Policy Expiry (${formatDate(doc.expiry_date)}) cannot be later than Master Insurance Validity (${formatDate(f.insurance_validity_date)})`, 
                            life: 6000 
                        });
                        return false;
                    }
                }

                // Bug 2: Roadworthy Certificate expiry cannot be EARLIER than master roadworthy validity
                if ((doc.document_type === "Roadworthy Certificate" || doc.document_type === "Fitness Certificate") && f.fitness_certificate_validity) {
                    const masterFitness = new Date(f.fitness_certificate_validity);
                    if (childExpiry < masterFitness) {
                        toast.add({ 
                            severity: 'error', 
                            summary: 'Roadworthy Date Conflict', 
                            detail: `Road worthy Certificate Expiry (${formatDate(doc.expiry_date)}) cannot be earlier than Master Road worthy Certificate Validity (${formatDate(f.fitness_certificate_validity)})`, 
                            life: 6000 
                        });
                        return false;
                    }
                }
            }
        }
    }

    isLoading.value = true;
    try {
        const payload = JSON.parse(JSON.stringify(form.value));

        // Numeric cast & check
        const fuel = parseFloat(payload.fuel_level);
        if (isNaN(fuel) || fuel < 0 || fuel > 100) {
            toast.add({ severity: 'error', summary: 'Limit Exceeded', detail: 'Fuel Level must be 0-100%', life: 3000 });
            return false;
        }
        payload.fuel_level = fuel;

        const odo = parseFloat(payload.current_odometer);
        if (isNaN(odo) || odo < 0) {
            toast.add({ severity: 'error', summary: 'Invalid Input', detail: 'Odometer must be non-negative', life: 3000 });
            return false;
        }
        payload.current_odometer = odo;

        payload.company = form.value.organization;
        payload.registration_validity_date = formatDate(form.value.registration_validity_date);
        payload.insurance_validity_date = formatDate(form.value.insurance_validity_date);
        payload.fitness_certificate_validity = formatDate(form.value.fitness_certificate_validity);
        payload.is_active = payload.is_active ? 1 : 0;
        
        // Pass modified timestamp if present to prevent update conflicts
        if (form.value.modified) {
            payload.modified = form.value.modified;
        }

        if (payload.compliance_documents) {
            payload.compliance_documents = payload.compliance_documents.map((item: any) => ({
                ...item,
                issue_date: formatDate(item.issue_date),
                expiry_date: formatDate(item.expiry_date),
                workflow_progress: parseInt(item.workflow_progress) || 0
            }));
        }

        let result: any;
        if (savedVehicleName.value) {
            result = await masterDataService.updateResource('TMS Vehicle Master', savedVehicleName.value, payload);
        } else {
            result = await masterDataService.createResource('TMS Vehicle Master', payload);
        }

        if (result?.name) {
            savedVehicleName.value = result.name;
            syncFromBackend(result);
            toast.add({ severity: 'success', summary: 'Success', detail: 'Vehicle profile saved securely', life: 2000 });
            emit('saved', form.value);
            return true;
        }
        return false;
    } catch (error: any) {
        console.error("Save Error:", error);
        const rawMsg = extractErrorMessage(error);
        if (rawMsg.toLowerCase().includes('already exists')) {
            toast.add({ severity: 'error', summary: 'Duplicate Entry', detail: `Vehicle number '${f.vehicle_number}' is already registered in the system`, life: 5000 });
        } else {
            const messages = extractErrorMessages(error);
            if (messages.length > 0) {
                messages.forEach(msg => toast.add({ severity: 'error', summary: 'Validation Error', detail: msg, life: 5000 }));
            } else {
                toast.add({ severity: 'error', summary: 'API Error', detail: rawMsg || 'Failed to save record', life: 4000 });
            }
        }
        return false;
    } finally {
        isLoading.value = false;
    }
};

const onSaveAndClose = async () => {
    const success = await onSave();
    if (success) emit('close');
};

const handleFooterAction = (id: string) => {
    if (id === 'comment') showCommentModal.value = true;
    else if (id === 'document') showDocumentModal.value = true;
    else if (id === 'email') showEmailModal.value = true;
    else if (id === 'exception') showExceptionModal.value = true;
};

const addComplianceRow = () => {
    let nextNum = 1;
    if (form.value.compliance_documents && form.value.compliance_documents.length > 0) {
        const nums = form.value.compliance_documents
            .map((doc: any) => {
                const match = doc.document_number?.toString().match(/DOC-(\d+)/);
                return match ? parseInt(match[1]) : 0;
            })
            .filter((n: number) => !isNaN(n));
            
        if (nums.length > 0) {
            nextNum = Math.max(...nums) + 1;
        }
    }
    const docNumber = `DOC-${String(nextNum).padStart(3, '0')}`;
    form.value.compliance_documents.push({
        document_number: docNumber,
        status: 'Active',
        expiry_date: null,
        attachment: null
    });
};

/* ===============================
   Lifecycle
================================= */
onMounted(async () => {
    try {
        const [types, carriers, orgs, branches, drivers] = await Promise.all([
            masterDataService.getResourceList('Vehicle Type', ['name', 'vehicle_type_name']),
            masterDataService.getResourceList('TMS Carrier Master', ['name', 'carrier_name']),
            masterDataService.getResourceList('MDM Org Header', ['name', 'full_name']),
            masterDataService.getResourceList('MDM Branch', ['name', 'branch_name']),
            masterDataService.getResourceList('TMS Driver Master', ['name', 'first_name', 'last_name', 'driver_code', 'assigned_vehicle'])
        ]);
        
        vehicleTypeOptions.value = types.map((t: any) => ({ label: t.vehicle_type_name, value: t.name }));
        carrierOptions.value = carriers.map((c: any) => ({ label: c.carrier_name, value: c.name }));
        orgOptions.value = orgs.map((o: any) => ({ label: o.full_name, value: o.name }));
        branchOptions.value = branches.map((b: any) => ({ label: b.branch_name || b.name, value: b.name }));
        
        allDriversRaw.value = drivers;

        if (savedVehicleName.value) {
            await loadVehicle();
            const [cCount, dCount, wfVehicles] = await Promise.all([
                commentService.getCommentCount('TMS Vehicle Master', savedVehicleName.value),
                documentService.getDocumentCount('TMS Vehicle Master', savedVehicleName.value),
                transportService.getWebfleetVehicleList()
            ]);
            commentCount.value = cCount;
            documentCount.value = dCount;
            
            if (wfVehicles && wfVehicles.message) {
                webfleetVehicleOptions.value = wfVehicles.message.map((v: any) => ({
                    label: `${v.objectname} (${v.objectno})`,
                    value: v.objectno
                }));
            }
        } else {
            const wfVehicles = await transportService.getWebfleetVehicleList();
            if (wfVehicles && wfVehicles.message) {
                webfleetVehicleOptions.value = wfVehicles.message.map((v: any) => ({
                    label: `${v.objectname} (${v.objectno})`,
                    value: v.objectno
                }));
            }
            updateDriverOptions();
        }
    } catch (e) {
        console.error("Mount Error:", e);
    }
});

const footerLeftActions = computed(() => [
    { id: 'comment', label: 'Comment', icon: 'pi pi-comments', count: commentCount.value },
    { id: 'document', label: 'Document', icon: 'pi pi-copy', count: documentCount.value },
    { id: 'email', label: 'Email', icon: 'pi pi-envelope' },
    { id: 'exception', label: 'Exception', icon: 'pi pi-exclamation-triangle' },
]);

const onClear = () => {
    form.value = { ...initialForm };
    toast.add({ severity: 'info', summary: 'Form Cleared', detail: 'All values have been reset', life: 2000 });
};

const footerActions = computed(() => {
    const actions: any[] = [];
    
    // Left - Cancel
    actions.push({ label: 'Cancel', severity: 'danger', outlined: true, command: () => emit('close') });

    actions.push({ label: 'Save & Close', severity: 'primary' as const, command: onSaveAndClose, disabled: !canWrite.value, loading: isLoading.value });
    actions.push({ label: 'Save', severity: 'primary' as const, command: onSave, disabled: !canWrite.value, loading: isLoading.value });

    return actions;
});

defineExpose({ onSave, isLoading });
</script>

<template>
    <div class="vehicle-form-container flex flex-col h-full bg-surface-50 dark:bg-surface-950 overflow-hidden">
        <Toast position="top-right" :life="2000" />
        <CommonPreview v-model:visible="previewVisible" :fileUrl="previewUrl" :fileName="previewFileName" />

        <div class="sticky top-0 z-[10] bg-surface-0 dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700">
            <CommonTabs :items="menuItems" v-model="activeTab" />
        </div>

        <div class="flex-1 overflow-y-auto p-6">
            <Fluid>
                <div class="max-w-[1600px] mx-auto space-y-6">
                    
                    <!-- General Tab -->
                    <div v-show="activeTab === 'General'" class="space-y-6">
                        <div class="card p-6 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <div class="flex justify-between items-center mb-4">
                                <CommonHeading text="Vehicle Information" level="2" icon="pi pi-car" />
                                <div class="flex items-center gap-2">
                                    <span class="text-[10px] font-bold text-surface-400 uppercase tracking-widest">Active</span>
                                    <InputSwitch v-model="form.is_active" class="custom-switch-xs" :trueValue="1" :falseValue="0" />
                                </div>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <CommonField label="Vehicle Number" v-model="form.vehicle_number" :disabled="!!savedVehicleName" required />
                                <CommonField label="Vehicle Type" v-model="form.vehicle_type" type="select" :options="vehicleTypeOptions" required />
                                <CommonField label="Organization" v-model="form.organization" type="select" :options="orgOptions" required />
                                <CommonField label="Branch" v-model="form.branch" type="select" :options="branchOptions" required />
                                <CommonField label="Carrier" v-model="form.carrier" type="select" :options="carrierOptions" />
                                <CommonField label="Owner Type" v-model="form.owner_type" type="select" :options="ownerTypeOptions" />
                                <CommonField label="Webfleet Object Mapping" v-model="form.webfleet_object_no" type="select" :options="webfleetVehicleOptions" filter placeholder="Select Webfleet Object" />
                                <CommonField label="Data Source" v-model="form.data_source" disabled />
                                <CommonField label="GPS Device ID" v-model="form.gps_device_id" />
                            </div>
                        </div>

                        <div class="card p-6 space-y-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <CommonHeading text="Operational Status" level="2" icon="pi pi-bolt" />
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <CommonField label="Vehicle Status" v-model="form.vehicle_status" type="select" :options="vehicleStatusOptions" />
                                <CommonField label="Assigned Driver" v-model="form.current_driver" type="select" :options="driverOptions" filter />
                                <CommonField label="Ignition Status" v-model="form.ignition_status" type="select" :options="ignitionOptions" />
                                <CommonField label="Fuel Level (%)" v-model="form.fuel_level" type="number" :min="0" :max="100" />
                            </div>
                        </div>
                    </div>

                    <!-- Specifications Tab -->
                    <div v-show="activeTab === 'Specifications'" class="space-y-6">
                        <div class="card p-6 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <CommonHeading text="Specs & Metrics" level="2" icon="pi pi-cog" />
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <CommonField label="Capacity Weight (KG)" v-model="form.capacity_weight" type="number" />
                                <CommonField label="Capacity Volume (CBM)" v-model="form.capacity_volume" type="number" />
                                <CommonField label="Current Odometer" v-model="form.current_odometer" type="number" />
                                <CommonField label="Engine Hours" v-model="form.engine_hours" type="number" />
                            </div>
                        </div>
                    </div>

                    <!-- Asset Photos Tab -->
                    <div v-show="activeTab === 'Asset Photos'" class="space-y-6">
                        <div class="card p-6 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <CommonHeading text="Vehicle Images" level="2" icon="pi pi-images" />
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div v-for="side in ['front', 'back', 'left', 'right']" :key="side" class="flex flex-col gap-2">
                                    <div class="relative border-2 border-dashed border-surface-200 dark:border-surface-700 rounded-xl h-64 flex flex-col items-center justify-center bg-surface-50 dark:bg-surface-800 group transition-all hover:border-primary/50 overflow-hidden shadow-sm">
                                        <label class="text-[9px] font-black text-surface-400 uppercase absolute top-2 z-10">Vehicle {{ side }} View</label>
                                        
                                        <img v-if="form['photo_' + side]" :src="getImageUrl(form['photo_' + side])" class="w-full h-full object-cover rounded-xl" />
                                        
                                        <template v-else>
                                            <i class="pi pi-camera text-3xl text-surface-300 mt-2 group-hover:text-primary transition-colors"></i>
                                            <span class="text-[11px] text-surface-400 font-medium group-hover:text-primary transition-colors mt-2">Upload Photo</span>
                                        </template>

                                        <input type="file" @change="onFileSelect($event, 'photo_' + side)" class="absolute inset-0 opacity-0 cursor-pointer z-20" accept="image/*" />
                                    </div>
                                    <CommonButton v-if="form['photo_' + side]" :label="'Preview ' + side" class="w-full !p-1.5 !text-xs font-bold" text @click="openPreview(form['photo_' + side], 'Vehicle ' + side + ' view')" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Compliance Tab -->
                    <div v-show="activeTab === 'Compliance'" class="space-y-6">
                        <div class="card p-6 space-y-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <CommonHeading text="Validity Deadlines" level="2" icon="pi pi-calendar-check" />
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <CommonField label="Registration Validity Date" v-model="form.registration_validity_date" type="date" dateFormat="dd/mm/yy" required />
                                <CommonField label="Insurance Validity Date" v-model="form.insurance_validity_date" type="date" dateFormat="dd/mm/yy" required />
                                <CommonField label="Road worthy Certificate" v-model="form.fitness_certificate_validity" type="date" dateFormat="dd/mm/yy" required />
                            </div>
                        </div>

                        <div class="card p-6 space-y-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900 shadow-sm">
                            <div class="flex items-center justify-between mb-4">
                                <div class="flex items-center gap-2">
                                    <i class="pi pi-folder text-primary text-lg"></i>
                                    <h2 class="text-xl font-bold text-primary">Document Repository</h2>
                                </div>
                                <Button 
                                    label="Add Document" 
                                    icon="pi pi-plus" 
                                    rounded
                                    severity="primary"
                                    class="!text-[10px] !font-bold !uppercase !tracking-widest !px-4 !py-2 !w-max !shadow-sm active:!scale-95 flex items-center gap-1.5"
                                    @click="addComplianceRow" 
                                />
                            </div>
                            
                            <DataTable :value="form.compliance_documents" class="compliance-table p-datatable-sm mt-6 border border-surface-100 dark:border-surface-800 rounded-lg overflow-hidden">
                                <Column header="TYPE" style="width: 25%" headerClass="text-[10px] font-bold text-surface-400 uppercase tracking-[0.2em] px-4 py-3 bg-surface-50 dark:bg-surface-800/50 border-b border-surface-100 dark:border-surface-800">
                                    <template #body="{ data }">
                                        <select v-model="data.document_type" class="child-input h-9 bg-surface-50/50 dark:bg-surface-800/50 text-xs">
                                            <option v-for="o in docTypeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
                                        </select>
                                    </template>
                                </Column>
                                <Column header="NUMBER" style="width: 25%" headerClass="text-[10px] font-bold text-surface-400 uppercase tracking-[0.2em] px-4 py-3 bg-surface-50 dark:bg-surface-800/50 border-b border-surface-100 dark:border-surface-800">
                                    <template #body="{ data }">
                                        <input v-model="data.document_number" class="child-input h-9 bg-surface-50/50 dark:bg-surface-800/50 text-xs" placeholder="DOC-001" />
                                    </template>
                                </Column>
                                <Column header="EXPIRY DATE" style="width: 20%" headerClass="text-[10px] font-bold text-surface-400 uppercase tracking-[0.2em] px-4 py-3 bg-surface-50 dark:bg-surface-800/50 border-b border-surface-100 dark:border-surface-800">
                                    <template #body="{ data }">
                                        <CommonField 
                                            v-model="data.expiry_date" 
                                            type="date" 
                                            isPlain 
                                            dateFormat="dd/mm/yy"
                                            placeholder="dd/mm/yyyy"
                                            class="!h-9 !bg-surface-50/50 dark:!bg-surface-800/50"
                                        />
                                    </template>
                                </Column>
                                <Column header="FILE" style="width: 15%" headerClass="text-[10px] font-bold text-surface-400 uppercase tracking-[0.2em] px-4 py-3 text-center bg-surface-50 dark:bg-surface-800/50 border-b border-surface-100 dark:border-surface-800">
                                    <template #body="{ data }">
                                        <div class="flex items-center gap-2 justify-center">
                                            <div class="relative cursor-pointer">
                                                <i :class="data.attachment ? 'pi pi-file-pdf text-primary' : 'pi pi-paperclip text-surface-400'" class="text-lg hover:text-primary transition-colors"></i>
                                                <input type="file" class="absolute inset-0 opacity-0 cursor-pointer" @change="onFileSelect($event, 'attachment', data)" />
                                            </div>
                                            <Button 
                                                v-if="data.attachment"
                                                icon="pi pi-eye" 
                                                severity="warning"
                                                text
                                                rounded
                                                size="small"
                                                class="scale-90 hover:bg-warning-50 !p-0"
                                                @click="openPreview(data.attachment, data.document_type || data.document_number)"
                                            />
                                        </div>
                                    </template>
                                </Column>
                                <Column style="width: 15%" headerClass="bg-surface-50 dark:bg-surface-800/50 border-b border-surface-100 dark:border-surface-800 text-center">
                                    <template #body="{ index }">
                                        <div class="flex justify-center">
                                            <Button 
                                                icon="pi pi-trash" 
                                                class="text-orange-500 hover:text-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20 scale-90" 
                                                text 
                                                rounded 
                                                @click="form.compliance_documents.splice(index, 1)" 
                                            />
                                        </div>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>

                    <!-- Additional Tab -->
                    <div v-show="activeTab === 'Additional'" class="space-y-6">
                        <div class="card p-8 border border-surface-200 dark:border-surface-700 rounded-2xl bg-surface-0 dark:bg-surface-900 shadow-md">
                            <div class="flex justify-between items-center mb-6">
                                <div class="flex items-center gap-3">
                                    <i class="pi pi-pencil text-primary text-xl"></i>
                                    <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Notes</h2>
                                </div>
                                <span class="text-xs font-bold text-surface-400 uppercase tracking-widest">
                                    {{ notesRemaining }} characters remaining
                                </span>
                            </div>
                            
                            <div class="space-y-2">
                                <label class="text-[10px] font-bold text-surface-500 uppercase tracking-widest">Notes</label>
                                <textarea 
                                    v-model="form.notes" 
                                    rows="10" 
                                    class="w-full p-5 rounded-2xl border-2 border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-800/50 focus:border-primary focus:bg-white dark:focus:bg-surface-900 transition-all outline-none resize-none text-sm leading-relaxed"
                                    placeholder="Enter internal vehicle notes here..."
                                    maxlength="250"
                                ></textarea>
                            </div>
                        </div>
                    </div>

                </div>
            </Fluid>
        </div>

        <FormFooter 
            :leftActions="footerLeftActions"
            :actions="footerActions"
            @action-click="handleFooterAction"
            @clear="onClear"
        />

        <CommonCommentModal v-model:visible="showCommentModal" doctype="TMS Vehicle Master" :docname="savedVehicleName" />
        <CommonDocumentModal v-model:visible="showDocumentModal" doctype="TMS Vehicle Master" :docname="savedVehicleName" />
        <CommonEmailModal v-model:visible="showEmailModal" doctype="TMS Vehicle Master" :docname="savedVehicleName" />
        <CommonExceptionModal v-model:visible="showExceptionModal" doctype="TMS Vehicle Master" :docname="savedVehicleName" />
    </div>
</template>

<style scoped>
.vehicle-form-container { height: 100%; }
.child-input {
    @apply w-full p-2 bg-transparent border border-surface-200 dark:border-surface-700 rounded-md text-xs outline-none focus:border-primary;
}
:deep(.custom-switch-xs.p-inputswitch) {
    width: 2.2rem;
    height: 1.1rem;
}
:deep(.custom-switch-xs.p-inputswitch .p-inputswitch-slider:before) {
    width: 0.8rem;
    height: 0.8rem;
    left: 0.15rem;
    margin-top: -0.4rem;
}
:deep(.custom-switch-xs.p-inputswitch.p-inputswitch-checked .p-inputswitch-slider:before) {
    transform: translateX(1.1rem);
}
</style> 
