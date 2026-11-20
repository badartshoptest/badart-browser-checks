# BADART Browser- und Geraetepruefung

Eigenes Testprojekt von **badartshoptest** fuer die BADART-Storefront.
Es enthaelt Testcode, keine Shop-Quelldateien und keine Kundendaten.

## Bestaetigter Stand am 19.11.2026

Erfolgreiche Anmeldung: Chrome, Edge, Firefox und Safari 26.6 auf Intel-Mac.
Android-Anmeldung: BLOCKED durch eine Shopantwort 403 vor jeder Eingabe.
iPhone/iPad-Anmeldung: noch kein bestaetigter PASS; Simulator-Infrastruktur blockiert.
[Gesamtergebnis und Nachweise](PRUEFERGEBNIS-2026-11-19.md).
Der Anmeldetest startet standardmaessig mit `desktop`; mobile Ziele bleiben
fuer die gezielte technische Nachpruefung waehlbar. Kein vollstaendiger
Registrierungs- oder Bestellnachweis.

## Start und Ergebnisse

Unter **Actions** gibt es zwei getrennte Pruefungen:

| Workflow | Umfang | Start |
|---|---|---|
| BADART Browser- und Geraetepruefung | 13 Grundpruefungen ohne Kundenanmeldung | Manuell oder bei Aenderungen an den Grundtest-Dateien |
| BADART Geschuetzter Anmeldetest | Anmeldung mit dem eigenen Shop-Testkundenkonto; positive Konto-/Logout-Bestaetigung | Ausschliesslich manuell auf main |

Workflow auswaehlen, **Run workflow**, Branch **main**, Ziel und Apple-Image
auswaehlen, danach starten. `all` prueft acht Ziele, hoechstens vier gleichzeitig.
Fuer den bestaetigten Intel-Mac-Weg `macos-15-intel` ausdruecklich auswaehlen;
die Startmaske kann eine fruehere Auswahl behalten.
`desktop`, `mobile`, `apple`, `android` oder ein einzelnes Ziel erlauben gezielte
Wiederholungen. Dasselbe Ziel mit demselben Systemimage laeuft nur einmal gleichzeitig.
Es gibt keinen Zeitplan und keine Hintergrundueberwachung.

Ergebnisse stehen in der Zusammenfassung jedes Jobs. **PASS** bestaetigt die
tatsaechlich erfuellte Erwartung, **FAIL** eine verletzte Erwartung. **BLOCKED**
bedeutet, dass beispielsweise Browserstart oder Elementzugriff eine belastbare
Aussage verhindert haben. Fehlende oder blockierte Tests gelten nie als bestanden.
Ein erfolgreicher Anmeldetest allein gibt keine Registrierung oder Bestellung frei.

## Browser und Geraete

| Ziel | Ausfuehrung | Grenze |
|---|---|---|
| Chrome, Edge, Firefox | Originalbrowser auf Windows-2025-Runner | Windows Server; kein Nachweis fuer alle Windows-PCs |
| Safari | Originalbrowser auf gewaehltem macOS-Standardimage | Die dort installierte Version |
| iPhone und iPad | Safari im Apple-Simulator | Neuester zum aktiven Xcode-SDK passender installierter iOS-Runtime; kein physisches Geraet |
| Android-Handy | Chrome im Android-15-Emulator | Pixel-7-Profil; keine OEM-Vollabdeckung |
| Android-Tablet | Android-Emulator mit Tablet-Aufloesung und -Dichte | Generisches Tablet-Profil |

Verfuegbare Apple-Standardimages: `macos-15-intel`, `macos-15`, `macos-26`.
Berichte nennen die tatsaechlich verwendete Umgebung. Simulatorstarts koennen
scheitern; ein solcher Lauf ist keine Aussage ueber einen Shopfehler. Historische
Safari-Versionen und echte iPhones/iPads werden durch diese Auswahl nicht ersetzt.

## Zugangsdaten des Anmeldetests

Unter **Settings -> Secrets and variables -> Actions** werden ausschliesslich
die Zugangsdaten des eigenen **Shop-Testkundenkontos** hinterlegt:

| Repository secret | Inhalt |
|---|---|
| SHOP_TEST_EMAIL | Im BADART-Shop registrierte E-Mail-Adresse des Testkunden |
| SHOP_TEST_PASSWORD | Passwort dieses Shop-Kundenkontos |

Die Daten werden vom Nutzer direkt in GitHub eingegeben. Sie sind keine GitHub-
oder Postfach-Zugangsdaten. Eine Mailbox allein erstellt kein Shop-Kundenkonto.
Die Secrets werden nur dem Schritt zur Shop-Anmeldung uebergeben. Die Grundpruefung
liest keine Secrets. Der Login wird nur auf dem freigegebenen HTTPS-Shop ausgefuehrt.

Der Anmeldetest sendet keine Registrierung, Reset-Mail oder Bestellung ab und
aendert weder Warenkorb noch Adressen. Er prueft zunaechst die Browservalidierung
der E-Mail-Adresse und verlangt nach dem Absenden einen positiven Anmeldenachweis.
Eine ausdrueckliche Ablehnung der Zugangsdaten wird als FAIL gemeldet.

## Umfang der Grundpruefung

- Cookieauswahl im frischen Browser, soweit sichtbar.
- Pflichtfelder, leere und ungueltige E-Mail-Eingaben ohne Absenden.
- Privat/Firma, abweichende Lieferadresse, Deutschland/Oesterreich/Schweiz.
- Deutsche Bundesland-Dubletten.
- Passwort-Wiederherstellungsseite und Ruecknavigation ohne Mailversand.
- Startseite, leerer Warenkorb, Kontakt, Wohnen-Listing und Produktdetail.
- Horizontales Ueberlaufen bei zwei Desktopbreiten beziehungsweise Hoch-/Querformat.

## Offene Abnahmefaelle

Erfolgreiche Privat-/Firmenregistrierung, Abbruch und Fortsetzung einer Registrierung,
doppelte E-Mail, abweichende Passwoerter, Servervalidierung, Reset-Mail-Zustellung,
Versand-/Steuerberechnung, Zahlungsabschluss und Rueckwege, Apple Pay, Bank-App-Wechsel,
Autofill, echte Geraete und historische Browserversionen sind durch diese Workflows
**nicht vollstaendig abgenommen**. Eine separate manuelle Testbestellung ist kein
geraeteuebergreifender Bestellnachweis. Weitere Bestellungen oder Zahlungspruefungen
benoetigen einen konkret abgestimmten Testmodus.

## Kosten und Schutz

Standard-GitHub-Runner im freigegebenen oeffentlichen Originalrepository; keine
kostenpflichtigen Zusatzdienste, Zahlungsdaten, Artefakt-Uploads oder Caches.
Die vorhandenen kostenlosen GitHub-Bedingungen und Nutzungsgrenzen gelten.
Workflows starten nicht in privaten Repositories oder Forks.

Der GitHub-Token ist nur lesend; Checkout speichert keine Zugangsdaten. Oeffentliche
Berichte enthalten feste Testbezeichnungen und technische Versionen, keine
Credentials, Kontoseiten, Screenshots, HTML-Dumps oder ungefilterten Fehlermeldungen.
Appium lauscht nur auf 127.0.0.1 im temporaeren Runner. Nur der Android-Chromedriver-
Download ist als Appium-Zusatzfunktion freigegeben. Runner werden nach dem Job verworfen.

## Technische Pflege

Python-Pakete und Appium/Treiber sind versionsgebunden, Actions auf Commit-SHAs.
Runner-Browser und Apple-Simulatoren werden vom Anbieter aktualisiert. Entfernte
Images oder fehlgeschlagene Laufzeiten muessen gezielt repariert und nachgeprueft werden.
Fuer Xcode 16 verwendet die Auswahl XCUITest 12.12.4 mit WDA 16.12.8; fuer Xcode 26+
XCUITest 12.22.8. Grundlage ist die [Appium-Kompatibilitaetstabelle](https://appium.github.io/appium-xcuitest-driver/12.22/getting-started/system-requirements/).
Die tatsaechliche Auswahl steht im Installationsprotokoll. Nicht erkannte oder aeltere
Xcode-Versionen werden abgewiesen.

Appium-Anfragen sind ausdruecklich auf 240 Sekunden je Anfrage begrenzt. Der gesamte
Anmeldetest hat ein Joblimit von 35 Minuten, die Grundpruefung 25 Minuten;
der Simulatorstart hat eigene Zeitgrenzen. Der Apple-Testagent wird im Anmeldetest
vorab in einem eigenen Schritt mit hoechstens 8 Minuten gebaut, damit Buildfehler
vor jeder Verwendung der Shop-Zugangsdaten sichtbar werden. Standard ist das
verfuegbare Intel-Mac-Image; ARM-Images bleiben gezielt auswaehlbar.
Ein 403-Zugriffsverbot wird ohne erneute Anmeldung als BLOCKED behandelt.
Zur Diagnose fehlender Anmeldefelder werden nur Seitentitel und Feldbezeichnungen
vor der ersten Zugangsdaten-Eingabe erfasst, niemals Feldwerte. Konto-URL oder eine
leere Seite allein reichen nicht als Anmeldenachweis. Nach dem Absenden werden nur
Status und Kontoseite gelesen; der Login wird nicht automatisch erneut abgesendet.
Bei einem Fehler waehrend des Browserstarts werden hoechstens sechs gefilterte
Appium-Fehlerzeilen ausgegeben. Dieser Pfad liegt vor jeder Zugangsdaten-Eingabe;
Secrets, E-Mail-Adressen und URLs werden zusaetzlich entfernt.

Lokal: `python -m pip install -r requirements.txt`, danach
`python -m unittest -v test_mechanism test_login`. Diese Selbsttests pruefen den
Mechanismus, nicht den Shop. Grundpruefung: `python check_shop.py`.
Opt-in-Anmeldepruefung mit konfigurierten Umgebungsvariablen: `python check_login.py`.
Secrets niemals in Kommandozeilen, Dateien oder oeffentliche Berichte schreiben.

Quellen: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://www.selenium.dev/documentation/webdriver/
https://appium.github.io/appium-xcuitest-driver/latest/overview/
https://appium.github.io/appium-uiautomator2-driver/latest/

## Alternative iOS-Steuerung

Im geschuetzten Anmeldetest waehlt `ios_backend=native` Apples eigenen Safari-WebDriver
fuer den ausgewaehlten iPhone-/iPad-Simulator. Dieser Weg benoetigt keinen Appium-/WDA-Build.
Die Sitzung muss tatsaechlich iOS melden; ein Mac-Fallback wird abgewiesen.
Der native Weg ist erst nach einem bestaetigten Lauf freigegeben. Bei fehlender
Remote-Automation oder fehlgeschlagenen Eingaben bleibt das Ergebnis BLOCKED.
Es werden keine Eingabewerte per JavaScript eingesetzt.
Quelle: https://webkit.org/blog/9395/webdriver-is-coming-to-safari-in-ios-13/

## Separater Checkout-Vorschaucheck (nur manuell)

`python3 -m unittest -v test_checkout_smoke` prueft die Sicherheitsgrenze offline.
Der optionale manuelle Vorschauworkflow startet standardmaessig nur diese Tests. Er
verwendet einen kostenlosen Ubuntu-Standardrunner im freigegebenen oeffentlichen
Originalrepo, keine Secrets, keinen Cache/Upload und keinen Zeitplan.

Der ausdruecklich aktivierbare GET-Probeaufruf fuehrt keine Browser-Skripte aus
und laedt nur Warenkorb und Bestelluebersicht bzw. fest zugelassene
Vorstufen. Ein leerer Warenkorb, ein Login-Redirect oder eine Sperre ergibt
keine erfolgreiche Bestelluebersicht. Selbst wenn Review-Markup sichtbar ist,
wird kein Formular gesendet und kein Bestell-/Zahlungs-Endpunkt aufgerufen.
Das ist kein Kundenablauf mit befuelltem Warenkorb, kein Steuer-/Versandnachweis
und keiner Zahlungsfreigabe. Fuer diese Abschnitte ist ein abgestimmter
Testshop/Testartikel mit Testzahlungsweg erforderlich. Keine Zugangsdaten oder
Antworttexte werden geloggt.
