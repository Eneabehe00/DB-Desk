-- Aggiunge la colonna intervento_in_garanzia alla tabella fogli_tecnici (MySQL/MariaDB)
-- Eseguire una sola volta sul database esistente.

ALTER TABLE fogli_tecnici
ADD COLUMN intervento_in_garanzia TINYINT(1) NOT NULL DEFAULT 0
COMMENT 'Intervento in garanzia (0=No, 1=Sì)';
