# Karlsruher Retweet Bot

Was!? Siehe [karlsruher.md](karlsruher.md)

## Technik

### Technologie & Bibliotheken
* Entwickelt mit Python 3.
* verwendet [Tweepy](https://www.tweepy.org/) als Twitter API Adapter.
* ...

### Quelltext & Laufzeit

Der Quelltext besteht aus einem ausführbaren Skript *karlsruher.py* und einer Beispieldatei *credentials.py.example* für die Konfiguartion der notwendigen [API-Keys](https://developer.twitter.com).

Zur Laufzeit erstellt der Bot eine Datenbank *botname.db*, die er bei Bedarf selbst anlegt und mit der Zeit befüllt, sowie eine Lock-Datei *.lock.botname*, die er i.d.R. nach einem Lauf auch wieder selbst löscht.

Dokumentation findet sich hier in *README.md* und für Twitter in [karlsruher.md](karlsruher.md).

### Dateien
#### karlsruher.py
Ein Ausführbares Python3 Skript.

Selbsttest des Bots ausführen:
	`# ./karlsruher.py -test`

Starten des Bots im nur-lesen Modus mit:
	`# ./karlsruher.py`

Starten des Bots im regulären Einsatz:
	`# ./karlsruher.py -talk`

Starten per Cronjob:
	`*/5 *  * * * /path/to/karlsruher.py -talk >> /path/to/karlsruher.log 2>&1`

#### credentials.py.example
Kopiere diese Datei

	`# cp credentials.py.example credentials.py`

und trage in die neue Kopie *credentials.py* Deine eigenen [API-Keys](https://developer.twitter.com) ein. Der Bot erkennt seinen Account selbst, keine Konfiguration notwendig.


#### register.py
Registriert den Bot manuell, irgendwie.
