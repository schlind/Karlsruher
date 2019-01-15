# Karlsruher Retweet Bot

Hallo, das wird der neue \@Karlsruher Retweet Bot.

Implementierung basiert auf tweepy.

## Quick & Dirty

``` ./run-cron.py -test ```

* karlsruher.py ist das Modul mit der "bot" Klasse.
* mock.py enthält Testdaten und Twitter Mock
* register.py Registriert den Bot manuell, irgendwie.
* credentials.py.default enthält die Zugangsdaten
* run-cron.py führt die Aufgaben des Bots aus.
mit "-test" als erstes und einziges Argument, simuliert der Bot seine Aktionen mit Testdaten und ohne Verbindung.

...
