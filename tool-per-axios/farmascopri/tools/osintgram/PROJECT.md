# Osintgram — Instagram OSINT Tool

## Descrizione
Tool OSINT per Instagram. Analisi account, follower, commenti, foto, geolocalizzazione. Fork da Datalux/Osintgram.

## Installazione
```bash
cd ~/progetti/osint-projects/osintgram
source venv/bin/activate
pip install -r requirements.txt
```

## Configurazione
Inserire credenziali Instagram in `config/credentials.ini`:
```ini
[Credentials]
username = tuo_instagram
password = tua_password
hikerapi_token = (opzionale)
```

## Utilizzo
```bash
source venv/bin/activate
python3 main.py <username_target>
```

## Comandi principali
| Comando | Funzione |
|---------|----------|
| `info` | Info profilo |
| `photos` | Scarica foto |
| `followers` | Lista follower |
| `comments` | Commenti recenti |
| `stories` | Storie |
| `user_id` | ID numerico |

## Stato
✅ Installato (richiede credenziali)
