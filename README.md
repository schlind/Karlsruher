# Karlsruher Retweet Bot

Hallo, ich bin der [\@Karlsruher Retweet Bot](https://twitter.com/Karlsruher "Karlsruher RT Bot")

## Was mache ich?
Ich retweete automatisch alle Tweets, die mich erwähnen und erreichen.


Beispiel: Du schreibst "Liebe \@Karlsruher, heute hamwa aber auch wieder Wetter, was!?" und ich retweete das dann in die Timelines der Karlsruher, die über solche und ähnlich gelagerte Sachverhalte informiert bleiben möchten.

Ich lese den Inhalt Deiner Tweets nicht, Du musst daher selbst entscheiden, wie relevant Deine Information für die Empfänger sein wird. Triff diese Entscheidung am besten noch bevor Du einen Tweet an mich schreibst.

Aus den Antworten auf meine Retweets halte ich mich raus und ich retweete auch nicht, wenn ich in einer Antwort zu einem anderen Tweet erwähnt werde.

Wenn Du über mich auf einen anderen Tweet hinweisen möchtest, benutze einfach die "Retweet mit Zitat" Funktion von Twitter und erwähne mich im Zitat.

Ich schaue nur alle fünf Minuten auf Twitter und lese dann auch nur eine Hand voll Tweets, meist nur die neusten.


## Historie
Die Idee und eine Urimplementierung dieses Bots stammt von [Marco, \@syn2](https://twitter.com/syn2), der den Karlsruher auch jahrelang mit reichlich Strom und gutem Internet versorgt hat. Vielen Dank dafür!

## Code Quick & Dirty, mitmachen?

Der Code hier ist ein spontaner Rewrite auf Basis von Marcos Code, zwei Tassen Kaffee und circa 8 Stunden Python lernen, weil das mein erster Kontakt mit Python ist. Ich hoffe, man kann den Code gut lesen, aber er funktioniert! Fehlerhandling (fehlende Datei usw.) mache ich selbstverständlich später vielleicht noch.

Keine Lizenz, keine Garantie, keine Zeit für Support.

Der Bot-Code ist generalisiert und nicht an den Karlsruher Account gebunden. So kann er vermutlich -auf eigene Veranwtortung- mit jedem beliebigen Twitter-Account betrieben werden, wenn für ihn API-Keys vorliegen. https://developer.twitter.com

Kopiere dafür die mitgelieferte Beispieldatei so

	`# cp credentials.py.example credentials.py`

und trage in die neue Kopie Deine eigenen API-Keys ein.
Der Bot erkennt den Account selbst und legt automagisch eine Datenbank für ihn an.


	`# ./karlsruher.py [-test] [-talk]`


Dateien:
* karlsruher.py ist das ausführbare Modul.
* register.py Registriert den Bot manuell, irgendwie.
* credentials.py.example enthält die API Zugangsdaten (nach credentials.py kopieren)

...
