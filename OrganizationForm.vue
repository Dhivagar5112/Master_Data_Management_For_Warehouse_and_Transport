<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import { masterDataService } from '@/domains/master-data/services/master-data.service';
import OrganizationAddress from './OrganizationAddress.vue';
import OrganizationContact from './OrganizationContact.vue';
import OrganizationCompany from './OrganizationCompany.vue';
import OrganizationEmployee from './OrganizationEmployee.vue';
import OrganizationRelatedParties from './OrganizationRelatedParties.vue';
import OrganizationReference from './OrganizationReference.vue';
import OrganizationTransport from './OrganizationTransport.vue';
import OrganizationWarehouse from './OrganizationWarehouse.vue';
import OrganizationConsignee from './OrganizationConsignee.vue';
import OrganizationConsignor from './OrganizationConsignor.vue';
import OrganizationConfiguration from './OrganizationConfiguration.vue';
import FormFooter from '@/components/FormFooter.vue';
import CommonCommentModal from '@/components/CommonCommentModal.vue';
import CommonDocumentModal from '@/components/CommonDocumentModal.vue';
import CommonEmailModal from '@/components/CommonEmailModal.vue';
import CommonExceptionModal from '@/components/CommonExceptionModal.vue';
import { documentService } from '@/core/api/document.service';
import { commentService } from '@/core/api/comment.service';
import { usePermissions } from '@/composables/usePermissions';
import { extractErrorMessage } from '@/core/utils/errorUtils';

import Panel from 'primevue/panel';
import CommonHeading from '@/components/CommonHeading.vue'; 
import CommonField from '@/components/CommonField.vue';
import CommonTabs from '@/components/CommonTabs.vue';

const props = defineProps({
    initialData: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['saved', 'close']);

const toast = useToast();
const { canWrite } = usePermissions('MDM Org Header');
const activeTab = ref('General');
const isLoading = ref(false);

const orgTypes = [
    { label: 'Is Consignee', field: 'is_consignee', desc: 'Organization receives shipments' },
    { label: 'Is Transporter', field: 'is_transporter', desc: 'Provides transport services' },
    { label: 'Is Air CTO', field: 'is_air_cto', desc: 'Air Cargo Terminal Operator' },
    { label: 'Is Consignor', field: 'is_consignor', desc: 'Organization sends shipments' },
    { label: 'Is Forwarder', field: 'is_forwarder', desc: 'Freight forwarder organization' },
    { label: 'Is Airline', field: 'is_air_line', desc: 'Airline carrier' },
    { label: 'Is Transport Client', field: 'is_transport_client', desc: 'Uses transport services' },
    { label: 'Is Shipping Provider', field: 'is_shipping_provider', desc: 'Provides shipping services' },
    { label: 'Is Broker', field: 'is_broker', desc: 'Customs or freight broker' },
    { label: 'Is Warehouse Client', field: 'is_warehouse_client', desc: 'Uses warehouse services' },
    { label: 'Is Warehouse Provider', field: 'is_warehouse_provider', desc: 'Provides warehouse services' },
    { label: 'Is Container Park', field: 'is_container_park', desc: 'Container storage facility' },
    { label: 'Is Fleet Maintenance', field: 'is_fleet_maintenance', desc: 'Container storage facility' },
    { label: 'Is Fuel Provider', field: 'is_fuel_provider', desc: 'Container storage facility' },
];

const additionalOrgTypes = [
    { label: 'Is Local Transport', field: 'is_local_transport', desc: 'Local transport provider' },
    { label: 'Is Pack Depot', field: 'is_pack_depot', desc: 'Packaging depot facility' },
    { label: 'Is Sea CTO', field: 'is_sea_cto', desc: 'Sea Cargo Terminal Operator' },
    { label: 'Is Shipping Line', field: 'is_shipping_line', desc: 'Shipping line carrier' },
    { label: 'Is Unpack Depot', field: 'is_unpack_depot', desc: 'Unpacking depot facility' },
    { label: 'Is Rail Head', field: 'is_rail_head', desc: 'Rail terminal or railhead' },
    { label: 'Is Road Freight Depot', field: 'is_road_freight_depot', desc: 'Road freight depot' },
    { label: 'Is Road Freight', field: 'is_road_freight', desc: 'Road freight services' },
    { label: 'Is Shipping Consortium', field: 'is_shipping_consortium', desc: 'Shipping consortium member' },
    { label: 'Is Fumigation Contractor', field: 'is_fumigation_contractor', desc: 'Fumigation service provider' },
    { label: 'Is Freight Carrier', field: 'is_freight_carrier', desc: 'Freight carrier' },
    { label: 'Is Misc Freight Services', field: 'is_misc_freight_services', desc: 'Provides miscellaneous freight services' },
    { label: 'Is Global Account', field: 'is_global_account', desc: 'Global account classification' },
    { label: 'Is National Account', field: 'is_national_account', desc: 'National account classification' },
    { label: 'Is Sales Lead', field: 'is_sales_lead', desc: 'Sales lead or prospect' },
    { label: 'Is Sales', field: 'is_sales', desc: 'Sales organization' },
    { label: 'Is Competitor', field: 'is_competitor', desc: 'Competitor organization' },
    { label: 'Is Temp Account', field: 'is_temp_account', desc: 'Temporary account' },
    { label: 'Is Services', field: 'is_services', desc: 'Services organization' },
    { label: 'Is SO Auto Confirm', field: 'is_so_auto_confirm', desc: 'Automatically confirm sales orders' },
    { label: 'Is Personal Effects Account', field: 'is_personal_effects_account', desc: 'Personal effects shipment account' },
    { label: 'Is Distribution Centre', field: 'is_distribution_centre', desc: 'Distribution center facility' },
    { label: 'Is Store', field: 'is_store', desc: 'Retail store location' },
    { label: 'Is Depot', field: 'is_depot', desc: 'Depot facility' },
];

const form = ref<any>({
    name: '',
    code: '',
    full_name: '',
    short_name: '',
    is_fleet_vendor: false,
    enable_org_code: false,
    customer_org_code: '',
    language: 'EN',
    is_active: true,
    is_valid: false,
    oad_address1: '',
    oad_address2: '',
    oad_city: '',   
    oad_state: '',
    oad_state_desc: '',
    oad_post_code: '',
    oad_country_code: '',
    oad_country_code_desc: '',
    oad_related_port_code: '',
    oad_related_port_code_desc: '',
    closest_port: '',
    oad_phone: '',
    oad_mobile: '',
    oad_email: '',
    oad_fax: '',
    oad_company_name_override: '',
    oad_code: '',
    site_id: '',
    site_name: '',
    external_site_id: '',
    gst_no: '',
    oad_latitude: '',
    oad_longitude: '',
    loading_unloading_constraints: '',
    is_custom_filing_by_branch: false,
    is_custom_filing_by_dna: false,
    pickup_service_default: false,
    export_clearance_service_default: false,
    eft_customs_from_importer_account: false,
    is_po_mandatory: false,
    is_orderline_processing: false,
    is_eft_required: false,
    is_eft_3_step_approval_required: false,
    is_update_container_priority_task_required: false,
    show_ar_invoice_documents: false,
    is_re_approval_needed: false,
    is_booking_approval_mandatory: false,
    user_discretion_booking: false,
    enable_bcn_consol_approval: false,
    booking_approval_to_buyer: false,
    booking_approval_to_destination_cs: false,
    is_po_approval_required: false,
    order_approval_to_buyer: false,
    order_approval_to_destination_cs: false,
    delivery_service_default: false,
    import_clearance_service_default: false,
    multi_client_configuration: false,
    manifest_accrual_restriction_for_transporter: false,
    manifest_creation_restriction_for_transporter: false,
    disable_payment_visibility: false,
    docket_number_length: null,
    docket_number_min_length: null,
    docket_number_max_length: null,
    docket_number_type: '',
    use_packing_date: false,
    package_dimension: false,
    use_expiry_date: false,
    product_dimension: false,
    putaway_same_product_together: false,
    overriding_system_setting: false,
    location_fallback: '0',
    pick_face: '0',
    client_area: '0',
    product_area: '0',
    fifo_fallback: '0',
    picking_expiry_date: '0',
    udf1_name: '', udf1_type: '',
    udf2_name: '', udf2_type: '',
    udf3_name: '', udf3_type: '',
    barcode_type: '',
    product_rule: '',
    udf1_rule: '',
    udf2_rule: '',
    udf3_rule: '',
    barcode_packing_date: '',
    barcode_expiry_date: '',
    is_asn_mandatory: false,
    update_dispatch_information: false,
    edi_inward_gate_pass: false,
    enable_split_po: false,
    enabled_email_validation: false,
    disable_generate_wms_lrnumber: false,
    enable_scan_all: false,
    enable_inward_invoice_value: false,
    enable_so_consolidation: false,
    enable_double_scanning_for_client: false,
    release_capture_bulkoption: false,
    update_grn_in_client_system: false,
    additional_reference_config: false,
    enable_return_goods_grn: false,
    enable_pick_completion_validation: false,
    enabled_mobile_number_validation: false,
    enable_order_number_length_capacity: false,
    enable_reverse_pickup: false,
    enable_dimension_for_outward: false,
    disable_release_capture_scanning_mtr: false,
    update_invoice_information: false,
    edi_client_restriction: false,
    update_invoice_from_client_system: false,
    enable_direct_invoicing: false,
    edi_client_enable_line_no_editable: false,
    enabled_email_and_mobile_no_validation: false,
    enable_pick_confirmation_after_load_complete_edi: false,
    enable_release_captured_product_scanning_in_inward: false,
    enable_outward_invoice_value: false,
    enable_split_pick: false,
    enable_auto_acp: false,
    by_pass_invoice_document: false,
    enable_shuttle_method: false,
    auto_so_confirm: false,
    min_amt_to_trigger_eft: null,
    followup_source: '',
    followup_due: '',
    handling_instructions: '',
    pickup_notes: '',
    consignor_handling_instructions: '',
    address_list: [],
    time_table_list: [],
    contact_list: [],
    contact_group_list: [],
    contact_group_mapping_list: [],
    company_list: [],
    employee_list: [],
    related_party_list: [],
    reference_list: [],
    transport_config_list: [],
    transport_mapping_list: [],
    receiving_warehouse_config_list: [],
    consignee_defaults_list: [],
    consignor_config_list: [],
    consignor_default_document_list: [],
    consignor_transport_country_doc_list: [],
    user_role_access_list: [],
    security_mapping_domain_list: [],
    security_mapping_party_list: [],
    access_rights_event_list: [],
    access_rights_event_v2_list: [],
    access_rights_task_list: [],
    access_rights_comment_list: [],
    access_rights_document_list: [],
    access_rights_exception_list: [],
    access_rights_email_list: [],
    configuration_list: [],
    document_delivery_config_list: [],
    warehouse_config_list: [],
    consignee_mapping_list: [],
    consignor_mapping_list: []
});

const documentCount = ref(0);
const commentCount = ref(0);
const validationErrors = ref<Record<string, string>>({});

const fetchDocumentCount = async () => {
    if (!form.value.name) return;
    try {
        const docs = await documentService.getDocuments('MDM Org Header', form.value.name);
        documentCount.value = docs.length;
    } catch (error) {
        console.error('Error fetching document count:', error);
    }
};

const fetchCommentCount = async () => {
    if (!form.value.name) return;
    try {
        const comments = await commentService.getComments('MDM Org Header', form.value.name);
        commentCount.value = comments.length;
    } catch (error) {
        console.error('Error fetching comment count:', error);
    }
};

const menuItems = computed(() => [
    { label: 'General', icon: 'pi pi-id-card', command: () => { activeTab.value = 'General'; } },
    { label: 'Address', icon: 'pi pi-map-marker', command: () => { activeTab.value = 'Address'; } },
    { label: 'Contact', icon: 'pi pi-user', command: () => { activeTab.value = 'Contact'; } },
    { label: 'Company', icon: 'pi pi-building', command: () => { activeTab.value = 'Company'; } },
    { label: 'Employee', icon: 'pi pi-users', command: () => { activeTab.value = 'Employee'; } },
    { label: 'Related Parties', icon: 'pi pi-users', command: () => { activeTab.value = 'Related Parties'; } },
    { label: 'Reference', icon: 'pi pi-bookmark', command: () => { activeTab.value = 'Reference'; } },
    { label: 'Transport', icon: 'pi pi-truck', command: () => { activeTab.value = 'Transport'; } },
    { label: 'Warehouse', icon: 'pi pi-warehouse', command: () => { activeTab.value = 'Warehouse'; } },
    { label: 'Consignee', icon: 'pi pi-download', command: () => { activeTab.value = 'Consignee'; } },
    { label: 'Consignor', icon: 'pi pi-upload', command: () => { activeTab.value = 'Consignor'; } },
    { label: 'Configuration', icon: 'pi pi-cog', command: () => { activeTab.value = 'Configuration'; } },
]);

const countryList = ref<any[]>([]);
const stateList = ref<any[]>([]);
const cityList = ref<any[]>([]);
const portList = ref<any[]>([]);
const languages = ref([
    { label: 'English', value: 'EN' }, 
    { label: 'Tamil', value: 'TA' },
    { label: 'Hindi', value: 'HI' }
]);

const onCountryChange = async () => {
    if (form.value.oad_country_code) {
        const selectedCountry = countryList.value.find(c => c.value === form.value.oad_country_code);
        if(selectedCountry) form.value.oad_country_code_desc = selectedCountry.label;

        try {
            const states = await masterDataService.getStates(form.value.oad_country_code);
            stateList.value = states.map((s: any) => ({ label: s.state_name, value: s.name }));

            if (form.value.oad_state && !stateList.value.some(s => s.value === form.value.oad_state)) {
                form.value.oad_state = '';
                form.value.oad_state_desc = '';
                form.value.oad_city = '';
                cityList.value = [];
            }
        } catch (error) {
            console.error('Error loading states:', error);
            stateList.value = [];
        }
    } else {
        stateList.value = [];
        form.value.oad_state = '';
        form.value.oad_state_desc = '';
        form.value.oad_city = '';
        cityList.value = [];
    }
};

const onStateChange = async () => {
    cityList.value = [];
    if (form.value.oad_state) {
        const cities = await masterDataService.getCities(form.value.oad_state);
        cityList.value = cities.map(c => ({ label: c.city_name, value: c.name }));

        const selectedState = stateList.value.find(s => s.value === form.value.oad_state);
        if(selectedState) form.value.oad_state_desc = selectedState.label;
    }
};

const onPostCodeBlur = async () => {
    if (form.value.oad_post_code) {
        try {
            const pcList = await masterDataService.getPostcodes(form.value.oad_post_code);
            if (pcList && pcList.length > 0) {
                const exact = pcList.find((c: any) => c.postcode === form.value.oad_post_code);
                const pc = exact || pcList[0];

                if (pc.country && form.value.oad_country_code !== pc.country) {
                    form.value.oad_country_code = pc.country;
                    await onCountryChange();
                }
                if (pc.state && form.value.oad_state !== pc.state) {
                    form.value.oad_state = pc.state;
                    await onStateChange();
                }
                if (pc.city && form.value.oad_city !== pc.city) {
                    form.value.oad_city = pc.city;
                }
            }
        } catch (error) {
            console.error('Error fetching post code details:', error);
        }
    }
};

const validateForm = () => {
    validationErrors.value = {};
    const errors: Record<string, string> = {};

    if (form.value.enable_org_code && !form.value.code) errors.code = 'Organization Code is required';
    if (!form.value.full_name) errors.full_name = 'Organization Name is required';
    if (!form.value.oad_address1) errors.oad_address1 = 'Address Line 1 is required';
    if (!form.value.oad_city) errors.oad_city = 'City is required';
    if (!form.value.oad_state) errors.oad_state = 'State is required';
    if (!form.value.oad_post_code) {
        errors.oad_post_code = 'Post Code is required';
    } else if (!/^[a-zA-Z0-9\s-]{3,10}$/.test(form.value.oad_post_code)) {
        errors.oad_post_code = 'Invalid Postal Code Format';
    }
    if (!form.value.oad_country_code) errors.oad_country_code = 'Country Code is required';
    if (!form.value.oad_related_port_code) errors.oad_related_port_code = 'Related Port Code is required';
    if (!form.value.language) errors.language = 'Language is required';

    if (form.value.oad_email) {
        const emailPattern = /^([\w\.\-]+)@([\w\-]+)((\.(\w){2,4})+)$/;
        if (!emailPattern.test(form.value.oad_email)) {
            errors.oad_email = 'Invalid Email Format';
        }
    }

    const phonePattern = /^\+?[\d\s\-\(\)]+$/;
    if (form.value.oad_phone && !phonePattern.test(form.value.oad_phone)) {
        errors.oad_phone = 'Invalid Phone Format';
    }
    if (form.value.oad_mobile && !phonePattern.test(form.value.oad_mobile)) {
        errors.oad_mobile = 'Invalid Mobile Format';
    }

    const hasOrgType = [...orgTypes, ...additionalOrgTypes].some(type => form.value[type.field]);
    if (!hasOrgType) {
        toast.add({ severity: 'warn', summary: 'Validation', detail: 'At least one organization type must be selected', life: 5000 });
        errors.org_types = 'At least one type required';
    }

    validationErrors.value = errors;
    if (Object.keys(errors).length > 0) {
        const hasAny = (keys: string[]) => keys.some((k) => errors[k]);
        if (hasAny(['code', 'full_name', 'oad_address1', 'oad_city', 'oad_state', 'oad_post_code', 'oad_country_code', 'oad_related_port_code', 'language', 'oad_email', 'oad_phone', 'oad_mobile', 'org_types'])) {
            activeTab.value = 'General';
        }
    }

    return Object.keys(errors).length === 0;
};

const onSave = async () => {
    if (!validateForm()) {
        const errorMessages = Object.values(validationErrors.value).join('. ');
        toast.add({ severity: 'error', summary: 'Validation Error', detail: errorMessages || 'Please fix the errors before saving', life: 5000 });
        return false;
    }

    try {
        isLoading.value = true;
        const payload = JSON.parse(JSON.stringify(form.value));
        const booleanFields = [
            'is_fleet_vendor', 'enable_org_code', 'is_active', 'is_valid', 'auto_so_confirm',
            'is_custom_filing_by_branch', 'is_custom_filing_by_dna', 'pickup_service_default', 'export_clearance_service_default',
            'eft_customs_from_importer_account', 'is_po_mandatory', 'is_orderline_processing', 'is_eft_required', 
            'is_eft_3_step_approval_required', 'is_update_container_priority_task_required', 'show_ar_invoice_documents', 
            'is_re_approval_needed', 'is_booking_approval_mandatory', 'user_discretion_booking', 'enable_bcn_consol_approval', 
            'booking_approval_to_buyer', 'booking_approval_to_destination_cs', 'is_po_approval_required', 
            'order_approval_to_buyer', 'order_approval_to_destination_cs', 'delivery_service_default', 'import_clearance_service_default',
            'multi_client_configuration', 'manifest_accrual_restriction_for_transporter', 'manifest_creation_restriction_for_transporter', 'disable_payment_visibility',
            'use_packing_date', 'package_dimension', 'use_expiry_date', 'product_dimension',
            'putaway_same_product_together', 'overriding_system_setting',
            'is_asn_mandatory', 'update_dispatch_information', 'edi_inward_gate_pass', 'enable_split_po',
            'enabled_email_validation', 'disable_generate_wms_lrnumber', 'enable_scan_all',
            'enable_inward_invoice_value', 'enable_so_consolidation', 'enable_double_scanning_for_client',
            'release_capture_bulkoption', 'update_grn_in_client_system', 'edi_client_restriction',
            'additional_reference_config', 'enable_return_goods_grn', 'enable_pick_completion_validation',
            'enabled_mobile_number_validation', 'enable_order_number_length_capacity', 'enable_reverse_pickup',
            'enable_dimension_for_outward', 'disable_release_capture_scanning_mtr', 'update_invoice_information',
            'enable_shuttle_method', 'update_invoice_from_client_system', 'enable_direct_invoicing',
            'edi_client_enable_line_no_editable', 'enabled_email_and_mobile_no_validation',
            'enable_pick_confirmation_after_load_complete_edi', 'enable_release_captured_product_scanning_in_inward',
            'enable_outward_invoice_value', 'enable_split_pick', 'enable_auto_acp', 'by_pass_invoice_document',
            ...orgTypes.map(c => c.field),
            ...additionalOrgTypes.map(c => c.field)
        ];
        booleanFields.forEach(field => {
            if(payload[field] !== undefined) payload[field] = payload[field] ? 1 : 0;
        });

        const orgCode = payload.code;

        const childBooleanFields: Record<string, string[]> = {
            'address_list': ['is_active'],
            'time_table_list': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
            'contact_list': ['is_active', 'is_primary_contact'],
            'company_list': ['is_default', 'is_active', 'is_debtor', 'is_creditor'],
            'employee_list': ['is_active'],
            'related_party_list': ['is_active'],
            'consignee_mapping_list': ['is_default'],
            'consignor_mapping_list': ['is_default'],
            'transport_config_list': ['is_active'],
            'transport_mapping_list': ['is_active', 'is_default']
        };

        Object.entries(childBooleanFields).forEach(([tableName, fields]) => {
            if (payload[tableName] && Array.isArray(payload[tableName])) {
                payload[tableName].forEach((row: any) => {
                    fields.forEach(field => {
                        if (row[field] !== undefined) {
                            row[field] = row[field] ? 1 : 0;
                        }
                    });
                });
            }
        });
        
        if (payload.time_table_list) {
            payload.time_table_list = payload.time_table_list.map((row: any) => {
                const newRow = { ...row };
                if (newRow.time_from) {
                    const date = newRow.time_from instanceof Date ? newRow.time_from : new Date(newRow.time_from);
                    if (!isNaN(date.getTime())) {
                        newRow.time_from = date.toTimeString().split(' ')[0];
                    }
                }
                if (newRow.time_to) {
                    const date = newRow.time_to instanceof Date ? newRow.time_to : new Date(newRow.time_to);
                    if (!isNaN(date.getTime())) {
                        newRow.time_to = date.toTimeString().split(' ')[0];
                    }
                }
                return newRow;
            });
        }

        if (payload.reference_list) {
            payload.reference_list = payload.reference_list.map((row: any) => {
                const newRow = { ...row };
                const dateFields = ['available_from', 'available_to', 'start_date', 'end_date'];
                dateFields.forEach(field => {
                    if (newRow[field]) {
                        const date = newRow[field] instanceof Date ? newRow[field] : new Date(newRow[field]);
                        if (!isNaN(date.getTime())) {
                            newRow[field] = date.toISOString().split('T')[0];
                        }
                    }
                });
                return newRow;
            });
        }

        if (payload.address_list) {
            payload.address_list.forEach((addr: any) => {
                addr.language = addr.language || 'EN';
            });
        }

        if (orgCode) {
            const orgName = form.value.name || orgCode;
            const tablesWithOrgFk = [
                'contact_group_list', 'contact_group_mapping_list',
                'company_list', 'warehouse_config_list', 'document_delivery_config_list',
                'consignee_mapping_list', 'consignor_mapping_list',
                'consignee_defaults_list', 'consignor_config_list',
                'consignor_default_document_list', 'consignor_transport_country_doc_list',
                'transport_config_list', 'transport_mapping_list', 'receiving_warehouse_config_list'
            ];

            tablesWithOrgFk.forEach(tableName => {
                if (payload[tableName] && Array.isArray(payload[tableName])) {
                    payload[tableName].forEach((row: any) => {
                        row.org_fk = orgName;
                        delete row.idx;
                    });
                }
            });
        }

        const multiSelectTables = ['consignor_default_document_list', 'consignor_transport_country_doc_list'];
        multiSelectTables.forEach(tableName => {
            if (payload[tableName] && Array.isArray(payload[tableName])) {
                payload[tableName].forEach((row: any) => {
                    if (Array.isArray(row.document_type)) {
                        row.document_type = row.document_type.join(',');
                    }
                });
            }
        });

        let result: any = null;
        if (form.value.name) {
            result = await masterDataService.updateOrganization(payload.name, payload);
            toast.add({ severity: 'success', summary: 'Success', detail: 'Organization Updated', life: 3000 });
        } else {
            result = await masterDataService.createOrganization(payload);
            toast.add({ severity: 'success', summary: 'Successful', detail: 'Organization Created', life: 3000 });
        }

        if (result) {
            syncFromBackend(result);
        }
        emit('saved', form.value);
        return true;
    } catch (error: any) {
        console.error('Save error:', error);
        if (error.response?.status === 409) {
            toast.add({ severity: 'error', summary: 'Version Conflict', detail: 'This document has been modified by another user. Please reload and try again.', life: 5000 });
        } else {
            toast.add({ severity: 'error', summary: 'Error', detail: extractErrorMessage(error), life: 5000 });
        }
        return false;
    } finally {
        isLoading.value = false;
    }
};

const syncFromBackend = (doc: any) => {
    Object.assign(form.value, doc);
    
    // Boolean conversions
    const booleanFields = [
        'is_fleet_vendor', 'enable_org_code', 'is_active', 'is_valid', 'auto_so_confirm',
        'is_custom_filing_by_branch', 'is_custom_filing_by_dna', 'pickup_service_default', 'export_clearance_service_default',
        'eft_customs_from_importer_account', 'is_po_mandatory', 'is_orderline_processing', 'is_eft_required', 
        'is_eft_3_step_approval_required', 'is_update_container_priority_task_required', 'show_ar_invoice_documents', 
        'enable_org_code', 'is_active', 'is_custom_filing_by_branch', 'is_custom_filing_by_dna',
        'pickup_service_default', 'export_clearance_service_default', 'eft_customs_from_importer_account',
        'is_po_mandatory', 'is_orderline_processing', 'is_eft_required', 'is_eft_3_step_approval_required',
        'is_update_container_priority_task_required', 'show_ar_invoice_documents', 'is_re_approval_needed',
        'is_booking_approval_mandatory', 'user_discretion_booking', 'enable_bcn_consol_approval',
        'booking_approval_to_buyer', 'booking_approval_to_destination_cs', 'is_po_approval_required',
        'order_approval_to_buyer', 'order_approval_to_destination_cs', 'delivery_service_default',
        'import_clearance_service_default', 'multi_client_configuration', 'manifest_accrual_restriction_for_transporter',
        'manifest_creation_restriction_for_transporter', 'disable_payment_visibility', 'use_packing_date',
        'package_dimension', 'use_expiry_date', 'product_dimension', 'putaway_same_product_together',
        'overriding_system_setting', 'is_asn_mandatory', 'update_dispatch_information', 'edi_inward_gate_pass', 
        'enable_split_po', 'enabled_email_validation', 'disable_generate_wms_lrnumber', 'enable_scan_all',
        'enable_inward_invoice_value', 'enable_so_consolidation', 'enable_double_scanning_for_client',
        'release_capture_bulkoption', 'update_grn_in_client_system', 'edi_client_restriction',
        'additional_reference_config', 'enable_return_goods_grn', 'enable_pick_completion_validation',
        'enabled_mobile_number_validation', 'enable_order_number_length_capacity', 'enable_reverse_pickup',
        'enable_dimension_for_outward', 'disable_release_capture_scanning_mtr', 'update_invoice_information',
        'enable_shuttle_method', 'update_invoice_from_client_system', 'enable_direct_invoicing',
        'edi_client_enable_line_no_editable', 'enabled_email_and_mobile_no_validation',
        'enable_pick_confirmation_after_load_complete_edi', 'enable_release_captured_product_scanning_in_inward',
        'enable_outward_invoice_value', 'enable_split_pick', 'enable_auto_acp', 'by_pass_invoice_document',
        'is_fleet_vendor', 'auto_so_confirm',
        ...orgTypes.map(c => c.field),
        ...additionalOrgTypes.map(c => c.field)
    ];
    booleanFields.forEach(field => {
        if (form.value[field] !== undefined) form.value[field] = !!form.value[field];
    });

    const childBooleanFields: Record<string, string[]> = {
        'address_list': ['is_active'],
        'time_table_list': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        'contact_list': ['is_active', 'is_primary_contact'],
        'company_list': ['is_default', 'is_active', 'is_debtor', 'is_creditor'],
        'employee_list': ['is_active'],
        'related_party_list': ['is_active'],
        'consignee_mapping_list': ['is_default'],
        'consignor_mapping_list': ['is_default'],
        'consignor_config_list': ['authority_to_leave', 'transfer_related', 'first_ship'],
        'transport_config_list': ['is_active'],
        'transport_mapping_list': ['is_active', 'is_default']
    };

    const multiSelectTables = ['consignor_default_document_list', 'consignor_transport_country_doc_list'];

    Object.keys(childBooleanFields).forEach(listName => {
        if (form.value[listName] && Array.isArray(form.value[listName])) {
            const fields = childBooleanFields[listName];
            form.value[listName].forEach((row: any, index: number) => {
                row.idx = index + 1;
                fields.forEach(f => { if (row[f] !== undefined) row[f] = !!row[f]; });
                if (multiSelectTables.includes(listName) && typeof row.document_type === 'string') {
                    row.document_type = row.document_type ? row.document_type.split(',') : [];
                }
            });
        }
    });

    if (form.value.time_table_list) {
        form.value.time_table_list.forEach((row: any) => {
            if (row.time_from && typeof row.time_from === 'string' && row.time_from.includes(':')) {
                const [h, m, s] = row.time_from.split(':').map(Number);
                const d = new Date(); d.setHours(h, m, s || 0); row.time_from = d;
            }
            if (row.time_to && typeof row.time_to === 'string' && row.time_to.includes(':')) {
                const [h, m, s] = row.time_to.split(':').map(Number);
                const d = new Date(); d.setHours(h, m, s || 0); row.time_to = d;
            }
        });
    }

    if (form.value.reference_list) {
        form.value.reference_list.forEach((row: any) => {
            ['available_from', 'available_to', 'start_date', 'end_date'].forEach(f => {
                if (row[f]) { const d = new Date(row[f]); if (!isNaN(d.getTime())) row[f] = d; }
            });
        });
    }
};

const onSaveAndClose = async () => {
    const success = await onSave();
    if (success) {
        emit('close');
    }
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
    { label: 'Save', severity: 'primary' as const, command: onSave, disabled: !canWrite.value, loading: isLoading.value }
]);

const showCommentModal = ref(false);
const showDocumentModal = ref(false);
const showEmailModal = ref(false);
const showExceptionModal = ref(false);

const handleFooterAction = (actionId: string) => {
    if (actionId === 'comment') showCommentModal.value = true;
    else if (actionId === 'document') showDocumentModal.value = true;
    else if (actionId === 'email') showEmailModal.value = true;
    else if (actionId === 'exception') showExceptionModal.value = true;
};

watch(showDocumentModal, (newVal) => { if (!newVal) fetchDocumentCount(); });
watch(showCommentModal, (newVal) => { if (!newVal) fetchCommentCount(); });

const generateOrganizationCode = () => {
    if (form.value.enable_org_code || !form.value.full_name || !form.value.oad_related_port_code) return;
    try {
        let fullName = form.value.full_name.replace(/[^0-9.a-zA-Z\s]/g, "").replace(/\s+/g, ' ').trim();
        let words = fullName.split(" ");
        let prefix = words.length >= 2 ? (words[0].substring(0, 3) + words[1].substring(0, 3)).toUpperCase() : words[0].substring(0, 6).toUpperCase();
        let suffix = form.value.oad_related_port_code.toUpperCase();
        form.value.code = prefix + suffix;
    } catch (error) { console.error("Error generating organization code:", error); }
};

watch(() => [form.value.full_name, form.value.oad_related_port_code, form.value.enable_org_code], () => {
    if (!form.value.enable_org_code) generateOrganizationCode();
});

watch(() => form.value.code, (newVal: string) => {
    if (newVal) form.value.code = newVal.toUpperCase();
});

const initializeForm = async () => {
    if (props.initialData && (props.initialData.name || props.initialData.code)) {
        const docId = props.initialData.name || props.initialData.code;
        
        // Skip API call if this is a new record placeholder
        if (docId === 'new') {
            console.log('[OrganizationForm] New record mode - skipping fetch');
            [...orgTypes, ...additionalOrgTypes].forEach(c => { form.value[c.field] = false; });
            return;
        }

        try {
            isLoading.value = true;
            const fullDoc = await masterDataService.getOrganization(docId);
            if (fullDoc) {
                syncFromBackend(fullDoc);
                fetchDocumentCount();
                fetchCommentCount();
            }
        } catch (error) {
            console.error('Error loading organization:', error);
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load organization details', life: 3000 });
        } finally {
            isLoading.value = false;
        }
    } else {
        // Create Mode - initialize boolean defaults
        [...orgTypes, ...additionalOrgTypes].forEach(c => { form.value[c.field] = false; });
    }
};

onMounted(async () => {
    try {
        const [countries, unlocos] = await Promise.all([
            masterDataService.getCountries(),
            masterDataService.getUnlocos(),
            initializeForm()
        ]);
        countryList.value = countries.map((c: any) => ({ label: c.description, value: c.name }));
        portList.value = unlocos.map((p: any) => ({ label: `${p.port_name} (${p.code})`, value: p.name }));
        if (form.value.oad_country_code) await onCountryChange();
        if (form.value.oad_state) await onStateChange();
    } catch (error) { console.error('Error loading master data drops:', error); }
});

</script>

<template>
    <div class="flex flex-col h-full border border-0.25 border-surface-300">
        <!-- Header -->
        

        <!-- Horizontal Tabs -->
        <div class="sticky top-[48px] z-[900] bg-surface-0 dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700">
            <CommonTabs :key="form.name || form.code || 'new-org'" :items="menuItems" v-model="activeTab" />
        </div>

        <!-- Content Body -->
        <div class="flex-1 overflow-y-auto p-4 bg-surface-50 dark:bg-surface-950">
            <div v-show="activeTab === 'General'" class="space-y-4 w-full">
                <div class="card p-2 md:p-4 space-y-2 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900">
                    <CommonHeading text="Basic Information" level="2" icon="pi pi-id-card" />
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <CommonField label="Organization Code" v-model="form.code" :required="form.enable_org_code" :error="validationErrors.code" :disabled="!form.enable_org_code"  />  
                        <CommonField label="Organization Name" v-model="form.full_name" required :error="validationErrors.full_name"  />
                        <div class="flex flex-col gap-4 pt-2">
                           <CommonField type="checkbox" label="Enable Organization Code" v-model="form.enable_org_code"  />
                            <div class="flex gap-4">
                                <CommonField type="checkbox" label="Is Active" v-model="form.is_active" />
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card p-2 md:p-4 space-y-2 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900">
                    <CommonHeading text="Organization Types" level="2" icon="pi pi-tags" :error="validationErrors.org_types" />
                    <p class="text-surface-500 mb-2 text-xs">Select all applicable organization types. At least one type is required.</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
                        <div v-for="type in orgTypes" :key="type.field">
                            <CommonField type="checkbox" :label="type.label" v-model="form[type.field]"  />
                        </div>
                    </div>
                </div>
                <div class="card p-2 md:p-6 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900">
                    <Panel toggleable collapsed class="custom-panel no-padding">
                        <template #header>
                            <div class="flex items-center gap-2">
                                 <CommonHeading text="Additional Organization Types" level="2" icon="pi pi-plus-circle" />
                                <span class="text-xs text-surface-500 font-normal ml-2 mb-2">(Optional)</span>
                            </div>
                        </template>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4 pt-2">
                             <div v-for="type in additionalOrgTypes" :key="type.field">
                                <CommonField type="checkbox" :label="type.label" v-model="form[type.field]"  />
                            </div>
                        </div>
                    </Panel>
                </div>
                <div class="card p-2 md:p-6 space-y-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900">
                    <CommonHeading text="Primary Address" level="2" icon="pi pi-map-marker" />
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        <CommonField label="Address Line 1" v-model="form.oad_address1" required :error="validationErrors.oad_address1" />
                        <CommonField label="Address Line 2" v-model="form.oad_address2" />
                        <CommonField type="select" label="Country" v-model="form.oad_country_code" :options="countryList" required :error="validationErrors.oad_country_code" @change="onCountryChange" />
                        <CommonField type="select" label="State" v-model="form.oad_state" :options="stateList" required :error="validationErrors.oad_state" @change="onStateChange" />
                        <CommonField type="select" label="City" v-model="form.oad_city" :options="cityList" required :error="validationErrors.oad_city" />
                        <CommonField label="Post Code" v-model="form.oad_post_code" required :error="validationErrors.oad_post_code" @blur="onPostCodeBlur" />
                        <CommonField type="select" label="Related Port" v-model="form.oad_related_port_code" :options="portList" required :error="validationErrors.oad_related_port_code" />
                        <CommonField label="Phone" v-model="form.oad_phone" :error="validationErrors.oad_phone" />
                        <CommonField label="Mobile" v-model="form.oad_mobile" :error="validationErrors.oad_mobile" />
                        <CommonField label="Fax" v-model="form.oad_fax" />
                        <CommonField label="Email" v-model="form.oad_email" :error="validationErrors.oad_email" />
                        <CommonField type="select" label="Language" v-model="form.language" :options="languages" required :error="validationErrors.language" />
                        <CommonField label="Latitude" v-model="form.oad_latitude" />
                        <CommonField label="Longitude" v-model="form.oad_longitude" />
                    </div>
                </div>
                <div class="card p-2 md:p-6 border border-surface-200 dark:border-surface-700 rounded-xl bg-surface-0 dark:bg-surface-900">
                    <Panel toggleable collapsed class="custom-panel no-padding">
                        <template #header>
                            <div class="flex items-center gap-2">
                                <CommonHeading text="Site Information" level="2" icon="pi pi-building" />
                            </div>
                        </template>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                            <CommonField label="Site ID" v-model="form.site_id" />
                            <CommonField label="External Site ID" v-model="form.external_site_id" />
                            <CommonField label="Site Name" v-model="form.site_name" />
                            <CommonField label="GST No" v-model="form.gst_no" />
                        </div>
                    </Panel>
                </div>
            </div>

            <div :key="'tab-Address'" v-show="activeTab === 'Address'"><OrganizationAddress v-model:addressList="form.address_list" v-model:timeTable="form.time_table_list" v-model:deliveryInstructions="form.loading_unloading_constraints" :cityList="cityList" /></div>
            <div :key="'tab-Contact'" v-show="activeTab === 'Contact'"><OrganizationContact v-model:contactList="form.contact_list" v-model:contactGroups="form.contact_group_list" v-model:contactGroupMappings="form.contact_group_mapping_list" :addressList="form.address_list" /></div>
            <div :key="'tab-Company'" v-show="activeTab === 'Company'"><OrganizationCompany v-model:companyList="form.company_list" /></div>
            <div :key="'tab-Employee'" v-show="activeTab === 'Employee'"><OrganizationEmployee v-model:employeeAssignments="form.employee_list" /></div>
            <div :key="'tab-RelatedParties'" v-show="activeTab === 'Related Parties'"><OrganizationRelatedParties v-model="form.related_party_list" /></div>
            <div :key="'tab-Reference'" v-show="activeTab === 'Reference'"><OrganizationReference v-model="form.reference_list" /></div>
            <div :key="'tab-Transport'" v-show="activeTab === 'Transport'"><OrganizationTransport :form="form" /></div>
            <div :key="'tab-Warehouse'" v-show="activeTab === 'Warehouse'"><OrganizationWarehouse :form="form" /></div>
            <div :key="'tab-Consignee'" v-show="activeTab === 'Consignee'"><OrganizationConsignee :form="form" /></div>
            <div :key="'tab-Consignor'" v-show="activeTab === 'Consignor'"><OrganizationConsignor :form="form" /></div>
            <div :key="'tab-Configuration'" v-show="activeTab === 'Configuration'"><OrganizationConfiguration :form="form" /></div>
        </div>
        
        <FormFooter :leftActions="footerLeftActions" :actions="footerActions" @action-click="handleFooterAction" />

        <CommonCommentModal v-model:visible="showCommentModal" doctype="MDM Org Header" :docname="form.name || form.code || ''" />
        <CommonDocumentModal v-model:visible="showDocumentModal" doctype="MDM Org Header" :docname="form.name || form.code || ''" />
        <CommonEmailModal v-model:visible="showEmailModal" doctype="MDM Org Header" :docname="form.name || form.code || ''" />
        <CommonExceptionModal v-model:visible="showExceptionModal" doctype="MDM Org Header" :docname="form.name || form.code || ''" />
    </div>
</template>

<style scoped>
:deep(.custom-panel .p-panel-header) { background: transparent; border: none; padding: 0; margin-bottom: 1rem; }
:deep(.custom-panel .p-panel-content) { border: none; padding: 0; }
:deep(.custom-panel) { background: #ffffff; border: 1px solid var(--p-surface-200); border-radius: var(--p-border-radius); padding: 1.25rem; }
:deep(.dark .custom-panel) { background: var(--p-surface-900); border-color: var(--p-surface-700); }
:deep(.custom-panel.no-padding) { background: transparent; border: none; padding: 0; }
:deep(.dark .custom-panel.no-padding) { background: transparent; border-color: transparent; }
</style>
