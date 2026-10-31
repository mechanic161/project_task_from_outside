import logging

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.safe_eval import datetime

_logger = logging.getLogger(__name__)


class RemoteTaskController(http.Controller):

    @http.route(
        route="/api/v1/create_remote_task",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def create_remote_task(self, **payload):
        # Main task data

        payload_unit_name = payload.get("unit_name")

        Project = request.env["project.project"].sudo()
        project_id = 3
        project = Project.browse(project_id).exists()
        if not project:
            raise UserError(f"Project {project_id} not found")

        unit_id = request.env["project.unit"].sudo().search([("name", "=", payload_unit_name)], limit=1).id or False
        payload_act_date = datetime.datetime.strptime(payload.get("actuality_date"), "%d/%m/%Y").date()  # 30/06/2026
        vals = {
            "name": payload.get("task_name") or "Завдання з Signal",
            "project_id": project.id,
            "unit_id": unit_id,
            "actuality_date": payload_act_date,
        }

        try:
            Task = request.env["project.task"].sudo()
            task = Task.with_context(
                mail_create_nosubscribe=True,
                tracking_disable=True,
            ).create(vals)
        except Exception as ex:
            _logger.error(ex)
            return request.make_response(data="error", status=500)

        # Attachments
        attachments = payload.get("attachments") or []
        for att in attachments:
            data_b64 = att.get("datas")
            if not data_b64:
                continue

            request.env["ir.attachment"].sudo().create({
                "name": att.get("filename") or "attachment",
                "datas": data_b64,
                "res_model": "project.task",
                "res_id": task.id,
                "mimetype": att.get("mimetype") or "application/octet-stream",
            })

        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")

        return {
            "ok": True,
            "id": task.id,
            "name": task.name,
            "task_url": f"{base_url.rstrip('/')}/odoo/project/{project.id}/tasks/{task.id}",
        }

    @http.route(
        "/api/v1/upload-attachment-to-task",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def upload_attachment(self, **kwargs):

        data = {**kwargs}

        task_id = data.get("task_id") or False
        if not task_id:
            _logger.error(f"upload_attachment: Task {task_id} not in payload")

        task = request.env["project.task"].browse(task_id).exists()

        _logger.warning(f"upload_attachment: Task {task_id} upload attachment")

        if not task:
            _logger.error(f"upload_attachment: Task {task_id} not found")
            return request.make_json_response(
                {"error": "Task not found"},
                status=404,
            )

        attachments = data.get("attachments") or []
        _logger.warning(f"upload_attachment: Attachments: {len(attachments)}")
        for att in attachments:
            data_b64 = att.get("datas")
            if not data_b64:
                continue

            request.env["ir.attachment"].sudo().create({
                "name": att.get("filename") or "attachment",
                "datas": data_b64,
                "res_model": "project.task",
                "res_id": task.id,
                "mimetype": att.get("mimetype") or "application/octet-stream",
            })

        return request.make_response(data="ok", status=200)

    @http.route(route='/api/health', type='http', auth='user', methods=['GET'])
    def health(self):
        pick = request.env['ir.attachment'].search([('id', '=', '11277')])
        return f"<img src='{pick.image_src}' alt='It`s Alive!'/>"

    # @http.route(route="/api/update_lists", type="json", auth="user", methods=["POST"], csrf=False)
    # def update_lists(self, **payload):
    #
    #     table_name = payload["table_name"]
    #
    #     if not table_name:
    #         return request.make_response(data="error", status=404)
    #
    #     try:
    #         setting = request.env["project.unit.settings"].search([], limit=1)
    #         match table_name:
    #             case "DivisionROV":
    #                 setting.get_units_data()
    #                 return request.make_response(data="ok", status=200)
    #             case "Task_description":
    #                 setting.get_data_type_data()
    #                 return request.make_response(data="ok", status=200)
    #             case "Source":
    #                 setting.get_doc_sources_data()
    #                 return request.make_response(data="ok", status=200)
    #             case "document_type":
    #                 setting.get_docs_folders()
    #                 return request.make_response(data="ok", status=200)
    #             case "output_documents":
    #                 setting.get_out_docs_folders()
    #                 return request.make_response(data="ok", status=200)
    #             case "equipment":
    #                 setting.get_ovt_list()
    #                 return request.make_response(data="ok", status=200)
    #             case "division_ua":
    #                 setting.get_friendly_units()
    #                 return request.make_response(data="ok", status=200)
    #             case _:
    #                 return request.make_response(data="not found", status=404)
    #     except Exception as ex:
    #         return request.make_response(data=ex.args, status=500)

# 1. Get auth cookie:
# url = 'https://erp-test.ac3.army/web/session/authenticate'
# body = {
#     "jsonrpc": "2.0",
#     "method": "call",
#     "params": {
#         "db": "odoo_db",
#         "login": "task_bot@mail.here",
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
# 2. POST /api/v1/create_remote_task
# Content-Type: application/json
#
# {
#     "jsonrpc": "2.0",
#     "method": "call",
#     "params": {
#         "task_name": "Task name",
#         "project_id": 3,
#         "description": "This text will go to Вхідні дані",
#         "attachments": [
#             {
#                 "filename": "image.png",
#                 "mimetype": "image/png",
#                 "datas": "iVBORiAGPcegd8..." // converted to base64
#             }
#         ]
#     }
# }
