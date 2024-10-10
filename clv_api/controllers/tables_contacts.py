from typing import List
from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from odoo.api import Environment


class TableContactsProcessor(TableProcessorBase):
    """
    Processes Contacts table requests.
    The structure of the TableContactsRow is:
    id:
        type: string
        description: Unique identifier for the partner.
    street1:
        type: string
        description: Primary street address of the partner.
    street2:
        type: string
        description: Secondary street address of the partner.
    city:
        type: string
        description: City where the partner is located.
    state:
        type: string
        description: State where the partner is located.
    country:
        type: string
        description: Country where the partner is located.
    countryCode:
        type: string
        description: Code of country where the partner is located.
    zip:
        type: string
        description: ZIP or postal code of the partner's address.
    phone:
        type: string
        description: Contact phone number of the partner.
    email:
        type: string
        description: Contact email address of the partner.
    isCompany:
        type: boolean
        description: Indicates if the partner is a company.
    addressType:
        type: string
        description: Type or category of the partner ('contact', 'invoice', 'delivery', 'other').
    """

    _mapping_fields : List[FieldInfo] = [
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='street1', api_type_arg=str, odoo_name_arg='street', odoo_type_arg=str),
        FieldInfo(api_name_arg='street2', api_type_arg=str, odoo_name_arg='street2', odoo_type_arg=str),
        FieldInfo(api_name_arg='city', api_type_arg=str, odoo_name_arg='city', odoo_type_arg=str),
        FieldInfo(api_name_arg='state', api_type_arg=str, odoo_name_arg='state_id.name', odoo_type_arg=str),
        FieldInfo(api_name_arg='country', api_type_arg=str, odoo_name_arg='country_id.name', odoo_type_arg=str),
        FieldInfo(api_name_arg='countrycode', api_type_arg=str, odoo_name_arg='country_code', odoo_type_arg=str),
        FieldInfo(api_name_arg='zip', api_type_arg=str, odoo_name_arg='zip', odoo_type_arg=str),
        FieldInfo(api_name_arg='phone', api_type_arg=str, odoo_name_arg='phone', odoo_type_arg=str),
        FieldInfo(api_name_arg='email', api_type_arg=str, odoo_name_arg='email', odoo_type_arg=str),
        FieldInfo(api_name_arg='iscompany', api_type_arg=bool, odoo_name_arg='is_company', odoo_type_arg=bool),
        FieldInfo(api_name_arg='addresstype', api_type_arg=str, odoo_name_arg='type', odoo_type_arg=str)
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool) -> List:
        where_root = query.get('whereTreeRoot')

        domain_filter = [('active', '=', True), ('is_blacklisted', '=', False)]

        if where_root:
            additional_field = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            domain_filter.extend(additional_field)

        if request_count:
            contacts_count = env['res.partner'].search_count(domain_filter)
            return [contacts_count, None]

        partners = env['res.partner'].search(domain_filter, limit=limit, offset=offset, order='id ASC')

        contacts = []
        for partner in partners:
            contact = self._convert_odoo_partner_to_contact(partner)
            contacts.append(contact)

        return [None, contacts]

    def _convert_odoo_partner_to_contact(self, partner):
        return {
            'id': self._model_converter.clear_to_str(partner.id),
            'street1': self._model_converter.clear_to_str(partner.street),
            'street2': self._model_converter.clear_to_str(partner.street2),
            'city': self._model_converter.clear_to_str(partner.city),
            'state': self._model_converter.clear_to_str(partner.state_id.name),
            'country': self._model_converter.clear_to_str(partner.country_id.name),
            'countryCode': self._model_converter.clear_to_str(partner.country_code),
            'zip': self._model_converter.clear_to_str(partner.zip),
            'phone': self._model_converter.clear_to_str(partner.phone_sanitized),
            'email': self._model_converter.clear_to_str(partner.email_normalized),
            'isCompany': partner.is_company,
            'addressType': self._model_converter.clear_to_str(partner.type)
        }
