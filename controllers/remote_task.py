from odoo import http
from odoo.http import request
from odoo.tools import config
import logging

_logger = logging.getLogger(__name__)

class RemoteTaskController(http.Controller):

    @http.route(
        route='/api/create_remote_task',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def create_remote_task(self, **payload):
        # Main task data
        vals = {
            'name': payload.get('name') or 'No title',
            'project_id': config.get("project_id_for_custom_fields"),
            'partner_id': None,
            'user_ids': None,
            'description': payload.get('description'),
        }
        task = request.env['project.task'].sudo().create(vals)

        # Attachments
        attachments = payload.get('attachments') or []
        for att in attachments:
            data_b64 = att.get('data')
            if not data_b64:
                continue

            request.env['ir.attachment'].sudo().create({
                'name': att.get('filename') or 'attachment',
                'datas': data_b64,
                'res_model': 'project.task',
                'res_id': task.id,
                'mimetype': att.get('mimetype') or 'application/octet-stream',
            })

        return {
            'id': task.id,
            'name': task.name,
        }

    @http.route(route='/api/health', type='http', auth='user', methods=['GET'])
    def health(self):
        pick = request.env['ir.attachment'].search([('id', '=', '11277')])
        return f"<img src='{pick.image_src}' alt='It`s Alive!'/>"


    @http.route(route='/api/update_lists', type='json', auth='user', methods=['POST'], csrf=False)
    def update_lists(self,  **payload):

        table_name = payload['table_name']

        if not table_name:
            return request.make_response(data="error", status=404)

        try:
            setting = request.env['project.unit.settings'].search([])
            match table_name:
                case 'DivisionROV':
                    setting.get_units_data()
                    return request.make_response(data="ok", status=200)
                case 'Task_description':
                    setting.get_data_type_data()
                    return request.make_response(data="ok", status=200)
                case 'Source':
                    setting.get_doc_sources_data()
                    return request.make_response(data="ok", status=200)
                case 'document_type':
                    setting.get_docs_folders()
                    return request.make_response(data="ok", status=200)
                case 'output_documents':
                    setting.get_out_docs_folders()
                    return request.make_response(data="ok", status=200)
                case _:
                    return request.make_response(data="not found", status=404)
        except Exception as ex:
            return request.make_response(data=ex.args, status=500)

# 1. Get auth cookie:
# url = 'https://test.krp-crm.site/web/session/authenticate'
# body = {
#     "jsonrpc": "2.0",
#     "method": "call",
#     "params": {
#         "db": "odoo_db",
#         "login": "task_bot",
#         "password": "Task_b0t!",
#     }
# }
#
#
# get from HEADERS:
# headers["Set-Cookie"] : session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7; Expires=Thu, 26 Nov 2026 10:47:44 GMT; Max-Age=604800; HttpOnly; Path=/
#
# res = requests.post(url=url, json=body)
# cook = res.headers.get('Set-Cookie')
# cook_sid = cook.split(';')[1] # take id only from "session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7"
#
# and put to other requests headers:
# Cookie: session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7
#
#
# 2. POST /api/create_remote_task
# Content-Type: application/json
#
# {
#     "jsonrpc": "2.0",
#     "method": "call",
#     "params": {
#         "name": "Task name",
#         "project_id": 1,
#         "description": "This text will go to Вхідні дані",
#         "attachments": [
#             {
#                 "filename": "image.png",
#                 "mimetype": "image/png",
#                 "data": "iVBORiAGPcegd8..." // converted to base64
#             }
#         ]
#     }
# }
