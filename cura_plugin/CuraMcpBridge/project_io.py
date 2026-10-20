"""Project destinations and validated, atomic 3MF writes; no Cura dependency."""
import hashlib
import os
import stat
import tempfile
import zipfile


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def path_info(path):
    if not isinstance(path, str) or not os.path.isabs(path):
        raise ValueError('An absolute local path is required')
    result = {'path': path, 'resolved_path': os.path.realpath(path),
              'exists': False, 'is_file': False, 'is_directory': False}
    try:
        info = os.stat(path)
        result.update(exists=True, is_file=stat.S_ISREG(info.st_mode),
                      is_directory=stat.S_ISDIR(info.st_mode), size=info.st_size)
        if result['is_file']:
            with open(path, 'rb') as source:
                source.read(1)
            result['readable'] = True
    except OSError as error:
        result.update(error_type=type(error).__name__, errno=error.errno,
                      winerror=getattr(error, 'winerror', None), detail=str(error))
    return result


def plan_save(payload, current_project, current_folder):
    mode = payload.get('mode', 'save')
    if mode not in ('save', 'save_as'):
        raise ValueError('mode must be save or save_as')
    if mode == 'save':
        if payload.get('folder') or payload.get('file_name') or payload.get('create_folder'):
            raise ValueError('Use save_as to select another name or folder')
        if not current_project:
            raise ValueError('No known current project path; use save_as first')
        target = current_project
    else:
        folder = payload.get('folder') or current_folder
        name = payload.get('file_name') or (os.path.basename(current_project) if current_project else None)
        if not folder or not os.path.isabs(folder):
            raise ValueError('Specify an absolute folder; there is no known current folder')
        if not isinstance(name, str) or not name.strip() or any(c in name for c in ('/', '\\', ':', '\x00')) or name in ('.', '..'):
            raise ValueError('Specify a filename without folder separators')
        if not name.lower().endswith('.3mf'):
            name += '.3mf'
        target = os.path.join(folder, name)
    if not os.path.isabs(target) or not target.lower().endswith('.3mf'):
        raise ValueError('Project destination must be an absolute .3mf path')
    if os.path.islink(target):
        raise ValueError('Refusing a symbolic-link project destination')
    target = os.path.join(os.path.realpath(os.path.dirname(target)), os.path.basename(target))
    exists = os.path.lexists(target)
    if exists and not os.path.isfile(target):
        raise ValueError('Project destination is not a regular file')
    if mode == 'save_as' and exists:
        raise ValueError('Save As requires a new filename; destination already exists')
    folder = os.path.dirname(target)
    create = bool(payload.get('create_folder', False))
    if not os.path.isdir(folder) and not create:
        raise ValueError('Destination folder does not exist; specify create_folder=true to create it')
    return {'mode': mode, 'file_path': target, 'create_folder': create,
            'expected_sha256': file_hash(target) if exists else None,
            'source_project': current_project}


def atomic_project_write(plan, write):
    """Call native writer, verify archive, commit only on success; preserve old file."""
    target = plan['file_path']
    parent = os.path.dirname(target)
    if os.path.join(os.path.realpath(parent), os.path.basename(target)) != target:
        raise ValueError('Destination folder changed after confirmation')
    if plan.get('create_folder'):
        os.makedirs(parent, exist_ok=True)
    expected = plan.get('expected_sha256')
    def check_destination():
        if os.path.islink(target):
            raise ValueError('Destination became a symbolic link')
        if expected is None:
            if os.path.lexists(target):
                raise ValueError('Destination appeared after confirmation')
        elif not os.path.isfile(target) or file_hash(target) != expected:
            raise ValueError('Current project changed on disk after confirmation')
    check_destination()
    descriptor, temporary = tempfile.mkstemp(prefix='.cura-mcp-save-', suffix='.3mf', dir=parent)
    try:
        with os.fdopen(descriptor, 'w+b') as stream:
            if write(stream) is not True:
                raise RuntimeError('Cura project writer reported failure')
            stream.flush()
            os.fsync(stream.fileno())
        with zipfile.ZipFile(temporary) as archive:
            names = archive.namelist()
            if '3D/3dmodel.model' not in names or not any(n.startswith('Cura/') and n.endswith('.cfg') for n in names):
                raise ValueError('Writer did not produce a complete Cura project')
            if archive.testzip() is not None:
                raise ValueError('Saved project archive failed integrity verification')
        check_destination()
        if expected is None:
            # Atomic create without replacing any file that appeared concurrently.
            if os.name == 'nt':
                os.rename(temporary, target)  # Windows rename refuses existing targets, including FAT volumes.
            else:
                os.link(temporary, target)
        else:
            os.replace(temporary, target)
        return {'file_path': target, 'bytes': os.path.getsize(target), 'sha256': file_hash(target)}
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
