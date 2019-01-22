# Karlsruher Retweet Bot

Was!? Siehe [karlsruher.md](karlsruher.md)

## Technik

### Technologie & Bibliotheken
* Entwickelt mit Python 3
* verwendet [Tweepy](https://www.tweepy.org/) als Twitter API Adapter
* verwendet Unittests
* verwendet Logging
* ...


### Quelltext & Laufzeit

Der Quelltext besteht aus einem ausführbaren Skript *karlsruher.py* und einer Beispieldatei *credentials.py.example* für die Konfiguartion der notwendigen [API-Keys](https://developer.twitter.com).

Zur Laufzeit erstellt der Bot eine Datenbank *botname.db*, die er bei Bedarf selbst anlegt und mit der Zeit befüllt, sowie eine Lock-Datei *.lock.botname*, die er i.d.R. nach einem Lauf auch wieder selbst löscht.

Dokumentation findet sich hier in *README.md* und für Twitter in [karlsruher.md](karlsruher.md).

#### Disclaimer

Das ist mein erstes Projekt mit Python, Feedback willkommen!


### Kommandos

Der Bot kann auf Kommandos seiner Berater hören.
Berater sind Mitglieder seiner Liste "Advisors" auf Twitter.

Dieses Feature ist zwar fertig, aber noch nicht ausgiebig gestestet.


### Housekeeping

Der Bot muss seine Follower kennen. Da der Bot atkuell über 2000 Follower hat und diese nicht *schnell* und alle 5 Minuten über die Twitter-API gelesen werden können, werden Follower nur 1x am Tag (möglichst nachts) importiert.

Während dieses Imports führt der Bot keine weiteren Aktionen parallel aus.

### Dateien

#### karlsruher.py
Ein ausführbares, fast selbsterklärendes Python3 Skript.


	`# ./karlsruher.py`

Zeigt die Optionen, der Code den Rest. :)


#### credentials.py.example
Kopiere diese Datei

	`# cp credentials.py.example credentials.py`

und trage in die neue Kopie *credentials.py* Deine eigenen [API-Keys](https://developer.twitter.com) ein. Der Bot erkennt seinen Account selbst, keine Konfiguration notwendig.


#### register.py
Registriert den Bot manuell, irgendwie.
