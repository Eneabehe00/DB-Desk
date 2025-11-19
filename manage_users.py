#!/usr/bin/env python3
"""
Script completo per gestire utenti (creare, eliminare, riassegnare ticket)
"""

import sys
import os

# Aggiungi il percorso del progetto al path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from getpass import getpass

def show_menu():
    print("\n" + "="*50)
    print("🔧 GESTIONE UTENTI DB-DESK")
    print("="*50)
    print("1. 👤 Visualizza tutti gli utenti")
    print("2. ➕ Crea nuovo utente")
    print("3. 🔑 Crea nuovo amministratore")
    print("4. 🗑️  Elimina utente (con riassegnazione ticket)")
    print("5. 🔄 Reset password utente")
    print("0. ❌ Esci")
    print("="*50)

def list_users():
    """Visualizza tutti gli utenti"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    print(f"\n📋 UTENTI REGISTRATI ({len(users)} totali)")
    print("-" * 80)
    print(f"{'ID':<4} {'Username':<15} {'Nome Completo':<25} {'Admin':<8} {'Stato':<8} {'Creato'}")
    print("-" * 80)
    
    for user in users:
        admin = "🔑 Sì" if user.is_admin else "👤 No"
        status = "✅ Attivo" if user.is_active else "❌ Inattivo"
        created = user.created_at.strftime('%d/%m/%Y')
        
        print(f"{user.id:<4} {user.username:<15} {user.full_name:<25} {admin:<8} {status:<8} {created}")
    
    print("-" * 80)

def create_user(is_admin=False):
    """Crea un nuovo utente"""
    print(f"\n➕ CREA NUOVO {'AMMINISTRATORE' if is_admin else 'UTENTE'}")
    print("-" * 40)
    
    # Username
    while True:
        username = input("Username: ").strip()
        if not username:
            print("❌ Username obbligatorio!")
            continue
            
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' già esistente!")
            continue
        break
    
    # Nome e cognome
    first_name = input("Nome: ").strip()
    if not first_name:
        print("❌ Nome obbligatorio!")
        return
        
    last_name = input("Cognome: ").strip()
    if not last_name:
        print("❌ Cognome obbligatorio!")
        return
    
    # Email
    while True:
        email = input("Email: ").strip()
        if not email:
            print("❌ Email obbligatoria!")
            continue
            
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' già esistente!")
            continue
        break
    
    # Password
    while True:
        password = getpass("Password: ")
        if len(password) < 6:
            print("❌ La password deve essere di almeno 6 caratteri!")
            continue
            
        password_confirm = getpass("Conferma password: ")
        if password != password_confirm:
            print("❌ Le password non coincidono!")
            continue
        break
    
    try:
        # Crea il nuovo utente
        new_user = User(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        role = "amministratore" if is_admin else "utente"
        print(f"\n✅ {role.title()} '{username}' creato con successo!")
        print(f"📋 Dettagli:")
        print(f"   Nome completo: {new_user.full_name}")
        print(f"   Email: {new_user.email}")
        print(f"   Ruolo: {'Amministratore' if new_user.is_admin else 'Utente'}")
        print(f"   Stato: {'Attivo' if new_user.is_active else 'Inattivo'}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Errore durante la creazione: {str(e)}")

def delete_user():
    """Elimina un utente con riassegnazione ticket"""
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    if len(users) <= 1:
        print("❌ Impossibile eliminare utenti: deve rimanere almeno un utente attivo!")
        return
    
    print(f"\n🗑️  ELIMINA UTENTE")
    print("-" * 40)
    print("Utenti disponibili per eliminazione:")
    
    for i, user in enumerate(users, 1):
        admin = "🔑" if user.is_admin else "👤"
        tickets_created = user.created_tickets.count()
        tickets_assigned = user.assigned_tickets.count()
        print(f"{i}. {admin} {user.username} - {user.full_name} (Ticket: {tickets_created} creati, {tickets_assigned} assegnati)")
    
    print("0. Annulla")
    
    # Selezione utente
    while True:
        try:
            choice = input(f"\nSeleziona utente da eliminare (1-{len(users)}) o 0 per annullare: ").strip()
            choice = int(choice)
            
            if choice == 0:
                print("Operazione annullata.")
                return
                
            if 1 <= choice <= len(users):
                user_to_delete = users[choice - 1]
                break
            else:
                print("❌ Selezione non valida!")
        except ValueError:
            print("❌ Inserisci un numero valido!")
    
    # Verifica se può essere eliminato
    can_delete, reason = user_to_delete.can_be_deleted()
    if not can_delete:
        print(f"❌ {reason}")
        return
    
    # Mostra informazioni sui ticket
    tickets_created = user_to_delete.created_tickets.count()
    tickets_assigned = user_to_delete.assigned_tickets.count()
    total_tickets = tickets_created + tickets_assigned
    
    print(f"\n⚠️  ATTENZIONE!")
    print(f"   Utente da eliminare: {user_to_delete.username} - {user_to_delete.full_name}")
    if total_tickets > 0:
        print(f"   Ticket da riassegnare: {tickets_created} creati + {tickets_assigned} assegnati = {total_tickets} totali")
        print(f"   Tutti i ticket verranno riassegnati al primo amministratore disponibile.")
    else:
        print(f"   Nessun ticket da riassegnare.")
    
    # Conferma eliminazione
    confirm = input(f"\nSei SICURO di voler eliminare '{user_to_delete.username}'? (scrivi 'ELIMINA' per confermare): ")
    if confirm != 'ELIMINA':
        print("Operazione annullata.")
        return
    
    try:
        # Riassegna ticket se ce ne sono
        if total_tickets > 0:
            admin_user, reassigned_created, reassigned_assigned = user_to_delete.reassign_tickets_to_admin()
            print(f"🔄 Riassegnando {reassigned_created + reassigned_assigned} ticket a '{admin_user.username}'...")
        
        # Elimina l'utente
        username = user_to_delete.username
        db.session.delete(user_to_delete)
        db.session.commit()
        
        print(f"\n✅ Utente '{username}' eliminato con successo!")
        if total_tickets > 0:
            print(f"📋 {reassigned_created + reassigned_assigned} ticket riassegnati a '{admin_user.username}'")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Errore durante l'eliminazione: {str(e)}")

def reset_password():
    """Reset password di un utente"""
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    print(f"\n🔄 RESET PASSWORD")
    print("-" * 40)
    print("Utenti disponibili:")
    
    for i, user in enumerate(users, 1):
        admin = "🔑" if user.is_admin else "👤"
        print(f"{i}. {admin} {user.username} - {user.full_name}")
    
    print("0. Annulla")
    
    # Selezione utente
    while True:
        try:
            choice = input(f"\nSeleziona utente (1-{len(users)}) o 0 per annullare: ").strip()
            choice = int(choice)
            
            if choice == 0:
                print("Operazione annullata.")
                return
                
            if 1 <= choice <= len(users):
                selected_user = users[choice - 1]
                break
            else:
                print("❌ Selezione non valida!")
        except ValueError:
            print("❌ Inserisci un numero valido!")
    
    print(f"\n📋 Reset password per: {selected_user.username} - {selected_user.full_name}")
    
    # Nuova password
    while True:
        new_password = getpass("Nuova password: ")
        if len(new_password) < 6:
            print("❌ La password deve essere di almeno 6 caratteri!")
            continue
            
        confirm_password = getpass("Conferma password: ")
        if new_password != confirm_password:
            print("❌ Le password non coincidono!")
            continue
        break
    
    try:
        selected_user.set_password(new_password)
        db.session.commit()
        print(f"✅ Password di '{selected_user.username}' aggiornata con successo!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Errore durante l'aggiornamento: {str(e)}")

def main():
    app = create_app()
    
    with app.app_context():
        while True:
            show_menu()
            
            try:
                choice = input("\nSeleziona un'opzione: ").strip()
                
                if choice == '0':
                    print("👋 Arrivederci!")
                    break
                elif choice == '1':
                    list_users()
                elif choice == '2':
                    create_user(is_admin=False)
                elif choice == '3':
                    create_user(is_admin=True)
                elif choice == '4':
                    delete_user()
                elif choice == '5':
                    reset_password()
                else:
                    print("❌ Opzione non valida!")
                    
                if choice != '0':
                    input("\nPremi INVIO per continuare...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Operazione interrotta dall'utente!")
                break
            except Exception as e:
                print(f"\n❌ Errore imprevisto: {str(e)}")
                input("Premi INVIO per continuare...")

if __name__ == "__main__":
    main()