# Karlsruher Retweet Bot

Hallo, ich bin der \@Karlsruher Retweet Bot.

Ich retweete automatisch alle Tweets, die mich mit \@Karlsruher erreichen. Refresh alle 5 Minuten.

https://twitter.com/Karlsruher

Die Idee und eine Urimplementierung dieses Bots stammt von Marco, \@syn2
https://twitter.com/syn2, der den Karlsruher auch jahrelang mit reichlich Strom und gutem Internet versorgt hat. Vielen Dank dafür!

##


## Code Quick & Dirty

Der Code hier ist ein spontaner Rewrite auf Basis von Marcos Code, zwei Tassen Kaffee und circa 4 Stunden Python lernen, weil das mein erster Kontakt mit Python ist. Ich hoffe, man kann den Code gut lesen, aber er funktioniert! Fehlerhandling (fehlende Datei usw.) mache ich selbstverständlich später vielleicht noch.

Keine Lizenz, keine Garantie, keine Zeit für Support.

Der Bot-Code ist generalisiert und nicht an den Karlsruher Account gebunden. So kann er vermutlich -auf eigene Veranwtortung- mit jedem beliebigen Twitter-Account betrieben werden, wenn für ihn API-Keys vorliegen. https://developer.twitter.com

Kopiere dafür die mitgelieferte Beispieldatei so

	`# cp credentials.py.example credentials.py`

und trage in die neue Kopie Deine eigenen API-Keys ein.
Der Bot erkennt den Account selbst und legt automagisch eine Datenbank für ihn an.


	`# ./run-cron.py`


Dateien:

* karlsruher.py ist das Modul mit der "bot" Klasse.
* register.py Registriert den Bot manuell, irgendwie.
* credentials.py.example enthält die API Zugangsdaten (nach credentials.py kopieren)
* run-cron.py führt die Aufgaben des Bots aus.
mit "-test" als erstes und einziges Argument, simuliert der Bot seine Aktionen mit Testdaten und ohne Verbindung zu Twitter.
* mock.py enthält Testdaten und Twitter Mock für lokales Gefrickel.

...
