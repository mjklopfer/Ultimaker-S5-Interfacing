"""Loopback-only MCP status and guarded workspace-command endpoint for Cura 5.13."""
import json
import os
import secrets
import socket
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .project_io import path_info, plan_save, atomic_project_write

from PyQt6.QtCore import QObject, QTimer, QUrl

from UM.Extension import Extension
from UM.Logger import Logger


class ExclusiveLoopbackServer(ThreadingHTTPServer):
    """Prevent competing Windows Cura instances from sharing one bridge port."""
    allow_reuse_address = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class CuraMcpBridge(QObject, Extension):
    """Run a loopback bridge without touching Cura state until a command is accepted."""

    PORT = 49621
    CONNECTION_FILE = "cura-mcp-bridge.json"

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._lock = threading.Lock()
        self._pending_commands = []
        self._started = False
        self._current_project = None
        self._pending_project = None
        self._tracking_connected = False
        self._save_jobs = {}
        self._snapshot = {"schema_version": 1, "ready": False, "detail": "Cura bridge is starting."}
        self._connection_path = os.path.join(self._preferences_directory(), self.CONNECTION_FILE)
        self._token = self._load_or_create_token()
        self._timer = QTimer(self)
        self._timer.setInterval(750)
        # Do not inspect the active machine, extruders, or scene at startup.
        # Cura lazily constructs those objects; doing so can surface a damaged
        # user profile and make an otherwise recoverable session unusable.
        self._timer.timeout.connect(self._execute_pending_commands)
        # Startup deliberately avoids CuraApplication, Preferences, machine stacks,
        # material containers, and scene state. This plugin must not influence Cura's
        # profile recovery or material filtering.
        QTimer.singleShot(0, self._start)

    @staticmethod
    def _preferences_directory():
        if sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "cura", "5.13")
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "cura", "5.13")

    def _load_or_create_token(self):
        try:
            with open(self._connection_path, "r", encoding="utf-8") as source:
                existing = json.load(source).get("token")
            if isinstance(existing, str) and existing:
                return existing
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        return secrets.token_urlsafe(32)

    def _start(self):
        if self._started:
            return
        self._started = True
        with self._lock:
            self._snapshot = {
                "schema_version": 1,
                "ready": True,
                "bridge_version": "0.1.7",
                "process_id": os.getpid(),
                "printer": None,
                "active_profile": None,
                "extruders": [],
                "build_plate_object_count": 0,
                "detail": "Bridge is running without inspecting Cura configuration, profiles, materials, or scene state.",
            }
        self._timer.start()
        self._start_http_server()

    def _start_http_server(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/v1/status":
                    self.send_error(404)
                    return
                if not secrets.compare_digest(self.headers.get("X-Cura-Bridge-Token", ""), bridge._token):
                    self.send_error(401)
                    return
                with bridge._lock:
                    body = json.dumps(bridge._snapshot).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                command_name = self.path.removeprefix('/v1/commands/')
                if command_name not in {'load_file', 'inspect', 'get_settings', 'set_settings', 'slice', 'export_gcode',
                                        'path_info', 'plan_project_save', 'save_project', 'project_save_status'}:
                    self.send_error(404)
                    return
                if not secrets.compare_digest(self.headers.get("X-Cura-Bridge-Token", ""), bridge._token):
                    self.send_error(401)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > 16 * 1024:
                        raise ValueError("invalid request length")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    command = {'action': command_name, 'payload': payload, 'event': threading.Event(), 'cancelled': False}
                    with bridge._lock:
                        bridge._pending_commands.append(command)
                    if not command['event'].wait(6):
                        with bridge._lock:
                            command['cancelled'] = True
                        self.send_error(504, 'Cura main-thread command timed out; inspect state before retrying')
                        return
                    body = json.dumps(command['result'], default=str).encode('utf-8')
                    self.send_response(400 if 'error' in command['result'] else 200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                except (ValueError, json.JSONDecodeError) as error:
                    self.send_error(400, str(error))

            def log_message(self, *_args):
                return

        try:
            self._server = ExclusiveLoopbackServer(("127.0.0.1", self.PORT), Handler)
        except OSError as error:
            Logger.error("Cura MCP Bridge could not bind loopback port %s: %s", self.PORT, error)
            return
        thread = threading.Thread(target=self._server.serve_forever, name="CuraMcpBridge", daemon=True)
        thread.start()
        os.makedirs(os.path.dirname(self._connection_path), exist_ok=True)
        with open(self._connection_path, "w", encoding="utf-8") as output:
            json.dump({"host": "127.0.0.1", "port": self.PORT, "token": self._token}, output)
        try:
            os.chmod(self._connection_path, 0o600)
        except OSError:
            pass
        Logger.log("i", "Cura MCP Bridge status endpoint enabled on loopback.")

    def _execute_pending_commands(self):
        """Run queued loopback requests on Cura's main thread, never the HTTP thread."""
        with self._lock:
            commands = self._pending_commands
            self._pending_commands = []
        for command in commands:
            try:
                if command.get('cancelled'):
                    continue
                command['result'] = self._execute_workspace_command(command['action'], command['payload'])
            except Exception as error:
                Logger.logException("e", "Cura MCP Bridge command failed: %s", error)
                command['result'] = {'error': str(error)}
            finally:
                if 'event' in command:
                    command['event'].set()

    def _execute_workspace_command(self, action, payload):
        """Explicit on-demand Cura access, exclusively on the main thread."""
        from cura.CuraApplication import CuraApplication
        app = CuraApplication.getInstance()
        if not self._tracking_connected:
            app.workspaceLoaded.connect(self._on_workspace_loaded)
            self._tracking_connected = True
        if action == 'path_info':
            return path_info(payload.get('file_path'))
        if action == 'project_save_status':
            job = self._save_jobs.get(payload.get('operation_id'))
            if job is None:
                raise ValueError('Unknown project save operation')
            return {key: value for key, value in job.items() if key not in ('job', 'callback')}
        if action in ('load_file', 'set_settings', 'slice', 'save_project') and any(j['status'] == 'running' for j in self._save_jobs.values()):
            raise ValueError('A project save is running; poll its status before changing the workspace')
        if action == 'load_file':
            filename = payload.get('file_path')
            info = path_info(filename)
            if not info.get('is_file') or not info.get('readable'):
                raise ValueError('Cura cannot read requested file: ' + json.dumps(info))
            if os.path.splitext(filename)[1].lower() not in {'.stl', '.3mf', '.obj', '.amf', '.x3d', '.gcode', '.ufp'}:
                raise ValueError('Unsupported Cura file extension')
            mode = payload.get('project_mode', 'open_as_project')
            if mode not in ('open_as_project', 'open_as_model'):
                raise ValueError('Invalid project_mode')
            if filename.lower().endswith('.3mf') and mode == 'open_as_project':
                self._pending_project = os.path.realpath(filename)
            app.readLocalFile(QUrl.fromLocalFile(filename), project_mode=mode)
            return {'accepted': True, 'file_path': filename, 'project_mode': mode,
                    'detail': 'File read requested; inspect scene after loading completes.'}
        if action == 'plan_project_save':
            location = self._project_location(app)
            return plan_save(payload, location['file_path'], location['folder'])
        if action == 'save_project':
            return self._start_project_save(app, payload)
        stack = app.getGlobalContainerStack()
        if stack is None:
            raise ValueError('No active Cura machine')
        if action == 'inspect':
            scene = app.getController().getScene()
            from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
            objects = [{'name': node.getName()} for node in DepthFirstIterator(scene.getRoot())
                       if hasattr(node, 'callDecoration') and node.callDecoration('isSliceable') and node.getMeshData() is not None]
            return {'machine': {'id': stack.getId(), 'name': stack.getName()},
                    'quality': stack.quality.getName(),
                    'extruders': [{'position': extruder.position, 'material': extruder.material.getName(),
                                   'variant': extruder.variant.getName()} for extruder in stack.extruderList],
                    'objects': objects, 'backend_state': getattr(app.getBackend(), '_backend_state').name,
                    'gcode_build_plates': list(getattr(scene, 'gcode_dict', {}).keys()),
                    'project_location': self._project_location(app)}
        index = payload.get('extruder')
        if index is not None:
            if not isinstance(index, int) or not 0 <= index < len(stack.extruderList):
                raise ValueError('Invalid extruder index')
            stack = stack.extruderList[index]
        if action == 'get_settings':
            keys = payload.get('keys')
            if not keys:
                return {'keys': sorted(stack.getAllKeys())}
            if len(keys) > 200:
                raise ValueError('Read at most 200 settings per call')
            return {'settings': {key: {'value': stack.getProperty(key, 'value'),
                'type': stack.getProperty(key, 'type'), 'enabled': stack.getProperty(key, 'enabled')}
                for key in keys if key in stack.getAllKeys()}}
        if action == 'set_settings':
            values = payload.get('values')
            if not isinstance(values, dict) or not values or len(values) > 100:
                raise ValueError('Provide 1 to 100 setting values')
            for key in values:
                if key not in stack.getAllKeys():
                    raise ValueError('Unknown Cura setting: ' + key)
                if stack.getProperty(key, 'type') == 'category':
                    raise ValueError('Cannot write a setting category')
            previous = {key: stack.getProperty(key, 'value') for key in values}
            for key, value in values.items():
                stack.userChanges.setProperty(key, 'value', value)
            return {'updated': list(values), 'previous_values': previous,
                    'values': {key: stack.getProperty(key, 'value') for key in values}}
        if action == 'slice':
            app.getBackend().slice()
            return {'requested': True, 'detail': 'Slicing requested; inspect backend state before exporting.'}
        if action == 'export_gcode':
            filename = payload.get('file_path')
            if not isinstance(filename, str) or not os.path.isabs(filename) or not filename.lower().endswith('.gcode'):
                raise ValueError('Provide an absolute .gcode output path')
            plate = payload.get('build_plate', 0)
            lines = getattr(app.getController().getScene(), 'gcode_dict', {}).get(plate)
            if not lines:
                raise ValueError('No sliced G-code is available for this build plate')
            if 'done' not in getattr(app.getBackend(), '_backend_state').name.lower():
                # BackendState is an IntEnum in some Cura versions.
                from UM.Backend.Backend import BackendState
                if getattr(app.getBackend(), '_backend_state') != BackendState.Done:
                    raise ValueError('Slicing has not finished; refusing stale export')
            with open(filename, 'x', encoding='utf-8') as output:
                output.writelines(lines)
            return {'exported': True, 'file_path': filename, 'bytes': os.path.getsize(filename)}
        raise ValueError('Unknown workspace command')

    def _project_location(self, app):
        folder = os.path.dirname(self._current_project) if self._current_project else app.getPreferences().getValue('local_file/dialog_save_path')
        return {'file_path': self._current_project, 'folder': folder or None,
                'source': 'bridge_open_or_save' if self._current_project else 'Cura_save_folder_only'}

    def _on_workspace_loaded(self, name=None):
        if not name:
            self._current_project = None
            return
        self._current_project = self._pending_project
        self._pending_project = None

    def _start_project_save(self, app, payload):
        from UM.Job import Job
        from UM.Workspace.WorkspaceWriter import WorkspaceWriter
        from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
        root = app.getController().getScene().getRoot()
        if not any(node.callDecoration('isSliceable') and node.getMeshData() is not None for node in DepthFirstIterator(root)):
            raise ValueError('No sliceable geometry to save')
        if payload.get('source_project') != self._current_project:
            raise ValueError('Current project changed after confirmation')
        writer = app.getWorkspaceFileHandler().getWriter('3MFWriter')
        if writer is None:
            raise ValueError('Native Cura 3MF writer is unavailable')
        options = {'mode': payload.get('mode'), 'create_folder': payload.get('create_folder', False)}
        if options['mode'] == 'save_as':
            options.update(folder=os.path.dirname(payload['file_path']), file_name=os.path.basename(payload['file_path']))
        plan = plan_save(options, self._current_project, self._project_location(app)['folder'])
        if plan != payload:
            raise ValueError('Save destination or existing file changed after confirmation')
        operation = str(uuid.uuid4())
        class ProjectSaveJob(Job):
            def run(job):
                try:
                    job.setResult(atomic_project_write(plan, lambda stream: writer.write(stream, [root], WorkspaceWriter.OutputMode.BinaryMode)))
                except Exception as error:
                    job.setError(error)
        job = ProjectSaveJob()
        callback = lambda finished: app.callLater(self._finish_project_save, operation, finished)
        self._save_jobs[operation] = {'operation_id': operation, 'status': 'running',
                                     'file_path': payload['file_path'], 'job': job, 'callback': callback}
        job.finished.connect(callback)
        job.start()
        return {'operation_id': operation, 'status': 'running', 'file_path': payload['file_path'], 'writer': type(writer).__name__,
                'detail': 'Poll project_save_status to confirm a validated completed save.'}

    def _finish_project_save(self, operation, job):
        result = self._save_jobs[operation]
        if job.hasError():
            result.update(status='failed', error=str(job.getError()))
        else:
            result.update(job.getResult(), status='completed')
            self._current_project = result['file_path']
            from cura.CuraApplication import CuraApplication
            app = CuraApplication.getInstance()
            app.getPreferences().setValue('local_file/dialog_save_path', os.path.dirname(self._current_project))
        result.pop('job', None)
        result.pop('callback', None)
