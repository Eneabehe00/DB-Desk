"""Genera un report PDF per ticket specifici ed esclude i ticket dal report giornaliero."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.ticket_report_pdf import generate_custom_ticket_report


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else 'alex'
    ticket_numbers = sys.argv[2:] if len(sys.argv) > 2 else [
        'TK2026050074',
        'TK2026050010',
        'TK2026050102',
        'TK2026050112',
        'TK2026050113',
        'TK2026050093',
        'TK2026050117',
        'TK2026050127',
        'TK2026060004',
    ]

    app = create_app()
    with app.app_context():
        pdf_path, tickets = generate_custom_ticket_report(app, username, ticket_numbers)
        print(f'Report generato: {pdf_path}')
        print(f'Ticket inclusi ({len(tickets)}):')
        for ticket in tickets:
            print(f'  - {ticket.numero_ticket} (escluso da report giornaliero)')
        print('I ticket sopra non compariranno più nel report giornaliero PDF per intervallo date.')


if __name__ == '__main__':
    main()
