import datetime
import logging
from typing import Union

from odoo.api import Environment

from .clv_settings_provider import ClvSettingsProvider
from .model_converter import ModelConverter
from .common_utils import CommonUtils
from .documents_utils import DocumentsUtils


class DocumentStockTakingImpl:
    """
    Implements the processing of stock taking documents.
    """
    _model_converter = ModelConverter()
    _cutils = CommonUtils()
    _logger = logging.getLogger(__name__)

    def get_descriptions(
            self,
            env: Environment,
            document_type_name: str,
            offset: Union[int, None],
            limit: Union[int, None],
            request_count: Union[bool, None]):

        result = {}
        if request_count:
            result['totalCount'] = self._get_inv_adj_doc_descriptions_count(env)
            return result

        result['result'] = self._generate_inv_adj_doc_descriptions(env)

        return result

    def get_document(
            self,
            env: Environment,
            search_mode: str,
            search_code: str,
            document_type_name: str):

        warehouse_id = CommonUtils.convert_warehouse_id_from_clv_to_odoo(search_code)

        found_warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True),
            ('id', '=', warehouse_id)
        ])

        if found_warehouses and len(found_warehouses) > 0:
            warehouse = found_warehouses[0]
            return self._generate_inv_adj_doc(warehouse, env)

        return None

    def set_document(self, env: Environment, doc, device_info):
        if doc is None:
            raise RuntimeError('Document is null')

        # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
        warehouse_id = doc.get('warehouseId', '') or doc.get('warehouseExternalId', '')
        if not warehouse_id:
            raise RuntimeError('Warehouse is not specified')

        warehouse_id = CommonUtils.convert_warehouse_id_from_clv_to_odoo(warehouse_id)
        found_warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True),
            ('id', '=', warehouse_id)
        ])
        if not found_warehouses or len(found_warehouses) == 0:
            raise RuntimeError('Unknown or inactive warehouse id')

        warehouse = found_warehouses[0]
        return self._set_inv_adj_doc(doc, device_info, warehouse, env)

    def _get_inv_adj_doc_descriptions_count(self, env: Environment) -> int:
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        # So, count of inventory adjustment documents is equal to warehouse count.
        return env['stock.warehouse'].searc_count([
            ('active', '=', True),
            ('company_id.active', '=', True)
        ])

    def _generate_inv_adj_doc_descriptions(self, env: Environment):
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        descriptions = []

        warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True)
        ])

        for warehouse in warehouses:
            scan_locations = CommonUtils.is_storage_locations_enabled(env) \
                             and bool(warehouse.lot_stock_id.child_ids) \
                             and ClvSettingsProvider(env).default_scan_locations

            modified_warehouse_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id)

            inv_adj_doc = {
                'id': self._model_converter.clear_to_str(warehouse.id),
                'name': 'Full inventory adjustment',
                'documentTypeName': 'StockTaking',
                'distributeByBarcode': True,
                'autoAppointed': False,
                'scanLocations': scan_locations,
                # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
                'warehouseExternalId': self._model_converter.clear_to_str(modified_warehouse_id),
                'warehouseId': self._model_converter.clear_to_str(modified_warehouse_id),
                'warehouseName': self._model_converter.clear_to_str(warehouse.name),
                'sourceDocumentType': 'StockTaking'
            }
            descriptions.append(inv_adj_doc)

        return descriptions

    def _generate_inv_adj_doc(self, warehouse, env: Environment):
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        scan_locations = CommonUtils.is_storage_locations_enabled(env) \
                         and bool(warehouse.lot_stock_id.child_ids) \
                         and ClvSettingsProvider(env).default_scan_locations

        modified_warehouse_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id)

        doc = {
            'id': self._model_converter.clear_to_str(warehouse.id),
            'name': 'Full inventory adjustment',
            'documentTypeName': 'StockTaking',
            'distributeByBarcode': True,
            'autoAppointed': False,
            'scanLocations': scan_locations,
            # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
            'warehouseExternalId': self._model_converter.clear_to_str(modified_warehouse_id),
            'warehouseId': self._model_converter.clear_to_str(modified_warehouse_id),
            'warehouseName': self._model_converter.clear_to_str(warehouse.name),
            'sourceDocumentType': 'StockTaking'
        }

        stock_quants = env['stock.quant'].search([
            ('warehouse_id', '=', warehouse.id),
            ('location_id.active', '=', True)
        ])

        expected_lines = []
        actual_lines = []

        for stock_quant in stock_quants:
            if stock_quant.quantity <= 0 and not stock_quant.inventory_quantity_set and stock_quant.inventory_quantity <= 0:
                continue

            expected_line = {
                'uid': self._model_converter.clear_to_str(stock_quant.id),
                'inventoryItemId': self._model_converter.clear_to_str(stock_quant.product_id.id),
                'expectedQuantity': self._model_converter.clear_to_str(stock_quant.quantity),
                'actualQuantity': self._model_converter.clear_to_str(stock_quant.inventory_quantity),
                'unitOfMeasureId': self._model_converter.clear_to_str(stock_quant.product_uom_id.id),
                'inventoryItemName': self._model_converter.clear_to_str(stock_quant.product_id.name),
                'inventoryItemBarcode': self._model_converter.clear_to_str(stock_quant.product_id.barcode),
                'unitOfMeasureName': self._model_converter.clear_to_str(stock_quant.product_uom_id.name),
                'registrationDate': str(),
                'documentId': self._model_converter.clear_to_str(doc['id']),
                'lastChangeDate': str(),
                'price': str(),
                'purchasePrice': str(),
                'sourceDocumentId': str(),
                'firstStorageId': self._model_converter.clear_to_str(stock_quant.location_id.id)
            }

            if stock_quant.tracking == 'serial':
                expected_line['serialNumber'] = self._model_converter.clear_to_str(stock_quant.lot_id.name)
            elif stock_quant.tracking == 'lot':
                expected_line['seriesId'] = self._model_converter.clear_to_str(stock_quant.lot_id.id)
                expected_line['seriesName'] = self._model_converter.clear_to_str(stock_quant.lot_id.name)

            expected_lines.append(expected_line)

        doc['expectedLines'] = expected_lines
        doc['actualLines'] = actual_lines

        return {'document': doc}

    def _set_inv_adj_doc(self, doc, device_info, warehouse, env: Environment):

        bp_settings = DocumentsUtils.extract_business_process_settings(doc)

        auto_apply_inventory_adjustment = False
        if bp_settings.get('AutoApplyInventoryAdjustment'):
            auto_apply_inventory_adjustment = str(bp_settings.get('AutoApplyInventoryAdjustment')).lower() == 'true'

        rewrite_all_stock = False
        if bp_settings.get('RewriteAllStock'):
            rewrite_all_stock = str(bp_settings.get('RewriteAllStock')).lower() == 'true'

        modified_stock_ids = []
        if doc.get('actualLines'):
            for actual_line in doc.get('actualLines'):

                if actual_line.get('firstStorageId'):
                    location_id = int(actual_line.get('firstStorageId'))
                    if env['stock.location'].search_count([('id', '=', location_id), ('warehouse_id', '=', warehouse.id)]) < 1:
                        raise RuntimeError('Document contains actual line with location of another warehouse')
                else:
                    location_id = warehouse.lot_stock_id.id

                product_id = int(actual_line.get('inventoryItemId'))
                uom_id = int(actual_line.get('unitOfMeasureId'))

                lot_id = False
                if actual_line.get('serialNumber'):
                    lot_id = actual_line.get('serialNumber')
                elif actual_line.get('seriesName'):
                    lot_id = actual_line.get('seriesName')

                domain_filter = [
                    ('product_id.id', '=', product_id),
                    ('product_uom_id.id', '=', uom_id),
                    ('location_id.id', '=', location_id),
                    ('warehouse_id.id', '=', warehouse.id),
                    ('company_id.id', '=', warehouse.company_id.id)
                ]

                if lot_id:
                    domain_filter.append(('lot_id.name', '=', lot_id))

                found_stock_quants = env['stock.quant'].search(domain_filter, limit=1)
                if found_stock_quants and len(found_stock_quants) > 0:
                    existing_stock_quant = found_stock_quants[0]

                    # In case 'RewriteAllStock' option is disabled and 'stock.quant' line was not modified and was not scanned then skip it
                    if not existing_stock_quant.inventory_quantity_set and not rewrite_all_stock and actual_line.get('actualQuantity') == 0:
                        continue

                    values = {
                        'inventory_quantity': existing_stock_quant.inventory_quantity + actual_line.get('actualQuantity'),
                        'inventory_quantity_set': True,
                        'last_count_date': datetime.datetime.now()
                    }
                    existing_stock_quant.write(values)
                    if existing_stock_quant.id not in modified_stock_ids:
                        modified_stock_ids.append(existing_stock_quant.id)
                    continue

                new_stock_quant = {
                    'product_id': product_id,
                    'product_uom_id': uom_id,
                    'location_id': location_id,
                    'quantity': 0,
                    'inventory_quantity': actual_line.get('actualQuantity'),
                    'inventory_quantity_set': True,
                    'last_count_date': datetime.datetime.now(),
                    'warehouse_id': warehouse.id,
                    'company_id': warehouse.company_id.id
                }

                if lot_id:
                    found_lots = env['stock.lot'].search([
                        ('product_id', '=', product_id),
                        ('name', '=', lot_id),
                        ('company_id', '=', warehouse.company_id.id)
                    ], limit=1)
                    if found_lots and len(found_lots) > 0:
                        existing_lot = found_lots[0]
                        new_stock_quant['lot_id'] = existing_lot.id
                    else:
                        new_lot = {
                            'product_id': product_id,
                            'name': lot_id,
                            'company_id': warehouse.company_id.id
                        }

                        new_lot = env['stock.lot'].create(new_lot)
                        new_stock_quant['lot_id'] = new_lot.id

                new_stock_quant = env['stock.quant'].create(new_stock_quant)
                if new_stock_quant.id not in modified_stock_ids:
                    modified_stock_ids.append(new_stock_quant.id)

        if auto_apply_inventory_adjustment:
            for stock_quant_id in modified_stock_ids:
                stock_quant = env['stock.quant'].search([('id', '=', stock_quant_id)], limit=1)[0]
                stock_quant \
                    .with_context({f'inventory_name': self._generate_completed_inv_adj_doc_name(doc, device_info)}) \
                    .action_apply_inventory()

    def _group_actual_quantities(self, actual_lines):
        result = {}

        if actual_lines:
            for actual_line in actual_lines:
                product_id = int(actual_line.get('inventoryItemId'))
                uom_id = int(actual_line.get('unitOfMeasureId'))

                location_id = None
                if actual_line.get('firstStorageId'):
                    location_id = int(actual_line.get('firstStorageId'))

                lot_id = None
                if actual_line.get('serialNumber'):
                    lot_id = actual_line.get('serialNumber')
                elif actual_line.get('seriesName'):
                    lot_id = actual_line.get('seriesName')

                group_key = (location_id, product_id, uom_id, lot_id)

                if group_key in result:
                    result[group_key] += actual_line.get('actualQuantity')
                else:
                    result[group_key] = actual_line.get('actualQuantity')

        return result

    def _generate_completed_inv_adj_doc_name(self, doc, device_info) -> str:

        user_id = 'UNKNOWN_USER'
        device_id = 'UNKNOWN_DEVICE'

        if doc and doc.get('userId'):
            user_id = str(doc.get('userId')).upper()
        elif device_info and device_info.get('userId'):
            user_id = str(device_info.get('userId')).upper()

        if doc and doc.get('deviceId'):
            device_id = str(doc.get('deviceId')).upper()
        elif device_info.get('deviceId'):
            device_id = str(device_info.get('deviceId')).upper()

        return f'Warehouse 15: Stock Taking by {user_id} with {device_id}'
