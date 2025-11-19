from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func, extract, desc
from app import db
from app.models.foglio_tecnico import FoglioTecnico
from app.models.cliente import Cliente
from app.models.user import User
from app.models.macchina import Macchina
from app.models.ricambio import Ricambio
from app.forms.foglio_tecnico import (
    FoglioTecnicoStep1Form, FoglioTecnicoStep2Form, FoglioTecnicoStep3Form,
    FoglioTecnicoStep4Form, FoglioTecnicoStep5Form, FoglioTecnicoFinalizeForm,
    FoglioTecnicoFilterForm, FoglioTecnicoQuickEditForm
)
from app.utils.permissions import filter_by_department_access, PermissionManager, require_permission
from datetime import datetime, timedelta
import os
import base64
from werkzeug.utils import secure_filename

fogli_tecnici_bp = Blueprint('fogli_tecnici', __name__)


@fogli_tecnici_bp.route('/')
@login_required
def list_fogli():
    """Lista di tutti i fogli tecnici con filtri"""
    form = FoglioTecnicoFilterForm()
    
    # Query base - filtra per reparto accessibile
    query = filter_by_department_access(FoglioTecnico.query, FoglioTecnico)
    
    # Applica filtri da parametri URL
    search_term = request.args.get('search', '').strip()
    if search_term:
        form.search.data = search_term
        search_pattern = f"%{search_term}%"
        query = query.filter(or_(
            FoglioTecnico.titolo.like(search_pattern),
            FoglioTecnico.descrizione.like(search_pattern),
            FoglioTecnico.numero_foglio.like(search_pattern)
        ))
    
    stato_filter = request.args.get('stato', '').strip()
    if stato_filter:
        form.stato.data = stato_filter
        query = query.filter(FoglioTecnico.stato == stato_filter)
    
    categoria_filter = request.args.get('categoria', '').strip()
    if categoria_filter:
        form.categoria.data = categoria_filter
        query = query.filter(FoglioTecnico.categoria == categoria_filter)
    
    cliente_filter = request.args.get('cliente', '').strip()
    if cliente_filter:
        try:
            cliente_id = int(cliente_filter)
            if cliente_id > 0:
                form.cliente.data = cliente_id
                query = query.filter(FoglioTecnico.cliente_id == cliente_id)
        except (ValueError, TypeError):
            pass
    
    tecnico_filter = request.args.get('tecnico', '').strip()
    if tecnico_filter:
        try:
            tecnico_id = int(tecnico_filter)
            if tecnico_id > 0:
                form.tecnico.data = tecnico_id
                query = query.filter(FoglioTecnico.tecnico_id == tecnico_id)
        except (ValueError, TypeError):
            pass
    
    modalita_filter = request.args.get('modalita_pagamento', '').strip()
    if modalita_filter:
        form.modalita_pagamento.data = modalita_filter
        query = query.filter(FoglioTecnico.modalita_pagamento == modalita_filter)
    
    # Ordinamento (default: più recenti prima)
    query = query.order_by(desc(FoglioTecnico.created_at))
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 15
    fogli = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'fogli_tecnici/list.html',
        fogli=fogli,
        form=form,
        title='Fogli Tecnici'
    )


@fogli_tecnici_bp.route('/nuovo')
@login_required
def nuovo_foglio():
    """Inizia nuovo foglio tecnico - Redirect al Step 1"""
    return redirect(url_for('fogli_tecnici.step1'))


@fogli_tecnici_bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():
    """Step 1: Informazioni Base"""
    form = FoglioTecnicoStep1Form()
    
    if form.validate_on_submit():
        # Crea nuovo foglio tecnico
        foglio = FoglioTecnico(
            titolo=form.titolo.data,
            descrizione=form.descrizione.data,
            data_intervento=form.data_intervento.data,
            cliente_id=form.cliente.data,
            tecnico_id=current_user.id,  # Il tecnico corrente
            department_id=current_user.department_id,
            indirizzo_intervento=form.indirizzo_intervento.data,
            stato='In compilazione'
        )
        
        # Marca il step 1 come completato
        foglio.mark_step_completato(1)
        foglio.step_corrente = 2
        
        try:
            db.session.add(foglio)
            db.session.commit()
            
            flash('Step 1 completato! Procedi con i dettagli tecnici.', 'success')
            return redirect(url_for('fogli_tecnici.step2', id=foglio.id))
            
        except Exception as e:
            db.session.rollback()
            
            # Se è un errore di duplicato numero foglio, rigenera
            if 'Duplicate entry' in str(e) and 'numero_foglio' in str(e):
                # Forza rigenerazione numero foglio con timestamp
                import time
                current_year = datetime.utcnow().year
                timestamp_suffix = int(time.time() * 1000) % 10000
                foglio.numero_foglio = f'FT-{current_year}-{timestamp_suffix:04d}'
                
                try:
                    db.session.add(foglio)
                    db.session.commit()
                    
                    flash('Step 1 completato! Procedi con i dettagli tecnici.', 'success')
                    return redirect(url_for('fogli_tecnici.step2', id=foglio.id))
                    
                except Exception as e2:
                    db.session.rollback()
                    flash(f'Errore nella creazione del foglio tecnico: {str(e2)}', 'error')
            else:
                flash(f'Errore nella creazione del foglio tecnico: {str(e)}', 'error')
    
    return render_template(
        'fogli_tecnici/step1.html',
        form=form,
        title='Nuovo Foglio Tecnico - Step 1'
    )


@fogli_tecnici_bp.route('/step2/<int:id>', methods=['GET', 'POST'])
@login_required
def step2(id):
    """Step 2: Dettagli Tecnici"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    # Verifica permessi
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoStep2Form()
    
    # Popola le macchine del cliente selezionato
    if foglio.cliente_id:
        macchine = Macchina.query.filter_by(cliente_id=foglio.cliente_id).order_by(Macchina.codice).all()
        form.macchine.choices = [
            (macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}")
            for macchina in macchine
            if PermissionManager.can_view_machine(current_user, macchina)
        ]
    
    if request.method == 'GET':
        # Pre-popola form con dati esistenti
        form.durata_intervento.data = foglio.durata_intervento
        form.km_percorsi.data = foglio.km_percorsi
        form.tipo_operazione_macchine.data = foglio.tipo_operazione_macchine
        
        # Pre-seleziona macchine già collegate
        macchine_ids = [m.id for m in foglio.macchine_collegate]
        form.macchine.data = macchine_ids
    
    if form.validate_on_submit():
        # Import necessari
        from app.models.foglio_tecnico import foglio_macchine
        
        # Aggiorna foglio
        foglio.durata_intervento = form.durata_intervento.data
        foglio.km_percorsi = form.km_percorsi.data
        foglio.tipo_operazione_macchine = form.tipo_operazione_macchine.data
        foglio.updated_at = datetime.utcnow()
        
        # Aggiorna macchine collegate
        # Rimuovi tutte le associazioni esistenti
        db.session.execute(
            foglio_macchine.delete().where(foglio_macchine.c.foglio_id == foglio.id)
        )
        
        # Aggiungi nuove associazioni se presenti
        macchine_selezionate = request.form.get('macchine', '')
        if macchine_selezionate:
            macchine_ids = [int(mid) for mid in macchine_selezionate.split(',') if mid.strip().isdigit()]
            for macchina_id in macchine_ids:
                macchina = Macchina.query.get(macchina_id)
                if macchina and PermissionManager.can_view_machine(current_user, macchina):
                    foglio.macchine_collegate.append(macchina)

        # Gestisci operazioni sulle macchine (solo se specificato tipo operazione)
        if macchine_selezionate and form.tipo_operazione_macchine.data:
            tipo_operazione = form.tipo_operazione_macchine.data
            
            for macchina_id in macchine_ids:
                macchina = Macchina.query.get(macchina_id)
                if macchina and PermissionManager.can_view_machine(current_user, macchina):
                    try:
                        if tipo_operazione == 'prestito_semplice':
                            # Presta macchina al cliente (anche se attiva presso altro cliente)
                            if macchina.is_disponibile or macchina.is_attiva:
                                if macchina.is_disponibile:
                                    # Macchina disponibile - usa metodo standard
                                    movimento = macchina.assegna_a_cliente(
                                        foglio.cliente_id, 
                                        'In prestito', 
                                        f'Prestito semplice per foglio tecnico {foglio.numero_foglio}'
                                    )
                                else:
                                    # Macchina attiva - usa prestito temporaneo
                                    movimento = macchina.presta_temporaneamente(
                                        foglio.cliente_id,
                                        f'Prestito semplice per foglio tecnico {foglio.numero_foglio}'
                                    )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede':
                            # Porta macchina in sede per riparazione (solo ritiro)
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede per foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede_con_prestito':
                            # Porta macchina del cliente in riparazione (solo se non già in riparazione)
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede con prestito per foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_cliente':
                            # Riparazione presso cliente - non cambia stato ma registra movimento
                            from app.models.macchina import MovimentoMacchina
                            movimento = MovimentoMacchina(
                                macchina_id=macchina.id,
                                tipo_movimento='Riparazione presso cliente',
                                stato_precedente=macchina.stato,
                                stato_nuovo=macchina.stato,
                                cliente_id=foglio.cliente_id,
                                foglio_id=foglio.id,
                                user_id=current_user.id,
                                note=f'Riparazione presso cliente per foglio tecnico {foglio.numero_foglio}'
                            )
                            db.session.add(movimento)
                        elif tipo_operazione == 'ritiro_riparazione':
                            # Ritira macchina per riparazione
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Ritiro per riparazione - foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'consegna_riparata':
                            # Consegna macchina riparata
                            if macchina.is_in_riparazione:
                                movimento = macchina.completa_riparazione(
                                    f'Consegna macchina riparata - foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'rientro_prestito':
                            # Rientro da prestito - riporta in magazzino
                            if macchina.is_in_prestito:
                                movimento = macchina.riporta_in_magazzino(
                                    f'Rientro da prestito - foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'rientro_riparazione':
                            # Rientro da riparazione - macchina riparata torna disponibile
                            if macchina.is_in_riparazione:
                                movimento = macchina.completa_riparazione(
                                    f'Rientro da riparazione - foglio tecnico {foglio.numero_foglio}'
                                )
                                movimento.foglio_id = foglio.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'altro':
                            # Movimento generico
                            from app.models.macchina import MovimentoMacchina
                            movimento = MovimentoMacchina(
                                macchina_id=macchina.id,
                                tipo_movimento='Altro',
                                stato_precedente=macchina.stato,
                                stato_nuovo=macchina.stato,
                                cliente_id=foglio.cliente_id,
                                foglio_id=foglio.id,
                                user_id=current_user.id,
                                note=f'Operazione per foglio tecnico {foglio.numero_foglio}'
                            )
                            db.session.add(movimento)
                    except Exception as e:
                        flash(f'Errore nell\'operazione sulla macchina {macchina.codice}: {str(e)}', 'warning')
                        current_app.logger.error(f'Errore operazione macchina {macchina.id}: {str(e)}')
        
        # Gestisci macchine sostitutive per riparazione con prestito
        if form.tipo_operazione_macchine.data == 'riparazione_sede_con_prestito':
            macchine_sostitutive_selezionate = request.form.get('macchine_sostitutive', '')
            if macchine_sostitutive_selezionate:
                macchine_sostitutive_ids = [int(mid) for mid in macchine_sostitutive_selezionate.split(',') if mid.strip().isdigit()]
                for macchina_sostitutiva_id in macchine_sostitutive_ids:
                    macchina_sostitutiva = Macchina.query.get(macchina_sostitutiva_id)
                    if macchina_sostitutiva and macchina_sostitutiva.is_disponibile and PermissionManager.can_view_machine(current_user, macchina_sostitutiva):
                        try:
                            movimento = macchina_sostitutiva.assegna_a_cliente(
                                foglio.cliente_id,
                                'In prestito',
                                f'Prestito sostitutivo durante riparazione per foglio tecnico {foglio.numero_foglio}'
                            )
                            movimento.foglio_id = foglio.id
                            movimento.user_id = current_user.id
                        except Exception as e:
                            flash(f'Errore nell\'assegnazione della macchina sostitutiva {macchina_sostitutiva.codice}: {str(e)}', 'warning')
        
        # Marca step come completato
        foglio.mark_step_completato(2)
        foglio.step_corrente = 3
        
        db.session.commit()
        
        flash('Step 2 completato! Procedi con i ricambi.', 'success')
        return redirect(url_for('fogli_tecnici.step3', id=foglio.id))
    
    return render_template(
        'fogli_tecnici/step2.html',
        form=form,
        foglio=foglio,
        title=f'Foglio {foglio.numero_foglio} - Step 2'
    )


@fogli_tecnici_bp.route('/step3/<int:id>', methods=['GET', 'POST'])
@login_required  
def step3(id):
    """Step 3: Ricambi Utilizzati"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoStep3Form()
    
    if request.method == 'GET':
        # Pre-popola form con dati esistenti
        form.note_aggiuntive.data = foglio.note_aggiuntive
        
        # Pre-seleziona ricambi già collegati
        ricambi_ids = [r.id for r in foglio.ricambi_utilizzati]
        form.ricambi_utilizzati.data = ricambi_ids
    
    if form.validate_on_submit():
        # Aggiorna foglio
        foglio.note_aggiuntive = form.note_aggiuntive.data
        foglio.updated_at = datetime.utcnow()
        
        # Aggiorna ricambi utilizzati
        # Rimuovi tutte le associazioni esistenti
        from app.models.foglio_tecnico import foglio_ricambi
        db.session.execute(
            foglio_ricambi.delete().where(foglio_ricambi.c.foglio_id == foglio.id)
        )
        
        # Aggiungi nuove associazioni se presenti
        ricambi_selezionati = request.form.get('ricambi_utilizzati', '')
        if ricambi_selezionati:
            ricambi_ids = [int(rid) for rid in ricambi_selezionati.split(',') if rid.strip().isdigit()]
            for ricambio_id in ricambi_ids:
                ricambio = Ricambio.query.get(ricambio_id)
                if ricambio:
                    foglio.ricambi_utilizzati.append(ricambio)
        
        # Marca step come completato
        foglio.mark_step_completato(3)
        foglio.step_corrente = 4
        
        db.session.commit()
        
        flash('Step 3 completato! Procedi con le informazioni commerciali.', 'success')
        return redirect(url_for('fogli_tecnici.step4', id=foglio.id))
    
    return render_template(
        'fogli_tecnici/step3.html',
        form=form,
        foglio=foglio,
        title=f'Foglio {foglio.numero_foglio} - Step 3'
    )


@fogli_tecnici_bp.route('/step4/<int:id>', methods=['GET', 'POST'])
@login_required
def step4(id):
    """Step 4: Informazioni Commerciali"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoStep4Form()
    
    if request.method == 'GET':
        # Pre-popola form con dati esistenti
        form.modalita_pagamento.data = foglio.modalita_pagamento
        form.importo_intervento.data = foglio.importo_intervento
    
    if form.validate_on_submit():
        # Aggiorna foglio
        foglio.modalita_pagamento = form.modalita_pagamento.data
        foglio.importo_intervento = form.importo_intervento.data
        foglio.updated_at = datetime.utcnow()
        
        # Marca step come completato
        foglio.mark_step_completato(4)
        foglio.step_corrente = 5
        
        db.session.commit()
        
        flash('Step 4 completato! Procedi con la raccolta firme.', 'success')
        return redirect(url_for('fogli_tecnici.step5', id=foglio.id))
    
    return render_template(
        'fogli_tecnici/step4.html',
        form=form,
        foglio=foglio,
        title=f'Foglio {foglio.numero_foglio} - Step 4'
    )


@fogli_tecnici_bp.route('/step5/<int:id>', methods=['GET', 'POST'])
@login_required
def step5(id):
    """Step 5: Raccolta Firme"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoStep5Form()
    
    if request.method == 'GET':
        # Pre-popola form con dati esistenti
        form.nome_firmatario_cliente.data = foglio.nome_firmatario_cliente
    
    if form.validate_on_submit():
        # Aggiorna foglio
        foglio.nome_firmatario_cliente = form.nome_firmatario_cliente.data
        foglio.updated_at = datetime.utcnow()
        
        # Salva firme se presenti
        if form.firma_tecnico_data.data:
            _save_signature(foglio, 'tecnico', form.firma_tecnico_data.data)
        
        if form.firma_cliente_data.data:
            _save_signature(foglio, 'cliente', form.firma_cliente_data.data)
        
        # Marca step come completato
        foglio.mark_step_completato(5)
        foglio.stato = 'In attesa firme' if not (foglio.firma_tecnico_path and foglio.firma_cliente_path) else 'Completato'
        
        db.session.commit()
        
        flash('Step 5 completato! Procedi con la finalizzazione.', 'success')
        return redirect(url_for('fogli_tecnici.finalize', id=foglio.id))
    
    return render_template(
        'fogli_tecnici/step5.html',
        form=form,
        foglio=foglio,
        title=f'Foglio {foglio.numero_foglio} - Raccolta Firme'
    )


@fogli_tecnici_bp.route('/finalize/<int:id>', methods=['GET', 'POST'])
@login_required
def finalize(id):
    """Finalizzazione del foglio tecnico"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoFinalizeForm()
    
    # Pre-popola email del cliente se disponibile
    if request.method == 'GET' and not form.email_destinatario.data:
        if foglio.cliente and foglio.cliente.email:
            form.email_destinatario.data = foglio.cliente.email
    
    if form.validate_on_submit():
        azione = form.azione.data
        
        try:
            if azione == 'salva_bozza':
                foglio.stato = 'Completato'
                foglio.completed_at = datetime.utcnow()
                
            elif azione == 'genera_pdf':
                from app.services.pdf_generator import genera_pdf_foglio_tecnico
                pdf_path = genera_pdf_foglio_tecnico(foglio.id)
                foglio.stato = 'Completato'
                foglio.completed_at = datetime.utcnow()
                flash(f'PDF generato: {os.path.basename(pdf_path)}', 'success')
                
            elif azione == 'invia_email':
                from app.services.email_sender import invia_foglio_per_email
                invia_foglio_per_email(
                    foglio.id, 
                    form.email_destinatario.data,
                    form.note_finali.data
                )
                flash(f'Foglio inviato a {form.email_destinatario.data}', 'success')
                
            elif azione == 'genera_e_invia':
                from app.services.pdf_generator import genera_pdf_foglio_tecnico
                from app.services.email_sender import invia_foglio_per_email
                
                pdf_path = genera_pdf_foglio_tecnico(foglio.id)
                invia_foglio_per_email(
                    foglio.id,
                    form.email_destinatario.data, 
                    form.note_finali.data
                )
                flash(f'PDF generato e inviato a {form.email_destinatario.data}', 'success')
            
            db.session.commit()
            return redirect(url_for('fogli_tecnici.view', id=foglio.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'operazione: {str(e)}', 'error')
    
    return render_template(
        'fogli_tecnici/finalize.html',
        form=form,
        foglio=foglio,
        title=f'Finalizza Foglio {foglio.numero_foglio}'
    )


@fogli_tecnici_bp.route('/view/<int:id>')
@login_required
def view(id):
    """Visualizza dettagli foglio tecnico"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_view_foglio_tecnico(current_user, foglio):
        abort(403)
    
    # Se il foglio è in compilazione, reindirizza alla fase di creazione corrente
    if foglio.stato in ['Bozza', 'In compilazione', 'In attesa firme']:
        step_route = f'fogli_tecnici.step{foglio.step_corrente}'
        flash(f'Il foglio è ancora in compilazione. Continua dal passo {foglio.step_corrente}.', 'info')
        return redirect(url_for(step_route, id=foglio.id))
    
    # Ottieni i movimenti delle macchine collegati a questo foglio
    from app.models.macchina import MovimentoMacchina
    movimenti_macchine = MovimentoMacchina.query.filter_by(foglio_id=foglio.id).order_by(MovimentoMacchina.created_at.desc()).all()
    
    # Solo i fogli completati possono essere visualizzati in dettaglio
    return render_template(
        'fogli_tecnici/view.html',
        foglio=foglio,
        movimenti_macchine=movimenti_macchine,
        title=f'Foglio {foglio.numero_foglio}'
    )


@fogli_tecnici_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifica rapida di un foglio esistente"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    form = FoglioTecnicoQuickEditForm()
    
    if request.method == 'GET':
        form.titolo.data = foglio.titolo
        form.descrizione.data = foglio.descrizione
        form.stato.data = foglio.stato
        form.note_aggiuntive.data = foglio.note_aggiuntive
    
    if form.validate_on_submit():
        foglio.titolo = form.titolo.data
        foglio.descrizione = form.descrizione.data
        foglio.stato = form.stato.data
        foglio.note_aggiuntive = form.note_aggiuntive.data
        foglio.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Foglio aggiornato con successo!', 'success')
        return redirect(url_for('fogli_tecnici.view', id=foglio.id))
    
    return render_template(
        'fogli_tecnici/edit.html',
        form=form,
        foglio=foglio,
        title=f'Modifica Foglio {foglio.numero_foglio}'
    )


@fogli_tecnici_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Elimina un foglio tecnico"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    # Verifica che l'utente possa eliminare il foglio
    if not PermissionManager.can_edit_foglio_tecnico(current_user, foglio):
        abort(403)
    
    try:
        # PRIMA DI ELIMINARE: Ripristina stati originali delle macchine
        _ripristina_stati_macchine_foglio(foglio)
        
        # Elimina file firme se esistono
        if foglio.firma_tecnico_path and os.path.exists(foglio.firma_tecnico_path):
            os.remove(foglio.firma_tecnico_path)
        
        if foglio.firma_cliente_path and os.path.exists(foglio.firma_cliente_path):
            os.remove(foglio.firma_cliente_path)
        
        # Elimina PDF se esiste
        if foglio.pdf_path and os.path.exists(foglio.pdf_path):
            os.remove(foglio.pdf_path)
        
        numero_foglio = foglio.numero_foglio
        db.session.delete(foglio)
        db.session.commit()
        
        flash(f'Foglio {numero_foglio} eliminato con successo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('fogli_tecnici.list_fogli'))


# API Routes
@fogli_tecnici_bp.route('/api/client_machines/<int:cliente_id>')
@login_required
def get_client_machines(cliente_id):
    """API per ottenere macchine di un cliente (per AJAX)"""
    try:
        macchine = Macchina.query.filter_by(cliente_id=cliente_id).order_by(Macchina.codice).all()
        
        machines_data = []
        for macchina in macchine:
            if PermissionManager.can_view_machine(current_user, macchina):
                machines_data.append({
                    'id': macchina.id,
                    'codice': macchina.codice,
                    'marca': macchina.marca,
                    'modello': macchina.modello,
                    'display': f"{macchina.codice} - {macchina.marca} {macchina.modello}"
                })
        
        return jsonify({
            'success': True,
            'machines': machines_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@fogli_tecnici_bp.route('/api/search_clients')
@login_required
def search_clients():
    """API per cercare clienti (autocomplete)"""
    query = request.args.get('q', '').strip()
    
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        # Ricerca case-insensitive in ragione sociale, codice fiscale e email
        clienti = Cliente.query.filter(
            and_(
                Cliente.is_active == True,
                or_(
                    Cliente.ragione_sociale.ilike(f'%{query}%'),
                    Cliente.codice_fiscale.ilike(f'%{query}%') if query else False,
                    Cliente.email.ilike(f'%{query}%') if query else False
                )
            )
        ).order_by(Cliente.ragione_sociale).limit(10).all()
        
        
        results = []
        for cliente in clienti:
            if PermissionManager.can_view_client(current_user, cliente):
                results.append({
                    'id': cliente.id,
                    'text': cliente.ragione_sociale,
                    'email': cliente.email or '',
                    'subtitle': f'{cliente.codice_fiscale or "N/A"} - {cliente.email or "Nessuna email"}'
                })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fogli_tecnici_bp.route('/api/get_available_machines')
@login_required
def get_available_machines():
    """API per ottenere le macchine disponibili per prestito sostitutivo"""
    try:
        # Ottieni solo le macchine disponibili
        macchine = Macchina.query.filter_by(stato='Disponibile').order_by(Macchina.codice).all()
        
        # Filtra per permessi e dipartimento
        macchine_filtrate = [
            macchina for macchina in macchine 
            if PermissionManager.can_view_machine(current_user, macchina)
        ]
        
        machines_data = [
            {
                'id': macchina.id,
                'codice': macchina.codice,
                'marca': macchina.marca,
                'modello': macchina.modello,
                'stato': macchina.stato,
                'ubicazione': macchina.ubicazione or 'Magazzino'
            }
            for macchina in macchine_filtrate
        ]
        
        return jsonify({
            'success': True,
            'machines': machines_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fogli_tecnici_bp.route('/api/get_client_ongoing_operations/<int:cliente_id>')
@login_required
def get_client_ongoing_operations(cliente_id):
    """API per ottenere le operazioni in corso per un cliente"""
    try:
        from app.models.macchina import MovimentoMacchina
        
        # Verifica che l'utente possa vedere questo cliente
        cliente = Cliente.query.get_or_404(cliente_id)
        
        if not PermissionManager.can_view_cliente(current_user, cliente):
            return jsonify({'success': False, 'error': 'Permessi insufficienti'}), 403
        
        # Trova macchine del cliente in prestito (nostre macchine presso il cliente)
        macchine_in_prestito = Macchina.query.filter(
            and_(
                Macchina.cliente_id == cliente_id,
                Macchina.stato == 'In prestito'
            )
        ).all()
        
        # Trova macchine del cliente in riparazione presso di noi
        macchine_in_riparazione = Macchina.query.filter(
            and_(
                Macchina.stato == 'In riparazione'
            )
        ).all()
        
        # Filtra le macchine in riparazione che appartengono al cliente
        # (controllando i movimenti per trovare quelle che erano "Attiva" presso questo cliente)
        macchine_cliente_in_riparazione = []
        for macchina in macchine_in_riparazione:
            ultimo_movimento = MovimentoMacchina.query.filter_by(macchina_id=macchina.id).order_by(MovimentoMacchina.created_at.desc()).first()
            if ultimo_movimento and ultimo_movimento.cliente_originale_id == cliente_id:
                macchine_cliente_in_riparazione.append(macchina)
        
        # Prepara i dati per il frontend
        operazioni_in_corso = []
        
        # Macchine nostre in prestito presso il cliente
        for macchina in macchine_in_prestito:
            if PermissionManager.can_view_machine(current_user, macchina):
                operazioni_in_corso.append({
                    'tipo': 'prestito_nostro',
                    'macchina': {
                        'id': macchina.id,
                        'codice': macchina.codice,
                        'marca': macchina.marca,
                        'modello': macchina.modello,
                        'stato': macchina.stato
                    },
                    'descrizione': f'Nostra macchina {macchina.codice} in prestito presso cliente',
                    'operazione_suggerita': 'rientro_prestito',
                    'operazione_suggerita_label': 'Rientro da prestito'
                })
        
        # Macchine del cliente in riparazione presso di noi
        for macchina in macchine_cliente_in_riparazione:
            if PermissionManager.can_view_machine(current_user, macchina):
                operazioni_in_corso.append({
                    'tipo': 'riparazione_cliente',
                    'macchina': {
                        'id': macchina.id,
                        'codice': macchina.codice,
                        'marca': macchina.marca,
                        'modello': macchina.modello,
                        'stato': macchina.stato
                    },
                    'descrizione': f'Macchina cliente {macchina.codice} in riparazione presso di noi',
                    'operazione_suggerita': 'consegna_riparata',
                    'operazione_suggerita_label': 'Consegna macchina riparata'
                })
        
        return jsonify({
            'success': True,
            'operazioni_in_corso': operazioni_in_corso,
            'has_operations': len(operazioni_in_corso) > 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fogli_tecnici_bp.route('/download_pdf/<int:id>')
@login_required
def download_pdf(id):
    """Scarica il PDF di un foglio tecnico"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_view_foglio_tecnico(current_user, foglio):
        abort(403)
    
    # Verifica che il PDF esista
    if not foglio.pdf_generato or not foglio.pdf_path or not os.path.exists(foglio.pdf_path):
        # Genera PDF se non esiste
        try:
            from app.services.pdf_generator import genera_pdf_foglio_tecnico
            pdf_path = genera_pdf_foglio_tecnico(foglio.id)
        except Exception as e:
            flash(f'Errore nella generazione del PDF: {str(e)}', 'error')
            return redirect(url_for('fogli_tecnici.view', id=foglio.id))
    else:
        pdf_path = foglio.pdf_path
    
    # Invia file
    directory = os.path.dirname(pdf_path)
    filename = os.path.basename(pdf_path)
    
    return send_from_directory(
        directory, 
        filename, 
        as_attachment=True,
        download_name=f"FoglioTecnico_{foglio.numero_foglio}.pdf"
    )


@fogli_tecnici_bp.route('/generate_pdf/<int:id>')
@login_required
def generate_pdf(id):
    """Genera il PDF di un foglio tecnico"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_view_foglio_tecnico(current_user, foglio):
        abort(403)
    
    try:
        from app.services.pdf_generator import genera_pdf_foglio_tecnico
        pdf_path = genera_pdf_foglio_tecnico(foglio.id)
        flash('PDF generato con successo!', 'success')
        
    except Exception as e:
        flash(f'Errore nella generazione del PDF: {str(e)}', 'error')
    
    return redirect(url_for('fogli_tecnici.view', id=foglio.id))


@fogli_tecnici_bp.route('/preview_html/<int:id>')
@login_required
def preview_html(id):
    """Anteprima HTML del foglio tecnico con il nuovo design moderno"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_view_foglio_tecnico(current_user, foglio):
        abort(403)
    
    try:
        from app.services.pdf_generator import get_signature_base64
        from datetime import datetime
        
        # Render del template HTML direttamente
        return render_template(
            'fogli_tecnici/pdf_template.html',
            foglio=foglio,
            timestamp=datetime.now().strftime('%d/%m/%Y alle %H:%M'),
            is_html=True,
            get_signature_base64=get_signature_base64
        )
        
    except Exception as e:
        flash(f'Errore nella generazione dell\'anteprima: {str(e)}', 'error')
        return redirect(url_for('fogli_tecnici.view', id=foglio.id))


@fogli_tecnici_bp.route('/send_email/<int:id>', methods=['GET', 'POST'])
@login_required
def send_email(id):
    """Invia foglio tecnico per email"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_finalize_foglio_tecnico(current_user, foglio):
        abort(403)
    
    if request.method == 'POST':
        email_destinatario = request.form.get('email_destinatario')
        note_aggiuntive = request.form.get('note_aggiuntive', '')
        
        if not email_destinatario:
            flash('Email destinatario obbligatoria', 'error')
            return redirect(url_for('fogli_tecnici.send_email', id=foglio.id))
        
        try:
            from app.services.email_sender import invia_foglio_per_email
            invia_foglio_per_email(foglio.id, email_destinatario, note_aggiuntive)
            flash(f'Foglio inviato con successo a {email_destinatario}', 'success')
            return redirect(url_for('fogli_tecnici.view', id=foglio.id))
            
        except Exception as e:
            flash(f'Errore nell\'invio dell\'email: {str(e)}', 'error')
    
    # GET - mostra form di invio
    email_default = foglio.cliente.email if foglio.cliente else ''
    
    return render_template(
        'fogli_tecnici/send_email_form.html',
        foglio=foglio,
        email_default=email_default,
        title=f'Invia Foglio {foglio.numero_foglio}'
    )


@fogli_tecnici_bp.route('/api/ricambi_department')
@login_required
def api_ricambi_department():
    """API per ottenere ricambi filtrati per reparto dell'utente corrente"""
    try:
        # Filtra ricambi per reparto accessibile
        from app.utils.permissions import filter_by_department_access
        ricambi_query = filter_by_department_access(Ricambio.query, Ricambio)

        # Aggiungi filtri aggiuntivi se necessario
        search_term = request.args.get('search', '').strip()
        if search_term:
            ricambi_query = ricambi_query.filter(
                or_(
                    Ricambio.codice.ilike(f'%{search_term}%'),
                    Ricambio.descrizione.ilike(f'%{search_term}%')
                )
            )

        # Limita risultati per performance
        ricambi = ricambi_query.order_by(Ricambio.codice).limit(1000).all()

        results = []
        for ricambio in ricambi:
            results.append({
                'id': ricambio.id,
                'codice': ricambio.codice,
                'descrizione': ricambio.descrizione,
                'quantita': ricambio.quantita_disponibile,
                'stato': ricambio.stato_disponibilita,
                'ubicazione': ricambio.ubicazione or '',
                'fornitore': ricambio.fornitore or '',
                'prezzo_unitario': float(ricambio.prezzo_unitario) if ricambio.prezzo_unitario else None
            })

        return jsonify({
            'success': True,
            'ricambi': results,
            'total': len(results)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@fogli_tecnici_bp.route('/view_signature/<int:id>/<tipo>')
@login_required
def view_signature(id, tipo):
    """Visualizza una firma salvata"""
    foglio = FoglioTecnico.query.get_or_404(id)
    
    if not PermissionManager.can_view_foglio_tecnico(current_user, foglio):
        abort(403)
    
    # Verifica tipo firma
    if tipo == 'tecnico':
        signature_path = foglio.firma_tecnico_path
    elif tipo == 'cliente':
        signature_path = foglio.firma_cliente_path
    else:
        abort(404)
    
    # Verifica che il file esista
    if not signature_path or not os.path.exists(signature_path):
        abort(404)
    
    # Invia file
    directory = os.path.dirname(signature_path)
    filename = os.path.basename(signature_path)
    
    return send_from_directory(directory, filename)


def _save_signature(foglio, tipo, signature_data):
    """Salva una firma su file"""
    try:
        # Decodifica base64
        if signature_data.startswith('data:image/png;base64,'):
            signature_data = signature_data.replace('data:image/png;base64,', '')
        
        signature_bytes = base64.b64decode(signature_data)
        
        # Crea cartella se non esiste
        signatures_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'signatures')
        os.makedirs(signatures_dir, exist_ok=True)
        
        # Nome file sicuro
        filename = f"{foglio.numero_foglio}_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(signatures_dir, filename)
        
        # Salva file
        with open(filepath, 'wb') as f:
            f.write(signature_bytes)
        
        # Aggiorna foglio
        if tipo == 'tecnico':
            foglio.firma_tecnico_path = filepath
        else:
            foglio.firma_cliente_path = filepath
        
        return filepath
        
    except Exception as e:
        return None


def _ripristina_stati_macchine_foglio(foglio):
    """
    Ripristina gli stati originali delle macchine quando si elimina un foglio tecnico.
    Utilizza i dati salvati nei MovimentoMacchina per ripristinare lo stato precedente.
    """
    from app.models.macchina import MovimentoMacchina
    
    try:
        # Trova tutti i movimenti collegati a questo foglio
        movimenti = MovimentoMacchina.query.filter_by(foglio_id=foglio.id).order_by(MovimentoMacchina.created_at.desc()).all()
        
        macchine_ripristinate = set()
        
        for movimento in movimenti:
            macchina = movimento.macchina
            if not macchina:
                # Salta movimenti con macchina non esistente (eliminata)
                current_app.logger.warning(f'Macchina ID {movimento.macchina_id} non trovata per ripristino foglio {foglio.numero_foglio}')
                continue

            if macchina.id in macchine_ripristinate:
                # Salta macchine già ripristinate
                continue
                
            # Ripristina lo stato originale della macchina
            if movimento.cliente_originale_id is not None:
                # La macchina aveva un cliente originale - ripristina stato completo
                macchina.cliente_id = movimento.cliente_originale_id
                macchina.stato = 'Attiva' if movimento.cliente_originale_id else 'Disponibile'
                macchina.ubicazione = movimento.ubicazione_originale
                macchina.data_assegnazione = movimento.data_assegnazione_originale
                macchina.data_vendita = movimento.data_vendita_originale
                macchina.prezzo_vendita = movimento.prezzo_vendita_originale
                macchina.prossima_manutenzione = movimento.prossima_manutenzione_originale
                
                # Crea movimento di ripristino
                movimento_ripristino = MovimentoMacchina(
                    macchina_id=macchina.id,
                    tipo_movimento='Ripristino automatico',
                    stato_precedente=macchina.stato,
                    stato_nuovo='Attiva' if movimento.cliente_originale_id else 'Disponibile',
                    cliente_id=movimento.cliente_originale_id,
                    user_id=current_user.id,
                    note=f'Ripristino automatico per eliminazione foglio {foglio.numero_foglio}'
                )
                db.session.add(movimento_ripristino)
                
            else:
                # Ripristina solo lo stato precedente
                if movimento.stato_precedente:
                    macchina.stato = movimento.stato_precedente
                    
                    # Se era disponibile, rimuovi cliente
                    if movimento.stato_precedente == 'Disponibile':
                        macchina.cliente_id = None
                        macchina.ubicazione = 'Magazzino'
                    
                    # Crea movimento di ripristino
                    movimento_ripristino = MovimentoMacchina(
                        macchina_id=macchina.id,
                        tipo_movimento='Ripristino automatico',
                        stato_precedente=macchina.stato,
                        stato_nuovo=movimento.stato_precedente,
                        user_id=current_user.id,
                        note=f'Ripristino automatico per eliminazione foglio {foglio.numero_foglio}'
                    )
                    db.session.add(movimento_ripristino)
            
            macchine_ripristinate.add(macchina.id)
            current_app.logger.info(f'Ripristinato stato macchina {macchina.codice} per eliminazione foglio {foglio.numero_foglio}')
        
        # Elimina i movimenti originali del foglio
        MovimentoMacchina.query.filter_by(foglio_id=foglio.id).delete()
        
        if macchine_ripristinate:
            current_app.logger.info(f'Ripristinati stati di {len(macchine_ripristinate)} macchine per eliminazione foglio {foglio.numero_foglio}')
            
    except Exception as e:
        current_app.logger.error(f'Errore nel ripristino stati macchine per foglio {foglio.numero_foglio}: {str(e)}')
        # Non rilanciare l'errore per non bloccare l'eliminazione del foglio
        pass
