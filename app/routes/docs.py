from flask import Blueprint, render_template, request, current_app, send_from_directory, redirect, url_for, flash
from flask_login import login_required
import os
from werkzeug.utils import secure_filename


docs_bp = Blueprint('docs', __name__)


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
    files = []
    for fname in sorted(os.listdir(base_dir)):
        full = os.path.join(base_dir, fname)
        if os.path.isfile(full):
            if not q or q in fname.lower():
                files.append(fname)

    allowed_exts = sorted(list(current_app.config['ALLOWED_DOC_EXTENSIONS']))
    return render_template(
        'docs/index.html',
        categories=categories,
        category=category,
        files=files,
        q=q,
        allowed_exts=allowed_exts
    )


@docs_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    category = request.form.get('category') or 'manuali'
    docs_root = current_app.config['DOCS_FOLDER']
    os.makedirs(os.path.join(docs_root, category), exist_ok=True)

    if 'file' not in request.files:
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('docs.index', category=category))
    file = request.files['file']
    if file.filename == '':
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('docs.index', category=category))
    if not _allowed_doc(file.filename, current_app.config['ALLOWED_DOC_EXTENSIONS']):
        flash('Estensione file non permessa.', 'error')
        return redirect(url_for('docs.index', category=category))
    fname = secure_filename(file.filename)
    save_path = os.path.join(docs_root, category, fname)
    file.save(save_path)
    flash('Documento caricato con successo.', 'success')
    return redirect(url_for('docs.index', category=category))


@docs_bp.route('/view/<path:category>/<path:filename>')
@login_required
def view(category, filename):
    docs_root = current_app.config['DOCS_FOLDER']
    return send_from_directory(os.path.join(docs_root, category), filename)


@docs_bp.route('/delete', methods=['POST'])
@login_required
def delete():
    """Elimina un documento dalla categoria indicata."""
    category = request.form.get('category') or ''
    filename = request.form.get('filename') or ''

    docs_root = current_app.config['DOCS_FOLDER']
    safe_name = secure_filename(filename)
    file_path = os.path.join(docs_root, category, safe_name)

    if not category or not filename:
        flash('Categoria o file mancanti.', 'error')
        return redirect(url_for('docs.index', category=category or 'manuali'))

    if not os.path.isfile(file_path):
        flash('File non trovato.', 'error')
        return redirect(url_for('docs.index', category=category))

    try:
        os.remove(file_path)
        flash('Documento eliminato con successo.', 'success')
    except OSError as e:
        flash(f'Errore durante l\'eliminazione: {e}', 'error')

    return redirect(url_for('docs.index', category=category))


@docs_bp.route('/move', methods=['POST'])
@login_required
def move():
    """Sposta un documento da una categoria a un'altra."""
    source_category = request.form.get('source_category') or ''
    target_category = request.form.get('target_category') or ''
    filename = request.form.get('filename') or ''

    docs_root = current_app.config['DOCS_FOLDER']
    safe_name = secure_filename(filename)
    src_path = os.path.join(docs_root, source_category, safe_name)
    dst_dir = os.path.join(docs_root, target_category)
    dst_path = os.path.join(dst_dir, safe_name)

    if not source_category or not target_category or not filename:
        flash('Dati per lo spostamento incompleti.', 'error')
        return redirect(url_for('docs.index', category=source_category or 'manuali'))

    if not os.path.isfile(src_path):
        flash('File sorgente non trovato.', 'error')
        return redirect(url_for('docs.index', category=source_category))

    os.makedirs(dst_dir, exist_ok=True)

    if os.path.exists(dst_path):
        flash('Esiste già un file con lo stesso nome nella destinazione.', 'error')
        return redirect(url_for('docs.index', category=source_category))

    try:
        os.rename(src_path, dst_path)
        flash('Documento spostato con successo.', 'success')
    except OSError as e:
        flash(f'Errore durante lo spostamento: {e}', 'error')
        return redirect(url_for('docs.index', category=source_category))

    return redirect(url_for('docs.index', category=target_category))
