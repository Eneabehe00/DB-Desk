from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.macchina import Macchina, TipoMacchina, MovimentoMacchina
from app.models.cliente import Cliente
from app.models.ticket import Ticket
from app.models.department import Department
from app.forms.macchina import MacchinaForm, MacchinaFilterForm
from app.forms.tipo_macchina import TipoMacchinaForm
from app.utils.permissions import PermissionManager
import os

macchine_bp = Blueprint('macchine', __name__)


@macchine_bp.route('/')
@login_required
def index():
    """Lista macchine con statistiche e filtri"""
    form = MacchinaFilterForm()

    # Query base - filtra per reparto utente se non è admin
    query = Macchina.query
    if not current_user.has_permission('can_view_all_departments'):
        if current_user.department_id:
            # Filtra per tipi di macchina associati al reparto dell'utente
            from app.models.department import Department
            user_department = Department.query.get(current_user.department_id)
            if user_department:
                allowed_tipo_ids = [t.id for t in user_department.tipi_macchine.all()]
                if allowed_tipo_ids:
                    query = query.filter(Macchina.tipo_macchina_id.in_(allowed_tipo_ids))
                else:
                    # Se il reparto non ha tipi associati, non mostra nessuna macchina
                    query = query.filter(Macchina.id == -1)

    # Applica filtri da parametri URL
    search_term = request.args.get('search', '').strip()
    if search_term:
        form.search.data = search_term
        search_pattern = f"%{search_term}%"
        query = query.filter(or_(
            Macchina.codice.like(search_pattern),
            Macchina.modello.like(search_pattern),
            Macchina.marca.like(search_pattern),
            Macchina.numero_serie.like(search_pattern)
        ))

    tipo_filter = request.args.get('tipo_macchina_id', '').strip()
    if tipo_filter and tipo_filter != '':
        try:
            tipo_id = int(tipo_filter)
            form.tipo_macchina_id.data = tipo_id
            query = query.filter(Macchina.tipo_macchina_id == tipo_id)
        except ValueError:
            pass  # Ignora valori non validi

    stato_filter = request.args.get('stato', '').strip()
    if stato_filter:
        form.stato.data = stato_filter
        query = query.filter(Macchina.stato == stato_filter)

    department_filter = request.args.get('department_id', '').strip()
    if department_filter and department_filter != '':
        try:
            dept_id = int(department_filter)
            form.department_id.data = dept_id
            query = query.filter(Macchina.department_id == dept_id)
        except ValueError:
            pass  # Ignora valori non validi

    cliente_filter = request.args.get('cliente_id', '').strip()
    if cliente_filter and cliente_filter != '':
        try:
            cliente_id = int(cliente_filter)
            form.cliente_id.data = cliente_id
            query = query.filter(Macchina.cliente_id == cliente_id)
        except ValueError:
            pass  # Ignora valori non validi

    # Statistiche per la dashboard
    total_macchine = query.count()
    macchine_disponibili = query.filter_by(stato='Disponibile').count()
    macchine_in_prestito = query.filter_by(stato='In prestito').count()
    macchine_in_riparazione = query.filter_by(stato='In riparazione').count()

    # Macchine con manutenzione prossima (30 giorni)
    from datetime import datetime, timedelta
    data_limite = datetime.now().date() + timedelta(days=30)
    macchine_manutenzione = query.filter(
        Macchina.prossima_manutenzione <= data_limite
    ).count()

    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = query.order_by(Macchina.codice).paginate(
        page=page, per_page=per_page, error_out=False
    )

    macchine = pagination.items

    # Movimenti recenti (solo per le macchine visibili)
    macchine_ids = [m.id for m in macchine] if macchine else []
    movimenti_recenti = MovimentoMacchina.query.filter(
        MovimentoMacchina.macchina_id.in_(macchine_ids)
    ).order_by(MovimentoMacchina.created_at.desc()).limit(10).all() if macchine_ids else []

    return render_template('macchine/index.html',
                         macchine=macchine,
                         pagination=pagination,
                         form=form,
                         total_macchine=total_macchine,
                         macchine_disponibili=macchine_disponibili,
                         macchine_in_prestito=macchine_in_prestito,
                         macchine_in_riparazione=macchine_in_riparazione,
                         macchine_manutenzione=macchine_manutenzione,
                         movimenti_recenti=movimenti_recenti)




@macchine_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_macchina():
    """Creazione nuova macchina"""
    # Verifica permessi
    if not PermissionManager.can_create_machine(current_user):
        abort(403)

    form = MacchinaForm()

    if form.validate_on_submit():
        try:
            macchina = Macchina(
                codice=form.codice.data.upper(),
                modello=form.modello.data,
                marca=form.marca.data,
                numero_serie=form.numero_serie.data.upper() if form.numero_serie.data else None,
                tipo_macchina_id=form.tipo_macchina_id.data,
                stato=form.stato.data,
                ubicazione=form.ubicazione.data,
                anno_produzione=form.anno_produzione.data,
                peso=form.peso.data,
                dimensioni=form.dimensioni.data,
                alimentazione=form.alimentazione.data,
                prezzo_acquisto=form.prezzo_acquisto.data,
                prezzo_vendita=form.prezzo_vendita.data,
                fornitore=form.fornitore.data,
                data_acquisto=form.data_acquisto.data,
                data_scadenza_garanzia=form.data_scadenza_garanzia.data,
                intervallo_manutenzione_giorni=form.intervallo_manutenzione_giorni.data,
                note=form.note.data,
                department_id=form.department_id.data,
                cliente_id=form.cliente_id.data
            )

            # Calcola prossima manutenzione se specificato intervallo
            if macchina.intervallo_manutenzione_giorni and macchina.data_acquisto:
                from datetime import timedelta
                macchina.prossima_manutenzione = macchina.data_acquisto + timedelta(days=macchina.intervallo_manutenzione_giorni)

            db.session.add(macchina)
            db.session.commit()  # Salva la macchina prima di creare movimenti

            # Se è stato specificato un cliente e la macchina è disponibile, assegnala automaticamente
            if macchina.cliente_id and macchina.stato == 'Disponibile':
                movimento = macchina.assegna_a_cliente(macchina.cliente_id, 'In prestito', 'Assegnazione automatica alla creazione')
                db.session.commit()  # Commit del movimento creato

            return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'danger')

    return render_template('macchine/form_macchina.html',
                         form=form,
                         title='Nuova Macchina',
                         action_url=url_for('macchine.create_macchina'))


@macchine_bp.route('/<int:macchina_id>')
@login_required
def detail_macchina(macchina_id):
    """Dettagli di una macchina"""
    macchina = Macchina.query.get_or_404(macchina_id)

    # Verifica permessi (solo utenti del dipartimento o admin)
    if not (PermissionManager.can_view_machine(current_user, macchina) or current_user.is_admin):
        abort(403)

    # Movimenti recenti della macchina
    movimenti = MovimentoMacchina.query.filter_by(macchina_id=macchina_id)\
        .order_by(MovimentoMacchina.created_at.desc())\
        .limit(10).all()

    # Ticket collegati
    tickets_collegati = macchina.tickets_collegati.limit(10).all()

    return render_template('macchine/dettaglio_macchina.html',
                         macchina=macchina,
                         movimenti=movimenti,
                         tickets_collegati=tickets_collegati)


@macchine_bp.route('/<int:macchina_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_macchina(macchina_id):
    """Modifica macchina"""
    macchina = Macchina.query.get_or_404(macchina_id)

    # Verifica permessi
    if not PermissionManager.can_edit_machine(current_user, macchina):
        abort(403)

    form = MacchinaForm(obj=macchina)
    # Passa l'oggetto macchina al form per la validazione
    form.macchina = macchina

    if form.validate_on_submit():
        try:
            # Salva il cliente precedente per confronto
            cliente_precedente = macchina.cliente_id

            form.populate_obj(macchina)

            # Ricalcola prossima manutenzione se cambiato intervallo
            if macchina.intervallo_manutenzione_giorni and macchina.data_acquisto:
                from datetime import timedelta
                macchina.prossima_manutenzione = macchina.data_acquisto + timedelta(days=macchina.intervallo_manutenzione_giorni)

            # Gestisci cambiamenti di assegnazione cliente
            if cliente_precedente != macchina.cliente_id:
                if macchina.cliente_id and macchina.stato == 'Disponibile':
                    # Nuovo cliente assegnato
                    movimento = macchina.assegna_a_cliente(macchina.cliente_id, 'In prestito', 'Assegnazione durante modifica')
                    flash(f'Macchina aggiornata e assegnata al nuovo cliente! Movimento #{movimento.id} creato.', 'success')
                elif cliente_precedente and not macchina.cliente_id and macchina.stato == 'In prestito':
                    # Cliente rimosso - riporta in magazzino
                    movimento = macchina.riporta_in_magazzino('Rimozione assegnazione cliente durante modifica')
                    flash(f'Macchina aggiornata e riportata in magazzino! Movimento #{movimento.id} creato.', 'success')
                else:
                    db.session.commit()
                    flash('Macchina aggiornata con successo!', 'success')
            else:
                db.session.commit()
                flash('Macchina aggiornata con successo!', 'success')

            return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'danger')

    return render_template('macchine/form_macchina.html',
                         form=form,
                         macchina=macchina,
                         title='Modifica Macchina',
                         action_url=url_for('macchine.edit_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/delete', methods=['POST'])
@login_required
def delete_macchina(macchina_id):
    """Elimina macchina"""
    macchina = Macchina.query.get_or_404(macchina_id)

    # Verifica permessi
    if not PermissionManager.can_delete_machine(current_user, macchina):
        abort(403)

    try:
        # Elimina foto se esiste
        if macchina.foto_filename:
            foto_path = os.path.join('app/static/uploads/macchine', macchina.foto_filename)
            if os.path.exists(foto_path):
                os.remove(foto_path)

        db.session.delete(macchina)
        db.session.commit()

        flash('Macchina eliminata con successo!', 'success')
        return redirect(url_for('macchine.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/assegna', methods=['POST'])
@login_required
def assegna_macchina(macchina_id):
    """Assegna macchina a cliente"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_assign_machine(current_user, macchina):
        abort(403)

    cliente_id = request.form.get('cliente_id', type=int)
    stato = request.form.get('stato', 'In prestito')
    note = request.form.get('note', '')

    if not cliente_id:
        flash('Seleziona un cliente valido', 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    try:
        movimento = macchina.assegna_a_cliente(cliente_id, stato, note)
        db.session.commit()

        flash(f'Macchina assegnata con successo! Movimento #{movimento.id} creato.', 'success')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/rientro', methods=['POST'])
@login_required
def rientro_macchina(macchina_id):
    """Riporta macchina in magazzino"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_return_machine(current_user, macchina):
        abort(403)

    note = request.form.get('note', '')

    try:
        movimento = macchina.riporta_in_magazzino(note)
        db.session.commit()

        flash(f'Macchina riportata in magazzino! Movimento #{movimento.id} creato.', 'success')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/riparazione', methods=['POST'])
@login_required
def invia_riparazione(macchina_id):
    """Invia macchina in riparazione"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_repair_machine(current_user, macchina):
        abort(403)

    note = request.form.get('note', '')

    try:
        movimento = macchina.invia_in_riparazione(note)
        db.session.commit()

        flash(f'Macchina inviata in riparazione! Movimento #{movimento.id} creato.', 'success')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/completa-riparazione', methods=['POST'])
@login_required
def completa_riparazione(macchina_id):
    """Completa riparazione e riporta disponibile"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_repair_machine(current_user, macchina):
        abort(403)

    note = request.form.get('note', '')

    try:
        movimento = macchina.completa_riparazione(note)
        db.session.commit()

        flash(f'Riparazione completata! Movimento #{movimento.id} creato.', 'success')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


@macchine_bp.route('/<int:macchina_id>/attiva', methods=['POST'])
@login_required
def attiva_macchina(macchina_id):
    """Marca macchina come attiva (venduta e in uso presso cliente)"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_sell_machine(current_user, macchina):
        abort(403)

    cliente_id = request.form.get('cliente_id', type=int)
    prezzo_vendita = request.form.get('prezzo_vendita', type=float)
    note = request.form.get('note', '')

    try:
        movimento = macchina.attiva(cliente_id, prezzo_vendita, note)
        db.session.commit()

        flash(f'Macchina attivata presso cliente! Movimento #{movimento.id} creato.', 'success')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('macchine.detail_macchina', macchina_id=macchina.id))


# API endpoints per AJAX
@macchine_bp.route('/api/search')
@login_required
def api_search_macchine():
    """API per ricerca macchine (usato nei form)"""
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])

    macchine = Macchina.query.filter(
        or_(
            Macchina.codice.like(f'%{q}%'),
            Macchina.modello.like(f'%{q}%'),
            Macchina.marca.like(f'%{q}%')
        )
    ).limit(10).all()

    return jsonify([{
        'id': m.id,
        'codice': m.codice,
        'modello': m.modello,
        'marca': m.marca,
        'text': f'{m.codice} - {m.marca} {m.modello}'
    } for m in macchine])


@macchine_bp.route('/<int:macchina_id>/movimenti')
@login_required
def movimenti_macchina(macchina_id):
    """Mostra tutti i movimenti di una macchina"""
    macchina = Macchina.query.get_or_404(macchina_id)

    # Verifica permessi
    if not PermissionManager.can_view_machine(current_user, macchina):
        abort(403)

    # Paginazione movimenti
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    pagination = MovimentoMacchina.query.filter_by(macchina_id=macchina_id)\
        .order_by(MovimentoMacchina.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    movimenti = pagination.items

    return render_template('macchine/movimenti_macchina.html',
                         macchina=macchina,
                         movimenti=movimenti,
                         pagination=pagination)


@macchine_bp.route('/<int:macchina_id>/api/movimenti')
@login_required
def api_movimenti_macchina(macchina_id):
    """API per ottenere movimenti di una macchina"""
    macchina = Macchina.query.get_or_404(macchina_id)

    if not PermissionManager.can_view_machine(current_user, macchina):
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = MovimentoMacchina.query.filter_by(macchina_id=macchina_id)\
        .order_by(MovimentoMacchina.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'movimenti': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })


# ========== CRUD TipoMacchina ==========

@macchine_bp.route('/movimenti')
@login_required
def movimenti_generale():
    """Mostra tutti i movimenti di tutte le macchine"""
    # Verifica che l'utente possa visualizzare macchine
    # Gli utenti possono vedere movimenti se possono vedere macchine del loro reparto o tutti i reparti
    if not (current_user.has_permission('can_view_all_departments') or
            current_user.has_permission('can_manage_system') or
            (current_user.department_id and current_user.is_active)):
        abort(403)

    # Paginazione movimenti globali
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Filtro per macchina specifica (opzionale)
    macchina_id = request.args.get('macchina_id', type=int)
    if macchina_id:
        query = MovimentoMacchina.query.filter_by(macchina_id=macchina_id)
    else:
        query = MovimentoMacchina.query

    pagination = query.order_by(MovimentoMacchina.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    movimenti = pagination.items

    # Lista macchine per filtro
    macchine = Macchina.query.order_by(Macchina.codice).all()

    return render_template('macchine/movimenti_generale.html',
                         movimenti=movimenti,
                         pagination=pagination,
                         macchine=macchine,
                         filtro_macchina_id=macchina_id)


@macchine_bp.route('/tipi')
@login_required
def list_tipi_macchina():
    """Lista tipi di macchina"""
    if not current_user.has_permission('can_manage_system'):
        abort(403)

    tipi = TipoMacchina.query.order_by(TipoMacchina.nome).all()
    return render_template('macchine/tipi_macchina.html', tipi=tipi)


@macchine_bp.route('/tipi/create', methods=['GET', 'POST'])
@login_required
def create_tipo_macchina():
    """Crea nuovo tipo di macchina"""
    if not current_user.has_permission('can_manage_system'):
        abort(403)

    form = TipoMacchinaForm()

    if form.validate_on_submit():
        try:
            tipo = TipoMacchina(
                nome=form.nome.data,
                descrizione=form.descrizione.data
            )
            db.session.add(tipo)
            db.session.commit()

            flash('Tipo di macchina creato con successo!', 'success')
            return redirect(url_for('macchine.list_tipi_macchina'))

        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'danger')

    return render_template('macchine/form_tipo_macchina.html',
                         form=form,
                         title='Nuovo Tipo di Macchina',
                         action_url=url_for('macchine.create_tipo_macchina'))


@macchine_bp.route('/tipi/<int:tipo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tipo_macchina(tipo_id):
    """Modifica tipo di macchina"""
    if not current_user.has_permission('can_manage_system'):
        abort(403)

    tipo = TipoMacchina.query.get_or_404(tipo_id)
    form = TipoMacchinaForm(obj=tipo, tipo_macchina=tipo)

    if form.validate_on_submit():
        try:
            form.populate_obj(tipo)
            db.session.commit()

            flash('Tipo di macchina aggiornato con successo!', 'success')
            return redirect(url_for('macchine.list_tipi_macchina'))

        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'danger')

    return render_template('macchine/form_tipo_macchina.html',
                         form=form,
                         tipo=tipo,
                         title='Modifica Tipo di Macchina',
                         action_url=url_for('macchine.edit_tipo_macchina', tipo_id=tipo.id))


@macchine_bp.route('/tipi/<int:tipo_id>/delete', methods=['POST'])
@login_required
def delete_tipo_macchina(tipo_id):
    """Elimina tipo di macchina"""
    if not current_user.has_permission('can_manage_system'):
        abort(403)

    tipo = TipoMacchina.query.get_or_404(tipo_id)

    # Controlla se ci sono macchine associate
    if tipo.macchine.count() > 0:
        flash(f'Impossibile eliminare il tipo "{tipo.nome}": ci sono {tipo.macchine.count()} macchine associate.', 'danger')
        return redirect(url_for('macchine.list_tipi_macchina'))

    try:
        db.session.delete(tipo)
        db.session.commit()

        flash('Tipo di macchina eliminato con successo!', 'success')
        return redirect(url_for('macchine.list_tipi_macchina'))

    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
        return redirect(url_for('macchine.list_tipi_macchina'))
