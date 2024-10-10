import uuid

from datetime import datetime
from typing import List, Union

from odoo.api import Environment
from odoo.release import version_info
from .document_type_info import DocumentTypeInfo, BusinessLocationType


class CommonUtils:
    """
    Regular util functions
    """

    """Documents description lists"""
    document_types = [
        DocumentTypeInfo("IN", "Receiving", BusinessLocationType.DEST, True, True, True, False),
        DocumentTypeInfo("INT", "Allocation", BusinessLocationType.DEST, False, False, True, True),
        DocumentTypeInfo("PICK", "Pick", BusinessLocationType.SRC, False, False, True, False),
        DocumentTypeInfo("OUT", "Ship", BusinessLocationType.SRC, True, False, False, False)
    ]

    def get_stock_lot_env_name(self):
        """
        Returns environment stock lot entity name
        @return:
        """
        if version_info[0] >= 16:
            return 'stock.lot'
        return 'stock.production.lot'

    def get_document_type_info_by_document(self, pick_doc) -> DocumentTypeInfo:
        """
        Returns DocumentTypeInfo description of the odoo document. None if not found
        @param pick_doc: stock.picking document
        @return: DocumentTypeInfo object describes passing odoo stock picking document
        """
        if not pick_doc:
            return None
        for doc_type in CommonUtils.document_types:
            if doc_type.odoo_sequence_code == pick_doc.picking_type_id.sequence_code:
                return doc_type
        return None

    def get_location_parent_path_from_document(self, pick_doc):
        """
        Returns path to the parent location of the document location

        @param pick_doc: stock.picking document
        @return: None is it is impossible to determine valid parent path
                location or string with parent path defined in the current document
        """
        doc_type = self.get_document_type_info_by_document(pick_doc)
        if not doc_type:
            return None

        if doc_type.main_location_type == BusinessLocationType.DEST:
            return pick_doc.location_dest_id.parent_path
        return pick_doc.location_id.parent_path

    def append_company_filter_by_doc(self, domain, odoo_doc):
        """
        Appends document's company filter to the domain query
        @param domain: domain filter list
        @param odoo_doc: stock picking odoo document
        """
        if odoo_doc:
            self.append_company_filter(domain, odoo_doc.company_id.id)

    def append_company_filter(self, domain, company_id):
        """
        Appends company filter to the domain query
        @param domain: domain filter list
        @param company_id: id of the company
        """
        if company_id:
            domain.append(('company_id', '=?', company_id))

    def get_warehouse_route_steps_by_doc(self, env: Environment, odoo_doc):
        """
        Returns string with routing scheme corresponds to this document (warehouse)
        @param env: Environment
        @param odoo_doc: stock.picking odoo document
        @return: string with warehouse route
        """
        document_warehouse = self.get_document_warehouse(env, odoo_doc)
        if not document_warehouse:
            # raise RuntimeError('No warehouse found for the document')
            # In case of document has a virtual destination location then there is no warehouse.
            # So route steps is empty.
            return None

        doc_type = self.get_document_type_info_by_document(odoo_doc)
        if not doc_type:
            raise RuntimeError('Not supported document type')

        if doc_type.main_location_type == BusinessLocationType.DEST:
            return document_warehouse.reception_steps
        return document_warehouse.delivery_steps

    def get_doc_main_location(self, odoo_doc):
        """
        Returns effective document location
        @param odoo_doc: stock.oicking odoo document
        @return: location object ofthe document depends on its type (IN/INT/PICK/SHIP/...)
        """
        doc_type = self.get_document_type_info_by_document(odoo_doc)
        if not doc_type:
            return False
        doc_location = odoo_doc.location_id
        if doc_type.main_location_type == BusinessLocationType.DEST:
            doc_location = odoo_doc.location_dest_id
        return doc_location[0]

    def get_document_warehouse(self, env: Environment, odoo_doc):
        """
        Returns document's warehouse orm object
        @param env: Environment
        @param odoo_doc: stock.picking odoo doc
        @return: stock.warehouse objects which coresponds to the document's source location
        """
        doc_type = self.get_document_type_info_by_document(odoo_doc)
        if not doc_type:
            raise RuntimeError('Not supported document type')

        doc_location = self.get_doc_main_location(odoo_doc).parent_path

        # lookup for the second level
        parent_ids = doc_location.split('/')
        if len(parent_ids) < 2:
            raise RuntimeError('Invalid warehouse location in document')
        location_id = int(parent_ids[1])
        wh_location = env['stock.location'].search([('id', '=', location_id)])
        if not wh_location:
            raise RuntimeError('Invalid warehouse location in document')
        wh_code_name = wh_location.name
        finded_wh = env['stock.warehouse'].search([('code', '=', wh_code_name)])
        if not finded_wh:
            return None
        return finded_wh[0]

    def get_odoo_doc_from_device_info(self, env: Environment, device_info):
        """
        Returns odoo document from device info
        @param env: Environment
        @param device_info: DeviceInfo dictionary passed to INventoryAPI call
        @return: Found odoo document object or None if not found
        """
        document_id = device_info.get('documentId')
        if not document_id or not document_id.isdigit():
            return None

        document_type = device_info.get('documentTypeName')

        docs = []
        if document_type and document_type.lower() == 'stocktaking':
            return None
        else:
            docs = env['stock.picking'].search([('id', '=', int(document_id))])
        if not docs or len(docs) != 1:
            return None
        return docs[0]

    def create_random_fake_serial_number(self):
        """
        Creates random serial number
        @return:
        """
        return 'clv_fake_' + str(uuid.uuid4())

    def is_fake_serial_number(self, serial_number) -> bool:
        """
        Determines if passed string is fake serial number generated by InventoryAPI odoo module
        @param serial_number: testing serial number string
        @return:
        """
        if not serial_number or len(serial_number) < 9:
            return False
        return serial_number[0:9] == 'clv_fake_'

    @staticmethod
    def create_or_update_connected_database_info(env: Environment, database_info):
        """
        Creates or updates information about connected Cleverence's database.
        """

        database_id = database_info.get('database_id', 'UNKNOWN_ID')
        already_connected_db = env['clv_api.connected_database_info'].search([('database_id', '=', database_id)])

        values = {
            'database_name': database_info.get('database_name', 'UNKNOWN_DATABASE_NAME'),
            'web_app_url': database_info.get('web_app_url', 'UNKNOWN_WEB_APP_URL'),
            'installation_type': database_info.get('installation_type', 'UNKNOWN_INSTALLATION_TYPE'),
            'last_data_exchange_time': datetime.now(),
            'cleverence_user_login': database_info.get('cleverence_user_login', 'UNKNOWN_CLEVERENCE_USER_LOGIN')
        }

        if already_connected_db:
            already_connected_db.write(values)
        else:
            values['database_id'] = database_id
            env['clv_api.connected_database_info'].create(values)

    @staticmethod
    def is_storage_locations_enabled(env: Environment) -> bool:
        """
        Determines if storage locations is enabled in Odoo 'stock' (Inventory) module.
        """
        # 'stock' (Inventory) module allows enabling and disabling storage locations tracking.
        # Here's a tricky way to define if storage locations enabled.
        return env.user.has_group('stock.group_stock_multi_locations')

    @staticmethod
    def convert_warehouse_id_from_clv_to_odoo(warehouse_id: str) -> int:
        """
        Converts Cleverence warehouse id to Odoo warehouse id.
        Uses
        """
        return int(warehouse_id.removeprefix('clv_wh_'))

    @staticmethod
    def convert_warehouse_id_from_odoo_to_clv(warehouse_id: int) -> str:
        """
        Converts Odoo warehouse id to Cleverence warehouse id.
        """
        return f'clv_wh_{warehouse_id}'

    @staticmethod
    def generate_search_string(values: List[Union[bool, str, int, float, datetime]]) -> str:
        """
        Generates a search string by concatenating all non-None and non-empty input values,
        separated by a single space, with all characters converted to lowercase.
        """
        cleared_values = []
        for value in values:
            if value is not None and value != '':
                if isinstance(value, datetime):
                    cleared_values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    cleared_values.append(str(value).lower())

        return ' '.join(cleared_values)
