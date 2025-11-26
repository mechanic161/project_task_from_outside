from odoo import http
from odoo.http import request
import requests


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
            'project_id': payload.get('project_id'),
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
        pick = request.env['ir.attachment'].search([('id', '=', '985')])

        return f"<img src='{pick.image_src}' alt='It`s Alive!'/>"


# 1. Get auth cookie:
# localhost:8069/web/session/authenticate
# {
#   "jsonrpc": "2.0",
#   "params": {
#     "db": "odoo_db",
#     "login": "task_bot",
#     "password": "task_bot"
#   }
# }
# response:
# get from HEADERS:
# headers["Set-Cookie"] : session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7; Expires=Thu, 26 Nov 2026 10:47:44 GMT; Max-Age=604800; HttpOnly; Path=/
# take  "session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7"

# and put to other requests headers:
# Cookie: session_id=EzMoKXmsTZXd4JT9M4mdPhJrM-UQwLpWCvWK1VnN7S6hBGpsMBk-WxLre3bb9zGgNRCCk0fZSWzDBilfMPM7


# 2. POST /api/create_remote_task
# Content-Type: application/json
#
# {
#     "jsonrpc": "2.0",
#     "method": "call",
#     "params": {
#         "name": "Назва завдання",
#         "project_id": 1,
#         "cr_user_id": 8,
#         "description": "Вхідні дані",
#         "attachments": [
#             {
#                 "filename": "image.png",
#                 "mimetype": "image/png",
#                 "data": "iVBORiAGPcegd8..." // converted to base64
#             }
#         ]
#     }
# }
