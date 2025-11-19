#!/usr/bin/env python3
import os
import subprocess
import re
from app import create_app
from config import config


def get_network_ip():
    """
    Rileva se è attiva una connessione ZeroTier e restituisce l'IP appropriato.
    Se ZeroTier è attivo, restituisce l'IP della VPN, altrimenti l'IP della scheda principale.
    """
    try:
        # Esegue ipconfig per ottenere informazioni sulle interfacce di rete
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')

        if result.returncode != 0:
            print("Errore nell'esecuzione di ipconfig")
            return '0.0.0.0'

        output = result.stdout

        # Cerca interfacce ZeroTier
        zerotier_interfaces = re.findall(r'ZeroTier One \[([^\]]+)\]:', output, re.IGNORECASE)

        if zerotier_interfaces:
            # Cerca l'IP IPv4 per l'interfaccia ZeroTier
            # Cerca direttamente nell'output le linee che contengono Indirizzo IPv4 dopo ZeroTier
            lines = output.split('\n')
            in_zerotier_section = False

            for line in lines:
                if 'ZeroTier One' in line and '[' in line and ']' in line:
                    in_zerotier_section = True
                    continue

                if in_zerotier_section:
                    # Se siamo in una sezione ZeroTier e troviamo una scheda diversa, usciamo
                    if ('Scheda Ethernet' in line or 'Scheda Wi-Fi' in line) and 'ZeroTier' not in line:
                        in_zerotier_section = False
                        continue

                    # Cerca Indirizzo IPv4
                    ip_match = re.search(r'Indirizzo IPv4[.\s]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line, re.IGNORECASE)
                    if ip_match:
                        vpn_ip = ip_match.group(1)
                        print(f"Rilevata connessione ZeroTier con IP: {vpn_ip}")
                        return vpn_ip

        # Se non trova ZeroTier, cerca l'IP della scheda principale (quella con gateway)
        # Prima cerca schede Ethernet o Wi-Fi con gateway
        interfaces = re.split(r'\n\s*\n', output)

        for interface in interfaces:
            if ('Ethernet' in interface or 'Wi-Fi' in interface or 'Wireless' in interface) and 'Media disconnected' not in interface:
                # Controlla se ha un gateway (Default Gateway)
                if 'Default Gateway' in interface and '0.0.0.0' not in interface:
                    # Estrai Indirizzo IPv4
                    ip_match = re.search(r'Indirizzo IPv4[.\s]*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', interface, re.IGNORECASE)
                    if ip_match:
                        local_ip = ip_match.group(1)
                        print(f"Usando IP scheda di rete locale: {local_ip}")
                        return local_ip

        # Fallback: usa 0.0.0.0
        print("Impossibile determinare IP, usando 0.0.0.0")
        return '0.0.0.0'

    except Exception as e:
        print(f"Errore nel rilevamento IP: {e}")
        return '0.0.0.0'


# Determina l'ambiente di esecuzione
config_name = os.environ.get('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    # Ottieni configurazione dalla classe Config
    config_obj = config[config_name]
    port = config_obj.FLASK_PORT
    debug = config_obj.FLASK_DEBUG

    # Determina l'host: se configurato esplicitamente usa quello, altrimenti rileva automaticamente
    configured_host = config_obj.FLASK_HOST
    if configured_host != '0.0.0.0':
        # Host configurato esplicitamente
        host = configured_host
        print(f"Usando host configurato: {host}")
    else:
        # Rilevamento automatico dell'IP di rete
        host = get_network_ip()

    print(f"Avviando DB-Desk su {host}:{port}")
    print(f"URL di accesso: http://{host}:{port}")
    if host == '0.0.0.0':
        print("L'app è accessibile da qualsiasi interfaccia di rete")

    app.run(host=host, port=port, debug=debug)