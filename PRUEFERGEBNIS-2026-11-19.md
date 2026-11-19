# BADART: Browser- und Anmeldepruefung vom 19.11.2026

## Ergebnis und Umfang

Die Zugangsdaten des eigenen Shop-Testkundenkontos wurden in GitHub hinterlegt und
durch echte Anmeldungen bestaetigt. Der Pruefmechanismus ist im eigenen Repository
eingerichtet. Die Gesamtfreigabe fuer alle Geraete, Registrierungen und Zahlungen
bleibt offen. Eine Zugriffssperre oder ein nicht verbundener Simulator gilt nie als PASS.

## Abnahme nach Geraetegruppe

| Gruppe | Grundpruefung ohne Absenden | Geschuetzte Anmeldung |
|---|---|---|
| Windows / Chrome | 12 PASS, 1 FAIL | PASS |
| Windows / Edge | 12 PASS, 1 FAIL | PASS |
| Windows / Firefox | 12 PASS, 1 FAIL | PASS |
| Mac / Safari | 11 PASS, 1 FAIL, 1 BLOCKED | PASS, Safari 26.6 auf Intel |
| iPhone / Safari | 12 PASS, 1 FAIL im Simulator | BLOCKED: Safari-Sitzung startet nicht |
| iPad / Safari | 12 PASS, 1 FAIL im Simulator | BLOCKED: Safari-Sitzung startet nicht |
| Android-Handy / Chrome | 12 PASS, 1 FAIL im Emulator | BLOCKED: Shopantwort 403 |
| Android-Tablet / Chrome | 12 PASS, 1 FAIL im Emulator | BLOCKED: Shopantwort 403 |

FAIL bedeutet hier die unten beschriebene Bundesland-Dublette, keine gescheiterte
Anmeldung. Die Grundpruefung und Anmeldung sind getrennte Laeufe; ihre Ergebnisse
werden nicht zu einer vollstaendigen Bestellfreigabe zusammengezogen.

## Erfolgreiche Desktop-Anmeldungen

| Browser | Tatsaechliche Version | System | Ergebnis / Nachweis |
|---|---|---|---|
| Chrome | 156.0.8078.80 | Windows Server 2025 | PASS: Konto-/Abmeldenachweis, [Lauf 10](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44554282175) |
| Firefox | 159.0.1 | Windows Server 2025 | PASS: Konto-/Abmeldenachweis, [Lauf 10](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44554282175) |
| Edge | 156.0.4314.58 | Windows Server 2025 | PASS nach Korrektur der DOM-Wechsel-Wartebehandlung, [Lauf 12](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44554881093) |
| Safari | 26.6 | macOS 15.7.9, Intel | PASS mit finaler Vorabpruefung, [Lauf 14](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44557007651) |

Die Browser stammen aus den jeweiligen gehosteten Standardimages. Versionsnummern
koennen sich zwischen zwei Runnern unterscheiden; die Job-Zusammenfassung ist massgebend.

## Mobile Anmeldung und Infrastruktur

**iPhone und iPad, iOS 18.6:** Die oeffentlichen Formular-Grundtests gelangen am
Vormittag. Die geschuetzte Anmeldung ist dagegen noch nicht bestaetigt.
Appium/WDA baut erfolgreich, verbindet die Safari-Sitzung aber nicht innerhalb
des expliziten 240-Sekunden-Limits. Auch der zum installierten Xcode 16 passende
Treiber loeste den iPad-Startfehler nicht. Der Fehler liegt vor Shop-Aufruf und
Zugangsdaten-Eingabe. Das ist eine blockierte Testinfrastruktur, kein nachgewiesener
Shop- oder Passwortfehler.

Nachweis: [Apple-Anmeldelauf 17](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44563897482).

Apples direkter Safari-WebDriver wurde als zweiter Weg ohne Appium/WDA ausgefuehrt.
Auf dem iPad beendete er den Browserstart mit SessionNotCreatedException, ebenfalls
vor Shop-Aufruf und Eingabe. Es gibt daher auch ueber diesen Weg keinen iPad-Login-PASS.
Der konkrete Grund dieser nativen Sitzungsablehnung ist noch nicht eingegrenzt.
Die alternative Steuerung bleibt als ausdruecklicher Diagnosemodus verfuegbar.
Auch auf dem iPhone SE (3. Generation) mit iOS 18.6 endete der native Browserstart
mit WebDriverException vor dem Shop-Aufruf. Der iPad-Simulator war ein iPad mini
(A17 Pro), ebenfalls iOS 18.6. Beide Wege haben somit keinen mobilen Apple-Login-PASS.
Nachweis: [Direkter Apple-Lauf 18](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44566397574).

**Android-Handy und Android-Tablet:** BLOCKED. Die Emulatoren starten mit Android 15.
Der Shop liefert dem Testbrowser auf der Anmeldeseite jedoch **403 Forbidden**,
ohne die erwarteten Eingabefelder. Es wurden in diesen blockierten Laeufen keine
Zugangsdaten eingegeben oder abgesendet. Die Diagnose bestaetigt ein Zugriffsverbot,
nicht dessen Ursache und nicht einen Fehler auf normalen Android-Kundengeraeten.

Nachweise: [Android-Paarlauf 7](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44551718008)
und [gezielte Diagnose 9](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44552832258).
Eine einmalige Neuladung loeste das Problem nicht. Weitere Android-Versuche wurden
nach dem bestaetigten Zugriffsverbot gestoppt. Der finale Testcode erkennt 403 direkt.

**ARM-Macs:** GitHub meldete Kapazitaetsprobleme. Die Jobs auf macOS 26 wurden nach
mehreren erfolglosen Zuteilungsversuchen vom Anbieter beendet; der anschliessende
macOS-15-ARM-Versuch erhielt ebenfalls keinen Runner und wurde beendet. Kein
Safari-27-/ARM-Anmeldenachweis aus diesen Laeufen.

Nachweise: [Lauf 6](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44550527257)
und [Lauf 11](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44554380745).

## Bereits bestaetigte Grundpruefung am Vormittag

Die 13 Grundfaelle umfassen Formularpflichtfelder, E-Mail-Constraints ohne Absenden,
Privat/Firma, Lieferadresse, Laender, Wiederherstellungsseite ohne Mailversand,
oeffentliche Shopseiten sowie horizontales Ueberlaufen.

- Chrome, Edge, Firefox, Android-Handy, Android-Tablet, iPhone und iPad: jeweils
  12 PASS und 1 FAIL in den bestaetigten Laeufen.
- Der gemeinsame FAIL betrifft deutsche Bundeslaender: 21 Optionen, aber nur 16
  eindeutige Namen. Doppelt: Baden-Wuerttemberg, Bayern, Brandenburg, Hamburg, Hessen.
- Safari Desktop: 11 PASS, derselbe FAIL und 1 BLOCKED bei der Ruecknavigation von
  der Passwort-Wiederherstellungsseite. Der BLOCKED-Fall ist kein belegter Kundenfehler.
- Die damaligen mobilen Grundtests ersetzen keinen heutigen erfolgreichen Login.
  Simulatorstarts waren auch am Vormittag nicht in jedem Lauf stabil.

Belege: [iPhone und Desktop / Lauf 16](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44478903496),
[iPad / Lauf 18](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44481145731),
[Android nach Scrollkorrektur / Lauf 20](https://github.com/badartshoptest/badart-browser-checks/actions/runs/44482701279).
Bei spaeter abgebrochenen Gesamtlaeufen bleiben die jeweils abgeschlossenen Einzeljobs
mit ihren Ergebnissen erhalten.

## Noch nicht freigegeben

Erfolgreiche neue Privat-/Firmenregistrierung, Abbruch/Fortsetzung, doppelte E-Mail,
Reset-Mail-Zustellung, geraeteuebergreifende Warenkorb-/Steuer-/Versandberechnung,
Zahlungsabschluss, Apple Pay und Bank-App-Rueckkehr sind nicht vollstaendig abgenommen.
Eine zuvor separat durchgefuehrte und stornierte manuelle Testbestellung ist kein
Bestellnachweis fuer alle Browser. In diesen automatischen Laeufen wurden keine
weiteren Registrierungen, Mails oder Bestellungen ausgeloest.

## Betrieb und naechste technische Schritte

Die Bedienung und die beiden Workflows stehen in [README.md](README.md). Es gibt
keinen Zeitplan und keine Hintergrundueberwachung. Die Standardauswahl des
Anmeldetests ist die bestaetigte Desktop-Gruppe. Es wurden keine kostenpflichtigen
Runner, Zusatzdienste oder Tarifwechsel eingerichtet.

Der Anmeldetest verlangt Konto-Inhalt oder Abmeldelink, nicht bloss eine Konto-URL.
Er behandelt den DOM-Wechsel nach der Anmeldung lesend, ohne erneut abzusenden.
Die Appium-Verbindung hat 240 Sekunden Zeitlimit je Anfrage; Jobs haben insgesamt
35 Minuten (Grundpruefung: 25 Minuten). Ergebnisse werden sofort ausgegeben. Die 27 lokalen Schutzpruefungen
einschliesslich Datenschutz, fehlender Secrets, falscher Positivnachweise, begrenzter
Neuladung und Verbindungszeitlimit bestehen.

Fuer Android ist die serverseitige Ursache des 403 zu klaeren: Shop-/Webserver- bzw.
Schutzsystem-Logs fuer 19.11.2026 etwa 16:05 bis 16:20 Uhr Europe/Berlin,
GET auf die Shop-Anmeldeseite von den GitHub-Linux-Testrechnern. Ob Webserver,
Schutzregel oder ein anderer Bestandteil sperrt, ist noch nicht bestaetigt. Es
wurde keine Schutzregel geaendert oder umgangen.

Die Quelle der doppelten Bundesland-Optionen ist im Shop bzw. beteiligten Plugin
zu ermitteln, zu korrigieren und danach gezielt nachzupruefen. Eine Ursache fuer Registrierungsabbrueche wurde
dadurch noch nicht nachgewiesen.
