from flask import Blueprint, render_template, request, current_app, send_from_directory, redirect, url_for, flash
from flask_login import login_required
import os
import zipfile
import tarfile
import shutil
import tempfile
from werkzeug.utils import secure_filename


docs_bp = Blueprint('docs', __name__)


def _allowed_doc(filename, allowed_set):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in {e.strip().lower() for e in allowed_set}


def _sanitize_relative_path(path):
    """Sanitizza un percorso relativo per prevenire directory traversal."""
    import os.path

    # Rimuovi eventuali percorsi assoluti
    path = path.replace('\\', '/')

    # Dividi il percorso in componenti
    parts = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        elif part == '..':
            # Rimuovi l'ultimo elemento (directory traversal)
            if parts:
                parts.pop()
        else:
            # Sanitizza il nome del file/cartella
            parts.append(secure_filename(part))

    # Ricostruisci il percorso
    return '/'.join(parts)


def _extract_archive(archive_path, extract_to):
    """Estrae un archivio in una directory specifica."""
    try:
        if archive_path.endswith(('.zip', '.ZIP')):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar.gz', '.tgz', '.TAR.GZ', '.TGZ')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar.bz2', '.tbz2', '.TAR.BZ2', '.TBZ2')):
            with tarfile.open(archive_path, 'r:bz2') as tar_ref:
                tar_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar', '.TAR')):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
        return True
    except Exception as e:
        current_app.logger.error(f"Errore durante l'estrazione dell'archivio {archive_path}: {e}")
        return False


def _copy_folder_structure(source_dir, target_dir):
    """Copia una struttura di cartelle mantenendo la gerarchia."""
    for root, dirs, files in os.walk(source_dir):
        # Calcola il percorso relativo dalla directory sorgente
        relative_path = os.path.relpath(root, source_dir)
        if relative_path == '.':
            current_target = target_dir
        else:
            current_target = os.path.join(target_dir, relative_path)

        # Crea le directory se non esistono
        os.makedirs(current_target, exist_ok=True)

        # Copia i file
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(current_target, file)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)


def _process_uploaded_files(files, category):
    """Processa i file caricati, gestendo archivi e cartelle."""
    docs_root = current_app.config['DOCS_FOLDER']
    category_dir = os.path.join(docs_root, category)
    os.makedirs(category_dir, exist_ok=True)

    uploaded_files = []
    extracted_archives = []

    # Verifica se stiamo caricando file con struttura di cartelle
    has_folder_structure = any('/' in file.filename or '\\' in file.filename for file in files if file.filename)

    for file in files:
        if file.filename == '':
            continue

        original_fname = file.filename
        fname = secure_filename(file.filename)

        # Gestisci percorsi relativi per cartelle (quando si trascina una cartella)
        if '/' in original_fname or '\\' in original_fname:
            # È un file con percorso relativo (da drag & drop di cartella)
            # Usa il nome originale per preservare la struttura delle cartelle
            relative_path = original_fname.replace('\\', '/')

            # Assicura che il percorso abbia una struttura di cartelle valida
            if not os.path.dirname(relative_path):
                # Se non c'è una cartella nel percorso, creane una
                relative_path = f"Documenti/{os.path.basename(relative_path)}"

            # Valida e sanitizza il percorso
            relative_path = _sanitize_relative_path(relative_path)

            save_path = os.path.join(category_dir, relative_path)

            # Crea tutte le directory necessarie
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            if _allowed_doc(os.path.basename(relative_path), current_app.config['ALLOWED_DOC_EXTENSIONS']):
                file.save(save_path)
                uploaded_files.append(relative_path)
            else:
                flash(f'Estensione file non permessa: {os.path.basename(relative_path)}', 'error')
        elif fname.endswith(('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.tar.gz', '.tar.bz2')):
            # Gestisci archivio
            temp_dir = tempfile.mkdtemp()
            try:
                temp_archive_path = os.path.join(temp_dir, fname)
                file.save(temp_archive_path)

                # Estrai l'archivio in una sottodirectory
                extract_dir = os.path.join(category_dir, fname.rsplit('.', 1)[0])
                os.makedirs(extract_dir, exist_ok=True)

                if _extract_archive(temp_archive_path, extract_dir):
                    extracted_archives.append(fname)
                    archive_name = fname.rsplit('.', 1)[0]
                    uploaded_files.extend(_get_files_from_directory_with_prefix(extract_dir, archive_name))
                else:
                    flash(f'Errore nell\'estrazione dell\'archivio {fname}.', 'error')
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            # File regolare
            if _allowed_doc(fname, current_app.config['ALLOWED_DOC_EXTENSIONS']):
                save_path = os.path.join(category_dir, fname)
                file.save(save_path)
                uploaded_files.append(fname)
            else:
                flash(f'Estensione file non permessa: {fname}', 'error')

    return uploaded_files, extracted_archives


def _get_files_from_directory(directory):
    """Restituisce una lista di tutti i file in una directory ricorsivamente."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, directory)
            files.append(rel_path)
    return files


def _get_files_from_directory_with_prefix(directory, prefix):
    """Restituisce una lista di tutti i file in una directory ricorsivamente con prefisso."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, directory)
            files.append(f"{prefix}/{rel_path}")
    return files


def _allowed_doc(filename, allowed_set):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in {e.strip().lower() for e in allowed_set}


@docs_bp.route('/')
@login_required
def index():
    category = request.args.get('category', 'manuali')
    q = (request.args.get('q') or '').strip().lower()
    current_path = request.args.get('path', '').strip('/')

    docs_root = current_app.config['DOCS_FOLDER']
    default_categories = ['manuali', 'contratti', 'preventivi', 'procedure', 'dev', 'altro']
    os.makedirs(docs_root, exist_ok=True)
    # Assicura le cartelle di default
    for c in default_categories:
        os.makedirs(os.path.join(docs_root, c), exist_ok=True)

    # Legge dinamicamente gli argomenti disponibili (cartelle)
    categories = sorted([
        d for d in os.listdir(docs_root)
        if os.path.isdir(os.path.join(docs_root, d))
    ])

    # Se l'argomento richiesto non esiste, ripiega su manuali o primo disponibile
    if category not in categories:
        category = 'manuali' if 'manuali' in categories else (categories[0] if categories else 'manuali')

    base_dir = os.path.join(docs_root, category)
    if current_path:
        base_dir = os.path.join(base_dir, current_path)
        os.makedirs(base_dir, exist_ok=True)

    files = []
    folders = []

    try:
        for fname in sorted(os.listdir(base_dir)):
            full = os.path.join(base_dir, fname)
            if os.path.isdir(full):
                folders.append(fname)
            elif os.path.isfile(full):
                if not q or q in fname.lower():
                    files.append(fname)
    except OSError:
        # Directory non accessibile, mostra lista vuota
        pass

    allowed_exts = sorted(list(current_app.config['ALLOWED_DOC_EXTENSIONS']))

    # Costruisci il breadcrumb
    breadcrumbs = []
    if current_path:
        parts = current_path.split('/')
        current_breadcrumb_path = ''
        for part in parts:
            current_breadcrumb_path += part
            breadcrumbs.append({
                'name': part,
                'path': current_breadcrumb_path
            })
            current_breadcrumb_path += '/'

    return render_template(
        'docs/index.html',
        categories=categories,
        category=category,
        files=files,
        folders=folders,
        q=q,
        current_path=current_path,
        breadcrumbs=breadcrumbs,
        allowed_exts=allowed_exts
    )


@docs_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    category = request.form.get('category') or 'manuali'

    if 'files' not in request.files and 'file' not in request.files:
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('docs.index', category=category))

    # Supporta sia il caricamento singolo che multiplo
    files = []
    if 'files' in request.files:
        files = request.files.getlist('files')
    elif 'file' in request.files:
        files = [request.files['file']]

    if not files or all(f.filename == '' for f in files):
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('docs.index', category=category))

    uploaded_files, extracted_archives = _process_uploaded_files(files, category)

    # Messaggi di successo
    if uploaded_files:
        if len(uploaded_files) == 1:
            flash('Documento caricato con successo.', 'success')
        else:
            flash(f'Caricati {len(uploaded_files)} documenti con successo.', 'success')

    if extracted_archives:
        if len(extracted_archives) == 1:
            flash(f'Archivio {extracted_archives[0]} estratto con successo.', 'success')
        else:
            flash(f'Estratti {len(extracted_archives)} archivi con successo.', 'success')

    if not uploaded_files and not extracted_archives:
        flash('Nessun file valido caricato.', 'warning')

    return redirect(url_for('docs.index', category=category))


@docs_bp.route('/view/<path:category>/<path:filepath>')
@login_required
def view(category, filepath):
    docs_root = current_app.config['DOCS_FOLDER']
    # filepath potrebbe contenere sia il percorso che il nome file
    # Separiamo il percorso dalla directory dal nome del file
    filepath_parts = filepath.split('/')
    filename = filepath_parts[-1]
    subpath = '/'.join(filepath_parts[:-1]) if len(filepath_parts) > 1 else ''

    directory = os.path.join(docs_root, category, subpath) if subpath else os.path.join(docs_root, category)
    return send_from_directory(directory, filename)


@docs_bp.route('/delete', methods=['POST'])
@login_required
def delete():
    """Elimina un documento dalla categoria indicata."""
    category = request.form.get('category') or ''
    filename = request.form.get('filename') or ''
    current_path = request.form.get('current_path') or ''

    docs_root = current_app.config['DOCS_FOLDER']
    safe_name = secure_filename(filename)
    file_path = os.path.join(docs_root, category, current_path, safe_name) if current_path else os.path.join(docs_root, category, safe_name)

    if not category or not filename:
        flash('Categoria o file mancanti.', 'error')
        return redirect(url_for('docs.index', category=category or 'manuali', path=current_path))

    if not os.path.isfile(file_path):
        flash('File non trovato.', 'error')
        return redirect(url_for('docs.index', category=category, path=current_path))

    try:
        os.remove(file_path)
        flash('Documento eliminato con successo.', 'success')
    except OSError as e:
        flash(f'Errore durante l\'eliminazione: {e}', 'error')

    return redirect(url_for('docs.index', category=category, path=current_path))


@docs_bp.route('/delete_folder', methods=['POST'])
@login_required
def delete_folder():
    """Elimina una cartella dalla categoria indicata."""
    category = request.form.get('category') or ''
    foldername = request.form.get('foldername') or ''
    current_path = request.form.get('current_path') or ''

    docs_root = current_app.config['DOCS_FOLDER']
    safe_name = secure_filename(foldername)
    folder_path = os.path.join(docs_root, category, current_path, safe_name) if current_path else os.path.join(docs_root, category, safe_name)

    if not category or not foldername:
        flash('Categoria o cartella mancanti.', 'error')
        return redirect(url_for('docs.index', category=category or 'manuali', path=current_path))

    if not os.path.isdir(folder_path):
        flash('Cartella non trovata.', 'error')
        return redirect(url_for('docs.index', category=category, path=current_path))

    # Controllo di sicurezza: non eliminare le cartelle di sistema
    default_categories = ['manuali', 'contratti', 'preventivi', 'procedure', 'dev', 'altro']
    if foldername in default_categories and not current_path:
        flash('Non è possibile eliminare le categorie principali del sistema.', 'error')
        return redirect(url_for('docs.index', category=category, path=current_path))

    try:
        import shutil
        shutil.rmtree(folder_path)
        flash('Cartella eliminata con successo.', 'success')
    except OSError as e:
        flash(f'Errore durante l\'eliminazione della cartella: {e}', 'error')

    return redirect(url_for('docs.index', category=category, path=current_path))


@docs_bp.route('/move', methods=['POST'])
@login_required
def move():
    """Sposta un documento da una categoria a un'altra."""
    source_category = request.form.get('source_category') or ''
    target_category = request.form.get('target_category') or ''
    filename = request.form.get('filename') or ''
    current_path = request.form.get('current_path') or ''

    docs_root = current_app.config['DOCS_FOLDER']
    safe_name = secure_filename(filename)
    src_path = os.path.join(docs_root, source_category, current_path, safe_name) if current_path else os.path.join(docs_root, source_category, safe_name)
    dst_dir = os.path.join(docs_root, target_category)
    dst_path = os.path.join(dst_dir, safe_name)

    if not source_category or not target_category or not filename:
        flash('Dati per lo spostamento incompleti.', 'error')
        return redirect(url_for('docs.index', category=source_category or 'manuali', path=current_path))

    if not os.path.isfile(src_path):
        flash('File sorgente non trovato.', 'error')
        return redirect(url_for('docs.index', category=source_category, path=current_path))

    os.makedirs(dst_dir, exist_ok=True)

    if os.path.exists(dst_path):
        flash('Esiste già un file con lo stesso nome nella destinazione.', 'error')
        return redirect(url_for('docs.index', category=source_category, path=current_path))

    try:
        os.rename(src_path, dst_path)
        flash('Documento spostato con successo.', 'success')
    except OSError as e:
        flash(f'Errore durante lo spostamento: {e}', 'error')
        return redirect(url_for('docs.index', category=source_category, path=current_path))

    return redirect(url_for('docs.index', category=target_category))
