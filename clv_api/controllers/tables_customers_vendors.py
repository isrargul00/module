from typing import List

from odoo.api import Environment
from .field_info import FieldInfo
from .tables_base import TableProcessorBase


class TableCustomersVendorsProcessor(TableProcessorBase):
    """
    Processes requests to CustomersVendors table.
    The structure of the TableCustomersVendorsRow is:
    barcode:
        type: string
        description: Customer or vendor barcode.
    code:
        type: string
        description: ???
    id:
        type: string
        description: Customer or vendor identifier. Primary key.
    isFolder:
        type: boolean
        description: ???
    name:
        type: string
        description: Customer or vendor name.
    parentId:
        type: string
        description: Customer or vendor group identifier.
    search:
        type: string
        description: Concatenated data in a lower case for searching.
    tIN:
        type: string
        description: Customer or vendor 'Taxpayer Identification Number' or 'Individual Taxpayer Number'.
    type:
        type: string
        description: Customer or vendor filter.
    """

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='barcode', api_type_arg=str, odoo_name_arg='barcode', odoo_type_arg=str),
        FieldInfo(api_name_arg='code', api_type_arg=str, odoo_name_arg='ref', odoo_type_arg=str),
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='isFolder'.lower(), api_type_arg=bool, odoo_name_arg='is_folder', odoo_type_arg=bool),
        FieldInfo(api_name_arg='name', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='parentId'.lower(), api_type_arg=str, odoo_name_arg='parent_id', odoo_type_arg=str),
        FieldInfo(api_name_arg='tin', api_type_arg=str, odoo_name_arg='vat', odoo_type_arg=str),
        FieldInfo(api_name_arg='type', api_type_arg=str, odoo_name_arg='type', odoo_type_arg=str)
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool) -> List:
        where_root = query.get('whereTreeRoot')

        domain_filter = [('active', '=', True)]

        if where_root:
            additional_filter = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            additional_filter = self._modify_domain_query(env, additional_filter)
            domain_filter.extend(additional_filter)

        if request_count:
            customers_vendors_count = env['res.partner'].search_count(domain_filter)
            return [customers_vendors_count, None]

        partners = env['res.partner'].search(domain_filter, limit=limit, offset=offset, order='id ASC')

        customers_vendors = []
        for partner in partners:
            customers_vendors.append(self._model_converter.convert_odoo_partner_to_customers_vendors_row(partner))

        return [None, customers_vendors]

    # noinspection PyMethodMayBeStatic
    def _modify_domain_query(self, env, domain_filter):
        result = []
        for origin_field_filter in domain_filter:
            modified_field_filter = origin_field_filter
            if isinstance(origin_field_filter, tuple):
                field_name = origin_field_filter[0]
                if field_name == 'barcode':
                    modified_field_filter = self._modify_barcode_field_filter(env, origin_field_filter)
                elif field_name == 'is_folder':
                    modified_field_filter = self._modify_is_folder_field_filter(env, origin_field_filter)
                elif field_name == 'parent_id':
                    modified_field_filter = self._modify_parent_id_field_filter(env, origin_field_filter)
                elif field_name == 'ref':
                    modified_field_filter = self._modify_ref_field_filter(env, origin_field_filter)
                elif field_name == 'type':
                    modified_field_filter = self._modify_type_field_filter(env, origin_field_filter)
                elif field_name == 'vat':
                    modified_field_filter = self._modify_vat_field_filter(env, origin_field_filter)

            result.append(modified_field_filter)

        return result

    # noinspection PyMethodMayBeStatic
    def _modify_barcode_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_is_folder_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('child_ids', '=' if (origin_filter[1] == '=') ^ origin_filter[2] else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_parent_id_field_filter(self, env, origin_filter):
        if origin_filter[2] is None or origin_filter[2] == '':
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], False)
        if origin_filter[2].isdigit():
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], int(origin_filter[2]))
        # noinspection PyRedundantParentheses
        return ('id', '=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_ref_field_filter(self, env, origin_filter):
        if 'ref' in env['res.partner']:
            if origin_filter[2] is None or origin_filter[2] == '':
                # noinspection PyRedundantParentheses
                return (origin_filter[0], origin_filter[1], False)
            return origin_filter
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_type_field_filter(self, env, origin_filter):
        # There is no strict difference between customer and vendor in Odoo
        # but partner object has 'supplier_rank' and 'customer_rank' (only if Sales module installed)
        # which depend on amount of bills or invoices for this partner.
        # We consider a partner to be a customer if 'customer_rank' is greater than 'supplier_rank'
        # and consider a partner to be a vendor if 'supplier_rank' is greater than 'customer_rank'.
        # In all other cases, the type is not assigned.
        # To provide filtering by 'type' field, we use an additional query to 'res.partner' table.
        # Direct SQL-request is using to improve performance.

        if not ('customer_rank' in env['res.partner'] and 'supplier_rank' in env['res.partner']):
            # noinspection PyRedundantParentheses
            return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

        operator = origin_filter[1]
        value = origin_filter[2]

        query = f"""
                    SELECT id
                    FROM res_partner
                    WHERE
                    CASE
                        WHEN customer_rank > supplier_rank THEN 'customer'
                        WHEN supplier_rank > customer_rank THEN 'vendor'
                        ELSE ''
                    END {operator} '{value}'
                """
        env.cr.execute(query)
        partners = env.cr.fetchall()
        ids = [partner[0] for partner in partners]

        # noinspection PyRedundantParentheses
        return ('id', 'in', ids)

    # noinspection PyMethodMayBeStatic
    def _modify_vat_field_filter(self, env, origin_filter):
        if origin_filter[2] is None or origin_filter[2] == '':
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], False)
        return origin_filter
