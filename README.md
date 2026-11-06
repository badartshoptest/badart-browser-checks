# BADART Browser- und Geraetepruefung

Eigenes Testprojekt von **badartshoptest**. Es enthaelt ausschliesslich Testcode fuer
die oeffentliche Storefront, keine Shop-Quelldateien und keine Kundendaten.

## Start und Ergebnis

Unter **Actions → BADART Browser- und Geraetepruefung → Run workflow** starten.
`necessary` waehlt notwendige Cookies, `all` alle Cookies, soweit die Schaltflaeche
in der frischen Sitzung vorhanden ist. Ein gesonderter Fall zeigt, ob die Auswahl
tatsaechlich ausgefuehrt werden konnte. Es besteht kein Zeitplan und keine Ueberwachung
im Hintergrund. Ein weiterer Start wartet auf den vorherigen Durchlauf.

Die Auswahl `all` prueft acht Ziele, hoechstens vier gleichzeitig. `desktop`, `mobile`, `apple`, `android` und einzelne Browser/Geraete ermoeglichen gezielte Wiederholungen. Der Ergebnisbericht steht
direkt in der Zusammenfassung des jeweiligen Actions-Jobs. Er nennt Browser, Version,
Betriebssystem, Simulator/Emulator und jeden Testfall.

| Ziel | Ausfuehrung | Grenze |
|---|---|---|
| Chrome, Edge, Firefox | Originalbrowser auf Windows-2025-Runner | Windows Server, kein Nachweis fuer alle Windows-PCs |
| Safari | Originalbrowser auf gewaehltem macOS-Standardimage | Die dort installierte Version |
| iPhone und iPad | Safari im Apple-Simulator | Neuester zum aktiven Xcode-SDK passender installierter iOS-Runtime; kein physisches Geraet |
| Android-Handy | Chrome im Android-15-Emulator | Pixel-7-Profil, keine OEM-Vollabdeckung |
| Android-Tablet | Derselbe Emulator mit Tablet-Aufloesung und -Dichte | Generisches Tablet-Profil, kein bestimmtes physisches Tablet |

**PASS** bedeutet: die konkrete Assertion wurde ausgefuehrt und erfuellt.
**FAIL** bedeutet: eine konkrete Erwartung ist verletzt.
**BLOCKED** bedeutet: beispielsweise Browserstart, Elementzugriff oder Infrastruktur
verhinderten eine belastbare Aussage. Fehlende Berichte, leere Testlisten und blockierte
Tests gelten niemals als bestanden. Auch ein gruener Grundprueflauf ist keine
vollstaendige Freigabe fuer Registrierung, Anmeldung und Bestellung.

## Testumfang

- Cookieauswahl im frischen Browser (soweit sichtbar).
- Sichtbare Pflichtfelder fuer Anmeldung und Registrierung.
- Browservalidierung leerer und ungueltiger E-Mail-Eingaben, ohne Absenden.
- Privat/Firma-Umschaltung und abweichende Lieferadresse.
- Auswahl Deutschland, Oesterreich, Schweiz; deutsche Bundesland-Dubletten.
- Passwort-Wiederherstellungsseite und Ruecknavigation, ohne Mailversand.
- Startseite, leerer Warenkorb, Kontaktseite, Wohnen-Listing und Produktdetail.
- Horizontales Ueberlaufen des Anmeldeformulars bei zwei Desktopbreiten bzw.
  Hoch-/Querformat im Simulator/Emulator. Dies ersetzt keine manuelle Sichtpruefung.

## Offene Abnahmefaelle

Erfolgreiche Privat-/Firmenregistrierung, Login mit Testkonto, abgebrochene und
fortgesetzte Registrierung, doppelte E-Mail, abweichende Passwoerter, Servervalidierung,
Passwort-Reset-Zustellung, bezahlter Artikel im Warenkorb, Versand-/Steuerberechnung,
Zahlungsabschluss und Rueckwege, Apple Pay, Bank-App-Wechsel, Autofill, echte Geraete
und historische Browserversionen sind **nicht abgenommen**. Hierfuer fehlen noch
Testkonto, geeignete Testdaten und ein abgestimmter Testmodus fuer E-Mail/Bestellung/
Zahlung. Diese Faelle werden nicht durch reine Seitenaufrufe als bestanden markiert.

## Kosten und Schutz

Nur manuell gestartete Standard-GitHub-Runner im freigegebenen oeffentlichen Original-
Repository. Keine kostenpflichtigen Zusatzdienste, keine Artefakt-Uploads und keine
Caches. Der Job startet nicht in privaten Repositories oder Forks. Die vorhandenen
kostenlosen GitHub-Bedingungen und Nutzungsgrenzen gelten; kuenftige Tarifaenderungen
muessen erneut bewertet werden. Es werden keine Zahlungsdaten hinterlegt.

Der GitHub-Token ist nur lesend; Checkout speichert keine Zugangsdaten. Keine Secrets
werden eingelesen. Keine automatischen E-Mails, Registrierungen oder Bestellungen.
Die oeffentlichen Berichte enthalten feste Testbezeichnungen und technische Versionen,
keine Screenshots, HTML-Dumps, Formularinhalte oder ungefilterten Fehlermeldungen.
Appium lauscht nur auf 127.0.0.1 im temporaeren Runner. Nur sein Android-Chromedriver-
Download ist freigegeben. Der Runner wird nach dem Job verworfen.

## Technische Pflege

Python-Pakete und Appium/Treiber sind versionsgebunden, GitHub-Actions auf Commit-SHAs.
Runner-Browser und installierte Apple-Simulatoren werden von GitHub aktualisiert;
der Bericht nennt daher den wirklich ausgefuehrten Stand. Fehlgeschlagene Laufzeiten
oder entfernte Images muessen repariert und erneut getestet werden.

Lokal: `python -m pip install -r requirements.txt`, danach
`python -m unittest -v test_mechanism`. Diese Selbsttests pruefen den Mechanismus,
nicht den Shop. Echte Browserpruefungen laufen getrennt mit `python check_shop.py`.

Quellen: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://www.selenium.dev/documentation/webdriver/
https://appium.github.io/appium-xcuitest-driver/latest/overview/
https://appium.github.io/appium-uiautomator2-driver/latest/
