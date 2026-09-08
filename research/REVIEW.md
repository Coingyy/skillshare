> Update 2026-09-08: Website and Worker are deployed. The active catalog now contains 55 entries. Storage Cleanup approval was withdrawn after source review and the entry moved to quarantine. See [current queue decisions](QUEUE-REVIEW.md). The migration observations below describe the earlier state. Automated API review remains unavailable without a key.

# Skillshare: Recherche und Umsetzungsprüfung

Stand: 8. September 2026. Die Umsetzung liegt **lokal** vor. Website, Worker, GitHub-Einstellungen und offene Issues wurden nicht verändert. Es gab keinen kostenpflichtigen API-Aufruf.

## Ergebnis und Methode

47 vorhandene Einträge wurden einzeln anhand von Repository-Metadaten und Anbieter-Dokumentation durchgesehen. Ihre IDs bleiben erhalten. Neun Angebote wurden nach zusätzlichem Sicherheitsscan und dokumentarischer KI-Bewertung ergänzt: insgesamt 56. Der [Einzelbericht](ENTRY-REVIEW.md) enthält jede Entscheidung; [repositories.json](repositories.json) enthält 79 Abfragen einschließlich Alias-Abfragen mit exakten Sternzahlen, UTC-Zeiten und Quellen.

Die meisten Metadaten wurden am 7. September gegen 18:06 UTC erhoben, vier ergänzende Kandidaten am 8. September gegen 12:42 UTC. Sterne sind diese Momentaufnahme, keine Livewerte und kein Sicherheits- oder Qualitätsnachweis. Alle 47 ursprünglichen Repositories waren erreichbar und nicht archiviert; Umbenennungen und inhaltlich veraltete Angaben wurden dennoch korrigiert.

Die neuen Angebote wurden von Codex (GPT-6 Astra) anhand von Anbieter-Dokumentation, Scannerberichten und konkreten Warnungs-Fundstellen bewertet. Dies war eine dokumentarische KI-Prüfung in dieser Arbeit, kein vorgetäuschter Lauf des späteren API-Workflows. Scan-Commits und Zeiten stehen in [scans/](scans/), alle 23 Warnungsbewertungen in [warning-reviews.json](warning-reviews.json). Fremde Installationsskripte, Hooks und Skills wurden nicht ausgeführt. Abhängigkeiten, Geräte und tatsächliche Plattformfunktionen wurden nicht getestet.

## Plattformen unterscheiden

Lokale Codex-Skills werden über Skill-Verzeichnisse bereitgestellt. Eine lokale SKILL.md ist keine automatische ChatGPT-Integration. OpenAI beschreibt inzwischen eine gemeinsame Plugin-Struktur für mehrere Oberflächen; Komponenten, Tools, Berechtigungen und Einrichtung unterscheiden sich weiterhin. Deshalb gilt die Zuordnung pro Angebot und Plattform anhand konkreter Quellen. [OpenAI Skills](https://learn.chatgpt.com/docs/build-skills), [OpenAI Plugins](https://learn.chatgpt.com/docs/plugins).

Es gibt 44 dokumentierte Claude-Code-Zuordnungen, 23 für Codex und vier für ChatGPT; Mehrfachzuordnungen zählen separat. Kein Eintrag erhält „Self-tested“. Für ChatGPT sind Apps SDK Examples ein Entwicklungsbeispiel, FastMCP ein Server-Framework, Context7 eine dokumentierte OAuth-App und Taste Skill eine manuell eingefügte Gesprächsanweisung. Die [Context7-Anleitung](https://context7.com/docs/resources/all-clients) beschreibt die konkrete ChatGPT-Einrichtung; [FastMCP](https://gofastmcp.com/integrations/chatgpt) erfordert einen erreichbaren Server und passende Kontoberechtigungen.

## Vergleich je Kategorie

Die Tabelle berücksichtigt bestehende Angebote und mehrere Alternativen pro Thema. Nicht ausgewählte Kandidaten wurden nicht alle vollständig gescannt. Nicht-Aufnahme ist keine Malware-Bewertung. Quellen, Pflegezustand und Erhebungszeiten stehen zusätzlich in repositories.json.

| Kategorie | Vergleich mit erhobenen Sternzahlen | Entscheidung |
|---|---|---|
| UI Design | [Impeccable](https://github.com/pbakaus/impeccable) 66.291; [Stitch](https://github.com/google-labs-code/stitch-skills) 8.266; [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) 30.935; [MCP UI](https://github.com/MCP-UI-Org/mcp-ui) 5.128 | Stitch ergänzt die dokumentierte Google-Stitch-Einbindung für beide Coding-Hosts. Impeccable bleibt. Vercel überlappt vorhandene Frontend-Guidance; MCP UI ist ein Entwicklerbaustein mit weiterer Integrationsarbeit. |
| 3D Modeling | [Blender MCP](https://github.com/ahujasid/blender-mcp) 27.518; [FreeCAD MCP](https://github.com/neka-nat/freecad-mcp) 2.069; [Printable](https://github.com/AaronGoldsmith/mcp-printable) 2 | Die etablierten passenden Angebote sind vorhanden. Printable nennt konkrete Agenten, ist aber noch sehr klein und überlappt vorhandene Werkzeuge. Keine Ergänzung nur zum Auffüllen. |
| 3D Printing | [Kiln](https://github.com/codeofaxel/Kiln) 53; [3DP MCP](https://github.com/brs077/3dp-mcp-server) 11; Printable 2; [Bambu Printer MCP](https://github.com/DMontgomery40/bambu-printer-mcp) 128 | Bestehende Spezialisierungen bleiben. 3DP hat eine Claude-Code-Pluginroute, aber abweichende Clone-Owner und geringe Etablierung; Printable ist ebenfalls sehr klein. Keine zusätzliche schwache Empfehlung. |
| Game Dev | [Unity MCP](https://github.com/CoplayDev/unity-mcp) 13.990; [Godot MCP](https://github.com/Coding-Solo/godot-mcp) 5.561; [Godogen](https://github.com/htdt/godogen) 6.753 | Unity MCP ergänzt Unity mit dokumentierten Coding-Hosts. Godogen bleibt. Godot MCP hat keinen Scan-Fund, seine geprüfte Einrichtung fokussiert andere Clients; keine pauschale Host-Zusage. |
| Web | [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp) 36.869; [ExecuteAutomation Playwright](https://github.com/executeautomation/mcp-playwright) 5.645; [Remotion Skills](https://github.com/remotion-dev/skills) 4.501; Vercel Agent Skills 30.935 | Microsoft Playwright ergänzt Browserarbeit mit expliziten Code-/Codex-Befehlen. Der zweite Playwright-Server überlappt stark; Remotion zielt speziell auf Video und wurde hier nicht zusätzlich aufgenommen. |
| Audio & Music | [Ableton MCP](https://github.com/ahujasid/ableton-mcp) 2.990; [ElevenLabs MCP](https://github.com/elevenlabs/elevenlabs-mcp) 1.536; [Coding with Beat](https://github.com/jaychempan/coding-with-beat) 114 | Keine Aufnahme. Ableton dokumentiert vor allem Claude Desktop/Cursor. ElevenLabs hat das lokale Repository archiviert und verweist auf einen gehosteten Nachfolger. Coding with Beat nennt Code/Codex, bleibt ein kleiner macOS-Musikbegleiter mit Installern/Hooks und kein etablierter Ersatz für Audio-Produktion. |
| Automation | [Planning with Files](https://github.com/OthmanAdi/planning-with-files) 26.697; [n8n MCP](https://github.com/czlonkowski/n8n-mcp) 22.844; [n8n](https://github.com/n8n-io/n8n) 203.647; [Codex Action](https://github.com/openai/codex-action) 1.228 | Planning bleibt. n8n ist eine eigene Plattform; n8n MCP hatte 50 Warnungen und benötigt weitere Prüfung. Dessen gelesene Claude-Setup-Datei beschreibt Desktop. Codex Action ist eine API-pflichtige CI-Integration; die eigene Automatisierung verwendet hier eine enger begrenzte API-Ausgabe ohne Agentenwerkzeuge. |
| Code Quality | [Superpowers](https://github.com/obra/superpowers) 282.771; Vercel Agent Skills 30.935; [Verify-First Skills](https://github.com/SOCHI-Co/skills) 0 | Superpowers bleibt. Verify-First ergänzt eine konkrete offene Community-Einreichung nach Scan/Inhaltsprüfung. Es ist keine Popularitätsempfehlung; 0 Sterne bleiben sichtbar. |
| Docs | [Context7](https://github.com/upstash/context7) 61.738; [MarkItDown](https://github.com/microsoft/markitdown) 179.837; [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) 53.647 | Context7 ergänzt aktuelle Bibliotheksdokumentation und konkrete Einrichtung. MarkItDown ist primär Konverter; die gelesene MCP-Anleitung beschreibt lokale vertrauenswürdige Clients/Claude Desktop. Keine weitere ungeprüfte ChatGPT-Zusage. |
| Integrations | [FastMCP](https://github.com/PrefectHQ/fastmcp) 27.553; [GitHub MCP](https://github.com/github/github-mcp-server) 32.785; [MCP Servers](https://github.com/modelcontextprotocol/servers) 90.138; [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) 94.565 | FastMCP bietet konkrete Code-/ChatGPT-Anleitungen. GitHub MCP bleibt wegen HIGH blockiert. Sammelverzeichnisse beweisen keine Kompatibilität oder Sicherheit aller verlinkten Server. |
| Subagents | [Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents) 6.108; [Claude Code Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) 24.909; [wshobson Agents](https://github.com/wshobson/agents) 39.470 | Die Codex-Sammlung ergänzt die vorhandene Claude-Code-Sammlung. wshobsons aktuelle native Mehrfachunterstützung wurde korrigiert. |
| Prompting | [prompts.chat](https://github.com/f/prompts.chat) 169.567; [Humanizer](https://github.com/blader/humanizer) 44.895; [Karpathy Skills](https://github.com/multica-ai/andrej-karpathy-skills) 210.846 | Vorhandene Angebote bleiben mit korrigierten Aussagen. prompts.chat, vormals awesome-chatgpt-prompts, bleibt wegen HIGH blockiert. Karpathy-inspiriert bedeutet keine autorisierte Originalarbeit. |
| LLM Tooling | [Claude Code Templates](https://github.com/davila7/claude-code-templates) 30.557; [ECC](https://github.com/affaan-m/ECC) 252.562; [CC Switch](https://github.com/farion1231/cc-switch) 131.532; FastMCP 27.553 | ECC und CC Switch decken Konfiguration/Agentenwerkzeuge ab. Templates überlappt die Sammlungen. FastMCP wurde gezielter unter Integrations ergänzt; keine ChatGPT-Zuordnung aus Werbetexten. |
| Official | [OpenAI Plugins](https://github.com/openai/plugins) 5.471; [OpenAI Skills](https://github.com/openai/skills) 25.924; [Apps SDK Examples](https://github.com/openai/openai-apps-sdk-examples) 2.325; [OpenAI Cookbook](https://github.com/openai/openai-cookbook) 75.831 | Apps SDK Examples ergänzt einen ChatGPT-Entwicklungsweg. openai/skills ist deprecated und verweist auf plugins, obwohl archived=false. openai/plugins bleibt wegen HIGH blockiert. API-Cookbooks sind keine installierbaren ChatGPT-Plugins. |
| Other | [Marketing Skills](https://github.com/coreyhaines31/marketingskills) 47.988; [Storage Cleanup](https://github.com/SOCHI-Co/storage-cleanup) 0; prompts.chat 169.567 | Marketing bleibt. Storage Cleanup wird als liegen gebliebene Community-Einreichung nach Scan/Inhaltsprüfung aufgenommen, mit ungeprüfter Host-Zuordnung. Keine Behauptung, es sei etabliert. |

## Korrekturen am Bestand

- anthropics/anthropic-cookbook wurde zu anthropics/claude-cookbooks umbenannt und als Reference eingeordnet.
- Veraltete Skill-/Befehlszahlen und unbelegte Sicherheits- oder Erfolgsaussagen wurden entfernt, etwa bei Impeccable, UI UX Pro Max, offiziellen Plugins und Meshwright.
- UI UX Pro Max verweist auf ui-ux-pro-max-cli; Graphify auf graphifyy. Das Codex-Plugin-CC wird in Claude Code installiert und benutzt Codex als Abhängigkeit.
- Bambu-only-Fork und allgemeiner Drucker-Server bleiben getrennt, mit Hinweisen auf abweichende Installations-Owner. Generische MCP-Aussagen wurden nicht automatisch zu Plattformfreigaben.
- Der aktuelle OpenSCAD-MCP-Server kompiliert SCAD beziehungsweise explizite Primitive; frühere Rekonstruktionsprototypen sind unter legacy/ archiviert.
- Widersprüche bei Blender-Versionen, Skill-Anzahlen sowie unvollständige Roblox-/Codex-Einrichtung stehen sichtbar in den Einträgen.

## Scannerentscheidungen

Die vorhandenen regulären Ausdrücke und Kontext-Downgrades wurden nicht abgeschwächt. Ergänzt wurden genaue Commit-/Zeitnachweise, Maschinenberichte, Fehler bei unvollständigen Reads und begrenzte Textauswahl für die KI.

| Neue Aufnahme | Scan | Bewertung |
|---|---|---|
| Playwright MCP, Stitch Skills, Codex Subagents, Apps SDK Examples, Storage Cleanup, Verify-First Skills | Jeweils 0 Funde | Dokumentarisch akzeptiert; keine Ausführung oder Prüfung nachgeladener Abhängigkeiten. |
| Context7 | 7 WARN, 0 HIGH | GitHub-/App-/Verschlüsselungskonfiguration und Testdaten. Zwei exec-Treffer sind SDK-Methoden in Tests. Token-Berechtigungen bleiben relevant. |
| Unity MCP | 6 WARN, 0 HIGH | BOM-Verarbeitung, Instanz-Token, Statistikskript und dokumentierte offizielle Installer. Keiner wurde ausgeführt. |
| FastMCP | 10 WARN, 0 HIGH | OAuth-/Umgebungsbeispiele, Tests und Anbieter-CI. Ein echter Cloud-Session-Hook lädt bei Bedarf die GitHub CLI. Aufnahme als Framework, keine pauschale Freigabe von Entwicklungshooks. |

Jede Warnung wurde am Scan-Commit bewertet; siehe [warning-reviews.json](warning-reviews.json).

Nicht aufgenommen: [openai/plugins](blocked/openai__plugins.scan.json) mit vier HIGH, [github/github-mcp-server](blocked/github__github-mcp-server.scan.json) mit einem HIGH und [prompts.chat](blocked/f__prompts.chat.scan.json) mit einem HIGH. Treffer betreffen unter anderem Injection-Formulierungen, Credential-/Netzwerk-Nähe und einen Pipe-to-Shell-Linter-Installer. Beispiel- oder Entwicklungskontext kann Treffer erklären; die Regeln wurden deshalb nicht nachträglich gelockert. Blockiert bedeutet Regelentscheidung, nicht bewiesene Schadsoftware.

## Automatisierung und Nachweise

Claude-Verarbeitung wurde durch verpflichtende OpenAI-Prüfung ersetzt. Das Modell erhält Daten, keine Werkzeuge. Vertrauenswürdiger Projektcode kontrolliert Schema, Belege, unveränderten Bestand, PR-Diff und Merge. Fehlender Schlüssel, unvollständige Antwort, HIGH oder nicht akzeptierte Warnung stoppen die Aufnahme.

Empfang, Prüfung, Merge und Veröffentlichung sind getrennt. Erst der Vergleich mit der vollständig ausgelieferten skills.json erlaubt Published-Meldung und Issue-Schließung. Die beim Kollegen beobachtete Benachrichtigungslücke, Ursache und notwendige Live-Konfiguration stehen in [ACTIVATION.md](ACTIVATION.md).

Lokale Nachweise: Schema/semantische Validierung; 26 Python-Regressionstests für Pflicht-KI, HIGH/Warnungen, Quellen, Legacy-Formate, Duplikate, unveränderten Bestand, tatsächlichen PR-Inhalt, Limits und Veröffentlichung; sechs Worker-Tests; 512 Thema/Programm/Typ-Kombinationen; 260 HTTPS-Links im gerenderten Katalog; Suche, Reset, Mehrfachzuordnung und persistenter Einreichungsstatus. Chrome-Prüfung mit 1440, 390 und 320 Pixeln, auch mit aufgeklappter Einrichtung, ohne horizontalen Überlauf oder JavaScript-Fehler. Dienste/Einreichungen wurden simuliert. Ein AST-Vergleich bestätigte unveränderte Scanner-Regeln und Grenzwerte gegenüber dem ursprünglichen Projektstand. Aktuelle Zahlen und Screenshots liegen unter `.test-output/`.

Quellenlinks stammen aus abgerufenen Anbieter-READMEs/API-Daten oder geöffneten offiziellen Seiten. Die UI-Prüfung kontrolliert Linkformate, nicht jede externe Zielseite. Neue interne Berichtlinks werden erst mit Veröffentlichung dieser Dateien erreichbar. Desktop-/Handyansichten wurden visuell geprüft; die bestehende Gestaltung blieb erhalten.

Offen bleiben der reale API-Durchlauf einer neuen Einreichung nach Hinterlegung des Secrets sowie die Veröffentlichung von Website/Worker. Dieser Bericht behauptet nicht, dass diese Schritte erfolgt seien.
